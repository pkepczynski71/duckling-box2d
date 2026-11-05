from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                            
from collections import Counter
from contextlib import contextmanager
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import hashlib

HERE=Path(__file__).resolve().parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

p=module('solver_tests_compare','porownaj-solver.py');g=p.g
build=module('solver_tests_builder','budowa-solver.py')
storage=module('solver_tests_storage','zapis-solver.py')
ci=module('solver_tests_ci','ci-solver.py')

@contextmanager
def work():
    root=HERE.parents[1]/'_solver-tests';root.mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=root) as name:yield Path(name)
    finally:
        if root.exists() and not any(root.iterdir()):root.rmdir()

def empty_snapshot():
    from test_kontakty import empty_world_fixture
    cases,records=empty_world_fixture();c=cases[0]
    records=[(t,v) for t,v in records if t not in ('PORT9B','CASE','ENDCASE','END','I8','I9','Z8','Z9')]
    records += [('W10',(1,1,0,*map(g.bits,(30,10,3,1,1,0)),1,1)),('HN10',(1,1,0,0))]
    counts=Counter(t for t,v in records)
    records += [('I8',(1,1,*[counts[t] for t in 'X P T F U H Y DN RT JW'.split()])),
                ('I9',(1,1,*[counts[t] for t in p.p9.PRIVCOUNTS],0,1)),
                ('I10',(1,1,*[counts[t] for t in p.NEW_COUNTS])),
                ('Z8',(1,1,1,0,0,1,0,0,*[counts[t] for t in p.p9.p8.PUBLIC_COUNTS],1,0)),
                ('Z9',(1,1,0,0,0,*[counts[t] for t in p.p9.PUBCOUNTS],1,1,3,0,1,0)),
                ('Z10',(1,1,1,0,0,0,0))]
    records=sorted(records,key=lambda r:p.RANK[r[0]])
    records=[('PORT10',(1,)),('CASE',(1,1)),*records,('ENDCASE',(1,)),('END',(1,))]
    return (c,),records

class Corpus(unittest.TestCase):
    def test_all_frozen_steps_configs_and_no_internal_public_control(self):
        rows=g.verify();manifest=g.MANIFEST['przypadki']
        self.assertEqual([c.id for c in rows],list(range(1,125)))
        self.assertEqual(sum(m['kroki'] for m in manifest[:108]),86400)
        self.assertEqual(sum(m['kroki'] for m in manifest[108:]),56)
        for family in range(1,19):
            self.assertEqual({(m['podkroki'],m['warm']) for m in manifest if m['rodzina']==family and m['id']<=108},
                             {(n,w) for n in (1,4,8) for w in (0,1)})
        self.assertFalse(any(row[0] in (*range(41,46),51,52,53) for c in rows for row in c.ops))
    def test_C_and_D_encodings_preserve_all64_words(self):
        rows=g.cases()[:1]
        c=g.encode(rows).splitlines();d=g.encode(rows,True).splitlines()
        self.assertEqual(c[:2],d[:2])
        for a,b in zip(c[2:],d[2:]):
            aa=a.split();bb=b.split();self.assertEqual(aa[:3],bb[:3]);self.assertEqual(len(aa),67)
            self.assertEqual([int(v,16) for v in aa[3:]],[int(v) for v in bb[3:]])
    def test_component_seeds_do_not_supply_solver_outputs(self):
        rows=g.components();self.assertEqual(len(rows),96);self.assertEqual(sum(len(c.phases) for c in rows),2368)
        self.assertEqual(len({(c.fixture,c.substeps,c.warm) for c in rows}),96)
        for c in rows:
            text=g.encode_components((c,));self.assertNotIn('SC10',text);self.assertNotIn('BV10',text)
            self.assertTrue(all(len(v)==17 for v in c.bodies));self.assertTrue(all(len(v)==51 for color,local,v in c.contacts))
            if c.fixture==16:self.assertEqual(len(c.helpers),30)
    def test_natural_overflow_and_large_block_scene_are_not_forced(self):
        rows=g.cases()
        star=rows[78].ops;large=rows[96].ops
        self.assertEqual(sum(r[0]==30 for r in star),14)
        self.assertEqual(sum(r[0]==30 for r in large),70)
        self.assertTrue(all(r[0] not in (41,42,43,44,45,51,52,53) for r in (*star,*large)))
    def test_input_pin_failure_cannot_overwrite_the_pin_or_publish_new_inputs(self):
        with work() as directory:
            pin=directory/'wejscia-solver-sha256.json';pin.write_text('{"wrong":"pin"}\n')
            before=pin.read_bytes();out=directory/'out'
            with mock.patch.object(g,'HERE',directory),mock.patch.object(g,'verify',return_value=g.cases()[:1]):
                with self.assertRaisesRegex(ValueError,'input hashes changed'):g.write(out)
            self.assertEqual(pin.read_bytes(),before);self.assertFalse(list(out.iterdir()))
    def test_short_contact_scenes_do_not_start_above_the_ground(self):
        for c in g.cases()[108:113]:
            bs=[r for r in c.ops if r[0]==30];ss=[r for r in c.ops if r[0]==40]
            top=g.number(bs[0][5])+g.number(ss[0][6])
            for b,s in zip(bs[1:],ss[1:]):
                bottom=g.number(b[5])-g.number(s[6])
                self.assertLessEqual(bottom,top,(c.id,b[1]))
    def test_hit_flag_off_pair_and_mixed_packet_are_explicit_inputs(self):
        shapes=[r for r in g.cases()[114].ops if r[0]==40]
        self.assertEqual([r[58] for r in shapes],[0,1,0])
        packet=[r[4] for r in g.cases()[72].ops if r[0]==40][1:]
        self.assertEqual(set(packet),{0,4})

