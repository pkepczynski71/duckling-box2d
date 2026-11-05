pass                                                                       

                                                                            
                                                                  
   
import argparse
from collections import Counter, deque
import io
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys
import time

import importlib.util
def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
g=load('world_motion_inputs','przypadki-ruch-swiata.py')
base=load('world_motion_shape_comparison','porownaj-ksztalty.py')
storage=load('world_motion_stream_storage','zapis-strumieni.py')
g.w6=g.g7.w6
HANDLE,MASS,AABB,OBJECT,BODY=base.HANDLE,base.MASS,base.AABB,base.OBJECT,base.BODY
Obj,halves,check_equal=base.Obj,base.halves,base.check_equal
pair_arguments,geometry_refusal=base.pair_arguments,base.geometry_refusal
s12_refusal,s12_change_refusal=base.s12_refusal,base.s12_change_refusal
expected_geometry_type=base.expected_geometry_type
Invalid=base.Invalid
FIELDS={k:v for k,v in base.FIELDS.items() if k not in ('PORT7','J','I','Z')}
FIELDS.update({
 'PORT8':('N',),
 'UP':('id','seq',*(f'{s}.{x}' for s in ('shapeA','shapeB') for x in ('slot','birth.low','birth.high','owner.low','owner.high'))),
 'QGN':('id','seq','phase','count'),
 'QG':('id','seq','phase','j',*HANDLE),
 'SB':('id','seq','status','has',*HANDLE),
 'K':('id','seq','worldSlot','dt','requestedSubSteps','effectiveSubSteps','didSolve','moveCount'),
 'M':('id','seq','worldSlot','j',*HANDLE[:3],'position.x','position.y','rotation.c','rotation.s',*OBJECT,'fellAsleep'),
 'MCN':('id','seq','copySlot','count'),
 'MC':('id','seq','copySlot','j','body.slot','body.birth.low','body.birth.high','body.owner.low','body.owner.high',
       'position.x','position.y','rotation.c','rotation.s',*OBJECT,'fellAsleep'),
 'Y':('id','seq','bodySlot','force.x','force.y','torque','deltaPosition.x','deltaPosition.y','deltaRotation.c','deltaRotation.s',
      'sim.isSpeedCapped','body.isSpeedCapped','bodyMoveIndex','setIndex','localIndex','linearDamping','angularDamping','gravityScale','allowFastRotation','isFast'),
 'DN':('id','seq','worldSlot','j',*HANDLE[:3]),
 'RT':('id','seq','worldSlot','treeType','root','nodeCount','nodeCapacity','freeList','proxyCount','height','areaRatio',*(f'rootAABB.{x}' for x in AABB)),
 'JW':('id','seq','worldSlot','stepIndex.low','stepIndex.high','inv_h','locked','endEventArrayIndex','bodyMoveEvents.count','movePairCapacity','movePairIndex'),
 'I8':('id','seq','nX','nP','nT','nF','nU','nH','nY','nDN','nRT','nJW'),
 'Z8':('id','seq','savedWorlds','savedBodies','savedShapes','liveWorlds','liveBodies','liveShapes',
       'nE','nR','nUP','nV','nW','nB','nS','nG','nL','nA','nQ','nK','nM','nMCN','nMC','nQGN','nQG','nSB','lastIssued.low','lastIssued.high'),
})
DECIMALS={k:base.DECIMALS.get(k,0) for k in FIELDS}
DECIMALS.update(PORT8=1,UP=2,QGN=3,QG=4,SB=2,K=3,M=4,MCN=3,MC=4,Y=3,DN=4,RT=4,JW=3,I8=2,Z8=2)
PRIVATE=frozenset(('X','P','T','F','U','H','Y','DN','RT','JW','I8'))
MAX_LINE=65536
PUBLIC_COUNTS=('E','R','UP','V','W','B','S','G','L','A','Q','K','M','MCN','MC','QGN','QG','SB')

def location(tag,v):
    cid=v[0] if tag not in ('PORT8','END') and v else 0
    seq=v[1] if tag not in ('PORT8','CASE','ENDCASE','END') and len(v)>1 else 0
    extra=''
    if 'Slot' in ''.join(FIELDS.get(tag,())) and len(v)>2: extra+=f', slot {v[2]}'
    if tag in ('M','MC','DN','QG','U') and len(v)>3: extra+=f', j {v[3]}'
    return f'id {cid}, seq {seq}{extra}, record {tag}'

def error(tag,v,name,detail):
    raise Invalid(f'{location(tag, v)}, field {name}: {detail}')

