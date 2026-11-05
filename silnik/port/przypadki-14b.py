pass                                                                      
import argparse
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('inputs14a_for_b',HERE/'przypadki-polaczenia.py')
A=importlib.util.module_from_spec(spec);sys.modules[spec.name]=A;spec.loader.exec_module(A)
MANIFEST_BYTES=(HERE/'polaczenia-14b-przypadki.json').read_bytes()
if hashlib.sha256(MANIFEST_BYTES).hexdigest()!='e04bd8e4c37ceda58236b42f5efef1b6f548f07723cd1b756189ebfc323fe6f0':raise ValueError('M14b annex pin changed')
MANIFEST=json.loads(MANIFEST_BYTES)
Case=A.Case;bits=A.bits;value=A.value
MUTATOR_ARITY={**A.MUTATOR_ARITY,**{k:2 if k in (37,53) else 1 for k in (*range(32,41),*range(48,57))}}
NEW_ARITY=A.NEW_ARITY

def op(code,*words):
    if code!=203:return A.op(code,*words)
    if len(words)<4 or words[3] not in MUTATOR_ARITY or len(words)!=4+MUTATOR_ARITY[words[3]]:raise ValueError('203 kind/arity')
    if any(type(x) is not int or not 0<=x<=0xffffffff for x in words):raise ValueError('u32 input required')
    return {'opcode':code,'a':tuple(words)}

def default(type,dest=0):return op(200,type,dest)
def field(index,word,dest=0):return op(202,dest,index,word)
def mutate(kind,*words,mode=1,owner=0,target=0):return op(203,mode,owner,target,kind,*words)
create=A.create;read=A.read;destroy=A.destroy;step=A.step;body=A.body;shape=A.shape;world=A.world

def description(type):
    if type==0:return [0,0,0,0,bits(1),0,0,0,0,0,bits(100000),0,0,0,0,0,0,0]
    words=[0]*(20 if type==5 else 21);words[15 if type==5 else 4]=bits(.25 if type==5 else 1);return words

def pair(type,*,contact=False,disabled=False,joint=True):
    rows=[world(),body(0,kind=0),body(1,p=(.5 if contact else 2,0),enabled=int(not disabled))]
    if contact:rows += [shape(0,parent=0,geometry=A.legacy.circle(r=1)),shape(1,parent=1,geometry=A.legacy.circle(r=1))]
    rows += [default(type)]
    if contact:rows += [field(16 if type==5 else 17 if type==4 else 14,1)]
    if joint:rows += [create()]
    return rows

def args_for(k):
    if k in (0,1):return [0,0]
    if k==3:return [bits(1),0]
    if k in (37,53):return [bits(-.5),bits(.5)]
    if k in (32,36,38,48,52,54):return [1]
    if k in (33,34,40,49,50,56):return [bits(2)]
    if k in (39,55):return [bits(-2)]
    return [0]

def defect_words(type,field_name,witness,route):
    desc=description(type);setter=route.startswith('203/');k=int(route.split('/')[1]) if setter else None
    args=args_for(k) if setter else None
    name=field_name
    if name.startswith('anchor'):
        index={'anchorA.x':0,'anchorA.y':1,'anchorB.x':2,'anchorB.y':3}[name.removesuffix('-finite')]
        index=index%2 if setter else index
    elif name.startswith('reference'):index=0 if setter else 4 if type==5 else 6
    elif name.startswith('target'):index=0 if setter else 5 if type==5 else 7
    elif name.startswith('drawSize'):index=15
    elif name.startswith('hertz'):index=0 if setter else 7 if type==5 else 9
    elif name.startswith('damping'):index=0 if setter else 8 if type==5 else 10
    elif name.startswith('max'):index=0 if setter else 13 if type==5 else 15
    elif name.startswith('speed'):index=0 if setter else 14 if type==5 else 16
    elif name=='axis':
        if setter:return [0,0]
        desc[4:6]=[0,0];return desc
    else:index=0
    target=args if setter else desc
    lower=0 if setter else 10 if type==5 else 12
    if name in ('angle-lower','angle-upper','limit-order','lower-finite','upper-finite'):
        pair_values={'angle-lower':(-4,0),'angle-upper':(0,4),'limit-order':(1,0),'lower-finite':(-float('inf'),0),'upper-finite':(0,float('inf'))}[name]
        target[lower:lower+2]=map(bits,pair_values)
    else:
        token=witness['wordOrValue']
        word=int(token,16) if re.fullmatch('[0-9a-f]{8}',token) else bits(float('inf') if token=='+Inf' else -1)
        target[index]=word
    return target

