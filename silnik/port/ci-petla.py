from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                              

                                                                             
                                                                    
   
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import time
from types import SimpleNamespace

SUPPORTED_STEPS = (10,)
TRIAL_OPERATION_IDS = ('budowa-zadanie', 'budowa-artefakt', 'budowa-push',
                       'wykonanie-publish-final', 'wykonanie-artifact-final')
BUILD = ['narzedzia', 'c-solver', 'duckling-solver', 'duckling-component-solver',
         'fixtury-solver-budowa', 'c-only-solver-budowa']
EXECUTE = ['proba-solver', 'porownanie-solver', 'component-solver', 'check-solver',
           'oslony-solver', 'testy-solver', 'summary-solver', 'zapis-strumieni-solver']


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))
    return path


def load(root, filename, name):
    port = Path(root) / 'silnik/port'
    spec = importlib.util.spec_from_file_location(name, port / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(port))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def select_mode(ref, root, run, attempt, commit):
    if ref.startswith('uruchom/port-krok-'):
        suffix = ref[len('uruchom/port-krok-'):]
        if suffix != '10':
            raise ValueError('PETLA: nieobslugiwany step: ' + suffix + '; dozwolone: 10')
        mode = 'proba'
    elif ref == 'uruchom/port':
        mode = 'full'
    else:
        raise ValueError('PETLA: nieobslugiwana galaz: ' + ref)
    if not (re.fullmatch(r'[0-9]+', str(run)) and int(run) > 0 and
            re.fullmatch(r'[0-9]+', str(attempt)) and int(attempt) > 0 and
            re.fullmatch(r'[a-fA-F0-9]{40}', commit)):
        raise ValueError('PETLA: niepoprawne metadane biegu')
    if not (Path(root) / 'silnik/port/solver-swiata.dk').is_file():
        raise ValueError('PETLA: missing port kroku 10: silnik/port/solver-swiata.dk')
    return dict(mode=mode, N=10, ref=ref, run=str(run), attempt=str(attempt), commit=commit,
                result_dir=('RESULT-PORT-PROBA/' if mode == 'proba' else 'RESULT-PORT/') + str(run) + '_' + str(attempt))


def plan(selection):
    legacy = []
    if selection['mode'] == 'full':
        workflow = Path(__file__).resolve().parents[2] / '.github/workflows/port.yml'
        job = None
        by_job = {name: [] for name in ('port', 'ruch8', 'pary9a', 'kontakty9b', 'solver10')}
        for line in workflow.read_text(encoding='utf-8').splitlines():
            match = re.fullmatch(r'  ([A-Za-z0-9_-]+):', line)
            if match:
                job = match[1]
            if job not in ('port', 'ruch8', 'pary9a', 'kontakty9b', 'solver10'):
                continue
            for match in re.finditer(r'silnik/port/ci\.py ([a-z0-9-]+)|silnik/port/ci-solver-oslony\.py|unittest discover -s silnik/port', line):
                by_job[job].append(job + ':' + (match[1] or ('oslony-solver' if 'ci-solver-oslony' in match[0] else 'testy-solver')))
        legacy = [entry for entries in by_job.values() for entry in entries]
    return dict(build=BUILD.copy(), execute=EXECUTE.copy(),
                dependencies=['silnik/port/test_*.py (bez natywnych korpusow 1-9b)'], legacy=legacy)


def inventory(root, N):
    if N not in SUPPORTED_STEPS:
        raise ValueError('PETLA: nieobslugiwany step: ' + str(N) + '; dozwolone: 10')
    fixtures = load(root, 'fixtury-solver.py', 'petla_inventory_fixtures')
    inputs = load(root, 'przypadki-solver.py', 'petla_inventory_inputs')
    probe = load(root, 'proba-solver-c.py', 'petla_inventory_probe')
    mutations = json.loads((Path(root) / 'silnik/port/mutacje-solver.json').read_bytes())
    return dict(c_units=35, public_cases=len(inputs.verify()), component_cases=len(inputs.components()),
                long_steps=86400, short_steps=56, fixtures=[f.name for f in fixtures.definitions()],
                mutations=[r['name'] for r in mutations['native_mutations']],
                equivalent_proofs=len(mutations['equivalent_proofs']), c_only_profiles=[
                    dict(profile=p, original_units=35, drivers=['public', 'helper'],
                         scenes=len(probe.probe_inputs()), steps=sum(e[0]['kroki'] for e in probe.probe_inputs()),
                         flags=probe.flags(p)) for p in probe.PROFILES])


def run_batch(tasks, *, emit, deadline=None, clock=time.monotonic):
    rows = []
    for task in tasks:
        requires = task.get('requires', [])
        bases = {r['id']: r for r in rows if sum(x['id'] == r['id'] for x in rows) == 1}
        missing = next((name for name in requires if not bases.get(name, {}).get('usable')), None)
        row = dict(id=task['id'], code=1, usable=False, status='ZABLOKOWANE', reason='', detected=False)
        if deadline is not None and clock() >= deadline:
            row.update(code=124, reason='limit czasu; korpus niepelny')
        elif missing is not None:
            row['reason'] = 'missing uzywalnej bazy: ' + missing
        else:
            try:
                value = task['action']()
                if not isinstance(value, dict) or type(value.get('code')) is not int or type(value.get('usable')) is not bool:
                    raise ValueError('niepoprawny receipt action')
                row.update(value)
                row['id'] = task['id']
                row['status'] = 'OK' if row['code'] == 0 else 'BLAD'
                if 'detected' in value:
                    detected = bool(requires and value['detected'] and value['code'] == 0 and
                                    value.get('clean') is True and value.get('replayed') is True and
                                    value.get('difference') is not None)
                    row['detected'] = detected
                    if not detected and row['code'] == 0:
                        row.update(code=1, status='BLAD')
                if deadline is not None and clock() > deadline:
                    row.update(code=124, usable=False, status='BLAD', reason='limit czasu; korpus niepelny', detected=False)
            except Exception as exc:
                row.update(code=1, usable=False, status='BLAD', reason=type(exc).__name__ + ': ' + str(exc), detected=False)
        rows.append(row)
        emit(row)
    return rows


