pass                                                                            
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('zywy_inputs11',HERE/'przypadki-sen.py')
g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
op,bits,number,Case=g.op,g.bits,g.number,g.Case
shape,circle,box,capsule,segment=g.shape,g.circle,g.box,g.capsule,g.segment
MANIFEST=json.loads((HERE/'zywy-przypadki.json').read_bytes())
AVAILABLE_N=160

def body(slot=0,owner=0,enabled=1,name=b'',object_id=None,**kw):
    row=g.body(slot=slot,owner=owner,**kw)
    return op(90,*row[1:20],enabled,len(name),*name,*([0]*(32-len(name))),
              int(object_id is not None),(object_id or 0)&0xffffffff,(object_id or 0)>>32)

def bmut(kind,*values,slot=1,owner=0,mode=1):return op(80,owner,slot,mode,kind,*values)
def smut(kind,*values,slot=1,owner=0,mode=1):return op(81,owner,slot,mode,kind,*values)
def scalar(kind,value,**kw):return bmut(kind,bits(value),**kw)
def vector(kind,xy=(.25,.5),slot=1,owner=0,mode=1):return op(92,owner,slot,mode,kind,*map(bits,xy))
def meta(target=1,slot=1,owner=0,mode=1):return op(91,owner,target,slot if target else 0,mode)
def polygon(vertices=((-0.5,-0.5),(.5,-.5),(.5,.5),(-.5,.5)),radius=0):
    return 3,(len(vertices),bits(radius),*(bits(v) for point in vertices for v in point))
def geometry(value,slot=1,owner=0,mode=1):
    tag,words=value
    if tag==4:raise ValueError('No box tag in replacement geometry')
    return smut(tag+5,*words,*([0]*(40-len(words))),slot=slot,owner=owner,mode=mode)
def target(p=(.5,.75),q=(.8,.6),dt=1,**kw):return bmut(8,*map(bits,(*p,*q,dt)),**kw)
def filt(category=1,mask=(1<<64)-1,group=0,**kw):
    return smut(4,category&0xffffffff,category>>32,mask&0xffffffff,mask>>32,group&0xffffffff,**kw)

def setup(m,*,compound=False):
    rows=[g.world(gravity=(0,0),warm=m['warm']),body(0,kind=0,p=(0,-1.3)),
          shape(0,parent=0,geometry=box(h=(4,.5))),body(1,p=(0,0),w=.125),
          shape(1,parent=1,geometry=circle((.125,0),.5)),body(2,p=(.9,0),awake=0),
          shape(2,parent=2,geometry=circle(r=.5))]
    if compound:rows += [shape(3,parent=1,geometry=circle((-.3,.1),.2),density=.5)]
    return rows