def guard_case(row):
    key,route,witness=row['key'],row['route'],row['witness'];ga=[0]*64;kind=0
    match=re.search(r'-(5|4)-',key);type=int(match[1]) if match else 4 if key.startswith('AXIS') else 5
    if key.startswith('TYPE-'):
        type=witness['jointType'];ops=pair(type)
        if route.startswith('203/'):
            k=int(route.split('/')[1]);ops += [mutate(k,*args_for(k))]
        else:kind=4;ga[2]=int(route.split('/')[1].split(':')[0])
    elif key.startswith('LOCK-'):
        ops=pair(type,contact=True);kind=5;ga[2]=int(route.split('/')[0])
        if ga[2]==201:ga[4:7]=[0,1,0]
        else:
            ga[3]=int(route.split('/')[1]);args=args_for(ga[3]);ga[4:4+len(args)]=args
        ops += [op(83,0,1,1,0,2,1),op(86,0,0,1,1,6,0,0),step()]
    elif key.startswith('COPY-'):
        kind=10;ga[0]={'description':2,'view':0,'bodyJointList':1}[route]
        ops=pair(type)+[op(207,0,0,0),op(207,0,0,1),op(206,1,0,1,0,2),step()]
    elif key.startswith('ATTACHED-'):
        kind=8;ga[1]=1;disable=route=='Disable';noop=witness.get('state')=='actual-noop';after=witness.get('state')=='after-last-destroy'
        ops=pair(type,disabled=disable and noop)
        if after:ops += [destroy()]
        ga[2]=int(disable);ga[3]=0 if disable else 2 if noop else 1
    else:
        kind=6;ga[2]=int(route.split('/')[0]);ops=pair(type)
        if key.startswith('DOM-'):data=defect_words(type,witness['field'],witness,route)
        else:
            data=args_for(int(route.split('/')[1])) if route.startswith('203/') else description(type)
            if key.startswith('AXIS'):
                at=0 if ga[2]==203 else 4;data[at:at+2]=[int(witness['axis.x'],16),int(witness['axis.y'],16)]
            elif key.startswith('ANGLE') or key.startswith('TARGET'):
                target=key.startswith('TARGET');at=0 if ga[2]==203 else (5 if target else 4 if type==5 else 6)
                data[at]=int(witness['target' if target else 'reference'],16)
            elif key.startswith('LIMIT-ANGLE'):
                at=0 if ga[2]==203 else 10
                bound=bits(value(bits(.99))*value(0x40490fdb));data[at:at+2]=[bound|0x80000000,bound]
            else:raise ValueError('unknown guard '+key)
        if ga[2]==201:ga[4:4+len(data)]=data;ga[25]=type
        else:ga[3]=int(route.split('/')[1]);ga[4:4+len(data)]=data
    return Case(row['id'],key,'GUARD',row['rodzina'],tuple(ops),guard_kind=kind,ga=tuple(ga))

