pass                                                                              
import argparse
from collections import Counter
from dataclasses import dataclass, field
import importlib.util
import io
import math
from itertools import zip_longest
from pathlib import Path
import sys

_spec=importlib.util.spec_from_file_location('shape_inputs',Path(__file__).with_name('przypadki-ksztalty.py'))
g=importlib.util.module_from_spec(_spec); sys.modules[_spec.name]=g; _spec.loader.exec_module(g)
HANDLE=('index1','world0','generation','packed.low','packed.high','owner.low','owner.high','birth.low','birth.high')
MASS=('mass','center.x','center.y','rotationalInertia')
AABB=('lower.x','lower.y','upper.x','upper.y')
OBJECT=('object.has','object.low','object.high')
BODY=('type','position.x','position.y','rotation.c','rotation.s','worldCenter.x','worldCenter.y',
      'linearVelocity.x','linearVelocity.y','angularVelocity','mass','rotationalInertia','localCenter.x',
      'localCenter.y','shapeCount','isAwake','isEnabled','fixedRotation',*OBJECT)
FIELDS={
 'PORT7':('N',),'CASE':('id','opCount'),
 'E':('id','seq','opcode',*(f'a{i}' for i in range(64))),
 'J':('id','seq','j','phase',*HANDLE,'oldRawValid','oldGameValid','worldShapeCount','bodyShapeCount',*MASS),
 'R':('id','seq','resultIndex','status','kind',*HANDLE),
 'V':('id','seq','kind','slot','rawValid','gameValid'),
 'W':('id','seq','slot',*HANDLE[:5],'birth.low','birth.high','gravity.x','gravity.y','maximumLinearSpeed','bodyCount','shapeCount','islandCount'),
 'B':('id','seq','slot',*HANDLE,*BODY),
 'S':('id','seq','slot',*HANDLE,*(f'body.{x}' for x in HANDLE[:3]),*(f'world.{x}' for x in HANDLE[:3]),
      'shapeType','density','friction','restitution','rollingResistance','tangentSpeed','userMaterialId','customColor',
      'category.low','category.high','mask.low','mask.high','groupIndex','isSensor',*MASS,*(f'aabb.{x}' for x in AABB),*OBJECT),
 'G':('id','seq','slot',*(f'h{i}' for i in range(40))),
 'L':('id','seq','bodySlot','count'), 'A':('id','seq','bodySlot',*AABB),
 'Q':('id','seq','bodySlot','capacity','returnedCount'),
 'X':('id','seq','bodySlot','invMass','invInertia','minExtent','maxExtent','center0.x','center0.y','rotation0.c','rotation0.s'),
 'P':('id','seq','shapeSlot','id','bodyId','prevShapeId','nextShapeId','proxyKey','localCentroid.x','localCentroid.y',*(f'fatAABB.{x}' for x in AABB),'enlargedAABB'),
 'T':('id','seq','shapeSlot','treeType','proxyId',*(f'leafAABB.{x}' for x in AABB),'category.low','category.high','treeUserData.low','treeUserData.high'),
 'F':('id','seq','worldSlot','moveCount','staticProxyCount','kinematicProxyCount','dynamicProxyCount','pairCount'),
 'U':('id','seq','worldSlot','j','proxyKey'),
 'H':('id','seq','worldSlot','setKind','capacity','count'),
 'I':('id','seq','nX','nP','nT','nF','nU','nH'),
 'Z':('id','seq','savedWorlds','savedBodies','savedShapes','liveWorlds','liveBodies','liveShapes',
      'nE','nR','nV','nW','nB','nS','nG','nL','nA','nQ','nJ','lastIssued.low','lastIssued.high'),
 'ENDCASE':('id',),'END':('N',)}
DECIMALS={k:(1 if k in ('PORT7','END','ENDCASE') else 2 if k in ('CASE','I','Z') else
                  5 if k=='R' else 4 if k in ('J','V','U','H') else 3) for k in FIELDS}
