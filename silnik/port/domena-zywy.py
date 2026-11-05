pass                                                                    

                                                                          
                                                                             
                                                                            
   
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

n=load('zywy_domain_inputs','ujemne-zywy.py')
m=load('zywy_domain_model','model-zywy.py')
NAMES=frozenset(('raw-negative-dt','zero-hertz-positive-dt','zero-hertz-restored-before-step'))


class DomainPolicy:
    pass                                                               
    def __init__(self,name):
        m.require(name in NAMES,'explicit named domain fixture required')
        self.name=name;self.tuning={};self.infinite={};self.next_seq=1;self.failure=None
        self.allowed_snapshots=0

    def check(self,seq,operation,packet):
        m.require(self.failure is None,'domain history unavailable after failure')
        try:
            m.require(seq==self.next_seq,'domain continuous sequence')
            rows=m.SnapshotGrammar().check(1,seq,operation,packet,True)
            code,*a=operation
            status=rows['AP12'][0][2] if 80<=code<=92 else rows['R'][0][3]
            m.require(status==0,'named domain operation must succeed')
            if code==56:
                m.require(a[0] not in self.tuning,'domain world register collision')
                self.tuning[a[0]]=tuple(map(n.bits,(30.,10.,3.)));self.infinite[a[0]]=False
            elif code==82 and a[2]==3:self.tuning[a[0]]=tuple(a[3:6])
            elif code in (31,32) and m.number(a[1])!=0:
                hertz,damping,push=map(m.number,self.tuning[a[0]])
                expected=m.number(a[1])<0 or hertz==0
                m.require(not expected or push>0,'named diagnostic excludes 0/0')
                self.infinite[a[0]]=expected
            m.require({v[2] for v in rows['WS12']}==set(self.tuning),'domain world completeness')
            for v in rows['WS12']:
                m.require(v[6:9]==self.tuning[v[2]],'tuning is derived from input, not learned from output')
            m.require({v[2] for v in rows['W10']}==set(self.tuning),'domain W10 completeness')
            for tag in ('W10','CX10','BV10','HR10','HG10','SC10'):
                d,_=m.m10.SCHEMA[tag]
                for v in rows[tag]:
                    allowed=tag=='W10' and self.infinite[v[2]]
                    if allowed:
                        m.require(v[d+5]==0x7f800000,'exact predicted positive contactSpeed infinity')
                        self.allowed_snapshots+=1
                    m.m10.finite_words(tag,(0,*v[1:d]),v[d:],allow_contact_speed_inf=allowed)
            self.next_seq+=1
            return rows
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            self.failure={'seq':seq,'error':str(exc)}
            raise


def fixtures():
    read=n.op(91,0,0,0,1)
    def tune(h):return n.op(82,0,1,3,n.bits(h),n.bits(10),n.bits(3))
    def step(dt,game=False):return n.op(32 if game else 31,0,n.bits(dt),1,0)
    return (
        ('raw-negative-dt',(n.g.world(),step(-.125),read,n.op(82,0,1,5,0,0),step(0),step(1/60))),
        ('zero-hertz-positive-dt',(n.g.world(),tune(0),step(1/60,True),read,tune(30),step(0,True),step(1/60,True))),
        ('zero-hertz-restored-before-step',(n.g.world(),tune(0),tune(30),step(1/60,True))),
    )


def native(runtime):
    result={'code':1,'full_ownership_acceptance':False,'native_product_mutants':0,
            'baseline_pairs':0,'stand_controls':0,'failed_controls':0,'fixtures':[],'controls':[],'errors':[],
            'positive_steps_per_side':4,'raw_negative_steps_per_side':1,'zero_steps_per_side':2}
    collected=[]
    for name,operations in fixtures():
        sides={};outputs={};packets={}
        for side in ('C','D'):
            try:
                code,output,error,meta=runtime.run(side,n.encode(operations,side=='D'),'GUARD12')
                m.require(not code and not error,'named domain native code/stderr')
                header=n.encode(operations).split(b'O 1 ',1)[0]+f'CASE 1 {len(operations)}\n'.encode('ascii')
                m.require(output.startswith(header),'domain exact GUARD/GA/CASE framing')
                policy=DomainPolicy(name);current=[];frames=[]
                                                                                   
                for line in output.decode('ascii').splitlines(keepends=True):
                    tag,v=m.parse(line)
                    if tag=='CASE':m.require(v==(1,len(operations)),'domain CASE')
                    elif tag=='E':
                        if current:
                            seq=len(frames)+1;policy.check(seq,operations[seq-1],current);frames.append(tuple(current))
                        current=[(tag,v)]
                    elif current and tag not in ('ENDCASE','END'):current.append((tag,v))
                    elif tag=='ENDCASE':
                        seq=len(frames)+1;policy.check(seq,operations[seq-1],current);frames.append(tuple(current));current=[]
                m.require(len(frames)==len(operations) and output.endswith(b'END 1\n'),'domain full EOF/history')
                canonical=header+''.join(m.format_record(t,v) for packet in frames for t,v in packet).encode('ascii')+b'ENDCASE 1\nEND 1\n'
                m.require(output==canonical,'domain complete canonical stream, no extra record')
                outputs[side]=output;packets[side]=frames
                sides[side]={'ok':True,'run':meta,'bytes':len(output),'sha256':hashlib.sha256(output).hexdigest(),
                             'allowed_snapshots':policy.allowed_snapshots}
            except Exception as exc:sides[side]={'ok':False,'error':str(exc)}
        ok=len(outputs)==2 and outputs['C']==outputs['D']
        result['baseline_pairs']+=int(ok);result['fixtures'].append({'name':name,'ok':ok,'sides':sides})
        if ok:collected.append((name,operations,packets))
    if collected:
        name,operations,packets=collected[0]
                                                                               
        for label,seq,field,value in (
            ('NaN',2,8,0x7fc00000),('negative-infinity',2,8,0xff800000),
            ('finite-instead-of-required-infinity',2,8,0),('other-field-infinity',2,3,0x7f800000),
            ('lost-persistent-infinity',4,8,0)):
            checked={}
            for side,frames in packets.items():
                policy=DomainPolicy(name);rejected=False
                try:
                    for at,packet in enumerate(frames,1):
                        bad=list(packet)
                        if at==seq:
                            j=next(j for j,(t,v) in enumerate(bad) if t=='W10')
                            v=list(bad[j][1]);v[field]=value;bad[j]=('W10',tuple(v))
                        policy.check(at,operations[at-1],bad)
                except ValueError:
                    rejected=bool(policy.failure and policy.failure['seq']==seq)
                poisoned=False
                if policy.failure:
                    try:policy.check(1,operations[0],frames[0])
                    except ValueError as exc:poisoned='history unavailable' in str(exc)
                checked[side]={'ok':rejected and poisoned,'failure':policy.failure,'poisoned':poisoned}
            ok=all(v['ok'] for v in checked.values());result['stand_controls']+=1
            result['failed_controls']+=int(not ok);result['controls'].append({'name':label,'sides':checked,'ok':ok})
    result['code']=int(result['baseline_pairs']!=3 or result['stand_controls']!=5 or bool(result['failed_controls']))
    return result
