from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                  

                                                                       
                                       
   
import copy
import importlib.util
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('lancuchy13b_controls', HERE / 'ci-lancuchy-oslony.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
m = c.m


def open_new_groups():
    pass                                                                  
    operation = c.chain_op13b()
    rows = [('E13B', (1, 3, 100, *operation['a']))]
    rows += [('EP13B', (1, 3, i, *p)) for i, p in enumerate(operation['points'])]
    rows += [('EU13B', (1, 3, 0, *operation['materials'][0])),
             ('A13', (1, 3, 0, 0)),
             ('CN13', (1, 3, 0, 1, 0, 1, 0, 3, 0, 1, 0)),
             ('V13', (1, 3, 0, 1, 1)),
             ('CS13', (1, 3, 0, 0, 0x40000000, 0, 0x3f800000, 0,
                       0xbf800000, 0, 0xc0000000, 0, 0)),
             ('CH13', (1, 3, 0, 0, 1, 0, 0xffffffff, 1, 1)),
             ('CI13', (1, 3, 0, 0, 0, 1, 0, 1, 0, 4, 0, 1, 0)),
             ('CM13', (1, 3, 0, 0, 0, 0x3f19999a, 0, 0, 0, 0, 0)),
             ('BH13', (1, 3, 0, 0, 0)),
             ('IP13', (1, 3, 0, 1, 0)),
             ('CG13', (1, 3, 0, 0, 1, 1, 3, 0, 1, 0)),
             ('I13', (1, 3, 1, 1, 1, 1, 1, 1)),
             ('Z13', (1, 3, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 3, 4, 1, 1))]
    return operation, rows


def recount(rows):
    pass                                                                  
    counts = {tag: sum(t == tag for t, _ in rows) for tag, _ in rows}
    result = []
    for tag, v in rows:
        if tag == 'I13':
            v = (*v[:2], *(counts.get(t, 0) for t in ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13')))
        if tag == 'Z13':
            v = (*v[:2], *(counts.get(t, 0) for t in (
                'A13', 'CN13', 'CQ13', 'QL13', 'CS13', 'PC13', 'COPY13', 'CV13', 'CE13', 'ENDCOPY13')),
                 counts.get('CN13', 0), sum(x[4] for t, x in rows if t == 'CH13'),
                 0, v[1], counts.get('EP13B', 0), counts.get('EU13B', 0), counts.get('V13', 0))
        result.append((tag, v))
    return result


def read_new_groups(opcode):
    _, original = open_new_groups()
    operation = c.op13b(opcode, 1, 0, 0) if opcode in (102, 104) else c.op13b(108, 0, 0, 123)
    rows = [(tag, (v[0], 4, *v[2:])) for tag, v in original if tag not in ('EP13B', 'EU13B')]
    rows[0] = ('E13B', (1, 4, opcode, *operation['a']))
    index = next(i for i, (t, _) in enumerate(rows) if t == 'CS13')
    if opcode == 102:
        rows[index:index] = [
            ('CQ13', (1, 4, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 1, 0, 1, 1, 0x3f19999a, 0, 0)),
            ('QL13', (1, 4, 0, 0, 1, 0, 1, 0, 4, 0, 1, 0))]
    elif opcode == 104:
        rows[index + 1:index + 1] = [('PC13', (1, 4, 0, 0, 1, 1, 0, 1, 0, 3, 0, 1, 0))]
    else:
        blocks = []
        for phase in range(3):
            blocks += [('COPY13', (1, 4, 0, phase)),
                       ('CV13', (1, 4, 0, phase, 1, 0, 1, 0, 3, 0, 1, 0, 0, 2, 0, 1, 0, 1)),
                       ('CE13', (1, 4, 0, phase, 0, 1, 0, 1, 123 if phase == 1 else 0, 4, 0, 1, 0)),
                       ('ENDCOPY13', (1, 4, 0, phase))]
        rows[index + 1:index + 1] = blocks
    return operation, recount(rows)


class Frozen13bControls(unittest.TestCase):
    def test_literal_new_syntax_from_repo_contract(self):
                                                                           
        text = norm_text(HERE / 'fixtures/norms/KONTRAKT-13.json')
        section = text.split('### 9.1. Literalne wzory13', 1)[1].split('### 9.2.', 1)[0]
        tags = set()
        for line in section.splitlines():
            tag = line.split(' ', 1)[0]
                                                                      
                                                                       
            if (tag in m.SCHEMA13B or tag == 'IP13') and (tag != 'G' or len(line.split()) == 5):
                with self.subTest(tag=tag, line=line[:32]):
                    parsed, _ = m.parse13b(line + '\n')
                    self.assertEqual(parsed, tag)
                    tags.add(tag)
        self.assertTrue(set(m.SCHEMA13B) - {'G'} <= tags)
        self.assertIn('IP13', tags)

    def test_strict_new_record_physical_corruptions(self):
        good = b'CN13 1 3 0 00000001 00000000 00000001 00000000 00000003 00000000 00000001 00000000\n'
        for bad in (good[:-1], good[:-1] + b'\r\n', b'\xef\xbb\xbf' + good,
                    good.replace(b' ', b'  ', 1), good.replace(b' ', b'\t', 1),
                    good.replace(b' 1 ', b' 01 ', 1), good.replace(b'00000003', b'0000000A'),
                    good.replace(b'00000003', b'3'), good.replace(b'CN13', b'CN14'),
                    good.replace(b'00000003', b'100000000'), good[:-10] + b'\n'):
            with self.subTest(bad=bad[:40]), self.assertRaises((ValueError, UnicodeError)):
                m.parse13b(bad)

    def test_ip_count_and_slot_domain(self):
        self.assertEqual(m.parse13b('IP13 1 6 0 00000001 00000001 00000000\n')[1][-1], 0)
        for line in ('IP13 1 6 0 00000001 00000002 00000000\n',
                     'IP13 1 6 0 00000011 00000011 ' + ' '.join(['00000000'] * 17) + '\n'):
            with self.assertRaises(ValueError):
                m.parse13b(line)

    def test_projection_exact_public_tags_and_tuning_only(self):
        public = ('CS13', 'CN13', 'V13', 'CQ13', 'QL13', 'PC13',
                  'COPY13', 'CV13', 'CE13', 'ENDCOPY13', 'EF12', 'I12', 'Z13')
        for tag in public:
            line = (tag + ' fixture\n').encode('ascii')
            self.assertEqual(m.projection13b_line(line), line)
        for tag in m.PRIVATE13B:
            self.assertIsNone(m.projection13b_line((tag + ' fixture\n').encode('ascii')))
        source = b'WS12 1 3 0 ' + b' '.join(f'{x:08x}'.encode() for x in range(11)) + b'\n'
        expected = b'WS12 1 3 0 00000000 00000001 00000002 00000000 00000000 00000000 00000006 00000007 00000008 00000009 0000000a\n'
        self.assertEqual(m.projection13b_line(source), expected)

    def test_all_frozen_guards_and_no_false_native_claim(self):
        rows = c.guard_definitions13b()
        self.assertEqual(len(rows), 96)
        self.assertEqual(sum(not x['liczonyJakoZabicie'] for x in rows), 4)
        self.assertFalse(any(x['native_verified'] for x in rows))
        self.assertEqual(sum(x['id'].startswith('GB1-ROUTE-') for x in rows), 27)
        self.assertEqual(sum(x['id'].startswith('GB2-ROUTE-') for x in rows), 5)
        self.assertEqual(sum(x['id'].startswith('GB3-SET-') for x in rows), 4)

    def test_guard_wire_both_word_encodings_and_complete_groups(self):
        for row in c.guard_definitions13b():
            if not row['materialized']:
                with self.assertRaises(ValueError):
                    c.encode_guard13b(row)
                continue
            cc, dd = [c.encode_guard13b(row, decimal=d).splitlines() for d in (False, True)]
            self.assertEqual(len(cc), len(dd))
            self.assertEqual(cc[0], b'GUARD13B 1')
            self.assertEqual(cc[1], dd[1])
            for a, b in zip(cc[2:], dd[2:]):
                aa, bb = a.split(), b.split()
                offset = {b'GA': 2, b'O': 3, b'P13B': 4, b'U13B': 4}[aa[0]]
                self.assertEqual(aa[:offset], bb[:offset])
                self.assertEqual([int(x, 16) for x in aa[offset:]], [int(x) for x in bb[offset:]])
                self.assertLessEqual(len(a), 2048)
            if row['kind'] == 200:
                self.assertEqual(sum(x.startswith(b'P13B ') for x in cc), row['ga'][4])
                self.assertEqual(sum(x.startswith(b'U13B ') for x in cc), row['ga'][6])

    def test_exact_f32_slop_and_derived_overflow(self):
        zero = (0, 0)
        r = m.distance_predicate13b(zero, (0, 0x3ba3d70a))
        self.assertEqual(r['H'], ['00000000', '3ba3d70a', '00000000', '37d1b717', '37d1b717'])
        self.assertTrue(r['equal'])
        self.assertFalse(r['above'])
        d = m.distance_predicate13b(zero, (0x5f502ab5, 0x5f502ab5))
        self.assertEqual(d['H'][-3:], ['7f29456d', '7f29456d', '7f800000'])
        self.assertEqual(d['finite'], [True, True, True, True, False])
        o = m.orient_predicate13b(zero, (0x5f502ab5, 0), (0x5f502ab5, 0x5f502ab5))
        self.assertTrue(all(o['finite']))

    def test_shadowed_witnesses_stay_explicit_not_counted_as_kills(self):
        audit = {x['id']: x for x in c.b.predicate_audit13b(c.guard_definitions13b())}
        self.assertEqual([(r['i'], r['j'], r['kind']) for r in audit['GB5-COLLINEAR']['remaining_refusals']], [(0, 2, 'touch')])
        self.assertEqual([(r['i'], r['j'], r['kind']) for r in audit['GB5-ADJACENT']['remaining_refusals']], [(0, 2, 'touch')])
        self.assertTrue(audit['GB5-COLLINEAR']['shadowed'])
        self.assertTrue(audit['GB5-ADJACENT']['shadowed'])
        self.assertFalse(audit['GB5-CROSS']['shadowed'])
        self.assertFalse(audit['GB5-CLOSE']['shadowed'])
        self.assertTrue(all(not r['native_mutation'] for r in audit.values()))

    def test_onsegment_closed_bounds_adjacency_axis_and_signed_zero(self):
        bits = lambda p: tuple(map(m.bits, p))
        straight = m.edge_predicate13b(*map(bits, ((0, -0.), (1, 0), (1, 0), (2, 0))), True)
        self.assertFalse(straight['rejected'])
        tie = m.edge_predicate13b(*map(bits, ((0, 0), (3, 3), (3, 3), (1, 1))), True)
        self.assertEqual(tie['axis'], 0)
        self.assertTrue(tie['positive_overlap'])
        touch = m.edge_predicate13b(*map(bits, ((0, 0), (4, 0), (2, 0), (2, 2))), False)
        self.assertTrue(touch['rejected'])
        self.assertEqual(touch['cause'], 'touch')

    def test_counts_material_priority_and_last_material(self):
        call = c.chain_op13b([(0, 0), (1, 0), (2, 0)])
        self.assertEqual(m.description_status13b(call['a'], call['points'], call['materials']), (4, 84))
        self.assertEqual(m.description_status13b(call['a'], call['points'], call['materials'], 2), (5, 80))
        for field in range(4):
            materials = [(m.bits(.6), 0, 0, 0, 0, 0)] * 3 + [(m.bits(.6), 0, 0, 0, 0, 0)]
            last = list(materials[-1]); last[field] = 0x7f800000; materials[-1] = tuple(last)
            call = c.chain_op13b(materials=materials)
            self.assertEqual(m.description_status13b(call['a'], call['points'], call['materials']), (5, 0))
        call = c.chain_op13b(materials=[(m.bits(.6), 0, 0, m.bits(-1.), 0x80000000, 0xffffffff)])
        self.assertEqual(m.description_status13b(call['a'], call['points'], call['materials']), (0, 0))

    def test_topology_both_ends_material_index_and_no_ghost_shapes(self):
        points = tuple((i, 0) for i in range(5))
        loop = m.topology13b(points, True, 5)
        self.assertEqual(loop[-2]['points'], (points[2], points[3], points[4], points[0]))
        self.assertEqual(loop[-1]['points'], (points[3], points[4], points[0], points[1]))
        opened = m.topology13b(points, False, 5)
        self.assertEqual(len(opened), 2)
        self.assertEqual([x['material'] for x in opened], [1, 2])
        self.assertEqual(opened[0]['points'], points[:4])

    def test_ticket_batch_full_reservation_and_carry(self):
        self.assertEqual(m.ticket_batch13b(0xfffffffc, 0xffffffff, 3), (3, 4))
        self.assertEqual(m.ticket_batch13b(0xfffffffb, 0xffffffff, 3), (0, 4))
        self.assertEqual(m.ticket_batch13b(0xffffffff, 0xffffffff, 0), (3, 1))
        self.assertEqual(m.ticket_batch13b(0xffffffff, 0, 3), (0, 4))

    def test_new_groups_normative_fragment_is_not_full_snapshot_acceptance(self):
        operation, rows = open_new_groups()
        checked = m.check13b_groups(rows, operation, 1, 3, {0: 0})
        self.assertTrue(checked['new_groups_checked'])
        self.assertFalse(checked['complete_snapshot'])

    def test_new_group_deletion_duplicate_order_id_echo_and_counters(self):
        operation, rows = open_new_groups()
        bad_rows = []
        for i in range(len(rows)):
            bad_rows += [rows[:i] + rows[i + 1:], rows[:i] + [rows[i]] + rows[i:]]
        swapped = list(rows); swapped[-4], swapped[-3] = swapped[-3], swapped[-4]; bad_rows.append(swapped)
        for i, (tag, values) in enumerate(rows):
            changed = list(rows); changed[i] = (tag, (2, *values[1:])); bad_rows.append(changed)
        for bad in bad_rows:
            with self.assertRaises((ValueError, IndexError, KeyError)):
                m.check13b_groups(bad, operation, 1, 3, {0: 0})

    def test_identical_both_sides_owner_birth_reuse_and_last_child_corruption(self):
        operation, rows = open_new_groups()
        for tag, index in (('CN13', 7), ('CN13', 9), ('CG13', 6), ('CG13', 8),
                           ('CS13', 12), ('CH13', 7), ('CI13', 8), ('CM13', 4), ('BH13', 4)):
            changed = copy.deepcopy(rows)
            i = next(i for i, (t, _) in enumerate(changed) if t == tag)
            value = list(changed[i][1]); value[index] ^= 1; changed[i] = (tag, tuple(value))
                                                                                  
            for same_side in (changed, copy.deepcopy(changed)):
                with self.subTest(tag=tag, index=index), self.assertRaises(ValueError):
                    m.check13b_groups(same_side, operation, 1, 3, {0: 0})

    def test_reads_and_copies_require_complete_groups_even_with_repaired_counts(self):
        for opcode, tags in ((102, ('CQ13', 'QL13')), (104, ('PC13',)),
                             (108, ('COPY13', 'CV13', 'CE13', 'ENDCOPY13'))):
            operation, rows = read_new_groups(opcode)
            m.check13b_groups(rows, operation, 1, 4, {0: 0})
            for tag in tags:
                bad = recount([(t, v) for t, v in rows if t != tag])
                with self.subTest(opcode=opcode, tag=tag), self.assertRaises((ValueError, KeyError, IndexError)):
                    m.check13b_groups(bad, operation, 1, 4, {0: 0})
        operation, rows = open_new_groups()
        for tag in ('CS13', 'CG13', 'CM13', 'CI13', 'CH13', 'BH13', 'IP13'):
            bad = recount([(t, v) for t, v in rows if t != tag])
            with self.subTest(tag=tag), self.assertRaises((ValueError, KeyError, IndexError)):
                m.check13b_groups(bad, operation, 1, 3, {0: 0})

    def test_copy_changes_one_slot_only_and_constructor_values_are_pinned(self):
        operation, rows = read_new_groups(108)
        for phase, index in ((2, 8), (1, 9), (1, 5)):
            bad = list(rows)
            at = next(i for i, (t, v) in enumerate(bad) if t == 'CE13' and v[3] == phase)
            tag, v = bad[at]; changed = list(v); changed[index] ^= 1; bad[at] = (tag, tuple(changed))
            with self.assertRaises(ValueError):
                m.check13b_groups(bad, operation, 1, 4, {0: 0})
        operation, rows = open_new_groups()
        for tag, index in (('CM13', 5), ('CS13', 4), ('CS13', 10)):
            bad = list(rows)
            at = next(i for i, (t, _) in enumerate(bad) if t == tag)
            t, v = bad[at]; changed = list(v); changed[index] ^= 1; bad[at] = (t, tuple(changed))
            with self.assertRaises(ValueError):
                m.check13b_groups(bad, operation, 1, 3, {0: 0})

    def test_empty_omitted_branch_or_fake_native_receipt_cannot_pass(self):
        guards = c.guard_definitions13b()
        table = c.b.table13b(guards)
        self.assertEqual(len(table['reachability']), 64)
        self.assertEqual(table['verified'], 0)
        self.assertEqual(table['code'], 1)
        requirement = table['rows'][0]['id']
        fake = {'requirement': requirement, 'detected': True, 'native_executed': False}
        self.assertEqual(c.b.table13b(guards, [fake])['verified'], 0)
        with self.assertRaises(ValueError):
            c.b.table13b(guards[:-1])
        with self.assertRaises(ValueError):
            c.b.table13b(guards, [{'requirement': 'unknown'}])

    def test_negative_catalogue_reachability_and_bounded_inputs(self):
        catalogue = c.parser_reachability13b()
        definitions = c.negative_definitions13b()
        self.assertEqual(len(catalogue), 33)
        self.assertEqual(len({r['name'] for r in definitions}), len(definitions))
        for profile in ('PORT13B', 'GUARD13B'):
            rows = [r for r in definitions if r['profile'] == profile]
            self.assertLessEqual(len(rows), 256)
            for item in catalogue:
                if item[profile]['reachable']:
                    self.assertTrue(any(r['error'] == item['error'] for r in rows), item['error'])
                    if item[profile]['after_legal_O']:
                        self.assertTrue(any(r['error'] == item['error'] and r['after_legal_O'] for r in rows), item['error'])
                else:
                    self.assertFalse(any(r['error'] == item['error'] for r in rows), item['error'])
            self.assertTrue(all(not r['native_verified'] for r in rows))
        self.assertEqual({r['error'] for r in catalogue if not r['PORT13B']['reachable']},
                         {'INPUT_CACHE', 'INPUT_FIXTURE_MANIFOLD', 'INPUT_CAPTURE_UNCLOSED'})
        for row in definitions:
            self.assertEqual(row['expected_stderr'], ('PORT13B: ' + row['error'] + '\n').encode())
            self.assertTrue(row['data_C'] and row['data_D'])

    def test_profile_specific_N_opcount_and_group_error_inputs(self):
        rows = {r['name']: r for r in c.negative_definitions13b()}
        for profile, bad_n, bad_ops in (('PORT13B', 65, 65), ('GUARD13B', 2, 17)):
            self.assertEqual(rows[f'{profile}/N{bad_n}']['data_C'], f'{profile} {bad_n}\n'.encode())
            self.assertEqual(rows[f'{profile}/opCount{bad_ops}']['error'], 'INPUT_OPCOUNT')
            for tag, diagnostic in (('P13B', 'INPUT_POINT'), ('U13B', 'INPUT_MATERIAL')):
                self.assertEqual(rows[f'{profile}/{tag}/id']['error'], diagnostic)
                self.assertEqual(rows[f'{profile}/{tag}/tag']['error'], 'INPUT_TAG')
                self.assertEqual(rows[f'{profile}/{tag}/word']['error'], 'INPUT_WORD')
                self.assertEqual(rows[f'{profile}/{tag}/eof']['error'], 'INPUT_EOF')


if __name__ == '__main__':
    unittest.main()
