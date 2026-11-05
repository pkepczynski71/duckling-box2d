from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                       
from collections import Counter, defaultdict
import copy
import importlib.util
from pathlib import Path
import re
import sys
import unittest

HERE=Path(__file__).resolve().parent


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


m=load('test_zywy_records','model-zywy.py')
n=load('test_zywy_negatives','ujemne-zywy.py')
b=load('test_zywy_branches','galezie-zywy.py')
f=load('test_zywy_guards','wejscia-zywy-oslony.py')
CONTRACT=norm_text(HERE/'fixtures/norms/KONTRAKT-12.json')


def literal_snapshots():
    section=CONTRACT.split('### 13.3.',1)[1].split('### 13.4.',1)[0]
    output=re.findall(r'```text\n(.*?)```',section,re.S)[-1]
    result=[]
    current=[]
    operation=None
    for line in output.splitlines(keepends=True):
        tag,value=m.parse(line)
        if tag=='E':
            operation=value[2:]
            current=[]
        if operation is not None:
            current.append((tag,value))
        if tag=='Z12':
            result.append((value[0],value[1],operation,current))
            operation=None
    return output,result


class Frozen12Grammar(unittest.TestCase):
    def test_every_literal_new_record_and_inherited_complete_example(self):
        section=CONTRACT.split('### 13.1.',1)[1].split('### 13.4.',1)[0]
        seen=Counter()
        for block in re.findall(r'```text\n(.*?)```',section,re.S):
            for line in block.splitlines(keepends=True):
                tag=line.split(' ',1)[0]
                if tag in m.SCHEMA:
                    if tag=='GA' and not all(m.HEX.fullmatch(w) for w in line.rstrip('\n').split(' ')[2:]):
                                                                          
                        words=line.rstrip('\n').split(' ')
                        self.assertEqual(len(words),66)
                        self.assertTrue(all(m.DEC.fullmatch(w) and int(w)<=0xffffffff for w in words[1:]))
                        continue
                    parsed,value=m.parse(line)
                    self.assertEqual(m.format_record(parsed,value),line)
                    seen[tag]+=1
        self.assertTrue(set(m.SCHEMA)-{'PORT12','COMPONENT12'}<=set(seen))
        output,snapshots=literal_snapshots()
        self.assertEqual(len(output.encode('ascii')),14099)
        self.assertEqual(len(snapshots),2)
        for args in snapshots:
            m.SnapshotGrammar().check(*args,private=True)

    def test_independent_completeness_rejects_same_missing_row_and_adjusted_counter(self):
        for missing,counter_index in (('WS12',1),('NM12',2),('UD12',3),('HC12',4)):
            _,snapshots=literal_snapshots()
            args=list(snapshots[1]);rows=copy.deepcopy(args[3])
            removed=False
            changed=[]
            for tag,value in rows:
                if tag==missing and not removed:
                    removed=True
                    continue
                if tag=='I12':
                    words=list(value);words[2+counter_index]-=1;value=tuple(words)
                changed.append((tag,value))
            args[3]=changed
            self.assertTrue(removed)
                                                                              
            for side in ('C','D'):
                with self.subTest(tag=missing,side=side),self.assertRaises(ValueError):
                    m.SnapshotGrammar().check(*args,private=True)

    def test_order_duplicate_name_tail_and_defined_finite_are_not_hash_checks(self):
        _,snapshots=literal_snapshots()
        for mutation in ('order','duplicate','name-tail','nonfinite'):
            args=list(snapshots[1]);rows=copy.deepcopy(args[3])
            if mutation=='order':
                i=next(i for i,(tag,_) in enumerate(rows) if tag=='WS12')
                rows[i],rows[i+1]=rows[i+1],rows[i]
            elif mutation=='duplicate':
                i=next(i for i,(tag,_) in enumerate(rows) if tag=='NM12');rows.insert(i,rows[i])
            else:
                tag='NM12' if mutation=='name-tail' else 'WS12'
                i=next(i for i,(t,_) in enumerate(rows) if t==tag)
                values=list(rows[i][1]);values[-1 if mutation=='name-tail' else 3]=1 if mutation=='name-tail' else 0x7f800000
                rows[i]=(tag,tuple(values))
            args[3]=rows
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                m.SnapshotGrammar().check(*args,private=True)

    def test_projection_masks_only_three_tuning_words_and_private_tags(self):
        line='WS12 1 2 0 '+' '.join(f'{v:08x}' for v in (0x80000000,1,0x42c80000,1,2,3,4,5,1,1,0))+'\n'
        tag,original=m.parse(line)
        result=list(m.projection((line,'NP12 1 2 0 0 '+' '.join(['00000000']*32)+'\n')))
        self.assertEqual(len(result),1)
        _,projected=m.parse(result[0])
        self.assertEqual([i for i,(a,b) in enumerate(zip(original,projected)) if a!=b],[6,7,8])
        self.assertEqual(projected[3],0x80000000)

    def test_variants_and_lexical_arity_are_strict(self):
        section=CONTRACT.split('### 13.1.',1)[1].split('### 13.2.',1)[0]
        for block in re.findall(r'```text\n(.*?)```',section,re.S):
            for line in block.splitlines(keepends=True):
                if line.split(' ',1)[0] not in m.SCHEMA:
                    continue
                for bad in (line.replace(' ','  ',1),line.rstrip('\n')+' 00000000\n',line.replace('\n','\r\n')):
                    with self.subTest(tag=line.split(' ',1)[0]),self.assertRaises(ValueError):
                        m.parse(bad)

    def test_shape_contact_copies_include_both_nested_points(self):
        number=lambda slot,birth:(slot,birth,0,1,0)
        manifold=(0,0x3f800000,0,2,*range(1,27))
        contact=(*number(0,2),*number(0,3),*number(1,4),1,*manifold)
        second=(*number(1,5),*number(0,3),*number(2,6),1,*manifold)
        first=list(contact);first[16]=0x42f60000
        rows=defaultdict(list)
        for phase,values in ((0,(contact,second)),(1,(second,tuple(first))),(2,(contact,second))):
            rows['CL12'].append((1,1,2,0,phase,0,2))
            for j,value in enumerate(values):rows['CV12'].append((1,1,2,0,phase,j,*value))
        m._contact_lists(rows)
        value=list(rows['CV12'][-2]);value[6+16+4+13]^=1
        rows['CV12'][-2]=tuple(value)
        with self.assertRaises(ValueError):m._contact_lists(rows)


