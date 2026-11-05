from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                                           
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
                                                                        
                                                                            
if __name__ == '__main__' and len(sys.argv)>1 and sys.argv[1].startswith('polaczenia-14a'):
    route=sys.argv[1]
    phase='all' if route=='polaczenia-14a' else route.removeprefix('polaczenia-14a-')
    spec14=importlib.util.spec_from_file_location('port_ci14',ROOT/'silnik/port/ci-polaczenia.py')
    ci14=importlib.util.module_from_spec(spec14);sys.modules[spec14.name]=ci14;spec14.loader.exec_module(ci14)
    sys.exit(ci14.stage(phase=phase))
spec = importlib.util.spec_from_file_location('silnik_proba_ci', ROOT / 'silnik/proba/ci.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OUT = base.OUT
base.CACHE = ROOT / '.port-cache'
base.PINS = {'box2d': base.PINS['box2d']}
base.OPTIONS = {'box2d': [option.replace('-DBOX2D_DISABLE_SIMD=OFF', '-DBOX2D_DISABLE_SIMD=ON')
                          for option in base.OPTIONS['box2d']]}
PORT = ROOT / 'silnik/port'


def c_side():
    (OUT / 'start-unix.csv').write_text(f'{time.time():.6f}\n', encoding='ascii')
                                                                                               
    sys.argv[1] = 'probe'
    (OUT / 'metadane.json').write_text(json.dumps({
        'box2d': base.PINS, 'options': base.OPTIONS,
        'cflags': '-fno-fast-math -ffp-contract=off', 'duckling_sha256': base.SHA,
        'duckling_commit': 'be929a1a49aa9938bc9d65caa0897b8dd855e8cf',
        'commit': os.environ.get('GITHUB_SHA'), 'run_id': os.environ.get('GITHUB_RUN_ID'),
        'attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
    }, indent=2) + '\n', encoding='utf-8')
    sources = [ROOT / '.github/workflows/port.yml', ROOT / 'silnik/proba/ci.py',
               *sorted(PORT.glob('*.py')), *sorted(PORT.glob('*.c')), *sorted(PORT.glob('fixtures/norms/KONTRAKT*.json')),
               *sorted(PORT.glob('fixtures/norms/PLAN-8*.json')), ROOT / 'fixtures/norms/KONTRAKT-8-DOPOWIEDZENIE.json',
               *sorted(PORT.glob('mutacje-*.json')),
               *sorted((ROOT / 'silnik/fizyka').rglob('*.dk')), *sorted(PORT.glob('*.dk'))]
    snapshot = OUT / 'zrodla'
    hashes = []
    for source in sources:
        relative = source.relative_to(ROOT)
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes.append(f'{hashlib.sha256(source.read_bytes()).hexdigest()}  {relative.as_posix()}\n')
    (OUT / 'zrodla-sha256.csv').write_text(''.join(hashes), encoding='ascii')
    base.need('generator', [sys.executable, '-B', PORT / 'przypadki.py', '--katalog', OUT])
    for name, command in (('system', ['uname', '-a']), ('cc-wersja', ['cc', '--version']),
                          ('cmake-wersja', ['cmake', '--version'])):
        base.need(name, command, seconds=10)
                                                                                                  
    base.build()
    executable = base.TEMP / 'kontrola-port'
    base.need('kontrola-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
        '-fno-fast-math', '-ffp-contract=off', '-I' + str(base.CACHE / 'box2d/include'),
        PORT / 'kontrola.c', base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', executable], seconds=30)
    base.need('kontrola', [executable, OUT / 'przypadki.csv'], stdout=OUT / 'c.csv', seconds=15)
    shutil.copy2(executable, OUT / 'kontrola-bin')
    polygon_executable = base.TEMP / 'kontrola-wiel'
    base.need('kontrola-wiel-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
        '-fno-fast-math', '-ffp-contract=off', '-I' + str(base.CACHE / 'box2d/include'),
        PORT / 'kontrola-wiel.c', base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', polygon_executable], seconds=30)
    base.need('generator-wiel', [sys.executable, '-B', PORT / 'przypadki-wiel.py',
        '--katalog', OUT, '--kontrola', polygon_executable], seconds=30)
    base.need('kontrola-wiel', [polygon_executable, OUT / 'przypadki-wiel.csv'],
              stdout=OUT / 'c-wiel.csv', seconds=15)
    shutil.copy2(polygon_executable, OUT / 'kontrola-wiel-bin')
    motion_executable = base.TEMP / 'kontrola-ruch'
    base.need('kontrola-ruch-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
        '-fno-fast-math', '-ffp-contract=off', '-I' + str(base.CACHE / 'box2d/include'),
        PORT / 'kontrola-ruch.c', base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', motion_executable], seconds=30)
    base.need('generator-ruch', [sys.executable, '-B', PORT / 'przypadki-ruch.py',
        '--katalog', OUT, '--kontrola', motion_executable], seconds=30)
    base.need('kontrola-ruch', [motion_executable, OUT / 'przypadki-ruch.csv'],
              stdout=OUT / 'c-ruch.csv', seconds=30)
    shutil.copy2(motion_executable, OUT / 'kontrola-ruch-bin')
    base.need('generator-drzewo', [sys.executable, '-B', PORT / 'przypadki-drzewo.py',
        '--katalog', OUT], seconds=15)
    tree_executable = base.TEMP / 'kontrola-drzewo'
    base.need('kontrola-drzewo-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
        '-fno-fast-math', '-ffp-contract=off', '-I' + str(base.CACHE / 'box2d/include'),
        PORT / 'kontrola-drzewo.c', base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', tree_executable], seconds=30)
    base.need('kontrola-drzewo', [tree_executable, OUT / 'przypadki-drzewo.csv'],
              stdout=OUT / 'c-drzewo.csv', seconds=30)
    shutil.copy2(tree_executable, OUT / 'kontrola-drzewo-bin')
    c_broad()


def prepare_box2d_sources():
                                                                                  
                                                         
    source = base.TEMP / 'box2d'
    if not (source / 'src/broad_phase.c').is_file():
        repo, commit = base.PINS['box2d']
        archive = base.TEMP / f'box2d-{commit}.tar.gz'
        source.mkdir(parents=True, exist_ok=True)
        base.need('szeroka-zrodla-pobranie', ['curl', '--fail', '--location', '--retry', '2',
            '--max-time', '45', f'https://codeload.github.com/{repo}/tar.gz/{commit}',
            '--output', archive], seconds=100)
        base.need('szeroka-zrodla', ['tar', '-xzf', archive, '--strip-components=1', '-C', source])
    files = sorted([*source.joinpath('src').glob('*.c'), *source.joinpath('src').glob('*.h'),
                    *source.joinpath('include/box2d').glob('*.h')])
    if len(files) != 63:
        raise base.StepFailed(f'Krok 5: niepelny zestaw oryginalu C/H: {len(files)} zamiast 63')
    sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(source).as_posix()}\n' for p in files)
    (OUT / 'box2d-szeroka-sha256.csv').write_text(sums, encoding='ascii')
                                                                               
    contract = norm_text(PORT / 'fixtures/norms/KONTRAKT-5.json')
    if any(line not in contract for line in sums.splitlines()):
        raise base.StepFailed('step 5: checksum Ebcfcaef2df6f E03f320064365 E7a3fe7501a2a E70f0b8e6e134 E32f30ea0e83c KONTRAKT-5')


def c_broad():
    prepare_box2d_sources()
    source = base.TEMP / 'box2d'
    base.need('generator-szeroka', [sys.executable, '-B', PORT / 'przypadki-szeroka.py', '--katalog', OUT], seconds=30)
                                                                               
                                                                            
    for suffix, trace in (('', '1'), ('-bez', '0')):
        name = 'kontrola-szeroka'+suffix
        executable = base.TEMP / name
        base.need(name+'-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
            '-DNDEBUG', '-DBOX2D_DISABLE_SIMD', '-DTRACE='+trace,
            '-fno-fast-math', '-ffp-contract=off', '-I'+str(source / 'include'), '-I'+str(source / 'src'),
            PORT / 'kontrola-szeroka.c', base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', executable], seconds=30)
        base.need(name, [executable, OUT / 'przypadki-szeroka.csv'], stdout=OUT / ('c-szeroka'+suffix+'.csv'), seconds=30)
        shutil.copy2(executable, OUT / (name+'-bin'))


def prepare_duckling_tools():
    pass                                                                   
    download = base.TEMP / 'pobranie'
    toolchain = base.TEMP / 'toolchain-port'
    download.mkdir(parents=True, exist_ok=True)
    toolchain.mkdir(parents=True, exist_ok=True)
    asset = 'duckling-dev-linux-x86_64.tar.gz'
    url = 'https://github.com/ducktype-org/duckling/releases/download/dev-weekly/'
                                                                                     
    if os.environ.get('ARCHIVE_CACHE_HIT') != 'true':
        for file in (asset, asset + '.sha256'):
            base.need('pobranie-' + file, ['curl', '--fail', '--location', '--retry', '2',
                '--retry-max-time', '80', '--max-time', '60', url + file, '--output', download / file], seconds=100)
    if (download / asset).stat().st_size != 81334394:
        raise base.StepFailed('ERROR ENV TOOLCHAIN: archive size differs from be929a1a')
    pinned = OUT / 'duckling-przypiete.sha256'
    pinned.write_text(f'{base.SHA}  {asset}\n', encoding='ascii')
    shutil.copy2(download / (asset + '.sha256'), OUT / (asset + '.sha256'))
    base.need('sha256-przypiete', ['sha256sum', '--check', pinned], cwd=download)
    base.need('sha256-sidecar-przypiete', ['sha256sum', '--check', asset + '.sha256'], cwd=download)
    base.need('archiwum-spis', ['tar', '-tzvf', download / asset])
    base.need('rozpakowanie', ['tar', '-xzf', download / asset, '-C', toolchain])
    tools = [p for p in toolchain.rglob('duckc') if p.is_file() and os.access(p, os.X_OK)]
    if len(tools) != 1:
        raise base.StepFailed(f'Oczekiwano jednego duckc: {tools}')
    duckc = tools[0]
    base.need('duckc-wersja', [duckc, '--version'], seconds=15)
    base.need('duckc-pakiet-pomoc', [duckc, 'compile_packages', '--help'], seconds=15)
    return duckc


def duckling_side():
    if not (PORT / 'kola.dk').is_file():
        message = 'missing port — E4a32c3c6b097 E95c0e17f48d9 C'
        print(message, flush=True)
        (OUT / 'brak-portu.csv').write_text(message + '\n', encoding='utf-8')
        (OUT / 'duckling.csv').write_text('', encoding='ascii')
        (OUT / 'duckling-kod.csv').write_text('125\n', encoding='ascii')
        return 0                                                                              
    sys.argv[1] = 'probe'
    duckc = prepare_duckling_tools()
    artifacts = base.TEMP / 'port-duck-build'
    artifacts.mkdir(exist_ok=True)
                                                                                        
    manifest = OUT / 'duckling-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka',
             'path': str(ROOT / 'silnik/fizyka/kola.dk')},
            {'id': 'kola', 'name': 'kola', 'path': str(PORT / 'kola.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'kola', 'strategy': 'native', 'output_file': 'kola',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2) + '\n', encoding='utf-8')
                                                                                  
    base.need('duckling-kompilacja', [duckc, 'compile_packages', manifest,
        '-a', artifacts, '-O', '0'], seconds=150)
    executables = []
    for path in artifacts.rglob('*'):
        if path.is_file() and os.access(path, os.X_OK):
            with path.open('rb') as stream:
                if stream.read(4) == b'\x7fELF':
                    executables.append(path)
    (OUT / 'pliki-natywne.csv').write_text(''.join(str(p) + '\n' for p in executables), encoding='utf-8')
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-bin')
    base.need('duckling', ['bash', '-c', 'exec "$1" < "$2"', 'port-stdin',
              executables[0], OUT / 'przypadki-stdin.csv'], stdout=OUT / 'duckling.csv', seconds=15)
    polygon_code = duckling_polygons(duckc)
    motion_code = duckling_motion(duckc)
    tree_code = duckling_tree(duckc)
    broad_code = duckling_broad(duckc)
    world_code = duckling_world(duckc)
    return polygon_code or motion_code or tree_code or broad_code or world_code


def previous_physics():
                                                                              
                                                                             
    source = ROOT / 'silnik/fizyka'
    names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk')
    extra = [p for p in source.rglob('*.dk') if p.relative_to(source).as_posix() not in names]
    if not extra:
        return source
                                                                            
    target = base.TEMP / 'kroki-1-3' / 'fizyka'
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        if (source / name).is_file():
            shutil.copy2(source / name, target / name)
    (OUT / 'fizyka-kroki-1-3.csv').write_text(
        'E17b022365622 1-3: E8ea20d7601da Ea82fc86cacf9 E5c749b70b331 E65f8dc81817e E283ada7088c2 E669673d4ce6c Ee49548d1b24b.\nstep 4: E79175f2d7303 E8ea20d7601da E4bcb97f09bb0 E65f8dc81817e E2f2457405c54. E4c2b8bbff702 Ee6f723fb7925 Ede7d1b721a1e E2080b1d8e359.\nModuly poza krokami 1-3:\n'+''.join(str(p.relative_to(ROOT))+'\n' for p in extra), encoding='utf-8')
    return target


def duckling_polygons(duckc):
                                                                          
    (OUT / 'duckling-wiel.csv').write_text('', encoding='ascii')
    (OUT / 'duckling-wiel-kod.csv').write_text('125\n', encoding='ascii')
    missing = [p for p in (PORT / 'wielokaty.dk', ROOT / 'silnik/fizyka/fizyka.dk',
                           ROOT / 'silnik/fizyka/wielokaty.dk') if not p.is_file()]
    if missing:
        message = 'missing port Ec3f183a85574: ' + ', '.join(str(p.relative_to(ROOT)) for p in missing)
        print(message, flush=True)
        (OUT / 'brak-portu-wiel.csv').write_text(message+'\n', encoding='utf-8')
        return 1
    artifacts = base.TEMP / 'port-wiel-duck-build'
    artifacts.mkdir(exist_ok=True)
    physics = previous_physics()
    manifest = OUT / 'duckling-wiel-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(physics)},
            {'id': 'wielokaty', 'name': 'wielokaty', 'path': str(PORT / 'wielokaty.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'wielokaty', 'strategy': 'native', 'output_file': 'wielokaty',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2)+'\n', encoding='utf-8')
    code = base.run('duckling-wiel-kompilacja', [duckc, 'compile_packages', manifest,
                   '-a', artifacts, '-O', '0'], seconds=150)
    if code:
        message = (f'E72e9a59f5a1d Ec3f183a85574 Ecd5b158f21b7 E81c44bfabb26 E70f0b8e6e134 (code {code}); E6ca5837c8c3d E360e5aa9cc7f Ea36c0cd8ffd0 E282b94cc1bb1 E2f2457405c54, E6fe2a0f5118f E2016d624afef.E867b4bf4357a. Ef4bee879fc24 Edaaf5582b890 E22aa16649c84 E13b1e13bb5ff E08a2a7517c79 Ede7d1b721a1e E2016d624afef; E5ac741c22156 Ecd6edd571098 E9676b21cd39e.E867b4bf4357a E22aa16649c84 E13b1e13bb5ff E03b382aabe85 three ports. circles have separate manifest file.')
        print(message, flush=True)
        (OUT / 'blad-portu-wiel.csv').write_text(message+'\n', encoding='utf-8')
        return code
    executables = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                   and p.read_bytes()[:4] == b'\x7fELF']
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF wielokatow: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-wiel-bin')
    return base.run('duckling-wiel', ['bash', '-c', 'exec "$1" < "$2"', 'port2-stdin',
                    executables[0], OUT / 'przypadki-wiel-stdin.csv'],
                    stdout=OUT / 'duckling-wiel.csv', seconds=15)


def duckling_motion(duckc):
                                                                                     
    (OUT / 'duckling-ruch.csv').write_text('', encoding='ascii')
    (OUT / 'duckling-ruch-kod.csv').write_text('125\n', encoding='ascii')
    missing = [p for p in (PORT / 'ruch.dk', ROOT / 'silnik/fizyka/fizyka.dk',
                           ROOT / 'silnik/fizyka/ruch.dk') if not p.is_file()]
    if missing:
        message = 'missing port motion: ' + ', '.join(str(p.relative_to(ROOT)) for p in missing)
        print(message, flush=True)
        (OUT / 'brak-portu-ruch.csv').write_text(message+'\n', encoding='utf-8')
        return 1
    artifacts = base.TEMP / 'port-ruch-duck-build'
    artifacts.mkdir(exist_ok=True)
    physics = previous_physics()
    manifest = OUT / 'duckling-ruch-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(physics)},
            {'id': 'ruch', 'name': 'ruch', 'path': str(PORT / 'ruch.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'ruch', 'strategy': 'native', 'output_file': 'ruch',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2)+'\n', encoding='utf-8')
    code = base.run('duckling-ruch-kompilacja', [duckc, 'compile_packages', manifest,
                   '-a', artifacts, '-O', '0'], seconds=150)
    if code:
        message = (f'E72e9a59f5a1d motion Ecd5b158f21b7 E81c44bfabb26 E70f0b8e6e134 (code {code}); Eab3f151cdcce E428c9140f6d7 E2f2457405c54 E35e99f929e01 E54ccc6038f6e z Ebc91c2b22f8f. Ef4bee879fc24 Edaaf5582b890 Ecd5b158f21b7 E35e99f929e01 E04e634fb22eb; Ea1d3e01a0b2c E4a32c3c6b097 E2080b1d8e359 E8b45e91521c3, E1a65254ca5e8 Efe660d905c1c E82d4e79cff82 Ea352cd1d82a0. Ef4bee879fc24 Ecd6edd571098 E9676b21cd39e.E867b4bf4357a E22aa16649c84 E13b1e13bb5ff E03b382aabe85 three ports.')
        print(message, flush=True)
        (OUT / 'blad-portu-ruch.csv').write_text(message+'\n', encoding='utf-8')
        return code
    executables = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                   and p.read_bytes()[:4] == b'\x7fELF']
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF motion: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-ruch-bin')
    return base.run('duckling-ruch', ['bash', '-c', 'exec "$1" < "$2"', 'port3-stdin',
                    executables[0], OUT / 'przypadki-ruch-stdin.csv'],
                    stdout=OUT / 'duckling-ruch.csv', seconds=30)


def duckling_tree(duckc):
    (OUT / 'duckling-drzewo.csv').write_text('', encoding='ascii')
    (OUT / 'duckling-drzewo-kod.csv').write_text('125\n', encoding='ascii')
    missing = [p for p in (PORT / 'drzewo.dk', ROOT / 'silnik/fizyka/fizyka.dk',
                           ROOT / 'silnik/fizyka/drzewo.dk') if not p.is_file()]
    if missing:
        message = 'missing port E930e79f4d2d2: ' + ', '.join(str(p.relative_to(ROOT)) for p in missing)
        print(message, flush=True)
        (OUT / 'brak-portu-drzewo.csv').write_text(message+'\n', encoding='utf-8')
        return 1
    artifacts = base.TEMP / 'port-drzewo-duck-build'
    artifacts.mkdir(exist_ok=True)
    manifest = OUT / 'duckling-drzewo-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(tree_physics())},
            {'id': 'drzewo', 'name': 'drzewo', 'path': str(PORT / 'drzewo.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'drzewo', 'strategy': 'native', 'output_file': 'drzewo',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2)+'\n', encoding='utf-8')
    code = base.run('duckling-drzewo-kompilacja', [duckc, 'compile_packages', manifest,
                   '-a', artifacts, '-O', '0'], seconds=150)
    if code:
        message = (f'E72e9a59f5a1d E930e79f4d2d2 Ecd5b158f21b7 E81c44bfabb26 E70f0b8e6e134 (code {code}); missing E33d277cf0ef5 = 125, Ebc2e4bea2e33 E74b62e088ba2. Ebcd8b38e500d Ef642974cfcb1, Ec3f183a85574 Ede7d1b721a1e motion E631f494748f8; E3605589eca62 1-3 E2e29135f4e2b E283ada7088c2 E036a8a704eee E65f8dc81817e E930e79f4d2d2.')
        print(message, flush=True)
        (OUT / 'blad-portu-drzewo.csv').write_text(message+'\n', encoding='utf-8')
        return code
    executables = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                   and p.read_bytes()[:4] == b'\x7fELF']
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF drzewa: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-drzewo-bin')
    return base.run('duckling-drzewo', ['bash', '-c', 'exec "$1" < "$2"', 'port4-stdin',
                    executables[0], OUT / 'przypadki-drzewo-stdin.csv'],
                    stdout=OUT / 'duckling-drzewo.csv', seconds=30)


def tree_physics():
                                                                        
                                                              
    source = ROOT / 'silnik/fizyka'
    names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk', 'drzewo.dk')
    extra = [p for p in source.rglob('*.dk') if p.relative_to(source).as_posix() not in names]
    if not extra:
        return source
    target = base.TEMP / 'kroki-1-4' / 'fizyka'
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        if (source / name).is_file():
            shutil.copy2(source / name, target / name)
    (OUT / 'fizyka-kroki-1-4.csv').write_text(
        'step 4: E8ea20d7601da E4bcb97f09bb0 E65f8dc81817e E283ada7088c2 E669673d4ce6c Ee49548d1b24b, E283ada7088c2 E65f8dc81817e E434f66e44101 5.\n'
        + ''.join(str(p.relative_to(ROOT))+'\n' for p in extra), encoding='utf-8')
    return target


def duckling_broad(duckc):
    (OUT / 'duckling-szeroka.csv').write_text('', encoding='ascii')
    (OUT / 'duckling-szeroka-kod.csv').write_text('125\n', encoding='ascii')
    missing = [p for p in (PORT / 'szeroka.dk', ROOT / 'silnik/fizyka/fizyka.dk') if not p.is_file()]
    if missing:
        message = 'missing port broad phase: '+', '.join(str(p.relative_to(ROOT)) for p in missing)
        print(message, flush=True)
        (OUT / 'brak-portu-szeroka.csv').write_text(message+'\n', encoding='utf-8')
        return 1
    artifacts = base.TEMP / 'port-szeroka-duck-build'
    artifacts.mkdir(exist_ok=True)
    manifest = OUT / 'duckling-szeroka-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(broad_physics())},
            {'id': 'szeroka', 'name': 'szeroka', 'path': str(PORT / 'szeroka.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'szeroka', 'strategy': 'native', 'output_file': 'szeroka',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2)+'\n', encoding='utf-8')
    code = base.run('duckling-szeroka-kompilacja', [duckc, 'compile_packages', manifest,
                   '-a', artifacts, '-O', '0'], seconds=150)
    if code:
        message = f'E72e9a59f5a1d broad phase Ecd5b158f21b7 E81c44bfabb26 E70f0b8e6e134 (code {code}); missing E33d277cf0ef5 = 125, Ebc2e4bea2e33 E74b62e088ba2.'
        print(message, flush=True)
        (OUT / 'blad-portu-szeroka.csv').write_text(message+'\n', encoding='utf-8')
        return code
    executables = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                   and p.read_bytes()[:4] == b'\x7fELF']
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF broad phase: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-szeroka-bin')
    return base.run('duckling-szeroka', ['bash', '-c', 'exec "$1" < "$2"', 'port5-stdin',
                    executables[0], OUT / 'przypadki-szeroka-stdin.csv'],
                    stdout=OUT / 'duckling-szeroka.csv', seconds=30)


def broad_physics():
                                                                          
    source = ROOT / 'silnik/fizyka'
    names = ('fizyka.dk', 'kola.dk', 'wielokaty.dk', 'ruch.dk', 'drzewo.dk', 'szeroka.dk', 'zbior.dk')
    extra = [p for p in source.rglob('*.dk') if p.relative_to(source).as_posix() not in names]
    if not extra:
        return source
    target = base.TEMP / 'kroki-1-5' / 'fizyka'
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        if (source / name).is_file():
            shutil.copy2(source / name, target / name)
    (OUT / 'fizyka-kroki-1-5.csv').write_text(
        'step 5: E8ea20d7601da E6618ffa16a3d E65f8dc81817e E283ada7088c2 E669673d4ce6c Ee49548d1b24b, E283ada7088c2 E65f8dc81817e E434f66e44101 6.\n'
        + ''.join(str(p.relative_to(ROOT))+'\n' for p in extra), encoding='utf-8')
    return target


def c_world():
                                                                      
    sys.argv[1] = 'probe'                                                        
    base.need('generator-swiat', [sys.executable, '-B', PORT / 'przypadki-swiat.py', '--katalog', OUT], seconds=30)
    source = base.TEMP / 'box2d'
    files = sorted([*source.joinpath('src').glob('*.c'), *source.joinpath('src').glob('*.h'),
                    *source.joinpath('include/box2d').glob('*.h')])
    if len(files) != 63:
        raise base.StepFailed(f'Krok 6: niepelny oryginal C/H: {len(files)} zamiast 63')
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    sums = ''.join(f'{digest}  {p.relative_to(source).as_posix()}\n' for p, digest in before.items())
    (OUT / 'box2d-swiat-sha256.csv').write_text(sums, encoding='ascii')
    contract = norm_text(PORT / 'fixtures/norms/KONTRAKT-6.json')
    if any(line not in contract for line in sums.splitlines()):
        raise base.StepFailed('step 6: checksum E5dd583469d69 E7a3fe7501a2a E70f0b8e6e134 E32f30ea0e83c KONTRAKT-6')
    executable = base.TEMP / 'kontrola-swiat'
    base.need('kontrola-swiat-kompilacja', ['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
        '-DNDEBUG', '-DBOX2D_DISABLE_SIMD', '-fno-fast-math', '-ffp-contract=off',
        '-I'+str(source / 'include'), PORT / 'kontrola-swiat.c',
        base.CACHE / 'box2d/lib/libbox2d.a', '-lm', '-o', executable], seconds=30)
    shutil.copy2(executable, OUT / 'kontrola-swiat-bin')
    base.need('kontrola-swiat-bilety', [executable, '--test-tickets'], stdout=OUT / 'c-swiat-bilety.csv', seconds=15)
    if (OUT / 'c-swiat-bilety.csv').read_text(encoding='ascii') != 'TICKETS OK\n':
        raise base.StepFailed('step 6: E0efdce0533cc Ebc2e4bea2e33 Ecb2499512837 u64 E838a24f46c85 C')
    base.need('kontrola-swiat', [executable, OUT / 'przypadki-swiat-pelne.csv'], stdout=OUT / 'c-swiat.csv', seconds=30)
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != digest for p, digest in before.items()):
        raise base.StepFailed('Krok 6: oryginal zmieniony podczas budowy / wykonania')


def duckling_world(duckc):
    (OUT / 'duckling-swiat.csv').write_text('', encoding='ascii')
    (OUT / 'duckling-swiat-kod.csv').write_text('125\n', encoding='ascii')
    missing = [p for p in (PORT / 'swiat.dk', ROOT / 'silnik/fizyka/swiat.dk',
                           ROOT / 'silnik/fizyka/gra.dk') if not p.is_file()]
    if missing:
        message = 'missing port swiata: '+', '.join(str(p.relative_to(ROOT)) for p in missing)
        print(message, flush=True)
        (OUT / 'brak-portu-swiat.csv').write_text(message+'\n', encoding='utf-8')
        return 1
    artifacts = base.TEMP / 'port-swiat-duck-build'
    artifacts.mkdir(exist_ok=True)
    manifest = OUT / 'duckling-swiat-manifest.json'
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(ROOT / 'silnik/fizyka')},
            {'id': 'swiat', 'name': 'swiat', 'path': str(PORT / 'swiat.dk'),
             'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'swiat', 'strategy': 'native', 'output_file': 'swiat',
             'linking_options': {
                 'additional_link_options': [str(artifacts.resolve() / 'libfizyka.a'), '-lm'],
                 'link_c_standard_library': True,
             }},
        ],
    }, indent=2)+'\n', encoding='utf-8')
    code = base.run('duckling-swiat-kompilacja', [duckc, 'compile_packages', manifest,
                   '-a', artifacts, '-O', '0'], seconds=150)
    if code:
        (OUT / 'blad-portu-swiat.csv').write_text(
            f'E72e9a59f5a1d Ee7fdde45e4d9 Ecd5b158f21b7 E81c44bfabb26 E70f0b8e6e134 (code {code}); kroki 1-5 have osobne pakiety i wyniki.\n', encoding='utf-8')
        return code
    executables = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                   and p.read_bytes()[:4] == b'\x7fELF']
    if len(executables) != 1:
        raise base.StepFailed(f'Oczekiwano jednego ELF swiata: {executables}')
    shutil.copy2(executables[0], OUT / 'duckling-swiat-bin')
    return base.run('duckling-swiat', ['bash', '-c', 'exec "$1" < "$2"', 'port6-stdin',
                    executables[0], OUT / 'przypadki-swiat-pelne-stdin.csv'],
                    stdout=OUT / 'duckling-swiat.csv', seconds=30)


def check_world():
    def code_of(name):
        path = OUT / (name+'-kod.csv')
        return int(path.read_text()) if path.is_file() else 125
    comparison = base.run('porownanie-swiat', [sys.executable, '-B', PORT / 'porownaj-swiat.py',
        '--c', OUT / 'c-swiat.csv', '--duckling', OUT / 'duckling-swiat.csv',
        '--wejscie', OUT / 'przypadki-swiat-pelne.csv', '--sumy-wejscia', OUT / 'wejscia-swiat-sha256.json',
        '--kod-c', code_of('kontrola-swiat'),
        '--kod-wyjscia', code_of('duckling-swiat'), '--raport', OUT / 'COMPARISON-SWIAT.md'], seconds=60)
    tests = base.run('sprawdziany-swiat', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_swiat.py', '-v'], seconds=45,
        env={**os.environ, 'SWIAT_C_BIN': str(OUT / 'kontrola-swiat-bin')})
    if not (OUT / 'COMPARISON-SWIAT.md').is_file():
        (OUT / 'COMPARISON-SWIAT.md').write_text('# FAIL\n\nmissing Ef2e01d0058c9 Ee7fdde45e4d9.\n', encoding='utf-8')
        comparison = 1
    return int(bool(comparison or tests))


def world_module(filename, name):
    spec = importlib.util.spec_from_file_location(name, PORT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def world_duckc():
    paths = [p for p in (base.TEMP / 'toolchain-port').rglob('duckc')
             if p.is_file() and os.access(p, os.X_OK)]
    if len(paths) != 1:
        raise base.StepFailed('missing E39d1e3909959 E4d1ad5d0c6b7 E14a4af4fb417; E283ada7088c2 E52788c3eb7a0 Ec1a78613530c Eb9b561238280')
    return paths[0]


def compile_world_fixture(duckc, name, driver, physics):
    artifacts = base.TEMP / (name+'-build')
    artifacts.mkdir(parents=True, exist_ok=True)
    manifest = OUT / (name+'-manifest.json')
    manifest.write_text(json.dumps({
        'packages': [
            {'id': 'fizyka', 'name': 'fizyka', 'path': str(physics)},
            {'id': 'proba', 'name': 'proba', 'path': str(driver), 'dependencies': [{'id': 'fizyka'}]},
        ],
        'tasks': [
            {'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
            {'package': 'proba', 'strategy': 'native', 'output_file': 'proba',
             'linking_options': {'additional_link_options': [str(artifacts.resolve()/'libfizyka.a'), '-lm'],
                                 'link_c_standard_library': True}},
        ],
    }, indent=2)+'\n', encoding='utf-8')
                                                                           
    base.need(name+'-kompilacja', [duckc, 'compile_packages', manifest, '-a', artifacts, '-O', '0'], seconds=150)
    binaries = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                and p.read_bytes()[:4] == b'\x7fELF']
    if len(binaries) != 1:
        raise base.StepFailed(f'{name}: oczekiwano jednego ELF, jest {len(binaries)}')
    target = OUT / (name+'-bin')
    shutil.copy2(binaries[0], target)
    return target


                                                                              
PROCESS_DIAGNOSIS_FIELDS = ('code', 'stderr', 'exception', 'validation_error')


def process_diagnosis(code, stderr=b'', exception=None, validation_error=None):
    return dict(zip(PROCESS_DIAGNOSIS_FIELDS,
                    (code, stderr.decode('utf-8', errors='replace'), exception, validation_error)))


def record_process_exception(name, command, exc, *, stdout=None):
    pass                                                                   
    message=type(exc).__name__+': '+str(exc)
    error=OUT/(name+'-stderr.csv')
    with error.open('ab') as stream:stream.write((message+'\n').encode('utf-8'))
    output=Path(stdout) if stdout is not None else OUT/(name+'.csv')
    if not output.exists():output.write_bytes(b'')
    base.record(name, list(map(str, command)), 1, 0, ROOT)
    return message


def run_world_fixture(name, executable, data=b'', file_argument=False):
    if not executable.is_file():
        exc=base.StepFailed('Brak programu: '+str(executable))
        record_process_exception(name+'-wykonanie', [executable], exc, stdout=OUT/(name+'.csv'))
        raise exc
    inputs = OUT / 'wejscia-swiat'
    inputs.mkdir(exist_ok=True)
    path = inputs / (name+'.csv')
    path.write_bytes(data)
    command = ([executable, path] if file_argument else
               ['bash', '-c', 'exec "$1" < "$2"', 'world-fixture', executable, path])
    code = base.run(name+'-wykonanie', command,
                    stdout=OUT / (name+'.csv'), seconds=30)
    return code, (OUT / (name+'.csv')).read_bytes()


def tickets_standalone():
    sys.argv[1] = 'probe'
    executable = compile_world_fixture(world_duckc(), 'bilety-proba', PORT/'proba-bilety.dk', ROOT/'silnik/fizyka')
    code, output = run_world_fixture('bilety-proba', executable)
    return int(code != 0 or output != b'BILETY OK\n')


def tickets_transport():
    sys.argv[1] = 'probe'
    bad = False
    for name, data in (('bilety-port', b'BILETY\n'), ('bilety-port-crlf', b'BILETY\r\n')):
        code, output = run_world_fixture(name, OUT/'duckling-swiat-bin', data)
        bad |= code != 0 or output != b'BILETY OK\n'
    return int(bad)


WORLD_MUTATIONS = (
    ('carry', 'gra.dk', 'return Key64(0u32, last.high + 1u32);', 'return Key64(0u32, last.high);'),
    ('limit', 'gra.dk', 'return last.low == 4294967295u32 and last.high == 4294967295u32;', 'return false;'),
    ('high', 'gra.dk', 'return Key64(last.low + 1u32, last.high);', 'return Key64(last.low + 1u32, 0u32);'),
    ('island', 'swiat.dk', 'world.islands.at(movedId as i64).localIndex = local;', '# mutation: no island localIndex repair'),
)


def replace_once(path, old, new):
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise base.StepFailed(f'{path.name}: E8b8a499e3a57 E003a8cb6dbd7 1 hits, E35e99f929e01 {text.count(old)}: {old}')
    path.write_bytes(text.replace(old, new, 1).encode('utf-8'))


def world_mutations():
    sys.argv[1] = 'probe'
    duckc = world_duckc()
    physics = ROOT/'silnik/fizyka'
    protected = [*physics.rglob('*.dk'), PORT/'proba-bilety.dk', PORT/'swiat.dk']
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    results, bad = [], False
    try:
        for mutation, filename, old, new in WORLD_MUTATIONS:
            work = base.TEMP/'mutacje-swiat'/mutation
            copied = work/'fizyka'
            shutil.copytree(physics, copied, dirs_exist_ok=True)
            replace_once(copied/filename, old, new)
            probes = ('port',) if mutation == 'island' else ('proba', 'port')
            for probe in probes:
                name = 'mutacja-'+mutation+'-'+probe
                driver = PORT/('swiat.dk' if probe == 'port' else 'proba-bilety.dk')
                                                                                 
                driver_copy = work/driver.name
                shutil.copy2(driver, driver_copy)
                binary = compile_world_fixture(duckc, name, driver_copy, copied)
                data = ((OUT/'przypadki-swiat-pelne-stdin.csv').read_bytes() if mutation == 'island'
                        else (b'BILETY\n' if probe == 'port' else b''))
                code, output = run_world_fixture(name, binary, data)
                stderr = (OUT/(name+'-wykonanie-stderr.csv')).read_bytes()
                detected = ((code == 4 and stderr == b'BLAD: indeks wyspy.\n') if mutation == 'island'
                            else (code != 0 or output != b'BILETY OK\n'))
                                                                                 
                detected &= code not in (124, 125, 126, 127)
                results.append({'mutation': mutation, 'probe': probe,
                                'expected': '4 + BLAD: indeks wyspy.' if mutation == 'island' else '!=0 lub inne wyjscie',
                                'actual': code, 'detected': bool(detected)})
                (OUT/'mutacje-swiat-wynik.json').write_text(json.dumps(results, indent=2)+'\n', encoding='ascii')
                bad |= not detected
    finally:
        if any(hashlib.sha256(p.read_bytes()).hexdigest() != digest for p, digest in before.items()):
            raise base.StepFailed('Mutacje zmienily zrodla repozytorium')
    return int(bad or len(results) != 7)


def world_negative():
    sys.argv[1] = 'probe'
    module = world_module('ujemne-swiat.py', 'world_negative_ci')
    results, bad = [], False
    for name, c_data, d_data in module.variants():
        for side, data, executable, wanted in (('c', c_data, OUT/'kontrola-swiat-bin', 2),
                                               ('duckling', d_data, OUT/'duckling-swiat-bin', 3)):
            tag = 'ujemny-'+name+'-'+side
            code, _ = run_world_fixture(tag, executable, data, file_argument=side == 'c')
            stderr = (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes()
            valid = code == wanted and (side == 'c' or stderr.startswith(b'BLAD:'))
            results.append({'input': name, 'side': side, 'expected': wanted, 'actual': code, 'ok': valid})
            (OUT/'ujemne-swiat-wynik.json').write_text(json.dumps(results, indent=2)+'\n', encoding='ascii')
            bad |= not valid
    return int(bad or len(results) != 46)


def world_evidence():
    pass                                                                       
    def code(name):
        return int((OUT/(name+'-kod.csv')).read_text(encoding='ascii'))
    try:
        for name in ('bilety-proba', 'bilety-port', 'bilety-port-crlf'):
            if code(name+'-wykonanie') != 0 or (OUT/(name+'.csv')).read_bytes() != b'BILETY OK\n':
                return False
        if code('bilety-proba-kompilacja') or code('duckling-swiat-kompilacja'):
            return False
        for name in ('bilety-proba-bin', 'duckling-swiat-bin', 'bilety-proba-manifest.json', 'duckling-swiat-manifest.json'):
            if not (OUT/name).is_file():
                return False
        rows = json.loads((OUT/'mutacje-swiat-wynik.json').read_bytes())
        wanted = {(m[0], probe) for m in WORLD_MUTATIONS for probe in (('port',) if m[0] == 'island' else ('proba', 'port'))}
        if len(rows) != 7 or {(r['mutation'], r['probe']) for r in rows} != wanted:
            return False
        for row in rows:
            name = 'mutacja-'+row['mutation']+'-'+row['probe']
            actual = code(name+'-wykonanie')
            output = (OUT/(name+'.csv')).read_bytes()
            stderr = (OUT/(name+'-wykonanie-stderr.csv')).read_bytes()
            valid = (actual == 4 and stderr == b'BLAD: indeks wyspy.\n') if row['mutation'] == 'island' else (actual != 0 or output != b'BILETY OK\n')
            if code(name+'-kompilacja') or actual != row['actual'] or not valid or not row['detected'] or actual in (124, 125, 126, 127):
                return False
        rows = json.loads((OUT/'ujemne-swiat-wynik.json').read_bytes())
        wanted = {(name, side) for name, _, _ in world_module('ujemne-swiat.py', 'world_evidence_inputs').variants()
                  for side in ('c', 'duckling')}
        if len(rows) != 46 or {(r['input'], r['side']) for r in rows} != wanted:
            return False
        for row in rows:
            name = 'ujemny-'+row['input']+'-'+row['side']
            actual = code(name+'-wykonanie')
            if actual != (2 if row['side'] == 'c' else 3) or actual != row['actual'] or not row['ok']:
                return False
            (OUT/(name+'.csv')).read_bytes()
            stderr = (OUT/(name+'-wykonanie-stderr.csv')).read_bytes()
            if row['side'] == 'duckling' and not stderr.startswith(b'BLAD:'):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def world_positive_errors():
    pass                                                                     
    inputs = world_module('ujemne-swiat.py', 'world_positive_inputs')
    comparison = world_module('porownaj-swiat.py', 'world_positive_comparison')
    rows = inputs.small_cases()
    outputs, codes = [], []
    for side, decimal in (('c', False), ('duckling', True)):
        name = 'baza-ujemnych-'+side
        if (OUT/'wejscia-swiat'/(name+'.csv')).read_bytes() != inputs.g.encode(rows, decimal).encode('ascii'):
            return ['Niezgodne bytes poprawnej bazy '+side]
        codes.append(int((OUT/(name+'-wykonanie-kod.csv')).read_text(encoding='ascii')))
        outputs.append((OUT/(name+'.csv')).read_bytes().decode('ascii'))
    return comparison.compare(*outputs, rows, *codes)


def world_positive():
    sys.argv[1] = 'probe'
    inputs = world_module('ujemne-swiat.py', 'world_positive_ci')
    rows = inputs.small_cases()
    for side, decimal, binary in (('c', False, 'kontrola-swiat-bin'), ('duckling', True, 'duckling-swiat-bin')):
        run_world_fixture('baza-ujemnych-'+side, OUT/binary,
                          inputs.g.encode(rows, decimal).encode('ascii'), file_argument=side == 'c')
    errors = world_positive_errors()
    report = '# BLAD\n\n'+'\n'.join(errors) if errors else '# OK\n\nE5e34408f7b18 N=64: C Ede7d1b721a1e Duckling, code 0, E35921752e752 exit E13991feb1b0c z E0bcf7a000869 Ede7d1b721a1e E33129567e0bd E78b4f45f84f8.'
    (OUT/'BAZA-UJEMNYCH-SWIAT.md').write_text(report+'\n', encoding='utf-8')
    print(report)
    return int(bool(errors))


def world_negative_round2():
                                                                            
    if world_positive_errors():
        return 1
    bad = bool(world_negative())
    inputs = world_module('ujemne-swiat.py', 'world_negative_round2_inputs')
    results = []
    for name, c_data, d_data in inputs.boundary_variants():
        for side, data, binary, wanted in (('c', c_data, 'kontrola-swiat-bin', 2),
                                           ('duckling', d_data, 'duckling-swiat-bin', 3)):
            tag = 'ujemny-'+name+'-'+side
            actual, _ = run_world_fixture(tag, OUT/binary, data, file_argument=side == 'c')
            stderr = (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes()
            valid = actual == wanted and (side == 'c' or stderr.startswith(inputs.expected_diagnostic(name)))
            results.append(dict(input=name, side=side, expected=wanted, actual=actual, ok=valid))
            (OUT/'ujemne-granice-swiat-wynik.json').write_text(json.dumps(results, indent=2)+'\n', encoding='ascii')
            bad |= not valid
                                                                              
                                                                                
    rows = json.loads((OUT/'ujemne-swiat-wynik.json').read_bytes())
    for row in rows:
        if row['side'] == 'duckling':
            stderr = (OUT/('ujemny-'+row['input']+'-duckling-wykonanie-stderr.csv')).read_bytes()
            row['ok'] &= stderr.startswith(inputs.expected_diagnostic(row['input']))
            bad |= not row['ok']
    (OUT/'ujemne-swiat-wynik.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='ascii')
    return int(bad)


def world_evidence_round2():
    try:
        if not world_evidence() or world_positive_errors():
            return False
        inputs = world_module('ujemne-swiat.py', 'world_round2_evidence_inputs')
        boundaries = inputs.boundary_variants()
        rows = json.loads((OUT/'ujemne-granice-swiat-wynik.json').read_bytes())
        wanted = {(name, side) for name, _, _ in boundaries for side in ('c', 'duckling')}
        if len(rows) != 4 or {(r['input'], r['side']) for r in rows} != wanted:
            return False
        for row in rows:
            tag = 'ujemny-'+row['input']+'-'+row['side']
            actual = int((OUT/(tag+'-wykonanie-kod.csv')).read_text(encoding='ascii'))
            if actual != (2 if row['side'] == 'c' else 3) or actual != row['actual'] or not row['ok']:
                return False
            (OUT/(tag+'.csv')).read_bytes()
            (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes()
        for name, _, _ in (*inputs.variants(), *boundaries):
            stderr = (OUT/('ujemny-'+name+'-duckling-wykonanie-stderr.csv')).read_bytes()
            if not stderr.startswith(inputs.expected_diagnostic(name)):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def check_broad():
    def code_of(name):
        path = OUT / (name+'-kod.csv')
        return int(path.read_text()) if path.is_file() else 125
    comparison = base.run('porownanie-szeroka', [sys.executable, '-B', PORT / 'porownaj-szeroka.py',
        '--c', OUT / 'c-szeroka.csv', '--duckling', OUT / 'duckling-szeroka.csv',
        '--c-bez', OUT / 'c-szeroka-bez.csv', '--wejscie', OUT / 'przypadki-szeroka.csv',
        '--kod-c', code_of('kontrola-szeroka'), '--kod-wyjscia', code_of('duckling-szeroka'),
        '--kod-c-bez', code_of('kontrola-szeroka-bez'), '--raport', OUT / 'COMPARISON-SZEROKA.md'], seconds=60)
    tests = base.run('sprawdziany-szeroka', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_szeroka.py', '-v'], seconds=45)
    if not (OUT / 'COMPARISON-SZEROKA.md').is_file():
        (OUT / 'COMPARISON-SZEROKA.md').write_text('# FAIL\n\nmissing Ef2e01d0058c9 broad phase.\n', encoding='utf-8')
        comparison = 1
    return int(bool(comparison or tests))


def check_tree():
    def code_of(name):
        path = OUT / (name+'-kod.csv')
        return int(path.read_text()) if path.is_file() else 125

    comparison = base.run('porownanie-drzewo', [sys.executable, '-B', PORT / 'porownaj-drzewo.py',
        '--c', OUT / 'c-drzewo.csv', '--duckling', OUT / 'duckling-drzewo.csv',
        '--wejscie', OUT / 'przypadki-drzewo.csv', '--kod-wyjscia', code_of('duckling-drzewo'),
        '--kod-c', code_of('kontrola-drzewo'), '--raport', OUT / 'COMPARISON-DRZEWO.md'], seconds=45)
    tests = base.run('sprawdziany-drzewo', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_drzewo.py', '-v'], seconds=45)
    if not (OUT / 'COMPARISON-DRZEWO.md').is_file():
        (OUT / 'COMPARISON-DRZEWO.md').write_text('# FAIL\n\nmissing Ef2e01d0058c9 E930e79f4d2d2.\n', encoding='utf-8')
        comparison = 1
    return 1 if comparison or tests else 0


def check_motion():
    def code_of(name):
        path = OUT / (name+'-kod.csv')
        return int(path.read_text()) if path.is_file() else 125

    comparison = base.run('porownanie-ruch', [sys.executable, '-B', PORT / 'porownaj-ruch.py',
        '--c', OUT / 'c-ruch.csv', '--duckling', OUT / 'duckling-ruch.csv',
        '--wejscie', OUT / 'przypadki-ruch.csv', '--kod-wyjscia', code_of('duckling-ruch'),
        '--kod-c', code_of('kontrola-ruch'), '--raport', OUT / 'COMPARISON-RUCH.md'], seconds=45)
    tests = base.run('sprawdziany-ruch', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_ruch.py', '-v'], seconds=45)
    if not (OUT / 'COMPARISON-RUCH.md').is_file():
        (OUT / 'COMPARISON-RUCH.md').write_text('# FAIL\n\nmissing Ef2e01d0058c9 motion.\n', encoding='utf-8')
        comparison = 1
    return 1 if comparison or tests else 0


def check():
    code_file = OUT / 'duckling-kod.csv'
    exit_code = int(code_file.read_text()) if code_file.is_file() else 125
    comparison = base.run('porownanie', [sys.executable, '-B', PORT / 'porownaj.py',
        '--c', OUT / 'c.csv', '--duckling', OUT / 'duckling.csv', '--kod-wyjscia', exit_code,
        '--raport', OUT / 'COMPARISON.md'], seconds=30)
    tests = base.run('sprawdziany', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_porownaj.py', '-v'], seconds=30)
    if not (OUT / 'COMPARISON.md').is_file():
        (OUT / 'COMPARISON.md').write_text('# FAIL\n\nEf84a80af38b9 Ecd5b158f21b7 Eef324d26415d Ef2e01d0058c9.\n', encoding='utf-8')
        comparison = 1
    def code_of(name):
        path = OUT / (name+'-kod.csv')
        return int(path.read_text()) if path.is_file() else 125

    polygons = base.run('porownanie-wiel', [sys.executable, '-B', PORT / 'porownaj-wiel.py',
        '--c', OUT / 'c-wiel.csv', '--duckling', OUT / 'duckling-wiel.csv',
        '--wejscie', OUT / 'przypadki-wiel.csv', '--kod-wyjscia', code_of('duckling-wiel'),
        '--kod-c', code_of('kontrola-wiel'), '--raport', OUT / 'COMPARISON-WIEL.md'], seconds=30)
    polygon_tests = base.run('sprawdziany-wiel', [sys.executable, '-B', '-m', 'unittest', 'discover',
        '-s', 'silnik/port', '-p', 'test_wiel.py', '-v'], seconds=30)
    if not (OUT / 'COMPARISON-WIEL.md').is_file():
        (OUT / 'COMPARISON-WIEL.md').write_text('# FAIL\n\nmissing Ef2e01d0058c9 Ec3f183a85574.\n', encoding='utf-8')
        polygons = 1
    return 1 if comparison or tests or polygons or polygon_tests else 0


def summary(include_broad=False, include_world=False, include_probes=False, include_round2=False):
                                                                        
                                                                            
    stages = ('c', 'duckling', 'check', 'check-ruch', 'check-drzewo')
    if include_broad:
        stages += ('check-szeroka',)
    if include_world:
        stages += ('c-swiat', 'check-swiat')
    if include_probes:
        stages += ('bilety-proba', 'bilety-port', 'mutacje-swiat', 'ujemne-swiat')
    if include_round2:
        stages += ('baza-ujemnych-swiat',)
    failed = False
    lines = ['# E72e9a59f5a1d Ef642974cfcb1, Ec3f183a85574, motion, E930e79f4d2d2 Ede7d1b721a1e broad phase — E5c74971662f4', '', '| Etap | Kod | Sekundy |', '|---|---:|---:|']
    if include_world:
        lines[0] = '# Port krokow 1-6, ze swiatem — dziennik'
    for stage in stages:
        code_file = OUT / f'etap-port-{stage}-kod.csv'
        code = code_file.read_text().strip() if code_file.is_file() else 'MISSING'
        seconds_file = OUT / f'etap-port-{stage}-czas.csv'
        seconds = seconds_file.read_text().strip() if seconds_file.is_file() else '-'
        failed |= code != '0'
        lines.append(f'| {stage} | {code} | {seconds} |')
    outcomes = ('C', 'DUCKLING', 'CHECK', 'RUCH', 'DRZEWO') + (('SZEROKA',) if include_broad else ())
    if include_world:
        outcomes += ('C_SWIAT', 'SWIAT')
    if include_probes:
        outcomes += ('BILETY_PROBA', 'BILETY_PORT', 'MUTACJE_SWIAT', 'UJEMNE_SWIAT')
    if include_round2:
        outcomes += ('BAZA_UJEMNYCH_SWIAT',)
    for name in outcomes:
        outcome = os.environ.get(name + '_OUTCOME', 'MISSING')
        failed |= outcome != 'success'
        lines.append(f'| GitHub {name} | {outcome} | - |')
    if include_probes:
        failed |= not (world_evidence_round2() if include_round2 else world_evidence())
        if include_round2:
            for side in ('c', 'duckling'):
                tag = 'baza-ujemnych-'+side+'-wykonanie'
                code_file = OUT/(tag+'-kod.csv')
                value = code_file.read_text().strip() if code_file.is_file() else 'MISSING'
                lines.append(f'| {tag} | {value} | - |')
        for name in ('bilety-proba', 'bilety-port', 'bilety-port-crlf'):
            output, code = OUT/(name+'.csv'), OUT/(name+'-wykonanie-kod.csv')
            failed |= not (output.is_file() and code.is_file() and output.read_bytes() == b'BILETY OK\n'
                           and code.read_text().strip() == '0')
        tables = [('mutacje-swiat-wynik.json', 7, 'detected', 'Mutacje natywne'),
                  ('ujemne-swiat-wynik.json', 46, 'ok', 'Proby ujemne')]
        if include_round2:
            tables.append(('ujemne-granice-swiat-wynik.json', 4, 'ok', 'Transport boundary equality checks'))
        for filename, count, key, title in tables:
            lines += ['', '## '+title, '', '| E73703ed95b4c | Eaba8044f8d8c code | code Ec2d78d2c1f3a | E931647da0d5b |', '|---|---|---:|---|']
            try:
                rows = json.loads((OUT/filename).read_bytes())
                failed |= len(rows) != count or not all(row[key] for row in rows)
                for row in rows:
                    label = row.get('mutation', row.get('input'))+' / '+row.get('probe', row.get('side'))
                    lines.append(f'| {label} | {row['expected']} | {row['actual']} | {row[key]} |')
            except (OSError, ValueError, KeyError, TypeError):
                failed = True
                lines.append('| MISSING / Eea99d4252f4e Ebc2e4bea2e33 | - | - | BLAD |')
    lines += ['', 'RESULT: ' + ('FAIL' if failed else 'OK'), '',
              '125 = missing E259329252908 Ee6b67ce8a51d; 124 = E55ea09e5715d Ea3fe81deb86e. missing port E35e99f929e01 E74b62e088ba2.',
              'Polecenia, czasy, stdout i stderr: osobne pliki obok tego dziennika.', '']
    (OUT / 'DZIENNIK.md').write_text('\n'.join(lines), encoding='utf-8')
    (OUT / 'wynik-kod.csv').write_text('1\n' if failed else '0\n', encoding='ascii')
    print('\n'.join(lines))


                                                                          
                                                                
def shape_module(filename, name):
    return world_module(filename, name)


def shape_run(name, executable, data, c_side=False):
    if not executable.is_file():
        raise base.StepFailed('step 7: missing E571f18490e82 '+str(executable))
    inputs=OUT/'wejscia-ksztalty'
    inputs.mkdir(exist_ok=True)
    path=inputs/(name+'.csv')
    path.write_bytes(data)
    command=([executable,path] if c_side else
             ['bash','-c','exec "$1" < "$2"','shape-stdin',executable,path])
    code=base.run(name+'-wykonanie',command,stdout=OUT/(name+'.csv'),seconds=45)
    return code,(OUT/(name+'.csv')).read_bytes(),(OUT/(name+'-wykonanie-stderr.csv')).read_bytes()


def shape_code(name):
    path=OUT/(name+'-kod.csv')
    return int(path.read_text()) if path.is_file() else 125


def c_shapes():
    sys.argv[1]='probe'
    base.need('generator-ksztalty',[sys.executable,'-B',PORT/'przypadki-ksztalty.py','--katalog',OUT],seconds=30)
    source=base.TEMP/'box2d'
    files=sorted([*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),
                  *source.joinpath('include/box2d').glob('*.h')])
    if len(files)!=63:
        raise base.StepFailed('step 7: expected 63 Eaac69f7919f4 Ead9a1701b1d7 C/H')
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    library=base.CACHE/'box2d/lib/libbox2d.a'
    library_before=hashlib.sha256(library.read_bytes()).hexdigest()
    sums=''.join(f'{digest}  {p.relative_to(source).as_posix()}\n' for p,digest in before.items())
    contract=norm_text(PORT/'fixtures/norms/KONTRAKT-7.json')
    if any(line not in contract for line in sums.splitlines()):
        raise base.StepFailed('Krok 7: inne checksum oryginalu')
    (OUT/'box2d-ksztalty-sha256.csv').write_text(sums,encoding='ascii')
    (OUT/'box2d-ksztalty-biblioteka-sha256.csv').write_text(library_before+'\n',encoding='ascii')
    for suffix,obs in (('','1'),('-bez','0')):
        name='kontrola-ksztalty'+suffix
        executable=base.TEMP/name
        base.need(name+'-kompilacja',['cc','-std=c17','-O2','-Wall','-Wextra','-Werror',
            '-DNDEBUG','-DBOX2D_DISABLE_SIMD','-DOBS='+obs,'-fno-fast-math','-ffp-contract=off',
            '-I'+str(source/'include'),'-I'+str(source/'src'),PORT/'kontrola-ksztalty.c',library,'-lm','-o',executable],seconds=30)
        shutil.copy2(executable,OUT/(name+'-bin'))
                                                                         
        base.need(name+'-proba',[executable,OUT/'proba-ksztalty.csv'],stdout=OUT/('c-ksztalty-proba'+suffix+'.csv'),seconds=15)
        base.need(name,[executable,OUT/'przypadki-ksztalty.csv'],stdout=OUT/('c-ksztalty'+suffix+'.csv'),seconds=60)
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=digest for p,digest in before.items()) or hashlib.sha256(library.read_bytes()).hexdigest()!=library_before:
        raise base.StepFailed('Krok 7: zmieniono oryginal lub biblioteke')
    return 0


def duckling_shapes():
    sys.argv[1]='probe'
    target=PORT/'ksztalty.dk'
    (OUT/'duckling-ksztalty.csv').write_bytes(b'')
    if not target.is_file():
        raise base.StepFailed('step 7: missing ksztalty.dk; Ebc2e4bea2e33 E74b62e088ba2')
    binary=compile_world_fixture(world_duckc(),'duckling-ksztalty',target,ROOT/'silnik/fizyka')
    code,_,_=shape_run('duckling-ksztalty-proba',binary,(OUT/'proba-ksztalty-stdin.csv').read_bytes())
    if code:
        return code
    return base.run('duckling-ksztalty',['bash','-c','exec "$1" < "$2"','port7-stdin',binary,
                   OUT/'przypadki-ksztalty-stdin.csv'],stdout=OUT/'duckling-ksztalty.csv',seconds=60)


def check_shapes():
    comparison=base.run('porownanie-ksztalty',[sys.executable,'-B',PORT/'porownaj-ksztalty.py',
        '--c',OUT/'c-ksztalty.csv','--c-bez',OUT/'c-ksztalty-bez.csv',
        '--duckling',OUT/'duckling-ksztalty.csv','--wejscie',OUT/'przypadki-ksztalty.csv',
        '--kod-c',shape_code('kontrola-ksztalty'),'--kod-c-bez',shape_code('kontrola-ksztalty-bez'),
        '--kod-wyjscia',shape_code('duckling-ksztalty'),'--raport',OUT/'POROWNANIE-KSZTALTY.md'],seconds=150)
    tests=base.run('sprawdziany-ksztalty',[sys.executable,'-B','-m','unittest','discover',
        '-s','silnik/port','-p','test_ksztalty*.py','-v'],seconds=180,
        env={**os.environ,'KSZTALTY_C_BIN':str(OUT/'kontrola-ksztalty-bin')})
    return int(bool(comparison or tests))


def shape_positive_errors(prefix, rows, inputs):
    p=shape_module('porownaj-ksztalty.py','shape_positive_compare')
    errors=[]
    for side,decimal in (('c',False),('duckling',True)):
        name=prefix+'-'+side
        try:
            data=(OUT/'wejscia-ksztalty'/(name+'.csv')).read_bytes()
            if data!=inputs.encode(rows,decimal).encode('ascii'):
                errors.append(name+': Ebdfad9bd4075 bytes E95d3b17f0fb1')
            code=shape_code(name+'-wykonanie')
            if code!=0:errors.append(name+': code '+str(code))
            if (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():errors.append(name+': stderr poprawnej bazy')
            with (OUT/(name+'.csv')).open(encoding='ascii',newline='') as stream:
                p.validate_output(stream,rows)
        except (OSError,ValueError,KeyError,IndexError) as exc:
            errors.append(name+': '+str(exc))
    if not errors:
        with (OUT/(prefix+'-c.csv')).open(encoding='ascii',newline='') as a,(OUT/(prefix+'-duckling.csv')).open(encoding='ascii',newline='') as b:
            diff=p.first_difference(a,b)
            if diff:errors.append(diff)
    return errors


def shape_probes():
    sys.argv[1]='probe'
    inputs=shape_module('przypadki-ksztalty.py','shape_probe_inputs')
    negative=shape_module('ujemne-ksztalty.py','shape_negative_ci')
    results=[];bad=False
    for side,decimal in (('c',False),('duckling',True)):
        binary=OUT/('kontrola-ksztalty-bin' if side=='c' else 'duckling-ksztalty-bin')
        shape_run('ksztalty-baza-'+side,binary,inputs.encode(inputs.small_cases(),decimal).encode('ascii'),side=='c')
    errors=shape_positive_errors('ksztalty-baza',inputs.small_cases(),inputs)
    (OUT/'ksztalty-baza-bledy.json').write_text(json.dumps(errors)+'\n',encoding='ascii')
    if errors:
        raise base.StepFailed('step 7: E33acac3391f6 E706a217d179d Ecd5b158f21b7 E9328ce79a033: '+str(errors))
                                                                             
    for suffix in ('','-bez'):
        name='ksztalty-bilety-c'+suffix
        code=base.run(name+'-wykonanie',[OUT/('kontrola-ksztalty'+suffix+'-bin'),'--test-tickets'],stdout=OUT/(name+'.csv'),seconds=15)
        valid=code==0 and (OUT/(name+'.csv')).read_bytes()==b'BILETY OK\n' and not (OUT/(name+'-wykonanie-stderr.csv')).read_bytes()
        results.append({'name':name,'expected':0,'actual':code,'ok':valid});bad|=not valid
    for suffix,data in (('',b'BILETY\n'),('-crlf',b'BILETY\r\n')):
        name='ksztalty-bilety-duckling'+suffix
        code,out,err=shape_run(name,OUT/'duckling-ksztalty-bin',data)
        valid=code==0 and out==b'BILETY OK\n' and not err
        results.append({'name':name,'expected':0,'actual':code,'ok':valid});bad|=not valid
    standalone=compile_world_fixture(world_duckc(),'ksztalty-bilety-osobne',PORT/'proba-ksztalty-bilety.dk',ROOT/'silnik/fizyka')
    code,out,err=shape_run('ksztalty-bilety-osobne',standalone,b'')
    valid=code==0 and out==b'KSZTALTY BILETY OK\n' and not err
    results.append({'name':'ksztalty-bilety-osobne','expected':0,'actual':code,'ok':valid});bad|=not valid
    for name,cdata,ddata,cdiag,ddiag in negative.variants():
        for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
            tag='ksztalty-ujemny-'+name+'-'+side
            code,_,stderr=shape_run(tag,OUT/('kontrola-ksztalty-bin' if side=='c' else 'duckling-ksztalty-bin'),data,side=='c')
            valid=code==wanted and stderr.splitlines(keepends=True)[:1]==[diag]
            results.append({'name':tag,'expected':wanted,'actual':code,'ok':valid});bad|=not valid
            (OUT/'proby-ksztalty-wynik.json').write_text(json.dumps(results,indent=2)+'\n',encoding='ascii')
    return int(bad or len(results)!=5+2*len(negative.variants()))


def shape_mutations():
    sys.argv[1]='probe'
    inputs=shape_module('przypadki-ksztalty.py','shape_mutation_inputs')
    comparator=shape_module('porownaj-ksztalty.py','shape_mutation_compare')
    rows=inputs.cases()[:24]
    for side,decimal in (('c',False),('duckling',True)):
        binary=OUT/('kontrola-ksztalty-bin' if side=='c' else 'duckling-ksztalty-bin')
        shape_run('ksztalty-mutacje-baza-'+side,binary,inputs.encode(rows,decimal).encode('ascii'),side=='c')
    errors=shape_positive_errors('ksztalty-mutacje-baza',rows,inputs)
    if errors:
        raise base.StepFailed('step 7: missing E7a801e182e93 E2728d228cd0b E0840f545c010 '+str(errors))
    physics=ROOT/'silnik/fizyka';driver=PORT/'ksztalty.dk'
    protected=[*physics.rglob('*.dk'),driver]
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    recipes=json.loads((PORT/'mutacje-ksztalty.json').read_bytes())['native_mutations']
    results=[];bad=False
    try:
        for recipe in recipes:
            name='ksztalty-mutacja-'+recipe['name'];work=base.TEMP/'mutacje-ksztalty'/recipe['name'];copied=work/'fizyka'
            shutil.copytree(physics,copied,dirs_exist_ok=True)
            path=copied/Path(recipe['source']).name
            replace_once(path,recipe['expression'],recipe['replacement'])
            driver_copy=work/driver.name;shutil.copy2(driver,driver_copy)
            binary=compile_world_fixture(world_duckc(),name,driver_copy,copied)
            data=b'BILETY\n' if recipe['probe']=='tickets' else inputs.encode(rows,True).encode('ascii')
            code,output,stderr=shape_run(name,binary,data)
            errors=[]
            if recipe['probe']=='tickets':
                detected=code==3 and stderr.splitlines(keepends=True)[:1]==[b'BLAD: proba biletow.\n']
            else:
                if code==0:
                    try:
                        comparator.validate_output(output.decode('ascii'),rows)
                        with (OUT/'ksztalty-mutacje-baza-c.csv').open(encoding='ascii',newline='') as source:
                            diff=comparator.first_difference(source,io.StringIO(output.decode('ascii')))
                        if diff:errors.append(diff)
                    except (ValueError,KeyError,IndexError) as exc:errors.append(str(exc))
                    detected=bool(errors)
                else:
                    detected=recipe['expected_failure']=='integrity' and code==4 and stderr.splitlines(keepends=True)[:1]==[b'BLAD: lista ksztaltow.\n']
            detected=bool(detected and code not in (124,125,126,127))
            if code==4 and detected:
                echoes=[line for line in output.decode('ascii').splitlines() if line.startswith('E ')]
                if not echoes:detected=False
                else:
                    prefix=echoes[-1].split(' ')
                    errors.append(f'id {prefix[1]}, seq {prefix[2]}, record integralnosc, field lista ksztaltow: native code 4')
            results.append({'name':name,'probe':recipe['probe'],'actual':code,'detected':detected,'errors':errors})
            (OUT/'mutacje-ksztalty-wynik.json').write_text(json.dumps(results,indent=2)+'\n',encoding='ascii')
            bad|=not detected
    finally:
        if any(hashlib.sha256(p.read_bytes()).hexdigest()!=digest for p,digest in before.items()):
            raise base.StepFailed('Krok 7: mutacje naruszyly oryginaly')
    return int(bad or len(results)!=len(recipes))


def shape_evidence():
    inputs=shape_module('przypadki-ksztalty.py','shape_evidence_inputs')
    negative=shape_module('ujemne-ksztalty.py','shape_evidence_negative')
    try:
        inputs.verify_input_hashes(OUT)
        if shape_positive_errors('ksztalty-baza',inputs.small_cases(),inputs):return False
        if shape_positive_errors('ksztalty-mutacje-baza',inputs.cases()[:24],inputs):return False
        for suffix in ('','-bez'):
            name='ksztalty-bilety-c'+suffix
            if shape_code(name+'-wykonanie')!=0 or (OUT/(name+'.csv')).read_bytes()!=b'BILETY OK\n' or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
        for suffix,data in (('',b'BILETY\n'),('-crlf',b'BILETY\r\n')):
            name='ksztalty-bilety-duckling'+suffix
            if shape_code(name+'-wykonanie')!=0 or (OUT/(name+'.csv')).read_bytes()!=b'BILETY OK\n' or (OUT/'wejscia-ksztalty'/(name+'.csv')).read_bytes()!=data or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
        name='ksztalty-bilety-osobne'
        if shape_code(name+'-kompilacja')!=0 or shape_code(name+'-wykonanie')!=0 or (OUT/(name+'.csv')).read_bytes()!=b'KSZTALTY BILETY OK\n' or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes() or (OUT/'wejscia-ksztalty'/(name+'.csv')).read_bytes()!=b'':return False
        for name,cdata,ddata,cdiag,ddiag in negative.variants():
            for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
                tag='ksztalty-ujemny-'+name+'-'+side
                if shape_code(tag+'-wykonanie')!=wanted or (OUT/'wejscia-ksztalty'/(tag+'.csv')).read_bytes()!=data or (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes().splitlines(keepends=True)[:1]!=[diag]:return False
        recipes=json.loads((PORT/'mutacje-ksztalty.json').read_bytes())['native_mutations']
        results=json.loads((OUT/'mutacje-ksztalty-wynik.json').read_bytes())
        if [r['name'] for r in results]!=['ksztalty-mutacja-'+r['name'] for r in recipes]:return False
        for recipe,row in zip(recipes,results):
            name=row['name'];code=shape_code(name+'-wykonanie')
            if not row['detected'] or code!=row['actual'] or shape_code(name+'-kompilacja')!=0 or code in (124,125,126,127):return False
            stderr=(OUT/(name+'-wykonanie-stderr.csv')).read_bytes()
            if recipe['probe']=='tickets':
                if code!=3 or stderr.splitlines(keepends=True)[:1]!=[b'BLAD: proba biletow.\n']:return False
            elif code:
                if recipe['expected_failure']!='integrity' or code!=4 or stderr.splitlines(keepends=True)[:1]!=[b'BLAD: lista ksztaltow.\n']:return False
            else:
                p=shape_module('porownaj-ksztalty.py','shape_evidence_compare')
                actual=(OUT/(name+'.csv')).read_text(encoding='ascii')
                detected=False
                try:p.validate_output(actual,inputs.cases()[:24])
                except (ValueError,IndexError,KeyError):detected=True
                if not detected:
                    with (OUT/'ksztalty-mutacje-baza-c.csv').open(encoding='ascii',newline='') as original:
                        detected=p.first_difference(original,io.StringIO(actual)) is not None
                if not detected:return False
    except (OSError,ValueError,KeyError,IndexError,TypeError):
        return False
    return True


def summary_shapes():
    summary(include_broad=True,include_world=True,include_probes=True,include_round2=True)
    failed=(OUT/'wynik-kod.csv').read_text().strip()!='0'
    lines=['','## Krok 7 — oddzielne etapy','','| Etap | Kod |','|---|---:|']
    for stage,outcome in (('c-ksztalty','C_KSZTALTY'),('duckling-ksztalty','DUCKLING_KSZTALTY'),
                          ('check-ksztalty','KSZTALTY'),('proby-ksztalty','PROBY_KSZTALTY'),('mutacje-ksztalty','MUTACJE_KSZTALTY')):
        code=shape_code('etap-port-'+stage)
        actual=os.environ.get(outcome+'_OUTCOME','MISSING')
        failed|=code!=0 or actual!='success'
        lines.append(f'| {stage} / GitHub {actual} | {code} |')
    evidence=shape_evidence();failed|=not evidence
    lines+=['',f'Dowody kroku 7: {evidence}.', '', 'RESULT KROKOW 1–7: '+('FAIL' if failed else 'OK'),'']
    with (OUT/'DZIENNIK.md').open('a',encoding='utf-8') as out:out.write('\n'.join(lines))
    (OUT/'wynik-kod.csv').write_text('1\n' if failed else '0\n',encoding='ascii')
    print('\n'.join(lines));return int(failed)


def motion8_stage(name):
                                                                          
                                                                          
    module = world_module('ci-ruch-swiata.py', 'motion8_ci')
    return module.stage(SimpleNamespace(**globals()), name)


def pair9a_stage(name):
    module = world_module('ci-pary.py', 'pair9a_ci')
    return module.stage(SimpleNamespace(**globals()), name)


def contact9b_stage(name):
    module = world_module('ci-kontakty.py', 'contact9b_ci')
    return module.stage(SimpleNamespace(**globals()), name)


def solver10_stage(name):
    module = world_module('ci-solver.py', 'solver10_ci')
    return module.stage(SimpleNamespace(**globals()), name)


def sen11_stage(name):
    module = world_module('ci-sen.py', 'sen11_ci')
    return module.stage(SimpleNamespace(**globals()), name)


def lancuchy13_stage():
    module = world_module('ci-lancuchy.py', 'lancuchy13_ci')
    return module.stage(SimpleNamespace(**globals()))

def lancuchy13b_stage():
    module = world_module('ci-lancuchy.py', 'lancuchy13b_ci')
    result=module.stage13b(SimpleNamespace(**globals()));module.summary()
    return result['code']

def lancuchy13c_stage():
    module = world_module('ci-lancuchy.py', 'lancuchy13c_ci')
    result=module.stage13c(SimpleNamespace(**globals()));module.summary()
    return result['code']


def main():
    global OUT
    stage = sys.argv[1]
    if stage in ('budowa-zywy','proba-zywy','porownanie-zywy-12a','porownanie-zywy','component-zywy','swiadki-zywy-2a','check-zywy','summary-zywy'):
                                                                          
                                                                             
        OUT=OUT if OUT.name=='krok12' else OUT.parent/'krok12' if OUT.name in ('krok10','krok11') else OUT/'krok12'
        OUT.mkdir(parents=True,exist_ok=True)
        base.OUT=OUT
    start = time.monotonic()
    code = 1
    try:
        code = {'lancuchy': lancuchy13_stage, 'lancuchy-13b': lancuchy13b_stage, 'lancuchy-13c': lancuchy13c_stage,
        **{name: (lambda name=name: world_module('ci-zywy.py','zywy12_ci').stage(SimpleNamespace(**globals()),name)) for name in
                   ('budowa-zywy','proba-zywy','porownanie-zywy-12a','porownanie-zywy','component-zywy','swiadki-zywy-2a','check-zywy','summary-zywy')},
                **{name: (lambda name=name: sen11_stage(name)) for name in
                   ('budowa-sen', 'proba-sen', 'porownanie-sen', 'component-sen',
                    'porownanie-sen-11a', 'component-sen-11a',
                    'check-sen', 'summary-sen', 'zapis-strumieni-sen')},
                **{name: (lambda name=name: solver10_stage(name)) for name in
                   ('proba-solver', 'porownanie-solver', 'component-solver',
                    'check-solver', 'summary-solver', 'zapis-strumieni-solver')},
                **{name: (lambda name=name: contact9b_stage(name)) for name in
                   ('proba-kontakty', 'c-kontakty-obs0', 'c-kontakty-obs1', 'native-kontakty',
                    'check-kontakty', 'ujemne-kontakty', 'fixtury-kontakty', 'mutacje-kontakty',
                    'summary-kontakty', 'zapis-strumieni-kontakty')},
                **{name: (lambda name=name: pair9a_stage(name)) for name in
                   ('proba-pary', 'c-pary', 'duckling-pary', 'check-pary',
                    'proby-pary', 'mutacje-pary', 'summary-pary', 'zapis-strumieni-pary')},
                **{name: (lambda name=name: motion8_stage(name)) for name in
                   ('proba-ruch-swiata', 'c-ruch-swiata', 'duckling-ruch-swiata',
                    'check-ruch-swiata', 'proby-ruch-swiata', 'mutacje-ruch-swiata',
                    'summary-ruch-swiata', 'zapis-strumieni')},
                'c-ksztalty': c_shapes, 'duckling-ksztalty': duckling_shapes,
                'check-ksztalty': check_shapes, 'proby-ksztalty': shape_probes,
                'mutacje-ksztalty': shape_mutations, 'summary-ksztalty': summary_shapes,
                'c': c_side, 'duckling': duckling_side, 'check': check,
                'check-ruch': check_motion, 'check-drzewo': check_tree,
                'check-szeroka': check_broad, 'summary': lambda: summary(include_broad=True),
                'c-swiat': c_world, 'check-swiat': check_world,
                'summary-swiat': lambda: summary(include_broad=True, include_world=True),
                'bilety-proba': tickets_standalone, 'bilety-port': tickets_transport,
                'mutacje-swiat': world_mutations, 'ujemne-swiat': world_negative_round2,
                'baza-ujemnych-swiat': world_positive,
                'summary-swiat-proby': lambda: summary(include_broad=True, include_world=True, include_probes=True, include_round2=True)}[stage]() or 0
    except Exception:
        traceback.print_exc()
    finally:
        stage_out=(OUT if OUT.name=='krok12' else OUT.parent/'krok12' if OUT.name in ('krok10','krok11') else OUT/'krok12') if stage in ('budowa-zywy','proba-zywy','porownanie-zywy-12a','porownanie-zywy','component-zywy','swiadki-zywy-2a','check-zywy','summary-zywy') else OUT
        stage_out.mkdir(parents=True,exist_ok=True)
        (stage_out / f'etap-port-{stage}-kod.csv').write_text(f'{code}\n', encoding='ascii')
        (stage_out / f'etap-port-{stage}-czas.csv').write_text(f'{time.monotonic() - start:.6f}\n', encoding='ascii')
    return code


if __name__ == '__main__':
    sys.exit(main())