def long_a(m):
    family=int(m['rodzina'][1:]);rows=setup(m,compound=family in (3,4,5,6,7))
    if family==8:rows += [body(3,p=(-.9,0)),shape(3,parent=3,geometry=circle(r=.5)),g.op(15,0,2,1,1,0x12345678,0x87654321)]
    at={}
    def put(frame,*operations):at.setdefault(frame,[]).extend(operations)
    if family==1:
        for frame,kind in zip((50,100,150,200,250,300),(0,1,2,1,0,2)):put(frame,bmut(0,kind))
        put(301,bmut(0,2));put(350,bmut(0,1,slot=2));put(351,bmut(0,2,slot=2))
    elif family==2:
        put(75,bmut(1,0),bmut(1,0),shape(3,parent=1,geometry=circle((.2,0),.2)),op(18,0,3))
        put(150,bmut(1,1),bmut(1,1));put(250,bmut(1,0,slot=0));put(275,bmut(1,1,slot=0))
        put(350,bmut(1,0,slot=2));put(400,bmut(1,1,slot=2))
    elif family==3:
        for frame,operation in ((50,filt()),(100,filt(category=1<<63)),(150,filt(mask=0)),
            (200,filt(category=1<<63,mask=1<<63)),(250,filt(category=0)),(300,filt(group=1)),
            (350,filt(group=-1)),(400,filt(category=0x100000001,mask=0x80000000ffffffff)),(450,filt())):put(frame,operation)
    elif family==4:
        values=(capsule((-.2,0),(.2,0),.25),segment((-.4,0),(.4,0)),polygon(),circle((.25,.125),.4))
        for j,value in enumerate(values):
            put(80+j*100,geometry(value,mode=j%2))
            if j%2==0:put(81+j*100,bmut(3))
        put(500,bmut(1,0),geometry(capsule((0,0),(.001,0),.25),mode=0),bmut(1,1),bmut(3))
    elif family==5:
        put(60,bmut(2,*map(bits,(4,.2,-.1,3)),mode=0));put(61,bmut(3))
        put(180,bmut(2,*map(bits,(2,.125,.25,2))));put(181,bmut(3))
        put(300,op(12,0,1,bits(1),0));put(301,op(19,0,1,bits(1)))
        put(420,op(19,0,3,bits(.75)));put(500,bmut(3))
    elif family==6:
        for frame,kind,value in ((50,4,.125),(60,5,.5),(70,6,-1),(170,6,0),(270,6,1),(300,4,0)):put(frame,scalar(kind,value))
        put(100,bmut(7,1),bmut(7,1));put(200,bmut(7,0));put(320,target())
        for j in range(6):put(321+j,vector(j))
        put(450,g.awake(1,0),target(p=(1,.25),q=(1,0),dt=.5))
    elif family==7:
        put(200,filt(mask=0),geometry(circle((.2,0),.5)),bmut(0,1),bmut(1,0),bmut(1,1),filt())
        put(400,bmut(0,0),bmut(0,2),geometry(polygon()),bmut(3))
    elif family==8:
        put(100,op(49,0,0),op(15,0,2,1,1,0x11223344,0xaabbccdd))
        put(150,filt(mask=0),g.step(dt=0,n=1),filt(mask=0,slot=2),op(49,0,1))
        put(200,op(18,0,1),shape(1,parent=1,geometry=circle((.125,0),.5)),op(50,0),op(50,1))
        put(250,filt(),filt(slot=2),op(49,0,2));put(500,op(50,0,1),op(50,1),op(50,2))
    for frame in range(600):
        rows += at.get(frame,[])
        rows.append(g.step(dt=number(int(m['dtH'],16)),n=m['podkroki']))
    return rows

def short_a(m):
    f=int(m['rodzina'][1:]);rows=setup(m,compound=f in (16,19,20,22,29,30,32))
    if f==9:rows += [bmut(0,2),bmut(1,0),bmut(0,2),bmut(1,0),bmut(1,1)]
    elif f==10:
        rows += [bmut(0,k) for k in (0,1,2,1,0,2)]
    elif f==11:rows += [bmut(1,0),bmut(1,0),meta()]
    elif f==12:rows += [bmut(1,1),bmut(1,1),meta()]
    elif f==13:
        rows += [body(3,p=(3,0)),body(4,p=(4,0)),bmut(1,0,slot=3),bmut(1,0,slot=4),bmut(1,0),bmut(1,1,slot=4)]
    elif f==14:rows += [bmut(0,1,slot=2),bmut(1,0,slot=2),bmut(1,1,slot=2),g.awake(2,0),bmut(0,0,slot=2)]
    elif f==15:rows += [filt(),filt(category=1<<63),filt(mask=1<<63),filt(group=1),filt(group=-1),filt()]
    elif f==16:rows += [g.awake(1,0),smut(3,*map(bits,(.25,.5,.1,-.125)),3,0x123456),meta(2,1)]
    elif f==17:rows += [geometry(capsule((0,0),(.001,0),.25),mode=0),geometry(segment()),geometry(circle()),geometry(polygon())]
    elif f==18:rows += [geometry(polygon()),geometry(polygon(((-.5,-.5),(.5,-.5),(0,.5)),.125))]
    elif f==19:rows += [bmut(2,*map(bits,(0,0,0,0)),mode=0),bmut(2,*map(bits,(3,.2,.1,2)),mode=0)]
    elif f==20:rows += [bmut(2,*map(bits,(3,.2,.1,2)),mode=0),bmut(3)]
    elif f==21:rows += [scalar(4,0),scalar(4,.25),scalar(5,.5),scalar(6,-1),scalar(6,0),scalar(6,1)]
    elif f==22:rows += [bmut(7,1),bmut(7,1),bmut(7,0),bmut(7,0)]
    elif f==23:rows += [target(dt=0,mode=0),target(dt=-1,mode=0),target(dt=1,slot=0,mode=0)]
    elif f==24:
        rows += [body(3,p=(3,0),enabled=0),target(p=(3,0),slot=3),target(p=(3.1,0),slot=3)]
        rows += [g.threshold(2,.25),target(p=(.9,0),q=(1,0),slot=2),target(p=(1.15,0),q=(1,0),slot=2),target(p=(1.4,0),q=(1,0),slot=2)]
    elif f==25:rows += [vector(kind) for kind in range(6)]+[vector(kind,slot=0) for kind in range(6)]
    elif f==26:
        rows += [g.world(slot=1),scalar(4,.25,owner=1),op(3,0,1),meta(),body(3,p=(3,0)),meta()]
    elif f==27:rows += [scalar(4,-1),scalar(5,float('inf')),scalar(6,-1),target(dt=0),target(p=(3.402823466e38,0),q=(1,0),dt=1)]
    elif f==28:rows += [geometry(circle(r=0)),geometry(capsule((0,0),(1,0),0)),geometry(segment((0,0),(0,0))),geometry(polygon(((0,0),(1,0))))]
    elif f==29:rows += [geometry(circle((8192,0),1)),bmut(2,1,0,0,0),bmut(3)]
    elif f==30:rows += [g.force(1,1,value=(3,4)),geometry(circle(r=0)),scalar(4,.125),meta()]
    elif f==31:rows += [filt(mask=0),bmut(1,0),bmut(1,1),filt(),meta()]                                                
    elif f==32:rows += [bmut(2,*map(bits,(4,.2,0,3)),mode=0),geometry(circle((.25,0),.5)),op(19,0,1,bits(1))]
    else:raise ValueError('Unimplemented short family '+str(f))
    return rows

