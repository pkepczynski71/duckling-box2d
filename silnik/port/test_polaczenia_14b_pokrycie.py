pass                                                                   
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('coverage14b_under_test', HERE/'klasyfikacja-14b.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class CoverageEvidenceTests(unittest.TestCase):
    def write_counter(self, path, count):
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {'files': [{'file': '/pinned/src/joint.c', 'lines': [
            {'function_name': 'b2CreateJoint', 'line_number': 160, 'count': count,
             'branches': [{'count': count}, {'count': 0}]}]}]}
        with gzip.open(path, 'wt') as f:
            json.dump(data, f)

    def test_zero_branch_is_kept_in_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_counter(root/'CMakeFiles/sen11.dir/joint.c.gcov.json.gz', 3)
            counts, raw = M.counters(root)
            zero = ('src/joint.c', 'b2CreateJoint', 160, 'edge1')
            self.assertIn(zero, counts)
            self.assertEqual(counts[zero], 0)
            self.assertEqual(len(counts), 3)
            self.assertEqual(raw[zero][0]['count'], 0)

    def test_emitted_inline_copies_are_aggregated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_counter(root/'CMakeFiles/first.dir/joint.c.gcov.json.gz', 0)
            self.write_counter(root/'CMakeFiles/second.dir/joint.c.gcov.json.gz', 5)
            counts, raw = M.counters(root)
            key = ('src/joint.c', 'b2CreateJoint', 160, 'line')
            self.assertEqual(counts[key], 5)
            self.assertEqual(len(raw[key]), 2)

    def historical_fixture(self, root, source_content):
        history, source = root/'history', root/'source'
        history.mkdir()
        (source/'src').mkdir(parents=True)
        (source/'src/joint.c').write_text(source_content)
        expected = hashlib.sha256(b'original').hexdigest()
        (history/'original-pins.json').write_text(json.dumps({'pins': {'src/joint.c': expected}}))
        self.write_counter(history/'gcov-new/N14-01/unit/joint.c.gcov.json.gz', 7)
        return history, source

    def test_changed_source_never_gets_historical_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            history, source = self.historical_fixture(Path(tmp), 'changed')
            key = ('src/joint.c', 'b2CreateJoint', 160, 'line')
            old, matching = M.historical(history, {key}, source)
            self.assertEqual(old, {})
            self.assertNotIn('src/joint.c', matching)

    def test_identical_source_requires_a_positive_raw_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            history, source = self.historical_fixture(Path(tmp), 'original')
            line = ('src/joint.c', 'b2CreateJoint', 160, 'line')
            zero = ('src/joint.c', 'b2CreateJoint', 160, 'edge1')
            old, matching = M.historical(history, {line, zero}, source)
            self.assertEqual(old[line]['count'], 7)
            self.assertNotIn(zero, old)
            self.assertIn('src/joint.c', matching)


if __name__ == '__main__':
    unittest.main()
