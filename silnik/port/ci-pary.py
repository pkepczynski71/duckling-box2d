from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                               

                                                                      
                                                                      
   
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

RECIPE_COUNT=48
NEGATIVE_COUNT=46
STAGES=('proba-pary','c-pary','duckling-pary','check-pary','proby-pary','mutacje-pary')

def init(context):
    global C,OUT,PORT,ROOT,g,p,negative,mutator
    C=context;OUT=C.OUT;PORT=C.PORT;ROOT=C.ROOT;sys.argv[1]='pary9a'
    g=C.world_module('przypadki-pary.py','ci_pair_inputs')
    p=C.world_module('porownaj-pary.py','ci_pair_compare')
    negative=C.world_module('ujemne-pary.py','ci_pair_negative')
    mutator=C.world_module('mutacje-pary.py','ci_pair_mutator')

def code(name):return C.shape_code(name)
def json_file(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def source_sums():
    source=C.base.TEMP/'box2d'
    files=sorted([*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),*source.joinpath('include/box2d').glob('*.h')])
    json_file('box2d-pary-inwentarz.json',{'count':len(files),'files':[path.relative_to(source).as_posix() for path in files]})
    if len(files)!=63:raise C.base.StepFailed('9a: restored original must contain 63 C/H files')
    sums={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    text=''.join(f'{digest}  {Path(path).relative_to(source).as_posix()}\n' for path,digest in sums.items())
    contract=norm_text(PORT/'fixtures/norms/KONTRAKT-7.json')
    expected=(C.base.TEMP.parent/'box2d-port7-sha256.csv').read_text(encoding='ascii')
    if len(expected.splitlines())!=63 or text!=expected or any(line not in contract for line in text.splitlines()):
        raise C.base.StepFailed('9a: restored source hashes differ from original v3.1.1')
    (OUT/'box2d-port7-sha256.csv').write_text(expected,encoding='ascii')
    library=C.base.CACHE/'box2d/lib/libbox2d.a';sums[str(library)]=hashlib.sha256(library.read_bytes()).hexdigest()
    json_file('box2d-pary-sha256.json',sums);return sums

def unchanged(sums):
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest for path,digest in sums.items()):
        raise C.base.StepFailed('9a: protected source/library changed')

def run(name,binary,data,c_side=False,seconds=30):
    if not binary.is_file():raise C.base.StepFailed('9a: missing executable '+str(binary))
    directory=OUT/'wejscia-pary';directory.mkdir(exist_ok=True)
    path=directory/(name+'.csv');path.write_bytes(data)
                                                                              
                                                                              
    listing=OUT/'pary-lista-strumieni.json'
    names=json.loads(listing.read_bytes()) if listing.is_file() else []
    if name+'.csv' not in names:names.append(name+'.csv')
    json_file(listing.name,names)
    command=[binary,path] if c_side else ['bash','-c','exec "$1" < "$2"','pair-stdin',binary,path]
    actual=C.base.run(name+'-wykonanie',command,stdout=OUT/(name+'.csv'),seconds=seconds)
    return actual,OUT/(name+'.csv'),OUT/(name+'-wykonanie-stderr.csv')

def comparison(name,small=False):
    suffix='-proba' if small else ''
    command=[sys.executable,'-B',PORT/'porownaj-pary.py','--c',OUT/('c-pary'+suffix+'.csv'),
        '--duckling',OUT/('duckling-pary'+suffix+'.csv'),'--wejscie',OUT/('proba-pary.csv' if small else 'przypadki-pary.csv'),
        '--kod-c',code('c-pary'+suffix+'-wykonanie'),'--kod-wyjscia',code('duckling-pary'+suffix+'-wykonanie'),
        '--raport',OUT/(name+'.md')]
    if small:command.append('--small')
    return C.base.run(name,command,seconds=60)

