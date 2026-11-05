pass                                                                              
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import subprocess

STAGES=('budowa-zywy','proba-zywy','porownanie-zywy-12a','porownanie-zywy','component-zywy','swiadki-zywy-2a','check-zywy','summary-zywy')

def init(context):
    global C,OUT,g,storage,builder
    C=context
    OUT=C.OUT if C.OUT.name=='krok12' else C.OUT.parent/'krok12' if C.OUT.name in ('krok10','krok11') else C.OUT/'krok12'
    OUT.mkdir(parents=True,exist_ok=True);sys.argv[1]='zywy12'
    g=C.world_module('przypadki-zywy.py','zywy_ci_inputs')
    storage=C.world_module('zapis-zywy.py','zywy_ci_storage')
    builder=C.world_module('budowa-zywy.py','zywy_ci_build')

def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def compile_c():
    source=Path(os.environ.get('ZY12_BOX2D_SOURCE',C.base.TEMP/'box2d'))
    if not (source/'src/world.c').is_file():raise ValueError('Pinned original C missing; no download in step12')
    return builder.build(source,C.base.TEMP/'zywy12-build',OUT)

def compile_duck(component=False,guard=False):
    name='duckling-zywy-component' if component else 'duckling-zywy-guard' if guard else 'duckling-zywy'
    target=OUT/(name+'-bin');target.unlink(missing_ok=True)
    driver=C.PORT/'zywy-swiata.dk'
    if not driver.is_file():raise ValueError('Driver zywy-swiata.dk is missing')
    before=hashlib.sha256(driver.read_bytes()).hexdigest()
    artifacts=C.base.TEMP/(name+'-build');(artifacts/'proba').unlink(missing_ok=True)
    entry=driver
    if component or guard:
        entry=C.base.TEMP/('zywy-component-driver.dk' if component else 'zywy-guard-driver.dk')
        entry.write_text(builder.once(driver.read_text(encoding='utf-8-sig'),
            'const CONTACT_PROFILE: i32 = 8i32;',f'const CONTACT_PROFILE: i32 = {(10 if component else 9)}i32;'),encoding='utf-8',newline='\n')
    try:
        binary=C.compile_world_fixture(C.world_duckc(),name,entry,C.ROOT/'silnik/fizyka')
        if binary.resolve()!=target.resolve():shutil.copy2(binary,target)
        if hashlib.sha256(driver.read_bytes()).hexdigest()!=before:raise ValueError('Product transport changed during compile')
        save(name+'-sha256.json',{'source':before,'binary':hashlib.sha256(target.read_bytes()).hexdigest()})
    finally:
        if component or guard:entry.unlink(missing_ok=True)

def component_math():
    work=OUT/'component';work.mkdir(exist_ok=True);path=work/'input-c.csv'
    path.write_text(g.encode_math(),encoding='ascii',newline='\n')
    result={'N_math':len(g.math_components()),'programs':{},'errors':[],'full_component_acceptance':False}
    streams={}
    try:
        for label,argv,stdin in (('obs1',[OUT/'c12-obs1-bin',path],None),('obs0',[OUT/'c12-obs0-bin',path],None),
                                 ('duckling',[OUT/'duckling-zywy-component-bin'],g.encode_math(True).encode())):
            start=time.monotonic();r=subprocess.run(argv,input=stdin,capture_output=True,timeout=30);streams[label]=r.stdout
            result['programs'][label]={'code':r.returncode,'stderr_bytes':len(r.stderr),'stderr_window':r.stderr[:4096].decode(errors='replace'),'seconds':time.monotonic()-start,'bytes':len(r.stdout)}
            if r.returncode or r.stderr:result['errors'].append(label+' code/stderr')
        result['all_words_equal']=streams['obs1']==streams['obs0']==streams['duckling']
        if not result['all_words_equal']:
            result['errors'].append('math C0/C1/D bytes differ')
            from itertools import zip_longest
            for i,rows in enumerate(zip_longest(*(v.decode('ascii').splitlines() for v in streams.values())),1):
                if len(set(rows))>1:result['first_difference']={'line':i,'records':dict(zip(streams,rows))};break
        grammar=C.world_module('model-zywy.py','zywy_component_grammar')
        for label,data in streams.items():
            records=[grammar.parse(line) for line in data.decode('ascii').splitlines(keepends=True)]
            expected=[];require=storage.p.require
            require(records.pop(0)==('COMPONENT12',(len(g.math_components()),)),'component header')
            for id,row in enumerate(g.math_components(),1):
                require(records.pop(0)==('CASE',(id,1)),'math CASE')
                require(records.pop(0)==('FE12',(id,*row)),'math full64-word echo')
                tag,value=records.pop(0);require(tag=='FV12' and value[:2]==(id,row[0]),'math result identity')
                require(records.pop(0)==('ENDCASE',(id,)),'math ENDCASE')
            require(records==[('END',(len(g.math_components()),))],'math END/EOF')
            result['programs'][label]['sha256']=hashlib.sha256(data).hexdigest()
        result['independent_grammar']=True
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    finally:path.unlink(missing_ok=True)
    result['math_code']=int(bool(result['errors']))
    result['errors'].append('This diagnostic covers only21 math fixtures; full COMPONENT12 acceptance uses compare(32,component=True)')
    save('component-zywy.json',result);return result

