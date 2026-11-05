pass                                                                           
import copy
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controls13c',HERE/'ci-lancuchy-oslony.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);m=c.m


def literal(a=None):
    a=tuple(a or c.direct_call13c())
    manifold=(0,m.bits(1.),0,1,*((0,)*26))
    return [('E13C',(1,1,120,*a)),('A13',(1,1,0,0)),('KI13',(1,1,*a[36:43])),
            ('M13C',(1,1,*manifold)),('K13C',(1,1,*a[36:43])),('DC13',(1,1,1,1,1,1,1))]


class Controls13c(unittest.TestCase):
    def test_audit_does_not_credit_unreached_else_if_from_computed_u(self):
        import tempfile
        from types import SimpleNamespace
        a=list(c.direct_call13c());a[20:22]=(m.bits(2.),m.bits(.25))
        pred=m.circle_predicates13c(tuple(a))
        self.assertIn('u',pred['values_H']);self.assertNotIn('circle/u<=0',pred['reached'])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'silnik/fizyka/swiat.dk';source.parent.mkdir(parents=True)
            source.write_text('fun b2CollideChainSegmentAndCircle() { offset < 0.0f32; v <= 0.0f32; u <= 0.0f32; }\nfun b2CollideChainSegmentAndPolygon() {}\n',encoding='utf-8')
            audit=c.b.predicate_audit13c([SimpleNamespace(id=1,ops=[{'a':tuple(a)}])],root)
        self.assertEqual(sum(audit['sites']['u']['reached_counts'].values()),0)
        self.assertEqual(sum(audit['sites']['v']['reached_counts'].values()),1)

    def test_each_scene_requires600_or1200_even_with_equal_global_sum(self):
        full={'positive_steps':32400,'cases':[
            {'id':i,'streams':{s:{'positive_steps':0 if i<=384 else 1200 if 421<=i<=426 else 600}
                              for s in ('c0','c1','d')}} for i in range(1,433)]}
        self.assertTrue(c.validate_population13c(full))
        for ident in (385,421):
            changed=copy.deepcopy(full)
            for side in ('c0','c1','d'):
                changed['cases'][ident-1]['streams'][side]['positive_steps']-=1
                changed['cases'][431]['streams'][side]['positive_steps']+=1
            with self.assertRaises(ValueError):c.validate_population13c(changed)

    def test_guard_prefix_changes_only_header_and_preserves_BASE12_geometry(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'prefix'
            path.write_bytes(b'PORT13C 1\nG 1 0 0 3\nCASE 1 3\nG 1 3 0 00000003 00000002\nENDCASE 1\nEND 1\n')
            result=b''.join(c.negative_prefix_lines13c(path,{'ident':1,'count':4,'drop_endcase':True}))
            self.assertEqual(result,b'PORT13C 1\nG 1 0 0 4\nCASE 1 4\nG 1 3 0 00000003 00000002\n')

    def test_literal_circle_front_and_back(self):
        a=c.direct_call13c();self.assertEqual(m.check_direct13c(literal(a),1,1,a)['pointCount'],1)
        a=list(a);a[21]=m.bits(-2.);a=tuple(a)
        rows=literal(a);rows[3]=('M13C',(1,1,*((0,)*30)))
        self.assertEqual(m.check_direct13c(rows,1,1,a)['predicates']['region'],'back')

    def test_all22_frozen_keys_and_control_not_kill(self):
        rows=c.guard_definitions13c();self.assertEqual(len(rows),22)
        self.assertEqual([x['id'] for x in rows if x['control_only']],['GD-CAPSULE-POINT'])
        self.assertEqual(sum(x['counted_as_kill'] for x in rows),21)
        self.assertEqual(next(x for x in rows if x['id']=='GD-CAPSULE-ABOVE-EPSILON')['status'],0)

    def test_capsule_length_exact_neighbors(self):
        rows={r['id']:r for r in c.guard_definitions13c()}
        for name,wanted,status in (('BELOW',0x33ffffff,4),('EQUAL',0x34000000,4),('ABOVE',0x34000001,0)):
            a=rows['GD-CAPSULE-'+name+'-EPSILON']['a'];d=m.vsub13c(tuple(map(m.number,a[22:24])),tuple(map(m.number,a[20:22])))
            self.assertEqual(m.bits(m.dot13c(d,d)),wanted);self.assertEqual(m.direct_status13c(a)[0],status)

    def test_direct_priority_and_circle_active_indices(self):
        a=list(c.direct_call13c());a[36:43]=(3,255,254,253,252,251,250)
        self.assertEqual(m.direct_status13c(tuple(a)),(0,0))
        a[0]=1;a[18]=0
        self.assertEqual(m.direct_status13c(tuple(a)),(4,84))
        a[19]=0x7f800000
        self.assertEqual(m.direct_status13c(tuple(a)),(5,0))

    def test_both_rotations_each_norm_and_position(self):
        for start in (10,14):
            for field,value in ((0,0x7f800000),(1,0x7fc00000),(2,0),(2,m.bits(2.))):
                a=list(c.direct_call13c());a[start+field]=value
                self.assertEqual(m.direct_status13c(tuple(a)),(5,0))

    def test_identical_damage_both_sides_fails_before_comparison(self):
        a=c.direct_call13c();rows=literal(a)
        damages=[('missing',lambda x:x.pop(2)),('duplicate',lambda x:x.insert(2,x[2])),
                 ('order',lambda x:x.__setitem__(slice(2,4),x[2:4][::-1])),
                 ('count',lambda x:x.__setitem__(-1,('DC13',(1,1,1,1,0,1,1)))),
                 ('empty-M',lambda x:x.__setitem__(3,('M13C',(1,1,*((0,)*30))))),
                 ('point-count',lambda x:x.__setitem__(3,('M13C',(1,1,0,m.bits(1.),0,2,*((0,)*26))))),
                 ('id',lambda x:x.__setitem__(3,('M13C',(*x[3][1][:17],1,*x[3][1][18:]))))]
        for name,damage in damages:
            for side in ('C','D'):
                with self.subTest(name=name,side=side):
                    changed=copy.deepcopy(rows);damage(changed)
                    with self.assertRaises(ValueError):m.check_direct13c(changed,1,1,a)

    def test_all7_KI_and_outgoing_cache_corruptions(self):
        a=list(c.direct_call13c());a[36:43]=(3,0,1,2,2,1,0);a=tuple(a)
        for slot in range(7):
            for at in (2,4):
                rows=literal(a);v=list(rows[at][1]);v[slot+2]^=1;rows[at]=(rows[at][0],tuple(v))
                with self.subTest(slot=slot,tag=rows[at][0]),self.assertRaises(ValueError):m.check_direct13c(rows,1,1,a)

    def test_warm_uses_own_previous_all7(self):
        a=list(c.direct_call13c());history=(3,0,1,2,2,1,0);rows=literal()
        rows=[(tag,(1,2,*v[2:])) for tag,v in rows]
        for at in (2,4):rows[at]=(rows[at][0],(1,2,*history))
        self.assertEqual(m.check_direct13c(rows,1,2,tuple(a),history=history,warm=True)['cache'],history)
        with self.assertRaises(ValueError):m.check_direct13c(rows,1,2,tuple(a),history=(0,)*7,warm=True)

    def test_refusal_has_no_new_result_and_preserves_history(self):
        a=list(c.direct_call13c());a[36]=4;a=tuple(a)
        rows=[('E13C',(1,1,120,*a)),('A13',(1,1,5,82)),('DC13',(1,1,1,1,0,0,0))]
        self.assertEqual(m.check_direct13c(rows,1,1,a)['cache'],a[36:43])
        for tag,values in literal()[2:5]:
            bad=rows[:-1]+[(tag,values)]+rows[-1:]
            with self.assertRaises(ValueError):m.check_direct13c(bad,1,1,a)

    def test_parser_arity_word_and_final_LF(self):
        raw='M13C 1 1 '+' '.join(['00000000']*30)+'\n'
        self.assertEqual(len(m.parse13c(raw)[1]),32)
        for bad in (raw[:-1],raw.replace(' ','  ',1),raw.replace('00000000','0000000A',1),raw+'\n',raw.replace(' 00000000','',1)):
            with self.assertRaises(ValueError):m.parse13c(bad)

    def test_every_direct_tag_parses_before_any_comparison(self):
        for tag,values in literal():
            prefix=3 if tag=='E13C' else 2
            raw=tag+' '+' '.join(str(x) if j<prefix else f'{x:08x}' for j,x in enumerate(values))+'\n'
            self.assertEqual(m.parse13c(raw),(tag,values))

    def test_full_ownership_debt_preserved(self):
        self.assertIs(m.Model13C.full_ownership_ready,False)

    def test_scene_requires_crossing_sleep_wake_ends_and_all_child_routes(self):
        scene={'crossings':{(0.,1),(4.,1),(0.,-1),(4.,-1)},'contact_bodies':{1,2,3},
            'cache_nonzero':True,'cache_changed':True,'loop79to0':True,'B_survives':True,
            'sleep':True,'wake_destroy':True,'end_destroy':True,
            'refusals':{('type',1),('type',2),(18,0),(19,0)}|{(81,j) for j in range(9)},
            'category63':True,'groups':{0xffffffff,1},'hooks':{0,1}}
        for family in range(1,9):self.assertTrue(m.validate_scene13c(family,scene))
        for family,key in ((1,'crossings'),(2,'cache_nonzero'),(2,'cache_changed'),(3,'contact_bodies'),
                           (4,'loop79to0'),(5,'B_survives'),(7,'sleep'),(7,'wake_destroy'),(7,'end_destroy'),
                           (8,'refusals'),(8,'category63'),(8,'groups'),(8,'hooks')):
            changed=copy.deepcopy(scene);changed[key]=set() if isinstance(scene[key],set) else False
            with self.subTest(family=family,key=key),self.assertRaises(ValueError):m.validate_scene13c(family,changed)

    def test_matrix_denominator_all_classes_and_source_mismatch_fail(self):
        spec=c.b.accounting_spec13c();ledger=c.b.table13c(product_root=HERE.parents[1])
        self.assertEqual(len(ledger['rows']),len(spec['rows']))
        self.assertTrue(ledger['denominator_independent_of_git'])
        self.assertEqual({x['accounting_type'] for x in ledger['rows']},{'native_target','control_trial','aggregate','equivalence_proof'})
        self.assertEqual(len(ledger['unresolved_class_mappings']),65)
        self.assertFalse(ledger['matrix_complete_after_final_K'])

    def test_native_receipt_cannot_be_empty_or_wrong_owner(self):
        target=next(r for r in c.b.accounting_spec13c()['rows'] if r['type']=='native_target')
        receipt={'id':'fake','requirement':target['id'],'native_executed':True,'detected':True,'clean':True}
        ledger=c.b.table13c([receipt],product_root=HERE.parents[1])
        self.assertFalse(next(r['verified'] for r in ledger['rows'] if r['id']==target['id']))
        self.assertEqual(len(ledger['rejected_receipts']),1)

    def test_F13_complete_and_each_profile_within_256(self):
        rows=c.negative_definitions13c()
        frozen=__import__('json').loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))['parserOdmowy']
        self.assertEqual(set(frozen),{r['error'] for r in rows})
        self.assertEqual(len(rows),len({r['name'] for r in rows}))
        for profile in ('DIRECT','PUBLIC','GUARD','COMPONENT'):
            self.assertLessEqual(sum(r['profile']==profile for r in rows),256)
        self.assertTrue(any(r['name']=='PUBLIC/late-case-INPUT_ID' for r in rows))
        self.assertTrue(any(r['name']=='GUARD/second-G' and r['error']=='INPUT_TRAILING_DATA' for r in rows))

    def test_mutation_intentions_are_nonempty_unique_and_unbound(self):
        rows=c.b.mutation_proposals13c()
        self.assertTrue(rows);self.assertEqual(len(rows),len({r['id'] for r in rows}))
        self.assertTrue(all(r['status']=='PROPOSAL_UNBOUND_UNEXECUTED' and r['anchor_owner']=='T-13c-2a' for r in rows))


if __name__=='__main__':unittest.main()
