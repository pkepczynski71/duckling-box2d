from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                        

                                                                            
                                                                         
   
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

RECIPE_COUNT=53

def init(context):
    global C,OUT,PORT,ROOT,g,p
    C=context;OUT=C.OUT;PORT=C.PORT;ROOT=C.ROOT
    g=C.world_module('przypadki-ruch-swiata.py','ci_motion_inputs')
    p=C.world_module('porownaj-ruch-swiata.py','ci_motion_compare')
                                                                         
                                                                            
    sys.argv[1]='ruch8'

def code(name):return C.shape_code(name)

def json_file(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def source_sums():
    source=C.base.TEMP/'box2d'
    files=sorted([*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),*source.joinpath('include/box2d').glob('*.h')])
    inventory={'source':str(source),'count':len(files),'files':[path.relative_to(source).as_posix() for path in files]}
    json_file('box2d-ruch-swiata-inwentarz.json',inventory)
    if len(files)!=63:
        print(json.dumps(inventory,indent=2),flush=True)
        raise C.base.StepFailed(f'Krok 8: original must contain 63 C/H files; found {len(files)} in {source}')
    sums={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    contract=norm_text(PORT/'fixtures/norms/KONTRAKT-7.json')
    lines=''.join(f'{digest}  {Path(path).relative_to(source).as_posix()}\n' for path,digest in sums.items())
    if any(line not in contract for line in lines.splitlines()):raise C.base.StepFailed('Krok 8: original source hash mismatch')
    expected=(C.base.TEMP.parent/'box2d-port7-sha256.csv').read_text(encoding='ascii')
    if len(expected.splitlines())!=63 or lines!=expected:
        raise C.base.StepFailed('Krok 8: restored source differs from the 63 hashes measured by port')
    (OUT/'box2d-port7-sha256.csv').write_text(expected,encoding='ascii')
    library=C.base.CACHE/'box2d/lib/libbox2d.a'
    sums[str(library)]=hashlib.sha256(library.read_bytes()).hexdigest()
    return sums

def unchanged(sums):
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest for path,digest in sums.items()):
        raise C.base.StepFailed('Krok 8: source/library changed')

def run(name,binary,data=b'',c_side=False,seconds=45,unbuffered=False):
    if not binary.is_file():raise C.base.StepFailed('Krok 8: missing executable '+str(binary))
    directory=OUT/'wejscia-ruch-swiata';directory.mkdir(exist_ok=True)
    path=directory/(name+'.csv');path.write_bytes(data)
    command=[binary,path] if c_side else ['bash','-c','exec '+('stdbuf -o0 ' if unbuffered else '')+'"$1" < "$2"','motion-stdin',binary,path]
    value=C.base.run(name+'-wykonanie',command,stdout=OUT/(name+'.csv'),seconds=seconds)
    return value,OUT/(name+'.csv'),OUT/(name+'-wykonanie-stderr.csv')

def run_full(name,binary,path,c_side=False,seconds=600):
    command=[binary,path] if c_side else ['bash','-c','exec "$1" < "$2"','motion-full-stdin',binary,path]
    return C.base.run(name,command,stdout=OUT/(name+'.csv'),seconds=seconds)

def check_files(left,right,rows,guard=False,private=True):
    errors=[]
    for name,path in (('C',left),('Duckling',right)):
        with path.open(encoding='ascii',newline='') as stream:
            try:p.validate_output(stream,rows,private=private,guard=guard)
            except (ValueError,KeyError,IndexError) as exc:errors.append(name+': '+str(exc))
    if not errors:
        with left.open(encoding='ascii',newline='') as a,right.open(encoding='ascii',newline='') as b:
            diff=p.first_difference(a,b)
            if diff:errors.append(diff)
    return errors

