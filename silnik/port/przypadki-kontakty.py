pass                                                                              

                                                                               
                                                                              
   
import argparse
import hashlib
import json
from pathlib import Path
import sys
from dataclasses import asdict

from importlib.util import spec_from_file_location, module_from_spec

HERE = Path(__file__).resolve().parent
def load(name, filename):
    spec=spec_from_file_location(name,HERE/filename)
    mod=module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod

g8=load('contact_motion_inputs','przypadki-ruch-swiata.py')
g7=g8.g7
Case,op,bits,number=g8.Case,g8.op,g8.bits,g8.number
U32,U64=g8.U32,g8.U64
world,body,transform=g8.world,g8.body,g7.transform
circle,capsule,segment,box,polygon=g8.circle,g8.capsule,g8.segment,g8.box,g8.polygon
USED={**g8.USED,40:59,41:1,42:1,43:1,44:1,45:1,46:4,47:3,48:3,49:2,50:2,51:39,52:7,53:3}
LIMITS=((0,0,0),(2,2,1),(2,2,1),(3,3,3),(3,3,3),(2,2,1),(8,8,12),(8,8,12),
        (8,8,12),(14,14,13),(14,14,13),(4,4,4),(65,130,129),(6,12,16),(8,16,16),(8,16,16))

def shape(slot=0,parent=0,owner=0,geometry=None,density=1,friction=.6,restitution=0,
          rolling=0,tangent=0,material=0,category=1,mask=U64,group=0,invoke=1,events=1,hit=0,game=1):
    tag,geo=geometry or circle()
    return op(40,slot,owner,parent,tag,*geo,*([0]*(40-len(geo))),
              *map(bits,(density,friction,restitution,rolling,tangent)),material&U32,
              category&U32,category>>32,mask&U32,mask>>32,group&U32,invoke,events,hit,game)

def cycle(owner=0):return [op(code,owner) for code in range(41,46)]
def save(a=0,b=1,target=0,owner=0):return op(46,owner,a,b,target)
def get(contact=0,mutate=0,owner=0):return op(47,owner,contact,mutate)
def event_copy(target=0,owner=0):return op(49,owner,target)
def seed(variant=0):
                                                               
                                                                      
    ids=(0x201,0x300)
    if variant==0:ids=ids[::-1]
    if variant==1:ids=(ids[0],65534)
    if variant==2:ids=(65533,65534)
    if variant==3:ids=(ids[0],ids[0])
    m=[0]*30;m[0:4]=[0,bits(1),bits(.5),2]
    for j,ident in enumerate(ids):
        k=4+13*j;m[k+7:k+13]=[bits(1+j),bits(-.5 if j==0 else .25),bits(3),bits(-2),ident,1]
    return m+[3,0,1,2,2,1,0]

def pair_scene(ga=None,gb=None,distance=.9,events=(1,1),reverse=False,kinds=(2,2),q=(1,0)):
    rows=[world(gravity=(0,0))]
    order=(1,0) if reverse else (0,1)
    for i in order:rows.append(body(i,kind=kinds[i],p=(0,0 if i==0 else distance),q=q))
    for i in order:rows.append(shape(i,parent=i,geometry=(ga,gb)[i],events=events[i]))
    return rows