def write_build(out, selection, receipts, *, expected):
    complete = bool(expected > 0 and len(receipts) == expected and
                    len({r['id'] for r in receipts}) == expected and
                    all(r['code'] == 0 and r['status'] == 'OK' for r in receipts))
    return save(Path(out) / 'BUDOWA.json', dict(commit=selection['commit'], complete=complete,
                expected=expected, executed=sum(r['status'] != 'ZABLOKOWANE' for r in receipts), receipts=receipts))


def write_diagnosis(out, selection, stage, case, predicates, *, executed, expected, blocked, logs):
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', s) for s in (stage, case)):
        raise ValueError('PETLA: niepoprawny identyfikator diagnozy')
    value = {key: selection[key] for key in ('run', 'attempt', 'commit', 'mode', 'N')}
    predicates = [dict(p) for p in predicates]
    value.update(stage=stage, case=case, predicates=predicates,
                 failed=[p['name'] for p in predicates if not p['ok']],
                 executed=executed, expected=expected, blocked=blocked, logs=logs)
    while len(encoded(value)) > 65536:
        candidates = [(len(encoded(p[key])), p, key) for p in predicates for key in ('expected', 'actual')
                      if not (isinstance(p[key], dict) and p[key].get('omitted') is True)]
        if not candidates:
            raise ValueError('PETLA: limit diagnozy etapu: ' + stage)
        size, pred, key = max(candidates, key=lambda item: item[0])
        data = encoded(pred[key])
        pred[key] = dict(bytes=size, sha256=hashlib.sha256(data).hexdigest(), omitted=True)
    directory = Path(out) / 'DIAGNOZA'
    path = directory / (stage + '-' + case + '.json')
    data = encoded(value)
    if path.exists() or sum(p.stat().st_size for p in directory.glob(stage + '-*.json')) + len(data) > 1048576:
        raise ValueError('PETLA: limit diagnozy etapu: ' + stage)
    directory.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def prepare_tools(selection, *, cache_hit, verify, restore, build):
    try:
        code = (restore if cache_hit else build)()
        return code or verify()
    except Exception:
        return 1


def verify_bundle(selection, manifest, files, *, sources, tools, flags):
    expected = dict(commit=selection['commit'], run=selection['run'], attempt=selection['attempt'],
                    source_sha256=sources, tools_sha256=tools, flags=flags,
                    files={name: hashlib.sha256(data).hexdigest() for name, data in files.items()})
    return int(manifest != expected or not files)


def publish(out, selection, *, current_commit, compact, filter_payload, push):
    def call(action):
        try:
            return action()
        except Exception:
            return 1
    compact_code = call(compact)
    filtered = call(filter_payload)
    if filtered or current_commit != selection['commit']:
        return 1
    message = 'Wyniki proby kroku 10 [skip ci]' if selection['mode'] == 'proba' else 'Wyniki port [skip ci]'
    pushed = call(lambda: push(message))
    return int(bool(compact_code or pushed))


