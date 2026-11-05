pass                                                                      

                                                                            
                                                                  
   
import argparse
from collections import Counter,defaultdict,deque
import io
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys

from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=spec_from_file_location(name,HERE/file);m=module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('contact_inputs','przypadki-kontakty.py')
p8=load('contact_motion_compare','porownaj-ruch-swiata.py')
Invalid=ValueError
PRIVATE=p8.PRIVATE|frozenset('RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 TASK I9'.split())
SCHEMA={
 'PORT9B':(1,0),'NC9':(3,5),'RC9':(2,7),'CD':(6,None),'GV':(3,47),'GL':(5,None),
 'GE':(6,None),'GC':(6,None),'Z9':(2,16),'RQ':(4,9),'CP':(3,3),'CF':(4,1),'CT':(4,20),
 'CA':(5,1),'CS':(6,52),'GB':(4,None),'CB':(4,None),'BL9':(4,None),'IP':(3,3),'IF':(4,1),
 'IS':(4,15),'IL':(6,1),'EB':(4,36),'EE0':(4,6),'EE1':(4,6),'EN9':(3,5),'I9':(2,20),'TASK':(5,None),
}
PUBCOUNTS=('NC9','RC9','CD','GV','GL','GE','GC')
PRIVCOUNTS=tuple('RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 TASK'.split())
ORDER=[('E',),('R',),('UP',),('V',),('W',),('B',),('S',),('G',),('L','A','Q'),('QGN','QG'),('SB',),('K','M','MCN','MC'),('CD',),
       ('NC9',),('RC9',),('GV',),('GL',),('GE',),('GC',),('X',),('P',),('T',),('F','U','H'),('Y',),('DN',),('RT',),('JW',),
       *[(x,) for x in 'RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 I8 I9 Z8 Z9'.split()]]
RANK={tag:k for k,tags in enumerate(ORDER) for tag in tags}
NULL=g.U32

def require(condition,message):
    if not condition:raise Invalid(message)
