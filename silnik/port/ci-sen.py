pass                                                                           
import importlib.util
import hashlib
import json
import os
from pathlib import Path
try:
    import resource
except ImportError:
    resource=None
import shutil
import sys
import time
import traceback

STAGES=('budowa-sen','proba-sen','porownanie-sen','component-sen','check-sen')


def init(context):
    global C,OUT,LEGACY_OUT,ROOT,PORT,g,p,builder,storage
    C=context;ROOT=C.ROOT;PORT=C.PORT
    OUT=C.OUT if C.OUT.name=='krok11' else C.OUT.parent/'krok11' if C.OUT.name=='krok10' else C.OUT/'krok11'
    LEGACY_OUT=OUT.parent/'krok10';OUT.mkdir(parents=True,exist_ok=True)
    sys.argv[1]='sen11'                                                                 
    g=C.world_module('przypadki-sen.py','sen_ci_inputs');p=C.world_module('porownaj-sen.py','sen_ci_compare')
    builder=C.world_module('budowa-sen.py','sen_ci_builder');storage=C.world_module('zapis-sen.py','sen_ci_storage')


def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def compile_c():
    source=Path(os.environ.get('SEN_BOX2D_SOURCE',C.base.TEMP/'box2d'))
    if not (source/'src/world.c').is_file():raise ValueError('pinned original source missing; this stage never downloads')
    return builder.build(source,C.base.TEMP/'sen11-build',OUT)


