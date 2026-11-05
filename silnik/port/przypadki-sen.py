pass                                                                         

                                                                              
                                                                              
   
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sen_inputs10',HERE/'przypadki-solver.py')
g10=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g10;spec.loader.exec_module(g10)
g9,g8=g10.g9,g10.g8
Case,op,bits,number=g10.Case,g10.op,g10.bits,g10.number
shape,circle,box,capsule,segment=g10.shape,g10.circle,g10.box,g10.capsule,g10.segment
step,force,linear,angular=g8.step,g8.force,g8.linear,g8.angular
MANIFEST=json.loads((HERE/'sen-przypadki.json').read_bytes())
USED={**g10.USED,56:12,57:19,58:4,59:4,60:4,61:3,62:3,64:4}
PUBLIC=g10.PUBLIC|set(range(56,63))
U32=g10.U32


def world(slot=0,mode=1,gravity=(0,0),warm=1,enabled=1,**kw):
    old=g10.world(slot=slot,mode=mode,gravity=gravity,warm=warm,**kw)
    return op(56,*old[1:12],enabled)


def body(slot=0,owner=0,kind=2,p=(0,0),q=(1,0),v=(0,0),w=0,damping=0,
         angular_damping=0,gravity_scale=1,fixed=0,fast=0,enable=1,awake=1,threshold=.05,mode=1):
    return op(57,owner,slot,mode,kind,*map(bits,(*p,*q,*v,w,damping,angular_damping,gravity_scale)),
              fixed,fast,enable,awake,bits(threshold))


def awake(slot=0,value=1,owner=0,mode=1):return op(58,owner,slot,mode,value)
def enable(slot=0,value=1,owner=0,mode=1):return op(59,owner,slot,mode,value)
def threshold(slot=0,value=.05,owner=0,mode=1):return op(60,owner,slot,mode,bits(value))
def world_enable(value=1,owner=0,mode=1):return op(61,owner,mode,value)
def state(slot=0,owner=0,mode=1):return op(62,owner,slot,mode)
def helper(kind,object_,owner=0):return op(64,owner,kind,object_)


def floor(slot=0,x=0,width=12,owner=0):
    return [body(slot,owner=owner,kind=0,p=(x,-.5)),
            shape(slot,owner=owner,parent=slot,geometry=box(h=(width,.5)))]


def stack(count=3,*,x=0,start=1,shape_start=None,owner=0,enable_=1,rolling=0):
    rows=[];shape_start=start if shape_start is None else shape_start
    for j in range(count):
        rows += [body(start+j,owner=owner,p=(x,.5+j),enable=enable_),
                 shape(shape_start+j,owner=owner,parent=start+j,geometry=box(h=(1.,.5)),
                       rolling=rolling,friction=.6)]
    return rows


