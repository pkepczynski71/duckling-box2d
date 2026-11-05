pass                                                                      

                                                                              
                                                                             
   
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct

HERE=Path(__file__).resolve().parent
COUNT=448
PAIRS=((1,0),(3,0),(1,1),(2,0),(2,1),(3,1),(2,3))
EPS=2.0**-23

def bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def number(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def f32(value):return number(bits(value))

@dataclass(frozen=True)
class Shape:
    tag:int
    words:tuple

@dataclass(frozen=True)
class Case:
    id:int
    kind:int
    name:str
    a:Shape
    b:Shape
    witnesses:tuple=()

def valid_rotation(c,s):
    qq=f32(f32(c*c)+f32(s*s))
    return f32(1-f32(.0006))<qq<f32(1+f32(.0006))

def validate_shape(shape,constructor=False):
    if shape.tag not in range(5) or len(shape.words)!=44:raise ValueError('shape width/tag')
    if any(type(u) is not int or not 0<=u<=0xffffffff for u in shape.words):raise ValueError('u32 width')
    g=shape.words[4:];v=tuple(number(u) for u in shape.words)
    if any(not math.isfinite(x) for i,x in enumerate(v) if not (shape.tag==3 and i==4)):
        raise ValueError('NaN/Inf')
    if not valid_rotation(v[2],v[3]):raise ValueError('rotation')
    f=tuple(number(u) for u in g)
    if shape.tag==0:
        used=3
        if f[2]<0:raise ValueError('circle radius')
    elif shape.tag in (1,2):
        used=5 if shape.tag==1 else 4
        dx=f32(f[2]-f[0]);dy=f32(f[3]-f[1]);dd=f32(f32(dx*dx)+f32(dy*dy))
        threshold=EPS if constructor else f32(EPS*EPS)
        if not math.isfinite(dd) or not dd>threshold:raise ValueError('segment length')
        if shape.tag==1 and f[4]<0:raise ValueError('capsule radius')
    elif shape.tag==4:
        used=7
        if f[0]<=0 or f[1]<=0 or f[6]<0 or not valid_rotation(f[4],f[5]):raise ValueError('box')
    else:
        count=g[0];used=2+2*count
        if not 3<=count<=8 or f[1]<0:raise ValueError('polygon count/radius')
        vertices=[(f[2+2*i],f[3+2*i]) for i in range(count)]
                                                                             
                                                                            
        for i,p in enumerate(vertices):
            q=vertices[(i+1)%count];dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
            if not length>0:raise ValueError('polygon edge')
            for j,r in enumerate(vertices):
                if j not in (i,(i+1)%count) and (dx*(r[1]-p[1])-dy*(r[0]-p[0]))/length<=0:
                    raise ValueError('polygon hull')
            r=vertices[(i+2)%count];ex=r[0]-p[0];ey=r[1]-p[1]
            if (ex*(q[1]-p[1])-ey*(q[0]-p[0]))/math.hypot(ex,ey)>=-.005:
                raise ValueError('polygon collinear')
    if any(g[used:]):raise ValueError('unused geometry')

def validate_case(case):
    if not 1<=case.id<=COUNT or not 0<=case.kind<7:raise ValueError('id/kind')
    actual=tuple(3 if s.tag==4 else s.tag for s in (case.a,case.b))
    if actual!=PAIRS[case.kind]:raise ValueError('kind/type')
    for side,shape in enumerate((case.a,case.b)):
        constructor=(case.kind==5 and side==1) or (case.kind==6 and side==0)
        validate_shape(shape,constructor)

def cases():
    data=json.loads((HERE/'przypadki-pary.json').read_text(encoding='utf-8'))
    rows=tuple(Case(c['id'],c['kind'],c['name'],
        Shape(c['a']['tag'],tuple(int(u,16) for u in c['a']['words'])),
        Shape(c['b']['tag'],tuple(int(u,16) for u in c['b']['words'])),tuple(c['witnesses'])) for c in data['cases'])
    if len(rows)!=COUNT or [c.id for c in rows]!=list(range(1,COUNT+1)):raise ValueError('448 ids')
    if Counter(c.kind for c in rows)!=Counter({k:64 for k in range(7)}):raise ValueError('7 x 64')
    for case in rows:validate_case(case)
    return rows

def encode(rows,decimal=False,ending='\n'):
    rows=tuple(rows)
    if not 1<=len(rows)<=COUNT:raise ValueError('N')
    lines=['PORT9A '+str(len(rows))]
    for c in rows:
        validate_case(c)
        lines.append(f'P {c.id} {c.kind}')
        for label,s in zip(('A','B'),(c.a,c.b)):
            lines.append(label+' '+str(s.tag)+' '+' '.join(str(u) if decimal else f'{u:08x}' for u in s.words))
    return ending.join(lines)+ending

def read_input(text,decimal=False):
    if not text or not text.isascii() or '\0' in text or len(text)>1000000:raise ValueError('ASCII/length')
    normalized=text.replace('\r\n','\n')
    if '\r' in normalized:raise ValueError('CR')
    lines=normalized.split('\n')
    if lines[-1]=='':lines.pop()
    def tokens(line):
        ts=line.split(' ')
        if any(not t for t in ts) or any('\t' in t for t in ts):raise ValueError('spacing')
        return ts
    def dec(t):
        if not re.fullmatch(r'0|[1-9][0-9]{0,9}',t) or int(t)>0xffffffff:raise ValueError('decimal')
        return int(t)
    header=tokens(lines[0])
    if len(header)!=2 or header[0]!='PORT9A':raise ValueError('header')
    n=dec(header[1])
    if not 1<=n<=COUNT or len(lines)!=1+3*n:raise ValueError('N/lines')
    result=[]
    for index in range(n):
        p=tokens(lines[1+3*index])
        if len(p)!=3 or p[0]!='P':raise ValueError('P')
        ident,kind=map(dec,p[1:])
        if ident!=index+1:raise ValueError('id')
        shapes=[]
        for offset,label in enumerate(('A','B')):
            ts=tokens(lines[2+3*index+offset])
            if len(ts)!=46 or ts[0]!=label:raise ValueError('A/B width')
            words=[]
            for t in ts[2:]:
                if decimal:words.append(dec(t))
                elif re.fullmatch('[0-9a-f]{8}',t):words.append(int(t,16))
                else:raise ValueError('hex')
            shapes.append(Shape(dec(ts[1]),tuple(words)))
        c=Case(ident,kind,'input',*shapes);validate_case(c);result.append(c)
    return tuple(result)

def small_cases():
                                                                   
    from dataclasses import replace
    return tuple(replace(c,id=i+1) for i,c in enumerate(cases()[::64]))

def write(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for prefix,rows in (('przypadki',cases()),('proba',small_cases())):
        for dec,suffix in ((False,''),(True,'-stdin')):
            name=prefix+'-pary'+suffix+'.csv';data=encode(rows,dec).encode('ascii')
            (directory/name).write_bytes(data);hashes[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'N':len(rows),'records':1+3*len(rows)}
    (directory/'wejscia-pary-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='ascii')
    return hashes

def verify_input_hashes(directory):
    directory=Path(directory);expected=json.loads((HERE/'wejscia-pary-sha256.json').read_bytes())
    for name,item in expected.items():
        data=(directory/name).read_bytes()
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('input hash '+name)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--katalog',type=Path,default=HERE)
    print(json.dumps(write(ap.parse_args().katalog),indent=2))