def world_mut(kind,*values,owner=0,mode=1):return op(82,owner,mode,kind,*values)
def flag(target,event,value=1,reg=1,owner=0,mode=1):return op(83,owner,target,reg,mode,event,value)
def name(value=b'',reg=1,owner=0,mode=1,null=0):return op(84,owner,reg,mode,null,len(value),*value,*([0]*(32-len(value))))
def object_id(target,value=0,present=1,reg=1,owner=0,mode=1):return op(85,owner,target,reg if target else 0,mode,present,value&0xffffffff,value>>32)
def install(kind,enabled=1,function=0,context=0,owner=0,mode=1):return op(86,owner,mode,kind,enabled,function,context&0xffffffff,context>>32)
def clear(kind,owner=0):return op(87,owner,kind,0)
def pair_rule(kind=0,a=1,b=2,allow=1,direction=(1,0),threshold=0,normal=None,owner=0):
    return op(87,owner,kind,1,a,b,allow,*((*map(bits,(*direction,threshold)),int(normal is not None),*map(bits,normal or (0,0))) if kind else ()))
def material_rule(kind=2,a=3,b=5,value=.5,owner=0):return op(87,owner,kind,1,a,b,bits(value))
def contacts(reg=1,owner=0,mode=1,capacity=0):return op(88,owner,mode,reg,capacity)
def contact_copy(action=0,slot=0,reg=1,owner=0):return op(89,action,owner if action<2 else 0,reg if action<2 else 0,slot)

def history_tail(rows,*,body_reg=1,shape_reg=1):
                                                                              
                                                                       
    rows += [contact_copy(0,0,body_reg),op(49,0,0),op(1,0),contact_copy(2,0),op(50,0),op(37,0),
             g.world(slot=1,gravity=(0,0)),meta(1,body_reg,owner=0),meta(2,shape_reg,owner=1),op(1,1)]
    return rows

