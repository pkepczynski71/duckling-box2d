pass                                                                      
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

g7 = load('motion_shape_inputs', 'przypadki-ksztalty.py')
Case, op, bits, number = g7.Case, g7.op, g7.bits, g7.number
world, circle, box, capsule, segment, polygon = (g7.world, g7.circle, g7.box, g7.capsule, g7.segment, g7.polygon)
U32, U64, HEX, DEC = g7.U32, g7.U64, g7.HEX, g7.DEC
COUNT = 64
USED = {0:4,1:1,2:11,3:2,4:6,5:2,10:55,11:3,12:4,13:2,14:2,15:6,
        16:63,17:55,18:2,19:3,21:3,30:16,31:3,32:4,33:8,34:8,35:5,36:4,37:1,38:3,39:2}

def body(slot=0, owner=0, kind=2, p=(0,0), q=(1,0), v=(0,0), w=0,
         fixed=0, damping=0, angular_damping=0, gravity_scale=1, fast=0, game=1):
    return op(30, slot, owner, kind, *map(bits, (*p,*q,*v,w)), fixed,
              bits(damping), bits(angular_damping), bits(gravity_scale), fast, game)

def shape(slot=0, owner=0, parent=0, **kw):
    return g7.shape(slot, owner, parent, **{'mask':0, **kw})

def step(owner=0, dt=1/60, n=4, copy=0, raw=False):
    return op(31 if raw else 32, owner, bits(dt), n & U32, *([] if raw else [copy]))

def force(slot=0, kind=1, value=(3,-2), point=(2,1), owner=0, raw=False, wake=1):
    scalar = kind in (2,5)
    center = kind in (1,4) or scalar
    return op(33 if raw else 34, owner, slot, kind, bits(value[0]),
              0 if scalar else bits(value[1]), *(map(bits,(0,0) if center else point)), wake)

def linear(slot, x, y=0, owner=0, game=1):
    return op(35, owner, slot, bits(x), bits(y), game)

def angular(slot, w, owner=0, game=1):
    return op(36, owner, slot, bits(w), game)

def signed(u):
    return u if u < 1<<31 else u-(1<<32)

def validate_operation(row):
    if len(row)!=65 or any(type(x) is not int or not 0<=x<=U32 for x in row):
        raise ValueError('operation length / u32')
    code,*a=row
    if code not in USED: raise ValueError('opcode')
    if any(a[USED[code]:]): raise ValueError('unused')
    if code<30:
        g7.validate_operation(row)
        return
    floats=[]; bools=[]; allow_nonfinite=False
    if code==30:
        if a[0]>255 or a[1]>15 or a[2]>2: raise ValueError('body definition')
        floats=[*range(3,10),11,12,13]; bools=[10,14,15]; allow_nonfinite=bool(a[15])
        if not allow_nonfinite and (not g7.w6.valid_rotation(number(a[5]),number(a[6])) or number(a[11])<0 or number(a[12])<0):
            raise ValueError('raw body definition')
    elif code in (31,32):
        if a[0]>15 or (code==32 and a[3]>3): raise ValueError('register')
        floats=[1]; allow_nonfinite=True
    elif code in (33,34):
        if a[0]>15 or a[1]>255 or a[2]>5: raise ValueError('register/kind')
        floats=[3,4,5,6]; bools=[7]; allow_nonfinite=code==34
        if a[2] in (1,4) and any(a[5:7]): raise ValueError('unused force point')
        if a[2] in (2,5) and any(a[4:7]): raise ValueError('unused scalar')
    elif code in (35,36):
        if a[0]>15 or a[1]>255: raise ValueError('register')
        floats=[2,3] if code==35 else [2]; bools=[4 if code==35 else 3]
        allow_nonfinite=bool(a[bools[0]])
    elif code==37:
        if a[0]>3: raise ValueError('copy register')
    elif code==38:
        if a[0]>15 or a[1]>255: raise ValueError('register')
        bools=[2]
    elif code==39:
        if a[0]>15 or a[1]>511: raise ValueError('register')
    if any(a[i]>1 for i in bools): raise ValueError('bool')
    if not allow_nonfinite and not all(math.isfinite(number(a[i])) for i in floats):
        raise ValueError('nonfinite')

