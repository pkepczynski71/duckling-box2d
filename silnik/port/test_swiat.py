pass                                                                            
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
ROOT = HERE.parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


p = module('world_comparison_test', 'porownaj-swiat.py')
g = p.g


def fixture():
    pass                                                                        

                                                                     
                                                   
       
    ops = (g.world(), g.body(p=(3, -7), q=(0, 1), v=(9, -11), w=5, fixed=1),
           g.op(3, 0, 0), g.body(1, kind=0, p=(13, -17), v=(99, 101), w=103),
           g.op(5, 0, 0), g.world(1), g.transform(1, 1, (777, 888)),
           g.op(6, 0, 2, 2, 0), g.op(1, 0), g.world(2), g.body(3, 2, p=(19, -23)),
           g.op(5, 2, 0), g.op(5, 0, 3))
    rows = (g.Case(1, 'jawna fixtura', ops),)
                                                                         
    w0 = (1, 0, 0, 0x10000, 0, 0, 0, 1, 0)
    w1 = (2, 0, 0, 0x20000, 0, 0, 0, 4, 0)
    w2 = (1, 0, 1, 0x10001, 0, 0, 0, 7, 0)
    b0 = (1, 0, 1, 1, 1, 1, 0, 2, 0)
    b1 = (1, 0, 2, 2, 1, 1, 0, 3, 0)
    tmp1 = (2, 0, 1, 1, 2, 1, 0, 5, 0)
    b2 = (2, 0, 2, 2, 2, 1, 0, 6, 0)
    b3 = (1, 0, 1, 1, 1, 7, 0, 8, 0)
    wh = {0: w0, 1: w1, 2: w2}
    bh = {0: b0, 1: b1, 2: b2, 3: b3}
    f = g.bits
    states = {
        0: (2, f(3), f(-7), f(0), f(1), f(3), f(-7), f(9), f(-11), f(5), 0, 0, 0, 0, 0, 1, 1, 1),
        1: (0, f(13), f(-17), f(1), f(0), f(13), f(-17), 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0),
        2: (2, 0, 0, f(1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0),
        3: (2, f(19), f(-23), f(1), 0, f(19), f(-23), 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0),
    }
                                                                                 
                                                                             
    ledger = [
        (0, 1, w0, (0,), (), (0,), (), ()),
        (0, 2, b0, (0,), (0,), (0,), (0,), (0,)),
        (0, 2, b0, (0,), (0,), (0,), (), ()),
        (0, 2, b1, (0,), (0, 1), (0,), (1,), (1,)),
        (1, 2, b0, (0,), (0, 1), (0,), (1,), (1,)),
        (0, 1, w1, (0, 1), (0, 1), (0, 1), (1,), (1,)),
        (2, 2, b1, (0, 1), (0, 1), (0, 1), (1,), (1,)),
        (0, 2, b2, (0, 1), (0, 1, 2), (0, 1), (1, 2), (1, 2)),
        (0, 1, w0, (0, 1), (0, 1, 2), (1,), (), ()),
        (0, 1, w2, (0, 1, 2), (0, 1, 2), (1, 2), (), ()),
        (0, 2, b3, (0, 1, 2), (0, 1, 2, 3), (1, 2), (3,), (0, 3)),
        (2, 2, b0, (0, 1, 2), (0, 1, 2, 3), (1, 2), (3,), (0, 3)),
        (1, 2, b3, (0, 1, 2), (0, 1, 2, 3), (1, 2), (3,), (0, 3)),
    ]
    records = [('PORT6', (1,)), ('CASE', (1, len(ops)))]
    for seq, ((code, *a), entry) in enumerate(zip(ops, ledger), 1):
        status, kind, result, sw, sb, lw, lb, rb = entry
        records.append(('E', (1, seq, code, *a)))
        if seq == 8:
            for j, phase, h, count, islands in ((1, 1, tmp1, 2, 1), (2, 0, tmp1, 1, 0), (2, 1, b2, 2, 1)):
                records.append(('J', (1, seq, j, phase, *h, 0, 0, count, islands)))
        records.append(('R', (1, seq, status, kind, *result)))
        for s in sw:
            records.append(('V', (1, seq, 1, s, int(s in lw), int(s in lw))))
        for s in sb:
            records.append(('V', (1, seq, 2, s, int(s in rb), int(s in lb))))
        for s in lw:
            children = [b for b in lb if bh[b][5:7] == wh[s][7:9]]
            islands = sum(states[b][0] != 0 for b in children)
            records.append(('W', (1, seq, s, *wh[s][:5], *wh[s][7:9], 0, f(-10), f(400), len(children), 0, islands)))
        for s in lb:
            records.append(('B', (1, seq, s, *bh[s], *states[s])))
        records.append(('Z', (1, seq, len(sw), len(sb), len(lw), len(lb), len(sw)+len(sb), len(lw), len(lb))))
    records += [('ENDCASE', (1,)), ('END', (1,))]
    return rows, '\n'.join(p.format_record(t, v) for t, v in records)+'\n'


def mutate(text, tag, field, value=None, seq=None, ordinal=0):
    lines = text.splitlines()
    found = 0
    for n, line in enumerate(lines):
        t = line.split(' ')
        if t[0] != tag or (seq is not None and int(t[2]) != seq):
            continue
        if found == ordinal:
            i = p.FIELDS[tag].index(field)
            old = int(t[i+1], 10 if i < p.DECIMALS[tag] else 16)
            new = old ^ 1 if value is None else value
            t[i+1] = str(new) if i < p.DECIMALS[tag] else f'{new:08x}'
            lines[n] = ' '.join(t)
            return '\n'.join(lines)+'\n'
        found += 1
    raise AssertionError((tag, field, seq))


class ComparatorTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.good = fixture()

    def rejects(self, bad):
                                                                             
        for side in ('C', 'Duckling', 'both'):
            c = bad if side in ('C', 'both') else self.good
            d = bad if side in ('Duckling', 'both') else self.good
            errors = p.compare(c, d, self.rows)
            self.assertTrue(errors, side)
            for name in (('C:', 'Duckling:') if side == 'both' else (side+':',)):
                self.assertTrue(any(e.startswith(name) for e in errors), errors)
        return '\n'.join(errors)

    def test_hand_ledger_green_lf_crlf_eof(self):
        self.assertEqual(p.compare(self.good, self.good, self.rows), [])
        for version in (self.good.replace('\n', '\r\n'), self.good.rstrip('\n')):
            self.assertEqual(p.compare(self.good, version, self.rows), [])

    def test_missing_record(self):
        self.rejects(self.good.replace(next(l+'\n' for l in self.good.splitlines() if l.startswith('B ')), '', 1))

    def test_extra_record(self):
        self.rejects(self.good+'END 1\n')

    def test_duplicate_record(self):
        line = next(l for l in self.good.splitlines() if l.startswith('V '))+'\n'
        self.rejects(self.good.replace(line, line+line, 1))

    def test_wrong_order(self):
        lines = self.good.splitlines()
        i = next(i for i, l in enumerate(lines) if l.startswith('B '))
        lines[i], lines[i+1] = lines[i+1], lines[i]
        self.rejects('\n'.join(lines)+'\n')

    def test_wrong_seq(self):
        self.rejects(mutate(self.good, 'R', 'seq', 20))

    def test_wrong_case(self):
        self.rejects(mutate(self.good, 'E', 'id', 2))

    def test_truncated_stream(self):
        self.rejects(self.good[:-30])

    def test_nonzero_exit_either_side(self):
        for c, d in ((7, 0), (0, 9), (125, 125)):
            errors = p.compare(self.good, self.good, self.rows, c, d)
            self.assertTrue(errors)
            self.assertIn('field code', '\n'.join(errors))

    def test_over_u32(self):
        self.rejects(mutate(self.good, 'V', 'rawValid', 1 << 32))

    def test_uppercase_short_prefix_and_decimal_hex(self):
        for token in ('0001000A', '10000', '0x010000', '65536'):
            self.rejects(self.good.replace('00010000', token, 1))

    def test_noncanonical_decimal_and_whitespace(self):
        for first in ('PORT6 01', 'PORT6 +1', 'PORT6  1', 'PORT6\t1', 'PORT6 1 '):
            self.rejects(self.good.replace('PORT6 1', first, 1))
        self.rejects(self.good.replace('\n', '\r', 1))

    def test_echo_bit(self):
        self.rejects(mutate(self.good, 'E', 'a1', seq=1))

    def test_position_one_bit_reports_full_location(self):
        detail = self.rejects(mutate(self.good, 'B', 'position.x', seq=2))
        self.assertIn('id 1, seq 2, record B, field position.x', detail)

    def test_world_counters(self):
        for name in ('bodyCount', 'shapeCount', 'islandCount'):
            self.rejects(mutate(self.good, 'W', name, seq=8))

    def test_z_counts_even_when_both_sides_agree(self):
        for name in p.FIELDS['Z'][2:]:
            self.rejects(mutate(self.good, 'Z', name, seq=8))

    def test_v_raw_and_game_independent(self):
        self.rejects(mutate(self.good, 'V', 'rawValid', seq=11, ordinal=3))
        self.rejects(mutate(self.good, 'V', 'gameValid', seq=11, ordinal=3))

    def test_owner_birth_and_halves(self):
        for name in ('owner.low', 'owner.high', 'birth.low', 'birth.high', 'packed.low', 'packed.high'):
            self.rejects(mutate(self.good, 'B', name, seq=11))
                                                                             
        bad = mutate(self.good, 'R', 'birth.low', 0, seq=10)
        self.rejects(mutate(bad, 'R', 'birth.high', 7, seq=10))

    def test_stale_foreign_priority_and_refused_mutation(self):
        for seq, status in ((5, 0), (7, 1), (12, 0), (13, 2)):
            self.rejects(mutate(self.good, 'R', 'status', status, seq=seq))
        self.rejects(mutate(self.good, 'B', 'position.x', g.bits(777), seq=7))

    def test_static_body_has_no_state_and_fixed_keeps_initial_w(self):
        self.rejects(mutate(self.good, 'B', 'linearVelocity.x', g.bits(99), seq=4))
        self.rejects(mutate(self.good, 'B', 'angularVelocity', 0, seq=2))
        self.rejects(mutate(self.good, 'B', 'isAwake', 1, seq=4))

    def test_j_each_field_and_short_churn(self):
        for name in p.FIELDS['J'][2:]:
            self.rejects(mutate(self.good, 'J', name, seq=8))
        line = next(l+'\n' for l in self.good.splitlines() if l.startswith('J '))
        self.rejects(self.good.replace(line, '', 1))
        self.assertIn('j 1, phase 1, record J', self.rejects(mutate(self.good, 'J', 'oldGameValid', seq=8)))


class InputTests(unittest.TestCase):
    def setUp(self):
        self.rows, _ = fixture()
        self.text = g.encode(self.rows)

    def bad_word(self, index, value):
        rows = copy.deepcopy(self.rows)
        op = list(rows[0].ops[1]); op[index+1] = value
        changed = (g.Case(1, '', (rows[0].ops[0], tuple(op), *rows[0].ops[2:])),)
        return g.encode(changed)

    def test_input_transport_roundtrip(self):
        for decimal in (False, True):
            encoded = g.encode(self.rows, decimal)
            for variant in (encoded, encoded.replace('\r\n', '\n')+'\n', encoded.replace('\r\n', '\n').replace('\n', '\r\n')):
                self.assertEqual(g.read_input(variant, decimal, 1)[0].ops, self.rows[0].ops)

    def test_nan_inf_rotation_type_flags_and_unused(self):
        for index, value in ((3, 0x7fc00000), (4, 0x7f800000), (7, 0xff800000),
                             (6, 0), (2, 3), (10, 2), (23, 0x80000000)):
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                g.read_input(self.bad_word(index, value), expected_count=1)

    def test_input_decimal_overflow_and_negative(self):
        text = g.encode(self.rows, True)
        for token in ('4294967296', '-1', '+0', '00', '0x0'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                g.read_input(text.replace('O 1 0 0 ', 'O 1 0 '+token+' ', 1), True, 1)

    def test_truncation_extra_words_sequence_and_count(self):
        for text in (self.text[:-40], self.text+'\nEND 1', self.text.replace('O 2 2', 'O 3 2', 1),
                     self.text.replace('C 1 13', 'C 1 12', 1), self.text.replace('00000000', '000000000', 1)):
            with self.assertRaises(ValueError):
                g.read_input(text, expected_count=1)

    def test_saved_file_is_deterministic_and_64_cases(self):
        rows = g.build()
        self.assertEqual(len(rows), 64)
        self.assertEqual(sum(len(c.ops) for c in rows), 1287)
        for decimal, name in ((False, 'przypadki-swiat.csv'), (True, 'przypadki-swiat-stdin.csv')):
            text = (HERE/name).read_bytes().decode('ascii')
            self.assertEqual(text, g.encode(rows, decimal))
            self.assertEqual([c.ops for c in g.read_input(text, decimal)], [c.ops for c in rows])

    def test_growth_and_churn_population(self):
        rows = g.build()
        for c in rows[40:48]:
            creates = [o for o in c.ops if o[0] == 2]
            self.assertGreaterEqual(len(creates), 65)
            self.assertEqual(len({o[4:6] for o in creates[:65]}), 65)
            self.assertEqual({o[3] for o in creates}, {0, 1, 2})
            model = p.Life(); model.begin()
            maximum = 0
            for seq, op in enumerate(c.ops, 1):
                list(model.execute(c.id, seq, op))
                maximum = max(maximum, sum(model.body_live(b) for b in model.bodies.values()))
            self.assertGreaterEqual(maximum, 65)
        self.assertEqual([o[3] for o in rows[58].ops if o[0] == 6], [65535])
        self.assertEqual([o[3] for o in rows[59].ops if o[0] == 6], [65536])


class LifetimeTests(unittest.TestCase):
    def test_full_wrap_old_raw_revives_game_stays_dead_and_no_mutation(self):
        c = g.build()[59]
        model = p.Life(); model.begin()
        trace_count = 0
        for seq, op in enumerate(c.ops, 1):
            for tag, values in model.execute(c.id, seq, op):
                if tag == 'J':
                    trace_count += 1
                    if values[2:] and values[2:4] == (65536, 1):
                        self.assertEqual(values[6], 1)              
                        self.assertEqual(values[13:15], (1, 0))
                if tag == 'R' and seq in (5, 6, 7):
                    self.assertEqual(values[2], 1)
            if seq in (4, 5, 6, 7):
                self.assertEqual(model.bodies[1].state[1:3], (0, 0))
                self.assertTrue(model.body_live(model.bodies[1]))
        self.assertEqual(trace_count, 131071)
        self.assertEqual(model.bodies[1].state[1:3], (g.bits(47), g.bits(-53)))

    def test_u64_carry_reservation_refusal_keeps_registers_and_counter(self):
        self.assertEqual(p.next_ticket(0xffffffff), 0x100000000)
        self.assertEqual(p.next_ticket(g.U64-1), g.U64)
        self.assertIsNone(p.next_ticket(g.U64))
        model = p.Life(g.U64-2); model.begin()
        status, w = model.create_world(0, g.world()[1:]); self.assertEqual(status, 0)
        status, b = model.create_body(0, w, g.body()[1:]); self.assertEqual(status, 0)
        before = (model.last, dict(model.worlds), dict(model.bodies), model.counters(w))
        self.assertEqual(model.create_world(0, g.world()[1:]), (3, None))
        self.assertEqual(model.create_body(0, w, g.body()[1:]), (3, None))
        self.assertEqual((model.last, model.worlds, model.bodies, model.counters(w)), before)
        self.assertEqual(w.handle()[7:9], (0xfffffffe, 0xffffffff))
        self.assertEqual(b.handle()[7:9], (0xffffffff, 0xffffffff))
        model.destroy_world(w)
        self.assertEqual(model.create_body(0, w, g.body()[1:]), (1, None))
        self.assertIs(model.bodies[0], b)
        self.assertEqual(model.last, g.U64)

    def test_ticket_no_float_roundtrip_above_2_to_53(self):
        m = p.Life(2**53); m.begin()
        _, w = m.create_world(0, g.world()[1:])
        self.assertEqual(w.handle()[7:9], (1, 0x200000))

    def test_exact_record_budget(self):
        counts, size = p.measure(g.build())
        self.assertEqual({t: counts[t] for t in ('E', 'R', 'V', 'W', 'B', 'J', 'Z')},
                         dict(E=1287, R=1287, V=24639, W=1461, B=21823, J=262174, Z=1287))
        self.assertEqual(size, 41537752)
        self.assertLessEqual(2*size, 128*1024**2)


class SourceTests(unittest.TestCase):
    def test_public_c_only_no_private_includes_or_expected_physics(self):
        text = (HERE/'kontrola-swiat.c').read_text(encoding='utf-8')
        includes = [l for l in text.splitlines() if l.startswith('#include')]
        self.assertEqual([l for l in includes if 'box2d/' in l], ['#include <box2d/box2d.h>'])
        self.assertFalse(any('"' in l for l in includes))
        for forbidden in ('b2GetWorld', 'b2GetBody', 'b2AllocId', 'b2FreeId', 'RemoveSwap', 'b2_worlds'):
            self.assertNotIn(forbidden, text)
        for getter in ('b2Body_GetPosition', 'b2Body_GetRotation', 'b2Body_GetWorldCenterOfMass',
                       'b2Body_GetLinearVelocity', 'b2Body_GetMass', 'b2World_GetCounters',
                       'b2StoreBodyId', 'b2StoreWorldId', 'b2Body_IsValid', 'b2World_IsValid'):
            self.assertIn(getter+'(', text)
        self.assertIn('--test-tickets', text)


@unittest.skipUnless(os.environ.get('SWIAT_C_BIN'), 'SWIAT_C_BIN is not set')
class NativeCTests(unittest.TestCase):
    def setUp(self):
        self.executable = Path(os.environ['SWIAT_C_BIN'])
        self.assertTrue(self.executable.is_file(), 'missing zbudowanej kontroli C')
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.input = Path(self.temp.name)/'input.csv'
                                                                         
        small = g.build()[1].ops
        self.rows = (g.Case(1, 'E8c586909c59a case', small), *(
            g.Case(i, 'E9617961b221b E98fc34a4e5dc', (g.world(), g.op(1, 0))) for i in range(2, 65)))

    def run_c(self, text):
        self.input.write_bytes(text.encode('ascii'))
        return subprocess.run([str(self.executable), str(self.input)], capture_output=True, timeout=10)

    def test_small_public_cycle_lf_crlf_eof_and_u64_fixture(self):
        text = g.encode(self.rows).replace('\r\n', '\n')
        for variant in (text+'\n', (text+'\n').replace('\n', '\r\n'), text):
            result = self.run_c(variant)
            self.assertEqual(result.returncode, 0, result.stderr)
            p.validate_output(result.stdout.decode('ascii'), self.rows)
        result = subprocess.run([str(self.executable), '--test-tickets'], capture_output=True, timeout=10)
        self.assertEqual((result.returncode, result.stdout), (0, b'TICKETS OK\n'), result.stderr)

    def test_c_reader_rejects_sixteen_corruptions(self):
        lines = g.encode(self.rows).replace('\r\n', '\n').splitlines()
                                                                       
        def change(line, token, value):
            changed = list(lines); words = changed[line].split(' ')
            words[token] = value; changed[line] = ' '.join(words)
            return '\n'.join(changed)
        variants = [change(2, 4, '7fc00000'), change(2, 6, '7f800000'), change(2, 6, '00000000'),
                    change(2, 7, '00000001'), change(2, 26, '80000000'), change(2, 6, '43C80000'),
                    change(2, 3, '100000000'), change(2, 3, '0000000'), change(2, 2, '7'),
                    change(2, 1, '2'), change(2, 1, '01'), change(3, 5, '00000003'),
                    change(3, 8, '00000000'), change(3, 13, '00000002'),
                    '\n'.join(lines).replace('64\n', '64\x00hidden\n', 1),
                    '\n'.join(lines)[:-30]]
        self.assertEqual(len(variants), 16)
        for n, text in enumerate(variants):
            with self.subTest(corruption=n):
                result = self.run_c(text)
                self.assertNotEqual(result.returncode, 0, 'C accepted invalid input')


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = patch.dict(os.environ, RESULT_DIR=str(self.root/'out'), RUNNER_TEMP=str(self.root/'temp'))
        env.start(); self.addCleanup(env.stop)
        argv = patch.object(sys, 'argv', ['ci.py', 'test-world'])
        argv.start(); self.addCleanup(argv.stop)
        self.ci = module('port_ci_world_test', 'ci.py')

    def test_all_old_packages_exclude_new_modules_and_keep_bytes(self):
        physics = self.root/'silnik/fizyka'; physics.mkdir(parents=True)
        names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk', 'drzewo.dk', 'szeroka.dk', 'zbior.dk')
        for name in (*names, 'swiat.dk', 'gra.dk'):
            (physics/name).write_text('INVALID new file '+name)
        with patch.object(self.ci, 'ROOT', self.root):
            for method, count in ((self.ci.previous_physics, 4), (self.ci.tree_physics, 5), (self.ci.broad_physics, 7)):
                target = method()
                self.assertEqual(sorted(p.name for p in target.iterdir()), sorted(names[:count]))
                for name in names[:count]:
                    self.assertEqual((target/name).read_bytes(), (physics/name).read_bytes())

    def test_world_missing_red_and_old_outputs_preserved(self):
        names = ('duckling.csv', 'duckling-wiel.csv', 'duckling-ruch.csv', 'duckling-drzewo.csv', 'duckling-szeroka.csv')
        for n in names:
            (self.ci.OUT/n).write_text(n)
        with patch.object(self.ci, 'PORT', self.root/'absent'):
            self.assertEqual(self.ci.duckling_world('never-run'), 1)
        self.assertEqual((self.ci.OUT/'duckling-swiat-kod.csv').read_text(), '125\n')
        for n in names:
            self.assertEqual((self.ci.OUT/n).read_text(), n)

    def test_failed_compile_preserves_previous_results_and_links_no_c(self):
        port = self.root/'silnik/port'; port.mkdir(parents=True)
        physics = self.root/'silnik/fizyka'; physics.mkdir()
        (port/'swiat.dk').touch()
        for n in ('swiat.dk', 'gra.dk'):
            (physics/n).touch()
        old = self.ci.OUT/'duckling-szeroka.csv'; old.write_text('old measured result')
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci, 'ROOT', self.root),\
                patch.object(self.ci.base, 'run', return_value=19):
            self.assertEqual(self.ci.duckling_world('never-run'), 19)
        self.assertEqual(old.read_text(), 'old measured result')
        manifest = json.loads((self.ci.OUT/'duckling-swiat-manifest.json').read_text())
        self.assertEqual(manifest['packages'][0]['path'], str(physics))
        self.assertNotIn('box2d', json.dumps(manifest).replace(json.dumps(str(ROOT.resolve()))[1:-1], '').lower())

    def test_checks_run_even_after_comparison_failure(self):
        with patch.object(self.ci.base, 'run', side_effect=[1, 0]) as run:
            self.assertEqual(self.ci.check_world(), 1)
        self.assertEqual([c.args[0] for c in run.call_args_list], ['porownanie-swiat', 'sprawdziany-swiat'])

    def test_summary_cannot_ignore_world_missing_or_red(self):
        stages = ('c', 'duckling', 'check', 'check-ruch', 'check-drzewo', 'check-szeroka', 'c-swiat')
        for stage in stages:
            (self.ci.OUT/f'etap-port-{stage}-kod.csv').write_text('0\n')
        env = {n+'_OUTCOME': 'success' for n in ('C', 'DUCKLING', 'CHECK', 'RUCH', 'DRZEWO', 'SZEROKA', 'C_SWIAT', 'SWIAT')}
        with patch.dict(os.environ, env), patch('builtins.print'):
            self.ci.summary(include_broad=True, include_world=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')
            (self.ci.OUT/'etap-port-check-swiat-kod.csv').write_text('0\n')
            self.ci.summary(include_broad=True, include_world=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '0\n')
            with patch.dict(os.environ, SWIAT_OUTCOME='failure'):
                self.ci.summary(include_broad=True, include_world=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')

    def test_c_build_public_release_hashes_before_and_after(self):
        source = self.ci.base.TEMP/'box2d'
        (source/'src').mkdir(parents=True)
        (source/'include/box2d').mkdir(parents=True)
        files = [source/f'src/f{i}.c' for i in range(63)]
        for f in files:
            f.write_text('unchanged source fixture')
        sums = ''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(source).as_posix()}\n' for f in sorted(files))
        port = self.root/'port'; port.mkdir()
        (port/'fixtures/norms/KONTRAKT-6.json').parent.mkdir(parents=True,exist_ok=True)
        (port/'fixtures/norms/KONTRAKT-6.json').write_text(sums)
        calls = []
        def need(name, command, **kwargs):
            calls.append((name, list(map(str, command))))
            if name == 'kontrola-swiat-kompilacja':
                Path(command[-1]).write_bytes(b'fixture binary')
            if name == 'kontrola-swiat-bilety':
                kwargs['stdout'].write_text('TICKETS OK\n')
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci.base, 'need', side_effect=need):
            self.ci.c_world()
        build = next(cmd for name, cmd in calls if name == 'kontrola-swiat-kompilacja')
        for flag in ('-std=c17', '-DNDEBUG', '-DBOX2D_DISABLE_SIMD', '-Werror', '-ffp-contract=off', '-fno-fast-math'):
            self.assertIn(flag, build)
        self.assertNotIn('-I'+str(source/'src'), build)
        self.assertTrue(any(v.endswith('libbox2d.a') for v in build))
        self.assertIn(('kontrola-swiat-bilety', [str(self.ci.base.TEMP/'kontrola-swiat'), '--test-tickets']), calls)
        files[0].write_text('changed')
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci.base, 'need', side_effect=need),\
                self.assertRaisesRegex(self.ci.base.StepFailed, 'checksum'):
            self.ci.c_world()

    def test_workflow_always_and_budget_unchanged(self):
        from public_ci import check
        check(self)