def models():
    path=C.PORT/'model-zywy.py'
    if not path.is_file():return None,['Independent model model-zywy.py is missing']
    module=C.world_module(path.name,'zywy_ci_model')
    if not hasattr(module,'OwnershipModel'):return None,['OwnershipModel interface missing']
    return {side:module.OwnershipModel() for side in ('obs1','obs0','duckling')},[]

def compare(n,name,component=False):
    cases=g.component_cases() if component else g.verify(n);model,errors=models();work=OUT/name;work.mkdir(exist_ok=True)
    inputs={}
    for label,decimal in (('C',False),('D',True)):
        path=work/('input-'+label+'.csv');path.write_text(g.encode_components(cases,decimal) if component else g.encode(cases,decimal),encoding='ascii',newline='\n');inputs[label]=path
    save(name+'-wejscia.json',{label:hashlib.sha256(path.read_bytes()).hexdigest() for label,path in inputs.items()})
    commands={'obs1':[OUT/'c12-obs1-bin',inputs['C']],'obs0':[OUT/'c12-obs0-bin',inputs['C']],
              'duckling':[OUT/('duckling-zywy-component-bin' if component else 'duckling-zywy-bin')]}
    for label,command in commands.items():
        if not Path(command[0]).is_file():errors.append(label+' fresh binary missing')
    if any(not Path(command[0]).is_file() for command in commands.values()):
        result={'N':n,'errors':errors,'full_acceptance':False,'completed_cases':0}
    else:
        result=storage.run(commands,cases,work,models=model,stdin_paths={'duckling':inputs['D']},component=component)
        result['errors']+=errors
        if errors:result['full_acceptance']=False
    result['part']='COMPONENT12' if component else '12a' if n==72 else 'sample' if n<72 else '12c'
    save(name+'-zywy.json',result)
                                                                             
    for path in inputs.values():path.unlink(missing_ok=True)
    return result

def forecast(sample):
    elapsed=sample.get('seconds');measured=sample.get('streams',{}).get('obs1',{}).get('bytes')
    observed=sample.get('completed_snapshots',0)
                                                                                  
    result={'source':'all160 complete input recipes and frozen manifest; measured cost remains separate',
            'all_manifest_q_bytes_per_program':g.MANIFEST['sufityWyjsciaBajty']['razemNaProgram'],
            'implemented_ids':g.AVAILABLE_N,'not_implemented_ids':list(range(g.AVAILABLE_N+1,161)),
            'recipe_operations':sum(len(c.ops) for c in g.verify(g.AVAILABLE_N)),
            'measured_seconds':elapsed,'measured_C1_bytes':measured,'measured_snapshots':observed,
            'complete_cost_forecast':False,
            'missing':['C0/C1/D printing/model/compare cost split over representative hooks/overflow/grid and entire160 forecast']}
    if elapsed and observed:
        result['linear_implemented_seconds']=elapsed*sum(len(c.ops) for c in g.verify(g.AVAILABLE_N))/observed
    save('prognoza-zywy.json',result);return result

