pass                                                                              
from pathlib import Path
import importlib.util,json,sys
from wybuch19a import HERE,manifest
s=importlib.util.spec_from_file_location('cmp19',HERE/'porownaj-wybuch19a.py');cmp=importlib.util.module_from_spec(s);s.loader.exec_module(cmp)
def audit(paths):
 m=manifest();checks=0;failures=[]
 def check(ok,label):
  nonlocal checks
  checks+=1
  if not ok:failures.append(label)
 for profile,path in paths.items():
  data=m['direct' if profile=='DIRECT' else 'public'] if profile!='GUARD' else m['guards']
  if profile=='GUARD':
   for _ in cmp.validated(path,profile):pass
   checks+=96;continue
  states={};traces={};results={};args={};copies={};physical={}
  with cmp.open_log(path) as f:
   for raw in f:
    tag=raw.split(b' ',1)[0]
    if profile=='PUBLIC' and tag not in (b'CASE',b'ENDCASE',b'END'):
     p=raw.rstrip(b'\n').split(b' ');cid,seq=map(int,p[1:3])
     counter=tag.decode() in cmp.BASE.COUNTERS or tag==b'J14' and len(p)>6 and p[6]==b'8'
     if seq in (6,7) and tag not in (b'E19',b'A19',b'R19',b'I19',b'X19',b'Z19') and not counter:
      physical.setdefault((cid,seq),[]).append((tag,*p[3:]))
    if tag not in (b'S19',b'X19',b'R19',b'I19',b'V19'):continue
    t,v=cmp.parse(raw);cid,seq=v[:2]
    if tag==b'S19' and v[4]==0:states[cid,seq,v[2]]=v[6:]
    elif tag==b'X19':traces.setdefault((cid,seq),[]).append(v)
    elif tag==b'R19':results[cid,seq]=v[5:]
    elif tag==b'I19':args[cid,seq]=v[3:]
    elif tag==b'V19':copies[cid,seq,v[2]]=v[4:]
  for c in data:
   cid=c['id']
   if profile=='DIRECT':
    if c['kind'] in (0,1,5):
     n=7 if c['kind']==0 else 4;check(results[cid,1]==tuple(int(x,16) for x in c['cResultH'][:n]),f'D{cid:03} result C18')
     if n==4:check(args[cid,1]==tuple(int(x,16) for x in c['cPreparedInputH']),f'D{cid:03} prepared C18')
    else:check(states[cid,1,0]==tuple(int(x,16) for x in c['cResultH'][14:28]),f'D{cid:03} post explosion C18')
   else:
    expected=tuple(int(x,16) for x in c['cStateBeforeAfterFinalH'])
    if cid in (23,24):check(results[cid,1]==expected,f'P{cid:03} native C18')
    else:
     check(states[cid,3,0]==expected[14:28],f'P{cid:03} post C18')
     check(states[cid,9,c['sceneWords'][21]]==expected[28:42],f'P{cid:03} final C18')
     check(copies[cid,2,0]==copies[cid,9,0],f'P{cid:03} historical bank0')
     check(copies[cid,5,1][0]==0x42f60000 and copies[cid,5,1][1:]==copies[cid,2,1][1:],f'P{cid:03} edit bank1 only')
     check(physical[cid,6]==physical[cid,7],f'P{cid:03} checked refusal full physical snapshot unchanged')
   for stage in (1,2):
    seq=1 if profile=='DIRECT' else 3 if stage==1 else 8
    old=[x.split() for x in c['cTrace'] if int(x.split()[2])==stage]
    new=traces.get((cid,seq),[]) if profile!='DIRECT' or stage==1 else []
    check(len(old)==len(new),f'{profile}{cid} stage{stage} trace count')
    for ordinal,(x,y) in enumerate(zip(old,new)):
                                                                        
     expected=(cid,seq,ordinal,int(x[5]),int(x[6]),int(x[4]),1 if int(x[4])!=2 else 10,*map(lambda z:int(z,16),x[7:]))
     check(y==expected,f'{profile}{cid} trace stage{stage}/{ordinal}')
 return dict(ok=not failures,checks=checks,failures=failures)
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args();w=args.out
 rows={}
 for profile in ('DIRECT','PUBLIC','GUARD'):
  rows[profile]=cmp.compare(w/(profile+'-obs0.out'),w/(profile+'-obs1.out'),profile,True)
  print(profile,'neutral',rows[profile]['ok'],rows[profile]['comparedRows'],flush=True)
 rows['C18']=audit({p:w/(p+'-obs1.out') for p in ('DIRECT','PUBLIC','GUARD')});print('C18',rows['C18'],flush=True)
 (w/'checks.json').write_text(json.dumps(rows,indent=2)+'\n')
 if not rows['C18']['ok']:sys.exit(1)