def check_equal(tag,v,index,expected):
    for j,wanted in enumerate(expected):
        if v[index+j]!=wanted:error(tag,v,names_for(tag,v)[index+j],f'{v[index + j]:08x} zamiast {wanted:08x}')

def names_for(tag,v):
    if tag in ('L','Q','H'): return base.names_for(tag,v)
    return FIELDS[tag]

def parse_record(line):
    if len(line)>MAX_LINE:raise Invalid('Ea56145270ce6 0, E4f5260d71c7e 0, record E6694ea807500, field E971a9c469cb2: E526fe1539fe4 Ed8ac4a470cb0 65536 Ea9fec58e15e1')
    if not line.isascii() or not line.endswith('\n') or '\r' in line:
        raise Invalid('Ea56145270ce6 0, E4f5260d71c7e 0, record E6694ea807500, field Ebc39040aa269: expected ASCII Ede7d1b721a1e LF')
    ts=line[:-1].split(' ');tag=ts[0]
    if tag not in FIELDS: raise Invalid('id 0, seq 0, record transport, field tag: '+repr(tag))
    v=[]
    for i,t in enumerate(ts[1:]):
        dec=i<DECIMALS[tag]
        if not (g.DEC if dec else g.HEX).fullmatch(t): error(tag,v,FIELDS[tag][i] if i<len(FIELDS[tag]) else str(i),'E2e398c23d2bf E11fd9b8cd5c2')
        n=int(t,10 if dec else 16)
        if n>g.U32: error(tag,v,str(i),'ponad u32')
        v.append(n)
    if len(v)<len(FIELDS[tag]) or len(v)!=len(names_for(tag,v)): error(tag,v,'długość','niezgodna z kontraktem')
    return tag,tuple(v)

def format_record(tag,v):
    return tag+' '+' '.join(str(x) if i<DECIMALS[tag] else f'{x:08x}' for i,x in enumerate(v))+'\n'

class Reader:
    def __init__(self,source):
        self.stream=io.StringIO(source) if isinstance(source,str) else source
        self.counts=Counter();self.lines=0;self.window=deque(maxlen=7)
    def take(self,tag,prefix=(),expected=None):
        line=self.stream.readline(MAX_LINE+1);self.lines+=1;self.window.append(line[:8192])
        if not line: error(tag,prefix,'rekord','missing / E446efde3d38b E8f42f9f9f5d4')
        actual,v=parse_record(line)
        if actual!=tag: error(tag,prefix,'kolejność','otrzymano '+actual)
        for i,x in enumerate(prefix):
            if v[i]!=x: error(tag,v,names_for(tag,v)[i],f'{v[i]} zamiast {x}')
        if expected is not None:
            if len(v)!=len(expected): error(tag,v,'długość','niezgodna z modelem')
            for i,(x,y) in enumerate(zip(v,expected)):
                if y is not None and x!=y: error(tag,v,names_for(tag,v)[i],f'{x:08x} zamiast {y:08x}')
        self.counts[tag]+=1
        return v
    def end(self):
        if self.stream.read(1): raise Invalid('id 0, seq 0, record END, field nadmiar: dodatkowe dane')

class Life(base.Life):
    def begin(self):
        super().begin();self.copies={};self.outcome={};self.operation_start=Counter()
    def create_world(self,slot,a):
        w=super().create_world(slot,a)
        if w is not None:
            w.dense={0:[],2:[]};w.steps=0;w.inv_h=0;w.end_index=0;w.move_count=0
        return w
    def create_body(self,slot,w,a):
        b=super().create_body(slot,w,a)
        w.dense[0 if a[2]==0 else 2].append(b)
        b.motion=tuple(a[11:15]) if len(a)>=16 and a[5] is not None else (0,0,g.bits(1),0)
        b.zero_motion=all(g.number(a[i])==0 for i in (7,8,9))
        return b
    def destroy(self,o):
        if o.kind==2:
            dense=o.world.dense[0 if o.args[2]==0 else 2];i=dense.index(o)
            dense[i]=dense[-1];dense.pop()
        super().destroy(o)

def valid_body(a):
    return (all(math.isfinite(g.number(a[i])) for i in (*range(3,10),11,12,13))
            and g.w6.valid_rotation(g.number(a[5]),g.number(a[6]))
            and g.number(a[11])>=0 and g.number(a[12])>=0)

def valid_step(a):
    dt=g.number(a[1]);n=g.signed(a[2])
    if not math.isfinite(dt) or dt<0 or n<=0:return False
    if dt==0:return True
    inv=g.w6.f32(1/dt);h=g.w6.f32(dt/n);invh=g.w6.f32(g.w6.f32(n)*inv)
    return h>0 and all(math.isfinite(x) for x in (inv,h,invh))