def check():
    errors=[];path=OUT/'public-zywy.json'
    if not path.is_file():errors.append('full160 receipt missing')
    else:
        result=json.loads(path.read_bytes())
        if result.get('N')!=160 or result.get('completed_cases')!=160 or not result.get('full_acceptance') or result.get('errors'):
            errors.append('full160 or models/projection/C=D incomplete')
    if g.AVAILABLE_N!=160:errors.append(f'only{g.AVAILABLE_N}/160 input recipes implemented')
    forecast_path=OUT/'prognoza-zywy.json'
    if not forecast_path.is_file() or not json.loads(forecast_path.read_bytes()).get('complete_cost_forecast'):
        errors.append('complete measured forecast missing')
    save('kompletnosc-zywy.json',{'errors':errors,'required_N':160,'required_positive_Step':64800})
    return errors

def summary():
    errors=check()
    for name in STAGES[:-1]:
        path=OUT/(name+'-kod.csv')
        if not path.is_file() or path.read_text().strip()!='0':errors.append(name+' missing/red')
    oslony=OUT/'OSLONY.md'
    if not oslony.is_file() or 'RESULT: OK' not in oslony.read_text(encoding='utf-8'):errors.append('Guard checks missing or failed')
    if os.environ.get('ZY12_OSLONY_OUTCOME')!='success':errors.append('Guard workflow step missing or failed')
    prior=OUT.parent/'krok11/wynik-kod.csv'
    if not prior.is_file() or prior.read_text().strip()!='0':errors.append('regressions1–11 missing/red')
    (OUT/'DZIENNIK.md').write_text('\n'.join(['# Krok12','',*['- '+e for e in errors],'',
        'RESULT: '+('FAIL / UNEXECUTED' if errors else 'OK'),'']),encoding='utf-8')
    (OUT/'wynik-kod.csv').write_text(str(int(bool(errors)))+'\n',encoding='ascii')
    save('podsumowanie-zywy.json',{'errors':errors,'code':int(bool(errors))});return int(bool(errors))

def stage(context,name):
    init(context);start=time.monotonic();code=1;error=None
    try:
        if name=='budowa-zywy':
            errors=[]
            for label,fn in (('C',compile_c),('Duckling',compile_duck),('Duckling COMPONENT',lambda:compile_duck(True)),('Duckling GUARD',lambda:compile_duck(guard=True))):
                try:fn()
                except Exception as exc:errors.append(label+': '+str(exc))
            save('budowy-zywy.json',{'errors':errors});code=int(bool(errors))
        elif name=='proba-zywy':
            result=compare(13,'proba');estimate=forecast(result)
            code=int(not result.get('full_acceptance') or not estimate['complete_cost_forecast'])
        elif name=='porownanie-zywy-12a':code=int(not compare(72,'public-12a').get('full_acceptance'))
        elif name=='porownanie-zywy':
            estimate=OUT/'prognoza-zywy.json'
            if not estimate.is_file() or not json.loads(estimate.read_bytes()).get('complete_cost_forecast'):
                raise ValueError('Full160 requires measured entire-manifest forecast; no shortened substitute')
            code=int(not compare(160,'public').get('full_acceptance'))
        elif name=='component-zywy':code=int(not compare(32,'component',True).get('full_acceptance'))
        elif name=='swiadki-zywy-2a':code=C.world_module('mutacje-zywy-2a.py','zywy_2a_native_witnesses').run(C,OUT)
        elif name=='check-zywy':code=int(bool(check()))
        elif name=='summary-zywy':code=summary()
        else:raise ValueError(name)
    except Exception as exc:error=str(exc);traceback.print_exc()
    finally:
        (OUT/(name+'-kod.csv')).write_text(str(code)+'\n',encoding='ascii')
        save(name+'-etap.json',{'code':code,'seconds':time.monotonic()-start,'error':error})
    return code