def short(entry):
    type=entry['jointTypes'][0];v=entry['wariant'];base=32 if type==5 else 48
    rows=pair(type)
    if v==1:rows += [read(),destroy(),create(target=1),read(target=1),op(212,1,0,0)]
    elif v==2:
        rows=pair(type,joint=False)
        for index,value_ in ((4,4),(5,-4)) if type==5 else ((4,3),(5,4)):
            rows += [field(index,bits(value_))]
        rows += [create(mode=0),read(),mutate(2,bits(4),mode=0),read()]
        if type==5:rows += [mutate(35,bits(-4),mode=0),read()]
    elif v in (3,4):
        rows += [step(),read()]
        if v==3:
            for k in (base,base+4,base+6):rows += [mutate(k,1),read(),mutate(k,1),read(),mutate(k,0),read()]
        else:rows += [mutate(base+5,bits(-.5),bits(.5)),read(),mutate(base+5,bits(-.5),bits(.5)),read(),mutate(base+5,bits(-1),bits(1)),read()]
    elif v==5:
        for speed in (2,-2,0):rows += [mutate(base+7,bits(speed)),read()]
    elif v in (6,7):
        rows += [mutate(base,1),mutate(base+1,bits(2)),mutate(base+3,bits(.5)),step(),read()]
        if v==7:rows += [mutate(2,bits(.25)),A.old(A.legacy.g.linear(1,.25,.5)),step(),read()]
    elif v in (8,9):
        rows += [op(207,0,0,0),op(207,0,0,1),op(206,1,0,1,0,2),op(206,1,0,1,0,3),step()]
        rows += [op(209,0,4,38,1) if v==8 else op(209,2,0,0,17),op(208,0),op(208,1),op(208,2),op(208,3),read(),destroy(),create(target=1),op(208,0),op(208,2),read(target=1)]
    elif v in (10,11):
        rows += [step(),A.old(A.legacy.g.awake(1,0)),mutate(base+1,bits(2)),read()]
        if v==11:rows += [mutate(6),read(),step(),read()]
    else:rows += [read(),op(206,0,0,0,128,0)]
    return tuple(rows)

def bridge_ball_chain(entry):
    pass                                                                        
    rows=[world(gravity=(0,-10),warm=int(entry['warmStarting'])),body(0,kind=0),default(5)]
    rows += [field(i,bits(v) if i in (7,8,13) else v) for i,v in ((6,1),(7,2),(8,.7),(12,1),(13,200))]
    rows += [field(0,bits(-16)),field(1,bits(20)),field(2,bits(-.5))]
    for i in range(32):
        rows += [body(i+1,p=(-15.5+i,20),damping=.1,angular_damping=.1),
                 shape(i,parent=i+1,geometry=A.legacy.box(h=(.5,.125)),density=20,events=0,hit=0),create(i,i+1,i,mode=0)]
        if i==0:rows += [field(0,bits(.5)),field(1,0)]
    rows += [field(2,bits(16)),field(3,bits(20)),create(32,0,32,mode=0)]
    for i in range(2):
        rows += [body(33+i,p=(-8+8*i,22)),shape(32+i,parent=33+i,geometry=A.legacy.polygon(((-.5,0),(.5,0),(0,1.5))),density=20,events=0,hit=0)]
    for i in range(3):
        rows += [body(35+i,p=(-6+6*i,25)),shape(34+i,parent=35+i,geometry=A.legacy.circle(r=.5),density=20,events=0,hit=0)]
    rows += [default(5),field(0,0),field(1,bits(4)),field(2,bits(-.5)),field(7,bits(4)),field(12,1),field(13,bits(100))]
    for i in range(8):
        rows += [body(38+i,p=(.5+i,4)),shape(37+i,parent=38+i,geometry=A.legacy.capsule(p1=(-.5,0),p2=(.5,0),r=.125),density=20,category=1,mask=2,events=0,hit=0),
                 create(0 if i==0 else 37+i,38+i,33+i,mode=0)]
        if i==0:rows += [field(0,bits(.5)),field(1,0),field(6,1)]
    rows += [body(46,p=(12,4)),shape(45,parent=46,geometry=A.legacy.circle(r=4),density=20,category=2,mask=1,events=0,hit=0),field(2,bits(-4)),create(45,46,41,mode=0)]
    for frame in range(1200):
        if frame==600:rows += [op(3,0,11)]
        if frame in (900,901):rows += [A.old(A.legacy.g.awake(17,int(frame==901)))]
        rows += [step(entry['subSteps'],raw=True)]
    return tuple(rows)


