pass                                                                             
import argparse
import hashlib
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZERO, ONE, HALF, SMALL = 0, 0x3f800000, 0x3f000000, 0x3e4ccccd


def op(code, *words):
    a = [int(x) & 0xffffffff for x in words]
    if code < 200:
        if len(a) > 64: raise ValueError('legacy arity')
        a += [0]*(64-len(a))
    return (code, a)


def description(c, field, **updates):
    a = [int(x, 16) for x in c[field]]
    for i, value in updates.items(): a[int(i)] = value
    return a


def body(c, reg=0, *, x=0, y=0, kind=None):
    a = description(c, 'sensorBodyH' if reg == 0 else 'visitorBodyH')
    a[1], a[4], a[5] = reg, x, y
    if kind is not None: a[3] = kind
    return op(309, *a)


def shape(c, reg=0, parent=None, *, sensor=None, radius=None, geom=0, events=None, mass=None):
    a = description(c, 'sensorShapeH' if sensor is True or reg == 0 else 'visitorShapeH')
    a[0], a[2] = reg, reg if parent is None else parent
    if sensor is not None: a[59] = int(sensor)
    if events is not None: a[60] = int(events)
    if mass is not None: a[61] = int(mass)
    if mass is False: a[58] = 0
    if radius is not None or geom:
        r = radius if radius is not None else SMALL
        a[3], a[4:44] = geom, [0]*40
        if geom == 0: a[6] = r
        elif geom == 1: a[4:9] = [0xbf000000, 0, HALF, 0, r]
        elif geom == 2: a[4:8] = [0xbf000000, 0, HALF, 0]
        elif geom == 4: a[4:11] = [0x3f19999a, 0x3ecccccd, 0, 0, ONE, 0, r]
        else: raise ValueError('nonliteral geometry request')
    return op(400, *a)


def transform(reg, x, y=0): return op(4, 0, reg, x, y, ONE, 0)
def step(c, dt=None, raw=False): return op(31 if raw else 32, 0, int(c.get('dtH','3c888889'),16) if dt is None else dt, c.get('subSteps',4))
def flag(reg, value): return op(401, 0, 0, reg, int(value))
def destroy_shape(reg): return op(11, 0, reg, 1)
def destroy_body(reg): return op(3, 0, reg)
def enabled(reg, value): return op(80, 0, reg, 0, 1, int(value))
def sleep(reg): return op(58, 0, reg, 0, 0)
def filter_shape(reg, category=1, mask=0xffffffffffffffff, group=0):
    return op(81, 0, reg, 0, 4, category & 0xffffffff, category >> 32, mask & 0xffffffff, mask >> 32, group)
def circle(reg, radius): return op(81, 0, reg, 0, 5, 0, 0, radius)
def hook(kind=0, fixture=1): return op(86, 0, 0, kind, 1, fixture)


def setup(c):
    return [op(308, *map(lambda x:int(x,16), c['worldDescriptionH'])),
            op(309, *map(lambda x:int(x,16), c['sensorBodyH'])),
            op(309, *map(lambda x:int(x,16), c['visitorBodyH'])),
            op(400, *map(lambda x:int(x,16), c['sensorShapeH'])),
            op(400, *map(lambda x:int(x,16), c['visitorShapeH']))]


