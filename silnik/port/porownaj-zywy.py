pass                                                                             
from collections import Counter,defaultdict
import hashlib
import importlib.util
from itertools import zip_longest
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
p11=load('zywy_compare11','porownaj-sen.py');g=load('zywy_compare_inputs','przypadki-zywy.py')
require=p11.require
NEW_PUBLIC=('AP12','WS12','NM12','UD12','EF12','HC12','HR12','HT12','CL12','CV12','VR12')
PRIVATE=p11.PRIVATE|frozenset(('NP12','IP12'))
SCHEMA={**p11.SCHEMA,'PORT12':(1,0),'COMPONENT12':(1,0),
        'AP12':(2,4),'WS12':(3,11),'NM12':(3,33),'NP12':(4,32),'UD12':(4,3),'EF12':(3,3),
        'HC12':(3,13),'HR12':(5,None),'HT12':(5,None),'CL12':(5,2),'CV12':(6,46),'VR12':(4,3),
        'I12':(2,11),'IP12':(2,1),'Z12':(2,2),'FE12':(2,64),'FV12':(2,1)}
SCHEMA.pop('PORT11');SCHEMA.pop('COMPONENT11')
ORDER=list(p11.ORDER)
index=ORDER.index(('X',));ORDER[index:index]=[(x,) for x in NEW_PUBLIC[:8]]+[('CL12','CV12'),('VR12',)]
ORDER.insert(ORDER.index(('I8',)),('NP12',));ORDER += [('I12',),('IP12',),('Z12',)]
RANK={tag:i for i,group in enumerate(ORDER) for tag in group}
FIELDS={'WS12':('gravity.x','gravity.y','maxSpeed','contactHertz','dampingRatio','pushSpeed','restitutionThreshold','hitThreshold','warmEnabled','sleepEnabled','awakeBodyCount'),
        'AP12':('status','reason','kind','register'),'UD12':('present','object.low','object.high'),
        'EF12':('contact','hit','preSolve'),'VR12':('status','x','y')}

def parse_record(line):
    require(line.isascii() and line.endswith('\n') and '\r' not in line and len(line)<=131072,'canonical ASCII/LF/row size12')
    words=line[:-1].split(' ');tag=words[0]
    require(tag not in ('PORT11','COMPONENT11','SN11','SE11','KS11','KE11','UP'),'tag outside12: '+tag)
    if tag not in SCHEMA or tag in ('F','G'):return p11.parse_record(line)
    d,k=SCHEMA[tag];values=[]
    for j,word in enumerate(words[1:]):
        require((g.g.g8.DEC if j<d else g.g.g8.HEX).fullmatch(word) is not None,tag+' canonical word')
        value=int(word,10 if j<d else 16);require(value<=0xffffffff,tag+' u32');values.append(value)
    if tag=='AB11':require(len(values)>=d+2,'AB11 prefix');k=2+2*values[d]
    if tag=='HR12':
        require(len(values)>=d and values[3] in range(4),'HR12 kind');k=(11,17,3,3)[values[3]]
    if tag=='HT12':
        require(len(values)>=d and values[4] in range(4),'HT12 kind');k=(7,67,5,5)[values[4]]
    require(len(values)==d+k,tag+' arity');return tag,tuple(values)

def format_record(tag,values):
    if tag not in SCHEMA or tag in ('F','G'):return p11.format_record(tag,values)
    d,_=SCHEMA[tag];return tag+' '+' '.join(str(v) if j<d else f'{v:08x}' for j,v in enumerate(values))+'\n'

def projection(records):
    for tag,values in records:
        if tag in PRIVATE:continue
        if tag=='WS12':values=(*values[:6],0,0,0,*values[9:])
        yield tag,values