def small_cases():
    return (Case(1,'one dynamic body / three steps / owned copy',
        (world(),body(v=(1,0)),shape(),force(),step(n=4),step(n=4,raw=True),
         step(n=4,raw=True),op(37,0))),)

def boundary_case(family, guard=False):
    pass                                                                   
    late=family>=59
                                                                         
    distance=4 if late else 0 if family==57 else 1.08
    group=1 if family in (57,59) and guard else -1 if family in (58,60) and not guard else 0
    mask=U64 if guard and not group else 0
    rows=[world(gravity=(0,0)), body(),body(1,p=(distance,0)),
          shape(mask=mask,group=group),shape(1,parent=1,mask=mask,group=group),
          step(dt=0),force(value=(1,2))]
    if late:
        rows += [linear(0,3),linear(1,-3),step(dt=.5,n=1)]
    rows += [step(dt=1/60),step(dt=1/60),op(37,0)]
    return tuple(rows)

def guard_cases():
    return tuple(Case(i,'GUARD8 family '+str(f),boundary_case(f,True)) for i,f in enumerate(range(57,61),1))

def cases():
    result=[]
    populations=(0,3,8,4,6,8,8,8,8,8,8,8,12,8,9,65)
    for family,count in enumerate(populations,1):
        for n in (1,4,8):
            rows=[world(gravity=(0,-10) if family not in (7,8,9,16) else (0,0),speed=8 if family in (7,9) else 400)]
            if family==13: rows += [world(1,gravity=(2,-3))]
            for i in range(count):
                owner=int(family==13 and i>=6)
                kind=0 if family==2 else 1 if family==10 else 2
                speed=number(bits(8)+(i%3-1)) if family==7 else 0 if i%3==0 else .125*(i+1)
                                                                                 
                threshold=g7.w6.f32(g7.w6.f32(.25*g7.w6.f32(math.pi))*8)
                omega=number(bits(threshold)+(i%3-1))*(-1 if i&1 else 1) if family==8 else .25*(i%4)
                velocity=(speed,0)
                if family==7 and i>=3: velocity=(number(bits(4.8)+(i%3-1)),6.4)
                rows += [body(i,owner,kind,p=(i*2000,0) if family==3 else (i*.25,i*.125),
                    q=(.6,.8) if family==14 and i==0 else (1,0),v=velocity,w=omega,
                    fixed=int(family==11 and i%2==0), damping=(0,.125,4,20)[i%4] if family in (4,10) else 0,
                    angular_damping=.5 if family in (4,10) else 0,
                    gravity_scale=(-1,0,.5,2)[i%4] if family in (3,10) else 1,
                    fast=int(family==8 and i>=4))]
                if family==12 and i==7: continue
                geom=(circle(),capsule(),segment(),polygon(),box())[i%5] if family==12 else circle()
                if family==14 and i==0: geom=circle((2,1))
                rows += [shape(i,owner,i,geometry=geom,density=0 if family==12 and i%3==0 else .5+i*.125,
                               mask=U64 if family==3 else 0)]
                if family!=16: rows += [g7.object_op(2,i,(1<<63)+(i<<32)+i,owner)]
            if family==14:
                rows += [shape(8,parent=0,geometry=box(c=(-1,2))),shape(9,parent=0,geometry=circle((0,-2))),op(38,0,0,1),op(39,0,8)]
            if family==16:
                rows += [op(3,0,1),body(65,v=(1,0)),shape(65,parent=65)]
            if family==2:
                rows += [force(0,k) for k in range(6)]+[linear(0,200),angular(0,100)]
            if family in (4,5,6,10,14):
                rows += [force(0,k,wake=k%2 if family==5 else 1) for k in range(6)]+[force(0,0,value=(-2,5)),force(0,1,value=(4,-1))]
            if family==4:rows += [force(1,1,value=(5,-2)),force(1,2,value=(1,0))]
            if family==9:
                rows += [linear(0,20),force(1,4,value=(200,0)),angular(2,100),force(2,5,value=(100,0))]
            if family==11: rows += [angular(0,7),angular(1,-7)]
            if family==13:
                rows += [force(0,owner=1),op(38,1,0,1),op(39,1,0),force(6,owner=1)]
            for frame in range(1,601):
                if family==6 and frame in (2,3,100,300): rows += [force(0),force(1,2)]
                if family==14 and frame==300: rows += [op(19,0,8,bits(2))]
                if family==15 and frame==301:
                    rows += [op(37,0),op(3,0,4),body(9,v=(2,-1)),shape(9,parent=9),
                             g7.object_op(2,9,0x1234567887654321),force(4),op(38,0,4,1),op(39,0,4),op(37,0)]
                rows += [step(owner=frame%2 if family==13 else 0,dt=.125 if family==8 else 1/60,n=n,copy=frame%2)]
            rows += [op(37,0),op(37,1)]
            result.append(Case(len(result)+1,'template '+str(family)+' / n='+str(n),tuple(rows)))
    for cid in range(49,65):
        rows=[world(),body(v=(1,0),kind=0 if cid==56 else 2),shape(game=cid==64),step(),force()]
        if cid in (49,50): rows += [step(dt=0.0 if cid==49 else -0.0,n=4,copy=1),op(37,0),op(37,1),step(copy=2),op(37,0),op(37,2)]
        elif cid in (51,52): rows += [step(dt=-.125 if cid==51 else -.25,raw=True),step(dt=-.125),op(37,0),step()]
        elif cid in (53,54):
            rows=[world(),world(1),body(),body(1,1),shape(),shape(1,1,1)]
            for value in ((0,-1,-2147483648) if cid==53 else (-2147483648,-1,0)): rows += [step(n=value,raw=True),step(1,n=1,raw=True),step(n=value),step(dt=0,n=value)]
        elif cid in (55,56):
            for word in (0x7fc00001 if cid==55 else 0x7fc00002,0x7fe12345,0x7f800000,0xff800000):
                rows += [op(32,0,word,4,1)]
            for k in range(6):
                f=list(force(kind=k));f[4]=0x7f800000;rows.append(tuple(f))
            for k in (0,3):
                for field in (5,6):
                    f=list(force(kind=k));f[1+field]=0x7fc00001;rows.append(tuple(f))
            for k in (1,4):
                f=list(force(kind=k));f[5]=0xff800000;rows.append(tuple(f))
            rows += [op(35,0,0,0x7fc00001,0,1),op(36,0,0,0xff800000,1),
                     op(32,0,1,8,1),op(32,0,0x00800000,0x7fffffff,1),op(37,0)]
            rows += [op(35,0,0,0,0x7f800000,1)]
            for field,value in ((5,0),(11,bits(-1)),(12,bits(-1)),(13,0x7fc00001),(3,0x7f800000),
                                (4,0xff800000),(7,0x7f800000),(8,0x7fc00001),(9,0x7f800000),
                                (11,0x7f800000),(12,0x7fc00001),(6,0x7fc00001)):
                bad=list(body(10));bad[1+field]=value;rows.append(tuple(bad))
                                                                          
                                                 
            rows += [op(31,0,0x7fc00001,1),op(31,0,0xff800000,1),world(1),op(31,1,0x7f800000,1)]
        elif 57<=cid<=60: rows=list(boundary_case(cid))
        elif cid==61:
            rows += [g7.object_op(2,0,0x8000000100000000),step(copy=1),g7.object_op(2,0,0),step(copy=2),op(37,1),
                     op(1,0),op(37,0),op(37,1),op(37,2),world(1),body(1,1),force(owner=1),op(38,1,0,1),op(39,1,0),
                     step(),op(38,0,0,1),op(39,0,0)]
        elif cid==62:
            rows += [shape(1,geometry=box()),op(38,0,0,1),op(39,0,1),op(11,0,1,1),op(39,0,1),
                     shape(3),op(39,0,1),op(38,0,0,1),
                     world(1),body(1,1),shape(2,1,1),op(38,1,0,1),op(39,1,0),op(3,0,0),
                     force(),op(38,0,0,1),linear(0,1),angular(0,1),
                     force(owner=1),linear(0,1,owner=1),angular(0,1,owner=1),
                     op(1,0),step(),force(),linear(0,1),angular(0,1),op(38,0,0,1),op(39,0,0)]
        elif cid==63:
            rows=[world(),body(),shape(update=0),force(),step(),op(13,0,0),force(),step(),op(37,0)]
        elif cid==64:
                                                                             
                                                                          
                                                                    
            rows += [op(3,0,0),body(1,v=(7,9),w=2),shape(1,parent=1,game=True),
                     force(),linear(0,3,4),angular(0,5),op(38,0,0,1),op(39,0,0),
                     step(dt=0),op(37,0),step(dt=.25,n=9,copy=1),op(1,0),op(37,0)]
        result.append(Case(cid,'boundary '+str(cid),tuple(rows)))
    return tuple(result)

