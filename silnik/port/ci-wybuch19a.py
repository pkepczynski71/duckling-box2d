pass                                                                   
                                                                             
                                                                             
   
from pathlib import Path
import argparse,datetime,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile,time,traceback
from wybuch19a import HERE,manifest,sha,write_inputs,run,inventory

def module(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
B=module('build19','budowa-wybuch19a.py');C=module('compare19','porownaj-wybuch19a.py');A=module('audit19','19a-check.py')
ARCHIVE='f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519'
def save(p,data):Path(p).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def identity(receipt,binary,inp,expected_binary,expected_input):
 if receipt['binarySHA256']!=expected_binary or sha(binary)!=expected_binary or receipt['inputSHA256']!=expected_input or sha(inp)!=expected_input:raise ValueError('foreign binary/input binding')
 return True
def bind(receipt,binary,inp,expected_binary,expected_input):
 identity(receipt,binary,inp,expected_binary,expected_input)
 if receipt['exit'] or receipt['stderr'] or receipt['failure']:raise ValueError('program failed or exceeded envelope')
 return True
def byte_equal(a,b,projection=False):
 n=0
 with C.open_log(a) as x,C.open_log(b) as y:
  left=iter(x);right=C.project(y) if projection else iter(y)
  from itertools import zip_longest
  for n,(u,v) in enumerate(zip_longest(left,right),1):
   if u!=v:raise ValueError(f'bit/order difference row {n}: {u!r} / {v!r}')
 return n
def replay_frozen(actual,profile,frozen=None):
 frozen=Path(frozen) if frozen is not None else HERE/'wybuch19a-frozen';record=json.loads((frozen/'REFERENCE.json').read_bytes());path=frozen/(profile+'-C1.out.csv.gz')
 if sha(path)!=record['frozen'][path.name]['sha256']:raise ValueError('accepted frozen stream pin')
 return dict(comparedRows=byte_equal(path,actual))
def compile_d(archive,duckc,driver,work):
 archive,duckc,driver=map(lambda p:Path(p).resolve(),(archive,duckc,driver));work=Path(work);work.mkdir(exist_ok=True)
 if not driver.is_file():raise ValueError('Native driver is missing: '+str(driver))
 if sha(archive)!=ARCHIVE:raise ValueError('official be929a1a archive pin')
 with tarfile.open(archive) as tar:
  names=[m for m in tar.getmembers() if m.isfile() and Path(m.name).name=='duckc']
  if len(names)!=1:raise ValueError('compiler archive inventory')
  expected=hashlib.file_digest(tar.extractfile(names[0]),'sha256').hexdigest()
 if sha(duckc)!=expected:raise ValueError('compiler binary pin')
 artifacts=work/'artifacts';binary=artifacts/'wybuch19a-bin';library=artifacts/'libfizyka.a'
 if binary.exists() or library.exists():raise ValueError('fresh D artifact directory required')
 packages={'packages':[{'id':'fizyka','name':'fizyka','path':str(HERE.parent/'fizyka')},{'id':'wybuch19a','name':'wybuch19a','path':str(driver),'dependencies':[{'id':'fizyka'}]}],
           'tasks':[{'package':'fizyka','strategy':'lib','output_file':library.name},{'package':'wybuch19a','strategy':'native','output_file':binary.name,'linking_options':{'additional_link_options':[str(library),'-lm'],'link_c_standard_library':True}}]}
 save(work/'packages.json',packages);sources={p.name:sha(p) for p in (HERE.parent/'fizyka').glob('*.dk')};before=sha(driver)
                                                                         
 started=time.monotonic();commands=[]
 r=dict(archiveSHA256=ARCHIVE,compilerSHA256=expected,driverSHA256=before,sources=sources,commands=commands)
 for label,task in zip(('library','driver'),packages['tasks']):
  remaining=180-(time.monotonic()-started)
  if remaining<=0:raise ValueError('D combined compilation limit')
  path=work/(label+'-task.json');save(path,dict(packages=packages['packages'],tasks=[task]))
  result=run([duckc,'compile_packages',path,'-a',artifacts,'-O','0','-w','1'],None,work/(label+'-compile.log'),remaining,2*1024**3);commands.append(result)
  r.update(exit=result['exit'],failure=result['failure'],seconds=time.monotonic()-started,peakTreeRSS=max(x['peakTreeRSS'] for x in commands));save(work/'build.json',r)
  if result['exit'] or result['failure']:raise ValueError('D '+label+' task failed')
 if time.monotonic()-started>180 or not binary.is_file() or not library.is_file() or binary.read_bytes()[:4]!=b'\x7fELF':raise ValueError('D build failed/no fresh ELF')
 if sources!={p.name:sha(p) for p in (HERE.parent/'fizyka').glob('*.dk')} or before!=sha(driver):raise ValueError('D sources changed')
 r['binarySHA256']=sha(binary);save(work/'build.json',r);return str(binary),r

def campaign(args):
 work,out=Path(args.work).resolve(),Path(args.out).resolve();work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 marker=work/'OWNER'
 if marker.exists() and marker.read_text()!=B.OWNER:raise ValueError('OWNER mismatch')
 marker.write_text(B.OWNER)
 started=time.monotonic();receipt=dict(protocol='PORT19A',mode=args.mode,full_acceptance=False,startedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),stages={},failures=[])
 def bounded_run(argv,inp,dest):
  remaining=600-(time.monotonic()-started)
  if remaining<=0:raise ValueError('campaign600s exceeded')
  return run(argv,inp,dest,min(30,remaining))
 def stage(label,fn):
  t=time.monotonic();print('START',label,flush=True)
  try:
   if time.monotonic()-started>=600:raise ValueError('campaign600s exceeded')
   value=fn()
   if time.monotonic()-started>600:raise ValueError('campaign600s exceeded')
   receipt['stages'][label]=dict(ok=True,seconds=time.monotonic()-t,value=value);print('OK',label,flush=True);return value
  except Exception as e:receipt['stages'][label]=dict(ok=False,seconds=time.monotonic()-t,error=str(e),traceback=traceback.format_exc());receipt['failures'].append(label);print('FAIL',label,str(e),flush=True)
  finally:save(out/'campaign.json',receipt)
 inv=stage('inventory',lambda:inventory(args.source));save(out/'source-inventory.json',inv)
 input_hashes=stage('inputs',lambda:write_inputs(work/'inputs'))
 builds={}
 for variant in ('Bfix','B0'):
  r=stage('build-'+variant,lambda v=variant:B.build(args.source,work/('c-'+v),v));builds[variant]=r
  log=work/('c-'+variant)/'build.json'
  if log.exists():shutil.copy2(log,out/('build-'+variant+'.json'))
 paths={};runs={}
 for variant in builds:
  if not builds[variant]:continue
  for profile in ('DIRECT','PUBLIC','GUARD'):
   for side in ('obs0','obs1') if variant=='Bfix' else ('obs1',):
    label=f'{variant}-{profile}-{side}';path=work/(label+'.out');binary=Path(builds[variant]['binaries'][side]['path']);inp=work/'inputs'/(profile+'C.in')
    def execute():
     r=bounded_run([binary],inp,path);save(out/(label+'.json'),r);bind(r,binary,inp,builds[variant]['binaries'][side]['sha256'],input_hashes[profile+'C']);return r
    r=stage(label,execute);paths[variant,profile,side]=path;runs[label]=r
                                                                             
                                                                      
 for profile in ('DIRECT','PUBLIC','GUARD'):
  if all(k in paths for k in [('Bfix',profile,'obs0'),('Bfix',profile,'obs1')]):
   stage('neutral-'+profile,lambda p=profile:C.compare(paths['Bfix',p,'obs0'],paths['Bfix',p,'obs1'],p,True))
  if ('B0',profile,'obs1') in paths and ('Bfix',profile,'obs1') in paths:
   stage('B0-equals-Bfix-'+profile,lambda p=profile:dict(comparedRows=byte_equal(paths['B0',p,'obs1'],paths['Bfix',p,'obs1'])))
  if ('Bfix',profile,'obs1') in paths:
   stage('frozen-replay-'+profile,lambda p=profile:replay_frozen(paths['Bfix',p,'obs1'],p))
 if all(('Bfix',p,'obs1') in paths for p in ('DIRECT','PUBLIC','GUARD')):
  def c18():
   r=A.audit({p:paths['Bfix',p,'obs1'] for p in ('DIRECT','PUBLIC','GUARD')})
   if not r['ok']:raise ValueError(r)
   return r
  stage('C18-reproduced-by-PORT19',c18)
 binary=Path(builds['Bfix']['binaries']['obs1']['path']) if builds.get('Bfix') else None
 if binary:
  def parsers():
   rows=[]
   for c in manifest()['parsers']:
    pair=[]
    for key in ('inputC','positiveC'):
     name=f'parser{c['id']:02}-{key}.in';r=bounded_run([binary,*c['args']],work/'inputs'/name,work/(f'parser{c['id']:02}-{key}.out'));identity(r,binary,work/'inputs'/name,builds['Bfix']['binaries']['obs1']['sha256'],input_hashes[name]);pair.append(r)
    ok=pair[0]['exit']==c['exit'] and pair[0]['stderr']==c['stderr'] and pair[1]['exit']==0 and not pair[1]['stderr']
                                                                              
                                                                         
    invalid=(work/(f'parser{c['id']:02}-inputC.out')).read_bytes()
    ok &= b'END ' not in invalid
    if c['class'] in ('HEADER','PART','PROFILE','N','LINE_LENGTH','ASCII'):ok &= len(invalid)==0
    rows.append(dict(id=c['id'],kind=c['class'],ok=ok,negative=pair[0],positive=pair[1]))
   save(out/'parsers-C.json',rows)
   if not all(x['ok'] for x in rows):raise ValueError('parser pair failure '+str([x['kind'] for x in rows if not x['ok']]))
   return dict(pairs=len(rows),positive=24,negative=24)
  stage('parser-pairs-C',parsers)
  def endings(binary,expected_binary,side):
   rows=[]
   for profile in ('DIRECT','PUBLIC','GUARD'):
    original=manifest()['literalInputs'][profile+side].encode()
    for suffix,data in [('CRLF',original.replace(b'\n',b'\r\n')),('EOF',original[:-1])]:
     inp=work/f'{profile}-{side}-{suffix}.in';dest=work/f'{profile}-{side}-{suffix}.out';inp.write_bytes(data)
     r=bounded_run([binary],inp,dest);save(out/(f'endings-{side}-{profile}-{suffix}.json'),r);bind(r,binary,inp,expected_binary,hashlib.sha256(data).hexdigest());r['comparedRows']=byte_equal(paths['Bfix',profile,'obs1'],dest);rows.append(dict(profile=profile,variant=suffix,**r));dest.unlink()
   save(out/('endings-'+side+'.json'),rows);return dict(variants=6,ok=True)
  stage('CRLF-EOF-C',lambda:endings(binary,builds['Bfix']['binaries']['obs1']['sha256'],'C'))
 if args.mode=='full':
  if not args.duckc or not args.archive:stage('D-compile',lambda:(_ for _ in ()).throw(ValueError('Full mode requires --duckc/--archive and native product --driver')))
  else:
   built=stage('D-compile',lambda:compile_d(args.archive,args.duckc,args.driver or HERE/'wybuch19a.dk',work/'d'))
   if (work/'d/build.json').exists():shutil.copy2(work/'d/build.json',out/'build-D.json')
   if built:
    d,dr=built;save(out/'build-D.json',dr)
    for profile in ('DIRECT','PUBLIC','GUARD'):
     def execute_d(p=profile):
      inp=work/'inputs'/(p+'D.in');dest=work/(p+'-D.out');r=bounded_run([d],inp,dest);save(out/(p+'-D.json'),r);bind(r,d,inp,dr['binarySHA256'],input_hashes[p+'D']);return C.compare(paths['Bfix',p,'obs1'],dest,p)
     stage('C1-equals-D-'+profile,execute_d)
    def parsers_d():
     errors=[]
     for c in manifest()['parsers']:
      for key in ('inputD','positiveD'):
       name=f'parser{c['id']:02}-{key}.in';r=bounded_run([d,*c['args']],work/'inputs'/name,work/(f'parser{c['id']:02}-{key}.out'));identity(r,d,work/'inputs'/name,dr['binarySHA256'],input_hashes[name])
       expected=(c['exit'],c['stderr']) if key=='inputD' else (0,'')
       if (r['exit'],r['stderr'])!=expected:errors.append((c['class'],key,r))
       else:
        ckey='inputC' if key=='inputD' else 'positiveC'
        try:byte_equal(work/(f'parser{c['id']:02}-{ckey}.out'),work/(f'parser{c['id']:02}-{key}.out'))
        except ValueError as e:errors.append((c['class'],key,str(e)))
     if errors:raise ValueError(errors)
     return dict(pairs=24)
    stage('parser-pairs-D',parsers_d)
    stage('CRLF-EOF-D',lambda:endings(d,dr['binarySHA256'],'D'))
                                                                             
 if not receipt['failures']:
  for profile in ('DIRECT','PUBLIC','GUARD'):
   src=paths['Bfix',profile,'obs1'];dest=out/(profile+'-C1.out.csv.gz')
   with src.open('rb') as f,dest.open('wb') as z,gzip.GzipFile(filename='',mode='wb',fileobj=z,mtime=0) as g:shutil.copyfileobj(f,g)
  receipt['frozen']={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in out.glob('*-C1.out.csv.gz')}
 receipt['seconds']=time.monotonic()-started;receipt['source_unchanged']=inv==inventory(args.source)
 receipt['reference_ready']=not receipt['failures'] and receipt['source_unchanged'];receipt['full_acceptance']=False
 receipt['note']='Reference comparison does not include coverage or sample checks.'
 save(out/'campaign.json',receipt);return 1 if receipt['failures'] else 0

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--work',required=True);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['reference','full'],default='full');p.add_argument('--duckc');p.add_argument('--archive');p.add_argument('--driver');args=p.parse_args();sys.exit(campaign(args))