def finish(out, selection, *, required, receipts, publication, regressions, read_results=True, result_cache=None):
    result_cache = {} if result_cache is None else result_cache
    required = list(required)
                                                                         
                                                                             
    if selection['mode'] == 'proba' and ('pakiet' in required or set(required).intersection(TRIAL_OPERATION_IDS)):
        required += [name for name in TRIAL_OPERATION_IDS if name not in required]
    counts = Counter(r['id'] for r in receipts)
    good = bool(required and len(set(required)) == len(required) and all(counts[n] == 1 for n in required)
                and all(r.get('code') == 0 and r.get('status') == 'OK' for r in receipts if r['id'] in required)
                and all(publication.get(n) == 0 for n in ('compact', 'filter', 'push', 'artifact'))
                and publication.get('commit') == selection['commit'])
    missing_regressions = []
    inconsistent_regressions = []
    failed_regressions = []
    if selection['mode'] == 'full':
        metadata = {r['id']: r.get('sha256') for r in receipts if r['id'] in ('sources', 'tools')}
        good = good and counts['sources'] == counts['tools'] == 1 and bool(metadata.get('sources') and metadata.get('tools'))
        for name in ('1-7', '8', '9a', '9b'):
            row = (regressions or {}).get(name, {})
            if not row:missing_regressions.append(name)
            elif (row.get('commit'), row.get('source_sha256'), row.get('tools_sha256')) != (
                    selection['commit'], metadata.get('sources'), metadata.get('tools')):
                inconsistent_regressions.append(name)
            elif row.get('code') != 0 or row.get('outcome') != 'success':
                failed_regressions.append(name)
                if not selection.get('evidence') and selection.get('N') != 11:inconsistent_regressions.append(name)
            elif row != dict(commit=selection['commit'], source_sha256=metadata.get('sources'),
                     tools_sha256=metadata.get('tools'), code=0, outcome='success'):
                inconsistent_regressions.append(name)
            good = good and row == dict(commit=selection['commit'], source_sha256=metadata.get('sources'),
                     tools_sha256=metadata.get('tools'), code=0, outcome='success')
    trial = selection['mode'] == 'proba'
    scope = 'KROK 10 / TRIAL' if trial else 'RESULT 1…11' if selection.get('N') == 11 else 'RESULT 1…10'
    marker = Path(out) / ('KROK.json' if trial else 'RESULT.json')
                                                                            
                                                                                
    marker.unlink(missing_ok=True)
    marker.parent.mkdir(parents=True, exist_ok=True)
    journal = ''
    table = []
                                                                                 
                                                                           
                                                                                 
    summary = Path(out) / 'summary-solver-console.csv'
    if not summary.exists():summary = Path(out) / 'DZIENNIK.md'
    if summary.exists():
        table = [line for line in summary.read_text(encoding='utf-8').splitlines() if line.startswith('|')]
        if table:journal += '\nTabela obliczonego summary:\n\n' + '\n'.join(table) + '\n'
    if missing_regressions:
        journal += '\nBrak regresji: ' + ', '.join(missing_regressions) + '\n'
    if inconsistent_regressions:
        journal += '\nNiezgodne regresje: ' + ', '.join(inconsistent_regressions) + '\n'
    if failed_regressions:
        journal += '\nCzerwone regresje (uruchomione): ' + ', '.join(failed_regressions) + '\n'
    reasons = []
    detailed = selection.get('evidence') or selection.get('N') == 11
    if detailed:journal += '\nE11366eeda268 expected E0c6729e37728:\n\n| E56c87cea9aa8 | code / E1a5e497a2bfa | E44e7e3fa41e3 |\n|---|---|---|\n'
    for name in required:
        rows = [r for r in receipts if r['id'] == name]
        reason = ('missing uruchomienia / potwierdzenia' if not rows else
                  'powielone potwierdzenie' if len(rows) != 1 else
                  rows[0].get('reason', '') or ('czerwony etap' if rows[0].get('code') != 0 or rows[0].get('status') != 'OK' else ''))
        if reason:reasons.append(name + ': ' + reason)
        if detailed:journal += '| ' + name + ' | ' + (str(rows[0].get('code')) + ' / ' + str(rows[0].get('status')) if len(rows) == 1 else 'MISSING' if not rows else 'DUPLIKAT') + ' | ' + reason.replace('|', '\\|').replace('\n', ' ') + ' |\n'
    for name in ('compact', 'filter', 'push', 'artifact'):
        value = publication.get(name)
        if value != 0:reasons.append('publikacja ' + name + ': ' + str(value))
        if detailed:journal += '| publikacja ' + name + ' | ' + str(value) + ' | ' + ('OK' if value == 0 else 'missing / błąd') + ' |\n'
    if publication.get('commit') != selection['commit']:reasons.append('publikacja: inny commit')
    reasons += ['missing regresji: ' + n for n in missing_regressions]
    reasons += ['niezgodna proweniencja regresji: ' + n for n in inconsistent_regressions]
    reasons += ['czerwona regresja: ' + n + (': ' + '; '.join((regressions or {})[n].get('errors', []))
                if (regressions or {})[n].get('errors') else '') for n in failed_regressions]
    if detailed and selection['mode'] == 'full':
        for name in ('1-7', '8', '9a', '9b'):
            row = (regressions or {}).get(name, {})
            state = 'MISSING' if name in missing_regressions else 'NIEZGODNA' if name in inconsistent_regressions else 'CZERWONA' if name in failed_regressions else 'OK'
            if row.get('errors'):state += ': ' + '; '.join(row['errors']).replace('|', '\\|').replace('\n', ' ')
            journal += '| regresja ' + name + ' | ' + str(row.get('code', 'MISSING')) + ' / ' + str(row.get('outcome', 'MISSING')) + ' | ' + state + ' |\n'
        for name in ('sources', 'tools'):
            journal += '| proweniencja ' + name + ' | ' + str(metadata.get(name) or 'MISSING') + ' | ' + ('OK' if counts[name] == 1 and metadata.get(name) else 'missing / duplikat') + ' |\n'
    if selection['mode'] == 'full' and not (counts['sources'] == counts['tools'] == 1 and metadata.get('sources') and metadata.get('tools')):
        reasons.append('missing jednoznacznej proweniencji sources/tools')
    if table or any((Path(out)/name).is_file() for name in ('public10-manifest.json','component10-manifest.json')):
        journal += ('\nE5ae1f29cb35a Eb46d2b5dbabf Ee88ca20c17ea: [public10-manifest.E02bd175f3297](public10-manifest.E02bd175f3297) (PUBLIC10: expected 124), [component10-manifest.json](component10-manifest.json) (COMPONENT10: expected 96).\n')
                                                                           
                                                 
    for name in (('W1-BILETY-PUBLIC10.json', 'ujemne-solver-wynik.json', 'oslony-wynik.json') if read_results else ()):
        path = Path(out) / name
        if path not in result_cache:
            try:
                result_cache[path] = dict(value=json.loads(path.read_bytes()), failed=False) if path.exists() else None
            except (OSError, ValueError) as exc:
                result_cache[path] = dict(value=dict(file=name, error=type(exc).__name__ + ': ' + str(exc)), failed=True)
        result = result_cache[path]
        if result is None:continue
        value = result['value']
        if result['failed']:
            good = False
            reasons.append(name + ': ' + value['error'])
            if not result.get('diagnosed'):
                                                                                
                                                                              
                result['diagnosed'] = True
                case = 'json-' + name.replace('.', '-') + '-' + str(1 + len(list((Path(out) / 'DIAGNOZA').glob('przygotowanie-*.json'))))
                write_diagnosis(out, selection, 'przygotowanie', case,
                                [dict(name='odczyt-json', ok=False, expected='poprawny JSON', actual=value)],
                                executed=1, expected=1, blocked=[name + ': ' + value['error']], logs=dict(json=name))
        journal += '\n' + name + '\n```json\n' + encoded(value).decode('utf-8') + '```\n'
    code = int(not good)
    journal = scope + ': ' + ('OK' if good else 'FAIL / INCOMPLETE') + '\n' + journal
    (Path(out) / 'DZIENNIK.md').write_bytes(journal.encode('utf-8'))
    (Path(out) / ('wynik-proba-kod.csv' if trial else 'wynik-kod.csv')).write_bytes((str(code) + '\n').encode('ascii'))
    try:
        value = dict(scope=scope, commit=selection['commit'], complete=bool(good), code=code)
        if selection.get('evidence') or selection.get('N') == 11:
            value.update(
                         source_sha256=next((r.get('sha256') for r in receipts if r['id'] == 'sources'), None),
                         tools_sha256=next((r.get('sha256') for r in receipts if r['id'] == 'tools'), None),
                         required=required, receipts=receipts, publication=publication,
                         regressions=regressions, errors=reasons)
        save(marker, value)
    except Exception:
        marker.unlink(missing_ok=True)
        raise
    return code


def operation_receipts():
    variables = ('PETLA_BUILD_RESULT', 'PETLA_BUILD_ARTIFACT', 'PETLA_BUILD_PUSH',
                 'PETLA_FINAL_PUSH', 'PETLA_FINAL_ARTIFACT')
    return [dict(id=ident, code=0 if os.environ.get(variable) == 'success' else 1,
                 usable=os.environ.get(variable) == 'success',
                 status='OK' if os.environ.get(variable) == 'success' else 'BLAD',
                 reason='' if os.environ.get(variable) == 'success' else variable + ': ' + os.environ.get(variable, 'MISSING'),
                 detected=False) for ident, variable in zip(TRIAL_OPERATION_IDS, variables)]


def source_digest(root):
    files = sorted(p for folder in ('silnik', '.github') for p in (root / folder).rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts)
    return hashlib.sha256(encoded({p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in files})).hexdigest()