def long_b(m):
    family=int(m['rodzina'][1:]);rows=setup(m,compound=family in (4,6))
    if family==3:rows += [geometry(polygon(),slot=1),geometry(polygon(),slot=2)]
    if family==6:rows += [body(3,p=(-.9,0)),shape(4,parent=3,geometry=circle(r=.5))]
    at={}
    def put(frame,*ops):at.setdefault(frame,[]).extend(ops)
    if family==1:
        for frame,kind,value in ((40,1,0),(80,2,0),(120,4,20),(160,1,1.5),(200,2,2),(240,4,100)):
            put(frame,world_mut(kind,bits(value)))
        put(280,world_mut(0,0));put(320,world_mut(0,1));put(360,world_mut(3,*map(bits,(15,5,1))))
        put(400,world_mut(5,bits(.25),bits(-.5)));put(440,world_mut(5,0,0))
        put(480,world_mut(3,*map(bits,(30,10,3))))
    elif family==2:
        put(0,install(0,mode=0,context=0x1234567887654321));put(50,install(0,function=1,mode=0,context=0x1122334455667788),filt(mask=0),filt())
        put(100,install(0,0,mode=0,context=0x8877665544332211),g.op(4,0,1,bits(.1),0,bits(1),0))
        put(150,install(0),pair_rule(allow=0),pair_rule(a=2,b=1,allow=1),filt(mask=0),filt())
        put(250,clear(0),pair_rule(allow=1),pair_rule(allow=0),filt(category=1<<63),filt())
        put(350,op(18,0,2),shape(5,parent=2,geometry=circle(r=.5)),filt(mask=0),filt())
        put(450,clear(0),install(0,0))
    elif family==3:
        put(0,flag(1,2,reg=1),flag(1,2,reg=2),install(1,mode=0,context=0x123456789abcdef0))
        put(100,install(1,function=5,mode=0,context=0xabcdef0123456789))
        put(200,install(1,function=1,mode=0));put(250,install(1,function=2,mode=0))
        put(300,install(1),pair_rule(1,normal=(0,1),direction=(1,0),threshold=-1))
        put(400,clear(1),pair_rule(1,allow=0,direction=(1,0),threshold=1));put(500,install(1,0))
    elif family==4:
        put(0,smut(2,3),smut(2,5,slot=2),install(2,function=3,mode=0),install(3,function=3,mode=0))
        put(100,smut(3,*map(bits,(.125,1.5,.05,-.25)),3,0x123456),g.awake(1,0))
        put(200,install(2),install(3),material_rule(),material_rule(3,value=1.5))
        put(300,material_rule(value=.25),material_rule(3,value=.5),scalar(6,-1))
        put(400,clear(2),clear(3));put(500,install(2,0),install(3,0),g.awake(1,1))
    elif family==5:
        put(0,flag(0,0),flag(0,1),flag(1,2),install(1,mode=0))
        put(100,flag(1,0,0),flag(1,1,0),flag(1,2,0));put(101,op(49,0,0))
        put(200,flag(0,0,0),shape(3,parent=1,geometry=circle((-.25,0),.25)),flag(0,1))
        put(300,flag(1,0),flag(1,1),flag(1,2),g.linear(2,-2,0),op(49,0,1))
        put(400,op(18,0,2),op(50,0),op(50,1));put(401,shape(5,parent=2,geometry=circle(r=.5)))
        put(450,filt(mask=0),g.step(dt=0),filt(mask=0,slot=3),op(49,0,2));put(500,filt(),op(50,2))
    elif family==6:
        put(0,name(b'body-A'),object_id(0,0x1234567800000001),object_id(1,0x2345678900000002),object_id(2,0x3456789a00000003))
        put(50,contacts(),contacts(mode=0,capacity=0),contacts(mode=0,capacity=1),contact_copy(0,0),contact_copy(1,1),contact_copy(3,0),contact_copy(2,1))
        put(150,name('żółw'.encode()),object_id(1,0x55667788aabbccdd),g.force(1,1,value=(1,0)))
        put(250,filt(mask=0),contacts(),contact_copy(3,0),contact_copy(2,1));put(350,filt(),name(b''),object_id(2,present=0))
        put(450,contacts(),contact_copy(0,2),contact_copy(3,2),name(b'0123456789012345678901234567890'))
    for frame in range(600):
        rows += at.get(frame,[]);rows.append(g.step(dt=number(int(m['dtH'],16)),n=m['podkroki']))
    return history_tail(rows)