def sample():
    C.base.need('generator-pary',[sys.executable,'-B',PORT/'przypadki-pary.py','--katalog',OUT],seconds=30)
    g.verify_input_hashes(OUT);before=source_sums()
    sources=[*PORT.glob('*.py'),*PORT.glob('*.c'),*PORT.glob('*.json'),*PORT.glob('fixtures/norms/KONTRAKT*.json'),
             *PORT.glob('fixtures/norms/PLAN-9*.json'),*ROOT.joinpath('silnik/fizyka').glob('*.dk'),*PORT.glob('*.dk'),
             ROOT/'fixtures/norms/KONTRAKT-9A-DOPOWIEDZENIE.json',ROOT/'.github/workflows/port.yml']
    hashes={}
    for path in sorted(set(sources)):
        relative=path.relative_to(ROOT);target=OUT/'zrodla'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);hashes[relative.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    json_file('zrodla-pary-sha256.json',hashes)
    source=C.base.TEMP/'box2d';binary=OUT/'kontrola-pary-bin';library=C.base.CACHE/'box2d/lib/libbox2d.a'
    C.base.need('kontrola-pary-kompilacja',['cc','-std=c17','-O2','-Wall','-Wextra','-Werror','-DNDEBUG',
        '-DBOX2D_DISABLE_SIMD','-fno-fast-math','-ffp-contract=off','-I'+str(source/'include'),
        PORT/'kontrola-pary.c',library,'-lm','-o',binary],seconds=45)
    driver=PORT/'pary.dk'
    if not driver.is_file():raise C.base.StepFailed('9a transport entry point is missing')
    duck=C.compile_world_fixture(C.world_duckc(),'duckling-pary',driver,ROOT/'silnik/fizyka')
    stats=[]
    for name,exe,input_name,c_side in (('c-pary-proba',binary,'proba-pary.csv',True),
                                      ('duckling-pary-proba',duck,'proba-pary-stdin.csv',False)):
        started=time.monotonic();actual,path,err=run(name,exe,(OUT/input_name).read_bytes(),c_side)
        stats.append({'name':name,'code':actual,'bytes':path.stat().st_size,'seconds':time.monotonic()-started})
        if actual or err.read_bytes():raise C.base.StepFailed('9a: failed positive sample '+name)
                                                                           
                                                       
    exact=len(p.format_record('PORT9A',(448,)))+len(p.format_record('END',(448,)))
    for case in g.cases():
        exact+=len(p.format_record('E',p.echo(case)))+len(p.format_record('M',(case.id,*([0]*30))))+len(p.format_record('ENDCASE',(case.id,)))
    forecast={'N':448,'records':3*448+2,'exact_bytes_per_full_stream':exact,
              'upper_bytes_per_stream':448*2048,'two_streams_upper':2*448*2048,
              'native_output_upper':(RECIPE_COUNT+4)*448*2048,'inputs':json.loads((OUT/'wejscia-pary-sha256.json').read_bytes())}
    free=shutil.disk_usage(C.base.TEMP).free
    json_file('pary-proba-pomiar.json',{'streams':stats,'free_bytes':free,'forecast':forecast})
    (OUT/'PROBA-PARY.md').write_text('# E33e6de651289 E318a09570e1d 9a\n\n'+json.dumps({'streams':stats,'free_bytes':free,'forecast':forecast},indent=2)+'\n',encoding='utf-8')
    unchanged(before)
    if free<forecast['native_output_upper']+2*1024**3:
        (OUT/'PYTANIE-PARY.md').write_text('STATUS: PYTANIE — missing Efa360362903c; N, E279cf128155b Ede7d1b721a1e Ee904c9ccfa42 E283ada7088c2 E3268fef5c876.\n',encoding='utf-8');return 1
    return comparison('POROWNANIE-PARY-PROBA',True)

def full(c_side):
    if code('etap-port-proba-pary'):raise C.base.StepFailed('9a: full run requires a successful sample')
    g.verify_input_hashes(OUT);before=source_sums()
    name='c-pary' if c_side else 'duckling-pary';exe=OUT/('kontrola-pary-bin' if c_side else 'duckling-pary-bin')
    actual,path,err=run(name,exe,(OUT/('przypadki-pary.csv' if c_side else 'przypadki-pary-stdin.csv')).read_bytes(),c_side)
    unchanged(before);return int(bool(actual or err.read_bytes()))

def check():
    actual=comparison('POROWNANIE-PARY')
    tests=C.base.run('sprawdziany-pary',[sys.executable,'-B','-m','unittest','discover','-s','silnik/port','-p','test_pary*.py','-v'],seconds=300,
        env={**os.environ,'PARY_REQUIRE_PRODUCT':'1','PARY_C_BIN':str(OUT/'kontrola-pary-bin')})
    return int(bool(actual or tests))

def assertions():
    source=C.base.TEMP/'box2d';build=C.base.TEMP/'box2d-assert9a-build'
    C.base.need('assert9a-configure',['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Debug',
        '-DBUILD_SHARED_LIBS=OFF','-DBOX2D_SAMPLES=OFF','-DBOX2D_UNIT_TESTS=OFF','-DBOX2D_BENCHMARKS=OFF',
        '-DBOX2D_DOCS=OFF','-DBOX2D_PROFILE=OFF','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF','-DBOX2D_VALIDATE=OFF'],seconds=60)
    C.base.need('assert9a-build',['cmake','--build',build,'--target','box2d','--parallel','2'],seconds=180)
    libraries=list(build.rglob('libbox2dd.a'))
    if len(libraries)!=1:raise C.base.StepFailed('ASSERT9A: expected exactly one Debug libbox2dd.a')
    binary=OUT/'kontrola-pary-asercje-bin'
    C.base.need('assert9a-link',['cc','-std=c17','-O0','-Wall','-Wextra','-Werror','-fno-fast-math','-ffp-contract=off',
        '-I'+str(source/'include'),PORT/'kontrola-pary-asercje.c',libraries[0],'-lm','-o',binary],seconds=30)
    results=[]
    for arg,wanted,diag in assertion_cases():
        name='assert9a-'+arg;actual=C.base.run(name,[binary,arg],seconds=15)
        valid=actual==wanted and (OUT/(name+'-stderr.csv')).read_bytes()==diag and not (OUT/(name+'.csv')).read_bytes()
        results.append({'name':name,'expected':wanted,'actual':actual,'ok':valid})
    json_file('asercje-pary-wynik.json',results);return not all(row['ok'] for row in results)

def assertion_cases():
    return tuple((arg,86 if arg.startswith('capsules') else 87,
        b'ASSERT9A: dd1 > epsSqr && dd2 > epsSqr\n' if arg.startswith('capsules') else b'ASSERT9A: b2LengthSquared( d ) > FLT_EPSILON\n')
        for arg in ('capsules-A','capsules-B','polygon-capsule','segment-polygon'))

def probes():
    if code('etap-port-proba-pary'):raise C.base.StepFailed('9a: probes require positive sample')
    before=source_sums();results=[]
    for name,cdata,ddata,cdiag,ddiag in negative.variants():
        for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
            tag='pary-ujemny-'+name+'-'+side;exe=OUT/('kontrola-pary-bin' if side=='c' else 'duckling-pary-bin')
            actual,path,err=run(tag,exe,data,side=='c',15)
            valid=actual==wanted and err.read_bytes()==diag
            results.append({'name':tag,'expected':wanted,'actual':actual,'diagnostic':diag.decode('ascii'),'ok':valid})
    for label,rows,ending in (('CRLF',g.small_cases(),'\r\n'),('EOF',g.small_cases(),''),('N1',g.cases()[:1],'\n')):
        for side in ('c','duckling'):
            data=g.encode(rows,side=='duckling',ending='\n' if ending=='' else ending)
            if ending=='':data=data[:-1]
            name='pary-dodatni-'+label+'-'+side;exe=OUT/('kontrola-pary-bin' if side=='c' else 'duckling-pary-bin')
            actual,path,err=run(name,exe,data.encode('ascii'),side=='c');valid=actual==0 and not err.read_bytes()
            try:
                with path.open(encoding='ascii',newline='') as stream:p.validate_output(stream,rows)
            except (OSError,ValueError):valid=False
            results.append({'name':name,'expected':0,'actual':actual,'ok':bool(valid)})
    debug_bad=assertions();unchanged(before);json_file('proby-pary-wynik.json',results)
    return int(debug_bad or len(results)!=2*NEGATIVE_COUNT+6 or not all(row['ok'] for row in results))

def clean_acceptance(path,expected_n,*,finite_refusal_echoes=None,nonfinite_fields=None):
    pass                                                                     

                                                                         
                                                                             
                                                                             
       
    if (finite_refusal_echoes is None)!=(nonfinite_fields is None):return False
    with path.open(encoding='ascii',newline='') as stream:
        tag,header=p.parse_record(stream.readline(p.MAX_LINE+1))
        if tag!='PORT9A' or header!=(expected_n,) or not 0<=header[0]<=449:return False
        if finite_refusal_echoes is not None and len(finite_refusal_echoes)!=expected_n:return False
        for index in range(expected_n):
            tag,echo=p.parse_record(stream.readline(p.MAX_LINE+1))
            if tag!='E':return False
            if finite_refusal_echoes is not None and echo!=finite_refusal_echoes[index]:return False
            tag,values=p.parse_record(stream.readline(p.MAX_LINE+1))
            if tag!='M' or values[0]!=echo[0]:return False
            words=list(values[1:])
            if finite_refusal_echoes is not None and index==0 and echo[0]==1:
                                                                          
                                                                               
                for field in (0,1,4,5,6,7,8,9,10):
                    if not math.isfinite(p.g.number(words[field])):
                        nonfinite_fields.append(p.FIELDS[field]);words[field]=0
            p.validate_manifold(words,values[0])
            if p.parse_record(stream.readline(p.MAX_LINE+1))!=('ENDCASE',(echo[0],)):return False
        return p.parse_record(stream.readline(p.MAX_LINE+1))==('END',header) and not stream.read(1)

def finite_refusal_echoes(data):
    pass                                                                  
    lines=data.decode('ascii').splitlines();header=lines[0].split()
    if header!=['PORT9A','7'] or len(lines)!=22:raise ValueError('wrong finite refusal input')
    echoes=[]
    for index in range(7):
        pair=lines[1+3*index].split();a=lines[2+3*index].split();b=lines[3+3*index].split()
        if len(pair)!=3 or pair[0]!='P' or len(a)!=46 or a[0]!='A' or len(b)!=46 or b[0]!='B':
            raise ValueError('wrong finite refusal records')
        echoes.append(tuple(map(int,(*pair[1:],*a[1:],*b[1:]))))
    if echoes[0][:3]!=(1,0,1) or echoes[0][52]!=0x7f800000:raise ValueError('wrong nonfinite input witness')
    return echoes

def detection(recipe,actual,path,err,reference,rows):
    if actual!=0 or err.read_bytes():return False,{'error':'mutation must build and exit cleanly with empty stderr','code':actual}
    try:
        if recipe['probe']=='negative':
            data=recipe_input(recipe);expected_n=int(data.splitlines()[0].split()[1])
            finite_guard=(recipe.get('name')=='parser-finite' and recipe.get('variant')=='Inf-circle'
                and recipe.get('scope')=='decodeFloat' and recipe.get('source')=='silnik/port/pary.dk')
            observed=[]
            clean=clean_acceptance(path,expected_n,
                finite_refusal_echoes=finite_refusal_echoes(data) if finite_guard else None,
                nonfinite_fields=observed if finite_guard else None)
            detail={'variant':recipe['variant'],'expected_original_code':3,'actual':actual,'clean_acceptance':clean}
            if finite_guard:detail.update(cause='missing finite-input refusal',expected_stderr='BLAD: NaN/Inf.\n',nonfinite_fields=observed)
            return clean,detail
        with path.open(encoding='ascii',newline='') as stream:mutated=p.validate_output(stream,rows)
        with reference.open(encoding='ascii',newline='') as stream:original=p.validate_output(stream,rows)
        for ident in recipe['witness_ids']:
            a=original['manifolds'][ident];b=mutated['manifolds'][ident]
            for field in recipe['fields']:
                index=p.FIELDS.index(field)
                if a[index]!=b[index]:return True,{'id':ident,'field':field,'C':f'{a[index]:08x}','Duckling':f'{b[index]:08x}'}
        return False,{'error':'no prescribed field difference at the frozen witness'}
    except (OSError,ValueError,UnicodeError,IndexError,KeyError) as exc:return False,{'error':str(exc)}

def recipe_input(recipe):
    if recipe['probe']=='physics':return g.encode(g.cases(),True).encode('ascii')
    return next(row[2] for row in negative.variants() if row[0]==recipe['variant'])

def mutations():
    if code('etap-port-check-pary') or code('etap-port-proby-pary'):raise C.base.StepFailed('9a: mutations require valid comparison and parser probes')
    before=source_sums();protected={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [*ROOT.joinpath('silnik/fizyka').glob('*.dk'),PORT/'pary.dk']}
    json_file('produkt-pary-sha256.json',protected)
    recipes=json.loads((PORT/'mutacje-pary.json').read_bytes())['native_mutations']
    if len(recipes)!=RECIPE_COUNT:raise C.base.StepFailed('9a: wrong native recipe count')
    results=[];duckc=C.world_duckc();work=C.base.TEMP/'pary-mutacje'
    if work.exists():raise C.base.StepFailed('9a: mutation directory already exists, refusing reuse')
    work.mkdir()
    try:
        for recipe in recipes:
            name='pary-mutacja-'+recipe['name'];directory=work/recipe['name'];directory.mkdir()
            physics=directory/'fizyka';shutil.copytree(ROOT/'silnik/fizyka',physics)
            driver=directory/'pary.dk';shutil.copy2(PORT/'pary.dk',driver)
            target=driver if recipe['source']=='silnik/port/pary.dk' else physics/Path(recipe['source']).name
            target.write_text(mutator.apply(target.read_text(encoding='utf-8'),recipe),encoding='utf-8')
            binary=C.compile_world_fixture(duckc,name,driver,physics);data=recipe_input(recipe)
            actual,path,err=run(name,binary,data,seconds=15)
            detected,detail=detection(recipe,actual,path,err,OUT/'c-pary.csv',g.cases())
            results.append({'name':recipe['name'],'probe':recipe['probe'],'detected':detected,'actual':actual,'difference':detail,
                            'input_sha256':hashlib.sha256(data).hexdigest()})
            json_file('mutacje-pary-wynik.json',results)
    finally:
        unchanged(before);unchanged(protected)
        if work.resolve().is_relative_to(C.base.TEMP.resolve()):shutil.rmtree(work)
    return int(len(results)!=RECIPE_COUNT or not all(row['detected'] for row in results))

def evidence():
    try:
        g.verify_input_hashes(OUT)
        for small in (False,True):
            name='POROWNANIE-PARY-PROBA' if small else 'POROWNANIE-PARY';suffix='-proba' if small else ''
            recorded=json.loads((OUT/(name+'.json')).read_bytes())
            actual=p.compare_files(OUT/('c-pary'+suffix+'.csv'),OUT/('duckling-pary'+suffix+'.csv'),g.small_cases() if small else g.cases(),
                code('c-pary'+suffix+'-wykonanie'),code('duckling-pary'+suffix+'-wykonanie'))
            if recorded!=actual or actual['errors']:return False
            for side in ('c','duckling'):
                if (OUT/(side+'-pary'+suffix+'-wykonanie-stderr.csv')).read_bytes():return False
        if code('kontrola-pary-kompilacja') or code('duckling-pary-kompilacja') or code('sprawdziany-pary'):return False
        probes=json.loads((OUT/'proby-pary-wynik.json').read_bytes())
        if len(probes)!=2*NEGATIVE_COUNT+6 or not all(r['ok'] for r in probes):return False
        for name,cdata,ddata,cdiag,ddiag in negative.variants():
            for side,data,wanted,diag in (('c',cdata,2,cdiag),('duckling',ddata,3,ddiag)):
                tag='pary-ujemny-'+name+'-'+side
                if code(tag+'-wykonanie')!=wanted or (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes()!=diag:return False
                if (OUT/'wejscia-pary'/(tag+'.csv')).read_bytes()!=data:return False
        for row in probes[2*NEGATIVE_COUNT:]:
            name=row['name'];side=name.rsplit('-',1)[1];input_data=(OUT/'wejscia-pary'/(name+'.csv')).read_bytes()
            rows=g.read_input(input_data.decode('ascii'),side=='duckling')
            if code(name+'-wykonanie') or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
            with (OUT/(name+'.csv')).open(encoding='ascii',newline='') as stream:p.validate_output(stream,rows)
        asserts=json.loads((OUT/'asercje-pary-wynik.json').read_bytes())
        if len(asserts)!=4 or not all(r['ok'] for r in asserts):return False
        for arg,wanted,diag in assertion_cases():
            name='assert9a-'+arg
            if code(name)!=wanted or (OUT/(name+'-stderr.csv')).read_bytes()!=diag or (OUT/(name+'.csv')).read_bytes():return False
        if any(code(name) for name in ('assert9a-configure','assert9a-build','assert9a-link')):return False
        recipes=json.loads((PORT/'mutacje-pary.json').read_bytes())['native_mutations'];results=json.loads((OUT/'mutacje-pary-wynik.json').read_bytes())
        if len(recipes)!=RECIPE_COUNT or [r['name'] for r in results]!=[r['name'] for r in recipes]:return False
        for recipe,row in zip(recipes,results):
            name='pary-mutacja-'+recipe['name'];data=recipe_input(recipe)
            if code(name+'-kompilacja') or code(name+'-wykonanie')!=row['actual'] or not row['detected']:return False
            if row['input_sha256']!=hashlib.sha256(data).hexdigest() or (OUT/'wejscia-pary'/(name+'.csv')).read_bytes()!=data:return False
            detected,detail=detection(recipe,row['actual'],OUT/(name+'.csv'),OUT/(name+'-wykonanie-stderr.csv'),OUT/'c-pary.csv',g.cases())
            if not detected or detail!=row['difference']:return False
        original=json.loads((OUT/'box2d-pary-sha256.json').read_bytes())
        source=C.base.TEMP/'box2d'
        expected_source=[*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),*source.joinpath('include/box2d').glob('*.h')]
        if len(expected_source)!=63 or set(original)!={str(path) for path in [*expected_source,C.base.CACHE/'box2d/lib/libbox2d.a']}:return False
        product=json.loads((OUT/'produkt-pary-sha256.json').read_bytes())
        expected_product=[*ROOT.joinpath('silnik/fizyka').glob('*.dk'),PORT/'pary.dk']
        if set(product)!={str(path) for path in expected_product} or len(expected_product)<2:return False
        unchanged(original);unchanged(product)
    except (OSError,ValueError,TypeError,KeyError,IndexError,UnicodeError,StopIteration):return False
    return True

def summary():
    prior=OUT.parent/'krok8/wynik-kod.csv'
    failed=os.environ.get('REGRESJE_OUTCOME')!='success' or not prior.is_file() or prior.read_text().strip()!='0'
    failed|=code('narzedzia9-odtworzenie')!=0 or code('kod-miedzy-zadaniami')!=0
    lines=['# Krok 9a — osobne zadanie','',f'Kroki 1–8: {os.environ.get('REGRESJE_OUTCOME', 'MISSING')}.',
           '','| Etap | Kod | GitHub |','|---|---:|---|']
    for name in STAGES:
        actual=code('etap-port-'+name);outcome=os.environ.get(name.replace('-','_').upper()+'_OUTCOME','MISSING')
        failed|=actual!=0 or outcome!='success';lines.append(f'| {name} | {actual} | {outcome} |')
    valid=evidence();failed|=not valid
    lines+=['',f'Dowody kroku 9a: {valid}.','RESULT STEPS 1–9a: '+('FAIL' if failed else 'OK'),'']
    if (OUT/'PROBA-PARY.md').is_file():lines.append((OUT/'PROBA-PARY.md').read_text(encoding='utf-8'))
    (OUT/'DZIENNIK.md').write_text('\n'.join(lines),encoding='utf-8');(OUT/'wynik-kod.csv').write_text('1\n' if failed else '0\n',encoding='ascii')
    print('\n'.join(lines));return int(failed)

def compact():
    storage=C.world_module('zapis-strumieni.py','pair_storage8')
    return compact_outputs(OUT,storage.manifest)

def compact_outputs(directory,manifest):
    directory=Path(directory).resolve();records={}
    names=json.loads((directory/'pary-lista-strumieni.json').read_bytes())
    if len(names)!=len(set(names)):raise ValueError('duplicate output names')
    for name in names:
        if Path(name).name!=name or not name.endswith('.csv'):raise ValueError('output path escaped directory')
        path=directory/name;entry=manifest(path);records[name]=entry
        path.with_name(path.name+'.manifest.json').write_text(json.dumps(entry,indent=2)+'\n',encoding='ascii')
        path.unlink()
    (directory/'STRUMIENIE-PARY-MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n',encoding='ascii')
    (directory/'ZAPIS-PARY.md').write_text('# E93cba7eb5092 Ee31d41b918d5 9a\n\nEff624a4b9cdb E7e059e4c7eb8 Edbe5939feed5 E6199aecf23ab E039ede6928f9 Ede7d1b721a1e E126fdee86d01 E41776fb28e41 E984ff3afe521 E5ea52c02e5e6 SHA-256, bytes, E828c68d0f522 Ede7d1b721a1e E5de2502ef871. E028cf3732286 E52b3d71a10fe.\n',encoding='utf-8')
    return 0

def stage(context,name):
    init(context)
    return {'proba-pary':sample,'c-pary':lambda:full(True),'duckling-pary':lambda:full(False),'check-pary':check,
            'proby-pary':probes,'mutacje-pary':mutations,'summary-pary':summary,'zapis-strumieni-pary':compact}[name]()