class RefusalInputs(unittest.TestCase):
    def test_frozen_16_diagnostics_and_budget_are_not_product_learned(self):
        probes=n.variants()
        self.assertEqual(set(p.error for p in probes),set(n.CLASSES))
        self.assertEqual(len({p.name for p in probes}),len(probes))
        self.assertLessEqual(len(probes),256)
        for probe in probes:
            self.assertEqual(probe.stderr.count(b'\n'),1)
            self.assertRegex(probe.stderr,rb'^PORT12: INPUT_[A-Z_]+\n$')
            self.assertNotEqual(probe.c,probe.controls[0])
            self.assertNotEqual(probe.duckling,probe.controls[1])

    def test_control_transport_roundtrip_u32_for_both_parsers(self):
        for probe in n.variants():
            sides=[]
            for decimal,data in zip((False,True),probe.controls):
                parsed=[]
                for line in data.decode('ascii').splitlines():
                    if not line.startswith('O '):continue
                    words=line.split(' ')
                    self.assertEqual(len(words),67)
                    parsed.append((int(words[1]),int(words[2]),tuple(int(v,10 if decimal else 16) for v in words[3:])))
                self.assertEqual([r[0] for r in parsed],list(range(1,len(parsed)+1)))
                self.assertLessEqual(len(parsed),16)
                sides.append(parsed)
            self.assertEqual(*sides)

    def test_literal_F04_F06_F07_F08_F10_F11_F12_F13_patterns(self):
        probes={p.name:p for p in n.variants()}
        def last(name):return probes[name].c.decode('ascii').splitlines()[-1].split(' ')
        self.assertEqual(last('O-u32-overflow')[-1],'100000000')
        self.assertEqual(last('mode-80')[5],'00000002')
        self.assertEqual(last('bool-event')[8],'00000002')
        self.assertEqual(last('unused-minus-zero')[-1],'80000000')
        self.assertEqual(last('copy-uninitialized-K12')[2],'89')
        self.assertEqual(last('domain-raw-friction-negative')[7],'bf800000')
        self.assertEqual(last('body-preSolve-raw')[6:9],['00000000','00000002','00000001'])
        self.assertEqual(last('private-phase-64')[3:7],['00000000','00000003','00000000','00000000'])

    def test_fatal_check_rejects_second_line_further_stdout_and_wrong_code(self):
        probe=next(p for p in n.variants() if p.boundary=='header')
        n.check(probe,2,b'',probe.stderr,b'')
        for code,output,stderr in ((0,b'',probe.stderr),(2,b'',probe.stderr+b'error\n'),(2,b'END 1\n',probe.stderr)):
            with self.assertRaises(ValueError):n.check(probe,code,output,stderr,b'')

    def test_prefix_checked_through_final_complete_snapshot(self):
        output,_=literal_snapshots()
        probe=next(p for p in n.variants() if p.name=='O-seq')
        prefix=n.expected_prefix(probe,output.encode())
        self.assertTrue(prefix.endswith(b'Z12 1 1 00000000 00000001\n'))
        n.check(probe,2,prefix,probe.stderr,output.encode())
        with self.assertRaises(ValueError):n.check(probe,2,prefix+b'ENDCASE 1\n',probe.stderr,output.encode())

    def test_zero_negative_dt_game_numbers_are_not_raw_domain_fatal_fixtures(self):
                                                                           
                                                                             
        for probe in n.variants():
            if probe.name.startswith('domain-raw-friction'):
                last=probe.c.decode('ascii').splitlines()[-1].split(' ')
                self.assertEqual(last[5],'00000000')
        self.assertEqual({name for name,_,_ in n.positives()},{'LF','CRLF','last-O-without-LF'})


class HonestCoverage(unittest.TestCase):
    def test_empty_or_claim_only_receipts_cannot_pass_native_table(self):
        for receipts in ((),({'name':'fake','detected':True,'code':0},)):
            table=b.frozen_table(receipts=receipts)
            self.assertNotEqual(table['code'],0)
            self.assertEqual(table['accepted_receipts'],0)
            self.assertEqual(len(table['native_gaps']),93)
            self.assertTrue(all(r['port'] is None and r['operation'] is None for r in table['rows']))

    def test_binary32_receipts_pin_the_contract_counterexamples(self):
        receipts=b.predicate_receipts()
        self.assertEqual([receipts['S12'][k] for k in ('mass','invMass','weightedCenter','localCenter','originInertia','subtracted','inertia')],
                         ['40490fdb','3ea2f983','46c90fdb','46000000','4d490fdb','4d490fdb','00000000'])
        self.assertEqual(receipts['target_derived']['lengthSquared'],'7f800000')
        self.assertTrue(receipts['Bupper11']['131059']['accepted'])
        self.assertFalse(receipts['Bupper11']['131060']['accepted'])
        self.assertEqual(len(receipts['Atan2']),16)
        self.assertFalse(m.OWNERSHIP_READY)

    def test_unfinished_ownership_model_cannot_silently_validate_a_comparison(self):
        _,snapshots=literal_snapshots()
        with self.assertRaisesRegex(ValueError,'full OwnershipModel12 incomplete'):
            m.OwnershipModel().check(*snapshots[0],True)

    def test_diagnostic_ledger_literal_and_poisoned_history_across_CASE(self):
        _,snapshots=literal_snapshots()
        model=m.OwnershipModel(diagnostic_only=True)
        for snapshot in snapshots:model.check(*snapshot,True)
        self.assertEqual(model.last_ticket,2)
        bad=list(snapshots[1]);bad[1]=3
        bad[3]=[(tag,(*v[:1],3,*v[2:])) for tag,v in bad[3]]
                                                                         
        with self.assertRaises(ValueError):model.check(*bad,True)
        self.assertIsNotNone(model.failure)
        ticket=model.last_ticket
        args=list(snapshots[0]);args[0]=2
        args[3]=[(tag,(2,*v[1:])) for tag,v in args[3]]
        with self.assertRaisesRegex(ValueError,'history unavailable'):model.check(*args,True)
        self.assertEqual(model.last_ticket,ticket)
        self.assertEqual(len(model.continuity_gaps),1)

    def test_grammar_failure_also_poisons_temporal_state(self):
        _,snapshots=literal_snapshots()
        model=m.OwnershipModel(diagnostic_only=True)
        bad=list(snapshots[0]);bad[3]=[row for row in bad[3] if row[0]!='WS12']
        with self.assertRaises(ValueError):model.check(*bad,True)
        self.assertIsNotNone(model.failure)


class GuardTransport(unittest.TestCase):
    def test_all_locked_opcodes_and_subroutes_from_contract(self):
        fixtures=f.lock_routes()
        expected={1,2,3,4,10,11,12,13,15,16,17,18,19,30,32,34,35,36,40,55,57,58,59,60,61,80,81,82,83,84,85,86,87,90}
        self.assertEqual({item.kind-200 for item in fixtures},expected)
        self.assertEqual(len(fixtures),68)
        self.assertEqual({item.words[3] for item in fixtures if item.kind==280},set(range(9)))
        self.assertEqual({item.words[3] for item in fixtures if item.kind==281},set(range(9)))
        self.assertEqual({item.words[2] for item in fixtures if item.kind==282},set(range(6)))
        for item in fixtures:
            self.assertEqual((item.status,item.rows,item.positive_setup),(7,(),1))
            self.assertEqual(item.helper,2000+item.kind-200)
            self.assertNotIn(item.kind,(200,254,256,231))

    def test_every_helper_has_exact_64_words_and_literal_GR12_response(self):
        fixtures=f.definitions()
        self.assertLessEqual(len(fixtures),160)
        self.assertEqual(len({item.name for item in fixtures}),len(fixtures))
        for item in fixtures:
            parsed=[]
            for decimal in (False,True):
                lines=item.encode(decimal).decode('ascii').splitlines()
                words=lines[2].split(' ')
                self.assertEqual(len(words),66)
                parsed.append(tuple(int(w,10 if decimal else 16) for w in words[2:]))
            self.assertEqual(*parsed)
            if item.rows:
                self.assertTrue(item.all_success)
                self.assertEqual(item.positive_setup,0)
                continue
            response=[m.parse(line) for line in item.expected_helper_output().decode('ascii').splitlines(keepends=True)]
            gr=next(v for tag,v in response if tag=='GR12')
            self.assertEqual(gr,(1,0,item.helper,item.status,int(item.status==0),item.value&0xffffffff,item.value>>32))

    def test_prepared_guards_are_not_natively_claimed_and_setups_are_separate(self):
        fixtures=f.definitions()
        self.assertEqual(sum(item.positive_setup for item in fixtures),68)
        self.assertTrue(f.MISSING)
        self.assertEqual(len([item for item in fixtures if item.rows]),3)
        self.assertNotIn('G1',{item.group for item in fixtures})

    def test_polygon_count2_witness_has_only_count_fault_not_unused_vertices(self):
        fixture=next(item for item in f.definitions() if item.name=='G12-GEOM-polygon')
        self.assertEqual(fixture.words[3:6],(8,2,0))
        self.assertEqual(fixture.words[6:10],(0,0,0x3f800000,0))
        self.assertEqual(fixture.words[10:],(0,)*54)