PRIVATE=frozenset(('X','P','T','F','U','H','I'))

class Invalid(ValueError):
    pass


def location(tag, values):
    cid=values[0] if tag not in ('PORT7','END') and values else 0
    seq=values[1] if tag not in ('PORT7','CASE','ENDCASE','END') and len(values)>1 else 0
    extra=f', j {values[2]}, phase {values[3]}' if tag=='J' and len(values)>3 else ''
    if tag in ('W','B','S','G','L','A','Q','X','P','T','F','U','H') and len(values)>2:
        extra+=f', slot {values[2]}'
    return f'id {cid}, seq {seq}{extra}, record {tag}'


def error(tag, values, name, detail):
    raise Invalid(f'{location(tag, values)}, field {name}: {detail}')


def names_for(tag, values):
    names=FIELDS[tag]
    if tag in ('L','Q'):
        n=values[3 if tag=='L' else 4]
        if n>256:
            error(tag,values,'count','ponad 256')
        names+=tuple(f'shapes[{i}].{p}' for i in range(n) for p in HANDLE[:3])
    if tag=='H':
        cap=values[4]
        if cap<16 or cap>1024 or cap&(cap-1):
            error(tag,values,'capacity','E9f6e664b314e E13512bb12c29 Ea73c746364dd')
        names+=tuple(f'items[{i}].{p}' for i in range(cap) for p in ('low','high','hash'))
    return names


def parse_record(line):
    if not line.isascii() or not line.endswith('\n') or '\r' in line:
        raise Invalid('Ea56145270ce6 0, E4f5260d71c7e 0, record E6694ea807500, field Ebc39040aa269: expected ASCII Ede7d1b721a1e LF')
    ts=line[:-1].split(' '); tag=ts[0]
    if tag not in FIELDS:
        raise Invalid('id 0, seq 0, record transport, field tag: '+repr(tag))
    v=[]
    for i,t in enumerate(ts[1:]):
        dec=i<DECIMALS[tag]
        if not (g.DEC if dec else g.HEX).fullmatch(t):
            error(tag,v,FIELDS[tag][i] if i<len(FIELDS[tag]) else f'[{i}]','E2e398c23d2bf E11fd9b8cd5c2')
        n=int(t,10 if dec else 16)
        if n>g.U32:
            error(tag,v,f'[{i}]','ponad u32')
        v.append(n)
    if len(v)<len(FIELDS[tag]):
        error(tag,v,'długość','E3c42d9ac9807 E2300eca14adb record')
    names=names_for(tag,v)
    if len(v)!=len(names):
        error(tag,v,'długość',f'{len(v) + 1} zamiast {len(names) + 1}')
    return tag,tuple(v)


def format_record(tag,values):
    return tag+' '+' '.join(str(v) if i<DECIMALS[tag] else f'{v:08x}' for i,v in enumerate(values))+'\n'


def halves(v):
    return v&g.U32,v>>32


@dataclass
class Obj:
    kind:int
    index:int
    generation:int
    birth:int
    world:object=None
    parent:object=None
    live:bool=True
    args:tuple=()
    object_id:tuple=(0,0,0)
    children:list=field(default_factory=list)
    free_b:list=field(default_factory=list)
    free_s:list=field(default_factory=list)
    gens_b:dict=field(default_factory=dict)
    gens_s:dict=field(default_factory=dict)
    current_b:dict=field(default_factory=dict)
    current_s:dict=field(default_factory=dict)
    next_b:int=1
    next_s:int=1
    shape_args:tuple=()
    density:int=0
    mass_current:bool=True

    def handle(self):
        if self.kind==1:
            return self.index,0,self.generation,(self.index<<16)|self.generation,0,0,0,*halves(self.birth)
        return self.index,self.world.index-1,self.generation,((self.world.index-1)<<16)|self.generation,self.index,*halves(self.world.birth),*halves(self.birth)


