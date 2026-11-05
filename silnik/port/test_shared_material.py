pass                                                                       
import copy,json,unittest
from test_kontakty import HERE,module,work
m=module('shared_material_tests','mutacje-kontakty.py')
b=module('shared_material_coverage_tests','galezie-kontakty.py')
EXPECTED=('material-route-addPreparedShape','material-route-addShape','material-route-addBox',
 'material-route-createBodyWithBox','material-route-createBodyWithShape','material-route-createBodyWithPreparedShape')
def control():
    manifest=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
    recipe=next(r for r in manifest['native_mutations'] if r['name']=='material-shared-preflight')
    rows=[dict(name=w['name'],code=0,detected=True,detected_by='roznica',replayed_before_compaction=True,input_sha256=w['input_sha256'],
        difference=dict(baseline_ok=True,baseline_code=0,baseline_status=5,mutant_status=[4])) for w in recipe['witnesses']]
    return manifest,recipe,rows
class SharedMaterial(unittest.TestCase):
    def test_one_target_six_preserved_witnesses_and_history(self):
        manifest,recipe,rows=control();self.assertEqual(len(manifest['native_mutations']),203)
        self.assertEqual(tuple(w['name'] for w in recipe['witnesses']),EXPECTED)
        self.assertEqual(len(manifest['replaced_native_mutations']),6)
        self.assertTrue(m.shared_material_complete(recipe,rows))
        source=(HERE.parents[1]/recipe['source']).read_text(encoding='utf8');lo,hi=m.function_span(source,recipe['scope'])
        self.assertEqual(source[lo:hi].count(recipe['expression']),1)
        children=m.shared_material_children(recipe)
        for old,child,witness in zip(manifest['replaced_native_mutations'],children,recipe['witnesses']):
            self.assertEqual(old['replaced_by'],recipe['name'])
            for key in ('name','entry_call','specimen_seed','witness_id','expected_tags','expected_fields','baseline_status','mutant_status'):
                self.assertEqual(old['definition'].get(key),witness.get(key),key)
            self.assertEqual(child['expression'],recipe['expression']);self.assertEqual(child['replacement'],recipe['replacement'])
    def test_each_surviving_witness_remains_red(self):
        manifest,recipe,rows=control()
        for i,name in enumerate(EXPECTED):
            with self.subTest(name=name):
                bad=copy.deepcopy(rows);bad[i]['detected']=False;bad[i]['difference']['mutant_status']=[5]
                self.assertFalse(m.shared_material_complete(recipe,bad))
    def test_each_baseline_must_pass_and_input_must_match(self):
        manifest,recipe,rows=control()
        for i,name in enumerate(EXPECTED):
            for fault in ('baseline','exit','input','replay','missing'):
                with self.subTest(name=name,fault=fault):
                    bad=copy.deepcopy(rows)
                    if fault=='baseline':bad[i]['difference']['baseline_ok']=False
                    elif fault=='exit':bad[i]['code']=9
                    elif fault=='input':bad[i]['input_sha256']='bad'
                    elif fault=='replay':bad[i]['replayed_before_compaction']=False
                    else:bad.pop(i)
                    self.assertFalse(m.shared_material_complete(recipe,bad))
    def test_duplicate_or_extra_witness_is_rejected(self):
        manifest,recipe,rows=control();bad=copy.deepcopy(rows);bad[1]=bad[0]
        self.assertFalse(m.shared_material_complete(recipe,bad));self.assertFalse(m.shared_material_complete(recipe,rows+rows[:1]))
    def test_full_gate_rechecks_all_six_despite_green_parent(self):
        manifest,recipe,rows=control()
        results=[dict(name=r['name'],**{'class':r.get('class_id')},code=0,detected=True,replayed_before_compaction=True,difference={'controlled':True}) for r in manifest['native_mutations']]
        parent=next(r for r in results if r['name']==recipe['name']);parent['witness_results']=rows
        self.assertEqual(b.mutation_coverage(results,manifest)['code'],0)
        for i,name in enumerate(EXPECTED):
            with self.subTest(name=name):
                bad=copy.deepcopy(results);target=next(r for r in bad if r['name']==recipe['name']);target['witness_results'][i]['detected']=False
                self.assertEqual(b.mutation_coverage(bad,manifest)['code'],1)
if __name__=='__main__':unittest.main()