class SplitMarkHistoryControls(unittest.TestCase):
    def test_history_guards_are_bounded_separate_preparations(self):
        fixtures=f.history_routes()
        self.assertEqual(len(fixtures),3)
        self.assertEqual(sum(item.positive_setup for item in fixtures),3)
        for item in fixtures:
            self.assertLessEqual(len(item.rows),16)
            self.assertEqual(sum(row[0] in (31,32) and n.g.number(row[2])>0 for row in item.rows),1)
            self.assertIn(n.op(1,0),item.rows)
            self.assertTrue(all(len(row)==65 for row in item.rows))

    def fixture(self,mark=0,body_birth=1,contact_birth=3):
        rows=defaultdict(list)
        for bid in (0,1):
            body=[0]*30;body[:6]=[1,1,bid,bid+1,0,1]
            body[8:12]=[7,0,body_birth+bid,0];body[12]=2
            rows['B'].append(tuple(body))
            rows['BS11'].append((1,1,0,bid,0,0,1,mark,0,1))
            rows['BL9'].append((1,1,0,bid,0,0,4,0xffffffff,0xffffffff,0))
        island=[1,2,0,4,0,1,2,0,0,1,0xffffffff,0xffffffff,0,0xffffffff,1]
        rows['IS']=[(1,1,0,4,*island)]
        contact=[1,0,2,0,0,0,1,0,0xffffffff,0xffffffff,1,0xffffffff,0xffffffff,4,0xffffffff,0xffffffff,1,mark,contact_birth,0]
        rows['CT']=[(1,1,0,0,*contact)]
        rows['WS11']=[(1,1,0,1,1,4,4,0)]
        model=m.OwnershipModel(diagnostic_only=True)
        model.regs['W'][0]={'live':True,'number':(0,7,0,0,0)}
        return model,rows

    def test_split_sets_marks_and_nonstep_retains_them(self):
        model,before=self.fixture()
        model._mark_history(before,n.op(90),0)
        model.previous=before
        _,after=self.fixture(mark=1)
        after['TR11']=[(1,2,0,0,3,4,2,2,2,1,1)]
        model._mark_history(after,n.op(32,0,n.bits(1/60),1),0)
        self.assertEqual(model.witnesses['split_mark_writes'],3)
        model.previous=after
        unchanged=copy.deepcopy(after);unchanged['TR11']=[]
        model._mark_history(unchanged,n.op(91,0,0,0,1),0)
        for tag,index in (('BS11',7),('CT',21)):
            damaged=copy.deepcopy(unchanged);row=list(damaged[tag][0]);row[index]=0;damaged[tag][0]=tuple(row)
            for side in ('C','D'):
                with self.subTest(side=side,tag=tag),self.assertRaises(ValueError):
                    model._mark_history(damaged,n.op(91,0,0,0,1),0)

    def test_missing_split_and_invented_mark_are_rejected(self):
        model,before=self.fixture();model._mark_history(before,n.op(90),0);model.previous=before
        _,after=self.fixture(mark=1)
        with self.assertRaises(ValueError):model._mark_history(after,n.op(32,0,n.bits(1/60),1),0)
        with self.assertRaises(ValueError):model._mark_history(after,n.op(91,0,0,0,1),0)

    def test_merge_destroys_pending_child_before_split_task_can_start(self):
        model,before=self.fixture()
        second=list(before['IS'][0]);second[3]=5;before['IS'].append(tuple(second))
        link=list(before['BL9'][1]);link[6]=5;before['BL9'][1]=tuple(link)
        contact=list(before['CT'][0]);contact[20]=0;before['CT'][0]=tuple(contact)
        before['WS11']=[(1,1,0,1,1,5,5,0)]
        model._mark_history(before,n.op(90),0);model.previous=before
        _,after=self.fixture(mark=1)
                                                                            
                                                                   
        after['TR11']=[(1,2,0,0,3,5,2,2,2,1,1)]
        with self.assertRaises(ValueError):model._mark_history(after,n.op(32,0,n.bits(1/60),1),0)

    def test_finalize_candidate_uses_M_before_sleep_and_resets_sleeping_body_move_index(self):
        model,rows=self.fixture()
        for j in range(2):
            b=list(rows['B'][j]);b[15]=n.bits(1);b[27]=j;b[28]=1;rows['B'][j]=tuple(b)
            h=list(rows['BS11'][j]);h[5]=n.bits(.75);h[8]=0xffffffff if j==0 else 1;rows['BS11'][j]=tuple(h)
            model.object_values[1][j]=(0,0,0)
            rows['M'].append((1,2,0,j,j+1,0,1,0,0,n.bits(1),0,0,0,0,int(j==0)))
        island=list(rows['IS'][0]);island[5]=3;island[18]=0;rows['IS'][0]=tuple(island)
        second=list(island);second[3]=5;second[5]=2;second[18]=1;rows['IS'].append(tuple(second))
        link=list(rows['BL9'][1]);link[6]=5;rows['BL9'][1]=tuple(link)
        rows['WS11']=[(1,2,0,0,1,0xffffffff,5,n.bits(.75)),(1,2,0,1,1,5,5,n.bits(.75))]
        operation=n.op(32,0,n.bits(1/60),1)
        model._finalize_history(rows,operation,0)
        for tag,row_index,field,value in (('WS11',0,6,0xffffffff),('M',0,14,0),('BS11',0,8,0),('M',1,7,1)):
            damaged=copy.deepcopy(rows);v=list(damaged[tag][row_index]);v[field]=value;damaged[tag][row_index]=tuple(v)
            for side in ('C','D'):
                with self.subTest(side=side,tag=tag,field=field),self.assertRaises(ValueError):
                    model._finalize_history(damaged,operation,0)


