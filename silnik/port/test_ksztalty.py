from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                              
from collections import Counter
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).parent

def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

p=module('shape_comparison_test','porownaj-ksztalty.py');g=p.g
n=module('shape_negative_test','ujemne-ksztalty.py')


def fixture():
    pass                                                                   

                                                                     
                                                                      
                                                                    
       
    f=g.bits
    ops=(g.world(),g.body(kind=0),g.shape(density=0,invoke=0),
         g.shape(1,density=0,invoke=0),g.shape(2,density=0,invoke=0),g.op(11,0,1,1),
         g.shape(3,density=0,invoke=0),g.op(14,0,1),g.op(21,0,0,1),
         g.object_op(3,3,1<<63),g.op(3,0,0))
    rows=(g.Case(1,'E2e53a13aa80a Ea7eeb9382233',ops),)
    wh=(1,0,0,0x10000,0,0,0,1,0);bh=(1,0,1,1,1,1,0,2,0)
    sh={0:(1,0,1,1,1,1,0,3,0),1:(2,0,1,1,2,1,0,4,0),
        2:(3,0,1,1,3,1,0,5,0),3:(2,0,2,2,2,1,0,6,0)}
                                                                                
    ledger=((1,(),(),1,0,0),(2,(),(),2,0,0),(3,(0,),(0,),3,0,0),
            (4,(0,1),(1,0),3,1,0),(5,(0,1,2),(2,1,0),3,2,0),
            (5,(0,1,2),(2,0),3,1,0),(6,(0,1,2,3),(3,2,0),3,3,0),
            (6,(0,1,2,3),(3,2,0),3,1,1),(6,(0,1,2,3),(3,2,0),2,0,0),
            (6,(0,1,2,3),(3,2,0),3,3,0),(6,(0,1,2,3),(),2,0,0))
    records=[('PORT7',(1,)),('CASE',(1,len(ops)))]
    spec=g.w6.f32(.02);upper=g.w6.f32(.5+spec);fat=g.w6.f32(upper+spec)
    aa=tuple(map(f,(-upper,-upper,upper,upper)));ff=tuple(map(f,(-fat,-fat,fat,fat)))
    proxy={0:0,1:1,2:3,3:1}
    for seq,(row,entry) in enumerate(zip(ops,ledger),1):
        last,saved,children,kind,slot,status=entry;live_b=2<=seq<11;handles={1:{0:wh},2:{0:bh},3:sh}
        records += [('E',(1,seq,*row)),('R',(1,seq,0,status,kind,*handles[kind][slot]))]
        records += [('V',(1,seq,1,0,1,1))]
        if seq>=2:records += [('V',(1,seq,2,0,int(live_b),int(live_b)))]
        for ss in saved:
            records += [('V',(1,seq,3,ss,int(ss in children),int(ss in children)))]
        records += [('W',(1,seq,0,*wh[:5],*wh[7:9],0,f(-10),f(400),int(live_b),len(children),0))]
        if live_b:
            state=(0,0,0,f(1),0,0,0,0,0,0,0,0,0,0,len(children),0,1,0,0,0,0)
            records += [('B',(1,seq,0,*bh,*state))]
        for ss in sorted(children):
            obj=(1,0,0x80000000) if seq>=10 and ss==3 else (0,0,0)
            records += [('S',(1,seq,ss,*sh[ss],*bh[:3],*wh[:3],0,0,f(.6),0,0,0,0,0,
                              1,0,g.U32,g.U32,0,0,0,0,0,0,*aa,*obj))]
        for ss in sorted(children):
            geom=[0]*40;geom[1]=1;geom[2]=f(.5)
            records += [('G',(1,seq,ss,*geom))]
        if live_b:
            records += [('L',(1,seq,0,len(children),*(x for ss in children for x in sh[ss][:3]))),
                        ('A',(1,seq,0,*(aa if children else (0,0,0,0))))]
        if seq==9:records += [('Q',(1,seq,0,1,1,*sh[3][:3]))]
        if live_b:records += [('X',(1,seq,0,0,0,f(100000),0,0,0,f(1),0))]
        for ss in sorted(children):
            j=children.index(ss);prev=sh[children[j-1]][0]-1 if j else g.U32
            nxt=sh[children[j+1]][0]-1 if j+1<len(children) else g.U32
            records += [('P',(1,seq,ss,sh[ss][0]-1,0,prev,nxt,proxy[ss]<<2,0,0,*ff,0))]
        for ss in sorted(children):
            records += [('T',(1,seq,ss,0,proxy[ss],*ff,1,0,sh[ss][0]-1,0))]
        records += [('F',(1,seq,0,0,len(children),0,0,0))]
        records += [('H',(1,seq,0,0,16,0,*([0]*48))),('H',(1,seq,0,1,32,0,*([0]*96)))]
        records += [('I',(1,seq,int(live_b),len(children),len(children),1,0,2))]
        sw,sb,ss=1,int(seq>=2),len(saved);lb=int(live_b);ls=len(children)
        records += [('Z',(1,seq,sw,sb,ss,1,lb,ls,1,1,sw+sb+ss,1,lb,ls,ls,lb,lb,int(seq==9),0,last,0))]
    records += [('ENDCASE',(1,)),('END',(1,))]
    return rows,''.join(p.format_record(tag,v) for tag,v in records)


