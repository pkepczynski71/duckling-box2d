pass                                                                         

                                                                             
                                                                                 
   
import argparse
from collections import Counter,defaultdict
import hashlib
import importlib.util
import io
from itertools import zip_longest
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
p10=load('sen_compare10','porownaj-solver.py');g=load('sen_compare_inputs','przypadki-sen.py')
require=p10.require
NEW_PRIVATE=tuple('WS11 BS11 SS11 SD11 SM11 AB11 TR11 SP11 SF11 BP11 BF11'.split())
PRIVATE=p10.PRIVATE|frozenset((*NEW_PRIVATE,'I11'))
SCHEMA={**p10.SCHEMA,'PORT11':(1,0),'COMPONENT11':(1,0),
        'SW11':(3,2),'GS11':(3,10),'WS11':(4,4),'BS11':(4,6),'SS11':(4,6),
        'SD11':(5,1),'SM11':(5,28),'AB11':(4,None),'TR11':(4,7),
        'SP11':(3,3),'SF11':(4,1),'BP11':(3,3),'BF11':(4,1),'I11':(2,11),'Z11':(2,3)}
SCHEMA.pop('PORT10');SCHEMA.pop('COMPONENT10')
ORDER=[*p10.ORDER[:18],('SW11',),('GS11',),*p10.ORDER[18:]]
                                                                                 
ORDER=[('E',),('R',),('V',),('W',),('B',),('S','G'),('L','A'),('Q',),('QGN','QG'),('SB',),
       ('K','M','MCN','MC'),('CD',),('NC9',),('RC9',),('GV',),('GL',),('GE',),('GC',),
       ('HN10','HR10'),('HC10','HG10'),('SW11',),('GS11',),
       *[(x,) for x in 'X P T F U H Y DN RT JW RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 W10 CX10 SB10 PK10 SC10 BV10'.split()],
       *[(x,) for x in NEW_PRIVATE],('I8',),('I9',),('I10',),('I11',),('Z8',),('Z9',),('Z10',),('Z11',)]
RANK={tag:j for j,group in enumerate(ORDER) for tag in group}
I8_TAGS=tuple('X P T F U H Y DN RT JW'.split())
FIELDS={
    'SW11':('status','enableSleeping'),
    'GS11':('status','slot','birth.low','birth.high','owner.low','owner.high','isAwake','isSleeping','sleepEnabled','sleepThreshold'),
    'WS11':('enableSleep','world.splitIslandId','task.splitIslandId','task.splitSleepTime'),
    'BS11':('sleepThreshold','sleepTime','enableSleep','isMarked','bodyMoveIndex','hasBodyState'),
    'SS11':('alive','setIndex','bodyCount','stateCount','contactCount','islandCount'),
    'TR11':('kind','objectId','sourceSet','targetSet','bodyCountBefore','contactCountBefore','didWork'),
    'SM11':('transform.p.x','transform.p.y','transform.q.c','transform.q.s','center.x','center.y','localCenter.x','localCenter.y',
            'rotation0.c','rotation0.s','center0.x','center0.y','force.x','force.y','torque','invMass','invInertia','minExtent','maxExtent',
            'linearDamping','angularDamping','gravityScale','bodyId','isFast','isBullet','isSpeedCapped','allowFastRotation','enlargeAABB')}


def parse_record(line,component=False):
    require(line.isascii() and line.endswith('\n') and '\r' not in line and len(line)<=131072,'canonical ASCII/LF/line length')
    words=line[:-1].split(' ');tag=words[0]
    require(tag not in ('PORT10','PORT9B','COMPONENT10','SN11','SE11','KS11','KE11','UP'),'tag outside11: '+tag)
    if tag not in SCHEMA:return p10.p9.parse_record(line)
                                                                             
    if tag in ('F','G'):return p10.p9.parse_record(line)
    d,k=SCHEMA[tag];values=[]
    for j,word in enumerate(words[1:]):
        require((g.g8.DEC if j<d else g.g8.HEX).fullmatch(word) is not None,tag+' canonical word')
        value=int(word,10 if j<d else 16);require(value<=g.U32,tag+' u32');values.append(value)
    if tag=='AB11':
        require(len(values)>=d+2,'AB11 prefix');k=2+2*values[d]
    require(len(values)==d+k,tag+' arity')
    return tag,tuple(values)


