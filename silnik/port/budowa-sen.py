from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                    

                                                                               
                                                                               
   
import importlib.util
import argparse
import json
import platform
import subprocess
import time
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sen_build10', HERE / 'budowa-solver.py')
old = importlib.util.module_from_spec(spec); sys.modules[spec.name] = old; spec.loader.exec_module(old)
FLAGS = old.FLAGS
once = old.once
source_sums = old.source_sums


def adapter(port, directory):
    port, directory = Path(port), Path(directory)
    old.adapter(port, directory)
    base = (directory / 'solver-base10.inc').read_text(encoding='utf-8')
    base = base.replace('PORT10', 'PORT11')
    mapping='''    const char* oldCodes[]={"INPUT_ASCII","INPUT_CR","INPUT_EMPTY_LINE","INPUT_SPACING","INPUT_TAG","INPUT_N","INPUT_ID","INPUT_SEQ","INPUT_OPCOUNT","INPUT_DECIMAL","INPUT_ARITY","INPUT_WORD","INPUT_ENUM","INPUT_ROTATION","INPUT_REGISTER_RANGE","INPUT_REGISTER_UNINITIALIZED","INPUT_REGISTER_COLLISION"};
    const char* newCodes[]={"INPUT_HEADER","INPUT_HEADER","INPUT_HEADER","INPUT_HEADER","INPUT_HEADER","INPUT_N_RANGE","INPUT_SEQUENCE","INPUT_SEQUENCE","INPUT_SEQUENCE","INPUT_SEQUENCE","INPUT_WORDS","INPUT_WORDS","INPUT_DOMAIN","INPUT_DOMAIN","INPUT_REGISTER","INPUT_REGISTER","INPUT_REGISTER"};
    for(int j=0;j<17;++j)if(!strcmp(code,oldCodes[j])){code=newCodes[j];break;}
    if(!strcmp(code,"INPUT_FIXTURE_MANIFOLD")||!strcmp(code,"INPUT_FIXTURE_CACHE"))code="INPUT_DOMAIN";
'''
    base=once(base,'    if(output9){fclose(output9);',mapping+'    if(output9){fclose(output9);')
    base=once(base,'static char* row(FILE* file)','static bool rowEof11;\nstatic char* row(FILE* file)')
    base=once(base,'    if(c==EOF&&!n)fail("INPUT_EOF");','    rowEof11=c==EOF; if(c==EOF&&!n)fail("INPUT_EOF");')
    base = once(base, 'vec(state?sim->force:b2Vec2_zero);real(state?sim->torque:0);',
                'vec(sim->force);real(sim->torque);')
    (directory / 'solver-base10.inc').write_text(base, encoding='utf-8', newline='\n')
    contact = (directory / 'solver-contact9.inc').read_text(encoding='utf-8')
                                                                            
                                                                      
    start=contact.index('static void finish_requests9(b2World* w)\n{')
    end=contact.index('\nvoid sim9(',start)
    contact=contact[:start]+'static void finish_requests9(b2World* w)\n{\n    (void)w; population_after9();\n}\n'+contact[end:]
    contact = once(contact, 'index<(domain?12:3)', 'index<(domain?12:w->solverSetIdPool.nextIndex)')
    contact = once(contact, 'for(int s=0;s<3;++s)for(int j=0;j<w->solverSets.data[s].islandSims.count;++j)',
                   'for(int s=0;s<w->solverSetIdPool.nextIndex;++s)if(w->solverSets.data[s].setIndex==s)for(int j=0;j<w->solverSets.data[s].islandSims.count;++j)')
    (directory / 'solver-contact9.inc').write_text(contact, encoding='utf-8', newline='\n')
    manifest = json.loads((port / 'sen-przypadki.json').read_bytes())
    limits = 'static const int limits10['+str(manifest['N'])+'][4]={\n' + ',\n'.join(
        '{' + ','.join(str(m[k]) for k in ('maxB','maxS','maxC','opMax')) + '}'
        for m in manifest['przypadki']) + '\n};\n'
    (directory / 'solver-limity10.inc').write_text(limits, encoding='ascii')
    main = (port / 'kontrola-solver.c').read_text(encoding='utf-8')
    main = once(main, 'int main(int argc,char** argv)', 'int unused_main10(int argc,char** argv)')
    main = once(main, 'return guardMode10?guardBounds[field]:limits10[case9-1][field];',
                'static const int componentBounds[]={8,16,16};return profile11==7?componentBounds[field]:guardMode10?guardBounds[field]:limits10[case9-1][field];')
    main = once(main, 'if(!strcmp(tokens[0],"Z9")&&i==15){replacement=true;value=guardMode10?4:3;}',
                'if(!strcmp(tokens[0],"Z9")&&i==15){replacement=true;value=profile11;}')
    main = once(main, 'if(!strcmp(tokens[0],"Z9")&&i==16){replacement=true;value=guardMode10&&guardSeedApplied10;}',
                'if(!strcmp(tokens[0],"Z9")&&i==16){replacement=true;value=fixture11;}')
    main = once(main, '"HC10/HG10","X"', '"HC10/HG10","SW11","GS11","X"')
    main = once(main, '"BV10","I8"',
                '"BV10","WS11","BS11","SS11","SD11","SM11","AB11","TR11","SP11","SF11","BP11","BF11","I8"')
    main = once(main, '"I10","Z8","Z9","Z10"', '"I10","I11","Z8","Z9","Z10","Z11"')
    main = once(main,'if(count!=expected)fail("INPUT_ARITY");',
                'if(count!=expected)fail(rowEof11?"INPUT_EOF":"INPUT_WORDS");')
    main = once(main,'if(o.u[1]>1||(code==54&&o.u[10]>1))fail("INPUT_BOOL");',
                'if(code==54&&o.u[1]>1)fail("INPUT_MODE");if((code==55&&o.u[1]>1)||(code==54&&o.u[10]>1))fail("INPUT_BOOL");')
    main = once(main, 'static int rank10(const char* tag)\n{',
                'static int rank10(const char* tag)\n{\n    if(!strcmp(tag,"TASK")&&profile11==7)return 0;')
    main = once(main, 'if(!strcmp(tag,"TASK")){p=end+1;continue;}',
                'if(!strcmp(tag,"TASK")&&profile11!=7){p=end+1;continue;}')
    main = once(main, 'if(!strcmp(tokens[0],"I9")&&(i==20||i==21))',
                'if(profile11!=7&&!strcmp(tokens[0],"I9")&&(i==20||i==21))')
    main = once(main, 'port10OriginalCreateContact(w,a,b);',
                'int existed=find_contact9(w,a->id,b->id); uint64_t issuedBefore=lastIssued; port10OriginalCreateContact(w,a,b); if(existed>=0||lastIssued!=issuedBefore)return;')
                                                                              
    main = once(main, 'body_blocks_fit10((uint64_t)w->solverSets.data[b2_awakeSet].bodySims.count)',
                'body_upper_fit11(port11BodyUpper(w))')
                                                                  
    guard = once((port / 'kontrola-solver-guard.h').read_text(encoding='utf-8'),
                 'printf("GR10 1 %"', 'printf("GR11 1 %"')
    (directory / 'sen-guard10.inc').write_text(guard, encoding='utf-8', newline='\n')
    main = once(main, '#include "kontrola-solver-guard.h"', '#include "sen-guard10.inc"')
    (directory / 'sen-solver10.inc').write_text(main, encoding='utf-8', newline='\n')
    solver = (port / 'kontrola-solver-solver.c').read_text(encoding='utf-8')
    solver += '\nvoid port11CaptureFinalize(b2TaskCallback* task,void* context) { if(task==b2FinalizeBodiesTask)port11AfterFinalize(((b2StepContext*)context)->world); }\n'
    solver = '#include "kontrola-sen11.h"\n' + solver
    (directory / 'sen-solver.c').write_text(solver, encoding='utf-8', newline='\n')
    world = (port / 'kontrola-solver-world.c').read_text(encoding='utf-8')
    world = once(world, 'port10CaptureSolver(task,context);',
                 'port10CaptureSolver(task,context); port11CaptureFinalize(task,context);')
    (directory / 'sen-world.c').write_text('#include "kontrola-sen11.h"\n' + world, encoding='utf-8', newline='\n')
    return {name: old.hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in
            ('solver-base10.inc','solver-contact9.inc','solver-limity10.inc','sen-solver10.inc','sen-guard10.inc','sen-solver.c','sen-world.c')}


