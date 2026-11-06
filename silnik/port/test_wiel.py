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
spec = importlib.util.spec_from_file_location('porownaj_wiel', HERE / 'porownaj-wiel.py')
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)
g = p.g
ROOT = HERE.parents[1]

def manifest_without_repo_root(manifest):
    root = json.dumps(os.path.normcase(str(ROOT.resolve())))[1:-1]
    flags = re.IGNORECASE if os.path.normcase('A') == 'a' else 0
    separator = re.escape(json.dumps(os.sep)[1:-1])
    return re.sub(r'(?<!\\)"' + re.escape(root) + r'(?="|' + separator + ')', '"',
                  json.dumps(manifest), flags=flags)


def square_words(position):
    pass                                                                           
    return (4, *map(g.bits, (-1, -1, 1, -1, 1, 1, -1, 1, *([0]*8))),
            *map(g.bits, (0, -1, 1, 0, 0, 1, -1, 0, *([0]*8))),
            0, 0, 0, *map(g.bits, (*position, 1, 0)))


def fixture():
    cases, lines = [], [f'PORT2 {g.COUNT}']
    for params in g.parameters():
        x, y = params.id/64, -params.id/128
        case = g.Case(params.id, params.category, (*square_words((x, y)), *square_words((x+1.5, y))))
        cases.append(case)
        result = [0]*30
        result[:3] = (2, g.bits(1), 0)
        for i, dy in enumerate((-1, 1)):
            start = 4+13*i
            result[start:start+7] = map(g.bits, (x+.75, y+dy, .75, dy, -.75, dy, -.5))
            result[start+11] = i+1
        lines.append('R '+str(case.id)+' '+' '.join(map(str, (*case.words, *result))))
    return tuple(cases), '\n'.join((*lines, f'END {g.COUNT}', ''))


def change(log, id, field, value=None):
    lines = log.splitlines()
    tokens = lines[id].split(' ')
    index = 2+p.ALL_FIELDS.index(field)
    tokens[index] = str(int(tokens[index])^1 if value is None else value)
    lines[id] = ' '.join(tokens)
    return '\n'.join(lines)+'\n'


def constructor_fixture():
    pass                                                                             
    lines = []
    for r in g.parameters():
        if r.id > g.BASE_COUNT:
            witness = next(c for c in g.mutation_data()['cases'] if c['id'] == r.id)
            lines.append(str(r.id)+' '+' '.join(f'{w:08x}' for w in witness['words']))
            continue
        words = []
        for shape, transform in ((r.a, r.ta), (r.b, r.tb)):
            if shape.kind == 2:
                vertices = shape.points
            else:
                vertices = ((-shape.hx, -shape.hy), (shape.hx, -shape.hy),
                            (shape.hx, shape.hy), (-shape.hx, shape.hy))
                if shape.kind == 1:
                    c, s = map(lambda v: g.number(g.bits(v)), (shape.c, shape.s))
                    vertices = tuple((c*x-s*y+shape.cx, s*x+c*y+shape.cy) for x, y in vertices)
            vertices = tuple(tuple(g.number(g.bits(v)) for v in point) for point in vertices)
            normals = []
            for a, b in p.edges(vertices):
                dx, dy = b[0]-a[0], b[1]-a[1]
                length = math.hypot(dx, dy)
                normals.extend((dy/length, -dx/length))
            centroid = tuple(sum(v[j] for v in vertices)/len(vertices) for j in range(2))
            words.extend((shape.count, *map(g.bits, (v for point in vertices for v in point)),
                          *([0]*(16-2*shape.count)), *map(g.bits, normals),
                          *([0]*(16-2*shape.count)), *map(g.bits, centroid),
                          g.bits(shape.radius), *map(g.bits, transform)))
        lines.append(str(r.id)+' '+' '.join(f'{w:08x}' for w in words))
    return '\n'.join(lines)+'\n'


