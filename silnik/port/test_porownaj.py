pass                                                                                        
from collections import Counter
import contextlib
import io
import math
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import porownaj as p
import przypadki as g


def fixture():
    lines = ['PORT1 180']
    for case in g.cases():
        expected, _ = p.geometry(case)
        result = [int(expected[field]) if field == 'pointCount' or field.endswith(('.id', '.persisted'))
                  else g.bits(expected[field]) for field in p.RESULT_FIELDS]
        lines.append('R ' + str(case.id) + ' ' + ' '.join(map(str, (*case.words, *result))))
    return '\n'.join([*lines, 'END 180', ''])


def change(log, id, field, value=None):
    lines = log.splitlines()
    tokens = lines[id].split(' ')
    index = 2 + p.ALL_FIELDS.index(field)
    tokens[index] = str(int(tokens[index]) ^ 1 if value is None else value)
    lines[id] = ' '.join(tokens)
    return '\n'.join(lines) + '\n'


def axis_values(case):
    pass                                                                            
    v = tuple(map(g.number, case.words))
    assert v[:2] == v[7:9] == (0, 0)
    assert v[3:7] == (0, 0, 1, 0) and v[11:14] == (0, 1, 0)
    f32 = lambda value: g.number(g.bits(value))
    length = f32(math.sqrt(f32(v[10] * v[10])))
    separation = f32(f32(length - v[2]) - v[9])
    return length, separation