class Life:
    pass                                                                      
    def __init__(self,last=0):
        self.last=last; self.current={}; self.world_gen=[0]*128; self.begin()
    def begin(self):
        self.reg={1:{},2:{},3:{}}
    def live(self,o):
        if o is None or not o.live:
            return False
        if o.kind==1:
            return self.current.get(o.index) is o
        return self.live(o.world) and (o.world.current_b if o.kind==2 else o.world.current_s).get(o.index) is o
    def raw_valid(self,o):
        if o.kind==1:
            cur=self.current.get(o.index)
        else:
            w=self.current.get(o.world.index)
            cur=(w.current_b if o.kind==2 else w.current_s).get(o.index) if w else None
        return int(cur is not None and cur.generation==o.generation)
    def guard(self,w,o=None):
        if not self.live(w):
            return 1
        if o is None:
            return 0
        if o.world.birth!=w.birth:
            return 2
        return 0 if self.live(o) else 1
    def create_world(self,slot,a):
        if self.last==g.U64:
            return None
        i=next(i for i in range(1,129) if i not in self.current)
        self.last+=1
        w=Obj(1,i,self.world_gen[i-1],self.last,args=tuple(a[1:4]))
        self.reg[1][slot]=self.current[i]=w
        return w
    def create_body(self,slot,w,a):
        i=w.free_b.pop() if w.free_b else w.next_b; w.next_b=max(w.next_b,i+1)
        gen=(w.gens_b.get(i,0)+1)&65535; w.gens_b[i]=gen; self.last+=1
        b=Obj(2,i,gen,self.last,world=w,args=tuple(a))
        self.reg[2][slot]=w.current_b[i]=b
        return b
    def create_shape(self,slot,b,a):
        w=b.world; i=w.free_s.pop() if w.free_s else w.next_s; w.next_s=max(w.next_s,i+1)
        gen=(w.gens_s.get(i,0)+1)&65535; w.gens_s[i]=gen; self.last+=1
        s=Obj(3,i,gen,self.last,world=w,parent=b,shape_args=tuple(a),density=a[4],object_id=tuple(a[12:15]))
        self.reg[3][slot]=w.current_s[i]=s; b.children.insert(0,s); b.mass_current=bool(a[5])
        return s
    def destroy(self,o):
        if o.kind==1:
            for b in list(o.current_b.values()):
                self.destroy(b)
            del self.current[o.index]; self.world_gen[o.index-1]=(o.generation+1)&65535
        elif o.kind==2:
            for s in list(o.children):
                self.destroy(s)
            del o.world.current_b[o.index]; o.world.free_b.append(o.index)
        else:
            o.parent.children.remove(o); del o.world.current_s[o.index]; o.world.free_s.append(o.index)
        o.live=False
    def get(self,kind,slot):
        if slot not in self.reg[kind]:
            raise Invalid(f'niezapisany rejestr kind {kind}, slot {slot}')
        return self.reg[kind][slot]
    def target_free(self,kind,slot):
        if slot in self.reg[kind] and self.live(self.reg[kind][slot]):
            raise Invalid(f'Ef2314669498c Edbeb5e67b753 E80b4e95db3b2 E0b27c158feb3 {kind}, slot {slot}')
    def cleanup(self):
        for _,w in sorted(self.reg[1].items()):
            if self.live(w):
                self.destroy(w)


def pair_arguments(a):
    ba=(a[0],a[2],a[3],*a[4:11],a[11],*([0]*53))
    sa=(a[1],a[2],a[0],a[12],a[13],1,a[14],*a[18:23],*a[15:18],*a[23:63],*([0]*9))
    assert len(ba)==len(sa)==64
    return ba,sa