def signed(x):return x-(1<<32) if x&(1<<31) else x
def wide(x):return x[0]|x[1]<<32
def name(tag,v,i):
    if tag=='CT' and i>=4:
        return ('alive','contactId','setIndex','colorIndex','localIndex','shapeIdA','shapeIdB','edgeA.bodyId','edgeA.prevKey','edgeA.nextKey',
                'edgeB.bodyId','edgeB.prevKey','edgeB.nextKey','islandId','islandPrev','islandNext','flags','isMarked','birth.low','birth.high')[i-4]
    if tag in ('CS','TASK'):
        d=SCHEMA[tag][0]+(3 if tag=='TASK' else 0)
        names=('contactId','bodySimIndexA','bodySimIndexB','shapeIdA','shapeIdB','invMassA','invIA','invMassB','invIB','friction','restitution','rollingResistance','tangentSpeed','simFlags')
        if d<=i<d+14:return names[i-d]
        if d+14<=i<d+21:return ('cache.count','cache.indexA[0]','cache.indexA[1]','cache.indexA[2]','cache.indexB[0]','cache.indexB[1]','cache.indexB[2]')[i-d-14]
        if d+21<=i<d+51:
            k=i-d-21
            if k<4:return ('normal.x','normal.y','rollingImpulse','pointCount')[k]
            return 'point'+str((k-4)//13)+'.'+('point.x','point.y','anchorA.x','anchorA.y','anchorB.x','anchorB.y','separation','normalImpulse','tangentImpulse','totalNormalImpulse','normalVelocity','id','persisted')[(k-4)%13]
    if tag in p8.FIELDS:return p8.names_for(tag,v)[i]
    return f'word[{i}]'

def context(tag,v):
    if tag=='CT':return {'worldRegister':v[2],'contactId':v[3],'colorIndex':signed(v[7]),'localIndex':signed(v[8])}
    if tag=='CS':return {'worldRegister':v[2],'domain':v[3],'index':v[4],'localIndex':v[5],'contactId':v[6]}
    if tag=='TASK':return {'worldRegister':v[2],'part':v[3],'j':v[4],**({'domain':v[5],'index':v[6],'localIndex':v[7],'contactId':v[8]} if v[3]==1 else {})}
    if tag in ('GV','GL'):return {'phase':v[2]}
    if tag in ('GE','GC'):return {'worldOrCopyRegister':v[2],'phase':v[3],'part':v[4],'j':v[5]}
    return {}
def parse_record(line):
    require(line.isascii() and line.endswith('\n') and '\r' not in line and len(line)<=131072,'output ASCII/LF/line length')
    ts=line[:-1].split(' ');tag=ts[0]
    if tag not in SCHEMA:return p8.parse_record(line)
    d,k=SCHEMA[tag];v=[]
    for i,t in enumerate(ts[1:]):
        require((g.g8.DEC if i<d else g.g8.HEX).fullmatch(t) is not None,f'{tag} canonical word {i}')
        x=int(t,10 if i<d else 16);require(x<=g.U32,f'{tag} u32');v.append(x)
    require(len(v)>=d,f'{tag} prefix')
    if k is None:
        h=v[d:]
        if tag=='CD':k=2 if v[4]==0 else 36 if v[4]==1 else -1
        elif tag=='GL':k=2 if v[3]==0 else 46 if v[3]==1 else -1
        elif tag in ('GE','GC'):k={0:4,1:40,2:10}.get(v[4],-1)
        elif tag=='GB':k=3+2*h[1] if len(h)>=3 else -1
        elif tag=='CB':k=2+2*h[0] if len(h)>=2 else -1
        elif tag=='BL9':k=5+2*h[1] if len(h)>=5 else -1
        elif tag=='TASK':k=(6+2*h[4] if len(h)>=6 else -1) if v[3]==0 else 55 if v[3]==1 else -1
    require(k>=0 and len(v)==d+k,f'{tag} arity {len(v)} != {d}+{k}')
    return tag,tuple(v)

def format_record(tag,v):
    d=SCHEMA[tag][0] if tag in SCHEMA else p8.DECIMALS[tag]
    return tag+' '+' '.join(str(x) if i<d else f'{x:08x}' for i,x in enumerate(v))+'\n'

def manifold(words,where):
    require(len(words)==30 and words[3]<=2,where+' pointCount')
    for j in (15,28):require(words[j]<=65535,where+' featureId')
    for j in (16,29):require(words[j]<=1,where+' persisted')
    for j,x in enumerate(words):
        if j not in (3,15,16,28,29):require(math.isfinite(g.number(x)),where+' nonfinite manifold')

def index_rows(rows,tag,prefix):
    result={}
    for v in rows[tag]:
        key=v[2:2+prefix];require(key not in result,f'{tag} duplicate {key}');result[key]=v[2+prefix:]
    require(list(result)==sorted(result),f'{tag} index order')
    return result

class Pool:
    def __init__(self):self.next=0;self.free=[];self.alive=set()
    def allocate(self):
        if self.free:i=self.free.pop()
        else:i=self.next;self.next+=1
        require(i not in self.alive,'pool allocate live');self.alive.add(i);return i
    def release(self,i):require(i in self.alive,'pool free dead');self.alive.remove(i);self.free.append(i)
    def check(self,header,free,slots):
        require(header==(self.next,len(self.free),len(self.alive)),'pool header/history')
        require(free==self.free,'pool LIFO/free order');require(set(slots)==set(range(self.next)),'pool missing sparse slot')
        require({k for k,v in slots.items() if v[0]}==self.alive,'pool live/free partition')

class Model:
    def __init__(self,guard=False):self.last=0;self.guard=guard;self.begin()
    def begin(self):
        self.previous=None;self.contact_pools={};self.public_contact_counts={};self.island_pools={};self.contact_regs={};self.copies={};self.worlds={};self.bodies={};self.shapes={};self.owner_meta={};self.phase=0;self.seeded={};self.events={};self.bitmeta={}
    def status(self,world,kind=None,reg=None):
        w=self.worlds[world]
        if not w['live']:return 1
        if kind:
            o={'B':self.bodies,'S':self.shapes,'C':self.contact_regs}[kind][reg]
            if o['owner']!=w['birth']:return 2
            if kind=='C':
                if not getattr(self,'private_mode',True):return None
                slot=o['slot'];pool=self.contact_pools.get(world,Pool())
                return 0 if slot in pool.alive and self.owner_meta.get((world,slot))==o['birth'] else 1
            return 0 if o['live'] else 1
        return 0
    def update_life(self,row,rows):
        code,*a=row;rr=rows['R'];statuses=[r[3] for r in rr];status=statuses[0]
        creations={0:('W',a[0],None),2:('B',a[0],a[1]),30:('B',a[0],a[1]),10:('S',a[0],a[1]),17:('S',a[0],a[1]),40:('S',a[0],a[1])}
        if code in creations and status==0:
            kind,reg,owner=creations[code];r=rr[0];birth=wide(r[12:14]);require(birth==self.last+1,'ticket issue once at allocation');self.last=birth
            o={'live':True,'birth':birth,'owner':0 if owner is None else self.worlds[owner]['birth'],'raw':r[5:8],'slot':r[5]-1}
            require(wide(r[10:12])==o['owner'],'object owner ticket')
            {'W':self.worlds,'B':self.bodies,'S':self.shapes}[kind][reg]=o
            if kind=='W':
                self.contact_pools[reg]=Pool();self.events[reg]={'begin':[],'end':[[],[]],'index':0}
                self.island_pools[reg]=Pool()
                self.bitmeta[reg]={'colors':[[1,1] for _ in range(11)],'changed':[0,16]}
            if kind=='B':
                o['world']=owner;o['type']=a[2]
                if o['type']!=0:o['initial_island']=self.island_pools[owner].allocate()
            if kind=='S':o['world']=owner;o['parent']=a[2];o['events']=bool(a[56]) if code==40 else False
        if code==16 and status==0:
                                                                                   
            for k,reg,kind in ((0,a[0],'B'),(1,a[1],'S')):
                r=rr[k];birth=wide(r[12:14]);require(birth==self.last+1,'pair ticket');self.last=birth
                o={'live':True,'birth':birth,'owner':self.worlds[a[2]]['birth'],'world':a[2],'raw':r[5:8],'slot':r[5]-1}
                if kind=='B':
                    o['type']=a[3];self.bodies[reg]=o
                    if o['type']!=0:o['initial_island']=self.island_pools[a[2]].allocate()
                else:o['parent']=a[0];o['events']=False;self.shapes[reg]=o
        if code==1 and status==0:
            self.worlds[a[0]]['live']=False
            for reg in (self.bodies,self.shapes):
                for o in reg.values():
                    if o['owner']==self.worlds[a[0]]['birth']:o['live']=False
        if code==3 and status==0:
            b=self.bodies[a[1]];b['live']=False
            for s in self.shapes.values():
                if s['owner']==b['owner'] and s['parent']==a[1]:s['live']=False
        if code in (11,18) and status==0:self.shapes[a[1]]['live']=False
                                                                       
        expected=None
        if code==46:
            expected=self.status(a[0],'S',a[1]);expected=expected or self.status(a[0],'S',a[2])
        elif code==47:expected=self.status(a[0],'C',a[1])
        elif code==48:expected=self.status(a[0],'B',a[1])
        elif code==49:expected=self.status(a[0])
        elif code==40:
            expected=self.status(a[1],'B',a[2])
            if not expected and a[58]:
                vals=[g.number(x) for x in a[45:49]]
                if not all(math.isfinite(x) and (j==3 or x>=0) for j,x in enumerate(vals)):expected=5
            if expected==0 and status in (3,4):expected=None                                                           
        elif code==32 and g.number(a[1])<0:expected=self.status(a[0]) or 5
        if expected is not None:require(status==expected,f'game status {code}: {status} != {expected}')
                                                                                
        for tag,reg in (('W',self.worlds),('B',self.bodies),('S',self.shapes)):
            emitted={v[2]:v for v in rows[tag]};require(set(emitted)=={i for i,o in reg.items() if o['live']},tag+' live completeness')
            for i,v in emitted.items():
                o=reg[i];require(v[3:6]==o['raw'],tag+' raw lifetime')
                if tag=='W':require(wide(v[8:10])==o['birth'],'world birth')
                else:require(wide(v[8:10])==o['owner'] and wide(v[10:12])==o['birth'],tag+' owner/birth')
        for v in rows['V']:
            kind,reg,raw,game=v[2:];objects={1:self.worlds,2:self.bodies,3:self.shapes};require(game==objects[kind][reg]['live'],'validity history')
        z=rows['Z8'][0]
        require(z[2:5]==tuple(len(x) for x in (self.worlds,self.bodies,self.shapes)),'Z8 saved')
        require(z[5:8]==tuple(sum(o['live'] for o in x.values()) for x in (self.worlds,self.bodies,self.shapes)),'Z8 live')
        return status
    def check(self,case,seq,row,observations,task,private=True):
        self.private_mode=private
        rows=defaultdict(list)
        previous_rank=-1
        for tag,v in observations:
            require(v[:2]==(case,seq),f'{tag} case/seq')
            rank=RANK[tag];require(rank>=previous_rank,f'{tag} group order');previous_rank=rank;rows[tag].append(v)
        require(len(rows['E'])==1 and rows['E'][0]==(case,seq,*row),'echo/operation')
        require(len(rows['R'])==(2 if row[0]==16 else 1),'result count')
        for j,r in enumerate(rows['R']):require(r[2]==j and r[3]<=6 and r[4]<=3,'R status/kind/index')
        for t in ('Z8','Z9'):require(len(rows[t])==1,t+' exactly one')
        status=self.update_life(row,rows);code,*a=row
        if code in (31,32) and self.previous:
            dt=g.number(a[1]);world_status=self.status(a[0])
            if not world_status and math.isfinite(dt) and dt!=0 and not (code==32 and dt<0):
                oldcontacts=len(self.contact_pools[a[0]].alive) if private else self.public_contact_counts.get(a[0],0)
                if oldcontacts:require(status==6,'nonzero raw/game Step with live contacts is unsupported')
            if status==6:
                require(len(rows['UP'])==1,'unsupported pair description')
                for tag in ('W','B','S','G','L','A','X','P','T','F','U','H','Y','DN','RT','JW','CP','CF','CT','CA','CS','GB','CB','BL9','IP','IF','IS','IL','EB','EE0','EE1','EN9'):
                    require([v[2:] for v in rows[tag]]==[v[2:] for v in self.previous[1][tag]],'Step refusal changed '+tag)
        counts=Counter(t for t,v in observations);counts['TASK']=len(task)
        require(rows['Z8'][0][8:26]==tuple(counts[t] for t in p8.PUBLIC_COUNTS),'Z8 public counters')
        z=rows['Z9'][0][2:]
        require(z[3:10]==tuple(counts[t] for t in PUBCOUNTS),'Z9 row counters')
        require(z[10:13]==(seq,seq,2 if self.guard else 1),'Z9 completed/profile')
        require(z[13]==int(self.guard or code in (51,52,53)),'Z9 fixture input')
        if private:
            require(len(rows['I8'])==len(rows['I9'])==1,'private counters missing')
            require(rows['I8'][0][2:]==tuple(counts[t] for t in ('X','P','T','F','U','H','Y','DN','RT','JW')),'I8 private counters')
            i9=rows['I9'][0][2:]
            require(i9[:18]==tuple(counts[t] for t in PRIVCOUNTS),'I9 counts')
            require(i9[18]==sum(v[3]==0 for t,v in task) and i9[19]==seq,'I9 task/completed')
            self.private(case,seq,row,rows,task,status)
            self.event_history(row,rows,task,status)
            self.contact_views(row,rows,status)
        else:
            require(not any(rows[t] for t in PRIVATE),'OBS0 private record')
            if code==42 and not status:
                before=0 if self.previous is None else self.previous[1]['Z9'][0][3]
                require(z[1]>=before,'PAIRS cannot destroy contacts');self.last+=z[1]-before
        self.public(case,seq,row,rows,status,private)
        if not private:
            delta=z[1]-sum(self.public_contact_counts.values())
            if delta:
                owner=a[2] if code==16 else a[1] if code in (2,30,10,17,40) else a[0]
                self.public_contact_counts[owner]=self.public_contact_counts.get(owner,0)+delta
                require(self.public_contact_counts[owner]>=0,'OBS0 per-world contact count')
        require(wide(z[14:16])==self.last and wide(rows['Z8'][0][-2:])==self.last,'lastIssued')
        self.previous=(row,rows,task)
    def private(self,case,seq,row,rows,task,status):
        code,*a=row
        cp=index_rows(rows,'CP',1);cf=index_rows(rows,'CF',2);ct=index_rows(rows,'CT',2)
        ca=index_rows(rows,'CA',3);cs=index_rows(rows,'CS',4);gb=index_rows(rows,'GB',2);cb=index_rows(rows,'CB',2)
        bl=index_rows(rows,'BL9',2);ip=index_rows(rows,'IP',1);ifs=index_rows(rows,'IF',2);islands=index_rows(rows,'IS',2)
        live_worlds={i for i,w in self.worlds.items() if w['live']}
        require({k[0] for k in cp}==live_worlds and {k[0] for k in ip}==live_worlds,'pool worlds')
        for owner in live_worlds:
            pool=self.contact_pools[owner];slots={k[1]:v for k,v in ct.items() if k[0]==owner}
            actual_alive={k for k,v in slots.items() if v[0]}
            oldalive=pool.alive.copy()
                                                                                 
            if code==42 and owner==a[0]:
                for j,r in enumerate(rows['RQ']):
                    require(r[2:4]==(owner,j),'RQ order/world');h=r[4:]
                    require(h[4]<=1 and h[5]<=1,'RQ bool')
                    if h[3]==NULL:require(h[4:]==(0,0,NULL,NULL,NULL),'unregistered pair allocation')
                    elif not status:
                        require(h[5]==1,'registered request not consumed');cid=pool.allocate();require(h[6]==cid,'request/LIFO contactId')
                        self.last+=1;self.owner_meta[owner,cid]=self.last
                        require(slots[cid][5:7]==h[7:9],'request canonical shapes')
            removed=pool.alive-actual_alive
            release=sorted(removed)
            if removed and code in (3,11,18) and self.previous:
                prior=self.previous[1]
                reg=a[1] if code==3 else self.shapes[a[1]]['parent'];bid=self.bodies[reg]['slot']
                previous_bl=next(v[4:] for v in prior['BL9'] if v[2:4]==(owner,bid))
                release=[previous_bl[j] for j in range(5,len(previous_bl),2) if previous_bl[j] in removed]
                require(set(release)==removed,'destroy edge release history')
            for cid in release:pool.release(cid)
            free=[v[0] for k,v in cf.items() if k[0]==owner]
            pool.check(cp[(owner,)],free,slots)
            if not (code==42 and owner==a[0]):require(actual_alive<=oldalive,'contact created outside PAIRS')
            sims={}
            for key,s in cs.items():
                if key[0]!=owner:continue
                _,domain,index,j=key;cid=s[0];require(cid not in sims,'duplicate contact sim');sims[cid]=(key,s)
                require(ca[(owner,domain,index)][0]>j,'CS outside count');require(s[51]<=1 and (s[51] or s[11]==0),'rollingDefined mask')
                require(s[14]<=3 and all(x<=255 for x in s[15:21]),'cache range');manifold(s[21:51],'CS')
            require(set(sims)==actual_alive,'one sim for every live contact')
            require(set(k[1:] for k in ca if k[0]==owner)=={(d,i) for d in range(2) for i in range(12 if d else 3)},'all 15 CA')
            for (o,d,i),v in ca.items():
                if o==owner:require([k[3] for k in cs if k[:3]==(o,d,i)]==list(range(v[0])),'CA/CS dense completeness')
            bodies={b['slot']:(r,b) for r,b in self.bodies.items() if b['live'] and b['world']==owner}
            used=defaultdict(set)
            for cid in actual_alive:
                c=slots[cid];require(c[1]==cid and c[2]==2 and c[17]==0,'CT identity/set/marked')
                require(wide(c[18:20])==self.owner_meta[owner,cid],'contact birth')
                key,s=sims[cid];touch=bool(c[16]&1);require(s[3:5]==c[5:7],'CT/CS shape')
                require((key[1],key[2],key[3])==(int(c[3]!=NULL),c[3] if c[3]!=NULL else c[2],c[4]),'CT localIndex reciprocity')
                require(touch==bool(s[13]&0x10000)==bool(s[24]),'touching/count/flags')
                require((c[13]!=NULL)==touch and (c[3]!=NULL)==touch,'island/graph touching membership')
                if not touch:continue
                color=c[3];require(color<12,'color range')
                for bid in (c[7],c[10]):
                    require(bid in bodies,'edge body lives');b=bodies[bid][1]
                    if b['type']==0:require(color!=0,'static color0');continue
                    if color<11:require(bid not in used[color],'color body conflict');used[color].add(bid)
                if code==43:
                    for side,bid,mi,ii,si in ((0,c[7],5,6,1),(1,c[10],7,8,2)):
                        reg,b=bodies[bid];y=next(v for v in rows['Y'] if v[2]==reg)
                        require(s[si]==(NULL if b['type']==0 else y[14]),'collide refresh bodySimIndex')
            for color in range(12):
                h=gb[(owner,color)]
                if color==11:require(h==(0,0,0),'overflow has no bitset');continue
                meta=self.bitmeta[owner]['colors'][color]
                needed=max(used[color],default=-1)//64+1
                if needed>meta[0]:
                    if needed>meta[1]:meta[1]=needed+needed//2
                    meta[0]=needed
                require(h[:3]==(1,*meta),'bodySet exact logical count/capacity history')
                bits_={64*j+k for j in range(h[1]) for k in range(64) if wide(h[3+2*j:5+2*j])>>k&1}
                require(bits_==used[color],'bodySet exact occupancy')
            require(set(k[1] for k in bl if k[0]==owner)==set(bodies),'BL9 live bodies')
            for bid in bodies:
                h=bl[(owner,bid)];key=h[0];seen=[];prev=NULL
                while key!=NULL:
                    cid,e=key>>1,key&1;require(cid in actual_alive and key not in seen,'edge missing/cycle');seen.append(key);c=slots[cid];k=7+3*e
                    require(c[k]==bid and c[k+1]==prev,'edge prev/body');prev=key;key=c[k+2]
                require(h[1]==len(seen) and h[5:]==tuple(x for key_ in seen for x in (key_>>1,key_&1)),'edge list order/count')
                require(set(x>>1 for x in seen)=={cid for cid in actual_alive if bid in (slots[cid][7],slots[cid][10])},'edge completeness')
                                                                           
            pair=next(v for v in rows['H'] if v[2:4]==(owner,1));items=pair[6:];keys={wide(items[j:j+2]) for j in range(0,len(items),3) if items[j+2]}
            expected={(min(c[5],c[6])<<32)|max(c[5],c[6]) for c in slots.values() if c[0]}
            require(keys==expected and pair[5]==len(expected),'pairSet contacts')
            self.islands(owner,row,rows,bl,slots,islands,ip,ifs,status)
                                                                                  
            if code==51 and owner==a[0] and not status:
                n=self.contact_regs[a[1]];s=sims[n['slot']][1];require(s[21:51]==tuple(a[2:32]) and s[14:21]==tuple(a[32:39]),'fixture seed exact words')
            if code==43 and owner==a[0]:self.transfers(owner,rows,task,slots,sims)
            changed=self.bitmeta[owner]['changed']
            before=next((v[5] for v in self.previous[1]['CP'] if v[2]==owner),0) if self.previous else 0
            if code==43 and owner==a[0] and before:
                count=(pool.next+63)//64
                if changed[1]<count:changed[1]=(pool.next+(pool.next>>1)+63)//64
                changed[0]=count
                header=task[0][1][5:]
                require(cb[(owner,0)]==header[4:],'CB retains actual TASK bitset')
            else:
                oldcb=next((v[4:] for v in self.previous[1]['CB'] if v[2]==owner),None) if self.previous else None
                if oldcb is not None:require(cb[(owner,0)]==oldcb,'CB unchanged outside nonempty Collide')
            require(cb[(owner,0)][:2]==tuple(changed),'CB logical count/capacity history')
        before_contacts=0
        if code==43 and self.previous:
            before_contacts=sum(v[5] for v in self.previous[1]['CP'] if v[2]==a[0])
        require(bool(task)==(code==43 and bool(before_contacts)),'TASK presence from pre-operation contact count')
        if task:
            require(all(v[:3]==(case,seq,a[0]) for t,v in task),'TASK case/seq/world')
            require(task[0][1][3:5]==(0,0),'TASK header first');h=task[0][1][5:];require(h[0:2]==(0,0) and h[2]==h[3] and len(task)==h[3]+1,'TASK range/count')
            for j,(tag,v) in enumerate(task[1:]):require(v[3:5]==(1,j),'TASK sim order');manifold(v[29:59],'TASK')
            prior=[v for v in self.previous[1]['CS'] if v[2]==a[0]]
            gather=sorted(prior,key=lambda v:(0 if v[3] else 1,v[4],v[5]))
            require([v[5:9] for t,v in task[1:]]==[v[3:7] for v in gather],'TASK graph colors then nonTouching dense order')
    def islands(self,owner,row,rows,bl,ct,islands,ip,ifs,status):
        code,*a=row
        slots={k[1]:v for k,v in islands.items() if k[0]==owner};head=ip[(owner,)];free=[v[0] for k,v in ifs.items() if k[0]==owner]
        pool=self.island_pools[owner]
        if self.previous and not status and code in (3,44) and owner==a[0]:
            old=self.previous[1];oldslots={v[3]:v[4:] for v in old['IS'] if v[2]==owner}
            if code==44:
                dense=[v[6] for v in old['IL'] if v[2:5]==(owner,0,2)]
                for ident in reversed(dense):
                    if oldslots[ident][13]!=NULL:pool.release(ident)
            else:
                bid=self.bodies[a[1]]['slot'];island=next(v[6] for v in old['BL9'] if v[2:4]==(owner,bid))
                if island!=NULL and oldslots[island][6]==1:pool.release(island)
        pool.check(head,free,slots)
        require(set(slots)==set(range(head[0])) and len(set(free))==head[1] and len(free)==head[1],'island pool completeness')
        live={i for i,v in slots.items() if v[0]};require(live==set(range(head[0]))-set(free) and len(live)==head[2],'island pool partition')
        il=defaultdict(list)
        for v in rows['IL']:
            if v[2]==owner:require(v[5]==len(il[v[3:5]]),'IL dense j');il[v[3:5]].append(v[6])
        mapped=[]
        for s in range(3):
            for j,i in enumerate(il[0,s]):require(i in live and slots[i][1:4]==(s,j,i),'islandSim reciprocity');mapped.append(i)
        require(set(mapped)==live and len(mapped)==len(live),'island sims completeness')
        body_seen=[];contact_seen=[]
        for i in live:
            h=slots[i];require(h[10:13]==(NULL,NULL,0),'joints empty')
            path={i};parent=h[13]
            while parent!=NULL:require(parent in live and parent not in path,'parent cycle/dead');path.add(parent);parent=slots[parent][13]
            for kind,start,tail,count,source,prevfield,nextfield in ((1,h[4],h[5],h[6],{k[1]:v for k,v in bl.items() if k[0]==owner},3,4),
                                                                   (2,h[7],h[8],h[9],ct,14,15)):
                seen=[];n=start;prev=NULL
                while n!=NULL:
                    require(n in source and n not in seen,'island list missing/cycle');h_=source[n];require(h_[prevfield]==prev,'island prev')
                    require(h_[2 if kind==1 else 13]==i,'island member remap')
                    seen.append(n);prev=n;n=h_[nextfield]
                require(len(seen)==count and (seen[-1] if seen else NULL)==tail and il[kind,i]==seen,'island head/tail/count/order')
                if kind==1:body_seen+=seen
                else:contact_seen+=seen
        require(len(set(body_seen))==len(body_seen),'body belongs to two islands');require(len(set(contact_seen))==len(contact_seen),'contact belongs to two islands')
        require(set(body_seen)=={b['slot'] for b in self.bodies.values() if b['live'] and b['world']==owner and b['type']!=0},'island body completeness')
        require(set(contact_seen)=={i for i,c in ct.items() if c[0] and c[16]&1},'island touching completeness')
    def transfers(self,owner,rows,task,ct,sims):
        if not self.previous:return
        _,oldrows,_=self.previous;oldcs={v[2:3]+v[6:7]:v[6:] for v in oldrows['CS']}
        for cid,(key,s) in sims.items():
            old=oldcs.get((owner,cid))
            if old is None:continue
            task_s=next((v[8:] for t,v in task if v[3]==1 and v[8]==cid),None)
                                                                            
            if task_s is not None and not task_s[13]&0x20000:
                shape_rows={v[3]-1:v for v in rows['S'] if self.shapes[v[2]]['world']==owner}
                ga={v[2]:v[3:] for v in rows['G']}
                aa,bb=(shape_rows[s[j]] for j in (3,4))
                f=g.g8.g7.w6.f32
                product=f(g.number(aa[20])*g.number(bb[20]))
                friction=g.bits(f(math.sqrt(product)))
                maximum=lambda x,y:x if g.number(x)>g.number(y) else y
                rest=maximum(aa[21],bb[21])
                roll=0
                if g.number(aa[22])>0 or g.number(bb[22])>0:
                    radius=maximum(ga[aa[2]][2],ga[bb[2]][2])
                    roll=g.bits(f(g.number(maximum(aa[22],bb[22]))*g.number(radius)))
                tangent=g.bits(f(g.number(aa[23])+g.number(bb[23])))
                require(s[9:13]==(friction,rest,roll,tangent),'f32 material refresh from shape properties/radii')
                                                                                         
            require(s[14:21]==old[14:21],'ordinary cache preservation')
            m=s[21:51];om=old[21:51]
            remaining=[list(om[4+13*q:17+13*q]) for q in range(om[3])]
            for j in range(m[3]):
                k=4+13*j;matches=[q for q in range(om[3]) if om[15+13*q]==m[k+11]]
                want=tuple(remaining[matches[0]][7:9]) if matches else (0,0)
                if matches:remaining[matches[0]][7:9]=[0,0]
                require(m[k+7:k+9]==want and m[k+9:k+11]==(0,0) and m[k+12]==bool(matches),'warm start by first id/reset/persisted')
            require(m[2]==(om[2] if m[3] else 0),'rollingImpulse transfer')
    def shape_value(self,owner,slot):
        birth=self.worlds[owner]['birth'];found=[o for o in self.shapes.values() if o['owner']==birth and o['slot']==slot]
        require(bool(found),'shape ticket for event/contact');o=max(found,key=lambda x:x['birth'])
        return (slot,o['birth']&NULL,o['birth']>>32,birth&NULL,birth>>32),o['raw']
    def event_history(self,row,rows,task,status):
        code,*a=row;previous=defaultdict(list) if self.previous is None else self.previous[1]
        for owner,w in self.worlds.items():
            if not w['live']:continue
            state=self.events[owner]
            if (code==41 or code in (31,32) and not status and g.number(a[1])==0) and owner==a[0]:state['begin']=[]
            oldct={v[3]:v[4:] for v in previous['CT'] if v[2]==owner and v[4]}
            def append(c,m=None,begin=False):
                na,ra=self.shape_value(owner,c[5]);nb,rb=self.shape_value(owner,c[6]);value=(ra,rb,na,nb,tuple(m) if m is not None else ())
                if begin:state['begin'].append(value)
                else:state['end'][state['index']].append(value)
            if code==43 and owner==a[0]:
                ts={v[8]:v[8:] for tag,v in task if v[3]==1}
                if task:
                    h=task[0][1][5:];bits_=sum(wide(h[6+2*j:8+2*j])<<(64*j) for j in range(h[4]))
                    expected=sum(1<<cid for cid,s in ts.items() if s[13]&0xe0000)
                    require(bits_==expected,'TASK changed bits match disjoint/start/stop flags')
                for cid,s in sorted(ts.items()):
                    c=oldct[cid];flags=s[13]
                    if flags&0x20000:
                        if c[16]&5==5:append(c)
                    elif flags&0x40000:
                        if c[16]&4:append(c,s[21:51],True)
                    elif flags&0x80000:
                        if c[16]&4:append(c)
            elif code in (3,11,18,53) and not status and owner==a[0]:
                now={v[3] for v in rows['CT'] if v[2]==owner and v[4]};removed=set(oldct)-now
                if code==53:order=[self.contact_regs[a[1]]['slot']]
                else:
                    reg=a[1] if code==3 else self.shapes[a[1]]['parent'];bid=self.bodies[reg]['slot']
                    h=next(v[4:] for v in previous['BL9'] if v[2:4]==(owner,bid));order=[h[j] for j in range(5,len(h),2)]
                for cid in order:
                    if cid in removed and oldct[cid][16]&5==5:append(oldct[cid])
            if (code==45 or code in (31,32) and not status and g.number(a[1])==0) and owner==a[0]:state['index']=1-state['index'];state['end'][state['index']]=[]
            require([v[4:] for v in rows['EB'] if v[2]==owner]==[(*ra,*rb,*m) for ra,rb,na,nb,m in state['begin']],'raw begin emission order/manifold')
            for side in (0,1):require([v[4:] for v in rows['EE'+str(side)] if v[2]==owner]==[(*ra,*rb) for ra,rb,na,nb,m in state['end'][side]],'raw end history/order/side')
            en=[v[3:] for v in rows['EN9'] if v[2]==owner]
            require(en==[(len(state['begin']),len(state['end'][0]),len(state['end'][1]),state['index'],0)],'end buffer counts/index')
    def contact_views(self,row,rows,status):
        code,*a=row;ct={(v[2],v[3]):v[4:] for v in rows['CT'] if v[4]};cs={(v[2],v[6]):v[6:] for v in rows['CS']}
        def value(owner,cid):
            c=ct[owner,cid];birth=self.owner_meta[owner,cid];wb=self.worlds[owner]['birth'];na,_=self.shape_value(owner,c[5]);nb,_=self.shape_value(owner,c[6])
            return (cid,birth&NULL,birth>>32,wb&NULL,wb>>32,*na,*nb,int(bool(c[16]&1)),*cs[owner,cid][21:51])
        seen=set()
        for v in rows['CD']:
            owner,bid,part,j=v[2:6]
            if part!=0:continue
            require(j==0 and (owner,bid) not in seen,'CD duplicate header');seen.add((owner,bid))
            bl=next(b[4:] for b in rows['BL9'] if b[2:4]==(owner,bid));touch=[bl[k] for k in range(5,len(bl),2) if ct[owner,bl[k]][16]&1]
            require(v[6:]==(bl[1],len(touch)),'CD capacity/touching count')
            actual=[x for x in rows['CD'] if x[2:5]==(owner,bid,1)]
            expected=[]
            for k,cid in enumerate(touch):
                c=ct[owner,cid];_,ra=self.shape_value(owner,c[5]);_,rb=self.shape_value(owner,c[6]);expected.append((v[0],v[1],owner,bid,1,k,*ra,*rb,*cs[owner,cid][21:51]))
            require(actual==expected,'public contact data uses touching edge order/cached manifold')
        require(seen=={(b['world'],b['slot']) for b in self.bodies.values() if b['live']},'CD every live body')
        if code==47 and not status:
            n=self.contact_regs[a[1]];wanted=value(a[0],n['slot']);actual=[v for v in rows['GV'] if v[2]==0]
            require(len(actual)==1 and actual[0][3:]==(0,*wanted),'lookup number/shapes/cached manifold')
        if code==48 and not status:
            bid=self.bodies[a[1]]['slot'];bl=next(v[4:] for v in rows['BL9'] if v[2:4]==(a[0],bid));touch=[bl[k] for k in range(5,len(bl),2) if ct[a[0],bl[k]][16]&1]
            header=[v for v in rows['GL'] if v[2:5]==(0,0,0)];require(len(header)==1 and header[0][5:]==(0,len(touch)),'GL header')
            require([v[5:] for v in rows['GL'] if v[2:4]==(0,1)]==[value(a[0],cid) for cid in touch],'game list contact numbers/order/value')
    def public(self,case,seq,row,rows,status,private):
        code,*a=row
        nc=index_rows(rows,'NC9',1)
        if code==46 and status==0:
            rc=rows['RC9'][0];n=rc[4:9]
            if private:
                sa=self.shapes[a[1]]['slot'];sb=self.shapes[a[2]]['slot']
                matches=[v for v in rows['CT'] if v[2]==a[0] and v[4] and {v[9],v[10]}=={sa,sb} and sa!=sb]
                require(len(matches)<=1 and rc[3]==bool(matches),'find contact pair/has')
                if matches:
                    v=matches[0];wb=self.worlds[a[0]]['birth']
                    require(n==(v[3],v[22],v[23],wb&NULL,wb>>32),'find contact number')
                else:require(n==(NULL,0,0,0,0),'find missing contact empty number')
            self.contact_regs[a[3]]={'slot':signed(n[0]),'birth':wide(n[1:3]),'owner':wide(n[3:5])}
        require(set(k[0] for k in nc)==set(self.contact_regs),'NC9 saved completeness')
        for (i,),n in nc.items():
            o=self.contact_regs[i];require(n==(o['slot']&NULL,o['birth']&NULL,o['birth']>>32,o['owner']&NULL,o['owner']>>32),'NC9 historical number')
        require(len(rows['RC9'])==int(code in (46,47)),'RC9 presence')
        if code in (46,47):
            rc=rows['RC9'][0];require(rc[2]==status and rc[3]<=1,'RC9 status')
            if status and code==46:require(rc[3:]==(0,NULL,0,0,0,0),'46 refusal empty value')
            if code==47:require(rc[4:9]==nc[(a[1],)],'47 echoes historical number')
            require(bool(rows['GV'])==(code==47 and not status),'GV presence')
        for tag in ('GV','GL','GC'):
            grouped=defaultdict(list)
            for v in rows[tag]:grouped[v[2] if tag=='GC' else 0].append(v)
            for values in grouped.values():
                phase_index=3 if tag=='GC' else 2;phases=sorted({v[phase_index] for v in values})
                require(phases in ([0],[0,1,2]),tag+' phases')
                if phases==[0,1,2]:
                    def normalized(phase):return [v[:phase_index]+v[phase_index+1:] for v in values if v[phase_index]==phase]
                    require(normalized(0)==normalized(2),tag+' owned copies')
                    nonempty=tag=='GV' or len(normalized(0))>1
                    if nonempty:require(normalized(0)!=normalized(1),tag+' mutation witness is not empty')
        ge={};gc={}
        for tag,dest in (('GE',ge),('GC',gc)):
            grouped=defaultdict(list)
            for v in rows[tag]:
                if v[3]==0:grouped[v[2]].append(v)
            for reg,values in grouped.items():
                head=values[0];require(head[4:6]==(0,0) and head[9]==0,tag+' header/hit')
                require(len(values)==1+head[7]+head[8],tag+' event count')
                require([(v[4],v[5]) for v in values[1:]]==[(1,j) for j in range(head[7])]+[(2,j) for j in range(head[8])],tag+' order')
                dest[reg]=tuple(v[4:] for v in values)
        if private:
            expected_worlds={i for i,w in self.worlds.items() if w['live']}|({a[0]} if code==49 and status else set())
            require(set(ge)==expected_worlds,'GE world completeness')
            for owner,values in ge.items():
                if not self.worlds[owner]['live']:require(values==((0,0,1,0,0,0),),'GE stale refusal');continue
                e=self.events[owner];begins=e['begin'];ends=e['end'][1-e['index']]
                want=[(0,0,0,len(begins),len(ends),0)]
                want += [(1,j,*na,*nb,*m) for j,(ra,rb,na,nb,m) in enumerate(begins)]
                want += [(2,j,*na,*nb) for j,(ra,rb,na,nb,m) in enumerate(ends)]
                require(values==tuple(want),'historical event numbers/manifold and previous end side')
        require(set(gc)==set(self.copies)|({a[1]} if code==49 and not status else set()),'GC saved completeness')
        if code==49 and not status:self.copies[a[1]]=ge[a[0]]
        for k,value in gc.items():require(value==self.copies[k],'event copies retained after mutations/destroy')
        z=rows['Z9'][0][2:];require(z[0]==len(nc) and z[2]==len(gc),'Z9 saved contacts/copies')
        require(sum(v[6] for v in rows['CD'] if v[4]==0)==2*z[1],'public contact capacities cover every contact twice')
        if private:require(z[1]==sum(v[5] for v in rows['CP']),'Z9 live contacts')

def validate_output(source,rows,private=True,guard=False,seed_last=None):
    stream=io.StringIO(source) if isinstance(source,str) else source;counts=Counter();model=Model(guard)
    def take(tag):
        line=stream.readline(131073);require(bool(line),'truncated '+tag);actual,v=parse_record(line);require(actual==tag,'expected '+tag+', got '+actual);counts[tag]+=1;return v
    require(take('PORT9B')==(len(rows),),'header N')
    for c in rows:
        model.begin();require(take('CASE')==(c.id,len(c.ops)),'CASE input')
        for seq,row in enumerate(c.ops,1):
            if seed_last and seq in seed_last:model.last=seed_last[seq]
            observations=[];task=[]
            while True:
                line=stream.readline(131073);require(bool(line),'truncated snapshot');tag,v=parse_record(line);counts[tag]+=1
                if tag=='TASK':require(not observations,'TASK before E');task.append((tag,v));continue
                require(tag in RANK,'unexpected snapshot '+tag);observations.append((tag,v))
                if tag=='Z9':break
            try:model.check(c.id,seq,row,observations,task,private)
            except (ValueError,KeyError,IndexError) as exc:raise Invalid(f'id {c.id}, seq {seq}, opcode {row[0]}: {exc}') from exc
        require(take('ENDCASE')==(c.id,),'ENDCASE')
    require(take('END')==(len(rows),),'END N');require(not stream.read(1),'trailing output');return counts

def projection(source):
    for line in source:
        tag,v=parse_record(line)
        if tag not in PRIVATE:yield line

def first_difference(left,right,project=False):
    for lineno,(a,b) in enumerate(zip_longest(projection(left) if project else left,right),1):
        if a==b:continue
        if a is None or b is None:return {'line':lineno,'error':'missing/excess row','left':a,'right':b}
        ta,va=parse_record(a);tb,vb=parse_record(b)
        if ta!=tb:return {'line':lineno,'tag':ta,'other_tag':tb,'left':a[:8192],'right':b[:8192]}
        for i,(x,y) in enumerate(zip(va,vb)):
            if x!=y:return {'line':lineno,'case':va[0],'seq':va[1] if len(va)>1 else 0,'tag':ta,**context(ta,va),'field':name(ta,va,i),'C':f'{x:08x}','Duckling':f'{y:08x}','left':a[:8192],'right':b[:8192]}
        return {'line':lineno,'error':'different length','left':a[:8192],'right':b[:8192]}
    return None

def compare_files(c,d,c0,rows,codes=(0,0,0),guard=False):
    errors=[];streams={}
    for label,path,code,private in zip(('C OBS1','Duckling','C OBS0'),(c,d,c0),codes,(True,True,False)):
        if code:errors.append(label+f' exit {code}')
        try:
            with Path(path).open(encoding='ascii',newline='') as inp:counts=validate_output(inp,rows,private,guard)
            streams[label]={'records':dict(counts),'bytes':Path(path).stat().st_size}
        except (ValueError,OSError) as exc:errors.append(label+': '+str(exc))
    difference=None
    for left,right,project in ((c,d,False),(c,c0,True)):
        try:
            with Path(left).open(encoding='ascii',newline='') as a,Path(right).open(encoding='ascii',newline='') as b:diff=first_difference(a,b,project)
            if diff:errors.append(diff);difference=difference or diff
        except (ValueError,OSError) as exc:errors.append(str(exc))
    return {'profile':'GUARD9' if guard else 'COMPONENT_A9','N':len(rows),'errors':errors,'first_difference':difference,'streams':streams}

def main():
    parser=argparse.ArgumentParser()
    for x in ('c','duckling','c-bez','raport'):parser.add_argument('--'+x,type=Path,required=True)
    parser.add_argument('--N',type=int,default=64)
    for x in ('kod-c','kod-duckling','kod-c-bez'):parser.add_argument('--'+x,type=int,required=True)
    args=parser.parse_args();result=compare_files(args.c,args.duckling,args.c_bez,g.cases()[:args.N],(args.kod_c,args.kod_duckling,args.kod_c_bez))
    args.raport.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False));return int(bool(result['errors']))
if __name__=='__main__':sys.exit(main())
