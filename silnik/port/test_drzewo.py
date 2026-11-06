pass                                                                                    
from collections import Counter
from dataclasses import replace
import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('porownaj_drzewo_test', HERE/'porownaj-drzewo.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
g = p.g

def manifest_without_repo_root(manifest):
    root = json.dumps(os.path.normcase(str(ROOT.resolve())))[1:-1]
    flags = re.IGNORECASE if os.path.normcase('A') == 'a' else 0
    separator = re.escape(json.dumps(os.sep)[1:-1])
    return re.sub(r'(?<!\\)"' + re.escape(root) + r'(?="|' + separator + ')', '"',
                  json.dumps(manifest), flags=flags)


def fixture():
    pass                                                                      
    cases = (g.Case(1, 'puste', 1, (g.query(), g.rebuild(0), g.rebuild(1))),
             g.Case(2, 'dwa', 1, (g.create((-1, -1, 1, 1), 1, 17),
                 g.create((1, -1, 3, 1), 1 << 63, 0xffffffff), g.query(),
                 g.query((1, 1, 1, 1)), g.categories(1, 0), g.query(mask=1 << 63),
                 g.move(0, (-3, -1, -1, 1)), g.move(1, (0, -2, 4, 2), True),
                 g.rebuild(1), g.query(), g.delete(0), g.delete(1),
                 g.create((0, 0, 1, 1), g.ALL, 0x80000000), g.query())))
    lines = ['PORT4 2']
    for case in cases:
        for k, (op, live) in enumerate(zip(case.ops, g.states(case)), 1):
            proxies = {0: 0, 1: 1, 2: 1}
            if op[0] == 0:
                result = (proxies[max(live)],)
            elif op[0] == 6:
                result = (len(live),)
            elif op[0] == 5:
                box = tuple(map(g.number, op[1:5]))
                mask = op[5] | op[6] << 32
                hits = [(proxies[n], user, 0) for n, (a, cat, user) in reversed(tuple(live.items()))
                        if cat & mask and g.overlaps(tuple(map(g.number, a)), box)]
                result = (max(0, 2*len(live)-1), len(hits), len(hits), *(w for h in hits for w in h))
            else:
                result = ()
            lines.append('O '+str(case.id)+' '+str(k)+' '+' '.join(map(str, (*op, *result))))
            count = len(live)
            root = 2 if count == 2 else proxies[next(iter(live))] if count else p.NULL
            free = 3 if count == 2 else (1 if k == 12 else 0) if case.id == 2 and k >= 11 else 1 if count else 0
            if count:
                boxes = [tuple(map(g.number, a)) for a, _, _ in live.values()]
                bounds = (min(a[0] for a in boxes), min(a[1] for a in boxes),
                          max(a[2] for a in boxes), max(a[3] for a in boxes))
            else:
                bounds = (0, 0, 0, 0)
            values = (root, max(0, 2*count-1), 16, free, count, (count-1).bit_length() if count else 0,
                      0, *map(g.bits, bounds), count,
                      *(v for n, (a, cat, user) in live.items()
                        for v in (n, proxies[n], *a, cat & 0xffffffff, cat >> 32, user, 0)))
            lines.append('D '+str(case.id)+' '+str(k)+' '+' '.join(map(str, values)))
    return cases, '\n'.join((*lines, 'END 2', ''))


def change(text, tag, case, k, field, value=None):
    lines = text.splitlines()
    prefix = f'{tag} {case} {k} '
    at = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    row = lines[at].split(' ')
    index = 3+field
    row[index] = str(int(row[index]) ^ 1 if value is None else value)
    lines[at] = ' '.join(row)
    return '\n'.join(lines)+'\n'


class GeneratorTests(unittest.TestCase):
    def test_all_cases_roundtrip_and_committed_inputs(self):
        rows = g.cases()
        self.assertEqual(len(rows), 50)
        self.assertEqual(g.read_inputs(HERE/'przypadki-drzewo.csv'), rows)
        decimal = (HERE/'przypadki-drzewo-stdin.csv').read_text(encoding='ascii').splitlines()
        self.assertEqual(len(decimal), 50)
        for case, line in zip(rows, decimal):
            self.assertEqual(line, f'{case.id} '+' '.join(map(str, case.words)))
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            g.write_inputs(directory)
            for name in ('przypadki-drzewo.csv', 'przypadki-drzewo-stdin.csv'):
                self.assertEqual((Path(directory)/name).read_bytes(), (HERE/name).read_bytes())

    def test_plan_coverage_and_volume(self):
        rows = g.cases()
        self.assertEqual(Counter(c.category for c in rows), {
            'puste': 3, 'jeden': 4, 'wzrost-puli': 5, 'wolne-miejsca': 5, 'obroty': 6,
            'przesun-powieksz': 4, 'kategorie-maski': 4, 'styk': 4, 'przebudowa': 4,
            '200-obszarow': 1, 'remisy-sasiada': 2, 'obroty-B-lisc': 2,
            'obszar-punkt': 2, 'znaczniki-przodkow': 1, 'powieksz-usun-przebuduj': 2,
            'nawiasowanie-kosztu': 1})
        self.assertEqual({op[0] for c in rows for op in c.ops}, set(range(7)))
        large = rows[39]
        self.assertEqual(len(large.ops), 200)
        self.assertEqual(len(list(g.states(large))[-1]), 200)
        self.assertEqual(large.dump_every, 0)
        self.assertEqual(list(p.schedule(large)).count(('D', 200)), 1)
        self.assertEqual(sum(tag == 'D' for tag, _ in p.schedule(large)), 1)
        maximum = max(max(0, 2*len(s)-1) for c in rows for s in g.states(c))
        capacity, grows = 16, 0
        while capacity < maximum:
            capacity += capacity//2
            grows += 1
        self.assertGreaterEqual(grows, 7)
        self.assertLessEqual(g.output_size_bound(rows)['both_outputs_at_most'], 5_000_000)

    def test_all_move_enlarge_source_assertions(self):
        moves = enlarges = 0
        for c in g.cases():
            previous = {}
            for op, live in zip(c.ops, g.states(c)):
                if op[0] in (2, 3):
                    self.assertIn(op[1], previous)
                    a = tuple(map(g.number, op[2:6]))
                    self.assertTrue(all(map(math.isfinite, a)))
                    self.assertLess(a[2]-a[0], 100000)
                    self.assertLess(a[3]-a[1], 100000)
                    self.assertLessEqual(a[0], a[2])
                    self.assertLessEqual(a[1], a[3])
                    if op[0] == 3:
                        self.assertFalse(g.contains(tuple(map(g.number, previous[op[1]][0])), a))
                        enlarges += 1
                    else:
                        moves += 1
                previous = live
        self.assertGreater(moves, 50)
        self.assertGreater(enlarges, 50)

    def test_original_42_inputs_are_byte_identical(self):
        for suffix, expected in (
                ('.csv', '93163b481aa4615a6313651f9ca4e488fd3735b3dbde3fce10bb81b0f949dec5'),
                ('-stdin.csv', '0cabe23c65798c12a44ec9bf2af4c67f08935b0a4e8f9ec56679f240e4374b79')):
            lines = (HERE/('przypadki-drzewo'+suffix)).read_bytes().splitlines(keepends=True)
            self.assertEqual(hashlib.sha256(b''.join(lines[:42])).hexdigest(), expected)

    def test_review_branch_cases(self):
        rows = g.cases()
                                                                             
        rotations = (
            ((12, -3, 28, -2.5), (12, 14, 20, 22), (-1, 12, -.5, 12.5), (-7, 1, -3, 17)),
            ((-15, 2, -7, 10), (-12, -4, -11.5, 0), (-17, 0, -1, .5), (-19, -11, -11, -3)))
        for case, boxes in zip(rows[42:44], rotations):
            self.assertEqual(case.dump_every, 1)
            self.assertEqual([op[0] for op in case.ops], [0, 0, 0, 0, 5])
            self.assertEqual([op[1:5] for op in case.ops[:4]], [tuple(map(g.bits, a)) for a in boxes])
            self.assertEqual([op[7] for op in case.ops[:4]], [1, 2, 3, 4])
            self.assertTrue(all(op[5:7] == (1, 0) for op in case.ops[:4]))
        self.assertEqual(rows[46].ops[:15], rows[26].ops[:15])
        self.assertEqual(rows[46].ops[15], g.rebuild(0))
        for case in rows[47:49]:
            kinds = [op[0] for op in case.ops]
            self.assertIn([3, 1, 5, 6, 0], [kinds[i:i+5] for i in range(len(kinds)-4)])
            self.assertTrue(any(not state for state in g.states(case)))

    def test_invalid_operations_fail_before_native_execution(self):
        create = g.create((0, 0, 1, 1))
        bad = [(g.delete(0),), (create, g.delete(0), g.move(0, (0, 0, 2, 2))),
               (create, g.move(0, (0, 0, 1, 1), True)),
               (create, g.move(0, (.25, .25, .75, .75), True)),
               (create, g.move(0, (1, 0, 0, 1))),
               (create, g.move(0, (0, 0, 100000, 1))),
               (create, g.move(0, (0, 0, float('inf'), 1))),
               (g.rebuild(2),), ((7, 0, 0, 0, 0, 0, 0, 0),),
               ((1, 0, 1, 0, 0, 0, 0, 0),), (create,)*201]
        for ops in bad:
            with self.subTest(ops=ops[:2]), self.assertRaises(ValueError):
                list(g.states(g.Case(1, 'invalid', 1, ops)))
                                                                           
        list(g.states(g.Case(1, 'valid', 1, (create, g.move(0, (1, 1, 2, 2), True)))))

    def test_bad_input_format_and_recipe_fail(self):
        source = (HERE/'przypadki-drzewo.csv').read_text(encoding='ascii')
        variants = [source.replace('1 ', '01 ', 1), source.replace('00000004', '00000003', 1),
                    source.replace('00000004', '4', 1), source+'\n', '\n'.join(source.splitlines()[1:])]
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            file = Path(directory)/'bad.csv'
            for text in variants:
                file.write_text(text, encoding='ascii')
                with self.assertRaises(ValueError):
                    g.read_inputs(file)

    def test_review_mutations_reference_real_cases(self):
        data = json.loads((HERE/'mutacje-drzewo.json').read_text(encoding='utf-8'))
        self.assertEqual(len(data['mutations']), 8)
        for mutation in data['mutations']:
            self.assertIsNone(mutation['result'])
            self.assertTrue(mutation['cases'])
            self.assertTrue(set(mutation['cases']) <= set(range(1, g.COUNT+1)))

    def test_inherited_cost_parentheses_have_an_f32_witness(self):
        case = g.cases()[49]
        self.assertEqual([op[0] for op in case.ops], [0, 0, 0, 0, 0, 6, 2, 5, 5])
        boxes = [tuple(map(g.number, op[1:5])) for op in case.ops[:4]]
        point = tuple(map(g.number, case.ops[6][2:6]))
        f = lambda x: g.number(g.bits(x))
        def union(a, b):
            return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
        def perimeter(a):
            return f(2*f(f(a[2]-a[0])+f(a[3]-a[1])))
        left, right = union(boxes[0], boxes[1]), union(boxes[2], boxes[3])
        root = union(left, right)
                                                                          
                                                                            
        centers = [(f(.5*f(a[0]+a[2])), f(.5*f(a[1]+a[3]))) for a in (*boxes, boxes[0])]
        dx, dy = (f(max(c[i] for c in centers)-min(c[i] for c in centers)) for i in (0, 1))
        self.assertGreater(dx, dy)
        pivot_x = f(.5*f(min(c[0] for c in centers)+max(c[0] for c in centers)))
        self.assertEqual([i for i,c in enumerate(centers) if c[0] < pivot_x], [0, 1, 4])
        group = [centers[i] for i in (0, 1, 4)]
        self.assertGreater(f(max(c[1] for c in group)-min(c[1] for c in group)),
                           f(max(c[0] for c in group)-min(c[0] for c in group)))
        pivot_y = f(.5*f(min(c[1] for c in group)+max(c[1] for c in group)))
        self.assertEqual([i for i in (0, 1, 4) if centers[i][1] < pivot_y], [0, 4])
        inherited = f(perimeter(union(root, point))-perimeter(root))
        direct, area = perimeter(union(left, point)), perimeter(left)
        original = f(inherited+f(direct-area))
        mutant = f(f(inherited+direct)-area)
        self.assertEqual((g.bits(original), g.bits(mutant)), (1018629294, 1018629292))
        parent_cost = f(direct+inherited)
        leaf_direct = perimeter(union(boxes[1], point))
        self.assertGreaterEqual(f(leaf_direct+original), parent_cost)
        self.assertLess(f(leaf_direct+mutant), parent_cost)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.good = fixture()
        self.assertEqual(p.compare(self.good, self.good, 0, self.cases)[0], 0)

    def fails(self, bad, expected='', both=False, code=0, ccode=0):
        status, report = p.compare(bad if both else self.good, bad, code, self.cases, ccode)
        self.assertEqual(status, 1, report)
        self.assertIn(expected, report)
        return report

    def test_bad_bit_first_operation_field(self):
        bad = change(self.good, 'D', 2, 2, 6, g.bits(2**-20))
        bad = change(bad, 'O', 2, 3, 8, 2)
        report = self.fails(bad)
        first = next(line for line in report.splitlines() if line.startswith('PIERWSZY'))
        self.assertIn('case 2, operation 2, field D.areaRatio', first)

    def test_every_echo_result_and_dump_word_is_compared(self):
        rows, errors = p.parse_log(self.good, 'C', self.cases)
        self.assertEqual(errors, [])
        for (tag, case, k), values in rows.items():
            for index in range(len(values)):
                with self.subTest(tag=tag, case=case, k=k, index=index):
                    self.fails(change(self.good, tag, case, k, index))

    def test_wrong_hit_order_is_red_even_when_set_is_correct(self):
        rows, _ = p.parse_log(self.good, 'C', self.cases)
        row = rows['O', 2, 3]
        self.assertEqual(row[11:], (1, 0xffffffff, 0, 0, 17, 0))
        bad = self.good
        for i, v in enumerate((*row[14:17], *row[11:14]), 11):
            bad = change(bad, 'O', 2, 3, i, v)
        self.fails(bad, 'field O.hit[0].proxyId')
                                                                  
        self.assertEqual(p.query_properties(self.cases[1].ops[2],
            (*row[:11], *row[14:17], *row[11:14]), list(g.states(self.cases[1]))[2], {0: 0, 1: 1}), [])

    def test_missing_extra_duplicate_reordered_rows(self):
        lines = self.good.splitlines()
        for rows in (lines[:9]+lines[10:], lines+[lines[2]], lines[:3]+[lines[2]]+lines[3:],
                     lines[:9]+[lines[10], lines[9]]+lines[11:], lines[:-1]):
            self.fails('\n'.join(rows)+'\n')

    def test_echo_checked_against_input_on_both_sides(self):
        self.fails(change(self.good, 'O', 2, 1, 7, 18), 'echo.w7', both=True)
        self.fails(change(self.good, 'O', 2, 7, 2, g.bits(-4)), 'echo.w2', both=True)

    def test_exit_codes(self):
        for code in (1, 124, 125, -9):
            self.fails(self.good, f'Duckling: code exit {code}', code=code)
            self.fails(self.good, f'C: code exit {code}', ccode=code)

    def test_strict_u32_header_footer_id_and_spaces(self):
        for old, new in (('PORT4 2', 'PORT4 3'), ('END 2', 'END 3'),
                         ('O 2 3 ', 'O 2 03 '), ('D 2 2 ', 'D 3 2 '),
                         ('O 2 3 ', 'O 2 3  '), ('O 2 3 5', 'O 2 3 05')):
            self.fails(self.good.replace(old, new, 1))
        for value in (-1, 2**32):
            self.fails(change(self.good, 'O', 2, 3, 8, value), 'format')

    def test_crlf_and_optional_last_newline(self):
        for text in (self.good.rstrip('\n'), self.good.replace('\n', '\r\n')):
            self.assertEqual(p.compare(text, text, 0, self.cases)[0], 0)

    def test_zero_sign_compared_bitwise(self):
        self.fails(change(self.good, 'D', 2, 2, 6, 0x80000000), 'D.areaRatio')

    def test_dump_zero_still_requires_last_dump(self):
        cases = tuple(replace(c, dump_every=0) for c in self.cases)
        good = '\n'.join(line for line in self.good.splitlines()
            if not line.startswith('D ') or line.startswith(('D 1 3 ', 'D 2 14 ')))+'\n'
        self.assertEqual(p.compare(good, good, 0, cases)[0], 0)
        bad = '\n'.join(line for line in good.splitlines() if not line.startswith('D 2 '))+'\n'
        self.assertEqual(p.compare(good, bad, 0, cases)[0], 1)

    def test_missing_duckling_keeps_independent_c_count(self):
        status, report = p.compare(self.good, '', 125, self.cases)
        self.assertEqual(status, 1)
        self.assertIn('C 2/2; Duckling 0/2', report)

    def test_cli_missing_files_writes_red(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            d = Path(directory)
            report = d/'report.md'
            self.assertEqual(p.main(['--c', str(d/'c'), '--duckling', str(d/'duck'),
                '--wejscie', str(d/'input'), '--raport', str(report),
                '--kod-c', '0', '--kod-wyjscia', '125']), 1)
            self.assertIn('RESULT: FAIL', report.read_text(encoding='utf-8'))


class IndependentTests(unittest.TestCase):
    setUp = ComparisonTests.setUp
    fails = ComparisonTests.fails

    def test_point_root_permits_nan_but_still_compares_its_bits(self):
        case = g.Case(1, 'obszar-punkt', 1, (g.create((0, 0, 0, 0), 1, 45),))
        def log(nan):
            dump = (0, 1, 16, 1, 1, 0, nan, 0, 0, 0, 0, 1,
                    0, 0, 0, 0, 0, 0, 1, 0, 45, 0)
            return ('PORT4 1\nO 1 1 '+' '.join(map(str, (*case.ops[0], 0)))+
                    '\nD 1 1 '+' '.join(map(str, dump))+'\nEND 1\n')
        for nan in (0x7fc00000, 0xffc00000, 0x7fc00001):
            status, report = p.compare(log(nan), log(nan), 0, (case,))
            self.assertEqual(status, 0, report)
        status, report = p.compare(log(0x7fc00000), log(0xffc00000), 0, (case,))
        self.assertEqual(status, 1)
        self.assertIn('D.areaRatio', report)
        for value in (g.bits(float('inf')), g.bits(float('-inf')), g.bits(-1)):
            status, report = p.compare(log(value), log(value), 0, (case,))
            self.assertEqual(status, 1, report)
            self.assertIn('areaRatio', report)
                                                                               
        for tag, cid, k in (('D', 2, 2), ('D', 1, 1)):
            self.fails(change(self.good, tag, cid, k, 6, 0x7fc00000), 'areaRatio', both=True)
        line = change(log(0x7fc00000), 'D', 1, 1, 9, g.bits(1))
        self.assertEqual(p.compare(line, line, 0, (case,))[0], 1)
                                                                              
        for field, value in ((4, 2), (13, 7), (14, g.bits(1))):
            bad = change(log(0x7fc00000), 'D', 1, 1, field, value)
            self.assertEqual(p.compare(bad, bad, 0, (case,))[0], 1)

    def test_identical_bad_hit_set_userdata_and_duplicates_fail(self):
        for field, value in ((11, 4), (12, 0), (13, 1), (14, 1), (15, 0xffffffff)):
            self.fails(change(self.good, 'O', 2, 3, field, value), 'independent hits', both=True)
        self.fails(change(self.good, 'O', 2, 6, 9, 1), 'independent leafVisits', both=True)

    def test_identical_bad_root_counts_height_and_leaf_readback_fail(self):
        for field, value, expected in ((0, p.NULL, 'root'), (1, 2, 'nodeCount'),
                (2, 17, 'nodeCapacity'), (3, 16, 'freeList'), (4, 1, 'proxyCount'),
                (5, 0, 'height'), (6, g.bits(float('nan')), 'areaRatio'),
                (7, g.bits(0), 'bounds'), (12, 1, 'live[0].n'),
                (13, 7, 'live[0].proxyId'), (14, g.bits(-2), 'live[0].lowerX'),
                (20, 0, 'live[0].userDataLow'), (21, 1, 'live[0].userDataHigh')):
            self.fails(change(self.good, 'D', 2, 2, field, value), expected, both=True)

    def test_category_high_bits_and_stale_category_propagation_fail(self):
        self.fails(change(self.good, 'D', 2, 2, 29, 0), 'categoryHigh', both=True)
                                                                                 
        lines = self.good.splitlines()
        at = next(i for i, line in enumerate(lines) if line.startswith('O 2 3 '))
        row = lines[at].split(' ')
        row[12:14] = ['1', '1']                           
        lines[at] = ' '.join(row[:14]+row[17:20])
        self.fails('\n'.join(lines)+'\n', 'hits', both=True)

    def test_closed_edge_corner_query_and_zero_masks(self):
        self.assertTrue(g.overlaps((-1, -1, 1, 1), (1, 1, 2, 2)))
        self.assertFalse(g.overlaps((-1, -1, 1, 1), (1.0000001, 1, 2, 2)))
        live = {0: (tuple(map(g.bits, (-1, -1, 1, 1))), 1 << 63, 9)}
        op = g.query((1, 1, 1, 1), 1 << 63)
        self.assertEqual(p.query_properties(op, (*op, 1, 1, 1, 5, 9, 0), live, {0: 5}), [])
        op = g.query(mask=0)
        self.assertEqual(p.query_properties(op, (*op, 1, 0, 0), live, {0: 5}), [])

    def test_capacity_full_null_and_height_bounds(self):
        values = (0, 1, 1, p.NULL, 1, 0, 0, *map(g.bits, (0, 0, 1, 1)), 1,
                  0, 0, *map(g.bits, (0, 0, 1, 1)), 1, 0, 3, 0)
        live = {0: (tuple(map(g.bits, (0, 0, 1, 1))), 1, 3)}
        self.assertTrue(any('nodeCapacity' in e for e in p.dump_properties(values, live, {0: 0})))
        self.fails(change(self.good, 'D', 1, 1, 5, 1), 'height', both=True)


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        environment = patch.dict(os.environ, RESULT_DIR=str(root/'out'), RUNNER_TEMP=str(root/'temp'))
        environment.start()
        self.addCleanup(environment.stop)
        spec = importlib.util.spec_from_file_location('port_ci_tree_test', HERE/'ci.py')
        self.ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ci)

    def test_directory_manifests_require_matching_main_source(self):
                                                                             
                                                                                  
        root = Path(self.temp.name)
        physics = root/'silnik/fizyka'
        port = root/'silnik/port'
        physics.mkdir(parents=True)
        port.mkdir()
        for name in ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk', 'drzewo.dk'):
            (physics/name).write_text('# fixture\n', encoding='ascii')
        for name in ('wielokaty.dk', 'ruch.dk'):
            (port/name).touch()

        def check_manifest(_name, command, **_kwargs):
            manifest = json.loads(Path(command[2]).read_text(encoding='utf-8'))
            for package in manifest['packages']:
                directory = Path(package['path'])
                if directory.is_dir():
                    main = directory/(directory.name+'.dk')
                    self.assertTrue(main.is_file(), f'Brak pliku glownego pakietu: {main}')
                    self.assertEqual(directory.name, package['name'])
            return 19                                                         

        with patch.object(self.ci, 'ROOT', root), patch.object(self.ci, 'PORT', port),\
                patch.object(self.ci.base, 'run', side_effect=check_manifest) as run:
            self.assertEqual(self.ci.duckling_polygons('never-run'), 19)
            self.assertEqual(self.ci.duckling_motion('never-run'), 19)
        self.assertEqual(run.call_count, 2)

    def test_missing_tree_is_explicit_red_and_125(self):
        with patch.object(self.ci, 'PORT', Path(self.temp.name)/'missing'):
            self.assertEqual(self.ci.duckling_tree('never-run'), 1)
        self.assertEqual((self.ci.OUT/'duckling-drzewo-kod.csv').read_text(), '125\n')
        self.assertIn('missing port E930e79f4d2d2', (self.ci.OUT/'brak-portu-drzewo.csv').read_text(encoding='utf-8'))

    def test_tree_compile_failure_keeps_all_previous_outputs(self):
        root = Path(self.temp.name)
        port = root/'silnik/port'
        physics = root/'silnik/fizyka'
        port.mkdir(parents=True)
        physics.mkdir()
        (port/'drzewo.dk').touch()
        for name in ('fizyka.dk', 'drzewo.dk'):
            (physics/name).touch()
        for name in ('duckling.csv', 'duckling-wiel.csv', 'duckling-ruch.csv'):
            (self.ci.OUT/name).write_text(name)
        with patch.object(self.ci, 'ROOT', root), patch.object(self.ci, 'PORT', port),\
                patch.object(self.ci.base, 'run', return_value=19) as run:
            self.assertEqual(self.ci.duckling_tree('never-run'), 19)
        self.assertEqual(run.call_count, 1)
        for name in ('duckling.csv', 'duckling-wiel.csv', 'duckling-ruch.csv'):
            self.assertEqual((self.ci.OUT/name).read_text(), name)
        manifest = json.loads((self.ci.OUT/'duckling-drzewo-manifest.json').read_text())
        self.assertEqual(Path(manifest['packages'][0]['path']), physics)
        self.assertEqual(manifest['packages'][1]['dependencies'], [{'id': 'fizyka'}])
        self.assertEqual(manifest['tasks'][1]['linking_options']['additional_link_options'][-1], '-lm')
        self.assertNotIn('box2d', manifest_without_repo_root(manifest))
        self.assertEqual((self.ci.OUT/'duckling-drzewo-kod.csv').read_text(), '125\n')
        self.assertIn('Ebcd8b38e500d Ef642974cfcb1, Ec3f183a85574 Ede7d1b721a1e motion E631f494748f8',
                      (self.ci.OUT/'blad-portu-drzewo.csv').read_text(encoding='utf-8'))

    def test_bad_tree_module_not_compiled_with_previous_steps(self):
        root = Path(self.temp.name)
        physics = root/'silnik/fizyka'
        physics.mkdir(parents=True)
        names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk')
        for name in (*names, 'drzewo.dk'):
            (physics/name).write_text(name+' invalid tree only' if name == 'drzewo.dk' else name)
        with patch.object(self.ci, 'ROOT', root):
            target = self.ci.previous_physics()
        self.assertNotEqual(target, physics)
        self.assertEqual(sorted(f.name for f in target.iterdir()), sorted(names))
        for name in names:
            self.assertEqual((target/name).read_bytes(), (physics/name).read_bytes())
        self.assertTrue((physics/'drzewo.dk').is_file())

        port = root/'silnik/port'
        port.mkdir()
        for name in ('wielokaty.dk', 'ruch.dk'):
            (port/name).touch()
        with patch.object(self.ci, 'ROOT', root), patch.object(self.ci, 'PORT', port),\
                patch.object(self.ci.base, 'run', return_value=19):
            self.assertEqual(self.ci.duckling_polygons('never-run'), 19)
            self.assertEqual(self.ci.duckling_motion('never-run'), 19)
        for suffix in ('wiel', 'ruch'):
            manifest = json.loads((self.ci.OUT/f'duckling-{suffix}-manifest.json').read_text())
            self.assertEqual(Path(manifest['packages'][0]['path']), target)

    def test_summary_cannot_ignore_red_tree_stage(self):
        for stage in ('c', 'duckling', 'check', 'check-ruch', 'check-drzewo'):
            (self.ci.OUT/f'etap-port-{stage}-kod.csv').write_text('0\n')
        outcomes = {name+'_OUTCOME': 'success' for name in ('C', 'DUCKLING', 'CHECK', 'RUCH', 'DRZEWO')}
        with patch.dict(os.environ, outcomes), patch('builtins.print'):
            self.ci.summary()
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '0\n')
            (self.ci.OUT/'etap-port-check-drzewo-kod.csv').write_text('1\n')
            self.ci.summary()
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')
            (self.ci.OUT/'etap-port-check-drzewo-kod.csv').write_text('0\n')
            with patch.dict(os.environ, DRZEWO_OUTCOME='failure'):
                self.ci.summary()
            self.assertEqual((self.ci.OUT/'wynik-kod.csv').read_text(), '1\n')

    def test_tree_check_runs_tests_after_red_comparison(self):
        with patch.object(self.ci.base, 'run', side_effect=[1, 0]) as run:
            self.assertEqual(self.ci.check_tree(), 1)
        self.assertEqual([c.args[0] for c in run.call_args_list], ['porownanie-drzewo', 'sprawdziany-drzewo'])
        self.assertTrue((self.ci.OUT/'COMPARISON-DRZEWO.md').is_file())

    def test_workflow_all_comparisons_always_and_pinned_actions(self):
        from public_ci import check
        check(self)


if __name__ == '__main__':
    unittest.main()
