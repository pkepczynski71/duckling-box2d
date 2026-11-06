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
spec = importlib.util.spec_from_file_location('porownaj_ruch', HERE/'porownaj-ruch.py')
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)
g = p.g

def manifest_without_repo_root(manifest):
    root = json.dumps(os.path.normcase(str(ROOT.resolve())))[1:-1]
    flags = re.IGNORECASE if os.path.normcase('A') == 'a' else 0
    separator = re.escape(json.dumps(os.sep)[1:-1])
    return re.sub(r'(?<!\\)"' + re.escape(root) + r'(?="|' + separator + ')', '"',
                  json.dumps(manifest), flags=flags)


def analytic_case(id=1, steps=3, gravity=(0, 0), velocity=(0, 0), commands=(), position=(0, 0), maximum=400):
    w = list(g.cases()[0].words)
    w[:6] = (*map(g.bits, (*gravity, maximum, .25)), 4, steps)
    w[6:18] = (*map(g.bits, (*position, 1, 0, *velocity, 0, 0, 0, 1)), 0, 0)
    w[18:38] = (1, *g.box(), *((0,)*9), len(commands))
    w[38:] = tuple(v for cmd in commands for v in cmd)+((0,)*(48-6*len(commands)))
    g.validate(w)
    return g.Case(id, 'analityczny', tuple(w))


def fixture(cases=None):
                                                                                 
    cases = tuple(cases) if cases is not None else tuple(analytic_case(i, position=(i/8, -i/4)) for i in range(1, 67))
    lines = [f'PORT3 {len(cases)}']
    for case in cases:
        mass = (g.bits(2), g.bits(5/6), 0, 0)
        lines.append(f'M {case.id} '+' '.join(map(str, (*case.words, *mass))))
        w = case.words
        dt, sub = g.number(w[3]), w[4]
        px, py = map(g.number, w[6:8])
        vx, vy = map(g.number, w[10:12])
        ax, ay = (g.number(v)*g.number(w[15]) for v in w[:2])
        commands = tuple(w[38+6*i:44+6*i] for i in range(w[37]))
        for k in range(1, w[5]+1):
            t, n = k*dt, k*sub
            velocity = [vx+ax*t, vy+ay*t]
            center = [px+vx*t+ax*t*t*(1+1/n)/2, py+vy*t+ay*t*t*(1+1/n)/2]
            for cmd in commands:
                if cmd[0] <= k and cmd[1] in (1, 4):
                    for j, value in enumerate(map(g.number, cmd[2:4])):
                        velocity[j] += value/2*(dt if cmd[1] == 1 else 1)
                        factor = dt*dt*((k-cmd[0])+(sub+1)/(2*sub)) if cmd[1] == 1 else dt*(k-cmd[0]+1)
                        center[j] += value/2*factor
            state = (*center, 1, 0, *center, *velocity, 0)
            lines.append(f'S {case.id} {k} '+' '.join(str(g.bits(v)) for v in state))
    return cases, '\n'.join((*lines, f'END {len(cases)}', ''))


def change(log, tag, id, step, field, value=None):
    lines = log.splitlines()
    prefix = f'{tag} {id} '+(f'{step} ' if tag == 'S' else '')
    index = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    tokens = lines[index].split(' ')
    offset = (3 if tag == 'S' else 2)+field
    tokens[offset] = str(int(tokens[offset]) ^ 1 if value is None else value)
    lines[index] = ' '.join(tokens)
    return '\n'.join(lines)+'\n'