def n1_witness(log):
    pass                                                                   
    rows = list(g.cases())
    words = list(rows[90].words)
    words[5:7] = (g.bits(-1), g.bits(0))
    rows[90] = g.Case(91, 'wspolny', tuple(words))
    for field, word in (('echo.xfA.q.c', g.bits(-1)), ('echo.xfA.q.s', 0),
                        ('normal.x', 0x80000000), ('p0.anchorA.x', 0x80000000)):
        log = change(log, 91, field, word)
    return tuple(rows), log


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = fixture()

    def fails(self, c=None, d=None, exit_code=0, message=''):
        code, report = p.compare(self.good if c is None else c, self.good if d is None else d, exit_code)
        self.assertEqual(code, 1, report)
        self.assertIn(message, report)
        return report

    def test_good_180(self):
        code, report = p.compare(self.good, self.good, 0)
        self.assertEqual(code, 0, report)
        self.assertIn('180/180; echo: 180/180', report)
        self.assertIn('162/162', report)

    def test_one_result_bit(self):
        report = self.fails(d=change(self.good, 19, 'normal.x'), message='normal.x: C=0x3f800000')
        self.assertIn('Duckling=0x3f800001', report)

    def test_wrong_point_count(self):
        self.fails(d=change(self.good, 19, 'pointCount', 2), message='independent pointCount')

    def test_wrong_echo(self):
        self.fails(d=change(self.good, 19, 'echo.A.radius'), message='Duckling: echo A.radius')

    def test_identical_wrong_echo_is_rejected(self):
        wrong = change(self.good, 19, 'echo.A.radius')
        self.fails(c=wrong, d=wrong, message='C: echo A.radius')

    def test_missing_case(self):
        lines = self.good.splitlines()
        del lines[100]
        self.fails(d='\n'.join(lines) + '\n', message='Duckling: brakujacy case: 100')

    def test_extra_case(self):
        lines = self.good.splitlines()
        extra = lines[1].split(' ')
        extra[1] = '181'
        lines.insert(-1, ' '.join(extra))
        self.fails(d='\n'.join(lines) + '\n', message='Duckling: nadmiarowy case 181')

    def test_nonzero_exit(self):
        self.fails(exit_code=7, message='Duckling: code exit 7')

    def test_reference_violates_independent_geometry(self):
        wrong = change(self.good, 19, 'p0.separation', g.bits(0.5))
        self.fails(c=wrong, d=wrong, message='C: independent p0.separation')

    def test_reference_wrong_normal(self):
        wrong = change(self.good, 19, 'normal.x', g.bits(-1))
        self.fails(c=wrong, d=wrong, message='C: independent normal.x')

    def test_coincident_normal_corrupted_in_both_logs(self):
        wrong = change(self.good, 91, 'normal.x', g.bits(1))
        self.fails(c=wrong, d=wrong, message='C: independent normal.x')

    def test_coincident_zero_fields_reject_even_smallest_nonzero_word(self):
        for field in ('normal.x', 'normal.y', 'p0.anchorA.x', 'p0.anchorB.y', 'p0.point.x'):
            with self.subTest(field=field):
                wrong = change(self.good, 91, field, 1)
                self.fails(c=wrong, d=wrong, message='C: independent ' + field)

    def test_n1_half_turn_accepts_negative_computed_zeros(self):
        rows, log = n1_witness(self.good)
        with patch.object(p, 'cases', return_value=rows):
            code, report = p.compare(log, log, 0)
        self.assertEqual(code, 0, report)

    def test_n1_half_turn_still_rejects_nonzero_in_both_logs(self):
        rows, log = n1_witness(self.good)
        for word in (g.bits(1), 1):
            with self.subTest(word=word), patch.object(p, 'cases', return_value=rows):
                wrong = change(log, 91, 'normal.x', word)
                self.fails(c=wrong, d=wrong, message='C: independent normal.x')

    def test_n1_computed_zero_sign_must_match_between_languages(self):
        rows, log = n1_witness(self.good)
        with patch.object(p, 'cases', return_value=rows):
            self.fails(c=log, d=change(log, 91, 'normal.x', 0),
                       message='normal.x: C=0x80000000, Duckling=0x00000000')

    def test_zero_initialized_fields_still_require_positive_zero_in_both_logs(self):
        fields = ('rollingImpulse', 'p0.normalImpulse', 'p0.tangentImpulse',
                  'p0.totalNormalImpulse', 'p0.normalVelocity', 'p1.point.x')
        for field in fields:
            with self.subTest(field=field):
                wrong = change(self.good, 19, field, 0x80000000)
                self.fails(c=wrong, d=wrong, message='C: independent ' + field)
        wrong = change(self.good, 1, 'normal.x', 0x80000000)
        self.fails(c=wrong, d=wrong, message='C: independent normal.x')

    def test_mutant_m1_greater_or_equal_rejects_exact_speculative_contact(self):
        self.assertEqual(g.bits(axis_values(g.cases()[80])[1]), 0x3ca3d70a)
                                                                                      
        mutant = self.good
        for field in p.RESULT_FIELDS:
            mutant = change(mutant, 81, field, 0)
        self.fails(d=mutant, message='pointCount: C=0x00000001, Duckling=0x00000000')

    def test_mutant_m2_less_or_equal_zeroes_normal_at_exact_epsilon(self):
        self.assertEqual(g.bits(axis_values(g.cases()[176])[0]), 0x34000000)
                                                                                
                                                                                  
        self.assertEqual(p.geometry(g.cases()[176])[0]['normal.x'], 1)
        mutant = change(self.good, 177, 'normal.x', 0)
        self.fails(d=mutant, message='normal.x: C=0x3f800000, Duckling=0x00000000')

    def test_reference_wrong_midpoint(self):
        wrong = change(self.good, 19, 'p0.point.y', g.bits(1))
        self.fails(c=wrong, d=wrong, message='C: independent p0.point.y')

    def test_unused_second_point(self):
        self.fails(d=change(self.good, 19, 'p1.normalVelocity'), message='p1.normalVelocity')

    def test_rolling_impulse_is_checked(self):
        wrong = change(self.good, 19, 'rollingImpulse', g.bits(1))
        self.fails(c=wrong, d=wrong, message='C: independent rollingImpulse')

    def test_edge_cases_still_compare_every_bit(self):
        self.fails(d=change(self.good, 73, 'normal.x'), message='normal.x: C=')

    def test_nan_is_rejected(self):
        wrong = change(self.good, 19, 'normal.x', 0x7fc00000)
        self.fails(c=wrong, d=wrong, message='C: independent normal.x: nan')

    def test_minus_zero_bits_differ(self):
        self.fails(d=change(self.good, 19, 'normal.y', 0x80000000), message='normal.y: C=0x00000000')

    def test_duplicate_case(self):
        lines = self.good.splitlines()
        lines[2] = lines[1]
        self.fails(d='\n'.join(lines) + '\n', message='Duckling: powtorzony case 1')

    def test_wrong_order(self):
        lines = self.good.splitlines()
        lines[1], lines[2] = lines[2], lines[1]
        self.fails(d='\n'.join(lines) + '\n', message='Duckling: kolejnosc')

    def test_no_port(self):
        report = self.fails(d='', exit_code=125, message='Duckling: code exit 125')
        self.assertIn('C 162/162; Duckling 0/162', report)

    def test_c_geometry_is_checked_without_port(self):
        wrong = change(self.good, 19, 'p0.separation', g.bits(0.5))
        self.fails(c=wrong, d='', exit_code=125, message='C: independent p0.separation')

    def test_bad_type_range(self):
        self.fails(d=change(self.good, 19, 'p0.id', 65536), message='p0.id: wartosc poza typem')

    def test_missing_trailer(self):
        self.fails(d=self.good.removesuffix('END 180\n'), message='missing/zly koniec')

    def test_file_cli_writes_report_on_missing_input(self):
                                                               
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'c.csv').write_text(self.good, encoding='ascii')
            with contextlib.redirect_stdout(io.StringIO()):
                code = p.main(['--c', str(root / 'c.csv'), '--duckling', str(root / 'missing'),
                               '--kod-wyjscia', '125', '--raport', str(root / 'COMPARISON.md')])
            self.assertEqual(code, 1)
            self.assertIn('Ecd5b158f21b7 E04ff0184c025 E675b88752d5e missing', (root / 'COMPARISON.md').read_text(encoding='utf-8'))

    def test_crlf_is_accepted(self):
        code, report = p.compare(self.good, self.good.replace('\n', '\r\n'), 0)
        self.assertEqual(code, 0, report)


