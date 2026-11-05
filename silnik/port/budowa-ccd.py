pass                                                                     
import argparse
import collections
import hashlib
import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ccd_recipes', HERE / 'przypadki-ccd.py')
recipes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipes)
FLAGS = ['-std=c17', '-O2', '-g', '-DNDEBUG', '-DBOX2D_DISABLE_SIMD',
         '-ffp-contract=off', '-fno-fast-math']


def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    return {'files': len(files), 'directories': sum(p.is_dir() for p in root.rglob('*')),
            'extensions': dict(sorted(collections.Counter(p.suffix or '<none>' for p in files).items())),
            'top': dict(sorted(collections.Counter(p.relative_to(root).parts[0] for p in files).items())),
            'subdirectories': {str(d.relative_to(root)): sum(p.is_relative_to(d) for p in files)
                               for d in sorted(p for p in root.rglob('*') if p.is_dir())}}


def original_hashes(source):
    expected = {row['path']: row['sha256'] for row in recipes.manifest()['sourceHashes']}
    actual = {name: recipes.sha(source / name) for name in expected}
    if actual != expected:
        raise ValueError('Original Box2D hashes differ: ' + repr([k for k in actual if actual[k] != expected[k]]))
    return actual


def observer(source):
                                                                                  
                                                                                               
    hooks = {n: 'ccd_make(f.type,F(f.axis.x),F(f.axis.y),F(f.localPoint.x),F(f.localPoint.y))' for n in (967, 992, 1015)}
    hooks[1214] = ('ccd_after(distanceIterations,&cache,&distanceOutput)')
    hooks[1351] = 'ccd_root(distanceIterations,pushBackIterations,rootIterationCount,F(a1),F(a2),F(s1),F(s2),F(t),F(s))'
    hooks[1413] = 'ccd_final(output.state,F(output.fraction),distanceIterations)'
    lines = source.read_text().splitlines()
    out = ['#define F(x) ccd_bits(x)', '#define CAT_(a,b) a##b', '#define CAT(a,b) CAT_(a,b)']
    for n, line in enumerate(lines, 1):
        if re.search(r'\b(if\s*\(|return\b)', line) and not line.lstrip().startswith(('#', '//')):
            out.append(f'#define HOOK_{n} {hooks.get(n, '((void)0)')}')
        if re.match(r'\s*for\s*\(', line):
            hook = 'for(; (ccd_before(distanceIterations,&cache),1);)' if n == 1182 else 'for(__VA_ARGS__)'
            out.append(f'#define FOR_{n}(...) {hook}')
    out += ['#if CCD_OBS', '#define for(...) CAT(FOR_,__LINE__)(__VA_ARGS__)',
            '#define if(...) if ((CAT(HOOK_,__LINE__),(__VA_ARGS__)))',
            '#define return CAT(HOOK_,__LINE__); return', '#endif',
            '#include "distance.c"', '#undef if', '#undef return', '#undef for']
    return '\n'.join(out) + '\n'


def build(source, directory, coverage=False, no_inline=False):
    source, directory = Path(source).resolve(), Path(directory).resolve()
    if str(directory).startswith('/mnt/'):
        raise ValueError('Build must use Linux filesystem')
                                                                       
    inv = {'original': inventory(source), 'apparatus': inventory(HERE)}
    pins = original_hashes(source)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'ccd-original.inc').write_text(observer(source / 'src/distance.c'))
    m = recipes.manifest()
    rows = ','.join(str(c['operationCount']) for c in m['cases'])
    mutations = ','.join(str(c.get('copyMutation', {}).get('inputWord', 1)) for c in m['cases'])
    outputs = ','.join(str(c.get('copyMutation', {}).get('outputWord', 0)) for c in m['cases'])
    (directory / 'ccd-recipes.inc').write_text(
        f'static const unsigned ccd_counts[128]={{{rows}}};\nstatic const unsigned ccd_mut_in[128]={{{mutations}}};\nstatic const unsigned ccd_mut_out[128]={{{outputs}}};\n')
    journal = []
    for obs in (0, 1):
        flags = FLAGS + (['--coverage'] if coverage else []) + (['-fno-inline', '-fno-inline-functions'] if no_inline else [])
        binary = directory / f'ccd-c{obs}'
        command = ['gcc', *flags, f'-DCCD_OBS={obs}', '-I' + str(directory),
                   '-I' + str(source / 'include'), '-I' + str(source / 'src'),
                   str(HERE / 'kontrola-ccd.c'), str(source / 'src/math_functions.c'),
                   str(source / 'src/core.c'), '-lm', '-o', str(binary)]
        start = time.monotonic()
        r = subprocess.run(command, capture_output=True, text=True)
        journal.append({'command': command, 'exit': r.returncode, 'seconds': time.monotonic() - start,
                        'stdout': r.stdout, 'stderr': r.stderr, 'binary': str(binary),
                        'sha256': recipes.sha(binary) if r.returncode == 0 else None})
        if r.returncode:
            (directory / 'build-failure.json').write_text(json.dumps(journal, indent=2))
            raise RuntimeError(r.stderr)
        names = subprocess.check_output(['nm', '--defined-only', str(binary)], text=True).splitlines()
        if sum(line.endswith(' b2ShapeDistance') for line in names) != 1 or sum(line.endswith(' b2TimeOfImpact') for line in names) != 1:
            raise ValueError('Exactly one original distance kernel required')
    if original_hashes(source) != pins:
        raise ValueError('Original changed during build')
    receipt = {'compiler': subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
               'inventory': inv, 'sourceHashes': pins, 'pins': recipes.PINS,
               'apparatusHashes': {p.name: recipes.sha(p) for p in (HERE / 'kontrola-ccd.c', HERE / 'budowa-ccd.py', HERE / 'przypadki-ccd.py')},
               'units': ['distance.c (included once)', 'math_functions.c', 'core.c'],
               'lengthUnitsPerMeter': 1, 'B2_VALIDATE': 0, 'coverage': coverage,
               'noInline': no_inline, 'journal': journal}
    (directory / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--coverage', action='store_true')
    p.add_argument('--no-inline', action='store_true')
    a = p.parse_args()
    r = build(a.source, a.build, a.coverage, a.no_inline)
    print(json.dumps({'built': [x['binary'] for x in r['journal']], 'sourcePins': len(r['sourceHashes'])}))
