pass                                                                       

                                                                                
                                                                                 
   
from pathlib import Path
from collections import Counter
from itertools import zip_longest
import argparse,gzip,importlib.util,json,re,sys
from wybuch19a import HERE,manifest

def load_base():
 spec=importlib.util.spec_from_file_location('wybuch19_compare14',HERE/'porownaj-polaczenia.py')
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
BASE=load_base();H=re.compile(rb'[0-9a-f]{8}\Z');D=re.compile(rb'(?:0|[1-9][0-9]*)\Z')
NEW={'CASE','ENDCASE','END','E19','A19','R19','I19','X19','V19','S19','Z19','G19','GA19'}
def require(ok,message):
 if not ok:raise ValueError(message)
def dec(x):
 require(D.fullmatch(x) is not None,'canonical decimal');v=int(x);require(v<=0xffffffff,'decimal range');return v
def parse(raw):
 require(0<len(raw)<=131072 and raw.endswith(b'\n'),'line envelope/LF')
 require(re.fullmatch(rb'[!-~]+(?: [!-~]+)*\n',raw) is not None,'ASCII/spacing')
 p=raw[:-1].split(b' ');tag=p[0].decode();require(tag in NEW or tag not in ('PORT14','E14','A14'),'foreign transport')
 if tag not in NEW:return BASE.parse(raw)
 prefix={'CASE':2,'ENDCASE':1,'END':1,'E19':4,'A19':5,'R19':5,'I19':3,'X19':7,'V19':4,'S19':6,'Z19':7,'G19':4,'GA19':5}[tag]
 require(len(p)>=1+prefix,tag+' prefix');v=tuple(dec(x) for x in p[1:prefix+1]);payload=p[prefix+1:]
 require(all(H.fullmatch(x) for x in payload),tag+' H8')
 if tag in ('E19','R19','I19','X19','V19','S19','G19'):require(len(payload)==v[-1],tag+' arity')
 else:require(not payload,tag+' extra payload')
 if tag=='R19':require(v[3] in range(6) and v[4]==(0,7,4,19,30,19)[v[3]],'result kind/arity')
 if tag=='X19':require(v[5] in range(3) and v[6]==(1,1,10)[v[5]],'trace phase/arity')
 if tag=='V19':require(v[2]<2 and v[3]==19,'bank copy arity')
 if tag=='S19':require(v[3]==0 and v[4]<2 and v[5]==14,'state arity/slot')
 return tag,(*v,*(int(x,16) for x in payload))
def open_log(path):return gzip.open(path,'rb') if str(path).endswith('.gz') else Path(path).open('rb')
def operations(text):
 lines=iter(text.splitlines());header=next(lines).split();profile=header[2];cases=[]
 for row in lines:
  c=row.split();require(c[0]=='C','frozen case row');cid,count=map(int,c[1:]);ops=[]
  for _ in range(2 if profile=='GUARD' else count):
   op=next(lines).split();ops.append(dict(seq=int(op[1]),code=int(op[2]),n=int(op[3]),a=tuple(int(x,16) for x in op[4:])))
  cases.append(dict(id=cid,count=count,ops=ops))
 require(len(cases)==int(header[3]),'frozen input population');return cases

class Reader:
 def __init__(self,f):self.f=f;self.pending=None;self.rows=0
 def get(self):
  raw=self.pending if self.pending is not None else self.f.readline();self.pending=None
  require(bool(raw),'premature EOF');self.rows+=1;return raw,parse(raw)
 def peek(self):
  if self.pending is None:self.pending=self.f.readline()
  require(bool(self.pending),'premature EOF');return self.pending.split(b' ',1)[0].rstrip(b'\n').decode('ascii')

