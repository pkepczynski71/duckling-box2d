from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                          
from collections import defaultdict
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
try:
    import resource
except ImportError:
    resource=None
import shutil
import sys
import time
import re

STAGES=('proba-solver','porownanie-solver','component-solver','check-solver')

def init(context):
    global C,OUT,PORT,ROOT,g,p,build,storage
    C=context;OUT=C.OUT;PORT=C.PORT;ROOT=C.ROOT
                                                                                
                                                            
    sys.argv[1]='solver10'
    g=C.world_module('przypadki-solver.py','solver_ci_inputs')
    p=C.world_module('porownaj-solver.py','solver_ci_compare')
    build=C.world_module('budowa-solver.py','solver_ci_builder')
    storage=C.world_module('zapis-solver.py','solver_ci_storage')

def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def code(name):return C.shape_code(name)

def compile_c():
    source=C.base.TEMP/'box2d';directory=C.base.TEMP/'solver10-build';directory.mkdir(parents=True,exist_ok=True)
    before=build.source_sums(source)
    contract=norm_text(PORT/'fixtures/norms/KONTRAKT-7.json')
    if any(f'{digest}  {name}' not in contract for name,digest in before.items()):raise C.base.StepFailed('10 original source hashes differ from accepted 7')
    save('box2d-solver-przed-sha256.json',before)
    specialized=build.adapter(PORT,directory);commands=build.commands(PORT,source,directory)
    save('solver-compile_commands.json',commands)
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
        raise C.base.StepFailed('normative C profile requires x86_64 Linux, no substitute platform')
    C.base.need('c10-cc-version',['cc','--version'],seconds=15)
    C.base.need('c10-uname',['uname','-a'],seconds=15)
    includes=['-I'+str(directory),'-I'+str(PORT),'-I'+str(source/'include'),'-I'+str(source/'src')]
    C.base.need('c10-preprocessor',['cc',*build.FLAGS,*includes,'-dM','-E',PORT/'kontrola-solver-contact.c'],seconds=30)
    macros={}
    for line in (OUT/'c10-preprocessor.csv').read_text(encoding='ascii').splitlines():
        fields=line.split(maxsplit=2)
        if len(fields)>=2 and fields[0]=='#define':macros[fields[1]]=fields[2] if len(fields)>2 else ''
    if macros.get('B2_SIMD_WIDTH')!='4' or 'B2_SIMD_NONE' not in macros or 'BOX2D_AVX2' in macros or macros.get('B2_VALIDATE')!='0':
        raise C.base.StepFailed('actual preprocessor profile differs from frozen scalar width4 Release')
    if not re.search(r'^#define\s+B2_FORCE_OVERFLOW\s+0\s*$',(source/'src/constraint_graph.c').read_text(),re.M):
        raise C.base.StepFailed('natural overflow configuration changed')
    failures=[]
    for item in commands:
        try:C.base.need('c10-unit-'+Path(item['original']).stem,item['arguments'],seconds=60)
        except C.base.StepFailed as exc:
            failures.append(str(exc))
    if failures:raise C.base.StepFailed('; '.join(failures))
    archive=directory/'libbox2d-solver10.a'
    C.base.need('c10-archive',['ar','rcs',archive,*[r['output'] for r in commands]],seconds=180)
    C.base.need('c10-symbols',['nm','--defined-only',archive],seconds=180)
    symbols=(OUT/'c10-symbols.csv').read_text(encoding='ascii').splitlines()
    for symbol in ('b2World_Step','b2UpdateBroadPhasePairs','b2Solve','b2PrepareContactsTask','port10OriginalCreateContact'):
        if sum(line.split()[-1:]==[symbol] for line in symbols)!=1:raise C.base.StepFailed('10 symbol must occur exactly once: '+symbol)
    failures=[]
    for label,obs,defines in (('obs0',0,()),('obs1',1,()),('component',1,('-DCOMPONENT10_MAIN',))):
        binary=OUT/f'c10-{label}-bin'
        try:
            C.base.need(f'c10-{label}-kompilacja',['cc',*build.FLAGS,'-Wall','-Wextra','-Wno-unused-function','-Wno-unused-value',
                        '-Wno-misleading-indentation','-DOBS='+str(obs),*defines,*includes,PORT/'kontrola-solver.c',archive,'-lm','-o',binary],seconds=90)
        except C.base.StepFailed as exc:
            binary.unlink(missing_ok=True)
            failures.append(str(exc))
    after=build.source_sums(source);save('box2d-solver-po-sha256.json',after)
    if before!=after:raise C.base.StepFailed('10 original source changed during build')
    if failures:raise C.base.StepFailed('; '.join(failures))
    save('solver-linkowanie-A.json',{'original_count':35,'units':commands,'original_sources':before,
          'specialized_transport_sha256':specialized,'original_contact_definition_renamed':'port10OriginalCreateContact',
          'transparent_create_wrapper':'b2CreateContact: exactly one original call before metadata stamp',
          'flags':build.FLAGS,'width':4,'workers':1,'full_legacy_archive_linked':False,
          'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
          'compiler_path':shutil.which('cc'),'compiler_version':(OUT/'c10-cc-version.csv').read_text(encoding='utf-8'),
          'platform':platform.uname()._asdict(),'cpuinfo':Path('/proc/cpuinfo').read_text() if Path('/proc/cpuinfo').is_file() else None,
          'actual_profile_macros':{key:macros.get(key) for key in ('B2_SIMD_WIDTH','B2_SIMD_NONE','B2_VALIDATE','BOX2D_DISABLE_SIMD','BOX2D_AVX2','NDEBUG')},
          'natural_force_overflow':0,'source_archive_downloaded':False})

