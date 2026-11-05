pass                                                              

                                                                          
   
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('test14_inputs', HERE/'przypadki-polaczenia.py')
g = importlib.util.module_from_spec(spec); sys.modules[spec.name] = g; spec.loader.exec_module(g)


class Inputs14(unittest.TestCase):
    def test_literal_default_create_read(self):
                                                               
        case = g.Case(1, 'literal', 'PUBLIC', 'fixture',
                      (g.op(200, 0, 0), g.op(201, 1, 0, 0, 1, 0, 0), g.op(204, 1, 0, 0)))
        self.assertEqual(''.join(g.text((case,))),
                         'PORT14 A PUBLIC 1\nC 1 3\n'
                         'O 1 200 2 00000000 00000000\n'
                         'O 2 201 6 00000001 00000000 00000000 00000001 00000000 00000000\n'
                         'O 3 204 3 00000001 00000000 00000000\n')
        self.assertEqual(''.join(g.text((case,), True)),
                         'PORT14 A PUBLIC 1\nC 1 3\nO 1 200 2 0 0\n'
                         'O 2 201 6 1 0 0 1 0 0\nO 3 204 3 1 0 0\n')

    def test_all_allocations_and_exact_long_steps(self):
        public = g.cases('PUBLIC'); direct = g.cases('DIRECT')
        self.assertEqual([c.key for c in public], [f'A{i:02}' for i in range(1, 97)])
        self.assertEqual([c.key for c in direct], [f'D{i:03}' for i in range(1, 129)])
        for case in public[48:]:
            steps = [o for o in case.ops if o['opcode'] in (31, 32) and g.value(o['a'][1]) > 0]
            self.assertEqual(len(steps), 1200, case.key)
            self.assertEqual({o['a'][2] for o in steps}, {g.MANIFEST['przypadki'][case.id-1]['subSteps']})
        self.assertEqual(sum(x['positiveSteps'] for x in g.execution_manifest(public)['cases'][48:]), 57600)

    def test_every_short_count_obeys_its_allocation(self):
        for entry, case in zip(g.MANIFEST['przypadki'][:48], g.cases('PUBLIC', 48)):
            count = sum(o['opcode'] in (31, 32) and g.value(o['a'][1]) > 0 for o in case.ops)
            self.assertGreaterEqual(count, entry['positiveStepsMin'], case.key)
            self.assertLessEqual(count, entry['positiveStepsMax'], case.key)
            self.assertLessEqual(len(case.ops), 128, case.key)

    def test_common_and_solver_are_disjoint(self):
        rows = g.cases('DIRECT')
        self.assertTrue(all(not c.fixtures for c in rows[:64]))
        for c in rows[64:]:
            self.assertEqual(tuple(map(len, c.fixtures)), (5, 17, 26, 20, 16))
            self.assertEqual(c.ops[0]['a'], (0, 0, 0))
            self.assertTrue(all(o['opcode'] == 210 for o in c.ops))
            self.assertEqual(c.fixtures[2][7:11], tuple(map(g.bits, (1, 2, 3, 4))))
        self.assertIn(18, [o['a'][0] for o in rows[2].ops if o['opcode'] == 211])

    def test_payload_formats_are_same_u32_bits(self):
        for profile in ('PUBLIC', 'DIRECT'):
            rows = g.cases(profile)
            c_lines = iter(g.text(rows)); d_lines = iter(g.text(rows, True))
            for c, d in zip(c_lines, d_lines, strict=True):
                ch, dh = c.split(), d.split()
                self.assertEqual(len(ch), len(dh))
                offset = 5 if ch[0] == 'F14' else 4 if ch[0] == 'O' and int(ch[2]) >= 200 else 3 if ch[0] == 'O' else len(ch)
                self.assertEqual(ch[:offset], dh[:offset])
                self.assertEqual([int(w, 16) for w in ch[offset:]], [int(w) for w in dh[offset:]])
                self.assertLessEqual(len(c.rstrip('\n')), 2048)
                self.assertLessEqual(len(d.rstrip('\n')), 2048)

    def test_headers_do_not_combine_profiles(self):
        for profile in ('PUBLIC', 'DIRECT'):
            self.assertEqual(next(g.text(g.cases(profile, 1))), f'PORT14 A {profile} 1\n')
        with self.assertRaises(ValueError): g.cases('GUARD')
        with self.assertRaises(ValueError): g.cases('PUBLIC', 97)
        with self.assertRaises(ValueError): g.cases('DIRECT', 129)
        with self.assertRaises(ValueError): list(g.text((g.cases('PUBLIC')[1],)))

    def test_long_scenes_include_lifecycle_and_owned_history(self):
        rows = g.cases('PUBLIC')
        for c in rows[48:]:
            self.assertIn(207, [o['opcode'] for o in c.ops], c.key)
            self.assertIn(208, [o['opcode'] for o in c.ops], c.key)
        for c in rows[84:90]: self.assertIn(205, [o['opcode'] for o in c.ops])
        for c in rows[90:96]: self.assertIn(3, [o['opcode'] for o in c.ops])
                                                                              
        for c in rows[72:78]: self.assertGreaterEqual(sum(o['opcode'] == 201 for o in c.ops), 12)

    def test_execution_manifest_does_not_invent_observations(self):
        result = g.execution_manifest(g.cases('PUBLIC', 48))
        self.assertEqual(len(result['cases']), 48)
        for row in result['cases']:
            self.assertIsNone(row['actualMaxima'])
            self.assertIsNone(row['observations'])
            self.assertEqual(len(row['inputSHA']['c']), 64)
            self.assertEqual(len(row['inputSHA']['d']), 64)
            self.assertGreater(row['inputBytes']['c'], 0)

    def test_word_arity_and_u32_guards(self):
        for args in ((203, 1, 0, 0, 25, 0), (204, 1, 0), (200, 0, 0, 0), (204, -1, 0, 0), (204, 1<<32, 0, 0)):
            with self.assertRaises(ValueError): g.op(*args)
        self.assertEqual(len(g.op(0, 0)['a']), 64)


if __name__ == '__main__': unittest.main()