class MovementCopyHistoryControls(unittest.TestCase):
    def test_fresh_MC_must_copy_M_before_it_becomes_historical(self):
        model=m.OwnershipModel(diagnostic_only=True)
        body=(0,1,0,7,0)
        model.regs['W'][0]={'live':True,'number':(0,7,0,0,0)}
        model.regs['B'][0]={'live':True,'number':body,'raw':(1,0,1)}
        model.known_bodies.add(body)
        value=(0,0,n.bits(1),0,1,19,23,0)
        rows=defaultdict(list)
        rows['M']=[(1,1,0,0,1,0,1,*value)]
        rows['MCN']=[(1,1,0,1)];rows['MC']=[(1,1,0,0,*body,*value)]
        operation=n.op(32,0,n.bits(1/60),1,0)
        model._copies(rows,operation,0,False)
        wrong=copy.deepcopy(rows);v=list(wrong['MC'][0]);v[-2]^=1;wrong['MC'][0]=tuple(v)
        for side in ('C','D'):
            with self.subTest(side=side),self.assertRaises(ValueError):model._copies(wrong,operation,0,False)

    def test_noop_after_step_does_not_reemit_operation_local_M_or_K8_copy(self):
        model=m.OwnershipModel(diagnostic_only=True)
        before=defaultdict(list)
        body=[0]*30;body[:3]=[1,1,0];body[12]=2
        before['B']=[tuple(body)]
        before['K']=[(1,1,0,n.bits(1/60),1,1,1,1)]
        before['M']=[(1,1,0,0,1,0,1,0,0,n.bits(1),0,0,0,0,0)]
        before['MCN']=[(1,1,0,0)]
        model.previous=before
        after=defaultdict(list);after['B']=before['B'][:]
        model._atomic(after,n.op(80,0,0,1,0,2),0)
        damaged=copy.deepcopy(after);v=list(damaged['B'][0]);v[13]=1;damaged['B'][0]=tuple(v)
        with self.assertRaises(ValueError):model._atomic(damaged,n.op(80,0,0,1,0,2),0)

    def test_old_K8_copy_is_emitted_only_on_stepgame_or_readcopy(self):
        model=m.OwnershipModel(diagnostic_only=True)
        body=(0,1,0,1,0)
        saved=(*body,0,0,0x3f800000,0,0,0,0,0)
        model.known_bodies.add(body)
        model.saved_moves[0]=(saved,)
                                                                           
                                                                
        empty=defaultdict(list)
        model._copies(empty,n.op(80,0,0,1,0,0),0,False)
        read=defaultdict(list)
        read['MCN']=[(1,2,0,1)]
        read['MC']=[(1,2,0,0,*saved)]
        model._copies(read,n.op(37,0),0,False)
        damaged=copy.deepcopy(read)
        damaged['MC'][0]=(*read['MC'][0][:-1],1)
        for side in ('C','D'):
            with self.subTest(side=side),self.assertRaises(ValueError):
                model._copies(damaged,n.op(37,0),0,False)
        with self.assertRaises(ValueError):model._copies(empty,n.op(37,0),0,False)


class BodyTemporalHistoryControls(unittest.TestCase):
    def pool_rows(self,alive,free,next_id):
        rows=defaultdict(list)
        rows['BP11']=[(1,1,0,next_id,len(free),len(alive))]
        rows['BF11']=[(1,1,0,j,bid) for j,bid in enumerate(free)]
        rows['BS11']=[(1,1,0,bid,0,0,1,0,0,1) for bid in alive]
        return rows

    def test_body_allocator_pops_last_free_and_rejects_equal_partition_wrong_order(self):
        model=m.OwnershipModel(diagnostic_only=True)
        model.previous=self.pool_rows([0],[2,1],3)
        model._body_pool_history(self.pool_rows([0,1],[2],3))
        for side in ('C','D'):
            with self.subTest(side=side),self.assertRaises(ValueError):
                model._body_pool_history(self.pool_rows([0,2],[1],3))
        model.previous=self.pool_rows([0,2,4],[3,1],5)
        with self.assertRaises(ValueError):model._body_pool_history(self.pool_rows([0,2,4],[1,3],5))

    def test_body_free_push_and_nextIndex_extension_are_temporal(self):
        model=m.OwnershipModel(diagnostic_only=True)
        model.previous=self.pool_rows([0,1,2],[],3)
        model._body_pool_history(self.pool_rows([0,2],[1],3))
        model._body_pool_history(self.pool_rows([0,1,2,3],[],4))
        with self.assertRaises(ValueError):model._body_pool_history(self.pool_rows([0,1,2,4],[3],5))

    def layout(self,arrays,target,kind=2,enabled=1):
        rows=defaultdict(list)
        b=[0]*30;b[:4]=[1,1,target,target+1];b[12]=kind;b[28]=enabled;rows['B']=[tuple(b)]
        for (w,s),ids in arrays.items():rows['SD11'] += [(1,1,w,s,j,bid) for j,bid in enumerate(ids)]
        return rows

    def test_TransferBody_uses_RemoveSwap_not_stable_removal_even_if_sparse_is_consistent(self):
        model=m.OwnershipModel(diagnostic_only=True)
        model.previous=self.layout({(0,2):[0,1,2],(1,2):[8,9]},0)
        good=self.layout({(0,0):[0],(0,2):[2,1],(1,2):[8,9]},0,kind=0)
        operation=n.op(80,0,0,1,0,0)
        model._body_layout_history(good,operation,0)
        for bad in (self.layout({(0,0):[0],(0,2):[1,2],(1,2):[8,9]},0,kind=0),
                    self.layout({(0,0):[0],(0,2):[2,1],(1,2):[9,8]},0,kind=0)):
            for side in ('C','D'):
                with self.subTest(side=side),self.assertRaises(ValueError):model._body_layout_history(bad,operation,0)

    def test_wake_appends_sleeping_dense_bodies_before_target_transfer(self):
        model=m.OwnershipModel(diagnostic_only=True)
        model.previous=self.layout({(0,2):[0,1],(0,3):[2,3]},2)
        after=self.layout({(0,2):[0,1,3],(0,0):[2]},2,kind=0)
        after['TR11']=[(1,2,0,0,1,3,3,2,2,0,1)]
        model._body_layout_history(after,n.op(80,0,2,1,0,0),0)
        bad=self.layout({(0,2):[3,1,0],(0,0):[2]},2,kind=0);bad['TR11']=after['TR11']
        with self.assertRaises(ValueError):model._body_layout_history(bad,n.op(80,0,2,1,0,0),0)


