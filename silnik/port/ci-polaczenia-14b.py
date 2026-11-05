pass                                                                         
from pathlib import Path
from collections import deque
import argparse,datetime,hashlib,importlib.util,json,os,shutil,signal,subprocess,sys,tarfile,threading,time,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
A=module('ci14b_base','ci-polaczenia.py');B=module('ci14b_build','budowa-14b.py');T=module('ci14b_compare','odbior-14b.py');N=module('ci14b_negative','polaczenia-14b-ujemne.py')
def save(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def process_tree(pid):
 rows={}
 for p in Path('/proc').glob('[0-9]*/stat'):
  try:
   v=p.read_text().rsplit(')',1)[1].split();status=p.with_name('status').read_text();rss=int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')))*1024;rows[int(p.parent.name)]=(int(v[1]),rss)
  except (FileNotFoundError,ProcessLookupError,PermissionError,StopIteration):pass
 descendants={pid}
 while True:
  expanded=descendants|{n for n,(parent,rss) in rows.items() if parent in descendants}
  if expanded==descendants:break
  descendants=expanded
 return descendants,sum(rows.get(n,(0,0))[1] for n in descendants)
def bounded_build(argv,out,seconds,env):
 start=time.monotonic();peak=0;failure=None
 with out.with_suffix('.stdout').open('wb') as stdout,out.with_suffix('.stderr').open('wb') as stderr:
  p=subprocess.Popen(list(map(str,argv)),stdout=stdout,stderr=stderr,start_new_session=True,env=env)
  while p.poll() is None:
   children,rss=process_tree(p.pid);peak=max(peak,rss)
   if rss>2*1024**3:failure='process tree RSS2GiB'
   elif time.monotonic()-start>seconds:failure='shared build180s'
   if failure:
    for pid in children:
     try:os.kill(pid,signal.SIGKILL)
     except ProcessLookupError:pass
    break
   time.sleep(.05)
  code=p.wait()
 result=dict(argv=list(map(str,argv)),exit=code,seconds=time.monotonic()-start,peakTreeRSS=peak,failure=failure,limitSeconds=seconds,limitBytes=2*1024**3);save(out.with_suffix('.json'),result)
 if code or failure:raise ValueError('D compilation failed: '+str(result))
 return result
def compile_d(duckc,archive,work):
 duckc,archive,work=map(lambda p:Path(p).resolve(),(duckc,archive,work));work.mkdir(parents=True,exist_ok=False)
 if digest(archive)!=A.OFFICIAL_B_SHA:raise ValueError('official B archive SHA mismatch')
 with tarfile.open(archive,'r:gz') as tar:
  members=[m for m in tar.getmembers() if m.isfile() and Path(m.name).name=='duckc'];assert len(members)==1
  expected=hashlib.file_digest(tar.extractfile(members[0]),'sha256').hexdigest()
 if digest(duckc)!=expected:raise ValueError('compiler differs from pinned archive member')
 sources=A.source_identity();raw=(HERE/'polaczenia.dk').read_bytes();anchor=b'const PORT14_PART_B: bool = false;'
 if raw.count(anchor)!=1:raise ValueError('one accepted compile-time profile selector required')
 entry=work/'entry';entry.mkdir();driver=entry/'polaczenia.dk';driver.write_bytes(raw.replace(anchor,b'const PORT14_PART_B: bool = true;'))
 artifacts=work/'artifacts';artifacts.mkdir();binary=artifacts/'polaczenia-bin';library=artifacts/'libfizyka.a'
 packages=[dict(id='fizyka',name='fizyka',path=str(HERE.parent/'fizyka')),dict(id='polaczenia',name='polaczenia',path=str(driver),dependencies=[dict(id='fizyka')])]
 tasks=[dict(package='fizyka',strategy='lib',output_file=library.name),dict(package='polaczenia',strategy='native',output_file=binary.name,linking_options=dict(additional_link_options=[str(library),'-lm'],link_c_standard_library=True))]
 env=os.environ.copy();env.update(MALLOC_ARENA_MAX='1',MALLOC_TRIM_THRESHOLD_='131072',MALLOC_MMAP_THRESHOLD_='131072')
 start=time.monotonic();stamp=time.time_ns();commands=[]
 for i,task in enumerate(tasks):
  path=work/f'packages-{i}.json';save(path,dict(packages=packages,tasks=[task]));argv=[duckc,'compile_packages',path,'-a',artifacts,'-O','0','-w','1','--no-incremental']
  if i:argv+=['--custom-std-artifacts-path',artifacts]
  commands.append(bounded_build(argv,work/f'task-{i}',180-(time.monotonic()-start),env))
 r=dict(code=0,commands=commands,seconds=time.monotonic()-start,peakTreeRSS=max(x['peakTreeRSS'] for x in commands),fresh=all(p.is_file() and p.stat().st_mtime_ns>=stamp for p in (binary,library)),ELF=binary.read_bytes()[:4]==b'\x7fELF',archiveSHA256=A.OFFICIAL_B_SHA,compilerSHA256=expected,binary=str(binary),binarySHA256=digest(binary),driverSHA256=digest(driver),sources=sources,sourceSHA256=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest(),sources_unchanged=sources==A.source_identity(),originalEntrySHA=hashlib.sha256(raw).hexdigest(),specializedEntrySHA=digest(driver),part='B')
 save(work/'build.json',r)
 if not all(r[k] for k in ('fresh','ELF','sources_unchanged')) or r['seconds']>180:raise ValueError('stale/non-ELF/changed D build')
 return r
def strict_run(bins,cases,out,seconds):
                                                                           
                                                                        
 original=T.Reader.take;finish=T.Reader.finish;pending=deque();state=dict(rows=0,bytes=0,bufferBytes=0,firstDifference=None);started=time.monotonic()
 def observed_finish(self,case):
  result=finish(self,case)
  if self.label=='d':
   save(Path(out)/'progress.json',dict(profile=case.profile,key=case.key,completedCases=case.id,seconds=time.monotonic()-started,positiveSteps=result['positiveSteps']))
   print('CASE',case.profile,case.key,flush=True)
  return result
 def take(self,expected=None):
  cached=self.pending is not None;raw,record=original(self,expected)
  if not cached and self.label=='c1':
   pending.append(raw);state['bufferBytes']+=len(raw)
   if state['bufferBytes']>13833216+1048576:raise ValueError('one-snapshot streaming envelope')
  elif not cached and self.label=='d':
   if not pending:raise ValueError('D emitted an unpaired physical line')
   left=pending.popleft();state['bufferBytes']-=len(left);state['rows']+=1;state['bytes']+=len(raw)
   if left!=raw:
    state['firstDifference']=dict(row=state['rows'],left=left[:512].decode(errors='replace'),right=raw[:512].decode(errors='replace'));raise ValueError('C1/D byte difference')
  return raw,record
 T.Reader.take=take;T.Reader.finish=observed_finish
 try:r=T.run(bins,cases,out,seconds=seconds)
 finally:T.Reader.take=original;T.Reader.finish=finish
 state['complete']=r.get('complete',False) and not pending and state['firstDifference'] is None and state['bytes']==r.get('streams',{}).get('c1',{}).get('bytes')
 r['byteComparison']=state;save(Path(out)/'result.json',r)
 if not r.get('functional_C_D_ok') or not state['complete']:raise ValueError('full native/byte/snapshot/history comparison failed: '+str(Path(out)/'result.json'))
 return r
def campaign(args):
 work,out=Path(args.work).resolve(),Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
 receipt=dict(protocol='PORT14B',mode=args.mode,sourceCommit=os.environ.get('GITHUB_SHA'),startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=False,functional_ok=False,full_acceptance=False,stages={},failures=[],unexecuted=[])
 start=time.monotonic();deadline=start+6000;original_source=Path(args.source).resolve();source_before=B.A.source_sums(original_source);product_before=A.source_identity()
 def stage(name,fn):
  stamp=time.monotonic();print('START',name,flush=True)
  try:
   if time.monotonic()>=deadline:raise ValueError('campaign100min')
   value=fn();receipt['stages'][name]=dict(ok=True,seconds=time.monotonic()-stamp,value=value);print('OK',name,flush=True);return value
  except Exception as exc:
   receipt['stages'][name]=dict(ok=False,seconds=time.monotonic()-stamp,error=str(exc),traceback=traceback.format_exc());receipt['failures'].append(name);print('FAIL',name,str(exc),flush=True)
  finally:save(out/'campaign.json',receipt)
 try:
  if work.exists():raise ValueError('fresh empty campaign work path required')
  work.mkdir(parents=True);(work/'OWNER').write_text('PORT14B CI 31f14aa1b\n')
  stage('inputs',lambda:{p:T.G.execution_manifest(T.G.cases(p)) for p in ('PUBLIC','DIRECT','GUARD')})
  def build_c():
   fixed=work/'Bfix';shutil.copytree(original_source,fixed)
   run=subprocess.run(['patch','-p1','-i',str(HERE/'14b-bfix.patch')],cwd=fixed,capture_output=True)
   (out/'Bfix-patch.log').write_bytes(run.stdout+run.stderr)
   if run.returncode:raise ValueError('exact Bfix patch failed')
   try:return B.build(fixed,work/'cbuild',work/'c',source_kind='Bfix',part='B')
   finally:
    if (work/'c').exists():
     for p in (work/'c').iterdir():
      if p.suffix in ('.json','.stdout','.stderr'):shutil.copy2(p,out/('C-'+p.name))
  def build_d():
   try:return compile_d(args.duckc,args.archive,work/'d')
   finally:
    if (work/'d').exists():
     for p in (work/'d').iterdir():
      if p.suffix in ('.json','.stdout','.stderr'):shutil.copy2(p,out/('D-'+p.name))
  cr=stage('build-C',build_c);dr=stage('build-D',build_d)
  if dr:save(out/'build-D.json',dr)
  if cr and dr:
   bins=dict(c0=Path(cr['binaries']['obs0']['binary']),c1=Path(cr['binaries']['obs1']['binary']),d=Path(dr['binary']))
   stage('binding',lambda:T.binding(bins))
   def selftest():
    r=T.selftest(dict(c0=bins['c0'],c1=bins['c1']),out/'selftest')
    if not r['complete']:raise ValueError('comparator selftest failed')
    return r
   stage('selftest',selftest)
                                                                   
   for profile in ('DIRECT','GUARD'):
    stage(profile,lambda p=profile:strict_run(bins,T.G.cases(p),out/p,deadline-time.monotonic()))
   for label,binary in bins.items():
    def parsers(side=label,binary=binary):
     r=N.run(binary,out/('parsers-'+side+'.json'),decimal=side=='d')
     if not r['trials_complete'] or r['passed']!=84 or r['trials']!=84 or not all(x['boundary_proved'] for x in r['unavailable']):raise ValueError('parser trials/neighbours/reachability proof failed')
     return r
    stage('parsers-'+label,parsers)
   if not receipt['failures']:stage('PUBLIC',lambda:strict_run(bins,T.G.cases('PUBLIC'),out/'PUBLIC',deadline-time.monotonic()))
   else:receipt['unexecuted'].append('PUBLIC')
  else:receipt['unexecuted']=['binding','selftest','PUBLIC','DIRECT','GUARD','parsers-c0','parsers-c1','parsers-d']
 except Exception as exc:
  receipt['failures'].append('environment');receipt['environmentError']=str(exc);receipt['traceback']=traceback.format_exc()
 finally:
  receipt.update(seconds=time.monotonic()-start,source_unchanged=source_before==B.A.source_sums(original_source),product_unchanged=product_before==A.source_identity())
  required=['inputs','build-C','build-D','binding','selftest','PUBLIC','DIRECT','GUARD','parsers-c0','parsers-c1','parsers-d']
  receipt['unexecuted']=sorted(set(receipt['unexecuted'])|{s for s in required if s not in receipt['stages']})
  receipt['functional_ok']=not receipt['failures'] and not receipt['unexecuted'] and receipt['source_unchanged'] and receipt['product_unchanged'] and receipt['seconds']<=6000
  receipt['complete']=receipt['functional_ok'];receipt['code']=int(not receipt['functional_ok']);receipt['note']='Functional comparison only; coverage, sample and input checks are separate requirements. Parser complete=false records an unexecuted stage.'
  save(out/'campaign.json',receipt);(out/'PODSUMOWANIE.md').write_text('# PORT14B\n\n'+('C1=D; full B functional campaign complete' if receipt['functional_ok'] else 'BLAD / MISSING')+'\n\n'+json.dumps({k:v for k,v in receipt.items() if k!='stages'},indent=2)+'\n',encoding='utf-8')
 return receipt['code']
def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['full'],default='full');p.add_argument('--source',required=True);p.add_argument('--work',required=True);p.add_argument('--out',required=True);p.add_argument('--duckc',required=True);p.add_argument('--archive',required=True);return campaign(p.parse_args())
if __name__=='__main__':sys.exit(main())