def mutate(text,tag,name,value=None,seq=None):
    lines=text.splitlines(keepends=True)
    for i,line in enumerate(lines):
        t,v=p.parse_record(line)
        if t==tag and (seq is None or v[1]==seq):
            ix=p.names_for(t,v).index(name);a=list(v);a[ix]=a[ix]^1 if value is None else value
            lines[i]=p.format_record(t,a);return ''.join(lines)
    raise AssertionError((tag,name,seq))


class Corpus(unittest.TestCase):
    def test_population_and_transports(self):
        rows=g.cases();self.assertEqual([c.id for c in rows],list(range(1,97)))
        self.assertEqual(len({c.ops for c in rows}),96)
        for decimal in (False,True):
            result=g.read_input(g.encode(rows,decimal),decimal,96)
            self.assertEqual([c.ops for c in rows],[c.ops for c in result])
        self.assertEqual(len(g.small_cases()),1)
    def test_all_permitted_N(self):
        rows=g.cases()
        for count in range(1,97):
            for decimal in (False,True):
                result=g.read_input(g.encode(rows[:count],decimal),decimal,count)
                self.assertEqual(len(result),count)
    def test_saved_bytes(self):
        g.verify_input_hashes(HERE)
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp)
            for name in (*g.INPUT_NAMES,'wejscia-ksztalty-sha256.json'):(root/name).write_bytes((HERE/name).read_bytes())
            name=g.INPUT_NAMES[0];(root/name).write_bytes((root/name).read_bytes().replace(b'\r\n',b'\n'))
            with self.assertRaisesRegex(ValueError,'bytes'):g.verify_input_hashes(root)
    def test_negative_pairs(self):
        self.assertGreaterEqual(len(n.variants()),20)
        for name,c,d,cd,dd in n.variants():
            for text,decimal in ((c,False),(d,True)):
                with self.subTest(name=name,decimal=decimal),self.assertRaises(ValueError):
                    g.read_input(text.decode('ascii'),decimal)
            self.assertTrue(cd.startswith(b'PORT7: '));self.assertTrue(dd.startswith(b'BLAD: '))
    def test_normalized_rotation_open_interval(self):
        for word in (0x3f7fec56,0x3f8009d4):
            self.assertFalse(g.w6.valid_rotation(g.number(word),0))
        self.assertTrue(g.w6.valid_rotation(.6,.8))
    def test_pair_layout(self):
        a=g.pair(bslot=3,sslot=7,owner=2,kind=1,geometry=g.box(q=(.6,.8)),object_id=1<<63)[1:]
        b,s=p.pair_arguments(a)
        self.assertEqual(b,g.body(3,2,1)[1:]);self.assertEqual(s,g.shape(7,2,3,g.box(q=(.6,.8)),object_id=1<<63)[1:])