def tool_digest(C, groups=('c', 'duck')):
    pass                                                                         
    builder = C.world_module('budowa-solver.py', 'petla_tools_builder')
    probe = C.world_module('proba-solver-c.py', 'petla_tools_probe')
    files = sorted(p for p in (C.base.TEMP / 'toolchain-port').rglob('*') if p.is_file()) if 'duck' in groups else []
    if 'duck' in groups and not files:
        raise ValueError('PETLA: missing narzedzi')
    asset = C.base.TEMP / 'pobranie/duckling-dev-linux-x86_64.tar.gz'
    if 'duck' in groups and asset.exists() and hashlib.sha256(asset.read_bytes()).hexdigest() != C.base.SHA:
        raise ValueError('PETLA: zla checksum archiwum Ducklinga')
    originals = builder.source_sums(C.base.TEMP / 'box2d') if 'c' in groups else {}
    contract = norm_text(C.PORT / 'fixtures/norms/KONTRAKT-7.json')
    if any(f'{digest}  {name}' not in contract for name, digest in originals.items()):
        raise ValueError('PETLA: zle checksum oryginalu C')
    identity = dict(duckling=C.base.SHA, box2d=C.base.PINS['box2d'][1], originals=originals,
                    tools={p.relative_to(C.base.TEMP).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                    flags=[builder.FLAGS, *[probe.flags(p) for p in probe.PROFILES]])
    return hashlib.sha256(encoded(identity)).hexdigest()


def bundle_files(C, groups=('c', 'duck')):
    files = {'out/' + p.name: p for p in C.OUT.iterdir() if p.is_file() and
             (p.name.endswith('-bin') or p.name in ('c-only-build.json', 'BUDOWA.json'))}
    for folder in (['box2d'] if 'c' in groups else []) + (['toolchain-port', 'pobranie'] if 'duck' in groups else []):
        files.update({'temp/' + p.relative_to(C.base.TEMP).as_posix(): p
                      for p in (C.base.TEMP / folder).rglob('*') if p.is_file() and not p.is_symlink()})
    return files


def pack_bundle(C, selection, sources, receipts):
    groups = [group for group, ident in (('c', 'narzedzia-c'), ('duck', 'narzedzia-duck'))
              if any(r['id'] == ident and r['usable'] for r in receipts)]
    files = bundle_files(C, groups)
    builder = C.world_module('budowa-solver.py', 'petla_bundle_builder')
    probe = C.world_module('proba-solver-c.py', 'petla_bundle_probe')
    flags = [builder.FLAGS, *[probe.flags(p) for p in probe.PROFILES]]
    manifest = dict(commit=selection['commit'], run=selection['run'], attempt=selection['attempt'],
                    source_sha256=sources, tools_sha256=tool_digest(C, groups), flags=flags,
                    files={name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in files.items()})
    private = Path(os.environ['RUNNER_TEMP']) / 'petla-private'
    private.mkdir(exist_ok=True)
    save(private / 'PAKIET.json', manifest)
    with tarfile.open(private / 'pakiet.tar.gz', 'w:gz') as archive:
        for name, path in files.items():
            archive.add(path, arcname=name, recursive=False)
    return manifest


def restore_bundle(C, selection, sources):
    private = Path(os.environ['RUNNER_TEMP']) / 'petla-private'
    manifest = json.loads((private / 'PAKIET.json').read_bytes())
    builder = C.world_module('budowa-solver.py', 'petla_bundle_builder')
    probe = C.world_module('proba-solver-c.py', 'petla_bundle_probe')
    flags = [builder.FLAGS, *[probe.flags(p) for p in probe.PROFILES]]
    identity = dict(commit=selection['commit'], run=selection['run'], attempt=selection['attempt'],
                    source_sha256=sources, tools_sha256=manifest.get('tools_sha256'), flags=flags,
                    files=manifest.get('files'))
    if manifest != identity or not re.fullmatch('[0-9a-f]{64}', str(manifest.get('tools_sha256', ''))):
        raise ValueError('PETLA: tozsamosc paczki niezgodna z biegiem')
                                                                              
                                                                            
                                                                            
    errors = []
    with tarfile.open(private / 'pakiet.tar.gz', 'r:gz') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names) or set(names) - set(manifest['files']):
            raise ValueError('PETLA: nadmiarowe pliki paczki')
        bad = set(manifest['files']) - set(names)
        files = {}
        for member in members:
            parts = PurePosixPath(member.name).parts
            if (not member.isfile() or not parts or parts[0] not in ('out', 'temp') or '\\' in member.name
                    or PurePosixPath(member.name).as_posix() != member.name or any(p in ('.', '..') for p in parts)):
                raise ValueError('PETLA: niedozwolona sciezka paczki')
            data = archive.extractfile(member).read()
            if hashlib.sha256(data).hexdigest() != manifest['files'][member.name]:
                bad.add(member.name)
            else:
                files[member.name] = data
        errors += ['missing lub zla checksum: ' + name for name in sorted(bad)]
        if not errors and verify_bundle(selection, manifest, files, sources=sources,
                                        tools=manifest['tools_sha256'], flags=flags):
            raise ValueError('PETLA: paczka niezgodna z receptura')
        for prefix in ('temp/box2d/', 'temp/toolchain-port/', 'temp/pobranie/'):
            if any(name.startswith(prefix) for name in bad):
                for name in list(files):
                    if name.startswith(prefix):del files[name]
                                                                             
                if prefix != 'temp/box2d/':
                    for name in list(files):
                        if name.startswith(('temp/toolchain-port/', 'temp/pobranie/')):del files[name]
        for path in C.OUT.glob('*-bin'):
            path.unlink()
        for member in members:
            if member.name not in files:continue
            prefix, *parts = Path(member.name).parts
            target_root = C.OUT if prefix == 'out' else C.base.TEMP
            target = target_root.joinpath(*parts).resolve()
            if not target.is_relative_to(target_root.resolve()):
                raise ValueError('PETLA: sciezka poza paczka')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[member.name])
            target.chmod(member.mode & 0o777)
    groups = [group for group, prefix in (('c', 'temp/box2d/'), ('duck', 'temp/toolchain-port/'))
              if any(name.startswith(prefix) for name in files)]
    actual_tools = tool_digest(C, groups)
    if not errors and actual_tools != manifest['tools_sha256']:
        raise ValueError('PETLA: podmienione narzedzia')
    return manifest, errors