def commands(port, source, directory):
    commands_ = old.commands(port, source, directory)
    directory = Path(directory)
    for item in commands_:
        name = Path(item['original']).name
        replacement = {'world.c':directory/'sen-world.c', 'solver.c':directory/'sen-solver.c'}.get(name)
        if replacement:
            i = item['arguments'].index(item['file']); item['arguments'][i] = str(replacement); item['file'] = str(replacement)
        renames = {'solver_set.c': ['-Db2WakeSolverSet=port11OriginalWakeSolverSet', '-Db2TrySleepIsland=port11OriginalTrySleepIsland'],
                   'island.c': ['-Db2SplitIsland=port11OriginalSplitIsland',
                                '-Db2SplitIslandTask=port11OriginalSplitIslandTask']}.get(name, [])
        item['arguments'][1:1] = renames
    return commands_


def cmake_project(port, source, directory, output):
    pass                                                                  
    port, source, directory, output = (Path(x).resolve() for x in (port,source,directory,output))
    specialized = adapter(port,directory)
    units = commands(port,source,directory)
    quote = lambda p: '"'+str(p).replace('\\','/')+'"'
    text = ['cmake_minimum_required(VERSION 3.22)', 'project(sen11 LANGUAGES C)',
            'set(CMAKE_C_STANDARD 17)', 'set(CMAKE_C_STANDARD_REQUIRED ON)',
            'set(CMAKE_C_EXTENSIONS OFF)',
            'set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)',
            'if(NOT BOX2D_DISABLE_SIMD OR BOX2D_AVX2)', 'message(FATAL_ERROR "scalar profile required")','endif()',
            'add_library(sen11 STATIC '+ ' '.join(quote(r['file']) for r in units)+')',
            'target_include_directories(sen11 PUBLIC '+ ' '.join(map(quote,(directory,port,source/'include',source/'src')))+')',
            'target_compile_definitions(sen11 PUBLIC NDEBUG BOX2D_DISABLE_SIMD _POSIX_C_SOURCE=200809L)',
            'target_compile_options(sen11 PUBLIC -fno-fast-math -ffp-contract=off -Wno-unused-value -Wno-misleading-indentation)']
    for item in units:
        defines = [a[2:] for a in item['arguments'] if a.startswith('-Db2')]
        if defines:text += ['set_source_files_properties('+quote(item['file'])+' PROPERTIES COMPILE_DEFINITIONS "'+';'.join(defines)+'")']
    for label,obs in (('obs0',0),('obs1',1)):
        target='c11-'+label+'-bin'
        text += ['add_executable('+target+' '+quote(port/'kontrola-sen.c')+')',
                 'target_compile_definitions('+target+' PRIVATE OBS='+str(obs)+')',
                 'target_link_libraries('+target+' PRIVATE sen11 m)',
                 'set_target_properties('+target+' PROPERTIES RUNTIME_OUTPUT_DIRECTORY '+quote(output)+')']
    (directory/'CMakeLists.csv').write_text('\n'.join(text)+'\n',encoding='utf-8')
    return specialized