def long_public(entry):
    family=entry['nativePilotFamily'];v=entry['wariant'];typ=entry['jointTypes'][0]
    rows=[world(gravity=(0,-10),warm=int(entry['warmStarting'])),body(0,kind=0)]
    count=15 if family==11 else 4
    for i in range(1,count):
        rows += [body(i,p=((i-1)*1.5,4 if family!=11 else 0),
                      kind=1 if family==0 and i==2 and v%2 else 2,
                      q=(.8,.6) if family==6 and i==1 else (1,0),
                      w=.25 if family==6 and i==1 else 0,
                      awake=0 if family==10 else 1,fixed=int(family==9)),
                 shape(i-1,parent=i,geometry=A.legacy.circle(r=.8 if family==11 else .5),density=2 if i==2 else 1,events=1,hit=1)]
    if family==11:
        for dest,t in enumerate((0,4,5)):rows += [default(t,dest)]
        for i in range(2,count):rows += [create(1,i,i-2,description=(i-2)%3,mode=0)]
    else:
        rows += [default(typ)]
        if typ==5:
            rows += [field(0,bits(.125)),field(3,bits(.25))]
            if family==1:rows += [field(4,bits(.35)),field(5,bits(-.2)),field(6,1),field(7,bits(2)),field(8,bits(.7))]
            if family in (2,3,5):rows += [field(9,1),field(10,bits(-.5)),field(11,bits(.5))]
            if family in (3,5):rows += [field(6,1),field(7,bits(2)),field(8,bits(.7)),field(12,1),field(13,bits((0,12,200)[v%3])),field(14,bits((0,3,-3)[v%3]))]
        else:
            rows += [field(0,bits(.25)),field(3,bits(-.125)),field(4,bits(.8)),field(5,bits(.6))]
            if family in (7,10):rows += [field(8,1),field(9,bits(0 if v%2 else 2)),field(10,bits(.7))]
            if family in (8,9):rows += [field(11,1),field(12,bits(-.75)),field(13,bits(.75))]
            if family in (7,8,10):rows += [field(14,1),field(15,bits(100)),field(16,bits((0,3,-3)[v%3]))]
        rows += [create(1 if family==6 else 0,1 if family!=6 else 2,0,mode=0),create(1,3,1,mode=0)]
    rows += [op(207,0,0,0),op(206,1,0,1,0,2)]
    for frame in range(1200):
        if family==5 and frame in (300,600,900):
            rows += [mutate(32,1),mutate(32,1),mutate(32,0),mutate(32,1),mutate(36,0),mutate(36,1),mutate(37,bits(-.5),bits(.5)),mutate(37,bits(-.25),bits(.25))]
        if family==10 and frame in (600,900,901):
            rows += [A.old(A.legacy.g.awake(1 if frame!=901 else 3,int(frame==901))),mutate(55,bits(-2 if frame==900 else 2))]
        if frame in (0,599,899,1199):rows += [op(208,0),op(208,2)]
        rows += [step(entry['subSteps'],raw=True)]
    rows += [read(),op(208,0),op(208,2)]
    return tuple(rows)