class Station(unittest.TestCase):
    def setUp(self):self.rows,self.good=fixture()
    def rejects(self,bad):
        for side in ('C','Duckling','both'):
            c=bad if side in ('C','both') else self.good;d=bad if side in ('Duckling','both') else self.good
            errors=p.compare(c,d,self.rows)
            self.assertTrue(errors,side)
            for name in (('C:','Duckling:') if side=='both' else (side+':',)):
                self.assertTrue(any(e.startswith(name) for e in errors),errors)
    def test_independent_positive(self):
        self.assertEqual(p.compare(self.good,self.good,self.rows),[])
        pub=''.join(p.public_lines(io.StringIO(self.good)))
        self.assertEqual(p.validate_output(pub,self.rows,False)['Z'],11)
        self.assertIsNone(p.first_difference(self.good,pub,True))
    def test_damaged_fields_both_sides(self):
        mutations=[('B','mass',None,3),('P','fatAABB.upper.x',g.bits(.1),3),('S','shapeType',1,3),
          ('G','h0',1,3),('E','a4',None,3),('Z','nS',None,3),('I','nP',None,3),
          ('R','birth.high',None,3),('R','owner.high',None,3),('R','packed.low',None,3),
          ('R','generation',None,3),('R','status',0,8),('L','shapes[0].index1',1,5),
          ('P','prevShapeId',g.U32,4),('P','nextShapeId',None,4),('P','id',42,3),
          ('T','leafAABB.lower.x',None,3),('T','treeUserData.high',1,3),('F','dynamicProxyCount',1,3),
          ('S','object.high',None,10),('G','h39',1,3),('W','shapeCount',0,3),('V','gameValid',0,3),
          ('H','count',1,3),('X','rotation0.c',0,3),('A','upper.x',None,2)]
        for tag,name,value,seq in mutations:
            with self.subTest(tag=tag,field=name):self.rejects(mutate(self.good,tag,name,value,seq))
    def test_missing_duplicate_reordered_extra(self):
        lines=self.good.splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.startswith('S '))
        for bad in (''.join(lines[:i]+lines[i+1:]),''.join(lines[:i]+[lines[i]]+lines[i:]),
                    ''.join(lines[:i]+[lines[i+1],lines[i]]+lines[i+2:]),self.good+'END 1\n',self.good[:-8]):
            self.rejects(bad)
    def test_noncanonical_H_D_and_overflow(self):
        for bad in (self.good.replace('3f800000','3F800000',1),self.good.replace('PORT7 1','PORT7 01',1),
                    self.good.replace('00000000','100000000',1),self.good.replace('00000000','0000000',1),
                    self.good.replace('\n','\r\n',1),self.good.replace('E 1 1','E  1 1',1)):
            self.rejects(bad)
    def test_exit_codes(self):
        for c,d in ((1,0),(0,3),(124,0),(0,125),(1,1)):
            self.assertTrue(p.compare(self.good,self.good,self.rows,c,d))
    def test_first_difference_location(self):
        bad=mutate(self.good,'P','fatAABB.upper.x',seq=3)
        err=p.first_difference(self.good,bad)
        for text in ('id 1','seq 3','record P','fatAABB.upper.x'):self.assertIn(text,err)
    def test_public_projection_is_bytewise(self):
        pub=''.join(p.public_lines(io.StringIO(self.good)))
        self.assertIsNotNone(p.first_difference(self.good,pub.replace('00000000','80000000',1),True))
    def test_metadata_does_not_change_physics(self):
        self.rejects(mutate(self.good,'A','upper.x',g.bits(1),10))
    def test_refusal_does_not_change_any_observation(self):
        self.rejects(mutate(self.good,'X','minExtent',g.bits(1),8))
    def test_pair_requires_two_consecutive_tickets(self):
        a=g.pair()[1:];ba,sa=p.pair_arguments(a);m=p.Life();w=m.create_world(0,g.world()[1:])
        b=m.create_body(0,w,ba);s=m.create_shape(0,b,sa)
        self.assertEqual((w.birth,b.birth,s.birth,m.last),(1,2,3,3))
    def test_wrap_model_and_child_list(self):
        m=p.Life();w=m.create_world(0,g.world()[1:]);b=m.create_body(0,w,g.body()[1:]);old=m.create_shape(0,b,g.shape()[1:]);m.destroy(old)
        for i in range(65536):
            s=m.create_shape(1,b,g.shape(1)[1:])
            if i!=65535:m.destroy(s)
        self.assertEqual((m.raw_valid(old),m.live(old)),(1,False))
        self.assertEqual(b.children,[s]);m.destroy(b);self.assertFalse(m.live(s));self.assertEqual(w.free_s,[1])


