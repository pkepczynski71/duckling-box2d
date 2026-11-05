pass                                                                          

                                                                           
                                                                              
   
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('w2_witness_model', HERE / 'model-polaczenia.py')
m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('w2_witness_negative', HERE / 'polaczenia-ujemne.py')
negative = importlib.util.module_from_spec(spec); sys.modules[spec.name] = negative; spec.loader.exec_module(negative)
DATA = json.loads((HERE / 'polaczenia-w2-swiadki.json').read_text(encoding='utf-8'))['native_witnesses']


def copy_words(rows):
    return {(tag, v[2], v[4] if tag == 'J14' else v[5]): v[7:]
            for tag, v in rows if tag in ('J14', 'L14') and
            (tag == 'J14' and v[5] == 0 and v[2] <= 4 or tag == 'L14' and v[4] == 0 and v[2] in range(1, 5))}


def copy_errors(item, snapshots):
    before = copy_words(snapshots.get(item['before_seq'], ()))
    expected = dict(before)
    key = ('J14', 3, 0)
    if key not in before or ('J14', 4, 0) not in before or ('L14', 3, 1) not in before:
        return ['missing two independently captured A42 own lists']
    value = list(before[key]); value[item['field']] = item['value']; expected[key] = tuple(value)
    errors = []
    for seq in range(item['edit_seq'], item['last_seq'] + 1):
        actual = copy_words(snapshots.get(seq, ()))
        for k in sorted(set(expected) | set(actual)):
            if actual.get(k) != expected.get(k):
                errors.append({'seq': seq, 'record': k, 'expected': expected.get(k), 'actual': actual.get(k)})
                                                                       
    live = [v[7:] for t, v in snapshots.get(17, ()) if t == 'L14' and v[2] == 0 and v[4] == 0]
    if live != [before[('L14', 3, 1)]]:
        errors.append({'seq': 17, 'record': 'live L0', 'expected': [before[('L14', 3, 1)]], 'actual': live})
    return errors


def direct_errors(item, rows):
    expected = tuple(item['expected_J10_after_prepare'])
    states = [v[7:] for t, v in rows if t == 'J14' and v[5] == 10]
    errors = []
    if states != [expected]:
        errors.append({'record': 'J10 A,B', 'expected': expected, 'actual': states})
                                                                              
                                                                            
    for reg in range(2):
        bodies = [v for t, v in rows if t == 'B' and v[2] == reg]
        actual = [v[19:22] for v in bodies]
        wanted = tuple(item['expected_B_velocity'][reg])
        if actual != [wanted]:
            errors.append({'record': 'B velocity reg' + str(reg), 'expected': wanted, 'actual': actual})
    return errors


def native(binary, side, out, keys=None):
    out = Path(out).resolve()
    if not out.is_relative_to(ROOT.resolve()):
        raise ValueError('native output outside assigned tree')
    out.mkdir(parents=True, exist_ok=True)
    results = []
    selected = [r for r in DATA if not keys or r['key'] in keys]
    reference = None
    if any(r['kind'] == 'fatal' for r in selected):
        item = next(r for r in DATA if r['key'] == 'solver-reference-prepare')
        reference_input = item['input_d' if side == 'd' else 'input_c'].encode('ascii')
        reference = subprocess.run([str(binary)],input=reference_input,capture_output=True,timeout=60)
        if reference.returncode or reference.stderr:
            raise ValueError('paired legal native reference failed before fatal prefix comparison')
    for item in selected:
        data = item['input_d' if side == 'd' else 'input_c'].encode('ascii')
        path = out / (item['key'] + '.stdout.tmp')
        started = time.monotonic()
        with path.open('wb') as stream:
            run = subprocess.run([str(binary)], input=data, stdout=stream, stderr=subprocess.PIPE, timeout=60)
        sha = hashlib.sha256(); snapshots = {}; echoes = []; errors = []; end = False; rows = 0
        with path.open('rb') as stream:
            for line in stream:
                sha.update(line); rows += 1
                tag, v = m.parse(line)
                if tag == 'END': end = True
                if tag == 'E14': echoes.append((v[0], v[1], v[2]))
                if len(v) >= 2 and v[0] == item['id'] and tag in ('A14', 'B', 'J14', 'L14'):
                    snapshots.setdefault(v[1], []).append((tag, v))
        prefix = {}
        if item['kind'] == 'fatal':
            if run.returncode != 2 or run.stderr != item['expected_stderr'].encode('ascii'):
                errors.append('exact fatal exit/stderr mismatch')
            if len(echoes) != 64 or any(i == 65 for i, seq, code in echoes) or end:
                errors.append('bad operation emitted or legal64-prefix missing or END emitted')
            try:
                with path.open('rb') as actual:
                    prefix = negative.compare_prefix(actual,io.BytesIO(reference.stdout),
                        {'failure_scope':'operation','prefix_operations':64,'variant':'DIRECT-solver'})
                prefix.update(reference_argv=[str(binary)],reference_exit=reference.returncode,
                              reference_stderr=reference.stderr.decode('ascii'),
                              reference_outputSHA256=hashlib.sha256(reference.stdout).hexdigest())
            except ValueError as exc: errors.append('paired native prefix: '+str(exc))
        else:
            if run.returncode or run.stderr or not end: errors.append('native process/stderr/END')
            if item['kind'] == 'copy': errors += copy_errors(item, snapshots)
            if item['kind'] == 'direct': errors += direct_errors(item, snapshots.get(1, ()))
        receipt = {'key': item['key'], 'side': side, 'argv': [str(binary)],
                   'native_product': True, 'scope': 'isolated witness; not full BASE13 or14a acceptance',
                   'binarySHA256': hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
                   'inputSHA256': hashlib.sha256(data).hexdigest(), 'outputSHA256': sha.hexdigest(),
                   'sourceSHA256': {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in
                       ('silnik/port/kontrola-polaczenia.c', 'silnik/port/polaczenia.dk')},
                   'exit': run.returncode, 'stderr': run.stderr.decode('ascii', errors='backslashreplace'),
                   'seconds': time.monotonic()-started, 'stdoutBytes': path.stat().st_size, 'rows': rows,
                   'echoes': len(echoes), 'errors': errors, 'ok': not errors,
                   'exact_prefix': prefix,
                   'selectedSnapshots': {str(seq): records for seq, records in snapshots.items()
                                         if item['kind'] != 'copy' or 13 <= seq <= 17}}
        path.unlink()
        (out/(item['key']+'.json')).write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
        results.append(receipt)
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'side': side, 'total': len(results), 'passed': sum(r['ok'] for r in results),
                      'red': [r['key'] for r in results if not r['ok']]}))
    return int(any(not r['ok'] for r in results))