class ParserDecisionD121(unittest.TestCase):
    def test_create90_names_cover_scalar_UTF8_byte_length_and_NUL_before_allocation(self):
        fixtures=f.name_routes()
        for fixture in fixtures:
            row=fixture.rows[-1];data=bytes(row[22:22+row[21]])
            self.assertEqual(row[0],90)
            self.assertEqual(len(row),65)
            self.assertEqual(row[22+len(data):54],(0,)*(32-len(data)))
            try:data.decode('utf-8');utf8=True
            except UnicodeDecodeError:utf8=False
            legal=row[3]==0 or len(data)<=31 and 0 not in data and utf8
            self.assertEqual(fixture.last_status,0 if legal else 5)
            self.assertEqual(fixture.expected_reason,0 if legal else 3)
        by_name={fixture.name:fixture for fixture in fixtures}
        self.assertEqual(by_name['G12-NAME-create-length32-UTF8'].last_status,5)
        self.assertEqual(by_name['G12-NAME-create-legal31-UTF8'].last_status,0)
        raw=by_name['G12-NAME-create-raw-readable32'].rows[-1]
        self.assertEqual(raw[21],32);self.assertEqual(raw[22:54],(0,*([90]*31)))

    def test_Target_equality_wakes_as_frozen_contract_requires(self):
        self.assertIn('equality passes',CONTRACT)
        fixtures=f.core_routes()
        self.assertEqual([x.expected_awake for x in fixtures],[0,1,1])
        self.assertEqual([x.rows[-1][5] for x in fixtures],[0x3d4ccccc,0x3d4ccccd,0x3d4cccce])
        table={r['id']:r for r in b.route_plan(HERE.parents[1])}
        self.assertEqual([table[x.name]['f32_steps'][-1]['passes'] for x in fixtures],[True,False,False])

    def test_route_table_carries_exact_field_traces_without_native_credit(self):
        rows={r['id']:r for r in b.route_plan(HERE.parents[1])}
        finite=rows['G12-BODY-linearDamping-finite']['f32_steps']
        sign=rows['G12-BODY-linearDamping-sign']['f32_steps']
        self.assertEqual(finite[0]['bits'],'7f800000')
        self.assertEqual([r['value'] for r in finite[1:]],[False,True])
        self.assertEqual(sign[0]['bits'],'bf800000')
        self.assertEqual([r['value'] for r in sign[1:]],[True,False])
        self.assertFalse(rows['G12-TARGET-norm-lower']['f32_steps'][-2]['passes'])
        self.assertFalse(rows['G12-TARGET-norm-upper']['f32_steps'][-1]['passes'])
        for row in rows.values():
            self.assertIsNone(row['deletion_effect'])
            self.assertEqual(row['native_mutation_status'],'UNVERIFIED')
            self.assertEqual(len(row['input_GA64']),64)

    def test_all_frame_physical_subclasses_and_first_error_intersections_are_explicit(self):
        probes={p.name:p for p in n.variants()}
        for tag,error in (('G','SEQUENCE'),('GA','WORDS'),('F','WORDS')):
            for kind in ('tag','BOM','tab','spacing','CR','nonASCII','overlong','arity-short','arity-long'):
                with self.subTest(tag=tag,kind=kind):
                    self.assertEqual(probes[tag+'-physical-'+kind].error,error)
        for name,error in (('word-before-mode','WORDS'),('opcode-before-word','OPCODE'),
                           ('mode-before-unused-register','MODE'),('unused-before-register','UNUSED'),
                           ('register-before-raw-domain','REGISTER')):
            self.assertEqual(probes['priority-'+name].error,error)
            self.assertEqual(probes['priority-'+name+'-after-O'].error,error)
        self.assertEqual(set(n.UNREACHABLE_AFTER_O),{'INPUT_HEADER','INPUT_N_RANGE'})
        self.assertTrue(all('D12-1(2)' in proof for proof in n.UNREACHABLE_AFTER_O.values()))

    def test_EOF_before_G_has_no_echo_as_guard10_and_guard11_precedent(self):
        probe=next(p for p in n.variants() if p.name=='EOF-before-G')
        control=b'GUARD12 1\nG 1 0 0 1\nGA 1\nCASE 1 1\n'
        self.assertEqual(n.expected_prefix(probe,control),b'')
        n.check(probe,2,b'',probe.stderr,control)
        with self.assertRaises(ValueError):n.check(probe,2,b'GUARD12 1\n',probe.stderr,control)


class CallbackModelControls(unittest.TestCase):
    def setup_model(self,kind,function=0,game=False,rules=()):
        model=m.OwnershipModel(diagnostic_only=True)
        model.regs['W'][0]={'live':True,'number':(0,1,2,0,0)}
        a=(0,2,3,1,2);b=(1,4,5,1,2)
        model.raw_shapes[(1|(2<<32),(1,0,1))]=a
        model.raw_shapes[(1|(2<<32),(2,0,1))]=b
        model.rules[0]=[[],[],[],[]];model.rules[0][kind]=list(rules)
        model.hook_values[0]=[1<<kind,0,0,0,0,0,0,0,0,0,0,0,0]
        model.hook_values[0][1+kind]=function
        model.hook_values[0][9+kind]=len(rules)
        model.hook_modes[0]=[0]*4;model.hook_modes[0][kind]=int(game)
        rows=defaultdict(list)
        rows['HC12']=[(1,1,0,*model.hook_values[0])]
        rows['HR12']=[(1,1,0,kind,j,*r) for j,r in enumerate(rules)]
        return model,rows,a,b

    def test_raw_fixture5_both_nested_points_are_checked_independently(self):
        model,rows,a,b=self.setup_model(1,function=5)
        before=(0x3f800000,0,0,2,*([0]*26))
        after=list(before);after[:2]=(0,0x3f800000)
        for j in range(2):
            for offset in (4,6,8):after[offset+13*j]=0x3e800000 if j==0 else 0xbe800000
        rows['HT12']=[(1,1,0,0,1,1,0,1,2,0,1,1,*before,*after)]
        model._rules_and_callbacks(rows,n.op(31,0,n.bits(1/60),1),0)
        self.assertEqual(model.witnesses['pre_fixture5_two_points'],1)
        for offset in (4,6,8):
            damaged=list(rows['HT12'][0]);damaged[5+37+13+offset]=0
            broken=copy.deepcopy(rows);broken['HT12']=[tuple(damaged)]
            for side in ('C','D'):
                with self.subTest(point1_field=offset,side=side),self.assertRaises(ValueError):
                    model._rules_and_callbacks(broken,n.op(31,0,n.bits(1/60),1),0)

    def test_rule_sides_and_both_ticket_halves_are_not_slot_matches(self):
        a=(0,2,3,1,2);b=(1,4,5,1,2)
        model,rows,_,_=self.setup_model(0,game=True,rules=((*a,*b,0),))
                                                                             
        rows['HT12']=[(1,1,0,0,0,2,0,1,1,0,1,1)]
        model._rules_and_callbacks(rows,n.op(31,0,n.bits(1/60),1),0)
        bad=copy.deepcopy(rows);v=list(bad['HT12'][0]);v[-1]=0;bad['HT12']=[tuple(v)]
        with self.assertRaises(ValueError):model._rules_and_callbacks(bad,n.op(31,0,n.bits(1/60),1),0)
                                                                           
        model.raw_shapes[(1|(2<<32),(1,0,1))]=(0,2,4,1,2)
        rows['HT12']=[(1,1,0,0,0,1,0,1,2,0,1,1)]
        model._rules_and_callbacks(rows,n.op(31,0,n.bits(1/60),1),0)
        v=list(rows['HT12'][0]);v[-1]=0;rows['HT12']=[tuple(v)]
        with self.assertRaises(ValueError):model._rules_and_callbacks(rows,n.op(31,0,n.bits(1/60),1),0)


class ParserDecisionD123(unittest.TestCase):
    def test_private64_has_real_dynamic_body_island_before_phase_refusal(self):
        for name in ('private-phase-64','private-phase-64-after-O'):
            probe=next(p for p in n.variants() if p.name==name)
            for decimal,data in enumerate((probe.c,probe.duckling)):
                rows=[line.split() for line in data.decode('ascii').splitlines() if line.startswith('O ')]
                self.assertEqual([int(r[2]) for r in rows][-3:],[56,90,64])
                create=rows[-2]
                self.assertEqual(int(create[6],10 if decimal else 16),2)
                self.assertEqual(probe.completed,len(rows)-1)
            self.assertEqual(probe.stderr,b'PORT12: INPUT_PHASE\n')

    def test_acceptance12a_N73_and_final_N161_are_separate_profiles(self):
        a={p.name:p for p in n.variants('12a')}
        final={p.name:p for p in n.variants('12c')}
        self.assertIn('PORT12-N-73',a)
        self.assertNotIn('PORT12-N-73',final)
        self.assertIn('PORT12-N-161',final)
        for probe in (a['PORT12-N-73'],final['PORT12-N-161']):
            self.assertEqual(probe.stderr,b'PORT12: INPUT_N_RANGE\n')
            self.assertEqual(probe.boundary,'header')