def encode(rows, decimal=False):
    lines=[str(len(rows))]
    for c in rows:
        lines += [f'C {c.id} {len(c.ops)}']
        lines += [f'O {seq} {code} '+' '.join(str(x) if decimal else f'{x:08x}' for x in a)
                  for seq,(code,*a) in enumerate(c.ops,1)]
    return ''.join(line+('\r\n' if i%3==1 else '\n') for i,line in enumerate(lines[:-1]))+lines[-1]

def read_input(text, decimal=False, expected_count=None):
                                                                   
    normalized=text.replace('\r\n','\n')
    if not text.isascii() or '\r' in normalized: raise ValueError('ASCII / line endings')
    lines=normalized.split('\n')
    if lines[-1]=='': lines.pop()
    def dec(t):
        if not DEC.fullmatch(t) or int(t)>U32: raise ValueError('canonical decimal')
        return int(t)
    n=dec(lines[0])
    if not 1<=n<=64 or (expected_count is not None and n!=expected_count): raise ValueError('N')
    result=[];pos=1
    for cid in range(1,n+1):
        if pos>=len(lines): raise ValueError('truncated')
        h=lines[pos].split(' ');pos+=1
        if len(h)!=3 or h[0]!='C' or dec(h[1])!=cid or not 1<=dec(h[2])<=800: raise ValueError('CASE')
        ops=[]
        for seq in range(1,dec(h[2])+1):
            if pos>=len(lines): raise ValueError('truncated')
            ts=lines[pos].split(' ');pos+=1
            if len(ts)!=67 or ts[0]!='O' or dec(ts[1])!=seq: raise ValueError('O / seq')
            words=[]
            for t in ts[3:]:
                if decimal: words.append(dec(t))
                elif HEX.fullmatch(t): words.append(int(t,16))
                else: raise ValueError('canonical hex')
            row=(dec(ts[2]),*words);validate_operation(row);ops.append(row)
        result.append(Case(cid,'transport',tuple(ops)))
    if pos!=len(lines): raise ValueError('extra lines')
    return tuple(result)