def operation(model,reader,cid,seq,row,guard=False):
    model.operation_start=reader.counts.copy()
    code,*aa=row;a=tuple(aa)
    if code<30:
        result=base.operation(model,reader,cid,seq,row)
                                                                               
        if not result[0] and code in (2,16): model.get(2,a[0]).motion=(0,0,g.bits(1),0)
        model.outcome={'status':result[0]}
        return result
    reader.take('E',(cid,seq),(cid,seq,*row))
    status=0;o=None;w=None;target=None
    model.outcome={}
    if code==37:
        if a[0] not in model.copies: raise Invalid('unsaved copy register')
    else:
        w=model.get(1,a[1] if code==30 else a[0])
        if code in (33,34,35,36,38):target=model.get(2,a[1])
        if code==39:target=model.get(3,a[1])
        status=model.guard(w,target)
        if code==30:
            model.target_free(2,a[0])
            if not status and a[15] and not valid_body(a):status=5
            if not status and model.last==g.U64:status=3
            if not status:o=model.create_body(a[0],w,a)
        elif code in (31,32):
            o=w;dt=g.number(a[1]);n=g.signed(a[2])
            if not status and code==32 and not valid_step(a):status=5
                                                                             
                                                                    
            if not status and guard and dt!=0:
                family=cid+56
                if family<=58 or w.steps>=1:status=6
            if not status:
                if dt>0:w.steps+=1
                w.end_index=1-w.end_index
                if dt!=0:
                    w.inv_h=g.bits(g.w6.f32(g.w6.f32(n if n>0 else 1)*g.w6.f32(1/dt))) if dt>0 else 0
                w.move_count=len(w.dense[2]) if dt>0 else 0
                if code==32:model.copies.setdefault(a[3],())
        else:
            o=target
            game=code==34 or (code==35 and a[4]) or (code==36 and a[3])
            fields=range(3,7) if code==34 else (2,3) if code==35 else (2,) if code==36 else ()
            if not status and game and not all(math.isfinite(g.number(a[i])) for i in fields):status=5
            if not status and code in (33,34,35,36):target.zero_motion=False
    model.outcome={'status':status,'world':w,'target':target}
    reader.take('R',(cid,seq,0),(cid,seq,0,status,o.kind if o else 0,*(o.handle() if o else (0,)*9)))
    if status==6:
        up=reader.take('UP',(cid,seq));pair=[]
        for start in (2,7):
            slot,blo,bhi,olo,ohi=up[start:start+5]
            matches=[s for s in w.current_s.values() if s.index-1==slot and halves(s.birth)==(blo,bhi) and halves(w.birth)==(olo,ohi)]
            if len(matches)!=1:error('UP',up,'shape','not a live ticket')
            pair.append(matches[0])
        if pair[0] is pair[1]:error('UP',up,'shapeB','same shape')
        if guard:
                                                                         
                                                                              
            expected=(model.get(3,0),model.get(3,1))
            payload=tuple(x for s in expected for x in (s.index-1,*halves(s.birth),*halves(w.birth)))
            check_equal('UP',up,2,payload)
        model.outcome['pair']=pair
    return status,1,0,None

def public8(model,reader,cid,seq,live,bvals,svals,state,row):
    code,*a=row;out=model.outcome;status=out['status']
    if code==38:
        b=out['target'];children=b.children if not status else []
        original=tuple(s.handle() for s in children)
        phases=3 if not status and a[2] else 1
        for phase in range(phases):
            expected=list(original)
            if phase==1 and expected:
                expected.append(expected[0])
                if len(original)>=2:expected[0],expected[1]=expected[1],expected[0]
            reader.take('QGN',(cid,seq,phase),(cid,seq,phase,len(expected)))
            for j,h in enumerate(expected):reader.take('QG',(cid,seq,phase,j),(cid,seq,phase,j,*h))
    if code==39:
        h=out['target'].parent.handle() if not status else (0,)*9
        reader.take('SB',(cid,seq),(cid,seq,status,int(not status),*h))
        if not status:
            shape_slot=next(slot for slot,s in live[3] if s is out['target'])
            check_equal('S',svals[shape_slot],12,h[:3])
    if code in (31,32):
        w=out['world'];dt=g.number(a[1]);n=g.signed(a[2]);solved=not status and dt>0
        dense=w.dense[2] if solved else []
        reader.take('K',(cid,seq,a[0]),(cid,seq,a[0],a[1],a[2],0 if status or dt==0 else max(1,n),int(solved),len(dense)))
        copied=[]
        for j,b in enumerate(dense):
            slot=next(slot for slot,obj in live[2] if obj is b);bv=bvals[slot]
            m=reader.take('M',(cid,seq,a[0],j),(cid,seq,a[0],j,*b.handle()[:3],*bv[13:17],*b.object_id,0))
            copied.append((b.index-1,*halves(b.birth),*halves(w.birth),*m[7:]))
        if code==32 and not status:model.copies[a[3]]=tuple(copied)
    dest=a[0] if code==37 else a[3] if code==32 and not status else None
    if dest is not None:
        copy=model.copies[dest]
        reader.take('MCN',(cid,seq,dest),(cid,seq,dest,len(copy)))
        for j,e in enumerate(copy):reader.take('MC',(cid,seq,dest,j),(cid,seq,dest,j,*e))