def geometry_refusal(a, game=False):
    pass                                                                     

                                                                          
                                                                             
       
    tag=a[3]; geo=a[15:55]; f=[g.number(x) for x in geo]
    if g.number(a[4])<0:
        return True
    if tag==0:
        return f[2]<=0
    if tag==1:
        dx=g.w6.f32(f[2]-f[0]); dy=g.w6.f32(f[3]-f[1])
        dd=g.w6.f32(g.w6.f32(dx*dx)+g.w6.f32(dy*dy))
        return f[4]<=0 or (game and not math.isfinite(dd))
    if tag==2:
        dx=g.w6.f32(f[2]-f[0]); dy=g.w6.f32(f[3]-f[1])
        dd=g.w6.f32(g.w6.f32(dx*dx)+g.w6.f32(dy*dy))
        return dd<=g.w6.f32(g.w6.f32(.005)**2) or (game and not math.isfinite(dd))
    if tag==4:
        return f[0]<=0 or f[1]<=0 or f[6]<0
    if not 3<=geo[0]<=8 or f[1]<0:
        return True
                                                                      
                                                                           
    pts=[(f[2+2*i],f[3+2*i]) for i in range(geo[0])]
    for i,(x,y) in enumerate(pts):
        nx,ny=pts[(i+1)%len(pts)]
        if any((nx-x)*(py-y)-(ny-y)*(px-x)<=0
               for j,(px,py) in enumerate(pts) if j not in (i,(i+1)%len(pts))):
            return True
    return False


def s12_refusal(b,a):
    return (b.args[2]==2 and not b.args[10] and a[3]==0 and
            a[15:18]==(g.bits(16384),0,g.bits(.5)) and not b.children)


def s12_change_refusal(target, density=None):
    pass                                                              

                                                                          
                                                                            
                                                                            
       
    b=target.parent
    if b.args[2]!=2 or b.args[10]: return False
    future=[s for s in b.children if s is not target and g.number(s.density)!=0]
    if density is not None and g.number(density)!=0: future.append(target)
    return (len(future)==1 and future[0].shape_args[3]==0 and
            future[0].shape_args[15:18]==(g.bits(16384),0,g.bits(.5)))


class Reader:
    def __init__(self,source):
        self.stream=io.StringIO(source) if isinstance(source,str) else source
        self.counts=Counter(); self.lines=0
    def take(self,tag,prefix=(),expected=None):
        line=self.stream.readline(); self.lines+=1
        if not line:
            error(tag,prefix,'rekord','missing / E446efde3d38b E8f42f9f9f5d4')
        got,v=parse_record(line)
        if got!=tag:
            error(tag,prefix,'kolejność',f'otrzymano {got}')
        for i,x in enumerate(prefix):
            if v[i]!=x:
                error(tag,v,names_for(tag,v)[i],f'{v[i]} zamiast {x}')
        if expected is not None:
            for i,(x,y) in enumerate(zip(v,expected)):
                if y is not None and x!=y:
                    error(tag,v,names_for(tag,v)[i],f'{x:08x} zamiast {y:08x}')
            if len(v)!=len(expected):
                error(tag,v,'długość','niezgodna z modelem')
        self.counts[tag]+=1
        return v
    def end(self):
        if self.stream.read(1):
            raise Invalid('id 0, seq 0, record END, field nadmiar: dodatkowe dane')


def check_equal(tag,v,index,expected):
    if tuple(v[index:index+len(expected)])!=tuple(expected):
        for i,x in enumerate(expected):
            if v[index+i]!=x:
                error(tag,v,names_for(tag,v)[index+i],f'{v[index + i]:08x} zamiast {x:08x}')


def expected_geometry_type(s):
    a=s.shape_args; tag=a[3]
    if tag==4:
        return 3
    if tag==1:
        f=list(map(g.number,a[15:20])); dx=g.w6.f32(f[2]-f[0]); dy=g.w6.f32(f[3]-f[1])
        if g.w6.f32(g.w6.f32(dx*dx)+g.w6.f32(dy*dy))<=g.w6.f32(g.w6.f32(.005)**2):
            return 0
    return tag


