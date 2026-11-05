pass                                                                          
import argparse
import collections
import gzip
import importlib.util
import json
import os
from pathlib import Path
try:
    import resource
except ImportError:
    resource = None
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inputs = load('sensory_inputs', 'przypadki-sensory.py')
builder = load('sensory_builder', 'budowa-sensory.py')
compare = load('sensory_compare', 'porownaj-sensory.py')


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def archive(source, target):
    with source.open('rb') as src, target.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as dst:
            shutil.copyfileobj(src, dst, 65536)


def run_case(case, binaries, work, output, *, freeze):
    results, paths = [], []
    for obs in ('0', '1', '1plain'):
        stream = work/f'stream{obs}.bin'
        stdout = work/f'stdout{obs}.csv'
        stderr = work/f'stderr{obs}.csv'
        metrics = work/f'time{obs}.csv'
        command = ['/usr/bin/time', '-f', '%e %M', '-o', str(metrics),
                   binaries[obs]['path'], str(case['kind']), str(case['ordinal']), str(stream)]
        start = time.monotonic()
        with stdout.open('wb') as out, stderr.open('wb') as err:
            proc = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise
        if stdout.stat().st_size > 16*1024*1024 or stderr.stat().st_size > 65536:
            raise ValueError(f'{case['id']}: probe log bound exceeded')
        lines = stdout.read_text(encoding='ascii').splitlines()
        errors = stderr.read_text(encoding='ascii')
        elapsed, rss = metrics.read_text(encoding='ascii').splitlines()[-1].split()
        results.append({'command': command, 'exit': proc.returncode, 'stderr': errors,
                        'seconds': time.monotonic()-start,
                        'processSeconds': float(elapsed), 'processMaxRSSKiB': int(rss),
                        'childrenHighWaterKiB': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                        'rssScope': 'cumulative children high-water, including earlier build; not case RSS',
                        'lines': [x for x in lines if not x.startswith('BR ')],
                        'branches': [x for x in lines if x.startswith('BR ')]})
        paths.append(stream)
    measurement = compare.compare_files(*paths[:2])
    instrumentation = compare.compare_files(paths[1], paths[2])
    expected = case['expected']
    lines = expected.get('actualLines', expected.get('lines'))
    failures = []
    if not measurement['equal'] or not measurement['wordAligned']:
        failures.append('C18a C0/C1 full binary words differ')
    if not instrumentation['equal'] or results[1]['lines'] != results[2]['lines']:
        failures.append('C18a ordinary C1/gcov C1 differ')
    if measurement['bytes'] != [expected['streamBytes']]*2:
        failures.append('binary byte count differs from frozen C18a')
    if results[1]['lines'] != lines:
        failures.append('C1 diagnostics differ from frozen C18a')
    for result in results:
        if result['exit'] != 0 or result['stderr']:
            failures.append('probe exit/stderr')
    row = {'id': case['id'], 'family': case['family'], **measurement,
           'instrumentationNeutrality': instrumentation,
           'runs': results, 'failures': failures, 'passed': not failures}
    if freeze:
                                                                               
        target = output/f'{case['id']}.c18a.bin.gz'
        archive(paths[1], target)
        row['frozenStream'] = {'file': target.name, 'gzipSha256': builder.digest(target),
                               'bytes': target.stat().st_size}
        save(output/f'{case['id']}.json', row)
    for path in paths:
        path.unlink()
    return row