@unittest.skipUnless(os.environ.get('KSZTALTY_C_BIN'),'Native C executable is not supplied')
class NativeC(unittest.TestCase):
    def test_small_public_and_private(self):
        executable=Path(os.environ['KSZTALTY_C_BIN'])
        result=subprocess.run([str(executable),str(HERE/'proba-ksztalty.csv')],capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(p.validate_output(result.stdout.decode('ascii'),g.small_cases())['Z'],len(g.small_cases()[0].ops))
    def test_tickets(self):
        result=subprocess.run([os.environ['KSZTALTY_C_BIN'],'--test-tickets'],capture_output=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout),(0,b'BILETY OK\n'),result.stderr)


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(dir=HERE)
        cls.work=Path(cls.temp.name).resolve();root=HERE.resolve().parents[1]
        with patch.dict(os.environ,{'RESULT_DIR':str((cls.work/'wyniki').relative_to(root)),
                                    'RUNNER_TEMP':str(cls.work/'runner')}):
            cls.ci=module('shape_pipeline_test','ci.py')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.out=self.work/'evidence';self.out.mkdir(exist_ok=True)
        self.patches=[patch.object(self.ci,'OUT',self.out),patch.object(sys,'argv',['ci.py','proby-ksztalty'])]
        for item in self.patches:item.start()
        self.addCleanup(lambda:[item.stop() for item in reversed(self.patches)])
    def write(self,name,data):
        path=self.out/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data if isinstance(data,bytes) else str(data).encode('ascii'))
    def save_positive(self,prefix='base'):
        rows,text=fixture()
        for side,decimal in (('c',False),('duckling',True)):
            name=prefix+'-'+side
            self.write('wejscia-ksztalty/'+name+'.csv',g.encode(rows,decimal))
            self.write(name+'.csv',text.encode('utf-8'))
            self.write(name+'-wykonanie-kod.csv','0\n');self.write(name+'-wykonanie-stderr.csv',b'')
        return rows,text
    def test_positive_requires_each_side_and_exact_input(self):
        rows,text=self.save_positive()
        self.assertEqual(self.ci.shape_positive_errors('base',rows,g),[])
        for side in ('c','duckling'):
            self.save_positive();self.write('base-'+side+'-wykonanie-kod.csv','3\n')
            self.write('base-'+side+'.csv',b'');self.write('base-'+side+'-wykonanie-stderr.csv',b'BLAD: liczba przypadkow.\n')
            self.assertTrue(self.ci.shape_positive_errors('base',rows,g))
        self.save_positive();self.write('wejscia-ksztalty/base-duckling.csv',g.encode(rows,True)+'\n')
        self.assertTrue(self.ci.shape_positive_errors('base',rows,g))
    def test_positive_same_corruption_is_not_an_oracle(self):
        rows,text=self.save_positive()
        for side in ('c','duckling'):self.write('base-'+side+'.csv',mutate(text,'R','birth.high',seq=3))
        errors=self.ci.shape_positive_errors('base',rows,g)
        self.assertTrue(any(x.startswith('base-c:') for x in errors))
        self.assertTrue(any(x.startswith('base-duckling:') for x in errors))
    def test_bad_base_prevents_negative_execution(self):
        with patch.object(self.ci,'shape_run',return_value=(3,b'',b'BLAD: liczba przypadkow.\n')) as run,patch.object(self.ci,'shape_positive_errors',return_value=['bad N']):
            with self.assertRaises(self.ci.base.StepFailed):self.ci.shape_probes()
            self.assertEqual(run.call_count,2)
    def test_summary_requires_every_new_stage_and_outcome(self):
        stages={'c-ksztalty':'C_KSZTALTY','duckling-ksztalty':'DUCKLING_KSZTALTY',
                'check-ksztalty':'KSZTALTY','proby-ksztalty':'PROBY_KSZTALTY','mutacje-ksztalty':'MUTACJE_KSZTALTY'}
        def old_summary(**kwargs):self.write('wynik-kod.csv','0\n');self.write('DZIENNIK.md','# previous\n')
        env={name+'_OUTCOME':'success' for name in stages.values()}
        with patch.object(self.ci,'summary',side_effect=old_summary),patch.object(self.ci,'shape_evidence',return_value=True),patch.dict(os.environ,env),patch('builtins.print'):
            for stage in stages:self.write('etap-port-'+stage+'-kod.csv','0\n')
            self.assertEqual(self.ci.summary_shapes(),0)
            for stage,name in stages.items():
                for code in ('1','125',None):
                    path=self.out/('etap-port-'+stage+'-kod.csv')
                    if code is None:path.unlink()
                    else:self.write(path.name,code+'\n')
                    self.assertEqual(self.ci.summary_shapes(),1,(stage,code))
                    self.write(path.name,'0\n')
                for outcome in ('failure','skipped','MISSING'):
                    with patch.dict(os.environ,{name+'_OUTCOME':outcome}):
                        self.assertEqual(self.ci.summary_shapes(),1,(stage,outcome))
            with patch.object(self.ci,'shape_evidence',return_value=False):self.assertEqual(self.ci.summary_shapes(),1)
    def test_summary_retains_old_failure(self):
        def old_summary(**kwargs):self.write('wynik-kod.csv','1\n');self.write('DZIENNIK.md','# previous failure\n')
        with patch.object(self.ci,'summary',side_effect=old_summary),patch.object(self.ci,'shape_evidence',return_value=True),patch('builtins.print'):
            self.assertEqual(self.ci.summary_shapes(),1)
    def test_mutation_replacement_requires_one_hit(self):
        path=self.out/'copy.dk'
        for original in ('no match','value value'):
            path.write_text(original,encoding='utf-8')
            with self.assertRaises(self.ci.base.StepFailed):self.ci.replace_once(path,'value','bad')
        path.write_text('prefix value suffix',encoding='utf-8');self.ci.replace_once(path,'value','bad')
        self.assertEqual(path.read_text(),'prefix bad suffix')
    def test_workflow_isolation_and_required_codes(self):
        from public_ci import check
        check(self)
    def test_forecast_counts_and_evidence_limit(self):
        measured=p.measure(g.cases())
        self.assertEqual(measured['records']['E'],1957)
        self.assertEqual(measured['records']['J'],131138)
        self.assertEqual(measured['records']['R'],1994)
        self.assertLessEqual(measured['three_streams_bytes'],192*1024*1024)
        self.assertEqual(measured['three_streams_bytes'],197419503)


