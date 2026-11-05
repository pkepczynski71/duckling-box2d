from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                        

                                                                            
                                                                           
                                                                              
                                                
   
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load('polaczenia_build12', 'budowa-zywy.py')
source_sums = base.old.source_sums
once = base.once


def prepare_base13(source, directory, output):
    path = HERE/'budowa-lancuchy.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    outer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build13b')
    node = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == 'project')
    context = {'base': base, 'original': base.cmake_project, 'HERE': HERE, 'Path': Path,
               'part': '13c', 'hashlib': hashlib, 'json': json}
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(path), 'exec'), context)
    original_commands = base.old.commands

    def commands(port, source_, work):
        rows = original_commands(port, source_, work)
        for item in rows:
            if Path(item['original']).name == 'contact.c':
                new = str(HERE/'kontrola-lancuchy-contact.c')
                item['arguments'][item['arguments'].index(item['file'])] = new
                item['file'] = new
        return rows

    base.old.commands = commands
    try:
        result = context['project'](HERE, source, directory, output)
    finally:
        base.old.commands = original_commands
    return {'base13_project_source': 'silnik/port/budowa-lancuchy.py',
            'base13_project_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'generated_base13': result}


def project(source, directory, output):
    source, directory, output = (Path(p).resolve() for p in (source, directory, output))
    directory.mkdir(parents=True, exist_ok=True); output.mkdir(parents=True, exist_ok=True)
    receipt = prepare_base13(source, directory, output)
                                                                 
    p = directory/'solver-base10.inc'; text = p.read_text(encoding='utf-8')
    text = text.replace('PORT13C:', 'PORT14A:')
    text = text.replace('printf("E13C %d %"PRIu32', 'printf("E14 %d %"PRIu32')
                                                                            
    old_echo = base.function(text, 'static void echo(')
                                                                            
                                                                            
    text = once(text, old_echo, old_echo.replace('static void echo(', 'static void echo_base14('))
    text = once(text, 'for(int i=0;i<3;++i)word(live[i]);\n    word(1);',
                'for(int i=0;i<3;++i)word(live[i]);\n    word(echoCount14);')
                                                                                 
    text = text.replace('||counters.jointCount', '')
    text=once(text,'if(strlen(*cursor)<8)fail(rowEof11?"INPUT_EOF":"INPUT_WORDS");',
              'if(strcspn(*cursor," ")!=8)fail(strcspn(*cursor," ")<8&&rowEof11?"INPUT_EOF":"INPUT_WORD");')
    text=once(text,'static Body public_body_number(b2BodyId raw)\n{',
              'static bool port14CanonicalBody(b2BodyId raw,Body* value);\nstatic Body public_body_number(b2BodyId raw)\n{\n    Body physical;if(port14CanonicalBody(raw,&physical))return physical;')
    text=once(text,'if(!body_live(&b))fail("live body invalid");',
              'if(!body_live(&b)&&!port14CanonicalBody(b.raw,&b))fail("live body invalid");')
    text=once(text,'if(!world_live(&w))fail("live world invalid");',
              'if(!world_live(&w)&&!port14CanonicalWorld(&w))fail("live world invalid");')
    prototype='static void dump(int id,uint32_t seq,int nR,uint32_t nJ,int qBody,int capacity);'
    text=once(text,prototype, 'static bool port14CanonicalWorld(World* owner);\n'+prototype)
    p.write_text(text, encoding='utf-8', newline='\n')
                                                                    
    p = directory/'lancuchy-base12.inc'; text = p.read_text(encoding='utf-8')
    text = once(text,'    bool valid=body_values12(o);',
                '    if(game&&(kind==0||kind==1&&!a[4])&&port14Attached(owner,reg)){reason12=2;return PARAM;}\n    bool valid=body_values12(o);')
    text=once(text,'a[4]!=4&&a[4]!=5','a[4]!=4&&a[4]!=5&&a[4]!=6')
    p.write_text(text, encoding='utf-8', newline='\n')
    hooks=(HERE/'kontrola-zywy-haki.h').read_text(encoding='utf-8')
    hooks=once(hooks,'static bool pre12(', 'static void port14PreSolveRoute(void);\nstatic bool pre12(')
    hooks=once(hooks,'            case 5:', '            case 6:port14PreSolveRoute();break;\n            case 5:')
    (directory/'kontrola-zywy-haki.h').write_text(hooks,encoding='utf-8',newline='\n')
    p = directory/'sen-solver10.inc'; text = p.read_text(encoding='utf-8')
    needle='    if(o->code==32&&dt>0&&!body_upper_fit11(port11BodyUpper(w)))return LIMIT;'
    text=once(text,needle,needle+'\n    if(o->code==32&&dt>0){uint64_t count=(uint64_t)b2GetIdCount(&w->jointIdPool);if(count>16&&count/4+3>INT16_MAX)return LIMIT;}')
    p.write_text(text, encoding='utf-8', newline='\n')
                                                                           
    original = (HERE/'kontrola-lancuchy.c').read_text(encoding='utf-8').replace('int main(int argc,char** argv)', 'int unused_transport13_entry14(int argc,char** argv)')
                                                                             
    original = once(original, 'count13[0]=1;count13[10]=saved;', 'count13[10]=saved;')
    original = once(original, 'for(int j=0;j<17;++j)word(count13[j]);',
                    'for(int j=0;j<17;++j)word(count13[j]);word(echoCount14);')
                                                                           
    (directory/'polaczenia-base13.inc').write_text(original, encoding='utf-8', newline='\n')
                                                                             
                                                            
    p = directory/'solver-base10.inc'; text = p.read_text(encoding='utf-8')
    signature = base.function(text, 'static void echo_base14(')
    text = once(text, signature, signature+'\nstatic void echo(int,uint32_t,const Operation*);')
    p.write_text(text, encoding='utf-8', newline='\n')
    p = directory/'zywy-sen11.inc'; text = p.read_text(encoding='utf-8')
    text = once(text, 'profile12==15?(o.u[3]&~24u)!=0:o.u[3]!=0',
                'profile12==15?(o.u[3]&~25u)!=0:o.u[3]!=0')
    p.write_text(text, encoding='utf-8', newline='\n')
                                                                              
                                                             
    (directory/'solver-limity10.inc').write_text('static const int limits10[156][4]={\n'+
        ',\n'.join(['{64,128,256,1328}']*156)+'\n};\n', encoding='ascii')
    p = directory/'CMakeLists.csv'; text = p.read_text(encoding='utf-8')
    text = text.replace(str(HERE/'kontrola-lancuchy.c'), str(HERE/'kontrola-polaczenia.c'))
    text += '\nset_source_files_properties("'+(source/'src/distance_joint.c').as_posix()+'" PROPERTIES COMPILE_DEFINITIONS "b2PrepareDistanceJoint=port14OriginalPrepare;b2WarmStartDistanceJoint=port14OriginalWarm;b2SolveDistanceJoint=port14OriginalSolve")\n'
    text += 'target_sources(sen11 PRIVATE "'+(HERE/'kontrola-polaczenia-observer.c').as_posix()+'")\n'
                                                                               
    text += 'target_compile_options(sen11 PUBLIC -O2)\n'
    text += 'target_compile_definitions(sen11 PUBLIC B2_VALIDATE=0)\n'
    p.write_text(text, encoding='utf-8', newline='\n')
    return receipt


def build(source, directory, output, *, coverage=False):
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
        raise ValueError('PORT14A requires native Linux x86_64')
    source, directory, output = (Path(p).resolve() for p in (source, directory, output))
    before = source_sums(source)
    frozen = norm_text(HERE/'fixtures/norms/KONTRAKT-7.json')
    if len(before) != 63 or any(f'{sha}  {name}' not in frozen for name, sha in before.items()):
        raise ValueError('Box2D 63 C/H SHA mismatch')
    receipt = {'protocol': 'PORT14A', 'source_before': before, 'commands': [], 'code': 1}
    adapters=[p for p in HERE.iterdir() if p.suffix in ('.c','.h','.py')]
    receipt['adapters_before']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in adapters}
    output.mkdir(parents=True, exist_ok=True)
    try:
        receipt['preparation'] = project(source, directory, output)
        if coverage:
            with (directory/'CMakeLists.csv').open('a', encoding='utf-8') as cmake:
                cmake.write('\ntarget_compile_options(sen11 PUBLIC --coverage -fno-inline -fno-inline-functions -fno-inline-small-functions)\n')
                cmake.write('target_link_options(sen11 INTERFACE --coverage)\n')
            receipt['coverage'] = {'enabled': True, 'no_inline': True,
                                   'gcov_directory': str(directory/'make'),
                                   'flags': ['--coverage','-fno-inline','-fno-inline-functions','-fno-inline-small-functions']}
        for name, argv in (
            ('configure', ['cmake', '-S', str(directory), '-B', str(directory/'make'), '-G', 'Unix Makefiles',
                           '-DCMAKE_BUILD_TYPE=Release', '-DBOX2D_DISABLE_SIMD=ON', '-DBOX2D_AVX2=OFF', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']),
            ('compile', ['cmake', '--build', str(directory/'make'), '--parallel', '1'])):
            start = time.monotonic()
            with (output/(name+'-stdout.csv')).open('wb') as stdout, (output/(name+'-stderr.csv')).open('wb') as stderr:
                run = subprocess.run(argv, stdout=stdout, stderr=stderr)
            receipt['commands'].append({'name': name, 'argv': argv, 'code': run.returncode, 'seconds': time.monotonic()-start})
            if run.returncode: raise RuntimeError(name+' failed; see build logs')
        receipt['compile_commands'] = json.loads((directory/'make/compile_commands.json').read_text())
                                                                             
        commands = receipt['compile_commands']
        originals = [x for x in commands if 'CMakeFiles/sen11.dir' in x['command'] and not x['file'].endswith('kontrola-polaczenia-observer.c')]
        mapping={'broad_phase.c':'kontrola-kontakty-broad.c','contact.c':'kontrola-lancuchy-contact.c',
                 'contact_solver.c':'kontrola-solver-contact.c','solver.c':'sen-solver.c','world.c':'sen-world.c'}
        expected=sorted(mapping.get(p.name,p.name) for p in (source/'src').glob('*.c'))
        actual=sorted(Path(row['file']).name for row in originals)
        if len(originals) != 35 or actual != expected: raise ValueError('35 original translation units required exactly once')
        for row in commands:
            args=shlex.split(row['command'])
            if not all(flag in args for flag in ('-std=c17','-DNDEBUG','-DBOX2D_DISABLE_SIMD','-DB2_VALIDATE=0','-fno-fast-math','-ffp-contract=off')):
                raise ValueError('native flags missing in '+row['file'])
            if [x for x in args if x.startswith('-O')][-1:]!=['-O2'] or '-ffast-math' in args:
                raise ValueError('native effective optimization/fast-math mismatch')
        symbols=subprocess.check_output(['nm','--defined-only',str(directory/'make/libsen11.a')],text=True).splitlines()
        names=('b2CreateDistanceJoint','b2DestroyJoint','b2PrepareJoint','b2WarmStartJoint','b2SolveJoint',
               'b2PrepareDistanceJoint','b2WarmStartDistanceJoint','b2SolveDistanceJoint',
               'port14OriginalPrepare','port14OriginalWarm','port14OriginalSolve')
        receipt['joint_symbols']={name:sum(line.split()[-1:]==[name] for line in symbols) for name in names}
        if any(n!=1 for n in receipt['joint_symbols'].values()):raise ValueError('missing/duplicate joint original/wrapper')
        receipt['effective_flags_verified']=True
        receipt['original_unit_mapping']={p.name:mapping.get(p.name,p.name) for p in (source/'src').glob('*.c')}
        receipt['original_unit_count'] = len(originals)
        receipt['binaries'] = {}
        for label in ('obs0', 'obs1'):
            old = output/('c11-'+label+'-bin'); binary = output/('c14a-'+label+'-bin')
            old.replace(binary)
            receipt['binaries'][label] = {'binary': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        receipt['compiler'] = subprocess.check_output(['cc', '--version'], text=True)
        receipt['code'] = 0
    except Exception as exc:
        receipt['error'] = str(exc)
        raise
    finally:
        receipt['source_after'] = source_sums(source)
        receipt['source_unchanged'] = before == receipt['source_after']
        receipt['adapters_after']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in adapters}
        receipt['adapters_unchanged']=receipt['adapters_before']==receipt['adapters_after']
        (output/'budowa-polaczenia.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
        if not receipt['source_unchanged']: raise ValueError('original sources changed')
        if not receipt['adapters_unchanged']:raise ValueError('adapter changed during C0/C1 build')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('source', 'build', 'out'): parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--coverage', action='store_true')
    args = parser.parse_args(); build(args.source, args.build, args.out, coverage=args.coverage)
