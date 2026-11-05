from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                  
import argparse
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
spec = importlib.util.spec_from_file_location('build14a_for_b', HERE/'budowa-polaczenia.py')
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
FIXED = {'src/body.c':'61fd24f3f295716a1365516447db060a14cd19cd90517f98fcb5431b12d70e24',
         'src/island.c':'d7e54a34c002b1dd759336ea3fb1d5c6ce94deda7643283f7b7591e0ebffee31',
         'src/solver_set.c':'33868ea4d9c6445a3cb0edca187c6a05eb42e185cdb112748ff44298156ba1eb'}

def build(source, directory, output, *, source_kind, coverage=False, part="B"):
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64','AMD64'):
        raise ValueError('native Linux x86_64 required')
    source, directory, output = (Path(p).resolve() for p in (source,directory,output))
    before = A.source_sums(source)
    frozen = norm_text(HERE/'fixtures/norms/KONTRAKT-7.json')
    if source_kind not in ('B0','B956','Bfix') or len(before)!=63:
        raise ValueError('explicit B0/Bfix and all63 source pins required')
    for name,sha in before.items():
        expected = (('ea9e250c131606391ad305dd00e63702685afc16d75c3fc3aad4b886757cdf07' if name=='src/body.c' and source_kind=='B956' else FIXED[name]) if source_kind in ('Bfix','B956') and name in FIXED else None)
        if (expected is not None and sha!=expected) or (expected is None and f'{sha}  {name}' not in frozen):
            raise ValueError('source pin mismatch '+name)
    output.mkdir(parents=True,exist_ok=True)
    receipt={'protocol':'PORT14'+part,'source_kind':source_kind,'source_before':before,'commands':[],
             'complete':False,'unexecuted':['configure','compile','symbols'],'coverage':coverage}
    apparatus = sorted(p for p in HERE.iterdir() if p.suffix in ('.c','.h','.inc') and p.is_file())
    receipt['apparatusSHA']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in apparatus}
    try:
        receipt['preparation']=A.project(source,directory,output)
        if part=='B':(directory/'solver-limity10.inc').write_text('static const int limits10[221][4]={\n'+',\n'.join('{64,128,256,'+str(2048 if 49<=i<=54 else 1328)+'}' for i in range(1,222))+'\n};\n',encoding='ascii')
        for file in directory.glob('*.inc'):
            text=file.read_text(encoding='utf-8');text=text.replace('PORT14A:','PORT14B:') if part=='B' else text
            file.write_text(text,encoding='utf-8',newline='\n')
        cmake=directory/'CMakeLists.csv'; text=cmake.read_text(encoding='utf-8')
        if part=='B':text=text.replace(str(HERE/'kontrola-polaczenia.c'),str(HERE/'kontrola-polaczenia-14b.c'))
        for name,prefix in ([('revolute','R'),('prismatic','P')] if part=='B' else []):
            renames=';'.join(f'b2{phase}{name.title()}Joint=port14Original{prefix}{suffix}'
                             for phase,suffix in [('Prepare','Prepare'),('WarmStart','Warm'),('Solve','Solve')])
            text+='\nset_source_files_properties("'+(source/f'src/{name}_joint.c').as_posix()+'" PROPERTIES COMPILE_DEFINITIONS "'+renames+'")\n'
        if part=='B':text+='target_compile_definitions(sen11 PUBLIC PORT14_PART_B=1)\n'
        if coverage:
            text+='target_compile_options(sen11 PUBLIC --coverage -fno-inline -fno-inline-functions -fno-inline-small-functions)\ntarget_link_options(sen11 INTERFACE --coverage)\n'
        cmake.write_text(text,encoding='utf-8',newline='\n')
        for label,argv in [('configure',['cmake','-S',str(directory),'-B',str(directory/'make'),'-G','Unix Makefiles','-DCMAKE_BUILD_TYPE=Release','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']),
                           ('compile',['cmake','--build',str(directory/'make'),'--parallel','4'])]:
            started=time.monotonic()
            with (output/(label+'.stdout')).open('wb') as out,(output/(label+'.stderr')).open('wb') as err:
                run=subprocess.run(argv,stdout=out,stderr=err)
            receipt['commands'].append({'argv':argv,'code':run.returncode,'seconds':time.monotonic()-started})
            if run.returncode: raise RuntimeError(label+' failed; see '+str(output))
            receipt['unexecuted'].remove(label)
        commands=json.loads((directory/'make/compile_commands.json').read_text())
        receipt['compile_commands']=commands
        for row in commands:
            args=shlex.split(row['command'])
            if not all(x in args for x in ('-std=c17','-DNDEBUG','-DBOX2D_DISABLE_SIMD','-DB2_VALIDATE=0','-fno-fast-math','-ffp-contract=off')) or [x for x in args if x.startswith('-O')][-1:]!=['-O2'] or '-ffast-math' in args:
                raise ValueError('effective flags '+row['file'])
        originals=[r for r in commands if 'CMakeFiles/sen11.dir' in r['command'] and not r['file'].endswith('kontrola-polaczenia-observer.c')]
        mapping={'broad_phase.c':'kontrola-kontakty-broad.c','contact.c':'kontrola-lancuchy-contact.c','contact_solver.c':'kontrola-solver-contact.c','solver.c':'sen-solver.c','world.c':'sen-world.c'}
        if sorted(Path(x['file']).name for x in originals)!=sorted(mapping.get(x.name,x.name) for x in (source/'src').glob('*.c')) or len(originals)!=35:
            raise ValueError('all35 translation units exactly once required')
        receipt['original_units']=35
        symbols=subprocess.check_output(['nm','--defined-only',str(directory/'make/libsen11.a')],text=True).splitlines()
        names=[f'b2{phase}{typ}Joint' for typ in ('Distance','Revolute','Prismatic') for phase in ('Prepare','WarmStart','Solve')]
        names += ['port14Original'+prefix+suffix for prefix in (('','R','P') if part=='B' else ('',)) for suffix in ('Prepare','Warm','Solve')]
        receipt['symbols']={name:sum(line.split()[-1:]==[name] for line in symbols) for name in names}
        if any(x!=1 for x in receipt['symbols'].values()): raise ValueError('original/wrapper symbol count')
        receipt['unexecuted'].remove('symbols');receipt['binaries']={}
        for label in ('obs0','obs1'):
            binary=output/('c14'+part.lower()+'-'+label+'-bin');(output/('c11-'+label+'-bin')).replace(binary)
            receipt['binaries'][label]={'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
        receipt['compiler']=subprocess.check_output(['cc','--version'],text=True)
        receipt['complete']=True
    except Exception as exc:
        receipt['error']=str(exc)
        raise
    finally:
        receipt['source_after']=A.source_sums(source);receipt['source_unchanged']=before==receipt['source_after']
        receipt['apparatus_unchanged']=receipt['apparatusSHA']=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in apparatus}
        (output/'budowa-14b.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        if not receipt['source_unchanged']:raise ValueError('source changed during build')
        if not receipt['apparatus_unchanged']:raise ValueError('apparatus changed during build')
    return receipt

def build_duckling(duckc, archive, out, *, workers=2, part='A'):
                                                                            
                                                                           
    spec=importlib.util.spec_from_file_location('ci14b_d_build',HERE/'ci-polaczenia.py')
    ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
    ci.OFFICIAL_SHA='f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519'
    original=HERE/'polaczenia.dk';raw=original.read_bytes();anchor=b'const PORT14_PART_B: bool = false;'
    if part not in ('A','B') or raw.count(anchor)!=1:raise ValueError('Single compile-time profile selector required')
    if part=='B':
        entry=Path(out).resolve()/'entry';entry.mkdir(parents=True,exist_ok=True)
        (entry/'polaczenia.dk').write_bytes(raw.replace(anchor,b'const PORT14_PART_B: bool = true;'))
        source_identity=ci.source_identity
        def identity():
            ci.HERE=HERE
            try:result=source_identity()
            finally:ci.HERE=entry
            result[(entry/'polaczenia.dk').relative_to(ci.ROOT).as_posix()]=hashlib.sha256((entry/'polaczenia.dk').read_bytes()).hexdigest()
            return result
        ci.HERE=entry;ci.source_identity=identity
    receipt=ci.compile_duckling(duckc,archive,out,seconds=600,workers=workers)
    receipt.update(part=part,profileSelector='PORT14_PART_B',originalEntrySHA=hashlib.sha256(raw).hexdigest(),specializedEntrySHA=receipt['driverSHA256'])
    (Path(out)/'build.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('source','build','out'):parser.add_argument('--'+name,type=Path,required=name=='out')
    parser.add_argument('--source-kind',choices=('B0','B956','Bfix'))
    parser.add_argument('--coverage',action='store_true');parser.add_argument('--part',choices=('A','B'),default='B')
    parser.add_argument('--duckc',type=Path);parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if args.duckc:
        if not args.archive:parser.error('--archive required for D')
        build_duckling(args.duckc,args.archive,args.out,part=args.part)
    else:
        if not all((args.source,args.build,args.source_kind)):parser.error('C requires --source --build --source-kind')
        build(args.source,args.build,args.out,source_kind=args.source_kind,coverage=args.coverage,part=args.part)
