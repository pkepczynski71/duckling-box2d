pass                                                                          

                                                                         
   
import argparse
import collections
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


recipes = load('ccd_ci_recipes', 'przypadki-ccd.py')
checker = load('ccd_ci_compare', 'porownaj-ccd.py')


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def execute(binary, data, directory, name, diagnostic=False, timeout=120, output_limit=16 * 1024 * 1024):
    pass                                                                     
    directory = Path(directory)
    output, error = directory / (name + '.out'), directory / (name + '.err')
    rss_file = directory / (name + '.rss')
    argv = [str(Path(binary).resolve()), *(['--diagnostic'] if diagnostic else [])]
    if os.name == 'posix' and Path('/usr/bin/time').is_file():
        argv = ['/usr/bin/time', '-f', '%M', '-o', str(rss_file), *argv]
    start = time.monotonic()
                                                                              
    preexec = None
    if os.name == 'posix':
        def bounds():
            import resource
            resource.setrlimit(resource.RLIMIT_FSIZE, (output_limit, output_limit))
        preexec = bounds
    with output.open('wb') as out, error.open('wb') as err:
        p = subprocess.run(argv, input=data, stdout=out, stderr=err, timeout=timeout, preexec_fn=preexec)
    rss = None
    if rss_file.exists():
        try:
            rss = int(rss_file.read_text().splitlines()[-1])
        except ValueError:
            pass
    return {'exit': p.returncode, 'seconds': time.monotonic() - start,
            'stdoutBytes': output.stat().st_size, 'stderrBytes': error.stat().st_size,
            'maxRssKiB': rss, 'argv': argv, 'inputSha256': digest_bytes(data),
            'stdout': str(output), 'stderr': error.read_text(errors='replace')[:16384]}


def success(run):
    if run['exit'] != 0 or run['stderrBytes']:
        raise ValueError('Unexpected process outcome: ' + repr(run))


def parser_campaign(binary, side, directory, label=''):
    rows = []
    for p in recipes.manifest()['parserCases']:
        outcomes = []
        for positive in (False, True):
            key = ('positive' if positive else 'input') + side
            run = execute(binary, p[key].encode('ascii'), directory, label + p['id'] + side + str(positive), True)
            expected_exit = p['positiveExitCode'] if positive else p['exitCode']
            expected_err = p['positiveStderr'] if positive else p['stderr']
            good = run['exit'] == expected_exit and run['stderr'] == expected_err
            if positive:
                good = good and Path(run['stdout']).read_bytes().endswith(b'END 1\n')
            else:
                output = Path(run['stdout']).read_bytes()
                silent = ('HEADER', 'TAG', 'PART', 'PROFILE', 'N', 'CASE', 'ID', 'COUNT', 'LINE_LENGTH', 'EOF', 'ASCII')
                if p['classification'] in silent:
                    good = good and not output
                elif p['classification'] == 'TRAILING_DATA':
                                                                                
                    good = good and output.endswith(b'ENDCASE 1\n')
                else:
                    header = p['positiveC'].splitlines()[1].split()
                    good = good and output == ('CASE ' + header[1] + ' ' + header[2] + '\n').encode()
            outcomes.append({'positive': positive, 'ok': good, **run})
        if p['classification'] == 'TRAILING_DATA':
            negative, positive = [Path(x['stdout']).read_bytes() for x in outcomes]
            outcomes[0]['ok'] = outcomes[0]['ok'] and negative == positive.removesuffix(b'END 1\n')
        rows.append({'id': p['id'], 'class': p['classification'], 'ok': all(x['ok'] for x in outcomes), 'runs': outcomes})
    return rows


def pilot_complete(receipt, require_d=True):
    probes = receipt.get('probes', [])
    expected = {('DIRECT',i) for i in (1,17,49,81,87,113)} | {('GUARD',262)}
    if collections.Counter((r.get('profile'),r.get('id')) for r in probes) != collections.Counter(expected):
        return False
    parser_ids = {p['id'] for p in recipes.manifest()['parserCases']}
    for key in (('parsers','Dparsers') if require_d else ('parsers',)):
        rows = receipt.get(key, [])
        if (collections.Counter(r.get('id') for r in rows) != collections.Counter(parser_ids)
                or any(r.get('ok') is not True for r in rows)):
            return False
    return not require_d or (receipt.get('DpilotErrors') == [] and all(
        'Dstats' in r and r.get('Dcomparison', {}).get('differences') == 0 for r in probes))