def comparison(name,input_name,c_name,d_name,c0_name,*,small=False,guard=False):
    command=[sys.executable,'-B',PORT/'porownaj-ruch-swiata.py','--c',OUT/(c_name+'.csv'),
        '--c-bez',OUT/(c0_name+'.csv'),'--duckling',OUT/(d_name+'.csv'),'--wejscie',OUT/input_name,
        '--kod-c',code(c_name),'--kod-c-bez',code(c0_name),'--kod-wyjscia',code(d_name),
        '--raport',OUT/(name+'.md')]
    if small:command.append('--small')
    if guard:command.append('--guard')
    return C.base.run(name,command,seconds=180 if small or guard else 1200)

def sample():
    C.base.need('generator-ruch-swiata',[sys.executable,'-B',PORT/'przypadki-ruch-swiata.py','--katalog',OUT],seconds=45)
    forecast=p.measure(g.cases());json_file('ruch-swiata-limity.json',forecast)
    before=source_sums();json_file('box2d-ruch-swiata-sha256.json',before)
    source=C.base.TEMP/'box2d';library=C.base.CACHE/'box2d/lib/libbox2d.a'
    for suffix,obs,guard in (('',1,0),('-bez',0,0),('-guard',1,1),('-guard-bez',0,1)):
        name='kontrola-ruch-swiata'+suffix;binary=OUT/(name+'-bin')
        C.base.need(name+'-kompilacja',['cc','-std=c17','-O2','-Wall','-Wextra','-Werror','-DNDEBUG',
            '-DBOX2D_DISABLE_SIMD','-DOBS='+str(obs),'-DGUARD8='+str(guard),'-fno-fast-math','-ffp-contract=off',
            '-I'+str(source/'include'),'-I'+str(source/'src'),PORT/'kontrola-ruch-swiata.c',library,'-lm','-o',binary],seconds=45)
    driver=PORT/'ruch-swiata.dk'
    if not driver.is_file():raise C.base.StepFailed('Step8 transport entry point is missing')
    duck=C.compile_world_fixture(C.world_duckc(),'duckling-ruch-swiata',driver,ROOT/'silnik/fizyka')
    stats=[]
    for name,binary,input_name,c_side in (
        ('c-ruch-swiata-proba',OUT/'kontrola-ruch-swiata-bin','proba-ruch-swiata.csv',True),
        ('c-ruch-swiata-proba-bez',OUT/'kontrola-ruch-swiata-bez-bin','proba-ruch-swiata.csv',True),
        ('duckling-ruch-swiata-proba',duck,'proba-ruch-swiata-stdin.csv',False)):
        start=time.monotonic()
        command=[binary,OUT/input_name] if c_side else ['bash','-c','exec "$1" < "$2"','motion-sample',binary,OUT/input_name]
        C.base.need(name,command,stdout=OUT/(name+'.csv'),seconds=60)
        seconds=time.monotonic()-start;size=(OUT/(name+'.csv')).stat().st_size
        stats.append({'name':name,'bytes':size,'seconds':seconds,
                      'ceiling_seconds_linear_estimate':seconds*forecast['obs1_bytes_upper_bound']/max(1,size)})
    free=shutil.disk_usage(C.base.TEMP).free
    json_file('ruch-swiata-proba-pomiar.json',{'streams':stats,'free_bytes':free,'forecast':forecast})
    text=['# E33e6de651289 E318a09570e1d E434f66e44101 8','','| Strumień | Bajty | Sekundy |','|---|---:|---:|']
    text += [f'| {row['name']} | {row['bytes']} | {row['seconds']:.6f} |' for row in stats]
    text += ['',f'Wolne miejsce: {free} B; Ebfcc0ff1abe2 E66a1a48ae5aa Ed9959ff03720 E3ab717745a40: {forecast['three_streams_bytes_upper_bound']} B.',
             'E1efa978df191 Ea3fe81deb86e Eb1f0a70f8c9b E35e99f929e01 E95615b3a8d39: E360e5aa9cc7f Ecced28c6dc3f Eb6a3fcb95ca2 Ede7d1b721a1e Ecd5b158f21b7 E571ee8978e85 E6eb1f08a5a32 65 E9a747e5e7c0b. Eff624a4b9cdb E42a2184b6cbc E1bda60b69899 E55ea09e5715d 600 E043a718774c5 E62e6920c82a8.','']
    (OUT/'PROBA-RUCH-SWIATA.md').write_text('\n'.join(text),encoding='utf-8')
    unchanged(before)
    result=comparison('POROWNANIE-RUCH-SWIATA-PROBA','proba-ruch-swiata.csv','c-ruch-swiata-proba','duckling-ruch-swiata-proba','c-ruch-swiata-proba-bez',small=True)
                                                                          
                                                                               
    if free<forecast['three_streams_bytes_upper_bound']+2*1024**3:
        (OUT/'PYTANIE-RUCH-SWIATA.md').write_text('STATUS: PYTANIE — E35e438385930 E168390eb54f6 Efa360362903c E003a8cb6dbd7 Edf53be407226 Ed5d6891f39dd; Ecd5b158f21b7 E58e397f42095 64 E1f28d2f749ee, 600 E2db1fbdaf6e9 E33dcc1a09b95 E19358a3fa806.\n',encoding='utf-8')
        return 1
    return result