def private8(model,reader,cid,seq,live,bvals,state,row):
    code,*a=row
    for slot,b in live[2]:
        v=reader.take('Y',(cid,seq,slot));state[('Y',slot)]=v[3:]
        setindex=0 if b.args[2]==0 else 2
        check_equal('Y',v,13,(setindex,b.world.dense[setindex].index(b),*b.motion))
        check_equal('Y',v,6,(0,0,g.bits(1),0))
        if b.args[2]==0:check_equal('Y',v,3,(0,0,0))
        if code in (31,32) and not model.outcome['status'] and g.number(a[1])>0 and b.world is model.outcome['world'] and setindex==2:
            check_equal('Y',v,3,(0,0,0));check_equal('Y',v,10,(0,));check_equal('Y',v,12,(b.world.dense[2].index(b),))
            if b.zero_motion and all(g.number(x)==0 for x in b.world.args[:2]):check_equal('Y',v,11,(0,))
            if b.world.steps==1 and cid in (19,20,21) and slot in (0,1,2):check_equal('Y',v,11,(int(slot==2),))
            if b.world.steps==1 and cid in (22,23,24) and slot in (0,1,2,4,5):check_equal('Y',v,11,(int(slot==2),))
        if v[10]>1 or v[11]>1 or v[19]>1: error('Y',v,'flag','not boolean')
        if v[19]!=0:error('Y',v,'isFast','CCD disabled')
    for slot,w in live[1]:
        for j,b in enumerate(w.dense[2]):reader.take('DN',(cid,seq,slot,j),(cid,seq,slot,j,*b.handle()[:3]))
    for slot,w in live[1]:
        for typ in range(3):
            v=reader.take('RT',(cid,seq,slot,typ));state[('RT',slot,typ)]=v[4:]
            count=sum(s.parent.args[2]==typ for s in w.current_s.values())
            check_equal('RT',v,8,(count,))
            if v[6]<16 or v[5]!=(2*count-1 if count else 0):error('RT',v,'nodeCount','not a full binary tree')
            if count:
                bound=list(map(g.number,v[11:15]))
                for ss,s in live[3]:
                    if s.world is w and s.parent.args[2]==typ:
                        fat=list(map(g.number,state[('P',ss)][7:11]))
                        if not(bound[0]<=fat[0] and bound[1]<=fat[1] and bound[2]>=fat[2] and bound[3]>=fat[3]):error('RT',v,'rootAABB','omits a leaf')
    for slot,w in live[1]:
        v=reader.take('JW',(cid,seq,slot));state[('JW',slot)]=v[3:]
        check_equal('JW',v,3,(*halves(w.steps),w.inv_h,0,w.end_index,w.move_count))


