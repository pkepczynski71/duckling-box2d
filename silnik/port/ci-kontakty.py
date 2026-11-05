from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                                 
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

STAGES=('proba-kontakty','c-kontakty-obs0','c-kontakty-obs1','native-kontakty','check-kontakty',
        'ujemne-kontakty','fixtury-kontakty','mutacje-kontakty')
RECIPE_COUNT=203
FLAGS=['-std=c17','-D_POSIX_C_SOURCE=200809L','-O2','-DNDEBUG','-DBOX2D_DISABLE_SIMD','-fno-fast-math','-ffp-contract=off']

def init(context):
    global C,OUT,PORT,ROOT,g,p,negative
    C=context;OUT=C.OUT;PORT=C.PORT;ROOT=C.ROOT;sys.argv[1]='kontakty9b'
    g=C.world_module('przypadki-kontakty.py','ci_contact_inputs');p=C.world_module('porownaj-kontakty.py','ci_contact_compare')
    negative=C.world_module('ujemne-kontakty.py','ci_contact_negative')

def code(name):return C.shape_code(name)
def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def show_stderr(name):
    path=OUT/(name+'-stderr.csv')
    print(f'9b {name}: stderr (first 120 wierszy), {path.name}:',flush=True)
    try:
        with path.open(encoding='utf-8',errors='backslashreplace') as stream:
            for index,line in enumerate(stream):
                if index==120:break
                print(line,end='' if line.endswith('\n') else '\n',flush=True)
    except OSError as exc:print(f'9b Ecd5b158f21b7 E04ff0184c025 E675b88752d5e E7e6b710b7654: {exc}',flush=True)

def need(name,command,**kwargs):
    try:return C.base.need(name,command,**kwargs)
    except C.base.StepFailed:
        show_stderr(name)
        raise