def cases(profile='DIRECT',N=None):
    entries=MANIFEST[{'DIRECT':'direct','PUBLIC':'przypadki','GUARD':'guards'}[profile]]
    count=len(entries) if N is None else N
    if type(count) is not int or not 1<=count<=len(entries):raise ValueError('prefix1..N required')
    result=[]
    for entry in entries[:count]:
        if profile=='DIRECT':
            fixtures=tuple(tuple(int(w,16) for w in g['words']) for g in entry['frozenFixtureGroups'])
            ops=[op(210,0,0,0),op(210,0,1,0),op(210,0,2,1),op(210,0,2,0)]
            if 'mathFixtureId' in entry:ops += [op(210,entry['mathFixtureId'],0,0)]
            case=Case(entry['id'],entry['key'],profile,entry['rodzina'],tuple(ops),fixtures)
        elif profile=='GUARD':case=guard_case(entry)
        elif entry['id']<=24:case=Case(entry['id'],entry['key'],profile,entry['rodzina'],short(entry))
        elif 49<=entry['id']<=54:case=Case(entry['id'],entry['key'],profile,entry['rodzina'],bridge_ball_chain(entry))
        else:case=Case(entry['id'],entry['key'],profile,entry['rodzina'],long_public(entry))
        if not 1<=len(case.ops)<=entry['opMax']:raise ValueError(case.key+' operation bound')
        positive=sum(o['opcode'] in (31,32) and value(o['a'][1])>0 for o in case.ops)
        if not entry.get('positiveStepsMin',entry.get('positiveSteps',0))<=positive<=entry.get('positiveStepsMax',entry.get('positiveSteps',0)):raise ValueError(case.key+' Step allocation')
        result.append(case)
    return tuple(result)

def text(items,decimal=False):
    if not items or [c.id for c in items]!=list(range(1,len(items)+1)):raise ValueError('prefix IDs required')
    word=str if decimal else lambda x:f'{x:08x}'
    yield f'PORT14 B {items[0].profile} {len(items)}\n'
    for case in items:
        if case.profile=='GUARD':
            yield f'G14 {case.id} {case.guard_kind} {case.seed_after} {len(case.ops)}\n'
            yield f'GA14 {case.id} '+' '.join(map(word,case.ga))+'\n'
        else:yield f'C {case.id} {len(case.ops)}\n'
        for group,words in enumerate(case.fixtures):
            fixture=0 if group<5 else next(o['a'][0] for o in case.ops if o['opcode']==210 and o['a'][0])
            yield f'F14 {case.id} {fixture} {group} {len(words)} '+' '.join(map(word,words))+'\n'
        for seq,call in enumerate(case.ops,1):
            code,words=call['opcode'],call['a'];prefix=f'O {seq} {code} '+(f'{len(words)} ' if code>=200 else '')
            yield prefix+' '.join(map(word,words))+'\n'
            for tag,key in (('P13B','points'),('U13B','materials')):
                for i,row in enumerate(call.get(key,())):yield f'{tag} {case.id} {seq} {i} '+' '.join(map(word,row))+'\n'

def execution_manifest(items):
    result=[]
    for case in items:
        entry={'id':case.id,'key':case.key,'profile':case.profile,'family':case.family,'O':len(case.ops),'positiveSteps':sum(o['opcode'] in (31,32) and value(o['a'][1])>0 for o in case.ops),'inputs':{}}
        for decimal,side in ((False,'c'),(True,'d')):
            data=''.join(text((replace(case,id=1),),decimal)).encode('ascii')
            if any(len(x)>2048 for x in data.splitlines()):raise ValueError('input envelope '+case.key)
            entry['inputs'][side]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'scope':'isolated case renumbered1 with its own header'}
        result.append(entry)
    return {'schema':1,'protocol':'PORT14B','frozenSHA':hashlib.sha256(MANIFEST_BYTES).hexdigest(),'generatorSHA':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':result,'complete':False,'unexecuted':['native C0/C1/D']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=('PUBLIC','DIRECT','GUARD'),required=True);parser.add_argument('--N',type=int);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();items=cases(args.profile,args.N);args.out.mkdir(parents=True,exist_ok=True)
    for decimal,side in ((False,'c'),(True,'d')):(args.out/(args.profile.lower()+'-'+side+'.input')).write_text(''.join(text(items,decimal)),encoding='ascii',newline='\n')
    (args.out/'manifest.json').write_text(json.dumps(execution_manifest(items),indent=2)+'\n',encoding='utf-8')
