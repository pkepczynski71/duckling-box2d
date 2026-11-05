pass                                                                     
from collections import Counter
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent


def load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(s); sys.modules[name] = module; s.loader.exec_module(module)
    return module


d = load('test14_guard_data', 'polaczenia-oslony-dane.py')
b = load('test14_branches', 'galezie-polaczenia.py')


class DataControls(unittest.TestCase):
    def test_frozen156_and_every_route_preserved(self):
        items = d.guards()
        self.assertEqual(Counter(x['source']['rodzina'] for x in items),
            {'G1': 10, 'G2': 4, 'G3': 1, 'G4': 4, 'G5': 21, 'G6': 88, 'G8': 5, 'G9': 7, 'G10': 12, 'G11': 4})
        order = [*range(1, 84), *range(85, 157), 84]                   
        self.assertEqual([x['key'] for x in items], [d.MANIFEST['guard'][i-1]['key'] for i in order])
        for item in items:
            self.assertEqual(len(item['ga']), 64)
            self.assertLessEqual(len(item['ops']), 64)
            self.assertEqual(item['native_reachability'], 'UNEXECUTED')

    def test_all_G5_use_real_callback6_and_positive_step(self):
        for item in d.guards():
            if item['kind'] != 5: continue
            with self.subTest(key=item['key']):
                self.assertTrue(any(o['opcode'] == 86 and o['a'][:7] == (0, 0, 1, 1, 6, 0, 0) for o in item['ops']))
                self.assertEqual(item['ops'][-1]['opcode'], 32)
                self.assertEqual(item['expected_status'], 7)
                self.assertEqual(item['expected_reason'], 1)
        self.assertEqual(sum(x['kind'] == 5 for x in d.guards()), 21)

    def test_every_frozen_G6_word_and_domain_rejection(self):
        for item in d.guards():
            r, ga = item['source'], item['ga']
            if r['rodzina'] != 'G6': continue
            with self.subTest(key=item['key']):
                if 'inputWord' in r: self.assertIn(int(r['inputWord'], 16), ga[4:22])
                if ga[2] == 201:
                    predicates = d.m.domain_predicates(ga[4:22])
                    self.assertFalse(all(predicates.values()))
                self.assertEqual((item['expected_status'], item['expected_reason']), (5, 10))

    def test_all_G5_route_arguments_valid_before_lock(self):
        for item in d.guards():
            if item['kind'] != 5: continue
            code, kind = item['ga'][2:4]
            self.assertIn(code, (201, 203, 204, 205, 207))
            if code == 203: self.assertEqual(item['ga'][4:4 + d.m.MUTATOR_ARITY[kind]], d.MUTATOR_ARGUMENTS[kind])
            if code == 201: self.assertEqual(item['ga'][4:7], (0, 1, 0))

    def test_C_D_same_words_and_local_guard_ids(self):
        item = d.guards()[40]
        for decimal in (False, True):
            lines = d.encode_guard((item,), decimal=decimal).decode().splitlines()
            self.assertEqual(lines[0], 'PORT14 A GUARD 1')
            self.assertTrue(lines[1].startswith('G14 1 6 '))
            self.assertEqual(tuple(int(w, 10 if decimal else 16) for w in lines[2].split()[2:]), item['ga'])

    def test_shift_operators_not_comparisons(self):
        tokens = b.source_operators('x = (a << 1) | (b >> 2); y = a <= b; z = a >= b; // ignored ==\n"<= >>"; p->x += 1;')
        self.assertEqual([x['token'] for x in tokens if x['kind'] == 'comparison'], ['<=', '>='])
        self.assertEqual([x['token'] for x in tokens if x['kind'] == 'shift'], ['<<', '>>'])

    def test_ledger_covers_each_manifest_class_separately(self):
        ledger = b.obligations()
        expected = {(r['key'], c) for key in ('przypadki', 'direct') for r in d.MANIFEST[key] for c in r['mutationClasses']}
        self.assertEqual({(r['id'].split('/')[0], r['class']) for r in ledger['manifest_classes']}, expected)
        self.assertEqual(len([r for r in ledger['guards'] if r['classification'] == 'equivalent']), 4)
        result = b.settle(ledger, [])
        self.assertFalse(result['full_acceptance'])
        self.assertEqual(result['counts']['missing'], len(ledger['atoms']))
        self.assertGreater(result['counts']['open'], 0)

    def test_empty_mutation_and_missing_atom_are_red(self):
        ledger = b.obligations(); ledger['atoms'] = []
        self.assertFalse(b.settle(ledger, [])['full_acceptance'])
        ledger = b.obligations(); ledger['atoms'] = ledger['atoms'][:1]
        for symptom, value, state in [('build_code', 1, 'build-error'), ('timeout', True, 'timeout'),
                ('crash', True, 'unsafe'), ('unsafe_memory', True, 'unsafe'), ('anchor_hits', 0, 'anchor-error'),
                ('defined_difference', False, 'survived'), ('native_product', False, 'unverified')]:
            r = {'id': ledger['atoms'][0]['id'], 'executed': True, 'baseline_validated': True,
                 'anchor_hits': 1, 'build_code': 0, 'process_code': 0, 'stderr_bytes': 0,
                 'defined_difference': True, 'expected_difference': 'accepted0->accepted1', 'native_product': True, 'same_target': True}
            r[symptom] = value
            with self.subTest(symptom=symptom): self.assertEqual(b.settle(ledger, [r])['atoms'][0]['state'], state)

    def test_branch_predicate_uses_actual_transform(self):
        common = [0] * 17; common[4:8] = (0, 0, 0, 0); common[8:12] = [d.m.bits(1), d.m.bits(1), 0, 0]
        distance = [0] * 26
        distance[0], distance[3], distance[4] = d.m.bits(1), d.m.bits(2), d.m.bits(2)
        distance[17:19] = (d.m.bits(2), 0); distance[23:26] = (1, 1, 1)
        states = [0] * 16; states[6] = states[14] = d.m.bits(1)
        p = b.separation_predicates(common, distance, states)
        self.assertTrue(p['predicates']['lowerC=0']); self.assertTrue(p['predicates']['upperC=0'])
        self.assertFalse(p['predicates']['spring'])
        self.assertEqual(p['H']['k'], '40000000')
        states[12] = d.m.bits(.5)
        changed = b.separation_predicates(common, distance, states)
        self.assertTrue(changed['predicates']['lowerC>0']); self.assertTrue(changed['predicates']['upperC<0'])


if __name__ == '__main__': unittest.main()
