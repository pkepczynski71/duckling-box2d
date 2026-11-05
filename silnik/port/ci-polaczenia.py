pass                                                                     

                                                                           
                                                                          
   
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import threading
import time
import tarfile
try:import resource
except ImportError:resource=None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OFFICIAL_SHA = 'f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519'
                                                                         
OFFICIAL_B_SHA = OFFICIAL_SHA


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def within(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()): raise ValueError('PORT14A output outside assigned tree')
    return path


def source_identity():
    files=[ROOT/'.github/workflows/port.yml',HERE/'ci.py',
           *(p for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.c','.h','.py','.dk','.json') and p.name!='polaczenia-N5-odbior.json'),
           *sorted((ROOT/'silnik/fizyka').glob('*.dk'))]
    return {p.relative_to(ROOT).as_posix():digest(p) for p in files if p.is_file()}


def bound_native(side,binary,builds,sources):
    if source_identity()!=sources:raise ValueError('native source identity changed since stage inventory')
    source_sha=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    receipt=builds.get('d' if side=='d' else 'c',{})
    if receipt.get('sourceSHA256')!=source_sha or receipt.get('code')!=0:
        raise ValueError('matching successful source-bound build required')
    expected=receipt.get('binarySHA256') if side=='d' else receipt['binaries']['obs0' if side=='c0' else 'obs1']['sha256']
    if not expected or digest(binary)!=expected:raise ValueError('native binary differs from build receipt')
    return expected,source_sha


def runtime_adapters(out, binaries, builds, sources, seconds):
    pass                                                                    

                                                                               
                                                                          
       
    out=within(out);out.mkdir(parents=True,exist_ok=True)
    model=load('polaczenia_runtime_model','model-polaczenia.py')
    negative=load('polaczenia_runtime_negative','polaczenia-ujemne.py')
    compare=load('polaczenia_runtime_compare','porownaj-polaczenia.py')
    save(out/'sources.json',sources);save(out/'builds.json',builds)
    deadlines={};transient=[];serial=0
    def cleanup():
        for path in transient:path.unlink(missing_ok=True)
        transient.clear()
    def execute(side,data,observer,key,bucket):
        nonlocal serial
        if sys.platform!='linux':raise ValueError('native runtime requires Linux')
        if side not in ('c0','c1','d') or observer!=(side!='c0'):raise ValueError('native side/observer mismatch')
        budget=seconds.get(bucket,0)
        deadline=deadlines.setdefault(bucket,time.monotonic()+budget)
        binary=Path(binaries[side])
        expected,bound_source=bound_native(side,binary,builds,sources)
        remaining=deadline-time.monotonic()
        if remaining<=0:raise ValueError('N5 native stage budget missing/exhausted: '+bucket)
        serial+=1;prefix=out/str(serial);stdout=prefix.with_suffix('.stdout');stderr=prefix.with_suffix('.stderr')
        transient.extend((stdout,stderr));started=time.monotonic();timeout=False
        with stdout.open('wb') as target,stderr.open('wb') as err:
            try:process=subprocess.run([str(binary)],input=data,stdout=target,stderr=err,timeout=remaining);code=process.returncode
            except subprocess.TimeoutExpired:code=None;timeout=True
        elapsed=time.monotonic()-started
        result={'build_code':0,'code':code,'stderr':stderr.read_bytes(),'stdout_path':stdout,
                'native_product':True,'source_sha256':bound_source,'source_manifest':str(out/'sources.json'),'timeout':timeout,
                'argv':[str(binary)],'binarySHA256':expected,'inputSHA256':hashlib.sha256(data).hexdigest(),
                'stdoutSHA256':digest(stdout),'stdoutBytes':stdout.stat().st_size,'seconds':elapsed,
                'source_key':key,'observer':observer,'build_receipts':str(out/'builds.json')}
        save(prefix.with_suffix('.json'),{**result,'stderr':result['stderr'].decode('ascii',errors='backslashreplace'),'stdout_path':str(stdout)})
        return result
    def run(side,input_bytes,observer,source_key):
        cleanup()
        return execute(side,input_bytes,observer,source_key,'GUARD')
    def run_parser(side,item,observer):
        cleanup()
        actual=execute(side,item['input'],observer,item['key'],'parsers')
        reference=execute(side,item['reference_input'],observer,item['key']+'/reference','parsers')
        if actual['timeout'] or reference['timeout'] or reference['code']!=0 or reference['stderr']:
            raise ValueError('fatal prefix reference native process failed')
        with actual['stdout_path'].open('rb') as bad,reference['stdout_path'].open('rb') as good:
            actual.update(negative.compare_prefix(bad,good,item))
        save(out/(str(serial)+'-prefix.json'),{k:actual[k] for k in actual if k.startswith('prefix_')})
        return actual
    def validate(side,path,input_bytes,observer,source_key):
                                                                            
                                                              
        started=time.monotonic();operations={};helpers={};ident=None
        for line in input_bytes.splitlines():
            words=line.split()
            if words and words[0] in (b'C',b'G14'):ident=int(words[1])
            if words and words[0]==b'G14' and int(words[2]):
                count=int(words[4]);helpers[ident,count+1 if count else 0]=int(words[2])
            if words and words[0]==b'O':
                seq,code=map(int,words[1:3]);offset=4 if code>=200 else 3
                operations[ident,seq]={'opcode':code,'a':tuple(int(w,10 if side=='d' else 16) for w in words[offset:])}
        checker=model.Model14A(observer=observer);records=[];unresolved=[];checked=0;base_ok=True;joint_ok=True;seen=set()
        def check():
            nonlocal checked,base_ok,joint_ok
            if not records:return
            case,seq=records[0][1][:2];operation=operations.get((case,seq))
            if (case,seq) in seen:base_ok=False;unresolved.append('duplicate snapshot');return
            seen.add((case,seq))
            helper=helpers.get((case,seq))
            if operation is None and helper is None:unresolved.append('snapshot without matching input operation/helper');return
            try:
                base=model.check_base13_counts(records,case,seq,observer=observer,
                    positive=(checker.positive if checker.case==case else 0)+int(operation is not None and operation['opcode'] in (31,32) and model.number(operation['a'][1])>0 and next(v[2] for t,v in records if t=='A14')==0),ordinal=seq)
                if not base.get('complete'):unresolved.append('BASE13 model reports incomplete ownership')
            except (ValueError,AssertionError) as exc:base_ok=False;unresolved.append('BASE13: '+str(exc))
            try:
                if operation is None:
                    compare.snapshot_check(records, compare.generator.Case(case,source_key,'GUARD','helper',()), seq, None, observer, helper_kind=helper)
                    unresolved.append('full GUARD helper/history model remains open')
                    checked+=1
                    return
                value=checker.check(case,seq,operation,records,observer)
                joint_ok=joint_ok and value.get('joint_structure_checked') is True
                if not value.get('complete'):unresolved.append('model reports incomplete BASE13/history')
            except (ValueError,AssertionError) as exc:joint_ok=False;unresolved.append('joint model: '+str(exc))
            checked+=1
        try:
            with within(path).open('rb') as stream:
                for raw in stream:
                    tag,values=model.parse(raw)
                    if tag in ('PORT14','G14','GA14','CASE','ENDCASE','END','EF14'):
                        check();records=[]
                        continue
                    records.append((tag,values))
                    if tag=='Z13':check();records=[]
                check()
        except (ValueError,AssertionError) as exc:base_ok=False;unresolved.append('grammar: '+str(exc))
        if checked!=len(operations)+len(helpers) or seen!=operations.keys() | helpers.keys():unresolved.append('not all input operations validated')
        if not checker.full_model_ready:unresolved.append('full_model_ready=False')
        if not checker.full_ownership_ready:unresolved.append('full_ownership_ready=False')
        return {'complete':not unresolved and checked>0,'base_grammar':base_ok and checked>0,
                'base_model':False,'joint_model':joint_ok and checked>0,
                'full_model_ready':checker.full_model_ready,'full_ownership_ready':checker.full_ownership_ready,
                'unresolved':unresolved,'snapshots':checked,'source_key':source_key,'seconds':time.monotonic()-started}
    return {'POLACZENIA_RUN':run,'POLACZENIA_RUN_PARSER':run_parser,'POLACZENIA_VALIDATE':validate,
            'POLACZENIA_RUNTIME_CLEANUP':cleanup}


def native_compare(out, cases, binaries, *, seconds, builds=None, sources=None):
    pass                                                                      
    if sys.platform != 'linux': raise ValueError('native comparison requires Linux')
    if not builds or not sources:raise ValueError('source-bound native build receipts required')
    if set(binaries)!={'c0','c1','d'}:raise ValueError('native C0/C1/D required')
    identities={side:bound_native(side,binary,builds,sources) for side,binary in binaries.items()}
    out=within(out);out.mkdir(parents=True,exist_ok=True)
    compare=load('polaczenia_ci_compare','porownaj-polaczenia.py')
    inputs=compare.generator; processes={}; receipts={}; timed_out=threading.Event()
    started=time.monotonic();result={'full_acceptance':False}
    def expire():
        timed_out.set()
        for process in list(processes.values()):
            if process.poll() is None: process.kill()
    timer=threading.Timer(seconds,expire)
    try:
        with ExitStack() as stack:
            streams={}
            for side,binary in binaries.items():
                if side not in ('c0','c1','d'):raise ValueError('unknown native side')
                binary_sha,source_sha=identities[side]
                path=out/(side+'.input')
                with path.open('w',encoding='ascii',newline='\n') as stream:stream.writelines(inputs.text(cases,side=='d'))
                inp=stack.enter_context(path.open('rb'));err=stack.enter_context((out/(side+'.stderr')).open('wb'))
                process=subprocess.Popen([str(binary)],stdin=inp,stdout=subprocess.PIPE,stderr=err)
                processes[side]=process;streams[side]=process.stdout
                receipts[side]={'argv':[str(binary)],'binarySHA256':binary_sha,'inputSHA256':digest(path),'sourceSHA256':source_sha}
            timer.start()
            errors=stack.enter_context((out/'errors.jsonl').open('w',encoding='utf-8'))
            factory=None
            model_path=HERE/'model-polaczenia.py'
            if model_path.is_file():factory=load('polaczenia_ci_joint_model','model-polaczenia.py').Model14A
            try:result=compare.compare_streams(streams,cases,checker_factory=factory,error_sink=errors)
            except Exception as exc:result={'full_acceptance':False,'error':type(exc).__name__+': '+str(exc)}
            finally:
                for process in processes.values():
                    if process.stdout:process.stdout.close()
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
    finally:
        timer.cancel()
        for process in processes.values():
            if process.poll() is None:process.kill();process.wait()
            if process.stdout:process.stdout.close()
        for side,process in processes.items():
            receipts[side].update(code=process.returncode,stderrBytes=(out/(side+'.stderr')).stat().st_size)
        result.update(native=receipts,timeout=timed_out.is_set(),seconds=time.monotonic()-started,
                      peakChildRssKiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource else None,
                      fullStdoutStored=False)
        runtime_ok=not timed_out.is_set() and all(v['code']==0 and v['stderrBytes']==0 for v in receipts.values())
        result['native_runtime_ok']=runtime_ok
        result['full_acceptance']=bool(result.get('full_acceptance') and runtime_ok)
        save(out/'comparison.json',result)
    return result


def approved_limits(path, source_sha):
    if path is None:raise ValueError('N5 limits record not approved: explicit numeric limits required')
    receipt=json.loads(Path(path).read_text(encoding='utf-8'))
    required=('PUBLIC','DIRECT','GUARD','parsers','mutations','builds')
    if receipt.get('limits_profile') != 'LIMITS1' or receipt.get('sourceSHA256') != source_sha:
        raise ValueError('N5 profile/source identity missing')
    if not all(type(receipt.get('seconds',{}).get(k)) in (float,int) and receipt['seconds'][k]>0 for k in required):
        raise ValueError('N5 incomplete stage budgets')
    if receipt.get('pilot_complete') is not True or receipt.get('twofold_extrapolation_fits') is not True:
        raise ValueError('N5 complete observer pilot/2x forecast not accepted')
    return receipt


def compile_duckling(duckc, archive, out, *, seconds, workers=None):
    pass                                                                          
    if workers is not None and (type(workers) is not int or not 1 <= workers <= 8):
        raise ValueError('explicit compiler workers must be 1..8')
    out=within(out);out.mkdir(parents=True,exist_ok=True);duckc=Path(duckc);archive=Path(archive)
    driver=HERE/'polaczenia.dk'
    if not driver.is_file():raise FileNotFoundError('Product entry point polaczenia.dk is missing')
    if not duckc.is_file() or not archive.is_file():raise FileNotFoundError('explicit existing compiler and official archive required')
    if digest(archive)!=OFFICIAL_SHA:raise ValueError('official compiler archive SHA mismatch')
    with tarfile.open(archive,'r:gz') as tar:
        members=[m for m in tar.getmembers() if m.isfile() and Path(m.name).name=='duckc']
        if len(members)!=1:raise ValueError('one archived duckc required')
        with tar.extractfile(members[0]) as stream:expected=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest(duckc)!=expected:raise ValueError('existing duckc differs from pinned archive member')
    artifacts=out/'artifacts';artifacts.mkdir(exist_ok=True)
    binary=artifacts/'polaczenia-bin';library=artifacts/'libfizyka.a'
    binary.unlink(missing_ok=True);library.unlink(missing_ok=True)
    package={'packages':[{'id':'fizyka','name':'fizyka','path':str(ROOT/'silnik/fizyka')},
                         {'id':'polaczenia','name':'polaczenia','path':str(driver),'dependencies':[{'id':'fizyka'}]}],
             'tasks':[{'package':'fizyka','strategy':'lib','output_file':'libfizyka.a'},
                      {'package':'polaczenia','strategy':'native','output_file':binary.name,
                       'linking_options':{'additional_link_options':[str(library),'-lm'],'link_c_standard_library':True}}]}
    sources=source_identity()
    save(out/'packages.json',package);argv=[str(duckc),'compile_packages',str(out/'packages.json'),'-a',str(artifacts),'-O','0']
    if workers is not None:argv += ['-w',str(workers)]
    start=time.monotonic();stamp=time.time_ns()
    with (out/'build.stdout').open('wb') as stdout,(out/'build.stderr').open('wb') as stderr:
        run=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=seconds)
    fresh=all(p.is_file() and p.stat().st_mtime_ns>=stamp for p in (binary,library))
    elf=False
    if binary.is_file():
        with binary.open('rb') as stream:elf=stream.read(4)==b'\x7fELF'
    receipt={'code':run.returncode,'argv':argv,'workers':workers,'seconds':time.monotonic()-start,'fresh':fresh,'ELF':elf,
             'archiveSHA256':OFFICIAL_SHA,'compilerSHA256':expected,'binary':str(binary),
             'binarySHA256':digest(binary) if binary.is_file() else None,'driverSHA256':digest(driver),
             'sources':sources,'sourceSHA256':hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest(),
             'sources_unchanged':sources==source_identity()}
    save(out/'build.json',receipt)
    if run.returncode or not fresh or not elf or not receipt['sources_unchanged']:raise ValueError('native D build failed/stale/non-ELF/changed sources; see build.json')
    return receipt