class GeneratorTests(unittest.TestCase):
    def test_counts_coverage_and_repeatability(self):
        rows = g.parameters()
        self.assertEqual(len(rows), g.COUNT)
        self.assertEqual(rows, g.parameters())
        self.assertEqual(Counter(r.category for r in rows), {**dict.fromkeys(g.CATEGORIES, 20), 'mutacje': 11, 'prog-T': 1})
        self.assertEqual(len({r.words for r in rows}), g.COUNT)
        self.assertTrue(all(len(r.words) == 58 for r in rows))
        self.assertEqual({s.count for r in rows for s in (r.a, r.b)}, set(range(3, 9)))
        self.assertEqual({s.kind for r in rows for s in (r.a, r.b)}, {0, 1, 2})
        self.assertEqual(len(g.INPUT_FIELDS), 80)
        self.assertEqual(g.INPUT_FIELDS[0], 'A.count')
        self.assertEqual(g.INPUT_FIELDS[35:41], ('A.radius', 'xfA.p.x', 'xfA.p.y', 'xfA.q.c', 'xfA.q.s', 'B.count'))
        self.assertEqual(g.INPUT_FIELDS[79], 'xfB.q.s')

    def test_flip_pairs_are_full_swaps(self):
        rows = [r for r in g.parameters() if r.category == 'zamiana']
        for a, b in zip(rows[::2], rows[1::2]):
            self.assertEqual(a.words[:29], b.words[29:])
            self.assertEqual(a.words[29:], b.words[:29])

    def test_hull_points_are_strictly_convex(self):
        for n in range(3, 9):
            points = g.OCTAGON[:n]
            cross = []
            for i in range(n):
                a, b, c = points[i], points[(i+1)%n], points[(i+2)%n]
                cross.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
            self.assertTrue(all(v > 0 for v in cross), (n, cross))

    def test_thresholds_are_exact_f32_neighbors_after_sat_shift(self):
        f32 = lambda v: g.number(g.bits(v))
        rows = [r for r in g.parameters() if r.edge]
        for threshold, group in zip((0x3ca3d70a, g.bits(f32(.1)*f32(.005))), (rows[:10], rows[10:])):
            gaps = []
            for r in group:
                h = r.a.hx
                sf = f32(r.ta[0]-h)
                relative = f32(r.tb[0]-sf)
                if r.ta[0] == 0:
                    gap = f32(f32(relative-h)-f32(2*h))
                else:
                    gap = -f32(relative+h)
                gaps.append(g.bits(gap))
            self.assertEqual(gaps, [threshold+d for d in (-2, -1, 0, 1, 2) for _ in range(2)])

    def test_segment_degeneracy_epsilon_witnesses(self):
        f32 = lambda v: g.number(g.bits(v))
        samples = g.parameters()[135:138]
        squares = []
        for r in samples:
            edge = f32(r.a.hy-(-r.a.hy))
            self.assertEqual(g.bits(edge), 0x34000000+r.id-137)
            squares.append(f32(edge*edge))
        threshold = f32((2**-23)**2)
        self.assertLess(squares[0], threshold)
        self.assertEqual(squares[1], threshold)
        self.assertGreater(squares[2], threshold)

    def test_parameter_file_and_no_fabricated_structures(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            self.assertEqual(g.write_inputs(directory), ())
            path = Path(directory)
            lines = (path/'przypadki-wiel-parametry.csv').read_text().splitlines()
            self.assertEqual(len(lines), g.COUNT)
            self.assertTrue(all(len(line.split(' ')) == 59 for line in lines))
            self.assertFalse((path/'przypadki-wiel.csv').exists())

    def test_c_failure_is_fatal(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            with patch.object(g.subprocess, 'run', return_value=g.subprocess.CompletedProcess([], 7, '', 'hull failed')):
                with self.assertRaisesRegex(ValueError, 'code 7'):
                    g.write_inputs(directory, Path(directory)/'kontrola')

    def test_c_materialization_transport_and_decimal_file(self):
        text = constructor_fixture()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            with patch.object(g.subprocess, 'run', return_value=g.subprocess.CompletedProcess([], 0, text, '')) as run:
                rows = g.write_inputs(directory, Path(directory)/'kontrola')
            self.assertEqual(len(rows), g.COUNT)
            self.assertEqual(run.call_args.args[0][1], '--generuj')
            decimals = (Path(directory)/'przypadki-wiel-stdin.csv').read_text().splitlines()
            for row, line in zip(rows, decimals):
                self.assertEqual(tuple(map(int, line.split())), (row.id, *row.words))

    def test_parameter_geometric_meaning(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory)/'input.csv'
            path.write_text(constructor_fixture(), encoding='ascii')
            rows = g.read_inputs(path)
        for case in rows:
            separation = p.geometry(case)[-3]
            with self.subTest(id=case.id, category=case.category):
                if case.category == 'brak':
                    self.assertGreater(separation, p.SPECULATIVE)
                elif case.category == 'styk':
                    self.assertEqual(separation, 0)
                elif case.category in ('przenikanie', 'wspolny'):
                    self.assertLess(separation, 0)
                elif case.category == 'wyprzedzajacy':
                    self.assertGreater(separation, 0)
                    self.assertLess(separation, p.SPECULATIVE)

    def test_bad_materialized_inputs_fail(self):
        good = constructor_fixture()
        for index, word in ((1, '00000002'), (2, '7fc00000'), (10, '80000000'),
                            (18, '3f800000'), (36, '3f800000'), (37, '3f800000')):
            lines = good.splitlines()
            tokens = lines[0].split(' ')
            tokens[index] = word
            lines[0] = ' '.join(tokens)
            with self.subTest(index=index), tempfile.TemporaryDirectory(dir=ROOT) as directory:
                path = Path(directory)/'input.csv'
                path.write_text('\n'.join(lines)+'\n', encoding='ascii')
                with self.assertRaises(ValueError):
                    g.read_inputs(path)

    def test_materialized_framing_and_nonfinite_transform_fail(self):
        good = constructor_fixture()
        for bad in (good+'\n', '\n'.join(good.splitlines()[1:])+'\n',
                    good.replace('1 ', '01 ', 1), good.replace('1 ', '1  ', 1)):
            with self.subTest(prefix=bad[:35]), tempfile.TemporaryDirectory(dir=ROOT) as directory:
                path = Path(directory)/'input.csv'
                path.write_text(bad, encoding='ascii')
                with self.assertRaises(ValueError):
                    g.read_inputs(path)


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.good = fixture()

    def fails(self, c=None, d=None, code=0, c_code=0, message=''):
        status, report = p.compare(self.good if c is None else c, self.good if d is None else d,
                                   code, self.cases, c_code)
        self.assertEqual(status, 1, report)
        self.assertIn(message, report)
        return report

    def test_good(self):
        code, report = p.compare(self.good, self.good, 0, self.cases)
        self.assertEqual(code, 0, report)
        self.assertIn(f'{g.COUNT}/{g.COUNT}; echo: {g.COUNT}/{g.COUNT}', report)
        self.assertIn(f'C {g.COUNT - 20}/{g.COUNT - 20}; Duckling {g.COUNT - 20}/{g.COUNT - 20}', report)

    def test_bad_bit(self):
        self.fails(d=change(self.good, 1, 'normal.x'), message='normal.x: C=0x3f800000, Duckling=0x3f800001')

    def test_bad_count(self):
        self.fails(d=change(self.good, 1, 'pointCount', 3), message='pointCount')

    def test_wrong_valid_count(self):
        self.fails(d=change(self.good, 1, 'pointCount', 1), message='pointCount: C=0x00000002')

    def test_bad_echo_both_sides(self):
        bad = change(self.good, 1, 'echo.A.vertices[0].x')
        self.fails(c=bad, d=bad, message='echo A.vertices[0].x')

    def test_missing(self):
        lines = self.good.splitlines()
        del lines[2]
        self.fails(d='\n'.join(lines)+'\n', message='brakujace przypadki')

    def test_duplicate_order_and_extra(self):
        lines = self.good.splitlines()
        lines.insert(2, lines[1])
        self.fails(d='\n'.join(lines)+'\n', message='id/kolejnosc/powtorzenie')

    def test_bad_codes(self):
        self.fails(code=7, message='Duckling: code exit 7')
        self.fails(c_code=2, message='C: code exit 2')

    def test_all_protocol_words_compared_including_unused_point(self):
        for field in p.ALL_FIELDS:
            with self.subTest(field=field):
                self.fails(d=change(self.good, 1, field), message=field)

    def test_malformed_tokens_and_framing(self):
        for bad in (self.good.replace(f'PORT2 {g.COUNT}', f'PORT1 {g.COUNT}'), self.good.removesuffix(f'END {g.COUNT}\n'),
                    self.good+'\n', self.good.replace('R 1 ', 'R 01 ', 1),
                    self.good.replace('R 1 ', 'R 1  ', 1), self.good.replace('R 1 ', 'R -1 ', 1),
                    self.good.replace('R 1 ', 'R 4294967296 ', 1)):
            with self.subTest(prefix=bad[:35]):
                self.fails(d=bad)

    def test_same_wrong_normal_rejected_independently(self):
        bad = change(self.good, 1, 'normal.x', g.bits(.5))
        self.fails(c=bad, d=bad, message='normalna jednostkowa')

    def test_same_wrong_point_rejected_independently(self):
        bad = change(self.good, 1, 'p0.point.y', g.bits(20))
        self.fails(c=bad, d=bad, message='poza brzegiem')

    def test_same_wrong_anchor_rejected_independently(self):
        for field in ('p0.anchorA.x', 'p0.anchorB.y', 'p1.anchorA.y', 'p1.anchorB.x'):
            bad = change(self.good, 1, field, g.bits(20))
            self.fails(c=bad, d=bad, message=field)

    def test_computed_minus_zero_compared_bitwise(self):
        self.fails(d=change(self.good, 1, 'normal.y', 0x80000000), message='normal.y: C=0x00000000')

    def test_crlf_is_accepted(self):
        self.assertEqual(p.compare(self.good.replace('\n', '\r\n'), self.good, 0, self.cases)[0], 0)

    def test_cli_missing_inputs_records_report_and_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            missing, report = Path(directory)/'missing.csv', Path(directory)/'report.md'
            code = p.main(['--c', str(missing), '--duckling', str(missing), '--wejscie', str(missing),
                           '--kod-c', '125', '--kod-wyjscia', '125', '--raport', str(report)])
            self.assertEqual(code, 1)
            self.assertIn('RESULT: FAIL', report.read_text(encoding='utf-8'))

    def test_same_missing_contact_rejected_independently(self):
        lines = self.good.splitlines()
        tokens = lines[1].split(' ')
        tokens[82:] = ['0']*30
        lines[1] = ' '.join(tokens)
        bad = '\n'.join(lines)+'\n'
        self.fails(c=bad, d=bad, message='SAT/odleglosc')

    def test_nan_and_nonzero_initialized_fields(self):
        for field, value, message in (('p0.separation', 0x7fc00000, 'NaN/Inf'),
                                      ('rollingImpulse', 0x80000000, 'initialized zero'),
                                      ('p1.persisted', 1, 'initialized zero')):
            bad = change(self.good, 1, field, value)
            self.fails(c=bad, d=bad, message=message)

    def test_threshold_only_skips_properties(self):
        id = next(c.id for c in self.cases if c.edge)
        bad = change(self.good, id, 'normal.x', g.bits(.5))
        self.assertEqual(p.compare(bad, bad, 0, self.cases)[0], 0)
        self.fails(d=bad, message='normal.x')

    def test_c_properties_checked_without_duckling(self):
        report = self.fails(d='', code=125, message=f'C {g.COUNT - 20}/{g.COUNT - 20}; Duckling 0/{g.COUNT - 20}')
        self.assertIn('Duckling: code exit 125', report)


class GeometryTests(unittest.TestCase):
    def test_sat_overlap_touch_separation(self):
        a = ((-1, -1), (1, -1), (1, 1), (-1, 1))
        for shift, expected in ((1.5, -.5), (2, 0), (3, 1)):
            b = tuple((x+shift, y) for x, y in a)
            self.assertEqual(p.sat_gap(a, b), expected)

    def test_diagonal_distance_needs_more_than_face_sat(self):
        a = ((-1, -1), (1, -1), (1, 1), (-1, 1))
        b = tuple((x+2.125, y+2.125) for x, y in a)
        self.assertEqual(p.sat_gap(a, b), .125)
        self.assertAlmostEqual(min(p.boundary_distance(v, b) for v in a), math.sqrt(2)/8)

    def test_no_contact_all_zeros(self):
        case = g.Case(1, 'brak', (*square_words((0, 0)), *square_words((3, 0))))
        self.assertEqual(p.independent(case, [0]*30, 'C'), [])
        self.assertTrue(p.independent(case, [2, g.bits(1), *([0]*28)], 'C'))

    def test_scale_budget_does_not_include_unit_normals(self):
        case = g.Case(1, 'skale', (*square_words((0, 0)), *square_words((0, 0))))
        words = list(case.words)
        for o in (0, 40):
            for j in range(1, 17):
                words[o+j] = g.bits(g.number(words[o+j])*2**-18)
        case = replace(case, words=tuple(words))
        self.assertLess(p.geometry(case)[-2], 1e-9)


class MutationWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = g.mutation_data()
        cases, text = fixture()
        cases, lines = list(cases), text.splitlines()
        for witness in cls.data['cases']:
            id = witness['id']
            cases[id-1] = g.Case(id, witness['category'], tuple(witness['words']))
            lines[id] = 'R '+str(id)+' '+' '.join(map(str, (*witness['words'], *witness['expected'])))
        cls.cases, cls.good = tuple(cases), '\n'.join(lines)+'\n'

    def test_original_240_parameters_are_byte_identical(self):
        base = g.parameters()[:240]
        text = ''.join(f'{r.id} '+' '.join(f'{w:08x}' for w in r.words)+'\n' for r in base)
        self.assertEqual(hashlib.sha256(text.encode('ascii')).hexdigest(),
                         'f1feb422ec6376437e03624c672ef30984d6487a15fb7ccdfde36d7afd9d137b')

    def test_all_thirteen_review_mutations_have_different_results(self):
        names = {'T','late','eps','denominator','f2zero','f2one','clip','interp','sepT','id01','id10','clear','assoc'}
        self.assertEqual({m['name'] for m in self.data['mutations']}, names)
        self.assertEqual(len(self.data['mutations']), 13)
        witnesses = {c['id']: c for c in self.data['cases']}
        for mutation in self.data['mutations']:
            with self.subTest(mutation=mutation['name']):
                wanted = witnesses[mutation['case']]['expected']
                self.assertNotEqual(wanted, mutation['mutant'])
                self.assertEqual(mutation['different_fields'],
                                 [i for i,(a,b) in enumerate(zip(wanted,mutation['mutant'])) if a!=b])
                self.assertTrue(mutation['source'].startswith('silnik/fizyka/wielokaty.dk:'))

    def test_original_witness_results_pass_independent_properties(self):
        code, report = p.compare(self.good, self.good, 0, self.cases)
        self.assertEqual(code, 0, report)

    def test_all_thirteen_actual_mutant_results_are_rejected(self):
        for mutation in self.data['mutations']:
            lines = self.good.splitlines()
            id = mutation['case']
            row = lines[id].split(' ')
            row[82:] = list(map(str, mutation['mutant']))
            lines[id] = ' '.join(row)
            bad = '\n'.join(lines)+'\n'
            for left in (self.good, bad):
                with self.subTest(mutation=mutation['name'], both=left==bad):
                    code, report = p.compare(left, bad, 0, self.cases)
                    self.assertEqual(code, 1, report)
                    self.assertIn(f'Przypadek {id}', report)
                    self.assertIn('swiadek mutacji', report)

    def test_previously_uncovered_branch_witnesses(self):
        rows = {c['id']: c for c in self.data['cases']}
        self.assertTrue(rows[242]['branches']['nonparallel'])
        self.assertTrue(rows[241]['branches']['late_reject'])
        self.assertEqual(rows[243]['branches']['fractions'], [0,1])
        self.assertEqual(rows[244]['branches']['fractions'], [1,0])
        self.assertTrue(rows[243]['branches']['reduction_2_to_1'])
        self.assertTrue(rows[243]['branches']['flip_segment'])
        self.assertTrue(rows[247]['branches']['terminal_empty'])
        self.assertTrue(rows[246]['branches']['interpolation_epsilon_equal'])
        self.assertTrue(rows[250]['branches']['separation_T_equal'])
        self.assertNotEqual(rows[243]['expected'][19:21], [0,0])
        self.assertNotEqual(rows[243]['expected'][23], 0)
        self.assertNotEqual(rows[243]['expected'][28], 0)

    def test_c_population_matches_generator(self):
        self.assertIn(f'CASE_COUNT = {g.COUNT}', (HERE/'kontrola-wiel.c').read_text(encoding='utf-8'))

    def test_same_reversed_unit_normal_fails_both_logs(self):
        bad = change(self.good, 1, 'normal.x', g.bits(-1))
        bad = change(bad, 1, 'normal.y', g.bits(-0.0))
        code, report = p.compare(bad, bad, 0, self.cases)
        self.assertEqual(code, 1, report)
        self.assertIn('kierunek normalnej A->B', report)

    def test_direction_is_checked_also_on_original_threshold_cases(self):
        id = next(c.id for c in self.cases if c.edge)
        bad = change(self.good, id, 'normal.x', g.bits(-1))
        code, report = p.compare(bad, bad, 0, self.cases)
        self.assertEqual(code, 1, report)
        self.assertIn('kierunek normalnej A->B', report)

    def test_direction_tie_is_explicit_not_an_arbitrary_sign(self):
        case = g.Case(1, 'wspolny', (*square_words((0,0)), *square_words((0,0))))
        for normal in (1,-1):
            errors, status = p.normal_direction(case, (2,g.bits(normal),0,*([0]*27)), 'C')
            self.assertEqual(errors, [])
            self.assertEqual(status, 'remis')


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        self.environment = patch.dict(os.environ, RESULT_DIR=str(directory/'out'), RUNNER_TEMP=str(directory/'temp'))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        spec = importlib.util.spec_from_file_location('port_ci_test', HERE/'ci.py')
        self.ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ci)

    def test_missing_polygon_port_is_red_with_explicit_message(self):
        with patch.object(self.ci, 'PORT', Path(self.temp.name)/'missing'):
            self.assertEqual(self.ci.duckling_polygons('never-run'), 1)
        self.assertEqual((self.ci.OUT/'duckling-wiel-kod.csv').read_text(), '125\n')
        self.assertIn('missing port Ec3f183a85574', (self.ci.OUT/'brak-portu-wiel.csv').read_text(encoding='utf-8'))

    def test_polygon_compile_failure_records_red_without_execution(self):
        port = Path(self.temp.name)/'port'
        port.mkdir()
        (port/'wielokaty.dk').write_text('# fake input, compiler mocked\n')
        physics = Path(self.temp.name)/'silnik/fizyka'
        physics.mkdir(parents=True)
        (physics/'fizyka.dk').write_text('# fake package root, compiler mocked\n')
        (physics/'wielokaty.dk').write_text('# fake library, compiler mocked\n')
        with patch.object(self.ci, 'PORT', port), patch.object(self.ci, 'ROOT', Path(self.temp.name)),\
                patch.object(self.ci.base, 'run', return_value=19) as run:
            self.assertEqual(self.ci.duckling_polygons('never-run'), 19)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], 'duckling-wiel-kompilacja')
        self.assertEqual((self.ci.OUT/'duckling-wiel-kod.csv').read_text(), '125\n')
        manifest = json.loads((self.ci.OUT/'duckling-wiel-manifest.json').read_text())
        self.assertEqual(manifest['packages'][0]['name'], 'fizyka')
        self.assertEqual(Path(manifest['packages'][0]['path']), physics)
        self.assertEqual(manifest['packages'][1]['dependencies'], [{'id': 'fizyka'}])
        self.assertEqual(manifest['tasks'][1]['linking_options']['additional_link_options'][-1], '-lm')
        self.assertNotIn('box2d', manifest_without_repo_root(manifest))

    def test_both_comparisons_run_when_polygon_driver_is_missing(self):
        (self.ci.OUT/'duckling-kod.csv').write_text('0\n')
        (self.ci.OUT/'COMPARISON.md').write_text('180/180')
        (self.ci.OUT/'COMPARISON-WIEL.md').write_text('missing port')
        def outcome(name, command, **kwargs):
            return 1 if name == 'porownanie-wiel' else 0
        with patch.object(self.ci.base, 'run', side_effect=outcome) as run:
            self.assertEqual(self.ci.check(), 1)
        names = [call.args[0] for call in run.call_args_list]
        self.assertEqual(names, ['porownanie', 'sprawdziany', 'porownanie-wiel', 'sprawdziany-wiel'])
        circles, polygons = run.call_args_list[0].args[1], run.call_args_list[2].args[1]
        self.assertEqual(circles[circles.index('--kod-wyjscia')+1], 0)
        self.assertEqual(polygons[polygons.index('--kod-wyjscia')+1], 125)


if __name__ == '__main__':
    unittest.main()
