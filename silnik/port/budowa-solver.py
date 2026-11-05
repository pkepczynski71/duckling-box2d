pass                                                                              
import hashlib
import json
from pathlib import Path

FLAGS = ['-std=c17', '-D_POSIX_C_SOURCE=200809L', '-O2', '-DNDEBUG',
         '-DBOX2D_DISABLE_SIMD', '-fno-fast-math', '-ffp-contract=off']
WRAPPERS = {'world.c':'kontrola-solver-world.c', 'broad_phase.c':'kontrola-kontakty-broad.c',
            'solver.c':'kontrola-solver-solver.c', 'contact_solver.c':'kontrola-solver-contact.c'}

def once(text, before, after):
    if text.count(before) != 1:raise ValueError('adapter anchor must occur once: ' + before)
    return text.replace(before, after, 1)

def adapter(port, directory, *, population_limits=None):
    port, directory = Path(port), Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    source = (port / 'kontrola-kontakty.c').read_text(encoding='utf-8')
    header = (port / 'kontrola-kontakty9.h').read_text(encoding='utf-8')
                                                                                    
    source = once(source, '#include "kontrola-kontakty9.h"', '#include "solver-contact9.inc"')
    source = source.replace('PORT9B', 'PORT10')
    source = source.replace('moves[65]', 'moves[256]').replace('events[65]', 'events[256]')
    header = once(header, 'if(a[58]&&a[57])fail("INPUT_GAME_HIT");',
                  '/* PUBLIC10 explicitly permits game hit flags. */')
    header = once(header, 'if(e.hitCount)fail("INPUT_DOMAIN");',
                  '/* Hit values are retained by the separate HC10/HG10 transport. */')
    for index in range(3):
        header = once(header, f'bounds9[(case9-1)/4][{index}]', f'bound10({index})')
    (directory / 'solver-base10.inc').write_text(source, encoding='utf-8', newline='\n')
    (directory / 'solver-contact9.inc').write_text(header, encoding='utf-8', newline='\n')
    manifest = json.loads((port / 'solver-przypadki.json').read_bytes())
    if population_limits is not None:
        if len(population_limits)!=3 or any(type(x) is not int or x<=0 for x in population_limits):
            raise ValueError('explicit positive B/S/C limits required for the separate C-only corpus')
    rows=[(*(population_limits if population_limits is not None else
             tuple(m[k] for k in ('maxB','maxS','maxC'))),m['opMax']) for m in manifest['przypadki']]
    limits = 'static const int limits10[124][4]={\n' + ',\n'.join(
        '{' + ','.join(map(str,row)) + '}' for row in rows) + '\n};\n'
    (directory / 'solver-limity10.inc').write_text(limits, encoding='ascii')
    return {name:hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in ('solver-base10.inc','solver-contact9.inc','solver-limity10.inc')}

def source_sums(source):
    source = Path(source)
    files = sorted([*source.joinpath('src').glob('*.c'), *source.joinpath('src').glob('*.h'),
                    *source.joinpath('include/box2d').glob('*.h')])
    if len(files) != 63:raise ValueError(f'expected 63 original C/H files, got {len(files)}')
    return {p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def commands(port, source, directory):
    port, source, directory = map(Path, (port, source, directory))
    includes = ['-I'+str(port), '-I'+str(directory), '-I'+str(source/'include'), '-I'+str(source/'src')]
    units = sorted(source.joinpath('src').glob('*.c'))
    result = []
    for unit in units:
        input_ = port / WRAPPERS[unit.name] if unit.name in WRAPPERS else unit
        extra = ['-Db2CreateContact=port10OriginalCreateContact'] if unit.name == 'contact.c' else []
        obj = directory / (unit.name + '.o')
        argv = ['cc', *FLAGS, '-Wall', '-Wextra', '-Wno-unused-value', '-Wno-misleading-indentation',
                *extra, *includes, '-c', str(input_), '-o', str(obj)]
        result.append({'original':unit.relative_to(source).as_posix(), 'file':str(input_),
                       'directory':str(directory), 'arguments':argv, 'output':str(obj)})
    assert len(result) == len({r['original'] for r in result}) == 35
    return result