def run(source, work, output, jobs=4):
    work, output = Path(work).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = inputs.manifest()
    cases = list(inputs.c18a_cases(data))
    parser_rows = inputs.parser_inputs(data, output/'parser-inputs')
    guard_rows = inputs.guard_inputs(data, output/'guard-inputs')
    receipt = builder.build(source, work/'native', jobs=jobs)
    save(output/'build.json', receipt)
    start = time.monotonic()
                                                                               
    pilots = []
    seen = set()
    for case in cases:
        key = case['family']
        if key not in seen or case['id'] in ('D012', 'D016', 'EXTRA_LOCK001'):
            seen.add(key)
            pilots.append(run_case(case, receipt['binaries'], work, output, freeze=False))
    save(output/'pilot.json', pilots)
                                                                             
                                                                          
    for path in (work/'native').glob('c18a-*.gcda'):
        path.unlink()
    rows = []
    for case in cases:
        try:
            row = run_case(case, receipt['binaries'], work, output, freeze=True)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            row = {'id': case['id'], 'family': case['family'], 'passed': False,
                   'failures': [str(exc)]}
        rows.append(row)
    families = collections.defaultdict(lambda: {'cases': 0, 'bytes': 0, 'secondsC0': 0, 'secondsC1': 0})
    for row in rows:
        family = families[row['family']]
        family['cases'] += 1
        if 'runs' in row:
            family['bytes'] += row['bytes'][1]
            family['secondsC0'] += row['runs'][0]['seconds']
            family['secondsC1'] += row['runs'][1]['seconds']
    summary = {'stage': 'C18a replay, not PORT17', 'completePORT17': False,
               'cases': len(rows), 'passed': sum(x['passed'] for x in rows),
               'failed': [x['id'] for x in rows if not x['passed']],
               'pilotFailed': [x['id'] for x in pilots if not x['passed']],
               'seconds': time.monotonic()-start, 'families': dict(families),
               'frozenUncompressedBytes': sum(x.get('bytes', [0, 0])[1] for x in rows),
               'parserInputsMaterialized': len(parser_rows), 'parserExecutions': 0,
               'guardInputs': guard_rows, 'guardExecutions': 0,
               'unexecuted': {'PUBLIC_PORT17': 96, 'DIRECT_PORT17': 64, 'GUARD_PORT17': 697,
                              'parserPairs': 62, 'D': 'not supplied',
                              'BASE16B': 'PORT17 profile f73852bf; separate stage outside C18a replay',
                              'C0ProjectionC1': 'not the C18a binary equality'},
               'manifestSha256': inputs.MANIFEST_SHA, 'contractSha256': inputs.CONTRACT_SHA}
    save(output/'manifest.json', summary)
    (output/'PODSUMOWANIE.md').write_text(
        f'# C18a — odtworzenie oryginalu\n\nZgodne z zamrozonym C18a: {summary['passed']}/{len(rows)}. Bledy: {summary['failed']}.\n\ncompletePORT17=Efcbcf165908d. Ef4b06ef6d3c8 Ecd5b158f21b7 E35e99f929e01 Eabf985dcd515 E572b9094dd03 PORT17 E33dcc1a09b95 port Ee6b67ce8a51d. BASE16B, GUARD697, 62 pary parsera i C1=D pozostaja NIEURUCHOMIONE.\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--c18a-only', action='store_true')
    parser.add_argument('--base',type=Path,default=HERE)
    args = parser.parse_args()
    if not args.c18a_only:
        try:
            build17=load('sensory17_builder','budowa-sensory17.py')
            native17=load('sensory17_campaign','ci-sensory17.py')
            guard17=load('sensory17_guards','ci-sensory17-oslony.py')
            build17.build(args.source,args.work/'port17',args.base)
            ordinary=native17.run(args.work/'port17',args.output/'campaign',['PUBLIC','DIRECT'],jobs=args.jobs)
            guards=guard17.run(args.work/'port17',args.output/'guards')
            summary=dict(stage='PORT17 C',base='f73852bfadb7ce396e1cb52d7febfe9374b07724',completePORT17=False,
                ordinary={'cases':ordinary['cases'],'passed':ordinary['passed'],'failed':ordinary['failed']},
                parser=guards['parser'],guards={k:guards['guards'][k] for k in ('cases','phases','passed')},
                unexecuted=ordinary['unexecuted']+guards['unexecuted'],D='not supplied; frozen comparison command odbierz-sensory17.py')
            args.output.mkdir(parents=True,exist_ok=True);save(args.output/'manifest.json',summary)
            print(json.dumps(summary,indent=2));raise SystemExit(int(bool(ordinary['failed']) or guards['parser']['passed']!=124 or guards['guards']['passed']!=1390))
        except (OSError,subprocess.SubprocessError,ValueError,RuntimeError) as exc:
            args.output.mkdir(parents=True,exist_ok=True)
            save(args.output/'manifest.json',dict(stage='PORT17 setup/stage failed',completePORT17=False,error=str(exc)))
            print(str(exc),file=sys.stderr);raise SystemExit(2)
    try:
        summary = run(args.source, args.work, args.output, args.jobs)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        summary = {'stage': 'C18a setup/build failed', 'completePORT17': False,
                   'cases': 0, 'passed': 0, 'failed': ['setup/build'],
                   'pilotFailed': [], 'error': str(exc),
                   'unexecuted': 'all native stages; old files in output are not results of this attempt'}
        save(args.output/'manifest.json', summary)
        (args.output/'PODSUMOWANIE.md').write_text(
            '# C18a — blad przygotowania\n\ncompletePORT17=false.\n\n'+str(exc)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if args.c18a_only and not summary['failed'] and not summary['pilotFailed'] else 2)