def validated(path,profile,observed=True,input_text=None,stats=None):
 m=manifest();cases=operations(input_text or m['literalInputs'][profile+'C']);stats=stats if stats is not None else {}
 totals=Counter()
 with open_log(path) as f:
  r=Reader(f)
  def take(tag,expected=None):
   raw,(got,v)=r.get();require(got==tag,f'expected {tag}, got {got}');require(expected is None or tuple(expected)==v,tag+' fields/echo');totals[got]+=1;return raw,v
  for case in cases:
   cid=case['id'];raw,_=take('CASE',(cid,case['count']));yield raw
   saved=set()
   if profile=='GUARD':
    g=m['guards'][cid-1]
    for phase,op in enumerate(case['ops']):
     raw,_=take('G19',(cid,phase,600,9,*op['a']));yield raw
     expected=g['negativeExpected' if phase==0 else 'positiveExpected'];raw,_=take('GA19',(cid,phase,*expected));yield raw
   else:
    scene=m['direct' if profile=='DIRECT' else 'public'][cid-1].get('sceneWords',m['baseSceneWords'])
    native=profile=='PUBLIC' and cid in (23,24);nb=0 if native else 2 if scene[1]&16 else 1;ns=0 if native else scene[3]+int(bool(scene[1]&16));nj=0 if native else int(bool(scene[1]&16))
    for op in case['ops']:
     seq,code,n,a=op['seq'],op['code'],op['n'],op['a'];raw,_=take('E19',(cid,seq,code,n,*a));yield raw
     fixture=m['direct' if profile=='DIRECT' else 'public'][cid-1]
     stage=1 if profile=='DIRECT' or seq==3 else 2 if seq==8 else -1
     candidates=sum(int(x.split()[2])==stage for x in fixture.get('cTrace',[])) if code==600 else 0
     ordinal=0
     while r.peek()=='X19':
      raw,v=take('X19');require(observed and code==600 and v[:3]==(cid,seq,ordinal),'trace scope/order');require(v[3]<ns and v[4]<nb,'trace shape/body');ordinal+=1;yield raw
     require(ordinal==candidates if observed else ordinal==0,'frozen callback inventory')
     raw,v=take('A19');require(v[:3]==(cid,seq,code),'A19 operation');status,reason=v[3:]
     require((status,reason) in ((0,0),(1,0),(5,25),(7,1)),'status/reason');
     expected_status=(5,25) if profile=='PUBLIC' and not native and seq==7 else (0,0)
     require((status,reason)==expected_status,'frozen API status');yield raw
     raw,v=take('R19');require(v[:3]==(cid,seq,code),'R19 operation');kind={601:1,602:2,603:2,606:3,609:4+int(a[0]) if code==609 else 0}.get(code,0);require(v[3]==kind,'R19 kind');yield raw
     if observed and code in (600,601,602,603):
      raw,v=take('I19');require(v[:3]==(cid,seq,{600:7,601:0,602:39,603:39}[code]),'argument snapshot arity');yield raw
     if code==605:saved.add(a[0])
     if code==609 and a[0]==1:saved={0,1}
     for bank in sorted(saved):
      raw,v=take('V19');require(v[:4]==(cid,seq,bank,19),'owned bank inventory');yield raw
     native_step=code==609 and a[0]==0
     ticks=(1,0) if native_step else range(1,scene[21]+1) if code==607 and scene[21] else (0,)
     for tick in ticks:
      frame_nb,frame_ns,frame_nj=(2,2,0) if native_step and tick==1 else (nb,ns,nj)
      for body in range(frame_nb):
       raw,v=take('S19');require(v[:6]==(cid,seq,tick,0,body,14),'state/tick/body inventory');yield raw
      counts=Counter();previous=(-1,);seen=set()
      while r.peek()!='Z19':
       raw,(tag,v)=r.get();require(tag not in NEW,'unexpected new row in BASE13');require(v[:2]==(cid,seq),'BASE13 case/seq');rank=BASE.rank((tag,v));require(rank>=previous,'BASE13 order');previous=rank
       require(raw not in seen,'duplicate BASE13 record');seen.add(raw);counts[tag]+=1;totals[tag]+=1;yield raw
                                                                           
      for tag in ('Z8','Z9','Z10','Z11','Z12','Z13','I8','I9','I10','I11','I12','I13','IP12'):
       require(counts[tag]==1,'missing/duplicate full BASE13 '+tag)
      require(counts['B']==frame_nb and counts['S']==frame_ns and counts['G']==frame_ns,'BASE13 body/shape inventory')
      require(counts['W']==int(frame_nb>0),'BASE13 world inventory');require(counts['J14']>0,'joint observer summary missing')
      if frame_nb:require(counts['SS11']>=3 and counts['SM11']==frame_nb,'full solver sets/sims missing')
      raw,v=take('Z19',(cid,seq,tick,frame_nb,frame_ns,frame_nj,candidates));yield raw;totals['snapshots']+=1
   raw,_=take('ENDCASE',(cid,));yield raw
  raw,_=take('END',(len(cases),));yield raw;require(not f.read(1),'trailing output');stats.update(rows=r.rows,counts=dict(totals),cases=len(cases))

def project(lines):
 for raw in lines:
  if not raw.startswith((b'I19 ',b'X19 ')):yield raw
def compare(left,right,profile,neutral=False,input_text=None):
 ls,rs={},{};l=validated(left,profile,not neutral,input_text,ls);r=validated(right,profile,True,input_text,rs)
 if neutral:r=project(r)
 differences=[];count=0
 for count,(a,b) in enumerate(zip_longest(l,r),1):
  if a!=b and len(differences)<10:differences.append(dict(row=count,left=a.decode().rstrip() if a else None,right=b.decode().rstrip() if b else None))
 require(not differences,'bit/order mismatch '+json.dumps(differences[:2]));return dict(ok=True,comparedRows=count,left=ls,right=rs,neutral=neutral)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('left',type=Path);a.add_argument('right',type=Path);a.add_argument('--profile',choices=['DIRECT','PUBLIC','GUARD'],required=True);a.add_argument('--neutral',action='store_true');args=a.parse_args()
 try:print(json.dumps(compare(args.left,args.right,args.profile,args.neutral),indent=2))
 except (ValueError,OSError) as e:print(str(e),file=sys.stderr);sys.exit(1)
