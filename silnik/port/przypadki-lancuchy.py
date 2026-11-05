pass                                                                    
import argparse
from dataclasses import dataclass
import json,struct
from pathlib import Path

HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))
def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def value(u):return struct.unpack('<f',struct.pack('<I',u))[0]
def f32(f):return value(bits(f))
def op(kind,words):
    if len(words)!=64:raise ValueError('64 transport words required')
    return (kind,*words)
def distance(a,b=((0,0),),*,seed=(),radii=(0,0),xf=(0,0,1,0),xfb=None,use=False,mode=0,trace=False,capacity=0,canary=False):
    w=[0]*64;w[0:3]=[mode,len(a),bits(radii[0])]
    for i,(x,y) in enumerate(a):w[3+2*i:5+2*i]=[bits(x),bits(y)]
    w[19:23]=map(bits,xf);w[23:25]=[len(b),bits(radii[1])]
    for i,(x,y) in enumerate(b):w[25+2*i:27+2*i]=[bits(x),bits(y)]
    w[41:45]=map(bits,xf if xfb is None else xfb);w[45]=int(use);w[46]=len(seed)
    for i,(ia,ib) in enumerate(seed):w[47+i]=ia;w[50+i]=ib
    if canary:
        for i in range(len(seed),3):w[47+i]=161+i;w[50+i]=177+i
    w[53:55]=[capacity,int(trace)];return op(0,w)
def proxy(points,*,radius=0,offset=None,mode=0):
    w=[0]*64;w[:3]=[mode,len(points),bits(radius)]
    for i,(x,y) in enumerate(points):w[3+2*i:5+2*i]=[bits(x),bits(y)]
    if offset is not None:w[23:27]=map(bits,offset)
    return op(1 if offset is None else 2,w)

S2=[[(1,0),(2,0)],[(-2,0),(-1,0)],[(-1,1),(1,1)],[(0,1),(1,1)],[(-1,1),(0,1)],[(1,1),(1,1)]]
S3=[[(1,1),(2,1),(1,2)],[(-1,1),(1,1),(0,2)],[(1,-1),(2,0),(1,1)],
    [(-2,1),(-1,1),(-2,2)],[(1,-2),(2,-2),(1,-1)],[(2,0),(1,1),(1,-1)],[(-1,-1),(1,-1),(0,1)],
    [(0,1),(1,1),(0,2)],[(-1,0),(1,0),(0,1)],[(0,-1),(1,0),(0,1)],
    [(-1,1),(0,1),(-1,2)],[(1,-1),(2,-1),(1,0)],[(1,0),(0,1),(0,-1)],
    [(-1,-value(1)),(1,-value(1)),(0,1)]]
                                                                           
LIMIT_A=[tuple(map(value,p)) for p in ((0xc407ec67,0xc13480d9),(0xc407ec67,0xc13480d8),(0xc4873151,0xc12980f5),(0x3fd4d9ec,0xc16029e9))]
LIMIT_B=[tuple(map(value,p)) for p in ((0x45867264,0x3fc0fb1e),(0xc6d7960b,0x44de3c99),(0x3c40d65e,0xc09d7647),(0xc38560fc,0xbe003160),(0xbb06279f,0xc09d75b6))]
LIMIT_SEED=((1,1),(1,0),(1,3))
@dataclass(frozen=True)
class Case:
    id:int
    family:str
    memory:str
    ops:tuple