def check_snapshot(case,seq,operation,records,private,completed,positive,model=None,profile=8):
    rows=defaultdict(list);rank=-1
    for tag,value in records:
        require(value[:2]==(case,seq),tag+' case/seq')
        if profile==10 and tag=='TASK':rows[tag].append(value);continue
        require(tag in RANK and RANK[tag]>=rank,tag+' group order12');rank=RANK[tag];rows[tag].append(value)
    code=operation[0]
    require(rows['E']==[(case,seq,*operation)],'exact input/64 words12')
    expected_r=2 if code==16 else 1 if code<80 or code==90 else 0
    require(len(rows['R'])==expected_r,'R count12')
    for j,v in enumerate(rows['R']):require(v[2]==j and v[3] in range(8) and v[4] in range(4),'R status/kind/index12')
    callback_count=0
    hook_state={v[2]:v for v in rows['HC12']}
    for value in rows['HT12']:
        if value[4]==1 and hook_state[value[2]][5]==4:callback_count+=3
    require(len(rows['AP12'])==(1 if code>=80 else 0)+callback_count,'AP12 main/callback count')
    if code>=80:
        status,reason,kind,reg=rows['AP12'][0][2:]
        require(status in (0,1,2,3,4,5,7) and reason in range(6) and kind in range(3),'AP12 domain')
        target=2 if code in (81,88) else 0 if code in (82,86,87) else operation[2]+1 if code==83 else operation[2] if code in (85,91) else (operation[1]+1 if operation[1]<2 else 0) if code==89 else 1
        register=(operation[4] if operation[1]>=2 else operation[3]) if code==89 else operation[1] if target==0 else operation[3] if code in (83,85,88,91) else operation[2]
        require((kind,reg)==(target,register),'AP12 exact target')
    counts=Counter(tag for tag,_ in records)
    require(not counts['TASK'] or profile==10 and code==43,'TASK12 only explicit private43')
    for tag in ('Z8','Z9','Z10','Z11','I12','Z12'):require(len(rows[tag])==1,tag+' exactly one12')
    status=rows['R'][0][3] if rows['R'] else rows['AP12'][0][2]
    if code in (31,32) and not status:completed+=1;positive+=g.number(operation[2])>0
    if code in (31,32) and g.number(operation[2])>0:require(status==0,'positive Step refused12')
    require(rows['Z8'][0][8:26]==tuple(counts[t] for t in p11.p10.p9.p8.PUBLIC_COUNTS),'Z8 public counts12')
    require(rows['Z9'][0][5:12]==tuple(counts[t] for t in p11.p10.p9.PUBCOUNTS),'Z9 public counts12')
    require(rows['Z9'][0][12:16]==(seq,seq,profile,int(profile==10 and code in (51,52,64))),'12 profile/fixture')
    require(rows['Z10'][0][2:]==(*[counts[t] for t in p11.p10.HIT_COUNTS],completed),'Z10 completed12')
    require(rows['Z11'][0][2:]==(counts['SW11'],counts['GS11'],positive),'Z11 counts12')
    i12=('AP12','WS12','NM12','UD12','HC12','HR12','HT12','CL12','CV12','VR12','EF12')
    require(rows['I12'][0][2:]==tuple(counts[t] for t in i12),'I12 counts')
    require(rows['Z12'][0][2:]==(positive,seq),'Z12 positive/snapshot ordinal')
    for tag,target_tag in (('WS12','W'),('HC12','W'),('NM12','B'),('EF12','S')):
        require([v[2] for v in rows[tag]]==[v[2] for v in rows[target_tag]],tag+' live register completeness')
    require([v[2:4] for v in rows['UD12']]==[(kind,v[2]) for kind,tag in enumerate(('W','B','S')) for v in rows[tag]],'UD12 live completeness/order')
    for value in rows['NM12']:
        n=value[3];require(n<=31 and all(v<=255 for v in value[4:]),'NM12 byte domain')
        require(all(value[4+j] for j in range(n)) and not any(value[4+n:]),'NM12 length/NUL/canonical tail')
    if private:
        for tag in ('I8','I9','I10','I11','IP12'):require(len(rows[tag])==1,tag+' private exactly one12')
        require(rows['I8'][0][2:]==tuple(counts[t] for t in p11.I8_TAGS),'I8 counts12')
        require(rows['I9'][0][2:20]==tuple(counts[t] for t in p11.p10.p9.PRIVCOUNTS),'I9 counts12')
        require(rows['I9'][0][20:]==(sum(v[3]==0 for v in rows['TASK']),seq),'TASK blocks/completed12')
        require(rows['I10'][0][2:]==tuple(counts[t] for t in p11.p10.NEW_COUNTS),'I10 counts12')
        require(rows['I11'][0][2:]==tuple(counts[t] for t in p11.NEW_PRIVATE),'I11 counts12')
        require(rows['IP12'][0][2:]==(counts['NP12'],),'IP12 counts')
        require(counts['NP12']==sum(v[5] for v in rows['BP11']),'NP12 every live cold body')
    else:
        require(not any(rows[t] for t in PRIVATE),'OBS0 private record12')
        for v in rows['WS12']:require(v[6:9]==(0,0,0),'OBS0 tuning projection')
    return completed,positive