class GeneratorTests(unittest.TestCase):
    def test_population_and_coverage(self):
        rows = g.cases()[:66]
        self.assertEqual(rows, g.cases()[:66])
        self.assertEqual(len(rows), 66)
        self.assertEqual(len({c.words for c in rows}), 66)
        self.assertEqual(sum(c.words[5] for c in rows), 24520)
        self.assertEqual(Counter(c.category for c in rows), {
            'spoczynek': 4, 'grawitacja': 9, 'tlumienie': 6, 'skala-grawitacji': 3,
            'staly-obrot': 4, 'prog-liniowy': 6, 'prog-obrotowy': 12, 'srodek-masy': 6,
            'polecenia': 8, 'wspolrzedne': 4, 'polaczenia': 4})
        self.assertEqual({c.words[4] for c in rows}, {1, 4, 8})
        self.assertEqual({c.words[3] for c in rows}, set(g.DT_WORDS))
        self.assertEqual({c.words[18] for c in rows}, {1, 2})
        self.assertEqual({c.words[39+6*i] for c in rows for i in range(c.words[37])}, set(range(6)))
        self.assertTrue(any(c.words[5] == 600 for c in rows))
        for c in rows:
            g.validate(c.words)

    def test_all_field_indices_and_c_population(self):
        self.assertEqual(len(g.INPUT_FIELDS), 86)
        for index, name in ((0, 'gravity.x'), (18, 'shapeCount'), (19, 'shape[0].type'),
                            (28, 'shape[1].type'), (37, 'commandCount'), (38, 'command[0].step'),
                            (85, 'command[7].d')):
            self.assertEqual(g.INPUT_FIELDS[index], name)
        source = (HERE/'kontrola-ruch.c').read_text(encoding='utf-8')
        self.assertIn(f'CASE_COUNT = {g.COUNT}', source)
        self.assertIn('INPUT_WORDS = 86', source)

    def test_review_cases_append_without_changing_original_inputs(self):
        rows = g.cases()
        self.assertEqual(len(rows), 70)
        self.assertEqual(sum(c.words[5] for c in rows), 25256)
        self.assertEqual(len({c.words for c in rows}), 70)
        for name, digest in (
                ('przypadki-ruch.csv', '59bfbe4553bc670ad956d9779fb0d0db0c9399892461806450c111c800485efa'),
                ('przypadki-ruch-stdin.csv', '5e1d96f7ddea1a7e26b1796618c08eb151e488fd8c83dd67f94d7ae45dbbb778')):
            prefix = b'\n'.join((HERE/name).read_bytes().replace(b'\r\n', b'\n').splitlines()[:66])+b'\n'
            self.assertEqual(hashlib.sha256(prefix).hexdigest(), digest)
        self.assertEqual(rows[66].words[16], 1)
        self.assertNotEqual(rows[66].words[12], 0)
        self.assertEqual(rows[67].words[37], 8)
        self.assertEqual([rows[67].words[39+6*i] for i in (5, 6, 7)], [5, 0, 2])
        self.assertEqual([rows[67].words[38+6*i] for i in (5, 6, 7)], [60, 60, 120])
        for case in rows[68:]:
            self.assertEqual(g.f32(g.number(case.words[2])**2), 0)
            self.assertEqual(g.f32(g.number(case.words[10])**2), 0)
            self.assertGreater(g.number(case.words[2]), 0)
            g.validate(case.words)

    def test_thresholds_are_exact_neighbors(self):
        linear = [c for c in g.cases() if c.category == 'prog-liniowy']
        for maximum, group in zip((2, 400), (linear[:3], linear[3:])):
            self.assertEqual([c.words[10] for c in group], [g.bits(maximum)+d for d in (-1, 0, 1)])
            self.assertEqual([c.words[2] for c in group], [g.bits(maximum)]*3)
        angular = [c for c in g.cases() if c.category == 'prog-obrotowy']
        for offset in range(0, 12, 3):
            group = angular[offset:offset+3]
            self.assertEqual([c.words[12] for c in group], [g.bits(g.angular_limit(g.DT[0]))+d for d in (-1, 0, 1)])
        self.assertEqual({(c.words[4], c.words[17]) for c in angular}, {(1, 0), (1, 1), (8, 0), (8, 1)})

    def test_shape_order_pair_and_commands(self):
        rows = [c for c in g.cases() if c.category == 'srodek-masy']
        a, b = rows[3].words, rows[4].words
        self.assertEqual(a[19:28], b[28:37])
        self.assertEqual(a[28:37], b[19:28])
        rows = [c for c in g.cases() if c.category == 'polecenia']
        for case in rows[:6]:
            self.assertEqual([case.words[38+6*i] for i in range(3)], [1, 300, 600])
        self.assertEqual(rows[6].words[38:56:6], (1, 1, 1))

    def test_roundtrip_both_transports_and_committed_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            rows = g.write_inputs(directory)
            self.assertEqual(g.read_inputs(Path(directory)/'przypadki-ruch.csv'), rows)
            decimal = (Path(directory)/'przypadki-ruch-stdin.csv').read_text().splitlines()
            for case, line in zip(rows, decimal):
                self.assertEqual(tuple(map(int, line.split())), (case.id, *case.words))
            for name in ('przypadki-ruch.csv', 'przypadki-ruch-stdin.csv'):
                self.assertEqual((Path(directory)/name).read_bytes(), (HERE/name).read_bytes())

    def test_native_constants_disagreement_and_nonzero_code_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            for code, stdout in ((0, 'bad'), (7, ' '.join(f'{v:08x}' for v in g.constants()))):
                with patch.object(g.subprocess, 'run') as run:
                    run.return_value.returncode, run.return_value.stdout, run.return_value.stderr = code, stdout, ''
                    with self.assertRaisesRegex(ValueError, 'Native C f32 constants disagree'):
                        g.write_inputs(directory, 'mocked-control')
            with patch.object(g.subprocess, 'run') as run:
                run.return_value.returncode = 0
                run.return_value.stdout = ' '.join(f'{v:08x}' for v in g.constants())+'\n'
                run.return_value.stderr = ''
                self.assertEqual(len(g.write_inputs(directory, 'mocked-control')), g.COUNT)
                self.assertEqual(run.call_args.args[0], ['mocked-control', '--stale'])

    def test_bad_input_and_padding_rejected(self):
        for index, value in ((4, 0), (5, 601), (16, 2), (18, 3), (28, 1), (37, 9),
                             (38, 1), (2, g.bits(float('inf'))), (3, 0), (8, 0)):
            w = list(g.cases()[0].words)
            w[index] = value
            with self.subTest(index=index), self.assertRaises(ValueError):
                g.validate(w)
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            g.write_inputs(directory)
            path = Path(directory)/'przypadki-ruch.csv'
            original = path.read_text()
            for bad in (original.replace('00000000', '0000000A', 1), original+'\n',
                        original.replace('00000000', '00000001', 1), original.replace('1 ', '2 ', 1)):
                path.write_text(bad)
                with self.assertRaises(ValueError):
                    g.read_inputs(path)

    def test_review_mutation_recipes_point_to_existing_cases(self):
        data = json.loads((HERE/'mutacje-ruch.json').read_text(encoding='utf-8'))
        self.assertIn('UNMEASURED', data['status'])
        self.assertEqual(len(data['mutations']), 8)
        self.assertTrue({'kolejnosc-komend', 'brak-zacisku-liniowego', 'brak-zacisku-obrotowego',
                         'odwrotna-kolejnosc-ksztaltow', 'brak-zerowania-sily'}
                        <= {m['name'] for m in data['mutations']})
        for mutation in data['mutations']:
            self.assertIsNone(mutation['result'])
            self.assertTrue(all(1 <= id <= g.COUNT for id in mutation['cases']))
            self.assertTrue(set(mutation['observe']) <= set((*p.MASS_FIELDS, *p.STATE_FIELDS)))


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.good = fixture()

    def fails(self, c=None, d=None, code=0, ccode=0, text=None):
        result, report = p.compare(self.good if c is None else c, self.good if d is None else d,
                                   code, self.cases, ccode)
        self.assertEqual(result, 1, report)
        if text:
            self.assertIn(text, report)
        return report

    def test_good_analytic_full_population(self):
        code, report = p.compare(self.good, self.good, 0, self.cases)
        self.assertEqual(code, 0, report)
        self.assertIn('66/66; echo: 66/66; S: 198/198', report)

    def test_full_24520_step_population_and_last_step_bit(self):
        cases, good = fixture(analytic_case(c.id, c.words[5], position=(c.id/8, -c.id/4))
                              for c in g.cases()[:66])
        code, report = p.compare(good, good, 0, cases)
        self.assertEqual(code, 0, report)
        self.assertIn('S: 24520/24520', report)
        bad = change(good, 'S', 66, 400, 8)
        code, report = p.compare(good, bad, 0, cases)
        self.assertEqual(code, 1)
        self.assertIn('PIERWSZY ROZJAZD: case 66, step 400, field angularVelocity', report)

    def test_appended_population_frames_all_25256_steps(self):
        cases, good = fixture(analytic_case(c.id, c.words[5]) for c in g.cases())
        code, report = p.compare(good, good, 0, cases)
        self.assertEqual(code, 0, report)
        self.assertIn('70/70; echo: 70/70; S: 25256/25256', report)
        bad = change(good, 'S', 70, 8, 8)
        code, report = p.compare(good, bad, 0, cases)
        self.assertEqual(code, 1, report)
        self.assertIn('PIERWSZY ROZJAZD: case 70, step 8, field angularVelocity', report)

    def test_bad_bit_in_every_step_is_rejected(self):
        for case in self.cases:
            for step in range(1, case.words[5]+1):
                with self.subTest(case=case.id, step=step):
                    self.fails(d=change(self.good, 'S', case.id, step, 8),
                               text=f'case {case.id}, step {step}, field angularVelocity')

    def test_every_state_mass_and_echo_field_is_compared(self):
        for field in range(9):
            self.fails(d=change(self.good, 'S', 2, 2, field), text='field '+p.STATE_FIELDS[field])
        for field in range(90):
            self.fails(d=change(self.good, 'M', 2, 0, field),
                       text=('echo.'+g.INPUT_FIELDS[field] if field < 86 else p.MASS_FIELDS[field-86]))

    def test_first_difference_is_in_input_order(self):
        bad = change(self.good, 'S', 65, 3, 0)
        bad = change(bad, 'S', 2, 2, 7)
        bad = change(bad, 'S', 2, 1, 8)
        report = self.fails(d=bad)
        first = next(line for line in report.splitlines() if line.startswith('PIERWSZY ROZJAZD:'))
        self.assertIn('case 2, step 1, field angularVelocity', first)

    def test_missing_extra_duplicate_and_reordered_rows(self):
        lines = self.good.splitlines()
        for records in (lines[:2]+lines[3:], lines+[lines[2]], lines[:3]+[lines[2]]+lines[3:],
                        lines[:2]+[lines[3], lines[2]]+lines[4:], lines[:-1]):
            self.fails(d='\n'.join(records)+'\n')

    def test_wrong_step_count_and_echo_in_both_logs(self):
        bad = change(self.good, 'M', 2, 0, 5, 2)
        self.fails(c=bad, d=bad, text='echo.stepCount')
        bad = change(self.good, 'M', 2, 0, 0)
        self.fails(c=bad, d=bad, text='echo.gravity.x')

    def test_wrong_step_index_id_header_footer_and_format(self):
        for old, new in (('S 2 2 ', 'S 2 3 '), ('S 2 2 ', 'S 3 2 '), ('PORT3 66', 'PORT3 65'),
                         ('END 66', 'END 67'), ('S 2 2 ', 'S 2 2  '), ('M 2 ', 'M 02 ')):
            self.fails(d=self.good.replace(old, new, 1))
        for value in (-1, 2**32):
            self.fails(d=change(self.good, 'S', 2, 2, 0, value))
        line = next(line for line in self.good.splitlines() if line.startswith('S 2 2 '))
        tokens = line.split(' ')
        tokens[3] = '0'+tokens[3]
        self.fails(d=self.good.replace(line, ' '.join(tokens), 1))

    def test_exit_codes_on_either_side(self):
        for code in (1, 124, 125, -9):
            self.fails(code=code, text=f'Duckling: code exit {code}')
            self.fails(ccode=code, text=f'C: code exit {code}')

    def test_zero_sign_is_not_ignored(self):
        self.fails(d=change(self.good, 'S', 2, 2, 8, 0x80000000), text='angularVelocity')

    def test_crlf_and_optional_last_newline(self):
        for text in (self.good.rstrip('\n'), self.good.replace('\n', '\r\n')):
            self.assertEqual(p.compare(text, text, 0, self.cases)[0], 0)

    def test_missing_duckling_keeps_independent_c_count(self):
        self.fails(d='', code=125, text='C 66/66; Duckling 0/66')

    def test_cli_records_red_for_missing_files_and_exit_code(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            directory = Path(directory)
            report = directory/'raport.md'
            self.assertEqual(p.main(['--c', str(directory/'missing-c'), '--duckling', str(directory/'missing-d'),
                '--wejscie', str(directory/'missing-input'), '--raport', str(report),
                '--kod-c', '0', '--kod-wyjscia', '125']), 1)
            self.assertIn('RESULT: FAIL', report.read_text(encoding='utf-8'))


class IndependentTests(unittest.TestCase):
    def compare_fixture(self, cases):
        cases, log = fixture(cases)
        code, report = p.compare(log, log, 0, cases)
        self.assertEqual(code, 0, report)
        return cases, log

    def test_closed_form_gravity_and_constant_velocity(self):
                                                                                    
        self.compare_fixture((analytic_case(gravity=(.5, -10), velocity=(2, -.25), steps=600, maximum=4096),))
        self.compare_fixture((analytic_case(velocity=(1, -.5), steps=600),))

    def test_same_analytic_path_is_red_when_it_exceeds_a_400_limit(self):
        case = analytic_case(gravity=(.5, -10), velocity=(2, -.25), steps=600)
        words = list(case.words)
        words[2] = g.bits(400)
        cases, log = fixture((replace(case, words=tuple(words)),))
        code, report = p.compare(log, log, 0, cases)
        self.assertEqual(code, 1)
        self.assertIn('step 160: independent maximumLinearSpeed', report)

    def test_center_impulse_momentum_and_one_step_force(self):
        self.compare_fixture((analytic_case(commands=(g.command(1, 4, 2, -4), g.command(3, 4, -1, 2)), steps=5),))
        cases, log = self.compare_fixture((analytic_case(commands=(g.command(1, 1, 8),), steps=5),))
                                                                                             
        bad = change(log, 'S', 1, 2, 6, g.bits(2))
        code, report = p.compare(bad, bad, 0, cases)
        self.assertEqual(code, 1)
        self.assertIn('independent field linearVelocity.x', report)

    def test_common_mode_mass_q_center_velocity_and_nan_fail(self):
        cases, log = self.compare_fixture((analytic_case(),))
        for tag, field, value, expected in (
                ('M', 86, g.bits(3), 'field mass'), ('M', 88, g.bits(1), 'localCenter.x'),
                ('S', 2, g.bits(.5), 'norma'), ('S', 4, g.bits(10), 'worldCenter.x'),
                ('S', 6, g.bits(1), 'linearVelocity.x'), ('S', 8, g.bits(1), 'angularVelocity'),
                ('S', 8, g.bits(float('nan')), 'NaN/Inf')):
            bad = change(log, tag, 1, 2 if tag == 'S' else 0, field, value)
            code, report = p.compare(bad, bad, 0, cases)
            self.assertEqual(code, 1, report)
            self.assertIn(expected, report)

    def test_dynamic_omissions_do_not_disable_q_or_mass(self):
        case = analytic_case()
        w = list(case.words)
        w[13] = g.bits(.25)
        case = replace(case, words=tuple(w))
        cases, log = self.compare_fixture((case,))
        bad = change(log, 'S', 1, 2, 2, g.bits(.5))
        code, report = p.compare(bad, bad, 0, cases)
        self.assertEqual(code, 1)
        self.assertIn('norma', report)
        self.assertIn('Eb6112cde002b', report)

    def test_sum_of_two_elementary_masses(self):
        w = list(analytic_case().words)
        w[18:37] = (2, *g.circle(density=2, radius=.5, center=(1, 0)),
                     *g.box(density=3, half=(.5, .25), center=(-1, 0)))
        mass, cx, cy = p.shape_mass_center(w)
        self.assertAlmostEqual(mass, .5*math.pi+1.5)
        self.assertAlmostEqual(cx, (.5*math.pi-1.5)/mass)
        self.assertEqual(cy, 0)

    def test_stationary_unit_rotation_cannot_change_on_both_sides(self):
        case = replace(analytic_case(), category='spoczynek')
        cases, log = self.compare_fixture((case,))
        for step in (1, 2, 3):
            log = change(log, 'S', 1, step, 2, 0)
            log = change(log, 'S', 1, step, 3, g.bits(1))
        code, report = p.compare(log, log, 0, cases)
        self.assertEqual(code, 1)
        self.assertIn('E1a5e497a2bfa Ea5703a566bf2', report)

    def test_cancelled_large_forces_do_not_silently_skip_dynamics(self):
        case = g.cases()[56]
        mass = tuple(map(g.bits, (2, 5/6, 0, 0)))
        self.assertIsNone(p.motion_parameters(case, mass)[-1])

    def test_speed_bounds_apply_even_when_equations_are_skipped(self):
        for category in ('tlumienie', 'prog-liniowy', 'prog-obrotowy'):
            case = next(c for c in g.cases() if c.category == category)
            mass = tuple(map(g.bits, (2, 5/6, 0, 0)))
            params = p.motion_parameters(case, mass)
            state = (0, 0, 1, 0, 0, 0, g.number(case.words[2])*2, 0, 0)
            errors = p.velocity_properties(case, 1, state, params, None, 'C')
            self.assertTrue(any('maximumLinearSpeed' in e for e in errors), errors)
            state = (0, 0, 1, 0, 0, 0, 0, 0, 2*math.pi/(4*g.number(case.words[3])))
            errors = p.velocity_properties(case, 1, state, params, None, 'C')
            self.assertTrue(any('granica obrotu' in e for e in errors), errors)
        case = next(c for c in g.cases() if c.words[17])
        errors = p.velocity_properties(case, 1, state, p.motion_parameters(case, mass), None, 'C')
        self.assertFalse(any('granica obrotu' in e for e in errors), errors)

    def test_identical_bad_caps_and_missing_damping_fail_both_logs(self):
        case = analytic_case()
        words = list(case.words)
        words[13] = g.bits(.25)
        cases, log = self.compare_fixture((replace(case, words=tuple(words)),))
        for field, value, message in ((6, 800, 'maximumLinearSpeed'),
                                      (8, 2*math.pi, 'granica obrotu')):
            bad = change(log, 'S', 1, 2, field, g.bits(value))
            code, report = p.compare(bad, bad, 0, cases)
            self.assertEqual(code, 1, report)
            self.assertIn(message, report)
                                                                           
        case = analytic_case(velocity=(3, -4))
        words = list(case.words)
        words[13] = g.bits(.25)
        cases, bad = fixture((replace(case, words=tuple(words)),))
        code, report = p.compare(bad, bad, 0, cases)
        self.assertEqual(code, 1, report)
        self.assertIn('Eb6112cde002b Pade', report)

    def test_free_damping_matches_closed_form_and_rejects_growth_or_wrong_rate(self):
        case = analytic_case(steps=4, velocity=(3, -4))
        words = list(case.words)
        words[12:15] = tuple(map(g.bits, (-2, .5, .75)))
        case = replace(case, words=tuple(words))
        mass = tuple(map(g.bits, (2, 5/6, 0, 0)))
        params = p.motion_parameters(case, mass)
        previous = None
        for step in range(1, 5):
            linear = (1+.25/4*.5)**(-4*step)
            angular = (1+.25/4*.75)**(-4*step)
            values = (0, 0, 1, 0, 0, 0, 3*linear, -4*linear, -2*angular)
            self.assertEqual(p.velocity_properties(case, step, values, params, previous, 'C'), [])
            previous = tuple(map(g.bits, values))
        for bad_velocity, bad_angular, expected in ((6, -3, 'monotonicznosci'), (1, -.5, 'Pade')):
            values = (0, 0, 1, 0, 0, 0, bad_velocity, 0, bad_angular)
            errors = p.velocity_properties(case, 4, values, params, previous, 'C')
            self.assertTrue(any(expected in e for e in errors), errors)

    def test_bound_rounding_tolerance_and_tiny_finite_inputs(self):
        mass = tuple(map(g.bits, (2, 5/6, 0, 0)))
        for case in g.cases()[68:]:
            values = (0, 0, 1, 0, 0, 0, g.number(case.words[10]), 0, 0)
            self.assertEqual(p.velocity_properties(case, 1, values, p.motion_parameters(case, mass), None, 'C'), [])
        case = analytic_case()
        limit = g.number(case.words[2])
        values = (0, 0, 1, 0, 0, 0, limit*(1+4*p.EPS), 0, 0)
        self.assertEqual(p.velocity_properties(case, 1, values, p.motion_parameters(case, mass), None, 'C'), [])


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        environment = patch.dict(os.environ, RESULT_DIR=str(directory/'out'), RUNNER_TEMP=str(directory/'temp'))
        environment.start()
        self.addCleanup(environment.stop)
        spec = importlib.util.spec_from_file_location('port_ci_motion_test', HERE/'ci.py')
        self.ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ci)

    def test_missing_motion_is_explicit_red_and_125(self):
        with patch.object(self.ci, 'PORT', Path(self.temp.name)/'missing'):
            self.assertEqual(self.ci.duckling_motion('never-run'), 1)
        self.assertEqual((self.ci.OUT/'duckling-ruch-kod.csv').read_text(), '125\n')
        self.assertIn('missing port motion', (self.ci.OUT/'brak-portu-ruch.csv').read_text(encoding='utf-8'))

    def test_compile_failure_preserves_previous_results_and_manifest(self):
        root = Path(self.temp.name)
        port = root/'silnik/port'
        port.mkdir(parents=True)
        (port/'ruch.dk').touch()
        physics = root/'silnik/fizyka'
        physics.mkdir()
        for name in ('fizyka.dk', 'ruch.dk'):
            (physics/name).touch()
        for name, text in (('duckling.csv', 'circles'), ('duckling-wiel.csv', 'polygons')):
            (self.ci.OUT/name).write_text(text)
        with patch.object(self.ci, 'ROOT', root), patch.object(self.ci, 'PORT', port),\
                patch.object(self.ci.base, 'run', return_value=19) as run:
            self.assertEqual(self.ci.duckling_motion('never-run'), 19)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], 'duckling-ruch-kompilacja')
        self.assertEqual((self.ci.OUT/'duckling-ruch-kod.csv').read_text(), '125\n')
        self.assertEqual((self.ci.OUT/'duckling.csv').read_text(), 'circles')
        self.assertEqual((self.ci.OUT/'duckling-wiel.csv').read_text(), 'polygons')
        manifest = json.loads((self.ci.OUT/'duckling-ruch-manifest.json').read_text())
        self.assertEqual(Path(manifest['packages'][0]['path']), physics)
        self.assertEqual(manifest['packages'][1]['dependencies'], [{'id': 'fizyka'}])
        self.assertEqual(manifest['tasks'][1]['linking_options']['additional_link_options'][-1], '-lm')
        self.assertNotIn('box2d', manifest_without_repo_root(manifest))
        self.assertIn('Eab3f151cdcce E428c9140f6d7 E2f2457405c54 E35e99f929e01 E54ccc6038f6e',
                      (self.ci.OUT/'blad-portu-ruch.csv').read_text(encoding='utf-8'))

    def test_motion_check_runs_tests_even_when_comparison_is_red(self):
        with patch.object(self.ci.base, 'run', side_effect=[1, 0]) as run:
            self.assertEqual(self.ci.check_motion(), 1)
        self.assertEqual([call.args[0] for call in run.call_args_list], ['porownanie-ruch', 'sprawdziany-ruch'])
        self.assertTrue((self.ci.OUT/'COMPARISON-RUCH.md').is_file())

    def test_polygon_compile_failure_names_shared_library_dependency(self):
        with patch.object(self.ci.base, 'run', return_value=19):
            self.assertEqual(self.ci.duckling_polygons('never-run'), 19)
        message = (self.ci.OUT/'blad-portu-wiel.csv').read_text(encoding='utf-8')
        self.assertIn('Ea36c0cd8ffd0 E282b94cc1bb1 E2f2457405c54, E6fe2a0f5118f E2016d624afef.E867b4bf4357a', message)
        self.assertIn('E03b382aabe85 three ports', message)
        self.assertIn('circles have separate manifest file', message)

    def test_workflow_runs_old_and_new_checks_always_with_pinned_actions(self):
        from public_ci import check
        check(self)


if __name__ == '__main__':
    unittest.main()