def item(case_id,j):
    group=(case_id-1)//16;v=(case_id-1)%16;mode=(j//8)%2
    xf=(j/16,(-j)/32,1,0)
    if group==0:
        if case_id==8 and j==1:return proxy([(i/2,(-1 if i%2 else 1)/32) for i in range(10)],radius=1/64,offset=(1/8,-1/16,0,1))
        if case_id==15:return proxy([(0,0),(1,0)],radius=-1,mode=0)
        if case_id==16:return proxy([(1,0)],offset=(0,0,2,0),mode=0)
        count=(0,1,8,9,10,2,3,8,1,2,3,4,5,6)[v%14]
        points=[(i/2,(-1 if i%2 else 1)*j/32) for i in range(count)]
        offset=None if v<5 else (j/8,-j/16,0 if v%2 else 1,1 if v%2 else 0)
        return proxy(points,radius=j/64,offset=offset,mode=mode)
    if group==1:
        if case_id==17 and j==1:return distance([(1,0),(0,1)],[(3,0)],mode=0,canary=True)
        variants=[([(0,0)],[(2,0)]),([(-1,-1),(1,-1),(1,1),(-1,1)],[(3,0)]),
          ([(0,0),(0,0),(1,0)],[(2,1)]),([(-0.0,0),(1,-0.0)],[(2,0)]),
          ([(x/4,(x*x)%7/4) for x in range(8)],[(3,2)])]
        a,b=variants[v%len(variants)]
        if v%3==1:a,b=b,a
        q=((1,0),(0,1),(-1,0),(0,-1))[j%4]
        return distance(a,b,xf=(*xf[:2],*q),mode=mode,canary=True)
    if group==2:
        a=S2[v%len(S2)];scale=(.5,1,2)[j%3]
        a=[(x*scale,y*scale) for x,y in a]
        return distance(a,seed=((0,0),(1,0)),xf=xf,mode=mode,canary=True)
    if group==3:
        if case_id==55 and j==2:
            return distance([(0,0),(3,0),(0,3)],[(1,1),(1.5,1),(1,1.5)],seed=((0,0),(1,1),(2,2)),mode=mode)
        a=S3[v] if v<14 else S3[5 if v==14 else 2]
        return distance(a,seed=((0,0),(1,0),(2,0)),xf=(0,0,1,0),mode=mode)
    if group==4:
        if case_id==73 and j==1:return distance(S3[6],mode=mode)
        if case_id==65:return distance([(0,0)],[(2,0)],mode=mode,canary=True)
        if 66<=case_id<=68:return distance([(0,0)],[(value(bits(2**-23)+case_id-67),0)],mode=mode,canary=True)
        if 69<=case_id<=72:return distance([(-1,0),(1,0)],seed=((0,0),(1,0)),mode=mode,canary=True)
        if 73<=case_id<=76:return distance(S3[6],seed=((0,0),(1,0),(2,0)),mode=mode)
        if case_id==80:return distance(LIMIT_A,LIMIT_B,seed=LIMIT_SEED,mode=mode)
        return distance([(0,0),(1,0)],[(1+(j+1)/256,1/32)],mode=mode,canary=True)
    if group==5:
        if 81<=case_id<=84:
            count=case_id-81;return distance(S3[1],seed=tuple((i,0) for i in range(count)),xf=xf,mode=mode,canary=True)
        if 85<=case_id<=92:
            variant=(case_id-85)%4
            a=[(-1,-1),(1,-1),(1,1),(-1,1)]
            b=[(-.25,-.25),(.25,-.25),(0,.25)]
            return distance(a,b,xfb=(2+j/128,variant/16,1,0),mode=mode)
        a,b=([(0,0),(1,0)],[(2,1)]) if j%2 else (S3[1],[(3,0)])
        if case_id%2:a,b=b,a
        return distance(a,b,mode=mode,canary=True)
    if group==6:
        if case_id==97:return distance([(0,0)],[(2,0)],radii=(.25,.5),use=False,mode=mode)
        if 98<=case_id<=100:
            u=bits(f32(f32(.1)*f32(.005)))+case_id-99
            return distance([(0,0)],[(value(u),0)],radii=(.000125,.000125),use=True,mode=mode)
        if case_id==101:return distance([(0,0)],[(2,0)],radii=(.25,.5),use=True,mode=mode)
        if case_id==102:return distance([(0,0)],[(1,0)],radii=(1,1),use=True,mode=mode)
        return distance([(0,0)],[(2,0)],radii=(1.3,.1) if case_id%2 else (.1,1.3),use=True,mode=mode,canary=True)
    cap=(0,1,2,23)[v%4]
    if v<4:return distance([(0,0),(1,0)],[(2,1)],trace=True,capacity=cap)
    if v<7:return distance(S2[v-4],seed=((0,0),(1,0)),trace=True,capacity=cap,canary=True)
    if v<12:return distance(S3[(2,3,4,5,6)[v-7]],seed=((0,0),(1,0),(2,0)),trace=True,capacity=cap)
    if v==12:return distance([(0,0)],[(2,0)],trace=True,capacity=cap)
    if v==13:return distance([(0,0)],[(0,0)],seed=((0,0),),trace=True,capacity=cap)
    return distance(LIMIT_A,LIMIT_B,seed=LIMIT_SEED,trace=True,capacity=cap)

def cases(N=128):
    if not 1<=N<=128:raise ValueError('N in1..128')
    result=[]
    for m in MANIFEST['przypadki']:
        if m['profil']!='PORT13A' or m['id']>N:continue
        count=1 if m['id']>=113 else 32
        operations=tuple(item(m['id'],j) for j in range(count))
        if count>m['opMax']:raise ValueError('manifest operation bound')
        result.append(Case(m['id'],m['rodzina'],m['pamiec'],operations))
    if len(result)!=N:raise ValueError('manifest completeness')
    return tuple(result)

def text(items,profile='R',decimal=False):
    yield f'PORT13A {profile} {len(items)}\n'
    for case in items:
        yield f'C {case.id} {len(case.ops)}\n'
        for seq,row in enumerate(case.ops,1):
            payload=' '.join(str(x) if decimal else f'{x:08x}' for x in row[1:])
            yield f'O {seq} {row[0]} {payload}\n'

def write(directory,N=128):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);items=cases(N)
    for profile in ('R','D'):
        for decimal,suffix in ((False,'c'),(True,'duckling')):
            with (directory/f'{profile}-{suffix}.csv').open('w',encoding='ascii',newline='\n') as f:f.writelines(text(items,profile,decimal))
    return items

                                                                            
