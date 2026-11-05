pass                                                                   
from contextlib import contextmanager,redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_pary import HERE,g,module,p
from test_pary_porownanie import fixture,mutate

@contextmanager
def work():
    with tempfile.TemporaryDirectory(prefix='_pair-ci-test-',dir=HERE) as name:
        path=Path(name).resolve();assert path.is_relative_to(HERE.resolve());yield path

class Integration(unittest.TestCase):
    def test_CI_discovers_all_modules_and_pins_exact_counts(self):
        ci=module('pair_ci_pin','ci-pary.py');text=(HERE/'ci-pary.py').read_text(encoding='utf-8')
        self.assertIn("'test_pary*.py'",text);self.assertEqual(ci.RECIPE_COUNT,48);self.assertEqual(ci.NEGATIVE_COUNT,46)
        self.assertEqual(len(json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']),48)
        negative=module('pair_ci_negative_pin','ujemne-pary.py');self.assertEqual(len(negative.variants()),46)
    def test_new_job_restores_original_sources_toolchain_and_hashes(self):
        from public_ci import check
        check(self)
    def test_runner_budget_and_original_build_policy_are_unchanged(self):
        text=(HERE/'ci-pary.py').read_text(encoding='utf-8')
        self.assertIn("sys.argv[1]='pary9a'",text);self.assertNotIn('subprocess.run(',text)
        self.assertIn('libbox2dd.a',text);self.assertIn('if len(files)!=63',text)
        self.assertNotIn('curl',text);self.assertNotIn('base.build(',text)
        self.assertIn('remaining = 660 -',(HERE.parents[1]/'silnik/proba/ci.py').read_text(encoding='utf-8'))
    def test_C_reference_calls_all_seven_exports_without_copied_manifold_code(self):
        text=(HERE/'kontrola-pary.c').read_text(encoding='utf-8')
        names=('CapsuleAndCircle','PolygonAndCircle','Capsules','SegmentAndCircle','SegmentAndCapsule','PolygonAndCapsule','SegmentAndPolygon')
        for suffix in names:self.assertEqual(text.count('return b2Collide'+suffix+'('),1,suffix)
        self.assertNotIn('#include "',text);self.assertNotIn('static b2Polygon b2MakeCapsule',text)
        self.assertIn('vec(p->anchorB)',text);self.assertIn('word(p->persisted)',text)
    def test_source_restore_rejects_missing_files_before_building(self):
        ci=module('pair_restore_test','ci-pary.py')
        with work() as directory:
            ci.OUT=directory;ci.C=SimpleNamespace(base=SimpleNamespace(TEMP=directory,StepFailed=RuntimeError))
            (directory/'box2d/src').mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError,'63 C/H'):ci.source_sums()
    def test_summary_requires_prior_success_and_every_new_outcome(self):
        ci=module('pair_summary_test','ci-pary.py')
        with work() as directory:
            ci.OUT=directory/'krok9a';ci.OUT.mkdir();prior=directory/'krok8';prior.mkdir();(prior/'wynik-kod.csv').write_text('0\n')
            outcomes={name.replace('-','_').upper()+'_OUTCOME':'success' for name in ci.STAGES};outcomes['REGRESJE_OUTCOME']='success'
            with patch.object(ci,'code',return_value=0),patch.object(ci,'evidence',return_value=True),patch.dict(os.environ,outcomes,clear=True),redirect_stdout(io.StringIO()):
                self.assertEqual(ci.summary(),0)
                with patch.dict(os.environ,{'CHECK_PARY_OUTCOME':'failure'}):self.assertEqual(ci.summary(),1)
                with patch.dict(os.environ,{'REGRESJE_OUTCOME':'failure'}):self.assertEqual(ci.summary(),1)
                (prior/'wynik-kod.csv').write_text('1\n');self.assertEqual(ci.summary(),1)
            with patch.object(ci,'code',return_value=0),patch.object(ci,'evidence',return_value=False),patch.dict(os.environ,outcomes,clear=True),redirect_stdout(io.StringIO()):
                self.assertEqual(ci.summary(),1)
    def test_exact_output_byte_forecast_does_not_need_numerical_results(self):
        rows,text=fixture(g.cases())
        forecast=len(p.format_record('PORT9A',(448,)))+len(p.format_record('END',(448,)))
        for c in rows:forecast+=len(p.format_record('E',p.echo(c)))+len(p.format_record('M',(c.id,*([0]*30))))+len(p.format_record('ENDCASE',(c.id,)))
        self.assertEqual(forecast,len(text.encode('ascii')));self.assertLess(forecast,448*2048)

class NativeEvidence(unittest.TestCase):
    def setUp(self):
        self.ci=module('pair_detection_test','ci-pary.py');self.ci.p=p;self.rows,self.original=fixture()
        self.ci.negative=module('pair_detection_negative','ujemne-pary.py')
        self.recipe={'probe':'physics','witness_ids':[1],'fields':['normal.x']}
    def detect(self,code,text,stderr=b''):
        with work() as directory:
            original=directory/'original.csv';out=directory/'out.csv';err=directory/'err.csv'
            original.write_bytes(self.original.encode('ascii'));out.write_bytes(text.encode('ascii'));err.write_bytes(stderr)
            return self.ci.detection(self.recipe,code,out,err,original,self.rows)
    def test_only_clean_prescribed_field_difference_is_detected(self):
        bad=mutate(self.original,'M',1,0x80000000);detected,detail=self.detect(0,bad)
        self.assertTrue(detected);self.assertEqual(detail['field'],'normal.x');self.assertEqual(detail['id'],1)
        self.assertFalse(self.detect(0,self.original)[0])
        self.assertFalse(self.detect(0,mutate(self.original,'M',2,1))[0])
        self.assertFalse(self.detect(0,bad,b'unexpected\n')[0])
    def test_crash_timeout_build_error_truncation_and_NaN_never_count(self):
        bad=mutate(self.original,'M',1,0x80000000)
        for code in (-6,1,3,4,124,125,126,127):self.assertFalse(self.detect(code,bad)[0])
        self.assertFalse(self.detect(0,bad[:-8])[0]);self.assertFalse(self.detect(0,mutate(self.original,'M',1,0x7fc00001))[0])
    def test_parser_mutant_must_finish_with_finite_complete_output(self):
        self.recipe={'probe':'negative','variant':'N-zero'}
        accepted='PORT9A 0\nEND 0\n';self.assertTrue(self.detect(0,accepted)[0])
        self.assertFalse(self.detect(3,accepted)[0]);self.assertFalse(self.detect(0,accepted+'garbage\n')[0])
        self.assertFalse(self.detect(0,'PORT9A 1\nEND 1\n')[0])
        self.assertFalse(self.detect(0,mutate(self.original,'M',1,0x7f800000))[0])

class Storage(unittest.TestCase):
    def test_explicit_output_list_keeps_inputs_with_the_same_PORT9A_header(self):
        ci=module('pair_storage_test','ci-pary.py');storage=module('pair_storage_manifest8','zapis-strumieni.py');rows,text=fixture()
        with work() as directory:
            out=directory/'output.csv';data=text.encode('ascii');out.write_bytes(data)
            inputs=directory/'przypadki-pary.csv';inputs.write_bytes(g.encode(rows).encode('ascii'))
            folder=directory/'wejscia-pary';folder.mkdir();(folder/'same-name.csv').write_bytes(g.encode(rows,True).encode('ascii'))
            (directory/'pary-lista-strumieni.json').write_text('["output.csv"]')
            self.assertEqual(ci.compact_outputs(directory,storage.manifest),0)
            self.assertFalse(out.exists());self.assertTrue(inputs.exists());self.assertTrue((folder/'same-name.csv').exists())
            record=json.loads((directory/'STRUMIENIE-PARY-MANIFEST.json').read_bytes())['output.csv']
            self.assertEqual(record['bytes'],len(data));self.assertEqual(record['sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(record['records']['M'],1)
    def test_output_path_cannot_escape_the_directory(self):
        ci=module('pair_storage_path_test','ci-pary.py');storage=module('pair_storage_path_manifest8','zapis-strumieni.py')
        with work() as directory:
            (directory/'pary-lista-strumieni.json').write_text('["../other.csv"]')
            with self.assertRaisesRegex(ValueError,'escaped'):ci.compact_outputs(directory,storage.manifest)

class NativeC(unittest.TestCase):
    def test_original_exported_KC_matches_the_hand_equality_ledger(self):
        binary=os.environ.get('PARY_C_BIN')
        if not binary:
            if os.environ.get('PARY_REQUIRE_PRODUCT')=='1':self.fail('CI did not supply compiled C reference')
            self.skipTest('no local C compiler; CI supplies the full original library')
        rows,text=fixture()
        with work() as directory:
            path=directory/'input.csv';path.write_bytes(g.encode(rows).encode('ascii'))
            result=subprocess.run([binary,path],capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0);self.assertEqual(result.stderr,b'')
            actual=p.validate_output(io.StringIO(result.stdout.decode('ascii')),rows)['manifolds']
            expected=p.validate_output(io.StringIO(text),rows)['manifolds'];self.assertEqual(actual,expected)

if __name__=='__main__':unittest.main()