def operation(model,reader,cid,seq,row):
    code,*aa=row; a=tuple(aa); r=model.reg
    reader.take('E',(cid,seq), (cid,seq,*row))
    status=0; results=[]; nJ=0; capacity=None
    if code==0:
        model.target_free(1,a[0]); o=model.create_world(a[0],a); status=0 if o else 3; results=[o]
    else:
        wi=a[1] if code==2 else a[2] if code==16 else a[1] if code in (10,17) else a[0]
        w=model.get(1,wi)
        target=None
        if code in (3,4,5,13,20,21):
            target=model.get(2,a[1])
        elif code in (11,12,14,18,19):
            target=model.get(3,a[1])
        elif code==15:
            target=model.get(a[1],a[2])
        elif code in (10,17):
            target=model.get(2,a[2])
        status=model.guard(w,target)
        if code==1:
            results=[w]
            if not status: model.destroy(w)
        elif code==2:
            model.target_free(2,a[0]); o=None
            if not status:
                if model.last==g.U64: status=3
                else: o=model.create_body(a[0],w,a)
            results=[o]
        elif code in (10,17):
            model.target_free(3,a[0]); o=None
            if not status and (geometry_refusal(a,code==17) or (code==17 and s12_refusal(target,a))): status=4
            if not status:
                if model.last==g.U64: status=3
                else: o=model.create_shape(a[0],target,a)
            results=[o]
        elif code==16:
            model.target_free(2,a[0]); model.target_free(3,a[1]); ba,sa=pair_arguments(a); b=s=None
            dummy=Obj(2,0,0,0,args=ba)
            if not status and (geometry_refusal(sa,True) or s12_refusal(dummy,sa)): status=4
            if not status and model.last>g.U64-2: status=3
            if not status:
                b=model.create_body(a[0],w,ba); b.object_id=tuple(a[15:18]); s=model.create_shape(a[1],b,sa)
            results=[b,s]
        elif code==20:
            old=model.get(3,a[4]); model.target_free(3,a[2])
            if status or model.live(old) or old.parent is not target:
                raise Invalid('CHURN lifecycle')
            sa=tuple(g.shape(a[2],wi,a[1])[1:])
            for j in range(1,a[3]+1):
                if j>1:
                    model.destroy(o)
                    reader.take('J',(cid,seq,j,0),(cid,seq,j,0,*o.handle(),model.raw_valid(old),int(model.live(old)),len(w.current_s),len(target.children),*((0,0,0,0) if target.args[2]!=2 or not target.children else (None,None,None,None))))
                    nJ+=1
                o=model.create_shape(a[2],target,sa)
                reader.take('J',(cid,seq,j,1),(cid,seq,j,1,*o.handle(),model.raw_valid(old),int(model.live(old)),len(w.current_s),len(target.children),*((0,0,0,0) if target.args[2]!=2 or not target.children else (None,None,None,None))))
                nJ+=1
            results=[o]
        else:
            results=[target]
            if not status:
                if code in (3,11,18):
                    if code==18 and s12_change_refusal(target): status=4
                    else:
                        if code in (11,18): target.parent.mass_current=code==18 or bool(a[2])
                        model.destroy(target)
                elif code==4:
                    ba=list(target.args); ba[3:7]=a[2:6]; target.args=tuple(ba)
                elif code==15: target.object_id=tuple(a[3:6])
                elif code in (12,19):
                    if g.number(a[2])<0 or (code==19 and s12_change_refusal(target,a[2])): status=4
                    else:
                        changed=g.number(target.density)!=g.number(a[2])
                        if code==19 or changed: target.parent.mass_current=code==19 or bool(a[3])
                                                                              
                                                                             
                        if changed: target.density=a[2]
                elif code==13: target.mass_current=True
                elif code==21: capacity=a[2]
    for index,o in enumerate(results):
        payload=o.handle() if o else (0,)*9
        kind=o.kind if o else 0
        reader.take('R',(cid,seq,index), (cid,seq,index,status,kind,*payload))
    return status,len(results),nJ,capacity


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
        check_equal('B',v,3,b.handle()); check_equal('B',v,12,(b.args[2],*b.args[3:7]))
        check_equal('B',v,26,(len(b.children),int(b.args[2]!=0),1,b.args[10],*b.object_id))
        if b.args[2]!=2 or b.args[10]: check_equal('B',v,23,(0,))
        if b.args[2]!=2: check_equal('B',v,22,(0,))
        if b.args[2]==0: check_equal('B',v,19,(0,0,0))
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
        if not b.children: check_equal('A',v,3,(*b.args[3:5],*b.args[3:5]))
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
        reader.take('I',(cid,seq),(cid,seq,len(live[2]),len(live[3]),len(live[3]),len(live[1]),nu,2*len(live[1])))
    saved=[len(model.reg[k]) for k in (1,2,3)]; lengths=[len(live[k]) for k in (1,2,3)]
    reader.take('Z',(cid,seq),(cid,seq,*saved,*lengths,1,nR,sum(saved),*lengths,lengths[2],lengths[1],lengths[1],int(capacity is not None),nJ,*halves(model.last)))
    if lengths[0]>4 or lengths[1]>128 or lengths[2]>256: raise Invalid('corpus live limits')
    return state