def compile_duck(component=False):
    name='duckling-sen-component' if component else 'duckling-sen'
    (OUT/(name+'-bin')).unlink(missing_ok=True)
    driver=PORT/'sen-swiata.dk'
    if not driver.is_file():raise ValueError('Driver silnik/port/sen-swiata.dk is missing')
    before=hashlib.sha256(driver.read_bytes()).hexdigest();entry=driver
    if component:
                                                                            
        entry=C.base.TEMP/'sen-component-driver.dk'
        entry.write_text(builder.once(driver.read_text(encoding='utf-8-sig'),
            'const CONTACT_PROFILE: i32 = 5i32;','const CONTACT_PROFILE: i32 = 7i32;'),encoding='utf-8',newline='\n')
                                                                                 
    try:
                                                                                   
                                                                                  
        (C.base.TEMP/(name+'-build')/'proba').unlink(missing_ok=True)
        binary=C.compile_world_fixture(C.world_duckc(),name,entry,ROOT/'silnik/fizyka')
        target=OUT/(name+'-bin')
        if binary.resolve()!=target.resolve():shutil.copy2(binary,target)
        save(name+'-sha256.json',{'source_sha256':before,'profile':7 if component else 5,
            'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()})
    finally:
        if component:entry.unlink(missing_ok=True)
        if hashlib.sha256(driver.read_bytes()).hexdigest()!=before:raise ValueError('Product driver changed during compile')


def models(component=False):
    path=PORT/'model-sen.py'
    if not path.is_file():raise ValueError('Independent model model-sen.py is missing')
    m=C.world_module(path.name,'sen_ci_ownership')
                                                                             
    if not hasattr(m,'OwnershipModel'):raise ValueError('OwnershipModel interface missing')
    return {label:m.OwnershipModel() for label in ('C OBS1','Duckling','C OBS0')}


def run_cases(cases,*,component=False,probe=False,intermediate=False,full_ids=None):
    stem='proba' if probe else 'component' if component else 'public'
    if intermediate:stem+='-11a'
    work=OUT/stem;work.mkdir(exist_ok=True)
    model=models(component);commands={}
    safety={}
    class Track:
        def __init__(self,delegate):self.delegate=delegate
        def check(self,case,seq,operation,rows,private):
            self.delegate.check(case,seq,operation,rows,private)
            if not private:return
            r=safety.setdefault(case,{'split_calls':0,'removeCount':0,'candidate':False})
            for tag,v in rows:
                if tag=='TR11' and v[4]==3:r['split_calls']+=1
                if tag=='IS' and v[4]:r['removeCount']=max(r['removeCount'],v[18])
                if tag=='WS11' and (v[5]!=0xffffffff or v[3]==0 and v[6]!=0xffffffff):r['candidate']=True
    if intermediate:model={label:Track(value) for label,value in model.items()}
    for side in ('obs1','duckling','obs0'):
        path=work/('input-'+side+'.csv');path.write_text(g.encode(cases,side=='duckling',component),encoding='ascii',newline='\n')
        if side=='duckling':commands[side]=['bash','-c','exec "$1" < "$2"','sen11-stdin',OUT/('duckling-sen-component-bin' if component else 'duckling-sen-bin'),path]
        else:commands[side]=[OUT/('c11-'+side+'-bin'),path]
        if not Path(commands[side][-2] if side=='duckling' else commands[side][0]).is_file():raise ValueError(side+' binary missing')
    before=time.monotonic()
    try:result=storage.case_streams(work,p,cases,commands,models=model,component=component)
    finally:
        for path in work.glob('input-*.csv'):path.unlink()
    result['model_io_compare_seconds']=time.monotonic()-before
    result['max_child_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource else None
    result['parent_max_RSS_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource else None
    result['RSS_scope']='process-lifetime high-water marks; child maximum includes earlier children of this stage'
    result['free_bytes']=shutil.disk_usage(OUT).free
    if intermediate:
        full_ids=full_ids if full_ids is not None else [c.id for c in cases]
        result['full_scene_ids']=full_ids
        result['diagnostic_only_ids']=[c.id for c in cases if c.id not in full_ids]
        result['no_split_observations']=safety
        result['accepted_full_scenes']=sum(not any(safety.get(i,{}).values()) for i in full_ids)
        result['intermediate_only']=True
        if result['accepted_full_scenes']!=len(full_ids):result['errors'].append('11a subset required Split/removeCount/candidate')
    if probe:
        result['scope']='diagnostic prefixes only, zero full-scene credit'
        total=sum(s['bytes'] for s in result['original_streams'].values());operations=sum(len(c.ops) for c in cases)
        result['forecast']={'method':'observed sample bytes/time per operation, plus fixed frozen ceilings',
            'sample_operations':operations,'sample_bytes':total,'A_ceiling_per_side':g.MANIFEST['objetosc']['A_naStrone'],
            'B_ceiling_per_side':g.MANIFEST['objetosc']['B_naStrone'],'final_ceiling_per_side':g.MANIFEST['objetosc']['publicNaStrone'],
            'upper_seconds_from_observed_byte_rate':g.MANIFEST['objetosc']['publicNaStrone']*3/(total/max(result['seconds'],1e-9))}
    name='proba-sen' if probe else 'component-sen' if component else 'public-sen'
    if intermediate:name+='-11a'
    save(name+'.json',result)
    if result['errors']:raise ValueError('intermediate boundary failed; see '+name+'.json')
    return result


def sample():
    original=g.verify();selected={1:80,7:160,19:420,55:280,77:750};rows=[]
    for c in original[:77]:
        if c.id not in selected:ops=c.ops[:1]
        else:
            steps=0;ops=[]
            for operation in c.ops:
                if operation[0] in (31,32):steps+=1
                if steps>selected[c.id]:break
                ops.append(operation)
        rows.append(g.Case(c.id,'diagnostic prefix',tuple(ops)))
    return tuple(rows)


def check():
    errors=[]
    for stem,n in (('public',g.MANIFEST['N']),('component',16)):
        path=OUT/(stem+'-sen.json')
        if not path.is_file():errors.append(stem+' receipt missing');continue
        result=json.loads(path.read_bytes())
        if result.get('N')!=n or result.get('completed_cases')!=n or not result.get('global_END_checked') or result.get('errors'):
            errors.append(stem+' incomplete or red')
        if not all(c.get('models_checked') for c in result.get('cases',[])):errors.append(stem+' independent models not complete')
    save('kompletnosc-sen.json',{'errors':errors,'required_public':g.MANIFEST['N'],'required_component':16,'required_long_positive':115200})
    return int(bool(errors))


def summary():
    marker=OUT/'RESULT.json';marker.unlink(missing_ok=True)
    errors=[]
    for name in STAGES:
        path=OUT/(name+'-kod.csv')
        if not path.is_file() or path.read_text().strip()!='0':errors.append(name)
    oslony=OUT/'OSLONY.md'
    if not oslony.is_file() or 'RESULT: OK' not in oslony.read_text(encoding='utf-8'):errors.append('Guard checks missing or failed')
    if os.environ.get('SEN_OSLONY_OUTCOME')!='success':errors.append('Guard workflow step missing or failed')
    if check():errors.append('full corpus incomplete')
    old_receipt=LEGACY_OUT/'etap-port-summary-solver-kod.csv'
    old_code=old_receipt.read_text().strip() if old_receipt.is_file() else 'MISSING'
    if old_code!='0':errors.append('prior steps1–10 not green')
    lines=['# Krok11 — pierwsza polowa','',*['- '+e for e in errors],'','RESULT '+('BLAD' if errors else 'OK'),'']
    (OUT/'DZIENNIK.md').write_text('\n'.join(lines),encoding='utf-8')
    (OUT/'wynik-kod.csv').write_text(str(int(bool(errors)))+'\n',encoding='ascii')
    save('podsumowanie-sen.json',{'errors':errors,'prior_steps_code':old_code,'code':int(bool(errors))})
                                                                    
                                                                             
    petla=C.world_module('ci-petla.py','sen_summary_seal')
    provenance=[]
    try:
        provenance=[dict(id='sources',sha256=petla.source_digest(ROOT)),dict(id='tools',sha256=petla.tool_digest(C))]
    except Exception as exc:
        provenance=[dict(id='provenance',code=1,status='BLAD',reason=str(exc))]
    petla.finish(OUT,dict(mode='full',N=11,commit=os.environ.get('GITHUB_SHA')),
        required=[*STAGES,'oslony-sen','corpus-sen','prior-summary-1-10'],
        receipts=[dict(id=name,code=1 if name in errors else 0,status='BLAD' if name in errors else 'OK') for name in STAGES]+[
            dict(id='oslony-sen',code=int(any('OSLONY' in e or 'workflow' in e for e in errors)),status='BLAD' if any('OSLONY' in e or 'workflow' in e for e in errors) else 'OK'),
            dict(id='corpus-sen',code=int('full corpus incomplete' in errors),status='BLAD' if 'full corpus incomplete' in errors else 'OK'),
            dict(id='prior-summary-1-10',code=int(old_code!='0'),status='OK' if old_code=='0' else 'BLAD',reason='; '.join(errors))]+provenance,
        publication={},regressions=None,read_results=False)
                                                                      
    (OUT/'wynik-kod.csv').write_text(str(int(bool(errors)))+'\n',encoding='ascii')
    return int(bool(errors))


def stage(context,name):
    init(context);start=time.monotonic();code=1;error=None
    try:
        if name=='budowa-sen':
                                                                                   
            failures=[]
            for label,fn in (('C',compile_c),('Duckling',compile_duck),('Duckling COMPONENT',lambda:compile_duck(True))):
                try:fn()
                except Exception as exc:failures.append(label+': '+str(exc))
            save('budowy-sen.json',{'errors':failures});code=int(bool(failures))
        elif name=='proba-sen':
            if not (OUT/'budowa-sen-kod.csv').is_file() or (OUT/'budowa-sen-kod.csv').read_text().strip()!='0':
                raise ValueError('both current native builds must pass before the small trial')
            run_cases(sample(),probe=True);code=0
        elif name=='porownanie-sen':
            if not (OUT/'proba-sen-kod.csv').is_file() or (OUT/'proba-sen-kod.csv').read_text().strip()!='0':
                raise ValueError('small trial/projection/model/forecast must pass before the full long corpus')
            run_cases(g.verify());code=0
        elif name=='component-sen':run_cases(g.components(),component=True);code=0
        elif name=='porownanie-sen-11a':
            rows,ids=g.intermediate();run_cases(rows,intermediate=True,full_ids=ids);code=0
        elif name=='component-sen-11a':run_cases(g.components()[:10],component=True,intermediate=True);code=0
        elif name=='check-sen':code=check()
        elif name=='summary-sen':code=summary()
        elif name=='zapis-strumieni-sen':storage.prepare_publication(OUT);code=0
        else:raise ValueError(name)
    except Exception as exc:error=str(exc);traceback.print_exc()
    finally:
        (OUT/(name+'-kod.csv')).write_text(str(code)+'\n',encoding='ascii')
        save(name+'-etap.json',{'code':code,'seconds':time.monotonic()-start,'error':error})
    return code