def pilot(c0, c1, out, d=None):
    m = recipes.manifest()
    probes = [('DIRECT', x) for x in (1, 17, 49, 81, 87, 113)] + [('GUARD', 262)]
    result = []
    with tempfile.TemporaryDirectory(prefix='pilot-', dir=out) as tmp:
        for profile, i in probes:
            inp = recipes.input_bytes(profile, 'C', {i})
            row = {'profile': profile, 'id': i}
            row['run'] = execute(c1, inp, tmp, f'{profile}{i}', True)
            success(row['run'])
            row['stats'] = checker.inspect(row['run']['stdout'], profile, {i})
            row['family'] = m['cases'][i - 1]['family'] if profile == 'DIRECT' else 'GUARD'
            if d:
                row['D'] = execute(d, recipes.input_bytes(profile, 'D', {i}), tmp, f'D{profile}{i}', True)
                try:
                    success(row['D'])
                    row['Dstats'] = checker.inspect(row['D']['stdout'], profile, {i})
                    row['Dcomparison'] = checker.compare(row['run']['stdout'], row['D']['stdout'])
                except Exception as e:
                    row['Derror'] = str(e)[:16384]
            result.append(row)
        parsers = parser_campaign(c1, 'C', tmp)
        d_parsers = parser_campaign(d, 'D', tmp) if d else []
    family_cost = {}
    for row in result:
        f = row['family']
        cost = family_cost.setdefault(f, {'seconds': 0, 'bytes': 0, 'records': 0, 'q': 0, 'rssKiB': 0})
        cost['seconds'] = max(cost['seconds'], row['run']['seconds'])
        cost['bytes'] = max(cost['bytes'], row['stats']['bytes'])
        cost['records'] = max(cost['records'], row['stats']['records'])
        cost['q'] = max(cost['q'], row['stats']['tags'].get('Q16', 0))
        cost['rssKiB'] = max(cost['rssKiB'], row['run']['maxRssKiB'] or 0)
    multiplicity = collections.Counter(c['family'] for c in m['cases'])
    multiplicity['GUARD'] = 262
    predicted_bytes = sum(family_cost[f]['bytes'] * count for f, count in multiplicity.items())
    predicted_seconds = sum(family_cost[f]['seconds'] * count for f, count in multiplicity.items())
    d_cost = {}
    for row in result:
        if 'Dstats' not in row:
            continue
        cost = d_cost.setdefault(row['family'], {'seconds': 0, 'bytes': 0, 'records': 0, 'q': 0, 'rssKiB': 0})
        for key, value in [('seconds', row['D']['seconds']), ('bytes', row['Dstats']['bytes']),
                           ('records', row['Dstats']['records']), ('q', row['Dstats']['tags'].get('Q16', 0)),
                           ('rssKiB', row['D']['maxRssKiB'] or 0)]:
            cost[key] = max(cost[key], value)
    receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'beforeFullRun': True,
               'families': family_cost, 'probes': result, 'parsers': parsers,
               'predictedC1Bytes': predicted_bytes, 'predictedC1Seconds': predicted_seconds,
               'budget2xBytes': 2 * predicted_bytes, 'budget2xSeconds': 2 * predicted_seconds,
               'perOperationLimit': 2097152, 'directLimit': 613416960, 'guardLimit': 2121728,
               'buildBytes': sum(p.stat().st_size for p in Path(c1).parent.rglob('*') if p.is_file()),
               'freeBytes': shutil.disk_usage(out).free}
    if d:
        receipt['Dfamilies'] = d_cost
        receipt['Dparsers'] = d_parsers
        receipt['DpilotErrors'] = [row for row in result if row.get('Derror') or row.get('Dcomparison', {}).get('differences')]
        receipt['predictedDSeconds'] = sum(d_cost[f]['seconds'] * count for f, count in multiplicity.items() if f in d_cost)
        receipt['predictedDBytes'] = sum(d_cost[f]['bytes'] * count for f, count in multiplicity.items() if f in d_cost)
        receipt['budget2xDSeconds'] = 2 * receipt['predictedDSeconds']
        receipt['budget2xDBytes'] = 2 * receipt['predictedDBytes']
    save(Path(out) / 'pilot-receipt.json', receipt)
    if not pilot_complete(receipt, bool(d)):
        raise ValueError('Pilot incomplete/red: probes, C/D parser results or D comparisons')
    return receipt


