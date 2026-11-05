pass                                                                      
                                                                    
   
from pathlib import Path
import argparse,gzip,importlib.util,json,subprocess,sys
from wybuch19a import HERE,run,inventory,manifest
import hashlib
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
B=load('cov19_build','budowa-wybuch19a.py');CI=load('cov19_ci','ci-wybuch19a.py')
def selected_gcno(work):
 return sorted(p for p in (Path(work).resolve()/'c-coverage/project/make').rglob('*.gcno') if 'c11-obs0-bin.dir' not in p.parts)
def collect(work):
 work=Path(work).resolve();cov=work/'gcov';cov.mkdir(exist_ok=True);counts={}
                                                                             
                                                                                
 for p in selected_gcno(work):
  result=subprocess.run(['gcov','-j','-b','-c',str(p)],cwd=cov,capture_output=True,text=True,timeout=30)
  if result.returncode:raise ValueError(result.stderr)
 wanted={'b2World_Explode','ExplosionCallback','b2WakeBody','b2WakeSolverSet','b2Body_SetType','b2MergeAwakeIslands','b2UnlinkJoint','b2TransferBody','b2TransferJoint','b2ShapeDistance','b2GetShapePerimeter','b2GetShapeProjectedPerimeter'}
 for p in cov.glob('*.gcov.json.gz'):
  data=json.loads(gzip.decompress(p.read_bytes()))
  for f in data['files']:
   for fn in f.get('functions',[]):
    name=fn['name']
    if name in wanted or name=='port11OriginalWakeSolverSet':counts[name]=dict(source=f['file'],start=fn['start_line'],end=fn['end_line'],calls=fn['execution_count'])
 return counts
def measure(source,work,out):
 source,work,out=Path(source).resolve(),Path(work).resolve(),Path(out).resolve();b=B.build(source,work/'c-coverage','Bfix',True);binary=Path(b['binaries']['obs1']['path']);out.mkdir(exist_ok=True)
 receipt=dict(build=b,runs={},counts={},scope='neutrality + Bfix call-path pin only; no N/P/O/S/U classification')
 for profile in ('DIRECT','PUBLIC','GUARD'):
  path=work/(profile+'-coverage.out');r=run([binary],work/'inputs'/(profile+'C.in'),path);CI.bind(r,binary,work/'inputs'/(profile+'C.in'),b['binaries']['obs1']['sha256'],hashlib.sha256(manifest()['literalInputs'][profile+'C'].encode()).hexdigest())
  r['comparedRows']=CI.byte_equal(path,out/(profile+'-C1.out.csv.gz'));receipt['runs'][profile]=r
 receipt['counts']=collect(work)
 receipt['source_unchanged']=inventory(source)==b['inventory'];(out/'coverage-neutrality.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({k:v['calls'] for k,v in receipt['counts'].items()},indent=2));return receipt
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--work',required=True);a.add_argument('--out',required=True);x=a.parse_args();measure(x.source,x.work,x.out)