def check_review_mass(label,state,cid,seq):
    if label in ('B1.circle','B1.raw','B1.game'):
        expected=0x3fc90fdb if label=='B1.game' else 0x3f490fdb
        if state[('B',10)][19]!=expected:
            error('B',(cid,seq,10),'mass','R-7 B1 requires '+f'{expected:08x}')


def validate_output(source,rows,private=True,initial_ticket=0):
    reader=Reader(source); model=Life(initial_ticket); reader.take('PORT7',expected=(len(rows),))
    for c in rows:
        model.begin(); reader.take('CASE',expected=(c.id,len(c.ops))); previous=None
        witness=g.review_witnesses(); labels={}
        if c.id==1 and c.ops[-len(witness):]==tuple(row for _,row in witness):
            labels={len(c.ops)-len(witness)+i:name for i,(name,_) in enumerate(witness,1)}
        for seq,row in enumerate(c.ops,1):
            status,nR,nJ,capacity=operation(model,reader,c.id,seq,row)
            state=snapshot(model,reader,c.id,seq,private,nR,nJ,capacity,row)
            if status and previous is not None:
                                                                           
                                                                             
                old={k:v for k,v in previous.items() if k[0]!='Q'}
                new={k:v for k,v in state.items() if k[0]!='Q'}
                if old!=new:
                    ordered=(*old,*(k for k in new if k not in old))
                    key=next(k for k in ordered if old.get(k)!=new.get(k))
                    before,after=old.get(key),new.get(key)
                    prefix=(c.id,seq,*key[1:]);tag=key[0]
                    if before is None or after is None or len(before)!=len(after):
                        error(tag,prefix,'record','refusal changed persistent records')
                    field=next(i for i,(a,b) in enumerate(zip(before,after)) if a!=b)
                    values=(*prefix,*after)
                    error(tag,values,names_for(tag,values)[len(prefix)+field],'refusal changed persistent state')
            if row[0] in (5,14,21) and status==0 and previous is not None:
                for key,old in previous.items():
                    if key[0]!='Q' and state.get(key)!=old:
                        error(key[0],(c.id,seq,*key[1:]),'odczyt','read changed persistent state')
            if row[0]==15 and status==0 and previous is not None:
                for key,old in previous.items():
                    if key[0]=='Q': continue
                    new=state.get(key)
                    before=old[:-3] if key[0] in ('B','S') else old
                    after=new[:-3] if key[0] in ('B','S') and new is not None else new
                    if before!=after:
                        error(key[0],(c.id,seq,*key[1:]),'metadane','metadata changed physics')
            if 65<=c.id<=76 and seq==6 and row[0]==15:
                                                                             
                                                                         
                for tag,skip in (('B',9),('S',15),('G',0),('A',0),('X',0)):
                    if not private and tag=='X': continue
                    a=state[(tag,0)][skip:];b=state[(tag,1)][skip:]
                    if a!=b: error(tag,(c.id,seq,1),'pair/manual','different public construction results')
                                                                         
                                                                            
            if c.id==85 and seq==3 and row[0]==10:
                b=state.get(('B',0))
                if b is None or b[20]!=0:
                    error('B',(c.id,seq,0),'rotationalInertia','S12 witness not confirmed')
                if private and state[('X',0)][1]!=0x7f800000:
                    error('X',(c.id,seq,0),'invInertia','S12 witness must expose legacy +Inf')
            check_review_mass(labels.get(seq),state,c.id,seq)
            previous=state
        reader.take('ENDCASE',expected=(c.id,)); model.cleanup()
    reader.take('END',expected=(len(rows),)); reader.end()
    return reader.counts