INPUT_NAMES=tuple(prefix+suffix for prefix in ('przypadki-ruch-swiata','proba-ruch-swiata','guard8') for suffix in ('.csv','-stdin.csv'))

def inputs():
    return {name:encode(guard_cases() if name.startswith('guard8') else small_cases() if name.startswith('proba-') else cases(),
                        name.endswith('-stdin.csv')).encode('ascii') for name in INPUT_NAMES}

def mutation_cases():
    pass                                                                   

                                                                           
                                                                             
       
    rows=[]
    for c in cases():
        frame=0;ops=[]
        for row in c.ops:
            if c.id<=48 and row[0] in (31,32):
                frame+=1
                if frame not in (1,2,3,299,300,301,302,599,600):continue
            ops.append(row)
        rows.append(Case(c.id,'mutation '+c.category,tuple(ops)))
    return tuple(rows)

def recipe_cases(recipe):
    pass                                                                    
                                                                           
                                                              
       
    name=recipe['name'];rows=mutation_cases()
    if recipe['probe']=='guard':return guard_cases()
    if recipe['probe']=='fixture':return ()
    life={'applyAction-life':34,'setLinearVelocity-life':35,
          'setAngularVelocity-life':36,'getShapes-life':38}
    if name in life:
        c=rows[63]
        stop=next(i for i,r in enumerate(c.ops,1) if i>8 and r[0]==life[name])
        return (Case(1,'recycled live slot witness '+name,c.ops[:stop]),)
    if name=='shapeBody-life':
        c=rows[60];stop=next(i for i,r in enumerate(c.ops,1) if r[0]==39)
        return (Case(1,'exact foreign-empty shapeBody panic',c.ops[:stop]),)
    if name=='step-false-max8':
        c=rows[63];stop=next(i for i,r in enumerate(c.ops,1) if r[0]==32 and r[3]==9)
        return (Case(1,'valid positive dt with nine substeps',c.ops[:stop]),)
    numeric={'applyAction-finite':lambda r:r[0]==34 and r[4]==0x7f800000,
             'applyAction-point':lambda r:r[0]==34 and r[6]==0x7fc00001,
             'setLinearVelocity-finite':lambda r:r[0]==35 and r[3]==0x7fc00001,
             'setAngularVelocity-finite':lambda r:r[0]==36 and r[3]==0xff800000,
             'step-derived-guard':lambda r:r[0]==32 and r[2]==1,
             'create-body-param':lambda r:r[0]==30 and r[6]==0,
             'body-def-position':lambda r:r[0]==30 and r[4]==0x7f800000,
             'body-def-velocity':lambda r:r[0]==30 and r[8]==0x7f800000,
             'body-def-angular':lambda r:r[0]==30 and r[10]==0x7f800000,
             'body-def-linear-damping':lambda r:r[0]==30 and r[12]==bits(-1),
             'body-def-angular-damping':lambda r:r[0]==30 and r[13]==bits(-1),
             'body-def-gravity-scale':lambda r:r[0]==30 and r[14]==0x7fc00001,
             'body-def-rotation':lambda r:r[0]==30 and r[6]==0}
    if name in numeric:
        c=rows[54];stop=next(i for i,r in enumerate(c.ops,1) if numeric[name](r))
        return (Case(1,'guard witness '+name,c.ops[:stop]),)
    if name in ('game-step-parameters-bypassed','step-negative-guard'):
        return (Case(1,name,rows[50].ops),)
    if name=='step-count-guard':return (Case(1,name,rows[52].ops),)
                                                                            
    selected=[c for c in rows if c.id not in (55,56)]
    return tuple(Case(i,c.category,c.ops) for i,c in enumerate(selected,1))

def verify_input_hashes(directory):
    directory=Path(directory);manifest=json.loads((directory/'wejscia-ruch-swiata-sha256.json').read_bytes())
    expected=inputs()
    if set(manifest)!=set(expected): raise ValueError('manifest keys')
    for name,data in expected.items():
        actual=(directory/name).read_bytes()
        if actual!=data or hashlib.sha256(actual).hexdigest()!=manifest[name]: raise ValueError('input bytes: '+name)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--katalog',type=Path,required=True);args=parser.parse_args()
    args.katalog.mkdir(parents=True,exist_ok=True);manifest={}
    for name,data in inputs().items():
        (args.katalog/name).write_bytes(data);manifest[name]=hashlib.sha256(data).hexdigest()
    (args.katalog/'wejscia-ruch-swiata-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='ascii')
    verify_input_hashes(args.katalog)
    print(f'PUBLIC8 64 / GUARD8 4; operations {sum((len(c.ops) for c in cases()))}; long steps 28800')

if __name__=='__main__': main()