def format_record(tag,values):
    if tag not in SCHEMA or tag in ('F','G'):return p10.p9.format_record(tag,values)
    d,_=SCHEMA[tag]
    return tag+' '+' '.join(str(v) if j<d else f'{v:08x}' for j,v in enumerate(values))+'\n'


def projection(source):
    for line in source:
        tag,_=parse_record(line)
        if tag not in PRIVATE:yield line


def field_name(tag,values,index):
    if tag in FIELDS and index>=SCHEMA[tag][0]:return FIELDS[tag][index-SCHEMA[tag][0]]
    return p10.field_name(tag,values,index) if tag not in SCHEMA or tag in p10.SCHEMA else 'word['+str(index)+']'


def first_difference(left,right,project=False):
    for lineno,(a,b) in enumerate(zip_longest(projection(left) if project else left,right),1):
        if a==b:continue
        if a is None or b is None:return {'line':lineno,'error':'missing/excess row','C':a and a[:8192],'Duckling':b and b[:8192]}
        ta,va=parse_record(a);tb,vb=parse_record(b)
        if ta!=tb:return {'line':lineno,'tag':ta,'other_tag':tb,'C':a[:8192],'Duckling':b[:8192]}
        for j,(x,y) in enumerate(zip(va,vb)):
            if x==y:continue
            context={'line':lineno,'id':va[0],'seq':va[1] if len(va)>1 else 0,'tag':ta,'field':field_name(ta,va,j),'C':f'{x:08x}','Duckling':f'{y:08x}','left':a[:8192],'right':b[:8192]}
            if ta in NEW_PRIVATE:
                context['world']=va[2]
                if ta in ('WS11','AB11'):context['phase']=va[3]
                if ta in ('SS11','SD11','SM11'):context['set']=va[3]
                if ta in ('SD11','SM11'):context['local']=va[4]
                if ta=='BS11':context['body']=va[3]
            return context
        return {'line':lineno,'error':'arity','C':a[:8192],'Duckling':b[:8192]}
    return None


def check_snapshot(case,seq,operation,observations,private,completed,positive,component=False):
    rows=defaultdict(list);rank=-1;tasks=[]
    for tag,value in observations:
        require(value[:2]==(case,seq),tag+' case/seq')
        if component and tag=='TASK':tasks.append(value);rows[tag].append(value);continue
        require(tag in RANK and RANK[tag]>=rank,tag+' group order');rank=RANK[tag];rows[tag].append(value)
    require(rows['E']==[(case,seq,*operation)],'E exact input/64 words')
    require(len(rows['R'])==(2 if operation[0]==16 else 1),'R count')
    for j,value in enumerate(rows['R']):require(value[2]==j and value[3] in range(6) and value[4] in range(4),'R status/kind/index')
    status=rows['R'][0][3]
    if operation[0] in (31,32) and g.number(operation[2])>0:
        require(status==0,'positive Step refused; a partial scene is not a completed scene')
    if operation[0] in (31,32) and not status:
        completed+=1;positive+=g.number(operation[2])>0
    counts=Counter(tag for tag,value in observations)
    for tag in ('Z8','Z9','Z10','Z11'):require(len(rows[tag])==1,tag+' exactly one')
    require(rows['Z8'][0][8:26]==tuple(counts[t] for t in p10.p9.p8.PUBLIC_COUNTS),'Z8 public counters')
    require(rows['Z9'][0][5:12]==tuple(counts[t] for t in p10.p9.PUBCOUNTS),'Z9 public counters')
    profile=7 if component else 5
    require(rows['Z9'][0][12:16]==(seq,seq,profile,int(component and operation[0] in (51,52,64))),'Z9 profile/fixture')
    require(rows['Z10'][0][2:]==(*[counts[t] for t in p10.HIT_COUNTS],completed),'Z10 counters/completed')
    require(rows['Z11'][0][2:]==(counts['SW11'],counts['GS11'],positive),'Z11 counters/positive Step')
    if private:
        for tag in ('I8','I9','I10','I11'):require(len(rows[tag])==1,tag+' exactly one')
        require(rows['I8'][0][2:]==tuple(counts[t] for t in I8_TAGS),'I8 complete counters')
        require(rows['I9'][0][2:20]==tuple(counts[t] for t in p10.p9.PRIVCOUNTS),'I9 complete counters')
        require(rows['I9'][0][20:]==(sum(v[3]==0 for v in tasks),seq),'I9 TASK blocks/completed')
        require(rows['I10'][0][2:]==tuple(counts[t] for t in p10.NEW_COUNTS),'I10 complete counters')
        require(rows['I11'][0][2:]==tuple(counts[t] for t in NEW_PRIVATE),'I11 complete counters')
    else:require(not any(rows[t] for t in PRIVATE),'OBS0 private record')
    for tag in ('SW11','GS11',*NEW_PRIVATE):
        d,_=SCHEMA[tag];prefix=[v[2:d] for v in rows[tag]]
        require(prefix==sorted(prefix) and len(prefix)==len(set(prefix)),tag+' exact prefix order/uniqueness')
    return completed,positive


