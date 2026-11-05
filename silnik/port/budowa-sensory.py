pass                                                                      

                                                                             
                                                                            
   
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

HERE = Path(__file__).resolve().parent
PROBE_SHA = '9d6dac9966aa08fb6216180b0320d7737e776873f512c73f1b5f6007c87ccb07'
FLAGS = ['-std=c17', '-O2', '-DNDEBUG', '-DBOX2D_DISABLE_SIMD',
         '-DB2_VALIDATE=0', '-fno-fast-math', '-ffp-contract=off']


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_hashes(source):
    manifest = json.loads((HERE/'sensory-przypadki.json').read_bytes())
    result = []
    for item in manifest['sourceHashes']:
        name = item['path']
        path = source/name
        actual = digest(path)
        if actual != item['sha256']:
            raise ValueError(f'original source SHA mismatch: {name}')
        result.append({'file': name, 'sha256': actual})
    return result


def build(source, work, *, jobs=4):
    source, work = Path(source).resolve(), Path(work).resolve()
    if platform.system() != 'Linux' or str(work).startswith('/mnt/'):
        raise ValueError('native build requires the assigned Linux filesystem copy')
    if not 1 <= jobs <= 8:
        raise ValueError('jobs must be in 1..8')
    if source == work or source.is_relative_to(work) or work.is_relative_to(source):
        raise ValueError('build directory and original source must be disjoint')
    if digest(HERE/'kontrola-sensory-c18a.c') != PROBE_SHA:
        raise ValueError('C18a source differs from frozen original probe')
    hashes = source_hashes(source)
    work.mkdir(parents=True, exist_ok=True)
    commands = []
    start = time.monotonic()
    with (work/'build.log').open('w', encoding='utf-8') as log:
        def run(args):
            commands.append([str(x) for x in args])
            subprocess.run(args, check=True, stdout=log, stderr=subprocess.STDOUT)

                                                                                    
        project = work/'project'
        project.mkdir(exist_ok=True)
        (project/'CMakeLists.csv').write_text(
            f'cmake_minimum_required(VERSION 3.22)\nproject(sensor_c18a LANGUAGES C CXX)\nadd_subdirectory("{source}" box2d)\nset_target_properties(box2d PROPERTIES C_EXTENSIONS NO)\n',
            encoding='utf-8')
        run(['cmake', '-S', str(project), '-B', str(work/'build'),
             '-DBOX2D_SAMPLES=OFF', '-DBOX2D_UNIT_TESTS=OFF',
             '-DBOX2D_BENCHMARKS=OFF', '-DBOX2D_DOCS=OFF',
             '-DBOX2D_VALIDATE=OFF', '-DBOX2D_DISABLE_SIMD=ON',
             '-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_C_FLAGS_RELEASE=-O2 -DNDEBUG -D_POSIX_C_SOURCE=200809L -fno-fast-math -ffp-contract=off'])
        run(['cmake', '--build', str(work/'build'), '-j', str(jobs)])
        libraries = list((work/'build').rglob('libbox2d.a'))
        if len(libraries) != 1:
            raise ValueError('expected exactly one Box2D archive')
        library = work/'libprobe.a'
        library.write_bytes(libraries[0].read_bytes())
        run(['ar', 'd', str(library), 'sensor.c.o', 'shape.c.o', 'body.c.o', 'world.c.o'])
        units = []
        for module, name in enumerate(('sensor', 'shape', 'body', 'world')):
            if name == 'sensor':
                continue                                             
            original = source/'src'/f'{name}.c'
            includes = '\n'.join(line for line in original.read_text().splitlines()
                                 if line.startswith('#include'))
            unit = work/f'{name}-unit.c'
            unit.write_text(includes+'\nextern int probe_pred(int,const char*,int,int);\n'
                            '#if OBS\n#define if(...) if(probe_pred('
                            +str(module)+f',__FILE__,__LINE__,!!(__VA_ARGS__)))\n#endif\n#include "{original}"\n', encoding='utf-8')
            units.append(str(unit))
        binaries = {}
        for key, obs, coverage in (('0', 0, True), ('1', 1, True), ('1plain', 1, False)):
            binary = work/f'c18a-{key}'
            run(['gcc', *FLAGS, *(['--coverage'] if coverage else []), f'-DOBS={obs}',
                 '-I'+str(source/'include'), '-I'+str(source/'src'),
                 str(HERE/'kontrola-sensory-c18a.c'), *units, str(library), '-lm', '-o', str(binary)])
            symbols = subprocess.check_output(['nm', '--defined-only', str(binary)], text=True)
            for symbol in ('b2World_Step', 'b2DestroyBody', 'b2DestroyShape', 'b2OverlapSensors'):
                found = sum(line.split()[-1:] == [symbol] for line in symbols.splitlines())
                if found != 1:
                    raise ValueError(f'{symbol}: expected one linked definition, got {found}')
            binaries[key] = {'path': str(binary), 'sha256': digest(binary), 'gcov': coverage}
    if source_hashes(source) != hashes:
        raise ValueError('original sources changed during build')
    receipt = {'protocol': 'C18a', 'completePORT17': False,
               'seconds': time.monotonic()-start, 'commands': commands,
               'compiler': subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
               'sourceHashes': hashes, 'probeSha256': PROBE_SHA, 'binaries': binaries}
    (work/'build.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.work, jobs=args.jobs), indent=2))