def short_b(m):
    f=int(m['rodzina'][1:]);rows=setup(m,compound=f in (23,29,30,31,33))
    if f==7:rows += [name(),name(b'A')]
    elif f==8:rows += [name(b'x'*30),name(b'y'*31)]
    elif f==9:rows += [name(b'z'*32),meta()]
    elif f==10:rows += [name(b'a\0b'),meta()]
    elif f==11:rows += [name('żółw'.encode()),name(b'\xc4'),name(b'\xf0\x9f\x90\xa2'),name(b'\xed\xa0\x80')]
    elif f==12:rows += [name(b'a'*32,mode=0),name(null=1,mode=0),name(b'a\0bc',mode=0)]
    elif f==13:rows += [world_mut(1,0),world_mut(2,0),world_mut(5,0,0),world_mut(0,1),world_mut(0,1)]
    elif f==14:rows += [world_mut(1,bits(-1),mode=0),world_mut(2,bits(-1),mode=0),world_mut(3,*map(bits,(-1,-1,-1)),mode=0),world_mut(1,bits(-1)),world_mut(3,*map(bits,(-1,10,3)))]
    elif f==15:
        rows += [world_mut(kind,0x7f800000) for kind in (1,2,4)]
        rows += [world_mut(3,0x7f800000,bits(10),bits(3)),world_mut(3,bits(30),0x7f800000,bits(3)),world_mut(3,bits(30),bits(10),0x7f800000),world_mut(5,0x7f800000,0),world_mut(5,0,0x7f800000)]
    elif f in (16,17):
        kind=f-16;rows += [install(kind,mode=0,context=0x1234567887654321),install(kind,function=1,mode=0,context=0xfedcba9876543210),install(kind,0,mode=0,context=0x1122334455667788),install(kind)]
    elif f==18:rows += [install(k,function=3,mode=0) for k in (2,3)]+[install(k,0,mode=0) for k in (2,3)]+[install(k) for k in (2,3)]
    elif f==19:rows += [pair_rule(1,normal=(0,1)),pair_rule(1,normal=(0,0)),pair_rule(1,threshold=.5),install(1)]
    elif f==20:rows += [material_rule(value=1.5),material_rule(value=-1),material_rule(value=float('inf')),pair_rule(1,direction=(float('inf'),0)),pair_rule(1,threshold=float('nan'))]
    elif f==21:rows += [pair_rule(allow=1),pair_rule(allow=0),pair_rule(a=2,b=1),material_rule(value=.25),material_rule(value=.75),install(0),install(2)]
    elif f==22:rows += [pair_rule(),pair_rule(a=2,b=1),op(18,0,2),shape(4,parent=2,geometry=circle(r=.5)),pair_rule(b=4),meta(2,2)]
    elif f==23:rows += [contact_copy(0,0),contact_copy(1,1),contact_copy(3,0),contact_copy(2,1),contacts()]
    elif f==24:rows += [g.world(slot=1),contacts(owner=1),pair_rule(owner=1),op(18,0,1),contacts(),contact_copy(1,0),clear(0)]
    elif f==25:rows += [flag(1,2),install(1,function=4,mode=0,context=0x1234567887654321),meta(0),meta(2,1)]
    elif f==26:rows += [object_id(k,0x12345678abcdef01) for k in range(3)]+[object_id(k,present=0) for k in range(3)]
    elif f==27:rows += [flag(1,e,0) for e in range(3)]+[flag(1,e) for e in range(3)]+[smut(2,3)]
    elif f==28:rows += [flag(0,0),flag(0,1),shape(4,parent=1,geometry=circle((.25,0),.2)),flag(0,0,0),flag(0,1,0),flag(0,2)]
    elif f==29:rows += [contacts(mode=0,capacity=c) for c in (0,1,512)]+[contacts()]
    elif f==30:rows += [contacts(),filt(mask=0),contacts(),geometry(circle((3,0),.5)),contacts()]
    elif f==31:rows += [contact_copy(0,0),contact_copy(1,1),op(1,0),contact_copy(2,0),contact_copy(3,1),contacts()]
    elif f==32:rows += [install(0,mode=0,context=0x1234567887654321),install(1,mode=0,context=0xabcdef0198765432),install(2,function=3,mode=0),install(3,function=3,mode=0)]
    elif f==33:rows += [geometry(polygon()),geometry(polygon(),slot=2),flag(1,2),install(1,function=5,mode=0),install(1,function=1,mode=0)]
    elif f==34:rows += [name(b'A'),name(b'bad\0name'),install(0),install(0),world_mut(4,bits(-1)),meta(0),meta(1),meta(2),contacts()]
    else:raise ValueError('Unimplemented B family '+str(f))
    return rows