class PortableWitnessControls(unittest.TestCase):
    def test_copy_oracle_rejects_raw_alias_and_accepts_only_indicated_word(self):
        item = next(r for r in DATA if r['key'] == 'A42-copy-field0')
        def j(source, words): return 'J14', (42, 13, source, 16, 0, 0, 8, *words)
        def l(source, words): return 'L14', (42, 13, source, 16, 0, 1, len(words), *words)
        number = (1, 0, 1, 0, 4, 0, 1, 0)
        before = [j(0, number), j(3, number), l(3, number[:3]), j(4, number), l(4, number[:3])]
        after = [j(0, number), j(3, (17, *number[1:])), l(3, number[:3]), j(4, number), l(4, number[:3])]
        rows = {13: before, **{seq: copy.deepcopy(after) for seq in range(14, 18)}}
        rows[17].append(('L14', (42, 17, 0, 0, 0, 1, 3, *number[:3])))
        self.assertEqual(copy_errors(item, rows), [])
        rows[14][2] = l(3, (17, 0, 1))
        self.assertTrue(copy_errors(item, rows))

    def test_raw_and_Number_are_distinct_separate_witnesses(self):
        cases = [r for r in DATA if r['kind'] == 'copy']
        self.assertEqual([r['field'] for r in cases], [0, 3])
        for r in cases:
            last = [line for line in r['input_c'].splitlines() if line.startswith('O 14 209')][-1]
            self.assertEqual(last, f'O 14 209 4 00000002 00000000 {r['field']:08x} 00000011')

    def test_PROFILE_and_register_priority_are_independent_inputs(self):
        rows = {r['key']: r for r in DATA}
        profile = rows['solver-default-profile']; registers = rows['solver-create-uninitialized']
        self.assertEqual(profile['expected_stderr'], 'PORT14A: INPUT_PROFILE\n')
        self.assertEqual(registers['expected_stderr'], 'PORT14A: INPUT_REGISTER_UNINITIALIZED\n')
        self.assertEqual(profile['input_c'].splitlines()[:-1], registers['input_c'].splitlines()[:-1])
        self.assertEqual(profile['input_c'].splitlines()[-1], 'O 1 200 2 00000000 00000000')
        self.assertEqual(profile['prefix_operations'], 64)

    def test_DIRECT_orientations_have_A_then_B_and_static_dummy(self):
        for item in (r for r in DATA if r['kind'] == 'direct'):
            states = item['expected_J10_after_prepare']
            for lane, state in enumerate(item['orientation']):
                if state == 0: self.assertEqual(states[8*lane:8*lane+8], [0,0,0,0,0,0,0x3f800000,0])
            self.assertEqual(direct_errors(item, [('J14', (65,1,0,0,0,10,16,*states)),
                *[('B',(65,1,reg,*([0]*16),*item['expected_B_velocity'][reg],*([0]*11))) for reg in range(2)]]), [])


if __name__ == '__main__':
    if '--native' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--native', required=True, type=Path)
        parser.add_argument('--side', required=True, choices=('c0','c1','d'))
        parser.add_argument('--out', required=True, type=Path)
        parser.add_argument('--key', action='append')
        args = parser.parse_args()
        sys.exit(native(args.native, args.side, args.out, args.key))
    unittest.main()
