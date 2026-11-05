pass                                                                           
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from test_pary import HERE,g,module,p

RECIPE_COUNT=48
class Recipes(unittest.TestCase):
    def test_exact_recipe_count_and_seven_exported_functions(self):
        value=json.loads((HERE/'mutacje-pary.json').read_bytes());rows=value['native_mutations']
        self.assertEqual(value['recipe_count'],RECIPE_COUNT);self.assertEqual(len(rows),RECIPE_COUNT)
        self.assertEqual(len({r['name'] for r in rows}),RECIPE_COUNT)
        self.assertEqual({r['scope'] for r in rows if r['probe']=='physics'},{'b2CollideCapsuleAndCircle','b2CollidePolygonAndCircle',
            'b2CollideCapsules','b2CollideSegmentAndCircle','b2CollideSegmentAndCapsule',
            'b2CollidePolygonAndCapsule','b2CollideSegmentAndPolygon','b2MakeCapsule'})
        for r in rows:
            self.assertEqual(r['expected_code'],0)
            if r['probe']=='negative':self.assertTrue(r['variant']);continue
            self.assertTrue(r['witness_ids']);self.assertTrue(set(r['fields'])<=set(p.FIELDS))
            for ident in r['witness_ids']:self.assertEqual(g.cases()[ident-1].id,ident)
    def test_a_shortened_recipe_list_fails_the_executed_pin(self):
        value=json.loads((HERE/'mutacje-pary.json').read_bytes());value['native_mutations'].pop()
        with patch.object(Path,'read_bytes',return_value=json.dumps(value).encode('ascii')):
            with self.assertRaises(AssertionError):self.test_exact_recipe_count_and_seven_exported_functions()
    def test_native_edits_match_each_merged_product_function_once(self):
        mutator=module('pair_product_mutator','mutacje-pary.py')
        rows=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']
        if not (HERE.parents[1]/'silnik/port/pary.dk').is_file():
            if os.environ.get('PARY_REQUIRE_PRODUCT')=='1':self.fail('Product driver is missing from the CI checkout')
            self.skipTest('Product driver is absent; native comparison requires the port sources')
        for recipe in rows:
            source=(HERE.parents[1]/recipe['source']).read_text(encoding='utf-8')
            self.assertNotEqual(source,mutator.apply(source,recipe),recipe['name'])
    def test_scoping_does_not_mutate_another_function_or_accept_two_hits(self):
        mutator=module('pair_scope_mutator','mutacje-pary.py')
        src='fun a() -> () = { let q = 2; }\nfun b() -> () = { let q = 2; }\n'
        row={'name':'unit','scope':'a','expression':'let q = 2;','replacement':'let q = 3;'}
        changed=mutator.apply(src,row)
        self.assertIn('fun b() -> () = { let q = 2; }',changed)
        with self.assertRaisesRegex(ValueError,'single hit'):mutator.apply(src.replace('let q = 2;','let q = 2; let q = 2;'),row)

if __name__=='__main__':unittest.main()
