pass                                                                   
import importlib.util
from pathlib import Path
import unittest
import copy
import json
import tempfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controls13c_w3',HERE/'ci-lancuchy-oslony.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);m=c.m


class W3Controls(unittest.TestCase):
    def test_defined_circle_v_edit_does_not_match_the_suffix_of_uPrev(self):
        anchor='fun b2CollideChainSegmentAndCircle() { if (v <= 0.0f32) {} if (uPrev <= 0.0f32) {} }'
        recipe={'case':128,'replacement':anchor.replace('if (v <= 0.0f32)','if (v < 0.0f32)')}
        self.assertIsNotNone(c.defined_nonhelper_mutation13c(recipe,anchor))
        recipe['replacement']=anchor.replace('v <= 0.0f32','v < 0.0f32')
        self.assertIsNone(c.defined_nonhelper_mutation13c(recipe,anchor))

    def test_profile_envelopes_keep13b_and_guards_and_apply_frozen13c_bound(self):
        old=c.Runtime13B.__new__(c.Runtime13B);new=c.Runtime13C.__new__(c.Runtime13C)
        for profile in (b'PORT13B 64\n',b'GUARD13B 1\n',b'GUARD13C 1\n',b'COMPONENT13C 1\n'):
            self.assertEqual(new.output_limit(profile),old.output_limit(profile))
        self.assertEqual(new.output_limit(b'PORT13C 432\n'),104365340672)

    def test_witness_inputs_do_not_supply_or_rewrite_source_anchors(self):
        data=json.loads((HERE/'lancuchy-receptury-13c.json').read_text(encoding='utf-8'))
        self.assertEqual(set(data['witnesses13c']),{r['id'] for r in data['proposals']})
        for value in data['witnesses13c'].values():
            self.assertNotIn('anchor',value);self.assertNotIn('replacement',value);self.assertNotIn('source_sha256',value)
            self.assertIn(value['case'],(128,384,391))

    def test_circle_same_finite_damage_both_sides_rejected_for_each_result_word(self):
        a=c.direct_call13c();pred=m.circle_predicates13c(a)
        rows=[('E13C',(1,1,120,*a)),('A13',(1,1,0,0)),('KI13',(1,1,*a[36:43])),
              ('M13C',(1,1,*pred['manifold_H'])),('K13C',(1,1,*a[36:43])),('DC13',(1,1,1,1,1,1,1))]
        m.check_direct13c(rows,1,1,a)
        for slot in (0,1,4,5,6,7,8,9,10):
            bad=copy.deepcopy(rows);values=list(bad[3][1]);values[slot+2]^=1;bad[3]=(bad[3][0],tuple(values))
            for side in ('C','D'):
                with self.subTest(slot=slot,side=side),self.assertRaises(ValueError):m.check_direct13c(bad,1,1,a)

    def test_D5_maximal_operators_exclude_shifts_arrows_strings_and_comments(self):
        tokens=c.b.source_operators13('a << 16u32; b >> 16u32; a <= b; c >= d; a < b; c > d; fun f() -> i32; "x < y" # z > w\n')
        self.assertEqual([x['token'] for x in tokens if x['kind']=='comparison'],['<=','>=','<','>'])
        self.assertEqual([x['token'] for x in tokens if x['kind']=='shift'],['<<','>>'])

    def test_D5_all_historical_IDs_remain_as_aliases_of_actual_shift(self):
        graph=c.b.accounting_spec13b()
        self.assertTrue(set(graph['original_row_ids'])<=set(graph['relations']))
        for function,line,operator in (('b2StoreChainId',3394,'shift-left'),('b2LoadChainId',3396,'shift-right')):
            parent=f'K13b/swiat.dk/{function}/{line}'
            for number in (1,2):
                link=graph['relations'][parent+'/predicate'+str(number)]
                self.assertEqual(link['type'],'aggregate')
                self.assertEqual(link['components'],[parent+'/semantic/'+operator])
            self.assertEqual(len(graph['relations'][parent]['components']),9 if line==3394 else 8)
            self.assertTrue(all(graph['relations'][ident]['type']=='native_target' for ident in graph['relations'][parent]['components']))
            for field in ('index1','world0','generation'):
                for part in ('read','cast'):
                    self.assertIn(parent+'/semantic/'+field+'-'+part,graph['relations'][parent]['components'])

    def test_D5_missing13c_atom_cannot_silently_shrink_population(self):
        data=copy.deepcopy(c.b.accounting_spec13c());data['rows'].pop()
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'lancuchy-rozliczenie-13c.json').write_text(json.dumps(data),encoding='utf-8')
            with patch.object(c.b,'HERE',Path(folder)),self.assertRaisesRegex(ValueError,'changed'):
                c.b.accounting_spec13c()

    def test_D1_invalid_count_does_not_enable_relational_proxy_indices(self):
        for kind,counts in ((1,(0,1,3,8)),(2,(0,1,2,9,10))):
            for count in counts:
                a=list(c.direct_call13c(kind));a[18]=count;a[36:43]=(1,2,0,0,255,0,0)
                with self.subTest(kind=kind,count=count):
                    self.assertEqual(m.direct_status13c(tuple(a)),(4,84))
                for slot,value in ((36,4),(37,256),(40,256)):
                    bad=a.copy();bad[slot]=value
                    with self.subTest(kind=kind,count=count,physical_slot=slot):
                        self.assertEqual(m.direct_status13c(tuple(bad)),(5,82))
                bad=a.copy();bad[19]=0x7f800000
                self.assertEqual(m.direct_status13c(tuple(bad)),(5,0))

    def test_D1_valid_count_keeps_both_proxy_index_guards(self):
        for kind in (1,2):
            for index_slot,value in ((37,2),(40,2 if kind==1 else 4)):
                a=list(c.direct_call13c(kind));a[36]=1;a[index_slot]=value
                with self.subTest(kind=kind,slot=index_slot):
                    self.assertEqual(m.direct_status13c(tuple(a)),(5,82))
        a=list(c.direct_call13c());a[36:43]=(3,255,255,255,255,255,255)
        self.assertEqual(m.direct_status13c(tuple(a)),(0,0))


if __name__=='__main__':unittest.main()
