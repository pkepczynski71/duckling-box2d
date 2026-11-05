pass                                                                       

                                                                          
                                                                          
   
from collections import Counter, defaultdict
import importlib.util
import math
from pathlib import Path
import re
import struct
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('solver_model_legacy',HERE/'porownaj-kontakty.py')
legacy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=legacy;spec.loader.exec_module(legacy)
SCHEMA={
    'PORT10':(1,0),'GUARD10':(1,0),'COMPONENT10':(1,0),'G':(4,0),'GA':(1,64),'GR10':(3,4),
    'W10':(3,8),'CX10':(3,14),'HN10':(3,1),'HR10':(4,11),'HC10':(4,2),'HG10':(5,15),
    'SB10':(6,4),'PK10':(6,3),'SC10':(8,43),'BV10':(6,7),'I10':(2,6),'Z10':(2,5),
    'F':(8,0),'FW':(1,9),'FB':(2,17),'FC':(4,51),'FX':(3,16),'FP':(4,0),
    'FH10':(4,1),'FM10':(2,30),'FI10':(1,7),
}
HEX=re.compile('[0-9a-f]{8}');DEC=re.compile('0|[1-9][0-9]*')
NULL=0xffffffff


def require(condition, message):
    if not condition:raise ValueError(message)


def f32(value):
    try:return struct.unpack('<f',struct.pack('<f',value))[0]
    except OverflowError:return math.copysign(math.inf,value)


