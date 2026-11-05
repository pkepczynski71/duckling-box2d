pass                                                                         

                                                                          
                                                                              
   
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('zywy_guard_inputs',HERE/'ujemne-zywy.py')
n=importlib.util.module_from_spec(spec);sys.modules[spec.name]=n;spec.loader.exec_module(n)
g,op,bits=n.g,n.op,n.bits
MAX=0xffffffff


@dataclass(frozen=True)
class Fixture:
    name: str
    group: str
    kind: int
    words: tuple
    helper: int | None = None
    status: int | None = None
    value: int = 0
    rows: tuple = ()
    seed: int = 0
    positive_setup: int = 0
    last_status: int | None = None
    predicate: str = ''
    all_success: bool = False
    field_word: int | None = None
    sign_rule: str | None = None
    expected_awake: int | None = None
    expected_velocity: tuple | None = None
    expected_reason: int | None = None

    def encode(self,decimal=False):
        if len(self.words)!=64 or len(self.rows)>16 or any(type(w)is not int or not 0<=w<=MAX for w in self.words):
            raise ValueError('GUARD12 bounded64ai/16op')
        fmt=str if decimal else lambda w:f'{w:08x}'
        prefix=f'GUARD12 1\nG 1 {self.kind} {self.seed} {len(self.rows)}\nGA 1 '+' '.join(map(fmt,self.words))+'\n'
        return (prefix+''.join(n.operations(self.rows,decimal))).encode('ascii')

    def expected_helper_output(self):
        if self.helper is None or self.rows:raise ValueError('not helper-only')
        header=self.encode().decode('ascii')
        h=(self.status,int(self.status==0),self.value&MAX,self.value>>32)
        return (header+'CASE 1 0\n'+f'GR12 1 0 {self.helper} '+' '.join(f'{w:08x}' for w in h)+'\nENDCASE 1\nEND 1\n').encode('ascii')


def fixture(name,group,kind,words=(),**kw):
    if len(words)>64:raise ValueError('too many GA words')
    return Fixture(name,group,kind,(*words,*([0]*(64-len(words)))),**kw)


def body_mut(kind=0,values=(),body=0):return op(80,0,body,1,kind,*values)
def shape_mut(kind=0,values=(),shape=0):return op(81,0,shape,1,kind,*values)
def world_mut(kind=0,values=()):return op(82,0,1,kind,*values)


def geometry(kind):
    if kind==5:return (0,0,bits(1))
    if kind==6:return (0,0,bits(1),0,bits(.5))
    if kind==7:return (0,0,bits(1),0)
    if kind==8:return (3,0,0,0,bits(1),0,0,bits(1))
    raise ValueError('four ordinary setter geometries')