class FollowupInputs(unittest.TestCase):
    def test_open_f32_rotation_bounds_and_review_witness(self):
        self.assertEqual(g.bits(g.ROT_LOWER), 0x3f7fd8ae)
        self.assertEqual(g.bits(g.ROT_UPPER), 0x3f8013a9)
                                                                            
        for word, qq, valid in ((0x3f7fec55, 0x3f7fd8ac, False), (0x3f7fec56, 0x3f7fd8ae, False),
                                 (0x3f8009d4, 0x3f8013a9, False), (0x3f8009d5, 0x3f8013ab, False),
                                 (0x3f800400, 0x3f800800, True)):
            self.assertEqual(g.bits(g.norm_squared(g.number(word), 0)), qq)
            self.assertEqual(g.valid_rotation(g.number(word), 0), valid)
        self.assertFalse(g.valid_rotation(g.number(0x7f7fffff), 0))

    def test_added_cases_and_pinned_original_inputs(self):
        rows = g.cases()
        self.assertEqual(len(rows), 72)
        self.assertEqual([c.ops for c in rows[:64]], [c.ops for c in g.build()])
        self.assertEqual([c.id for c in rows[64:]], list(range(65, 73)))
        self.assertTrue(any(o[0] == 2 and o[6] and o[7] for c in rows[64:] for o in c.ops))
        self.assertTrue(any(o[0] == 2 and o[6] == 0x3f800400 for c in rows[64:] for o in c.ops))
        for decimal, name in ((False, 'przypadki-swiat-pelne.csv'), (True, 'przypadki-swiat-pelne-stdin.csv')):
            self.assertEqual((HERE/name).read_bytes(), g.encode(rows, decimal).encode('ascii'))
        g.verify_input_hashes(HERE, HERE/'wejscia-swiat-sha256.json')
        for name, digest in g.LEGACY_SHA256.items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(), digest)

    def test_publication_normalization_is_detected_even_with_rewritten_full_hash(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            directory = Path(directory)
            sums = json.loads((HERE/'wejscia-swiat-sha256.json').read_bytes())
            for name in g.INPUT_NAMES:
                (directory/name).write_bytes((HERE/name).read_bytes())
            target = directory/'przypadki-swiat-pelne.csv'
            target.write_bytes(target.read_bytes().replace(b'\r\n', b'\n'))
            manifest = directory/'sums.json'
            manifest.write_text(json.dumps(sums))
            with self.assertRaisesRegex(ValueError, 'bytes'):
                g.verify_input_hashes(directory, manifest)
            sums[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(sums))
            with self.assertRaisesRegex(ValueError, 'first 64'):
                g.verify_input_hashes(directory, manifest)

    def test_paired_negative_inputs_and_original_sixteen_unchanged(self):
        n = module('world_negatives_test', 'ujemne-swiat.py')
        variants = n.variants()
        self.assertEqual(len(variants), 23)
        for name, c, d in variants:
            for decimal, data in ((False, c), (True, d)):
                with self.subTest(name=name, decimal=decimal), self.assertRaises(ValueError):
                    g.read_input(data.decode('ascii'), decimal)
                                                                               
        from types import SimpleNamespace
        original = NativeCTests('test_c_reader_rejects_sixteen_corruptions')
        original.rows = n.small_cases()
        seen = []
        def capture(text):
            seen.append(text.encode('ascii'))
            return SimpleNamespace(returncode=2)
        original.run_c = capture
        original.test_c_reader_rejects_sixteen_corruptions()
        self.assertEqual(seen, [c for _, c, _ in variants[:16]])


class FollowupCI(unittest.TestCase):
    setUp = CITests.setUp

    def test_fixture_build_same_options_no_c_physics(self):
        def need(name, command, **kwargs):
            artifact = Path(command[command.index('-a')+1]); artifact.mkdir(exist_ok=True)
            (artifact/'program').write_bytes(b'\x7fELFfixture')
            (artifact/'program').chmod(0o755)
        with patch.object(self.ci.base, 'need', side_effect=need) as call:
            binary = self.ci.compile_world_fixture('duckc', 'fixture', HERE/'proba-bilety.dk', ROOT/'silnik/fizyka')
        self.assertEqual(binary.read_bytes(), b'\x7fELFfixture')
        self.assertEqual(list(call.call_args.args[1])[-2:], ['-O', '0'])
        manifest = json.loads((self.ci.OUT/'fixture-manifest.json').read_bytes())
        self.assertEqual(manifest['packages'][0]['path'], str(ROOT/'silnik/fizyka'))
        self.assertNotIn('box2d', json.dumps(manifest).replace(json.dumps(str(ROOT.resolve()))[1:-1], '').lower())

    def test_ticket_stages_reject_wrong_output_and_exit(self):
        for result, wanted in (((0, b'BILETY OK\n'), 0), ((3, b'BILETY OK\n'), 1),
                               ((0, b'BILETY OK\r\n'), 1), ((0, b''), 1)):
            with patch.object(self.ci, 'world_duckc', return_value='duckc'),\
                    patch.object(self.ci, 'compile_world_fixture', return_value=self.ci.OUT/'binary'),\
                    patch.object(self.ci, 'run_world_fixture', return_value=result):
                self.assertEqual(self.ci.tickets_standalone(), wanted)
                self.assertEqual(self.ci.tickets_transport(), wanted)

    def test_mutations_exactly_once_and_never_in_repository(self):
        repo = self.root/'repo'; physics = repo/'silnik/fizyka'; physics.mkdir(parents=True)
        port = repo/'silnik/port'; port.mkdir()
        for name in ('gra.dk', 'swiat.dk'):
            (physics/name).write_bytes((ROOT/'silnik/fizyka'/name).read_bytes())
        for name in ('proba-bilety.dk', 'swiat.dk'):
            (port/name).write_bytes((HERE/name).read_bytes())
        before = {f: f.read_bytes() for f in repo.rglob('*.dk')}
        (self.ci.OUT/'przypadki-swiat-pelne-stdin.csv').write_bytes(b'fixture corpus')
        def compile_copy(duckc, name, driver, copied):
            self.assertNotEqual(copied, physics)
            self.assertNotEqual(driver.parent, port)
            return self.ci.OUT/'binary'
        def execute(name, binary, data):
            island = 'island' in name
            (self.ci.OUT/(name+'-wykonanie-stderr.csv')).write_bytes(b'BLAD: indeks wyspy.\n' if island else b'')
            return (4 if island else 2), b''
        with patch.object(self.ci, 'ROOT', repo), patch.object(self.ci, 'PORT', port),\
                patch.object(self.ci, 'world_duckc', return_value='duckc'),\
                patch.object(self.ci, 'compile_world_fixture', side_effect=compile_copy),\
                patch.object(self.ci, 'run_world_fixture', side_effect=execute):
            self.assertEqual(self.ci.world_mutations(), 0)
            rows = json.loads((self.ci.OUT/'mutacje-swiat-wynik.json').read_bytes())
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(r['detected'] for r in rows))
            with patch.object(self.ci, 'run_world_fixture', return_value=(0, b'BILETY OK\n')):
                self.assertEqual(self.ci.world_mutations(), 1)
        self.assertEqual({f: f.read_bytes() for f in before}, before)
        target = self.root/'replace.dk'
        for text in ('zero', 'one one'):
            target.write_text(text)
            with self.assertRaises(self.ci.base.StepFailed):
                self.ci.replace_once(target, 'one', 'two')

    def test_negative_stage_invokes_c_with_file_argument_and_duckling_stdin(self):
        for name in ('kontrola-swiat-bin', 'duckling-swiat-bin'):
            (self.ci.OUT/name).touch()
        calls = []
        def run(name, command, **kwargs):
            calls.append(command)
            kwargs['stdout'].write_bytes(b'')
            d = name.endswith('-duckling-wykonanie')
            (self.ci.OUT/(name+'-stderr.csv')).write_bytes(b'BLAD: input\n' if d else b'input\n')
            return 3 if d else 2
        with patch.object(self.ci.base, 'run', side_effect=run):
            self.assertEqual(self.ci.world_negative(), 0)
        self.assertEqual(len(calls), 46)
        self.assertTrue(all(len(command) == 2 and Path(command[1]).is_file() for command in calls[::2]))
        self.assertTrue(all(command[:3] == ['bash', '-c', 'exec "$1" < "$2"'] for command in calls[1::2]))
        with patch.object(self.ci.base, 'run', side_effect=lambda *a, **kw: (kw['stdout'].write_bytes(b''), 0)[1]):
            self.assertEqual(self.ci.world_negative(), 1)

    def evidence_fixture(self):
        out = self.ci.OUT
        def code(name, value=0):
            (out/(name+'-kod.csv')).write_text(str(value)+'\n')
        for name in ('bilety-proba', 'bilety-port', 'bilety-port-crlf'):
            code(name+'-wykonanie'); (out/(name+'.csv')).write_bytes(b'BILETY OK\n')
        for name in ('bilety-proba-kompilacja', 'duckling-swiat-kompilacja'):
            code(name)
        for name in ('bilety-proba-bin', 'duckling-swiat-bin', 'bilety-proba-manifest.json', 'duckling-swiat-manifest.json'):
            (out/name).touch()
        rows = []
        for mutation, *_ in self.ci.WORLD_MUTATIONS:
            for probe in (('port',) if mutation == 'island' else ('proba', 'port')):
                tag = 'mutacja-'+mutation+'-'+probe
                actual = 4 if mutation == 'island' else 2
                code(tag+'-kompilacja'); code(tag+'-wykonanie', actual)
                (out/(tag+'.csv')).write_bytes(b'')
                (out/(tag+'-wykonanie-stderr.csv')).write_bytes(b'BLAD: indeks wyspy.\n' if actual == 4 else b'')
                rows.append(dict(mutation=mutation, probe=probe, actual=actual, detected=True, expected='4' if actual == 4 else '!=0'))
        (out/'mutacje-swiat-wynik.json').write_text(json.dumps(rows))
        n = module('world_negative_evidence', 'ujemne-swiat.py')
        rows = []
        for name, _, _ in n.variants():
            for side, actual in (('c', 2), ('duckling', 3)):
                tag = 'ujemny-'+name+'-'+side
                code(tag+'-wykonanie', actual)
                (out/(tag+'.csv')).write_bytes(b'')
                (out/(tag+'-wykonanie-stderr.csv')).write_bytes(b'BLAD: input\n')
                rows.append(dict(input=name, side=side, actual=actual, expected=actual, ok=True))
        (out/'ujemne-swiat-wynik.json').write_text(json.dumps(rows))

    def test_missing_evidence_green_mutant_and_wrong_codes_cannot_pass(self):
        self.evidence_fixture()
        self.assertTrue(self.ci.world_evidence())
        for name, bad in (('bilety-proba.csv', b''), ('mutacja-carry-proba-wykonanie-kod.csv', b'0\n'),
                          ('mutacja-island-port-wykonanie-kod.csv', b'3\n'),
                          ('ujemny-nan-duckling-wykonanie-stderr.csv', b'no BLAD prefix'),
                          ('ujemny-nan-c-wykonanie-kod.csv', b'0\n')):
            path = self.ci.OUT/name; original = path.read_bytes()
            path.write_bytes(bad)
            self.assertFalse(self.ci.world_evidence(), name)
            path.write_bytes(original)
            path.unlink()
            self.assertFalse(self.ci.world_evidence(), name+' missing')
            path.write_bytes(original)
        self.assertTrue(self.ci.world_evidence())

    def test_complete_workflow_requires_every_new_stage_and_result(self):
        from public_ci import check
        check(self)


