from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                      

                                                                     
   
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sen_w3_branches',HERE/'galezie-sen.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
mut=b.load('sen_w3_mutations','mutacje-sen11.py')
ROOT=HERE.parents[1]


class DecisionD114(unittest.TestCase):
    def test_only_the_accepted_crequest_row_with_measured_evidence_is_valid(self):
        accepted='|CREQUEST|G11-7/8/9/10/11|GUARD3 selector2,live131059+new1|OK0,suma131060→OK0,suma131059|NOT Eb13f1dcf4053 Eec72420df5df.|'
        proof=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        contract=norm_text(HERE/'fixtures/norms/KONTRAKT-11.json')
        self.assertEqual(contract.splitlines()[280],accepted)
        original_read=Path.read_text
        for row,valid in ((accepted,True),(proof['old_row'],False),
                          (accepted.replace('131060','131061'),False),
                          (accepted+' ',False),(' '+accepted,False),
                          (accepted+'\n'+proof['old_row'],False),('',False)):
            def read(path,*args,**kwargs):
                return contract.replace(accepted,row) if path==HERE/'fixtures/norms/KONTRAKT-11.json' else original_read(path,*args,**kwargs)
            with self.subTest(row=row),patch.object(Path,'read_text',read):
                self.assertEqual(b.crequest_decision(ROOT,proof) is not None,valid)
        forged=copy.deepcopy(proof)
        forged['proposed_row']=accepted.replace('131060','131061')
        self.assertIsNone(b.crequest_decision(ROOT,forged))

    def test_missing_w3_measurement_file_or_c_receipt_is_rejected(self):
        original_read=Path.read_bytes
        def read(path):
            if path==HERE/'sen-d11-4-crequest.json':raise FileNotFoundError(path)
            return original_read(path)
        with patch.object(Path,'read_bytes',read):self.assertIsNone(b.crequest_decision(ROOT))
        proof=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        del proof['c']
        self.assertIsNone(b.crequest_decision(ROOT,proof))

    def test_c_truth_needs_successful_complete_actual_processes(self):
        good=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        self.assertIsNotNone(b.crequest_decision(ROOT,good))
        for side in ('c','duckling'):
            for key,value in (('code',1),('code',-11),('stderr','runtime failure\n'),
                              ('binary_sha256',''),('replayed_before_compaction',False)):
                bad=copy.deepcopy(good);bad[side]['process'][key]=value
                with self.subTest(side=side,key=key,value=value):self.assertIsNone(b.crequest_decision(ROOT,bad))
            bad=copy.deepcopy(good);bad[side]['stdout']=bad[side]['stdout'].removesuffix('END 1\n')
            bad[side]['process']['sha256']=hashlib.sha256(bad[side]['stdout'].encode()).hexdigest()
            bad[side]['process']['bytes']=len(bad[side]['stdout'])
            with self.subTest(side=side,corruption='truncated and rehashed'):self.assertIsNone(b.crequest_decision(ROOT,bad))

    def test_identically_wrong_outputs_do_not_become_c_truth(self):
        bad=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        for side in ('c','duckling'):
            bad[side]['stdout']=bad[side]['stdout'].replace('0001fff4','0001fff3')
            bad[side]['process']['sha256']=hashlib.sha256(bad[side]['stdout'].encode()).hexdigest()
        self.assertIsNone(b.crequest_decision(ROOT,bad))

    def test_decision_expires_on_source_or_contract_change(self):
        good=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        for key in ('c_helper_sha256','d_function_sha256','old_row','proposed_row','decision'):
            bad=copy.deepcopy(good);bad[key]='changed'
            with self.subTest(key=key):self.assertIsNone(b.crequest_decision(ROOT,bad))

    def test_document_error_is_separate_from_kills_and_full_acceptance(self):
        table=b.frozen_table(ROOT)
        request=next(r for r in table['rows'] if r['id']=='CREQUEST')
        self.assertTrue(request['closed_by_decision']);self.assertFalse(request['counted_as_killed'])
        self.assertFalse(table['complete']);self.assertIn('HISTORY',table['native_gaps'])
        self.assertEqual(len(table['proofs']),11)
        self.assertFalse(any(p['counted_as_killed'] for p in table['proofs']))

    def test_every_secondary_mutation_edit_is_required_and_single_hit(self):
                                                                               
                                                                                
        for recipe in mut.planned():
            if not recipe['name'].startswith('W3-'):continue
            source=(ROOT/recipe['source']).read_text(encoding='utf-8')
            for edit in recipe.get('file_edits',[])+recipe.get('scoped_edits',[]):
                broken=source.replace(edit['expression'],'W3_MISSING_REQUIRED_ANCHOR')
                with self.subTest(recipe=recipe['name'],anchor=edit['expression']),self.assertRaises(ValueError):
                    mut.apply_recipe(broken,recipe)


if __name__=='__main__':unittest.main()
