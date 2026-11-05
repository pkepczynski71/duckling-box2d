from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                       

                                                                           
                                                                            
   
from contextlib import ExitStack
from dataclasses import replace
import argparse,gzip,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
try:import resource
except ImportError:resource=None
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def location():return ROOT/'RESULT-PORT13'/(os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1'))

def compile_duckling(duckc,work,out,*,part='13a'):
    if part not in ('13a','13b','13c'):raise ValueError('unknown native build profile')
    driver=HERE/('lancuchy13c.dk' if part=='13c' else 'lancuchy.dk');require=driver.is_file()
    if not require:raise FileNotFoundError('K13a driver missing')
    if not Path(duckc).is_file():raise FileNotFoundError('explicit existing official duckc required')
    build=Path(work)/('native-duckling13c' if part=='13c' else 'native-duckling');build.mkdir(parents=True,exist_ok=True)
    binary=build/'duckling-lancuchy-bin';binary.unlink(missing_ok=True)
    manifest={'packages':[{'id':'fizyka','name':'fizyka','path':str(ROOT/'silnik/fizyka')},
                         {'id':'port13a','name':'port13a','path':str(driver),'dependencies':[{'id':'fizyka'}]}],
              'tasks':[{'package':'fizyka','strategy':'lib','output_file':'libfizyka.a'},
                       {'package':'port13a','strategy':'native','output_file':binary.name,'linking_options':{'additional_link_options':[str(build/'libfizyka.a'),'-lm'],'link_c_standard_library':True}}]}
    if part=='13a':
                                                                               
        adapter=Path(work)/'source13a/lancuchy.dk';adapter.parent.mkdir(parents=True,exist_ok=True)
        original=driver.read_text(encoding='utf-8')
        old_entry='fun main() -> i64 = { return transportMain13(); }'
        new_entry='fun main() -> i64 = { return main13A(); }'
        if original.count(old_entry)!=1:raise ValueError('13a requires one legacy entry forwarding to transportMain13')
        adapter.write_text(original.replace(old_entry,new_entry,1),encoding='utf-8',newline='\n')
        manifest['packages'][-1]['path']=str(adapter)
    if part=='13c':
                                                                            
                                                                          
        adapter=Path(work)/'source13c/lancuchy.dk';adapter.parent.mkdir(parents=True,exist_ok=True)
        original=(HERE/'lancuchy.dk').read_text(encoding='utf-8')
        old_entry='fun main() -> i64 = { return transportMain13(); }'
        new_entry='fun legacyEntry13() -> i64 = { return transportMain13(); }'
        if original.count(old_entry)!=1:raise ValueError('D4 requires one committed legacy entry forwarding to transportMain13')
        adapter.write_text(original.replace(old_entry,new_entry,1),encoding='utf-8',newline='\n')
        manifest['packages'].insert(1,{'id':'lancuchy_adapter','name':'lancuchy_adapter','path':str(adapter),'dependencies':[{'id':'fizyka'}]})
        manifest['packages'][-1]['dependencies'].append({'id':'lancuchy_adapter'})
        manifest['tasks'].insert(1,{'package':'lancuchy_adapter','strategy':'lib','output_file':'liblancuchy_adapter.a'})
        manifest['tasks'][-1]['linking_options']['additional_link_options']=[str(build/'liblancuchy_adapter.a'),str(build/'libfizyka.a'),'-lm']
    path=build/'packages.json';save(path,manifest)
    argv=[str(duckc),'compile_packages',str(path),'-a',str(build),'-O','0'];start=time.monotonic()
    r=subprocess.run(argv,capture_output=True,text=True)
    (out/'duckling-build-stdout.csv').write_text(r.stdout[-16384:],encoding='utf-8');(out/'duckling-build-stderr.csv').write_text(r.stderr[-16384:],encoding='utf-8')
    elf=binary.is_file() and binary.read_bytes()[:4]==b'\x7fELF'
    result={'argv':argv,'code':r.returncode,'ELF':elf,'seconds':time.monotonic()-start,'binary':str(binary),
            'sha256':digest(binary) if elf else None,'compiler_sha256':digest(duckc),
            'profile':part,'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in [driver,*([HERE/'lancuchy.dk'] if part=='13c' else []),*sorted((ROOT/'silnik/fizyka').glob('*.dk'))]}}
    if part in ('13a','13c'):result['source_derivation']={'source':'silnik/port/lancuchy.dk','derived':str(adapter),'old':old_entry,'new':new_entry,'replacements':1,'sha256':digest(adapter),'transport_body_unchanged':adapter.read_text(encoding='utf-8').replace(new_entry,old_entry,1)==original}
    save(out/'duckling-build.json',result)
    if r.returncode or not elf:raise RuntimeError('native Duckling build failed; see duckling-build.json/logs')
    return result

def native_compare(out,work,items,binaries,*,sample=False,seconds=180):
    cmp=load('lancuchy_ci_compare','porownaj-lancuchy.py');g=cmp.g
    inputs=work/('sample-inputs' if sample else 'full-inputs');inputs.mkdir(parents=True,exist_ok=True)
    if sample:items=tuple(replace(c,ops=c.ops[:2 if 85<=c.id<=92 else 1]) for c in items)
    input_info={};processes={};codes={};stderr_bytes={};start=time.monotonic();finished=False
    result={'errors':[],'models_checked':False,'comparison_ok':False,'full_acceptance':False}
    model=None;model_missing=None
    try:model=cmp.independent_model_checker()
    except (FileNotFoundError,ImportError,AttributeError) as exc:model_missing=str(exc)
    try:
        with ExitStack() as stack:
            for name,profile,decimal,binary in (('c_r','R',False,binaries['R']),('d_r','R',True,binaries['duckling']),('c_d','D',False,binaries['D']),('d_d','D',True,binaries['duckling'])):
                path=inputs/(name+'.csv')
                with path.open('w',encoding='ascii',newline='\n') as f:f.writelines(g.text(items,profile,decimal))
                input_info[name]={'sha256':digest(path),'bytes':path.stat().st_size}
                stderr=stack.enter_context((out/(( 'sample' if sample else 'full')+'-'+name+'-stderr.csv')).open('wb'))
                processes[name]=subprocess.Popen(['timeout','--kill-after=5s',str(seconds)+'s',str(binary)],stdin=stack.enter_context(path.open('rb')),stdout=subprocess.PIPE,stderr=stderr)
            result=cmp.compare_streams({name:p.stdout for name,p in processes.items()},items,model_check=model,diagnostic=model is None)
            finished=result.get('global_END_checked',False)
    except Exception as exc:result['errors'].append(str(exc))
    finally:
        for name,p in processes.items():
            if not finished and p.poll() is None:p.terminate()
        for name,p in processes.items():
            try:codes[name]=p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();codes[name]=p.wait(timeout=10)
            if p.stdout:p.stdout.close()
            path=out/(('sample' if sample else 'full')+'-'+name+'-stderr.csv');stderr_bytes[name]=path.stat().st_size
                                                                                 
        if inputs.resolve().parent!=work.resolve():raise ValueError('input cleanup path')
        shutil.rmtree(inputs)
    result.update(process_codes=codes,stderr_bytes=stderr_bytes,inputs=input_info,sample_only=sample,
                  native_wall_with_pipe_backpressure=time.monotonic()-start,maxrss_children_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource else None)
    if any(codes.values()):result['errors'].append('native exit codes '+repr(codes))
    if any(stderr_bytes.values()):result['errors'].append('native stderr '+repr(stderr_bytes))
    if model_missing:result['errors'].append('independent model missing: '+model_missing)
    result['comparison_ok']=not result['errors'] and result.get('comparison_ok',False)
    save(out/('sample.json' if sample else 'full.json'),result)
    return result

def native_compare13b(out,work,items,binaries,*,sample=False,seconds=180,diagnostic=False):
    cmp=load('lancuchy_ci_compare13b','porownaj-lancuchy.py');inputs=Path(work)/('sample13b-inputs' if sample else 'full13b-inputs')
    inputs.mkdir(parents=True,exist_ok=True);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    processes={};codes={};input_info={};stderr_bytes={};start=time.monotonic();finished=False
    result={'errors':[],'comparison_ok':False,'global_END_checked':False,'full_acceptance':False}
    try:
        with ExitStack() as stack:
            for name,decimal,key in (('c0',False,'obs0'),('c1',False,'obs1'),('d',True,'duckling')):
                path=inputs/(name+'.csv')
                with path.open('w',encoding='ascii',newline='\n') as stream:stream.writelines(cmp.g.text13b(items,decimal))
                input_info[name]={'sha256':digest(path),'bytes':path.stat().st_size}
                error_path=out/(('sample' if sample else 'full')+'-'+name+'-stderr.csv')
                stderr=stack.enter_context(error_path.open('wb'))
                processes[name]=subprocess.Popen(['timeout','--kill-after=5s',str(seconds)+'s',str(binaries[key])],
                    stdin=stack.enter_context(path.open('rb')),stdout=subprocess.PIPE,stderr=stderr)
            result=cmp.compare13b_streams({name:p.stdout for name,p in processes.items()},items,require_history=not diagnostic,diagnostic=diagnostic)
            finished=result.get('global_END_checked',False)
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        for p in processes.values():
            if not finished and p.poll() is None:p.terminate()
        for name,p in processes.items():
            try:codes[name]=p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();codes[name]=p.wait(timeout=10)
            if p.stdout:p.stdout.close()
            error_path=out/(('sample' if sample else 'full')+'-'+name+'-stderr.csv');stderr_bytes[name]=error_path.stat().st_size
        if inputs.resolve().parent!=Path(work).resolve():raise ValueError('13b input cleanup path')
        shutil.rmtree(inputs)
    if any(codes.values()):result['errors'].append({'process_codes':codes})
    if any(stderr_bytes.values()):result['errors'].append({'stderr_bytes':stderr_bytes})
    result.update(process_codes=codes,stderr_bytes=stderr_bytes,inputs=input_info,sample_only=sample,
                  native_wall_with_pipe_backpressure=time.monotonic()-start,
                  maxrss_children_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource else None)
    result['comparison_ok']=result.get('comparison_ok',False) and not result['errors']
    save(out/('sample.json' if sample else 'full.json'),result);return result

def native_projection13b(out,work,items,binaries,seconds=180):
    cmp=load('lancuchy_ci_projection13b','porownaj-lancuchy.py');path=Path(work)/'C-only13b-input.csv'
    with path.open('w',encoding='ascii',newline='\n') as f:f.writelines(cmp.g.text13b(items))
    processes={};result={'errors':[],'comparison_ok':False,'scope':'C-only','Duckling_checked':False};started=time.monotonic()
    try:
        with ExitStack() as stack:
            for name in ('obs0','obs1'):
                processes[name]=subprocess.Popen(['timeout','--kill-after=5s',str(seconds)+'s',str(binaries[name])],
                    stdin=stack.enter_context(path.open('rb')),stdout=subprocess.PIPE,
                    stderr=stack.enter_context((out/('C-only-'+name+'-stderr.csv')).open('wb')))
            result=cmp.c_projection13b(processes['obs0'].stdout,processes['obs1'].stdout,items)
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        codes={}
        for name,p in processes.items():
            if not result.get('comparison_ok') and p.poll() is None:p.terminate()
            try:codes[name]=p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();codes[name]=p.wait(timeout=10)
            if p.stdout:p.stdout.close()
        path.unlink(missing_ok=True)
    result['process_codes']=codes;result['seconds']=time.monotonic()-started
    if any(codes.values()):result['errors'].append({'process_codes':codes})
    errors={name:(out/('C-only-'+name+'-stderr.csv')).stat().st_size for name in processes}
    result['stderr_bytes']=errors
    if any(errors.values()):result['errors'].append({'stderr_bytes':errors})
    save(out/'C-only.json',result);return result

def cost13b(duckc,work,out):
    pass                                                                            
    import math,statistics
    work=Path(work)/'cost13b';work.mkdir(parents=True,exist_ok=True);out=Path(out)
    support=work/'clock.c';support.write_text('''#include <stdint.h>
#include <time.h>
#include <sys/resource.h>
#include <malloc.h>
#include <stdio.h>
#include <unistd.h>
int64_t clock13(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
int64_t heap13(void){struct mallinfo2 m=mallinfo2();return (int64_t)m.uordblks+(int64_t)m.hblkhd;}
int64_t rss13(void){long n=0,r=0;FILE* f=fopen("/proc/self/statm","r");if(!f)return -1;if(fscanf(f,"%ld %ld",&n,&r)!=2)r=-1;fclose(f);return r*sysconf(_SC_PAGESIZE);}
int64_t peak13(void){struct rusage r;getrusage(RUSAGE_SELF,&r);return (int64_t)r.ru_maxrss*1024;}
''',encoding='ascii')
    driver=work/'cost.dk';driver.write_text('''import fizyka.gra as game;
import fizyka.swiat as raw;
import fizyka.kola as math2;
extern("C") { fundecl clock13() -> i64; fundecl heap13() -> i64; fundecl rss13() -> i64; fundecl peak13() -> i64; }
fun allocate13(points: ref List[math2.Vec2], closed: bool) -> i64 = {
 let w: raw.WorldId = raw.b2CreateWorld(math2.Vec2(),100.0f32);
 let b: raw.BodyId = raw.b2CreateBody(w,raw.BodyDef());
 var def = raw.ChainDef(); def.points = copy points; def.count = points.length() as i32; def.isLoop = closed;
 let start: i64 = clock13(); let c: raw.ChainId = raw.b2CreateChain(b,&def); let elapsed: i64 = clock13()-start;
 raw.b2DestroyChain(c); raw.b2DestroyWorld(w); return elapsed;
}
fun run13(n: i32, closed: bool, late: bool) -> i64 = {
 var p: List[math2.Vec2]; var i: i32 = 0i32;
 while (i < n) { var x: f32 = i as f32; var y: f32 = 0.0f32;
  if (closed) { if(i<32i32) x=i as f32; else if(i<64i32){x=32.0f32;y=(i-32i32) as f32;} else if(i<96i32){x=(96i32-i) as f32;y=32.0f32;} else{x=0.0f32;y=(128i32-i) as f32;} }
  if(late and i==n-1i32)x=n as f32-2.5f32; p.push(math2.Vec2(x,y)); i=i+1i32;
 }
 var k: i32 = 0i32;
 while(k<21i32){let start: i64=clock13();let reason: i32=game.validateChainGeometry(&p,closed);let elapsed: i64=clock13()-start;
  var allocated: i64=0i64;if(reason==0i32)allocated=allocate13(&p,closed);
  print("K13COST ");print(n.toString());print(" ");print(closed.toString());print(" ");print(late.toString());print(" ");print(k.toString());print(" ");print(reason.toString());print(" ");print(elapsed.toString());print(" ");print(allocated.toString());print(" ");print(heap13().toString());print(" ");print(rss13().toString());print(" ");print(peak13().toString());print("\\n");
  if((late and reason!=85i32) or (not late and reason!=0i32))return 1i64;k=k+1i32;
 }return 0i64;
}
fun main() -> i64 = {
 print("K13MEM BEFORE ");print(heap13().toString());print(" ");print(rss13().toString());print("\\n");
 if(run13(128i32,false,false)!=0i64)return 1i64;
 if(run13(4096i32,false,false)!=0i64)return 2i64;
 if(run13(128i32,true,false)!=0i64)return 3i64;
 if(run13(128i32,false,true)!=0i64)return 4i64;
 if(run13(4096i32,false,true)!=0i64)return 5i64;
 print("K13MEM AFTER ");print(heap13().toString());print(" ");print(rss13().toString());print("\\n");return 0i64;
}
''',encoding='utf-8')
    cc=['cc','-std=c17','-D_POSIX_C_SOURCE=200809L','-O2','-c',str(support),'-o',str(work/'clock.o')]
    subprocess.run(cc,check=True,capture_output=True)
    manifest={'packages':[{'id':'fizyka','name':'fizyka','path':str(ROOT/'silnik/fizyka')},
        {'id':'cost13b','name':'cost13b','path':str(driver),'dependencies':[{'id':'fizyka'}]}],
        'tasks':[{'package':'fizyka','strategy':'lib','output_file':'libfizyka.a'},
        {'package':'cost13b','strategy':'native','output_file':'cost13b','linking_options':{'additional_link_options':[str(work/'build/libfizyka.a'),str(work/'clock.o'),'-lm'],'link_c_standard_library':True}}]}
    save(work/'packages.json',manifest);argv=[str(duckc),'compile_packages',str(work/'packages.json'),'-a',str(work/'build'),'-O','0']
    receipt={'actual_K13b':True,'thresholds_checked':False,'optimization':0,'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'silnik/fizyka').glob('*.dk'))},
             'compiler_sha256':digest(duckc),'compiler_command':argv,'support_command':cc,'errors':[]}
    start=time.monotonic();r=subprocess.run(argv,capture_output=True,text=True,timeout=210);receipt['build_seconds']=time.monotonic()-start
    (out/'Q-COST-build-stdout.csv').write_text(r.stdout[-65536:],encoding='utf-8');(out/'Q-COST-build-stderr.csv').write_text(r.stderr[-65536:],encoding='utf-8')
    receipt['build_code']=r.returncode
    if r.returncode:save(out/'Q-COST.json',receipt);raise RuntimeError('actual K13b cost build failed')
                                                                                 
                                                                                
    native_argv=['timeout','--kill-after=5s','210s',str(work/'build/cost13b')]
    receipt['native_command']=native_argv
    start=time.monotonic();r=subprocess.run(native_argv,capture_output=True,text=True,timeout=220);receipt['native_seconds']=time.monotonic()-start
    (out/'Q-COST-native.csv').write_text(r.stdout,encoding='ascii');receipt['code']=r.returncode;receipt['stderr']=r.stderr
    groups={};memory=[]
    for line in r.stdout.splitlines():
        fields=line.split()
        if not fields:raise ValueError('cost13b empty row')
        if fields[0]=='K13MEM':
            if len(fields)!=4 or fields[1] not in ('BEFORE','AFTER') or not all(re.fullmatch(r'(?:0|[1-9][0-9]*)', x) for x in fields[2:]):raise ValueError('cost13b memory framing/types')
            memory.append(fields[1:]);continue
        if len(fields)!=11 or fields[0]!='K13COST':raise ValueError('cost13b framing')
        if fields[2] not in ('true','false') or fields[3] not in ('true','false') or not all(re.fullmatch(r'(?:0|[1-9][0-9]*)', fields[i]) for i in (1,4,5,6,7,8,9,10)):raise ValueError('cost13b canonical numeric/bool types')
        n=int(fields[1]);closed=fields[2]=='true';late=fields[3]=='true';iteration=int(fields[4]);reason=int(fields[5]);values=list(map(int,fields[6:]))
        groups.setdefault((n,closed,late),[]).append({'iteration':iteration,'reason':reason,'validation_ns':values[0],'allocation_ns':values[1],'heap':values[2],'rss':values[3],'peak':values[4]})
    expected={(128,False,False),(4096,False,False),(128,True,False),(128,False,True),(4096,False,True)}
    if set(groups)!=expected:receipt['errors'].append('Q-COST missing or non-normative variants: expected '+repr(sorted(expected))+'; got '+repr(sorted(groups)))
    receipt['variants']=[]
    for key,rows in groups.items():
        if len(rows)!=21 or [r['iteration'] for r in rows]!=list(range(21)):raise ValueError('one warmup +20 required')
        samples=rows[1:];v=sorted(r['validation_ns'] for r in samples);a=sorted(r['allocation_ns'] for r in samples)
        receipt['variants'].append({'N':key[0],'closed':key[1],'late_refusal':key[2],'samples':samples,
            'validation_ns':{'median':statistics.median(v),'p95':v[math.ceil(.95*len(v))-1],'max':max(v)},
            'allocation_ns':{'median':statistics.median(a),'p95':a[math.ceil(.95*len(a))-1],'max':max(a)},
            'distance_pairs':key[0]*(key[0]-1)//2,'edge_pairs':(key[0] if key[1] else key[0]-1)*((key[0] if key[1] else key[0]-1)-1)//2})
    receipt['memory_before_after']=memory;receipt['thresholds_checked']=set(groups)==expected and len(memory)==2 and [x[0] for x in memory]==['BEFORE','AFTER'] and r.returncode==0 and not r.stderr
    baseline_rss=int(memory[0][2]) if memory else 0
    receipt['peak_rss_increase']=max((s['peak'] for v in receipt['variants'] for s in v['samples']),default=0)-baseline_rss
    receipt['memory_threshold_passed']=receipt['peak_rss_increase']<=32*1024*1024
    receipt['heap_after_minus_before']=int(memory[-1][1])-int(memory[0][1]) if len(memory)==2 else None
                                                                                   
    receipt['thresholds_passed']=receipt['thresholds_checked'] and receipt['memory_threshold_passed'] and all(v['validation_ns']['p95']<=2700000 for v in receipt['variants'] if v['N']==128)
    receipt['memory_return']='Measured heap/RSS before/after; allocator retention is recorded, not normalized. Owned-list leak acceptance requires separate ownership evidence.'
    if not receipt['thresholds_passed']:receipt['errors'].append('Q-COST p95 threshold not met')
    save(out/'Q-COST.json',receipt);return receipt

def record_examples13b(out,work,binaries):
    inputs=load('lancuchy_examples_inputs','przypadki-lancuchy.py');model=load('lancuchy_examples_model','model-lancuchy.py')
    text=norm_text(HERE/'fixtures/norms/KONTRAKT-13.json').split('### 9.1.')[1].split('### 9.2.')[0]
    wanted=[line+'\n' for line in text.splitlines() if re.match(r'^(?:E13B|EP13B|EU13B|CN13|V13|CQ13|QL13|CH13|CI13|CM13|CS13|BH13|IP13|CG13|PC13|COPY13|CV13|CE13|ENDCOPY13|I13|Z13|GR13) 1 [03456] ',line)]
    if not wanted:raise ValueError('frozen literal examples missing')
    found=set();runs=[];examples={};work=Path(work);out=Path(out)
    for name,data in inputs.example_inputs13b():
        path=work/'example13b-input.csv';path.write_bytes(data);stderr=out/('example-'+name+'-stderr.csv')
        with stderr.open('wb') as error:
            process=subprocess.Popen(['timeout','--kill-after=5s','180s',str(binaries['obs1']),str(path)],stdout=subprocess.PIPE,stderr=error)
            try:
                for raw in iter(lambda:process.stdout.readline(131073),b''):
                    if len(raw)>131072:raise ValueError('example row envelope')
                    tag,values=model.parse_world13b(raw);line=raw.decode('ascii')
                    if tag in model.SCHEMA13B and tag not in ('G','GA'):examples.setdefault(tag,line)
                    if line in wanted:found.add(line)
                code=process.wait(timeout=10)
            finally:
                if process.poll() is None:process.terminate();process.wait(timeout=10)
                process.stdout.close();path.unlink(missing_ok=True)
        runs.append({'name':name,'code':code,'stderr_bytes':stderr.stat().st_size,'input_sha256':hashlib.sha256(data).hexdigest()})
    result={'required_literals':len(wanted),'matched':len(found),'unmatched':[x for x in wanted if x not in found],
            'runs':runs,'tags_observed':sorted(examples),'errors':[],'scope':'C literal format controls; acceptance separately'}
    if len(found)!=len(wanted) or any(r['code'] or r['stderr_bytes'] for r in runs):result['errors'].append('literal record/control mismatch')
    (out/'PORT13B-wzory.csv').write_text(''.join(sorted(found))+''.join(examples[t] for t in sorted(examples) if examples[t] not in found),encoding='ascii')
    save(out/'record-examples.json',result);return result

def native_metadata13b(out,binaries):
    pass                                                                     
    inputs=load('lancuchy_metadata_inputs','przypadki-lancuchy.py');second=load('lancuchy_metadata_second','ci-lancuchy-oslony.py')
    runtime=second.Runtime13B(out);result={'fixtures':[],'errors':[],'full_acceptance':False}
    for name,fixture in inputs.metadata_fixtures13b().items():
        cdata=''.join(inputs.text_fixture13b(fixture)).encode('ascii');ddata=''.join(inputs.text_fixture13b(fixture,True)).encode('ascii')
        row={'name':name,'kind':fixture['kind'],'sides':{},'errors':[]}
        try:
            with ExitStack() as stack:
                runs={name_:stack.enter_context(runtime.run(side,ddata if side=='D' else cdata,executable=binaries[key]))
                      for name_,side,key in (('c0','C0','obs0'),('c1','C','obs1'),('d','D','duckling'))}
                for side,(code,path,stderr,meta) in runs.items():
                    evidence={'code':code,'stderr_bytes':len(stderr),'run':meta}
                    try:
                        if code or stderr:raise ValueError('metadata native exit/stderr')
                        evidence['validation']=second.validate_file13b(path,ddata if side=='d' else cdata,side=='d',observer=side!='c0')
                    except Exception as exc:
                        evidence['error']=str(exc);row['errors'].append(side+': '+str(exc))
                    row['sides'][side]=evidence
                row['C0_projection_difference']=second.compare_files13b(runs['c1'][1],runs['c0'][1],project=True)
                row['C1_D_difference']=second.compare_files13b(runs['c1'][1],runs['d'][1])
                if row['C0_projection_difference'] or row['C1_D_difference']:row['errors'].append('metadata full words differ')
        except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
        row['ok']=not row['errors'];result['fixtures'].append(row)
        result['errors'] += [{'fixture':name,'error':error} for error in row['errors']]
    save(out/'metadata-fixtures.json',result);return result

def stage13b(ctx=None,*,source=None,duckc=None,work=None,out=None,N=64,duckling_binary=None):
    out=Path(out or location()).resolve();part=out/'13b';part.mkdir(parents=True,exist_ok=True)
    if not out.is_relative_to(ROOT.resolve()):raise ValueError('13b result outside repository')
    temp=Path(work or (Path(os.environ.get('RUNNER_TEMP',ROOT/'.port13-work'))/'silnik/port13')).resolve()
    temp.mkdir(parents=True,exist_ok=True)
    source=source or os.environ.get('BOX2D_SOURCE') or (ctx.base.TEMP/'box2d' if ctx else None)
    duckc=duckc or os.environ.get('DUCKLING_COMPILER')
    if not duckc and ctx:
        found=list((ctx.base.TEMP/'toolchain-port').rglob('duckc'))
        if len(found)==1:duckc=found[0]
    result={'scope':'13b','N':N,'stages':{},'code':1,'full_acceptance':False,'start_unix':time.time()};binaries={}
    def perform(name,fn,depends=()):
        started=time.monotonic()
        if any(result['stages'].get(d,{}).get('code')!=0 for d in depends):
            row={'code':1,'executed':False,'reason':'dependency failed/missing: '+','.join(depends)}
        else:
            try:
                value=fn();row={'code':int(bool(value.get('errors',[]))),'executed':True,'result':value}
            except Exception as exc:row={'code':1,'executed':True,'reason':type(exc).__name__+': '+str(exc)}
        row['seconds']=time.monotonic()-started;result['stages'][name]=row;save(part/'manifest.json',result)
        print('13b/'+name+': '+str(row['code']),flush=True);return row
    def cbuild():
        if source is None:raise FileNotFoundError('existing Box2D source required; no download')
        builder=load('lancuchy_ci_builder13b','budowa-lancuchy.py')
        receipt=builder.build13b(source,temp/'c-13b',temp/'c-13b/bin')
        for key,row in receipt['binaries'].items():binaries[key]=row['binary']
        save(part/'build-C.json',receipt);return {'binaries':receipt['binaries'],'source_unchanged':receipt['unchanged'],'symbols':receipt['symbols']}
    perform('build_C0_C1',cbuild)
    def dbuild():
        if duckling_binary and Path(duckling_binary).is_file():
            binaries['duckling']=str(duckling_binary);return {'binary':str(duckling_binary),'reused_same_native_build':True,'sha256':digest(duckling_binary)}
        receipt=compile_duckling(duckc or '',temp,part,part='13b');binaries['duckling']=receipt['binary'];return receipt
    perform('build_Duckling',dbuild)
    inputs=load('lancuchy_ci_inputs13b','przypadki-lancuchy.py');items=inputs.cases13b(N)
    perform('C0_C1_projection',lambda:native_projection13b(part,temp,items,binaries),('build_C0_C1',))
    perform('literal_record_examples',lambda:record_examples13b(part,temp,binaries),('build_C0_C1',))
    perform('small_probe',lambda:native_compare13b(part,temp,items[:min(N,16)],binaries,sample=True),('build_C0_C1','build_Duckling'))
    perform('full_comparison',lambda:native_compare13b(part,temp,items,binaries),('build_C0_C1','build_Duckling'))
    perform('metadata_fixtures',lambda:native_metadata13b(part,binaries),('build_C0_C1','build_Duckling'))
                                                                              
                                                                             
    perform('Q_COST_actual_K',lambda:cost13b(duckc or '',temp,part))
    result['binaries']=binaries;result['code']=int(any(row['code'] for row in result['stages'].values()))
    result['price_measurement']={'builds_seconds':{k:v['seconds'] for k,v in result['stages'].items() if k.startswith('build_')},
        'kernel_print_separation':'UNMEASURED: pipe wall includes formatting and backpressure; Q-COST is separate'}
    save(part/'manifest.json',result)
    manifest_path=out/'manifest.json'
    combined=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'stages':{},'scope':'13b; 13a not run here','first_half_code':0}
    combined['13b']=result;combined['first_half_code']=int(bool(combined.get('first_half_code',1) or result['code']))
    save(manifest_path,combined);return result

def probe13c(items):
    result=[]
    for case in items:
        if case.id<=384:result.append(replace(case,ops=case.ops[:2]));continue
        steps=0
        for i,o in enumerate(case.ops):
            steps+=o['opcode'] in (31,32)
            if steps==10:result.append(replace(case,ops=case.ops[:i+1]));break
        else:raise ValueError('13c sample requires10 positive Step per world')
    return tuple(result)

def native_compare13c(out,work,items,binaries,*,sample=False,c_only=False,require_history=True,seconds=2100):
    pass                                                                          
    cmp=load('lancuchy_ci_compare13c','porownaj-lancuchy.py');out=Path(out);out.mkdir(parents=True,exist_ok=True)
    label='C-only' if c_only else 'sample' if sample else 'full';inputs=Path(work)/('13c-'+label+'-inputs');inputs.mkdir(parents=True,exist_ok=True)
    if sample:items=probe13c(items)
    procs={};codes={};input_info={};start=time.monotonic();result={'errors':[],'comparison_ok':False,'global_END_checked':False,'full_acceptance':False}
    sides=[('c0',False,'obs0'),('c1',False,'obs1')]+([] if c_only else [('d',True,'duckling')])
    try:
        with ExitStack() as stack:
            for name,decimal,key in sides:
                path=inputs/(name+'.csv')
                with path.open('w',encoding='ascii',newline='\n') as f:f.writelines(cmp.g.text13c(items,decimal))
                input_info[name]={'bytes':path.stat().st_size,'sha256':digest(path),'binary_sha256':digest(binaries[key])}
                procs[name]=subprocess.Popen(['timeout','--kill-after=5s',str(seconds)+'s',str(binaries[key])],stdin=stack.enter_context(path.open('rb')),stdout=subprocess.PIPE,stderr=stack.enter_context((out/(label+'-'+name+'-stderr.csv')).open('wb')))
            def progress(row,state):save(out/(label+'-progress.json'),{'id':row['id'],'snapshots':state['snapshots'],'positive_steps':state['positive_steps'],'errors':state['error_count'],'seconds':time.monotonic()-start})
            with gzip.open(out/(label+'-errors.jsonl.gz'),'wt',encoding='utf-8') as errors:
                result=cmp.compare13c_streams({k:p.stdout for k,p in procs.items()},items,require_history=require_history,error_sink=errors,progress=progress)
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        for name,p in procs.items():
            if not result.get('global_END_checked') and p.poll() is None:p.terminate()
            try:codes[name]=p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();codes[name]=p.wait(timeout=10)
            if p.stdout:p.stdout.close()
        if inputs.resolve().parent!=Path(work).resolve():raise ValueError('13c input cleanup path')
        shutil.rmtree(inputs)
    stderr_bytes={k:(out/(label+'-'+k+'-stderr.csv')).stat().st_size for k in procs}
    if any(codes.values()):result['errors'].append({'process_codes':codes})
    if any(stderr_bytes.values()):result['errors'].append({'stderr_bytes':stderr_bytes})
    result.update(inputs=input_info,process_codes=codes,stderr_bytes=stderr_bytes,seconds=time.monotonic()-start,sample_only=sample,C_only=c_only)
    result['comparison_ok']=result.get('comparison_ok',False) and not result['errors'];save(out/(label+'.json'),result);return result

def stage13c(ctx=None,*,source=None,duckc=None,work=None,out=None,N=432,duckling_binary=None):
    out=Path(out or location()).resolve();part=out/'13c';part.mkdir(parents=True,exist_ok=True)
    if not out.is_relative_to(ROOT.resolve()):raise ValueError('13c result outside repository')
    temp=Path(work or (Path(os.environ.get('RUNNER_TEMP',ROOT/'.port13-work'))/'silnik/port13')).resolve();temp.mkdir(parents=True,exist_ok=True)
    source=source or os.environ.get('BOX2D_SOURCE') or (ctx.base.TEMP/'box2d' if ctx else None)
    duckc=duckc or os.environ.get('DUCKLING_COMPILER')
    if not duckc and ctx:
        found=list((ctx.base.TEMP/'toolchain-port').rglob('duckc'))
        if len(found)==1:duckc=found[0]
    result={'scope':'13c','N':N,'stages':{},'code':1,'full_acceptance':False,'start_unix':time.time()};binaries={}
    def perform(name,fn,depends=()):
        start=time.monotonic()
        if any(result['stages'].get(d,{}).get('code')!=0 for d in depends):row={'code':1,'executed':False,'reason':'dependency failed/missing: '+','.join(depends)}
        else:
            try:value=fn();row={'code':int(bool(value.get('errors',[]))),'executed':True,'result':value}
            except Exception as exc:row={'code':1,'executed':True,'reason':type(exc).__name__+': '+str(exc)}
        row['seconds']=time.monotonic()-start;result['stages'][name]=row;save(part/'manifest.json',result);print('13c/'+name+': '+str(row['code']),flush=True);return row
    def cbuild():
        if source is None:raise FileNotFoundError('existing original Box2D required; no download')
        receipt=load('lancuchy_builder13c','budowa-lancuchy.py').build13c(source,temp/'c-13c',temp/'c-13c/bin')
        for key,row in receipt['binaries'].items():binaries[key]=row['binary']
        save(part/'build-C.json',receipt);return {'source_unchanged':receipt['unchanged'],'binaries':receipt['binaries'],'symbols':receipt['symbols']}
    perform('build_C0_C1',cbuild)
    def dbuild():
        if duckling_binary and Path(duckling_binary).is_file():binaries['duckling']=str(duckling_binary);return {'reused_same_native_build':True,'binary':str(duckling_binary),'sha256':digest(duckling_binary)}
        receipt=compile_duckling(duckc or '',temp,part,part='13c');binaries['duckling']=receipt['binary'];return receipt
    perform('build_Duckling',dbuild)
    items=load('lancuchy_inputs13c','przypadki-lancuchy.py').cases13c(N)
    perform('C0_projection_C1_sample',lambda:native_compare13c(part,temp,items,binaries,sample=True,c_only=True,require_history=False),('build_C0_C1',))
    sample=perform('OBS_VOLUME',lambda:native_compare13c(part,temp,items,binaries,sample=True,require_history=False),('build_C0_C1','build_Duckling'))
    if sample.get('result',{}).get('word_comparison_ok'):
        measured=sample['result'];full_ops={c.id:len(c.ops) for c in items};sample_ops={r['id']:r['operations'] for r in measured['cases']}
        weighted=sum(r['streams']['c1']['bytes']*full_ops[r['id']]/sample_ops[r['id']] for r in measured['cases'])
        current=measured['streams']['c1']['bytes'];estimate=measured['seconds']*weighted/max(1,current)
        result['price_measurement']={'sample_seconds':measured['seconds'],'estimated_full_seconds':estimate,'with_2x_margin_seconds':2*estimate,'builds_separate':{k:v['seconds'] for k,v in result['stages'].items() if k.startswith('build_')},'method':'percase bytes/operations, physical print/model/compare combined; kernel-only and separate RAM still unmeasured'}
    else:result['price_measurement']={'status':'UNMEASURED: OBS/VOLUME sample failed'}
    perform('full_comparison',lambda:native_compare13c(part,temp,items,binaries,require_history=True),('build_C0_C1','build_Duckling'))
    result['binaries']=binaries;result['code']=int(any(x['code'] for x in result['stages'].values()));save(part/'manifest.json',result)
    path=out/'manifest.json';combined=json.loads(path.read_text()) if path.exists() else {'stages':{},'first_half_code':0}
    combined['13c']=result;combined['first_half_code']=int(bool(combined.get('first_half_code',1) or result['code']));save(path,combined);return result

def stage(ctx=None,*,source=None,duckc=None,work=None,out=None,N=128):
    out=Path(out or location()).resolve();out.mkdir(parents=True,exist_ok=True);part=out/'13a';part.mkdir(exist_ok=True)
    if not out.is_relative_to(ROOT.resolve()):raise ValueError('results must stay in current repository')
    temp=Path(work or (Path(os.environ.get('RUNNER_TEMP',ROOT/'.port13-work'))/'silnik/port13')).resolve();temp.mkdir(parents=True,exist_ok=True)
    source=source or os.environ.get('BOX2D_SOURCE') or (ctx.base.TEMP/'box2d' if ctx else None)
    if not duckc:
        duckc=os.environ.get('DUCKLING_COMPILER')
        candidates=list((ctx.base.TEMP/'toolchain-port').rglob('duckc')) if ctx else []
        if not duckc and len(candidates)==1:duckc=candidates[0]
    result={'stages':{},'code':1,'N':N,'full_acceptance':False,'scope':'13a only','start_unix':time.time()};binaries={}
    def perform(name,fn,depends=()):
        start=time.monotonic()
        if any(result['stages'].get(d,{}).get('code')!=0 for d in depends):
            row={'code':1,'executed':False,'reason':'dependency failed/missing: '+','.join(depends)}
        else:
            try:
                value=fn();row={'code':int(bool(value.get('errors',[]))),'executed':True,'result':value}
            except Exception as exc:row={'code':1,'executed':True,'reason':str(exc)}
        row['seconds']=time.monotonic()-start;result['stages'][name]=row;save(out/'manifest.json',result)
        print(name+': '+str(row['code']),flush=True);return row
    def cbuild(profile):
        if source is None:raise FileNotFoundError('existing Box2D source not supplied; no download permitted')
        builder=load('lancuchy_ci_builder','budowa-lancuchy.py')
        directory=temp/('c-'+profile)
        r=builder.build(source,directory,directory/'bin',(profile,));binaries[profile]=r['profiles'][profile]['binary']
        save(part/('build-'+profile+'.json'),r)
        shutil.copy2(directory/'bin/build-journal.json',part/('build-'+profile+'-journal.json'))
        return {'binary':binaries[profile],'sha256':r['profiles'][profile]['sha256']}
    perform('build_R',lambda:cbuild('R'));perform('build_D',lambda:cbuild('D'))
    def d_build():
        r=compile_duckling(duckc or '',temp,part);binaries['duckling']=r['binary'];return r
    perform('build_Duckling',d_build)
    g=load('lancuchy_ci_inputs','przypadki-lancuchy.py')
    items=g.cases(N)
    perform('small_probe',lambda:native_compare(part,temp,items,binaries,sample=True),('build_R','build_D','build_Duckling'))
                                                                              
    perform('full_comparison',lambda:native_compare(part,temp,items,binaries),('build_R','build_D','build_Duckling'))
    result['binaries']=binaries;result['code']=int(any(r['code'] for r in result['stages'].values()));result['first_half_code']=result['code']
    result['price_measurement']={'builds_seconds':{k:v['seconds'] for k,v in result['stages'].items() if k.startswith('build_')},
        'printing_kernel_separation':'UNMEASURED: native wall includes kernel, formatting and pipe backpressure; not an isolated physics time'}
    save(out/'manifest.json',result)
    if os.environ.get('LANCUCHY_PART') == '13a':
        return result['code']
    b13=stage13b(ctx,source=source,duckc=duckc,work=temp/'13b',out=out)
    result['13b']=b13;result['scope']='13a + 13b';result['first_half_code']=int(bool(result['first_half_code'] or b13['code']))
    c13=stage13c(ctx,source=source,duckc=duckc,work=temp/'13c',out=out)
    result['13c']=c13;result['scope']='13a + 13b + 13c';result['first_half_code']=int(bool(result['first_half_code'] or c13['code']))
    result['code']=result['first_half_code'];save(out/'manifest.json',result);summary(out)
    return result['code']

def second_half_stage(ctx=None):
    pass                                                                  
    second=load('lancuchy_second_half','ci-lancuchy-oslony.py');rows={};code=0
    if os.environ.get('LANCUCHY_PART') in ('13a', '13b', '13c'):
        return second.stage(ctx)
    path=location()/'13c/13c-oslony-wynik.json';before=path.stat().st_mtime_ns if path.exists() else None
    try:rows['legacy']=second.stage(ctx);code=int(bool(rows['legacy']))
    except Exception as exc:rows['legacy']={'error':str(exc)};code=1
    if not path.exists() or path.stat().st_mtime_ns==before:
        previous_binary=os.environ.get('LANCUCHY_D_BIN')
        try:
            manifest=location()/'13c/manifest.json'
            native=json.loads(manifest.read_text(encoding='utf-8')).get('binaries',{}).get('duckling') if manifest.is_file() else None
            if native:os.environ['LANCUCHY_D_BIN']=native
            rows['13c']=second.stage13c(ctx);code=int(bool(code or rows['13c']))
        except Exception as exc:rows['13c']={'error':str(exc)};code=1
        finally:
            if previous_binary is None:os.environ.pop('LANCUCHY_D_BIN',None)
            else:os.environ['LANCUCHY_D_BIN']=previous_binary
    else:
        rows['13c']='already executed by the independent stage';code=int(bool(code or json.loads(path.read_text()).get('code',1)))
    save(location()/'second-half-wrapper.json',rows);return code

def summary(out=None):
    out=Path(out or location());path=out/'manifest.json'
    data=json.loads(path.read_text()) if path.exists() else {'stages':{},'code':1}
    part=os.environ.get('LANCUCHY_PART')
    if part in ('13a', '13b', '13c'):
        first=data if part=='13a' else data.get(part, {'code':1, 'reason':'first half missing'})
        run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
        guard=(ROOT/os.environ.get('RESULT_DIR','RESULT-PORT/'+run)/'krok13/13a-oslony-wynik.json') if part=='13a' else out/part/(part+'-oslony-wynik.json')
        second=json.loads(guard.read_text(encoding='utf-8')) if guard.is_file() else {'code':1,'reason':'second half missing'}
        outcomes={name:os.environ.get('LANCUCHY_'+name.upper()+'_OUTCOME') for name in ('source','tools','comparison','guards')}
        code=int(bool(first.get('code',1) or second.get('code',1) or any(value is not None and value!='success' for value in outcomes.values())))
        result={'part':part,'code':code,'first_half':first,'second_half':second,'workflow_outcomes':outcomes,'full_acceptance':False}
        save(out/(part+'-podsumowanie.json'),result)
        (out/'PODSUMOWANIE.md').write_text('# '+part+'\n\nRESULT: '+('FAIL / MISSINGI' if code else 'COMPARISON I ETAPY ZGODNE; E50d888b3c61d OSOBNO')+'\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return code
    run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    legacy=ROOT/os.environ.get('RESULT_DIR','RESULT-PORT/'+run)
    if legacy.name in ('krok10','krok11','krok12'):legacy=legacy.parent
    guards=legacy/'krok13/13a-oslony-wynik.json'
    if guards.exists():data['second_half']=json.loads(guards.read_text(encoding='utf-8'))
    else:data['second_half']={'code':1,'reason':'second-half stage missing'}
    guards13b=out/'13b/13b-oslony-wynik.json'
    if guards13b.exists():data['second_half13b']=json.loads(guards13b.read_text(encoding='utf-8'))
    else:data['second_half13b']={'code':1,'reason':'13b second-half stage missing'}
    data['code']=int(bool(data.get('first_half_code',1) or data['second_half'].get('code',1) or data['second_half13b'].get('code',1)))
    if '13c' in data:
        guards13c=out/'13c/13c-oslony-wynik.json'
        data['second_half13c']=json.loads(guards13c.read_text()) if guards13c.exists() else {'code':1,'reason':'13c second-half stage missing'}
        data['code']=int(bool(data['code'] or data['second_half13c'].get('code',1)))
    workflow={name:os.environ.get('LANCUCHY_'+name.upper()+'_OUTCOME') for name in ('source','tools','comparison','guards')}
    if any(value is not None for value in workflow.values()):
        data['workflow_outcomes']=workflow
        if any(value!='success' for value in workflow.values()):data['code']=1
    data['full_acceptance']=False
    data['remaining_acceptance_gates']=['final once-bound native mutations and full branch witnesses','Regression checks1-12 on matching product sources','Independent native verification required']
    save(path,data)
    lines=['# PORT13A + PORT13B — Ebc2e4bea2e33 E323ff42b3213','','RESULT: '+('FAIL / MISSINGI' if data['code'] else 'COMPARISON I ETAPY ZGODNE; E50d888b3c61d OSOBNO'),'','|Etap|Kod|Wykonany|','|---|---:|---|']
    lines += [f'|{name}|{row['code']}|{row.get('executed', False)}|' for name,row in data['stages'].items()]
    lines += [f'|13b/{name}|{row['code']}|{row.get('executed', False)}|' for name,row in data.get('13b',{}).get('stages',{}).items()]
    lines += [f'|13c/{name}|{row['code']}|{row.get('executed', False)}|' for name,row in data.get('13c',{}).get('stages',{}).items()]
    if '13c' in data:lines += ['|Ef4465733b96b13E2e7d2c03a950 / E7e72a0f110a6 E40aa22cf9d0f|'+str(data['second_half13c'].get('code',1))+'|single guard stage|']
    lines += ['|Ef4465733b96b13E3e23e8160039 / E7e72a0f110a6 E40aa22cf9d0f|'+str(data['second_half13b'].get('code',1))+'|single guard stage|']
    lines += ['|Ef4465733b96b / E7e72a0f110a6 E40aa22cf9d0f|'+str(data['second_half'].get('code',1))+'|separate etap|','','E1f965d7d73ad Eddc1b687a5c213Eca978112ca1b: NOT. E8f2faefb7b47 Eacbc52b56ea8:']+['- '+x for x in data['remaining_acceptance_gates']]
    lines += ['','## Ed449338af5d2 E5fd9324ff1a4 E229b13358750','']+['- '+x for x in data['second_half'].get('errors',[])]
    if 'workflow_outcomes' in data:lines += ['','E912d8e962acf Ea192241e964a: '+json.dumps(data['workflow_outcomes'],ensure_ascii=False)]
    (out/'PODSUMOWANIE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return data['code']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--duckc',type=Path);p.add_argument('--work',type=Path);p.add_argument('--out',type=Path);p.add_argument('--N',type=int);p.add_argument('--summary',action='store_true');p.add_argument('--second-half',action='store_true');p.add_argument('--13b',dest='chain_world',action='store_true');p.add_argument('--13c',dest='chain_contact',action='store_true');a=p.parse_args()
    if a.second_half:code=second_half_stage()
    elif a.summary:code=summary(a.out)
    elif a.chain_contact:
        code=stage13c(source=a.source,duckc=a.duckc,work=a.work,out=a.out,N=432 if a.N is None else a.N)['code'];summary(a.out)
    elif a.chain_world:
        code=stage13b(source=a.source,duckc=a.duckc,work=a.work,out=a.out,N=64 if a.N is None else a.N)['code'];summary(a.out)
    else:code=stage(source=a.source,duckc=a.duckc,work=a.work,out=a.out,N=128 if a.N is None else a.N)
    sys.exit(code)
