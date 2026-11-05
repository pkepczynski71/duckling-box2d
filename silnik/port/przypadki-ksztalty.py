pass                                                                            
import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
from przypadki import bits, number

_spec = importlib.util.spec_from_file_location('shape_world_input', Path(__file__).with_name('przypadki-swiat.py'))
w6 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = w6
_spec.loader.exec_module(w6)
COUNT = 96
U32, U64 = (1 << 32)-1, (1 << 64)-1
HEX = re.compile(r'[0-9a-f]{8}\Z')
DEC = re.compile(r'(?:0|[1-9][0-9]{0,9})\Z')
INPUT_NAMES = ('przypadki-ksztalty.csv', 'przypadki-ksztalty-stdin.csv',
               'proba-ksztalty.csv', 'proba-ksztalty-stdin.csv')

@dataclass(frozen=True)
class Case:
    id: int
    category: str
    ops: tuple


def op(code, *a):
    if len(a) > 64:
        raise ValueError('operation length')
    return (code, *a, *([0]*(64-len(a))))


def world(slot=0, gravity=(0, -10), speed=400):
    return op(0, slot, *map(bits, gravity), bits(speed))


def body(slot=0, owner=0, kind=2, p=(0, 0), q=(1, 0), v=(0, 0), w=0, fixed=0):
    return op(2, slot, owner, kind, *map(bits, (*p, *q, *v, w)), fixed)


def transform(owner, slot, p, q=(1, 0)):
    return op(4, owner, slot, *map(bits, (*p, *q)))


def circle(c=(0, 0), r=.5):
    return 0, tuple(map(bits, (*c, r)))


def box(h=(.75, .5), c=(0, 0), q=(1, 0), r=0):
    return 4, tuple(map(bits, (*h, *c, *q, r)))


def capsule(p1=(-1, 0), p2=(1, 0), r=.25):
    return 1, tuple(map(bits, (*p1, *p2, r)))


def segment(p1=(-1, 0), p2=(1, 0)):
    return 2, tuple(map(bits, (*p1, *p2)))


def polygon(points=((-1, -1), (1, -1), (0, 1)), r=0):
    return 3, (len(points), bits(r), *(bits(v) for p in points for v in p))


def shape(slot=0, owner=0, parent=0, geometry=None, density=1, update=1, invoke=1,
          category=1, mask=U64, group=0, object_id=None, game=False):
    tag, geo = geometry or circle()
    return op(17 if game else 10, slot, owner, parent, tag, bits(density), update, invoke,
              category & U32, category >> 32, mask & U32, mask >> 32, group & U32,
              int(object_id is not None), (object_id or 0) & U32, (object_id or 0) >> 32,
              *geo, *([0]*(40-len(geo))))


def pair(bslot=0, sslot=0, owner=0, kind=2, p=(0, 0), q=(1, 0), v=(0, 0), w=0,
         fixed=0, geometry=None, density=1, invoke=1, object_id=None,
         category=1, mask=U64, group=0):
    tag, geo = geometry or circle()
    return op(16, bslot, sslot, owner, kind, *map(bits, (*p, *q, *v, w)), fixed,
              tag, bits(density), invoke, int(object_id is not None),
              (object_id or 0) & U32, (object_id or 0) >> 32, category & U32,
              category >> 32, mask & U32, mask >> 32, group & U32,
              *geo, *([0]*(40-len(geo))))


def object_op(kind, slot, value, owner=0):
    return op(15, owner, kind, slot, int(value is not None), (value or 0) & U32, (value or 0) >> 32)


def geometry_fields(tag, a, start):
    if tag == 3:
        count = a[start]
        if not 3 <= count <= 8:
                                                                               
                                                                              
            count = max(0, min(8, count))
        return [start+1, *range(start+2, start+2+2*count)]
    return list(range(start, start+{0:3, 1:5, 2:4, 4:7}[tag]))


