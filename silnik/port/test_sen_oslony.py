from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                              
import importlib.util
import copy
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


f = load('sen_test_fixtures', 'fixtury-sen.py')
n = load('sen_test_negative', 'ujemne-sen.py')
m = load('sen_test_model', 'model-sen.py')
native = load('sen_test_native', 'mutacje-sen.py')
ledger = load('sen_test_ledger', 'sen-ledger-test.py')

                                                                       
                                                                            
RESISTANCE_CLASSES = {
    'missing-snapshot': 'test_missing_duplicate_reordered_snapshot_and_group',
    'duplicate-snapshot': 'test_missing_duplicate_reordered_snapshot_and_group',
    'reordered-snapshot': 'test_missing_duplicate_reordered_snapshot_and_group',
    'M-count-after-sleep': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
    'fellAsleep': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
    'GS-awake-sleeping': 'test_model_checks_each_side_even_identically_corrupt',
    'historical-number-reuse': 'test_historical_contact_events_copies_and_touching_values',
    'signed-zero': 'test_public_projection_leaks_and_signed_zero',
    'ticket-high': 'test_model_checks_each_side_even_identically_corrupt',
    'owning-set': 'test_model_checks_each_side_even_identically_corrupt',
    'localIndex': 'test_model_checks_each_side_even_identically_corrupt',
    'sleeping-CS-missing': 'test_sleeping_contacts_missing_duplicate_defined_and_pool',
    'sleeping-CS-duplicate': 'test_sleeping_contacts_missing_duplicate_defined_and_pool',
    'rollingDefined': 'test_sleeping_contacts_missing_duplicate_defined_and_pool',
    'SS-SD-SM-pool-completeness': 'test_model_checks_each_side_even_identically_corrupt',
    'sim-impulse-transfer': 'test_pure_transfer_preserves_cache_material_sim_and_impulses',
    'projection-private-leak': 'test_public_projection_leaks_and_signed_zero',
    'canonical-H': 'test_model_checks_each_side_even_identically_corrupt',
    'canonical-D': 'test_model_checks_each_side_even_identically_corrupt',
    'echo': 'test_model_checks_each_side_even_identically_corrupt',
    'stderr-extra': 'test_native_process_evidence_cannot_be_skip_success',
    'EOF': 'test_model_checks_each_side_even_identically_corrupt',
    'build-code': 'test_native_process_evidence_cannot_be_skip_success',
    'process-code': 'test_native_process_evidence_cannot_be_skip_success',
    'candidate-phase0': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
    'LIFO': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
    'owned-copies': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
    'truncated-END': 'test_model_checks_each_side_even_identically_corrupt',
    'positive-Step-count': 'test_move_count_fell_asleep_copies_and_lifo_corruptions',
}


def contract_sample():
    text = norm_text(HERE / 'fixtures/norms/KONTRAKT-11.json')
    section = text.split('### 6.3.', 1)[1].split('## 7.', 1)[0]
    blocks = re.findall(r'```text\n(.*?)```', section, re.S)
    return next(b for b in blocks if b.startswith('GUARD11 1\nG ') and '\nCASE ' in b)


def sample_cases(text):
    return (tuple(value[2:] for tag, value in map(m.parse, text.splitlines(keepends=True)) if tag == 'E'),)


