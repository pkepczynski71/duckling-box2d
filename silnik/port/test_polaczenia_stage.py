pass                                                                          
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('test14_ci', HERE / 'ci-polaczenia-oslony.py')
ci = importlib.util.module_from_spec(spec); sys.modules[spec.name] = ci; spec.loader.exec_module(ci)


class StageControls(unittest.TestCase):
    def test_parser_catalogue_has_all31_exact_diagnoses_and_four_routes(self):
        rows = ci.n.catalogue()
        self.assertEqual(len(rows), 31)
        self.assertEqual(len({x['reason'] for x in rows}), 31)
        for x in rows:
            self.assertEqual(x['stderr'], 'PORT14A: ' + x['reason'] + '\n')
            self.assertEqual(x['exit'], 2)
            self.assertEqual({r['variant'] for r in x['variants']}, set(ci.n.VARIANTS))
            self.assertTrue(all(r['state'] == 'unexecuted' for r in x['variants']))

    def test_parser_corpus_bounded_late_prefix_and_no_silent_route_skips(self):
        c, d = ci.n.cases(), ci.n.cases(True)
        self.assertLessEqual(len(c), 256)
        self.assertEqual([r['key'] for r in c], [r['key'] for r in d])
        self.assertTrue(all(r['prefix_operations'] <= 64 for r in c))
        self.assertTrue(any(r['prefix_operations'] > 0 for r in c))
        seen = {(r['variant'], r['reason']) for r in c}
        gaps = {(r['variant'], r['reason']) for r in ci.n.route_gaps()}
        required = {(v, r['reason']) for r in ci.n.catalogue() for v in ci.n.VARIANTS}
        self.assertEqual(seen | gaps, required)
        self.assertFalse(seen & gaps)
        self.assertTrue(gaps)                                            

    def test_no_zero_discovery_and_missing_runtime_cannot_pass(self):
        with tempfile.TemporaryDirectory(prefix='.14a-stage-test-', dir=ROOT) as tmp:
            with patch.object(ci, 'selftest', return_value=[{'file': 'control', 'run': 0, 'ok': False, 'log': ''}]):
                code = ci.stage({'POLACZENIA_OUT': tmp})
            self.assertEqual(code, 1)
            r = json.loads((Path(tmp) / 'manifest.json').read_text(encoding='utf-8'))
            self.assertFalse(r['full_acceptance'])
            self.assertEqual(r['native_product_mutants'], 0)
            self.assertEqual(r['stages']['guards'], {'required': 156, 'passed': 0})
            self.assertGreater(r['stages']['parsers']['required'], 0)
            self.assertFalse(r['full_ownership_ready'])
            self.assertTrue(any('selftests' in s for s in r['errors']))

    def test_native_failure_crash_or_stderr_not_guard_success(self):
        base = {'native_product': True, 'source_sha256': 'f' * 64, 'code': 0, 'build_code': 0, 'stderr': b''}
        self.assertTrue(ci._runtime_ok(base))
        for key, value in (('build_code', 1), ('code', 139), ('stderr', b'bad\n'), ('timeout', True), ('source_sha256', None), ('native_product', False)):
            with self.subTest(key=key):
                self.assertFalse(ci._runtime_ok({**base, key: value}))

    def test_fatal_requires_byte_prefix_and_exact_stderr(self):
        case = next(r for r in ci.n.cases() if r['reason'] == 'INPUT_ASCII')
        with tempfile.TemporaryDirectory(prefix='.14a-fatal-test-', dir=ROOT) as tmp:
            path = Path(tmp) / 'out'; path.write_bytes(b'')
            receipt = {'native_product': True, 'build_code': 0, 'source_sha256': 'f' * 64,
                       'code': 2, 'stderr': b'PORT14A: INPUT_ASCII\n', 'stdout_path': path}
            with self.assertRaisesRegex(ValueError, 'prefix bytes'):
                ci._fatal_observation(receipt, case)
            receipt.update(prefix_bytes_compared=True, prefix_equal=True)
            self.assertTrue(ci._fatal_observation(receipt, case)['ok'])
            for bad in (b'PORT14A: INPUT_ASCII', b'PORT14A: INPUT_ASCII\r\n', b'PORT14A: INPUT_ASCII\nsecond\n'):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    ci._fatal_observation({**receipt, 'stderr': bad}, case)
            path.write_bytes(b'END 1\n')
            with self.assertRaisesRegex(ValueError, 'no END'): ci._fatal_observation(receipt, case)

    def test_guard_helpers_do_not_substitute_incomplete_base_model(self):
        item = ci.d.guards()[0]
        with tempfile.TemporaryDirectory(prefix='.14a-model-test-', dir=ROOT) as tmp:
            path = Path(tmp) / 'out'; path.write_bytes(b'A14 1 1 1 0\n')
            r = {'native_product': True, 'build_code': 0, 'source_sha256': 'f' * 64,
                 'code': 0, 'stderr': b'', 'stdout_path': path}
            with self.assertRaisesRegex(ValueError, 'complete BASE13'):
                ci.check_guard_result(item, r, side='d', observer=True, validate=lambda *a: {'complete': True}, input_bytes=b'')


if __name__ == '__main__': unittest.main()