def public_lines(stream):
    for line in stream:
        if line.split(' ',1)[0] not in PRIVATE:
            yield line


def first_difference(left,right,project=False):
    a=io.StringIO(left) if isinstance(left,str) else left
    b=io.StringIO(right) if isinstance(right,str) else right
    for x,y in zip_longest(public_lines(a) if project else a,b):
        if x==y: continue
        if x is None or y is None: return 'Ea56145270ce6 0, E4f5260d71c7e 0, record END, field E971a9c469cb2: E78efd5a7a5b9 E6d0a271d4a15'
        tag,v=parse_record(x); tt,vv=parse_record(y)
        if tt!=tag: return location(tag,v)+', field record: '+tt
        for name,q,r in zip(names_for(tag,v),v,vv):
            if q!=r: return location(tag,v)+f', field {name}: {q:08x} / {r:08x}'
        return location(tag,v)+', field bytes: E913d3b4475ff Ebc39040aa269'
    return None


def compare(c_text,d_text,rows,c_code=0,d_code=0):
    errors=[]
    for name,text,code in (('C',c_text,c_code),('Duckling',d_text,d_code)):
        if code: errors.append(f'{name}: Ea56145270ce6 0, E4f5260d71c7e 0, record E6a47054c782f, field code: {code}')
        try: validate_output(text,rows)
        except (ValueError,IndexError,KeyError) as exc: errors.append(name+': '+str(exc))
    if not errors:
        diff=first_difference(c_text,d_text)
        if diff: errors.append(diff)
    return errors


                                                                          
                                                                          
                                                                       
def measure(rows):
    model=Life();counts=Counter();public_size=private_size=0
    class CounterReader:
        def take(self,tag,prefix=(),expected=None):
            add(tag,expected if expected is not None else prefix)
            return expected
    def add(tag,values,variable=0):
        nonlocal public_size,private_size
        d=DECIMALS[tag]
        size=len(tag)+1+sum(1+len(str(x)) for x in values[:d])+9*(len(FIELDS[tag])-d+variable)
        counts[tag]+=1
        if tag in PRIVATE:private_size+=size
        else:public_size+=size
    reader=CounterReader();add('PORT7',(len(rows),))
    for c in rows:
        model.begin();add('CASE',(c.id,len(c.ops)));caps={}
        for seq,row in enumerate(c.ops,1):
            status,nR,nJ,capacity=operation(model,reader,c.id,seq,row)
            live={k:[(slot,o) for slot,o in sorted(model.reg[k].items()) if model.live(o)] for k in (1,2,3)}
            for kind in (1,2,3):
                for slot in sorted(model.reg[kind]):add('V',(c.id,seq,kind,slot))
            for slot,w in live[1]:add('W',(c.id,seq,slot))
            for slot,b in live[2]:add('B',(c.id,seq,slot))
            for tag in ('S','G'):
                for slot,s in live[3]:add(tag,(c.id,seq,slot))
            for slot,b in live[2]:
                add('L',(c.id,seq,slot),3*len(b.children));add('A',(c.id,seq,slot))
            if capacity is not None:
                b=model.get(2,row[2]);add('Q',(c.id,seq,row[2]),3*min(capacity,len(b.children)))
            for slot,b in live[2]:add('X',(c.id,seq,slot))
            for tag in ('P','T'):
                for slot,s in live[3]:add(tag,(c.id,seq,slot))
            for slot,w in live[1]:
                moves=len(w.current_s)
                if c.id in (37,49) and 3<=seq<=7:moves-=1
                if c.id==47 and 3<=seq<=4:moves-=1
                if moves<0:raise Invalid('forecast static witness')
                add('F',(c.id,seq,slot))
                for j in range(moves):add('U',(c.id,seq,slot,j))
                cap=caps.get(w.birth,16)
                while 2*moves>cap:cap*=2
                caps[w.birth]=cap
                add('H',(c.id,seq,slot,0),3*cap);add('H',(c.id,seq,slot,1),3*32)
            add('I',(c.id,seq));add('Z',(c.id,seq))
        add('ENDCASE',(c.id,));model.cleanup()
    add('END',(len(rows),))
    return {'records':dict(sorted(counts.items())), 'public_bytes':public_size,
            'private_bytes':private_size,'obs0_bytes':public_size,'obs1_bytes':public_size+private_size,
            'three_streams_bytes':3*public_size+2*private_size}