def compile_duck():
    driver=PORT/'solver-swiata.dk'
    if not driver.is_file():raise C.base.StepFailed('Transport silnik/port/solver-swiata.dk is missing')
    binary=C.compile_world_fixture(C.world_duckc(),'duckling-solver',driver,ROOT/'silnik/fizyka')
    save('duckling-solver-binary-sha256.json',{'bytes':binary.stat().st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()})
    directory=C.base.TEMP/'duckling-solver-build'
    if directory.resolve().is_relative_to(C.base.TEMP.resolve()) and directory.is_dir():shutil.rmtree(directory)
    return binary

def compile_component_duck():
    pass                                                              

                                                                            
                                                                        
       
    requested=os.environ.get('SOLVER_COMPONENT_DRIVER')
    generated=False;original=PORT/'solver-swiata.dk'
    before=hashlib.sha256(original.read_bytes()).hexdigest() if original.is_file() else None
    if requested:
        driver=(ROOT/requested).resolve()
        if not driver.is_relative_to(ROOT.resolve()) or not driver.is_file():
            raise C.base.StepFailed('COMPONENT entry must be an existing file in this checkout')
    else:
        if not (PORT/'fixtury-solver.py').is_file() or before is None:
            raise C.base.StepFailed('COMPONENT entry missing: merge T2b native_driver() and K before building a separate fixture')
        fixtures=C.world_module('fixtury-solver.py','solver_component_binding')
        driver=C.base.TEMP/'solver-component-driver.dk'
        driver.write_text(fixtures.native_driver(original.read_text(encoding='utf-8'),5),encoding='utf-8',newline='\n');generated=True
    try:
        binary=C.compile_world_fixture(C.world_duckc(),'duckling-solver-component',driver,ROOT/'silnik/fizyka')
        save('duckling-solver-component-binary-sha256.json',{'bytes':binary.stat().st_size,
            'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'driver':str(driver),
            'binding':'fixtury-solver.native_driver(profile=5)' if generated else 'explicit entry',
            'original_driver_sha256':before})
    finally:
        if generated and driver.is_file():driver.unlink()
        if before is not None and hashlib.sha256(original.read_bytes()).hexdigest()!=before:
            raise C.base.StepFailed('Protected product driver changed during COMPONENT fixture build')
    directory=C.base.TEMP/'duckling-solver-component-build'
    if directory.resolve().is_relative_to(C.base.TEMP.resolve()) and directory.is_dir():shutil.rmtree(directory)
    return binary

