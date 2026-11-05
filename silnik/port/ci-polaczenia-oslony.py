pass                                                              

                                                                         
                                                                            

                                                                             
                                                                                 
                                                                               
                                                                             
                                                                            

                                                                              
                                                                           
                                                                        
                                                                             
                                                                          
                                                                             
                                                                           
                                                                               
                                                                            
                                                                          
                                                                           
                                                                              
                                                                 
                                                                           
                                                                             
                                                                               
                                                                             
                                                                     
                                                                          
                                                                               
                                                                       
   
from collections import Counter
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


m = load('polaczenia_stage_m', 'model-polaczenia.py')
d = load('polaczenia_stage_d', 'polaczenia-oslony-dane.py')
b = load('polaczenia_stage_b', 'galezie-polaczenia.py')
n = load('polaczenia_stage_n', 'polaczenia-ujemne.py')


def field(ctx, name, default=None):
    return ctx.get(name, default) if isinstance(ctx, dict) else getattr(ctx, name, default)


def _path(path):
    path = Path(path).resolve()
    m.require(path.is_relative_to(ROOT.resolve()), '14a evidence path outside this tree')
    return path


def selftest():
                                                                            
    results = []
    for pattern in ('test_polaczenia_model.py', 'test_polaczenia_dane.py', 'test_polaczenia_stage.py', 'test_polaczenia_integracja.py',
                    'test_polaczenia_w2_ci.py', 'test_polaczenia_w2_model.py', 'test_polaczenia_w2_swiadki.py',
                    'test_polaczenia_w2_base13.py'):
        suite = unittest.defaultTestLoader.discover(str(HERE), pattern=pattern)
        text = io.StringIO(); run = unittest.TextTestRunner(stream=text, verbosity=2).run(suite)
        results.append({'file': pattern, 'run': run.testsRun, 'failures': len(run.failures),
            'errors': len(run.errors), 'skips': len(run.skipped),
            'ok': bool(run.testsRun) and run.wasSuccessful() and not run.skipped, 'log': text.getvalue()})
    return results


def _runtime_ok(r):
    return (r.get('native_product') is True and r.get('build_code') == 0 and r.get('code') == 0 and
            r.get('stderr') == b'' and not r.get('timeout') and bool(r.get('source_sha256')))


def check_guard_result(item, receipt, *, side, observer, validate, input_bytes):
    pass                                                                           
    m.require(_runtime_ok(receipt), 'guard native build/process/stderr/provenance')
    output = _path(receipt['stdout_path'])
    model = validate(side, output, input_bytes, observer, item['key'])
    m.require(all(model.get(key) is True for key in ('complete','base_grammar','base_model',
              'joint_model','full_model_ready','full_ownership_ready')) and model.get('unresolved') == [],
              'guard complete BASE13+14 model including history/ownership, no unresolved obligation')
    statuses = []; helpers = []; callbacks = 0
    with output.open('rb') as stream:
        for raw in stream:
            tag, values = m.parse(raw)
            if tag in ('PORT14', 'END'): continue
            if values[0] != item.get('localId', 1): continue
            if tag == 'A14': statuses.append((values[1], values[2:4]))
            if tag == 'J14' and values[5] == 11:
                m.require(values[2:6] == (0, 16, item['kind'], 11), 'helper actual kind/source/world')
                helpers.append(values[7:])
            if tag == 'HT12' and values[4] == 1: callbacks += 1
    expected = item['expected_status'], item['expected_reason']
    target_seq = (len(item['ops']) + 1 if item['ops'] else 0) if item['kind'] else len(item['ops'])
    m.require([status for seq, status in statuses if seq == target_seq] == [expected], 'guard expected status/reason at actual target sequence')
    if item['kind']:
        m.require(len(helpers) == 1, 'one real helper result')
        m.require(helpers[0][:2] == (expected[0], int(expected[0] == 0)), 'helper status/accepted')
    if item['kind'] == 5: m.require(callbacks > 0 and (7, 1) in [v for seq, v in statuses if seq == len(item['ops'])], 'real preSolve callback provenance')
    return {'ok': True, 'status': expected[0], 'reason': expected[1], 'helper': helpers,
            'callbacks': callbacks, 'model': model, 'native_product': True}


def guards_stage(ctx, items):
    run, validate = field(ctx, 'POLACZENIA_RUN'), field(ctx, 'POLACZENIA_VALIDATE')
    result = [{'key': item['key'], 'id': item['id'], 'sourceId': item['sourceId'],
               'sourceKey': item['sourceKey'], 'localId': local, 'route': item['source']['route'],
               'ok': False, 'state': 'unexecuted', 'sides': {}}
              for local, item in enumerate(items, 1)]
    for side, decimal, observer in (('c0', False, False), ('c1', False, True), ('d', True, True)):
        data = d.encode_guard(items, decimal=decimal)
        if not callable(run) or not callable(validate):
            for row in result: row['sides'][side] = {'state': 'missing', 'why': 'Native runner or complete model adapter not supplied'}
            continue
        try:
            receipt = run(side, data, observer, 'GUARD156')
            m.require(_runtime_ok(receipt), 'guard full batch native build/process/stderr/provenance')
            model = validate(side, _path(receipt['stdout_path']), data, observer, 'GUARD156')
            for item, row in zip(items, result):
                row['sides'][side] = check_guard_result(item, receipt, side=side, observer=observer,
                    validate=lambda *args: model, input_bytes=data)
        except Exception as exc:
            for row in result: row['sides'][side] = {'ok': False, 'state': 'failed', 'error': str(exc)}
    for row in result:
        row['ok'] = all(v.get('ok') for v in row['sides'].values())
        row['state'] = 'passed' if row['ok'] else 'unexecuted' if not callable(run) else 'failed'
    return result