def native_context(root, out, selection, deadline):
    os.environ['RESULT_DIR'] = str(out.relative_to(root))
    os.environ['PETLA_DEADLINE'] = str(deadline)
    C = load(root, 'ci.py', 'petla_existing_ci')
    C.selection = selection
    C = SimpleNamespace(**vars(C))
    solver = C.world_module('ci-solver.py', 'petla_existing_solver')
    solver.init(C)
    return C, solver


def build_ids(root):
    fixtures = load(root, 'fixtury-solver.py', 'petla_required_fixtures')
    return ['narzedzia-c', 'narzedzia-duck', 'c-solver', 'duckling-solver', 'duckling-component-solver',
            'profile-3', 'profile-4', 'profile-5',
            *['fixture-' + f.name for f in fixtures.definitions()], 'c-only-solver-budowa']


def build_trial(C, solver, selection, sources, emit, deadline):
    pass                                                                        
    def action(function):
        def run():
            value = function()
            code = value if isinstance(value, int) else 0
            return dict(code=code, usable=code == 0)
        return run
    def tools(group, prepare, cached):
        def verify():
            tool_digest(C, [group])
            return 0
        def operation():
            prepare()
            return 0
        return prepare_tools(selection, cache_hit=cached, restore=operation, build=operation, verify=verify)
    tasks = [dict(id='narzedzia-c', requires=[], action=action(lambda: tools('c', C.prepare_box2d_sources,
                       (C.base.TEMP / 'box2d/src').is_dir()))),
             dict(id='narzedzia-duck', requires=[], action=action(lambda: tools('duck', C.prepare_duckling_tools,
                       os.environ.get('ARCHIVE_CACHE_HIT') == 'true'))),
             dict(id='c-solver', requires=['narzedzia-c'], action=action(solver.compile_c)),
             dict(id='duckling-solver', requires=['narzedzia-duck'], action=action(solver.compile_duck)),
             dict(id='duckling-component-solver', requires=['narzedzia-duck'], action=action(solver.compile_component_duck))]
    native = C.world_module('mutacje-solver.py', 'petla_build_native')
    runtime = native.Runtime(C)
    try:
        for profile in (3, 4, 5):
            tasks.append(dict(id='profile-' + str(profile), requires=['narzedzia-duck'],
                              action=action(lambda profile=profile: runtime.profile(profile))))
        for fixture in native.f.definitions():
            tasks.append(dict(id='fixture-' + fixture.name, requires=['profile-4'],
                              action=action(lambda: runtime.profile(4))))
        probe = C.world_module('proba-solver-c.py', 'petla_build_c_probe')
        def c_only():
            result = probe.build_only(C)
            return dict(code=result['code'], usable=result['code'] == 0)
        tasks.append(dict(id='c-only-solver-budowa', requires=['narzedzia-c'], action=c_only))
        rows = run_batch(tasks, emit=emit, deadline=deadline)
        write_build(C.OUT, selection, rows, expected=len(tasks))
                                                                              
        runtime.profile_bins.clear()
    finally:
        runtime.close()
    return rows