class Protocol(unittest.TestCase):
    def test_frozen_new_output_examples_roundtrip(self):
        text=norm_text(HERE/'fixtures/norms/KONTRAKT-10.json');inside=False;count=0
        for line in text.splitlines():
            if line.startswith('```'):inside=line=='```text';continue
            if inside and line.split(' ',1)[0] in p.SCHEMA:
                tag,v=p.parse_record(line+'\n',True);self.assertEqual(p.format_record(tag,v,True),line+'\n');count+=1
        self.assertGreaterEqual(count,37)
    def test_complete_snapshot_and_exact_public_projection(self):
        cases,records=empty_snapshot();text=''.join(p.format_record(t,v) for t,v in records)
        self.assertEqual(p.validate_output(text,cases)['Z10'],1)
        public=''.join(p.projection(text.splitlines(keepends=True)))
        self.assertEqual(p.validate_output(public,cases,False)['Z10'],1)
        self.assertIn('HN10',public);self.assertIn('Z10',public);self.assertNotIn('W10',public)
        self.assertIsNone(p.first_difference(io.StringIO(text),io.StringIO(public),True))
    def test_identically_missing_group_or_changed_counter_fails_before_equality(self):
        cases,records=empty_snapshot()
        for removed in ('W10','HN10','I10','Z10','ENDCASE','END'):
            text=''.join(p.format_record(t,v) for t,v in records if t!=removed)
            with self.subTest(removed=removed),self.assertRaises(ValueError):p.validate_output(text,cases)
        for tag,index in (('I10',2),('Z10',2),('Z9',14)):
            changed=[]
            for t,v in records:
                if t==tag:v=list(v);v[index]^=1
                changed.append(p.format_record(t,v))
            with self.subTest(tag=tag),self.assertRaises(ValueError):p.validate_output(''.join(changed),cases)
    def test_first_difference_names_SC_field_and_both_words(self):
        a=(1,2,0,0,7,11,0,0,0x3fffffff,0,*([0]*41));b=list(a);b[35]=1
        diff=p.first_difference([p.format_record('SC10',a)],[p.format_record('SC10',b)])
        self.assertEqual(diff['field'],'point0.normalImpulse');self.assertEqual(diff['C'],'00000000');self.assertEqual(diff['Duckling'],'00000001')
    def test_SC_undefined_point_is_not_read_or_masked_into_a_fake_defined_value(self):
        rows={'W':[],'W10':[],'SC10':[(117,1,0,0,7,11,0,0,0x3fffffff,0,0,0,0,1,*([0]*37))],
              'PK10':[],'CX10':[(117,1,0,0,0,0,0,1,*([0]*8),1)],'BV10':[],'SB10':[]}
                                                                                         
        bad=list(rows['SC10'][0]);bad[-1]=1;rows['SC10']=[tuple(bad)]
        with self.assertRaisesRegex(ValueError,'undefined field'):p.check_trace(rows,True,117)