class Round2CI(unittest.TestCase):
    pass                                                                         
    setUp = CITests.setUp

    def positive_fixture(self):
        n = module('round2_positive_fixture', 'ujemne-swiat.py')
        output = ''.join(p.format_record(tag, values)+'\n' for tag, values in p.expected_records(n.small_cases())).encode('ascii')
        inputs = self.ci.OUT/'wejscia-swiat'; inputs.mkdir(exist_ok=True)
        for side, decimal in (('c', False), ('duckling', True)):
            tag = 'baza-ujemnych-'+side
            (inputs/(tag+'.csv')).write_bytes(n.g.encode(n.small_cases(), decimal).encode('ascii'))
            (self.ci.OUT/(tag+'.csv')).write_bytes(output)
            (self.ci.OUT/(tag+'-wykonanie-kod.csv')).write_text('0\n')
        return output

    def round2_evidence_fixture(self):
        FollowupCI.evidence_fixture(self)
        self.positive_fixture()
        n = module('round2_negative_fixture', 'ujemne-swiat.py')
        rows = []
        for name, _, _ in (*n.variants(), *n.boundary_variants()):
            (self.ci.OUT/('ujemny-'+name+'-duckling-wykonanie-stderr.csv')).write_bytes(n.expected_diagnostic(name))
        for name, _, _ in n.boundary_variants():
            for side, actual in (('c', 2), ('duckling', 3)):
                tag = 'ujemny-'+name+'-'+side
                (self.ci.OUT/(tag+'-wykonanie-kod.csv')).write_text(str(actual)+'\n')
                (self.ci.OUT/(tag+'.csv')).write_bytes(b'')
                if side == 'c':
                    (self.ci.OUT/(tag+'-wykonanie-stderr.csv')).write_bytes(b'input\n')
                rows.append(dict(input=name, side=side, expected=actual, actual=actual, ok=True))
        (self.ci.OUT/'ujemne-granice-swiat-wynik.json').write_text(json.dumps(rows))

    def test_exact_native_boundary_inputs_open_interval(self):
        n = module('round2_boundary_inputs', 'ujemne-swiat.py')
        self.assertEqual(len(n.variants()), 23)
        self.assertEqual([name for name, *_ in n.boundary_variants()], ['rotation-at-lower', 'rotation-at-upper'])
        for (_, c, d), word, qq in zip(n.boundary_variants(), (0x3f7fec56, 0x3f8009d4), (0x3f7fd8ae, 0x3f8013a9)):
            self.assertEqual(int(c.splitlines()[3].split()[8], 16), word)
            self.assertEqual(int(d.splitlines()[3].split()[8]), word)
            self.assertEqual(g.bits(g.norm_squared(g.number(word), 0)), qq)
            for decimal, data in ((False, c), (True, d)):
                with self.assertRaisesRegex(ValueError, 'rotation'):
                    g.read_input(data.decode('ascii'), decimal)

    def test_valid_base_is_executed_on_both_programs_and_fully_checked(self):
        output = self.positive_fixture()
        def execute(tag, binary, data, file_argument=False):
            self.assertEqual(file_argument, tag.endswith('-c'))
            return 0, output
        with patch.object(self.ci, 'run_world_fixture', side_effect=execute) as call, patch('builtins.print'):
            self.assertEqual(self.ci.world_positive(), 0)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(self.ci.world_positive_errors(), [])
        for side in ('c', 'duckling'):
            path = self.ci.OUT/('baza-ujemnych-'+side+'.csv')
            for bad in (b'', output[:-10], output.replace(b'PORT6 64', b'PORT6 72', 1)):
                path.write_bytes(bad)
                self.assertTrue(self.ci.world_positive_errors())
            path.write_bytes(output)
            code = self.ci.OUT/('baza-ujemnych-'+side+'-wykonanie-kod.csv')
            code.write_text('3\n')
            self.assertTrue(self.ci.world_positive_errors())
            code.write_text('0\n')
        path = self.ci.OUT/'wejscia-swiat/baza-ujemnych-duckling.csv'
        path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
        self.assertTrue(self.ci.world_positive_errors())

    def test_bad_base_prevents_all_negative_executions(self):
        with patch.object(self.ci, 'world_positive_errors', return_value=['Duckling rejects N=64']),\
                patch.object(self.ci, 'run_world_fixture') as run, patch.object(self.ci, 'world_negative') as old:
            self.assertEqual(self.ci.world_negative_round2(), 1)
        run.assert_not_called(); old.assert_not_called()

    def test_native_negative_stage_requires_field_diagnostic_for_all_25_pairs(self):
        self.positive_fixture()
        n = module('round2_negative_runner', 'ujemne-swiat.py')
        def execute(tag, binary, data, file_argument=False):
            name, side = tag.removeprefix('ujemny-').rsplit('-', 1)
            (self.ci.OUT/(tag+'-wykonanie-stderr.csv')).write_bytes(n.expected_diagnostic(name) if side == 'duckling' else b'input\n')
            return (2 if side == 'c' else 3), b''
        with patch.object(self.ci, 'run_world_fixture', side_effect=execute) as run:
            self.assertEqual(self.ci.world_negative_round2(), 0)
        self.assertEqual(run.call_count, 50)
        with patch.object(self.ci, 'run_world_fixture', side_effect=execute),\
                patch.object(self.ci, 'world_negative', return_value=0):
            (self.ci.OUT/'ujemny-nan-duckling-wykonanie-stderr.csv').write_bytes(b'BLAD: liczba przypadkow.\n')
            self.assertEqual(self.ci.world_negative_round2(), 1)

    def test_round2_evidence_rejects_wrong_cause_and_missing_or_broken_base(self):
        self.round2_evidence_fixture()
        self.assertTrue(self.ci.world_evidence_round2())
        n = module('round2_wrong_cause_inputs', 'ujemne-swiat.py')
        old_inputs, boundaries = n.variants(), n.boundary_variants()
                                                                              
                                                                                   
        with patch.object(self.ci, 'world_positive_errors', return_value=[]),\
                patch.object(self.ci, 'world_evidence', return_value=True),\
                patch.object(self.ci, 'world_module', return_value=n),\
                patch.object(n, 'variants', return_value=old_inputs),\
                patch.object(n, 'boundary_variants', return_value=boundaries):
            for name, _, _ in (*old_inputs, *boundaries):
                path = self.ci.OUT/('ujemny-'+name+'-duckling-wykonanie-stderr.csv')
                before = path.read_bytes()
                for bad in (b'BLAD: liczba przypadkow.\n', b'BLAD:\n', before.rstrip(b'\n')+b' extra\n'):
                    path.write_bytes(bad)
                    self.assertFalse(self.ci.world_evidence_round2(), name)
                path.write_bytes(before)
        for name in ('baza-ujemnych-c.csv', 'baza-ujemnych-duckling-wykonanie-kod.csv',
                     'ujemne-granice-swiat-wynik.json', 'ujemny-rotation-at-lower-c-wykonanie-kod.csv'):
            path = self.ci.OUT/name; before = path.read_bytes()
            path.unlink()
            self.assertFalse(self.ci.world_evidence_round2(), name)
            path.write_bytes(before)
        self.assertTrue(self.ci.world_evidence_round2())

    def test_round2_workflow_and_summary_require_positive_stage_and_evidence(self):
        from public_ci import check
        check(self)


if __name__ == '__main__':
    unittest.main()
