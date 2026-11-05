pass                                                                      

                                                                              
                                                                          
   
from dataclasses import dataclass
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib.util import spec_from_file_location, module_from_spec
spec=spec_from_file_location('solver_negative_fixtures',Path(__file__).with_name('fixtury-solver.py'))
f=module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)

NAMES = ('ASCII','SPACING','EMPTY_LINE','CR','EOF','TAG','N','DECIMAL','ARITY','WORD','ID',
         'OPCOUNT','SEQ','OPCODE','REGISTER_RANGE','REGISTER_UNINITIALIZED','REGISTER_COLLISION',
         'BOOL','ENUM','UNUSED','ROTATION','DOMAIN','FIXTURE_MANIFOLD','FIXTURE_CACHE','PHASE',
         None,'POPULATION','TRAILING_DATA','CAPTURE_UNCLOSED')
ERRORS={f'F{i:02}':f'PORT10: INPUT_{name}\n'.encode('ascii') for i,name in enumerate(NAMES,1) if name}


def payload(tag, prefix, words, decimal=False):
    fmt=str if decimal else lambda w:f'{w:08x}'
    return ' '.join([tag,*map(str,prefix),*map(fmt,words)])+'\n'


def component(decimal=False):
    pass                                                                    
    fb=[0,f.bits(1),f.bits(1),0,0,0,0,0,f.bits(1),0,0,0,0,0,0,f.bits(1),0]
    fc=[0,0,1,0,1,*([f.bits(1)]*4),f.bits(.5),0,0,0,0x10000,*([0]*7),
        0,f.bits(1),0,1,*([0]*26)]
    assert len(fc)==51
    lines=['COMPONENT10 1\n','F 1 1 1 0 2 1 0 8\n',
           payload('FW',(1,),(0,0,*f.WORLD[4:10],f.bits(1)),decimal),
           payload('FB',(1,0),fb,decimal),
           payload('FB',(1,1),[1,*fb[1:]],decimal),payload('FC',(1,0,0,0),fc,decimal)]
    phases=[(0,0),*((1,p) for p in range(1,6)),(0,6),(0,7)]
    lines += [f'FP 1 {j} {sub} {phase}\n' for j,(sub,phase) in enumerate(phases)]
    return ''.join(lines).encode('ascii')


@dataclass(frozen=True)
class Negative:
    name: str
    error: str
    c: bytes
    duckling: bytes
    controls: tuple
                                                                              
    boundary: tuple

    @property
    def stderr(self): return ERRORS[self.error]


def replace_word(data, tag, index, value):
    lines=data.decode('ascii').splitlines()
    target=next(j for j,line in enumerate(lines) if line.startswith(tag+' '))
    words=lines[target].split(' ');words[index]=value;lines[target]=' '.join(words)
    return ('\n'.join(lines)+'\n').encode('ascii')