class GuardInputs(unittest.TestCase):
    def test_guard_validator_all_helper_frames_and_full_snapshot(self):
        helpers = [item for item in f.definitions() if not item.rows]
        self.assertTrue(helpers)
        for item in helpers:
            with self.subTest(item=item.name):
                m.validate_guard_stream(item.expected_helper_output().decode(), item)
        sample = contract_sample()
        item = f.fixture('NORMATIVE', 'self-test', 0, rows=sample_cases(sample)[0], last_status=0)
        receipt = m.validate_guard_stream(sample, item)
        self.assertEqual(receipt['snapshots'], 2)
        for text in (sample.replace('GA 1 ', 'GA 2 ', 1), sample + '\n',
                     sample.replace('G 1 0 0 2', 'G 1 0 1 2', 1)):
            with self.subTest(text=text[:50]), self.assertRaises(ValueError): m.validate_guard_stream(text, item)
    def test_native_recipes_target_actual_product_once(self):
        manifest = native.recipes()
        self.assertEqual(manifest['recipe_count'], 16)
        self.assertEqual(len(manifest['native_mutations']), 16)
        matches = native.applicability(HERE.parents[1])
        self.assertTrue(all(row['single_hit'] and row['hits'] == 1 for row in matches), matches)
        preparations = native.preparations(HERE.parents[1])
        self.assertEqual(len(preparations),16)
        self.assertTrue(all(row['status'] == 'OK' for row in preparations),preparations)
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['core_classes_verified'], 0)
        self.assertEqual(manifest['M12'], 'ODROCZONE_DO_KROKU_11')

    def test_inherited_native_fixture_does_not_replace_helper_results(self):
        src = (HERE / 'solver-swiata.dk').read_text(encoding='utf-8')
        actual = f.inherited_helper_driver(src)
        expected = f.old.native_driver(src, 4).replace('GUARD10', 'GUARD11').replace('GR10', 'GR11')
        self.assertEqual(actual, expected)
        self.assertIn('accepted = game.validSolverWorldParameters', actual)
        self.assertIn('accepted = game.validStepParameters', actual)
    def test_threshold_all_routes_and_signed_zeros(self):
        items = f.definitions()
        for route in range(6):
            selected = [x for x in items if x.kind == 5 and x.words[0] == route]
            self.assertEqual({x.words[1] for x in selected}, {0x7f800000, 0x7fc00000, 0xff800000, f.bits(-1), 0, 0x80000000})
            self.assertEqual([x.status for x in selected if x.words[1] in (0, 0x80000000)], [0, 0])

    def test_paired_u32_encodings_and_budget(self):
        items = f.definitions(); self.assertEqual(len(items), 96)
        self.assertLessEqual(len(items), 128)
        for item in items:
            c, d = item.encode().splitlines(), item.encode(True).splitlines()
            self.assertEqual(c[:2], d[:2])
            self.assertEqual(tuple(int(w, 16) for w in c[2].split()[2:]), item.words)
            self.assertEqual(tuple(int(w) for w in d[2].split()[2:]), item.words)
            self.assertEqual(len(c), 3 + len(item.rows))

    def test_true_bounds_not_old_nonmonotonic_helper(self):
        for count in (0, 1, 128, 129, 131059): self.assertTrue(m.sleep_body_fit(count))
        for count in (-1, 131060, 131066, 131068, 1 << 63): self.assertFalse(m.sleep_body_fit(count))
        self.assertTrue(m.m.body_fit(131068))
        self.assertIsNone(m.m.checked_sum(0x7fffffffffffffff, 1))

    def test_parameter_binary32_and_signed_zero_domains(self):
        for word in (0, 0x80000000, f.bits(.05)):
            self.assertTrue(m.body_parameters_valid(f.replace(f.body(), 18, word)[1:]))
        for word in (0x7f800000, 0xff800000, 0x7fc00000, f.bits(-1)):
            self.assertFalse(m.body_parameters_valid(f.replace(f.body(), 18, word)[1:]))
        self.assertFalse(m.body_parameters_valid(f.replace(f.body(), 6, 0)[1:]))
        self.assertFalse(m.world_parameters_valid(f.replace(f.world(), 4, 0)[1:]))
        self.assertTrue(m.world_parameters_valid(f.replace(f.world(), 5, 0x80000000)[1:]))

    def test_copy_probes_are_separate_native_helper_inputs(self):
        items = {x.name: x for x in f.definitions()}
        for name, kind, helper, low in (('MOVE-COPY', 9, 40, 2), ('STATE-COPY', 10, 41, 1)):
            item = items[name]
            self.assertEqual((item.kind, item.rows, item.seed), (kind, (), 0))
            self.assertEqual(item.helper_record(), (1, 0, helper, 0, 1, low, 3))
            parsed = [m.parse(line) for line in item.expected_helper_output().decode().splitlines(keepends=True)]
            m.guard_result(item, parsed)

    def test_m12_input_requires_disabled_contact_growth_and_real_link(self):
        rows = f.m12_operations()
        self.assertEqual(len(rows), 10)
        bodies = [op for op in rows if op[0] == 57]
        self.assertEqual([op[18] for op in bodies], [0, 0, 0, 1])
        self.assertEqual(len([op for op in rows if op[0] == 40]), 4)
        recipe = native.m12_recipe(HERE.parents[1])
        source = (HERE.parents[1] / recipe['source']).read_text(encoding='utf-8')
        changed = native.base.apply(source, recipe)
        lo, hi = native.base.function_span(changed, recipe['scope'])
        body = changed[lo:hi]
        self.assertLess(body.index('var fresh: ref ContactSim'), body.index('b2LinkContact(world, id);'))
        self.assertFalse(recipe['counted_as_killed'])
        with self.assertRaises(ValueError): native.check_m12_setup([])


