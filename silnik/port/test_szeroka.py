pass                                                                            

                                                                           
   
from collections import Counter
from dataclasses import replace
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


g = module('szeroka_test_inputs', 'przypadki-szeroka.py')
p = module('szeroka_test_compare', 'porownaj-szeroka.py')


def line(tag, *words):
    return tag+' '+ ' '.join(map(str, words))


def hs(case, k, kind, capacity, keys):
                                                                                 
                                                                                 
    slots = [(key & g.NULL, key >> 32, i+1) for i, key in enumerate(sorted(keys))]
    slots += [(0, 0, 0)]*(capacity-len(slots))
    return line('HS', case, k, kind, capacity, len(keys), *(v for item in slots for v in item))


def fixture(custom=1):
    bodies = (2, 2, 2)
    shapes = (g.shape(0, generation=65535), g.shape(1), g.shape(2))
    ops = (g.create(0), g.create(1), g.create(2), g.op(5), g.op(5), g.query())
    c = g.Case(1, 'handwritten', 0, 1, ops, bodies, shapes, custom=custom, world=3)
    out = [line('PORT5', 1), line('I', 1, *c.header)]
    out += [line('EB', 1, n, t) for n, t in enumerate(bodies)]
    out += [line('ES', 1, n, *s) for n, s in enumerate(shapes)]
    keys = {0: 2, 1: 6, 2: 14}
    box = tuple(map(g.bits, (0, 0, 2, 2)))
    pairs = set()
    for k, op in enumerate(ops, 1):
        live = list(range(min(k, 3)))
        moved = live if k < 4 else []
        out.append(line('O', 1, k, *op, *([keys[k-1]] if k <= 3 else [])))
        if k == 4:
            for n in range(3):
                for j, tree in enumerate((1, 0, 2)):
                    hits = [(keys[x] >> 2, x) for x in range(3)] if tree == 2 else []
                    out.append(line('Q', 1, k, n*3+j, n, keys[n], tree,
                                    5 if tree == 2 else 0, len(hits), len(hits), *(v for hit in hits for v in hit)))
            if custom:
                for f, (a, b) in enumerate(((0, 1), (0, 2), (1, 2))):
                    out.append(line('F', 1, k, f, a+1, 3, shapes[a][7], b+1, 3, shapes[b][7], 1))
            for j, (owner, a, b) in enumerate(((0, 0, 2), (0, 0, 1), (1, 1, 2))):
                out.append(line('C', 1, k, j, owner, a, b))
            out.append(line('U', 1, k, 1, 3, 48, 3, 0, 3))
            pairs = {(0, 1), (0, 2), (1, 2)}
        elif k == 5:
            out.append(line('U', 1, k, 0, 0, 48, 3, 0, 0))
        elif k == 6:
            out.append(line('Q', 1, k, 0, g.NULL, g.NULL, 2, 5, 3, 3, 0, 0, 1, 1, 3, 2))
        cap, index = (0, 0) if k < 4 else (48, 3)
        out += [line('D', 1, k, len(moved), len(moved), len(pairs), len(live), cap, index),
                line('M', 1, k, len(moved), *(keys[x] for x in moved))]
        for t in range(3):
            if t < 2:
                out.append(line('T', 1, k, t, g.NULL, 0, 16, 0, 0, 0, 0, 0, 0, 0))
            else:
                root, free, height = ((0, 1, 0), (2, 3, 1), (4, 5, 2))[len(live)-1]
                out.append(line('T', 1, k, t, root, len(live)*2-1, 16, free, len(live), height, *box))
        for n in live:
            out.append(line('P', 1, k, n, keys[n], *box, g.NULL, g.NULL, n))
        out += [hs(1, k, 0, 16, {keys[x]+1 for x in moved}),
                hs(1, k, 1, 32, {(a << 32) | b for a, b in pairs}),
                line('PS', 1, k, len(pairs), *(v for pair in sorted(pairs) for v in pair))]
    out.append(line('END', 1))
    full = '\n'.join(out)+'\n'
    plain = '\n'.join(row for row in out if not row.startswith(('F ', 'C '))
                       and not row.startswith('Q 1 4 '))+'\n'
    return (c,), full, plain