def snapshot(model,reader,cid,seq,private,nR,nJ,capacity,row):
    live={k:[(slot,o) for slot,o in sorted(model.reg[k].items()) if model.live(o)] for k in (1,2,3)}
    for kind in (1,2,3):
        for slot,o in sorted(model.reg[kind].items()):
            reader.take('V',(cid,seq,kind,slot),(cid,seq,kind,slot,model.raw_valid(o),int(model.live(o))))
    state={}; bvals={}; svals={}; pvals={}; tvals={}; shape_slots={id(o):slot for slot,o in live[3]}
    def take(tag,slot):
        v=reader.take(tag,(cid,seq,slot)); state[(tag,slot)]=v[3:]; return v
    for slot,w in live[1]:
        v=take('W',slot); h=w.handle()
        check_equal('W',v,3,(*h[:5],*h[7:9],*w.args,len(w.current_b),len(w.current_s),sum(b.args[2]!=0 for b in w.current_b.values())))
    for slot,b in live[2]:
        v=take('B',slot); bvals[slot]=v
        check_equal('B',v,3,b.handle()); check_equal('B',v,12,(b.args[2],))
        check_equal('B',v,26,(len(b.children),int(b.args[2]!=0),1,b.args[10],*b.object_id))
        if b.args[2]!=2 or b.args[10]: check_equal('B',v,23,(0,))
        if b.args[2]!=2: check_equal('B',v,22,(0,))
        if b.args[2]==0:
            check_equal('B',v,13,b.args[3:7]); check_equal('B',v,19,(0,0,0))
    for slot,s in live[3]:
        v=take('S',slot); svals[slot]=v; a=s.shape_args; h=s.handle()
        check_equal('S',v,3,h); check_equal('S',v,12,s.parent.handle()[:3]); check_equal('S',v,15,s.world.handle()[:3])
        check_equal('S',v,18,(expected_geometry_type(s),s.density,g.bits(.6),0,0,0,0,0,*a[7:12],0))
        check_equal('S',v,40,s.object_id)
        if expected_geometry_type(s)==2: check_equal('S',v,32,(0,0,0,0))
        elif g.number(s.density)==0:
                                                                           
                                                                
            check_equal('S',v,32,(s.density,))
            if expected_geometry_type(s)==0 or s.density==0:
                check_equal('S',v,35,(s.density,))
    for slot,s in live[3]:
        v=take('G',slot); typ=expected_geometry_type(s)
        if v[3]!=typ: error('G',v,'h0','E2d64329465af Ec2d78d2c1f3a E5a5538c7c55f')
        count=1 if typ==0 else 2 if typ in (1,2) else s.shape_args[15] if s.shape_args[3]==3 else 4
        check_equal('G',v,4,(count,))
        if typ!=3: check_equal('G',v,6,(0,0))
        check_equal('G',v,8+2*count,(0,)*(16-2*count))
        if typ!=3: check_equal('G',v,24,(0,)*16)
        else: check_equal('G',v,24+2*count,(0,)*(16-2*count))
        check_equal('G',v,40,(0,0,0))
        a=s.shape_args; geo=a[15:55]
        if a[3]==0: check_equal('G',v,5,(geo[2],0,0,*geo[:2]))
        elif a[3]==1 and typ==1: check_equal('G',v,5,(geo[4],0,0,*geo[:4]))
        elif a[3]==1 and typ==0:
            midpoint=tuple(g.bits(g.w6.f32(g.w6.f32(.5*g.number(geo[j]))+g.w6.f32(.5*g.number(geo[j+2])))) for j in (0,1))
            check_equal('G',v,5,(geo[4],0,0,*midpoint))
        elif a[3]==2: check_equal('G',v,5,(0,0,0,*geo[:4]))
        elif a[3]==3: check_equal('G',v,5,(geo[1],)); check_equal('G',v,8,geo[2:2+2*count])
    for slot,b in live[2]:
        v=take('L',slot); raw=tuple(x for s in b.children for x in s.handle()[:3])
        check_equal('L',v,3,(len(b.children),*raw)); v=take('A',slot)
        if not b.children: check_equal('A',v,3,(*bvals[slot][13:15],*bvals[slot][13:15]))
        else:
            union=list(svals[shape_slots[id(b.children[0])]][36:40])
            for child in b.children[1:]:
                bound=svals[shape_slots[id(child)]][36:40]
                union=[x if (g.number(x)<g.number(y) if i<2 else g.number(x)>g.number(y)) else y
                       for i,(x,y) in enumerate(zip(union,bound))]
            check_equal('A',v,3,union)
    if capacity is not None:
        b=model.get(2,row[2]); v=take('Q',row[2]); children=b.children[:capacity]
        check_equal('Q',v,3,(capacity,len(children),*(x for s in children for x in s.handle()[:3])))
    public8(model,reader,cid,seq,live,bvals,svals,state,row)
    if private:
        for slot,b in live[2]:
            v=take('X',slot)
            if b.args[2]!=2: check_equal('X',v,3,(0,0))
            if b.args[10]: check_equal('X',v,4,(0,))
            check_equal('X',v,9,tuple(bvals[slot][15:17]))
            if b.args[2]!=0 and b.mass_current:
                minimum,maximum=map(g.number,v[5:7]);lc=list(map(g.number,bvals[slot][24:26]))
                for child in b.children:
                    geometry=state[('G',shape_slots[id(child)])]
                    typ,count,radius=geometry[:3];radius=g.number(radius)
                    if typ in (0,1) and minimum>radius:
                        error('X',v,'minExtent','omits a circle/capsule, including density zero')
                    if typ==2 and minimum!=0:
                        error('X',v,'minExtent','omits a segment, including density zero')
                    for k in range(count):
                        px,py=map(g.number,geometry[5+2*k:7+2*k])
                        dx=g.w6.f32(px-lc[0]);dy=g.w6.f32(py-lc[1])
                        dd=g.w6.f32(g.w6.f32(dx*dx)+g.w6.f32(dy*dy))
                        distance=g.w6.f32(g.w6.f32(math.sqrt(dd))+radius)
                        if maximum<distance:
                            error('X',v,'maxExtent','omits geometry, including density zero')
        for slot,s in live[3]:
            v=take('P',slot); pvals[slot]=v
            i=s.parent.children.index(s); ch=s.parent.children
            check_equal('P',v,3,(s.index-1,s.parent.index-1,ch[i-1].index-1 if i else g.U32,ch[i+1].index-1 if i+1<len(ch) else g.U32))
            check_equal('P',v,14,(0,))
            fat=list(map(g.number,v[10:14])); aa=list(map(g.number,svals[slot][36:40]))
            if not (fat[0]<=aa[0] and fat[1]<=aa[1] and fat[2]>=aa[2] and fat[3]>=aa[3]):
                error('P',v,'fatAABB','nie obejmuje AABB')
        for slot,s in live[3]:
            v=take('T',slot); tvals[slot]=v; p=pvals[slot]; a=s.shape_args
            check_equal('T',v,3,(s.parent.args[2],p[7]>>2,*p[10:14],*a[7:9],s.index-1,0))
            if p[7]&3 != s.parent.args[2]: error('P',p,'proxyKey','E2d64329465af E5a5538c7c55f E930e79f4d2d2')
        nu=0
        for slot,w in live[1]:
            v=take('F',slot); moves=v[3]
            check_equal('F',v,4,tuple(sum(s.parent.args[2]==kind for s in w.current_s.values()) for kind in range(3))+(0,))
            proxy_keys={pvals[ss][7] for ss,s in live[3] if s.world is w}
            if moves>len(proxy_keys): error('F',v,'moveCount','E3c42d9ac9807 multiple E41214554b66d')
            order=[]
            for j in range(moves):
                u=reader.take('U',(cid,seq,slot,j)); order.append(u[4]); state[('U',slot,j)]=u[4:]; nu+=1
            if len(set(order))!=len(order) or not set(order)<=proxy_keys: error('F',v,'moveCount','duplikat / martwe proxy')
            for kind in (0,1):
                h=reader.take('H',(cid,seq,slot,kind)); state[('H',slot,kind)]=h[4:]
                items=[h[i:i+3] for i in range(6,len(h),3)]; occupied=[x for x in items if x[2]]
                if any((x[0]==0 and x[1]==0)!=(x[2]==0) for x in items): error('H',h,'items','key/hash empty marker mismatch')
                if len(occupied)!=h[5] or len({x[:2] for x in occupied})!=h[5]: error('H',h,'count','E1a8ede14b808 E00409fe293d8 E4faff4509183')
                keys={x[0]|x[1]<<32 for x in occupied}
                if keys!=({key+1 for key in order} if kind==0 else set()): error('H',h,'items','E7bee5016cdbb E913d3b4475ff E32f30ea0e83c Ed32cef4de28c')
                if any(x[1] for x in occupied) and kind==0: error('H',h,'keyHigh','klucz motion ponad u32')
        private8(model,reader,cid,seq,live,bvals,state,row)
        reader.take('I8',(cid,seq),(cid,seq,len(live[2]),len(live[3]),len(live[3]),len(live[1]),nu,2*len(live[1]),len(live[2]),sum(len(w.dense[2]) for _,w in live[1]),3*len(live[1]),len(live[1])))
    saved=[len(model.reg[k]) for k in (1,2,3)]; lengths=[len(live[k]) for k in (1,2,3)]
    counts=reader.counts-model.operation_start
    reader.take('Z8',(cid,seq),(cid,seq,*saved,*lengths,*(counts[t] for t in PUBLIC_COUNTS),*halves(model.last)))
    if lengths[0]>2 or lengths[1]>65 or lengths[2]>130: raise Invalid('corpus live limits')
    return state


