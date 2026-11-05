pass                                                            

                                                                           
                                                                             
   
import argparse
from collections import Counter, defaultdict
import io
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys
from importlib.util import spec_from_file_location, module_from_spec

HERE = Path(__file__).resolve().parent
def load(name, file):
    spec = spec_from_file_location(name, HERE / file)
    m = module_from_spec(spec);sys.modules[name] = m;spec.loader.exec_module(m)
    return m

g = load('solver_compare_inputs', 'przypadki-solver.py')
p9 = load('solver_compare_contacts', 'porownaj-kontakty.py')
require = p9.require
PRIVATE = p9.PRIVATE | frozenset('W10 CX10 SB10 PK10 SC10 BV10 I10'.split())
SCHEMA = {
    'PORT10':(1,0), 'COMPONENT10':(1,0), 'W10':(3,8), 'CX10':(3,14),
    'HN10':(3,1), 'HR10':(4,11), 'HC10':(4,2), 'HG10':(5,15),
    'SB10':(6,4), 'PK10':(6,3), 'SC10':(8,43), 'BV10':(6,7), 'I10':(2,6), 'Z10':(2,5),
    'FW':(1,9), 'FB':(2,17), 'FC':(4,51), 'FX':(3,16), 'FP':(4,0),
    'FH10':(4,1), 'FM10':(2,30), 'FI10':(1,7),
}
ORDER = [('E',),('R',),('V',),('W',),('B',),('S','G'),('L','A'),('Q',),('QGN','QG'),
         ('SB',),('K','M','MCN','MC'),('CD',),('NC9',),('RC9',),('GV',),('GL',),('GE',),('GC',),
         ('HN10','HR10'),('HC10','HG10'),
         *[(x,) for x in 'X P T F U H Y DN RT JW RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 W10 CX10 SB10 PK10 SC10 BV10 I8 I9 I10 Z8 Z9 Z10'.split()]]
RANK = {tag:i for i, group in enumerate(ORDER) for tag in group}
NEW_COUNTS = ('W10','CX10','SB10','PK10','SC10','BV10')
HIT_COUNTS = ('HN10','HR10','HC10','HG10')
SC_FIELDS = ('contactId','indexA','indexB','pointCount','normal.x','normal.y','invMassA','invIA',
             'invMassB','invIB','friction','restitution','tangentSpeed','rollingResistance','rollingMass',
             'rollingImpulse','biasRate','massScale','impulseScale') + tuple(
                 f'point{point}.{name}' for point in range(2) for name in
                 ('anchorA.x','anchorA.y','anchorB.x','anchorB.y','baseSeparation','relativeVelocity',
                  'normalImpulse','tangentImpulse','totalNormalImpulse','normalMass','tangentMass'))

def parse_record(line, component=False):
    tag = line.split(' ', 1)[0]
    schema = (8, 0) if component and tag == 'F' else SCHEMA.get(tag)
    if schema is None:
        require(tag not in ('PORT9B','TASK','UP'), 'tag outside 10/1: ' + tag)
        return p9.parse_record(line)
    require(line.isascii() and line.endswith('\n') and '\r' not in line and len(line) <= 131072,
            'output ASCII/LF/line length')
    ts = line[:-1].split(' ');d,k = schema
    require(len(ts) == 1+d+k, tag + ' arity')
    values = []
    for i,t in enumerate(ts[1:]):
        require((g.g8.DEC if i<d else g.g8.HEX).fullmatch(t) is not None, tag + ' canonical word')
        value = int(t,10 if i<d else 16)
        require(value <= g.U32, tag + ' u32');values.append(value)
    return tag, tuple(values)

def format_record(tag, values, component=False):
    schema = (8,0) if component and tag=='F' else SCHEMA.get(tag)
    if schema is None:return p9.format_record(tag, values)
    d = schema[0]
    return tag + ' ' + ' '.join(str(v) if i<d else f'{v:08x}' for i,v in enumerate(values)) + '\n'

def projection(source):
    for line in source:
        tag,_ = parse_record(line)
        if tag not in PRIVATE:yield line