def lock_routes():
    pass                                                               
    circle=(0,0,bits(1),*([0]*37))
    old_shape=lambda code:op(code,2,0,1,0,bits(1),1,1,1,0,MAX,MAX,0,0,0,0,*circle)
    result=[('destroyWorld',op(1,0)),
        ('createBody',op(2,2,0,2,0,0,bits(1),0,0,0,0,0)),
        ('destroyBody',op(3,0,1)),('setTransform',op(4,0,1,0,0,bits(1),0)),
        ('createShapeRaw',old_shape(10)),('destroyShapeRaw',op(11,0,1,1)),
        ('densityRaw',op(12,0,1,bits(2),1)),('applyMassRaw',op(13,0,1)),
        ('objectIdBody',op(15,0,2,1,1,7,9)),('objectIdShape',op(15,0,3,1,1,7,9)),
        ('createBodyWithShape',op(16,2,2,0,2,0,0,bits(1),0,0,0,0,0,0,bits(1),1,0,0,0,1,0,MAX,MAX,0,*circle)),
        ('addShape',old_shape(17)),('destroyShape',op(18,0,1)),('density',op(19,0,1,bits(2))),
        ('createBody8',op(30,2,0,2,0,0,bits(1),0,0,0,0,0,0,0,bits(1),0,1)),
        ('step-entry-validation',g.step()),('force',op(34,0,1,1,bits(1),bits(2),0,0,1)),
        ('linearVelocity',op(35,0,1,bits(1),bits(2),1)),('angularVelocity',op(36,0,1,bits(1),1)),
        ('createShape9',g.shape(2,parent=1,geometry=g.circle(r=1))),('warmRawWrapper',op(55,0,1)),
        ('createBody11',g.body(slot=2)),('awake',op(58,0,1,1,1)),('sleepEnable',op(59,0,1,1,1)),
        ('sleepThreshold',op(60,0,1,1,bits(.05))),('worldSleeping',op(61,0,1,1)),
    ]
    body_values={0:(2,),1:(1,),2:(bits(1),0,0,bits(1)),3:(),4:(bits(.5),),5:(bits(.5),),
                 6:(bits(-1),),7:(1,),8:(0,0,bits(1),0,bits(1))}
    for kind,values in body_values.items():result.append((f'body80-{kind}',body_mut(kind,values,body=1)))
    shape_values={0:(bits(.5),),1:(bits(.5),),2:(3,),3:(bits(.5),0,0,0,3,0),4:(1,0,MAX,MAX,0),
                  **{kind:geometry(kind) for kind in range(5,9)}}
    for kind,values in shape_values.items():result.append((f'shape81-{kind}',shape_mut(kind,values,shape=1)))
    world_values={0:(1,),1:(bits(1),),2:(bits(1),),3:tuple(map(bits,(30,10,3))),4:(bits(100),),5:(0,0)}
    for kind,values in world_values.items():result.append((f'world82-{kind}',world_mut(kind,values)))
    for target in (0,1):
        for event in (0,1,2):
            if target==0 and event==2:continue
            result.append((f'flag83-{target}-{event}',op(83,0,target,1,1,event,1)))
    result.append(('name84',op(84,0,1,1,0,1,97)))
    for target in range(3):result.append((f'object85-{target}',op(85,0,target,int(target!=0),1,1,7,9)))
    for kind in range(4):result.append((f'install86-{kind}',op(86,0,1,kind,1)))
    for kind in range(4):result.append((f'rule87-{kind}',op(87,0,kind,0)))
    result.append(('create90',n.body(slot=2)))
    return tuple(fixture('G12-LOCK-'+name,'G2',200+row[0],row[1:],helper=2000+row[0],status=7,
                         positive_setup=1,predicate='locked before every scratch/metadata/clear/end/ticket mutation')
                 for name,row in result)


