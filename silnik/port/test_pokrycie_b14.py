pass                                                                           
import importlib.util
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('coverage14', Path(__file__).with_name('pokrycie-b14.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Coverage(unittest.TestCase):
    def fixture(self, root, profile='PUBLIC', corrupt=False):
        payload=gzip.compress(json.dumps({'gcc_version':'fixture','files':[{
            'file':'/x/box2d-fixture/src/joint.c','functions':[],
            'lines':[{'line_number':101,'function_name':'f','count':1,'branches':[]}]}]}).encode())
        (root/'one.gz').write_bytes(payload)
        digest=hashlib.sha256(payload).hexdigest()
        (root/'index.json').write_text(json.dumps({'entries':[{
            'raw':root.name+'/one.gz','profile':profile,
            'sha256':'0'*64 if corrupt else digest}]}))

    def test_changed_raw_gcov_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root,corrupt=True)
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):
                m.collect(root,('PUBLIC',))

    def test_missing_full_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            with self.assertRaisesRegex(ValueError,'missing full profile'):
                m.collect(root)

    def test_sum_translation_units_and_keep_zero(self):
        rows = {}
        f = {'file':'/x/src/joint.c', 'functions':[], 'lines':[
            {'line_number':101,'function_name':'f','count':2,'branches':[{'count':0},{'count':2}]},
            {'line_number':102,'function_name':'f','count':0,'branches':[]}]}
        m.add_file(rows, f, 'PUBLIC', 'src/joint.c')
        m.add_file(rows, f, 'PUBLIC', 'src/joint.c')
        m.add_file(rows, f, 'DIRECT', 'src/joint.c')
        self.assertEqual(rows[('src/joint.c','f',101,'line')]['hits'], {'PUBLIC':4,'DIRECT':2})
        self.assertEqual(rows[('src/joint.c','f',101,'edge0')]['hits']['PUBLIC'], 0)
        self.assertIn(('src/joint.c','f',102,'line'), rows)
        self.assertEqual(len(rows), 4)

    def test_scope_boundaries_and_omitted_interval(self):
        self.assertTrue(m.in_scope('src/distance_joint.c',198))
        self.assertFalse(m.in_scope('src/distance_joint.c',199))
        self.assertFalse(m.in_scope('src/distance_joint.c',214))
        self.assertTrue(m.in_scope('src/distance_joint.c',215))
        self.assertFalse(m.in_scope('src/revolute_joint.c',20))
        self.assertTrue(m.in_scope('src/joint.h',247))

    def test_headers_are_retained_but_not_automatically_s(self):
        self.assertTrue(m.in_scope('include/box2d/math_functions.h',140))
        row={'hits':{'PUBLIC':0}}
        self.assertEqual(m.default_class(row), 'U')
        self.assertIsNone(m.default_class({'hits':{'PUBLIC':1}}))

    def test_source_paths_are_not_basename_only(self):
        self.assertEqual(m.original_name('/x/box2d-abc/src/joint.c'), 'src/joint.c')
        self.assertEqual(m.original_name('/x/box2d-abc/include/box2d/id.h'), 'include/box2d/id.h')
        self.assertIsNone(m.original_name('/x/silnik/port/joint.c'))
        self.assertIsNone(m.original_name('/usr/include/stdio.h'))


if __name__ == '__main__':
    unittest.main()