def source_sums():
    source=C.base.TEMP/'box2d';files=sorted([*source.joinpath('src').glob('*.c'),*source.joinpath('src').glob('*.h'),*source.joinpath('include/box2d').glob('*.h')])
    inventory={'root':str(source),'count':len(files),'files':[f.relative_to(source).as_posix() for f in files]};save('box2d-kontakty-inwentarz.json',inventory)
    if len(files)!=63:raise C.base.StepFailed(f'9b needs 63 existing original C/H sources, found {len(files)}: {inventory}')
    sums={f.relative_to(source).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    contract=norm_text(PORT/'fixtures/norms/KONTRAKT-7.json')
    if any(f'{digest}  {name}' not in contract for name,digest in sums.items()):raise C.base.StepFailed('9b original source hashes differ from accepted 7/8')
    return sums

def unchanged(before):
    actual=source_sums();save('box2d-kontakty-po-sha256.json',actual)
    if before!=actual:raise C.base.StepFailed('9b original sources changed')

def build_c():
    source=C.base.TEMP/'box2d';directory=C.base.TEMP/'contact-a9-build';directory.mkdir(exist_ok=True)
    before=source_sums();save('box2d-kontakty-przed-sha256.json',before)
    units=sorted(source.joinpath('src').glob('*.c'));objects=[];manifest=[]
    include=['-I'+str(source/'include'),'-I'+str(source/'src')]
    for unit in units:
        wrapper=PORT/('kontrola-kontakty-world.c' if unit.name=='world.c' else 'kontrola-kontakty-broad.c' if unit.name=='broad_phase.c' else unit.name)
        input_=wrapper if unit.name in ('world.c','broad_phase.c') else unit
        obj=directory/(unit.name+'.o');name='c9b-unit-'+unit.stem
        need(name,['cc',*FLAGS,'-Wall','-Wextra','-Wno-unused-value','-Wno-misleading-indentation',*include,'-c',input_,'-o',obj],seconds=60)
        objects.append(obj);manifest.append({'original':unit.relative_to(source).as_posix(),'translation_unit':str(input_),'object':str(obj),'sha256':before[unit.relative_to(source).as_posix()]})
    if len({r['original'] for r in manifest})!=len(units):raise C.base.StepFailed('9b duplicate original translation unit')
    for original in ('src/world.c','src/broad_phase.c'):
        if sum(r['original']==original for r in manifest)!=1:raise C.base.StepFailed('9b method A compiled '+original+' other than once')
    object_stats=[{'path':str(obj),'bytes':obj.stat().st_size} for obj in objects]
    save('c9b-archive-obiekty.json',{'count':len(object_stats),'bytes':sum(row['bytes'] for row in object_stats),'objects':object_stats})
    print(f'9b przed ar: {len(object_stats)} plikow .o, {sum((row['bytes'] for row in object_stats))} bajtow',flush=True)
    archive=directory/'libbox2d-component-a9.a';need('c9b-archive',['ar','rcs',archive,*objects],seconds=180)
    need('c9b-symbols',['nm','--defined-only',archive],seconds=180)
    symbols=(OUT/'c9b-symbols.csv').read_text(encoding='ascii').splitlines()
    for symbol in ('b2World_Step','b2UpdateBroadPhasePairs'):
        if sum(line.split()[-1:]==[symbol] for line in symbols)!=1:raise C.base.StepFailed('9b symbol not linked exactly once: '+symbol)
    save('kontakty-linkowanie-A.json',{'profile':'COMPONENT_A9','locked_during_component':False,'workers':1,'original_units':manifest,
         'original_count':len(units),'world_c_count':1,'broad_phase_c_count':1,'full_legacy_archive_linked':False,'flags':FLAGS,
         'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
    for obs in (0,1):
        build_c_adapter('c9b-obs'+str(obs),obs=obs)
        build_c_adapter('c9b-guard-obs'+str(obs),obs=obs,guard=True)
    unchanged(before)

def build_c_adapter(name,obs=1,guard=False,defines=()):
    source=C.base.TEMP/'box2d';archive=C.base.TEMP/'contact-a9-build/libbox2d-component-a9.a';binary=OUT/(name+'-bin')
    need(name+'-kompilacja',['cc',*FLAGS,'-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DOBS='+str(obs),'-DGUARD9='+str(int(guard)),
        *defines,'-I'+str(source/'include'),'-I'+str(source/'src'),PORT/'kontrola-kontakty.c',archive,'-lm','-o',binary],seconds=60)
    return binary

def compile_duck(name,driver,physics):
    try:binary=C.compile_world_fixture(C.world_duckc(),name,driver,physics)
    except C.base.StepFailed:
        show_stderr(name+'-kompilacja')
        raise
    save(name+'-binary-sha256.json',{'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'bytes':binary.stat().st_size})
    build=C.base.TEMP/(name+'-build')
    if build.resolve().is_relative_to(C.base.TEMP.resolve()) and build.is_dir():shutil.rmtree(build)
    return binary

def track(name):
    path=OUT/'kontakty-lista-strumieni.json';names=json.loads(path.read_bytes()) if path.exists() else []
    if name not in names:names.append(name)
    save(path.name,names)

def run(name,binary,data=None,*,input_path=None,c_side=False,seconds=120,expected_code=0,expected_stderr=b''):
    if data is not None:
                                                                                   
        value,_=C.run_world_fixture(name,binary,data,file_argument=c_side);path=OUT/(name+'.csv')
    else:
        if input_path is None:raise ValueError('input path missing')
        command=[binary,input_path] if c_side else ['bash','-c','exec "$1" < "$2"','contact-input',binary,input_path]
        value=C.base.run(name+'-wykonanie',command,stdout=OUT/(name+'.csv'),seconds=seconds);path=OUT/(name+'.csv')
    track(path.name);stderr=OUT/(name+'-wykonanie-stderr.csv')
    if value!=expected_code or stderr.read_bytes()!=expected_stderr:
        print(f'9b {name}: wykonanie niezgodne z oczekiwaniem (code {value}, oczekiwano {expected_code}).',flush=True)
        show_stderr(name+'-wykonanie')
    return value,path,stderr

def need_success(result):
    value,path,stderr=result
    if value or stderr.read_bytes():raise C.base.StepFailed(f'9b {path.name}: exit {value}, stderr {stderr.read_bytes()!r}')
    return path

def sample():
    measured=g.write(OUT);save('kontakty-operacje.json',measured)
    build_c()
    driver=PORT/'kontakty.dk'
    if not driver.is_file():raise C.base.StepFailed('9b transport silnik/port/kontakty.dk is missing')
    duck=compile_duck('duckling-kontakty',driver,ROOT/'silnik/fizyka')
    stats=[]
    for name,binary,input_,side in (('c9b-proba-obs0',OUT/'c9b-obs0-bin','proba-kontakty.csv',True),
                                  ('c9b-proba-obs1',OUT/'c9b-obs1-bin','proba-kontakty.csv',True),
                                  ('duckling-kontakty-proba',duck,'proba-kontakty-stdin.csv',False)):
        start=time.monotonic();path=need_success(run(name,binary,input_path=OUT/input_,c_side=side,seconds=600))
        stats.append({'name':name,'seconds':time.monotonic()-start,'bytes':path.stat().st_size})
    result=p.compare_files(OUT/'c9b-proba-obs1.csv',OUT/'duckling-kontakty-proba.csv',OUT/'c9b-proba-obs0.csv',g.cases()[:49])
    save('POROWNANIE-KONTAKTY-PROBA.json',result)
    manifest=json.loads((PORT/'kontakty-przypadki.json').read_bytes());rows=g.cases()
    ceiling=sum(2*len(c.ops)*m['limitWyjscia']['qBajty'] for c,m in zip(rows,manifest['przypadki']))
    free=shutil.disk_usage(C.base.TEMP).free
    save('PROBA-KONTAKTY.json',{'N':49,'includes_family':13,'streams':stats,'free_bytes':free,'actual_operations':measured['operations'],
         'exact_operation_count_upper_bytes_per_stream':ceiling,'exact_operation_count_upper_bytes_three_streams':3*ceiling,
         'time_limit_full_seconds':1200,'extrapolation':[s['seconds']*measured['operations']/sum(len(c.ops) for c in rows[:49]) for s in stats]})
    if free<3*ceiling+2*1024**3:raise C.base.StepFailed('9b free disk below frozen format bound plus 2 GiB')
    if result['errors']:
        print('Odmowa proba-kontakty: '+str(result['errors']),flush=True);return 1
    return 0

def full(side):
    if code('etap-port-proba-kontakty'):raise C.base.StepFailed('9b full run requires successful method A / B13 sample')
    binary=OUT/(('duckling-kontakty' if side=='duckling' else 'c9b-'+side)+'-bin')
    name='duckling-kontakty' if side=='duckling' else 'c9b-'+side
    before=source_sums();result=run(name,binary,input_path=OUT/('przypadki-kontakty-stdin.csv' if side=='duckling' else 'przypadki-kontakty.csv'),c_side=side!='duckling',seconds=1200)
    unchanged(before);return int(result[0]!=0 or bool(result[2].read_bytes()))

def check():
    result=p.compare_files(OUT/'c9b-obs1.csv',OUT/'duckling-kontakty.csv',OUT/'c9b-obs0.csv',g.cases(),
        (code('c9b-obs1-wykonanie'),code('duckling-kontakty-wykonanie'),code('c9b-obs0-wykonanie')))
    save('POROWNANIE-KONTAKTY.json',result)
    branches=C.world_module('galezie-kontakty.py','ci_contact_branches')
    try:observed=branches.observed(OUT/'c9b-obs1.csv')
    except (ValueError,OSError,KeyError,IndexError) as exc:observed={'hits':{},'missing':['observations: '+str(exc)]}
    save('kontakty-galezie-obserwacje.json',observed)
    discovered={pattern:sorted(x.name for x in PORT.glob(pattern)) for pattern in ('test_kontakty*.py','test_pary*.py')}
    save('kontakty-moduly-sprawdzianow.json',discovered)
    expected=json.loads((PORT/'mutacje-kontakty.json').read_bytes())['test_modules']
    if discovered!=expected:raise C.base.StepFailed('9b discovered test modules differ from frozen mutation manifest')
    reasons=[]
    if result['errors']:reasons.append('porownanie/projekcja/model: '+str(result['errors']))
    if observed['missing']:reasons.append('obserwacje galezi: '+str(observed['missing']))
    failed=bool(reasons)
    for pattern in discovered:
        name='sprawdziany-'+('kontakty' if 'kontakty' in pattern else 'pary-regresja9b')
        actual=C.base.run(name,[sys.executable,'-B','-m','unittest','discover','-s','silnik/port','-p',pattern,'-v'],seconds=240,
            env={**os.environ,'KONTAKTY_REQUIRE_PRODUCT':'1'})
        if actual:
            failed=True;reasons.append(f'{name}: code {actual}');show_stderr(name)
    if failed:print('Odmowa check-kontakty: '+'; '.join(reasons),flush=True)
    return int(failed)

def refusal_prefix(ident,data,replay=False):
    plan=negative.prefix_plan(ident,data)
    if 'fixed' in plan:return negative.expected_prefix(plan)
    name='kontakty-prefiks-'+ident;encoded=g.encode(plan['rows']).encode('ascii')
    if replay:
        if code(name+'-wykonanie') or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():raise ValueError('fatal-prefix control failed: '+ident)
        if (OUT/'wejscia-swiat'/(name+'.csv')).read_bytes()!=encoded:raise ValueError('fatal-prefix control input changed: '+ident)
        path=OUT/(name+'.csv')
    else:path=need_success(run(name,OUT/'c9b-obs1-bin',encoded,c_side=True))
    with path.open(encoding='ascii',newline='') as stream:p.validate_output(stream,plan['rows'])
    return negative.expected_prefix(plan,path.read_bytes())

def negatives():
    negative.write(OUT/'ujemne-kontakty');results=[]
    for ident,c,d,diag in negative.probes():
        prefix=refusal_prefix(ident,c)
        for side,binary,data in (('c',OUT/'c9b-obs1-bin',c),('duckling',OUT/'duckling-kontakty-bin',d)):
            name=f'kontakty-ujemny-{ident}-{side}';actual,path,stderr=run(name,binary,data,c_side=side=='c',expected_code=2,expected_stderr=diag)
            stdout=path.read_bytes();ok=actual==2 and stderr.read_bytes()==diag and stdout==prefix
            results.append({'id':ident,'side':side,'code':actual,'stderr':stderr.read_text(encoding='ascii',errors='backslashreplace'),
                            'expected_stdout_bytes':len(prefix),'expected_stdout_sha256':hashlib.sha256(prefix).hexdigest(),'ok':ok})
    for variant,c,d in negative.positives():
        for side,binary,data in (('c',OUT/'c9b-obs1-bin',c),('duckling',OUT/'duckling-kontakty-bin',d)):
            name=f'kontakty-dodatni-{variant}-{side}';actual,path,stderr=run(name,binary,data,c_side=side=='c');ok=actual==0 and not stderr.read_bytes()
            try:
                with path.open(encoding='ascii',newline='') as inp:p.validate_output(inp,g.cases()[:1])
            except ValueError:ok=False
            results.append({'id':variant,'side':side,'code':actual,'ok':ok})
    save('kontakty-ujemne-wynik.json',results);return int(len(results)!=2*(len(negative.probes())+len(negative.positives())) or not all(r['ok'] for r in results))

def fixtures():
    module=C.world_module('fixtury-kontakty.py','ci_contact_fixtures');failed=module.run(C,sys.modules[__name__])
    if failed:print('Odmowa fixtury-kontakty: niepelne lub bledne wyniki; kontakty-fixtury-wynik.json.',flush=True)
    return failed
def mutations():
    blocked={stage_:code('etap-port-'+stage_) for stage_ in ('check-kontakty','ujemne-kontakty') if code('etap-port-'+stage_)}
    if not blocked:
        fixture_module=C.world_module('fixtury-kontakty.py','ci_contact_fixture_baseline')
        issues={}
        try:
            results=json.loads((OUT/'kontakty-fixtury-wynik.json').read_bytes())
            definitions=fixture_module.definitions()
            if [r['name'] for r in results]!=[r['name'] for r in definitions]:issues['manifest']='missing, duplicate or unexpected fixture'
            for fixture in definitions:
                sides={}
                for side in ('c','duckling'):
                    name='fixture9-'+fixture['name']+'-'+side
                    sides[side]={'code':code(name+'-wykonanie'),'stderr_bytes':(OUT/(name+'-wykonanie-stderr.csv')).stat().st_size,
                                 'output':fixture_module.output_signature(OUT/(name+'.csv'))}
                if sides['c']['output']!=sides['duckling']['output'] or any(s['code']!=0 or s['stderr_bytes'] for s in sides.values()):issues[fixture['name']]=sides
        except (OSError,ValueError,KeyError,TypeError) as exc:issues['evidence']=str(exc)
        if issues:blocked['fixtury-kontakty']=issues
    if blocked:
        save('mutacje-kontakty-wynik.json',[]);save('mutacje-kontakty-blokada.json',{'reason':'native baseline/comparison/negative/fixture execution mismatch','blocked':blocked})
        print('Eacfb7a6be77f E417ddba2a19e-Ea09b5116269e: expected E460e1a01683c Ecd5b158f21b7 E4cf6829aa937 Eb07d33317983: '+str(blocked)+
              '; Ec80f9808d6ac E019a6dde7ab9-Ea09b5116269e (Ee96e02d8e47f code Eb5ff149a858d Ecd5b158f21b7 E0f9e3d218af1): '+str(code('etap-port-fixtury-kontakty')),flush=True)
        return 1
    module=C.world_module('mutacje-kontakty.py','ci_contact_mutations');failed=module.run(C,sys.modules[__name__])
    branches=C.world_module('galezie-kontakty.py','ci_contact_native_branches')
    receipts=branches.native_receipts(json.loads((OUT/'mutacje-kontakty-wynik.json').read_bytes()),json.loads((OUT/'kontakty-galezie-obserwacje.json').read_bytes()))
    save('kontakty-galezie-wynik.json',receipts)
    if failed or receipts['blocking_gaps']:print(f'Odmowa mutacje-kontakty: niepelne wykrycie mutacji (code {failed}); luki galezi: {receipts['blocking_gaps']}.',flush=True)
    return int(failed or bool(receipts['blocking_gaps']))

def mutation_evidence(recipe,row):
    try:
        if recipe.get('probe')=='material-shared':
            shared=C.world_module('mutacje-kontakty.py','contact_shared_evidence')
            rows=row.get('witness_results',[])
            if not shared.shared_material_complete(recipe,rows):return False
            return all(mutation_evidence(child,result) for child,result in zip(shared.shared_material_children(recipe),rows))
        if recipe.get('solver_replacement'):
            approved={'g-step-b2World_Step':'A9-08','g-step-b2World_Step-negative':'A9-09'}
            approval=approved.get(recipe['name'])
            if not approval or recipe['solver_replacement']!=approval or row.get('approval')!=approval:return False
            native=C.world_module('mutacje-solver.py','ci_contact_successor_evidence')
            guard=native.group_for(native.replacement_recipe(recipe));data=guard.encode(True)
            storage=native.load('contact_successor_stream','zapis-strumieni.py')
            if row.get('name')!=recipe['name'] or row.get('class_id')!=recipe['class_id'] or row.get('witness')!=recipe['guard_group']:return False
            if row.get('input_sha256')!=hashlib.sha256(data).hexdigest():return False
            if not (row.get('detected') is True and row.get('clean') is True and row.get('replayed_before_compaction') is True and row.get('difference')):return False
            if row.get('baseline_code')!=0 or row.get('code')!=0:return False
            name='mutation10-'+recipe['name']
            if code('oslony-profile4-kompilacja') or code(name+'-kompilacja'):return False
            streams=[];outputs=[]
            for suffix in ('-base',''):
                tag=name+suffix
                if code(tag+'-wykonanie') or (OUT/(tag+'-wykonanie-stderr.csv')).read_bytes():return False
                if (OUT/'wejscia-swiat'/(tag+'.csv')).read_bytes()!=data:return False
                stream=json.loads((OUT/(tag+'-stream.json')).read_bytes())
                if not stream.get('sha256') or stream.get('bytes',0)<=0 or stream.get('records',{}).get('END')!=1:return False
                if stream.get('validation_before_compaction')!='native clean difference replayed from disk':return False
                path=OUT/(tag+'.csv');actual=storage.manifest(path)
                if any(stream.get(key)!=actual[key] for key in ('sha256','bytes','records')):return False
                outputs.append(native.public_records(path.read_bytes(),[(1,guard.rows)],guard=guard,properties=bool(suffix)))
                streams.append(stream['sha256'])
            if streams[0]==streams[1]:return False
            difference=native.first_difference(*outputs,recipe['expected_tags'])
            if not difference or json.dumps(difference,sort_keys=True)!=json.dumps(row['difference'],sort_keys=True):return False
                                                                           
                                                                          
                                                                               
            seq=len(guard.rows)-(2 if approval=='A9-08' else 1)
            if guard.rows[seq-1][0]!=(32 if approval=='A9-08' else 31):return False
            if difference.get('tag')!='R' or difference.get('word')!=3:return False
            if difference['before'][:2]!=(1,seq) or difference['after'][:2]!=(1,seq):return False
            if difference['before'][3]!=0 or difference['after'][3]!=5:return False
            before=json.loads((OUT/'oslony-produkt-przed-sha256.json').read_bytes())
            after=json.loads((OUT/'oslony-produkt-po-sha256.json').read_bytes())
            if not (bool(before) and before==after and all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in after.items())):return False
                                                                           
                                                                             
            binary=C.base.TEMP/(name+'-odbior-bin');compiled=json.loads((OUT/(name+'-binary.json')).read_bytes())
            if compiled!={'bytes':binary.stat().st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}:return False
            replay=name+'-odbior';replay_code,output=C.run_world_fixture(replay,binary,data)
            if replay_code or (OUT/(replay+'-wykonanie-stderr.csv')).read_bytes():return False
            return output==(OUT/(replay+'.csv')).read_bytes()==(OUT/(name+'.csv')).read_bytes()
        name='mutacja9-'+row['name']
        if row['code'] or code(name+'-wykonanie') or code(name+'-kompilacja') or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
        return bool(row['replayed_before_compaction'] and row['difference'] and row['stream']['sha256'])
    except (ValueError,KeyError,OSError,TypeError,IndexError):return False


def evidence():
    try:
        for file in ('kod-miedzy-zadaniami-kod.csv','narzedzia9b-odtworzenie-kod.csv'):
            if int((OUT/file).read_text())!=0:return False
        for name in STAGES:
            if code('etap-port-'+name):return False
        for name in ('POROWNANIE-KONTAKTY','POROWNANIE-KONTAKTY-PROBA'):
            if json.loads((OUT/(name+'.json')).read_bytes())['errors']:return False
        results=json.loads((OUT/'kontakty-ujemne-wynik.json').read_bytes())
        if len(results)!=2*(len(negative.probes())+len(negative.positives())) or not all(r['ok'] for r in results):return False
        for ident,c,d,diag in negative.probes():
            prefix=refusal_prefix(ident,c,replay=True)
            for side,data in (('c',c),('duckling',d)):
                name=f'kontakty-ujemny-{ident}-{side}'
                if code(name+'-wykonanie')!=2 or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes()!=diag:return False
                if (OUT/'wejscia-swiat'/(name+'.csv')).read_bytes()!=data:return False
                if (OUT/(name+'.csv')).read_bytes()!=prefix:return False
        for variant,c,d in negative.positives():
            for side,data in (('c',c),('duckling',d)):
                name=f'kontakty-dodatni-{variant}-{side}'
                if code(name+'-wykonanie') or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
                if (OUT/'wejscia-swiat'/(name+'.csv')).read_bytes()!=data:return False
                with (OUT/(name+'.csv')).open(encoding='ascii',newline='') as stream:p.validate_output(stream,g.cases()[:1])
        recipes=json.loads((PORT/'mutacje-kontakty.json').read_bytes())['native_mutations'];mutations_=json.loads((OUT/'mutacje-kontakty-wynik.json').read_bytes())
        if len(recipes)!=RECIPE_COUNT:return False
        if [r['name'] for r in recipes]!=[r['name'] for r in mutations_] or not all(r['detected'] for r in mutations_):return False
        branches=C.world_module('galezie-kontakty.py','contact_evidence_coverage')
        coverage=branches.mutation_coverage(mutations_,deferrals=json.loads((OUT/'mutacje-kontakty-odroczenia.json').read_bytes()))
        if coverage['errors']:return False
        fixture_module=C.world_module('fixtury-kontakty.py','contact_evidence_fixtures')
        fixtures_=json.loads((OUT/'kontakty-fixtury-wynik.json').read_bytes())
        if [f['name'] for f in fixture_module.definitions()]!=[f['name'] for f in fixtures_] or not all(f['ok'] for f in fixtures_):return False
        for fixture in fixture_module.definitions():
            paths=[]
            for side,dec in (('c',False),('duckling',True)):
                name='fixture9-'+fixture['name']+'-'+side;path=OUT/(name+'.csv');paths.append(path)
                if code(name+'-wykonanie') or (OUT/(name+'-wykonanie-stderr.csv')).read_bytes():return False
                if (OUT/'wejscia-swiat'/(name+'.csv')).read_bytes()!=fixture_module.input_data(fixture,dec):return False
                if fixture['kind']=='guard-helper':
                    if path.read_bytes().splitlines()[-1:]!=[f'GUARD9 {fixture['expected_guard_status']}'.encode('ascii')]:return False
                elif fixture['kind']=='bitset-helper':
                    if path.read_bytes()!=fixture_module.bitset_expected():return False
                else:
                    seeds={fixture['seed_seq']:fixture['seed_last']} if fixture['kind']=='ticket' else None
                    if fixture.get('stop_after_seq'):
                        text=path.read_text(encoding='ascii').replace('GUARD9 BATCH\n','ENDCASE 1\nEND 1\n')
                        p.validate_output(text,fixture['rows'],guard=True,seed_last=seeds)
                    else:
                        with path.open(encoding='ascii',newline='') as stream:p.validate_output(stream,fixture['rows'],guard=True,seed_last=seeds)
                    if 'expected_last_status' in fixture:
                        rs=[line.split() for line in path.read_text(encoding='ascii').splitlines() if line.startswith('R ')]
                        if int(rs[-1][4])!=fixture['expected_last_status']:return False
            if paths[0].read_bytes()!=paths[1].read_bytes():return False
        for recipe,row in zip(recipes,mutations_):
            if not mutation_evidence(recipe,row):return False
        if json.loads((OUT/'produkt-kontakty-przed-sha256.json').read_bytes())!=json.loads((OUT/'produkt-kontakty-po-sha256.json').read_bytes()):return False
        if json.loads((OUT/'kontakty-galezie-wynik.json').read_bytes())['blocking_gaps']:return False
        if source_sums()!=json.loads((OUT/'box2d-kontakty-przed-sha256.json').read_bytes()):return False
        linking=json.loads((OUT/'kontakty-linkowanie-A.json').read_bytes())
        if linking['world_c_count']!=1 or linking['broad_phase_c_count']!=1 or linking['full_legacy_archive_linked']:return False
        archive=C.base.TEMP/'contact-a9-build/libbox2d-component-a9.a'
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=linking['archive_sha256']:return False
        for side in ('c9b-obs0','c9b-obs1','duckling-kontakty'):
            if code(side+'-wykonanie') or (OUT/(side+'-wykonanie-stderr.csv')).read_bytes():return False
        return True
    except (ValueError,KeyError,OSError):return False

def summary():
    prior=OUT.parent/'krok9a/wynik-kod.csv';valid=evidence()
    failed=not valid or os.environ.get('REGRESJE_OUTCOME')!='success' or not prior.exists() or prior.read_text().strip()!='0'
    lines=['# Krok 9b — COMPONENT_A9','','| Etap | Kod | GitHub |','|---|---:|---|']
    for stage_ in STAGES:
        actual=code('etap-port-'+stage_);outcome=os.environ.get(stage_.replace('-','_').upper()+'_OUTCOME','MISSING');failed|=actual!=0 or outcome!='success';lines.append(f'| {stage_} | {actual} | {outcome} |')
    mutation_results=OUT/'mutacje-kontakty-wynik.json'
    if mutation_results.exists():
        try:
            results=json.loads(mutation_results.read_bytes())
            counts={kind:sum(r.get('detected') is True and r.get('detected_by','roznica')==kind for r in results) for kind in ('roznica','struktura')}
            counts['NIEWYKRYTY']=sum(r.get('status')=='NIEWYKRYTY' for r in results)
            counts['ERROR']=sum(r.get('detected') is not True and r.get('status')!='NIEWYKRYTY' for r in results)
            failed|=sum(counts.values())!=len(results)
            lines+=['','Mutacje: difference='+str(counts['roznica'])+'; struktura='+str(counts['struktura'])+'; NIEWYKRYTY='+str(counts['NIEWYKRYTY'])+'; ERROR='+str(counts['ERROR'])]
        except (ValueError,TypeError,AttributeError) as exc:failed=True;lines+=['','BLAD odczytu licznikow mutacji: '+str(exc)]
    deferred=OUT/'mutacje-kontakty-odroczenia.json'
    if deferred.exists():
        branches=C.world_module('galezie-kontakty.py','contact_summary_deferral')
        accepted=json.loads(deferred.read_bytes())==branches.unresolved_classes()
        failed|=not accepted;lines+=['','M12: '+('odroczenia9b=0; wymagany aktualny natywny dowod kroku11 (D11-3)' if accepted else 'BLAD: niedozwolone odroczenie')]
    lines+=['',f'Dowody: {valid}; N64; operacje {sum((len(c.ops) for c in g.cases()))}.','RESULT STEPS 1–9b: '+('FAIL' if failed else 'OK'),'']
    (OUT/'DZIENNIK.md').write_text('\n'.join(lines),encoding='utf-8');(OUT/'wynik-kod.csv').write_text('1\n' if failed else '0\n',encoding='ascii');print('\n'.join(lines));return int(failed)

def compact():
    try:
        try:return compact_streams()
        finally:
            storage=C.world_module('zapis-kontakty.py','contact_publication_safety')
            storage.prepare_publication(OUT)
    except Exception as exc:
        result=OUT/'wynik-kod.csv'
        if not result.exists() or result.read_text().strip()!='1':
            result.write_bytes(b'1\n')
            with (OUT/'DZIENNIK.md').open('a',encoding='utf-8',newline='\n') as log:
                log.write('\nFAIL Ec61c31625875 E3ab717745a40: '+str(exc)+'\nRESULT STEPS 1–9b: FAIL\n')
        raise

def compact_streams():
                                                                           
    if not code('etap-port-check-kontakty'):
        current=p.compare_files(OUT/'c9b-obs1.csv',OUT/'duckling-kontakty.csv',OUT/'c9b-obs0.csv',g.cases())
        if current['errors']:raise C.base.StepFailed('9b evidence changed before compaction')
    entries={};listing=OUT/'kontakty-lista-strumieni.json';names=json.loads(listing.read_bytes()) if listing.exists() else []
    if len(names)!=len(set(names)):raise ValueError('duplicate streams')
    storage=C.world_module('zapis-kontakty.py','contact_storage')
    for name in names:
        if Path(name).name!=name or not name.endswith('.csv'):raise ValueError('stream path escaped output')
        path=OUT/name
        if path.exists():entry=storage.manifest(path);save(name+'.manifest.json',entry);path.unlink()
        else:entry=json.loads((OUT/(name+'.manifest.json')).read_bytes())
        entries[name]=entry
    save('STRUMIENIE-KONTAKTY-MANIFEST.json',entries)
    for binary in OUT.glob('*-bin'):
        save(binary.name+'-sha256.json',{'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'bytes':binary.stat().st_size});binary.unlink()
    note='Eff624a4b9cdb E6d0a271d4a15 E5fade8046c7f Ee015828237b8 E40e5bdb58a49; E7d50bea2c625 SHA-256, bytes, E828c68d0f522, E5de2502ef871 E5165a53444c6 Ede7d1b721a1e E5422e223df9f. E5dc1c90633c4 Ed9959ff03720 E3ab717745a40 E50e721e49c01 E1d4d759b3692.\n'
    if code('etap-port-check-kontakty') or not listing.exists():
        note='E30d8f16a6d72 Ef5cd2c5d69b8 Ed0afe5ed2bd6 FAIL; missing E0c6729e37728 Ed9959ff03720 E3ab717745a40. E8b6ed86e0f70 Ed7d6ec01f500 Ee6f723fb7925, E5c74971662f4 Ede7d1b721a1e E03b382aabe85 Ead9a1701b1d7 E5788f15f781d; Ebc2e4bea2e33 Ed763a792f268 E01a44d970bf3 E74b62e088ba2.\n'
    (OUT/'ZAPIS-KONTAKTY.md').write_text(note,encoding='utf-8');return 0

def stage(context,name):
    init(context)
    return {'proba-kontakty':sample,'c-kontakty-obs0':lambda:full('obs0'),'c-kontakty-obs1':lambda:full('obs1'),
            'native-kontakty':lambda:full('duckling'),'check-kontakty':check,'ujemne-kontakty':negatives,
            'fixtury-kontakty':fixtures,'mutacje-kontakty':mutations,'summary-kontakty':summary,'zapis-strumieni-kontakty':compact}[name]()
