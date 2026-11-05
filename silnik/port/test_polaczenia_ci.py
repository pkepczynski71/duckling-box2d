pass                                                                         
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('test14_ci',HERE/'ci-polaczenia.py')
ci=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ci;spec.loader.exec_module(ci)


@contextmanager
def work():
    with tempfile.TemporaryDirectory(prefix='.selftest-polaczenia-',dir=ROOT) as directory:
        yield Path(directory)


class CI14(unittest.TestCase):
    def test_missing_or_partial_n5_cannot_start_campaign(self):
        with self.assertRaisesRegex(ValueError,'not approved'):ci.approved_limits(None,'sha')
        with work() as out:
            p=out/'approval.json';p.write_text(json.dumps({'limits_profile':'LIMITS1','sourceSHA256':'sha','seconds':{'PUBLIC':1}}))
            with self.assertRaisesRegex(ValueError,'incomplete'):ci.approved_limits(p,'sha')

    def test_n5_requires_full_pilot_identity_and_twofold_forecast(self):
        with work() as out:
            p=out/'approval.json'
            receipt={'limits_profile':'LIMITS1','sourceSHA256':'sha','seconds':{k:10 for k in ('PUBLIC','DIRECT','GUARD','parsers','mutations','builds')},
                     'pilot_complete':True,'twofold_extrapolation_fits':True}
            p.write_text(json.dumps(receipt));self.assertEqual(ci.approved_limits(p,'sha'),receipt)
            with self.assertRaisesRegex(ValueError,'identity'):ci.approved_limits(p,'other')
            receipt['twofold_extrapolation_fits']=False;p.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,'forecast'):ci.approved_limits(p,'sha')

    def test_independent_stage_runs_after_red_and_preserves_red(self):
        with work() as out:
            self.assertEqual(ci.stage(out=out,phase='PUBLIC'),1)
            with patch.object(ci,'selftest',return_value=[{'code':0,'file':'controlled'}]):
                self.assertEqual(ci.stage(out=out,phase='tools'),0)
            r=json.loads((out/'manifest.json').read_text())
            self.assertEqual(r['stages']['PUBLIC']['code'],1);self.assertEqual(r['stages']['tools']['code'],0)
            self.assertFalse(r['full_acceptance']);self.assertEqual(ci.stage(out=out,phase='summary'),1)
            self.assertTrue((out/'PODSUMOWANIE.md').is_file())

    def test_router_runs_only_requested_14a_phase_before_old_campaign(self):
        with work() as out:
            env={**os.environ,'POLACZENIA_RESULT_DIR':str(out),'PYTHONDONTWRITEBYTECODE':'1'}
            env.pop('POLACZENIA_N5_RECEIPT',None)
            run=subprocess.run([sys.executable,'-B',str(HERE/'ci.py'),'polaczenia-14a-N5'],env=env,capture_output=True,timeout=20)
            self.assertEqual(run.returncode,1,run.stderr)
            r=json.loads((out/'manifest.json').read_text())
            self.assertEqual(set(r['stages']),{'N5'})
            self.assertIn('dependency red',r['stages']['N5']['reason'])
            self.assertFalse((out/'start-unix.csv').exists())

    def test_unknown_phase_and_external_evidence_path_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown'):ci.stage(phase='lancuchy')
        with self.assertRaisesRegex(ValueError,'outside'):ci.within(ROOT.parent/'outside14a')

    def test_explicit_profile_reaches_comparator_and_overrides_environment(self):
        with work() as out:
            receipt={'stages':{'build_C0_C1':{'code':0,'result':{'binaries':{'obs0':{'binary':'c0'},'obs1':{'binary':'c1'}}}},
                               'build_D':{'code':0,'result':{'binary':'d'}},'N5':{'code':0,'result':{'seconds':{'DIRECT':10}}}},
                     'openRequirements':['not final integration'],'startUnix':ci.time.time()}
            ci.save(out/'manifest.json',receipt)
            with patch.dict(os.environ,{'POLACZENIA_PROFILE':'PUBLIC'}),patch.object(ci,'native_compare',return_value={'full_acceptance':False}) as compare:
                self.assertEqual(ci.stage(out=out,phase='DIRECT',profile='DIRECT',part='A'),1)
            args,kwargs=compare.call_args
            self.assertEqual(len(args[1]),128);self.assertEqual({x.profile for x in args[1]},{'DIRECT'})
            self.assertEqual(args[2],{'c0':'c0','c1':'c1','d':'d'});self.assertEqual(kwargs['seconds'],10)
            self.assertEqual(json.loads((out/'manifest.json').read_text())['selection']['profile'],'DIRECT')
        with self.assertRaisesRegex(ValueError,'part/profile'):ci.stage(part='B')

    def test_zero_discovered_tests_cannot_pass_tools_stage(self):
        def empty_run(argv,**kwargs):
            kwargs['stderr'].write(b'Ran 0 tests in 0.000s\n\nOK\n');return subprocess.CompletedProcess(argv,0)
        with work() as out,patch.object(ci.subprocess,'run',side_effect=empty_run):
            with self.assertRaisesRegex(ValueError,'selftest failed'):ci.selftest(out)

    def test_sources_pinned_and_missing_stage_never_green(self):
        from public_ci import check
        check(self)


if __name__=='__main__':unittest.main()