def validate_output(source,rows,private=True,initial_ticket=0,guard=False):
    reader=Reader(source);model=Life(initial_ticket);reader.take('PORT8',expected=(len(rows),))
    for c in rows:
        model.begin();reader.take('CASE',expected=(c.id,len(c.ops)));previous=None
        for seq,row in enumerate(c.ops,1):
            status,nR,nJ,capacity=operation(model,reader,c.id,seq,row,guard)
            state=snapshot(model,reader,c.id,seq,private,nR,nJ,capacity,row)
            if c.id in (53,54) and row[0]==31 and row[1]==1:
                                                                          
                                                                 
                for tag,skip in (('B',9),('S',15),('G',0),('A',0),('X',0),('P',0),('T',0),('Y',0),('F',0),('JW',0)):
                    if not private and tag in PRIVATE:continue
                    if state[(tag,0)][skip:]!=state[(tag,1)][skip:]:
                        error(tag,(c.id,seq,1),'raw clamp/n=1','different physical state')
            if previous is not None:
                old={k:v for k,v in previous.items() if k[0]!='Q'}
                new={k:v for k,v in state.items() if k[0]!='Q'}
                if status and old!=new:
                    key=next(k for k in (*old,*new) if old.get(k)!=new.get(k))
                    error(key[0],(c.id,seq,*key[1:]),'refusal','changed persistent state')
                if row[0] in (31,32) and not status and g.number(row[2])==0:
                    for key,value in old.items():
                        if key[0]!='JW' and new.get(key)!=value:error(key[0],(c.id,seq,*key[1:]),'Step0','changed persistent state')
                if row[0] in (5,14,21,37,38,39) and not status and old!=new:
                    key=next(k for k in (*old,*new) if old.get(k)!=new.get(k))
                    error(key[0],(c.id,seq,*key[1:]),'read','changed persistent state')
                if row[0]==15 and not status:
                    for key,value in old.items():
                        before=value[:-3] if key[0] in ('B','S') else value
                        now=new.get(key)
                        after=now[:-3] if key[0] in ('B','S') and now is not None else now
                        if before!=after:error(key[0],(c.id,seq,*key[1:]),'metadata','changed physics')
            previous=state
        reader.take('ENDCASE',expected=(c.id,));model.cleanup()
    reader.take('END',expected=(len(rows),));reader.end()
    return reader.counts