def field_name(tag, values, index):
    if tag=='SC10' and index>=8:
        return ('defined.low','defined.high',*SC_FIELDS)[index-8]
    if tag=='W10' and index>=3:
        return ('hertz','damping','push','restitutionThreshold','hitThreshold','contactSpeed','warm','speculative')[index-3]
    if tag=='CX10' and index>=3:
        return ('dt','inv_dt','h','inv_h','subStepCount','contactSoft.bias','contactSoft.mass','contactSoft.impulse',
                'staticSoft.bias','staticSoft.mass','staticSoft.impulse','restitutionThreshold','maxLinearVelocity','enableWarmStarting')[index-3]
    if tag=='BV10' and index>=6:return ('vx','vy','w','deltaPosition.x','deltaPosition.y','deltaRotation.c','deltaRotation.s')[index-6]
    if tag in SCHEMA:return f'word[{index}]'
    return p9.name(tag,values,index)

def first_difference(left, right, project=False, component=False):
    for lineno,(a,b) in enumerate(zip_longest(projection(left) if project else left, right),1):
        if a==b:continue
        if a is None or b is None:return {'line':lineno,'error':'missing/excess row','C':a,'Duckling':b}
        ta,va = parse_record(a,component);tb,vb = parse_record(b,component)
        if ta!=tb:return {'line':lineno,'tag':ta,'other_tag':tb,'C':a[:8192],'Duckling':b[:8192]}
        for i,(x,y) in enumerate(zip(va,vb)):
            if x!=y:
                context = {'case':va[0], 'seq':va[1] if len(va)>1 else 0, 'tag':ta}
                if ta=='SC10':context.update(world=va[2],sub=va[3],phase=va[4],color=va[5],packet=va[6],lane=va[7])
                return {'line':lineno,**context,'field':field_name(ta,va,i),
                        'C':f'{x:08x}','Duckling':f'{y:08x}','left':a[:8192],'right':b[:8192]}
        return {'line':lineno,'error':'different arity','C':a[:8192],'Duckling':b[:8192]}
    return None

def check_trace(rows, private, case):
    if not private:
        require(not any(rows[t] for t in PRIVATE), 'OBS0 private record');return
    worlds = {v[2] for v in rows['W']}
    require([v[2] for v in rows['W10']] == sorted(worlds), 'W10 live worlds/completeness')
    for v in rows['W10']:
        require(v[-2] <= 1 and v[-1] <= 1, 'W10 bool')
        for i, word in enumerate(v[3:9]):
            require(math.isfinite(g.number(word)) or (case in (117,120) and i==5 and word==0x7f800000),
                    'W10 nonfinite outside frozen domain')
    for v in rows['SC10']:
        color,packet,lane = v[5:8];defined = v[8] | v[9]<<32;f=v[10:]
        require(color<=11 and lane<(1 if color==11 else 4),'SC10 color/lane')
        expected = (1<<41)-1 if color<11 or f[3]==2 else (1<<30)-1
        require(defined==expected,'SC10 defined mask')
        require(f[3]<=2,'SC10 pointCount')
        for k,word in enumerate(f):
            if not (defined>>k)&1:require(word==0,'SC10 undefined field canonical zero')
            elif k>=4:require(math.isfinite(g.number(word)),'SC10 finite defined scalar')
    require(len({v[2:8] for v in rows['SC10']})==len(rows['SC10']),'SC10 duplicate prefix')
    require(len({v[2:6] for v in rows['PK10']})==len(rows['PK10']),'PK10 duplicate prefix')
    require(len({v[2:6] for v in rows['BV10']})==len(rows['BV10']),'BV10 duplicate prefix')
    require(len({v[2] for v in rows['CX10']})==len(rows['CX10']),'CX10 duplicate world')
    for v in rows['CX10']:
        require(v[7] in (1,4,8) and v[-1]<=1,'CX10 substeps/warm')
    for v in rows['PK10']:
        require(v[3]<=11 and v[5]<(1 if v[3]==11 else 4),'PK10 color/lane')
    solver_worlds={v[2] for v in rows['CX10']}
    for tag in ('SB10','PK10','SC10','BV10'):
        require(all(v[2] in solver_worlds for v in rows[tag]),tag+' without current task')

