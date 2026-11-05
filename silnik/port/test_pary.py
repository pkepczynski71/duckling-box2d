from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                        
from collections import Counter
from dataclasses import replace
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
p=module('pair_comparison_tests','porownaj-pary.py');g=p.g

class FrozenInputs(unittest.TestCase):
    def test_all_448_ids_and_seven_families_are_explicit(self):
        rows=g.cases();self.assertEqual(len(rows),448)
        self.assertEqual([c.id for c in rows],list(range(1,449)))
        self.assertEqual(Counter(c.kind for c in rows),Counter({k:64 for k in range(7)}))
        for c in rows:
            self.assertEqual(len(c.a.words),44);self.assertEqual(len(c.b.words),44);g.validate_case(c)
        self.assertEqual(len({(c.kind,c.a,c.b) for c in rows}),448)
    def test_both_committed_transports_match_the_frozen_words_and_hashes(self):
        g.verify_input_hashes(HERE)
        for prefix,rows in (('przypadki',g.cases()),('proba',g.small_cases())):
            for dec,suffix in ((False,''),(True,'-stdin')):
                data=(HERE/(prefix+'-pary'+suffix+'.csv')).read_bytes()
                self.assertEqual(data,g.encode(rows,dec).encode('ascii'))
                parsed=g.read_input(data.decode('ascii'),dec)
                self.assertEqual([(c.id,c.kind,c.a,c.b) for c in parsed],[(c.id,c.kind,c.a,c.b) for c in rows])
    def test_input_line_endings_LF_CRLF_and_EOF(self):
        for dec in (False,True):
            text=g.encode(g.small_cases(),dec)
            for version in (text,text.replace('\n','\r\n'),text.rstrip('\n')):
                self.assertEqual(len(g.read_input(version,dec)),7)
    def test_frozen_speculation_bits_and_neighbours_reach_the_predicate(self):
        f=g.f32;target=g.bits(.02)
        for start in (0,64):
            for offset,expected in ((0,target-1),(1,target),(2,target+1)):
                c=g.cases()[start+offset]
                if start==0:
                    distance=g.number(c.b.words[5]);ra=g.number(c.a.words[8]);rb=g.number(c.b.words[6])
                    separation=f(f(distance-ra)-rb)
                else:
                    separation=g.number(c.b.words[4]);ra=g.number(c.a.words[5]);rb=g.number(c.b.words[6])
                                                                                 
                    separation=f(separation-f(ra+rb))
                self.assertEqual(g.bits(separation),expected,(c.id,c.name))
    def test_endpoint_equalities_are_not_nearby_values(self):
        for offset,endpoint in ((7,0),(8,1)):
            c=g.cases()[offset];a=c.a.words;b=c.b.words
            self.assertEqual(b[4],a[4+2*endpoint]);self.assertEqual(g.number(b[5]),g.f32(.1))
    def test_epsilon_vertex_region_has_the_right_separating_edge(self):
        for offset in range(3):
            c=g.cases()[71+offset];center=tuple(g.number(u) for u in c.b.words[4:6]);words=c.a.words
            v1=tuple(g.number(u) for u in words[8:10]);v2=tuple(g.number(u) for u in words[10:12])
            self.assertEqual(v1,(0.,-.25));self.assertEqual(v2,(0.,.25))
            separation=center[0];self.assertEqual(g.bits(separation),g.bits(g.EPS)+offset-1)
            u1=g.f32((center[1]-v1[1])*(v2[1]-v1[1]));self.assertLess(u1,0)
            self.assertLess(-.25-center[1],separation)
    def test_positive_length_limits_are_pair_specific(self):
        rows=g.cases();short=next(c for c in rows if c.kind==2 and c.name=='short-A')
        constructor=next(c for c in rows if c.kind==5 and c.name=='short-legal')
        da=g.number(short.a.words[6]);db=g.number(constructor.b.words[6])
        self.assertGreater(g.f32(da*da),g.f32(g.EPS*g.EPS));self.assertLess(g.f32(da*da),g.EPS)
        self.assertGreater(g.f32(db*db),g.EPS)
        for c,side in ((short,'a'),(constructor,'b')):
            s=getattr(c,side);w=list(s.words);w[6]=w[4];w[7]=w[5]
            with self.assertRaisesRegex(ValueError,'length'):g.validate_case(replace(c,**{side:replace(s,words=tuple(w))}))
    def test_capsule_parallel_and_f2_recalculation_predicates(self):
        f=g.f32
        def sub(a,b):return tuple(f(x-y) for x,y in zip(a,b))
        def dot(a,b):return f(f(a[0]*b[0])+f(a[1]*b[1]))
        def point(s,offset):return tuple(g.number(u) for u in s.words[offset:offset+2])
        def fractions(c):
            p1=point(c.a,4);q1=point(c.a,6);p2=point(c.b,4);q2=point(c.b,6)
            d1=sub(q1,p1);d2=sub(q2,p2);r=sub(p1,p2)
            dd1=dot(d1,d1);dd2=dot(d2,d2);d12=dot(d1,d2);rd1=dot(r,d1);rd2=dot(r,d2)
            denom=f(f(dd1*dd2)-f(d12*d12))
            f1=0. if denom==0 else max(0.,min(1.,f(f(f(d12*rd2)-f(rd1*dd2))/denom)))
            f2=f(f(f(d12*f1)+rd2)/dd2)
            corrected=f(-rd1/dd1) if f2<0 else f(f(d12-rd1)/dd1)
            return denom,f1,f2,max(0.,min(1.,corrected))
        rows=g.cases()
        self.assertEqual(fractions(rows[128])[0],0.)
        self.assertNotEqual(fractions(rows[129])[0],0.)
        negative=fractions(rows[130]);over=fractions(rows[131])
        self.assertLess(negative[2],0.);self.assertGreater(over[2],1.)
        self.assertNotEqual(negative[1],negative[3]);self.assertNotEqual(over[1],over[3])
    def test_capsule_lengths_remain_legal_after_the_actual_relative_transform(self):
                                                                           
                                                                                
        f=g.f32
        def add(a,b):return tuple(f(x+y) for x,y in zip(a,b))
        def sub(a,b):return tuple(f(x-y) for x,y in zip(a,b))
        def rot(q,v):return (f(f(q[0]*v[0])-f(q[1]*v[1])),f(f(q[1]*v[0])+f(q[0]*v[1])))
        def invrot(q,v):return (f(f(q[0]*v[0])+f(q[1]*v[1])),f(-f(q[1]*v[0])+f(q[0]*v[1])))
        def vec(s,i):return tuple(g.number(u) for u in s.words[i:i+2])
        def dd(v):return f(f(v[0]*v[0])+f(v[1]*v[1]))
        for case in g.cases():
            if case.kind not in (2,4):continue
            a,b=case.a,case.b;qa=vec(a,2);qb=vec(b,2);origin=vec(a,4)
            sfap=add(vec(a,0),rot(qa,origin))
            xfp=invrot(qa,sub(vec(b,0),sfap))
            xfq=(f(f(qa[0]*qb[0])+f(qa[1]*qb[1])),f(f(qa[0]*qb[1])-f(qa[1]*qb[0])))
            p2=add(rot(xfq,vec(b,4)),xfp);q2=add(rot(xfq,vec(b,6)),xfp)
            self.assertGreater(dd(sub(vec(a,6),origin)),f(g.EPS*g.EPS),case.id)
            self.assertGreater(dd(sub(q2,p2)),f(g.EPS*g.EPS),case.id)
    def test_polygon_vertex_witness_uses_the_mutated_first_vertex_branch(self):
        c=g.cases()[70]
        self.assertEqual(c.name,'v2');self.assertIn('vertex-1',c.witnesses)
        center=tuple(g.number(u) for u in c.b.words[4:6])
                                                                           
        self.assertGreater(center[1]-1,center[0]-1)
        self.assertLess(g.f32((center[0]-1)*-2),0)
    def test_SAT_bias_is_required_and_the_other_side_is_also_present(self):
        f=g.f32
        def sub(a,b):return tuple(f(x-y) for x,y in zip(a,b))
        def dot(a,b):return f(f(a[0]*b[0])+f(a[1]*b[1]))
        def xy(s,i):return tuple(g.number(u) for u in s.words[i:i+2])
        def separations(case):
            a0=xy(case.a,4);a1=xy(case.a,6);b0=xy(case.b,4);b1=xy(case.b,6)
            d=sub(b1,b0);inv=f(1/f(math.sqrt(dot(d,d))));n=(-f(d[1]*inv),f(d[0]*inv))
            sa=max(min(b0[1],b1[1]),min(-b0[1],-b1[1]))
            s0=dot(sub(a0,b0),n);s1=dot(sub(a1,b0),n)
            sb=max(min(s0,s1),min(-s0,-s1));return sa,sb
        sa,sb=separations(g.cases()[134]);bias=f(f(.1)*f(.005))
        self.assertLess(sa,sb);self.assertGreaterEqual(f(sa+bias),sb);self.assertLess(f(sa-bias),sb)
        sa,sb=separations(g.cases()[132]);self.assertLess(f(sa+bias),sb)
    def test_each_family_contains_named_required_witnesses(self):
        required={0:{'s1-negative','s2-negative','s1-zero','s2-zero','zero-normal','spec-equal'},
            1:{'edge-tie','vertex-1','vertex-2','epsilon-below','epsilon-equal','epsilon-above'},
            2:{'denom-zero','denom-nonzero','f2-negative','f2-over','fallback','bias-window','reference-B','id-0-1'},
            3:{'segment-radius-zero','two-sided'},4:{'segment-radius-zero','fallback','f2-negative','f2-over'},
            5:{'constructor-count','constructor-radius','positive-length-constructor','reference-edge','origin'},
            6:{'adapter-side','segment-radius-zero','positive-length-constructor','spec-equal'}}
        for kind,wanted in required.items():
            got={w for c in g.cases() if c.kind==kind for w in c.witnesses}
            self.assertLessEqual(wanted,got,kind)
    def test_contract_is_the_exact_accepted_source_and_is_inside_repository(self):
        plan=norm_text(HERE/'fixtures/norms/PLAN-9-ZRODLO-KONTRAKTU.json')
        exact=plan[plan.index('### KONTRAKT-9a\n'):plan.index('### Przypadki 9a\n')]
        contract=norm_text(HERE/'fixtures/norms/KONTRAKT-9A.json')
        self.assertEqual(contract[contract.index('### KONTRAKT-9a\n'):][:len(exact)],exact)
        supplement=norm_text(HERE/'fixtures/norms/KONTRAKT-9A-DOPOWIEDZENIE.json')
        self.assertIn(supplement,contract)