def public(c, ticket_start=0):
    ident = c['ordinal']; rows = setup(c)
    if c['short']:
        if ident == 24: rows.append(shape(c,2,0,sensor=False,radius=SMALL))
        rows.append(step(c))
        if ident == 6: rows.append(step(c))
        if ident == 7: rows += [transform(1,0x40800000),step(c)]
        if ident == 8: rows += [flag(0,False),step(c)]
        if ident == 9: rows += [op(402,0,0,1,2)]
        if ident == 10: rows += [op(403,0,0,0,0),op(403,0,0,0,1)]
        if 11 <= ident <= 14:
            rows.append((destroy_shape if ident < 13 else destroy_body)(1 if ident in (11,13) else 0))
            rows += [step(c,0),step(c,0)]
            if ident in (11,13): rows.append(step(c))
        if ident == 15: rows += [filter_shape(0,mask=0),step(c)]
        if ident == 16: rows += [circle(0,0x3c23d70a),transform(1,HALF),step(c)]
        if ident == 17: rows += [transform(1,0x40800000),step(c)]
        if ident == 18: rows += [step(c,0),step(c,0)]
        if ident == 19: rows += [op(404,1,0,0),step(c),op(406,0,0)]
        if ident == 20: rows += [hook(),step(c,raw=True)]
        if ident == 21: rows += [sleep(1),step(c)]
        if ident == 22: rows += [enabled(0,False),step(c)]
        if ident == 23: rows += [body(c,2,x=0x41200000,kind=2),shape(c,2,2,sensor=True,radius=ONE),op(12,0,2,0,1)]
        return rows
    family=(ident-25)//6+1;variant=(ident-25)%6;steps=c['positiveSteps']; extras=[]
    if family == 1:
        rows += [op(309,*[int(x,16) for x in c['setupExtra'][0]['descriptionH']])]
        rows += [op(400,*[int(x,16) for x in item['descriptionH']]) for item in c['setupExtra'][1:]]
    if family == 6:
        rows += [body(c,2,y=0xbf000000,kind=0)]
        points=c['setupChain']['pointsH']; a=[0,0,2,0,len(points),0,1,0,0,0,1,0,0xffffffff,0xffffffff,0,1]
        rows.append((100,op(100,*a)[1],points,[[0x3f19999a,0,0,0,0,0]]))
    if family == 10:
                                                                                         
        jd=[0,0,0,0,HALF,0,0,0,0,0x3a83126f,0x47c35000,0,0,0,0,0,0,0]
        rows += [op(312,0,0,*jd),op(201,0,0,0,1,0,0)]
    if family == 12:
        for reg in range(2,66): rows.append(shape(c,reg,0,sensor=True,radius=ONE));extras.append(reg)
    for k in range(steps):
        if family == 2 and k%50==0: rows.append(flag(0 if (k//50)%2 else 1,(k//100)%2==0))
        if family == 3 and k%50==0:
            phase=(k//50)%6
            rows.append(filter_shape(0 if (k//50)%2 else 1,category=1<<63 if phase==2 else 1,mask=0 if phase in (1,4) else 0xffffffffffffffff,group=-1 if phase==3 else 1 if phase==4 else 0))
        if family == 4 and k%100==0: rows.append(enabled(0 if variant<3 else 1,(k//100)%2==1))
        if family == 4 and k%100==50: rows.append(sleep(1))
        if family == 5 and k>0 and k%60==0 and variant%4==0: rows.append(circle(0,0x3dcccccd))
        if family == 7 and k==200: rows += [destroy_shape(0),shape(c,0,0,sensor=True,radius=ONE)]
        if family == 7 and k==400: rows += [destroy_body(1),body(c,1),shape(c,1,1,sensor=False,radius=SMALL)]
        if family == 8 and k%100==50: rows += [destroy_shape(1),shape(c,1,1,sensor=False,radius=SMALL)]
        if family == 8 and k==800:
            rows += [op(1,0),rows[0],body(c,0),shape(c,0,0,sensor=True,radius=ONE),body(c,1),shape(c,1,1,sensor=False,radius=SMALL),op(407,0,0,0,0,12,(ticket_start+5)^1),op(406,0,0),op(406,0,1)]
        if family == 9 and k%20==0:
            if extras: rows.append(destroy_body(2));extras=[]
            rows += [body(c,2,kind=2),shape(c,2,2,sensor=False,radius=0x3dcccccd)];extras=[2]
        if family == 11 and k%100==50: rows += [destroy_shape(1),shape(c,1,1,sensor=False,radius=SMALL),step(c,0),step(c,0)]
        if family == 12 and k==200: rows += [destroy_shape(2),shape(c,2,0,sensor=True,radius=ONE)]
        if family == 12 and k==400:
            rows += [destroy_shape(r) for r in extras];extras=[]
        if family == 12 and k==450:
            for reg in range(2,128): rows.append(shape(c,reg,0,sensor=True,radius=ONE));extras.append(reg)
        if family == 10: rows += [transform(1,0xc0000000),op(35,0,1,0x43700000,0,0)]
        elif family != 4 and k%60==0:
            x=0x3e99999a if k%120<60 else 0x40200000;y=0xbf800000 if family==6 and k%240>=120 else 0
            rows.append(transform(1,x,y))
            if family==6:rows.append(transform(0,x,y))
        rows.append(step(c))
        if family==8 and k==0:rows += [op(404,1,0,0),op(404,1,0,1)]
        if family==11 and k%100==0:
                                                                           
                                                                           
            edit=op(407,1,0,2,0,0,3) if k%120<60 else op(406,1,0)
            rows += [op(404,1,0,0),op(404,1,0,1),op(405,0,0,0),op(405,0,0,1),edit,op(406,1,0),op(406,1,1)]
    return rows


def direct(c):
    i=c['ordinal']
    if i<=8:return [op(408,*map(lambda x:int(x,16),c['comparatorInputH']))]
    if i==64:return [op(409,0),op(409,1)]
    if i==62:
        rows=[]
        for route in range(6):
            base=setup(c);base[1][1][19]=int(route<4);base[3][1][60]=int(route<2)
            rows.append(base[0])
            if route%2==0:rows.append(hook())
            rows+=base[1:]
            if route%2:rows.append(hook())
                                                                               
                                                                                 
            rows += [step(c,raw=True),body(c,2,x=0x41200000,kind=0),body(c,3,x=0x4121999a,kind=2),shape(c,2,2,sensor=False,radius=ONE),shape(c,3,3,sensor=False,radius=ONE),step(c,raw=True),op(1,0)]
        return rows
    rows=setup(c)
    if i in (13,14):
        rows += [body(c,2,x=0 if i==13 else 0x40800000,kind=2),shape(c,2,2,sensor=False,radius=SMALL)]
        if i==13:rows.append(transform(1,0x40800000))
    if 33<=i<=35:rows += [circle(0,0),circle(1,0),transform(1,0x35a00000+i-34)]
    if i==39:rows += [transform(1,0x3727c5ac)]
    if i==17:rows += [shape(c,2,0,sensor=False,radius=SMALL)]
    if i==18:rows += [flag(1,False)]
    if i==19:rows += [filter_shape(1,mask=0)]
    if i in (20,21):rows += [filter_shape(1,mask=0 if i==20 else 0xffffffffffffffff,group=1 if i==20 else -1),filter_shape(0,mask=0 if i==20 else 0xffffffffffffffff,group=1 if i==20 else -1)]
    if i==22:rows += [transform(1,ONE,ONE)]
    if 23<=i<=26:
        geom=(0,1,4,2)[i-23]
        rows += [destroy_shape(0),shape(c,0,0,sensor=True,radius=ONE,geom=geom),destroy_shape(1),shape(c,1,1,sensor=False,radius=SMALL,geom=geom)]
    if i in (27,28):rows += [destroy_shape(1),shape(c,1,1,sensor=True,events=i==27,radius=SMALL)]
    if i==27:
        rows += [op(83,0,1,r,0,e,1) for r in (0,1) for e in (0,1,2)];rows += [hook(1,0)]
    if i==29:rows.append(sleep(1))
    if i==30:rows.append(enabled(1,False))
    if i==31:rows.append(flag(0,False))
    if i==32:rows.append(hook())
    if i==36:rows += [filter_shape(1,category=1<<63),filter_shape(0,mask=1<<63)]
    if i==37:rows += [filter_shape(0,group=1),filter_shape(1,mask=0,group=1)]
    if i==38:rows.append(filter_shape(0,mask=0))
    if i==40:rows += [shape(c,2,1,sensor=False,geom=1,radius=0x3dcccccd),shape(c,3,1,sensor=False,geom=4,radius=0x3dcccccd)]
    if i==16:rows += [destroy_shape(1),op(20,0,1,2,65534,1),flag(2,True)]
    if i==60:rows += [transform(1,0xc0000000),op(35,0,1,0x43700000,0,0)]
    rows.append(step(c,raw=i in (32,62)))
    if 9<=i<=16:
        if i==9:rows.append(transform(1,0x40800000))
        if i==10:rows.append(shape(c,2,1,sensor=False,radius=SMALL))
        if i==11:rows += [destroy_shape(1),shape(c,1,1,sensor=False,radius=SMALL)]
        if i==12:rows += [destroy_shape(1),op(20,0,1,2,65536,1),flag(2,True)]
        if i in (13,14):rows += [transform(1,0 if i==13 else 0x40800000),transform(2,0x40800000 if i==13 else 0)]
        if i==15:rows.append(step(c))
        if i==16:rows += [destroy_shape(2),shape(c,1,1,sensor=False,radius=SMALL)]
        rows.append(step(c))
    if 41<=i<=48:
        if i in (42,44):rows.append(body(c,2,kind=0))
        rows += [shape(c,2,2 if i in (42,44) else 0,sensor=True,radius=ONE),step(c)]
        if i==45:rows.append(destroy_shape(1))
        if i==46:rows.append(destroy_body(1))
        if i==48:return rows+[op(404,1,0,0),op(1,0),op(406,0,0)]
        if i==43:rows.append(destroy_shape(2))
        elif i==44:rows.append(destroy_body(2))
        elif i==47:rows += [destroy_shape(2),destroy_shape(0)]
        else:rows.append(destroy_shape(0) if i%2 else destroy_body(0))
        rows.append(step(c,0))
        if i in (41,42):rows += [flag(2,True),step(c)]
    if 49<=i<=56:
        if i in (49,50):rows.append(step(c,0))
        if i==50:rows.append(step(c,0))
        if i==51:rows.append(flag(0,False))
        if i==52:rows.append(enabled(0,False))
        if i in (53,54):
            if i==54:rows.append(destroy_body(1))
            rows += [shape(c,r,0,sensor=True,radius=ONE) for r in range(2,66 if i==53 else 129)]
        if i in (55,56):rows.append(destroy_shape(0))
        if i==56:rows.append(destroy_body(1))
        rows.append(step(c))
    if i==57:rows += [op(402,0,0,0,2),op(403,0,0,0,0),op(403,0,0,0,1),op(402,0,0,1,2),op(403,0,0,1,1)]
    if i==58:rows += [flag(0,True),step(c)]
    if i==59:rows += [op(402,0,0,r,k) for r in (0,1) for k in (0,1)]+[body(c,2,x=0x41200000,kind=2),shape(c,2,2,sensor=True,radius=ONE,mass=False),op(13,0,2)]
    if i==60:rows += [transform(1,0xc0000000),op(35,0,1,0x42700000,0,0),step(c)]
    if i==61:rows += [sleep(1),flag(1,False),step(c)]
    if i==63:rows += [op(404,1,0,0),op(404,1,0,1),op(407,0,0,0,0,3,3),op(1,0),rows[0],op(406,0,1),op(1,0)]
    return rows


def materialize(profile, side, data, ids=None, ticket_consumption=None):
    cases=data[profile.lower()]
    if ids is not None:cases=[c for c in cases if c['ordinal'] in ids]
    consumption=ticket_consumption or {}
    f8=[i for i,c in enumerate(cases) if profile=='PUBLIC' and 67<=c['ordinal']<=72]
    if f8:
        missing=[c['id'] for c in cases[:max(f8)] if c['id'] not in consumption]
        if missing:raise ValueError('multi-case F8 requires frozen C ticket consumption before output: '+','.join(missing))
    starts={};offset=0
    for c in cases:
        starts[c['id']]=offset
        if offset is not None:offset=offset+consumption[c['id']] if c['id'] in consumption else None
    yield f'PORT17 {profile} {len(cases)}\n'
    for c in cases:
        rows=public(c,starts[c['id']] or 0) if profile=='PUBLIC' else direct(c)
        if len(rows)!=c['operationCountExact']:
            raise ValueError(f'{c['id']}: recipe {len(rows)} operations != frozen {c['operationCountExact']}')
        yield f'C {c['ordinal']} {len(rows)}\n'
        for seq,row in enumerate(rows,1):
            code,words=row[:2]
            payload=' '.join(f'{x:08x}' if side=='C' else str(x) for x in words)
            yield f'O {seq} {code} '+(f'{len(words)} ' if code>=200 else '')+payload+'\n'
            if code==100:
                for tag,items in [('P13B',row[2]),('U13B',row[3])]:
                    for j,values in enumerate(items):
                        values=[int(x,16) if isinstance(x,str) else x for x in values]
                        yield f'{tag} {c['ordinal']} {seq} {j} '+' '.join(f'{x:08x}' if side=='C' else str(x) for x in values)+'\n'


def freeze_tickets(root):
    pass                                                                       
    root=Path(root);receipt=json.loads((root/'manifest.json').read_bytes())
    if not receipt['mode'].startswith('independent'):raise ValueError('independent C reference required')
    consumption={};sources=[]
    for case in receipt['results']:
        if not case.get('passed'):continue
        path=root/case['id']/'C1.out.csv.gz';sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=case['runs'][1]['sha256']:raise ValueError('frozen C changed '+case['id'])
        last=None
        with gzip.open(path,'rb') as f:
            for line in f:
                if line.startswith(b'Z8 '):last=line.split()[-2:]
        if last is None:raise ValueError('missing lastIssued '+case['id'])
        consumption[case['id']]=int(last[0],16)|(int(last[1],16)<<32)
        sources.append(dict(id=case['id'],C1SHA=sha,lastIssued=consumption[case['id']]))
    return dict(consumption=consumption,receipts=sources,source='Frozen independent C last Z8, before D; cleanup allocates no ticket.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',choices=['PUBLIC','DIRECT']);p.add_argument('--side',choices=['C','D']);p.add_argument('--output',type=Path,required=True);p.add_argument('--ids');p.add_argument('--ticket-consumption',type=Path);p.add_argument('--freeze-tickets',type=Path)
    a=p.parse_args();data=json.loads((HERE/'sensory-przypadki.json').read_bytes())
    if a.freeze_tickets:
        a.output.write_text(json.dumps(freeze_tickets(a.freeze_tickets),indent=2)+'\n');raise SystemExit(0)
    if not a.profile or not a.side:p.error('--profile and --side are required for tapes')
    ids=None if not a.ids else {int(x) for x in a.ids.split(',')}
    with a.output.open('wb') as f:
        consumption=None if a.ticket_consumption is None else json.loads(a.ticket_consumption.read_bytes())['consumption']
        for line in materialize(a.profile,a.side,data,ids,consumption):f.write(line.encode('ascii'))
