pass                                                                     

                                                                         
                                                                          
                                     
   
from collections import Counter, defaultdict
import importlib.util
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


p11 = load('zywy_grammar11', 'porownaj-sen.py')
m10 = load('zywy_numbers10', 'model-solver.py')
require, number = m10.require, m10.number
HEX, DEC = re.compile(r'[0-9a-f]{8}'), re.compile(r'0|[1-9][0-9]*')
SCHEMA = {
    'PORT12': (1,0), 'GUARD12': (1,0), 'COMPONENT12': (1,0),
    'AP12': (2,4), 'WS12': (3,11), 'NM12': (3,33), 'NP12': (4,32),
    'UD12': (4,3), 'EF12': (3,3), 'HC12': (3,13), 'HR12': (5,None), 'HT12': (5,None),
    'CL12': (5,2), 'CV12': (6,46), 'VR12': (4,3), 'I12': (2,11), 'IP12': (2,1),
    'Z12': (2,2), 'GR12': (3,4), 'GA': (1,64), 'FE12': (2,64), 'FV12': (2,1),
}
COUNTS = ('AP12','WS12','NM12','UD12','HC12','HR12','HT12','CL12','CV12','VR12','EF12')
PRIVATE = p11.PRIVATE | frozenset(('NP12','IP12'))
RETIRED = frozenset(('PORT11','GUARD11','COMPONENT11','PORT10','GUARD10','COMPONENT10',
                     'PORT9B','SN11','SE11','KS11','KE11','UP'))
OWNERSHIP_READY = False


def parse(line):
    require(isinstance(line,str) and line.isascii() and line.endswith('\n') and '\r' not in line,
            'canonical ASCII/LF output')
    require(len(line)<=131072, 'bounded output line')
    words = line[:-1].split(' ')
    tag = words[0]
    require(tag not in RETIRED, 'retired/outside12 tag '+tag)
    if tag not in SCHEMA:
        if tag=='G' and len(words)==5:
            return m10.parse(line)
        return p11.parse_record(line)
    d, k = SCHEMA[tag]
    require(len(words)>=d+1, tag+' prefix arity')
    values = []
    for i, word in enumerate(words[1:]):
        require((DEC if i<d else HEX).fullmatch(word) is not None, tag+' canonical word')
        value = int(word,10 if i<d else 16)
        require(value<=0xffffffff, tag+' u32')
        values.append(value)
    if tag=='HR12':
        require(values[3] in range(4), 'HR12 kind')
        k = (11,17,3,3)[values[3]]
    if tag=='HT12':
        require(values[4] in range(4), 'HT12 kind')
        k = (7,67,5,5)[values[4]]
    require(len(values)==d+k, tag+' arity')
    return tag,tuple(values)


def format_record(tag, values):
    if tag not in SCHEMA:
        if tag=='G' and len(values)==4:
            return m10.format_record(tag,values)
        return p11.format_record(tag,values)
    d,_ = SCHEMA[tag]
    result=tag+' '+' '.join(str(v) if i<d else f'{v:08x}' for i,v in enumerate(values))+'\n'
    parse(result)
    return result


def projection(source):
    for line in source:
        tag, values = parse(line)
        if tag in PRIVATE:
            continue
        if tag=='WS12':
            values=(*values[:6],0,0,0,*values[9:])
            line=format_record(tag,values)
        yield line


def keyed(rows, tag):
    d,_=SCHEMA[tag]
    result={}
    for value in rows[tag]:
        key=value[2:d]
        require(key not in result, tag+' duplicate index')
        result[key]=value[d:]
    require(list(result)==sorted(result), tag+' index order')
    return result


def _fixed_arities():
    old=p11.p10.p9.p8
    result={tag:len(fields) for tag,fields in old.FIELDS.items() if tag not in ('L','Q','H')}
    for schema in (p11.p10.p9.SCHEMA,p11.SCHEMA,SCHEMA):
        for tag,(d,k) in schema.items():
            if k is None:result.pop(tag,None)
            else:result[tag]=d+k
    return {tag:arity for tag,arity in result.items() if tag not in RETIRED}


FIXED_ARITIES=_fixed_arities()


def atan2_12(y,x):
    pass                                                             
    mm=m10
    if x==0 and y==0:return 0.
    ax,ay=abs(x),abs(y);a=mm.div(min(ax,ay),max(ax,ay))
    s=mm.mul(a,a);c=mm.mul(s,a);q=mm.mul(s,s)
    r=mm.add(mm.mul(.024840285,q),.18681418)
    t=mm.add(mm.mul(-.094097948,q),-.33213072)
    r=mm.add(mm.mul(r,s),t);r=mm.add(mm.mul(r,c),a)
    if ay>ax:r=mm.add(mm.number(0x3fc90fdb),-r)
    if x<0:r=mm.add(mm.number(0x40490fdb),-r)
    if y<0:r=-r
    return r


def validate_record(tag,values):
    pass                                                            

                                                                          
                                                                           
                                                                            
                                                                          
       
    arity=FIXED_ARITIES.get(tag)
    if arity is None or tag=='G' and len(values)==4 or not all(type(v)is int for v in values):
        parse(format_record(tag,values));return
    require(len(values)==arity,tag+' arity')
    require(all(0<=v<=0xffffffff for v in values),tag+' u32')


def new_records(case,seq,operation,observations,private=True):
    pass                                                                   

                                                                           
                                                                          
                                                                          
       
    rows=defaultdict(list)
    for tag, values in observations:
        validate_record(tag,values)
        require(values[:2]==(case,seq), tag+' case/seq')
        rows[tag].append(values)
    require(rows['E']==[(case,seq,*operation)], 'E exact input echo')
    for tag in ('I12','Z12'):
        require(len(rows[tag])==1, tag+' exactly one')
    require(rows['I12'][0][2:]==tuple(len(rows[t]) for t in COUNTS), 'I12 full current counts')
    require(rows['Z12'][0][3]==seq, 'Z12 snapshot ordinal')
    if private:
        require(len(rows['IP12'])==1 and rows['IP12'][0][2]==len(rows['NP12']), 'IP12 exact NP count')
    else:
        require(not rows['NP12'] and not rows['IP12'], 'private12 rows in OBS0')
    live={tag:{v[2] for v in rows[tag]} for tag in ('W','B','S')}
    require(len(rows['WS12'])==len(live['W']) and set(keyed(rows,'WS12'))=={(v,) for v in live['W']},
            'WS12 independent live W completeness')
    require(len(rows['NM12'])==len(live['B']) and set(keyed(rows,'NM12'))=={(v,) for v in live['B']},
            'NM12 independent live B completeness')
    require(set(keyed(rows,'EF12'))=={(v,) for v in live['S']}, 'EF12 independent live S completeness')
    require(set(keyed(rows,'HC12'))=={(v,) for v in live['W']}, 'HC12 independent live W completeness')
    require(set(keyed(rows,'UD12'))=={(kind,v) for kind,tag in enumerate(('W','B','S')) for v in live[tag]},
            'UD12 independent complete targets')
    for h in keyed(rows,'NM12').values():
        length,*data=h
        require(length<=31 and all(v<=255 for v in data), 'NM12 bounded byte value')
        require(0 not in data[:length] and data[length:]==[0]*(32-length), 'NM12 canonical first NUL and tail')
    for h in keyed(rows,'NP12').values():
        require(all(v<=255 for v in h) and h[31]==0, 'NP12 readable32 and byte31 NUL')
    for h in keyed(rows,'UD12').values():
        require(h[0] in (0,1) and (h[0] or h[1:]==(0,0)), 'UD12 presence/token')
    for h in keyed(rows,'EF12').values():
        require(all(v in (0,1) for v in h), 'EF12 bool flags')
    for h in keyed(rows,'WS12').values():
        require(all(math.isfinite(number(v)) for v in h[:8]), 'WS12 defined finite values')
        require(number(h[2])>0 and all(number(v)>=0 for v in h[3:8]), 'WS12 setting domains')
        require(h[8] in (0,1) and h[9] in (0,1), 'WS12 bool settings')
        if not private:
            require(h[3:6]==(0,0,0), 'OBS0 only contact-tuning projection')
    code,*a=operation
    aps=rows['AP12']
    require(all(v[2] in range(8) and v[3] in range(6) and v[4] in range(3) for v in aps), 'AP12 domains')
    for v in aps:
        require((v[2]==7)==(v[3]==1), 'AP12 LOCKED7/reason1 distinction')
        if v[3]==2:
            require(v[2]==5,'AP12 unsupported profile is PARAM')
        if v[3] in (3,4):
            require(v[2]==5, 'AP12 name/rules are PARAM')
        if v[3]==5:
            require(v[2]==4, 'AP12 derived S12 is GEOMETRY')
    if 80<=code<=92:
        require(len(aps)==1, 'one AP for a new operation')
        require(len(rows['R'])==int(code==90), 'R only create90 among new ops')
    else:
                                                                          
                                                                               
        require(len(aps)%3==0, 'legacy AP triples only fixture4')
        if aps:
            require(code in (31,32) and all(v[2:4]==(7,1) for v in aps), 'fixture4 statuses/reasons')
    _contact_lists(rows)
    if code==92:
        require(len(rows['VR12'])==1, 'one vector result')
        v=rows['VR12'][0]
        require(v[2:4]==(a[1],a[3]) and v[4]==aps[0][2], 'VR12 target/kind/status')
        require(all(math.isfinite(number(x)) for x in v[5:]), 'VR12 finite output')
        if v[4]:
            require(v[5:]==(0,0), 'VR12 refusal canonical +0')
    else:
        require(not rows['VR12'], 'unsolicited VR12')
    return rows


def _contact_lists(rows):
    lists={}
                                                                           
                                                                      
                                                                            
                                                                            
    for value in rows['CL12']:
        key=value[2:5]
        require(key not in lists, 'CL12 duplicate kind/reg/phase')
        status,count=value[5:]
        require(key[0] in (1,2) and key[2] in (0,1,2) and status in range(8), 'CL12 domains')
        require(not status or count==0, 'CL12 refusal empty')
        lists[key]=(status,count)
    elements=defaultdict(list)
    for value in rows['CV12']:
        key=value[2:5]
        require(key in lists and value[5]==len(elements[key]), 'CV12 source/index order')
        h=value[6:]
        require(h[15]==1, 'ContactList contains touching values')
        require(h[1]|h[2] and h[6]|h[7] and h[11]|h[12], 'CV12 nonzero historical births')
        require(h[19]<=2, 'CV12 manifold pointCount')
        elements[key].append(h)
    for key,(status,count) in lists.items():
        require(len(elements[key])==count,'CV12 exact count')
        if key[2]==2:
            require(lists.get((*key[:2],0))==(status,count) and elements[key]==elements[(*key[:2],0)],
                    'copy phase2 equals source phase0')
        if key[2]==1:
            original=elements.get((*key[:2],0))
            require(original is not None,'copy mutate phase0 required')
            wanted=list(original)
            if wanted:
                first=list(wanted[0]);first[16]=0x42f60000;wanted[0]=tuple(first)
                if len(wanted)>=2:
                    wanted[0],wanted[1]=wanted[1],wanted[0]
            require(elements[key]==wanted, 'copy phase1 exact normal.x/swap mutation')


class SnapshotGrammar:
    pass                                                                    
    def check(self,case,seq,operation,observations,private=True):
        observations=tuple(observations)
                                                                       
                                                                              
                                    
        groups=[('E',),('R',),('V',),('W',),('B',),('S','G'),('L','A'),('Q',),('QGN','QG'),('SB',),
                ('K','M','MCN','MC'),('CD',),('NC9',),('RC9',),('GV',),('GL',),('GE',),('GC',),
                ('HN10','HR10'),('HC10','HG10'),('SW11',),('GS11',),
                *[(t,) for t in ('AP12','WS12','NM12','UD12','EF12','HC12','HR12','HT12')],
                ('CL12','CV12'),('VR12',),
                *[(t,) for t in ('X P T F U H Y DN RT JW RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 '
                                  'W10 CX10 SB10 PK10 SC10 BV10 WS11 BS11 SS11 SD11 SM11 AB11 TR11 SP11 SF11 BP11 BF11 '
                                  'NP12 I8 I9 I10 I11 Z8 Z9 Z10 Z11 I12 IP12 Z12').split()]]
        rank={tag:i for i,group in enumerate(groups) for tag in group}
        rank['TASK']=-1
        previous=-1
        cl=None
        remaining=0
        prior_cl=None
        for tag,values in observations:
            require(tag in rank and rank[tag]>=previous, tag+' group order12')
            previous=rank[tag]
            if tag=='CL12':
                require(remaining==0,'prior CL12 missing elements')
                cl=values[2:5];remaining=values[6]
                require(prior_cl is None or cl>prior_cl,'CL12 kind/reg/phase order')
                prior_cl=cl
            elif tag=='CV12':
                require(cl==values[2:5] and remaining>0,'CV12 immediately follows its own CL12')
                remaining-=1
            else:
                require(remaining==0,'interrupted CL12/CV12 block')
        require(remaining==0,'truncated CV12 block')
        return new_records(case,seq,operation,observations,private)