class NegativeInputs(unittest.TestCase):
    def test_all_fatal_classes_and_subclasses_are_paired(self):
        items = n.variants()
        self.assertEqual({x.error for x in items}, {f'F{i:02}' for i in range(1, 16)})
        self.assertEqual(len({x.name for x in items}), len(items))
        self.assertEqual(len(items), 90)
        for item in items:
            self.assertTrue(item.stderr.endswith(b'\n'))
            self.assertEqual(item.stderr.count(b'\n'), 1)
            self.assertEqual(len(item.controls), 2)
        for expected in ('F01-bom', 'F01-ascii', 'F01-spacing', 'F01-tab', 'F01-cr',
                         'F03-seq', 'F04-overflow', 'F04-arity63', 'F04-line2049',
                         'F09-empty-source', 'F09-target-collision', 'F10-rotation',
                         'G-F03-helper-seed', 'G-F10-kind11', 'G-F04-arity63', 'G-F14-GA-eof'):
            self.assertIn(expected, {x.name for x in items})

    def test_exact_stderr_code_and_no_extra_output(self):
        probe = n.variants()[0]
        n.check(probe, 2, b'', probe.stderr, b'')
        for code, out, err in ((0, b'', probe.stderr), (2, b'x', probe.stderr),
                               (2, b'', probe.stderr + b'runtime\n'), (2, b'', probe.stderr[:-1])):
            with self.subTest(code=code, out=out, err=err), self.assertRaises(ValueError):
                n.check(probe, code, out, err, b'')

    def test_fatal_prefix_is_full_clean_control(self):
        probe = next(p for p in n.variants() if p.name == 'F10-threshold-negative')
        control = b'PORT11 1\nCASE 1 3\nE 1 1 ...\nR 1 1 ...\nE 1 2 ...\nR 1 2 ...\nE 1 3 ...\nENDCASE 1\nEND 1\n'
        self.assertEqual(n.expected_prefix(probe, control), control.split(b'\nE 1 3')[0] + b'\n')
        trailing = next(p for p in n.variants() if p.name == 'F15-blank')
        self.assertEqual(n.expected_prefix(trailing, control), control.rsplit(b'END 1\n',1)[0])
        n.check(trailing,2,n.expected_prefix(trailing,control),trailing.stderr,control)
        with self.assertRaises(ValueError): n.check(trailing,2,control,trailing.stderr,control)

    def test_positive_line_endings(self):
        forms = n.positives(); self.assertEqual([x[0] for x in forms], ['LF', 'CRLF', 'EOF'])
        for side in (1, 2):
            self.assertEqual(forms[1][side].replace(b'\r\n', b'\n'), forms[0][side])
            self.assertEqual(forms[2][side] + b'\n', forms[0][side])