def chain(count=6,kind=2):
    rows=[]
    for j in range(count):
        rows += [body(j,kind=kind if j==count//2 else 2,p=(j*.95,0)),
                 shape(j,parent=j,geometry=circle(r=.5))]
    return rows


def long_a(family,n,warm):
    rows=[world(warm=warm)];at={}
    if family==1:
        rows += [body(0),body(1,awake=0),body(2,enable=0,awake=0),body(3,p=(3,0))]
        at={60:[awake(1),state(1)],120:[awake(0,0),awake(0,0),state(0)],180:[awake(0),state(0)]}
    elif family==2:
        rows=[world(warm=warm,gravity=(0,-.1)),*floor(),*stack(8)]
    elif family==3:
        rows=[world(warm=warm,gravity=(0,-10)),*floor(0,x=-4,width=2),*floor(1,x=4,width=2),
              *stack(3,x=-4,start=2),*stack(3,x=4,start=5)]
                                                                                      
        at={360:[op(3,0,0)],600:[op(3,0,1),body(8,kind=0,p=(0,-2)),
                               shape(8,parent=8,geometry=box(h=(10,.5)))],900:[op(3,0,8)]}
    elif family==4:
        rows=[world(warm=warm,gravity=(0,-1)),*floor(),*stack(3),
              body(4,p=(-6,.5),enable=0),shape(4,parent=4,geometry=circle(r=.5))]
        at={120:[awake(1,0)],360:[g9.transform(0,2,(.02,1.5)),linear(4,8)],
            660:[awake(1,0)],720:[g9.transform(0,4,(6,.5)),linear(4,-8)]}
    elif family==5:
        rows=[world(warm=warm,gravity=(0,-10)),*floor(),*stack(3),body(4,p=(5,2))]
        at={0:[awake(4,0),state(4)],120:[awake(4),state(4)],360:[awake(2,0),awake(2,0),op(37,0)],
            480:[awake(2),awake(2)],720:[awake(1,0)],900:[awake(3)]}
    elif family==6:
        rows=[world(warm=warm,gravity=(0,-10)),*floor(width=10),*stack(2,x=-3),*stack(2,x=3,start=3),enable(1,0)]
        at={360:[enable(1),awake(4,0)],480:[enable(3,0)],600:[world_enable(0)],
            720:[world_enable(0)],840:[world_enable(1),awake(1,0),awake(3,0)],960:[world_enable(0)]}
    elif family==7:
        rows += [body(0,kind=1,w=.2),shape(0,parent=0,geometry=box(h=(2,.2))),
                 body(1,p=(5,0)),shape(1,parent=1,geometry=circle(r=.5))]
        at={600:[angular(0,0)],900:[state(0)]}
    elif family==8:
                                                                             
        for j in range(6):
            rows += [body(j,p=(j%3*1.05,j//3*1.05),awake=int(j%2==0)),
                     shape(j,parent=j,geometry=circle(r=.5))]
        at={120:[awake(0,0),awake(2,0),awake(4,0)],360:[awake(1),awake(3)],
            600:[op(18,0,2)],720:[shape(6,parent=2,geometry=circle(r=.5))],900:[awake(5)]}
    elif family==9:
        rows=[world(warm=warm,gravity=(0,-10)),*floor(),
              body(1,p=(0,.5),v=(.1,0),w=.1),shape(1,parent=1,geometry=circle(r=.5),rolling=.2),
              body(2,p=(0,1.5)),shape(2,parent=2,geometry=box(h=(.5,.5)),rolling=.3)]
        at={360:[awake(1,0),g9.save(0,1),g9.get()],480:[g9.transform(0,2,(.02,1.5)),awake(1)],
            720:[force(2,kind=4,value=(.1,0)),g9.get()]}
    elif family==10:
        rows += [body(0,enable=0),shape(0,parent=0,geometry=circle(r=4),density=20,category=1,mask=2)]
        for j,words in enumerate(g10.STAR10):
            px,py,vx,vy=map(number,words)
            rows += [body(j+1,p=(px,py),v=(vx,vy)),shape(j+1,parent=j+1,geometry=circle(r=.5),category=2,mask=1)]
        at={120:[enable(0),awake(0,0)],240:[awake(0)],600:[awake(0,0)],720:[awake(0)]}
    else:raise ValueError(family)
    rows += at.get(0,[])
    for j in range(1,1201):rows += [step(n=n)]+at.get(j,[])
    return rows


def short_a(family):
    rows=[world(),body()]
    if family==11:return rows+[awake(0,0),step(dt=0,n=1,raw=True),step(dt=-.125,n=1,raw=True),step(dt=-.125,n=1),state()]
    if family==12:return rows+[step(dt=.125,n=1)]*3+[state(),step(dt=.125,n=1),state()]
    if family in (13,14,15):
        velocity=number(0x3d4ccccd+family-14)
        return [world(),body(v=(velocity,0)),step(dt=.125,n=1),state()]
    if family==16:
        return [world(),*floor(),body(1,p=(0,.1)),shape(1,parent=1,geometry=box(h=(.5,.5))),step(dt=.125,n=1)]
    if family==17:
        return [world(),*floor(),body(1,p=(0,.1),q=(number(0x3f7eb77f),.1)),
                shape(1,parent=1,geometry=box(h=(2,.2),c=(.2,0))),step(dt=.125,n=1)]
    if family==18:return [world(),body(enable=0),step(dt=.125,n=1),awake(0,0),state(),step(dt=.125,n=1),state(),enable(0,0),state()]
    if family==19:return rows+[shape(parent=0),force(kind=0,value=(2,3)),force(kind=2,value=(4,0)),awake(0,0),state(),awake(),step(dt=.125,n=1)]
    if family==20:
        return rows+[body(1,fixed=1),body(2,kind=0),step(dt=.125,n=1),awake(0,0),awake(1,0),
                     linear(0,0),angular(0,0),angular(1,2),linear(2,2),angular(2,2),state(0),state(1),
                     linear(0,.1),awake(0,0),angular(0,.1),step(dt=.125,n=1)]
    if family==21:
        rows += [shape(parent=0),step(dt=.125,n=1)]
        for kind in range(6):
            for wake in (0,1):rows += [awake(0,0),force(kind=kind,value=(0,0) if wake else (1,0),wake=wake),state()]
        return rows+[step(dt=.125,n=1)]
    if family==22:return rows+[step(dt=.125,n=1),threshold(value=-0.),state(),threshold(value=0.),state(),step(dt=.125,n=1)]
    if family==23:return rows+[state(),awake(0,0),state(),awake(),step(dt=.125,n=1),state(),op(37,0)]
    if family==24:return rows+[step(dt=.125,n=1,copy=0)]*3+[step(dt=.125,n=1,copy=1),op(37,0),op(37,1),op(1,0),op(37,0),op(37,1)]
    if family==25:return rows+[world(1),awake(0,0),state(),awake(),state(owner=1),op(3,0,0),state(),body(1),state(0),state(1)]
    if family==26:
        rows += [threshold(value=-1),threshold(value=math.inf),threshold(value=math.nan)]
        for j,value in enumerate((-1,math.inf,math.nan)):
            rows += [body(j+1,threshold=value),state()]
        return rows+[threshold(value=-0.),threshold(value=0.)]
    raise ValueError(family)


def long_b(family,n,warm):
    rows=[world(warm=warm),*chain(6)];at={}
    if family==1:
        at={120:[g9.transform(0,2,(2*.95,4)),awake(0)],360:[awake(0,0),awake(5,0)],600:[g9.transform(0,2,(2*.95,0)),awake(0),awake(5)]}
    elif family==2:
        rows=[world(warm=warm)]
        for j,(x,y) in enumerate(((0,0),(.9,0),(.9,.9),(0,.9))):rows += [body(j,p=(x,y)),shape(j,parent=j,geometry=circle(r=.5))]
        at={120:[g9.transform(0,0,(-.3,0)),awake(0)],360:[awake(2,0)],600:[awake(2)]}
    elif family==3:
        rows=[world(warm=warm),*chain(4)]
        rows += [body(4,p=(10,0)),shape(4,parent=4,geometry=circle(r=.5)),body(5,p=(10.95,0)),shape(5,parent=5,geometry=circle(r=.5))]
        at={120:[g9.transform(0,1,(1,3)),g9.transform(0,5,(11,3)),awake(0),awake(4)],240:[threshold(0,.1),threshold(4,.2)],480:[awake(0),awake(4)]}
    elif family==4:
        at={240:[awake(0,0)],360:[op(3,0,2)],600:[body(6,p=(20,0)),shape(6,parent=6,geometry=circle(r=.5))],720:[awake(5,0)],900:[op(3,0,4)]}
    elif family==5:
        rows += [body(6,p=(20,0),awake=0)]
        at={120:[op(3,0,6)],360:[awake(0,0),op(37,0)],480:[op(3,0,2)],1200:[op(1,0),op(37,0)]}
    elif family==6:
        at={120:[g9.transform(0,1,(.95,4)),g9.transform(0,4,(3.8,4)),awake(0)],240:[awake(2,0)],360:[awake(5,0)],
            600:[g9.transform(0,1,(.95,0)),g9.transform(0,4,(3.8,0)),awake(0),awake(2),awake(5)]}
    else:raise ValueError(family)
    for j in range(1,1201):rows += [step(n=n)]+at.get(j,[])
    return rows


def short_b(family):
    m=next(x for x in MANIFEST['przypadki'] if x['rodzina']=='B'+str(family));count=m['krokiDodatnie']
    if family==7:return [world(),body(awake=0),awake(0,0),state()]
    if family==8:return [world(),body(),step(dt=.125,n=1),state(),awake()]
    if family==9:
        return [world(),*chain(6),step(dt=.125,n=1),op(18,0,1),step(dt=.125,n=1),awake(3,0),awake(3),
                op(18,0,3),awake(3,0),awake(3),step(dt=.125,n=1),step(dt=.125,n=1)]
    if family==10:
        rows=[world(),body(0),shape(0,parent=0,geometry=circle(r=.7))]
        for j,position in enumerate(((1.1,0),(-1.1,0),(0,1.1),(0,2.05),(0,-1.1)),1):
            rows += [body(j,p=position),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+[step(dt=.125,n=1),op(18,0,4),step(dt=.125,n=1),awake(0,0)]
    if family==12:
        rows=[world(),body(0,kind=0),shape(0,parent=0,geometry=box(h=(4,.2)))]
        for j,x in enumerate((-1.9,-.95,.95,1.9),1):rows += [body(j,p=(x,.6)),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+[step(dt=.125,n=1),op(18,0,2),step(dt=.125,n=1),awake(1,0)]
    if family==13:
        return [world(),*chain(6,kind=1),step(dt=.125,n=1),op(18,0,0),step(dt=.125,n=1),awake(3,0)]
    if family==14:
        rows=[world()]
        for j,position in enumerate(((0,0),(.9,0),(.9,.9),(0,.9))):rows += [body(j,p=position),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+[step(dt=.125,n=1),g9.transform(0,0,(-.3,0)),step(dt=.125,n=1),awake(2,0)]
    if family in (16,18):
        rows=[world(),body(0,p=(20,0)),shape(0,parent=0,geometry=circle(r=.5))]
        for j in range(1,6):rows += [body(j,p=((j-1)*.95,0)),shape(j,parent=j,geometry=circle(r=.5))]
        rows += [body(6,p=(-20,0)),shape(6,parent=6,geometry=circle(r=.5)),step(dt=.125,n=1),op(18,0,3)]
        if family==18:return rows+[step(dt=.125,n=1),awake(4,0)]
        rows += [awake(4,0),awake(4),op(18,0,2),op(18,0,4)]
        rows += [shape(7,parent=2,geometry=circle(r=.5)),shape(8,parent=4,geometry=circle(r=.5)),shape(9,parent=3,geometry=circle(r=.5))]
        return rows+[step(dt=.125,n=1),step(dt=.125,n=1)]
    if family==19:return [world(),body(),awake(0,0),step(dt=.125,n=1),awake()]+[step(dt=.125,n=1)]*3
    if family==20:
        return [world(),body(0),body(1,p=(.99,0)),shape(0,parent=0,geometry=circle(r=.5)),shape(1,parent=1,geometry=circle(r=.5)),
                step(dt=.125,n=1),g9.save(),g9.transform(0,1,(1.05,0)),step(dt=.125,n=1),g9.get(),
                op(18,0,1),shape(2,parent=1,geometry=circle(r=.5)),step(dt=.125,n=1),g9.save(a=0,b=2,target=1),g9.get(0),g9.get(1)]
    if family==22:
        return [world(),body(0),body(1,awake=0),body(2),body(3,enable=0),
                *[step(dt=.125,n=1,copy=0) for _ in range(3)],step(dt=.125,n=1,copy=1),op(37,0),op(37,1),
                step(dt=.125,n=1,copy=2),awake(1),awake(0),enable(3),step(dt=.125,n=1,copy=3),
                op(37,0),op(37,1),op(37,2),op(37,3),op(1,0),op(37,0),op(37,1)]
    rows=[world(),*chain(6,kind=1 if family==13 else 2)]
    if family==12:
                                                                    
        rows=[world(),body(0,kind=0),shape(0,parent=0,geometry=box(h=(3,.2))),
              body(1,p=(-2,.6)),shape(1,parent=1,geometry=circle(r=.5)),body(2,p=(2,.6)),shape(2,parent=2,geometry=circle(r=.5))]
    if family==21:
        return [world(),body(0,awake=0),body(1,awake=0),awake(0),op(3,0,1),body(2,awake=0),awake(2),awake(0,0)]+[step(dt=.125,n=1)]*4
    rows += [step(dt=.125,n=1)]
    if family in (9,10,11,14,15,16,17,18,20,22):
        rows += [g9.transform(0,1,(.95,3)),g9.transform(0,4,(3.8,3))]
        if family==11:rows += [g9.transform(0,1,(.95,1.05))]
        if family==15:rows += [op(3,0,0)]
        if family==18:rows += [op(3,0,2)]
    rows += [step(dt=.125,n=1)]
    rows += [awake(3 if family!=12 else 1,0),state(3 if family!=12 else 1),awake(3 if family!=12 else 1)]
    if family in (9,10,14,16,17,20,22):rows += [awake(0,0),awake(5,0),awake(0),awake(5)]
    if family==20:rows += [g9.transform(0,1,(.95,0))]
    rows += [step(dt=.125,n=1)]*(count-2)
    if family==22:rows += [op(37,0)]
    return rows


def component_rows(fixture):
    if fixture==1:return [world(),body(awake=0),helper(1,3)]
    if fixture==2:return [world(),body(),helper(2,0)]
    if fixture==3:return [world(),body(0),body(1),body(2),step(dt=.125,n=1),helper(2,1)]
    if fixture==10:return [world(),body(awake=0),op(3,0,0),body(1,awake=0),helper(1,3)]
    if fixture==11:return [world(),body(awake=0),helper(3,0)]
    if fixture==12:return [world(),body(),helper(3,0)]
    if fixture==13:
        rows=[world(),body(0),shape(0,parent=0,geometry=circle(r=.7))]
        for j,position in enumerate(((1.1,0),(-1.1,0),(0,1.1),(0,2.05),(0,-1.1)),1):
            rows += [body(j,p=position),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+g9.cycle()+[op(18,0,4),helper(3,0),op(18,0,1),helper(3,0)]
    if fixture==14:
        rows=[world(),body(0,kind=0,p=(0,-.7)),shape(0,parent=0,geometry=box(h=(4,.2)))]
        for j in range(1,6):rows += [body(j,kind=1 if j==3 else 2,p=((j-3)*.95,0)),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+g9.cycle()+[helper(3,2),op(18,0,3),helper(3,2)]
    if fixture==15:
        rows=[world(),body(0,p=(20,0)),shape(0,parent=0,geometry=circle(r=.5))]
        for j in range(1,6):rows += [body(j,p=((j-1)*.95,0)),shape(j,parent=j,geometry=circle(r=.5))]
        rows += [body(6,p=(-20,0)),shape(6,parent=6,geometry=circle(r=.5))]
        rows += g9.cycle()+[op(18,0,3),helper(3,1),op(18,0,2),op(18,0,4)]
        rows += [shape(7,parent=2,geometry=circle(r=.5)),shape(8,parent=4,geometry=circle(r=.5)),shape(9,parent=3,geometry=circle(r=.5))]
        return rows+g9.cycle()+[helper(3,2)]
    if fixture==16:
        return [world(),*chain(6),*g9.cycle(),op(18,0,1),op(18,0,4),awake(3,0),state(3)]
    if fixture==8:
                                                                          
                                                                           
        rows=[world(),body(0),shape(0,parent=0,geometry=circle(r=4),density=20,category=1,mask=2),body(1)]
        for j,words in enumerate(g10.STAR10):
            px,py,_,_=map(number,words)
            rows += [shape(j+1,parent=1,geometry=circle((px,py),.5),category=2,mask=1)]
        rows += [body(2,p=(20,0)),shape(14,parent=2,geometry=circle(r=.5)),body(3,p=(20.95,0)),shape(15,parent=3,geometry=circle(r=.5))]
        return rows+g9.cycle()+[awake(2,0),awake(2),awake(0,0),awake(0)]
    if fixture==9:
        rows=[world(),body(0)]
        for j in range(1,8):rows += [body(j,p=(j*1.05,0),awake=0),shape(j,parent=j,geometry=circle(r=.5))]
        return rows+g9.cycle()+[helper(1,7),helper(1,6),awake(0,0),awake(1,0),awake(2,0),awake(3,0),awake(4,0),awake(5,0),awake(6,0),awake(7,0),awake(4)]
    if fixture in (4,5,6):
        rows=[world()];count=2 if fixture==4 else 6
        for j in range(count):rows += [body(j,p=(j*1.05,0),awake=int(fixture==6)),shape(j,parent=j,geometry=circle(r=.5))]
        rows += g9.cycle()
        if fixture==4:rows += [helper(1,3)]
        elif fixture==5:rows += [helper(1,5),helper(1,6)]
        else:rows += [helper(2,0),helper(2,1),helper(2,2),helper(2,3)]
        return rows
    rows=[world(),*chain(4 if fixture==8 else 6)]
                                                                             
    rows += [op(41,0),op(42,0),op(43,0),op(44,0),op(45,0)]
    if fixture in (7,8,9):
        if fixture==7:
            seed=g9.seed(0);rows += [g9.save(),op(51,0,0,*seed)]
        rows += [awake(0,0),awake(0)]
    else:
        rows += [op(18,0,1),op(18,0,4),helper(3,0)]
        if fixture==16:rows += [awake(3,0)]
        if fixture==15:rows += [awake(0,0),awake(0)]
    return rows


def cases():
    result=[]
    for m in MANIFEST['przypadki']:
        if m['rodzina']=='B15b':
            rows=[world(),*chain(6),body(6,p=(20,0),enable=0)]
            rows += [threshold(j,1000) for j in range(6)]
            rows += [step(dt=.125,n=1)]*3+[op(18,0,2),step(dt=.125,n=1)]
            rows += [op(3,0,j) for j in range(6)]+[step(dt=.125,n=1)]
        else:
            letter=m['rodzina'][0];family=int(m['rodzina'][1:]);long=m['id']<=60 or 77<=m['id']<=112
            rows=(long_a if letter=='A' else long_b)(family,m['podkroki'],m['warm']) if long else (short_a if letter=='A' else short_b)(family)
        result.append(Case(m['id'],m['rodzina'],tuple(rows)))
    return tuple(result)


def components():return tuple(Case(j+1,m['id'],tuple(component_rows(j+1))) for j,m in enumerate(MANIFEST['component']))


def intermediate():
    pass                                                                    

                                                                        
                                                                           
                                                            
       
    full_ids=set(range(1,7))|set(range(61,77))
    rows=tuple(c if c.id in full_ids else Case(c.id,'diagnostic frame, no full-scene credit',c.ops[:1])
               for c in verify()[:76])
    return rows,sorted(full_ids)


def validate_operation(row,component=False):
    if len(row)!=65 or any(type(x) is not int or not 0<=x<=U32 for x in row):raise ValueError('u32 operation/64 words')
    code,*a=row
    if code not in (set(USED) if component else PUBLIC):raise ValueError('opcode outside profile11')
    if any(a[USED[code]:]):raise ValueError('unused nonzero')
    if code<56:
        if component and code in (41,42,43,44,45,51,52,53):
            if a[0]>15:raise ValueError('component world register')
            if code==51 and a[1]>255:raise ValueError('component contact register')
        else:g10.validate_operation(row)
        return
    if a[0]>15:raise ValueError('world register')
    if code not in (56,61) and a[1]>255:raise ValueError('body register')
    bools={56:(1,10,11),57:(2,14,15,16,17),58:(2,3),59:(2,3),60:(2,),61:(1,2),62:(2,),64:()}[code]
    if any(a[j]>1 for j in bools):raise ValueError('bool')
    if code==57 and a[3]>2:raise ValueError('body type')
    if code==64 and (a[1] not in (1,2,3) or a[3]):raise ValueError('helper/profileMask')


def verify():
    rows=cases();require=lambda condition,message:None if condition else (_ for _ in ()).throw(ValueError(message))
    require([c.id for c in rows]==list(range(1,MANIFEST['N']+1)),'complete manifest prefix')
    for c,m in zip(rows,MANIFEST['przypadki']):
        require(0<len(c.ops)<=m['opMax'],f'{c.id} opMax')
        for r in c.ops:validate_operation(r)
        steps=[r for r in c.ops if r[0] in (31,32)]
        actual=Counter('positive' if number(r[2])>0 else 'zero' if number(r[2])==0 else 'negative_raw' if r[0]==31 else 'refusal' for r in steps)
        require(actual==Counter({k:v for k,v in (('positive',m['krokiDodatnie']),('zero',m['krokiZero']),('negative_raw',m['krokiRawUjemne']),('refusal',m['odmowyGameStep'])) if v}),f'{c.id} exact Step counts: {actual}')
        require(all(r[3]==m['podkroki'] and (number(r[2])<=0 or r[2]==int(m['dtDodatnieH'],16)) for r in steps),f'{c.id} dt/substeps')
    for c,m in zip(components(),MANIFEST['component']):
        require(len(c.ops)<=m['opMax'],f'{m['id']} opMax')
        for r in c.ops:validate_operation(r,True)
        require(sum(r[0] in (31,32) and number(r[2])>0 for r in c.ops)==m['krokiDodatnie'],f'{m['id']} component Step')
    require(sum(m['krokiDodatnie'] for m in MANIFEST['przypadki'] if m['opMax']==1280)==115200,'115200 long positive steps')
    return rows


def encode(rows,decimal=False,component=False,*,header_n=None):
    n=len(rows) if header_n is None else header_n
    result=[('COMPONENT11' if component else 'PORT11')+' '+str(n)]
    for c in rows:
        result.append(f'C {c.id} {len(c.ops)}')
        for j,row in enumerate(c.ops,1):
            validate_operation(row,component)
            result.append(f'O {j} {row[0]} '+' '.join(str(x) if decimal else f'{x:08x}' for x in row[1:]))
    return '\n'.join(result)+'\n'


def write(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);rows=verify();result={}
    for stem,data,component in (('przypadki-sen',rows,False),('component-sen',components(),True)):
        for decimal in (False,True):
            name=stem+('-stdin' if decimal else '')+'.csv';raw=encode(data,decimal,component).encode('ascii')
            (directory/name).write_bytes(raw);result[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    (directory/'wejscia-sen-sha256.json').write_text(json.dumps(result,indent=2)+'\n',encoding='ascii');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();print(json.dumps(write(args.out),indent=2))
