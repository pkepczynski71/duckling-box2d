pass                                                                         
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('test_polaczenia_m', HERE / 'model-polaczenia.py')
m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)


def joint(group, payload, *, slot=0, world=0, source=0):
    return 'J14', (1, 1, source, world, slot, group, len(payload), *payload)


def listing(kind, parent, payload, world=0):
    return 'L14', (1, 1, 0, world, kind, parent, len(payload), *payload)


def snapshot():
    pass                                                              

                                                                            
                                                             
       
    n = m.NULL
    w = [0] * 16; w[0:2] = (1, 1); w[3] = 1
    b0 = [0] * 33; b0[0:2] = (1, 1); b0[3] = 1
    b1 = [0] * 33; b1[0:2] = (1, 1); b1[2], b1[3] = 1, 2
    data = [('E14', (1, 1, 204, 3, 1, 0, 0)), ('A14', (1, 1, 0, 0)),
            ('W', tuple(w)), ('B', tuple(b0)), ('B', tuple(b1)),
            joint(0, (1, 0, 1, 0, 4, 0, 1, 0)),
            joint(1, (0, 0, 0, 0, n, 0, 0, n, n, 1, n, n, 0, n, n, n, 0x3f800000, 0, 1, 0, 0)),
            joint(2, (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x42700000, 0x40000000, 0, 0x3f800000, 0)),
            joint(3, (0x3f800000, 0, 0, 0x3ba3d70a, 0x47c35000, *(0 for _ in range(21)))),
            joint(4, (0,) * 50), joint(5, (1, 1, 4, 0, 1, 0)),
            joint(7, (0, 1)), joint(7, (1, 1), slot=1),
            listing(2, 0, (0,)), listing(2, 1, ()), listing(2, 2, ())]
    data += [listing(3, c, ()) for c in range(12)]
    data += [listing(4, 0, (1, 0, 4, 0))]
    data += [('GB', (1, 1, 0, c, 1, 0, 0) if c < 11 else (1, 1, 0, c, 0, 0, 0)) for c in range(12)]
    data += [joint(8, (1, 1, 1, 1, 1, 1, 0, 2, 0, 0, 3, 12, 1, 0, 0, 1, 1, 0, 0, 0), world=16)]
    return data


OP = {'opcode': 204, 'a': (1, 0, 0)}