def definitions():
    result=list(lock_routes())
    def helper(name,group,row,status,predicate,field_word=None,sign_rule=None):
        result.append(fixture(name,group,100+row[0],row[1:],helper=1000+row[0],status=status,predicate=predicate,
                              field_word=field_word,sign_rule=sign_rule))
    def field_pair(name,row,index,*,nonnegative=False,positive=False,group='G3'):
        rule='positive' if positive else 'nonnegative' if nonnegative else None
        helper(name+'-finite',group,n.changed(row,index,0x7f800000),5,'finite of this field only; +Inf passes sign',index,rule)
        if nonnegative or positive:
            helper(name+'-sign',group,n.changed(row,index,0 if positive else bits(-1)),5,
                   '>0' if positive else '>=0; negative finite input',index,rule)
    for kind,name in ((4,'linearDamping'),(5,'angularDamping'),(6,'gravityScale')):
        field_pair('G12-BODY-'+name,body_mut(kind,(bits(1),)),4,nonnegative=kind!=6)
    mass=body_mut(2,(bits(1),0,0,bits(1)))
    for index,name in ((4,'mass'),(5,'center.x'),(6,'center.y'),(7,'inertia')):
        field_pair('G12-MASS-'+name,mass,index,nonnegative=index in (4,7))
    target=body_mut(8,(0,0,bits(1),0,bits(1)))
    for index,name in ((4,'position.x'),(5,'position.y'),(8,'dt')):
        field_pair('G12-TARGET-'+name,target,index,positive=index==8)
    helper('G12-TARGET-norm-lower','G3',n.changed(target,6,0),5,'lower strict squaredLength bound')
    helper('G12-TARGET-norm-upper','G3',n.changed(target,6,bits(2)),5,'upper strict squaredLength bound')
    helper('G12-TARGET-derived-maxVelocity','G3',n.changed(target,4,0x7f7fffff),5,
           'finite(v.x)=true, v.x*v.x=+Inf, finite(maxVelocity)=false')
    for kind,name in ((0,'friction'),(1,'restitution')):
        field_pair('G12-SHAPE-'+name,shape_mut(kind,(bits(.5),)),4,nonnegative=True)
    surface=shape_mut(3,(bits(.5),bits(.5),bits(.5),0,3,0))
    for index,name in ((4,'friction'),(5,'restitution'),(6,'rolling'),(7,'tangent')):
        field_pair('G12-SURFACE-'+name,surface,index,nonnegative=index!=7)
    for kind,name in ((1,'restitutionThreshold'),(2,'hitThreshold'),(4,'maxSpeed')):
        field_pair('G12-WORLD-'+name,world_mut(kind,(bits(1),)),3,nonnegative=kind!=4,positive=kind==4)
    tuning=world_mut(3,tuple(map(bits,(30,10,3))))
    for index,name in ((3,'hertz'),(4,'dampingRatio'),(5,'pushSpeed')):
        field_pair('G12-WORLD-'+name,tuning,index,nonnegative=True)
    for index,name in ((3,'gravity.x'),(4,'gravity.y')):
        field_pair('G12-WORLD-'+name,world_mut(5,(0,0)),index)
    for index,name in ((4,'vector.x'),(5,'vector.y')):
        field_pair('G12-VECTOR-'+name,op(92,0,0,1,0,0,0),index)
    for kind,name in ((5,'circle'),(6,'capsule'),(7,'segment'),(8,'polygon')):
        row=shape_mut(kind,geometry(kind))
        if kind in (5,6):row=n.changed(row,6 if kind==5 else 8,0)
        elif kind==7:row=n.changed(row,6,0)
        else:row=shape_mut(8,(2,0,0,0,bits(1),0))
        helper('G12-GEOM-'+name,'G4',row,4,'one invalid geometry member; no raw invalid geometry execution')
    helper('G12-S12-GEOMETRY','G5',shape_mut(5,(bits(8192),0,bits(1))),4,
           'dynamic !fixed, target circle(center8192,r1,density1), inertia cancellation +0')
    helper('G12-S12-invMass','G5',body_mut(2,(1,0,0,0)),4,'1/smallest positive subnormal overflows')
    helper('G12-S12-invInertia','G5',body_mut(2,(0,0,0,1)),4,'1/smallest positive subnormal overflows')
    for selector,name in ((0,'bodyUpper'),(1,'contactUpper')):
        for count,status in ((131059,0),(131060,3)):
            result.append(fixture(f'G12-BLOCK-{name}-{count}','G7',3,(selector,count,0,0,0),
                                  helper=2+selector,status=status,value=count,predicate='floor(upper/4)+3 <= 32767'))
    result.append(fixture('G12-BLOCK-checkedSum-overflow','G7',3,(2,MAX,0x7fffffff,1,0),
                          helper=4,status=3,predicate='MAXi64+1 rejected before addition'))
    setup=(g.world(),n.body(),g.shape(0,parent=0,geometry=g.circle(r=1)))
    body_ops=(body_mut(0,(1,)),body_mut(1,(0,)),body_mut(1,(1,)),
              body_mut(2,(bits(2),bits(.25),0,bits(3))),body_mut(3),
              body_mut(4,(bits(.5),)),body_mut(5,(bits(.25),)),body_mut(6,(bits(-1),)),
              body_mut(7,(1,)),body_mut(8,(bits(1),bits(2),bits(1),0,bits(1))))
    result.append(fixture('G12-POS-BODY','G3',0,rows=(*setup,*body_ops),last_status=0,all_success=True,
                          predicate='legal 12a mutators; no hidden positive Step'))
    shape_ops=(shape_mut(0,(bits(.7),)),shape_mut(1,(bits(1.5),)),shape_mut(2,(3,)),
               shape_mut(3,(bits(.5),bits(.25),bits(.1),bits(-1),5,0)),shape_mut(4,(1,0x80000000,MAX,MAX,0)),
               *(shape_mut(kind,geometry(kind)) for kind in range(5,9)))
    result.append(fixture('G12-POS-SHAPE','G4',0,rows=(*setup,*shape_ops),last_status=0,all_success=True,
                          predicate='all four legal setter geometries and independent material/filter fields'))
    source=n.body()
    for index,value in ((4,bits(1)),(5,bits(2)),(6,bits(.8)),(7,bits(.6)),(8,bits(3)),(9,bits(4)),(10,bits(1))):
        source=n.changed(source,index,value)
    result.append(fixture('G12-POS-VECTOR','G3',0,rows=(g.world(),source,*(op(92,0,0,1,kind,bits(.25),bits(.5)) for kind in range(6))),
                          last_status=0,all_success=True,predicate='local/world points/vectors/point velocities; rotated, translated and moving body'))
    if len(result)>160 or len({f.name for f in result})!=len(result):raise ValueError('GUARD fixture budget/uniqueness')
    return tuple(result)


