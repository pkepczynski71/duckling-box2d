pass                                                                              
from pathlib import Path
from collections import Counter
import hashlib,json,os,shutil,subprocess,time

HERE=Path(__file__).resolve().parent
MANIFEST_SHA='5734bd97552e453c85bb54b05fe204039afb0309298b7493ff420271e467cbbd'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def manifest():
 p=HERE/'wybuch-19a-przypadki.json'
 if sha(p)!=MANIFEST_SHA:raise ValueError('F19 manifest SHA')
 return json.loads(p.read_bytes())
def inventory(source):
 source=Path(source);files=sorted(p for p in source.rglob('*') if p.is_file())
 return dict(files=len(files),directoriesIncludingRoot=1+sum(p.is_dir() for p in source.rglob('*')),
             extensions=dict(Counter(p.suffix or '(none)' for p in files)),
             top=dict(Counter(p.relative_to(source).parts[0] if len(p.relative_to(source).parts)>1 else '(root)' for p in files)),
             ch={p.relative_to(source).as_posix():sha(p) for p in files if p.suffix in ('.c','.h')})
def write_inputs(out):
 out=Path(out);out.mkdir(exist_ok=True,parents=True);m=manifest();result={}
 for name,text in m['literalInputs'].items():
  path=out/(name+'.in');path.write_bytes(text.encode('ascii'));result[name]=sha(path)
 for c in m['parsers']:
  for key in ('inputC','inputD','positiveC','positiveD'):
   p=out/(f'parser{c['id']:02}-{key}.in');p.write_bytes(c[key].encode('ascii'));result[p.name]=sha(p)
 return result
def process_rss(pid):
 pass                                                                  
 total=0
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   stat=(p/'stat').read_text();parts=stat[stat.rfind(')')+2:].split()
   if int(parts[3])!=pid:continue
   total+=int(parts[21])*os.sysconf('SC_PAGE_SIZE')
  except (OSError,ValueError,IndexError):pass
 return total
def run(argv,input_path,out_path,seconds=30,memory=1024**3):
 pass                                                                       
 out_path=Path(out_path);out_path.parent.mkdir(exist_ok=True,parents=True);err=out_path.with_suffix(out_path.suffix+'.stderr')
 def limits():
  import resource
                                                                      
  resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 t=time.monotonic();peak=0;failure=None
 with (Path(input_path).open('rb') if input_path else open(os.devnull,'rb')) as inp,out_path.open('wb') as out,err.open('wb') as stderr:
  p=subprocess.Popen(list(map(str,argv)),stdin=inp,stdout=out,stderr=stderr,start_new_session=True,preexec_fn=limits)
  while p.poll() is None:
   peak=max(peak,process_rss(p.pid));elapsed=time.monotonic()-t
   if elapsed>seconds or peak>memory:
    import signal
    failure='TIME_LIMIT' if elapsed>seconds else 'MEMORY_LIMIT';os.killpg(p.pid,signal.SIGKILL);break
   time.sleep(.02)
  code=p.wait()
 r=dict(argv=list(map(str,argv)),exit=code,seconds=time.monotonic()-t,peakTreeRSS=peak,limitSeconds=seconds,limitRSS=memory,failure=failure,
        inputSHA256=sha(input_path) if input_path else None,binarySHA256=sha(shutil.which(str(argv[0])) or argv[0]),stdoutSHA256=sha(out_path),stdoutBytes=out_path.stat().st_size,stderr=err.read_text())
 out_path.with_suffix(out_path.suffix+'.json').write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--inputs',type=Path);a.add_argument('--source',type=Path);args=a.parse_args()
 print(json.dumps(write_inputs(args.inputs) if args.inputs else inventory(args.source),indent=2))