def long_c(m):
    f=int(m['rodzina'][1:]);rows=[g.world(gravity=(0,-10) if f==3 else (0,0),warm=m['warm'])];at={}
    def put(frame,*ops):at.setdefault(frame,[]).extend(ops)
    if f==1:
        for j in range(32):
            rows += [body(j,kind=0 if j%4==0 else 2,p=(2*(j%8),2*(j//8)),v=(0,.125) if j%3==1 else (0,0)),
                shape(2*j,parent=j,geometry=circle(r=.45)),shape(2*j+1,parent=j,geometry=circle((.6,0),.2))]
        put(100,g.op(4,0,8,bits(3),bits(1),bits(1),0),geometry(circle((.5,0),.7),slot=16))
        put(200,g.op(3,0,16));put(201,body(32,p=(3,3),v=(.5,0)),shape(64,parent=32,geometry=circle(r=.5)),shape(65,parent=32,geometry=polygon()))
        put(300,bmut(1,0,slot=8),bmut(0,2,slot=12));put(350,bmut(1,1,slot=8));put(450,filt(category=1<<63,slot=4),filt(slot=4))
    elif f==2:
                                                                          
                                                                            
        for j in range(113):
            side=8 if j<64 else 7;k=j if j<64 else j-64;offset=0 if j<64 else 10000
            rows += [body(j,kind=0 if j%7==0 else 2,p=(offset+2.125*(k%side),2.125*(k//side)),v=(.25,0) if j%11==1 else (0,0)),
                shape(2*j,parent=j,geometry=circle(r=.5)),shape(2*j+1,parent=j,geometry=circle((.6,0),.25))]
        for frame in (100,300):
            for j in (7,21,64,84):put(frame,g.op(4,0,j,bits((10000 if j>=64 else 0)+.9),bits((j%4)*2.125),bits(1),0))
        for j in (10,31,65,96):put(200,bmut(1,0,slot=j));put(250,bmut(1,1,slot=j));put(400,bmut(0,0,slot=j));put(450,bmut(0,2,slot=j))
        put(500,op(3,0,112));put(501,body(113,p=(10001,8)),shape(226,parent=113,geometry=circle(r=.5)),shape(227,parent=113,geometry=circle((.6,0),.25)))
    elif f==3:
        rows += g.floor();rows += g.stack(count=10)
        put(150,bmut(1,0,slot=0));put(200,bmut(1,1,slot=0),g.awake(1,1))
        put(300,smut(0,bits(.125),slot=4),bmut(2,*map(bits,(2,.125,0,2)),slot=4),bmut(3,slot=4))
        put(400,geometry(polygon(),slot=0),g.awake(7,0));put(450,g.awake(7,1),op(19,0,7,bits(.75)))
        put(500,body(11,p=(0,12)),shape(11,parent=11,geometry=polygon()))
    else:
        rows += setup(m)[1:]
        rows += [body(3,p=(-.9,0)),shape(3,parent=3,geometry=circle(r=.5)),g.world(slot=1,gravity=(0,0),warm=m['warm']),body(4,owner=1,p=(8,0)),shape(4,owner=1,parent=4,geometry=circle(r=.5))]
        put(50,install(0),pair_rule(allow=1),op(49,0,0),contact_copy(0,0),contact_copy(0,1),contact_copy(3,0))
        put(100,filt(category=1<<63),geometry(polygon()),bmut(3));put(200,bmut(0,1),bmut(1,0,slot=2));put(250,bmut(1,1,slot=2),bmut(0,2))
        put(300,op(18,0,1),op(49,0,1));put(301,shape(5,parent=1,geometry=circle(r=.5)),contacts(reg=5),contact_copy(2,0),op(50,0),op(50,1))
        put(400,clear(0),install(0,0),object_id(1,0xabcdef0123456789),contact_copy(3,1))
        put(500,op(1,1),g.world(slot=2,gravity=(0,0)),meta(1,4,owner=2))
    for frame in range(600):rows += at.get(frame,[]);rows.append(g.step(dt=number(int(m['dtH'],16)),n=m['podkroki']))
    if f==4:rows += [op(49,0,2),contact_copy(0,2),op(1,0),contact_copy(3,0),op(50,0),op(50,1),op(1,2)]
    else:history_tail(rows)
    return rows

def cases(count=AVAILABLE_N):
    if not 1<=count<=AVAILABLE_N:raise ValueError('Implemented prefix1..160')
    rows=[]
    for m in MANIFEST['przypadki'][:count]:
        recipe=(long_a if m['liczbaKrokowDodatnich'] else short_a) if m['rodzina'][0]=='A' else (long_b if m['liczbaKrokowDodatnich'] else short_b) if m['rodzina'][0]=='B' else long_c
        rows.append(Case(m['id'],m['opis'],tuple(recipe(m))))
    return tuple(rows)

def verify(count=72):
    rows=cases(count)
    for c,m in zip(rows,MANIFEST['przypadki']):
        if len(c.ops)>m['opMax'] or not c.ops:raise ValueError(('opMax',c.id,len(c.ops)))
        positive=[r for r in c.ops if r[0] in (31,32) and number(r[2])>0]
        if len(positive)!=m['liczbaKrokowDodatnich']:raise ValueError(('positive Step count',c.id,len(positive)))
        if any(r[0] in (*range(41,46),51,52,53,63,64) for r in c.ops):raise ValueError(('private PUBLIC operation',c.id))
        if any(len(r)!=65 for r in c.ops):raise ValueError(('64 words',c.id))
        if any(r[2]!=int(m['dtH'],16) or r[3]!=m['podkroki'] for r in positive):raise ValueError(('frozen dt/substeps',c.id))
    return rows

def encode(rows,decimal=False):
    output=['PORT12 '+str(len(rows))]
    for c in rows:
        output.append(f'C {c.id} {len(c.ops)}')
        for seq,row in enumerate(c.ops,1):
            output.append(f'O {seq} {row[0]} '+' '.join(str(v) if decimal else f'{v:08x}' for v in row[1:]))
    return '\n'.join(output)+'\n'

def math_components():
    axes=((0.,0.),(-0.,0.),(0.,-0.),(-0.,-0.),(1,0),(-1,0),(0,1),(0,-1),
          (1,1),(-1,1),(1,-1),(-1,-1),(.25,1),(1,.25),(-.25,-1),(-1,-.25))
    rows=[op(100,*map(bits,pair)) for pair in axes]
    rotations=((1,0),(0,1),(-1,0),(0,-1),(.8,.6))
    rows += [op(101,*map(bits,(*a,*b))) for a,b in zip(rotations,(*rotations[1:],rotations[0]))]
    return tuple(rows)

def encode_math(decimal=False):
    rows=math_components();output=['COMPONENT12 '+str(len(rows))]
    for id,row in enumerate(rows,1):output.append(f'F {id} {row[0]} '+' '.join(str(v) if decimal else f'{v:08x}' for v in row[1:]))
    return '\n'.join(output)+'\n'

def component_cases():
    rows=[Case(j,'math'+str(j),(row,)) for j,row in enumerate(math_components(),1)]
    recipes=[]
    recipes.append([g.world(gravity=(0,0)),body(0,kind=0),body(1),body(2),body(3,awake=0),
        bmut(0,2,slot=0),bmut(0,0,slot=1),bmut(1,0,slot=2),bmut(1,1,slot=2),bmut(1,0,slot=3),bmut(1,1,slot=3)])
    recipes.append(setup({'warm':1})+[install(0,mode=0,context=0x1234567887654321),g.step(),install(0,function=1,mode=0),filt(mask=0),filt(),g.step(),install(0),pair_rule(allow=1),filt(mask=0),filt(),g.step()])
    recipes.append(setup({'warm':1})+[geometry(polygon()),geometry(polygon(),slot=2),flag(1,2),flag(1,2,reg=2),install(1,function=5,mode=0),g.step(),install(1,function=1,mode=0),g.step(),install(1,0),g.step()])
    recipes.append(setup({'warm':1})+[smut(2,3),smut(2,5,slot=2),install(2,function=3,mode=0),install(3,function=3,mode=0),g.step(),g.awake(1,0),smut(0,bits(.125)),install(2),material_rule(),install(3),material_rule(3,value=1),g.awake(1,1),g.step(),install(2,0),install(3,0),g.step()])
    recipes.append(setup({'warm':1})+[body(3,p=(-.9,0)),shape(3,parent=3,geometry=circle(r=.5)),g.step(),contacts(),contact_copy(0,0),contact_copy(0,1),contact_copy(3,0),contacts(mode=0,capacity=1),op(1,0),contact_copy(3,1)])
    recipes.append(g.component_rows(8)+[g.step(),contacts(reg=0),contact_copy(0,0,reg=0),contact_copy(3,0)])
    grid=[g.world(gravity=(0,0))]
    for j in range(8):grid += [body(j,p=(2*(j%4),2*(j//4))),shape(2*j,parent=j,geometry=circle(r=.5)),shape(2*j+1,parent=j,geometry=circle((.6,0),.25))]
    recipes.append(grid+[g.op(4,0,3,bits(.9),0,bits(1),0),g.step(),bmut(1,0,slot=4),bmut(1,1,slot=4),geometry(polygon(),slot=8),g.step()])
    recipes.append([g.world(gravity=(0,-10)),*g.floor(),*g.stack(count=3),*[g.threshold(j,1000) for j in range(1,4)],*[g.step(dt=.125,n=1)]*4,
        bmut(1,0,slot=2),bmut(1,1,slot=2),g.step(),body(4,awake=0),bmut(1,0,slot=4)])
    recipes.append(setup({'warm':1})+[body(3,p=(-.9,0)),shape(3,parent=3,geometry=circle(r=.5)),g.step(),op(49,0,0),filt(mask=0),g.step(dt=0),filt(mask=0,slot=3),op(49,0,1),contact_copy(0,0),op(1,0),op(50,0),op(50,1),contact_copy(3,0)])
    recipes.append(setup({'warm':1})+[name(b'a'*32,mode=0),name(null=1,mode=0),name('żółw'.encode()),object_id(0,0x1234567887654321),object_id(1,0xabcdef0198765432),object_id(2,0xfedcba9876543210),g.step(),object_id(1,0x1122334455667788),g.step(),op(37,0)])
    recipes.append(setup({'warm':1})+[flag(1,2),flag(1,2,reg=2),install(1,function=4,mode=0,context=0x1234567887654321),g.step(),install(1),pair_rule(1,normal=(0,1),threshold=-1),g.step()])
    for ops in recipes:
        if not 1<=len(ops)<=64:raise ValueError('COMPONENT12 opMax64')
        rows.append(Case(len(rows)+1,'world'+str(len(rows)-20),tuple(ops)))
    if len(rows)!=32:raise ValueError('COMPONENT12 exact32')
    return tuple(rows)

def encode_components(rows=None,decimal=False):
    rows=component_cases() if rows is None else rows
    fmt=str if decimal else lambda v:f'{v:08x}'
    output=['COMPONENT12 '+str(len(rows))]
    for c in rows:
        if c.ops[0][0]>=100:
            row=c.ops[0];output.append(f'F {c.id} {row[0]} '+' '.join(map(fmt,row[1:])))
        else:
            output.append(f'C {c.id} {len(c.ops)}')
            for seq,row in enumerate(c.ops,1):output.append(f'O {seq} {row[0]} '+' '.join(map(fmt,row[1:])))
    return '\n'.join(output)+'\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--n',type=int,default=AVAILABLE_N)
    parser.add_argument('--decimal',action='store_true');parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();rows=verify(args.n);args.out.write_text(encode(rows,args.decimal),encoding='ascii',newline='\n')
    print(json.dumps({'N':len(rows),'positive_steps':sum(m['liczbaKrokowDodatnich'] for m in MANIFEST['przypadki'][:args.n]),
                      'operations':sum(len(c.ops) for c in rows)}))