class GeneratorTests(unittest.TestCase):
    def test_exact_f32_boundaries_and_immediate_neighbors(self):
        rows = g.cases()
        for id, delta in ((80, -1), (81, 0), (82, 1)):
            with self.subTest(id=id):
                self.assertEqual(rows[id - 1].category, 'prog')
                self.assertEqual(g.bits(axis_values(rows[id - 1])[1]), 0x3ca3d70a + delta)
        for id, delta in ((176, -1), (177, 0), (178, 1)):
            with self.subTest(id=id):
                self.assertEqual(rows[id - 1].category, 'skale')
                self.assertEqual(g.bits(axis_values(rows[id - 1])[0]), 0x34000000 + delta)
    def test_fixed_unique_180_and_categories(self):
        rows = g.cases()
        self.assertEqual(rows, g.cases())
        self.assertEqual(len({c.words for c in rows}), 180)
        self.assertEqual(Counter(c.category for c in rows), dict.fromkeys(g.CATEGORIES, 18))
        self.assertEqual(sum(c.edge for c in rows), 18)

    def test_transport_files_preserve_every_bit(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            rows = g.write_inputs(directory)
            root = Path(directory)
            hex_lines = (root / 'przypadki.csv').read_text().splitlines()
            dec_lines = (root / 'przypadki-stdin.csv').read_text().splitlines()
            self.assertEqual(len(hex_lines), 180)
            for row, hex_line, dec_line in zip(rows, hex_lines, dec_lines):
                h, d = hex_line.split(), dec_line.split()
                self.assertEqual(h[0], str(row.id))
                self.assertTrue(all(re.fullmatch('[0-9a-f]{8}', token) for token in h[1:]))
                self.assertEqual(tuple(int(token, 16) for token in h[1:]), row.words)
                self.assertEqual(tuple(map(int, d[1:])), row.words)


class GeometryTests(unittest.TestCase):
    pass                                                                              

    def test_exact_tangent(self):
        expected, _ = p.geometry(g.cases()[18])
        self.assertEqual(expected['pointCount'], 1)
        self.assertEqual(expected['normal.x'], 1)
        self.assertEqual(expected['normal.y'], 0)
        self.assertEqual(expected['p0.separation'], 0)
        self.assertEqual(expected['p0.point.x'], 1 / 16)
        self.assertEqual(expected['p0.point.y'], 0)
        self.assertEqual(expected['p0.anchorA.x'], 1 / 16)
        self.assertEqual(expected['p0.anchorB.x'], -19 / 16)

    def test_speculative_contact(self):
        expected, _ = p.geometry(g.cases()[54])
        self.assertEqual(expected['pointCount'], 1)
        self.assertEqual(expected['p0.separation'], 1 / 1024)
        self.assertEqual(expected['p0.point.x'], 1 + 1 / 2048)

    def test_coincident_centers(self):
        expected, _ = p.geometry(g.cases()[90])
        self.assertEqual(expected['pointCount'], 1)
        self.assertEqual(expected['normal.x'], 0)
        self.assertEqual(expected['normal.y'], 0)
        self.assertEqual(expected['p0.point.x'], 0)
        self.assertEqual(expected['p0.point.y'], 0)
        self.assertEqual(expected['p0.separation'], -1.25)

    def test_transformed_local_centers(self):
        expected, _ = p.geometry(g.cases()[144])
        root = math.sqrt(109)
        self.assertAlmostEqual(expected['normal.x'], 10 / root)
        self.assertAlmostEqual(expected['normal.y'], 3 / root)
        self.assertAlmostEqual(expected['p0.separation'], root / 8 - 1.75)
        self.assertAlmostEqual(expected['p0.point.x'], -3.125 + 1.25 / root)
        self.assertAlmostEqual(expected['p0.point.y'], -0.3125 + 0.375 / root)

    def test_sub_epsilon_nonzero_distance(self):
        expected, _ = p.geometry(g.cases()[171])
        scale = 2**-30
        self.assertEqual(expected['normal.x'], 0)
        self.assertEqual(expected['normal.y'], 0)
        self.assertEqual(expected['p0.point.x'], scale / 2)
        self.assertEqual(expected['p0.point.y'], scale / 4)
        self.assertAlmostEqual(expected['p0.separation'] / scale, math.sqrt(1.25) - 1.5)

    def test_category_geometric_meaning(self):
        for case in g.cases():
            expected, _ = p.geometry(case)
            if case.category == 'brak':
                self.assertEqual(expected['pointCount'], 0)
            elif case.category == 'stycznosc':
                self.assertEqual(expected['p0.separation'], 0)
            elif case.category in ('przenikanie', 'promienie', 'wspolny'):
                self.assertEqual(expected['pointCount'], 1)
                self.assertLess(expected['p0.separation'], 0)
            elif case.category == 'wyprzedzajacy':
                self.assertEqual(expected['pointCount'], 1)
                self.assertGreater(expected['p0.separation'], 0)
                self.assertLess(expected['p0.separation'], p.SPECULATIVE)

    def test_threshold_has_nine_on_either_side(self):
        counts = [p.geometry(case)[0]['pointCount'] for case in g.cases() if case.edge]
        self.assertEqual(counts, [1] * 9 + [0] * 9)

if __name__ == '__main__':
    unittest.main()