def check_snapshot(case, seq, operation, observations, private, completed):
    rows=defaultdict(list);rank=-1
    for tag,v in observations:
        require(v[:2]==(case,seq),tag+' case/seq')
        require(tag in RANK and RANK[tag]>=rank,tag+' group order');rank=RANK[tag];rows[tag].append(v)
    require(rows['E']==[(case,seq,*operation)],'E exact input words')
    require(len(rows['R'])==(2 if operation[0]==16 else 1),'R count')
    for j,v in enumerate(rows['R']):require(v[2]==j and v[3]<=5 and v[4]<=3,'R status/kind/index')
    counts=Counter(t for t,v in observations)
    for tag in ('Z8','Z9','Z10'):require(len(rows[tag])==1,tag+' exactly one')
    require(rows['Z8'][0][8:26]==tuple(counts[t] for t in p9.p8.PUBLIC_COUNTS),'Z8 public counters')
    z9=rows['Z9'][0]
    require(z9[5:12]==tuple(counts[t] for t in p9.PUBCOUNTS),'Z9 public counters')
    require(z9[12:16]==(seq,seq,3,0),'Z9 completed/profile/FIXTURE_INPUT')
    if operation[0] in (31,32) and rows['R'][0][3]==0:completed+=1
    require(rows['Z10'][0][2:]==(*[counts[t] for t in HIT_COUNTS],completed),'Z10 counters/completed')
    if private:
        for tag in ('I8','I9','I10'):require(len(rows[tag])==1,tag+' exactly one')
        require(rows['I8'][0][2:]==tuple(counts[t] for t in 'X P T F U H Y DN RT JW'.split()),'I8 counts')
        require(rows['I9'][0][2:20]==tuple(counts[t] for t in p9.PRIVCOUNTS),'I9 counts')
        require(rows['I9'][0][20:]==(0,seq),'I9 task blocks/completed')
        require(rows['I10'][0][2:]==tuple(counts[t] for t in NEW_COUNTS),'I10 counts')
    else:require(not rows['I10'],'OBS0 I10')
    for head,item,regsize in (('HN10','HR10',1),('HC10','HG10',2)):
        headers={v[2:2+regsize]:v for v in rows[head]}
        require(len(headers)==len(rows[head]),head+' duplicate prefix')
        items=defaultdict(list)
        for v in rows[item]:items[v[2:2+regsize]].append(v)
        require(set(items)<=set(headers),item+' without header')
        for key,h in headers.items():
            require([v[2+regsize] for v in items[key]]==list(range(h[-1])),item+' count/order')
            if head=='HC10':require(h[-2]<=5 and (h[-2]==0 or h[-1]==0),'HC10 status/count')
    check_trace(rows,private,case)
    return completed

def validate_output(source, cases, private=True, *, header_n=None, model=None):
    stream=io.StringIO(source) if isinstance(source,str) else source
    counts=Counter()
    def take(tag):
        line=stream.readline(131073);require(bool(line),'truncated '+tag);actual,v=parse_record(line)
        require(actual==tag,'expected '+tag+', got '+actual);counts[tag]+=1;return v
    require(take('PORT10')==((len(cases) if header_n is None else header_n),),'PORT10 N')
    for c in cases:
        require(take('CASE')==(c.id,len(c.ops)),'CASE input');completed=0
        for seq,operation in enumerate(c.ops,1):
            observations=[]
            while True:
                line=stream.readline(131073);require(bool(line),'truncated snapshot')
                tag,v=parse_record(line);counts[tag]+=1;observations.append((tag,v))
                if tag=='Z10':break
            try:
                completed=check_snapshot(c.id,seq,operation,observations,private,completed)
                if model is not None:model.check(c.id,seq,operation,observations,private)
            except (ValueError,KeyError,IndexError) as exc:raise ValueError(f'case {c.id}, seq {seq}: {exc}') from exc
        require(take('ENDCASE')==(c.id,),'ENDCASE')
    require(take('END')==((len(cases) if header_n is None else header_n),),'END N')
    require(not stream.read(1),'trailing output');return counts

