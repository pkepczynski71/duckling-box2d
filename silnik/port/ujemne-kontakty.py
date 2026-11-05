pass                                                                            
import json
from pathlib import Path
import re
import sys
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
spec=spec_from_file_location('contact_negative_inputs',HERE/'przypadki-kontakty.py');g=module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
NAMES=('ASCII','SPACING','EMPTY_LINE','CR','EOF','TAG','N','DECIMAL','ARITY','WORD','ID','OPCOUNT','SEQ','OPCODE',
       'REGISTER_RANGE','REGISTER_UNINITIALIZED','REGISTER_COLLISION','BOOL','ENUM','UNUSED','ROTATION','DOMAIN',
       'FIXTURE_MANIFOLD','FIXTURE_CACHE','PHASE','GAME_HIT','POPULATION','TRAILING_DATA','CAPTURE_UNCLOSED')
ERRORS={f'F{i:02}':f'PORT9B: INPUT_{name}\n'.encode('ascii') for i,name in enumerate(NAMES,1)}

def scene(rows,ident=1):
    prefix=list(g.cases()[:ident-1]);prefix.append(g.Case(ident,'negative control',tuple(rows)));return tuple(prefix)

def variants():
    pass                                                                              
    basic=scene([g.world(gravity=(0,0))]);full=scene([g.world(gravity=(0,0)),*g.cycle()])
    setup=[g.world(gravity=(0,0)),g.body(),g.body(1,p=(0,.9)),g.shape(geometry=g.box()),g.shape(1,parent=1,geometry=g.box()),*g.cycle(),g.save()]
    seed=g.seed()
    result=[]
    for i in range(1,30):
        key=f'F{i:02}';data=[]
        for duck in (False,True):
            text=g.encode(basic,duck)
            if i==1:text='\ufeff'+text
            elif i==2:text=text.replace('PORT9B 1','PORT9B  1')
            elif i==3:text='\n'+text
            elif i==4:text=text.replace('PORT9B 1\n','PORT9B 1\r')
            elif i==5:text='PORT9B 1\n'
            elif i==6:text=text.replace('PORT9B','PORT9X',1)
            elif i==7:text=text.replace('PORT9B 1','PORT9B 0',1)
            elif i==8:text=text.replace('PORT9B 1','PORT9B 01',1)
            elif i==9:text=text.rsplit(' ',1)[0]+'\n'
            elif i==10:
                lines=text.splitlines();ts=lines[-1].split(' ');ts[4]='01' if duck else '0000000A';lines[-1]=' '.join(ts);text='\n'.join(lines)+'\n'
            elif i==11:text=text.replace('C 1 1','C 2 1')
            elif i==12:text=text.replace('C 1 1','C 1 0')
            elif i==13:text=text.replace('O 1 0','O 2 0')
            elif i==14:text=text.replace('O 1 0','O 1 54')
            elif i==15:text=g.encode(scene([g.world(16)]),duck)
            elif i==16:text=g.encode(scene([g.op(41)]),duck)
            elif i==17:text=g.encode(scene([g.world(),g.world()]),duck)
            elif i==18:text=g.encode(scene([g.world(),g.op(30,0,0,2,0,0,g.bits(1),0,0,0,0,2,0,0,g.bits(1),0,1)],5),duck)
            elif i==19:text=g.encode(scene([g.world(),g.body(),g.op(34,0,0,6,0,0,0,0,1)],5),duck)
            elif i==20:text=g.encode(scene([g.world(),g.op(41,0,1),*g.cycle()[1:]]),duck)
            elif i==21:text=g.encode(scene([g.world(),g.body(),g.transform(0,0,(0,0),(0,0))],5),duck)
            elif i==22:text=g.encode(scene([g.world(),g.body(),g.op(21,0,0,257)],5),duck)
            elif i in (23,24):
                bad=seed.copy();bad[3 if i==23 else 30]=3 if i==23 else 4
                text=g.encode(scene([*setup,g.op(51,0,0,*bad)],5),duck)
            elif i==25:text=g.encode(scene([g.world(),g.op(41),g.op(41),*g.cycle()[1:]]),duck)
            elif i==26:text=g.encode(scene([g.world(),g.body(),g.shape(hit=1)],5),duck)
            elif i==27:text=g.encode(scene([g.world(),g.world(1),g.world(2)]),duck)
            elif i==28:text=g.encode(full,duck)+'x'
            elif i==29:text=g.encode(scene([g.world(),g.op(41)]),duck)
            data.append(text.encode('utf-8'))
        result.append((key,*data,ERRORS[key]))
    return tuple(result)

