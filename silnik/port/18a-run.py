pass                                                                         

                                                                              
                                                                            
   
import argparse
from collections import Counter
import gzip
import io
import json
import os
from pathlib import Path
try:
    import resource
except ImportError:
    resource = None
import signal
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

import zapytania18_tools as t

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SHA = '806f8a182643c4913c86a20f525a359098dabe80380d777a37feefd288058805'
SOURCES = ['geometry.c', 'distance.c', 'hull.c', 'math_functions.c', 'core.c']
FLAGS = ['-std=c17', '-O2', '-DNDEBUG', '-DB2_VALIDATE=0', '-DBOX2D_DISABLE_SIMD',
         '-fno-fast-math', '-ffp-contract=off']


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts)
    return {'files': len(files), 'directories': 1+sum(p.is_dir() for p in root.rglob('*') if '.git' not in p.relative_to(root).parts),
            'extensions': dict(Counter(p.suffix or '(none)' for p in files)),
            'byDirectory': dict(Counter(p.parent.relative_to(root).as_posix() for p in files)),
            'allFiles': [p.relative_to(root).as_posix() for p in files],
            'subtrees': dict(Counter(p.relative_to(root).parts[0] if len(p.relative_to(root).parts)>1 else '(root)' for p in files))}


def limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])


def rss_tree(pid):
    pass                                                                           
    total = 0
    pending = [pid]
    seen = set()
    while pending:
        current = pending.pop()
        if current in seen: continue
        seen.add(current)
        try:
            status = Path(f'/proc/{current}/status').read_text()
            rss = next((line for line in status.splitlines() if line.startswith('VmRSS:')), '')
            if rss: total += int(rss.split()[1])
            pending += list(map(int, Path(f'/proc/{current}/task/{current}/children').read_text().split()))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return total