def _fatal_observation(receipt, item):
    m.require(receipt.get('native_product') is True and receipt.get('build_code') == 0 and receipt.get('source_sha256'), 'fatal native provenance/build')
    m.require(receipt.get('code') == 2 and receipt.get('stderr') == item['stderr'], 'fatal exact exit2/stderr/LF')
    require_prefix = item['prefix_operations']
    forbidden = ('E14', 'A14', 'J14', 'L14', 'T14')
    emitted = 0; framing_after_bad = False
    with _path(receipt['stdout_path']).open('rb') as stream:
        for raw in stream:
            tag, v = m.parse(raw)
            if tag == 'E14': emitted += 1
            if tag == 'END': framing_after_bad = True
            if tag in forbidden: m.require(emitted <= require_prefix, 'fatal emitted bad O or later snapshot')
    m.require(emitted == require_prefix and not framing_after_bad, 'fatal legal prefix / no END')
                                                                              
                                                                              
                                                        
    m.require(receipt.get('prefix_bytes_compared') is True and receipt.get('prefix_equal') is True, 'fatal exact legal prefix bytes not checked')
    return {'ok': True, 'emitted_O': emitted, 'code': 2, 'stderr': item['stderr'].decode('ascii')}


def parsers_stage(ctx):
    run = field(ctx, 'POLACZENIA_RUN')
    run_parser = field(ctx, 'POLACZENIA_RUN_PARSER')
    c_cases = n.cases(False); d_cases = n.cases(True)
    m.require([r['key'] for r in c_cases] == [r['key'] for r in d_cases], 'same parser corpus C/D')
    result = []
    for c, duck in zip(c_cases, d_cases):
        row = {'key': c['key'], 'reason': c['reason'], 'variant': c['variant'], 'sides': {}, 'ok': False}
        for side, item in (('c1', c), ('d', duck)):
            if not callable(run) and not callable(run_parser): row['sides'][side] = {'state': 'missing'}; continue
            try:
                receipt = run_parser(side, item, True) if callable(run_parser) else run(side, item['input'], True, item['key'])
                row['sides'][side] = _fatal_observation(receipt, item)
            except Exception as exc: row['sides'][side] = {'ok': False, 'error': str(exc)}
        row['ok'] = all(v.get('ok') for v in row['sides'].values()); result.append(row)
    proof = n.inherited_cache()
    if proof is not None:
        result.append({'key': 'PORT13A/initial/cache-u8', 'reason': 'INPUT_CACHE',
            'evidence_kind': 'inherited-PORT13A', 'full_acceptance': False, 'ok': True,
            'proof': {'path': n.CACHE_PATH, 'receipt_sha256': n.CACHE_SHA},
            'sides': proof['observation']['sides']})
    return result