class MethodA(unittest.TestCase):
    def test_adapter_specialization_does_not_edit_original_or_legacy_files(self):
        before={name:(HERE/name).read_bytes() for name in ('kontrola-kontakty.c','kontrola-kontakty9.h')}
        with work() as directory:
            sums=build.adapter(HERE,directory);self.assertEqual(len(sums),3)
            source=(directory/'solver-base10.inc').read_text(encoding='utf-8')
            header=(directory/'solver-contact9.inc').read_text(encoding='utf-8')
            self.assertIn('events[256]',source);self.assertIn('bound10(2)',header)
            self.assertNotIn('if(e.hitCount)fail',header)
        self.assertEqual(before,{name:(HERE/name).read_bytes() for name in before})
    def test_original_four_translation_units_are_each_included_once(self):
        for wrapper,original in build.WRAPPERS.items():
            text=(HERE/original).read_text(encoding='utf-8')
            self.assertEqual(text.count('#include "'+wrapper+'"'),1)
        for wrapper in ('world.c','solver.c','contact_solver.c','broad_phase.c'):
            self.assertNotIn('#include "'+wrapper+'"',(HERE/'kontrola-solver.c').read_text(encoding='utf-8'))
    def test_failed_comparison_payload_filter_keeps_diagnostics_and_inputs(self):
        with work() as directory:
            raw=directory/'unexpected-output.csv';raw.write_bytes(b'PORT10 1\nCASE 1 1\npartial\n')
            source=directory/'proba-solver.csv';source.write_bytes(b'PORT10 1\nC 1 1\n')
            stderr=directory/'sample-obs1-stderr.csv';stderr.write_bytes(b'failure\n')
            removed=storage.prepare_publication(directory)
            self.assertIn(raw.name,removed);self.assertFalse(raw.exists());self.assertTrue(source.exists())
            self.assertEqual(stderr.read_bytes(),b'failure\n');self.assertFalse(removed[raw.name]['validated'])
    def test_guard_and_component_payload_are_filtered_after_other_half_failure(self):
        with work() as directory:
            for name,data in (('guard-extra.csv',b'GUARD10 1\nG 1 0 0 0\n'),
                              ('component-extra.csv',b'COMPONENT10 1\nF 1 1 1 0 0 0 0 8\n')):
                (directory/name).write_bytes(data)
                (directory/(Path(name).stem+'-kod.csv')).write_bytes(b'1\n')
            removed=storage.prepare_publication(directory)
            self.assertEqual(set(removed),{'guard-extra.csv','component-extra.csv'})
            self.assertTrue((directory/'guard-extra-kod.csv').is_file())