def validate_operation(row):
    if len(row) != 65 or any(type(v) is not int or not 0 <= v <= U32 for v in row):
        raise ValueError('operation length / u32')
    code, *a = row
    used = {0:4, 1:1, 2:11, 3:2, 4:6, 5:2, 10:55, 11:3, 12:4, 13:2,
            14:2, 15:6, 16:63, 17:55, 18:2, 19:3, 20:5, 21:3}
    if code not in used:
        raise ValueError('opcode')
    if any(a[used[code]:]):
        raise ValueError('unused')
    floats, bools = [], []
    if code <= 5:
        w6.validate_operation((code, *a[:24]))
        return
    if code in (10, 17):
        if a[0] > 511 or a[1] > 15 or a[2] > 255 or a[3] > 4:
            raise ValueError('register/tag')
        tag, start = a[3], 15
        floats, bools = [4], [5, 6, 12]
        if code == 17 and a[5] != 1:
            raise ValueError('game update')
        if not a[12] and any(a[13:15]):
            raise ValueError('object absent')
    elif code == 16:
        if a[0] > 255 or a[1] > 511 or a[2] > 15 or a[3] > 2 or a[12] > 4:
            raise ValueError('register/tag')
        floats, bools = [*range(4, 11), 13], [11, 14, 15]
        tag, start = a[12], 23
        if not a[15] and any(a[16:18]):
            raise ValueError('object absent')
        if not w6.valid_rotation(number(a[6]), number(a[7])):
            raise ValueError('rotation')
    else:
        if a[0] > 15 or a[1] > (255 if code in (13, 20, 21) else 511):
            raise ValueError('register')
        if code == 11:
            bools = [2]
        if code in (12, 19):
            floats = [2]
            if code == 12:
                bools = [3]
        if code == 15:
            if a[1] not in (2, 3) or a[2] > (255 if a[1] == 2 else 511):
                raise ValueError('object kind/register')
            bools = [3]
            if not a[3] and any(a[4:6]):
                raise ValueError('object absent')
        if code == 20 and (a[2] > 511 or not 1 <= a[3] <= 65536 or a[4] > 511 or a[2] == a[4]):
            raise ValueError('CHURN')
        if code == 21 and a[2] > 256:
            raise ValueError('capacity')
    if code in (10, 16, 17):
        gf = geometry_fields(tag, a, start)
        floats += gf
        active = set(gf) | ({start} if tag == 3 else set())
        if any(a[i] for i in range(start, start+40) if i not in active):
            raise ValueError('unused geometry')
        if tag == 4 and not w6.valid_rotation(number(a[start+4]), number(a[start+5])):
            raise ValueError('rotation')
    if code in (10,12) and number(a[4 if code==10 else 2])<0:
        raise ValueError('raw density')
    if code==10:
        geo=a[15:55];f=list(map(number,geo));tag=a[3]
        if ((tag==0 and f[2]<=0) or (tag==1 and f[4]<=0) or
            (tag==4 and (f[0]<=0 or f[1]<=0 or f[6]<0)) or
            (tag==3 and (not 3<=geo[0]<=8 or f[1]<0))):
            raise ValueError('raw geometry')
    if any(a[i] > 1 for i in bools):
        raise ValueError('bool')
    if not all(math.isfinite(number(a[i])) for i in floats):
        raise ValueError('nonfinite')