def variants():
    result=[]
    for error in ERRORS:
        i=int(error[1:]);sides=[];controls=[];boundary=('header',)
        for decimal in (False,True):
            rows=[f.world()]
            data=f.public_bytes(rows,decimal);control=data
            if i==1: data=b'\xef\xbb\xbf'+data
            elif i==2:data=data.replace(b'PORT10 1',b'PORT10  1',1)
            elif i==3:data=b'\n'+data
            elif i==4:data=data.replace(b'PORT10 1\n',b'PORT10 1\r',1)
            elif i==5:data=b'PORT10 1\n';boundary=('case',)
            elif i==6:data=data.replace(b'PORT10',b'PORT1X',1)
            elif i==7:data=b'PORT10 0\n'
            elif i==8:data=data.replace(b'PORT10 1',b'PORT10 01',1)
            elif i==9:data=data.rsplit(b' ',1)[0]+b'\n';boundary=('operation',1)
            elif i==10:data=replace_word(data,'O',3,'4294967296' if decimal else '0000000A');boundary=('operation',1)
            elif i==11:data=data.replace(b'C 1 1',b'C 2 1',1);boundary=('case',)
            elif i==12:data=data.replace(b'C 1 1',b'C 1 0',1);boundary=('case',)
            elif i==13:data=data.replace(b'O 1 54',b'O 2 54',1);boundary=('operation',1)
            elif i==14:data=data.replace(b'O 1 54',b'O 1 56',1);boundary=('operation',1)
            elif i==15:
                control=f.public_bytes([f.world(),f.g.body(),f.g.shape()],decimal)
                rows=[f.world(),f.g.body(),f.g.shape(slot=512)];data=f.public_bytes(rows,decimal);boundary=('operation',3)
            elif i==16:
                control=f.public_bytes([f.world(),f.op(55,0,1)],decimal)
                data=f.public_bytes([f.op(55,0,1)],decimal);boundary=('operation',1)
                control=f.public_bytes([f.world()],decimal)
            elif i==17:
                control=f.public_bytes([f.world(),f.op(55,0,1)],decimal)
                data=f.public_bytes([f.world(),f.world()],decimal);boundary=('operation',2)
            elif i==18:
                data=replace_word(data,'O',13,'2' if decimal else '00000002');boundary=('operation',1)
            elif i==19:
                control=f.public_bytes([f.world(),f.g.body()],decimal)
                data=f.public_bytes([f.world(),f.g.body(kind=3)],decimal);boundary=('operation',2)
            elif i==20:
                data=replace_word(data,'O',14,'2147483648' if decimal else '80000000');boundary=('operation',1)
            elif i==21:
                control=f.public_bytes([f.world(),f.g.body(),f.g.transform(0,0,(0,0),(1,0))],decimal)
                data=f.public_bytes([f.world(),f.g.body(),f.g.transform(0,0,(0,0),(0,0))],decimal);boundary=('operation',3)
            elif i==22:
                control=f.public_bytes([f.world(game=0)],decimal)
                data=replace_word(control,'O',8,'2143289344' if decimal else '7fc00000');boundary=('operation',1)
            elif i in (23,24,25,29):
                control=component(decimal);data=control
                if i==23:data=replace_word(data,'FC',5+24,'3' if decimal else '00000003');boundary=('record','FC')
                elif i==24:data=replace_word(data,'FC',5+14,'4' if decimal else '00000004');boundary=('record','FC')
                elif i==25:data=data.replace(b'FP 1 1 1 1\n',b'FP 1 1 1 2\n');boundary=('phase',1)
                else:data=data.split(b'FP 1 1 ',1)[0];boundary=('phase',1)
            elif i==27:
                control=f.public_bytes([f.world(),f.world(1),f.op(55,0,1)],decimal)
                data=f.public_bytes([f.world(),f.world(1),f.world(2)],decimal);boundary=('operation',3)
            elif i==28:data+=b'x';boundary=('trailing',)
            else:raise ValueError(error)
            sides.append(data);controls.append(control)
        result.append(Negative(error,error,*sides,tuple(controls),boundary))
    return tuple(result)


def expected_prefix(probe, control):
    pass                                                                    
    mode=probe.boundary[0]
    if mode=='header':return b''
    lines=control.splitlines(keepends=True)
    if mode=='case':return b'PORT10 1\n'
    output=[]
    for line in lines:
        ts=line.split();tag=ts[0]
        if tag==b'END' or (tag==b'ENDCASE' and mode!='trailing'):break
        if mode=='operation' and tag==b'E' and int(ts[2])>=probe.boundary[1]:break
        if mode=='record' and tag==probe.boundary[1].encode('ascii'):break
        if mode=='phase' and tag==b'FP' and int(ts[2])>=probe.boundary[1]:break
        output.append(line)
    return b''.join(output)


def check(probe, code, stdout, stderr, control):
    if code!=2:raise ValueError(probe.name+': expected exit2, got '+str(code))
    if stderr!=probe.stderr:raise ValueError(probe.name+': exact one-line stderr mismatch')
    expected=expected_prefix(probe,control)
    if stdout!=expected:raise ValueError(probe.name+': output after refusal / incomplete valid prefix')


def positives():
    rows=[f.world(),f.g.body(),f.g.shape(hit=1),f.op(55,0,1)]
    base=[f.public_bytes(rows,d) for d in (False,True)]
    return tuple((name,*(fn(data) for data in base)) for name,fn in (
        ('LF',lambda data:data),('CRLF',lambda data:data.replace(b'\n',b'\r\n')),
        ('EOF',lambda data:data.rstrip(b'\n'))))