def argv(side, *, component=False, sample=False):
    stem=('proba-' if sample else '')+('component-solver' if component else 'solver')
    if sample and not component:stem='proba6-solver'
    if not sample and not component:stem='przypadki-solver'
    input_=OUT/(stem+('-stdin' if side=='duckling' else '')+'.csv')
    if side=='duckling':
        binary='duckling-solver-component-bin' if component else 'duckling-solver-bin'
        return ['bash','-c','exec "$1" < "$2"','solver-input',OUT/binary,input_]
    return [OUT/('c10-component-bin' if component else 'c10-'+side+'-bin'),input_]

def w1_trial():
    fixture=C.world_module('proba-solver-bilety.py','solver_w1_fixture')
    c=fixture.case(g);inputs=OUT/'wejscia-solver';inputs.mkdir(exist_ok=True)
    paths={};results={};input_hashes={};errors=[];processes={}
    for side in ('obs0','obs1','duckling'):
        name='w1-bilety-'+side;path=OUT/(name+'.raw.csv');paths[side]=path
        command=[];exit_code=1;stderr=b'';exception=None;validation_error=None
        try:
            data=g.encode([c],side=='duckling').encode('ascii')
            source=inputs/('W1-BILETY-'+side+'.csv');source.write_bytes(data)
            input_hashes[side]=hashlib.sha256(data).hexdigest()
            command=([OUT/('c10-'+side+'-bin'),source] if side!='duckling' else
                     ['bash','-c','exec "$1" < "$2"','W1-input',OUT/'duckling-solver-bin',source])
            exit_code=C.base.run(name,command,stdout=path,seconds=60)
            stderr=(OUT/(name+'-stderr.csv')).read_bytes()
            if exit_code or stderr:errors.append('W1 '+side+': exit '+str(exit_code)+', stderr: '+stderr.decode('utf-8',errors='replace'))
        except Exception as exc:
            exception=C.record_process_exception(name,command,exc,stdout=path)
            stderr=(OUT/(name+'-stderr.csv')).read_bytes()
            errors.append('W1 '+side+': '+exception)
        results[side]=exit_code
        try:
            with path.open(encoding='ascii',newline='') as stream:p.validate_output(stream,[c],side!='obs0')
            if side!='obs0':
                with path.open(encoding='ascii',newline='') as stream:fixture.check(stream,c,p)
        except Exception as exc:
            validation_error=type(exc).__name__+': '+str(exc)
            errors.append('W1 '+side+': '+validation_error)
        processes[side]=C.process_diagnosis(exit_code,stderr,exception,validation_error)
    receipt={'errors':[]}
    try:
        receipt=p.compare_files(paths['obs1'],paths['duckling'],paths['obs0'],[c],
                    tuple(results[side] for side in ('obs1','duckling','obs0')),models=models())
    except Exception as exc:errors.append('W1 comparison: '+type(exc).__name__+': '+str(exc))
    receipt['errors']+=errors
    receipt.update(id=fixture.ID,input_sha256=input_hashes,codes=results,processes=processes,
                   models_checked=not receipt['errors'],W1_checks=not receipt['errors'])
    receipt['stream_manifests']={}
    for side,path in paths.items():
        try:receipt['stream_manifests'][side]=storage.manifest(path)
        except Exception as exc:receipt['errors'].append(side+' manifest: '+str(exc))
    save('W1-BILETY-PUBLIC10.json',receipt)
    if receipt['errors']:raise C.base.StepFailed('W1 full C/D/OBS mismatch: '+str(receipt['errors']))
                                                                               
    for path in paths.values():path.unlink()