def mutate(text, tag, k, index, value=None, ordinal=0):
    rows = text.splitlines()
    found = 0
    for i, row in enumerate(rows):
        t = row.split(' ')
        if t[0] == tag and (k is None or t[1:3] == ['1', str(k)]):
            if found == ordinal:
                t[index+1] = str(int(t[index+1]) ^ 1 if value is None else value)
                rows[i] = ' '.join(t)
                return '\n'.join(rows)+'\n'
            found += 1
    raise AssertionError((tag, k, ordinal))


class GeneratorTests(unittest.TestCase):
    def test_72_64_plus_8_and_transport_roundtrip(self):
        rows = g.cases()[:72]
        self.assertEqual(len(rows), 72)
        self.assertEqual(Counter(c.mode for c in rows), {0: 64, 1: 8})
        loaded = g.load(HERE/'przypadki-szeroka.csv')[:72]
        self.assertEqual([c.words for c in loaded], [c.words for c in rows])
        decimal = (HERE/'przypadki-szeroka-stdin.csv').read_text(encoding='ascii').splitlines()[:72]
        self.assertEqual(len(decimal), 72)
        for c, row in zip(rows, decimal):
            self.assertEqual(row, str(c.id)+' '+' '.join(map(str, c.words)))
            g.validate(c)

    def test_output_bound_before_native_run(self):
        self.assertEqual(g.output_bound(g.cases()[:72]), 17179704)
        self.assertLessEqual(g.output_bound(g.cases()), 20*1024**2)

    def test_all_nine_ordered_types_and_both_create_orders(self):
        found = set()
        for c in g.cases()[4:12]:
            for a in range(0, len(c.bodies), 2):
                found.add(tuple(c.bodies[a:a+2]))
                creates = [w[1] for w in c.ops if w[0] == 0 and w[1] in (a, a+1)]
                self.assertEqual(creates, [a, a+1, a+1, a])
        self.assertEqual(found, {(a, b) for a in range(3) for b in range(3)})

    def test_dense_all_2080_and_heap_capacity(self):
        c = g.cases()[62]
        live = {w[1]: w[2:6] for w in c.ops if w[0] == 0}
        keys = {n: i*4+2 for i, n in enumerate(live)}
        cand = g.candidates(c, live, set(live), keys)
        self.assertEqual(len(cand), 2080)
        self.assertGreater(len(cand), 16*65)
        self.assertEqual(c.dump, 0)
        self.assertEqual(sum(len(c.ops) for c in g.cases()[:72]), 2165)

    def test_set_collision_wrap_and_safe_constructor(self):
        for c in g.cases()[67:70]:
            keys = [g.join(*w[1:3]) for w in c.ops[:7]]
            self.assertTrue(all(g.key_hash(k) & 15 == 15 for k in keys))
            self.assertEqual(len(set(keys)), 7)
        for c in g.cases()[64:72]:
            self.assertIn(c.capacity, (16, 32, 64))
            for w in c.ops:
                if w[0] != 3:
                    self.assertTrue(g.join(*w[1:3]) and g.key_hash(g.join(*w[1:3])))

    def test_appended_cases_and_original_72_bytes(self):
        rows = g.cases()
        self.assertEqual(len(rows), 75)
        self.assertEqual(Counter(c.mode for c in rows), {0: 67, 1: 8})
        self.assertEqual([c.words for c in g.load(HERE/'przypadki-szeroka.csv')], [c.words for c in rows])
        pins = {
            'przypadki-szeroka.csv': 'de6bc40b5fb76893752599a15bb8d01d0369bb48839626a96dbf55eb2023f1f8',
            'przypadki-szeroka-stdin.csv': '0a680a5824996b83817e25ce930f5de39b10052640d5caf59c31c2c68b8a7556',
        }
        for name, expected in pins.items():
            data = (HERE/name).read_bytes().splitlines(keepends=True)
            self.assertEqual(len(data), 75)
            self.assertEqual(hashlib.sha256(b''.join(data[:72])).hexdigest(), expected)
        decimal = (HERE/'przypadki-szeroka-stdin.csv').read_text(encoding='ascii').splitlines()
        self.assertEqual(decimal, [str(c.id)+' '+' '.join(map(str, c.words)) for c in rows])
        self.assertEqual(sum(len(c.ops) for c in rows), 2174)
        self.assertLessEqual(g.output_bound(rows), 20*1024**2)

    def test_r5_w1_full_i32_group_decisions(self):
        witnesses = ((73, (32768, 32768), True),
                     (74, (-32769, -32769), False),
                     (75, (1, 65537), False))
        for c, (case_id, groups, accepted) in zip(g.cases()[72:], witnesses):
            with self.subTest(case=case_id):
                self.assertEqual(c.id, case_id)
                self.assertEqual(c.bodies, (2, 2))
                self.assertEqual(tuple(g.signed(s[5]) for s in c.shapes), groups)
                self.assertEqual(tuple(g.join(*s[1:3]) for s in c.shapes), (1, 2))
                self.assertEqual(tuple(g.join(*s[3:5]) for s in c.shapes), (0, 0))
                self.assertEqual(c.ops, (g.create(0), g.create(1), g.op(5)))
                live = {w[1]: w[2:6] for w in c.ops[:2]}
                self.assertEqual(g.candidates(c, live, {0, 1}, {0: 2, 1: 6}), {(0, 1): 0})
                self.assertEqual(g.allowed(c, 0, 1), accepted)
                narrowed = tuple((group+32768) % 65536-32768 for group in groups)
                mutant = replace(c, shapes=tuple((*s[:5], group & g.NULL, *s[6:])
                                                for s, group in zip(c.shapes, narrowed)))
                self.assertEqual(g.allowed(mutant, 0, 1), not accepted)

    def test_source_assertion_input_rejections(self):
        c = g.cases()[1]
        bad_ops = [g.create(1), g.op(1, 0), g.create(0, force=2),
                   g.create(0, (0, 0, float('inf'), 1)), g.create(0, (0, 0, 100000, 1)),
                   g.create(0, (2, 0, 1, 1)), g.op(10, 3), g.op(5, 1)]
        for w in bad_ops:
            with self.subTest(w=w), self.assertRaises(ValueError):
                g.validate(replace(c, ops=(w,)))
        for ops in ((g.create(0), g.create(0)), (g.create(0), g.move(0, (0, 0, 1, 1), True))):
            with self.assertRaises(ValueError):
                g.validate(replace(c, ops=ops))
        for cap in (0, 17, 24, 128):
            with self.assertRaises(ValueError):
                g.validate(replace(g.cases()[64], capacity=cap))

    def test_distance_joint_and_i32_group_limits(self):
        c = g.cases()[40]
        with self.assertRaises(ValueError):
            g.validate(replace(c, bodies=(0, 1, 0, 1)))
        with self.assertRaises(ValueError):
            g.validate(replace(c, joints=((0, 0, 1),)))
        self.assertEqual(g.signed(g.shape(0, group=-70000)[5]), -70000)
        self.assertEqual(g.shape(0, group=70000)[5], 70000)

    def test_no_incident_destroy_or_absent_release(self):
        c = g.Case(1, '', 0, 0, (g.create(0), g.create(1), g.op(5), g.op(1, 0)),
                   (2, 2), (g.shape(0), g.shape(1)))
        with self.assertRaisesRegex(ValueError, 'incident'):
            g.validate(c)
        with self.assertRaisesRegex(ValueError, 'absent'):
            g.validate(replace(c, ops=(g.create(0), g.create(1), g.op(9, 0, 1))))

    def test_boundary_direction_category_zero_groups_masks_sensors_joints(self):
        c = g.cases()[26]
        live = {0: tuple(map(g.bits, (0, 0, 1, 1))), 1: tuple(map(g.bits, (1, 1, 2, 2)))}
        self.assertTrue(g.allowed(c, 0, 1))                                      
        self.assertEqual(g.candidates(c, live, {0}, {0: 6, 1: 2}), {(0, 1): 0})
        self.assertEqual(g.candidates(c, live, {1}, {0: 6, 1: 2}), {})
        self.assertFalse(g.allowed(g.cases()[31], 0, 1))                            
        self.assertFalse(g.allowed(g.cases()[29], 0, 1))                         
        self.assertFalse(g.allowed(g.cases()[41], 0, 1))                            
        same = replace(c, shapes=(g.shape(0), g.shape(0)))
        self.assertFalse(g.allowed(same, 0, 1))
        sensor = replace(c, shapes=(g.shape(0), g.shape(1, sensor=1)))
        self.assertFalse(g.allowed(sensor, 0, 1))
        two = g.cases()[38]
        self.assertNotEqual(two.shapes[1][0], two.shapes[2][0])
        self.assertEqual((two.shapes[1][6], two.shapes[2][6]), (1, 1))
        clear_sensors = replace(two, shapes=tuple((*s[:6], 0, s[7]) for s in two.shapes))
        self.assertTrue(g.allowed(clear_sensors, 1, 2))
        self.assertFalse(g.allowed(two, 1, 2))


class ComparatorTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.good, self.plain = fixture()
        self.assertEqual(p.compare(self.good, self.good, self.plain, self.rows), [])

    def fails(self, bad, both=False, plain=None):
        errors = p.compare(bad if both else self.good, bad, self.plain if plain is None else plain, self.rows)
        self.assertTrue(errors)
        return '\n'.join(errors)

    def test_valid_fixture_lf_crlf_and_optional_final_newline(self):
        for text in (self.good.replace('\n', '\r\n'), self.good.rstrip('\n')):
            self.assertEqual(p.compare(text, text, self.plain, self.rows), [])

    def test_every_word_compared_with_first_case_operation_field(self):
        for row in self.good.splitlines():
            words = row.split(' ')
            for i in range(1, len(words)):
                bad = words[:]
                bad[i] = str(int(bad[i]) ^ 1)
                text = self.good.replace(row+'\n', ' '.join(bad)+'\n', 1)
                with self.subTest(tag=words[0], i=i):
                    errors = self.fails(text)
                    self.assertIn('case', errors)
                    self.assertIn('operation', errors)
                    self.assertIn('field', errors)

    def test_common_echo_fault_is_red(self):
        self.assertIn('echo.w2', self.fails(mutate(self.good, 'O', 1, 4), both=True))

    def test_all_three_exit_codes_red(self):
        for side in range(3):
            for code in (1, -9, 124, 125):
                codes = [0, 0, 0]; codes[side] = code
                self.assertTrue(p.compare(self.good, self.good, self.plain, self.rows, codes))

    def test_noncanonical_u32_and_spaces(self):
        for token in ('01', '+1', '-1', '4294967296', '0x1', '1.0', '１', '1\t1', ''):
            bad = self.good.replace('O 1 1 ', 'O 1 '+token+' ', 1)
            self.fails(bad)
        self.fails(self.good.replace('O 1 1 ', 'O 1 1  ', 1))
        self.fails(self.good+'\n')
        self.fails(self.good.replace('\n', '\r'))

    def test_missing_extra_duplicate_and_reordered_rows(self):
        lines = self.good.splitlines()
        for bad in (lines[:7]+lines[8:], lines+[lines[5]], lines[:7]+[lines[7]]+lines[7:],
                    lines[:7]+[lines[8], lines[7]]+lines[9:], lines[:-1]):
            self.fails('\n'.join(bad)+'\n')

    def test_move_order_is_native_comparison_not_set_oracle(self):
        old = 'M 1 3 3 2 6 14'
        bad = self.good.replace(old, 'M 1 3 3 6 2 14')
        p.validate_output(bad, self.rows)
        self.fails(bad)

    def test_hit_order_is_native_comparison_not_set_oracle(self):
        old = 'Q 1 4 2 0 2 2 5 3 3 0 0 1 1 3 2'
        bad = self.good.replace(old, 'Q 1 4 2 0 2 2 5 3 3 1 1 0 0 3 2')
        self.assertNotEqual(bad, self.good)
        p.validate_output(bad, self.rows)
        self.fails(bad)

    def test_filter_and_request_order_is_exact(self):
        for tag, k, width in (('F', 4, 7), ('C', 4, 3)):
            rows = self.good.splitlines()
            ids = [i for i, row in enumerate(rows) if row.startswith(f'{tag} 1 {k} ')]
            a, b = (rows[i].split(' ') for i in ids[:2])
            a[-width:], b[-width:] = b[-width:], a[-width:]
            rows[ids[0]], rows[ids[1]] = ' '.join(a), ' '.join(b)
            bad = '\n'.join(rows)+'\n'
            p.validate_output(bad, self.rows)
            self.fails(bad)

    def test_truncated_variable_lists_and_duplicate_hit(self):
        for tag in ('M', 'Q', 'HS', 'PS'):
            rows = self.good.splitlines()
            minimum = {'M': 4, 'Q': 10, 'HS': 6, 'PS': 4}[tag]
            i = next(i for i, row in enumerate(rows) if row.startswith(tag+' ') and len(row.split()) > minimum)
            rows[i] = rows[i].rsplit(' ', 1)[0]
            self.fails('\n'.join(rows)+'\n')
        bad = self.good.replace('5 3 3 0 0 1 1 3 2', '5 3 3 0 0 0 0 3 2')
        self.assertIn('Q.hit', self.fails(bad, both=True))

    def test_common_bad_filter_ids_and_decisions(self):
        for i in (3, 4, 5, 6, 7, 8, 9):
            self.fails(mutate(self.good, 'F', 4, i), both=True)

    def test_empty_update_retains_capacity_index_but_no_heap_requests(self):
        for i in range(2, 8):
            self.fails(mutate(self.good, 'U', 5, i), both=True)

    def test_existing_pair_and_persistence_checked(self):
        self.fails(mutate(self.good, 'D', 5, 4, 0), both=True)
        self.fails(mutate(self.good, 'PS', 5, 3, 1), both=True)

    def test_unobserved_c_is_validated_and_compared(self):
        bad = mutate(self.plain, 'T', 6, 3, 3, ordinal=2)
        p.validate_output(bad, self.rows, plain=True)                            
        errors = p.compare(self.good, self.good, bad, self.rows)
        self.assertTrue(errors)
        self.assertIn('C / C E283ada7088c2 Eae242858339f', '\n'.join(errors))
        self.assertTrue(p.compare(self.good, self.good, self.plain+'C 1 6 0 0 0 1\n', self.rows))

    def test_hash_slot_bit_compared_even_without_hash_oracle(self):
        bad = mutate(self.good, 'HS', 3, 7, 999, ordinal=0)
        p.validate_output(bad, self.rows)
        self.fails(bad)

    def test_set_result_duplicate_absent_clear_and_reuse(self):
        c = g.Case(1, '', 1, 1, (g.set_op(0, 1), g.set_op(0, 1), g.set_op(2, 2),
                   g.set_op(1, 2), g.set_op(1, 1), g.set_op(3), g.set_op(0, 2)))
        rows = [line('PORT5', 1), line('I', 1, *c.header)]
        for k, w in enumerate(c.ops, 1):
            rows.append(line('O', 1, k, *w, *([] if w[0] == 3 else [int(k in (2, 5))])))
            rows.append(hs(1, k, 2, 16, {1} if k < 5 else ({2} if k == 7 else set())))
        rows.append(line('END', 1))
        good = '\n'.join(rows)+'\n'
        self.assertEqual(p.compare(good, good, good, (c,)), [])
        self.assertTrue(p.compare(good, mutate(good, 'O', 2, 18, 0), good, (c,)))

    def test_no_custom_function_no_filter_rows(self):
        rows, good, plain = fixture(custom=0)
        self.assertEqual(p.compare(good, good, plain, rows), [])
        self.assertNotIn('\nF ', good)

    def test_first_difference_names_order_field(self):
        a = [('M', (1, 3, 3, 2, 6, 14))]
        b = [('M', (1, 3, 3, 6, 2, 14))]
        self.assertIn('case 1, operation 3, field M.', p.first_difference(a, b, 'test'))