def parameter_routes():
    pass                                                          

                                                                         
                                                                        
                                                                           
                                                                      
       
    from dataclasses import replace
    setup=(g.world(),n.body(),g.shape(0,parent=0,geometry=g.circle(r=1)))
    repair=body_mut(4,(bits(.5),))
    result=[]
    for source in definitions():
        if source.group!='G3' or not 100<=source.kind<200 or source.status!=5:continue
        variants=[('',source.words)]
        if source.field_word is not None and source.words[source.field_word]==0x7f800000:
            for suffix,value in (('-NaN',0x7fc00000),('-negative-Inf',0xff800000)):
                words=list(source.words);words[source.field_word]=value;variants.append((suffix,tuple(words)))
        for suffix,words in variants:
            rows=(*setup,op(source.kind-100,*words),repair)
            result.append((source.name,replace(source,name=source.name+'-public-route'+suffix,
                kind=0,words=(0,)*64,rows=rows,helper=None,positive_setup=0,
                last_status=0,expected_reason=0,all_success=False)))
    return tuple(result)


def history_routes():
    pass                                                                 

                                                                             
                                                                               
       
    def body_at(slot,kind=2,x=0,y=0):
        row=n.changed(n.body(slot=slot),3,kind)
        row=n.changed(row,4,bits(x));return n.changed(row,5,bits(y))
    setup=(g.world(),body_at(0,0),body_at(1,y=1.5),
           g.shape(0,parent=0,geometry=g.circle(r=1)),g.shape(1,parent=1,geometry=g.circle(r=1)))
    result=[]
    for parity in (0,1):
        rows=(*setup,*((g.step(dt=0,n=1),) if parity else ()),g.step(dt=1/60,n=1),
              op(49,0,0),op(18,0,1),g.shape(1,parent=1,geometry=g.circle(r=1)),
              g.step(dt=0,n=1),op(49,0,1),op(18,0,1),op(1,0),op(50,0,1),op(50,1,1))
        result.append(fixture('G12-HISTORY-end-side'+str(1-parity),'G12',0,rows=rows,
            all_success=True,last_status=0,positive_setup=1,
            predicate='old raw generation/full birth retained on both end sides, reuse before copy, read after world death'))
    boxes=(g.world(),body_at(0,0),body_at(1,x=-1.5,y=.75),body_at(2,x=1.5,y=.75),
           g.shape(0,parent=0,geometry=g.box(h=(4,.5))),
           g.shape(1,parent=1,geometry=g.box(h=(.5,.5))),g.shape(2,parent=2,geometry=g.box(h=(.5,.5))))
    result.append(fixture('G12-COPY-two-two-point-begins','G11',0,
        rows=(*boxes,g.step(dt=1/60,n=1),op(49,0,0),op(49,0,1),op(1,0),op(50,0,1),op(50,1)),
        all_success=True,last_status=0,positive_setup=1,
        predicate='two owned copies before mutation; >=2 begin contacts with both nested points; source and second copy survive world death'))
    if any(len(item.rows)>16 for item in result):raise ValueError('history GUARD <=16 operations')
    return tuple(result)