def historical_results(stats, row):
    expected = []
    for sample in row['samples']:
        expected.extend([sample['c18aResultH']] * (2 if sample['opcode'] in (300, 301) else 1))
    if [r['wordsH'] for r in stats['results']] != expected:
        raise ValueError('Native C differs from frozen C18a reference at ' + row['id'])


CAMPAIGN_SCOPE = '16a: DIRECT128/GUARD262/parsery'
UNEXECUTED = ['pokrycie 16a', 'TimeOfImpact sample', 'test_distance.c proba']


def campaign_complete(result, require_d=True):
    pass                                                                      
    if result.get('errors') != []:
        return False
    sides = {'C0','C1','D'} if require_d else {'C0','C1'}
    expected = {(profile,i) for profile,n in (('DIRECT',128),('GUARD',262)) for i in range(1,n+1)}
    cases = result.get('cases', [])
    if collections.Counter((r.get('profile'),r.get('id')) for r in cases) != collections.Counter(expected):
        return False
    if any(r.get('errors') != [] for r in cases):
        return False
    populations = [r for r in result.get('populations', []) if r.get('side') != 'instrumented']
    if collections.Counter((r.get('profile'),r.get('side')) for r in populations) != collections.Counter(
            (p,s) for p in ('DIRECT','GUARD') for s in sides):
        return False
    parser_ids = {p['id'] for p in recipes.manifest()['parserCases']}
    for side in sides:
        rows = result.get('parsers', {}).get(side, [])
        if collections.Counter(r.get('id') for r in rows) != collections.Counter(parser_ids):
            return False
        if any(r.get('ok') is not True for r in rows):
            return False
    return True