@dataclass(frozen=True)
class ChainCase:
    id:int
    family:str
    ops:tuple
    guard_required:tuple=()

def operation13b(code,*words,points=(),materials=()):
    if len(words)>64:raise ValueError('13b operation width')
    return {'opcode':code,'a':tuple((x&0xffffffff) for x in words)+(0,)*(64-len(words)),
            'points':tuple(tuple(p) for p in points),'materials':tuple(tuple(m) for m in materials)}

def chain13b(points=None,*,loop=False,materials=None,target=0,owner=0,parent=0,mode=1,
             object_id=None,category=1,mask=0xffffffffffffffff,group=0,sensor=0,encoded=False):
    points=[(2,0),(1,0),(-1,0),(-2,0)] if points is None else points
    pp=tuple(tuple(p) if encoded else tuple(map(bits,p)) for p in points)
    mm=((bits(.6),0,0,0,0,0),) if materials is None else tuple(tuple(m) for m in materials)
    obj=0 if object_id is None else object_id
    return operation13b(100,mode,owner,parent,target,len(pp),int(loop),len(mm),int(object_id is not None),
                       obj&0xffffffff,obj>>32,category&0xffffffff,category>>32,mask&0xffffffff,mask>>32,
                       group,sensor,points=pp,materials=mm)