class ForcedSleepSplitHistory(unittest.TestCase):
    def test_SetAwake_false_splits_dirty_awake_island_before_sleep(self):
        fixture=SplitMarkHistoryControls()
        model,before=fixture.fixture()
        before['B']=[tuple((*v[:27],1,*v[28:])) for v in before['B']]
        model._mark_history(before,n.op(90),0);model.previous=before
        _,after=fixture.fixture(mark=1)
        after['TR11']=[(1,2,0,0,3,4,2,2,2,1,1)]
        model._mark_history(after,n.op(58,0,0,1,0),0)
        self.assertEqual(model.witnesses['split_mark_writes'],3)
        broken=copy.deepcopy(after);broken['TR11']=[]
        fresh,_=fixture.fixture();fresh.previous=before
        with self.assertRaises(ValueError):fresh._mark_history(broken,n.op(58,0,0,1,0),0)


class CallbackScheduleControls(unittest.TestCase):
    def fixture(self,creation=False,pre=False):
        model=m.OwnershipModel(diagnostic_only=True);rows=defaultdict(list);prior=defaultdict(list)
        model.regs['W'][0]={'live':True,'number':(0,1,2,0,0)}
        model.hook_values[0]=[2 if pre else 12,*([0]*12)]
        for reg in (0,1):
            shape=[0]*43;shape[:6]=[1,1,reg,reg+1,0,1]
            shape[8:10]=[1,2];shape[12:15]=[reg+1,0,1]
            prior['S'].append(tuple(shape))
            prior['P'].append((1,1,reg,*([0]*7),*map(n.bits,(-1,-1,1,1)),0))
            body=[0]*33;body[:6]=[1,1,reg,reg+1,0,1];body[27]=1;prior['B'].append(tuple(body))
            model.shape_values[reg]={'material':(n.bits(.25 if reg==0 else 1),0,0,0,3+2*reg,0),'flags':(0,0,int(pre))}
        sim=[0]*52;sim[0]=2;sim[3:5]=[0,1];sim[13]=0x200000 if pre else 0;sim[24]=int(pre)
        if creation:rows['RQ']=[(1,2,0,0,0,0,1,0,1,1,2,0,1)]
        else:prior['CS']=[(1,1,0,1,4,0,*sim)]
        rows['CS']=[(1,2,0,1,4,0,*sim)]
        if pre:
            before=(0x3f800000,0,0,1,*([0]*26))
            rows['HT12']=[(1,2,0,0,1,1,0,1,2,0,1,1,*before,*before)]
        else:
            rows['HT12']=[(1,2,0,i,k,n.bits(.25) if k==2 else 0,3,n.bits(1) if k==2 else 0,5,0)
                          for i,k in enumerate((2,3,2,3) if creation else (2,3))]
        model.previous=prior
        return model,rows

    def test_Create_and_Update_each_call_mix_once_in_order(self):
        for creation in (False,True):
            model,rows=self.fixture(creation)
            model._callback_schedule(rows,n.op(31,0,n.bits(1/60),1),0,True)
            for kind in ('missing','duplicate','reordered'):
                bad=copy.deepcopy(rows)
                if kind=='missing':bad['HT12'].pop()
                elif kind=='duplicate':bad['HT12'].append(bad['HT12'][-1])
                else:bad['HT12'][0],bad['HT12'][1]=bad['HT12'][1],bad['HT12'][0]
                for side in ('C','D'):
                    with self.subTest(creation=creation,kind=kind,side=side),self.assertRaises(ValueError):
                        model._callback_schedule(bad,n.op(31,0,n.bits(1/60),1),0,True)

    def test_cached_preSolve_flag_and_positive_manifold_require_one_callback(self):
        model,rows=self.fixture(pre=True)
        model._callback_schedule(rows,n.op(31,0,n.bits(1/60),1),0,True)
        for kind in ('missing','duplicate','wrong_pair','pause'):
            bad=copy.deepcopy(rows);operation=n.op(31,0,n.bits(1/60),1)
            if kind=='missing':bad['HT12']=[]
            elif kind=='duplicate':bad['HT12']*=2
            elif kind=='pause':operation=n.op(31,0,0,1)
            else:
                value=list(bad['HT12'][0]);value[5],value[8]=value[8],value[5];bad['HT12']=[tuple(value)]
            with self.subTest(kind=kind),self.assertRaises(ValueError):model._callback_schedule(bad,operation,0,True)

    def test_refusal_clears_operation_local_HT_but_preserves_world_settings(self):
        model,trace=self.fixture()
        model.previous=defaultdict(list,HT12=trace['HT12'],WS12=[(1,1,0,3,4,5)])
        rows=defaultdict(list,WS12=[(1,2,0,3,4,5)])
        operation=n.op(82,0,1,4,0)
        model._callback_schedule(rows,operation,5,True)
        model._atomic(rows,operation,5)
        bad=copy.deepcopy(rows);bad['WS12']=[(1,2,0,3,4,6)]
        with self.assertRaises(ValueError):model._atomic(bad,operation,5)
        bad=copy.deepcopy(rows);bad['HT12']=trace['HT12']
        with self.assertRaises(ValueError):model._callback_schedule(bad,operation,5,True)


class ContactTemporalPoolControls(unittest.TestCase):
    def cold(self,cid):
        h=[0]*20;h[:7]=[1,cid,2,0xffffffff,0,0,1];h[7]=0;h[10]=1
        return (1,1,0,cid,*h)

    def test_RQ_allocation_uses_LIFO_even_with_consistent_wrong_partition(self):
        model=m.OwnershipModel(diagnostic_only=True)
        model.previous=defaultdict(list,CP=[(1,1,0,4,2,2)],CF=[(1,1,0,0,2),(1,1,0,1,3)],
                                   CT=[self.cold(0),self.cold(1)])
        rows=defaultdict(list,CP=[(1,2,0,4,1,3)],CF=[(1,2,0,0,2)],
                             CT=[self.cold(0),self.cold(1),self.cold(3)],
                             RQ=[(1,2,0,0,0,0,1,0,1,1,3,0,1)])
        model._contact_pool_history(rows,n.op(42,0),0)
        bad=copy.deepcopy(rows);bad['CF']=[(1,2,0,0,3)]
        bad['CT']=[self.cold(0),self.cold(1),self.cold(2)]
        request=list(bad['RQ'][0]);request[10]=2;bad['RQ']=[tuple(request)]
        with self.assertRaises(ValueError):model._contact_pool_history(bad,n.op(42,0),0)

    def test_body_destruction_pushes_contact_ids_in_old_edge_order(self):
        model=m.OwnershipModel(diagnostic_only=True)
        body=[0]*33;body[:6]=[1,1,0,1,0,1]
        model.previous=defaultdict(list,CP=[(1,1,0,2,0,2)],CT=[self.cold(0),self.cold(1)],B=[tuple(body)],
                                   BL9=[(1,1,0,0,2,2,0,0xffffffff,0xffffffff,1,0,0,0)])
        rows=defaultdict(list,CP=[(1,2,0,2,2,0)],CF=[(1,2,0,0,1),(1,2,0,1,0)])
        model._contact_pool_history(rows,n.op(3,0,0),0)
        bad=copy.deepcopy(rows);bad['CF']=[(1,2,0,0,0),(1,2,0,1,1)]
        with self.assertRaises(ValueError):model._contact_pool_history(bad,n.op(3,0,0),0)