def build(source,directory,output):
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
        raise ValueError('normative11 requires native Linux x86_64')
    source,directory,output=map(Path,(source,directory,output))
    output.mkdir(parents=True,exist_ok=True);directory.mkdir(parents=True,exist_ok=True)
    for side in ('obs0','obs1'):(output/('c11-'+side+'-bin')).unlink(missing_ok=True)
    before=source_sums(source)
    contract=norm_text(HERE/'fixtures/norms/KONTRAKT-7.json')
    if any(f'{digest}  {name}' not in contract for name,digest in before.items()):
        raise ValueError('original Box2D source mismatch against contract7')
    receipt={'source_before':before,'commands':[],'specialized':cmake_project(HERE,source,directory,output)}
    try:
        for name,argv in (
            ('configure',['cmake','-S',str(directory),'-B',str(directory/'make'),'-G','Unix Makefiles',
                          '-DCMAKE_BUILD_TYPE=Release','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']),
            ('compile',['cmake','--build',str(directory/'make'),'--parallel','1'])):
            start=time.monotonic()
            with (output/(name+'-stdout.csv')).open('wb') as stdout,(output/(name+'-stderr.csv')).open('wb') as stderr:
                result=subprocess.run(argv,stdout=stdout,stderr=stderr)
            receipt['commands'].append({'argv':argv,'code':result.returncode,'seconds':time.monotonic()-start})
            if result.returncode:raise RuntimeError(name+' failed: '+str(result.returncode))
        result=subprocess.run(['nm','--defined-only',str(directory/'make/libsen11.a')],capture_output=True,text=True,check=True)
        symbols=result.stdout.splitlines()
        required=('b2World_Step','b2Solve','b2UpdateBroadPhasePairs','b2PrepareContactsTask',
                  'port11OriginalWakeSolverSet','port11OriginalTrySleepIsland','port11OriginalSplitIsland',
                  'port11OriginalSplitIslandTask','port10OriginalCreateContact')
        receipt['symbols']={name:sum(line.split()[-1:]==[name] for line in symbols) for name in required}
        if any(v!=1 for v in receipt['symbols'].values()):raise ValueError('original symbol duplicated/missing')
        includes=['-I'+str(directory),'-I'+str(HERE),'-I'+str(source/'include'),'-I'+str(source/'src')]
        macros=subprocess.run(['cc',*FLAGS,*includes,'-dM','-E',str(HERE/'kontrola-solver-contact.c')],capture_output=True,text=True,check=True).stdout
        defines={}
        for line in macros.splitlines():
            words=line.split(maxsplit=2)
            if len(words)>=2 and words[0]=='#define':defines[words[1]]=words[2] if len(words)>2 else ''
        if defines.get('B2_SIMD_WIDTH')!='4' or 'B2_SIMD_NONE' not in defines or 'BOX2D_AVX2' in defines or defines.get('B2_VALIDATE')!='0':
            raise ValueError('actual scalar width4 Release preprocessor profile mismatch')
        receipt['actual_macros']={name:defines.get(name) for name in ('B2_SIMD_WIDTH','B2_SIMD_NONE','BOX2D_DISABLE_SIMD','BOX2D_AVX2','B2_VALIDATE','NDEBUG')}
        receipt['platform']=platform.uname()._asdict()
        receipt['compile_commands']=json.loads((directory/'make/compile_commands.json').read_bytes())
        receipt['compiler_version']=subprocess.run(['cc','--version'],capture_output=True,text=True,check=True).stdout
        receipt['code']=0
    except Exception as exc:
        receipt['code']=1;receipt['error']=str(exc);raise
    finally:
        receipt['source_after']=source_sums(source)
        receipt['unchanged']=receipt['source_after']==before
        (output/'budowa-sen.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not receipt['unchanged']:raise ValueError('original sources changed')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.source,args.build,args.out)
