pass                                                                   

                                                                               
   
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


r = load('test_ccd_recipes', 'przypadki-ccd.py')
c = load('test_ccd_checker', 'porownaj-ccd.py')


class Apparatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, text):
        path = self.root / name
        path.write_bytes(text.encode('ascii'))
        return path

    def simple(self):
                                                                               
        words = '00000000 00000000 00000000 00000000 00000000 00000000 00000000 3f800000 00000000 3f800000 00000000 00000000'
        checked = '00000001' + words[8:]
        result = '0 0 4 00000000 00000000 3f800000 00000000'
        return (f'CASE 1 2\nE16 1 1 300 12 {words}\nR16 1 1 300 {result}\nE16 1 2 300 12 {checked}\nR16 1 2 300 {result}\nENDCASE 1\nEND 1\n')

    def test_frozen_population_and_public_modes(self):
        m = r.manifest()
        ops = [op for case in m['cases'] for op in r.operations(case)]
        self.assertEqual((len(m['cases']), len(m['guards']), len(m['parserCases']), len(ops)), (128, 262, 24, 292))
        self.assertEqual(sum(len(case['samples']) for case in m['cases']), 160)
        for case in m['cases']:
            recipe = r.operations(case)
            if case['family'] == 'CACHE_VALUES':
                self.assertEqual([int(w[0], 16) for _, w in recipe], [0, 1, 0, 1, 0, 1])

    def test_two_transport_encodings_mean_same_bits(self):
        c_input = r.input_bytes('DIRECT', 'C').decode().splitlines()
        d_input = r.input_bytes('DIRECT', 'D').decode().splitlines()
        for a, b in zip(c_input, d_input):
            x, y = a.split(), b.split()
            if x[0] == 'O':
                self.assertEqual(x[:4], y[:4])
                self.assertEqual([int(z, 16) for z in x[4:]], [int(z) for z in y[4:]])
            else:
                self.assertEqual(x, y)

    def test_guard_negative_includes_28_accepted_unused(self):
        m = r.manifest()
        self.assertEqual(sum(x['expectedNegative']['accepted'] for x in m['guards']), 28)
        self.assertEqual(sum(x.startswith(b'G ') for x in r.input_bytes('GUARD').splitlines()), 524)

    def test_simple_contract_record_accepted(self):
        stats = c.inspect(self.put('a', self.simple()), 'DIRECT', {1})
        self.assertEqual(stats['operations'], 2)
        self.assertEqual(stats['tags'], {'CASE': 1, 'E16': 2, 'R16': 2, 'ENDCASE': 1, 'END': 1})

    def test_missing_duplicate_and_reordered_records_rejected(self):
        good = self.simple()
        lines = good.splitlines(keepends=True)
        for removed in range(len(lines)):
            with self.subTest(removed=removed):
                with self.assertRaises(c.Invalid):
                    c.inspect(self.put('bad', ''.join(lines[:removed] + lines[removed+1:])), 'DIRECT', {1})
        for duplicate in range(len(lines)):
            with self.subTest(duplicate=duplicate):
                with self.assertRaises(c.Invalid):
                    c.inspect(self.put('bad', ''.join(lines[:duplicate] + [lines[duplicate]] + lines[duplicate:])), 'DIRECT', {1})
        with self.assertRaises(c.Invalid):
            c.inspect(self.put('bad', ''.join([lines[0], lines[2], lines[1], *lines[3:]])), 'DIRECT', {1})

    def test_changed_echo_input_is_not_accepted(self):
        text = self.simple().replace('E16 1 1 300 12 00000000', 'E16 1 1 300 12 00000001')
        with self.assertRaises(c.Invalid):
            c.inspect(self.put('bad', text), 'DIRECT', {1})

    def test_f32_comparison_has_no_tolerance_or_minus_zero_exception(self):
        a = self.put('a', self.simple())
        for changed in ('00000001', '80000000'):
            b = self.put('b', self.simple().replace('R16 1 1 300 0 0 4 00000000', 'R16 1 1 300 0 0 4 ' + changed))
            self.assertGreater(c.compare(a, b)['differences'], 0)

    def test_only_q_is_removed_by_neutrality_projection(self):
        base = 'CASE 1 1\nE16 x\nR16 x\nV16 x\nENDCASE 1\nEND 1\n'
        a = self.put('a', base.replace('R16 x', 'Q16 x\nR16 x'))
        b = self.put('b', base)
        self.assertEqual(c.compare(a, b, True)['differences'], 0)
        for token in ('E16 x\n', 'R16 x\n', 'V16 x\n', 'ENDCASE 1\n', 'END 1\n'):
            self.assertGreater(c.compare(a, self.put('bad', base.replace(token, '')), True)['differences'], 0)

    def test_observer_q_and_copy_v_missing_or_duplicate_detected(self):
        original = 'CASE 113 6\nQ16 x\nV16 x\nENDCASE 113\nEND 1\n'
        a = self.put('a', original)
        for token in ('Q16 x\n', 'V16 x\n'):
            for replacement in ('', token + token):
                self.assertGreater(c.compare(a, self.put('bad', original.replace(token, replacement)))['differences'], 0)

    def test_invalid_output_lexical_forms_rejected(self):
        for text in (self.simple().replace('\n', '\r\n'), self.simple().replace('CASE 1', 'CASE  1'), self.simple().rstrip('\n'), self.simple() + 'END 1\n'):
            with self.assertRaises(c.Invalid):
                c.inspect(self.put('bad', text), 'DIRECT', {1})

    def test_difference_diagnostic_bounded(self):
        a = self.put('a', ('a' * 1000 + '\n') * 1000)
        b = self.put('b', ('b' * 1000 + '\n') * 1000)
        diff = c.compare(a, b)
        self.assertEqual(diff['differences'], 1000)
        self.assertLessEqual(len(diff['first']), 64)
        self.assertLessEqual(len(str(diff['first']).encode()), 65536)

    def test_script_cli_without_environment_paths(self):
        path = self.root / 'input'
        p = subprocess.run([sys.executable, str(HERE / 'przypadki-ccd.py'), '--profile', 'GUARD', '--side', 'D', '--out', str(path)], capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(path.read_bytes().startswith(b'PORT16 A GUARD 262\n'))


def native_controls(c0, c1):
    ci = load('test_ccd_native_ci', 'ci-ccd.py')
    results = []
    with tempfile.TemporaryDirectory(prefix='native-controls-', dir=Path.cwd()) as tmp:
        data = r.input_bytes('DIRECT', 'C', {17})
        for binary, observed, title in ((c0, True, 'wrong-C1-without-Q'), (c1, False, 'wrong-C0-with-Q')):
            run = ci.execute(binary, data, tmp, title, True)
            ci.success(run)
            try:
                c.inspect(run['stdout'], 'DIRECT', {17}, observed)
            except c.Invalid:
                results.append(title)
            else:
                raise AssertionError('Wrong binary accepted: ' + title)
        data = r.input_bytes('DIRECT', 'C', {1})
        altered = data.replace(b'O 1 300 12 00000000', b'O 1 300 12 00000001', 1)
        run = ci.execute(c1, altered, tmp, 'changed-input', True)
        ci.success(run)
        try:
            c.inspect(run['stdout'], 'DIRECT', {1}, True)
        except c.Invalid:
            results.append('changed-input')
        else:
            raise AssertionError('Wrong input echo accepted')
        original = ci.execute(c1, data, tmp, 'normal-input', True)
        for title, variant in [('CRLF', data.replace(b'\n', b'\r\n')), ('complete-EOF', data.rstrip(b'\n'))]:
            run = ci.execute(c1, variant, tmp, title, True)
            ci.success(run)
            if c.compare(original['stdout'], run['stdout'])['differences']:
                raise AssertionError(title + ' changed valid output')
            results.append(title)
        run = ci.execute(c1, b'\xef\xbb\xbf' + data, tmp, 'BOM', True)
        if run['exit'] != 2 or run['stderr'] != 'PORT16A: INPUT_HEADER\n' or run['stdoutBytes']:
            raise AssertionError('BOM priority/output incorrect')
        results.append('BOM-header-priority')
    return results


if __name__ == '__main__':
    if '--native-controls' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--native-controls', action='store_true')
        parser.add_argument('--c0', required=True)
        parser.add_argument('--c1', required=True)
        args = parser.parse_args()
        print(json.dumps({'detectedOrValidated': native_controls(args.c0, args.c1)}))
    else:
        unittest.main()