def sample(prebuilt=False):
    OUT.mkdir(parents=True,exist_ok=True)
    save('solver-proba-pomiar.json',{'resource_allowed':False,'reason':'sample resource measurement incomplete'})
    inputs=g.write(OUT);save('solver-operacje.json',inputs)
    probe_cases=g.verify()[:6]
    probe_hashes={}
    for decimal in (False,True):
        name='proba6-solver'+('-stdin' if decimal else '')+'.csv';data=g.encode(probe_cases,decimal).encode('ascii')
        (OUT/name).write_bytes(data);probe_hashes[name]=hashlib.sha256(data).hexdigest()
    save('proba6-solver-wejscia-sha256.json',probe_hashes)
    files=sorted(set([*PORT.glob('*.py'),*PORT.glob('*.c'),*PORT.glob('*.h'),*PORT.glob('*.json'),
                      *PORT.glob('*.dk'),PORT/'fixtures/norms/KONTRAKT-10.json',ROOT/'.github/workflows/port.yml',
                      *ROOT.joinpath('silnik/fizyka').glob('*.dk')]))
    sources={}
    for source in files:
        relative=source.relative_to(ROOT);target=OUT/'zrodla'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target);sources[relative.as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
    save('solver-zrodla-sha256.json',sources)
    if not prebuilt:
        compile_c();compile_duck()
    results={};paths={};started=time.monotonic();process_errors=[]
    for side in ('obs0','obs1','duckling'):
        name='sample-'+side;path=OUT/(name+'.raw.csv');paths[side]=path
        result=C.base.run(name,argv(side,sample=True),stdout=path,seconds=180)
        results[side]=result
        if result or (OUT/(name+'-stderr.csv')).read_bytes():process_errors.append('10 sample process failed: '+side)
    sample_processes_ok=not process_errors
    check=(p.compare_files(paths['obs1'],paths['duckling'],paths['obs0'],probe_cases,
                          tuple(results[s] for s in ('obs1','duckling','obs0')),models=models())
           if not process_errors else {'errors':process_errors,'first_difference':None})
    check['models_checked']=True
    save('solver-proba-porownanie.json',check)
    public_elapsed=time.monotonic()-started
    try:w1_trial()
    except C.base.StepFailed as exc:process_errors.append(str(exc))
    if not prebuilt:compile_component_duck()
    comp_paths={}
    for side in ('obs1','duckling'):
        name='sample-component-'+side;path=OUT/(name+'.raw.csv');comp_paths[side]=path
        result=C.base.run(name,argv(side,component=True,sample=True),stdout=path,seconds=180)
        if result or (OUT/(name+'-stderr.csv')).read_bytes():process_errors.append('10 COMPONENT sample process failed: '+side)
    component_check=(p.compare_files(comp_paths['obs1'],comp_paths['duckling'],None,g.components()[:1],component=True)
                     if not any('COMPONENT' in error for error in process_errors) else {'errors':process_errors,'first_difference':None})
    save('solver-component-proba-porownanie.json',component_check)
    elapsed=public_elapsed
    full=g.MANIFEST['przypadki'];maximum=max(m['limitWyjsciaNaStrone'] for m in full)
    free=shutil.disk_usage(OUT).free
                                                                      
                                                                            
    working_ceiling=3*maximum+2*1024**3
    operations=inputs['operations']
    weighted_bytes=sum(count*m['qSnapshotBytes'] for count,m in zip(operations,full))
    sample_weight=sum(count*m['qSnapshotBytes'] for count,m in zip(operations[:6],full[:6]))
    forecast_seconds=2*elapsed*weighted_bytes/sample_weight
    budget=int(os.environ.get('SOLVER_COMPARE_SECONDS','7200'))
    data={'sample_seconds':elapsed,'sample_streams':{k:storage.manifest(v) for k,v in paths.items()},
          'free_bytes':free,'working_ceiling_bytes':working_ceiling,'frozen_total_ceiling_bytes':g.MANIFEST['objetosc'],
          'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource is not None else None,
          'forecast_seconds':forecast_seconds,'comparison_budget_seconds':budget,
          'sample_N':6,'sample_configs':'substeps1/4/8 x warm0/1 (unchanged canonical prefix)',
          'forecast_method':'2x six-config sample elapsed scaled by checksum(actual opCount*qSnapshotBytes); estimate, not measured full run',
          'codes':results,'transparent_OBS':True,
          'resource_allowed':sample_processes_ok and free>=working_ceiling and forecast_seconds<=budget}
    save('solver-proba-pomiar.json',data)
    if free<working_ceiling or forecast_seconds>budget:
        raise C.base.StepFailed('10 sample forecast exceeds disk/time allocation')
    if check['errors'] or component_check['errors'] or process_errors:
        raise C.base.StepFailed('10 sample C/D/OBS/COMPONENT failures: '+str([*check['errors'],*component_check['errors'],*process_errors]))
                                                                              
                                                                               
    return 0

class ModelAdapter:
    def __init__(self,module,private):
        self.module=module;self.private=private;self.current=None;self.model=None
    def check(self,case,seq,operation,observations,private):
        if self.model is None:
            factory=getattr(self.module,'Model',None) or getattr(self.module,'OwnershipModel',None)
            if factory is None:raise ValueError('Model exports neither Model nor OwnershipModel')
            self.model=factory()
        if hasattr(self.model,'check'):
            return self.model.check(case,seq,operation,observations,private)
        if self.current is not None and self.current!=case:
            if hasattr(self.model,'begin'):self.model.begin()
            else:self.model=type(self.model)()
        self.current=case
        snapshot=getattr(self.model,'snapshot',None)
        if snapshot is None:raise ValueError('Model missing check/snapshot entry')
        rows=defaultdict(list)
        for tag,value in observations:rows[tag].append(value)
        parameters=inspect.signature(snapshot).parameters
        if 'private' in parameters:return snapshot(rows,private=private)
        if not private:raise ValueError('Model snapshot(rows) needs an explicit OBS0/public entry before compaction')
        return snapshot(rows)

def models():
    if not (PORT/'model-solver.py').is_file():raise C.base.StepFailed('Independent model is missing; validation is required before compaction')
    module=C.world_module('model-solver.py','solver_full_independent_model')
    return {label:ModelAdapter(module,private) for label,private in (('C OBS1',True),('Duckling',True),('C OBS0',False))}

def full(component=False):
    if getattr(C,'petla_prebuilt',False):
        try:allowed=json.loads((OUT/'solver-proba-pomiar.json').read_bytes()).get('resource_allowed') is True
        except (OSError,ValueError):allowed=False
        if not allowed:raise C.base.StepFailed('10 full corpus blocked: sample disk/time allocation missing or refused')
    if code('etap-port-proba-solver') and not getattr(C,'petla_prebuilt',False):
        raise C.base.StepFailed('10 sample required before full corpus')
    rows=g.components() if component else g.verify()
    if component and not (OUT/'duckling-solver-component-bin').is_file():
        raise C.base.StepFailed('Separate COMPONENT fixture executable not built in the small trial')
    commands={side:argv(side,component=component) for side in (('obs1','duckling') if component else ('obs0','obs1','duckling'))}
    receipt=storage.case_streams(C,p,rows,commands,component=component,models=None if component else models(),
                                 seconds=int(os.environ.get('SOLVER_COMPARE_SECONDS','7200')))
    return int(any(receipt['process_codes'].values()))

def check():
    bad=[]
    try:
        w1=json.loads((OUT/'W1-BILETY-PUBLIC10.json').read_bytes())
        if w1.get('id')!='W1-BILETY-PUBLIC10' or w1.get('errors') or not w1.get('W1_checks') or not w1.get('models_checked') or any(w1.get('codes',{'missing':1}).values()):
            bad.append('W1 separate real Step receipt incomplete')
        if set(w1.get('stream_manifests',{}))!={'obs0','obs1','duckling'}:bad.append('W1 stream manifests incomplete')
    except (OSError,ValueError,KeyError) as exc:bad.append('W1: '+str(exc))
    for stem,n in (('public10',124),('component10',96)):
        try:
            receipt=json.loads((OUT/(stem+'-manifest.json')).read_bytes())
            if receipt['N']!=n or receipt['completed_cases']!=n or not receipt['global_END_checked'] or any(receipt['process_codes'].values()):bad.append(stem+' incomplete run')
            expected_sides={'obs1','duckling'} if stem=='component10' else {'obs0','obs1','duckling'}
            if set(receipt.get('stderr_bytes',{}))!=expected_sides or any(receipt.get('stderr_bytes',{}).values()):bad.append(stem+' stderr missing/nonempty')
            if len(receipt['cases'])!=n or [r['case'] for r in receipt['cases']]!=list(range(1,n+1)):bad.append(stem+' missing case receipt')
            if any(r['errors'] for r in receipt['cases']):bad.append(stem+' case errors')
            if stem=='public10' and not all(r.get('models_checked') for r in receipt['cases']):bad.append('PUBLIC10 model not checked before compaction')
        except (OSError,ValueError,KeyError) as exc:bad.append(stem+': '+str(exc))
    save('solver-odbior.json',{'errors':bad,'N':124,'component':96,'steps':86456,'long_steps':86400,'phases':2368})
    return int(bool(bad))

def summary(provisional=False):
    outcomes={name:os.environ.get(name.replace('-','_').upper()+'_OUTCOME','MISSING') for name in STAGES}
    failed=check()!=0
    lines=['# step 10 — first Eb5dc7d76e2a2 z Eed4510e5830f','','| Etap | Kod | GitHub |','|---|---:|---|']
    for name in STAGES:
        value=code('etap-port-'+name);failed|=value!=0 or outcomes[name]!='success'
        lines.append(f'| {name} | {value} | {outcomes[name]} |')
    guards=os.environ.get('OSLONY_OUTCOME','MISSING');failed|=guards!='success'
    failed|=not (OUT/'OSLONY.md').is_file() or os.environ.get('REGRESJE_OUTCOME','MISSING')!='success'
    failed|=os.environ.get('TESTY_OUTCOME','MISSING')!='success'
    lines+=['',f'Independent model/guards/comparison: {guards}.','124 PUBLIC + 96 COMPONENT; 86400 Edf19fb2b6367 + 56 Ed3f9245ad84d E8e6a6cca7aae.',
            ('KROK 10: oczekuje odbioru regresji i publikacji' if provisional else
             'RESULT STEPS 1–10: '+('FAIL' if failed else 'OK')),'']
    (OUT/'DZIENNIK.md').write_text('\n'.join(lines),encoding='utf-8');(OUT/'wynik-kod.csv').write_text('1\n' if failed or provisional else '0\n',encoding='ascii')
    print('\n'.join(lines));return int(failed)

def compact():
                                                                              
                                                                              
    storage.prepare_publication(OUT)
    (OUT/'ZAPIS-SOLVER.md').write_text('D-B: Ef0786b32909d Eb5dc7d76e2a2 Ede7d1b721a1e E9372c470eead Ee015828237b8 Ed030df461fa4 Ee4099580139b E22e5cc71ffca; SHA256/bytes/E828c68d0f522/E57a073778132 E5165a53444c6. E371570f4aad0 Ec4352ad04334 E01a44d970bf3 E74b62e088ba2.\n',encoding='utf-8')
    return 0

def stage(context,name):
    init(context)
    return {'proba-solver':sample,'porownanie-solver':full,'component-solver':lambda:full(True),
            'check-solver':check,'summary-solver':lambda:summary(provisional=os.environ.get('GITHUB_REF_NAME')=='uruchom/port'),
            'zapis-strumieni-solver':compact}[name]()