class Campaign:
    def __init__(self, args):
        self.args = args
        self.out = args.out.resolve()
        self.build = args.build.resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.build.mkdir(parents=True, exist_ok=True)
        self.start = time.monotonic()
        self.stages = []
        self.processes = []
        self.meta = {'schema': '18A-RECEIPT-1', 'part': 'A', 'scope': 'C only' if args.c_only else 'C and D',
                     'compilerCommit': '2321f92c7a355ba95fa11e8afe28269b0d09cd69',
                     'countsRequired': {'DIRECT': 96, 'PUBLIC': 96, 'GUARD': 821, 'parserPairs': 24},
                     'complete': False, 'stages': self.stages, 'processes': self.processes}
        self.flush()

    def flush(self):
        self.meta['elapsedSeconds'] = time.monotonic()-self.start
        save(self.out/'receipt.json', self.meta)
        failures = [s for s in self.stages if s['code']]
        text = '# PORT18 A\n\n'
        text += 'RESULT: '+('INCOMPLETE / FAIL' if not self.meta['complete'] else 'OK zakresu pomiaru')+'\n\n'
        text += '\n'.join(f'- {s['name']}: {('OK' if s['code'] == 0 else 'FAIL')} — {s.get('diagnosis', '')}' for s in self.stages)+'\n'
        text += f'\ncomplete: {str(self.meta['complete']).lower()}; niezrealizowane: {self.meta.get('unexecuted', [])}\n'
        (self.out/'PODSUMOWANIE.md').write_text(text, encoding='utf-8')

    def stage(self, name, fn):
        start = time.monotonic()
        s = {'name': name, 'code': 1}
        try:
            s['measurement'] = fn()
            s['code'] = 0
        except Exception as e:
            s['diagnosis'] = f'{type(e).__name__}: {e}'[:65536]
        s['seconds'] = time.monotonic()-start
        self.stages.append(s)
        self.flush()
        print(name, 'OK' if s['code']==0 else s['diagnosis'], flush=True)
        return s['code']==0

    def run(self, name, argv, inp=None, seconds=30, cwd=None, env=None, compilation=False):
        remaining = 600-(time.monotonic()-self.start)
        ram_kib = (2 if compilation else 1)*1024**2
        if remaining <= 0:
            raise TimeoutError('whole 18a campaign limit 600 seconds')
        stdout, stderr = self.build/(name+'.stdout'), self.build/(name+'.stderr')
        start = time.monotonic()
        metrics = self.build/(name+'.time')
        input_path = self.build/(name+'.stdin')
        if inp is not None:
            input_path.write_bytes(inp)
                                                                                 
        command = ['/usr/bin/time', '-f', '%M', '-o', str(metrics), *map(str, argv)]
        timed_out = memory_exceeded = output_exceeded = False
        group_peak = 0
                                                                               
                                                                             
                                                     
        with stdout.open('wb') as out, stderr.open('wb') as err,\
                (input_path if inp is not None else Path('/dev/null')).open('rb') as source:
            child = subprocess.Popen(command, stdin=source,
                                     stdout=out, stderr=err, cwd=ROOT if cwd is None else cwd, preexec_fn=limits, start_new_session=True,
                                     env=None if env is None else dict(os.environ, **env))
            deadline = start+min(seconds, remaining)
            while True:
                group_peak = max(group_peak, rss_tree(child.pid))
                memory_exceeded = ram_kib is not None and group_peak>ram_kib
                output_exceeded = stdout.stat().st_size>32*1024**2 or stderr.stat().st_size>16*1024**2
                timed_out = time.monotonic()>=deadline
                if memory_exceeded or timed_out or output_exceeded:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
                    break
                try:
                    child.wait(timeout=max(0.001, min(0.02, deadline-time.monotonic())))
                    break
                except subprocess.TimeoutExpired:
                    pass
        rss = metrics.read_text().strip().splitlines() if metrics.is_file() else []
        measurement = {'name': name, 'argv': list(map(str, argv)), 'code': child.returncode,
                       'seconds': time.monotonic()-start, 'stdoutBytes': stdout.stat().st_size,
                       'stderrBytes': stderr.stat().st_size, 'peakRssKiB': int(rss[-1]) if rss and rss[-1].isdigit() else None}
        measurement['sampledProcessTreePeakRssKiB'] = group_peak
        measurement['profile'] = '18a-compilation' if compilation else '18a-execution'
        measurement['ramLimitKiB'] = ram_kib
        self.processes.append(measurement)
        if timed_out:
            raise TimeoutError(name+': killed complete owned process group after deadline')
        if memory_exceeded or ram_kib is not None and (measurement['peakRssKiB'] or 0)>ram_kib:
            raise MemoryError(name+f': resident memory limit {ram_kib}KiB exceeded')
        if output_exceeded or stdout.stat().st_size > 32*1024**2 or stderr.stat().st_size > 16*1024**2:
            raise ValueError('output/log size limit exceeded')
        return child.returncode, stdout, stderr

    def build_c(self, variant):
        dest = self.build/variant
        dest.mkdir(exist_ok=True)
        b = self.args.box2d.resolve()
        flags = FLAGS.copy()+['-I'+str(b/'include'), '-I'+str(b/'src')]
        if variant.startswith('gcov'):
            flags += ['--coverage']
        if variant == 'gcov-noinline':
            flags += ['-fno-inline', '-fno-inline-functions', '-fno-inline-small-functions']
        objects = []
        for source in [t.HERE/'kontrola-zapytania.c', *[b/'src'/s for s in SOURCES]]:
            obj = dest/(source.stem+'.o')
            own_flags = ['-Wall', '-Wextra', '-Werror'] if source.name=='kontrola-zapytania.c' else []
            code, out, err = self.run(variant+'-'+source.stem, ['gcc', *flags, *own_flags,
                '-DOBSERVE18='+('0' if variant=='c0' else '1'), '-c', source, '-o', obj], seconds=180, compilation=True)
            if code:
                raise ValueError(err.read_text()[:16000])
            objects.append(obj)
        binary = dest/'kontrola-zapytania'
        code, out, err = self.run(variant+'-link', ['gcc', *objects, *(['--coverage'] if variant.startswith('gcov') else []), '-lm', '-o', binary], seconds=180, compilation=True)
        if code:
            raise ValueError(err.read_text()[:16000])
        self.meta.setdefault('binaries', {})[variant] = {'path': str(binary), 'sha256': t.digest(binary)}
        return self.meta['binaries'][variant]

    def build_d(self):
        if not (t.HERE/'zapytania.dk').is_file() or not (ROOT/'silnik/fizyka/zapytania.dk').is_file():
            raise FileNotFoundError('real K18a product/transport not yet supplied; no substitute D')
        archive = self.args.archive.resolve()
        if t.digest(archive) != OFFICIAL_SHA:
            raise ValueError('official compiler archive SHA mismatch')
        self.meta['archiveSHA256'] = t.digest(archive)
        compiler_dir = self.build/'compiler'
        compiler_dir.mkdir(exist_ok=True)
        with tarfile.open(archive, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.issym() or member.islnk() or not (compiler_dir/member.name).resolve().is_relative_to(compiler_dir):
                    raise ValueError('compiler archive unsafe path/link')
            tar.extractall(compiler_dir, filter='data')
        candidates = list(compiler_dir.rglob('duckc'))
        if len(candidates)!=1:
            raise ValueError('one compiler binary required')
        duckc = candidates[0]
        self.meta['duckcSHA256'] = t.digest(duckc)
        code, out, err = self.run('duckling-version', [duckc, '--version-verbose'])
        version = out.read_text()+err.read_text()
        if code or '2321f92c' not in version:
            raise ValueError('compiler version does not match frozen 2321f92c')
        self.meta['compilerVersion'] = version
        artifact = self.build/'duck-artifacts'
        binary = artifact/'zapytania-bin'
        library = artifact/'libfizyka.a'
        package = {'packages': [{'id': 'fizyka', 'name': 'fizyka', 'path': str(ROOT/'silnik/fizyka')},
                                {'id': 'zapytania', 'name': 'zapytania', 'path': str(t.HERE/'zapytania.dk'), 'dependencies': [{'id': 'fizyka'}]}],
                   'tasks': [{'package': 'fizyka', 'strategy': 'lib', 'output_file': library.name},
                             {'package': 'zapytania', 'strategy': 'native', 'output_file': binary.name,
                              'linking_options': {'additional_link_options': [str(library), '-lm'], 'link_c_standard_library': True}}]}
        config = self.build/'packages18a.json'
        save(config, package)
        code, out, err = self.run('duckling-build', [duckc, 'compile_packages', config, '-a', artifact, '-O', '0', '-w', '8'], seconds=180, compilation=True)
        if code or not binary.is_file():
            raise ValueError('D compilation failed: '+err.read_text()[:16000]+out.read_text()[-4000:])
        self.meta.setdefault('binaries', {})['d'] = {'path': str(binary), 'sha256': t.digest(binary)}
        return self.meta['binaries']['d']

    def check(self, variant, profile):
        side = 'D' if variant=='d' else 'C'
        binary = self.meta['binaries'][variant]['path']
        inp = t.emit(profile, side, self.data).encode('ascii')
        self.meta.setdefault('inputs', {})[profile+side] = {'sha256': __import__('hashlib').sha256(inp).hexdigest(), 'bytes': len(inp)}
        code, out, err = self.run(variant+'-'+profile, [binary], inp)
        if code or err.stat().st_size:
            raise ValueError(f'exit={code}; stderr={err.read_text()[:4000]}')
        with out.open(encoding='ascii', newline='') as stream:
            result = t.compare(stream, t.expected(profile, self.data, observe=variant!='c0'))
        result['cases'] = 821 if profile=='GUARD' else 96
        result['operations'] = {'DIRECT': 96, 'PUBLIC': 768, 'GUARD': 1642}[profile]
        return result

    def parsers(self, variant):
        side = 'D' if variant=='d' else 'C'
        binary = self.meta['binaries'][variant]['path']
        failures = []
        for p in self.data['parsers']:
            for positive in [False, True]:
                key = ('positive' if positive else 'input')+side
                argv = [binary, *p['positiveArguments' if positive else 'arguments']]
                code, out, err = self.run(f'{variant}-parser{p['id']}-{positive}', argv, p[key].encode('utf-8'))
                wanted = p['positiveStdout' if positive else 'stdoutBeforeError']
                if variant=='c0':
                    wanted = ''.join(x for x in wanted.splitlines(keepends=True) if not x.startswith('I18 '))
                error = '' if positive else p['stderr']
                if code != (0 if positive else 2) or out.read_bytes()!=wanted.encode() or err.read_bytes()!=error.encode():
                    failures.append({'id': p['id'], 'positive': positive, 'code': code,
                                     'stderr': err.read_text()[:1000], 'stdout': out.read_text()[:2000]})
        if failures:
            save(self.out/(variant+'-parser-errors.json'), failures)
            raise ValueError(json.dumps(failures)[:12000])
                                                                             
        p = self.data['parsers'][0]
        for mode, inp in [('CRLF', p['positive'+side].replace('\n', '\r\n')), ('EOF', p['positive'+side].rstrip('\n'))]:
            code, out, err = self.run(variant+'-endings-'+mode, [binary, '--diagnostic'], inp.encode())
            wanted = p['positiveStdout']
            if variant=='c0': wanted=''.join(x for x in wanted.splitlines(keepends=True) if not x.startswith('I18 '))
            if code or err.stat().st_size or out.read_bytes()!=wanted.encode():
                raise ValueError('line ending/EOF '+mode)
        return {'negative': 24, 'positive': 24, 'lineEndingsAndEOF': 2}

    def sample(self, variant):
        example = self.data['examples'][0]
        side = 'D' if variant=='d' else 'C'
        code, out, err = self.run(variant+'-sample', [self.meta['binaries'][variant]['path'], '--diagnostic'], t.example_input(example, side).encode())
        if code or err.stat().st_size:
            raise ValueError('original sample exit/stderr')
        wanted = t.example_expected(example)
        if variant=='c0': wanted=[x for x in wanted if not x.startswith('I18 ')]
        with out.open(encoding='ascii', newline='') as stream:
            return t.compare(stream, wanted)

    def pilot(self, variant):
        pass                                                                       
        binary = self.meta['binaries'][variant]['path']
        side = 'D' if variant=='d' else 'C'
        measures = []
        for kind in range(13):
            rows = [r for r in self.data['direct'] if r['kind']==kind]
            lines = [f'PORT18 A DIRECT {len(rows)}\n']
            for row in rows:
                w = row['payloadH'] if side=='C' else [str(int(h,16)) for h in row['payloadH']]
                lines += [f'C {row['id']} 1\n', f'O 1 500 {len(w)} '+ ' '.join(w)+'\n']
            code, out, err = self.run(variant+'-pilot-kind'+str(kind), [binary, '--diagnostic'], ''.join(lines).encode())
            if code or err.stat().st_size: raise ValueError('pilot family '+str(kind)+': '+err.read_text()[:1000])
            subset = dict(self.data, direct=rows)
            with out.open(encoding='ascii', newline='') as stream:
                t.compare(stream, t.expected('DIRECT', subset, observe=variant!='c0'))
            measures.append(self.processes[-1])
        for profile in ['PUBLIC', 'GUARD']:
            self.check(variant, profile)
            measures.append(self.processes[-1])
                                                                                 
        self.parsers(variant)
        self.sample(variant)
        measures.append(self.processes[-1])
        parser_runs = [x for x in self.processes if x['name'].startswith(variant+'-parser')]
        measured = sum(x['seconds'] for x in measures+parser_runs)
        result = {'families': measures, 'parserPairs': 24, 'seconds': measured,
                  'forecast2xSeconds': 2*measured, 'limitsUnchanged': True}
        if 2*measured>600: raise ValueError('pilot forecast2x exceeds frozen 600s')
        save(self.out/(variant+'-pilot.json'), result)
        return result

    def gcov(self, variant):
        outputs = []
        dest = self.build/variant
        for source in SOURCES:
            code, out, err = self.run('export-'+variant+'-'+source, ['gcov', '-j', '-b', '-c', dest/(Path(source).stem+'.gcno')], cwd=dest)
            if code:
                raise ValueError(err.read_text()[:2000])
            outputs += list(dest.glob(Path(source).stem+'.gcov.json.gz'))
        for path in set(outputs):
            shutil.copy2(path, self.out/(variant+'-'+path.name))
        if len(set(outputs))!=len(SOURCES):
            raise ValueError('incomplete gcov files')
        return {'files': sorted(p.name for p in set(outputs)), 'neutrality': 'all full transcripts compared to F18A'}

    def additional(self, variant):
        packet=json.loads(self.args.additional.read_text(encoding='utf-8'))
        data=t.additional_data(packet,self.data)
        side='D' if variant=='d' else 'C'
        results={}
        for profile in ['DIRECT','PUBLIC']:
            inp=t.additional_input(packet,profile,side).encode('ascii')
            code,out,err=self.run(variant+'-N18A-'+profile,[self.meta['binaries'][variant]['path'],'--diagnostic'],inp)
            if code or err.stat().st_size: raise ValueError('N18A exit/stderr: '+err.read_text()[:2000])
            with out.open(encoding='ascii',newline='') as stream:
                results[profile]=t.compare(stream,t.expected(profile,data[profile],observe=variant!='c0'))
        self.meta['additionalPacketSHA256']=t.digest(self.args.additional)
        return {'cases':len(packet['direct']),'results':results,'sha256':t.digest(self.args.additional)}

    def source(self):
        self.data = t.manifest()
        b = self.args.box2d.resolve()
        inv = inventory(b)
        save(self.out/'source-inventory.json', inv)
        source_pins = json.loads((t.HERE/'18-zrodlo-sumy.json').read_text())['files']
        for name, wanted in source_pins.items():
            if t.digest(b/name)!=wanted:
                raise ValueError('Box2D hash mismatch '+name)
        self.meta['sourceCommit'] = self.data['sourceCommit']
        self.meta['sourceHashes'] = source_pins
        files = [*sorted((ROOT/'silnik/fizyka').glob('*.dk')),
                 *sorted(p for p in t.HERE.iterdir() if p.suffix in ('.c','.h','.py','.json','.dk')),
                 ROOT/'.github/workflows/port18.yml', ROOT/'.github/workflows/port.yml']
        if (t.HERE/'zapytania.dk').exists(): files.append(t.HERE/'zapytania.dk')
        self.meta['apparatusAndProductSHA256'] = {p.relative_to(ROOT).as_posix(): t.digest(p) for p in files}
        return {'sourceHashesMatched': len(source_pins), 'inventory': inv}

    def all(self):
        if not self.stage('source', self.source):
            self.meta['unexecuted']=['native: invalid source/specification']; self.flush(); return 1
        variants = ['c0', 'c1', 'gcov']+(['gcov-noinline'] if self.args.no_inline else [])
        for v in variants:
            self.stage('build-'+v, lambda v=v: self.build_c(v))
        if not self.args.c_only:
            self.stage('build-d', self.build_d)
            variants.append('d')
        if self.args.build_only:
            self.meta['unexecuted']=['all executions: --build-only']; self.flush(); return int(any(s['code'] for s in self.stages))
        for v in variants:
            if v not in self.meta.get('binaries', {}):
                self.meta.setdefault('unexecuted', []).append(v+': build failed'); continue
            if not self.stage(v+'-pilot', lambda v=v: self.pilot(v)):
                self.meta.setdefault('unexecuted', []).append(v+': full turn withheld after pilot failure'); continue
            for p in ['DIRECT', 'PUBLIC', 'GUARD']:
                self.stage(v+'-'+p, lambda v=v,p=p: self.check(v,p))
            self.stage(v+'-parser24', lambda v=v: self.parsers(v))
            self.stage(v+'-sample', lambda v=v: self.sample(v))
            if self.args.additional:
                self.stage(v+'-N18A', lambda v=v: self.additional(v))
            if v.startswith('gcov'):
                self.stage(v+'-export', lambda v=v: self.gcov(v))
                                                                                  
        executions = [x for x in self.processes if any(x['name'].endswith('-'+p) for p in ['DIRECT','PUBLIC','GUARD','sample'])]
        save(self.out/'pilot.json', {'measurements': executions, 'fullMeasuredSeconds': sum(x['seconds'] for x in executions),
                                    'forecast2xSeconds': 2*sum(x['seconds'] for x in executions),
                                    'limits': {'compileSeconds': 180, 'inputSeconds': 30, 'campaignSeconds': 600, 'compileRamBytes': 2*1024**3, 'executionRamBytes': 1024**3}})
        self.meta['unexecuted'] = self.meta.get('unexecuted', [])+(['D omitted by --c-only'] if self.args.c_only else [])
        if (t.HERE/'18a-N-propozycja.json').is_file() and not self.args.additional:
            self.meta['unexecuted'].append('Additional packet is not selected')
        self.meta['complete'] = not self.meta['unexecuted'] and not any(s['code'] for s in self.stages)
        self.meta['completeC'] = not any(s['code'] for s in self.stages if s['name']!='build-d' and not s['name'].startswith('d-'))
        self.flush()
        return int(not self.meta['completeC'] if self.args.c_only else not self.meta['complete'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--box2d', type=Path, required=True)
    parser.add_argument('--archive', type=Path, default=Path.home()/'duckling/duckling-dev-linux-x86_64.tar.gz')
    parser.add_argument('--build', type=Path, default=ROOT/'build18a')
    parser.add_argument('--out', type=Path, default=ROOT/'wyniki18a')
    parser.add_argument('--c-only', action='store_true')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--no-inline', action='store_true')
    parser.add_argument('--additional', type=Path, help='Additional numeric query cases')
    args = parser.parse_args()
    if args.additional is None and (t.HERE/'18a-N-zamrozone.json').is_file():
        args.additional=t.HERE/'18a-N-zamrozone.json'
    if sys.platform!='linux' or str(ROOT).startswith('/mnt/'):
        parser.error('native build/comparison only in an assigned Linux filesystem copy')
    for p in [args.build, args.out]:
        if not p.resolve().is_relative_to(ROOT): parser.error('build/out must stay inside own copy')
    return Campaign(args).all()


if __name__ == '__main__':
    raise SystemExit(main())
