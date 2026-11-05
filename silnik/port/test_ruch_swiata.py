from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                 

                                                                             
                                                                 
   
from collections import Counter
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import importlib.util

HERE=Path(__file__).parent
def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
p=module('motion_comparison_test','porownaj-ruch-swiata.py');g=p.g

def fixture():
    f=g.bits;wh=(1,0,0,0x10000,0,0,0,1,0)
    handles={s:(s+1,0,1,1,s+1,1,0,s+2,0) for s in range(3)}
    rows=(g.world(gravity=(0,0)),g.body(),g.body(1),g.body(2),g.step(dt=.125,n=4),
          g.op(3,0,1),g.step(dt=.125,n=4,copy=1),g.g7.object_op(2,0,0x8000000100000000),
          g.op(37,0),g.op(1,0),g.op(37,1))
                                                                            
                                                                     
    ledger=(((),(),1,1,0,0,1,0,0),((0,),(0,),1,2,0,0,2,0,0),
            ((0,1),(0,1),1,3,0,0,2,1,0),((0,1,2),(0,1,2),1,4,0,0,2,2,0),
            ((0,1,2),(0,1,2),1,4,1,3,1,0,0),((0,2),(0,2),1,4,1,3,2,1,0),
            ((0,2),(0,2),1,4,2,2,1,0,0),((0,2),(0,2),1,4,2,2,2,0,0),
            ((0,2),(0,2),1,4,2,2,0,0,0),((),(),0,4,2,2,1,0,0),((),(),0,4,2,2,0,0,0))
    records=[('PORT8',(1,)),('CASE',(1,len(rows)))];saved=[];last_move={}
    for seq,(row,entry) in enumerate(zip(rows,ledger),1):
        live,dense,wl,last,steps,events,kind,slot,status=entry
        start=len(records)
        if row[0]==30:saved.append(row[1])
        payload=wh if kind==1 else handles[slot] if kind==2 else (0,)*9
        records += [('E',(1,seq,*row)),('R',(1,seq,0,status,kind,*payload)),('V',(1,seq,1,0,wl,wl))]
        records += [('V',(1,seq,2,s,int(s in live),int(s in live))) for s in saved]
        if wl:records += [('W',(1,seq,0,*wh[:5],1,0,0,0,f(400),len(live),0,len(live)))]
        for s in live:
            obj=(1,0,0x80000001) if seq>=8 and s==0 else (0,0,0)
            records += [('B',(1,seq,s,*handles[s],2,0,0,f(1),0,0,0,0,0,0,0,0,0,0,0,1,1,0,*obj))]
        for s in live:records += [('L',(1,seq,s,0)),('A',(1,seq,s,0,0,0,0))]
        if row[0]==32:
            records += [('K',(1,seq,0,f(.125),4,4,1,len(dense)))]
            for j,s in enumerate(dense):
                last_move[s]=j
                records += [('M',(1,seq,0,j,*handles[s][:3],0,0,f(1),0,0,0,0,0))]
        copy_slot=0 if seq in (5,9) else 1 if seq in (7,11) else None
        if copy_slot is not None:
            copied=(0,1,2) if copy_slot==0 else (0,2)
            records += [('MCN',(1,seq,copy_slot,len(copied)))]
            for j,s in enumerate(copied):records += [('MC',(1,seq,copy_slot,j,s,s+2,0,1,0,0,0,f(1),0,0,0,0,0))]
        for s in live:records += [('X',(1,seq,s,0,0,f(100000),0,0,0,f(1),0))]
        if wl:
            records += [('F',(1,seq,0,0,0,0,0,0)),('H',(1,seq,0,0,16,0,*([0]*48))),('H',(1,seq,0,1,32,0,*([0]*96)))]
        for s in live:
            records += [('Y',(1,seq,s,0,0,0,0,0,f(1),0,0,0,last_move.get(s,g.U32),2,dense.index(s),0,0,f(1),0,0))]
        if wl:
            records += [('DN',(1,seq,0,j,*handles[s][:3])) for j,s in enumerate(dense)]
            records += [('RT',(1,seq,0,t,g.U32,0,16,0,0,0,0,0,0,0,0)) for t in range(3)]
            records += [('JW',(1,seq,0,steps,0,f(32) if steps else 0,0,steps%2,events,0,0))]
        records += [('I8',(1,seq,len(live),0,0,wl,0,2*wl,len(live),len(dense),3*wl,wl))]
        counts=Counter(t for t,_ in records[start:])
        records += [('Z8',(1,seq,1,len(saved),0,wl,len(live),0,*(counts[t] for t in p.PUBLIC_COUNTS),last,0))]
    records += [('ENDCASE',(1,)),('END',(1,))]
    return (g.Case(1,'independent zero-mass awake ledger',rows),),''.join(p.format_record(t,v) for t,v in records)

