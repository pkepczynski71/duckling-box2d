from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                           
import argparse,hashlib,json,re,subprocess,time
import importlib.util,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def build13b(source,directory,output,*,part='13b'):
    pass                                                                           
    dependency=HERE/'budowa-zywy.py'
    if not dependency.is_file():raise FileNotFoundError('BASE12 integration missing: budowa-zywy.py')
    spec=importlib.util.spec_from_file_location('lancuchy_build12',dependency)
    base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
    directory,output=map(Path,(directory,output));directory.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True)
    if part=='13c':
        old_commands=base.old.commands
        def contact_commands(port,source_,directory_):
            commands=old_commands(port,source_,directory_)
            for item in commands:
                if Path(item['original']).name=='contact.c':
                    replacement=str(HERE/'kontrola-lancuchy-contact.c')
                    i=item['arguments'].index(item['file']);item['arguments'][i]=replacement;item['file']=replacement
            return commands
        base.old.commands=contact_commands
    original=base.cmake_project
    def project(port,source_,work,out):
        original(port,source_,work,out)
        work=Path(work);once=base.once
        text=(work/'solver-base10.inc').read_text(encoding='utf-8')
        raw=(HERE/'kontrola-kontakty.c').read_text(encoding='utf-8')
        text=once(text,base.function(text,'static void fail('),base.function(raw,'static void fail(').replace('PORT9B:','PORT13C:' if part=='13c' else 'PORT13B:'))
        text=text.replace('c>127','c>=127').replace('fail(physical12);line[n++]','fail("INPUT_ARITY");line[n++]')
        text=once(text,'printf("E %d %"PRIu32','printf("E13C %d %"PRIu32' if part=='13c' else 'printf("E13B %d %"PRIu32')
        text=once(text,'    else fail("unexpected public shape type");',
                  '    else if(g.type==4)g.segment=b2Shape_GetChainSegment(id).segment;\n    else fail("unexpected public shape type");')
        text=text.replace('if (g->type == 2)', 'if (g->type == 2 || g->type == 4)')
        text=once(text,'else if(g.type==2) {count=2;','else if(g.type==2||g.type==4) {count=2;')
        text=once(text,'if(code==18||code==19) {',
                  'if((code==18||code==19)&&b2Shape_GetType(shapes[y].raw)==b2_chainSegmentShape){status=PARAM;reason13=81;break;}\n                if(code==18||code==19) {')
        (work/'solver-base10.inc').write_text(text,encoding='utf-8',newline='\n')
        if part=='13c':
            contact=(work/'solver-contact9.inc').read_text(encoding='utf-8')
            contact=once(contact,base.function(contact,'void port9Request('),'''extern int port13ContactKind(int,int,bool*);
void port9Request(b2World* w,int move,int a,int b)
{
    if(nr9>=1024)fail("INPUT_POPULATION");
    bool primary=false;int kind=port13ContactKind(w->shapes.data[a].type,w->shapes.data[b].type,&primary);
    if(kind< -1)fail("INPUT_DOMAIN");
    requests9[nr9++]=(Request9){move,a,b,kind,primary,0,-1,kind<0?-1:primary?a:b,kind<0?-1:primary?b:a};
}''')
            (work/'solver-contact9.inc').write_text(contact,encoding='utf-8',newline='\n')
        driver=(HERE/'kontrola-zywy.c').read_text(encoding='utf-8')
        driver=once(driver,'int main(int argc,char** argv)','int unused_main12(int argc,char** argv)')
        guard=(HERE/'kontrola-zywy-guard.h').read_text(encoding='utf-8').replace('"GR12 1 ', '"GR13 1 ')
        (work/'lancuchy-guard12.inc').write_text(guard,encoding='utf-8',newline='\n')
        driver=once(driver,'"kontrola-zywy-guard.h"','"lancuchy-guard12.inc"')
        driver=once(driver,'    if(g->type==0)return finite_vec',
                    '    if(g->type==4)return finite_vec(g->segment.point1)&&finite_vec(g->segment.point2);\n    if(g->type==0)return finite_vec')
        driver=once(driver,'    if(kind==0&&b2Body_GetType(id)==',
                    '    if(game&&kind==0&&a[4]!=0&&w->bodies.data[id.index1-1].headChainId!=-1){reason13=80;reason12=2;return PARAM;}\n    if(kind==0&&b2Body_GetType(id)==')
        driver=once(driver,'    b2ShapeId id=shapes[reg].raw;b2BodyId parent=',
                    '    b2ShapeId id=shapes[reg].raw;if(game&&b2Shape_GetType(id)==b2_chainSegmentShape){reason13=81;reason12=2;return PARAM;}b2BodyId parent=')
        (work/'lancuchy-base12.inc').write_text(driver,encoding='utf-8',newline='\n')
        if part=='13c':
            entries=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))['przypadki']
            entries=[x for x in entries if x['profil']=='PORT13C']
            limits='static const int limits10[432][4]={\n'+',\n'.join('{'+','.join(map(str,(*(x['maksima'][key] for key in ('B','S','C')),x['opMax'])))+'}' for x in entries)+'\n};\n'
        else:limits='static const int limits10[64][4]={\n'+',\n'.join(['{16,128,0,64}']*64)+'\n};\n'
        (work/'solver-limity10.inc').write_text(limits,encoding='ascii')
        main=(work/'sen-solver10.inc').read_text(encoding='utf-8')
        main=once(main,'guardBounds[]={4,8,8}','guardBounds[]={4,16,8}')
        main=once(main,'"E","R"','"E13B","EP13B","EU13B","A13","R"')
        if part=='13c':main=once(main,'"E13B"','"E13C"')
        main=once(main,'"VR12","X"','"VR12","CN13","V13","CQ13/QL13","CS13","PC13","COPY13/CV13/CE13/ENDCOPY13","X"')
        main=once(main,'"NP12","I8"','"NP12","CH13","CI13","CM13","BH13","IP13","CG13","I8"')
        main=once(main,'"IP12","Z12"};','"IP12","Z12","I13","Z13"};')
        if part=='13c':
            main=once(main,'return profile11==7?componentBounds[field]:guardMode10?guardBounds[field]:limits10[case9-1][field];',
                'static const int chainComponentBounds[]={8,32,24};return profile12==15?chainComponentBounds[field]:profile11==7?componentBounds[field]:guardMode10?guardBounds[field]:limits10[case9-1][field];')
            main=main.replace('profile12==10&&opcode9==43','(profile12==10||profile12==15)&&opcode9==43')
            sen=(work/'zywy-sen11.inc').read_text(encoding='utf-8')
            sen=sen.replace('profile11!=7','(profile11!=7&&profile12!=15)')
            sen=once(sen,'if(o.u[3])fail("INPUT_PROFILE");','if(profile12==15?(o.u[3]&~24u)!=0:o.u[3]!=0)fail("INPUT_PROFILE");')
            (work/'zywy-sen11.inc').write_text(sen,encoding='utf-8',newline='\n')
        (work/'sen-solver10.inc').write_text(main,encoding='utf-8',newline='\n')
        project_text=(work/'CMakeLists.csv').read_text(encoding='utf-8')
        project_text=project_text.replace(str(HERE/'kontrola-zywy.c'),str(HERE/'kontrola-lancuchy.c'))
        project_text=project_text.replace('PRIVATE OBS=','PRIVATE PORT13B=1 '+('PORT13C=1 ' if part=='13c' else '')+'OBS=')
        (work/'CMakeLists.csv').write_text(project_text,encoding='utf-8',newline='\n')
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in work.glob('*.inc')}
    base.old.cmake_project=project
    receipt=base.old.build(source,directory,output)
    receipt['protocol']='PORT13C' if part=='13c' else 'PORT13B';receipt['binaries']={}
    units=base.old.commands(HERE,Path(source),directory)
    names=[Path(row['original']).name for row in units]
    expected=sorted(p.name for p in (Path(source)/'src').glob('*.c'))
    if sorted(names)!=expected or len(names)!=len(set(names)):raise ValueError('each original C unit must be compiled exactly once')
    receipt['original_units_once']=names
    symbols=subprocess.check_output(['nm','--defined-only',str(directory/'make/libsen11.a')],text=True).splitlines()
    receipt['chain_symbols']={name:sum(line.split()[-1:]==[name] for line in symbols) for name in
        ('b2CreateChain','b2DestroyChain','b2FreeChainData','b2Body_SetType','b2Shape_GetChainSegment','b2Chain_GetSegments')}
    if any(count!=1 for count in receipt['chain_symbols'].values()):raise ValueError('original chain symbol duplicated/missing')
    for label in ('obs0','obs1'):
        target=output/('c'+part+'-'+label+'-bin');(output/('c11-'+label+'-bin')).replace(target)
        receipt['binaries'][label]={'binary':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (output/('budowa-lancuchy-'+part+'.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

def build13c(source,directory,output):return build13b(source,directory,output,part='13c')
FLAGS=['-std=c17','-D_POSIX_C_SOURCE=200809L','-O2','-DBOX2D_DISABLE_SIMD','-fno-fast-math','-ffp-contract=off']
ACTIONS={('b2MakeSimplexFromCache',179):1,('b2MakeSimplexFromCache',193):2,
 ('b2SolveSimplex2',282):3,('b2SolveSimplex2',292):4,('b2SolveSimplex2',299):5,
 ('b2SolveSimplex3',352):6,('b2SolveSimplex3',360):7,('b2SolveSimplex3',370):8,
 ('b2SolveSimplex3',381):9,('b2SolveSimplex3',390):10,('b2SolveSimplex3',399):11,('b2SolveSimplex3',408):12,
 ('b2ShapeDistance',451):13,('b2ShapeDistance',509):13,('b2ShapeDistance',570):13,
 ('b2ComputeSimplexWitnessPoints',227):15,('b2ComputeSimplexWitnessPoints',232):16}

def source_sums(source):
    source=Path(source)
    files=sorted([*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),*source.joinpath('include/box2d').glob('*.h')])
    if len(files)!=63:raise ValueError('63 original C/H files required')
    return {p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def metadata(obj):
    symbols=subprocess.check_output(['nm','-n',str(obj)],text=True)
    base=int(next(x.split()[0] for x in symbols.splitlines() if x.endswith(' b2ShapeDistance')),16)
    dump=subprocess.check_output(['objdump','-dr','--line-numbers',str(obj)],text=True)
    fun='';line=-1;last=None;entries=[]
    for text in dump.splitlines():
        m=re.match(r'^\s*[0-9a-f]+ <([^>]+)>:',text)
        if m:fun=m[1]
        m=re.search(r'distance\.c:(\d+)',text)
        if m:line=int(m[1])
        m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)(.*)',text)
        if m and re.search(r'\bcall\b',m[3]):last=(int(m[1],16)+len(m[2].split()),fun,line)
        if '__sanitizer_cov_trace_pc' in text and 'R_' in text and last:
            pc,function,number=last
            if (function,number) in ACTIONS:entries.append((pc-base,ACTIONS[function,number],function,number))
    required={1,2,3,4,5,6,7,8,9,10,11,12,13,15,16}
    if set(e[1] for e in entries)!=required:raise ValueError('compiler event coverage differs from pinned metadata: '+repr(entries))
    if len({x[0] for x in entries})!=len(entries):raise ValueError('duplicate compiler PC')
    return entries

def build(source,build_dir,out_dir,profiles=('R','D')):
    source,build_dir,out_dir=map(lambda p:Path(p).resolve(),(source,build_dir,out_dir))
    if not source.joinpath('src/distance.c').is_file():raise FileNotFoundError('explicit existing Box2D source required')
    build_dir.mkdir(parents=True,exist_ok=True);out_dir.mkdir(parents=True,exist_ok=True)
    before=source_sums(source)
    frozen=norm_text(HERE/'fixtures/norms/KONTRAKT-5.json')
    if any(sha+'  '+name not in frozen for name,sha in before.items()):raise ValueError('original C/H differs from frozen Box2D8c661469 pin')
    journal=[];result={}
    def run(argv):
        start=time.monotonic();r=subprocess.run(list(map(str,argv)),capture_output=True,text=True)
        journal.append({'argv':list(map(str,argv)),'code':r.returncode,'seconds':time.monotonic()-start,'stdout':r.stdout[-16384:],'stderr':r.stderr[-16384:]})
        (out_dir/'build-journal.json').write_text(json.dumps(journal,indent=2)+'\n')
        if r.returncode:raise RuntimeError('C build failed: '+repr(journal[-1]))
        return r
    for profile in profiles:
        if profile not in ('R','D'):raise ValueError('R/D only')
        directory=build_dir/profile;directory.mkdir(parents=True,exist_ok=True)
                                                                                  
        extension=directory/'compiler-observation.cmake'
        extension.write_text('cmake_language(DEFER CALL set_source_files_properties "'+(source/'src/distance.c').as_posix()+'" TARGET_DIRECTORY box2d PROPERTIES COMPILE_OPTIONS "-O0;-g;-fsanitize-coverage=trace-pc" COMPILE_DEFINITIONS "")\n')
        flags=FLAGS+(['-DNDEBUG'] if profile=='R' else [])
        run(['cmake','-S',source,'-B',directory,'-G','Unix Makefiles','-DBUILD_SHARED_LIBS=OFF','-DBOX2D_SAMPLES=OFF','-DBOX2D_UNIT_TESTS=OFF','-DBOX2D_BENCHMARKS=OFF','-DBOX2D_DOCS=OFF','-DBOX2D_PROFILE=OFF','-DBOX2D_VALIDATE=OFF','-DCMAKE_BUILD_TYPE=','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_C_FLAGS='+' '.join(flags),'-DCMAKE_PROJECT_INCLUDE='+str(extension)])
        run(['cmake','--build',directory,'-j','2'])
        commands=json.loads((directory/'compile_commands.json').read_text())
        originals=[r for r in commands if r['file'].endswith('.c')]
        if len(originals)!=35 or len({Path(r['file']).name for r in originals})!=35:raise ValueError('original C units must be compiled once')
        objs=list(directory.rglob('distance.c.o'));libs=list(directory.rglob('libbox2d*.a'))
        if len(objs)!=1 or len(libs)!=1:raise ValueError('one distance unit and one archive required')
        entries=metadata(objs[0])
        (directory/'lancuchy-meta.inc').write_text('/* Generated from actual compiler call-site PCs; not GJK predicates. */\nstatic const struct { intptr_t offset; unsigned action; } meta13[]={\n'+''.join('{'+str(o)+','+str(a)+'},\n' for o,a,_,_ in entries)+'};\n')
        binary=out_dir/('kontrola-lancuchy-'+profile)
        run(['cc',*flags,'-DPORT13_PROFILE='+str(ord(profile)),'-I'+str(source/'include'),'-I'+str(directory),HERE/'kontrola-lancuchy.c',libs[0],'-lm','-o',binary])
        nm=run(['nm',binary]).stdout
        if sum(x.endswith(' b2ShapeDistance') for x in nm.splitlines())!=1:raise ValueError('distance must be linked once')
        result[profile]={'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'metadata':entries,'compile_commands_sha256':hashlib.sha256((directory/'compile_commands.json').read_bytes()).hexdigest()}
    after=source_sums(source)
    if before!=after:raise ValueError('original source changed')
    receipt={'profiles':result,'source_before':before,'source_after':after,'flags':FLAGS,'compiler_metadata':'distance.c O0/g/trace-pc, rest O2; observer no FP and no second GJK'}
    (out_dir/'build-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--build',required=True);p.add_argument('--out',required=True);p.add_argument('--13b',dest='chain_world',action='store_true');p.add_argument('--13c',dest='chain_contact',action='store_true');a=p.parse_args()
    print(json.dumps((build13c if a.chain_contact else build13b if a.chain_world else build)(a.source,a.build,a.out),indent=2))