def proposed_cases():
    pass                                                                          
    result=[]
    for family in range(1,17):
        for v in range(4):
            rows=[]
            if family==1:
                rows=[world(gravity=(0,0))]
                if v==1:rows += [world(1,gravity=(0,0)),*cycle(1)]
                if v==2:rows += [op(1,0),world(1,gravity=(0,0))];owner=1
                else:owner=0
                rows += cycle(owner)+[event_copy(owner=owner)]
                if v==3:rows += cycle()+[event_copy(1),op(50,0,1),op(50,1)]
            elif family==2:
                geometries=((circle(),circle()),(capsule((.0995,.05),(.1005,.05),.5),capsule()),
                            (circle((.1,0)),box(c=(.1,0))),(capsule(),capsule(p1=(-.75,.1),p2=(.9,.1))))
                rows=pair_scene(*geometries[v],distance=.3,reverse=v==3)
                rows += [op(41),op(42),save(),get(),op(43),get(),op(44),op(45),op(48,0,0,1),event_copy()]
            elif family==3:
                x=number((0x3cb3d709,0x3cb3d70a,0x3cb3d70b,0x3cb3d709)[v])
                rows=[world(gravity=(0,0)),body(),body(1,p=((-x if v==3 else x),0)),
                      shape(geometry=circle(r=number(0x3a800000))),shape(1,parent=1,geometry=circle(r=number(0x3a800000)))]
                rows += cycle()+[save(),get()]
                rows += [transform(0,1,((-.04 if v==3 else .04),0)),*cycle(),get(),
                         transform(0,1,((-.01 if v==3 else .01),0)),*cycle(),get()]
            elif family==4:
                flags=((0,0),(1,0),(0,1),(1,1))[v]
                rows=pair_scene(box(),box(),distance=1.04,events=flags,reverse=v==2)
                rows += [body(2,p=(1.4,.5)),shape(2,parent=2,geometry=circle(r=.15),events=flags[v&1]),*cycle(),save()]
                for p in ((0,.9),(.7,.9),(0,1.04),(0,.9),(0,4)):
                    rows += [transform(0,1,p),*cycle(),get(),event_copy()]
            elif family==5:
                q=((0,1),(0,-1),(0,1),(0,-1))[v]
                rows=[world(gravity=(0,0)),body(q=q),body(1,p=(0,.6),q=(0,1)),
                      shape(geometry=box(h=(.5,.5),c=(.2,.1))),shape(2,parent=0,geometry=circle((-.4,.2),.25),mask=0),
                      shape(1,parent=1,geometry=circle((.1,-.2),r=.5)),*cycle(),save()]
                for vals in ((.25,.5,.3,-2),(1,1.5,.7,.5),(0,0,0,-0.0)):
                    rows += [op(52,0,0,*map(bits,vals),v),op(52,0,1,*map(bits,(1,1.5,0,2)),7),*cycle(),get()]
            elif family==6:
                rows=pair_scene(box(),box(),distance=.9)
                rows += cycle()+[save(),op(51,0,0,*seed(v)),*cycle(),get()]
                if v==3:
                    for p in ((1.5,1),(0,1.04),(0,.9)):
                        rows += [transform(0,1,p),*cycle(),get()]
                    rows += [op(51,0,0,*seed(3)),*cycle(),get()]
            elif family==7:
                                                                          
                rows=[world(gravity=(0,0))]
                order=list(range(8));order=order[::-1] if v&1 else order
                for i in order:
                    rows += [body(i,p=(0 if i<4 else 1.04,0)),shape(i,parent=i,category=1<<i,
                        mask=sum(1<<j for j in range(8) if (i<4)!=(j<4) and (i%4)!=(j%4)))]
                rows += cycle()
                pairs=[(i,j) for i in range(4) for j in range(4,8) if i%4!=j%4]
                for k,(a,b) in enumerate(pairs):rows.append(save(a,b,k))
                for k in ((5,0,11),(6,11,0),(11,0,5),(3,8,1))[v]:rows += [op(53,0,k,0),get(k)]
                rows += [transform(0,4,(1.05,0)),*cycle()]
            elif family==8:
                rows=[world(gravity=(0,0))]
                for i in range(8):rows += [body(i,kind=0 if v==1 and i%2==0 else 2,p=(3*(i//2),.9*(i%2))),shape(i,parent=i)]
                rows += cycle()+[save(2,3),save(0,1,1),save(4,5,2)]
                if v==1:rows += [op(3,0,3)]
                else:rows += [transform(0,3,(3,1.04 if v!=2 else 1.06)),*cycle(),transform(0,3,(3,.9)),*cycle()]
                if v==3:
                    rows += [transform(0,4,(.4,.2)),*cycle(),op(48,0,0,1),get(1,1),op(48,0,4,1)]
            elif family==9:
                rows=[world(gravity=(0,0))]
                def pos(x):return (0,x) if v&1 else (x,0)
                adjacency={0:(1,),1:(0,2,5),2:(1,3),3:(2,4),4:(3,),5:(1,),6:(),7:()}
                for i in (2,3,0,1,4,5,6,7):
                    x=(.4 if i==0 else .44 if i==1 else .04 if i==3 else 20 if i>=6 else 0)
                    rows.append(body(i,p=pos(x)))
                def add_shape(i):return shape(i,parent=i,geometry=circle(r=.001),category=1<<i,mask=sum(1<<j for j in adjacency[i]))
                                                                                       
                rows += [add_shape(2),add_shape(3),*cycle(),add_shape(0),add_shape(1),*cycle(),
                         transform(0,0,pos(0)),transform(0,1,pos(.04)),*cycle(),add_shape(4),add_shape(5),*cycle(),add_shape(6),add_shape(7)]
                for i in range(6):rows.append(transform(0,i,pos(0)))
                rows += cycle()+[save(0,1),transform(0,1,pos(.04)),*cycle(),get(),op(3,0,0),*cycle()]
                if v>=2:rows += [op(3,0,7),body(8,p=(20+v,0)),shape(8,parent=8,mask=0),*cycle()]
                if v==1:rows += [op(48,0,4,1)]
            elif family in (10,11):
                rows=[world(gravity=(0,0))]
                                                                                    
                order=list(range(14));order=order[::-1] if v==3 else order
                for i in order:
                    kind=2 if i==0 or family==11 else 0
                    geom=box() if family==10 and v==1 and i else circle(r=.5 if i==0 else .1)
                    staged=(family==11 and v in (1,3)) or (family==10 and v==2)
                    rows += [body(i,kind=kind,p=(0,20+i if staged and i else 0)),shape(i,parent=i,geometry=geom,category=1 if i==0 else 2,mask=2 if i==0 else 1)]
                rows += cycle()
                if family==10 and v==2:
                    for group in (range(1,11),(11,),(12,13)):
                        rows += [transform(0,i,(0,0)) for i in group]+cycle()
                if family==11 and v in (1,3):rows += [transform(0,i,(0,0)) for i in range(1,14)]+cycle()
                for i in range(1,14):rows.append(save(0,i,i-1))
                if (family==10 and v==2) or (family==11 and v in (1,3)):
                                                                                     
                                                                                            
                    rows += [op(3,0,12),*cycle()]
                if family==11 and v==2:
                    rows += [op(3,0,1),body(14,p=(0,0)),shape(14,parent=14,category=2,mask=1),*cycle()]
                if family==10 and v==3:
                                                                                
                    rows=[world(gravity=(0,0)),body(kind=0),shape(geometry=box(h=(8,.25)),category=1,mask=2)]
                    for i in range(1,14):rows += [body(i,p=(-6+i,.7)),shape(i,parent=i,geometry=circle(r=.5),category=2,mask=1)]
                    rows += cycle()
            elif family==12:
                if v==3:
                    rows=[world(gravity=(0,0)),body(kind=2),body(1,kind=1),body(2,kind=0),body(3,kind=0),
                          shape(geometry=segment()),shape(1,parent=1,geometry=segment()),
                          shape(2,parent=2,geometry=circle((0,.1),.2)),shape(3,parent=3,geometry=circle((0,-.1),.2)),*cycle()]
                else:
                    rows=pair_scene(distance=.3,kinds=(0 if v==2 else 1,2))
                    if v==1:rows += [body(2,p=(.6,0)),shape(2,parent=2)]
                    rows += cycle()+[save(),get(),op(48,0,0,1)]
            elif family==13:
                rows=[world(gravity=(0,0))]
                for i in (range(64,-1,-1) if v==3 else range(65)):rows.append(body(i))
                order=list(range(130));order=order[::-1] if v==1 else order
                for s in order:
                    if s==0:cat,mask=1,2
                    elif s==1:cat,mask=4,8
                    elif s%2==0:cat,mask=2,1
                    else:cat,mask=8,4
                    if s==3:cat,mask=10,5
                    rows.append(shape(s,parent=s//2,geometry=circle(r=.01 if s>=2 and s%2 else .05),category=cat,mask=mask))
                rows += cycle()+[save(0,2),save(1,129,1)]
                stopped=iter([*range(2,16),64])
                for n in range(1,6):
                    rows += [transform(0,next(stopped),(.0,.09)) for _ in range(n)]+cycle()
                if v>=2:rows += [op(3,0,32),body(65),shape(130,parent=65,category=2,mask=1),*cycle()]
            elif family==14:
                rows=[world(gravity=(0,0))]
                for i in range(6):rows.append(body(i,p=(20 if i==5 else .7*i,0)))
                for s in range(12):rows.append(shape(s,parent=s//2,geometry=circle((0,.08*(s%2)),.5),events=1))
                rows += cycle()+[save(2,4),save(4,6,1),event_copy()]
                if v==2:rows += [op(3,0,0),get(1),*cycle(),get(1)]
                elif v==1:rows += [op(3,0,2),event_copy(1),*cycle()]
                else:rows += [op(18,0,5 if v==3 else 4),get(1),*cycle()]
            elif family==15:
                rows=pair_scene(distance=.9)+cycle()+[save(),event_copy()]
                if v==0:
                    rows += [op(1,0),world(1,gravity=(0,0)),body(2,1),body(3,1,p=(0,.9)),
                             shape(2,parent=2,owner=1),shape(3,parent=3,owner=1),*cycle(1),save(2,3,1,owner=1),
                             get(1),op(48,0,2),event_copy(1),save(2,3,2),get(owner=1),op(50,0)]
                elif v==1:
                    rows += [world(1,gravity=(0,0)),body(2,1),body(3,1,p=(0,.9)),shape(2,parent=2,owner=1),shape(3,parent=3,owner=1),*cycle(1),
                             get(owner=1),op(48,1,0),save(0,0,1),save(0,2,2,owner=1)]
                elif v==2:
                    rows += [op(18,0,1),get(),shape(2,parent=1),*cycle(),save(0,2,1),get(),get(1),save(0,0,2),get(2)]
                else:
                    rows += [g8.force(value=(1,2)),g8.linear(0,1),g8.step(raw=True,n=1),g8.step(raw=True,dt=-1/60,n=1),
                             g8.step(n=1),g8.step(dt=-1/60,n=1),g8.step(dt=0,n=1)]
            elif family==16:
                rows=pair_scene(distance=.9)+cycle()+[save(),event_copy()]
                if v==0:
                    rows += [op(18,0,1),shape(2,parent=1),event_copy(1),*cycle(),event_copy(2),op(50,0),op(50,1),*cycle(),event_copy(3)]
                elif v==1:
                    rows += [event_copy(1),op(50,0,1),op(50,1),event_copy(2),op(50,0)]
                elif v==2:
                    rows += [transform(0,1,(.2,.7)),*cycle(),get(),op(50,0,1),event_copy(1)]
                else:
                    rows += [op(3,0,1),*cycle(),event_copy(1),event_copy(2),op(50,1,1),op(1,0),op(50,0),op(50,1),op(50,2)]
            ident=4*(family-1)+v+1
            result.append(Case(ident,f'B{family} / wariant {v + 1}',tuple(rows)))
    return tuple(result)

def cases():
    data=json.loads((HERE/'kontakty-sceny.json').read_bytes())
    return tuple(Case(r['id'],r['name'],tuple(tuple(int(x,16) for x in op_) for op_ in r['operations'])) for r in data['cases'])

def encode(rows,duckling=False):
    text=[f'PORT9B {len(rows)}']
    for c in rows:
        text.append(f'C {c.id} {len(c.ops)}')
        for seq,(code,*a) in enumerate(c.ops,1):text.append(f'O {seq} {code} '+' '.join(str(x) if duckling else f'{x:08x}' for x in a))
    return '\n'.join(text)+'\n'

def freeze():
    rows=proposed_cases()
    data={'profile':'COMPONENT_A9','N':64,'actual_operations':sum(len(c.ops) for c in rows),
          'cases':[{'id':c.id,'name':c.category,'operations':[[f'{x:08x}' for x in o] for o in c.ops]} for c in rows]}
    (HERE/'kontakty-sceny.json').write_text(json.dumps(data,indent=2)+'\n',encoding='ascii')

def verify():
    rows=cases();assert rows==proposed_cases(),'frozen scene data changed'
    assert len(rows)==64
    manifest=json.loads((HERE/'kontakty-przypadki.json').read_bytes())
    for c,m in zip(rows,manifest['przypadki']):
        assert c.id==m['id'] and 0<len(c.ops)<=m['opMax'],(c.id,len(c.ops))
        assert all(len(r)==65 and r[0] in USED and all(type(x)==int and 0<=x<=U32 for x in r) and not any(r[1+USED[r[0]]:]) for r in c.ops),c.id
        assert any(r[0] in (51,52,53) for r in c.ops)==(m['FIXTURE_INPUT']=='tak'),c.id
    return rows

def write(directory):
    rows=verify();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n,name in ((64,'przypadki'),(49,'proba')):
        for duck in (False,True):
            filename=name+'-kontakty'+('-stdin' if duck else '')+'.csv';data=encode(rows[:n],duck).encode('ascii')
            (directory/filename).write_bytes(data);hashes[filename]=hashlib.sha256(data).hexdigest()
    (directory/'wejscia-kontakty-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='ascii')
    return {'N':64,'operations':sum(len(c.ops) for c in rows),'per_case':[len(c.ops) for c in rows]}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--katalog',type=Path,default=HERE)
    args=parser.parse_args()
    if args.freeze:freeze()
    print(json.dumps(write(args.katalog)))