def validate_output(source,cases,private=True,*,header_n=None,component=False,model=None):
    stream=io.StringIO(source) if isinstance(source,str) else source;counts=Counter()
    def take(expected):
        line=stream.readline(131073);require(bool(line),'truncated '+expected);tag,v=parse_record(line,component)
        require(tag==expected,'expected '+expected+', got '+tag);counts[tag]+=1;return v
    n=len(cases) if header_n is None else header_n
    take_header='COMPONENT11' if component else 'PORT11'
    require(take(take_header)==(n,),'header N')
    for c in cases:
        require(take('CASE')==(c.id,len(c.ops)),'CASE input echo');completed=positive=0
        for seq,operation in enumerate(c.ops,1):
            observations=[]
            while True:
                line=stream.readline(131073);require(bool(line),'truncated snapshot')
                tag,value=parse_record(line,component);counts[tag]+=1;observations.append((tag,value))
                if tag=='Z11':break
            try:
                completed,positive=check_snapshot(c.id,seq,operation,observations,private,completed,positive,component)
                if model is not None:model.check(c.id,seq,operation,observations,private)
            except (ValueError,KeyError,IndexError,TypeError) as exc:raise ValueError(f'case {c.id}, seq {seq}: {exc}') from exc
        require(take('ENDCASE')==(c.id,),'ENDCASE')
    require(take('END')==(n,),'END N');require(not stream.read(1),'trailing output');return counts


def compare_files(c,duckling,c0,cases,codes=(0,0,0),*,header_n=None,component=False,models=None):
    result={'profile':'COMPONENT11' if component else 'PUBLIC11','N':len(cases),'errors':[],'streams':{},'first_difference':None,'models_checked':False}
    entries=[('C OBS1',c,codes[0],True),('Duckling',duckling,codes[1],True),('C OBS0',c0,codes[2],False)]
    for label,path,code,private in entries:
        if code:result['errors'].append(label+' exit '+str(code))
        if not models or label not in models:result['errors'].append(label+' independent model missing')
        try:
            with Path(path).open(encoding='ascii',newline='') as stream:
                counts=validate_output(stream,cases,private,header_n=header_n,component=component,model=(models or {}).get(label))
            result['streams'][label]={'records':dict(counts),'bytes':Path(path).stat().st_size}
        except (ValueError,OSError) as exc:result['errors'].append(label+': '+str(exc))
    for left,right,project in ((c,duckling,False),(c,c0,True)):
        try:
            with Path(left).open(encoding='ascii',newline='') as a,Path(right).open(encoding='ascii',newline='') as b:
                difference=first_difference(a,b,project)
            if difference:result['errors'].append(difference);result['first_difference']=result['first_difference'] or difference
        except (ValueError,OSError) as exc:result['errors'].append(str(exc))
                                                                               
    if not result['errors']:
        for label,path,_,_ in entries:
            digest=hashlib.sha256()
            with Path(path).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
            result['streams'][label]['sha256']=digest.hexdigest()
    result['models_checked']=bool(models and all(label in models for label,_,_,_ in entries) and not result['errors'])
    return result