def _legacy13b():
    import importlib.util,sys
    if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
    spec=importlib.util.spec_from_file_location('lancuchy_inputs11',HERE/'przypadki-sen.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m

def _loop13b(n):
    if n==4:return [(0,0),(4,0),(4,4),(0,4)]
    if n==5:return [(0,0),(4,0),(5,2),(2,5),(0,3)]
                                                                      
    return [(i,i*i/128) for i in range(n//2)]+[(i,-4-i*i/128) for i in reversed(range(n//2))]

def cases13b(N=64):
    if not 1<=N<=64:raise ValueError('PORT13B N in1..64')
    old=_legacy13b();wrap=lambda row:operation13b(row[0],*row[1:])
    result=[]
    for ident in range(1,N+1):
        v=(ident-1)%8;family='B'+str((ident-1)//8+1)
        rows=[wrap(old.world(speed=100)),wrap(old.body(kind=0))];guards=()
        def add(code,*a):rows.append(operation13b(code,*a))
        def create(**kw):rows.append(chain13b(**kw))
        def read(reg=0,owner=0):add(102,1,owner,reg)
        if ident<=16:
            loop=ident<=8;n=(4,5,80,4,5,80,4,5)[v] if loop else (4,5,8,80,4,5,8,80)[v]
            pp=_loop13b(n) if loop else [(i,(i%3)/16) for i in range(n)]
            if v%2:pp.reverse()
            mm=[(bits(.125+j/128),bits(j/64),bits(j/256),bits(-j/32),(0x80000000+j)&0xffffffff,0x123400+j) for j in range(n)] if v>=4 else None
            create(points=pp,loop=loop,materials=mm,object_id=0x800000018000ffff,sensor=v%2,
                   category=0x8000000100000001,mask=0x80000001ffffffff,group=-3)
            for cap in (0,1,128):add(102,0,0,0,cap)
            read();add(104,1,0,0);add(105,1,0,0);add(106,0,0,0)
            add(108,0,(n if loop else n-3)-1,123);add(101,1,0,0);add(107,0)
        elif ident<=24:
            for target in range(3):create(target=target,points=[(i,target*4) for i in range(5)])
            add(106,0,1,0);add(106,0,2,1)
            first=(2,1,0,2,1,0,2,1)[v];order=[first,*[x for x in (2,1,0) if x!=first]]
            for reg in order:add(101,1,0,reg);read(reg)
            create(target=3);read(3);add(107,0);add(107,1)
        elif ident<=32:
            if ident in (25,26):
                for target in range(4 if ident==26 else 3):create(target=target)
                if ident==26:add(101,1,0,1)
                add(106,0,0,0);add(3 if ident==25 else 1,0,0) if ident==25 else None
                if ident==26:add(1,0)
                add(107,0);read()
            elif ident==27:
                add(80,0,0,1,1,0);create();add(80,0,0,1,1,1);add(80,0,0,1,1,0);read()
            elif ident in (28,29):
                rows=[rows[0],wrap(old.body(kind=ident-27,mode=0))]
                create(mode=0);read();add(80,0,0,1,0,ident-27);add(101,0,0,0)
            else:
                create(points=[(-100,50),(-1,0),(1,0),(100,-50)])
                rows.append(wrap(old.shape(1,parent=0,geometry=old.circle(r=.5),events=0)))
                add(19,0,1,bits(2));add(80,0,0,1,0,0)
                rows.append(wrap(old.g9.transform(0,0,(.5,-.25))))
                read();add(105,1,0,0)
        elif ident<=40:
            n=(4,5,8,4,5,8,5,8)[v];loop=v%2==1
            pp=_loop13b(n) if loop else [(i,0) for i in range(n)]
            mm=[(bits(.25+j/16),bits(j/8),bits(j/32),bits(-j/4),j,0xabc000+j) for j in range(n)]
            create(points=pp,loop=loop,materials=mm);read()
            for kind,value_ in ((0,0),(0,bits(.875)),(1,bits(1.25)),(2,0x8000ffff),(2,0xffffffff)):
                add(103,1,0,0,kind,value_);read()
            add(103,0,0,0,1,bits(-.25));read();add(103,1,0,0,1,bits(-.25));read()
        elif ident<=48:
            create(points=[(i,0) for i in range(8)])
            rows.extend([wrap(old.world(slot=1,speed=100)),wrap(old.body(slot=1,owner=1,kind=0))])
            create(owner=1,parent=1,target=1)
            for code in (101,102,103):add(code,1,1,0)
            add(104,1,1,0);add(105,1,1,0)
            rows.append(wrap(old.shape(6,parent=0,geometry=old.circle(r=.5),events=0)))
            add(104,1,0,6);add(105,1,0,6)
            for cap in (0,1,5,128):add(102,0,0,0,cap)
            add(106,0,0,0);add(101,1,0,0);read();add(104,1,0,0)
            if ident>=45:
                add(1,0);rows.append(wrap(old.world(slot=0,speed=100)));rows.append(wrap(old.body(slot=2,kind=0)))
                create(target=2,parent=2);read();read(2)
            add(107,0)
        elif ident==49:
            for n in (0,1,2,3):create(points=[(i,0) for i in range(n)]);add(91,0,0,0,1)
            create();read()
        elif ident==50:
            for n in (0,2,3):create(materials=[(bits(.6),0,0,0,0,0)]*n)
            create(materials=[(bits(.6),0,0,0,0,0)]*4);read()
        elif ident==51:
            for field in range(4):
                for bad in ((bits(-1),0x7f800000) if field<3 else (0x7f800000,)):
                    mm=[bits(.6),0,0,0,0,0];mm[field]=bad;create(materials=[tuple(mm)])
            create();read()
        elif ident==52:
            for j in (0,3):
                for axis in (0,1):
                    pp=[list(map(bits,p)) for p in ((2,0),(1,0),(-1,0),(-2,0))];pp[j][axis]=0x7f800000
                    create(points=pp,encoded=True)
            create();read()
        elif ident==53:
            for u in (bits(.005)-1,bits(.005),bits(.005)+1):
                create(points=[(0,0),(bits(2),0),(bits(2),bits(2)),(0,u)],encoded=True)
            add(101,1,0,0)
            create(points=[(0,0),(2,0),(2,2),(0,0)],loop=True)
            create(points=[(0,0),(1.5e19,0),(1.5e19,1.5e19),(0,1.5e19)],loop=True)
            create();read()
        elif ident==54:
            for pp,loop in (([(-2,-1),(2,1),(-2,1),(2,-1)],False),
                ([(0,0),(4,0),(4,2),(1,0),(3,0)],False), ([(0,0),(4,0),(4,2),(2,0),(1,2)],False),
                ([(0,0),(3,0),(1,0),(1,2)],False), ([(0,0),(4,0),(0,4),(4,4)],True)):
                create(points=pp,loop=loop)
            create();read()
        elif ident==55:
            for kind in (1,2):
                rows.append(wrap(old.body(slot=kind,kind=kind)));create(parent=kind)
            create();add(80,0,0,1,0,1);add(80,0,0,1,0,2);add(80,0,0,1,0,0);read()
        elif ident==56:
            create();add(18,0,0);add(19,0,0,bits(2))
            for kind in range(9):
                val=(bits(.5),) if kind in (0,1) else (7,) if kind==2 else (bits(.5),0,0,0,7,0) if kind==3 else (1,0,0xffffffff,0xffffffff,0) if kind==4 else ()
                                                                           
                if kind>=5:val=(*(map(bits,(0,0,.5))) ,) if kind==5 else tuple(map(bits,(-1,0,1,0,.5))) if kind==6 else tuple(map(bits,(-1,0,1,0))) if kind==7 else (4,bits(0),bits(-1),bits(-1),bits(1),bits(-1),bits(1),bits(1),bits(-1),bits(1))
                add(81,0,0,1,kind,*val)
            read()
        else:
            n=80 if ident in (57,58,59,61,62,63,64) else 5
            create(points=[(i,0) for i in range(n)],materials=[(bits(.25+j/128),0,bits(j/256),bits(-j/32),j,j+0x123400) for j in range(n)])
            add(106,0,0,0);add(106,0,0,1)
            if ident in (57,58):
                add(109,ident-57,0);read();add(109,ident-57,1);read();add(107,0)
            elif ident==59:
                add(108,0,n-4,123);add(108,1,0,456);add(101,1,0,0);add(107,0);add(107,1)
            elif ident==60:add(1,0);add(107,0);add(108,1,0,123)
            else:
                add(101,1,0,0);create(target=1);read(1);read();add(107,0)
                guards={61:('GB7-CARRY',),62:('GB7-EXACT',),63:('GB7-PARTIAL','GB7-EMPTY-MAX'),64:('GUARD13B/Gkind11',)}[ident]
        if not 1<=len(rows)<=64:raise ValueError(f'13b case{ident} operation bound')
        result.append(ChainCase(ident,family,tuple(rows),guards))
    return tuple(result)

def text13b(items,decimal=False):
    word=str if decimal else lambda x:f'{x:08x}'
    yield f'PORT13B {len(items)}\n'
    for case in items:
        yield f'C {case.id} {len(case.ops)}\n'
        for seq,call in enumerate(case.ops,1):
            yield f'O {seq} {call['opcode']} '+ ' '.join(map(word,call['a']))+'\n'
            if call['opcode']==100:
                for tag,key in (('P13B','points'),('U13B','materials')):
                    for i,row in enumerate(call[key]):yield f'{tag} {case.id} {seq} {i} '+' '.join(map(word,row))+'\n'

def write13b(directory,N=64):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);items=cases13b(N)
    for decimal,side in ((False,'c'),(True,'duckling')):
        with (directory/('13b-'+side+'.csv')).open('w',encoding='ascii',newline='\n') as f:f.writelines(text13b(items,decimal))
    return items

def metadata_fixtures13b():
    pass                                                                          
    old=_legacy13b();wrap=lambda row:operation13b(row[0],*row[1:])
    setup=(wrap(old.world(speed=100)),wrap(old.body(kind=0)))
    def seed(kind,words,after,ops):return {'kind':kind,'ga':tuple(words)+(0,)*(64-len(words)),'seedAfterSeq':after,'operations':tuple(ops)}
    return {
        'carry-create':seed(4,(0,0xffffffff,0),2,(*setup,chain13b(),operation13b(102,1,0,0))),
        'exact-create':seed(4,(0,0xfffffffd,0xffffffff),2,(*setup,chain13b(),operation13b(102,1,0,0))),
        'limit-then-smaller':seed(4,(0,0xfffffffe,0xffffffff),2,(*setup,chain13b(),wrap(old.world(slot=1,speed=100)))),
        'generation-wrap':seed(11,(0,0,65535),3,(*setup,chain13b(),operation13b(102,1,0,0),operation13b(101,1,0,0),
            chain13b(target=1),operation13b(102,1,0,1),operation13b(102,1,0,0))),
    }

def text_fixture13b(fixture,decimal=False):
    word=str if decimal else lambda x:f'{x:08x}'
    yield 'GUARD13B 1\n'
    yield f'G 1 {fixture['kind']} {fixture['seedAfterSeq']} {len(fixture['operations'])}\n'
    yield 'GA 1 '+' '.join(map(word,fixture['ga']))+'\n'
    case=ChainCase(1,'metadata',fixture['operations'])
                                                                            
    yield from list(text13b((case,),decimal))[2:]

def example_inputs13b(decimal=False):
    pass                                                                          
    old=_legacy13b();wrap=lambda row:operation13b(row[0],*row[1:])
    base=(wrap(old.world(speed=100)),wrap(old.body(kind=0)),chain13b())
    operations=(*base,operation13b(102,1,0,0),operation13b(106,0,0,0),operation13b(101,1,0,0),
        operation13b(107,0),operation13b(108,0,0,123),operation13b(102,1,0,0))
    controls={'open-example':operations,
        'refused-query':(*operations[:4],operation13b(101,1,0,0),operation13b(102,1,0,0)),
        'parent-child':(*base,operation13b(104,1,0,0)),
        'parent-stale':(*operations[:4],operation13b(101,1,0,0),operation13b(104,1,0,0)),
        'parent-absent':(*base[:2],wrap(old.shape(0,parent=0,geometry=old.circle(r=.5),events=0)),
            operation13b(5,0,0),operation13b(5,0,0),operation13b(104,1,0,0)),
        'signed-zero':(*base[:2],chain13b(materials=((bits(-0.),bits(-0.),bits(-0.),bits(-0.),0xffffffff,0x80000000),)),
            operation13b(103,1,0,0,0,bits(-0.)),operation13b(103,1,0,0,1,bits(-0.)),operation13b(102,1,0,0))}
    for name,ops in controls.items():yield name,''.join(text13b((ChainCase(1,name,ops),),decimal)).encode('ascii')
    for name,kind,words in (('batch-helper',12,(0,0,0)),('batch-limit-helper',12,(0xffffffff,0xffffffff,1)),('store-helper',13,(0x80000001,0x8000,0xffff))):
        fixture={'kind':kind,'ga':(*words,*((0,)*61)),'seedAfterSeq':0,'operations':()}
        yield name,''.join(text_fixture13b(fixture,decimal)).encode('ascii')

                                                                                
def direct13c(kind,points,*,radius=.25,chain=((2,0),(1,0),(-1,0),(-2,0)),
              xf=(0,0,1,0),xfb=(0,0,1,0),mode=0,seed=(0,0,0,0,0,0,0)):
    a=[0]*64;a[:2]=[kind,mode];a[2:10]=map(bits,(v for p in chain for v in p));a[10:14]=map(bits,xf);a[14:18]=map(bits,xfb)
    a[18:20]=[len(points),bits(radius)]
    for j,p in enumerate(points):a[20+2*j:22+2*j]=map(bits,p)
    a[36:43]=seed;return operation13b(120,*a)

def _direct_recipe13c(meta,j):
    kind={'circle':0,'capsule':1,'polygon':2}[meta['para']];r=meta['receptura']-1;v=r%8;family=r//8
    chain=[(2,0),(1,0),(-1,0),(-2,0)];xfb=(0,0,1,0);xf=(0,0,1,0);radius=.5 if kind==0 else .25
    points=[(0,0)] if kind==0 else [(-.5,0),(.5,0)]
    if kind==2:
        octagon=[(-.5,-.25),(-.25,-.5),(.25,-.5),(.5,-.25),(.5,.25),(.25,.5),(-.25,.5),(-.5,.25)]
        count=3+v%6
        points=[octagon[(i*8)//count] for i in range(count)]
    seed=(0,)*7
    if kind==0:
        if r<8:points=[((j%3-1)/8,(-.5,0,.5)[(j+r)%3])]
        elif r<24:
            x=(-1 if r%2 else 1)+(j%3-1)/64;points=[(x,.25)]
            chain[0]=(2,(r%4-1)/4);chain[3]=(-2,(r%5-2)/8)
        elif r<40:
            radius=(0,.5)[v%2];points=[((j%3-1)/4,value(bits(f32(radius+f32(.02)))+j%3-1))]
        else:
            radius=(0,.5)[v%2];points=[((j%5-2)/8,(j%3)/8)];xf=((r%3)/4,-(r%2)/8,*((1,0),(0,1),(-1,0),(0,-1))[v%4]);xfb=((j%2)/8,0,1,0)
        if meta['id'] in (1,65) and j==0:points=[(0,-2)];radius=.5
        if meta['historia']=='warm' and j==0:seed=(3,0,1,2,2,1,0)
    else:
        x=(j%9-4)/4;y=(j%5-1)/8
        if family==0:
            chain[0]=(2,(v%3-1)/4);chain[3]=(-2,((v+1)%3-1)/4)
            x=(-1 if v%2 else 1)+(j%3-1)/64;y=.125
            if kind==2 and r in (0,1):
                chain=[(1,-.02),(0,0),(-2,0),(-3,0)];radius=.25
                if r==0:
                    slope=value((0x3c23d921,0x3c23d922,0x3c23d923)[j%3]);chain[0]=(1,-slope)
                    points=[(0,0),(.25,.25),(-.25,.125)];x,y=.00390625,.125
                else:
                    slope=value((0x3cf5d032,0x3cf5d033,0x3cf5d031)[j%3]);points=[(0,0),(.25,.25),(-.25,.25)];x,y=f32(slope*.125),.125
        elif family==1:
            chain[0]=(2,(v%3-1)/32);chain[3]=(-2,((v+1)%3-1)/32);y=(-.25,0,.25)[j%3]
        elif family==2:
            radius=0;points=[(-.25,0),(.25,0)] if kind==1 else [(-.25,0),(.25,0),(.25,.5),(-.25,.5)]
            x=0;y=value(0x3a03126f+j%3-1) if v<4 else (0,1,2)[j%3]
            if meta['historia']=='cold' or j==0:
                count=v%4;seed=(count,0,1 if count>1 else 0,0,0,0,1 if count>2 else 0)
        elif family==3:
            x=(-1,0,1)[j%3];y=.125
            if meta['historia']=='cold' or j==0:seed=(1+v%2,0,v%2,0,0,1 if v%2 else 0,0)
        elif family==4:
            chain[0]=(2,(v%2*2-1)/2);chain[3]=(-2,((v//2)%2*2-1)/2);x=(-1 if v%2 else 1)+(j%3-1)/32;y=.125
        elif family==5:x=(j%3-1)/16;y=(-.125,0,.125)[v%3]
        elif family==6:x=(j%3-1)/32;y=.25;xf=(0,0,*((1,0),(0,1),(-1,0),(0,-1))[v%4])
        else:x=(j%5-2)/8;y=.125;xfb=(0,0,*((1,0),(0,1),(-1,0),(0,-1))[v%4])
        xfb=(x,y,*xfb[2:])
    return direct13c(kind,points,radius=radius,chain=chain,xf=xf,xfb=xfb,mode=(j//8)%2,seed=seed)

def _world13c(meta):
    old=_legacy13b();wrap=lambda row:operation13b(row[0],*row[1:]);addrow=lambda code,*a:operation13b(code,*a)
    recipe=json.loads((HERE/'lancuchy-sceny13c.json').read_text(encoding='utf-8'))
    f=int(meta['rodzina'][1:]);v=meta['wariant'];rows=[wrap(old.world(speed=100,gravity=(0,-10),warm=int(meta['warmStarting'])))];used=set();child=[]
    def add(code,*a):rows.append(addrow(code,*a))
    def body(reg,**kw):rows.append(wrap(old.body(slot=reg,**kw)))
    def shape(parent,geometry,**kw):
        reg=next(i for i in range(512) if i not in used);used.add(reg);rows.append(wrap(old.shape(reg,parent=parent,geometry=geometry,friction=.6 if f==7 else 0,events=1,hit=1,**kw)));return reg
    def flag(reg):add(83,0,1,reg,1,2,1)
    def filter_(reg,group=0,mask=(1<<64)-1):add(81,0,reg,1,4,0,0x80000000,mask&0xffffffff,mask>>32,group)
    points=[tuple(p) for p in recipe['geometryOpenW1']]
    if f in (2,3):points[4]=(2,.0625);points[6]=(-2,-.0625)
    if f==4:points=[(20-2*i,0) for i in range(20)]+[(-20,i) for i in range(20)]+[(-20+2*i,20) for i in range(20)]+[(20,20-i) for i in range(20)]
    if f==5:points=[(12-2*i,0) for i in range(8)]
    def terrain(reg=0,group=0,pp=None):
        nonlocal child
        p=points if pp is None else pp;mm=None
        if f==6:mm=[(bits(i/16),bits((i%3)/8),bits((i%2)/64),bits((i-6)/16),(i-4)&0xffffffff,0x01000000+i) for i in range(len(p))]
        rows.append(chain13b(points=p,loop=f==4,materials=mm,target=reg,category=1<<63 if f==8 else 1,group=group))
        child=[]
        for _ in range(len(p) if f==4 else len(p)-3):
            slot=next(i for i in range(512) if i not in used);used.add(slot);child.append(slot)
    reverse=f==3 and v%2
    if not reverse:body(0,kind=0)
    if f==3 and not reverse:terrain()
    moving=[];count=3 if f in (3,7) else 8 if f==8 else 1
    for i in range(count):
        x,y,vx=-3,.5,2;geometry=old.circle(r=.5)
        if f==2:y=1;geometry=old.capsule((-.5,0),(.5,0),.25)
        if f==3:
            x,y=(-3,-1,1)[i],(.875,1,1.5)[i]
            if i==0:geometry=old.box(h=(.375,.375))
            else:
                p=([(-.25,-.25),(.25,-.25),(0,.25)] if i==1 else [(-.5,-.25),(-.25,-.5),(.25,-.5),(.5,-.25),(.5,.25),(.25,.5),(-.25,.5),(-.5,.25)])
                geometry=(3,(len(p),bits(0),*(bits(z) for q in p for z in q)))
        if f==4:x,vx=19,-2
        if f==6:vx=0
        if f==7:x,y,vx=0,.5+i,0;geometry=old.box(h=(.5,.5))
        if f==8:x,y,vx=i-4,.25,0;geometry=old.box(h=(.25,.25))
        body(i+1,p=(x,y),v=(vx,0))
        reg=shape(i+1,geometry,material=5 if f==6 else 0,**({'category':1<<63,'group':-1} if f==8 else {}));moving.append(reg)
        if f==8:flag(reg)
    if reverse:body(0,kind=0)
    if f!=3 or reverse:terrain(group=-1 if f==8 else 0)
    if f==4:body(2,p=(0,-.125),gravity_scale=0);shape(2,old.circle(r=.25))
    if f==5:terrain(1,pp=[(2-2*i,0) for i in range(8)])
    if f==6 and v>=3:add(87,0,2,1,2,5,bits(.5));add(86,0,1,2,1,0,0,0)
    def rules(filterAllow=False,preAllow=True,replace=False,which=None):
        if which in (None,0):
            add(87,0,0,0)
            for a,b,allow in [(moving[0],child[5],filterAllow),(moving[0],child[5],True),(child[5],moving[0],True)]:add(87,0,0,1,a,b,int(allow))
        if which in (None,1):
            add(87,0,1,0)
            for allow,threshold,rep in [(False,2,False),(preAllow,0,replace),(False,0,False)]:add(87,0,1,1,child[5],moving[0],int(allow),0,bits(1),bits(threshold),int(rep),0,bits(1) if rep else 0)
    if f==8:
                                                                             
        before=len(rows);rules();del rows[before+4];del rows[before]
        add(86,0,1,0,1,0,0,0);add(86,0,1,1,1,0,0,0)
    for t in range(1,meta['krokiDodatnie']+1):
        if t==301 and f in (1,2,3,5):
            for i in range(count):rows.append(wrap(old.linear(i+1,-2)))
        if f==4 and t==301:rows.append(wrap(old.g9.transform(0,1,(19.5,1.5))));rows.append(wrap(old.linear(1,0,-1)))
        if f==4 and t==351:rows.append(wrap(old.linear(1,-2)))
        if f==6 and t==421:add(88,0,1,1,0)
        if f==6 and t==481:rows.append(wrap(old.linear(1,1)))
        if f==7 and t==901:terrain(1)
        rows.append(wrap(old.step(dt=value(0x3c888889),n=meta['subSteps'])))
        if f==5 and t==550:add(101,1,0,0)
        if f==6 and t in (120,240,360,420):add(103,1,0,0,{120:0,240:1,360:2,420:0}[t],{120:bits(.75),240:bits(1.25),360:0xfffffff9,420:bits(.25)}[t])
        if f==7:
            if t==720:
                add(106,0,0,0);add(106,0,0,1);add(89,0,0,1,0);add(89,0,0,1,1);add(101,1,0,0)
            if t==721:add(49,0,0);add(49,0,1);add(107,0);add(107,1)
            if t==960:
                xy=tuple(value(int(x,16)) for x in recipe['W7']['replacementPositionBitsByVariant'][v]);add(3,0,2);body(2,p=xy);shape(2,old.box(h=(.5,.5)))
            if t==1200:add(50,0);add(50,1);add(89,2,0,0,0);add(89,2,0,0,1);add(107,0);add(107,1)
        if f==8:
            if t in (1,2):
                add(101,1,0,t-1);terrain(t,group=1 if t==1 else 0)
                for reg in moving:filter_(reg,1 if t==1 else 0,0 if t==1 else (1<<64)-1)
                rules()
            if t==20:filter_(moving[0],mask=1)
            if t==21:filter_(moving[0],mask=1<<63)
            if t==30:rules(filterAllow=True,which=0);filter_(moving[0],mask=0);filter_(moving[0])
            if t==35:rules(preAllow=False,which=1)
            if t==36:rules(preAllow=True,replace=True,which=1)
            if t in (120,180):rows.append(wrap(old.enable(0,int(t==180))))
            if t==240:rows.append(wrap(old.g9.transform(0,0,(.25,0))))
            if t==300:add(3,0,3)
            if t==360:body(3,p=(-2,.25));moving[2]=shape(3,old.box(h=(.25,.25)));flag(moving[2]);filter_(moving[2])
            if t==420:
                add(80,0,0,1,0,1);add(80,0,0,1,0,2);add(18,0,child[0]);add(19,0,child[0],bits(2))
                for kind in range(9):
                    val=(bits(.5),) if kind in (0,1) else (7,) if kind==2 else (bits(.5),0,0,0,7,0) if kind==3 else (1,0,0xffffffff,0xffffffff,0) if kind==4 else tuple(map(bits,(0,0,.5))) if kind==5 else tuple(map(bits,(-1,0,1,0,.5))) if kind==6 else tuple(map(bits,(-1,0,1,0))) if kind==7 else (4,bits(0),bits(-1),bits(-1),bits(1),bits(-1),bits(1),bits(1),bits(-1),bits(1))
                    add(81,0,child[0],1,kind,*val)
    if len(rows)>meta['opMax']:raise ValueError(f'13c case{meta['id']}: {len(rows)}>{meta['opMax']}')
    return tuple(rows)

def cases13c(N=432):
    if not 1<=N<=432:raise ValueError('PORT13C N in1..432')
    items=[]
    for m in MANIFEST['przypadki']:
        if m['profil']!='PORT13C' or m['id']>N:continue
        rows=tuple(_direct_recipe13c(m,j) for j in range(32)) if m['id']<=384 else _world13c(m)
        items.append(ChainCase(m['id'],m['rodzina'],rows))
    if [x.id for x in items]!=list(range(1,N+1)):raise ValueError('PORT13C manifest completeness')
    return tuple(items)

def text13c(items,decimal=False):
    for i,line in enumerate(text13b(items,decimal)):
        yield f'PORT13C {len(items)}\n' if i==0 else line

def write13c(directory,N=432):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);items=cases13c(N)
    for decimal,side in ((False,'c'),(True,'duckling')):
        with (directory/('13c-'+side+'.csv')).open('w',encoding='ascii',newline='\n') as f:f.writelines(text13c(items,decimal))
    return items

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--katalog',type=Path,required=True);p.add_argument('--N',type=int);p.add_argument('--13b',dest='chain_world',action='store_true');p.add_argument('--13c',dest='chain_contact',action='store_true');a=p.parse_args()
    result=(write13c(a.katalog,432 if a.N is None else a.N) if a.chain_contact else write13b(a.katalog,64 if a.N is None else a.N) if a.chain_world else write(a.katalog,128 if a.N is None else a.N));print(json.dumps({'N':len(result),'calls':sum(len(c.ops) for c in result)}))