def mutate(text,tag,field,value=None,seq=None):
    lines=text.splitlines(keepends=True)
    for j,line in enumerate(lines):
        t,v=p.parse_record(line)
        if t==tag and (seq is None or v[1]==seq):
            index=p.names_for(t,v).index(field);v=list(v);v[index]=v[index]^1 if value is None else value
            lines[j]=p.format_record(t,v);return ''.join(lines)
    raise AssertionError((tag,field,seq))

class Corpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=g.cases()
    def test_64_cases_48_long_600_steps(self):
        self.assertEqual([c.id for c in self.rows],list(range(1,65)))
        self.assertEqual(len({c.ops for c in self.rows}),64)
        for c in self.rows[:48]:
            self.assertEqual(sum(row[0] in (31,32) for row in c.ops),600)
            self.assertLessEqual(len(c.ops),800)
            self.assertEqual({row[3] for row in c.ops if row[0] in (31,32)},{(1,4,8)[(c.id-1)%3]})
        for c in self.rows[48:]:self.assertLessEqual(len(c.ops),64)
    def test_both_inputs_identical_u32(self):
        for rows in (self.rows,g.small_cases(),g.guard_cases()):
            for decimal in (False,True):
                actual=g.read_input(g.encode(rows,decimal),decimal,len(rows))
                self.assertEqual(tuple(c.ops for c in actual),tuple(c.ops for c in rows))
    def test_every_operation_validates(self):
        for c in (*self.rows,*g.small_cases(),*g.guard_cases()):
            for row in c.ops:g.validate_operation(row)
    def test_all_N_1_64_with_small_operations(self):
        for n in range(1,65):
            rows=tuple(replace(g.small_cases()[0],id=i) for i in range(1,n+1))
            self.assertEqual(len(g.read_input(g.encode(rows))),n)
    def test_generated_files_are_pinned(self):g.verify_input_hashes(HERE)
    def test_contract_source_verbatim_in_repository(self):
        source=norm_text(HERE/'fixtures/norms/PLAN-8-ZRODLO-KONTRAKTU.json')
        addition=norm_text(HERE/'fixtures/norms/KONTRAKT-8-DOPOWIEDZENIE.json')
        contract=norm_text(HERE/'fixtures/norms/KONTRAKT-8.json')
        self.assertIn(source,contract);self.assertIn(addition,contract)
        self.assertEqual(len(p.FIELDS['Z8'])+1,29)
    def test_forecast_limit_without_second_solver(self):
        forecast=p.measure(self.rows)
        self.assertLessEqual(forecast['obs1_bytes_upper_bound'],1900000000)
        self.assertEqual(forecast['operations'],sum(len(c.ops) for c in self.rows))
    def test_raw_negative_substeps_remain_u32(self):
        row=g.step(n=-2147483648,raw=True)
        self.assertEqual(row[3],0x80000000);g.validate_operation(row)
    def test_game_nonfinite_reaches_parameter_guard(self):
        for code,values in ((32,(0,0x7fc00001,4,0)),(34,(0,0,2,0x7f800000,0,0,0,1)),(35,(0,0,0xff800000,0,1)),(36,(0,0,0x7fc12345,1))):
            g.validate_operation(g.op(code,*values))
        with self.assertRaisesRegex(ValueError,'nonfinite'):g.validate_operation(g.op(36,0,0,0x7fc12345,0))