def campaign(c0, c1, out, frozen=None, d=None, freeze=False, instrumented=None):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if freeze and (out / 'freeze.json').exists():
        raise ValueError('Refuse to overwrite frozen C expectations')
    m = recipes.manifest()
    if frozen:
        frozen = Path(frozen).resolve()
        old = json.loads(frozen.read_text())
        if old['manifestSha256'] != recipes.sha(HERE / 'ccd-16a-przypadki.json') or not old['completeC']:
            raise ValueError('Invalid/incomplete frozen baseline')
        old_cases = {(x['profile'], x['id']): x for x in old['cases']}
    else:
        old_cases = {}
    result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'manifestSha256': recipes.sha(HERE / 'ccd-16a-przypadki.json'),
              'pins': recipes.PINS, 'binaries': {k: {'path': str(v), 'sha256': recipes.sha(v)} for k, v in [('C0', c0), ('C1', c1), ('D', d), ('instrumented', instrumented)] if v},
              'cases': [], 'errors': [], 'scope': CAMPAIGN_SCOPE, 'NIEWYKONANE': UNEXECUTED,
              'unexecuted': list(UNEXECUTED) + ([] if d else ['Native D driver not supplied']), 'completeC': False, 'completeD': False}
    if d and not frozen:
        raise ValueError('D requires C expectations frozen beforehand')
    with tempfile.TemporaryDirectory(prefix='cases-', dir=out) as tmp:
        for profile, rows in [('DIRECT', m['cases']), ('GUARD', m['guards'])]:
            for row in rows:
                i = row['ordinal']
                item = {'profile': profile, 'id': i, 'errors': []}
                try:
                    inp = recipes.input_bytes(profile, 'C', {i})
                    item['inputCsha256'] = digest_bytes(inp)
                    item['inputDsha256'] = digest_bytes(recipes.input_bytes(profile, 'D', {i}))
                    a = execute(c0, inp, tmp, 'c0', True)
                    b = execute(c1, inp, tmp, 'c1', True)
                    success(a); success(b)
                    item['C0'] = checker.inspect(a['stdout'], profile, {i}, False)
                    item['C1'] = checker.inspect(b['stdout'], profile, {i}, True)
                    item['neutrality'] = checker.compare(b['stdout'], a['stdout'], True)
                    item['cost'] = {k: b[k] for k in ('seconds', 'maxRssKiB', 'stdoutBytes')}
                    if item['neutrality']['differences']:
                        raise ValueError('C0 != projection C1')
                    if profile == 'DIRECT':
                        historical_results(item['C1'], row)
                    if frozen:
                        old_row = old_cases[(profile, i)]
                        expected = frozen.parent / old_row['expectedFile']
                        if recipes.sha(expected) != old_row['expectedGzipSha256']:
                            raise ValueError('Frozen expected file changed')
                        plain = Path(tmp) / 'expected.out'
                        with gzip.open(expected, 'rb') as src, plain.open('wb') as dst:
                            shutil.copyfileobj(src, dst)
                        item['frozenComparison'] = checker.compare(plain, b['stdout'])
                        if item['frozenComparison']['differences']:
                            raise ValueError('C output differs from frozen expectations')
                    if instrumented:
                        g = execute(instrumented, inp, tmp, 'gcov', True)
                        success(g)
                        item['instrumentation'] = checker.compare(b['stdout'], g['stdout'])
                        if item['instrumentation']['differences']:
                            raise ValueError('Instrumented C1 changed output')
                    if d:
                        di = recipes.input_bytes(profile, 'D', {i})
                        dr = execute(d, di, tmp, 'd', True)
                        success(dr)
                        item['D'] = checker.inspect(dr['stdout'], profile, {i}, True)
                        item['comparison'] = checker.compare(b['stdout'], dr['stdout'])
                        if item['comparison']['differences']:
                            raise ValueError('C1 != D')
                    if freeze:
                        dest = out / 'expected' / f'{profile}-{i:03d}.csv.gz'
                        dest.parent.mkdir(exist_ok=True)
                        with open(b['stdout'], 'rb') as src, dest.open('wb') as raw:
                            with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as dst:
                                shutil.copyfileobj(src, dst)
                        item['expectedFile'] = dest.relative_to(out).as_posix()
                        item['expectedGzipSha256'] = recipes.sha(dest)
                except Exception as e:
                    item['errors'].append(str(e)[:16000])
                    result['errors'].append({'profile': profile, 'id': i, 'error': str(e)[:16000]})
                result['cases'].append(item)
                if i % 16 == 0:
                    save(out / 'progress.json', {'profile': profile, 'id': i, 'errors': len(result['errors'])})
                                                                         
        result['populations'] = []
        for profile in ('DIRECT', 'GUARD'):
            for label, binary, side, obs in [('C0', c0, 'C', False), ('C1', c1, 'C', True), ('D', d, 'D', True), ('instrumented', instrumented, 'C', True)]:
                if not binary:
                    continue
                try:
                    run = execute(binary, recipes.input_bytes(profile, side), tmp, 'population-' + profile + label, False,
                                  output_limit=613416960 if profile == 'DIRECT' else 2121728)
                    success(run)
                    stats = checker.inspect(run['stdout'], profile, observed=obs)
                    comparison = None
                    if label != 'C0':
                        reference = Path(tmp) / ('population-' + profile + ('C0' if label == 'C1' else 'C1') + '.out')
                        comparison = checker.compare(run['stdout'], reference, label == 'C1')
                        if comparison['differences']:
                            raise ValueError('Full population output differs: ' + repr(comparison))
                    result['populations'].append({'profile': profile, 'side': label, 'stats': stats, 'comparison': comparison,
                                                  'inputSha256': run['inputSha256'], 'seconds': run['seconds'], 'maxRssKiB': run['maxRssKiB']})
                except Exception as e:
                    result['errors'].append({'profile': profile, 'side': label, 'error': str(e)[:16000]})
        result['parsers'] = {}
        for name, binary, side in [('C0', c0, 'C'), ('C1', c1, 'C'), ('D', d, 'D'), ('instrumented', instrumented, 'C')]:
            if binary:
                try:
                    rows = parser_campaign(binary, side, tmp, name)
                    result['parsers'][name] = rows
                    result['errors'].extend({'parser': row['id'], 'side': name, 'error': 'fatal/positive mismatch'} for row in rows if not row['ok'])
                    if name != 'C0':
                        reference = result['parsers'].get('C0' if name == 'C1' else 'C1', [])
                        for actual, expected in zip(rows, reference):
                            for ar, er in zip(actual['runs'], expected['runs']):
                                diff = checker.compare(ar['stdout'], er['stdout'], name == 'C1')
                                if diff['differences']:
                                    result['errors'].append({'parser': actual['id'], 'side': name, 'error': 'Parser stdout differs', 'comparison': diff})
                except Exception as e:
                    result['errors'].append({'stage': 'parsers', 'side': name, 'error': str(e)[:16000]})
    if not campaign_complete(result, bool(d)) and not result['errors']:
        result['errors'].append({'stage': 'completeness', 'error': 'Missing/duplicate required cases, populations or parser results'})
    result['completeC'] = not result['errors']
    result['completeD'] = bool(d) and not result['errors']
    result['status'] = 'FAIL' if result['errors'] else 'PASS' if d else 'C_FROZEN_NO_D' if freeze else 'C_ONLY_NO_D'
    save(out / 'campaign.json', result)
    if freeze and result['completeC']:
        save(out / 'freeze.json', result)
    (out / 'PODSUMOWANIE.md').write_text(
        '# ' + CAMPAIGN_SCOPE + '\n\nStatus: ' + result['status'] + '\n\n' +
        f'DIRECT: {sum((c['profile'] == 'DIRECT' and (not c['errors']) for c in result['cases']))}/128; ' +
        f'GUARD: {sum((c['profile'] == 'GUARD' and (not c['errors']) for c in result['cases']))}/262.\n\n' +
        f'Diagnozy: {len(result['errors'])}. Nie wykonano: {', '.join(result['unexecuted']) or 'nic'}.\n', encoding='utf-8')
    return result