def c_side():
    if code('etap-port-proba-ruch-swiata')!=0:raise C.base.StepFailed('Krok 8: full run requires successful small trial')
    before=source_sums();bad=0
    for suffix in ('','-bez'):
        bad|=bool(run_full('c-ruch-swiata'+suffix,OUT/('kontrola-ruch-swiata'+suffix+'-bin'),OUT/'przypadki-ruch-swiata.csv',True))
    unchanged(before);return int(bad)

def duckling():
    if code('etap-port-proba-ruch-swiata')!=0:raise C.base.StepFailed('Krok 8: full run requires successful small trial')
    return run_full('duckling-ruch-swiata',OUT/'duckling-ruch-swiata-bin',OUT/'przypadki-ruch-swiata-stdin.csv')

def check():
    result=comparison('POROWNANIE-RUCH-SWIATA','przypadki-ruch-swiata.csv','c-ruch-swiata','duckling-ruch-swiata','c-ruch-swiata-bez')
    tests=C.base.run('sprawdziany-ruch-swiata',[sys.executable,'-B','-m','unittest','discover','-s','silnik/port','-p','test_ruch_swiata*.py','-v'],seconds=240,
        env={**os.environ,'RUCH_SWIATA_C_BIN':str(OUT/'kontrola-ruch-swiata-bin'),'RUCH_SWIATA_REQUIRE_PRODUCT':'1'})
    return int(bool(result or tests))

def assertions():
    source=C.base.TEMP/'box2d';build=C.base.TEMP/'box2d-assert8-build'
    C.base.need('assert8-configure',['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Debug',
        '-DBUILD_SHARED_LIBS=OFF','-DBOX2D_SAMPLES=OFF','-DBOX2D_UNIT_TESTS=OFF','-DBOX2D_BENCHMARKS=OFF',
        '-DBOX2D_DOCS=OFF','-DBOX2D_PROFILE=OFF','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF','-DBOX2D_VALIDATE=OFF'],seconds=60)
    C.base.need('assert8-build',['cmake','--build',build,'--target','box2d','--parallel','2'],seconds=180)
    libraries=list(build.rglob('libbox2dd.a'))
    if len(libraries)!=1:raise C.base.StepFailed('ASSERT8: expected one Debug library libbox2dd.a; found '+repr([str(p) for p in libraries]))
    binary=OUT/'kontrola-ruch-swiata-asercje-bin'
    C.base.need('assert8-link',['cc','-std=c17','-O0','-Wall','-Wextra','-Werror','-fno-fast-math','-ffp-contract=off',
        '-I'+str(source/'include'),PORT/'kontrola-ruch-swiata-asercje.c',libraries[0],'-lm','-o',binary],seconds=30)
    results=[]
    for word,n in (('7fc00001',1),('7fe12345',1),('7f800000',1),('ff800000',1),('3e800000',0),('3e800000',-1),('3e800000',-2147483648)):
        name='assert8-'+word+'-'+str(n);actual=C.base.run(name,[binary,word,str(n)],seconds=15)
        wanted=86 if word!='3e800000' else 87
        diag=b'ASSERT8: b2IsValidFloat( timeStep )\n' if wanted==86 else b'ASSERT8: 0 < subStepCount\n'
        valid=actual==wanted and (OUT/(name+'-stderr.csv')).read_bytes()==diag
        results.append({'name':name,'expected':wanted,'actual':actual,'ok':valid})
    json_file('asercje-ruch-swiata-wynik.json',results)
    return not all(row['ok'] for row in results)