def review_witnesses():
    pass                                                                 

                                                                           
                                                                        
       
    rows = [
        ('B1.body', body(10)),
        ('B1.circle', shape(20, parent=10)),
        ('B1.raw', op(12, 0, 20, bits(2), 0)),
        ('B1.game', op(19, 0, 20, bits(2))),
        ('B1.cleanup', op(3, 0, 10)),
        ('B2a.remove.body', body(11)),
        ('B2a.remove.far', shape(21, parent=11, geometry=circle((16384, 0)))),
        ('B2a.remove.zero', shape(22, parent=11)),
        ('B2a.remove.refusal', op(18, 0, 22)),
        ('B2a.remove.cleanup', op(3, 0, 11)),
        ('B2a.density.body', body(12)),
        ('B2a.density.far', shape(23, parent=12, geometry=circle((16384, 0)))),
        ('B2a.density.zero', shape(24, parent=12)),
        ('B2a.density.refusal', op(19, 0, 24, bits(0))),
        ('B2a.density.cleanup', op(3, 0, 12)),
        ('B2b.body', body(13, kind=0)),
        ('B2b.refusal', shape(25, parent=13, game=True,
            geometry=polygon(((0, 0), (2, 0), (1, .5), (2, 2), (0, 2))))),
        ('W2.refusal', shape(26, parent=13, game=True,
            geometry=capsule((-1e19, 0), (1e19, 0), .25))),
    ]
                                                                          
    for slot, code, initial, requested in ((40, 12, -0.0, 0.0), (41, 12, 0.0, -0.0),
                                            (42, 19, -0.0, 0.0), (43, 19, 0.0, -0.0)):
        label = 'W1.'+str(code)+'.'+str(slot)
        rows += [(label+'.create', shape(slot, parent=13, density=initial)),
                 (label+'.set', op(code, 0, slot, bits(requested), *([1] if code == 12 else [])))]
    polygons = (((-1, -1), (1, -1), (0, 1)),
                ((0, -1), (1, -.25), (.6, 1), (-.6, 1), (-1, -.25)),
                ((-1, -.5), (-.5, -1), (.5, -1), (1, -.5), (1, .5), (.5, 1), (-.5, 1), (-1, .5)))
    for slot, points in enumerate(polygons, 30):
        rows.append(('polygon.'+str(len(points)), shape(slot, parent=13, game=True, geometry=polygon(points))))
    for game in (False, True):
        for offset in (-1, 0, 1):
            endpoint = number(bits(w6.f32(.005))+offset)
            slot = 33 + 3*int(game) + offset+1
            rows.append(('segment.'+str(int(game))+'.'+str(offset),
                shape(slot, parent=13, game=game, geometry=segment((0, 0), (endpoint, 0)))))
    rows.append(('W2.segment', shape(44, parent=13, game=True,
        geometry=segment((-1e19, 0), (1e19, 0)))))
    rows.append(('review.cleanup', op(3, 0, 13)))
    return tuple(rows)