class StreamingStorage(unittest.TestCase):
    def run_streams(self,directory,mutate=None,models=True):
        cases,records=empty_snapshot();text=''.join(p.format_record(t,v) for t,v in records)
        streams={'obs1':text,'duckling':text,'obs0':''.join(p.projection(text.splitlines(keepends=True)))}
        if mutate is not None:streams=mutate(streams)
        def run(name,command,**kwargs):
            (directory/(name+'-stderr.csv')).write_bytes(b'');return 0
        context=SimpleNamespace(OUT=directory,base=SimpleNamespace(TEMP=directory/'temp',run=mock.Mock(side_effect=run)))
        checks={label:SimpleNamespace(check=mock.Mock()) for label in ('C OBS1','Duckling','C OBS0')} if models else None
        def pipe(path):
            name=next(k for k in streams if path.name.endswith('-'+k+'.fifo'))
            path.write_bytes(streams[name].encode('ascii'))
        with mock.patch.object(storage.os,'mkfifo',side_effect=pipe,create=True):
            receipt=storage.case_streams(context,p,cases,{side:['native-'+side] for side in streams},models=checks)
        return receipt,streams,checks
    def test_actual_global_stream_hashes_and_no_raw_case_after_three_model_checks(self):
        with work() as directory:
            receipt,streams,models=self.run_streams(directory)
            self.assertTrue(receipt['global_END_checked']);self.assertFalse(list(directory.glob('*.raw.csv')))
            for name,text in streams.items():
                self.assertEqual(receipt['original_streams'][name]['sha256'],hashlib.sha256(text.encode()).hexdigest())
                self.assertEqual(receipt['original_streams'][name]['bytes'],len(text.encode()))
            for model in models.values():self.assertEqual(model.check.call_count,1)
    def test_independent_model_is_required_before_case_deletion(self):
        with work() as directory:
            with self.assertRaisesRegex(ValueError,'model required'):self.run_streams(directory,models=False)
            self.assertEqual(len(list(directory.glob('*.raw.csv'))),3)
            receipt=json.loads((directory/'public10-manifest.json').read_bytes())
            self.assertFalse(receipt['global_END_checked'])
            self.assertFalse(receipt['cases'][0]['models_checked'])
    def test_equal_corruption_cannot_be_compacted_or_reported_complete(self):
        def damage(streams):return {k:v.replace('Z10 1 1 00000001','Z10 1 1 00000002') for k,v in streams.items()}
        with work() as directory:
            with self.assertRaisesRegex(ValueError,'comparison failed'):self.run_streams(directory,damage)
            self.assertEqual(len(list(directory.glob('*.raw.csv'))),3)
            receipt=json.loads((directory/'public10-manifest.json').read_bytes());self.assertFalse(receipt['global_END_checked'])
            self.assertTrue(receipt['cases'][0]['errors'])
    def test_global_END_is_checked_even_after_case_receipts(self):
        def damage(streams):return {k:v.removesuffix('END 1\n') for k,v in streams.items()}
        with work() as directory:
            with self.assertRaisesRegex(ValueError,'global END'):self.run_streams(directory,damage)
            receipt=json.loads((directory/'public10-manifest.json').read_bytes())
            self.assertFalse(receipt['global_END_checked']);self.assertFalse(receipt['original_streams']['obs1']['complete'])

class Gates(unittest.TestCase):
    def test_failed_tests_guard_or_prior_regression_never_publish_a_green_summary(self):
        env={name.replace('-','_').upper()+'_OUTCOME':'success' for name in ci.STAGES}
        env.update(OSLONY_OUTCOME='success',REGRESJE_OUTCOME='success',TESTY_OUTCOME='success')
        with work() as directory:
            (directory/'OSLONY.md').write_text('RESULT OK\n',encoding='utf-8')
            with mock.patch.multiple(ci,OUT=directory,code=lambda name:0,check=lambda:0,create=True),mock.patch.dict(ci.os.environ,env),mock.patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(ci.summary(),0)
                for key in ('OSLONY_OUTCOME','REGRESJE_OUTCOME','TESTY_OUTCOME','COMPONENT_SOLVER_OUTCOME'):
                    with mock.patch.dict(ci.os.environ,{key:'failure'}):
                        self.assertEqual(ci.summary(),1)
                        self.assertEqual((directory/'wynik-kod.csv').read_text().strip(),'1')
                (directory/'OSLONY.md').unlink();self.assertEqual(ci.summary(),1)
    def test_missing_component_entry_does_not_rewrite_K_transport(self):
        class Failed(Exception):pass
        with work() as directory,mock.patch.multiple(ci,PORT=directory,C=SimpleNamespace(base=SimpleNamespace(StepFailed=Failed)),create=True),mock.patch.dict(ci.os.environ,{},clear=True):
            with self.assertRaisesRegex(Failed,'COMPONENT entry missing'):ci.compile_component_duck()
    def test_stateful_model_instance_survives_case_boundary(self):
        instance=SimpleNamespace(check=mock.Mock());factory=mock.Mock(return_value=instance)
        adapter=ci.ModelAdapter(SimpleNamespace(OwnershipModel=factory),True)
        adapter.check(1,1,(),[],True);adapter.check(2,1,(),[],True)
        self.assertEqual(factory.call_count,1);self.assertEqual(instance.check.call_count,2)

if __name__=='__main__':unittest.main()