def positives():
    base=g.encode(g.cases()[:1]);duck=g.encode(g.cases()[:1],True)
    return tuple((name,fn(base).encode('ascii'),fn(duck).encode('ascii')) for name,fn in (
        ('LF',lambda x:x),('CRLF',lambda x:x.replace('\n','\r\n')),('EOF',lambda x:x.rstrip('\n'))))

def probes():
                                                                    
    rows=scene([g.world(),g.world(1),g.op(41),g.op(42),g.op(43),g.op(41,1),
                g.op(42,1),g.op(43,1),g.op(44,1),g.op(45,1),g.op(44),g.op(45)])
    return (*variants(),('F25-two-worlds',g.encode(rows).encode('ascii'),g.encode(rows,True).encode('ascii'),ERRORS['F25']))

def prefix_plan(ident,data):
    pass                                                                    

                                                                           
                                                                              
                                                                          
       
    before_header={'F01','F02','F03','F04','F06','F07','F08'}
    if ident in before_header:return {'fixed':b'','rows':()}
    if ident in ('F05','F11','F12'):return {'fixed':b'PORT9B 1\n','rows':()}
    completed={'F17':1,'F18':1,'F19':2,'F20':1,'F21':2,'F22':2,'F23':11,'F24':11,
               'F25':2,'F26':2,'F27':2,'F28':6,'F29':2,'F25-two-worlds':5}.get(ident,0)
    last=5 if ident in ('F18','F19','F21','F22','F23','F24','F26') else 1
    lines=data.decode('ascii').splitlines();n=int(lines[0].split()[1]);cursor=1;rows=[];declared=0
    for case in range(1,last+1):
        header=lines[cursor].split();declared=int(header[2]);cursor+=1;ops=[]
        take=declared if case<last else completed
        for line in lines[cursor:cursor+take]:
            words=line.split();ops.append((int(words[2]),*(int(x,16) for x in words[3:])))
        cursor+=declared
        if case==last:
            phase=0;owner=0
            for op in ops:
                if 41<=op[0]<=45:phase=op[0];owner=op[1]
            if phase and phase<45:ops.extend(g.op(code,owner) for code in range(phase+1,46))
            if not ops:ops=[g.world(gravity=(0,0))]
        rows.append(g.Case(case,'valid fatal-prefix control',tuple(ops)))
    return {'rows':tuple(rows),'N':n,'case':last,'declared':declared,'completed':completed,'endcase':ident=='F28'}

def expected_prefix(plan,control=b''):
    if 'fixed' in plan:return plan['fixed']
    out=[f'PORT9B {plan['N']}\n'.encode('ascii')];case=0
    for line in control.splitlines(keepends=True):
        fields=line.split();tag=fields[0]
        if tag==b'PORT9B':continue
        if tag==b'CASE':
            case=int(fields[1])
            out.append(f'CASE {case} {plan['declared']}\n'.encode('ascii') if case==plan['case'] else line)
        elif tag==b'END':break
        elif case<plan['case']:out.append(line)
        elif tag==b'ENDCASE':
            if plan['endcase']:out.append(line)
        elif int(fields[2])<=plan['completed']:out.append(line)
    return b''.join(out)

def write(directory):
    import hashlib
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);manifest=[]
    for guard,c,d,stderr in probes():
        row={'id':guard,'stderr':stderr.decode('ascii'),'exit':2,'stop_after_refusal':True,'inputs':{}}
        for side,data in (('c',c),('duckling',d)):
            name=f'kontakty-ujemny-{guard}-{side}.csv';(directory/name).write_bytes(data);row['inputs'][side]={'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        manifest.append(row)
    (directory/'ujemne-kontakty-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='ascii');return manifest
if __name__=='__main__':write(HERE/'kontakty-ujemne')