def selftest(out):
    results=[]
    for pattern in ('test_polaczenia_wejscia.py','test_polaczenia_porownanie.py','test_polaczenia_ci.py'):
        argv=[sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p',pattern,'-v']
        start=time.monotonic()
        with (out/(pattern+'.stdout')).open('wb') as stdout,(out/(pattern+'.stderr')).open('wb') as stderr:
            run=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=180)
        log=(out/(pattern+'.stderr')).read_text(encoding='utf-8',errors='replace')
        count=re.search(r'Ran ([0-9]+) tests?',log)
        tests=int(count[1]) if count else 0
        bad=run.returncode!=0 or tests==0 or 'skipped=' in log or 'expected failures=' in log
        results.append(dict(file=pattern,code=int(bad),processCode=run.returncode,tests=tests,seconds=time.monotonic()-start))
    if any(x['code'] for x in results):raise ValueError('14a tool selftest failed: '+repr(results))
    return results


PHASES=('sources','tools','N5','build_C0_C1','build_D','PUBLIC','DIRECT','guards_parsers_mutations_OBS','summary')


def stage(ctx=None, *, out=None, phase='all', part=None, profile=None):
    if phase not in ('all',*PHASES):raise ValueError('unknown PORT14A phase: '+phase)
    part=part or os.environ.get('POLACZENIA_PART','A');profile=profile or os.environ.get('POLACZENIA_PROFILE','ALL')
    if part!='A' or profile not in ('ALL','PUBLIC','DIRECT','GUARD','PARSER','MUTATIONS'):raise ValueError('PORT14A explicit part/profile invalid')
    run=os.environ.get('GITHUB_RUN_ID','local');attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1')
    out=within(out or os.environ.get('POLACZENIA_RESULT_DIR',ROOT/'RESULT-PORT14'/f'{run}_{attempt}'/'14a'))
    out.mkdir(parents=True,exist_ok=True)
    (out/'errors.jsonl').touch(exist_ok=True)
    result={'part':'14a','code':1,'full_acceptance':False,'stages':{},'startUnix':time.time(),
            'sourceCommit':os.environ.get('GITHUB_SHA'),'run':run,'attempt':attempt,
            'regression1_13':'required on identical product code',
            'openRequirements':['complete BASE13 model ownership','Matching product, comparison and guard sources required',
                'N5 pilot and explicit resource limits','native mutations/guards/parsers',
                'Final source-bound mutation anchors required','Regression checks1-13','independent native verification']}
    if phase not in ('all','sources') and (out/'manifest.json').is_file():
        result=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    result['selection']={'phase':phase,'part':part,'profile':profile}
    binaries={};limits={}
    previous_c=result['stages'].get('build_C0_C1',{}).get('result',{})
    for label,key in (('c0','obs0'),('c1','obs1')):
        if key in previous_c.get('binaries',{}):binaries[label]=previous_c['binaries'][key]['binary']
    previous_d=result['stages'].get('build_D',{}).get('result',{})
    if previous_d.get('binary'):binaries['d']=previous_d['binary']
    limits.update(result['stages'].get('N5',{}).get('result',{}))
    def perform(name,fn,depends=()):
        if phase not in ('all',name):return
        if phase=='all' and profile!='ALL':
            if name in ('PUBLIC','DIRECT') and name!=profile:return
            if name=='guards_parsers_mutations_OBS' and profile in ('PUBLIC','DIRECT'):return
        failed=[d for d in depends if result['stages'].get(d,{}).get('code')!=0]
        start=time.monotonic()
        if failed:row={'code':1,'state':'unexecuted','reason':'dependency red: '+','.join(failed)}
        else:
            try:
                value=fn();row={'code':0,'state':'executed','result':value}
                if isinstance(value,dict) and (value.get('code',0) or value.get('full_acceptance') is False):row['code']=1
            except Exception as exc:row={'code':1,'state':'failed','reason':type(exc).__name__+': '+str(exc)}
        row['seconds']=time.monotonic()-start;result['stages'][name]=row;save(out/'manifest.json',result)
    def sources():
        hashes=source_identity()
        result['sources']=hashes;result['sourceSHA256']=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
        return hashes
    def gate():
        limits.update(approved_limits(os.environ.get('POLACZENIA_N5_RECEIPT'),result['sourceSHA256']));return limits
    def build_c():
        source=os.environ.get('BOX2D_SOURCE')
        if not source:raise ValueError('explicit existing BOX2D_SOURCE required; downloads forbidden')
        receipt=load('polaczenia_ci_build','budowa-polaczenia.py').build(source,out/'build-c',out/'c')
        if source_identity()!=result['sources']:raise ValueError('C build source identity changed')
        receipt.update(sourceSHA256=result['sourceSHA256'],sources=result['sources'])
        save(out/'c'/'budowa-polaczenia.json',receipt)
        binaries.update(c0=receipt['binaries']['obs0']['binary'],c1=receipt['binaries']['obs1']['binary']);return receipt
    perform('sources',sources)
    perform('tools',lambda:selftest(out))
    perform('N5',gate,('sources',))
    perform('build_C0_C1',build_c,('N5',))
                                                                               
                                                                                
    def build_d():
        receipt=compile_duckling(os.environ.get('DUCKLING_COMPILER',''),os.environ.get('DUCKLING_ARCHIVE',''),
                                out/'native-duckling14',seconds=limits['seconds']['builds'])
        binaries['d']=receipt['binary'];return receipt
    perform('build_D',build_d,('N5',))
    inputs=load('polaczenia_ci_inputs','przypadki-polaczenia.py')
    for case_profile in ('PUBLIC','DIRECT'):
        perform(case_profile,lambda case_profile=case_profile:native_compare(out/case_profile,inputs.cases(case_profile),binaries,seconds=limits['seconds'][case_profile],
            builds={'c':result['stages']['build_C0_C1']['result'],'d':result['stages']['build_D']['result']},sources=result.get('sources',{})),('build_C0_C1','build_D'))
    def second_half():
        module=load('polaczenia_ci_second_half','ci-polaczenia-oslony.py')
        adapters=runtime_adapters(out/'runtime',binaries,
                    {'c':result['stages'].get('build_C0_C1',{}).get('result',{}),
                     'd':result['stages'].get('build_D',{}).get('result',{})},result.get('sources',{}),limits.get('seconds',{}))
        try:
            code=module.stage({**adapters,'POLACZENIA_OUT':out/'oslony',
                    'POLACZENIA_PUBLIC96':{'ok':result['stages'].get('PUBLIC',{}).get('code')==0},
                    'POLACZENIA_DIRECT128':{'ok':result['stages'].get('DIRECT',{}).get('code')==0},
                    'POLACZENIA_final_clean_integration':{'ok':False}},part=part,
                    profile=profile if profile in ('GUARD','PARSER','MUTATIONS') else 'ALL',out=out/'oslony')
        finally:adapters['POLACZENIA_RUNTIME_CLEANUP']()
        return {'code':code,'runtime_adapter_received':True,'full_acceptance':False}
                                                                             
    perform('guards_parsers_mutations_OBS',second_half)
    missing=[p for p in PHASES[:-1] if p not in result['stages']]
    result['missingStages']=missing
    result['code']=int(any(s['code'] for s in result['stages'].values()) or bool(result['openRequirements']) or bool(missing))
    result['seconds']=time.time()-result['startUnix'];save(out/'manifest.json',result)
    lines=['# PORT14A — '+('FAIL' if result['code'] else 'OK'),'','| Etap | Kod | Stan / powód |','|---|---:|---|']
    lines += [f'| {name} | {s['code']} | {s.get('state', 'receipt')}: {s.get('reason', '')} |' for name,s in result['stages'].items()]
    lines+=['','Otwarte wymagania:']+['- '+v for v in result['openRequirements']]
    (out/'PODSUMOWANIE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result['code'] if phase in ('all','summary') else result['stages'][phase]['code']


if __name__=='__main__':
    if '--mode' in sys.argv:
        sys.exit(load('polaczenia_full14b','ci-polaczenia-14b.py').main())
    sys.exit(stage())