def stage(ctx=None, *, part=None, profile=None, inputs=None, binaries=None, out=None):
    pass                                                                    

                                                                              
                                                                             
                                                                               
                                                                       
                                                                           
                                                                            
       
    started = time.monotonic()
    part = field(ctx, 'part', 'A') if part is None else part
    profile = field(ctx, 'profile', 'ALL') if profile is None else profile
    selected = str(profile).upper()
    m.require(part == 'A' and selected in ('ALL', 'GUARD', 'PARSER', 'MUTATIONS', 'PUBLIC', 'DIRECT'), 'PORT14A stage part/profile')
                                                                               
    if ctx is None: ctx = {}
    if inputs is None: inputs = field(ctx, 'POLACZENIA_INPUTS')
    if binaries is None: binaries = field(ctx, 'POLACZENIA_BINARIES')
    out = _path(out if out is not None else field(ctx, 'POLACZENIA_OUT', ROOT / 'RESULT-PORT14/lokalny_1/14a/oslony'))
    out.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {'code': 1, 'full_acceptance': False, 'stages': {}, 'errors': [],
              'full_ownership_ready': False, 'native_product_mutants': 0,
              'full_model_ready': m.Model14A.full_model_ready,
              'scope': '14a guard stages; BASE1-13 regression is a separate required check',
              'selection': {'part': part, 'profile': selected, 'inputs_supplied': inputs is not None, 'binaries_supplied': binaries is not None}}
    checks = selftest()
    for r in checks: (out / (r['file'] + '.csv')).write_text(r.pop('log'), encoding='utf-8')
    result['stages']['selftests'] = checks
    if not checks or not all(r['ok'] and r.get('run', 0) > 0 and not any(r.get(k, 0) for k in ('failures', 'errors', 'skips')) for r in checks):
        result['errors'].append('14a selftests missing/red/skipped')
    if selected == 'ALL' and not m.Model14A.full_model_ready:
        result['errors'].append('full BASE13/history model14 is incomplete; partial model/equal words cannot give full acceptance')
                                                            
    items = None
    if selected in ('ALL', 'GUARD'):
        try:
            items = inputs.get('guards') if isinstance(inputs, dict) and 'guards' in inputs else d.guards()
            m.require([r['key'] for r in items] == [r['key'] for r in d.guards()], 'full156 guard keys/order')
            batch_sha = {side: hashlib.sha256(d.encode_guard(items, decimal=decimal)).hexdigest() for side, decimal in (('C',False),('D',True))}
            save('guard-inputs.json', [{'id': r['id'], 'sourceId': r['sourceId'], 'sourceKey': r['sourceKey'], 'localId': r['localId'], 'key': r['key'], 'kind': r['kind'], 'ga': r['ga'],
                'ops': r['ops'], 'expected_status': r['expected_status'], 'expected_reason': r['expected_reason'],
                'inputSHA_C': batch_sha['C'],
                'inputSHA_D': batch_sha['D']} for r in items])
        except Exception as exc: result['errors'].append('guard materialization: ' + str(exc))
    tasks = []
    if selected in ('ALL', 'GUARD') and items is not None: tasks.append(('guards', lambda: guards_stage(ctx, items)))
    if selected in ('ALL', 'PARSER'): tasks.append(('parsers', lambda: parsers_stage(ctx)))
    for name, fn in tasks:
        try:
            rows = fn(); save(name + '.json', rows)
            result['stages'][name] = {'required': len(rows), 'passed': sum(r['ok'] for r in rows)}
            if not all(r['ok'] for r in rows): result['errors'].append(name + ' native evidence missing/red')
        except Exception as exc: result['errors'].append(name + ': ' + str(exc))
    if selected in ('ALL', 'PARSER'):
        try:
            gaps = n.route_gaps(); save('parser-route-gaps.json', gaps)
            unresolved = [r for r in gaps if r['state'] not in ('unavailable', 'inherited') or not r.get('proof')]
            result['parser_routes'] = {'unresolved_variants': len(unresolved), 'unresolved_classes': len({r['reason'] for r in unresolved}),
                                       'unavailable_with_proof': sum(r['state'] == 'unavailable' and bool(r.get('proof')) for r in gaps),
                                       'inherited_with_proof': sum(r['state'] == 'inherited' and bool(r.get('proof')) for r in gaps)}
            if unresolved: result['errors'].append('parser route catalogue has ' + str(len(unresolved)) + ' unresolved variants')
        except Exception as exc: result['errors'].append('parser routes: ' + str(exc))
    if selected in ('ALL', 'MUTATIONS'):
        try:
            ledger = field(ctx, 'POLACZENIA_LEDGER')
            if ledger is None:
                ledger_path = HERE / 'polaczenia-macierz.json'
                ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else b.obligations()
            source_inventory = field(ctx, 'POLACZENIA_SOURCE_CANDIDATES')
            if source_inventory is not None: ledger = {**ledger, 'source_candidates': source_inventory}
            elif not ledger.get('source_candidates'): result['errors'].append('source candidate inventory/classification not supplied')
            settled = b.settle(ledger, field(ctx, 'POLACZENIA_MUTATION_RECEIPTS', [])); save('macierz.json', settled)
            result['stages']['mutations'] = settled['counts']
            result['native_product_mutants'] = settled['counts'].get('killed', 0)
            if not settled['full_acceptance']: result['errors'].append('native atom/candidate/aggregate ledger incomplete')
        except Exception as exc: result['errors'].append('mutation ledger: ' + str(exc))
    requirements = ('PUBLIC96', 'DIRECT128', 'OBS', 'scene_witnesses', 'final_clean_integration') if selected == 'ALL' else ('PUBLIC96',) if selected == 'PUBLIC' else ('DIRECT128',) if selected == 'DIRECT' else ()
    for name in requirements:
        evidence = field(ctx, 'POLACZENIA_' + name)
        result['stages'][name] = evidence or {'ok': False, 'state': 'missing'}
        if not evidence or not evidence.get('ok'): result['errors'].append(name + ' missing/red')
                                                                             
    result['inherited_debt'] = 'BASE12 full_ownership_ready=False; required by14a'
    result['seconds'] = time.monotonic() - started
    result['code'] = int(bool(result['errors']))
    result['full_acceptance'] = selected == 'ALL' and result['code'] == 0
    save('manifest.json', result)
    return result['code']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--part', choices=('A',), default='A')
    parser.add_argument('--profile', choices=('ALL', 'GUARD', 'PARSER', 'MUTATIONS', 'PUBLIC', 'DIRECT'), default='ALL')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    sys.exit(stage(part=args.part, profile=args.profile, out=args.out))