class ExtraStation(unittest.TestCase):
    def test_metadata_cannot_change_B_or_S_physics(self):
        rows,text=fixture()
        for tag,name in (('B','mass'),('S','density')):
            bad=mutate(text,tag,name,seq=10)
            self.assertTrue(p.compare(bad,bad,rows))
    def test_empty_hash_slot_cannot_keep_key(self):
        rows,text=fixture();bad=mutate(text,'H','items[0].low',1,3)
        self.assertTrue(p.compare(bad,bad,rows))
    def test_measurement_does_not_change_model_validation(self):
        rows,text=fixture();p.measure(rows)
        self.assertEqual(p.compare(text,text,rows),[])


def churn_fixture():
                                                                          
                                                                          
    base_rows,text=fixture();f=g.bits
    rows=(g.Case(1,'mikrokroki',(*base_rows[0].ops[:3],g.op(11,0,0,1),g.op(20,0,0,1,2,0),g.op(14,0,0))),)
    records=[]
    for line in text.splitlines(keepends=True):
        tag,v=p.parse_record(line)
        if tag=='PORT7':records.append((tag,v))
        elif tag=='CASE':records.append((tag,(1,6)))
        elif tag not in ('ENDCASE','END') and v[1]<=3:records.append((tag,v))
    wh=(1,0,0,0x10000,0,0,0,1,0);bh=(1,0,1,1,1,1,0,2,0)
    old=(1,0,1,1,1,1,0,3,0);first=(1,0,2,2,1,1,0,4,0);current=(1,0,3,3,1,1,0,5,0)
    upper=g.w6.f32(.5+g.w6.f32(.02));fat=g.w6.f32(upper+g.w6.f32(.02))
    aa=tuple(map(f,(-upper,-upper,upper,upper)));ff=tuple(map(f,(-fat,-fat,fat,fat)))
    for seq in (4,5,6):
        live=seq>=5;count=int(live);last=5 if live else 3
        records.append(('E',(1,seq,*rows[0].ops[seq-1])))
        if seq==5:
            for j,phase,h,nshape in ((1,1,first,1),(2,0,first,0),(2,1,current,1)):
                records.append(('J',(1,5,j,phase,*h,0,0,nshape,nshape,0,0,0,0)))
        records.append(('R',(1,seq,0,1 if seq==6 else 0,3,*(current if seq==5 else old))))
        records.extend([('V',(1,seq,1,0,1,1)),('V',(1,seq,2,0,1,1)),('V',(1,seq,3,0,0,0))])
        if live:records.append(('V',(1,seq,3,1,1,1)))
        records.append(('W',(1,seq,0,*wh[:5],*wh[7:9],0,f(-10),f(400),1,count,0)))
        state=(0,0,0,f(1),0,0,0,0,0,0,0,0,0,0,count,0,1,0,0,0,0)
        records.append(('B',(1,seq,0,*bh,*state)))
        if live:
            records.append(('S',(1,seq,1,*current,*bh[:3],*wh[:3],0,f(1),f(.6),0,0,0,0,0,
                                  1,0,g.U32,g.U32,0,0,0x3f490fdb,0,0,0x3dc90fdb,*aa,0,0,0)))
            geo=[0]*40;geo[1]=1;geo[2]=f(.5);records.append(('G',(1,seq,1,*geo)))
        records.append(('L',(1,seq,0,count,*(current[:3] if live else ()))))
        records.append(('A',(1,seq,0,*(aa if live else (0,0,0,0)))))
        records.append(('X',(1,seq,0,0,0,f(100000),0,0,0,f(1),0)))
        if live:
            records.append(('P',(1,seq,1,0,0,g.U32,g.U32,0,0,0,*ff,0)))
            records.append(('T',(1,seq,1,0,0,*ff,1,0,0,0)))
        records.append(('F',(1,seq,0,count,count,0,0,0)))
        if live:records.append(('U',(1,seq,0,0,0)))
        items=[0]*48
        if live:items[36:39]=[1,0,0x34c2cb2c]
        records.extend([('H',(1,seq,0,0,16,count,*items)),('H',(1,seq,0,1,32,0,*([0]*96)))])
        records.append(('I',(1,seq,1,count,count,1,count,2)))
        ss=2 if live else 1
        records.append(('Z',(1,seq,1,1,ss,1,1,count,1,1,2+ss,1,1,count,count,1,1,0,3 if seq==5 else 0,last,0)))
    records.extend([('ENDCASE',(1,)),('END',(1,))])
    return rows,''.join(p.format_record(t,v) for t,v in records)