def cases():
    rows = []
    def add(name, ops):
        rows.append(Case(len(rows)+1, name, tuple(ops)))
    geometries = (circle(), box(), capsule(), segment())
    for geo in geometries:
        for kind in range(3):
            ops = [world(), body(kind=kind, w=3, v=(2, -1), fixed=int(kind == 1)), shape(geometry=geo), op(5, 0, 0)]
            if len(rows) == 0:
                ops += [shape(1, geometry=box(c=(2, 0))), shape(2, geometry=circle((-2, 0))),
                        op(11, 0, 1, 1), shape(3, geometry=box(c=(3, 0))), op(14, 0, 1)]
            ops += [transform(0, 0, (3, -5), (.6, .8)), op(11, 0, 0, 1)]
            if len(rows) == 0:
                ops += [row for _, row in review_witnesses()]
            add('E5a5538c7c55f E6705d57f46f8 / E2d3bd495b557 / E8c586909c59a E1bf61810dc30', ops)
    for v in range(12):
        ops = [world(), body(w=7+v*.125, v=(2, -3), fixed=int(v == 3))]
        ds = (0, 0, 0) if v == 0 else (1, 1e-5, 1e5) if v % 3 == 1 else (1, 3, .7) if v%3 == 2 else (0, 3, .7)
        for i, d in enumerate(ds):
            ops += [shape(i, geometry=circle((i*1.25-1, i*.5), .5+i*.125), density=d)]
        ops += [op(12, 0, 1, bits(2.5), 0), op(12, 0, 1, bits(2.5), 1), op(13, 0, 0),
                op(19, 0, 1, bits(2.5)), op(19, 0, 2, bits(.25)), op(18, 0, v%3)]
        add('masa / prepend / prędkość / S04', ops)
    for v in range(12):
        ops = [world(), body(), body(1, kind=v%3)]
        ops += [shape(i, geometry=geometries[i%4], parent=i//4) for i in range(5)]
        target = (3, 1, 0, 2)[v%4]
        if v==3:
            ops += [op(11,0,4,1),shape(20,parent=1,geometry=segment())]
        ops += [op(11, 0, target, 1), op(11, 0, (target+1)%4, 1), shape(10, geometry=box()),
                shape(11, geometry=circle()), op(3, 0, 0), transform(0, 1, (11, -13)),
                body(2), shape(12, parent=2, geometry=capsule()), op(1, 0), world(1),
                body(3, 1), shape(13, 1, 3, segment())]
        add('E2b9e7e9c9226 Ea330395cc0a5 / LIFO / E5504fb4d56e1 / E98fc34a4e5dc', ops)
    for geo in geometries:
        for v in range(4):
            kind = (len(rows)+v)%3
            ops = [world(), body(kind=kind), shape(geometry=geo, invoke=v%2), shape(1, geometry=circle((3, 0)), invoke=1)]
                                                                             
                                                                           
            margin = .02 if kind == 0 else .05
            endpoint, radius = ((0,.5),(.75,0),(1,.25),(1,0))[geometries.index(geo)]
            def moved_upper(shift):
                return w6.f32(w6.f32(w6.f32(endpoint+shift)+w6.f32(radius))+w6.f32(.02))
            fat_upper=w6.f32(moved_upper(0)+w6.f32(margin))
            low, high = 0, bits(.25)
            while low+1<high:
                mid=(low+high)//2
                if moved_upper(number(mid))<=fat_upper: low=mid
                else: high=mid
            inside,outside=number(low),number(high)
            assert high==low+1 and moved_upper(inside)==fat_upper and moved_upper(outside)>fat_upper
            positions = (((0, 0), (.001, 0), (0, 0)), ((inside, 0), (outside, 0), (inside, 0)),
                         ((100, -71), (0, 0), (-100, 71)), ((0, 0), (2, -3), (0, 0)))[v]
            for p in positions:
                ops += [transform(0, 0, p, (0, 1) if v == 3 else (1, 0))]
            ops += [op(11, 0, 0, 1), shape(2, geometry=geo, invoke=1), op(11, 0, 1, 1)]
            add('obszary / Contains / margines static / ruchy', ops)
    polys = [((-1,0),(1,0),(0,number(bits(w6.f32(.005))+8))), ((0,-1),(1,-.25),(.6,1),(-.6,1),(-1,-.25)),
             ((-1,-.5),(-.5,-1),(.5,-1),(1,-.5),(1,.5),(.5,1),(-.5,1),(-1,.5))]
    slop = w6.f32(.005)
    special = [polygon(p, r) for p in polys for r in (0, .125)] + [
        box(q=(.6,.8)), box(q=(.6,.8), r=.1),
        capsule((0,0),(number(bits(slop)-1),0)), capsule((0,0),(slop,0)),
        capsule((number(bits(slop)+1),0),(0,0)), segment((-100,0),(100,0))]
    for i, geo in enumerate(special):
        ops = [world(), body(), shape(geometry=geo), shape(1, geometry=circle((2,0))), shape(2, geometry=box(c=(-2,0)))]
        ops += [op(21, 0, 0, cap) for cap in (0,1,2,3,4)]
        if i==8:
            ops += [shape(3,geometry=capsule((number(1),0),(number(1),0)))]
        add('E2b3b18120924 / Ef288e063d6d1 E881df12b68cd / Q', ops)
    for v in range(12):
        value = (None,0,1<<32,1<<63,U64,17)[v%6]
        ops = [world(), world(1), pair(object_id=value, geometry=geometries[v%4], group=-7 if v%2 else 5),
               body(1,1), shape(1,1,1,geometries[v%4],object_id=value,group=-7 if v%2 else 5), object_op(2,1,value,1), op(14,1,0),
               op(19,1,0,bits(9)), op(18,1,0), object_op(2,0,value),
               object_op(3,0,1<<63), object_op(3,0,None), op(3,0,0),
               op(14,0,0), body(2), shape(2,parent=2,geometry=box()),
               op(14,0,0), op(1,0), world(2), pair(3,3,2,geometry=capsule()), op(14,2,2)]
        add('stare / obce / metadane / para', ops)
    for v in range(8):
        ops = [world(), world(1)]
        for i in range(65):
            if v%2:
                ops += [body(i,1,kind=(i+v)%3,p=(i*3,v*.25)), shape(i,1,i,geometries[i%4],density=1+i*.01+v*.001,
                       object_id=(1<<63)+i,category=(1<<63)|(1<<32)|1)]
            else:
                if i == 0:
                    ops += [body(0,1,kind=v%3)]
                ops += [shape(i,1,0,circle((i*.01,0),.2+i*.001),density=1+i*.01+v*.001,
                              object_id=(1<<32)+i,category=(1<<63)|1)]
        ops += [op(11,1,32,1), shape(100,1,64 if v%2 else 0,box(),object_id=None),
                op(19,1,0,bits(2)), object_op(3,64,U64,1), transform(1,64 if v%2 else 0,(31,-37))]
        add('wzrost 16/32/64/65', ops)
    add('S12 legacy raw / odmowa gry / centered', [world(), body(), shape(geometry=circle((16384,0))),
        body(1), shape(1,parent=1,geometry=circle((16384,0)),game=True),
        pair(2,2,p=(16384,0)), op(14,0,0)])
    add('S12 para atomowa / fixed', [world(), pair(geometry=circle((16384,0))),
        pair(1,1,p=(16384,0)), pair(2,2,fixed=1,geometry=circle((16384,0)))])
    add('E6705d57f46f8 Efb4dac7b8936 E03e71c6d7dc6 E939b22bc707e', [world(), body(), shape(geometry=circle()),
        shape(1,geometry=polygon(((0,0),(1,0),(2,0))),game=True),
        shape(2,geometry=segment((0,0),(.001,0)),game=True),
        shape(3,geometry=circle(r=-1),game=True), shape(4,geometry=segment((0,0),(.001,0))),
        op(19,0,0,bits(-1)), shape(5,geometry=box(),game=True)])
    add('E0b39f7f25f61 E7e9e5ac30f22 E283ada7088c2 E3268fef5c876 E85a5525683c9', [world(), pair(object_id=U64),
        shape(1,geometry=box(h=(0,1)),game=True), shape(2,geometry=capsule(r=-.5),game=True),
        op(19,0,0,bits(-2)), object_op(3,0,0), op(18,0,0), shape(3,game=True)])
    for count in (7,11,17,65536):
        add('generation wrap' if count>100 else 'E2300eca14adb E8bdf9cae947b', [world(),body(),shape(),op(11,0,0,1),
            op(20,0,0,1,count,0),op(14,0,0),op(19,0,0,bits(9)),op(18,0,0),op(14,0,1)])
    for v in range(4):
        add('E6694ea807500 / E0366d9e50b40 E38fce4306bcb', [world(gravity=(-0.0,0.0)),pair(object_id=1<<63),op(1,0),world(1),
            pair(1,1,1,geometry=geometries[v]),op(14,1,0),object_op(3,1,0,1),op(21,1,1,1)])
    assert len(rows) == COUNT
    for c in rows:
        assert 1 <= len(c.ops) <= 512
        for row in c.ops:
            validate_operation(row)
    return tuple(rows)


def small_cases():
    return (Case(1, 'E8c586909c59a E1bf61810dc30', cases()[0].ops),)


def encode(rows, decimal=False):
    lines = [str(len(rows))]
    for c in rows:
        lines += [f'C {c.id} {len(c.ops)}']
        lines += [f'O {seq} {code} '+ ' '.join(str(x) if decimal else f'{x:08x}' for x in a)
                  for seq,(code,*a) in enumerate(c.ops,1)]
    return ''.join(line+ ('\r\n' if i%3 == 1 else '\n') for i,line in enumerate(lines[:-1]))+lines[-1]


def read_input(text, decimal=False, expected_count=None):
    text2 = text.replace('\r\n','\n')
    if not text.isascii() or '\r' in text2:
        raise ValueError('ASCII / line endings')
    lines = text2.split('\n')
    if lines[-1] == '':
        lines.pop()
    def dec(s):
        if not DEC.fullmatch(s) or int(s)>U32:
            raise ValueError('canonical decimal')
        return int(s)
    if not lines:
        raise ValueError('truncated')
    n = dec(lines[0])
    if not 1 <= n <= COUNT or (expected_count is not None and n != expected_count):
        raise ValueError('N')
    rows, pos = [], 1
    for cid in range(1,n+1):
        if pos >= len(lines):
            raise ValueError('truncated')
        h = lines[pos].split(' '); pos += 1
        if len(h)!=3 or h[0]!='C' or dec(h[1])!=cid or not 1<=dec(h[2])<=512:
            raise ValueError('CASE')
        ops=[]
        for seq in range(1,dec(h[2])+1):
            if pos >= len(lines):
                raise ValueError('truncated')
            p=lines[pos].split(' '); pos+=1
            if len(p)!=67 or p[0]!='O' or dec(p[1])!=seq:
                raise ValueError('O / seq')
            a=[]
            for t in p[3:]:
                if decimal:
                    a.append(dec(t))
                elif HEX.fullmatch(t):
                    a.append(int(t,16))
                else:
                    raise ValueError('canonical hex')
            row=(dec(p[2]),*a); validate_operation(row); ops.append(row)
        rows.append(Case(cid,'transport',tuple(ops)))
    if pos != len(lines):
        raise ValueError('extra lines')
    return tuple(rows)


def verify_input_hashes(directory, manifest=None):
    directory=Path(directory)
    sums=json.loads(Path(manifest or directory/'wejscia-ksztalty-sha256.json').read_bytes())
    if set(sums)!=set(INPUT_NAMES):
        raise ValueError('manifest keys')
    expected={name:encode(small_cases() if name.startswith('proba-') else cases(),name.endswith('-stdin.csv')).encode('ascii') for name in INPUT_NAMES}
    for name in INPUT_NAMES:
        data=(directory/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=sums[name] or data!=expected[name]:
            raise ValueError('E1a8ede14b808 bytes E5422e223df9f: '+name)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--katalog',type=Path,required=True)
    args=p.parse_args(); args.katalog.mkdir(parents=True,exist_ok=True)
    sums={}
    for name in INPUT_NAMES:
        data=encode(small_cases() if name.startswith('proba-') else cases(),name.endswith('-stdin.csv')).encode('ascii')
        (args.katalog/name).write_bytes(data); sums[name]=hashlib.sha256(data).hexdigest()
    (args.katalog/'wejscia-ksztalty-sha256.json').write_text(json.dumps(sums,indent=2)+'\n',encoding='ascii')
    verify_input_hashes(args.katalog)
    print(f'{COUNT} przypadków; {sum((len(c.ops) for c in cases()))} E6e548997f3f2; E5422e223df9f E41de145ea83c Ef4918b159ca2')

if __name__=='__main__':
    main()