class ModelControls(unittest.TestCase):
    def test_f32_round_each_operation(self):
        self.assertEqual(m.bits(m.add(16777216., 1.)), 0x4b800000)
        self.assertEqual(m.bits(m.sub(m.add(16777216., 1.), 16777216.)), 0)
        self.assertEqual(m.bits(m.mul(-0., 1.)), 0x80000000)

    def test_normative_planner_tails_and_conservative_guard(self):
        self.assertEqual(m.block_plan(0), ())
        self.assertEqual(m.block_plan(1), ((0, 1),))
        self.assertEqual(m.block_plan(4), ((0, 4),))
        self.assertEqual(m.block_plan(5), ((0, 4), (4, 1)))
        self.assertEqual(m.block_plan(16), ((0, 4), (4, 4), (8, 4), (12, 4)))
        self.assertEqual(m.block_plan(17), ((0, 4), (4, 4), (8, 4), (12, 5)))
        self.assertEqual(m.block_plan(131059)[-1], (98292, 32767))
        self.assertEqual(m.block_plan(131060)[-1], (98295, 32765))
        self.assertTrue(m.joint_fit(131059)); self.assertFalse(m.joint_fit(131060))
        with self.assertRaises(ValueError): m.block_plan(-1)

    def test_description_default_and_four_equivalences(self):
        self.assertEqual(m.default_description(), (0, 0, 0, 0, 0x3f800000, 0, 0, 0, 0, 0, 0x47c35000, 0, 0, 0, 0, 0, 0, 0))
        self.assertTrue(all(m.domain_predicates(m.default_description()).values()))
        for field, word, skipped in ((9, 0x7f800000, 'min.finite'), (10, 0xbf800000, 'max.nonnegative')):
            a = list(m.default_description()); a[field] = word
            p = m.domain_predicates(a); p.pop(skipped)
            self.assertFalse(all(p.values()))

    def test_exact_literal_J3_before_prepare(self):
        line = 'J14 1 6 0 0 0 3 26 3f800000 00000000 00000000 3ba3d70a 47c35000 ' + ' '.join(['00000000'] * 21) + '\n'
        tag, v = m.parse(line)
        self.assertEqual(tag, 'J14'); self.assertEqual(v[7:12], (0x3f800000, 0, 0, 0x3ba3d70a, 0x47c35000))
        self.assertEqual(m.render(tag, v), line)

    def test_grammar_damage_same_on_both_sides(self):
        good = 'J14 1 6 0 0 0 9 2 00000001 00000000\n'
        for bad in (good.replace(' 2 ', ' 3 '), good.replace('J14', 'Q14'), good[:-1],
                    good.replace('00000001', '0000000A'), good.replace(' 6 ', ' 06 '),
                    good.replace(' 0 ', '  0 ', 1), good.replace('\n', '\r\n')):
            for side in ('C', 'D'):
                with self.subTest(side=side, bad=bad), self.assertRaises(ValueError): m.parse(bad)

    def test_projection_J8_exact_fields(self):
        h = tuple(range(20)); line = m.render(*joint(8, h, world=16))
        tag, v = m.parse(m.project_line(line))
        self.assertEqual(v[7:], (0, 0, 0, 0, 4, 0, 6, 0, 8, 0, 0, 0, 0, 0, 14, 15, 16, 17, 18, 19))
        self.assertIsNone(m.project_line(m.render(*joint(3, (0,) * 26))))
        self.assertEqual(m.project_line('A14 1 1 5 10\n'), 'A14 1 1 5 10\n')

    def test_output_long_L_not_subject_to_input_limit(self):
        row = listing(0, 0, (1, 0, 1) * 128)
        line = m.render(*row)
        self.assertGreater(len(line), 2048)
        self.assertEqual(m.parse(line), row)

    def test_joint_structure_uses_actual_heads_not_sorting(self):
        result = m.check_joint_snapshot(snapshot(), 1, 1, OP)
        self.assertEqual(len(result['live']), 1)
        self.assertFalse(result['full_ownership_ready'])

    def test_missing_duplicate_sparse_and_summary_rejected(self):
        for group in (0, 1, 2, 3, 4, 5, 7, 8):
            data = snapshot(); i = next(i for i, (t, v) in enumerate(data) if t == 'J14' and v[5] == group)
            for mode in ('missing', 'duplicate'):
                damaged = copy.deepcopy(data)
                if mode == 'missing': damaged.pop(i)
                else: damaged.insert(i, damaged[i])
                with self.subTest(group=group, mode=mode), self.assertRaises(ValueError):
                    m.check_joint_snapshot(damaged, 1, 1, OP)

    def test_edges_both_sides_prev_next_count_and_dense_repair(self):
        mutations = [(1, 7, 0), (1, 10, 0), (1, 8, 0), (1, 11, 1),
                     (1, 5, 1), (1, 12, 1), (1, 18, 2), (2, 2, 0), (7, 0, 1), (7, 1, 2), (5, 0, 0)]
        for group, field, value in mutations:
            data = snapshot(); i = next(i for i, (t, v) in enumerate(data) if t == 'J14' and v[5] == group)
            t, v = data[i]; a = list(v); a[7 + field] = value; data[i] = (t, tuple(a))
            with self.subTest(group=group, field=field), self.assertRaises(ValueError):
                m.check_joint_snapshot(data, 1, 1, OP)

    def test_combined_occupation_detects_contact_joint_conflict(self):
                                                                      
                                                             
        p = [0] * 21; p[3], p[4], p[6], p[9] = 2, 0, 0, 1
        ct = [0] * 20; ct[2], ct[3], ct[7], ct[10] = 2, 0, 0, 1
        rows = {'W': [(1, 1, 0, 1)], 'CT': [(1, 1, 0, 0, *ct)], 'GB': []}
        with self.assertRaisesRegex(ValueError, 'conflict'):
            m._occupation(rows, {(0, 0): tuple(p)}, {(0, 0): 2, (0, 1): 2})

    def test_projection_preserves_historical_owner(self):
        row = joint(0, (1, 0, 1, 0, 4, 0, 0xaabbccdd, 0x11223344), source=1, world=16)
        self.assertEqual(m.parse(m.project_line(m.render(*row))), row)


if __name__ == '__main__': unittest.main()