def bounded_lines(stream):
    if not hasattr(stream,'readline'):
        yield from stream
        return
    while True:
        line=stream.readline(MAX_LINE+1)
        if not line:return
        if len(line)>MAX_LINE:raise Invalid('Ea56145270ce6 0, E4f5260d71c7e 0, record E6694ea807500, field E971a9c469cb2: E526fe1539fe4 Ed8ac4a470cb0 65536 Ea9fec58e15e1')
        yield line

def public_lines(stream):
    for line in bounded_lines(stream):
        if line.split(' ',1)[0] not in PRIVATE:yield line

def first_difference(left,right,project=False,window=None):
    left=io.StringIO(left) if isinstance(left,str) else left
    right=io.StringIO(right) if isinstance(right,str) else right
    history=deque(maxlen=3)
    for line,(x,y) in enumerate(zip_longest(public_lines(left) if project else bounded_lines(left),bounded_lines(right)),1):
        if x==y:
            history.append(x[:8192]);continue
        if window is not None:
            window.update(line=line,before=list(history),left=x[:8192] if x else None,right=y[:8192] if y else None)
        if x is None or y is None:return 'Ea56145270ce6 0, E4f5260d71c7e 0, record END, field E971a9c469cb2: E78efd5a7a5b9 E6d0a271d4a15'
        tag,v=parse_record(x);other,vv=parse_record(y)
        if tag!=other:return location(tag,v)+', field record: '+other
        for name,a,b in zip(names_for(tag,v),v,vv):
            if a!=b:return location(tag,v)+f', field {name}: {a:08x} / {b:08x}'
        return location(tag,v)+', field bytes: E913d3b4475ff Ebc39040aa269'
    return None

def compare(c_text,d_text,rows,c_code=0,d_code=0,guard=False):
    errors=[]
    for name,source,code in (('C',c_text,c_code),('Duckling',d_text,d_code)):
        if code:errors.append(f'{name}: Ea56145270ce6 0, E4f5260d71c7e 0, record E6a47054c782f, field code: {code}')
        try:validate_output(source,rows,guard=guard)
        except (ValueError,IndexError,KeyError) as exc:errors.append(name+': '+str(exc))
    if not errors:
        diff=first_difference(c_text,d_text)
        if diff:errors.append(diff)
    return errors

def sha_manifest(path):
    pass                                                                     
    value=storage.manifest(path)
    return {key:value[key] for key in ('bytes','sha256','records','max_line_bytes')}