def number(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def bits(value):return struct.unpack('<I',struct.pack('<f',f32(value)))[0]
def add(a,b):return f32(f32(a)+f32(b))
def mul(a,b):return f32(f32(a)*f32(b))


def div(a,b):
    a,b=f32(a),f32(b)
    if b==0:
        if a==0:return math.nan
        return math.copysign(math.inf,math.copysign(1,a)*math.copysign(1,b))
    return f32(a/b)


def block_plan(count, packets=False):
    require(type(count) is int and 0<=count<=0x7fffffffffffffff,'nonnegative i64 block count')
    threshold,minimum=(16,4) if packets else (128,32)
    if count==0:return 0,minimum,()
    base=count//4 if count>threshold else minimum
    blocks=4 if count>threshold else (count+minimum-1)//minimum
    return blocks,base,tuple((j*base, count-j*base if j==blocks-1 else base) for j in range(blocks))


def body_fit(count):return all(1<=width<=32767 for start,width in block_plan(count)[2])
def contact_fit(count):return count>=0 and count//4+3<=32767
def checked_sum(a,b):
    require(0<=a<=0x7fffffffffffffff and 0<=b<=0x7fffffffffffffff,'checked checksum input')
    return None if b>0x7fffffffffffffff-a else a+b


def valid_step(dt,count):
    if not math.isfinite(dt) or dt<0 or count<=0:return False
    if dt==0:return True
    inv=div(1,dt);h=div(dt,f32(count));inv_h=mul(f32(count),inv)
    return h>0 and all(map(math.isfinite,(inv,h,inv_h)))


def parse(line):
    require(line.isascii() and line.endswith('\n') and '\r' not in line,'canonical ASCII/LF output')
    words=line[:-1].split(' ');tag=words[0]
                                                                          
    if tag=='G' and len(words)==44:return legacy.parse_record(line)
                                                                   
                                                                             
    if tag=='F' and len(words)==9 and all(HEX.fullmatch(w) for w in words[4:]):return legacy.parse_record(line)
    if tag not in SCHEMA:return legacy.parse_record(line)
    d,k=SCHEMA[tag];require(len(words)==1+d+k,tag+' arity')
    values=[]
    for j,word in enumerate(words[1:]):
        require((DEC if j<d else HEX).fullmatch(word) is not None,tag+' canonical word')
        value=int(word,10 if j<d else 16);require(value<=NULL,tag+' u32');values.append(value)
    return tag,tuple(values)


def format_record(tag,values):
    if tag=='G' and len(values)==43:return legacy.format_record(tag,values)
    if tag not in SCHEMA:return legacy.format_record(tag,values)
    d,k=SCHEMA[tag];require(len(values)==d+k,tag+' output arity')
    return tag+' '+' '.join(str(x) if j<d else f'{x:08x}' for j,x in enumerate(values))+'\n'


def finite_words(tag, prefix, payload, allow_contact_speed_inf=False):
    if tag=='W10':indices=range(6)
    elif tag=='CX10':indices=(*range(4),*range(5,13))
    elif tag=='BV10':indices=range(7)
    elif tag=='HR10':indices=range(6,11)
    elif tag=='HG10':indices=range(10,15)
    elif tag=='SC10':
        mask=payload[0]|payload[1]<<32
        require(mask>>41==0,'SC10 extraneous defined bits')
        for j in range(41):
            if not (mask>>j)&1:require(payload[j+2]==0,'SC10 nonzero undefined field')
        indices=tuple(j+2 for j in range(4,41) if (mask>>j)&1)
    else:return
    for j in indices:
        word=payload[j]
        if tag=='W10' and j==5 and (prefix[0] in (117,120) or allow_contact_speed_inf) and word==0x7f800000:continue
        require(math.isfinite(number(word)),f'{tag} illegal nonfinite h{j}')


def indexed(rows,tag):
    d,k=SCHEMA[tag];result={}
    for value in rows.get(tag,()):
        key=value[2:d]
        require(key not in result,tag+' duplicate prefix')
        result[key]=value[d:]
    require(list(result)==sorted(result),tag+' index order')
    return result


def pool_partition(header,free,slots,label):
    next_index,free_count,live_count=header
    require(set(slots)==set(range(next_index)),label+' complete sparse slots')
    require(len(free)==free_count and len(set(free))==len(free),label+' free count/uniqueness')
    alive={index for index,value in slots.items() if value[0]}
    require(alive==set(range(next_index))-set(free) and len(alive)==live_count,label+' live/free partition')


def ownership_links(owner,rows,contacts,islands,body_types,occupied):
    pass                                                                         
    bl={key[1]:value for key,value in legacy.index_rows(rows,'BL9',2).items() if key[0]==owner}
    require(set(bl)==set(body_types),'body edge header completeness')
    for bid,h in bl.items():
        key=h[0];previous=NULL;seen=[]
        while key!=NULL:
            cid,side=key>>1,key&1;require(cid in contacts and key not in seen,'body edge cycle/dead contact')
            c=contacts[cid];index=7+3*side
            require(c[index]==bid and c[index+1]==previous,'body edge previous/owner')
            seen.append(key);previous=key;key=c[index+2]
        require(h[1]==len(seen) and h[5:]==tuple(x for edge in seen for x in (edge>>1,edge&1)),'body edge count/order')
        require({edge>>1 for edge in seen}=={cid for cid,c in contacts.items() if bid in (c[7],c[10])},'body edge completeness')
    gb=legacy.index_rows(rows,'GB',2)
    require({key[1] for key in gb if key[0]==owner}==set(range(12)),'all graph colors observed')
    for color in range(12):
        h=gb[owner,color]
        if color==11:require(h==(0,0,0),'overflow bitset absent');continue
        require(h[0]==1 and h[1]<=h[2] and len(h)==3+2*h[1],'ordinary color bitset framing')
        bits_={64*j+k for j in range(h[1]) for k in range(64) if legacy.wide(h[3+2*j:5+2*j])>>k&1}
        require(bits_==occupied[color],'graph occupancy equals actual nonstatic bodies')
    pair=next((v for v in rows.get('H',()) if v[2:4]==(owner,1)),None)
    require(pair is not None,'pairSet header present')
    items=pair[6:];keys={legacy.wide(items[j:j+2]) for j in range(0,len(items),3) if items[j+2]}
    expected={(min(c[5],c[6])<<32)|max(c[5],c[6]) for c in contacts.values()}
    require(keys==expected and pair[5]==len(expected),'pairSet/current contact ownership')
    live={key[1]:value for key,value in islands.items() if key[0]==owner and value[0]}
    il=defaultdict(list)
    for v in rows.get('IL',()):
        if v[2]!=owner:continue
        require(v[5]==len(il[v[3:5]]),'island dense list order');il[v[3:5]].append(v[6])
    mapped=[]
    for set_index in range(3):
        for j,ident in enumerate(il[0,set_index]):
            require(ident in live and live[ident][1:4]==(set_index,j,ident),'island sim/local reciprocity');mapped.append(ident)
    require(len(mapped)==len(live) and set(mapped)==set(live),'island sim completeness')
    body_seen=[];contact_seen=[]
    for ident,h in live.items():
        require(h[10:13]==(NULL,NULL,0),'no step10 joints')
        path={ident};parent=h[13]
        while parent!=NULL:
            require(parent in live and parent not in path,'island parent cycle/dead');path.add(parent);parent=live[parent][13]
        for kind,start,tail,count,source,prev_field,next_field,owner_field in (
            (1,h[4],h[5],h[6],bl,3,4,2),(2,h[7],h[8],h[9],contacts,14,15,13)):
            seen=[];index=start;previous=NULL
            while index!=NULL:
                require(index in source and index not in seen,'island member cycle/dead')
                value=source[index];require(value[prev_field]==previous and value[owner_field]==ident,'island member previous/owner')
                seen.append(index);previous=index;index=value[next_field]
            require(len(seen)==count and (seen[-1] if seen else NULL)==tail and il[kind,ident]==seen,'island head/tail/count/list')
            if kind==1:body_seen+=seen
            else:contact_seen+=seen
    require(len(set(body_seen))==len(body_seen) and set(body_seen)=={bid for bid,kind in body_types.items() if kind!=0},'island nonstatic body partition')
    require(len(set(contact_seen))==len(contact_seen) and set(contact_seen)=={cid for cid,c in contacts.items() if c[16]&1},'island touching contact partition')


class OwnershipModel:
    pass                                                                        
    def __init__(self):
        self.case=None;self.last_ticket=None;self.allow_contact_speed_inf=False;self.begin_case()

    def begin_case(self):
        self.saved={};self.completed=0;self.worlds={};self.bodies={};self.shapes={}
        self.contacts={};self.contact_regs={};self.shape_history=set();self.raw_shape_history={}
        self.body_history=set();self.move_copies={};self.previous=None

    def check(self,case,seq,operation,observations,private=True):
        pass                                                                    
        if self.case is None and case==1 and self.last_ticket is None:self.last_ticket=0
        if self.case!=case:self.begin_case();self.case=case
        rows=defaultdict(list)
        for tag,value in observations:
            require(value[:2]==(case,seq),tag+' model case/seq')
            rows[tag].append(value)
        require(rows['E']==[(case,seq,*operation)],'model exact input echo')
        require(len(rows['Z8'])==1,'model requires current ticket counter')
        self.snapshot(rows,private=private)

    def issue(self,birth):
        require(0<birth<1<<64,'nonzero allocation ticket')
        if self.last_ticket is not None:require(birth==self.last_ticket+1,'ticket allocation order / no reset')
        self.last_ticket=birth

    def life(self,rows,private):
        e=rows['E'][0];code,*a=e[2:];status=rows['R'][0][3]
        def creation(kind,target,owner,result,parent=None):
            register={'W':self.worlds,'B':self.bodies,'S':self.shapes}[kind]
            birth=legacy.wide(result[12:14]);self.issue(birth)
            owner_ticket=0 if owner is None else self.worlds[owner]['birth']
            require(legacy.wide(result[10:12])==owner_ticket,'allocation owner ticket')
            item={'raw':result[5:8],'slot':result[5]-1,'birth':birth,'owner':owner_ticket,'live':True,'world':owner,'parent':parent}
            register[target]=item
            number=(item['slot'],birth&NULL,birth>>32,owner_ticket&NULL,owner_ticket>>32)
            if kind=='S':
                self.shape_history.add(number);self.raw_shape_history[item['raw']]=number
            if kind=='B':self.body_history.add(number)
            if kind=='W':self.contacts[owner_ticket or birth]={}
        if status==0:
            if code in (0,54):creation('W',a[0],None,rows['R'][0])
            elif code in (2,30):creation('B',a[0],a[1],rows['R'][0])
            elif code in (10,17,40):creation('S',a[0],a[1],rows['R'][0],a[2])
            elif code==16:
                creation('B',a[0],a[2],rows['R'][0]);creation('S',a[1],a[2],rows['R'][1],a[0])
            elif code==1:
                owner=self.worlds[a[0]];owner['live']=False
                for item in (*self.bodies.values(),*self.shapes.values()):
                    if item['owner']==owner['birth']:item['live']=False
                self.contacts[owner['birth']]={}
            elif code==3:
                item=self.bodies[a[1]];item['live']=False
                for shape in self.shapes.values():
                    if shape['owner']==item['owner'] and shape['parent']==a[1]:shape['live']=False
            elif code in (11,18):self.shapes[a[1]]['live']=False
        for tag,register in (('W',self.worlds),('B',self.bodies),('S',self.shapes)):
            actual={v[2]:v for v in rows.get(tag,())}
            require(len(actual)==len(rows.get(tag,())),'duplicate live '+tag)
            require(set(actual)=={key for key,item in register.items() if item['live']},tag+' independent live completeness')
            for key,value in actual.items():
                item=register[key];require(value[3:6]==item['raw'],tag+' historical raw handle')
                if tag=='W':require(legacy.wide(value[8:10])==item['birth'],'world birth history')
                else:
                    require(legacy.wide(value[8:10])==item['owner'] and legacy.wide(value[10:12])==item['birth'],tag+' birth/owner history')
                                                                              
                                                                         
        if private:
            cold=legacy.index_rows(rows,'CT',2);sims=legacy.index_rows(rows,'CS',4)
            cp=legacy.index_rows(rows,'CP',1);cf=legacy.index_rows(rows,'CF',2)
            ip=legacy.index_rows(rows,'IP',1);ifs=legacy.index_rows(rows,'IF',2);islands=legacy.index_rows(rows,'IS',2)
            live_worlds={reg for reg,world in self.worlds.items() if world['live']}
            require({key[0] for key in cp}==live_worlds and {key[0] for key in ip}==live_worlds,'independent pool/world completeness')
            for world_id,world in self.worlds.items():
                if not world['live']:continue
                pool_partition(cp[(world_id,)],[value[0] for key,value in cf.items() if key[0]==world_id],
                               {key[1]:value for key,value in cold.items() if key[0]==world_id},'contact pool')
                pool_partition(ip[(world_id,)],[value[0] for key,value in ifs.items() if key[0]==world_id],
                               {key[1]:value for key,value in islands.items() if key[0]==world_id},'island pool')
                old=self.contacts.setdefault(world['birth'],{})
                live={slot:entry for (owner,slot),entry in cold.items() if owner==world_id and entry[0]}
                requests=[v for v in rows.get('RQ',()) if v[2]==world_id]
                for ordinal,value in enumerate(requests):
                    require(value[3]==ordinal,'request dense/original order')
                    h=value[4:]
                    if len(h)>=9 and h[5]:
                        cid=h[6];require(cid in live,'consumed request must own live contact')
                        if cid not in old or old[cid]!=legacy.wide(live[cid][18:20]):
                            self.issue(legacy.wide(live[cid][18:20]))
                next_state={cid:legacy.wide(entry[18:20]) for cid,entry in live.items()}
                for cid,birth in next_state.items():
                    require(old.get(cid)==birth or any(v[4+6]==cid and v[4+5] for v in requests),'contact birth changed outside consumed request')
                self.contacts[world['birth']]=next_state
                found={}
                for key,sim in sims.items():
                    if key[0]!=world_id:continue
                    cid=sim[0];require(cid not in found,'one live sim per contact');found[cid]=(key,sim)
                require(set(found)==set(live),'live CT/CS completeness')
                occupied=defaultdict(set)
                body_types={item['slot']:next((v[12] for v in rows.get('B',()) if v[2]==reg),None)
                            for reg,item in self.bodies.items() if item['live'] and item['owner']==world['birth']}
                for cid,entry in live.items():
                    key,sim=found[cid];require(entry[1]==cid and entry[17]==0,'cold contact identity/mark')
                    require(sim[3:5]==entry[5:7],'cold/hot shape identity')
                    color=entry[3]
                    require(key[1:]==(int(color!=NULL),color if color!=NULL else entry[2],entry[4]),'cold/hot local index reciprocity')
                    if color!=NULL and color<11:
                        for body in (entry[7],entry[10]):
                            if body_types.get(body)==0:continue
                            require(body not in occupied[color],'independent ordinary color conflict');occupied[color].add(body)
                    legacy.manifold(sim[21:51],'current solver manifold')
                ownership_links(world_id,rows,live,islands,body_types,occupied)
                                                                           
                                                                             
        last=legacy.wide(rows['Z8'][0][-2:])
        if private and self.last_ticket is not None:require(last==self.last_ticket,'lastIssued differs from actual allocations')
        if not private and self.last_ticket is not None:
            if code in (31,32) and status==0:require(last>=self.last_ticket,'public ticket counter decreased')
            else:require(last==self.last_ticket,'read/refusal unexpectedly issued ticket')
        self.last_ticket=last
        for value in rows.get('NC9',()):self.contact_regs[value[2]]=value[3:8]
        if code==47:
            world=self.worlds[a[0]];number=self.contact_regs[a[1]]
            expected=1 if not world['live'] else 2 if legacy.wide(number[3:5])!=world['birth'] else None
            if expected is None and private:
                expected=0 if self.contacts.get(world['birth'],{}).get(number[0])==legacy.wide(number[1:3]) else 1
            if expected is not None:require(status==expected,'contact lifetime/owner status priority')
        for hit in rows.get('HG10',()):
                                                                           
                                                                           
            if hit[3]!=1:require(tuple(hit[5:10]) in self.shape_history and tuple(hit[10:15]) in self.shape_history,'hit uses unknown historical number')
                                                                              
                                                                     
        if code==49 and status==0:
            raw=[value[4:] for value in rows.get('HR10',()) if value[2]==a[0]]
            copied=[value[5:] for value in rows.get('HG10',()) if value[2:4]==(a[1],0)]
            require(len(raw)==len(copied),'fresh copy hit count')
            for event,hit in zip(raw,copied):
                require(hit[:5]==self.raw_shape_history.get(tuple(event[:3])) and hit[5:10]==self.raw_shape_history.get(tuple(event[3:6])),'fresh copy used late shape number')
                require(hit[10:]==event[6:],'fresh copied hit numerical value')
        for value in rows.get('MC',()):require(tuple(value[4:9]) in self.body_history,'move copy uses unknown historical body')

    def snapshot(self, rows, private=True):
        for tag in SCHEMA:
            if tag in ('PORT10','GUARD10','COMPONENT10','G','GA','GR10','F','FW','FB','FC','FX','FP','FH10','FM10','FI10'):continue
            for value in rows.get(tag,()):
                d,k=SCHEMA[tag];finite_words(tag,value[:d],value[d:],self.allow_contact_speed_inf)
        for tag in ('W10','CX10','HN10','HR10','HC10','HG10','PK10','SC10','BV10'):
            indexed(rows,tag)
        counts=Counter({tag:len(values) for tag,values in rows.items()})
        require(len(rows.get('Z10',()))==1,'one Z10 per snapshot')
        if private:
            require(len(rows.get('I10',()))==1,'one I10 per private snapshot')
            require(rows['I10'][0][2:]==tuple(counts[t] for t in ('W10','CX10','SB10','PK10','SC10','BV10')),'I10 completeness')
        else:require(not rows.get('I10'),'OBS0 cannot publish I10')
        z=rows['Z10'][0]
        require(z[2:6]==tuple(counts[t] for t in ('HN10','HR10','HC10','HG10')),'Z10 hit completeness')
        echoes=rows.get('E',());require(len(echoes)==1,'one operation echo')
        e=echoes[0];opcode=e[2];a=e[3:]
        results=rows.get('R',());require(bool(results),'operation result required')
        status=results[0][3]
        require(all(value[3] in range(6) for value in results),'no old status6 in PUBLIC10')
        if rows.get('Z8'):self.life(rows,private)
        if opcode in (31,32) and status==0:self.completed+=1
        require(z[-1]==self.completed,'completedSteps includes zero/raw negative, excludes refusal')
        rawhits=indexed(rows,'HR10');hn=indexed(rows,'HN10')
        for (owner,),count in hn.items():
            require([j for w,j in rawhits if w==owner]==list(range(count[0])),'raw hit dense order/count')
        hc=indexed(rows,'HC10');hg=indexed(rows,'HG10')
        current={}
        for (slot,phase),(copy_status,count) in hc.items():
            require(copy_status in range(6),'copy status')
            require([j for s,p,j in hg if (s,p)==(slot,phase)]==list(range(count)),'copy hit dense order/count')
            if copy_status:
                require(count==0,'refused copy must have zero emitted hits');continue
            values=tuple(hg[(slot,phase,j)] for j in range(count))
            current[(slot,phase)]=values
            for hit in values:
                                                                            
                require(hit[0]!=NULL and hit[5]!=NULL,'hit has two historical shape numbers')
                require((hit[1]|hit[2])!=0 and (hit[6]|hit[7])!=0,'nonzero historical birth')
        for slot,phase in tuple(current):
            if phase==2:require(current[(slot,2)]==current.get((slot,0)),'phase2 changed saved hit copy')
            if phase==1:
                original=current.get((slot,0));require(original is not None,'mutate phase0 missing')
                expected=list(original)
                if expected:
                    first=expected[0];expected.append(first)
                    if len(original)>=2:expected[0],expected[1]=expected[1],expected[0]
                    words=list(expected[0]);words[1]^=1;words[10]^=0x80000000;expected[0]=tuple(words)
                require(current[(slot,1)]==tuple(expected),'phase1 exact independent value mutation')
        for (slot,phase),values in current.items():
            if phase!=0:continue
            replaced=opcode==49 and status==0 and a[1]==slot
            if slot in self.saved and not replaced:require(values==self.saved[slot],'saved hit history changed without successful49')
            if replaced:self.saved[slot]=values
        if opcode==49 and status:
            require(hc.get((a[1],0))==(status,0),'Q-HC refusal header')
        if opcode in (31,32) and (status!=0 or number(a[1])<=0):
            require(not any(rows.get(t) for t in ('CX10','SB10','PK10','SC10','BV10')),'stale solver trace after no task')
                                                                        
        packets=indexed(rows,'PK10');sc=indexed(rows,'SC10')
        grouped=defaultdict(list)
        for (world,color,packet,lane),payload in packets.items():
            require(0<=color<=11,'packet color');grouped[(world,color,packet)].append(lane)
            if payload[0]==NULL:require(payload[1:]==(NULL,NULL),'dummy indices')
        for (world,color,packet),lanes in grouped.items():require(lanes==([0] if color==11 else [0,1,2,3]),'packet lane completeness')
        for (world,sub,phase,color,packet,lane),payload in sc.items():
            require((world,color,packet,lane) in packets,'SC missing packet mapping')
            require(payload[2:5]==packets[(world,color,packet,lane)],'SC contact/dense mapping')
            point_count=payload[5];mask=payload[0]|payload[1]<<32
            wanted=(1<<30)-1 if color==11 and point_count==1 else (1<<41)-1
            require(mask==wanted,'SC exact defined mask')


def guard_result(item, records):
    pass                                                                      
    values=[v for tag,v in records if tag=='GR10']
    if item.helper is None:return
    require(values==[(1, len(item.rows), item.helper, item.status, int(item.status==0),
                      item.value&NULL,item.value>>32)],item.name+': GR10 exact helper result')


def predicate_receipts():
    dt=number(0x00400000);inv=div(1,dt);h=div(dt,4);inv_h=mul(4,inv)
    a,b,c=map(number,(0xbf800000,0x3f800001,0x3f7ffffe))
                                                                          
                                                                            
                                                                
    fused=bits(a+b*c);separate=bits(add(a,mul(b,c)))
    return {'step_inv_h':{'dt':'00400000','inv_dt':f'{bits(inv):08x}','h':f'{bits(h):08x}',
                         'inv_h':f'{bits(inv_h):08x}','accepted':valid_step(dt,4)},
            'mul_add':{'A':'bf800000','B':'3f800001','C':'3f7ffffe',
                       'separate':f'{separate:08x}','fused':f'{fused:08x}'},
            'body':{str(n):{'fit':body_fit(n),'blocks':block_plan(n)} for n in (0,128,129,131064,131065,131066,131067,131068)},
            'contact':{str(n):{'bound':n//4+3,'fit':contact_fit(n)} for n in (131059,131060)},
            'checked_overflow':checked_sum(0x7fffffffffffffff,1)}