def snapshots(source,cases,private=True,model=None,component=False):
    digest=hashlib.sha256();count=Counter();size=0
    model_errors=[];model_error_count=0
    def take(expected=None):
        nonlocal size
        line=source.readline(131073);require(bool(line),'truncated '+str(expected))
        digest.update(line.encode('ascii'));size+=len(line);tag,value=parse_record(line);count[tag]+=1
        if expected:require(tag==expected,'expected '+expected+', got '+tag)
        return tag,value
    require(take('COMPONENT12' if component else 'PORT12')[1]==(len(cases),),'12 N')
    for c in cases:
        require(take('CASE')[1]==(c.id,len(c.ops)),'CASE exact input12');completed=positive=0
        if component and c.ops[0][0]>=100:
            row=c.ops[0];records=[take('FE12'),take('FV12')]
            require(records[0][1]==(c.id,*row),'FE12 exact64 words')
            require(records[1][1][:2]==(c.id,row[0]),'FV12 identity')
            yield c.id,1,records
            require(take('ENDCASE')[1]==(c.id,),'ENDCASE math12');continue
        for seq,operation in enumerate(c.ops,1):
            records=[]
            while True:
                record=take();records.append(record)
                if record[0]=='Z12':break
            try:completed,positive=check_snapshot(c.id,seq,operation,records,private,completed,positive,model,10 if component else 8)
            except (ValueError,KeyError,IndexError,TypeError) as exc:raise ValueError(f'case{c.id}/seq{seq}: {exc}') from exc
            if model is not None:
                try:model.check(c.id,seq,operation,records,private)
                except Exception as exc:
                                                                              
                                                                                   
                                                                              
                    model_error_count+=1
                    if len(model_errors)<3:model_errors.append({'case':c.id,'seq':seq,'error':type(exc).__name__+': '+str(exc)})
            yield c.id,seq,records
        require(take('ENDCASE')[1]==(c.id,),'ENDCASE12')
    require(take('END')[1]==(len(cases),),'END N12');require(not source.read(1),'trailing output12')
    yield None,None,{'sha256':digest.hexdigest(),'bytes':size,'records':dict(count),'END_EOF':True,
                    'models_checked':model is not None and not model_error_count,
                    'model_errors':model_errors,'model_error_count':model_error_count}

def first_difference(left,right):
    for ordinal,(a,b) in enumerate(zip_longest(left,right),1):
        if a==b:continue
        result={'record':ordinal,'C':a,'other':b}
        if a and b and a[0]==b[0]:
            tag,va=a;vb=b[1]
            for j,(x,y) in enumerate(zip_longest(va,vb)):
                if x==y:continue
                d=SCHEMA.get(tag,(0,0))[0]
                result.update(tag=tag,field=FIELDS.get(tag,())[j-d] if tag in FIELDS and d<=j<d+len(FIELDS[tag]) else 'word['+str(j)+']',
                              left=None if x is None else f'{x:08x}',right=None if y is None else f'{y:08x}');break
        return result
    return None