def measure(rows):
    pass                                                                   

                                                                            
                                                                          
       
    model=Life();counts=Counter();snapshot_count=0;step_count=0;bound=0
    class CounterReader:
        def __init__(self):self.counts=Counter()
        def take(self,tag,prefix=(),expected=None):
            self.counts[tag]+=1
            return expected
    reader=CounterReader()
    for c in rows:
        model.begin()
        for seq,row in enumerate(c.ops,1):
            operation(model,reader,c.id,seq,row)
            sizes=[sum(model.live(o) for o in model.reg[k].values()) for k in (1,2,3)]
            b,s=sizes[1:];cap=max(16,1<<(max(1,2*s)-1).bit_length())
            bound+=8192+1536*b+1536*s+27*(2*cap+64)
            snapshot_count+=1;step_count+=row[0] in (31,32)
            counts.update(V=sum(len(model.reg[k]) for k in (1,2,3)),W=sizes[0],B=b,S=s,G=s,L=b,A=b,X=b,P=s,T=s,Y=b,DN=sum(len(w.dense[2]) for w in model.current.values()),RT=3*sizes[0],JW=sizes[0],I8=1,Z8=1)
        model.cleanup()
    counts.update(reader.counts);counts.update(PORT8=1,CASE=len(rows),ENDCASE=len(rows),END=1)
    return {'source':'PUBLIC8','cases':len(rows),'operations':snapshot_count,'step_calls':step_count,
            'fixed_records':dict(sorted(counts.items())),'obs1_bytes_upper_bound':bound,
            'three_streams_bytes_upper_bound':3*bound,'absolute_stream_ceiling':1900000000}

def main():
    parser=argparse.ArgumentParser()
    for x in ('c','c-bez','duckling','wejscie','raport'):parser.add_argument('--'+x,type=Path,required=True)
    for x in ('kod-c','kod-c-bez','kod-wyjscia'):parser.add_argument('--'+x,type=int,required=True)
    parser.add_argument('--guard',action='store_true');parser.add_argument('--small',action='store_true')
    args=parser.parse_args();errors=[];manifests={};window={};started=time.monotonic()
    try:
        g.verify_input_hashes(args.wejscie.parent)
        expected=g.guard_cases() if args.guard else g.small_cases() if args.small else g.cases()
        rows=g.read_input(args.wejscie.read_bytes().decode('ascii'),expected_count=len(expected))
        if tuple(c.ops for c in rows)!=tuple(c.ops for c in expected):raise ValueError('corpus changed')
        decimal=args.wejscie.with_name(args.wejscie.stem+'-stdin.csv')
        paired=g.read_input(decimal.read_bytes().decode('ascii'),True,len(rows))
        if tuple(c.ops for c in rows)!=tuple(c.ops for c in paired):raise ValueError('paired words differ')
        for name,path,code,private in (('C OBS1',args.c,args.kod_c,True),('C OBS0',args.c_bez,args.kod_c_bez,False),('Duckling',args.duckling,args.kod_wyjscia,True)):
            if code:errors.append(f'{name}: Ea56145270ce6 0, E4f5260d71c7e 0, record E6a47054c782f, field code: {code}')
            manifests[name]=sha_manifest(path)
            if manifests[name]['bytes']>1900000000:errors.append(name+': stream size exceeds contract bound')
            with path.open(encoding='ascii',newline='') as source:
                try:
                    counts=validate_output(source,rows,private,guard=args.guard)
                    if dict(sorted(counts.items()))!=manifests[name]['records']:errors.append(name+': manifest count mismatch')
                except (ValueError,IndexError,KeyError) as exc:errors.append(name+': '+str(exc))
        for left,right,project in ((args.c,args.c_bez,True),(args.c,args.duckling,False)):
            with left.open(encoding='ascii',newline='') as a,right.open(encoding='ascii',newline='') as b:
                try:
                    diff=first_difference(a,b,project,window)
                    if diff:errors.append(diff)
                except (ValueError,IndexError) as exc:errors.append(str(exc))
    except (OSError,ValueError,IndexError,KeyError) as exc:errors.append('input / files: '+str(exc))
    result={'source':'GUARD8' if args.guard else 'PUBLIC8','errors':errors,'streams':manifests,
            'first_difference':window,'seconds':time.monotonic()-started}
    args.raport.with_suffix('.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    message='# FAIL\n\n'+'\n'.join(errors) if errors else f'# OK\n\nEe80e82d04457 E4d3de6062df4: {len(rows)}/{len(rows)}; E03b382aabe85 E4c7c5c0ffa17, Ef39441f51b35 Ede7d1b721a1e E32cee0cd54d4 OBS E13991feb1b0c.'
    args.raport.write_text(message+'\n',encoding='utf-8');print(message)
    return int(bool(errors))

if __name__=='__main__':sys.exit(main())