def core_routes():
    pass                                                                      
    threshold=bits(.05)
    source=n.changed(n.body(),17,0)
    setup=(g.world(),source,g.shape(0,parent=0,geometry=g.circle(r=1)),op(60,0,0,1,threshold))
    return tuple(fixture('G12-TARGET-threshold-'+name,'G3',0,
        rows=(*setup,body_mut(8,(delta,0,bits(1),0,bits(1)))),all_success=True,last_status=0,
        expected_awake=awake,expected_velocity=(delta if awake else 0,0),
        predicate='finite f32 sqrt(dx*dx) with angular0; return only when maxVelocity < sleepThreshold; equality wakes')
        for name,delta,awake in (('below',threshold-1,0),('equal',threshold,1),('above',threshold+1,1)))


def transfer_routes():
    setup=[g.world()]
    for j in range(3):
        setup.extend((n.body(slot=j),g.shape(j,parent=j,geometry=g.circle(r=1))))
    rows=(*setup,body_mut(0,(0,),body=0),body_mut(1,(0,),body=2),
          body_mut(0,(1,),body=2),body_mut(0,(2,),body=2),body_mut(1,(1,),body=2),
          body_mut(0,(2,),body=0),body_mut(0,(2,),body=0))
    return (fixture('G12-TRANSFER-nonlast-disabled-type','G5',0,rows=rows,all_success=True,last_status=0,
        predicate='TransferBody nonlast RemoveSwap, disabled SetType both directions, enable/state recreation, same-type no-op'),)


def name_routes():
    pass                                                                           
    cases=(('length32',b'a'*32,5),('length32-UTF8',b'\xc4\x85'*16,5),('NUL',b'a\0b',5),('truncated2',b'\xc3',5),
           ('overlong2',b'\xc0\xaf',5),('surrogate',b'\xed\xa0\x80',5),
           ('out-of-range',b'\xf4\x90\x80\x80',5),('stray-continuation',b'\x80',5),
           ('truncated3',b'\xe2\x82',5),('overlong4',b'\xf0\x80\x80\x80',5),
           ('legal31-ASCII',b'a'*31,0),('legal31-UTF8',b'a'*29+b'\xc4\x85',0),
           ('legal-max-scalar',b'\xf4\x8f\xbf\xbf',0),('raw-readable32',b'\0'+b'Z'*31,0))
    result=[]
    for name,data,status in cases:
        row=n.body();row=n.changed(row,20,len(data))
        for j,byte in enumerate(data):row=n.changed(row,21+j,byte)
        if name=='raw-readable32':row=n.changed(row,2,0)
        result.append(fixture('G12-NAME-create-'+name,'G9',0,rows=(g.world(),row),
            all_success=status==0,last_status=status,expected_reason=3 if status else 0,
            predicate='Create90 len<=31 and complete scalar UTF8 without NUL before allocation; raw32 has a readable owned buffer, not a SetName84/B08 mutation proof'))
    return tuple(result)


MISSING = (
    'G1 every life/owner/birth predicate and every new route, plus two MEMORY_GUARD proofs',
    'G3 create90 field/route witnesses and redundant literal proofs tied to source-bound port locations',
    'G4 complete individual finite/threshold/convex/result geometry predicate set',
    'G5 SetType/fixedRotation/ApplyMass and COM-overflow prepared routes',
    'G6 full atomicity with contacts/end/forces/scratch/tickets before and after refusal',
    'G7 full-batch Step after separate SetFilter/Enable setup and route checks',
    'G8 game ApplyMass/density convenience on both shapes/COM',
    'G9 length/NUL/all UTF8 classes and B08 readable-buffer proof',
    'G10 every rule/normal/life/order predicate and actual callback signatures',
    'G11 >=2 contacts, every list and both nested points after destruction',
    'G12 each event/history kind and both end buffers with reused participants',
)