def probes():
    before=source_sums();results=[];bad=False
    for name,binary,c_side,input_name in (
        ('c-guard8',OUT/'kontrola-ruch-swiata-guard-bin',True,'guard8.csv'),
        ('c-guard8-bez',OUT/'kontrola-ruch-swiata-guard-bez-bin',True,'guard8.csv'),
        ('duckling-guard8',OUT/'duckling-ruch-swiata-bin',False,'guard8-stdin.csv')):
        bad|=bool(run_full(name,binary,OUT/input_name,c_side,60))
    bad|=bool(comparison('POROWNANIE-GUARD8','guard8.csv','c-guard8','duckling-guard8','c-guard8-bez',guard=True))
    negative=C.world_module('ujemne-ruch-swiata.py','ci_motion_negative')
    for name,cdata,ddata,cdiag,ddiag in negative.variants():
        for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
            tag='ruch8-ujemny-'+name+'-'+side
            actual,path,err=run(tag,OUT/('kontrola-ruch-swiata-bin' if side=='c' else 'duckling-ruch-swiata-bin'),data,side=='c',15)
            valid=actual==wanted and err.read_bytes()==diag
            results.append({'name':tag,'expected':wanted,'actual':actual,'diagnostic':diag.decode('ascii'),'ok':valid});bad|=not valid
    for suffix in ('','-bez','-guard','-guard-bez'):
        for option,output in (('--test-tickets',b'BILETY OK\n'),('--test-blocks',b'BLOKI OK\n')):
            name='ruch8-c-fixture'+suffix+option
            actual=C.base.run(name,[OUT/('kontrola-ruch-swiata'+suffix+'-bin'),option],seconds=30)
            valid=actual==0 and (OUT/(name+'.csv')).read_bytes()==output and not (OUT/(name+'-stderr.csv')).read_bytes()
            results.append({'name':name,'expected':0,'actual':actual,'ok':valid});bad|=not valid
    binary=C.compile_world_fixture(C.world_duckc(),'ruch8-bilety',PORT/'proba-ruch-swiata-bilety.dk',ROOT/'silnik/fizyka')
    actual,path,err=run('ruch8-bilety',binary)
    valid=actual==0 and path.read_bytes()==b'RUCH SWIATA BILETY OK\n' and not err.read_bytes()
    results.append({'name':'ruch8-bilety','expected':0,'actual':actual,'ok':valid});bad|=not valid
    bad|=assertions();unchanged(before)
    json_file('proby-ruch-swiata-wynik.json',results)
    return int(bad)