class ChurnStation(unittest.TestCase):
    def test_independent_churn_ledger(self):
        rows,text=churn_fixture();self.assertEqual(p.compare(text,text,rows),[])
        self.assertEqual(p.validate_output(text,rows)['J'],3)
    def test_same_churn_damage_is_detected_for_each_side(self):
        rows,text=churn_fixture()
        for name in ('generation','birth.high','oldRawValid','oldGameValid','worldShapeCount','bodyShapeCount','mass','phase','j'):
            bad=mutate(text,'J',name)
            with self.subTest(field=name):self.assertTrue(p.compare(bad,bad,rows))
        lines=text.splitlines(keepends=True);j=next(i for i,x in enumerate(lines) if x.startswith('J '))
        for index in (j,j+1,j+2):
            bad=''.join(lines[:index]+lines[index+1:]);self.assertTrue(p.compare(bad,bad,rows))
    def test_churn_difference_names_microstep(self):
        rows,text=churn_fixture();bad=mutate(text,'J','mass');err=p.first_difference(text,bad)
        for value in ('id 1','seq 5','j 1','phase 1','record J','mass'):self.assertIn(value,err)


class EvidenceReplay(unittest.TestCase):
    setUpClass=classmethod(Pipeline.setUpClass.__func__)
    tearDownClass=classmethod(Pipeline.tearDownClass.__func__)
    setUp=Pipeline.setUp
    write=Pipeline.write
    def make_evidence(self):
        from types import SimpleNamespace
        rows,text=fixture()
        inputs=SimpleNamespace(verify_input_hashes=lambda *a:None,cases=lambda:rows,small_cases=lambda:rows,encode=g.encode)
        for suffix in ('','-bez'):
            name='ksztalty-bilety-c'+suffix
            self.write(name+'-wykonanie-kod.csv','0\n');self.write(name+'.csv',b'BILETY OK\n');self.write(name+'-wykonanie-stderr.csv',b'')
        for suffix,data in (('',b'BILETY\n'),('-crlf',b'BILETY\r\n')):
            name='ksztalty-bilety-duckling'+suffix
            self.write(name+'-wykonanie-kod.csv','0\n');self.write(name+'.csv',b'BILETY OK\n');self.write(name+'-wykonanie-stderr.csv',b'')
            self.write('wejscia-ksztalty/'+name+'.csv',data)
        name='ksztalty-bilety-osobne'
        for phase in ('kompilacja','wykonanie'):self.write(name+'-'+phase+'-kod.csv','0\n')
        self.write(name+'.csv',b'KSZTALTY BILETY OK\n');self.write(name+'-wykonanie-stderr.csv',b'');self.write('wejscia-ksztalty/'+name+'.csv',b'')
        for name,cdata,ddata,cdiag,ddiag in n.variants():
            for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
                tag='ksztalty-ujemny-'+name+'-'+side
                self.write(tag+'-wykonanie-kod.csv',str(wanted)+'\n');self.write(tag+'-wykonanie-stderr.csv',diag)
                self.write('wejscia-ksztalty/'+tag+'.csv',data)
        recipes=json.loads((HERE/'mutacje-ksztalty.json').read_bytes())['native_mutations'];results=[]
        for recipe in recipes:
            name='ksztalty-mutacja-'+recipe['name'];self.write(name+'-kompilacja-kod.csv','0\n')
            if recipe['expected_failure']=='tickets':code=3;stderr=b'BLAD: proba biletow.\n';output=b''
            elif recipe['expected_failure']=='integrity':code=4;stderr=b'BLAD: lista ksztaltow.\n';output=b'E 1 4 11\n'
            else:code=0;stderr=b'';output=mutate(text,'B','mass',seq=3).encode('utf-8')
            self.write(name+'-wykonanie-kod.csv',str(code)+'\n');self.write(name+'-wykonanie-stderr.csv',stderr);self.write(name+'.csv',output)
            results.append({'name':name,'actual':code,'detected':True})
        self.write('mutacje-ksztalty-wynik.json',json.dumps(results))
        def modules(filename,name):
            return inputs if filename=='przypadki-ksztalty.py' else n if filename=='ujemne-ksztalty.py' else p
        return modules,recipes
    def test_replay_requires_right_rejection_reason_on_both_sides(self):
        modules,_=self.make_evidence()
        with patch.object(self.ci,'shape_module',side_effect=modules),patch.object(self.ci,'shape_positive_errors',return_value=[]):
            self.assertTrue(self.ci.shape_evidence())
            for name,cdata,ddata,cdiag,ddiag in n.variants():
                for side,diag in (('c',cdiag),('duckling',ddiag)):
                    path='ksztalty-ujemny-'+name+'-'+side+'-wykonanie-stderr.csv'
                    self.write(path,b'WRONG CAUSE\n');self.assertFalse(self.ci.shape_evidence(),(name,side));self.write(path,diag)
            self.assertTrue(self.ci.shape_evidence())
    def test_replay_rejects_compilation_failure_and_unexecuted_mutant(self):
        modules,recipes=self.make_evidence()
        with patch.object(self.ci,'shape_module',side_effect=modules),patch.object(self.ci,'shape_positive_errors',return_value=[]):
            for recipe in recipes:
                name='ksztalty-mutacja-'+recipe['name']
                self.write(name+'-kompilacja-kod.csv','1\n');self.assertFalse(self.ci.shape_evidence());self.write(name+'-kompilacja-kod.csv','0\n')
                original=(self.out/(name+'-wykonanie-kod.csv')).read_bytes()
                for code in (124,125,126,127):
                    self.write(name+'-wykonanie-kod.csv',str(code)+'\n');self.assertFalse(self.ci.shape_evidence())
                self.write(name+'-wykonanie-kod.csv',original)
            self.assertTrue(self.ci.shape_evidence())
    def test_replay_does_not_trust_mutation_json(self):
        modules,recipes=self.make_evidence()
        with patch.object(self.ci,'shape_module',side_effect=modules),patch.object(self.ci,'shape_positive_errors',return_value=[]):
            name='ksztalty-mutacja-'+recipes[0]['name'];rows,text=fixture()
            self.write(name+'.csv',text.encode('utf-8'));self.write('ksztalty-mutacje-baza-c.csv',text.encode('utf-8'))
            self.assertFalse(self.ci.shape_evidence())
    def test_contract_body_is_verbatim_plan(self):
        root=HERE.resolve().parents[1]
        plan=norm_text(HERE/'fixtures/norms/PLAN-7-ZRODLO-KONTRAKTU.json').splitlines()
        contract=norm_text(HERE/'fixtures/norms/KONTRAKT-7.json').splitlines()
        self.assertEqual(contract[4:104],plan)

if __name__=='__main__':unittest.main()