class SourceBoundaryTests(unittest.TestCase):
    def test_unused_value_suppression_wraps_only_original_include(self):
        source = (HERE/'kontrola-szeroka.c').read_text(encoding='utf-8')
        push = '#pragma GCC diagnostic push'
        ignore = '#pragma GCC diagnostic ignored "-Wunused-value"'
        pop = '#pragma GCC diagnostic pop'
        include = '#include "broad_phase.c"'
        diagnostics = [row.strip() for row in source.splitlines()
                       if row.lstrip().startswith('#pragma GCC diagnostic')]
        self.assertEqual(diagnostics, [push, ignore, pop])
        self.assertEqual(source.count(include), 1)
        scoped = source.split(push, 1)[1].split(pop, 1)[0]
        self.assertEqual(scoped.strip().splitlines(), [ignore, include])
        self.assertLess(source.index(pop), source.index('enum { CASES'))


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = patch.dict(os.environ, RESULT_DIR=str(self.root/'out'), RUNNER_TEMP=str(self.root/'temp'))
        env.start(); self.addCleanup(env.stop)
        self.ci = module('port_ci_broad_test', 'ci.py')

    def test_new_module_cannot_enter_step_four_package(self):
        physics = self.root/'silnik/fizyka'; physics.mkdir(parents=True)
        names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk', 'drzewo.dk')
        for name in (*names, 'szeroka.dk', 'zbior.dk'):
            (physics/name).write_text(name+' invalid if new')
        with patch.object(self.ci, 'ROOT', self.root):
            target = self.ci.tree_physics()
        self.assertEqual(target.name, 'fizyka')
        self.assertEqual(sorted(f.name for f in target.iterdir()), sorted(names))
        for name in names:
            self.assertEqual((target/name).read_bytes(), (physics/name).read_bytes())

    def test_missing_broad_port_is_125_and_clear_message(self):
        with patch.object(self.ci, 'PORT', self.root/'missing'):
            self.assertEqual(self.ci.duckling_broad('never-run'), 1)
        self.assertEqual((self.ci.OUT/'duckling-szeroka-kod.csv').read_text(), '125\n')
        self.assertIn('missing port broad phase', (self.ci.OUT/'brak-portu-szeroka.csv').read_text(encoding='utf-8'))

    def test_compile_error_keeps_all_four_existing_outputs(self):
        port = self.root/'silnik/port'; port.mkdir(parents=True)
        physics = self.root/'silnik/fizyka'; physics.mkdir()
        (port/'szeroka.dk').touch(); (physics/'fizyka.dk').touch()
        names = ('duckling.csv', 'duckling-wiel.csv', 'duckling-ruch.csv', 'duckling-drzewo.csv')
        for name in names:
            (self.ci.OUT/name).write_text(name)
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci, 'ROOT', self.root),\
                patch.object(self.ci.base, 'run', return_value=19):
            self.assertEqual(self.ci.duckling_broad('never-run'), 19)
        for name in names:
            self.assertEqual((self.ci.OUT/name).read_text(), name)
        manifest = json.loads((self.ci.OUT/'duckling-szeroka-manifest.json').read_text())
        self.assertEqual(Path(manifest['packages'][0]['path']), physics)
        self.assertEqual(manifest['packages'][1]['dependencies'], [{'id': 'fizyka'}])
        self.assertNotIn('box2d', json.dumps(manifest))

    def test_summary_cli_cannot_ignore_missing_or_red_step_five(self):
        for stage in ('c', 'duckling', 'check', 'check-ruch', 'check-drzewo'):
            (self.ci.OUT/f'etap-port-{stage}-kod.csv').write_text('0\n')
        env = {name+'_OUTCOME': 'success' for name in ('C', 'DUCKLING', 'CHECK', 'RUCH', 'DRZEWO', 'SZEROKA')}
        with patch.dict(os.environ, env), patch('builtins.print'):
            self.ci.summary(include_broad=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')
            (self.ci.OUT/'etap-port-check-szeroka-kod.csv').write_text('0\n')
            self.ci.summary(include_broad=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '0\n')
            with patch.dict(os.environ, SZEROKA_OUTCOME='failure'):
                self.ci.summary(include_broad=True)
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')
        self.assertIn("'summary': lambda: summary(include_broad=True)", (HERE/'ci.py').read_text(encoding='utf-8'))

    def test_check_runs_tests_even_after_failed_comparison(self):
        with patch.object(self.ci.base, 'run', side_effect=[1, 0]) as run:
            self.assertEqual(self.ci.check_broad(), 1)
        self.assertEqual([c.args[0] for c in run.call_args_list], ['porownanie-szeroka', 'sprawdziany-szeroka'])

    def test_workflow_always_pins_and_unchanged_time_budget(self):
        from public_ci import check
        check(self)

    def test_c_build_has_two_variants_checks_hashes_and_keeps_original_files(self):
        source = self.ci.base.TEMP/'box2d'
        (source/'src').mkdir(parents=True)
        (source/'include/box2d').mkdir(parents=True)
        paths = [source/'src/broad_phase.c'] + [source/f'src/f{i}.h' for i in range(62)]
        for path in paths:
            path.write_text('unchanged test fixture\n', encoding='ascii')
        sums = ''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(source).as_posix()}\n' for path in sorted(paths))
        port = self.root/'port'; port.mkdir()
        (port/'fixtures/norms/KONTRAKT-5.json').parent.mkdir(parents=True,exist_ok=True)
        (port/'fixtures/norms/KONTRAKT-5.json').write_text(sums, encoding='ascii')
        before = {path: path.read_bytes() for path in paths}
        calls = []
        def need(name, command, **kwargs):
            calls.append((name, list(map(str, command)), kwargs))
            if name.endswith('-kompilacja'):
                Path(command[-1]).write_bytes(b'fixture binary')
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci.base, 'need', side_effect=need):
            self.ci.c_broad()
        builds = [(name, command) for name, command, _ in calls if name.endswith('-kompilacja')]
        self.assertEqual([name for name, _ in builds], ['kontrola-szeroka-kompilacja', 'kontrola-szeroka-bez-kompilacja'])
        for (_, command), trace in zip(builds, ('1', '0')):
            for flag in ('-DNDEBUG', '-DBOX2D_DISABLE_SIMD', '-DTRACE='+trace, '-Werror', '-ffp-contract=off'):
                self.assertIn(flag, command)
            self.assertTrue(any(v.endswith('libbox2d.a') for v in command))
            self.assertNotIn('-DB2_ENABLE_ASSERT', command)
            self.assertNotIn('-DBOX2D_AVX2', command)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        (paths[0]).write_text('changed original\n', encoding='ascii')
        with patch.object(self.ci, 'PORT', port), self.assertRaisesRegex(self.ci.base.StepFailed, 'checksum'):
            self.ci.c_broad()


if __name__ == '__main__':
    unittest.main()