def checkpoint(C, solver, selection):
    pass                                                                       

                                                                              
                                                                   
       
    snapshot = C.OUT / 'POSTEP'
    files = [*C.OUT.joinpath('DIAGNOZA').glob('*.json'), *C.OUT.glob('*-receipts.json')]
    files += [C.OUT / name for name in ('TRYB.json', 'BUDOWA.json')]
    files += [p for p in C.OUT.glob('*.csv') if p.name.endswith(('-polecenie.csv', '-kod.csv', '-czas.csv', '-stderr.csv'))]
    for path in files:
        if not path.is_file():continue
        relative = path.relative_to(C.OUT)
        target = snapshot / relative
        if path.stat().st_size <= 65536:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        else:
            save(target.with_name(target.name + '.omitted.json'),
                 dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), omitted=True))
    def filtering():
        solver.storage.prepare_publication(snapshot)
        return 0
    def push(message):
        commands = [('config-name', ['git', 'config', 'user.name', 'github-actions[bot]']),
                    ('config-email', ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com']),
                    ('add', ['git', 'add', '--', str(snapshot.relative_to(C.ROOT))]),
                    ('commit', ['git', 'commit', '-m', message]),
                    ('push', ['git', 'push', 'origin', 'HEAD:' + selection['ref']])]
        for name, command in commands:
            code = C.base.run('postep-' + name, command, seconds=120)
            if code:return code
        return 0
    same_input = C.base.run('postep-input', ['git', 'diff', '--exit-code', selection['commit'], 'HEAD', '--',
                                           'silnik', '.github'], seconds=30) == 0
    return publish(snapshot, selection, current_commit=selection['commit'] if same_input else None,
                   compact=lambda: 0, filter_payload=filtering, push=push)


def execute_trial(C, solver, selection, emit, deadline, bundle_ok, bundle_errors=()):
    C.petla_prebuilt = True
    counts = Counter()
    def native_receipt(kind, ident, row):
        counts[kind] += 1
        predicates = list(row.get('predicates', []))
        def predicate(name, expected, actual):
            predicates.append(dict(name=name, ok=expected == actual, expected=expected, actual=actual))
        if 'detected' in row:
            for name in ('clean', 'detected', 'replayed_before_compaction'):
                predicate(name, True, row.get(name, False))
            predicate('exit', 0, row.get('code'))
            predicate('difference_present', True, row.get('difference') is not None)
        else:
            predicate('ok', True, row.get('ok', False))
            if 'equal' in row:predicate('equal', True, row['equal'])
            for side, process in row.get('processes', {}).items():
                predicate(side + '-exit', 0, process['code'])
                predicate(side + '-schema', None, process.get('error'))
                if 'stderr_sha256' in process:
                    predicate(side + '-stderr', hashlib.sha256(b'').hexdigest(), process['stderr_sha256'])
        predicate('error', None, row.get('error'))
        write_diagnosis(C.OUT, selection, kind, ident, predicates, executed=counts[kind],
                        expected=234 if kind == 'mutacje' else 95 if kind == 'fixtury' else 3 if kind == 'zastepstwa' else 2,
                        blocked=[], logs={})
    C.petla_receipt = native_receipt
    guards = C.world_module('ci-solver-oslony.py', 'petla_execute_guards')
    def stage(name):
        def run():
            if name == 'proba-solver':
                value = solver.sample(prebuilt=True)
            elif name == 'oslony-solver':
                value = guards.stage(C)
            elif name == 'testy-solver':
                value = C.base.run('testy-solver', [sys.executable, '-B', '-m', 'unittest', 'discover',
                                   '-s', 'silnik/port', '-p', 'test_*.py', '-v'], seconds=600)
            elif name == 'summary-solver':
                                                                               
                                                                              
                value = solver.check()
            else:
                value = {'porownanie-solver': solver.full, 'component-solver': lambda: solver.full(True),
                         'check-solver': solver.check, 'zapis-strumieni-solver': solver.compact}[name]()
            code = value or 0
            (C.OUT / ('etap-port-' + name + '-kod.csv')).write_bytes((str(code) + '\n').encode('ascii'))
            return dict(code=code, usable=code == 0)
        return run
    tasks = [dict(id='pakiet', requires=[], action=lambda: dict(code=0 if bundle_ok and not bundle_errors else 1,
                  usable=bundle_ok, reason='; '.join(bundle_errors)))]
    for name in EXECUTE:
        tasks.append(dict(id=name, requires=[] if name in ('testy-solver', 'summary-solver', 'zapis-strumieni-solver') else ['pakiet'],
                          action=stage(name)))
        if name == 'check-solver' and os.environ.get('PETLA_CHECKPOINTS') == '1':
            def save_checkpoint():
                code = checkpoint(C, solver, selection)
                return dict(code=code, usable=code == 0)
            tasks.append(dict(id='zapis-przed-mutacjami', requires=[], action=save_checkpoint))
    return run_batch(tasks, emit=emit, deadline=deadline)


def full_evidence(root, selection, out, phase, result_cache=None):
    pass                                                                 

                                                                            
                                                                           
       
    C = load(root, 'ci.py', 'petla_full_existing_ci')
    selection = {**selection, 'evidence':True}
    sources = source_digest(root)
    tools = tool_digest(C)
    if phase == 'regresja':
        errors = []
        path = out / 'wynik-kod.csv'
        if not path.is_file():errors.append('missing podsumowania zakresu')
        elif path.read_text().strip() != '0':errors.append('czerwone podsumowanie zakresu')
        for name in ('SUMMARY_OUTCOME', 'MIEJSCE_OUTCOME', 'PUBLISH_OUTCOME', 'ARTIFACT_OUTCOME', 'STORAGE_OUTCOME', 'FILTER_OUTCOME'):
            if name in os.environ and os.environ[name] != 'success':errors.append(name + ': ' + os.environ[name])
        code = int(bool(errors))
        if errors and (out / 'mutacje-kontakty-wynik.json').is_file():
            try:
                for row in json.loads((out / 'mutacje-kontakty-wynik.json').read_bytes()):
                    if row.get('detected') is not True:
                        messages = [e.get('message', '') for e in row.get('errors', [])]
                        errors.append(row['name'] + ': ' + ('; '.join(messages) or row.get('status', 'missing wykrycia')))
            except (OSError, ValueError, KeyError, TypeError) as exc:errors.append('odczyt przyczyn mutacji9b: ' + str(exc))
        proof = dict(commit=selection['commit'], source_sha256=sources, tools_sha256=tools,
                     code=code, outcome='success' if code == 0 else 'failure')
        if errors:
            proof['errors'] = errors
            if (out / 'DZIENNIK.md').is_file():proof['diagnosis'] = (out / 'DZIENNIK.md').read_text(encoding='utf-8')
        save(out / 'REGRESJA.json', proof)
        return code
    if phase == 'wynik-pelny-11':
        sen = load(root, 'ci-sen.py', 'petla_full_sen')
        required = [*sen.STAGES, 'porownanie-sen-11a', 'component-sen-11a', 'oslony-sen', 'summary-sen', 'zapis-strumieni-sen', 'prior-1-10']
        receipts = []
        for name in required[:-1]:
            path = out / (('etap-port-' if name == 'oslony-sen' else '') + name + '-kod.csv')
            try:code = int(path.read_text().strip());reason = ''
            except (OSError, ValueError):code = 1;reason = 'missing uruchomienia / potwierdzenia'
            if name == 'summary-sen':
                try:
                    summary = json.loads((out / 'podsumowanie-sen.json').read_bytes())
                    reason = '; '.join(summary['errors'])
                    if summary.get('code') != 0 or summary['errors']:code = 1
                except (OSError, ValueError, KeyError):reason = 'missing poprawnego podsumowania 11';code = 1
            elif code != 0 and not reason:
                detail = out / ('oslony-wynik.json' if name == 'oslony-sen' else name + '-etap.json')
                try:
                    value = json.loads(detail.read_bytes())
                    reason = '; '.join(value.get('errors', [])) or value.get('error') or ''
                except (OSError, ValueError, TypeError):pass
            receipts.append(dict(id=name, code=code, status='OK' if code == 0 else 'BLAD', reason=reason))
        try:
            prior = json.loads((out.parent / 'krok10/RESULT.json').read_bytes())
            valid = (prior.get('commit') == selection['commit'] and prior.get('source_sha256') == sources
                     and prior.get('tools_sha256') == tools and prior.get('scope') == 'RESULT 1…10'
                     and prior.get('complete') is True and prior.get('code') == 0)
            reason = '; '.join(prior.get('errors', [])) or 'wynik 1–10 czerwony lub niezgodny'
        except (OSError, ValueError):valid = False;reason = 'missing wyniku 1–10'
        receipts.append(dict(id='prior-1-10', code=0 if valid else 1, status='OK' if valid else 'BLAD', reason='' if valid else reason))
        required.append('workflow-summary-sen')
        outcome = os.environ.get('SEN_SUMMARY_OUTCOME', 'MISSING')
        receipts.append(dict(id='workflow-summary-sen', code=0 if outcome == 'success' else 1,
                             status='OK' if outcome == 'success' else 'BLAD', reason='' if outcome == 'success' else outcome))
        receipts += [dict(id='sources', sha256=sources), dict(id='tools', sha256=tools)]
        base = root / selection['result_dir']
        regressions = {}
        for name, directory in (('1-7', base), ('8', base / 'krok8'), ('9a', base / 'krok9a'), ('9b', base / 'krok9b')):
            try:regressions[name] = json.loads((directory / 'REGRESJA.json').read_bytes())
            except (OSError, ValueError):pass
        publication = {name: 0 if os.environ.get('PETLA_' + name.upper()) == 'success' else 1
                       for name in ('compact', 'filter', 'push', 'artifact')}
        if os.environ.get('SEN_STORAGE_OUTCOME') != 'success':publication['compact'] = 1
        publication['commit'] = selection['commit']
        return finish(out, {**selection, 'N':11}, required=required, receipts=receipts,
                      publication=publication, regressions=regressions, read_results=False)
    receipts = []
    for name in EXECUTE:
        reason = ''
        try:
            code = (0 if os.environ.get('PETLA_TESTY') == 'success' else 1) if name == 'testy-solver' else int(
                (out / ('etap-port-' + name + '-kod.csv')).read_text().strip())
        except (OSError, ValueError):
            code = 1
        if code != 0:
            details = {'oslony-solver':('oslony-wynik.json','mutacje-solver-pokrycie.json'),
                       'check-solver':('solver-odbior.json',), 'porownanie-solver':('public10-manifest.json',),
                       'component-solver':('component10-manifest.json',)}
            for filename in details.get(name, ()):
                try:reason += '; '.join(json.loads((out / filename).read_bytes()).get('errors', [])) + '; '
                except (OSError, ValueError, TypeError):pass
        receipts.append(dict(id=name, code=code, usable=code == 0, status='OK' if code == 0 else 'BLAD', reason=reason.rstrip('; ')))
    receipts += [dict(id='sources', sha256=sources), dict(id='tools', sha256=tools)]
    required = [*EXECUTE, 'miejsce-solver', 'workflow-summary-solver']
    place_ok = os.environ.get('PETLA_MIEJSCE') == 'success'
    receipts.append(dict(id='miejsce-solver', code=0 if place_ok else 1, status='OK' if place_ok else 'BLAD',
                         reason='' if place_ok else 'miejsce10: ' + os.environ.get('PETLA_MIEJSCE', 'MISSING')))
    outcome = os.environ.get('SUMMARY_OUTCOME', 'MISSING')
    receipts.append(dict(id='workflow-summary-solver', code=0 if outcome == 'success' else 1,
                         status='OK' if outcome == 'success' else 'BLAD', reason='' if outcome == 'success' else outcome))
    base = root / selection['result_dir']
    regressions = {}
    for name, directory in (('1-7', base), ('8', base / 'krok8'), ('9a', base / 'krok9a'), ('9b', base / 'krok9b')):
        try:
            regressions[name] = json.loads((directory / 'REGRESJA.json').read_bytes())
        except (OSError, ValueError):
            pass
    publication = {name: 0 if os.environ.get('PETLA_' + name.upper()) == 'success' else 1
                   for name in ('compact', 'filter', 'push', 'artifact')}
    publication['commit'] = selection['commit']
    return finish(out, selection, required=required, receipts=receipts,
                  publication=publication, regressions=regressions, result_cache=result_cache)


def dispatch(result_cache=None):
    result_cache = {} if result_cache is None else result_cache
    root = Path(__file__).resolve().parents[2]
    try:
        selection = select_mode(os.environ.get('GITHUB_REF_NAME', ''), root,
                                os.environ.get('GITHUB_RUN_ID', ''), os.environ.get('GITHUB_RUN_ATTEMPT', ''),
                                os.environ.get('GITHUB_SHA', ''))
    except ValueError as exc:
        sys.stderr.buffer.write((str(exc) + '\n').encode('utf-8'))
        return 2
    phase = sys.argv[1] if len(sys.argv) == 2 else ''
    if phase == 'plan':
        sys.stdout.buffer.write(encoded(selection))
        return 0
    if phase not in ('budowa', 'wykonanie', 'wynik', 'publikacja', 'regresja', 'wynik-pelny', 'wynik-pelny-11'):
        sys.stderr.write('PETLA: nieobslugiwana komenda\n')
        return 2
    out = root / selection['result_dir']
    if phase in ('regresja', 'wynik-pelny', 'wynik-pelny-11'):
        actual_out = (root / os.environ.get('RESULT_DIR', '')).resolve()
        if selection['mode'] != 'full' or not actual_out.is_relative_to(out.resolve()):
            raise ValueError('PETLA: niepoprawny zakres pelnego odbioru')
        try:
            return full_evidence(root, selection, actual_out, phase, result_cache=result_cache)
        except Exception as exc:
                                                                            
            if phase == 'regresja':
                save(actual_out / 'REGRESJA.json', dict(commit=selection['commit'], source_sha256=None,
                     tools_sha256=None, code=1, outcome='failure', errors=[str(exc)]))
                sys.stderr.write('PETLA: ' + str(exc) + '\n')
                return 1
            finish(actual_out, {**selection, 'N':11} if phase == 'wynik-pelny-11' else selection,
                   required=['odbior-11'] if phase == 'wynik-pelny-11' else EXECUTE,
                   receipts=[dict(id='odbior-11', code=1, status='BLAD', reason=str(exc))] if phase == 'wynik-pelny-11' else [],
                   publication={}, regressions=None, result_cache=result_cache)
            sys.stderr.write('PETLA: ' + str(exc) + '\n')
            return 1
    save(out / 'TRYB.json', selection)
    if phase == 'publikacja':
        C = load(root, 'ci.py', 'petla_publication_ci')
        solver = C.world_module('ci-solver.py', 'petla_publication_solver')
        solver.init(C)
        components = dict(compact=1, filter=1, push=1, commit=selection['commit'])
        def tracked(name, function):
            def call():
                components[name] = function() or 0
                return components[name]
            return call
        def filtering():
            solver.storage.prepare_publication(out)
            return 0
        def push_result(message):
            return C.base.run('petla-push', ['bash', '-c', 'push_result "$1"', 'petla-publish', message], seconds=120)
        same_input = C.base.run('petla-input', ['git', 'diff', '--exit-code', selection['commit'], 'HEAD', '--',
                                               'silnik', '.github'], seconds=30) == 0
        code = publish(out, selection, current_commit=selection['commit'] if same_input else None,
                       compact=tracked('compact', solver.compact), filter_payload=tracked('filter', filtering),
                       push=lambda message: tracked('push', lambda: push_result(message))())
        save(out / 'PUBLIKACJA.json', components)
        return code
    if phase == 'wynik':
        data = json.loads((out / 'WYKONANIE.json').read_bytes())
        try:
            outcomes = json.loads((out / 'PUBLIKACJA.json').read_bytes())
        except (OSError, ValueError):
            outcomes = {}
        outcomes['artifact'] = 0 if os.environ.get('PETLA_ARTIFACT') == 'success' else 1
        if os.environ.get('PETLA_FILTER') != 'success':outcomes['filter'] = 1
        required = list(data['required'])
        for ident in ('pakiet', *EXECUTE, *TRIAL_OPERATION_IDS):
            if ident not in required:required.append(ident)
        receipts = [row for row in data['receipts'] if row['id'] not in TRIAL_OPERATION_IDS] + operation_receipts()
        save(out / 'WYKONANIE.json', dict(required=required, receipts=receipts))
        return finish(out, selection, required=required, receipts=receipts,
                      publication=outcomes, regressions=None, result_cache=result_cache)
    seconds = 900 if phase == 'budowa' else 3600
    wall_deadline = time.time() + seconds
    deadline = time.monotonic() + seconds
    C, solver = native_context(root, out, selection, wall_deadline)
    sources = source_digest(root)
    rows = []
    expected_ids = build_ids(root) if phase == 'budowa' else ['pakiet', *EXECUTE]
    if phase == 'wykonanie' and os.environ.get('PETLA_CHECKPOINTS') == '1':
        expected_ids.append('zapis-przed-mutacjami')
    command_counts = Counter()
    def command_receipt(name, command, code, elapsed, cwd):
        command_counts[name] += 1
        ident = re.sub(r'[^A-Za-z0-9_-]', '_', name) + '-' + str(command_counts[name])
        write_diagnosis(out, selection, 'polecenia-' + phase, ident,
                        [dict(name='exit', ok=code == 0, expected=0, actual=code)],
                        executed=sum(command_counts.values()), expected=1, blocked=[],
                        logs={key: name + suffix for key, suffix in
                              (('command', '-polecenie.csv'), ('code', '-kod.csv'),
                               ('time', '-czas.csv'), ('stderr', '-stderr.csv'))})
    C.base.command_receipt = command_receipt
    def emit(row):
        rows.append(row)
        write_diagnosis(out, selection, phase, row['id'],
                        [dict(name='exit', ok=row['code'] == 0, expected=0, actual=row['code']),
                         dict(name='usable', ok=row['usable'], expected=True, actual=row['usable'])],
                        executed=sum(r['status'] != 'ZABLOKOWANE' for r in rows), expected=len(expected_ids),
                        blocked=[row['reason']] if row['reason'] else [], logs={})
        save(out / (phase + '-receipts.json'), rows)
    if phase == 'budowa':
        built = build_trial(C, solver, selection, sources, emit, deadline)
        try:
            pack_bundle(C, selection, sources, built)
        except Exception as exc:
            emit(dict(id='pakowanie', code=1, usable=False, status='BLAD', reason=str(exc), detected=False))
            write_build(out, selection, rows, expected=len(built) + 1)
        return int(any(r['code'] for r in rows))
    bundle_ok = False
    bundle_errors = []
    try:
        _, bundle_errors = restore_bundle(C, selection, sources)
        bundle_ok = True
    except Exception as exc:
        emit(dict(id='odtworzenie', code=1, usable=False, status='BLAD', reason=str(exc), detected=False))
    build = json.loads((out / 'BUDOWA.json').read_bytes()) if (out / 'BUDOWA.json').is_file() else {'receipts': []}
    execute_trial(C, solver, selection, emit, deadline, bundle_ok, bundle_errors)
    required = build_ids(root) + expected_ids
    required += [r['id'] for r in build['receipts'] if r['id'] not in required]
    required += [r['id'] for r in rows if r['id'] not in expected_ids]
    receipts = build['receipts'] + rows
    save(out / 'WYKONANIE.json', dict(required=required, receipts=receipts))
    finish(out, selection, required=required, receipts=receipts, publication={}, regressions=None, result_cache=result_cache)
    return int(any(r['code'] for r in receipts) or not build['receipts'])


def main():
    result_cache = {}
    try:
        return dispatch(result_cache=result_cache)
    except Exception as exc:
                                                                            
                                                                              
        root = Path(__file__).resolve().parents[2]
        try:
            selection = select_mode(os.environ.get('GITHUB_REF_NAME', ''), root,
                                    os.environ.get('GITHUB_RUN_ID', ''), os.environ.get('GITHUB_RUN_ATTEMPT', ''),
                                    os.environ.get('GITHUB_SHA', ''))
            out = root / selection['result_dir']
            (out / ('KROK.json' if selection['mode']=='proba' else 'RESULT.json')).unlink(missing_ok=True)
            fault = dict(id='przygotowanie', code=1, usable=False, status='BLAD',
                         reason=type(exc).__name__ + ': ' + str(exc), detected=False)
            rows=[]
                                                                                 
            for name in ('budowa-receipts.json', 'wykonanie-receipts.json'):
                try:rows += json.loads((out/name).read_bytes())
                except (OSError,ValueError):pass
            rows.append(fault)
            if not (out/'BUDOWA.json').exists():write_build(out,selection,rows,expected=max(1,len(rows)))
            required=[row['id'] for row in rows]+['pakiet',*EXECUTE,*TRIAL_OPERATION_IDS]
            save(out/'WYKONANIE.json',dict(required=required,receipts=rows))
            finish(out,selection,required=required,receipts=rows,publication={},regressions=None,result_cache=result_cache)
            case='blad-'+str(1+len(list((out/'DIAGNOZA').glob('przygotowanie-*.json'))))
            write_diagnosis(out,selection,'przygotowanie',case,
                            [dict(name='przygotowanie',ok=False,expected='gotowe',actual=fault['reason'])],
                            executed=len(rows)-1,expected=len(required),blocked=[fault['reason']],logs={})
        except Exception as fallback:
            sys.stderr.write('PETLA: zapis awaryjny: ' + str(fallback) + '\n')
        sys.stderr.write('PETLA: ' + type(exc).__name__ + ': ' + str(exc) + '\n')
        return 1


if __name__ == '__main__':
    sys.exit(main())
