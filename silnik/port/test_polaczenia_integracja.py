pass                                                                           

                                                                           
                                                                            
   
from collections import Counter
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


ci = load('test14_integration_ci', 'ci-polaczenia-oslony.py')
fixture = load('test14_integration_fixture', 'test_polaczenia_model.py')
m = ci.m
NUMBER = (1, 0, 1, 0, 4, 0, 1, 0)


def prepared_model():
    model = m.Model14A(observer=True); model.case = 1; model.numbers[0] = NUMBER
    return model


def summary(records):
    pass                                                                    
    counts = Counter(v[5] for t, v in records if t == 'J14')
    lists = Counter(v[4] for t, v in records if t == 'L14')
    for i, (t, v) in enumerate(records):
        if t == 'J14' and v[5] == 8:
            h = list(v[7:]); h[:8] = [counts[g] for g in range(8)]; h[8:13] = [lists[g] for g in range(5)]
            h[18] = len({p[2] for tag, p in records if tag in ('J14', 'L14') and p[2] in range(1, 5)})
            records[i] = t, (*v[:7], *h)
    return records


def view_records():
    operation = {'opcode': 207, 'a': (0, 0, 0)}
    records = [(t, v) for t, v in fixture.snapshot() if not (t == 'J14' and v[5] == 4)]
    records[0] = 'E14', (1, 1, 207, 3, 0, 0, 0)
    index = next(i for i, (t, v) in enumerate(records) if t == 'J14' and v[5] == 8)
    records[index:index] = [fixture.joint(0, NUMBER, world=16, source=1), fixture.joint(4, (0,) * 50, world=16, source=1)]
    return operation, summary(records)