class Stream(unittest.TestCase):
    def setUp(self):self.rows,self.text=fixture()
    def reject(self,text):
        self.assertTrue(p.compare(text,text,self.rows),'identical corruption accepted')
    def test_independent_ledger_both_observations(self):
        counts=p.validate_output(io.StringIO(self.text),self.rows)
        self.assertEqual(counts['M'],5);self.assertEqual(counts['MC'],10)
        public=''.join(p.public_lines(io.StringIO(self.text)))
        p.validate_output(io.StringIO(public),self.rows,False)
        self.assertIsNone(p.first_difference(self.text,public,True))
    def test_missing_record(self):self.reject(self.text.replace(next(x for x in self.text.splitlines(True) if x.startswith('M ')),'',1))
    def test_duplicate_record(self):
        line=next(x for x in self.text.splitlines(True) if x.startswith('M '));self.reject(self.text.replace(line,line*2,1))
    def test_extra_record(self):self.reject(self.text+'END 1\n')
    def test_missing_frame(self):
        lines=[x for x in self.text.splitlines(True) if not (x.split()[0] not in ('PORT8','CASE','ENDCASE','END') and x.split()[2]=='5')];self.reject(''.join(lines))
    def test_reordered_frame(self):
        lines=self.text.splitlines(True);a=next(i for i,x in enumerate(lines) if x.startswith('E 1 5 '));b=next(i for i,x in enumerate(lines) if x.startswith('E 1 6 '));lines[a:b]=reversed(lines[a:b]);self.reject(''.join(lines))
    def test_reordered_moves(self):
        lines=self.text.splitlines(True);ix=[i for i,x in enumerate(lines) if x.startswith('M 1 5 ')];lines[ix[0]],lines[ix[1]]=lines[ix[1]],lines[ix[0]];self.reject(''.join(lines))
    def test_bad_move_raw(self):self.reject(mutate(self.text,'M','index1',seq=7))
    def test_bad_move_transform(self):self.reject(mutate(self.text,'M','rotation.c'))
    def test_bad_move_metadata_high(self):self.reject(mutate(self.text,'M','object.high'))
    def test_bad_move_sleep(self):self.reject(mutate(self.text,'M','fellAsleep'))
    def test_bad_copy_birth_high(self):self.reject(mutate(self.text,'MC','body.birth.high'))
    def test_bad_copy_owner(self):self.reject(mutate(self.text,'MC','body.owner.low'))
    def test_bad_copy_object_high(self):self.reject(mutate(self.text,'MC','object.high',seq=9))
    def test_copy_after_world_destruction(self):self.reject(mutate(self.text,'MC','position.x',seq=11))
    def test_bad_echo(self):self.reject(mutate(self.text,'E','a63'))
    def test_bad_K_count(self):self.reject(mutate(self.text,'K','moveCount'))
    def test_bad_K_effective(self):self.reject(mutate(self.text,'K','effectiveSubSteps'))
    def test_bad_Z8_count(self):self.reject(mutate(self.text,'Z8','nM',seq=5))
    def test_bad_I8_count(self):self.reject(mutate(self.text,'I8','nDN',seq=5))
    def test_bad_copy_count(self):self.reject(mutate(self.text,'MCN','count'))
    def test_bad_dense_order(self):self.reject(mutate(self.text,'DN','index1',seq=6))
    def test_bad_localIndex(self):self.reject(mutate(self.text,'Y','localIndex',seq=6))
    def test_bad_stepIndex(self):self.reject(mutate(self.text,'JW','stepIndex.low',seq=5))
    def test_bad_inv_h(self):self.reject(mutate(self.text,'JW','inv_h',seq=5))
    def test_bad_force_reset(self):self.reject(mutate(self.text,'Y','force.x',seq=5))
    def test_bad_sim_cap_reset(self):self.reject(mutate(self.text,'Y','sim.isSpeedCapped',seq=5))
    def test_bad_body_cap_on_zero_motion(self):self.reject(mutate(self.text,'Y','body.isSpeedCapped',seq=5))
    def test_noncanonical_hex(self):self.reject(self.text.replace('00010000','0001000A',1))
    def test_noncanonical_decimal(self):self.reject(self.text.replace('E 1 1 ','E 01 1 ',1))
    def test_over_u32(self):self.reject(self.text.replace('00010000','100000000',1))
    def test_missing_END(self):self.reject(self.text[:-6])
    def test_EOF_mid_word(self):self.reject(self.text[:len(self.text)//2])
    def test_nonzero_process_status(self):self.assertTrue(p.compare(self.text,self.text,self.rows,d_code=124))
    def test_first_difference_names_field(self):
        diff=p.first_difference(self.text,mutate(self.text,'MC','body.birth.high',seq=9))
        self.assertIn('id 1, seq 9',diff);self.assertIn('record MC',diff);self.assertIn('body.birth.high',diff)
    def test_no_bulk_read(self):
        class Streaming(io.StringIO):
            def read(self,n=-1):
                if n<0:raise AssertionError('unbounded read')
                return super().read(n)
            def readline(self,n=-1):
                if n<0:raise AssertionError('unbounded line read')
                return super().readline(n)
        p.validate_output(Streaming(self.text),self.rows)
        self.assertIsNone(p.first_difference(Streaming(self.text),Streaming(self.text)))
    def test_overlong_line_rejected_with_bounded_read(self):
        self.reject('PORT8 1'+(' '*100000)+'\n')

class GameReads(unittest.TestCase):
    def setUp(self):
                                                                             
        self.m=p.Life();self.w=self.m.create_world(0,g.world()[1:]);self.b=self.m.create_body(0,self.w,g.body()[1:])
        self.s0=self.m.create_shape(0,self.b,g.shape()[1:]);self.s1=self.m.create_shape(1,self.b,g.shape(1)[1:])
        self.h0=(1,0,1,1,1,1,0,3,0);self.h1=(2,0,1,1,2,1,0,4,0)
        self.records=[]
        for phase,values in ((0,(self.h1,self.h0)),(1,(self.h0,self.h1,self.h1)),(2,(self.h1,self.h0))):
            self.records.append(('QGN',(1,1,phase,len(values))))
            self.records.extend(('QG',(1,1,phase,j,*h)) for j,h in enumerate(values))
        self.text=''.join(p.format_record(t,v) for t,v in self.records)
    def check_shapes(self,text):
        self.m.outcome={'status':0,'target':self.b}
        reader=p.Reader(text)
        p.public8(self.m,reader,1,1,{1:[(0,self.w)],2:[(0,self.b)],3:[(0,self.s0),(1,self.s1)]},{},{},{},g.op(38,0,0,1))
        reader.end()
    def test_actual_change_then_new_read_unchanged(self):self.check_shapes(self.text)
    def test_phase1_no_actual_change_rejected(self):
        broken=self.text.replace(p.format_record('QGN',(1,1,1,3)),p.format_record('QGN',(1,1,1,2)))
        with self.assertRaisesRegex(p.Invalid,'QGN.*count'):self.check_shapes(broken)
    def test_phase2_leaks_mutated_copy_rejected(self):
        bad=self.text.replace(p.format_record('QG',(1,1,2,0,*self.h1)),p.format_record('QG',(1,1,2,0,*self.h0)))
        with self.assertRaisesRegex(p.Invalid,'QG.*index1'):self.check_shapes(bad)
    def test_shape_ticket_high_is_not_dropped(self):
        bad=mutate(self.text,'QG','owner.high')
        with self.assertRaisesRegex(p.Invalid,'owner.high'):self.check_shapes(bad)
    def test_parent_is_actual_body_ticket(self):
        self.m.outcome={'status':0,'target':self.s1}
        bh=(1,0,1,1,1,1,0,2,0)
        text=p.format_record('SB',(1,1,0,1,*bh));sv=(1,1,1,*self.h1,*bh[:3])
        p.public8(self.m,p.Reader(text),1,1,{3:[(1,self.s1)]},{},{1:sv},{},g.op(39,0,1))
        with self.assertRaisesRegex(p.Invalid,'SB.*birth.high'):
            p.public8(self.m,p.Reader(mutate(text,'SB','birth.high')),1,1,{3:[(1,self.s1)]},{},{1:sv},{},g.op(39,0,1))
    def test_refused_reads_return_no_numbers(self):
        self.m.outcome={'status':2,'target':self.b}
        p.public8(self.m,p.Reader(p.format_record('QGN',(1,1,0,0))),1,1,{}, {},{},{},g.op(38,0,0,1))
        self.m.outcome={'status':1,'target':self.s1}
        p.public8(self.m,p.Reader(p.format_record('SB',(1,1,1,0,*([0]*9)))),1,1,{}, {},{},{},g.op(39,0,1))

if __name__=='__main__':unittest.main()
