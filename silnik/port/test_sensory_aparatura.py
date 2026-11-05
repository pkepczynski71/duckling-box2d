pass                                                                      
import gzip
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load('sensory_compare_tests', 'porownaj-sensory.py')
inputs = load('sensory_input_tests', 'przypadki-sensory.py')


class WordComparison(unittest.TestCase):
    def check_pair(self, a, b):
        return compare.compare_streams(io.BytesIO(a), io.BytesIO(b), chunk=8)

    def test_complete_equal_stream(self):
        result = self.check_pair(bytes(range(256))*1000, bytes(range(256))*1000)
        self.assertTrue(result['equal'])
        self.assertEqual(result['words'], [64000, 64000])

    def test_negative_zero_not_normalized(self):
        self.assertFalse(self.check_pair(struct.pack('<I', 0), struct.pack('<I', 0x80000000))['equal'])

    def test_nan_payload_not_normalized(self):
        self.assertFalse(self.check_pair(struct.pack('<I', 0x7fc00001), struct.pack('<I', 0x7fc00002))['equal'])

    def test_changed_word_at_chunk_boundary(self):
        result = self.check_pair(b'a'*16, b'a'*8+b'b'+b'a'*7)
        self.assertFalse(result['equal'])
        self.assertEqual(result['firstDifference']['byte'], 8)

    def test_dropped_word(self):
        self.assertFalse(self.check_pair(b'a'*8+b'b'*4, b'a'*8)['equal'])

    def test_duplicated_word(self):
        self.assertFalse(self.check_pair(b'a'*8, b'a'*12)['equal'])

    def test_empty_side(self):
        self.assertFalse(self.check_pair(b'', b'a'*4)['equal'])

    def test_partial_word_is_not_valid_binary_stream(self):
        self.assertFalse(self.check_pair(b'a', b'a')['wordAligned'])

    def test_continues_after_first_difference(self):
        a, b = io.BytesIO(b'a'*400), io.BytesIO(b'b'*400+b'extra')
        result = compare.compare_streams(a, b, chunk=8)
        self.assertEqual(result['bytes'], [400, 405])
        self.assertEqual(a.tell(), 400)
        self.assertEqual(b.tell(), 405)

    def test_diagnostic_bound(self):
        result = compare.compare_streams(io.BytesIO(b'a'*100000), io.BytesIO(b'b'*100000))
        self.assertLess(len(str(result['firstDifference'])), 1024)

    def test_gzip_compares_words_not_container_bytes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            a, b = root/'a.gz', root/'b.bin'
            a.write_bytes(gzip.compress(b'abcd'*100))
            b.write_bytes(b'abcd'*100)
            self.assertTrue(compare.compare_files(a, b)['equal'])


class FrozenInputs(unittest.TestCase):
    def test_all_historical_c_cases_not_guards(self):
        cases = list(inputs.c18a_cases(inputs.manifest()))
        self.assertEqual(len(cases), 161)
        self.assertEqual([c['id'] for c in cases[:96]], [f'P{i:03}' for i in range(1, 97)])
        self.assertEqual([c['id'] for c in cases[96:160]], [f'D{i:03}' for i in range(1, 65)])
        self.assertEqual(cases[-1]['id'], 'EXTRA_LOCK001')

    def test_parser_bytes_all_pairs_both_sides(self):
        data = inputs.manifest()
        with tempfile.TemporaryDirectory() as name:
            rows = inputs.parser_inputs(data, name)
            self.assertEqual(len(rows), 248)
            self.assertEqual(len({c['errorClass'] for c in data['parserCases']}), 34)
            for case in data['parserCases']:
                for side in ('C', 'D'):
                    for phase in ('negative', 'positive'):
                        path = Path(name)/f'{case['id']}-{side}-{phase}.in'
                        self.assertEqual(path.read_bytes(), case[phase+side].encode('utf-8'))

    def test_unchanged_manifest_counts(self):
        data = inputs.manifest()
        self.assertEqual(len(data['guards']), 697)
        self.assertEqual(sum(c['positiveSteps'] for c in data['public'] if not c['short']), 50400)
        self.assertEqual(sum(c['operationCountExact'] for c in data['public']), 62306)
        self.assertEqual(sum(c['operationCountExact'] for c in data['direct']), 777)

    def test_guard_all_phases_exact_frozen_words(self):
        data = inputs.manifest()
        for side in ('C', 'D'):
            rows = list(inputs.guard_lines(data, side))
            self.assertEqual(rows[0], 'PORT17 GUARD 697\n')
            self.assertEqual(len(rows), 1+697*3)
            for i, case in enumerate(data['guards']):
                self.assertEqual(rows[1+3*i], f'C {i + 1} 0\n')
                for phase, name in enumerate(('negative', 'positive')):
                    row = rows[2+3*i+phase].split()
                    self.assertEqual(row[:5], ['G', str(i+1), str(i+1), str(phase), str(case['routeId'])])
                    self.assertEqual(int(row[5]), len(row)-6)
                    actual = [int(w, 16 if side == 'C' else 10) for w in row[6:]]
                    expected = [int(w, 16) for w in case[name+'ContextH']+case[name+'PayloadH']]
                    self.assertEqual(actual, expected)

    def test_failed_native_setup_writes_red_receipt_and_preserves_independent_inputs(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result = subprocess.run([sys.executable, str(HERE/'ci-sensory.py'),
                                     '--source', str(root/'missing-source'), '--work', str(root/'work'),
                                     '--output', str(root/'results'), '--c18a-only'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            receipt = json.loads((root/'results/manifest.json').read_bytes())
            self.assertFalse(receipt['completePORT17'])
            self.assertEqual(receipt['passed'], 0)
            self.assertEqual(receipt['failed'], ['setup/build'])
            self.assertEqual(len(list((root/'results/parser-inputs').glob('*.in'))), 248)
            self.assertTrue((root/'results/guard-inputs/GUARD-C.in').is_file())


if __name__ == '__main__':
    unittest.main()