def base_counter_fixture(extra=()):
    pass                                                                     
    old = m.base.base12_13b()
    rows = [('E14', (1, 1, 200, 2, 0, 0)), *extra]
    counts = Counter(t for t, v in rows); counts['E'] = 1
    z8 = [1, 1, *([0] * 26)]; z8[8:26] = [counts[t] for t in old.p11.p10.p9.p8.PUBLIC_COUNTS]
    z9 = [1, 1, *([0] * 13)]; z9[5:12] = [counts[t] for t in old.p11.p10.p9.PUBCOUNTS]; z9[12:15] = (1, 1, 14)
    names = ('AP12', 'WS12', 'NM12', 'UD12', 'HC12', 'HR12', 'HT12', 'CL12', 'CV12', 'VR12', 'EF12')
    z13 = [counts['A13'], *([counts[t] for t in 'CN13 CQ13 QL13 CS13 PC13 COPY13 CV13 CE13 ENDCOPY13'.split()]), counts['CN13'], counts['CH13'], 0, 1, counts['EP13B'], counts['EU13B'], counts['V13'], counts['E14']]
    rows += [('Z8', tuple(z8)), ('Z9', tuple(z9)),
             ('Z10', (1, 1, *[counts[t] for t in old.p11.p10.HIT_COUNTS], 0)),
             ('Z11', (1, 1, counts['SW11'], counts['GS11'], 0)),
             ('I12', (1, 1, *[counts[t] for t in names])), ('Z12', (1, 1, 0, 1)),
             ('I8', (1, 1, *[counts[t] for t in old.p11.I8_TAGS])),
             ('I9', (1, 1, *[counts[t] for t in old.p11.p10.p9.PRIVCOUNTS])),
             ('I10', (1, 1, *[counts[t] for t in old.p11.p10.NEW_COUNTS])),
             ('I11', (1, 1, *[counts[t] for t in old.p11.NEW_PRIVATE])),
             ('IP12', (1, 1, counts['NP12'])),
             ('I13', (1, 1, *[counts[t] for t in ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13')])),
             ('Z13', (1, 1, *z13))]
    return rows


class IntegrationControls(unittest.TestCase):
    def test_incomplete_model_blocks_full_acceptance_even_if_adapters_claim_green(self):
        ctx = {('POLACZENIA_' + name): {'ok': True} for name in ('PUBLIC96', 'DIRECT128', 'OBS', 'scene_witnesses', 'final_clean_integration')}
        ctx['POLACZENIA_SOURCE_CANDIDATES'] = [{'id': 'control'}]
        with tempfile.TemporaryDirectory(prefix='.14a-integration-', dir=ROOT) as tmp:
            with patch.object(ci, 'selftest', return_value=[{'file': 'control', 'run': 1, 'ok': True, 'log': ''}]), patch.object(ci, 'guards_stage', return_value=[{'ok': True}]), patch.object(ci, 'parsers_stage', return_value=[{'ok': True}]), patch.object(ci.n, 'route_gaps', return_value=[]), patch.object(ci.b, 'settle', return_value={'counts': {'killed': 1}, 'full_acceptance': True}):
                self.assertEqual(ci.stage(ctx, out=tmp), 1)
            result = json.loads((Path(tmp) / 'manifest.json').read_text(encoding='utf-8'))
            self.assertFalse(result['full_acceptance']); self.assertFalse(result['full_model_ready'])
            self.assertTrue(any('model14 is incomplete' in e for e in result['errors']))

    def test_F_number_uses_prior_ticket_history_including_carry(self):
        world = [1, 1, 0, 1, *([0] * 12)]; world[8] = 1
        self.assertEqual(m.direct_fixture_number(0, world), (1, 0, 1, 0, 4, 0, 1, 0))
        world[8:10] = (0, 1)
        self.assertEqual(m.direct_fixture_number(0xffffffff, world), (1, 0, 1, 0, 3, 1, 0, 1))
        with self.assertRaises(ValueError): m.direct_fixture_number(0, world)
        with self.assertRaises(ValueError): m.direct_fixture_number(0xffffffffffffffff - 3, world)

    def test_bad_guard_header_prefix_ends_before_G14_echo(self):
        item = {'variant': 'GUARD', 'failure_scope': 'case', 'prefix_operations': 0}
        prefix = b'PORT14 A GUARD 1\n'
        reference = prefix + b'G14 1 0 0 1\nGA14 1 ignored\nCASE 1 1\n'
        self.assertTrue(ci.n.compare_prefix(io.BytesIO(prefix), io.BytesIO(reference), item)['prefix_equal'])
        with self.assertRaises(ValueError): ci.n.compare_prefix(io.BytesIO(reference), io.BytesIO(reference), item)

    def test_independent_BASE_counters_resolve_h0_but_keep_history_debt(self):
        result = m.check_base13_counts(base_counter_fixture(), 1, 1)
        self.assertTrue(result['base_counts_checked']); self.assertFalse(result['complete'])
        self.assertFalse(any('Z13.h0' in message for message in result['unresolved']))
        self.assertTrue(any('history/ownership' in message for message in result['unresolved']))

    def test_identical_EF12_omission_with_repaired_counters_is_rejected(self):
                                                                         
        data = base_counter_fixture([('S', (1, 1, 0)), ('G', (1, 1, 0)), ('UD12', (1, 1, 2, 0))])
        for side in ('C', 'D'):
            with self.subTest(side=side), self.assertRaisesRegex(ValueError, 'EF12 every live'):
                m.check_base13_counts(data, 1, 1)

    def test_BASE13_counters_h1_through_h16_remain_independent(self):
        for field in range(1, 17):
            data = base_counter_fixture(); tag, value = data[-1]; value = list(value); value[2 + field] += 1; data[-1] = tag, tuple(value)
            with self.subTest(field=field), self.assertRaises(ValueError): m.check_base13_counts(data, 1, 1)

    def test_model_import_and_BASE13_parse_from_root_without_previous_tests(self):
        program = "import importlib.util,sys;from pathlib import Path;p=Path('silnik/port/model-polaczenia.py');s=importlib.util.spec_from_file_location('isolated14',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);print(m.parse('END 1\\n'))"
        result = subprocess.run([sys.executable, '-B', '-c', program], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "('END', (1,))")

    def test_direct_boundaries_never_reload_F_without_own_previous_state(self):
        fixtures = ci.n.fixtures()
        operations = [ci.d.op(210, 0, 0, 0), ci.d.op(210, 0, 1, 0), ci.d.op(210, 0, 2, 1)]
        result = ci.b.direct_boundaries(65, 'D065', fixtures, operations)
        self.assertEqual([r['state'] for r in result], ['input-calculated', 'unexecuted', 'unexecuted'])
        self.assertEqual(result[0]['active_predicates'], ['normalizeZero', 'k>0'])
        self.assertTrue(all(r['native_witness'] is False for r in result))

    def test_all_frozen_G6_words_have_GAME_API_continuation(self):
        c, duck = ci.n.semantic_domain_cases(), ci.n.semantic_domain_cases(True)
        self.assertEqual(len(c), 88)
        self.assertEqual([r['key'] for r in c], [r['key'] for r in duck])
        for r in c:
            self.assertEqual(r['expected_status'], (5, 10))
            self.assertGreater(r['continuation_seq'], r['refused_seq'])
            self.assertTrue(r['input'].startswith(b'PORT14 A PUBLIC 1\n'))

    def test_API_Model14A_named_and_positional_observer(self):
        for named in (False, True):
            model = prepared_model()
            result = model.check(1, 1, fixture.OP, fixture.snapshot(), **{'observer': True}) if named else model.check(1, 1, fixture.OP, fixture.snapshot(), True)
            self.assertTrue(result['joint_structure_checked'])
            self.assertFalse(result['base_checked']); self.assertFalse(result['full_ownership_ready'])
        with self.assertRaisesRegex(ValueError, 'conflicting observer'):
            prepared_model().check(1, 1, fixture.OP, fixture.snapshot(), observer=True, private=False)

    def test_missing_READ_view_is_rejected_after_correct_counters(self):
        data = [(t, v) for t, v in fixture.snapshot() if not (t == 'J14' and v[5] == 4)]
        with self.assertRaisesRegex(ValueError, 'READ exactly one'):
            prepared_model().check(1, 1, fixture.OP, summary(data), observer=True)

    def test_SAVE_VIEW_pins_input_history_and_rejects_restamped_owner(self):
        operation, data = view_records()
        self.assertTrue(prepared_model().check(1, 1, operation, data)['joint_structure_checked'])
        damaged = copy.deepcopy(data)
        i = next(i for i, (t, v) in enumerate(damaged) if t == 'J14' and v[2] == 1 and v[5] == 0)
        t, v = damaged[i]; p = list(v); p[13] = 999; damaged[i] = t, tuple(p)
        with self.assertRaisesRegex(ValueError, 'historical number'):
            prepared_model().check(1, 1, operation, damaged)

    def test_invented_or_omitted_copy_is_rejected(self):
        operation, data = view_records()
        i = next(i for i, (t, v) in enumerate(data) if t == 'J14' and v[5] == 8)
        data.insert(i, fixture.joint(0, NUMBER, world=16, source=2))
        with self.assertRaisesRegex(ValueError, 'only initialized own copies'):
            prepared_model().check(1, 1, operation, summary(data))

    def test_each_guard_mutation_class_has_an_open_intent_no_claimed_kill(self):
        ledger = ci.b.obligations()
        native = [r for r in ledger['atoms'] if r['id'].startswith('guard/')]
        self.assertEqual(len(native), 99)
        self.assertTrue(all(r['independent'] is None for r in native))
        self.assertEqual(sum(len(r['atom_ids']) for r in ledger['guards']), 99)
        result = ci.b.settle(ledger, [])
        self.assertEqual(result['counts'].get('killed', 0), 0)
        self.assertGreater(result['counts']['unresolved_native_intents'], 99)

    def test_receipt_for_unknown_atom_cannot_disappear(self):
        result = ci.b.settle(ci.b.obligations(), [{'id': 'invented'}])
        self.assertEqual(result['unmatched_receipt_ids'], ['invented'])
        self.assertFalse(result['full_acceptance'])

    def test_omitted_guard_class_and_unknown_aggregate_atom_are_red(self):
        ledger = ci.b.obligations(); removed = ledger['guards'].pop()
        self.assertEqual(ci.b.settle(ledger, [])['missing_guard_ids'], [removed['id']])
        ledger = ci.b.obligations(); ledger['manifest_classes'][0]['atom_ids'] = ['not-an-atom']
        with self.assertRaisesRegex(ValueError, 'unknown atom'): ci.b.settle(ledger, [])

    def test_alias_does_not_add_a_native_kill(self):
        ledger = ci.b.obligations(); a, b = ledger['atoms'][:2]
        a['alias_of'] = b['id']; a['alias_proof'] = 'same predicate; requires finalK proof'
        result = ci.b.settle(ledger, [])
        self.assertEqual(result['counts']['aliases'], 1)
        self.assertEqual(result['counts'].get('killed', 0), 0)
        self.assertFalse(result['full_acceptance'])

    def test_empty_source_inventory_never_completes_denominator(self):
        result = ci.b.settle(ci.b.obligations(), [])
        self.assertEqual(result['counts']['candidate'], 0)
        self.assertFalse(result['full_acceptance'])

    def test_materialization_failure_does_not_skip_independent_stages(self):
        with tempfile.TemporaryDirectory(prefix='.14a-integration-', dir=ROOT) as tmp:
            with patch.object(ci, 'selftest', return_value=[{'file': 'control', 'run': 1, 'ok': True, 'log': ''}]), patch.object(ci.d, 'guards', side_effect=ValueError('injected fixture failure')):
                self.assertEqual(ci.stage({'POLACZENIA_OUT': tmp}), 1)
            r = json.loads((Path(tmp) / 'manifest.json').read_text(encoding='utf-8'))
            self.assertIn('parsers', r['stages']); self.assertIn('mutations', r['stages'])
            self.assertTrue(any('injected fixture failure' in s for s in r['errors']))

    def test_explicit_profile_is_honored_and_subset_is_not_full_acceptance(self):
        with tempfile.TemporaryDirectory(prefix='.14a-integration-', dir=ROOT) as tmp:
            with patch.object(ci, 'selftest', return_value=[{'file': 'control', 'run': 1, 'ok': True, 'log': ''}]):
                self.assertEqual(ci.stage({'profile': 'GUARD', 'POLACZENIA_PUBLIC96': {'ok': True}}, profile='PUBLIC', out=tmp), 0)
            r = json.loads((Path(tmp) / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(r['selection']['profile'], 'PUBLIC')
            self.assertNotIn('guards', r['stages']); self.assertFalse(r['full_acceptance'])

    def test_zero_tests_with_success_flag_still_fail(self):
        with tempfile.TemporaryDirectory(prefix='.14a-integration-', dir=ROOT) as tmp:
            with patch.object(ci, 'selftest', return_value=[{'file': 'control', 'run': 0, 'ok': True, 'log': ''}]):
                self.assertEqual(ci.stage({'POLACZENIA_PUBLIC96': {'ok': True}}, profile='PUBLIC', out=tmp), 1)

    def test_parser_line_boundary_inputs_are_exact_and_separate(self):
        for decimal in (False, True):
            items = ci.n.cases(decimal)
            for length in (2048, 2049):
                boundary = [r for r in items if r['key'].endswith('/line' + str(length))]
                self.assertEqual(len(boundary), 4)
                self.assertTrue(all(len(r['input'].splitlines()[-1]) == length for r in boundary))

    def test_exact_prefix_rejects_extra_records_or_same_hash_claim(self):
        item = {'variant': 'PUBLIC', 'failure_scope': 'operation', 'prefix_operations': 1}
        prefix = b'PORT14 A PUBLIC 1\nCASE 1 2\nE14 1 1 200 2 00000000 00000000\nA14 1 1 0 0\n'
        reference = prefix + b'E14 1 2 204 3 00000001 00000000 00000000\nENDCASE 1\nEND 1\n'
        self.assertTrue(ci.n.compare_prefix(io.BytesIO(prefix), io.BytesIO(reference), item)['prefix_equal'])
        for bad in (prefix[:-1], prefix + b'A14 1 2 0 0\n', prefix.replace(b'0 0\n', b'5 10\n')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ci.n.compare_prefix(io.BytesIO(bad), io.BytesIO(reference), item)

    def test_header_fatal_has_zero_stdout_without_a_hash_shortcut(self):
        item = {'variant': 'PUBLIC', 'failure_scope': 'header', 'prefix_operations': 0}
        self.assertEqual(ci.n.compare_prefix(io.BytesIO(), io.BytesIO(b'any reference'), item)['prefix_bytes'], 0)
        with self.assertRaises(ValueError): ci.n.compare_prefix(io.BytesIO(b'\n'), io.BytesIO(), item)


if __name__ == '__main__': unittest.main()