class FilterQueryScheduleControls(unittest.TestCase):
    def fixture(self):
        model,rows=CallbackScheduleControls().fixture()
        prior=model.previous
        model.hook_values[0]=[1,*([0]*12)];model.hook_modes[0]=[0]*4;model.rules[0]=[[],[],[],[]]
        third=list(prior['S'][1]);third[2]=2;third[3]=3;third[12]=3;prior['S'].append(tuple(third))
        body=list(prior['B'][1]);body[2]=2;body[3]=3;prior['B'].append(tuple(body))
        prior['B']=[tuple((*v[:12],2,*v[13:])) for v in prior['B']]
        model.shape_values[2]=copy.deepcopy(model.shape_values[1])
        for props in model.shape_values.values():props['filter']=(1,0,0xffffffff,0xffffffff,0)
        prior['T']=[(1,1,j,2,j,*map(n.bits,(-1,-1,1,1)),1,0,j,0) for j in range(3)]
        prior['U']=[(1,1,0,j,(j<<2)|2) for j in range(3)]
        h=[0]*20;h[:7]=[1,0,2,0xffffffff,0,0,1];prior['CT']=[(1,1,0,0,*h)]
        rows['RQ']=[(1,2,0,j,j,j,2,0,1,1,j+1,j,2) for j in (0,1)]
        rows['HT12']=[(1,2,0,j,0,j+1,0,1,3,0,1,1) for j in (0,1)]
        return model,rows

    def test_proxy_move_group_membership_and_count_are_independent_of_HT(self):
        model,rows=self.fixture()
        model._callback_schedule(rows,n.op(42,0),0,True)
        for kind in ('missing','duplicate','existing_pair','reordered_move'):
            bad=copy.deepcopy(rows)
            if kind=='missing':bad['HT12'].pop()
            elif kind=='duplicate':bad['HT12'].append(bad['HT12'][-1])
            elif kind=='reordered_move':bad['HT12'].reverse()
            else:
                v=list(bad['HT12'][0]);v[8]=2;bad['HT12'][0]=tuple(v)
            for side in ('C','D'):
                with self.subTest(kind=kind,side=side),self.assertRaises(ValueError):
                    model._callback_schedule(bad,n.op(42,0),0,True)


class FreshContactListControls(unittest.TestCase):
    def fixture(self,saving=False):
        model=m.OwnershipModel(diagnostic_only=True);rows=defaultdict(list)
        model.regs['W'][0]={'live':True,'number':(0,7,0,0,0)}
        model.regs['B'][0]={'live':True,'number':(0,10,0,7,0)}
        for j in range(3):model.regs['S'][j]={'live':True,'number':(j,11+j,0,7,0),'parent':(j,10+j,0,7,0)}
        model.known_shapes={v['number'] for v in model.regs['S'].values()}
        rows['BL9']=[(1,2,0,0,2,2,0,0xffffffff,0xffffffff,1,0,0,0)]
        values={}
        for cid in (0,1):
            c=[0]*20;c[:7]=[1,cid,2,cid,0,0,cid+1];c[16]=1;c[18]=20+cid
            rows['CT'].append((1,2,0,cid,*c))
            h=[0]*52;h[0]=cid;h[3:5]=[0,cid+1];h[21:25]=[0x3f800000,0,0,2]
            rows['CS'].append((1,2,0,1,cid,0,*h))
            number=(cid,20+cid,0,7,0);model.known_contacts.add(number)
            values[cid]=(*number,*model.regs['S'][0]['number'],*model.regs['S'][cid+1]['number'],1,*h[21:51])
        kind=2 if saving else 1
        rows['CL12']=[(1,2,kind,0,0,0,2)]
        rows['CV12']=[(1,2,kind,0,0,j,*values[cid]) for j,cid in enumerate((1,0))]
        return model,rows

    def test_fresh_88_and_K12_match_private_edge_order_numbers_and_both_points(self):
        for saving in (False,True):
            model,rows=self.fixture(saving)
            operation=n.op(89,1,0,0,0) if saving else n.op(88,0,1,0,0)
            model._copies(rows,operation,0,True)
            for kind in ('normal','second_point','order','missing'):
                bad=copy.deepcopy(rows);fresh,_=self.fixture(saving)
                if kind=='order':
                    a,b=bad['CV12'];bad['CV12']=[(*a[:6],*b[6:]),(*b[:6],*a[6:])]
                elif kind=='missing':
                    bad['CV12'].pop();v=list(bad['CL12'][0]);v[-1]-=1;bad['CL12']=[tuple(v)]
                else:
                    v=list(bad['CV12'][0]);v[6+16+(17 if kind=='second_point' else 0)]^=1;bad['CV12'][0]=tuple(v)
                for side in ('C','D'):
                    with self.subTest(saving=saving,kind=kind,side=side),self.assertRaises(ValueError):
                        fresh._copies(bad,operation,0,True)

    def test_raw_capacity_limits_values_but_game_returns_the_full_owned_list(self):
        model,rows=self.fixture()
        rows['CV12']=rows['CV12'][:1];rows['CL12']=[(1,2,1,0,0,0,1)]
        model._copies(rows,n.op(88,0,0,0,1),0,True)
        with self.assertRaises(ValueError):model._copies(rows,n.op(88,0,1,0,0),0,True)


class ContactCacheHistoryControls(unittest.TestCase):
    def fixture(self):
        model,rows=CallbackScheduleControls().fixture()
        prior=model.previous
        model.hook_values[0]=[0]*13;model.hook_modes[0]=[0]*4;model.rules[0]=[[],[],[],[]]
        model.regs['S']={j:{'live':True,'number':(j,10+j,0,1,2)} for j in (0,1)}
        old=list(prior['CS'][0]);old[6+9:6+13]=[n.bits(.5),0,0,0];old[6+51]=1
        prior['CS']=[tuple(old)];rows['CS']=[tuple(old)]
        c=[0]*20;c[:7]=[1,2,2,4,0,0,1]
        prior['CT']=rows['CT']=[(1,1,0,2,*c)]
        return model,rows

    def test_setter_does_not_refresh_cache_before_Update(self):
        model,rows=self.fixture();model.shape_values[0]['material']=(n.bits(4),0,0,0,3,0)
        model._contact_cache_history(rows,n.op(81,0,0,1,0,n.bits(4)),0,())
        bad=copy.deepcopy(rows);value=list(bad['CS'][0]);value[6+9]=n.bits(2);bad['CS']=[tuple(value)]
        with self.assertRaises(ValueError):model._contact_cache_history(bad,n.op(81,0,0,1,0,n.bits(4)),0,())

    def test_actual_Update_refreshes_mixing_and_defined_mask_only_then(self):
        model,rows=self.fixture();model.shape_values[0]['material']=(n.bits(4),0,0,0,3,0)
        v=list(rows['CS'][0]);v[6+9]=n.bits(2);rows['CS']=[tuple(v)]
        event=(('update',2,(0,1)),)
        model._contact_cache_history(rows,n.op(31,0,n.bits(1/60),1),0,event)
        for field in (9,10,12,51):
            bad=copy.deepcopy(rows);v=list(bad['CS'][0]);v[6+field]^=1;bad['CS']=[tuple(v)]
            with self.subTest(field=field),self.assertRaises(ValueError):model._contact_cache_history(bad,n.op(31,0,n.bits(1/60),1),0,event)

    def test_flag_changes_do_not_refresh_old_contact_or_preSolve_cache(self):
        model,rows=self.fixture();model.shape_values[0]['flags']=(1,1,1)
        model._contact_cache_history(rows,n.op(83,0,1,0,1,2,1),0,())
        bad=copy.deepcopy(rows);v=list(bad['CS'][0]);v[6+13]|=0x200000;bad['CS']=[tuple(v)]
        with self.assertRaises(ValueError):model._contact_cache_history(bad,n.op(83,0,1,0,1,2,1),0,())
        bad=copy.deepcopy(rows);v=list(bad['CT'][0]);v[4+16]|=4;bad['CT']=[tuple(v)]
        with self.assertRaises(ValueError):model._contact_cache_history(bad,n.op(83,0,1,0,1,0,1),0,())