def detection(recipe,actual,path,err,reference,rows):
    if actual in (124,125,126,127):return False,'timeout/infrastructure'
    stderr=err.read_bytes()
    if recipe['probe']=='fixture':
        wanted=recipe['expected_code']
        if recipe.get('expected_signal')==6:
                                                                             
                                                                            
            valid=(actual in (-6,134) and path.read_bytes()==b'Program panicked!\n'
                   and stderr in (b'',b'timeout: the monitored command dumped core\n'))
            return valid,f'fixture checked bounds panic {actual}, expected SIGABRT with exact message'
        return actual==wanted and not stderr and not path.read_bytes(),f'fixture exit {actual}, expected {wanted}'
    if recipe.get('panic_at_witness'):
                                                                           
                                                                                
                                                                               
        if actual not in (-6,134) or stderr not in (b'',b'timeout: the monitored command dumped core\n'):
            return False,'expected checked panic at the shapeBody witness'
        case=rows[-1];target=p.format_record('E',(case.id,len(case.ops),*case.ops[-1])).encode('ascii')
        if case.ops[-1][0]!=39:return False,'wrong shapeBody witness opcode'
        with reference.open('rb') as expected,path.open('rb') as produced:
            while True:
                line=expected.readline(p.MAX_LINE+1)
                if not line or len(line)>p.MAX_LINE or produced.readline(p.MAX_LINE+1)!=line:
                    return False,'panic prefix differs before the exact shapeBody witness'
                if line==target:
                    valid=produced.readline(p.MAX_LINE+1)==b'Program panicked!\n' and not produced.read(1)
                    return valid,f'checked shapeBody panic at id {case.id}, seq {len(case.ops)}, opcode 39'
    if actual<0:return False,'unexpected native signal'
    if actual:
        diag=recipe.get('diagnostic','').encode('ascii')
        if actual!=4 or not diag or stderr!=diag:return False,'unexpected native failure'
        last=None
        with path.open(encoding='ascii',newline='') as stream:
            for line in stream:
                if line.startswith('E '):last=p.parse_record(line)[1]
        allowed=recipe.get('failure_opcode',3 if recipe['class_id']==15 else 38)
        echoed=False
        if last is not None:
            cases={c.id:c for c in rows};case=cases.get(last[0]);seq=last[1]
            echoed=case is not None and 1<=seq<=len(case.ops) and tuple(last[2:])==case.ops[seq-1]
            if recipe['class_id']==18:echoed=echoed and case.id==rows[-1].id and seq==len(case.ops)
        return echoed and last[2]==allowed,repr(diag)+' at '+repr(last[:3] if last else None)
    if stderr:return False,'unexpected stderr'
    errors=[]
    with path.open(encoding='ascii',newline='') as stream:
        try:p.validate_output(stream,rows,guard=recipe['probe']=='guard')
        except (ValueError,KeyError,IndexError) as exc:errors.append(str(exc))
    with reference.open(encoding='ascii',newline='') as a,path.open(encoding='ascii',newline='') as b:
        window={}
        try:diff=p.first_difference(a,b,window=window)
        except (ValueError,KeyError,IndexError) as exc:diff=str(exc)
        if diff:errors.append(diff)
    if recipe['class_id']==18 and errors and 'record R, field status' not in errors[0]:
        return False,'numeric guard failed for an unrelated reason: '+errors[0]
    return bool(errors),' | '.join(errors[:2])

def solver_replacement_result(recipe,mutate):
                                                                                 
    if recipe.get('solver_replacement')!='A8-27':raise C.base.StepFailed('unapproved step8 solver replacement')
    row=mutate.run_solver_replacement(C,recipe)
    if row.get('name')!=recipe['name'] or row.get('class_id')!=recipe['class_id'] or row.get('approval')!='A8-27':
        raise C.base.StepFailed('step8 solver replacement identity changed')
    return {**row,'actual':row['code'],'detail':row.get('difference'),'reference':None}

def solver_replacement_evidence(recipe,row):
    if recipe.get('solver_replacement')!='A8-27' or row.get('approval')!='A8-27':return False
    native=C.world_module('mutacje-solver.py','ci_motion_successor_evidence')
    data=native.group_for(native.replacement_recipe(recipe)).encode(True)
    if row.get('name')!=recipe['name'] or row.get('class_id')!=recipe['class_id']:return False
    if row.get('input_sha256')!=hashlib.sha256(data).hexdigest():return False
    if not (row.get('detected') and row.get('clean') and row.get('replayed_before_compaction') and row.get('difference')):return False
    if row.get('baseline_code')!=0 or row.get('code')!=0 or row.get('actual')!=0:return False
    name='mutation10-'+recipe['name']
    if code('oslony-profile4-kompilacja') or code(name+'-kompilacja'):return False
    for suffix in ('-base',''):
        tag=name+suffix
        if code(tag+'-wykonanie') or (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes():return False
        if (OUT/'wejscia-swiat'/(tag+'.csv')).read_bytes()!=data:return False
        stream=json.loads((OUT/(tag+'-stream.json')).read_bytes())
        if not stream.get('sha256') or stream.get('bytes',0)<=0 or stream.get('records',{}).get('END')!=1:return False
        if stream.get('validation_before_compaction')!='native clean difference replayed from disk':return False
    before=json.loads((OUT/'oslony-produkt-przed-sha256.json').read_bytes())
    after=json.loads((OUT/'oslony-produkt-po-sha256.json').read_bytes())
    return bool(before) and before==after and all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in after.items())

