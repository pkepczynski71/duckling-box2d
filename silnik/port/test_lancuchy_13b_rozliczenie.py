pass                                                                          

                                                                              
                                                                
   
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('chain13b_accounting_controls',HERE/'ci-lancuchy-oslony.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
b=c.b


class Accounting13bControls(unittest.TestCase):
    def setUp(self):
        self.graph=b.accounting_spec13b()
        self.guards=c.guard_definitions13b()

    def native(self,ident):
        link=self.graph['receipt_links'][ident]
        def run(side):return {'code':0,'stderr_bytes':0,'stdout_bytes':100,
                              'binary_sha256':'0'*64,'input_sha256':link['input_sha256'][side]}
        return {'id':ident,'requirement':link['owner_requirement'],'anchor_owner':'T-13b-2a',
                'native_executed':True,'baseline_ok':True,'single_hit':True,'clean':True,'detected':True,
                'port':link['port'],'product_sha256':link['mutant_sha256'],
                'build':{'code':0},'run':run('D'),'baseline_C':run('C'),'baseline_D':run('D'),
                'difference':{'line':1,'baseline':'stand baseline','actual':'stand mutant'}}

    def control(self,ident):
        return {'id':ident,'ok':True,'control_only':True,'sides':{side:{'ok':True,
            'run':{'code':0,'stderr_bytes':0,'stdout_bytes':100,'binary_sha256':'0'*64,
                   'input_sha256':self.graph['control_inputs'][ident][side]},
            'model':{'END_EOF':True,'sha256':'1'*64}} for side in ('C','D')}}

    def table(self,receipts=(),**kw):return b.table13b(self.guards,receipts,**kw)

    def test_all_old_obligations_remain_and_empty_evidence_is_red(self):
        t=self.table();ids={r['id'] for r in t['rows']}
        self.assertEqual(len(self.graph['original_row_ids']),775)
        self.assertTrue(set(self.graph['original_row_ids'])<=ids)
        self.assertEqual(t['verified'],0);self.assertEqual(t['code'],1)
        self.assertEqual(set(t['accounting_types']),{'native_target','equivalence_proof','control_trial','aggregate'})
        self.assertFalse(t['matrix_complete_after_final_K'])

    def test_git_cannot_change_the_real_denominator(self):
        expected=self.table()['required']
        with patch.object(b.subprocess,'check_output',side_effect=AssertionError('Git must not be called')):
            self.assertEqual(self.table()['required'],expected)
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);p=root/'silnik/fizyka';p.mkdir(parents=True)
                (p/'gra.dk').write_text('fun chainOnSegment(a: f32) -> bool = { return a >= 0.0f32; }\n')
                (p/'swiat.dk').write_text('')
                t=self.table(product_root=root)
                self.assertEqual(t['required'],expected);self.assertEqual(t['code'],1)

    def test_exact_five_controls_are_not_native_kills(self):
        expected={'GB4-GHOST-X','GB4-GHOST-Y','GB4-LOOP-REPEAT','GB4-DERIVED-ORIENT','GB5-ADJACENT'}
        controls=[self.control(k) for k in expected]
        t=self.table(controls=controls);rows={r['id']:r for r in t['rows']}
        self.assertEqual({r['id'] for r in t['rows'] if r['accounting_type']=='control_trial'},expected)
        for ident in expected:
            self.assertTrue(rows[ident]['verified']);self.assertFalse(rows[ident]['counted_as_kill'])
            self.assertTrue(rows[ident]['accounting']['citation']['quote'])
        self.assertFalse(any(r['verified'] for r in t['rows'] if r['accounting_type']=='native_target'))

    def test_control_needs_both_native_parsers_and_the_frozen_rotation(self):
        good=self.control('GB5-ADJACENT')
        for side in ('C','D'):
            bad=copy.deepcopy(good);bad['sides'][side]['run']['input_sha256']='2'*64
            row=next(r for r in self.table(controls=[bad])['rows'] if r['id']==good['id'])
            self.assertFalse(row['verified'])
        bad=copy.deepcopy(good);bad['sides']['D']['run']['code']=139
        self.assertFalse(next(r for r in self.table(controls=[bad])['rows'] if r['id']==good['id'])['verified'])

    def test_same_ghost_operand_proves_named_goal_but_not_its_siblings(self):
        receipt=self.native('13b/loop-main-ghost1');t=self.table([receipt]);rows={r['id']:r for r in t['rows']}
        self.assertTrue(rows['loop-main/ghost1']['verified'])
        self.assertFalse(rows['loop-main/point1']['verified']);self.assertFalse(rows['loop-main/ghost2']['verified'])
        parent=rows['K13b/swiat.dk/b2CreateChain/3422']
        self.assertEqual(parent['accounting_type'],'aggregate');self.assertFalse(parent['verified'])
        self.assertTrue(rows['loop-main/ghost1']['evidence_refs'][0]['rotation'])

    def test_aggregate_requires_every_actual_operand(self):
        both=[self.native('13b/shared-scalar-finite'),self.native('13b/shared-scalar-sign')]
        ident='K13b/gra.dk/validNonnegative/1287'
        self.assertTrue(next(r for r in self.table(both)['rows'] if r['id']==ident)['verified'])
        self.assertFalse(next(r for r in self.table(both[:1])['rows'] if r['id']==ident)['verified'])
        self.assertFalse(next(r for r in self.table(both[1:])['rows'] if r['id']==ident)['verified'])

    def test_compound_deletion_does_not_prove_independent_comparators(self):
        t=self.table([self.native('13b/material-count')]);rows={r['id']:r for r in t['rows']}
        self.assertFalse(rows['K13b/gra.dk/validateChainDescription/167']['verified'])
        self.assertTrue(t['rejected_atomic_credits'])

    def test_return_constant_does_not_prove_the_index_zero_operand(self):
        t=self.table([self.native('13b/raw-friction-getter0')]);rows={r['id']:r for r in t['rows']}
        self.assertTrue(rows['K13b/swiat.dk/b2Chain_GetFriction/3520']['verified'])
        self.assertFalse(rows['set/friction/getter0']['verified'])

    def test_other_field_or_unreached_rotation_cannot_borrow_a_receipt(self):
        good=self.native('13b/loop-main-ghost1')
        for field,value in [('product_sha256','3'*64),('requirement','loop-main/point1'),('port','silnik/fizyka/swiat.dk:3430')]:
            bad=copy.deepcopy(good);bad[field]=value
            self.assertEqual(self.table([bad])['verified'],0)
        bad=copy.deepcopy(good);bad['run']['input_sha256']='4'*64
        self.assertEqual(self.table([bad])['verified'],0)

    def test_failed_build_crash_timeout_and_equal_window_are_not_kills(self):
        good=self.native('13b/loop-main-ghost1')
        variants=[]
        bad=copy.deepcopy(good);bad['build']['code']=1;variants.append(bad)
        bad=copy.deepcopy(good);bad['run']['code']=139;variants.append(bad)
        bad=copy.deepcopy(good);bad['run']['code']=124;variants.append(bad)
        bad=copy.deepcopy(good);bad['difference']['actual']=bad['difference']['baseline'];variants.append(bad)
        for bad in variants:self.assertEqual(self.table([bad])['verified'],0)

    def test_equivalence_description_without_measured_baseline_is_red(self):
        proof={'id':'point-finite','proof':'description','conditions_present':True,'native_baseline_verified':True,
               'counted_as_kill':False,'source':'silnik/fizyka/gra.dk','source_sha256':self.graph['sources']['silnik/fizyka/gra.dk']}
        t=self.table(equivalences=[proof])
        self.assertFalse(any(r['verified'] for r in t['rows'] if r['accounting_type']=='equivalence_proof'))

    def test_missing_or_changed_population_cannot_disappear(self):
        with tempfile.TemporaryDirectory() as folder:
            data=copy.deepcopy(self.graph);data['relations']['K13b/swiat.dk/b2CreateChain/3422']['components'].pop()
            Path(folder,'lancuchy-rozliczenie-13b.json').write_text(json.dumps(data),encoding='utf-8')
            with patch.object(b,'HERE',Path(folder)),self.assertRaisesRegex(ValueError,'changed'):
                b.accounting_spec13b()

    def test_model12_debt_is_separate_from_every_native13b_goal(self):
        t=self.table();self.assertEqual(len(t['inherited_dependencies']),5)
        self.assertTrue(all(r['inherited_model12'] for r in t['inherited_dependencies']))
        self.assertTrue(all(not r['inherited_model12'] for r in t['remaining_native_targets']))
        self.assertFalse(t['full_ownership_ready'])

    def test_real_pilot_receipts_keep_their_author_and_exact_field(self):
        carried=self.graph['carried_receipts']
        self.assertEqual(len(carried),2)
        self.assertTrue(all(r['native_authority']=='ZAKRES-13b-pilot' and r['anchor_owner'] is None for r in carried))
        rows={r['id']:r for r in self.table(carried)['rows']}
        self.assertTrue(rows['loop-tail1/point1']['verified'])
        self.assertFalse(rows['loop-tail1/point2']['verified'])
        self.assertTrue(rows['K13b/swiat.dk/b2Chain_SetFriction/3516/assignment1']['verified'])
        self.assertFalse(rows['K13b/swiat.dk/b2Chain_SetFriction/3516/assignment2']['verified'])
        bad=copy.deepcopy(carried[0]);bad['citation']['sha256']='5'*64
        self.assertEqual(self.table([bad])['verified'],0)

    def test_accounting_data_cannot_be_used_as_mutation_bindings(self):
        self.assertTrue(self.graph['not_an_anchor_inventory'])
        for relation in self.graph['receipt_links'].values():
            self.assertNotIn('anchor',relation);self.assertNotIn('replacement',relation)
        self.assertNotIn('recipes',self.graph);self.assertNotIn('recipes13b',self.graph)

    def test_pilot_selection_cannot_remove_default_recipes_or_select_none(self):
        import inspect
        signature=inspect.signature(c.mutation_stage13b)
        self.assertIsNone(signature.parameters['only_ids'].default)
                                                                              
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder,'bindings.json');path.write_text(json.dumps({'anchor_owner13b':'T-13b-2a','recipes13b':[]}))
            with self.assertRaisesRegex(ValueError,'empty/duplicate'):
                c.mutation_stage13b(None,path,{},Path(folder),only_ids=[])


if __name__=='__main__':unittest.main()