class Ownership(unittest.TestCase):
    def test_branch_predicate_receipt_uses_observed_f32_values(self):
        branches = load('sen_test_branch_predicates','galezie-sen.py')
        text = ledger.stream(m,f,contract_sample())
        records = [(t,v) for t,v in map(m.parse,text.splitlines(keepends=True)) if v[:2] == (1,4)]
        changed = []
        for tag,value in records:
            words = list(value)
            if tag == 'BS11': words[4:6] = [f.bits(.25),f.bits(.5)]
            if tag == 'SM11': words[23] = f.bits(2)                       
            if tag == 'CX10': words[4] = f.bits(8)                     
            if tag == 'BV10': words[6:13] = [f.bits(.125),0,f.bits(-.0625),f.bits(.0625),0,f.bits(1),0]
            changed.append((tag,tuple(words)))
        receipt = branches.trace_predicates(changed)
        self.assertEqual(len(receipt),1)
        self.assertEqual(receipt[0]['H']['sleepVelocity'],'3e800000')
        self.assertTrue(receipt[0]['sleepVelocity_eq_threshold'])
        self.assertTrue(receipt[0]['sleepTime_eq_half'])
        self.assertFalse(receipt[0]['sleepTime_lt_half'])
        self.assertTrue(receipt[0]['world_enableSleep'])
    def test_historical_contact_events_copies_and_touching_values(self):
        rows, verifier = ledger.contact_public_rows(m, f, contract_sample())
        verifier.public_values(rows, True)
        def field(tag, row, position, value):
            def change(rr):
                words = list(rr[tag][row]); words[position] = value; rr[tag][row] = tuple(words)
            return change
        changes = (
            ('CD-cached-manifold', field('CD', 1, -1, 1)),
            ('GE-emission-manifold', field('GE', 1, -1, 1)),
            ('GC-owned-manifold', field('GC', 1, -1, 1)),
            ('GC-missing-copy', lambda rr: rr.__setitem__('GC', [])),
            ('GC-duplicate-copy-item', lambda rr: rr['GC'].append(rr['GC'][1])),
            ('GC-old-number-after-reuse', field('GC', 1, 7, 99)),
            ('GE-high-ticket', field('GE', 1, 8, 1)),
            ('GE-hit-count', field('GE', 0, 9, 1)),
        )
        for name, change in changes:
            for side in ('C OBS1', 'Duckling'):
                bad = copy.deepcopy(rows); change(bad)
                with self.subTest(name=name, side=side), self.assertRaises(ValueError): verifier.public_values(bad, True)
                                                                           
                                                                            
        for side in ('C OBS1', 'Duckling'):
            bad, verifier = ledger.contact_public_rows(m, f, contract_sample())
            verifier.known_shapes.add((0,99,0,1,0))
            for tag in ('GE','GC'):
                words = list(bad[tag][1]); words[7] = 99; bad[tag][1] = tuple(words)
            with self.subTest(name='late-lookup-after-reuse', side=side), self.assertRaises(ValueError): verifier.public_values(bad, True)

    def test_sleeping_contacts_missing_duplicate_defined_and_pool(self):
        rows, maps, types = ledger.sleeping_contact_rows(m, f, contract_sample())
        m.OwnershipModel().contacts_and_lists(rows, maps, types)
        def payload(tag, position, value):
            def change(rr):
                entry = list(rr[tag][0]); entry[position] = value; rr[tag][0] = tuple(entry)
            return change
        changes = (
            ('sleeping-CS-missing', lambda rr: rr.__setitem__('CS', [])),
            ('sleeping-CS-duplicate', lambda rr: rr['CS'].append(rr['CS'][0])),
            ('rolling-defined-bit-lost', payload('CS', -1, 0)),
            ('sleeping-CS-wrong-local', payload('CS', 5, 1)),
            ('contact-pool-omitted', lambda rr: rr.__setitem__('CP', [])),
            ('contact-island-wrong-owner', payload('CT', 17, 1)),
            ('body-edge-cycle', payload('CT', 13, 0)),
            ('island-parent-cycle', payload('IS', 17, 0)),
        )
        for name, change in changes:
            for side in ('C OBS1', 'Duckling'):
                bad = copy.deepcopy(rows); change(bad)
                with self.subTest(name=name, side=side), self.assertRaises(ValueError):
                    m.OwnershipModel().contacts_and_lists(bad, maps, types)

    def test_pure_transfer_preserves_cache_material_sim_and_impulses(self):
        rows, _, _ = ledger.sleeping_contact_rows(m, f, contract_sample())
        rows['E'] = [(1, 2, *f.op(58, 0, 0, 1, 1))]
        verifier = m.OwnershipModel(); verifier.prior_rows = rows
        verifier.transfer_values(copy.deepcopy(rows))
        fields = (('BodySim-transform', 'SM11', 5), ('normal-impulse', 'CS', 38),
                  ('rolling-impulse', 'CS', 29), ('cache', 'CS', 20),
                  ('material', 'CS', 15), ('rolling-defined', 'CS', 57),
                  ('contact-birth-high', 'CT', 23))
        for name, tag, field in fields:
            for side in ('C OBS1', 'Duckling'):
                bad = copy.deepcopy(rows); value = list(bad[tag][0]); value[field] ^= 1; bad[tag][0] = tuple(value)
                with self.subTest(name=name, side=side), self.assertRaises(ValueError): verifier.transfer_values(bad)

    def test_public_projection_leaks_and_signed_zero(self):
        sample = contract_sample()
        public = ''.join(line for line in sample.splitlines(keepends=True) if m.parse(line)[0] not in m.ALL_PRIVATE)
        m.validate_stream(public, sample_cases(sample), private=False)
                                                                            
                                                                             
        for side in ('C OBS0', 'second identical public output'):
            with self.subTest(side=side), self.assertRaises(ValueError):
                m.validate_stream(sample, sample_cases(sample), private=False)
        zero = sample.replace('3d4ccccd', '80000000')
        m.validate_stream(zero, sample_cases(zero))
        wrong = '\n'.join(line.replace('80000000', '00000000') if line.startswith('GS11 ') else line for line in zero.split('\n'))
        for side in ('C OBS1', 'Duckling'):
            with self.subTest(side=side), self.assertRaises(ValueError): m.validate_stream(wrong, sample_cases(zero))

    def test_missing_duplicate_reordered_snapshot_and_group(self):
        sample = contract_sample(); cases = sample_cases(sample)
        lo = sample.index('E 1 1 '); mid = sample.index('E 1 2 '); end = sample.index('ENDCASE ')
        prefix, one, two, suffix = sample[:lo], sample[lo:mid], sample[mid:end], sample[end:]
        lines = one.splitlines(keepends=True); ri = next(j for j, line in enumerate(lines) if line.startswith('R '))
        reordered = list(lines); reordered[ri], reordered[ri+1] = reordered[ri+1], reordered[ri]
        changes = (('missing-step', prefix + two + suffix), ('duplicate-step', prefix + one + one + two + suffix),
                   ('reordered-step', prefix + two + one + suffix),
                   ('reordered-tag-group', prefix + ''.join(reordered) + two + suffix))
        for name, text in changes:
            for side in ('C OBS1', 'Duckling'):
                with self.subTest(name=name, side=side), self.assertRaises(ValueError): m.validate_stream(text, cases)
    def test_half_second_sleep_moves_survive_empty_awake_dense(self):
        sample = ledger.stream(m, f, contract_sample())
        receipt = m.validate_stream(sample, sample_cases(sample))
        self.assertEqual(receipt['snapshots'], 4)
        self.assertEqual(receipt['records']['M'], 1)
        records = [m.parse(s) for s in sample.splitlines(keepends=True)]
        self.assertEqual([v[-1] for t,v in records if t == 'M'], [1])
        self.assertFalse(any(t == 'DN' and v[1] == 4 for t,v in records))

    def test_move_count_fell_asleep_copies_and_lifo_corruptions(self):
        sample = ledger.stream(m, f, contract_sample()); cases = sample_cases(sample)
        def change(tag, seq, field, value, delete=False, duplicate=False):
            def mutate(text):
                result = []
                for line in text.splitlines(keepends=True):
                    t, v = m.parse(line)
                    if t == tag and v[:2] == (1, seq):
                        if delete: continue
                        words = list(v); words[field] = value
                        line = m.format_record(t, words)
                        if duplicate: result.append(line)
                    result.append(line)
                return ''.join(result)
            return mutate
        changes = (
            ('M-after-sleep-count', change('K', 4, 7, 0)),
            ('M-missing-finalized-body', change('M', 4, -1, 0, delete=True)),
            ('fellAsleep', change('M', 4, -1, 0)),
            ('bodyMoveIndex', change('BS11', 4, 8, 0)),
            ('MC-own-copy', change('MC', 4, -1, 0)),
            ('MC-high-ticket', change('MC', 4, 6, 1)),
            ('M-wrong-raw-number', change('M', 4, 4, 2)),
            ('LIFO-free-array', change('SF11', 3, 4, 2)),
            ('candidate-phase0', change('WS11', 4, 6, 0)),
            ('island-local-activity-bit', change('AB11', 4, 6, 1)),
            ('timer-whole-step', change('BS11', 4, 5, f.bits(.125))),
            ('positive-step-count', change('Z11', 4, -1, 0)),
        )
        for name, mutate in changes:
            corrupt = mutate(sample)
            for side in ('C OBS1', 'Duckling'):
                with self.subTest(name=name, side=side), self.assertRaises(ValueError):
                    m.validate_stream(corrupt, cases)
    def test_normative_complete_sleeping_singleton_stream(self):
        sample = contract_sample()
        receipt = m.validate_stream(sample, sample_cases(sample))
        self.assertEqual(receipt['snapshots'], 2)
        self.assertTrue(receipt['models_checked'])

    def test_allocator_lifo_and_free_order(self):
        m.allocator_transition((4, (1, 3)), (4, (1, 2)), [('alloc', 3)], [('free', 2)], 'test')
        for after, alloc in (((4, (3, 2)), 1), ((4, (1, 2)), 1), ((4, (2, 1)), 3)):
            with self.subTest(after=after, alloc=alloc), self.assertRaises(ValueError):
                m.allocator_transition((4, (1, 3)), after, [('alloc', alloc)], [('free', 2)], 'test')
                                                                             
                                                                      
        with self.assertRaisesRegex(ValueError,'sparse count before expansion'):
            m.pool((0xffffffff,0,0xffffffff),(),{},'huge corrupted pool')

    def test_dfs_seed_order_lifo_static_and_kinematic(self):
                                                                           
                                                                            
        types = {0: 0, 1: 2, 2: 2, 3: 1, 4: 2, 5: 2}
        edges = {1: [(10, 2, True), (11, 3, True), (12, 0, True)],
                 2: [(10, 1, True), (13, 3, True)],
                 3: [(11, 1, True), (13, 2, True), (14, 4, False)],
                 4: [(15, 0, True), (14, 3, False)], 5: []}
        self.assertEqual(m.dfs_plan((1, 2, 3, 4, 5), edges, types),
                         (((1, 3, 2), (10, 11, 12, 13)), ((4,), (15,)), ((5,), ())))
        self.assertEqual(m.dfs_plan((5, 4, 3, 2, 1), edges, types)[0], ((5,), ()))
        with self.assertRaises(ValueError): m.dfs_plan((1, 2), edges, types)

    def test_binary32_velocity_each_component(self):
                                                                            
                                                                     
        self.assertEqual(m.bits(m.sleep_velocity((.125, 0), 0, 2, (0, 0), 0, 8)), f.bits(.125))
        self.assertEqual(m.bits(m.sleep_velocity((0, 0), -.125, 2, (0, 0), 0, 8)), f.bits(.25))
        self.assertEqual(m.bits(m.sleep_velocity((0, 0), 0, 2, (.125, 0), 0, 8)), f.bits(.5))
        self.assertEqual(m.bits(m.sleep_velocity((0, 0), 0, 2, (0, 0), -.125, 8)), f.bits(1))

    def test_model_checks_each_side_even_identically_corrupt(self):
        sample = contract_sample(); cases = sample_cases(sample)
        def swap_sleep_flags(text):
            result = []
            for line in text.splitlines(keepends=True):
                tag, value = m.parse(line)
                if tag == 'GS11' and value[:2] == (1,2):
                    line = m.format_record(tag, (*value[:9], 1, 0, *value[11:]))
                result.append(line)
            return ''.join(result)
        changes = (
            ('missing-set', lambda s: '\n'.join(l for l in s.split('\n') if not l.startswith('SS11 1 2 0 3 '))),
            ('wrong-set', lambda s: s.replace('SS11 1 2 0 3 00000001 00000003', 'SS11 1 2 0 3 00000001 00000002')),
            ('state-sleeping', lambda s: s.replace('SS11 1 2 0 3 00000001 00000003 00000001 00000000', 'SS11 1 2 0 3 00000001 00000003 00000001 00000001')),
            ('wrong-local', lambda s: s.replace('SD11 1 2 0 3 0 00000000', 'SD11 1 2 0 3 1 00000000')),
            ('duplicate-sim', lambda s: s.replace('SD11 1 2 0 3 0 00000000\n', 'SD11 1 2 0 3 0 00000000\n' * 2)),
            ('missing-sim', lambda s: '\n'.join(l for l in s.split('\n') if not l.startswith('SM11 1 2 '))),
            ('missing-dense', lambda s: '\n'.join(l for l in s.split('\n') if not l.startswith('SD11 1 2 '))),
            ('missing-pool', lambda s: '\n'.join(l for l in s.split('\n') if not l.startswith('BP11 1 2 '))),
            ('bad-positive-count', lambda s: s.replace('Z11 1 2 00000001 00000001 00000000', 'Z11 1 2 00000001 00000001 00000001')),
            ('wrong-high-ticket', lambda s: s.replace('GS11 1 2 0 00000000 00000000 00000002 00000000', 'GS11 1 2 0 00000000 00000000 00000002 00000001')),
            ('GS-awake-sleeping-swapped', swap_sleep_flags),
            ('missing-phase1', lambda s: s.replace('WS11 1 2 0 1 ', 'WS11 1 2 0 0 ')),
            ('noncanonical-H', lambda s: s.replace('3d4ccccd', '3D4CCCCD')),
            ('noncanonical-D', lambda s: s.replace('CASE 1 2', 'CASE 01 2')),
            ('wrong-echo', lambda s: s.replace('E 1 2 57 ', 'E 1 2 58 ')),
            ('truncated-end', lambda s: s[:-6]),
            ('extra-output', lambda s: s + '\n'),
        )
        for name, mutate in changes:
            corrupt = mutate(sample); self.assertNotEqual(corrupt, sample, name)
            for side in ('C OBS1', 'Duckling'):
                with self.subTest(name=name, side=side), self.assertRaises((ValueError, UnicodeError)):
                    m.validate_stream(corrupt, cases)

    def test_native_process_evidence_cannot_be_skip_success(self):
        sample = contract_sample(); cases = sample_cases(sample)
        for kw in ({'code': 1}, {'code': -11}, {'stderr': b'runtime\n'}, {'build_code': 1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                m.validate_stream(sample, cases, **kw)


if __name__ == '__main__': unittest.main()