def mutation_probe(recipe):
                                                                              
                                                                               
                                                                                
    exits={'game-step-parameters-bypassed':2,'copy-object-id-lost':3,'step-world-life':2}
    if recipe['name'] not in exits:return recipe
    if recipe['source']!='silnik/fizyka/gra.dk' or recipe['scope']!='step':
        raise C.base.StepFailed('Krok 8: real step witness target changed')
    return {**recipe,'probe':'fixture','expected_code':exits[recipe['name']]}


def mutations():
    if code('etap-port-proba-ruch-swiata')!=0:raise C.base.StepFailed('Krok 8: mutations require successful small trial')
    recipes=json.loads((PORT/'mutacje-ruch-swiata.json').read_bytes())['native_mutations']
    if len(recipes)!=RECIPE_COUNT or {r['class_id'] for r in recipes}!=set(range(1,23)):raise C.base.StepFailed('Krok 8: missing mutation recipes/classes')
    mutate=C.world_module('mutacje-ruch-swiata.py','ci_motion_mutate')
    physics=ROOT/'silnik/fizyka';driver=PORT/'ruch-swiata.dk'
    protected=[*physics.rglob('*.dk'),driver,PORT/'proba-ruch-swiata-bilety.dk']
    before={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    bases={};results=[];started=time.monotonic()
    try:
        for recipe in recipes:
            if time.monotonic()-started>5400:raise C.base.StepFailed('Krok 8: mutation stage exceeded 90 minute budget')
            if recipe.get('solver_replacement'):
                row=solver_replacement_result(recipe,mutate)
                results.append(row);json_file('mutacje-ruch-swiata-wynik.json',results)
                continue
            recipe=mutation_probe(recipe)
            name='ruch8-mutacja-'+recipe['name'];rows=g.recipe_cases(recipe)
            reference=None
            if recipe['probe']!='fixture':
                encoded=g.encode(rows).encode('ascii');key=hashlib.sha256(encoded).hexdigest()[:16]+recipe['probe']
                if key not in bases:
                    cname='ruch8-baza-'+key+'-c';dname='ruch8-baza-'+key+'-duckling'
                    for n,decimal,bin in ((cname,False,OUT/('kontrola-ruch-swiata-guard-bin' if recipe['probe']=='guard' else 'kontrola-ruch-swiata-bin')),
                                          (dname,True,OUT/'duckling-ruch-swiata-bin')):
                        actual,path,err=run(n,bin,g.encode(rows,decimal).encode('ascii'),not decimal,60)
                        if actual or err.read_bytes():raise C.base.StepFailed('Krok 8: native mutation baseline failed '+n)
                    errors=check_files(OUT/(cname+'.csv'),OUT/(dname+'.csv'),rows,recipe['probe']=='guard')
                    if errors:raise C.base.StepFailed('Krok 8: mutation baseline: '+repr(errors))
                    bases[key]=OUT/(cname+'.csv')
                reference=bases[key]
            else:
                if code('ruch8-bilety-kompilacja') or code('ruch8-bilety-wykonanie') or (OUT/'ruch8-bilety-wykonanie-stderr.csv').read_bytes() or (OUT/'ruch8-bilety.csv').read_bytes()!=b'RUCH SWIATA BILETY OK\n':
                    raise C.base.StepFailed('Krok 8: fixture baseline absent')
            work=C.base.TEMP/'mutacje-ruch-swiata'/recipe['name'];copied=work/'fizyka'
            shutil.copytree(physics,copied,dirs_exist_ok=True)
            path=copied/Path(recipe['source']).name
            path.write_text(mutate.apply(path.read_text(encoding='utf-8'),recipe),encoding='utf-8')
            original=PORT/'proba-ruch-swiata-bilety.dk' if recipe['probe']=='fixture' else driver
            driver_copy=work/original.name;shutil.copy2(original,driver_copy)
            binary=C.compile_world_fixture(C.world_duckc(),name,driver_copy,copied)
            actual,path,err=run(name,binary,b'' if recipe['probe']=='fixture' else g.encode(rows,True).encode('ascii'),seconds=60,unbuffered=recipe.get('unbuffered',False))
            detected,detail=detection(recipe,actual,path,err,reference,rows)
            results.append({'name':recipe['name'],'class_id':recipe['class_id'],'actual':actual,'detected':detected,'detail':detail,
                            'input_sha256':hashlib.sha256(b'' if recipe['probe']=='fixture' else g.encode(rows,True).encode('ascii')).hexdigest(),
                            'reference':str(reference.relative_to(OUT)) if reference else None})
            json_file('mutacje-ruch-swiata-wynik.json',results)
    finally:
        for path,digest in before.items():
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise C.base.StepFailed('Krok 8: native mutation changed protected product')
    return int(len(results)!=RECIPE_COUNT or not all(row['detected'] for row in results))

def evidence():
    try:
        g.verify_input_hashes(OUT)
        comparisons=(('POROWNANIE-RUCH-SWIATA',64,('c-ruch-swiata','c-ruch-swiata-bez','duckling-ruch-swiata')),
                     ('POROWNANIE-GUARD8',4,('c-guard8','c-guard8-bez','duckling-guard8')),
                     ('POROWNANIE-RUCH-SWIATA-PROBA',1,('c-ruch-swiata-proba','c-ruch-swiata-proba-bez','duckling-ruch-swiata-proba')))
        for name,n,streams in comparisons:
            value=json.loads((OUT/(name+'.json')).read_bytes())
            if value['errors']:return False
            if set(value['streams'])!={'C OBS1','C OBS0','Duckling'}:return False
            if not all(s['sha256'] and s['records'].get('CASE')==n for s in value['streams'].values()):return False
            for side,stream in zip(('C OBS1','C OBS0','Duckling'),streams):
                if code(stream) or p.sha_manifest(OUT/(stream+'.csv'))!=value['streams'][side]:return False
        for suffix in ('','-bez','-guard','-guard-bez'):
            if code('kontrola-ruch-swiata'+suffix+'-kompilacja'):return False
        if code('duckling-ruch-swiata-kompilacja'):return False
        probes=json.loads((OUT/'proby-ruch-swiata-wynik.json').read_bytes())
        negative=C.world_module('ujemne-ruch-swiata.py','ci_motion_evidence_negative')
        if len(probes)!=2*len(negative.variants())+9 or not all(r['ok'] for r in probes):return False
        for name,cdata,ddata,cdiag,ddiag in negative.variants():
            for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
                tag='ruch8-ujemny-'+name+'-'+side
                if code(tag+'-wykonanie')!=wanted:return False
                if (OUT/'wejscia-ruch-swiata'/(tag+'.csv')).read_bytes()!=data:return False
                if (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes()!=diag:return False
        for suffix in ('','-bez','-guard','-guard-bez'):
            for option,output in (('--test-tickets',b'BILETY OK\n'),('--test-blocks',b'BLOKI OK\n')):
                name='ruch8-c-fixture'+suffix+option
                if code(name) or (OUT/(name+'.csv')).read_bytes()!=output or (OUT/(name+'-stderr.csv')).read_bytes():return False
        if code('ruch8-bilety-kompilacja') or code('ruch8-bilety-wykonanie') or (OUT/'ruch8-bilety.csv').read_bytes()!=b'RUCH SWIATA BILETY OK\n':return False
        if (OUT/'ruch8-bilety-wykonanie-stderr.csv').read_bytes():return False
        asserts=json.loads((OUT/'asercje-ruch-swiata-wynik.json').read_bytes())
        if len(asserts)!=7 or not all(r['ok'] for r in asserts):return False
        for row in asserts:
            wanted=row['expected'];name=row['name']
            diag=b'ASSERT8: b2IsValidFloat( timeStep )\n' if wanted==86 else b'ASSERT8: 0 < subStepCount\n'
            if code(name)!=wanted or (OUT/(name+'-stderr.csv')).read_bytes()!=diag:return False
        recipes=json.loads((PORT/'mutacje-ruch-swiata.json').read_bytes())['native_mutations']
        rows=json.loads((OUT/'mutacje-ruch-swiata-wynik.json').read_bytes())
        if len(recipes)!=RECIPE_COUNT or [r['name'] for r in rows]!=[r['name'] for r in recipes]:return False
        for recipe,row in zip(recipes,rows):
            if recipe.get('solver_replacement'):
                if not solver_replacement_evidence(recipe,row):return False
                continue
            recipe=mutation_probe(recipe)
            name='ruch8-mutacja-'+recipe['name']
            if code(name+'-kompilacja') or not row['detected'] or code(name+'-wykonanie')!=row['actual']:return False
            data=b'' if recipe['probe']=='fixture' else g.encode(g.recipe_cases(recipe),True).encode('ascii')
            if row['class_id']!=recipe['class_id'] or row['input_sha256']!=hashlib.sha256(data).hexdigest():return False
            if (OUT/'wejscia-ruch-swiata'/(name+'.csv')).read_bytes()!=data:return False
            reference=OUT/row['reference'] if row['reference'] else None
            detected,_=detection(recipe,row['actual'],OUT/(name+'.csv'),OUT/(name+'-wykonanie-stderr.csv'),reference,g.recipe_cases(recipe))
            if not detected:return False
        unchanged(json.loads((OUT/'box2d-ruch-swiata-sha256.json').read_bytes()))
    except (OSError,ValueError,IndexError,KeyError,TypeError):return False
    return True

STAGES=('proba-ruch-swiata','c-ruch-swiata','duckling-ruch-swiata','check-ruch-swiata','proby-ruch-swiata','mutacje-ruch-swiata')

def summary():
                                                                          
                                                                             
    prior=OUT.parent/'wynik-kod.csv'
    failed=os.environ.get('REGRESJE_OUTCOME')!='success' or not prior.is_file() or prior.read_text().strip()!='0'
    lines=['# Krok 8 — osobne zadanie','',f'Kroki 1–7: {os.environ.get('REGRESJE_OUTCOME', 'MISSING')}.',
           '','| Etap | Kod | GitHub |','|---|---:|---|']
    for name in STAGES:
        actual=code('etap-port-'+name);outcome=os.environ.get(name.replace('-','_').upper()+'_OUTCOME','MISSING')
        failed|=actual!=0 or outcome!='success';lines.append(f'| {name} | {actual} | {outcome} |')
    valid=evidence();failed|=not valid
    lines+=['',f'Dowody kroku 8: {valid}.','RESULT STEPS 1–8: '+('FAIL' if failed else 'OK'),'']
    if (OUT/'PROBA-RUCH-SWIATA.md').is_file():lines.append((OUT/'PROBA-RUCH-SWIATA.md').read_text(encoding='utf-8'))
    (OUT/'DZIENNIK.md').write_text('\n'.join(lines),encoding='utf-8')
    (OUT/'wynik-kod.csv').write_text('1\n' if failed else '0\n',encoding='ascii')
    print('\n'.join(lines));return int(failed)

def compact():
    module=C.world_module('zapis-strumieni.py','ci_motion_storage')
    module.compact(OUT)
    return 0

def stage(context,name):
    init(context)
    return {'proba-ruch-swiata':sample,'c-ruch-swiata':c_side,'duckling-ruch-swiata':duckling,
            'check-ruch-swiata':check,'proby-ruch-swiata':probes,'mutacje-ruch-swiata':mutations,
            'summary-ruch-swiata':summary,'zapis-strumieni':compact}[name]()