def validate_component(source, cases, *, header_n=None):
    stream=io.StringIO(source) if isinstance(source,str) else source;counts=Counter()
    def take(tag,expected=None):
        line=stream.readline(131073);require(bool(line),'truncated '+tag);t,v=parse_record(line,True)
        require(t==tag,'expected '+tag+', got '+t)
        if expected is not None:require(v==expected,tag+' echo/input')
        counts[t]+=1;return v
    n=len(cases) if header_n is None else header_n;take('COMPONENT10',(n,))
    for c in cases:
        before=counts.copy()
        take('F',(c.id,c.fixture,c.substeps,c.warm,len(c.bodies),len(c.contacts),len(c.helpers),len(c.phases)))
        take('FW',(c.id,*c.fw))
        for j,v in enumerate(c.bodies):take('FB',(c.id,j,*v))
        for j,(color,local,v) in enumerate(c.contacts):take('FC',(c.id,j,color,local,*v))
        for j,(kind,v) in enumerate(c.helpers):take('FX',(c.id,j,kind,*v))
        expected_helpers=[]
        for j,(kind,values) in enumerate(c.helpers):
            if kind==0:expected_helpers += [(j,op,lane) for op in range(14) for lane in range(4)]+[(j,14,0)]
            elif kind==1:expected_helpers += [(j,op,lane) for op in range(4) for lane in range(4)]
            else:
                count=values[0]|values[1]<<32;base=32 if values[2]==0 else 4
                blocks=4 if count>4*base else (count+base-1)//base
                expected_helpers += [(j,op,0) for op in range(2+2*blocks)]
        for expected in expected_helpers:
            v=take('FH10');require(v[:4]==(c.id,*expected),'FH10 order/prefix')
        for ordinal,(sub,phase) in enumerate(c.phases):
            take('FP',(c.id,ordinal,sub,phase));v=take('CX10')
            require(v[:3]==(c.id,ordinal+1,0),'CX10 component prefix')
            order=-1;last_bodies=[];sc=[];packets=[]
                                                                         
            while True:
                position=stream.tell();line=stream.readline(131073);require(bool(line),'truncated component phase')
                tag,v=parse_record(line,True)
                if tag not in ('SB10','PK10','SC10','BV10'):stream.seek(position);break
                rank=('SB10','PK10','SC10','BV10').index(tag);require(rank>=order,'component trace group order');order=rank;counts[tag]+=1
                require(v[:3]==(c.id,ordinal+1,0),tag+' component prefix')
                if tag!='PK10':require(v[3:5]==(sub,phase),tag+' sub/phase')
                if tag=='BV10':last_bodies.append(v[5])
                if tag=='SC10':sc.append(v)
                if tag=='PK10':packets.append(v)
            require(last_bodies==sorted(v[0] for v in c.bodies),'BV10 body completeness')
            expected=sum(((sum(x[0]==color for x in c.contacts)+3)//4)*4 for color in range(11))+sum(x[0]==11 for x in c.contacts)
            require(len(sc)==expected,'SC10 component lane completeness')
            require(len(packets)==(expected if phase==0 else 0),'PK10 Prepare only')
        for j in range(len(c.contacts)):v=take('FM10');require(v[:2]==(c.id,j),'FM10 order')
        v=take('FI10');actual=counts-before
        require(v==(c.id,len(c.phases),*[actual[t] for t in ('SC10','BV10','SB10','PK10','FH10','FM10')]),'FI10 counts')
        take('ENDCASE',(c.id,))
    take('END',(n,));require(not stream.read(1),'trailing component output');return counts

def compare_files(c, duckling, c0, cases, codes=(0,0,0), *, component=False, header_n=None, models=None):
    errors=[];streams={};difference=None
    entries=[('C OBS1',c,codes[0],True),('Duckling',duckling,codes[1],True)]
    if not component:entries.append(('C OBS0',c0,codes[2],False))
    for label,path,code,private in entries:
        if code:errors.append(label+f' exit {code}')
        try:
            with Path(path).open(encoding='ascii',newline='') as stream:
                counts=(validate_component(stream,cases,header_n=header_n) if component else
                        validate_output(stream,cases,private,header_n=header_n,model=(models or {}).get(label)))
            streams[label]={'records':dict(counts),'bytes':Path(path).stat().st_size}
        except (ValueError,OSError) as exc:errors.append(label+': '+str(exc))
    pairs=[(c,duckling,False)] if component else [(c,duckling,False),(c,c0,True)]
    for left,right,project in pairs:
        try:
            with Path(left).open(encoding='ascii',newline='') as a,Path(right).open(encoding='ascii',newline='') as b:
                diff=first_difference(a,b,project,component)
            if diff:errors.append(diff);difference=difference or diff
        except (ValueError,OSError) as exc:errors.append(str(exc))
    return {'profile':'COMPONENT10' if component else 'PUBLIC10','N':len(cases),'errors':errors,
            'first_difference':difference,'streams':streams}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('c','duckling','raport'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--c-bez',type=Path);parser.add_argument('--component',action='store_true')
    parser.add_argument('--N',type=int,default=124)
    args=parser.parse_args();cases=(g.components() if args.component else g.verify())[:args.N]
    result=compare_files(args.c,args.duckling,args.c_bez,cases,component=args.component)
    args.raport.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));sys.exit(int(bool(result['errors'])))