class ManifoldModel(unittest.TestCase):
    def test_full_thirty_word_index_table(self):
        self.assertEqual(len(p.FIELDS),30);self.assertEqual(p.FIELDS[15],'p0.id');self.assertEqual(p.FIELDS[29],'p1.persisted')
        self.assertEqual(len(p.E_FIELDS),92);self.assertEqual(p.E_FIELDS[47],'tagB')
        p.validate_manifold([0]*30,1)
    def test_every_float_field_rejects_infinity_and_NaN_in_both_equal_streams(self):
        for i in set(range(30))-p.INTEGER_FIELDS:
            for word in (0x7f800000,0xff800000,0x7fc00001):
                row=[0]*30;row[i]=word
                with self.assertRaisesRegex(ValueError,'NaN/Inf'):p.validate_manifold(row,7)
    def test_count_and_widths_for_both_points(self):
        for i,value in ((3,3),(15,65536),(28,65536),(16,2),(29,2)):
            row=[0]*30;row[i]=value
            with self.assertRaises(ValueError):p.validate_manifold(row,1)
    def test_zero_normal_and_signed_zero_are_valid(self):
        row=[0]*30;row[3]=1;row[0]=0x80000000;p.validate_manifold(row,1)
    def test_short_and_extra_manifolds_are_not_complete(self):
        for n in (0,29,31):
            with self.assertRaisesRegex(ValueError,'30 words'):p.validate_manifold([0]*n,1)

if __name__=='__main__':unittest.main()