def main():
    p=argparse.ArgumentParser()
    for x in ('c','c-bez','duckling','wejscie','raport'): p.add_argument('--'+x,type=Path,required=True)
    for x in ('kod-c','kod-c-bez','kod-wyjscia'): p.add_argument('--'+x,type=int,required=True)
    args=p.parse_args(); errors=[]
    try:
        g.verify_input_hashes(args.wejscie.parent)
        rows=g.read_input(args.wejscie.read_bytes().decode('ascii'),expected_count=96)
        dec=g.read_input((args.wejscie.parent/'przypadki-ksztalty-stdin.csv').read_bytes().decode('ascii'),True,96)
        if [c.ops for c in rows]!=[c.ops for c in dec]: raise ValueError('E78efd5a7a5b9 E5422e223df9f')
        forecast=measure(rows)
        if forecast['three_streams_bytes']>192*1024*1024: raise ValueError('forecast exceeds 192 MiB')
        measured_bytes=args.c.stat().st_size+args.c_bez.stat().st_size+args.duckling.stat().st_size
        if measured_bytes>192*1024*1024: raise ValueError('native evidence exceeds 192 MiB')
        for name,path,code,private in (('C OBS1',args.c,args.kod_c,True),('C OBS0',args.c_bez,args.kod_c_bez,False),('Duckling',args.duckling,args.kod_wyjscia,True)):
            if code: errors.append(f'{name}: Ea56145270ce6 0, E4f5260d71c7e 0, record E6a47054c782f, field code: {code}')
            with path.open(encoding='ascii',newline='') as stream:
                try:
                    counts=validate_output(stream,rows,private)
                    expected=Counter({k:v for k,v in forecast['records'].items() if private or k not in PRIVATE})
                    if counts!=expected: errors.append(name+': record counts differ from corpus forecast '+repr(counts-expected)+' / '+repr(expected-counts))
                except (ValueError,IndexError,KeyError) as exc: errors.append(name+': '+str(exc))
        if not errors:
            for left,right,projection in ((args.c,args.c_bez,True),(args.c,args.duckling,False)):
                with left.open(encoding='ascii',newline='') as a,right.open(encoding='ascii',newline='') as b:
                    diff=first_difference(a,b,projection)
                    if diff: errors.append(diff)
    except (ValueError,OSError) as exc: errors.append('wejście / pliki: '+str(exc))
    result=('# FAIL\n\n'+'\n'.join(errors)) if errors else '# OK\n\nE5b64b0fed429: 96/96; Ef39441f51b35 Ee2971bee9914 E8d0eebb37dce, E03b382aabe85 E1364b62d3782 Ede7d1b721a1e E32cee0cd54d4 OBS1/OBS0 E13991feb1b0c.'
    args.raport.write_text(result+'\n',encoding='utf-8'); print(result); return int(bool(errors))

if __name__=='__main__': sys.exit(main())