class HitGenerationHistoryControls(unittest.TestCase):
    def fixture(self):
        model,rows=ContactCacheHistoryControls().fixture()
        model.world_values[0]=[0]*10;model.world_values[0][7]=n.bits(1)
        for j,item in model.regs['S'].items():
            item['raw']=(j+1,0,1);model.raw_shapes[(1|(2<<32),item['raw'])]=item['number']
        c=list(rows['CT'][0]);c[4+16]|=1;rows['CT']=[tuple(c)]
        h=list(rows['CS'][0]);h[6+13]|=0x100000;h[6+21:6+25]=[n.bits(1),0,0,2]
        for j in (0,1):
            at=6+25+13*j;h[at:at+2]=map(n.bits,(4+2*j,5+2*j));h[at+9]=n.bits(1);h[at+10]=n.bits(-2-j)
        rows['CS']=[tuple(h)];rows['M']=[(1,1,0,0,1,0,1)]
        rows['PK10']=[(1,1,0,0,0,0,2,0,1)]
        rows['HN10']=[(1,1,0,1)]
        rows['HR10']=[(1,1,0,0,1,0,1,2,0,1,*map(n.bits,(6,7,1,0,3)))]
        return model,rows

    def test_max_approach_strict_threshold_and_positive_total_impulse(self):
        model,rows=self.fixture();model._hit_history(rows,n.op(32,0,n.bits(1/60),1,0),0,True)
        for mode in ('equal_threshold','zero_total_impulse','equal_speed_keeps_first'):
            fresh,bad=self.fixture();h=list(bad['CS'][0])
            for j in (0,1):
                at=6+25+13*j
                if mode=='zero_total_impulse':h[at+9]=0
                else:h[at+10]=n.bits(-1 if mode=='equal_threshold' else -3)
            bad['CS']=[tuple(h)]
            if mode=='equal_speed_keeps_first':
                v=list(bad['HR10'][0]);v[10:12]=map(n.bits,(4,5));bad['HR10']=[tuple(v)]
            else:bad['HR10']=[];bad['HN10']=[(1,1,0,0)]
            fresh._hit_history(bad,n.op(32,0,n.bits(1/60),1,0),0,True)

    def test_missing_packet_or_hit_and_nonstep_clear_are_rejected_on_each_side(self):
        for mode in ('missing_hit','missing_packet','wrong_point','nonstep_clear'):
            for side in ('C','D'):
                model,rows=self.fixture();bad=copy.deepcopy(rows)
                if mode in ('missing_hit','missing_packet','nonstep_clear'):
                    bad['HR10']=[];bad['HN10']=[(1,1,0,0)]
                    if mode=='missing_packet':bad['PK10']=[]
                else:
                    v=list(bad['HR10'][0]);v[10]^=1;bad['HR10']=[tuple(v)]
                operation=n.op(32,0,n.bits(1/60),1,0)
                if mode=='nonstep_clear':
                    model._hit_history(rows,operation,0,True);operation=n.op(91,0,0,0,1)
                with self.subTest(mode=mode,side=side),self.assertRaises(ValueError):model._hit_history(bad,operation,0,True)

    def test_GE_GC_hit_counts_follow_HR_and_owned_hit_copy_mutation(self):
        model,rows=self.fixture()
        rows['EN9']=[(1,1,0,0,0,0,0,1)]
        rows['GE']=[(1,1,0,0,0,0,0,0,0,1)]
        model._events(rows,n.op(91,0,0,0,1),0,True)
        raw=rows['HR10'][0][4:]
        typed=(*model.regs['S'][0]['number'],*model.regs['S'][1]['number'],*raw[6:])
        saved=copy.deepcopy(rows)
        saved['GC']=[(1,2,0,0,0,0,0,0,0,1)]
        saved['HC10']=[(1,2,0,0,0,1)];saved['HG10']=[(1,2,0,0,0,*typed)]
        model._events(saved,n.op(49,0,0),0,True)
        mutated=copy.deepcopy(saved)
        mutated['GC']=[(1,3,0,p,0,0,0,0,0,2 if p==1 else 1) for p in (0,1,2)]
        mutated['HC10']=[(1,3,0,p,0,2 if p==1 else 1) for p in (0,1,2)]
        changed=list(typed);changed[1]^=1;changed[10]^=0x80000000
        mutated['HG10']=[(1,3,0,0,0,*typed),(1,3,0,1,0,*changed),
                         (1,3,0,1,1,*typed),(1,3,0,2,0,*typed)]
        model._events(mutated,n.op(50,0,1),0,True)
        broken=copy.deepcopy(mutated);v=list(broken['GC'][1]);v[-1]=1;broken['GC'][1]=tuple(v)
        with self.assertRaises(ValueError):model._events(broken,n.op(50,0,1),0,True)


class NamedDomainControls(unittest.TestCase):
    def test_named_domain_inputs_do_not_extend_main_or_accept_arbitrary_names(self):
        domain=load('test_zywy_domain','domena-zywy.py')
        self.assertEqual({name for name,ops in domain.fixtures()},domain.NAMES)
        with self.assertRaises(ValueError):domain.DomainPolicy('case117')
        self.assertFalse(m.OWNERSHIP_READY)
        for name,operations in domain.fixtures():
            self.assertLessEqual(len(operations),16)
            self.assertTrue(n.encode(operations).startswith(b'GUARD12 1\nG 1 0 0 '))
            self.assertTrue(all(len(row)==65 for row in operations))


class AdditionalPhaseSources(unittest.TestCase):
    def test_private_phase_sources_and_controls_are_separate_from_old_probes(self):
        old={p.name for p in n.variants()};additional=n.phase_variants()
        self.assertEqual(len(additional),16)
        self.assertFalse(old&{p.name for p in additional})
        seen=set()
        for probe in additional:
            def rows(data,decimal):
                return [tuple([int(v[2]),*(int(w,10 if decimal else 16) for w in v[3:])])
                        for line in data.decode('ascii').splitlines() if (v:=line.split(' '))[0]=='O']
            c=rows(probe.c,False);d=rows(probe.duckling,True)
            self.assertEqual(c,d);self.assertEqual(probe.completed,len(c)-1)
            self.assertEqual(probe.stderr,b'PORT12: INPUT_PHASE\n')
            seen.add(c[-1][0]);self.assertLessEqual(len(c),16)
            self.assertEqual(c[:-1],rows(probe.controls[0],False)[:-1])
            if c[-1][0] in (51,53):
                self.assertEqual(c[-2],n.op(46,0,0,1,0))
                self.assertIn(32,{r[0] for r in c[:-1]})
            if c[-1][0]==51:self.assertEqual(c[-1][3:7],(n.bits(1),0,0,1))
        self.assertEqual(seen,{41,42,43,44,45,51,52,53})


if __name__=='__main__':unittest.main()