NULL=0xffffffff


def wide(words):return words[0]|words[1]<<32


def index_rows(rows,tag,d):
    found={}
    for value in rows[tag]:
        key=value[2:d]
        require(key not in found,tag+' duplicate prefix')
        found[key]=value[d:]
    require(list(found)==sorted(found),tag+' sorted prefix')
    return found


def pool(header,free,alive,label):
    require(header is not None and len(header)==3,label+' required pool')
    count,free_count,live_count=header
    require(free_count<=count and live_count==count-free_count,label+' logical counts')
    require(len(free)==free_count and len(set(free))==free_count and all(x<count for x in free),label+' free stack')
    require(set(alive)==set(range(count))-set(free),label+' complete live/free partition')


class OwnershipModel:
    pass                                                                       

                                                                             
                                                                            
                                                                          
       
    def __init__(self,fixture=None,*,diagnostic_only=False):
        self.fixture=fixture
        self.diagnostic_only=diagnostic_only
        self.case=0
        self.last_ticket=0
        self.failure=None
        self.last_verified=None
        self.continuity_gaps=[]
        self.math_cases=0
        self._begin_case()

    def _begin_case(self):
        self.next_seq=1
        self.regs={tag:{} for tag in ('W','B','S')}
        self.contacts={}
        self.known_bodies=set()
        self.known_shapes=set()
        self.known_contacts=set()
        self.raw_shapes={}
        self.saved_lists={}
        self.saved_moves={}
        self.body_marks={}
        self.contact_marks={}
        self.raw_event_history={}
        self.raw_hit_history={}
        self.saved_events={}
        self.saved_event_owners={}
        self.saved_hits={}
        self.rules={}
        self.world_values={}
        self.body_values={}
        self.shape_values={}
        self.object_values={0:{},1:{},2:{}}
        self.name_values={}
        self.hook_values={}
        self.hook_modes={}
        self.witnesses=Counter()
        self.previous=None
        self.completed=0
        self.positive=0

    def check(self,case,seq,operation,observations,private=True):
        require(OWNERSHIP_READY or self.diagnostic_only,
                'full OwnershipModel12 incomplete: '+ '; '.join(MODEL_GAPS))
        observations=tuple(observations)
        if self.failure is not None:
            gap={'case':case,'seq':seq,'after':dict(self.failure),'last_verified':self.last_verified}
            self.continuity_gaps.append(gap)
            raise ValueError('model history unavailable after '+str(self.failure)+'; no re-anchoring at CASE')
        try:
            if operation[0] in (100,101):
                self._math_case(case,seq,operation,observations)
                return
            rows=SnapshotGrammar().check(case,seq,operation,observations,private)
            if case!=self.case:
                require(case==self.case+1 and seq==1,'continuous CASE history from1')
                self._begin_case();self.case=case
            require(seq==self.next_seq,'missing/duplicate/reordered snapshot')
            if self.fixture is not None and self.fixture.kind==4 and seq==self.fixture.seed+1:
                self.last_ticket=wide(self.fixture.words[1:3])
            self._snapshot(rows,operation,private)
            self.next_seq+=1
            self.last_verified={'case':case,'seq':seq,'last_ticket':self.last_ticket}
            self.previous=rows
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            self.failure={'case':case,'seq':seq,'error':str(exc)}
            raise

    def _math_case(self,case,seq,operation,observations):
        require(case==self.case+1 and seq==1 and self.case==self.math_cases,
                'continuous COMPONENT math prefix from1, before world histories')
        code,*a=operation;used=2 if code==100 else 4
        require(len(a)==64 and all(v==0 for v in a[used:]),'math input64/unused')
        values=list(map(number,a[:used]));require(all(map(math.isfinite,values)),'math finite inputs')
        if code==100:y,x=values
        else:
            bc,bs,ac,ss=values
            for c,s in ((bc,bs),(ac,ss)):
                norm=m10.add(m10.mul(s,s),m10.mul(c,c))
                require(m10.add(1,-m10.f32(.0006))<norm<m10.add(1,m10.f32(.0006)),'math normalized rotations')
            y=m10.add(m10.mul(bs,ac),-m10.mul(bc,ss))
            x=m10.add(m10.mul(bc,ac),m10.mul(bs,ss))
        expected=(('FE12',(case,*operation)),('FV12',(case,code,m10.bits(atan2_12(y,x)))))
        for tag,value in observations:validate_record(tag,value)
        require(tuple(observations)==expected,'math exact echo and independent scalar binary32 result')
        require(self.last_ticket==0,'math prefix has no allocation history')
        self._begin_case();self.case=case;self.math_cases+=1;self.next_seq=2
        self.last_verified={'case':case,'seq':seq,'last_ticket':self.last_ticket}

    def _issue(self,birth):
        require(0<birth<1<<64 and birth==self.last_ticket+1,'monotone allocation ticket; no holes/reset')
        self.last_ticket=birth

    def _status(self,rows,code):
        if 80<=code<=92:return rows['AP12'][0][2]
        require(bool(rows['R']),'legacy operation R required')
        require(all(v[3] in range(8) for v in rows['R']),'legacy result status domain0..7')
        return rows['R'][0][3]

    def _world_of(self,number):
        return next((reg for reg,item in self.regs['W'].items() if item['number'][1:3]==number[3:5]),None)

    def _create(self,tag,reg,result,parent=None):
        require(result[4]=={'W':1,'B':2,'S':3}[tag],tag+' create result kind')
        number=(result[5]-1,*result[12:14],*result[10:12])
        self._issue(wide(number[1:3]))
        require(reg not in self.regs[tag] or not self.regs[tag][reg]['live'],'no live register overwrite')
        self.regs[tag][reg]={'number':number,'raw':result[5:8],'live':True,'parent':parent}
        if tag=='W':
            require(number[3:]==(0,0),'world allocation owner0')
            self.rules[reg]=[[],[],[],[]]
        else:
            owner=self._world_of(number)
            require(owner is not None and self.regs['W'][owner]['live'],tag+' live allocation owner')
            if tag=='B':self.known_bodies.add(number)
            else:
                self.known_shapes.add(number)
                self.raw_shapes[(wide(number[3:]),tuple(result[5:8]))]=number

    def _history(self,rows,operation,status,private):
        code,*a=operation
        if status==0:
            creates={0:('W',a[0]),54:('W',a[0]),56:('W',a[0]),2:('B',a[0]),30:('B',a[0]),
                     57:('B',a[1]),90:('B',a[1]),10:('S',a[0]),17:('S',a[0]),40:('S',a[0])}
            if code in creates:
                tag,target=creates[code]
                parent=self.regs['B'][a[2]]['number'] if tag=='S' else None
                self._create(tag,target,rows['R'][0],parent)
            elif code==16:
                self._create('B',a[0],rows['R'][0])
                self._create('S',a[1],rows['R'][1],self.regs['B'][a[0]]['number'])
            elif code==1:
                world=self.regs['W'][a[0]];world['live']=False
                for tag in ('B','S'):
                    for item in self.regs[tag].values():
                        if item['number'][3:]==world['number'][1:3]:item['live']=False
            elif code==3:
                item=self.regs['B'][a[1]];item['live']=False
                for shape in self.regs['S'].values():
                    if shape['parent']==item['number']:shape['live']=False
            elif code in (11,18):self.regs['S'][a[1]]['live']=False
        for tag in ('W','B','S'):
            actual={v[2]:v for v in rows[tag]}
            expected={reg for reg,item in self.regs[tag].items() if item['live']}
            require(len(actual)==len(rows[tag]) and set(actual)==expected,tag+' independent live register completeness')
            for reg,value in actual.items():
                item=self.regs[tag][reg]
                require(value[3:6]==item['raw'],tag+' stable raw identity')
                if tag=='W':require(value[8:10]==item['number'][1:3],'world birth identity')
                else:require(value[8:12]==(*item['number'][3:],*item['number'][1:3]),tag+' owner/birth identity')
                if tag=='S':
                    parent=next((b for b in self.regs['B'].values() if b['live'] and b['number']==item['parent']),None)
                    require(parent is not None and value[12:15]==parent['raw'],'shape parent identity, not register reuse')
        if private:
            ct=index_rows(rows,'CT',4)
            for reg,world in self.regs['W'].items():
                if not world['live']:continue
                old=self.contacts.get(world['number'][1:3],{})
                live={slot:h for (w,slot),h in ct.items() if w==reg and h[0]}
                issued={}
                for request in rows['RQ']:
                    if request[2]!=reg or not request[9]:continue
                    cid=request[10]
                    require(cid not in old and cid not in issued,'one allocation per new contact request')
                    birth=self.last_ticket+1
                    self._issue(birth);issued[cid]=birth
                    if cid in live:require(wide(live[cid][18:20])==birth,'contact birth follows request allocation order')
                    self.known_contacts.add((cid,birth&0xffffffff,birth>>32,*world['number'][1:3]))
                for cid,h in live.items():
                    birth=wide(h[18:20])
                    require(old.get(cid)==birth or cid in issued,'new contact must have a consumed request')
                    self.known_contacts.add((cid,h[18],h[19],*world['number'][1:3]))
                self.contacts[world['number'][1:3]]={cid:wide(h[18:20]) for cid,h in live.items()}
        observed=wide(rows['Z8'][0][-2:])
        if private:require(observed==self.last_ticket,'lastIssued equals real allocation history')
        elif code in (31,32) and status==0 and number(a[1])>0:
            require(observed>=self.last_ticket,'public lastIssued never decreases')
        else:require(observed==self.last_ticket,'read/no-op/refusal cannot issue tickets')
        self.last_ticket=observed

    def _snapshot(self,rows,operation,private):
        code,*a=operation
        status=self._status(rows,code)
        require(len(rows['Z8'])==1 and len(rows['Z9'])==1 and len(rows['Z10'])==1 and len(rows['Z11'])==1,'all legacy counters required')
        self._new_status(rows,operation,status)
        self._history(rows,operation,status,private)
        self._input_state(rows,operation,status,private)
        self._vector_result(rows,operation,status)
        self._rules_and_callbacks(rows,operation,status)
        callback_events=self._callback_schedule(rows,operation,status,private)
        if private:self._contact_cache_history(rows,operation,status,callback_events)
        if code in (31,32) and not status:
            self.completed+=1
            self.positive+=int(number(a[1])>0)
        require(rows['Z10'][0][-1]==self.completed,'completed Step count includes pauses, excludes refusals')
        require(rows['Z11'][0][-1]==self.positive and rows['Z12'][0][2]==self.positive,'positive Step independent count')
        counts=Counter({tag:len(values) for tag,values in rows.items()})
        require(rows['Z8'][0][8:26]==tuple(counts[t] for t in p11.p10.p9.p8.PUBLIC_COUNTS),'Z8 public counts')
        require(rows['Z9'][0][5:12]==tuple(counts[t] for t in p11.p10.p9.PUBCOUNTS),'Z9 public counts')
        require(rows['Z9'][0][12:14]==(rows['E'][0][1],rows['E'][0][1]),'Z9 operation/snapshot ordinal')
        require(rows['Z9'][0][14] in (8,9,10),'profile12; never old profiles')
        require(rows['Z10'][0][2:6]==tuple(counts[t] for t in ('HN10','HR10','HC10','HG10')),'Z10 hit counts')
        require(rows['Z11'][0][2:4]==(counts['SW11'],counts['GS11']),'Z11 sleep counts')
        if private:
            for counter,tags in (('I8',p11.I8_TAGS),('I9',p11.p10.p9.PRIVCOUNTS),
                                 ('I10',p11.p10.NEW_COUNTS),('I11',p11.NEW_PRIVATE)):
                require(len(rows[counter])==1 and rows[counter][0][2:2+len(tags)]==tuple(counts[t] for t in tags),counter+' complete full rows')
            self._mark_history(rows,operation,status)
            self._ownership(rows)
            self._finalize_history(rows,operation,status)
            self._body_pool_history(rows)
            self._contact_pool_history(rows,operation,status)
            self._body_layout_history(rows,operation,status)
        else:require(not any(rows[t] for t in PRIVATE),'OBS0 has no private tags')
        self._copies(rows,operation,status,private)
        self._hit_history(rows,operation,status,private)
        self._events(rows,operation,status,private)
        self._finite_and_masks(rows,operation,status)
        self._atomic(rows,operation,status)

    def _vector_result(self,rows,operation,status):
        code,*a=operation
        if code!=92 or status:return
        body=next(v for v in rows['B'] if v[2]==a[1])
        p=tuple(map(number,body[13:15]));q=tuple(map(number,body[15:17]))
        v=tuple(map(number,a[4:6]));kind=a[3]
        add,mul=m10.add,m10.mul
        def sub(x,y):return (add(x[0],-y[0]),add(x[1],-y[1]))
        def rotate(x):return (add(mul(q[0],x[0]),-mul(q[1],x[1])),add(mul(q[1],x[0]),mul(q[0],x[1])))
        def inverse(x):return (add(mul(q[0],x[0]),mul(q[1],x[1])),add(mul(-q[1],x[0]),mul(q[0],x[1])))
        if kind==0:wanted=inverse(sub(v,p))
        elif kind==1:
            r=rotate(v);wanted=(add(r[0],p[0]),add(r[1],p[1]))
        elif kind==2:wanted=inverse(v)
        elif kind==3:wanted=rotate(v)
        elif not body[27]:wanted=(0.,0.)
        else:
            r=rotate(sub(v,tuple(map(number,body[24:26])))) if kind==4 else sub(v,tuple(map(number,body[17:19])))
            angular=number(body[21])
            wanted=(add(number(body[19]),mul(-angular,r[1])),add(number(body[20]),mul(angular,r[0])))
        require(rows['VR12'][0][5:]==tuple(map(m10.bits,wanted)),
                'VR12 exact local/world getter f32 evaluation from current transform/state, without a solver')

    def _new_status(self,rows,operation,status):
        code,*a=operation
        if not 80<=code<=92:return
        def world(reg):return 0 if reg in self.regs['W'] and self.regs['W'][reg]['live'] else 1
        def item(w,tag,reg):
            life=world(w)
            if life:return life
            target=self.regs[tag].get(reg)
            require(target is not None,'initialized source register')
            if target['number'][3:]!=self.regs['W'][w]['number'][1:3]:return 2
            return 0 if target['live'] else 1
        if code==89 and a[0]>=2:
            require(status==0,'copy-only operation has no world lifetime lookup')
            return
        w=a[1] if code==89 else a[0]
        expected=world(w)
        targets=[]
        if code in (80,84,92):targets=[('B',a[1])]
        if code==81:targets=[('S',a[1])]
        if code==83:targets=[('B' if a[1]==0 else 'S',a[2])]
        if code in (85,91) and a[1]!=0:targets=[('B' if a[1]==1 else 'S',a[2])]
        if code==87 and a[2]==1 and a[1] in (0,1):targets=[('S',a[3]),('S',a[4])]
        if code==88:targets=[('S',a[2])]
        if code==89:targets=[('B' if a[0]==0 else 'S',a[2])]
        for tag,reg in targets:
            if expected:break
            expected=item(w,tag,reg)
        reason=rows['AP12'][0][3]
        if expected:
            require(status==expected and reason==0,'world then owner then lifetime, before PARAM/geometry')
            return
        require(status not in (1,2,6),'live current target cannot be STALE/FOREIGN/unsupported-pair6')
        mode={80:2,81:2,82:1,83:3,84:2,85:3,86:1,88:1,90:2,91:3,92:2}.get(code)
        if mode is not None and a[mode]==0:return
        finite=lambda index:math.isfinite(number(a[index]))
        nonnegative=lambda index:finite(index) and number(a[index])>=0
        invalid=False
        refusal_reason=0
        if code==80:
            kind=a[3]
            if kind==2:invalid=not (nonnegative(4) and finite(5) and finite(6) and nonnegative(7))
            if kind in (4,5):invalid=not nonnegative(4)
            if kind==6:invalid=not finite(4)
            if kind==8:
                squared=m10.add(m10.mul(number(a[7]),number(a[7])),m10.mul(number(a[6]),number(a[6])))
                invalid=not (all(finite(i) for i in range(4,9)) and number(a[8])>0 and
                             m10.add(1,-m10.f32(.0006))<squared<m10.add(1,m10.f32(.0006)))
                if not invalid:invalid=self._target_linear_overflow(a)
        elif code==81:
            if a[3] in (0,1):invalid=not nonnegative(4)
            if a[3]==3:invalid=not (all(nonnegative(i) for i in (4,5,6)) and finite(7))
        elif code==82:
            kind=a[2]
            if kind in (1,2):invalid=not nonnegative(3)
            if kind==3:invalid=not all(nonnegative(i) for i in (3,4,5))
            if kind==4:invalid=not (finite(3) and number(a[3])>0)
            if kind==5:invalid=not (finite(3) and finite(4))
        elif code==83 and a[1]==0 and a[4]==2:
            invalid=True;refusal_reason=2
        elif code in (84,90):
            if code==90:
                norm=m10.add(m10.mul(number(a[7]),number(a[7])),m10.mul(number(a[6]),number(a[6])))
                invalid=not (all(finite(i) for i in range(4,14)) and all(nonnegative(i) for i in (11,12,18)) and
                             m10.add(1,-m10.f32(.0006))<norm<m10.add(1,m10.f32(.0006)))
            if not invalid:
                length=a[4] if code==84 else a[20]
                data=bytes(a[5:37] if code==84 else a[21:53])
                bad=length>31 or 0 in data[:length]
                try:data[:length].decode('utf-8','strict')
                except UnicodeDecodeError:bad=True
                if bad:invalid=True;refusal_reason=3
        elif code==92:invalid=not (finite(4) and finite(5))
        elif code==87 and a[2]==1:
            refusal_reason=4
            if a[1] in (2,3):invalid=not nonnegative(5)
            if a[1]==1:
                invalid=not all(finite(i) for i in (6,7,8))
                if a[9]:
                    norm=m10.add(m10.mul(number(a[10]),number(a[10])),m10.mul(number(a[11]),number(a[11])))
                    invalid=invalid or not (finite(10) and finite(11) and
                        abs(m10.add(1,-norm))<m10.mul(100,m10.number(0x34000000)))
        if invalid:
            require(status==5 and reason==refusal_reason,'PARAM/reason after valid life, before S12/LIMIT')
        elif self._existing_circle_geometry(operation):
            require(status==4 and reason==0,'existing circle geometry before mass mutation')

    def _target_linear_overflow(self,a):
        pass                                                               

                                                                              
                                                                             
                                                                             
           
        if self.previous is None:return False
        prior=next((v for v in self.previous.get('B',()) if v[2]==a[1]),None)
        if prior is None:return False
        c,s=map(number,a[6:8]);lx,ly=map(number,prior[24:26]);mm=m10
        center=(mm.add(number(a[4]),mm.add(mm.mul(c,lx),-mm.mul(s,ly))),
                mm.add(number(a[5]),mm.add(mm.mul(s,lx),mm.mul(c,ly))))
        inv=mm.div(1,number(a[8]))
        velocity=tuple(mm.mul(inv,mm.add(p,-number(q))) for p,q in zip(center,prior[17:19]))
        squared=mm.add(mm.mul(velocity[0],velocity[0]),mm.mul(velocity[1],velocity[1]))
        return not all(math.isfinite(v) for v in (inv,*velocity,squared))

    def _existing_circle_geometry(self,operation):
        pass                                                                    

                                                                              
                                                                          
           
        if self.previous is None:return False
        code,*a=operation
        replaced=None
        if code==80 and a[3] in (0,3,7):
            props=self.body_values.get(a[1],{})
            if a[3]==0 and props.get('type')==a[4]:return False
            if a[3]==7 and props.get('fixed')==a[4]:return False
            parent=self.regs['B'][a[1]]['number']
        elif code==81 and a[3] in (5,6,7,8):
            replaced=a[1];parent=self.regs['S'][replaced]['parent']
        else:return False
        retained={reg for reg,item in self.regs['S'].items()
                  if item['live'] and item['parent']==parent and reg!=replaced}
        for value in self.previous.get('G',()):
            if value[2] not in retained or len(value)!=43:continue
            geometry=value[3:]
            if geometry[0]==0 and not number(geometry[2])>0:return True
        return False

    def _input_state(self,rows,operation,status,private):
        pass                                                                   
        code,*a=operation
        zero_object=(0,0,0)
        def body_properties(kind,fixed,damping,angular,gravity,enabled=1,sleep=0,threshold=0x3d4ccccd,fast=0):
            return {'type':kind,'fixed':fixed,'damping':damping,'angular':angular,'gravity':gravity,
                    'enabled':enabled,'sleep':sleep,'threshold':threshold,'fast':fast}
        if status==0:
            if code in (0,54,56):
                if code==0:
                    h=[a[1],a[2],a[3],0x41f00000,0x41200000,0x40400000,0x3f800000,0x3f800000,1,0]
                else:h=[a[2],a[3],*a[4:10],a[10],a[11] if code==56 else 0]
                self.world_values[a[0]]=h
                self.object_values[0][a[0]]=zero_object
                self.hook_values[a[0]]=[0]*13
                self.hook_modes[a[0]]=[0]*4
            if code in (2,30,57,90,16):
                target=a[1] if code in (57,90) else a[0]
                if code in (57,90):
                    props=body_properties(a[3],a[14],a[11],a[12],a[13],a[19] if code==90 else 1,a[16],a[18],a[15])
                elif code==30:props=body_properties(a[2],a[10],a[11],a[12],a[13],fast=a[14])
                elif code==2:props=body_properties(a[2],a[10],0,0,0x3f800000)
                else:props=body_properties(a[3],a[11],0,0,0x3f800000)
                self.body_values[target]=props
                self.object_values[1][target]=tuple(a[53:56]) if code==90 else tuple(a[15:18]) if code==16 else zero_object
                data=list(a[21:53]) if code==90 else [0]*32
                                                                               
                end=next((i for i,v in enumerate(data[:31]) if v==0),31)
                self.name_values[target]=tuple(data[:end]+[0]*(32-end))
            if code in (10,17,40,16):
                target=a[1] if code==16 else a[0]
                if code==40:
                    material=tuple(a[45:50])+(0,)
                    filter_=tuple(a[50:55])
                    density=a[44];flags=(a[56],a[57],0);object_=zero_object
                elif code==16:
                    material=(0x3f19999a,0,0,0,0,0);filter_=tuple(a[18:23]);density=a[13]
                    flags=(0,0,0);object_=tuple(a[15:18])
                else:
                    material=(0x3f19999a,0,0,0,0,0);filter_=tuple(a[7:12]);density=a[4]
                    flags=(0,0,0);object_=tuple(a[12:15])
                self.shape_values[target]={'material':material,'filter':filter_,'density':density,'flags':flags}
                self.object_values[2][target]=object_
            if code==80:
                props=self.body_values[a[1]]
                key={0:'type',1:'enabled',4:'damping',5:'angular',6:'gravity',7:'fixed'}.get(a[3])
                if key is not None:props[key]=a[4]
            if code in (12,19):self.shape_values[a[1]]['density']=a[2]
            if code==59:self.body_values[a[1]]['sleep']=a[3]
            if code==60:self.body_values[a[1]]['threshold']=a[3]
            if code==61:self.world_values[a[0]][9]=a[2]
            if code==55:self.world_values[a[0]][8]=a[1]
            if code==81:
                props=self.shape_values[a[1]];material=list(props['material'])
                if a[3] in (0,1,2):material[{0:0,1:1,2:4}[a[3]]]=a[4];props['material']=tuple(material)
                if a[3]==3:props['material']=tuple(a[4:10])
                if a[3]==4:props['filter']=tuple(a[4:9])
            if code==82:
                h=self.world_values[a[0]];kind=a[2]
                if kind==0:h[8]=a[3]
                elif kind==5:h[:2]=a[3:5]
                elif kind==4:h[2]=a[3]
                elif kind in (1,2):
                    value=a[3]
                    if a[1]==0 and number(value)<0:value=0
                    h[5+kind]=value
                else:
                    values=list(a[3:6])
                    if a[1]==0:values=[0 if number(v)<0 else v for v in values]
                    h[3:6]=values
            if code==83:
                if a[1]==1:targets=(a[2],)
                else:
                    parent=self.regs['B'][a[2]]['number']
                    targets=tuple(reg for reg,item in self.regs['S'].items() if item['live'] and item['parent']==parent)
                for target in targets:
                    flags=list(self.shape_values[target]['flags']);flags[a[4]]=a[5]
                    self.shape_values[target]['flags']=tuple(flags)
            if code==84:
                self.name_values[a[1]]=tuple([0]*32 if a[3] else [*a[5:36],0])
            if code==15:self.object_values[a[1]-1][a[2]]=tuple(a[3:6])
            if code==85:self.object_values[a[1]][a[0] if a[1]==0 else a[2]]=tuple(a[4:7])
        for (reg,),h in keyed(rows,'WS12').items():
            expected=tuple(self.world_values[reg])
            if not private:expected=(*expected[:3],0,0,0,*expected[6:])
            require(h[:10]==expected,'WS12 independent current settings from inputs')
            w=next(v for v in rows['W'] if v[2]==reg)
            require(w[10:13]==h[:3],'public world values agree with current settings')
            if private:
                awake=next((v[6] for v in rows['SS11'] if v[2:4]==(reg,2)),None)
                require(h[10]==awake,'WS12 AwakeBodyCount from current set2')
        for value in rows['B']:
            reg=value[2];props=self.body_values[reg]
            require((value[12],value[28],value[29])==(props['type'],props['enabled'],props['fixed']),
                    'B current type/enabled/fixed from mutable input ledger')
            require(value[30:33]==self.object_values[1][reg],'B current object token from inputs')
            if private:
                y=next((v for v in rows['Y'] if v[2]==reg),None)
                require(y is not None and y[15:19]==(props['damping'],props['angular'],props['gravity'],props['fast']),
                        'Y current damping/gravity/fast from inputs')
        for value in rows['S']:
            reg=value[2];props=self.shape_values[reg]
            require(value[19]==props['density'] and value[20:26]==props['material'] and value[26:31]==props['filter'],
                    'S current density/material/filter from inputs')
            require(value[40:43]==self.object_values[2][reg],'S object token from inputs')
        for (reg,),h in keyed(rows,'EF12').items():require(h==self.shape_values[reg]['flags'],'EF12 flags including body only-current-shapes')
        for (target,reg),h in keyed(rows,'UD12').items():require(h==self.object_values[target][reg],'UD12 independent presence/zero token identity')
        for (reg,),h in keyed(rows,'NM12').items():
            data=self.name_values[reg]
            length=data.index(0)
            require(h==(length,*data[:length],*([0]*(32-length))),'NM12 first NUL canonical copy, not raw tail')
        if private:
            for reg,item in self.regs['B'].items():
                if not item['live']:continue
                w=self._world_of(item['number'])
                expected=self.name_values[reg]
                require(keyed(rows,'NP12').get((w,item['number'][0]))==expected,'NP12 raw32 constructor/setter difference')

    def _rules_and_callbacks(self,rows,operation,status):
        code,*a=operation
        if status==0 and code==86:
            config=self.hook_values[a[0]]
            kind=a[2];bit=1<<kind
            config[0]=(config[0]|bit) if a[3] else (config[0]&~bit)
            config[1+kind]=a[4]
            self.hook_modes[a[0]][kind]=a[1]
            if kind<2:config[5+2*kind:7+2*kind]=a[5:7]
        if status==0 and code==87:
            rules=self.rules[a[0]][a[1]]
            if a[2]==0:rules.clear()
            elif a[1]<2:
                pair=(*self.regs['S'][a[3]]['number'],*self.regs['S'][a[4]]['number'])
                rules.append((*pair,*a[5:12]) if a[1]==1 else (*pair,a[5]))
            else:rules.append(tuple(a[3:6]))
        expected={}
        for w,item in self.regs['W'].items():
            if not item['live']:continue
            config=self.hook_values[w]
            config[9:13]=[len(values) for values in self.rules[w]]
            require(keyed(rows,'HC12')[w,]==tuple(config),'HC12 installed/function/context/rule count input ledger')
            for kind,values in enumerate(self.rules[w]):
                for j,value in enumerate(values):expected[w,kind,j]=value
        require(keyed(rows,'HR12')==expected,'HR12 immutable ordered full values; history survives participant death')
        traces=rows['HT12']
        require([v[3] for v in traces]==list(range(len(traces))),'HT12 global actual callback order/ordinal')
        lock_calls=[]
        for ordinal,value in enumerate(traces):
            w,kind=value[2],value[4]
            require(w in self.hook_values and self.regs['W'][w]['live'],'callback current live owner')
            config=self.hook_values[w]
            require(config[0]&(1<<kind),'no application HT when callback uninstalled')
            h=value[5:];function=config[1+kind]
            game=self.hook_modes[w][kind]==1
            rules=self.rules[w][kind]
            if kind<2:
                owner=wide(self.regs['W'][w]['number'][1:3])
                pair=(*self.raw_shapes.get((owner,tuple(h[:3])),()),*self.raw_shapes.get((owner,tuple(h[3:6])),()))
                require(len(pair)==10,'callback full ordered raw shape identities map to known Number5')
                if kind==0:
                    wanted=next((r[10] for r in rules if r[:10]==pair),1) if game else int(function!=1)
                    require(h[6]==wanted,'filter first exact ordered full-life rule; no symmetrizing')
                    continue
                before=h[7:37];after=h[37:67]
                m10.legacy.manifold(before,'HT12 pre before');m10.legacy.manifold(after,'HT12 pre after')
                wanted=list(before);allow=1
                if game:
                    for rule in rules:
                        if rule[:10]!=pair:continue
                        dot=m10.add(m10.mul(number(before[0]),number(rule[11])),m10.mul(number(before[1]),number(rule[12])))
                        if dot<number(rule[13]):continue
                        allow=rule[10]
                        if allow and rule[14]:wanted[:2]=rule[15:17]
                        break
                else:
                    allow=int(function!=1)
                    if function in (2,5):wanted[:2]=(0,0x3f800000)
                    if function==5:
                        for j in range(before[3]):
                            delta=.25 if j==0 else -.25
                            for offset in (4,6,8):
                                k=offset+13*j;wanted[k]=m10.bits(m10.add(number(before[k]),delta))
                        if before[3]==2:self.witnesses['pre_fixture5_two_points']+=1
                    if function==4:lock_calls.append(w)
                require(h[6]==allow and after==tuple(wanted),'pre callback edits both points exactly, false before later count0')
            else:
                x,material_a,y,material_b,result=h
                fx,fy=number(x),number(y)
                if game:
                    match=next((r for r in rules if r[:2]==(material_a,material_b)),None)
                    wanted=match[2] if match is not None else None
                elif function==3 and (material_a,material_b)==(3,5):wanted=0x3f000000 if kind==2 else 0x3f800000
                else:wanted=None
                if wanted is None:
                    wanted=m10.bits(m10.f32(math.sqrt(m10.mul(fx,fy)))) if kind==2 else (x if fx>fy else y)
                require(result==wanted,'material ordered first match/default; exact f32 product then sqrt/max')
                if kind==2 and config[0]&8:
                    require(ordinal+1<len(traces) and traces[ordinal+1][2]==w and traces[ordinal+1][4]==3,
                            'friction called immediately before restitution')
        if code in (31,32,42,43,52):
            expected=[]
            for w in lock_calls:
                expected.extend(((0,w),(2,None),(0,w)))
            require(len(rows['AP12'])==len(expected),'fixture4 exactly three legal attempts per actual preSolve')
            for value,(kind,reg) in zip(rows['AP12'],expected):
                require(value[2:5]==(7,1,kind) and (reg is None or value[5]==reg),'fixture4 ordered LOCKED7/reason1/kind/owner')

    def _filter_queries(self,rows,w,traces):
        pass                                                                 

                                                                           
                                                                            
                                                                       
           
        prior=self.previous
        shapes={s[2]:s for s in prior['S'] if tuple(s[8:10])==self.regs['W'][w]['number'][1:3]}
        proxies={(t[4]<<2)|t[3]:(t[2],t) for t in prior['T'] if t[2] in shapes}
        moves=[v[4] for v in prior['U'] if v[2]==w];moving=set(moves)
        bodies={tuple(b[3:6]):b for b in prior['B']}
        existing={tuple(sorted(h[5:7])) for key,h in index_rows(prior,'CT',4).items() if key[0]==w and h[0]}
        cursor=0
        for move,key in enumerate(moves):
            if key==NULL:continue
            require(key in proxies,'moved proxy remains a live prior leaf')
            reg,query=proxies[key];query_shape=shapes[reg];query_kind=key&3
            bounds=tuple(map(number,query[5:9]));accepted=[]
            for tree in ((1,0,2) if query_kind==2 else (2,)):
                candidates={}
                for candidate,(other,t) in proxies.items():
                    if candidate&3!=tree or not wide(t[9:11]):continue
                    other_bounds=tuple(map(number,t[5:9]))
                    if bounds[2]<other_bounds[0] or other_bounds[2]<bounds[0] or bounds[3]<other_bounds[1] or other_bounds[3]<bounds[1]:continue
                    if query_kind==2:
                        if tree==2 and candidate<key and candidate in moving:continue
                    elif candidate in moving:continue
                    first,second=(reg,other) if key<candidate else (other,reg)
                    sa,sb=shapes[first],shapes[second]
                    pair=(sa[3]-1,sb[3]-1)
                    if tuple(sorted(pair)) in existing or sa[12:15]==sb[12:15] or sa[31] or sb[31]:continue
                    ba,bb=bodies[tuple(sa[12:15])],bodies[tuple(sb[12:15])]
                    if ba[12]!=2 and bb[12]!=2:continue
                    fa,fb=(self.shape_values[r]['filter'] for r in (first,second))
                    group=fa[4] if fa[4]==fb[4] else 0
                    allowed=(not group&0x80000000) if group else bool(wide(fa[2:4])&wide(fb[:2]) and wide(fb[2:4])&wide(fa[:2]))
                    if not allowed:continue
                    candidates[(*sa[3:6],*sb[3:6])]=pair
                part=traces[cursor:cursor+len(candidates)]
                require(len(part)==len(candidates) and all(v[2]==w and v[4]==0 for v in part),
                        'filter callback count from independent proxy candidates')
                require(Counter(v[5:11] for v in part)==Counter(candidates.keys()),
                        'filter exact pair membership in move/tree query order')
                accepted.extend(candidates[v[5:11]] for v in part if v[11])
                cursor+=len(part)
            requests=[v[5:7] for v in rows['RQ'] if v[2]==w and v[4]==move]
            require(requests==list(reversed(accepted)),'accepted filter query order reverses into this move pair-list RQ')
        require(cursor==len(traces),'no additional filter callback or preflight invocation')
        self.witnesses['filter_query_calls']+=cursor

    def _callback_schedule(self,rows,operation,status,private):
        pass                                                              

                                                                             
                                                                            
                                                                           
                                                                               
                                                                    
           
        code,*a=operation
        active=not status and (code in (42,43) or code in (31,32) and number(a[1])!=0)
        if not active:
            require(not rows['HT12'],'no callback outside actual Pairs/Collide/nonzero Step')
            return ()
        if not private or self.previous is None:return ()
        w=a[0];prior=self.previous;config=self.hook_values[w]
        shapes={s[3]-1:s for s in prior['S'] if tuple(s[8:10])==self.regs['W'][w]['number'][1:3]}
        fat={p[2]:p[10:14] for p in prior['P']}
        bodies={tuple(b[3:6]):b for b in prior['B']}
        traces=rows['HT12'];cursor=0
                                                                       
        while cursor<len(traces) and traces[cursor][4]==0:
            require(code!=43 and traces[cursor][2]==w,'filter only target Pairs/Step before Create')
            cursor+=1
        if config[0]&1 and code!=43:self._filter_queries(rows,w,traces[:cursor])
        events=[]
        def mixed(pair):
            nonlocal cursor
            first,second=(self.shape_values[shapes[s][2]]['material'] for s in pair)
            for kind in (2,3):
                if not config[0]&(1<<kind):continue
                require(cursor<len(traces),'missing Create/Update material callback')
                v=traces[cursor];slot=kind-2
                require((v[2],v[4],*v[5:9])==(w,kind,first[slot],first[4],second[slot],second[4]),
                        'one ordered Create/Update material call with current shape inputs')
                cursor+=1
        old=index_rows(prior,'CS',6)
        updates=[(h[0],h[3:5],bool(h[13]&0x200000)) for key,h in
                 sorted(old.items(),key=lambda item:(0 if item[0][1]==1 else 1,item[0][2],item[0][3]))
                 if key[0]==w and (key[1]==1 or key[1:3]==(0,2))]
        if code!=43:
            for value in rows['RQ']:
                if value[2]!=w or not value[9]:continue
                pair=value[11:13];mixed(pair);events.append(('create',value[10],pair))
                awake=any(bodies[tuple(shapes[s][12:15])][27] for s in pair)
                cached=any(self.shape_values[shapes[s][2]]['flags'][2] for s in pair)
                if awake:updates.append((value[10],pair,cached))
        current={h[0]:h for key,h in index_rows(rows,'CS',6).items() if key[0]==w}
        if code!=42:
            for cid,pair,cached in updates:
                left,right=(tuple(map(number,fat[shapes[s][2]])) for s in pair)
                overlap=not (left[2]<right[0] or right[2]<left[0] or left[3]<right[1] or right[3]<left[1])
                if not overlap:continue
                mixed(pair);events.append(('update',cid,pair))
                                                                             
                                                                           
                                                                           
                required=bool(current.get(cid,(0,)*25)[24]) and cached and bool(config[0]&2)
                present=(cursor<len(traces) and traces[cursor][4]==1 and
                         traces[cursor][5:11]==(*shapes[pair[0]][3:6],*shapes[pair[1]][3:6]))
                if required or present:
                    require(cached and config[0]&2 and cursor<len(traces),'preSolve only installed/cached route')
                    value=traces[cursor]
                    require((value[2],value[4],*value[5:11])==(w,1,*shapes[pair[0]][3:6],*shapes[pair[1]][3:6]),
                            'preSolve follows its own Update in color/local order')
                    require(value[15]>0,'preSolve requires initial pointCount>0')
                    cursor+=1
        require(cursor==len(traces),'duplicate/extra/out-of-order callback after expected routes')
        self.witnesses['scheduled_create_mix_routes']+=sum(kind=='create' for kind,cid,pair in events)
        self.witnesses['scheduled_update_mix_routes']+=sum(kind=='update' for kind,cid,pair in events)
        return tuple(events)

    def _contact_cache_history(self,rows,operation,status,events):
        pass                                                                 

                                                                        
                                                                              
           
        prior=self.previous or defaultdict(list);code,*a=operation
        created={(a[0],cid):pair for kind,cid,pair in events if kind=='create'}
        updated={(a[0],cid):pair for kind,cid,pair in events if kind=='update'}
        old={(v[2],v[6]):v[6:] for v in prior['CS']}
        old_cold=index_rows(prior,'CT',4);cold=index_rows(rows,'CT',4)
        by_slot={}
        for reg,item in self.regs['S'].items():
            if item['live']:by_slot[self._world_of(item['number']),item['number'][0]]=reg
        for value in rows['CS']:
            w,cid=value[2],value[6];h=value[6:];key=(w,cid);c=cold[key]
            if key not in created:
                require(key in old and old_cold[key][18:20]==c[18:20],'retained material cache belongs to the same contact lifetime')
                require(h[13]&0x200000==old[key][13]&0x200000,'cached preSolve flag changes only on Create')
                require(c[16]&4==old_cold[key][16]&4,'cached contact-event flag changes only on Create')
            if key in created or key in updated:
                pair=created.get(key,updated.get(key))
                pa,pb=(self.shape_values[by_slot[w,s]] for s in pair)
                first,second=pa['material'],pb['material'];config=self.hook_values[w]
                def mix(kind):
                    index=kind-2;x,y=first[index],second[index];ma,mb=first[4],second[4]
                    if config[0]&(1<<kind):
                        if self.hook_modes[w][kind]:
                            rule=next((r for r in self.rules[w][kind] if r[:2]==(ma,mb)),None)
                            if rule is not None:return rule[2]
                        elif config[1+kind]==3 and (ma,mb)==(3,5):return 0x3f000000 if kind==2 else 0x3f800000
                    return m10.bits(m10.f32(math.sqrt(m10.mul(number(x),number(y))))) if kind==2 else (x if number(x)>number(y) else y)
                require(h[9:11]==(mix(2),mix(3)),'cached friction/restitution follow actual Create/Update and ordered callback rules')
                if key in updated:
                    require(h[51]==1 and h[12]==m10.bits(m10.add(number(first[3]),number(second[3]))),
                            'Update defines rolling cache and refreshes tangent speed')
                    hit=bool(c[16]&1) and bool(pa['flags'][1] or pb['flags'][1])
                    require(bool(h[13]&0x100000)==hit,'hit-enable flag refreshes only on actual touching Update')
                else:
                    require(h[51]==0 and h[11:13]==(0,0),'Create has unread rolling mask and zero tangent before first Update')
                    require(not h[13]&0x100000,'Create does not set hit cache')
                if key in created:
                    require(bool(h[13]&0x200000)==bool(pa['flags'][2] or pb['flags'][2]),'Create caches initial preSolve flag')
                    require(bool(c[16]&4)==bool(pa['flags'][0] or pb['flags'][0]),'Create caches initial contact-event flag')
            else:
                require(h[9:13]==old[key][9:13] and h[51]==old[key][51] and
                        h[13]&0x100000==old[key][13]&0x100000,
                        'all material caches/defined/hit bits stay unchanged outside Create/Update')

    def _mark_history(self,rows,operation,status):
        pass                                                           

                                                                              
                                                                              
                                                                                
                                                                         
           
        code,*a=operation
        bodies=index_rows(rows,'BS11',4)
        contacts={key:h for key,h in index_rows(rows,'CT',4).items() if h[0]}
        prior=self.previous or defaultdict(list)
        old_links=index_rows(prior,'BL9',4)
        old_islands=index_rows(prior,'IS',4)
        old_world=index_rows(prior,'WS11',4)
        public={}
        for value in rows['B']:
            owner=self._world_of((*value[3:4],*value[10:12],*value[8:10]))
            require(owner is not None,'mark body owner lifetime')
            public[owner,value[3]-1]=value
        body_keys={key:(*self.regs['W'][key[0]]['number'][1:3],key[1],*public[key][10:12]) for key in bodies}
        contact_keys={key:(*self.regs['W'][key[0]]['number'][1:3],key[1],*h[18:20]) for key,h in contacts.items()}
        for key in body_keys.values():self.body_marks.setdefault(key,0)
        for key in contact_keys.values():self.contact_marks.setdefault(key,0)
        for w in {key[0] for key in bodies}:
            parent={i:(i if h[13]==NULL else h[13]) for (owner,i),h in old_islands.items() if owner==w and h[0]}
            def root(i):
                while parent[i]!=i:i=parent[i]
                return i
            def union(x,y):
                if x in parent and y in parent:parent[root(y)]=root(x)
            for (owner,cid),h in sorted(contacts.items()):
                if owner==w and h[16]&1:
                    left=old_links.get((w,h[7]));right=old_links.get((w,h[10]))
                    if left is not None and right is not None:union(left[2],right[2])
            traces=[v[4:] for v in rows['TR11'] if v[2]==w and v[4]==3]
            require(len(traces)<=1,'at most one split call per world/operation')
            positive=code in (31,32) and not status and number(a[1])>0 and a[0]==w
            forced_base=None
            if code==58 and not status and a[0]==w and not a[3]:
                body=next((v for v in prior['B'] if v[2]==a[1]),None)
                if body is not None and body[27]:
                    link=old_links.get((w,body[3]-1))
                    if link is not None:
                        island=old_islands.get((w,link[2]))
                        if island is not None and island[14]>0:forced_base=link[2]
                if forced_base is not None:
                    require(bool(traces),'SetAwake(false) must split dirty awake island before TrySleep')
            pending=old_world.get((w,1),(0,NULL,0,0))[1]
            if positive and pending in parent:
                                                                           
                                                                              
                                                                         
                if root(pending)!=pending:require(not traces,'merge invalidates pending child before split scheduling')
                else:require(bool(traces),'surviving pending root must be consumed before Finalize')
            for trace in traces:
                _,base,source,target,body_count,contact_count,worked=trace
                require(worked in (0,1) and (w,base) in old_islands,'split trace live base and bool')
                island=old_islands[w,base]
                require(island[0] and source==island[1] and target==source,'split source/target before destruction')
                require(bool(worked)==(source==2 and island[14]>0),'split didWork from prior removal count/set')
                if positive:require(base==pending,'actual split consumes previous pending candidate')
                elif forced_base is not None:
                    require(base==forced_base,'forced sleep splits exactly its target body island')
                else:require(code==64 and a[1]==3 and base==a[2],
                             'split only through real Step, forced sleep, or explicit COMPONENT phase')
                self.witnesses['split_calls']+=1
                if not worked:continue
                members={bid for (owner,bid),h in old_links.items() if owner==w and h[2] in parent and root(h[2])==root(base)}
                live_contacts={cid for (owner,cid),h in contacts.items() if owner==w and h[16]&1 and (h[7] in members or h[10] in members)}
                require(len(members)==body_count and len(live_contacts)==contact_count,'split complete pre-DFS body/contact membership')
                for bid in members:
                    require((w,bid) in body_keys,'split body lifetime survives Step')
                    self.body_marks[body_keys[w,bid]]=1
                for cid in live_contacts:self.contact_marks[contact_keys[w,cid]]=1
                self.witnesses['split_mark_writes']+=len(members)+len(live_contacts)
            for key,h in bodies.items():
                if key[0]==w:require(h[3]==self.body_marks[body_keys[key]],'body mark equals persistent split history')
            for key,h in contacts.items():
                if key[0]==w:require(h[17]==self.contact_marks[contact_keys[key]],'contact mark equals persistent split history')

    def _finalize_history(self,rows,operation,status):
        pass                                                                 

                                                                        
                                                                               
           
        code,*a=operation
        if code not in (31,32) or status or number(a[1])<=0:return
        w=a[0]
        bs=index_rows(rows,'BS11',4);bl=index_rows(rows,'BL9',4)
        islands=index_rows(rows,'IS',4);world=index_rows(rows,'WS11',4)
        moves=[v for v in rows['M'] if v[2]==w]
        require([v[3] for v in moves]==list(range(len(moves))),'Finalize M exact dense order')
        public={tuple(v[3:6]):(v[2],v) for v in rows['B'] if tuple(v[8:10])==self.regs['W'][w]['number'][1:3]}
        candidate=NULL;sleep_time=0;seen=set()
        for value in moves:
            raw=tuple(value[4:7])
            require(raw in public and raw not in seen,'Finalize M live unique raw body identity')
            seen.add(raw);reg,body=public[raw];bid=raw[0]-1;state=bs[w,bid]
            require(state[4]==(NULL if value[14] else value[3]),'bodyMoveIndex dense before sleep; reset after sleep')
            require(value[7:11]==body[13:17],'M transform from Finalize survives sleep transfer')
            require(value[11:14]==self.object_values[1][reg],'M objectId captured from current input history')
            require(value[14]==int(not body[27] and bool(body[28])),'M fellAsleep follows final owning set')
            island=islands[w,bl[w,bid][2]]
            time=number(state[1])
            if time>=.5 and island[14]>0 and time>number(sleep_time):
                candidate=bl[w,bid][2];sleep_time=state[1]
        if moves:
            require((w,0) in world,'Finalize snapshot before sleeping exists for M')
            require(world[w,0][1:]==(NULL,candidate,sleep_time),'Finalize pending split chosen in pre-sleep dense order')
            require(world[w,1][2:]==(candidate,sleep_time),'task candidate survives post-Finalize sleep')
            require(world[w,1][1]==(candidate if world[w,1][0] else NULL),'world pending candidate follows sleep configuration')
            self.witnesses['finalize_before_sleep_events']+=len(moves)
        else:require((w,0) not in world,'no stale Finalize snapshot when no body was finalized')

    def _body_pool_history(self,rows):
        pass                                                      
        prior=self.previous or defaultdict(list)
        old_headers=index_rows(prior,'BP11',3);headers=index_rows(rows,'BP11',3)
        old_free=index_rows(prior,'BF11',4);free=index_rows(rows,'BF11',4)
        old_alive=set(index_rows(prior,'BS11',4));alive=set(index_rows(rows,'BS11',4))
        for (w,),header in headers.items():
            before=old_headers.get((w,),(0,0,0));next_id=before[0]
            stack=[old_free[w,j][0] for j in range(before[1])]
            created=sorted(bid for owner,bid in alive-old_alive if owner==w)
            destroyed=sorted(bid for owner,bid in old_alive-alive if owner==w)
            require(len(created)<=1 and len(destroyed)<=1,'one public body allocation/destruction per O')
            for bid in created:
                expected=stack.pop() if stack else next_id
                if expected==next_id:next_id+=1
                require(bid==expected,'body ID allocation pops the last free ID before extending')
            stack.extend(destroyed)
            require(header==(next_id,len(stack),sum(owner==w for owner,bid in alive)),'body pool exact temporal next/free/live counts')
            require([free[w,j][0] for j in range(header[1])]==stack,'body free stack retains exact LIFO order')

    def _contact_pool_history(self,rows,operation,status):
        pass                                                                   

                                                                           
                                                                          
                                                                           
           
        prior=self.previous or defaultdict(list);code,*a=operation
        headers=index_rows(rows,'CP',3);old_headers=index_rows(prior,'CP',3)
        old_ct={key:h for key,h in index_rows(prior,'CT',4).items() if h[0]}
        current={key for key,h in index_rows(rows,'CT',4).items() if h[0]}
        old_free=index_rows(prior,'CF',4);free=index_rows(rows,'CF',4)
        for (w,),header in headers.items():
            before=old_headers.get((w,),(0,0,0));next_id=before[0]
            stack=[old_free[w,j][0] for j in range(before[1])]
            alive={cid for owner,cid in old_ct if owner==w}
            created={}
            for v in rows['RQ']:
                if v[2]!=w or not v[9]:continue
                expected=stack.pop() if stack else next_id
                if expected==next_id:next_id+=1
                require(v[10]==expected and expected not in alive,'contact allocation uses exact LIFO request order')
                alive.add(expected);created[expected]=v[11:13]
            destroyed=[]
            if not status and a[0]==w:
                if code==43 or code in (31,32) and number(a[1])!=0:
                    shapes={s[3]-1:s for s in prior['S'] if s[2] in self.regs['S'] and
                            self._world_of(self.regs['S'][s[2]]['number'])==w}
                    fat={p[2]:tuple(map(number,p[10:14])) for p in prior['P']}
                    bodies={tuple(b[3:6]):b for b in prior['B']}
                    pairs={cid:h[5:7] for (owner,cid),h in old_ct.items() if owner==w and h[2]==2}
                    for cid,pair in created.items():
                        if any(bodies[tuple(shapes[s][12:15])][27] for s in pair):pairs[cid]=pair
                    for cid,pair in pairs.items():
                        left,right=(fat[shapes[s][2]] for s in pair)
                        if left[2]<right[0] or right[2]<left[0] or left[3]<right[1] or right[3]<left[1]:destroyed.append(cid)
                    destroyed.sort()
                else:
                    target=None;shape_id=None
                    if code==3 or code==80 and a[3] in (0,1):
                        body=next((b for b in prior['B'] if b[2]==a[1]),None)
                        if body is not None and (code==3 or a[3]==0 and body[12]!=a[4] and body[28] or
                                                 a[3]==1 and not a[4] and body[28]):target=body[3]-1
                    if code in (11,18) or code==81 and a[3]>=4:
                        shape=next((s for s in prior['S'] if s[2]==a[1]),None)
                        if shape is not None and not (code==81 and a[3]==4 and shape[26:31]==tuple(a[4:9])):
                            target=shape[12]-1;shape_id=shape[3]-1
                    if target is not None:
                        links=index_rows(prior,'BL9',4)[w,target]
                        destroyed=[links[j] for j in range(5,len(links),2)
                                   if shape_id is None or shape_id in old_ct[w,links[j]][5:7]]
                    elif code==53:
                                                                             
                                                                             
                        destroyed=sorted(alive-{cid for owner,cid in current if owner==w})
                        require(len(destroyed)==1,'one explicit DestroyContact fixture')
            require(len(destroyed)==len(set(destroyed)) and set(destroyed)<=alive,'ordered frees refer to live contacts once')
            alive.difference_update(destroyed);stack.extend(destroyed)
            require(alive=={cid for owner,cid in current if owner==w},'contact lifetime changes only through predicted Create/destroy routes')
            require(header==(next_id,len(stack),len(alive)),'contact pool temporal next/free/live')
            require([free[w,j][0] for j in range(header[1])]==stack,'contact free stack follows collision IDs or old edge order')

    def _body_layout_history(self,rows,operation,status):
        pass                                                               

                                                                               
                                                                           
           
        code,*a=operation
        if code!=80 or status or self.previous is None:return
        expected=defaultdict(list);actual=defaultdict(list)
        for source,dest in ((self.previous,expected),(rows,actual)):
            for value in source['SD11']:
                key=value[2:4]
                require(value[4]==len(dest[key]),'SD11 ordered dense body indices')
                dest[key].append(value[5])
        for value in rows['TR11']:
            if value[4]!=1:continue
            w=value[2];source,target,count,worked=value[6],value[7],value[8],value[10]
            require(worked==1 and target==2 and source>=3 and len(expected[w,source])==count,'WakeSolverSet appends the exact source dense array')
            expected[w,2].extend(expected[w,source]);expected[w,source]=[]
        before=next(v for v in self.previous['B'] if v[2]==a[1]);bid=before[3]-1;w=a[0]
        source=next(s for (owner,s),values in expected.items() if owner==w and bid in values)
        target=source
        if a[3]==0 and a[4]!=before[12]:target=1 if not before[28] else 0 if a[4]==0 else 2
        elif a[3]==1 and a[4]!=before[28]:target=(0 if before[12]==0 else 2) if a[4] else 1
        if source!=target:
            values=expected[w,source];at=values.index(bid);last=values.pop()
            if at<len(values):values[at]=last;self.witnesses['nonlast_body_remove_swap']+=1
            expected[w,target].append(bid);self.witnesses['body_transfers']+=1
        require({k:tuple(v) for k,v in actual.items() if v}=={k:tuple(v) for k,v in expected.items() if v},
                'TransferBody exact old/new dense order, including RemoveSwap and unchanged worlds')

    def _ownership(self,rows):
        bs=index_rows(rows,'BS11',4);sp=index_rows(rows,'SP11',3);sf=index_rows(rows,'SF11',4)
        bp=index_rows(rows,'BP11',3);bf=index_rows(rows,'BF11',4);ss=index_rows(rows,'SS11',4)
        sd=index_rows(rows,'SD11',5);sm=index_rows(rows,'SM11',5)
        cp=index_rows(rows,'CP',3);cf=index_rows(rows,'CF',4);ct=index_rows(rows,'CT',4)
        ip=index_rows(rows,'IP',3);ifs=index_rows(rows,'IF',4);islands=index_rows(rows,'IS',4)
        ca=index_rows(rows,'CA',5);cs=index_rows(rows,'CS',6)
        live_worlds={reg for reg,item in self.regs['W'].items() if item['live']}
        require({w for w, in sp}==live_worlds and {w for w, in bp}==live_worlds and
                {w for w, in cp}==live_worlds and {w for w, in ip}==live_worlds,'all private pools for each live world')
        for w in live_worlds:
            sets={s:h for (owner,s),h in ss.items() if owner==w}
            require(set(sets)==set(range(sp[w,][0])),'SS all sparse set slots')
            pool(sp[w,],[h[0] for (owner,j),h in sf.items() if owner==w],
                 {s for s,h in sets.items() if h[0]},'solver set')
            require(all(sets[s][:2]==(1,s) for s in (0,1,2)),'reserved sets0/1/2 alive')
            bodies={b:h for (owner,b),h in bs.items() if owner==w}
            pool(bp[w,],[h[0] for (owner,j),h in bf.items() if owner==w],bodies,'body')
            cold={c:h for (owner,c),h in ct.items() if owner==w}
            require(set(cold)==set(range(cp[w,][0])),'CT complete sparse slots')
            pool(cp[w,],[h[0] for (owner,j),h in cf.items() if owner==w],{c for c,h in cold.items() if h[0]},'contact')
            island_slots={i:h for (owner,i),h in islands.items() if owner==w}
            require(set(island_slots)==set(range(ip[w,][0])),'IS complete sparse slots')
            pool(ip[w,],[h[0] for (owner,j),h in ifs.items() if owner==w],{i for i,h in island_slots.items() if h[0]},'island')
            require({(domain,index) for (owner,domain,index) in ca if owner==w}==
                    {(0,s) for s in range(sp[w,][0])}|{(1,c) for c in range(12)},'CA exact all set slots+12 colors')
            mapped={}
            for s,h in sets.items():
                if not h[0]:
                    require(h==(0,NULL,0,0,0,0),'free SS canonical, no stale subarrays')
                    continue
                require(h[1]==s and h[3]==(h[2] if s==2 else 0),'state only in awake2')
                expected={(w,s,j) for j in range(h[2])}
                require({key for key in sd if key[:2]==(w,s)}==expected and
                        {key for key in sm if key[:2]==(w,s)}==expected,'SD/SM exact dense completeness')
                for j in range(h[2]):
                    bid=sd[w,s,j][0];sim=sm[w,s,j]
                    require(bid in bodies and bid not in mapped and sim[22]==bid,'SD/SM live unique body identity')
                    mapped[bid]=(s,j,sim)
                    require(bodies[bid][5]==int(s==2),'BS hasBodyState follows current owning set')
            require(set(mapped)==set(bodies),'every alive body owns exactly one dense sim')
            for reg,item in self.regs['B'].items():
                if not item['live'] or self._world_of(item['number'])!=w:continue
                b=next(v for v in rows['B'] if v[2]==reg);s,j,sim=mapped[item['number'][0]]
                require(bool(b[28])==(s!=1) and bool(b[27])==(s==2),'current enabled/awake matches owning set')
                require((s==0)==(b[12]==0 and bool(b[28])),'current type/static owning set')
                y=next((v[3:] for v in rows['Y'] if v[2]==reg),None)
                require(y is not None and y[10:12]==(s,j),'Y current sparse/dense local index')
                require(y[12:15]==sim[19:22],'Y current damping/gravityScale equals owning sim')
                if s!=2:require(y[3:7]==(0,0,0x3f800000,0),'identity deltas without BodyState')
            dns=[v for v in rows['DN'] if v[2]==w]
            require([v[3] for v in dns]==list(range(sets[2][2])),'DN exact awake dense order')
            require([v[4]-1 for v in dns]==[sd[w,2,j][0] for j in range(sets[2][2])],'DN only current awake set2')
            live_contacts={c:h for c,h in cold.items() if h[0]}
            sims={}
            for (owner,domain,index,j),h in cs.items():
                if owner!=w:continue
                cid=h[0]
                require(cid in live_contacts and cid not in sims,'each live CT has exactly one CS')
                c=live_contacts[cid]
                require((domain,index,j)==(int(c[3]!=NULL),c[3] if c[3]!=NULL else c[2],c[4]),'CT/CS set/color/local reciprocity')
                require(h[3:5]==c[5:7],'CT/CS ordered shape identity')
                m10.legacy.manifold(h[21:51],'current M30')
                require(h[51] in (0,1) and (h[51] or h[11]==0),'CS rollingDefined exact mask')
                sims[cid]=h
            require(set(sims)==set(live_contacts),'CT/CS full completeness')
            for (owner,domain,index),h in ca.items():
                if owner==w:require(h[0]==sum(1 for key in cs if key[:3]==(w,domain,index)),'CA current array count')
            self._islands_and_graph(w,rows,mapped,live_contacts,island_slots,sets)

    def _islands_and_graph(self,w,rows,bodies,contacts,island_slots,sets):
        bl={bid:h for (owner,bid),h in index_rows(rows,'BL9',4).items() if owner==w}
        require(set(bl)==set(bodies),'BL9 every live body')
        occupancy=defaultdict(set)
        for bid,h in bl.items():
            key=h[0];previous=NULL;seen=[]
            while key!=NULL:
                cid,side=key>>1,key&1
                require(cid in contacts and key not in seen,'body edge live/acyclic')
                c=contacts[cid];offset=7+3*side
                require(c[offset:offset+2]==(bid,previous),'body edge owner/previous')
                seen.append(key);previous=key;key=c[offset+2]
            require(h[1]==len(seen) and h[5:]==tuple(v for key in seen for v in (key>>1,key&1)),'BL9 full linked order/count')
            require({key>>1 for key in seen}=={cid for cid,c in contacts.items() if bid in (c[7],c[10])},'BL9 complete incident contacts')
        for cid,c in contacts.items():
            require(c[1]==cid,'CT identity; mark checked against phase history')
            if c[3]!=NULL:
                require(c[2]==2 and c[3]<12,'graph contacts own awake set2')
                for bid in (c[7],c[10]):
                    require(bid in bodies,'graph live participant')
                    if bodies[bid][0]==0 or c[3]==11:continue
                    require(bid not in occupancy[c[3]],'ordinary graph color nonstatic conflict')
                    occupancy[c[3]].add(bid)
        gb=index_rows(rows,'GB',4)
        require({color for owner,color in gb if owner==w}==set(range(12)),'all12 graph colors')
        for color in range(12):
            h=gb[w,color]
            if color==11:require(h==(0,0,0),'overflow color has no occupancy bitset');continue
            require(h[0]==1 and h[1]<=h[2],'ordinary graph bitset framing')
            found={64*j+k for j in range(h[1]) for k in range(64) if wide(h[3+2*j:5+2*j])>>k&1}
            require(found==occupancy[color],'graph full low/high block bits equal occupancy')
        pair=next((v for v in rows['H'] if v[2:4]==(w,1)),None)
        require(pair is not None,'pairSet header')
        data=pair[6:];keys={wide(data[j:j+2]) for j in range(0,len(data),3) if data[j+2]}
        expected={(min(c[5],c[6])<<32)|max(c[5],c[6]) for c in contacts.values()}
        require(keys==expected and pair[5]==len(expected),'pairSet exactly live cold contacts')
        live={i:h for i,h in island_slots.items() if h[0]}
        lists=defaultdict(list)
        for value in rows['IL']:
            if value[2]!=w:continue
            key=value[3:5]
            require(value[5]==len(lists[key]),'IL exact member order/ordinal')
            lists[key].append(value[6])
        found=[]
        for s,h in sets.items():
            expected_count=h[5] if h[0] else 0
            require(len(lists[0,s])==expected_count,'set island count/list')
            if s in (0,1):require(not lists[0,s],'static/disabled have no islands')
            for j,i in enumerate(lists[0,s]):
                require(i in live and live[i][1:4]==(s,j,i),'island sparse/dense reciprocal')
                found.append(i)
        require(len(found)==len(set(found)) and set(found)==set(live),'all alive islands mapped once')
        seen_bodies=[];seen_contacts=[]
        for i,h in live.items():
            path={i};parent=h[13]
            while parent!=NULL:
                require(parent in live and parent not in path,'island parent live/acyclic')
                path.add(parent);parent=live[parent][13]
            require(h[10:13]==(NULL,NULL,0),'joint-free profile')
            for kind,start,tail,count,source,pf,nf,ownerfield in ((1,h[4],h[5],h[6],bl,3,4,2),
                                                                (2,h[7],h[8],h[9],contacts,14,15,13)):
                walk=[];at=start;previous=NULL
                while at!=NULL:
                    require(at in source and at not in walk,'island member live/acyclic')
                    value=source[at]
                    require(value[pf]==previous and value[ownerfield]==i,'island member owner/previous')
                    walk.append(at);previous=at;at=value[nf]
                require(len(walk)==count and (walk[-1] if walk else NULL)==tail and lists[kind,i]==walk,'island head/tail/count/member order')
                if kind==1:seen_bodies+=walk
                else:seen_contacts+=walk
        require(len(set(seen_bodies))==len(seen_bodies) and set(seen_bodies)=={bid for bid,(s,j,sim) in bodies.items() if s not in (0,1)},
                'enabled nonstatic body island partition')
        require(len(set(seen_contacts))==len(seen_contacts) and set(seen_contacts)=={cid for cid,c in contacts.items() if c[16]&1},
                'touching contact island partition')

    def _live_contact_values(self,rows,w,kind,reg,capacity):
        pass                                                                      
        target=self.regs[kind][reg]
        body=target['number'][0] if kind=='B' else target['parent'][0]
        shape=target['number'][0] if kind=='S' else None
        links=index_rows(rows,'BL9',4).get((w,body))
        require(links is not None,'live contact-list source has its own body edge list')
        cold=index_rows(rows,'CT',4)
        sims={(v[2],v[6]):v[6:] for v in rows['CS']}
        numbers={item['number'][0]:item['number'] for item in self.regs['S'].values()
                 if item['live'] and item['number'][3:]==self.regs['W'][w]['number'][1:3]}
        result=[]
        for cid in links[5::2]:
            if len(result)==capacity:break
            c=cold[w,cid]
            require(c[0],'contact-list edge is live')
            if not c[16]&1 or shape is not None and shape not in c[5:7]:continue
            number_=(cid,*c[18:20],*self.regs['W'][w]['number'][1:3])
            result.append((*number_,*numbers[c[5]],*numbers[c[6]],1,*sims[w,cid][21:51]))
        return tuple(result)

    def _copies(self,rows,operation,status,private):
        code,*a=operation
        lists=keyed(rows,'CL12')
        values=defaultdict(list)
        for value in rows['CV12']:values[value[2:5]].append(value[6:])
        saving=code==89 and a[0] in (0,1) and status==0
        expected_current={(1,a[2],0)} if code==88 else set()
        require({key for key in lists if key[0]==1}==expected_current,'CL12 current shape list only on opcode88')
        if code==88:
            if status:wanted=()
            elif private:wanted=self._live_contact_values(rows,a[0],'S',a[2],512 if a[1] else a[3])
            else:wanted=None
            if wanted is not None:
                require(lists[1,a[2],0]==(status,len(wanted)) and tuple(values[1,a[2],0])==wanted,
                        'shapeContacts from private links, exact life/order/current nested manifold and raw capacity')
        if saving and private:
            wanted=self._live_contact_values(rows,a[1],'B' if a[0]==0 else 'S',a[2],512)
            require(lists[2,a[3],0]==(0,len(wanted)) and tuple(values[2,a[3],0])==wanted,
                    'fresh K12 must copy its actual body/shape source before becoming historical')
            self.witnesses['fresh_K12_values']+=len(wanted)
        if saving:self.saved_lists[a[3]]=(lists[2,a[3],0],tuple(values[2,a[3],0]))
        require({slot for kind,slot,phase in lists if kind==2 and phase==0}==set(self.saved_lists),'all saved K12 emitted, no invented copy')
        for slot,(header,data) in self.saved_lists.items():
            require(lists.get((2,slot,0))==header and tuple(values[2,slot,0])==data,'K12 saved history unchanged except successful save')
        for key,contacts in values.items():
            if key[2]==1:continue
            for h in contacts:
                require(tuple(h[5:10]) in self.known_shapes and tuple(h[10:15]) in self.known_shapes,'CV12 historical shape life, no late stamping')
                if private:require(tuple(h[:5]) in self.known_contacts,'CV12 historical contact identity')
        current={v[2]:v[3] for v in rows['MCN']}
        moves=defaultdict(list)
        for value in rows['MC']:
            require(value[3]==len(moves[value[2]]),'MC copy dense index')
            require(tuple(value[4:9]) in self.known_bodies,'MC historical BodyNumber')
            moves[value[2]].append(value[4:])
        for slot,count in current.items():require(len(moves[slot])==count,'MC exact count')
        require(len(current)==len(rows['MCN']) and set(moves)<=set(current),'MCN unique; no orphan MC')
        emitted={a[3]} if code==32 and status==0 else {a[0]} if code==37 else set()
        require(set(current)==emitted,'K8 movement copy emitted only on successful StepGame or ReadCopy')
        if code==32 and status==0:
            wanted=[];owner=self.regs['W'][a[0]]['number'][1:3]
            for value in rows['M']:
                if value[2]!=a[0]:continue
                item=next((item for item in self.regs['B'].values() if item['live'] and item['raw']==value[4:7] and item['number'][3:]==owner),None)
                require(item is not None,'fresh MC maps actual event raw ID to its current full body lifetime')
                wanted.append((*item['number'],*value[7:]))
            require(tuple(moves[a[3]])==tuple(wanted),'fresh MC is an independent copy of M with event-time number/objectId')
            self.saved_moves[a[3]]=tuple(moves[a[3]])
        for slot in emitted:
            require(slot in self.saved_moves,'MC previously saved movement copy')
            require(tuple(moves[slot])==self.saved_moves[slot],'MC own historical copy unchanged')

    def _hit_history(self,rows,operation,status,private):
        pass                                                                 

                                                                          
                                                                             
                                                      
           
        code,*a=operation
        worlds={w for w,item in self.regs['W'].items() if item['live']}
        counts={v[2]:v[3] for v in rows['HN10']}
        require(set(counts)==worlds and len(counts)==len(rows['HN10']),'HN10 exact live worlds')
        for w in worlds:
            birth=tuple(self.regs['W'][w]['number'][1:3]);owner=wide(birth)
            current=[v for v in rows['HR10'] if v[2]==w]
            require([v[3] for v in current]==list(range(len(current))) and counts[w]==len(current),'HR10 complete ordered hit count')
            actual=tuple(v[4:] for v in current)
            for hit in actual:
                require((owner,hit[:3]) in self.raw_shapes and (owner,hit[3:6]) in self.raw_shapes,
                        'raw hit retains known event-time shape identities')
            step=code in (31,32) and not status and a[0]==w
            if code==41 and not status and a[0]==w:
                wanted=()
            elif not step:
                wanted=self.raw_hit_history.get(birth,())
            elif number(a[1])<=0:
                wanted=()
            elif private:
                sims={v[6]:v[6:] for v in rows['CS'] if v[2]==w}
                cold={key[1]:h for key,h in index_rows(rows,'CT',4).items() if key[0]==w and h[0]}
                awake={v[4]-1 for v in rows['M'] if v[2]==w}
                packets=[h[0] for key,h in sorted(index_rows(rows,'PK10',6).items()) if key[0]==w and h[0]!=NULL]
                eligible={cid for cid,c in cold.items() if c[16]&1 and (c[7] in awake or c[10] in awake)}
                require(len(packets)==len(set(packets)) and set(packets)==eligible,
                        'PK10 complete pre-sleep touching contacts from Finalize bodies')
                shapes={item['number'][0]:item['raw'] for item in self.regs['S'].values()
                        if item['live'] and item['number'][3:]==birth}
                events=[];threshold=number(self.world_values[w][7])
                for cid in packets:
                    h=sims[cid]
                    if not h[13]&0x100000:continue
                    manifold=h[21:51];best=threshold;chosen=None;speed=0
                    for j in range(manifold[3]):
                        at=4+13*j;approach=manifold[at+10]^0x80000000
                        if number(approach)>best and number(manifold[at+9])>0:
                            best=number(approach);speed=approach;chosen=manifold[at:at+2]
                    if chosen is not None:events.append((*shapes[h[3]],*shapes[h[4]],*chosen,*manifold[:2],speed))
                wanted=tuple(events)
            else:wanted=actual
            require(actual==wanted,'HR10 hit generation/max approach/strict threshold/positive impulse or persistent non-Step history')
            self.raw_hit_history[birth]=actual
            if step:self.witnesses['generated_hit_events']+=len(actual)

    def _events(self,rows,operation,status,private):
        pass                                                                   

                                                                         
                                                                           
                                                                           
           
        code,*a=operation
        prior=self.previous or defaultdict(list)
        current_ct={key:h for key,h in index_rows(rows,'CT',4).items() if h[0]}
        old_ct={key:h for key,h in index_rows(prior,'CT',4).items() if h[0]}
        current_cs={(v[2],v[6]):v[6:] for v in rows['CS']}
        old_cs={(v[2],v[6]):v[6:] for v in prior['CS']}
        expected_ge={}
        worlds={w for w,item in self.regs['W'].items() if item['live']}
        for w in sorted(worlds):
            birth=tuple(self.regs['W'][w]['number'][1:3])
            owner=wide(birth)
            state=self.raw_event_history.setdefault(birth,{'begin':[],'end':[[],[]],'index':0})
            def shape(slot):
                found=[(number_,raw) for (life,raw),number_ in self.raw_shapes.items() if life==owner and raw[0]-1==slot]
                require(bool(found),'event participant has an actual historical shape allocation')
                return max(found,key=lambda item:wide(item[0][1:3]))
            def identity(c):
                na,ra=shape(c[5]);nb,rb=shape(c[6])
                return ra,rb,na,nb
            step=code in (31,32) and not status and a[0]==w
            collide=(step and number(a[1])!=0) or (code==43 and a[0]==w and not status)
            if step or (code==41 and a[0]==w and not status):state['begin']=[]
            starts=[];ends=[]
            if collide:
                for (owner_reg,cid),c in sorted(current_ct.items()):
                    if owner_reg!=w or c[16]&5!=5:continue
                    old=old_ct.get((w,cid))
                    if old is not None and old[18:20]==c[18:20] and old[16]&1:continue
                    manifold=list(current_cs[w,cid][21:51])
                    old_m=old_cs.get((w,cid),(0,)*51)[21:51]
                    if old is None or old[18:20]!=c[18:20]:old_m=(0,)*30
                    manifold[2]=old_m[2] if manifold[3] else 0
                    remaining=[list(old_m[4+13*j:17+13*j]) for j in range(old_m[3])]
                    for j in range(manifold[3]):
                        at=4+13*j
                        match=next((p for p in remaining if p[11]==manifold[at+11]),None)
                        manifold[at+7:at+11]=[*(match[7:9] if match is not None else (0,0)),0,0]
                        manifold[at+12]=int(match is not None)
                        if match is not None:match[7:9]=[0,0]
                    starts.append((*identity(c),tuple(manifold)))
            removed=[]
            for (owner_reg,cid),c in old_ct.items():
                if owner_reg!=w or c[16]&5!=5:continue
                now=current_ct.get((w,cid))
                gone=now is None or now[18:20]!=c[18:20]
                if gone or collide and not now[16]&1:removed.append(cid)
            if collide:order=sorted(removed)
            elif removed:
                if code in (3,80):bid=self.regs['B'][a[1]]['number'][0]
                elif code in (11,18,81):bid=self.regs['S'][a[1]]['parent'][0]
                else:bid=None
                links=index_rows(prior,'BL9',4).get((w,bid))
                order=[links[j] for j in range(5,len(links),2) if links[j] in removed] if links else sorted(removed)
                require(set(order)==set(removed),'destroy event old body-edge order covers all removed contacts')
            else:order=[]
            for cid in order:ends.append((*identity(old_ct[w,cid]),()))
            state['begin'].extend(starts);state['end'][state['index']].extend(ends)
            self.witnesses['begin_events']+=len(starts)
            self.witnesses['end_events_side'+str(state['index'])]+=len(ends)
            if step or (code==45 and a[0]==w and not status):
                state['index']=1-state['index'];state['end'][state['index']]=[]
                self.witnesses['end_buffer_rotations']+=1
            if private:
                require([v[4:] for v in rows['EB'] if v[2]==w]==[(*ra,*rb,*manifold) for ra,rb,na,nb,manifold in state['begin']],
                        'EB begin order and manifold captured before solver impulses')
                for side in (0,1):
                    require([v[4:] for v in rows['EE'+str(side)] if v[2]==w]==[(*ra,*rb) for ra,rb,na,nb,manifold in state['end'][side]],
                            'EE'+str(side)+' historical raw participants/order')
                hit_count=sum(v[2]==w for v in rows['HR10'])
                require([v[3:] for v in rows['EN9'] if v[2]==w]==[(len(state['begin']),len(state['end'][0]),len(state['end'][1]),state['index'],hit_count)],
                        'EN9 both buffers and current index from complete event history')
                begins=state['begin'];finished=state['end'][1-state['index']]
                expected_ge[w]=tuple([(0,0,0,len(begins),len(finished),hit_count)]+
                    [(1,j,*na,*nb,*manifold) for j,(ra,rb,na,nb,manifold) in enumerate(begins)]+
                    [(2,j,*na,*nb) for j,(ra,rb,na,nb,manifold) in enumerate(finished)])
        ge={};copies={}
        for tag,dest in (('GE',ge),('GC',copies)):
            for value in rows[tag]:
                if value[3]!=0:continue
                dest.setdefault(value[2],[]).append(value[4:])
            for reg,value in tuple(dest.items()):dest[reg]=tuple(value)
        expected_worlds=worlds|({a[0]} if code==49 and status else set())
        require(set(ge)==expected_worlds,'GE includes each live world and explicit failed49 only')
        if private:
            for w,value in ge.items():
                wanted=expected_ge.get(w,((0,0,status,0,0,0),))
                require(value==wanted,'GE event-time numbers/manifolds and previous end side actual='+str(value[:1])+' expected='+str(wanted[:1]))
        for value in ge.values():
            for event in value[1:]:
                require(tuple(event[2:7]) in self.known_shapes and tuple(event[7:12]) in self.known_shapes,'GE known full historical shape lives')
        if code==49 and not status:
            self.saved_events[a[1]]=ge[a[0]]
            self.saved_event_owners[a[1]]=tuple(self.regs['W'][a[0]]['number'][1:3])
        require(set(copies)==set(self.saved_events),'GC all saved copies survive reads/refusals/world destruction')
        for reg,value in copies.items():require(value==self.saved_events[reg],'GC exact owned historical event copy')
        phases={(v[2],v[3]) for v in rows['GC']}
        wanted_phases={(slot,0) for slot in self.saved_events}
        if code==50 and a[1]:wanted_phases|={(a[0],1),(a[0],2)}
        require(phases==wanted_phases,'GC exact saved slots and mutation phases')
        for slot,phase in phases:
            wanted=list(self.saved_events[slot])
            if phase==1 and wanted[0][-1]:
                header=list(wanted[0]);header[-1]+=1;wanted[0]=tuple(header)
            if phase==1 and len(wanted)>1:
                first=list(wanted[1]);first[3]^=1
                if first[0]==1:first[12]^=0x80000000
                wanted[1]=tuple(first)
            require(tuple(v[4:] for v in rows['GC'] if v[2:4]==(slot,phase))==tuple(wanted),
                    'GC exact returned-copy mutation; fresh phase2 and other copies stay original')
        if code==50 and self.saved_event_owners[a[0]] not in {tuple(item['number'][1:3]) for item in self.regs['W'].values() if item['live']}:
            self.witnesses['event_copy_reads_after_world_death']+=1
        hc=index_rows(rows,'HC10',4);hg=index_rows(rows,'HG10',5)
        if code==49 and not status:
            values=[];owner=wide(self.regs['W'][a[0]]['number'][1:3])
            for hit in rows['HR10']:
                if hit[2]!=a[0]:continue
                raw=hit[4:];na=self.raw_shapes.get((owner,raw[:3]));nb=self.raw_shapes.get((owner,raw[3:6]))
                require(na is not None and nb is not None,'hit event-time full identity before copying')
                values.append((*na,*nb,*raw[6:]))
            self.saved_hits[a[1]]=tuple(values)
        expected_keys={(slot,0) for slot in self.saved_hits}
        if code==50 and a[1]:expected_keys|={(a[0],1),(a[0],2)}
        if code==49 and status:expected_keys.add((a[1],0))
        require(set(hc)==expected_keys,'HC10 exact all historical copy slots/phases')
        for (slot,phase),header in hc.items():
            if code==49 and status and slot==a[1]:
                require(header==(status,0),'failed49 Q-HC status without destroying the old saved copy');continue
            original=self.saved_hits[slot];wanted=list(original)
            if phase==1 and wanted:
                wanted.append(wanted[0])
                if len(original)>=2:wanted[0],wanted[1]=wanted[1],wanted[0]
                words=list(wanted[0]);words[1]^=1;words[10]^=0x80000000;wanted[0]=tuple(words)
            require(header==(0,len(wanted)),'HC10 saved hit count/status per phase')
            require(tuple(hg[slot,phase,j] for j in range(len(wanted)))==tuple(wanted),'HG10 immutable event-time numbers and exact copy mutation')

    def _finite_and_masks(self,rows,operation,status):
                                                                        
                                                                              
                                                                          
        for tag in ('W10','CX10','BV10','HR10','HG10','SC10'):
            d,_=m10.SCHEMA[tag]
            for value in rows[tag]:m10.finite_words(tag,(0,*value[1:d]),value[d:])
        packets=index_rows(rows,'PK10',6)
        groups=defaultdict(list)
        for (w,color,packet,lane),h in packets.items():
            require(color<=11,'packet color')
            groups[w,color,packet].append(lane)
            if h[0]==NULL:require(h[1:]==(NULL,NULL),'dummy packet initialized indices')
        for (w,color,packet),lanes in groups.items():require(lanes==([0] if color==11 else [0,1,2,3]),'packet exact lane completeness')
        for key,h in index_rows(rows,'SC10',8).items():
            w,sub,phase,color,packet,lane=key
            require((w,color,packet,lane) in packets and h[2:5]==packets[w,color,packet,lane],'SC actual packet/dense mapping')
            wanted=(1<<30)-1 if color==11 and h[5]==1 else (1<<41)-1
            require(wide(h[:2])==wanted,'SC exact defined mask')
        code,*a=operation
        if code in (31,32) and (status or number(a[1])<=0):
            require(not any(rows[t] for t in ('CX10','SB10','PK10','SC10','BV10')),'no stale solver trace after pause/refusal')

    def _atomic(self,rows,operation,status):
        if self.previous is None:return
        code,*a=operation
        no_op=False
        if status==0 and code==80:
            prior=next((v for v in self.previous['B'] if v[2]==a[1]),None)
            if prior is not None:
                if a[3] in (0,1,7):no_op=prior[{0:12,1:28,7:29}[a[3]]]==a[4]
                if a[3]==8 and a[2]==0:no_op=prior[12]==0 or number(a[8])<=0
        if status==0 and code==81 and a[3]==4:
            prior=next((v for v in self.previous['S'] if v[2]==a[1]),None)
            no_op=prior is not None and prior[26:31]==tuple(a[4:9])
        life_refusal=80<=code<=92 and status in (1,2)
        if status not in (3,4,5,7) and not no_op and not life_refusal:return
                                                                        
                                                                           
                                                                          
        ignored={'E','R','V','SB','NC9','RC9','GV','GL','AP12','VR12','I8','I9','I10','I11','I12','IP12',
                 'Z8','Z9','Z10','Z11','Z12','RQ','CX10','SB10','PK10','SC10','BV10','WS11','AB11','TR11',
                 'GS11','CL12','CV12','HC10','HG10','GC','K','M','MCN','MC','HT12'}
        def stable(source):
            return {tag:[v[2:] for v in values] for tag,values in source.items() if values and tag not in ignored}
        current,prior=stable(rows),stable(self.previous)
        for tag in sorted(set(current)|set(prior)):
            require(current.get(tag)==prior.get(tag),
                    'full refusal/no-op atomicity '+tag+' before='+str(prior.get(tag,[])[:1])[:512]+
                    ' after='+str(current.get(tag,[])[:1])[:512])


MODEL_GAPS = (
    'all status precedences and every new/legacy route, including complete 12b current-setting/material/name/flags semantics',
    'temporal LIFO/RemoveSwap beyond body IDs and opcode80: contact/island/solver-set/tree transitions, transient contact allocation/deletion inside one O',
    'filter query membership/tree order and zero-after-false-pre geometric membership; private Create/Update mixing schedule is checked independently',
    'complete shapeContacts88/K12/89 derivation from private links and all hit generation/cache-refresh predicates; full160 histories',
    'Named negative-dt/hertz0 diagnostics; full mutation-based model self-controls on matching port sources',
)
