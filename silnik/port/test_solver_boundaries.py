pass                                                                           
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unittest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('solver_boundary_native',HERE/'mutacje-solver.py')
native=importlib.util.module_from_spec(spec);sys.modules[spec.name]=native;spec.loader.exec_module(native)


def profile_dependencies(source):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[A-Za-z_][A-Za-z_0-9]*',source)
    return [token for token in tokens if not token.startswith(('"','#')) and
            re.search(r'profile|profil|legacy|(?:port|guard)_?[89](?:b|$)',token,re.I)]


def replacements():
    rows=[]
    for file in ('mutacje-ruch-swiata.json','mutacje-kontakty.json'):
        rows += [r for r in json.loads((HERE/file).read_bytes())['native_mutations'] if r.get('solver_replacement')]
    return rows


class ApprovedBoundaries(unittest.TestCase):
    def test_W2_no_physics_profile_switch_or_profile_dependency(self):
        paths=sorted((ROOT/'silnik/fizyka').glob('*.dk'))
        self.assertTrue(paths)
        found={p.name:profile_dependencies(p.read_text(encoding='utf-8')) for p in paths}
        self.assertEqual({name:tokens for name,tokens in found.items() if tokens},{})

    def test_W2_catches_both_profiles_and_alias_declarations_but_allows_unsupported_pairs(self):
        for source in ('if (CONTACT_PROFILE == 1i32) return;', 'const oldProfile = 8i32; let active = oldProfile;',
                       'fun legacyStep() -> () = {}', 'let profile: i32 = 9i32;'):
            self.assertTrue(profile_dependencies(source))
        self.assertEqual(profile_dependencies('# legacy profile8 is forbidden\nlet message = "PROFILE8"; if (kind == -1i32) result.status = 6i32;'),[])

    def test_W3_cardinalities_and_only_the_three_approved_replacements(self):
        d8=json.loads((HERE/'mutacje-ruch-swiata.json').read_bytes());d9=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
        self.assertEqual(len(d8['native_mutations']),53)
        self.assertEqual({r['class_id'] for r in d8['native_mutations']},set(range(1,23)))
        self.assertEqual(len(d9['native_mutations']),208)
        self.assertEqual({r['class_id'] for r in d9['native_mutations'] if r.get('class_id')},{f'M{i:02}' for i in range(1,41)}-{'M12'})
        self.assertEqual({r['solver_replacement'] for r in replacements()},{'A8-27','A9-08','A9-09'})
        self.assertTrue(all(1<=r['witness_id']<=64 for r in d9['native_mutations']))
        for recipe in replacements():
            self.assertTrue(recipe['expected_tags'])
            self.assertFalse(native.group_for(recipe).gap)
            self.assertIn(recipe['guard_group'],{x.group for x in native.f.definitions()})

    @unittest.skipUnless((HERE/'solver-swiata.dk').is_file() or os.environ.get('SOLVER_REQUIRE_PRODUCT')=='1','Product driver must be present in the checked source tree')
    def test_W3_each_replacement_changes_one_real_solver_site(self):
        for recipe in replacements():
            source=(ROOT/recipe['source']).read_text(encoding='utf-8')
            with self.subTest(approval=recipe['solver_replacement']):
                self.assertNotEqual(native.apply(source,recipe),source)


if __name__=='__main__':unittest.main()