def compile_duckling(duckc, work):
    work = Path(work).resolve()
    if str(work).startswith('/mnt/'):
        raise ValueError('Native build must use Linux filesystem')
    driver = HERE / 'ccd.dk'
    if not driver.is_file():
        raise FileNotFoundError('Product driver ccd.dk not supplied')
    work.mkdir(parents=True, exist_ok=True)
    config = {'packages': [{'id': 'fizyka', 'name': 'fizyka', 'path': str(ROOT / 'silnik/fizyka')},
                           {'id': 'port16a', 'name': 'port16a', 'path': str(driver), 'dependencies': [{'id': 'fizyka'}]}],
              'tasks': [{'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
                        {'package': 'port16a', 'strategy': 'native', 'output_file': 'ccd-native',
                         'linking_options': {'additional_link_options': [str(work / 'libfizyka.a'), '-lm'], 'link_c_standard_library': True}}]}
    save(work / 'packages.json', config)
    argv = [str(Path(duckc).resolve()), 'compile_packages', str(work / 'packages.json'), '-a', str(work), '-O', '0']
    start = time.monotonic()
    p = subprocess.run(argv, capture_output=True, text=True, timeout=600)
    binary = work / 'ccd-native'
    receipt = {'argv': argv, 'exit': p.returncode, 'seconds': time.monotonic() - start, 'stdout': p.stdout[-16384:], 'stderr': p.stderr[-16384:],
               'compilerSha256': recipes.sha(duckc), 'sourceHashes': {str(x.relative_to(ROOT)): recipes.sha(x) for x in [driver, *sorted((ROOT / 'silnik/fizyka').glob('*.dk'))]},
               'binary': str(binary), 'binarySha256': recipes.sha(binary) if binary.exists() and p.returncode == 0 else None}
    save(work / 'native-receipt.json', receipt)
    if p.returncode or not binary.exists():
        raise ValueError('Native compile failed: ' + repr(receipt))
    return receipt


def whole_campaign(source, archive, work, frozen, out):
    pass                                                                 
    work, out = Path(work).resolve(), Path(out).resolve()
    if os.name != 'posix' or str(work).startswith('/mnt/'):
        raise ValueError('Whole native campaign requires a Linux filesystem copy')
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    stages, errors = {}, []
    builder = load('ccd_ci_builder', 'budowa-ccd.py')
    try:
        stages['C'] = builder.build(source, work / 'c')
    except Exception as e:
        errors.append({'stage': 'build-C', 'error': str(e)[:16384]})
    try:
        archive_hash = recipes.sha(archive)
        if archive_hash != 'f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519':
            raise ValueError('Compiler archive is not official pinned be929a1a')
        toolchain = work / 'toolchain'
        toolchain.mkdir(exist_ok=True)
        with tarfile.open(archive, 'r:gz') as tar:
            tar.extractall(toolchain, filter='data')
        compilers = list(toolchain.rglob('duckc'))
        if len(compilers) != 1:
            raise ValueError('Exactly one official duckc required')
        stages['D'] = compile_duckling(compilers[0], work / 'd')
        stages['D']['archiveSha256'] = archive_hash
        stages['D']['versionCommit'] = 'be929a1a49aa9938bc9d65caa0897b8dd855e8cf'
    except Exception as e:
        errors.append({'stage': 'build-D', 'error': str(e)[:16384]})
    if 'C' in stages:
        c0, c1 = work / 'c/ccd-c0', work / 'c/ccd-c1'
        try:
            pilot(c0, c1, out, stages.get('D', {}).get('binary'))
        except Exception as e:
            errors.append({'stage': 'pilot', 'error': str(e)[:16384]})
        try:
            result = campaign(c0, c1, out, frozen, stages.get('D', {}).get('binary'))
        except Exception as e:
            errors.append({'stage': 'campaign', 'error': str(e)[:16384]})
            result = {'completeC': False, 'completeD': False, 'errors': []}
    else:
        result = {'completeC': False, 'completeD': False, 'errors': []}
    result['buildStages'] = stages
    result['errors'].extend(errors)
    result.update(scope=CAMPAIGN_SCOPE, NIEWYKONANE=UNEXECUTED)
    result['code'] = int(not campaign_complete(result) or not result['completeC'] or not result['completeD'])
    if result['code']:
        result['status'] = 'FAIL'
    save(out / 'campaign.json', result)
    (out / 'PODSUMOWANIE.md').write_text(
        '# ' + CAMPAIGN_SCOPE + '\n\nStatus: ' + result['status'] + '\n\n' +
        CAMPAIGN_SCOPE + '\n\nNIEWYKONANE: ' + ', '.join(UNEXECUTED) + '\n\n' +
        f'C complete: {result['completeC']}; D complete: {result['completeD']}; diagnozy: {len(result['errors'])}.\n',
        encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--c0', type=Path)
    p.add_argument('--c1', type=Path)
    p.add_argument('--d', type=Path)
    p.add_argument('--instrumented', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--freeze', action='store_true')
    p.add_argument('--frozen', type=Path)
    p.add_argument('--pilot-only', action='store_true')
    p.add_argument('--duckc', type=Path)
    p.add_argument('--native-build', type=Path)
    p.add_argument('--source', type=Path, help='one-command C + native D + complete comparison')
    p.add_argument('--archive', type=Path, help='existing pinned official archive; never downloaded')
    p.add_argument('--work', type=Path)
    a = p.parse_args()
    if a.source:
        if not all((a.archive, a.work, a.frozen, a.out)):
            p.error('--source requires --archive --work --frozen --out')
        r = whole_campaign(a.source, a.archive, a.work, a.frozen, a.out)
        print(json.dumps({'status': r['status'], 'errors': len(r['errors']), 'completeC': r['completeC'], 'completeD': r['completeD']}))
        sys.exit(r['code'])
    elif a.duckc:
        print(json.dumps(compile_duckling(a.duckc, a.native_build)))
    else:
        if not a.c0 or not a.c1 or not a.out:
            p.error('--c0 --c1 --out are required')
        a.out.mkdir(parents=True, exist_ok=True)
        pilot(a.c0, a.c1, a.out, a.d)
        if not a.pilot_only:
            r = campaign(a.c0, a.c1, a.out, a.frozen, a.d, a.freeze, a.instrumented)
            print(json.dumps({'status': r['status'], 'errors': len(r['errors']), 'completeC': r['completeC'], 'completeD': r['completeD']}))
            sys.exit(bool(r['errors']) or not campaign_complete(r, bool(a.d)))
