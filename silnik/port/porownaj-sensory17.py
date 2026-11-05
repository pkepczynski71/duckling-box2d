pass                                                                             
import argparse
from collections import Counter,defaultdict
import gzip
import importlib.util
from itertools import zip_longest
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sensory_projection14',HERE/'porownaj-polaczenia.py')
base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
HEX=re.compile(rb'[0-9a-f]{8}\Z');DEC=re.compile(rb'(?:0|[1-9][0-9]*)\Z')


def check(ok,message):
    if not ok:raise ValueError(message)


def parse(raw):
    check(len(raw)<=131072 and re.fullmatch(rb'[!-~]+(?: [!-~]+)*\n',raw) is not None,'ASCII/spacing/LF/line length')
    p=raw[:-1].split(b' ');tag=p[0].decode()
    if tag=='J':
        check(len(p)==22 and all(DEC.fullmatch(t) for t in p[1:5]) and all(HEX.fullmatch(t) for t in p[5:]),'J arity/words')
        return tag,p
    if tag=='PORT17':
        check(len(p)==3 and p[1] in (b'PUBLIC',b'DIRECT',b'GUARD') and DEC.fullmatch(p[2]) is not None,'header')
        return tag,p
    prefixes={'E17':5,'E16':5,'R17':7,'R16':7,'V17':6,'T17':9,'U17':8,'W17':5,'W16':5,'Q17':6,'G17':7,'I16':4}
    if tag in prefixes:
        start=prefixes[tag]
        check(len(p)>=start,'short '+tag)
        for token in p[1:start]:check(DEC.fullmatch(token) is not None and int(token)<=0xffffffff,'decimal '+tag)
        n=int(p[start-1]);check(len(p)==start+n,'arity '+tag)
        for token in p[start:]:check(HEX.fullmatch(token) is not None,'word '+tag)
        fixed={'V17':2,'W17':8,'W16':1,'Q17':4,'I16':8,'G17':0}
        if tag in fixed:check(n==fixed[tag],'fixed arity '+tag)
        if tag=='T17':check(n==(8 if int(p[5])==2 else 16),'T17 row width')
        if tag=='U17':check(n=={0:3,1:4,2:4,3:2,4:16,5:16}.get(int(p[5])),'U17 group width')
        if tag=='R17':check(n=={400:8,401:0,402:1,403:1,404:0,405:0,406:0,407:0,408:1,409:6,32:0,86:0}.get(int(p[3])),'R17 opcode width')
        return tag,p
    if tag=='L17':
        check(len(p)==8 and all(DEC.fullmatch(t) for t in p[1:]),'L17 header')
        return tag,p
    base.parse(raw)
    return tag,p


def project(raw):
    tag,p=parse(raw)
    if tag in ('U17','Q17'):return None
    if tag=='W17':
        p[7:13]=[b'00000000']*6;return b' '.join(p)+b'\n'
    if tag in ('PORT17','E17','E16','R17','R16','V17','L17','T17','W16','G17','I16','J'):return raw
    return base.project(raw)


def open_stream(path):
    path=Path(path);return gzip.open(path,'rb') if path.suffix=='.gz' else path.open('rb')


class G6:
    def __init__(self,recipes,observer):
        self.recipes=recipes;self.observer=observer;self.case=None;self.seq=0;self.frames=0;self.ended=False;self.tags=Counter();self.frame=[];self.caseCount=0;self.totalBytes=0
        self.guardPhase=0;self.metrics=Counter();self.frameBytes=0;self.priorCase=0;self.savedRows={};self.savedLists={};self.profile=None

    def finish_frame(self):
        if not self.frame:return
        tags=Counter(t for t,p in self.frame)
        for tag,p in self.frame:
            check((int(p[1]),int(p[2]))==(self.case,self.seq),'record case/sequence differs')
            if tag=='R17':
                status,reason=int(p[4]),int(p[5]);check(status in range(8) and reason in (0,1,20,21),'R17 status/reason')
                check(not status or all(int(w,16)==0 for w in p[7:]),'nonzero refusal result')
                check(reason==0 if status==0 else reason==1 if status==7 else reason in (0,20,21) if status==5 else reason==0,'R17 reason precedence')
                                                                           
                                                                                
                                                                               
        legacy_records=[]
        inherited={'PORT17','E16','E17','R16','R17','V17','L17','T17','U17','W17','W16','Q17','G17','I16','J'}
        for tag,p in self.frame:
            if tag not in inherited:legacy_records.append(base.parse(b' '.join(p)+b'\n'))
        recipe=self.recipes[self.case]
        code,words=recipe[self.seq-1][:2] if recipe else (400,[])
        if recipe:
            want=code>=400 or code==32 or code==86 and words[1]==1 and words[2]==0
            check(tags['R17']==int(want),'missing/duplicate/unassigned R17')
        operation={'opcode':code,'a':words}
        synthetic=('E14',(self.case,self.seq,code,len(words),*words))
        if tags['E14']==0:
            legacy_records.insert(0,synthetic)
            adjusted=[]
            for tag,v in legacy_records:
                if tag=='Z13':
                    check(v[-1]==0,'Z13 real E14 count');v=(*v[:-1],1)
                adjusted.append((tag,v))
            legacy_records=adjusted
        base.snapshot_check(legacy_records,SimpleNamespace(id=self.case),self.seq,operation,self.observer)
        for tag in ('A14','Z8','Z9','Z10','Z11','I12','Z12','Z13','I16'):
            check(tags[tag]==1,f'missing/duplicate {tag} at {self.case}/{self.seq}')
        pending=None;seen_lists=set();tcount=0;vcount=Counter();begins={};worlds={};queries=Counter();refs=Counter();declared_refs={}
        for tag,p in self.frame:
            if pending and tag!='T17':check(pending[-1]==0,'truncated L17/T17 block');pending=None
            if tag=='L17':
                key=tuple(p[3:7]);check(key not in seen_lists,'duplicate L17');seen_lists.add(key)
                pending=[key,0,int(p[7])]
                if p[3]==b'0' and p[5]==b'0':begins[int(p[4])]=int(p[7])
            elif tag=='T17':
                check(pending is not None and tuple(p[3:7])==pending[0] and int(p[7])==pending[1] and pending[2]>0,'orphan/duplicate/out-of-order T17')
                pending[1]+=1;pending[2]-=1;tcount+=1
            elif tag=='V17':
                check(int(p[6],16) in (0,1) and int(p[7],16) in (0,1),'V17 bool');vcount[int(p[3])]+=int(p[6],16)
            elif tag=='W17':worlds[int(p[3])]=[int(x,16) for x in p[5:]]
            elif tag=='Q17':
                w=int(p[3]);check(int(p[4])==queries[w],'Q17 ordinal');queries[w]+=1
            elif tag=='U17':
                key=(int(p[3]),int(p[4]));group=int(p[5]);j=int(p[6])
                if group==0:declared_refs[key]=[int(p[9],16),int(p[10],16)]
                if group in (1,2):
                    check(j==refs[(key,group)],'U17 ref ordinal');refs[(key,group)]+=1
        if pending:check(pending[-1]==0,'truncated last list')
        saved_rows={tuple(map(int,p[4:8])):tuple(int(x,16) for x in p[9:]) for tag,p in self.frame if tag=='T17' and p[3]==b'2'}
        saved_lists={tuple(map(int,p[4:7])):int(p[7]) for tag,p in self.frame if tag=='L17' and p[3]==b'2'}
        if recipe:
            if code==407:
                key=(words[1],words[2],0,words[3]);check(key in self.savedRows,'edit missing previous owned row')
                old=self.savedRows[key];expected=dict(self.savedRows);edited=list(old);edited[words[4]]=words[5];expected[key]=tuple(edited)
                check(old[words[4]]!=words[5] and saved_rows==expected and saved_lists==self.savedLists,'edit changed wrong/aliased owned copy')
                if self.profile==b'PUBLIC' and (67<=self.case<=72 or 85<=self.case<=90):
                    check(words[5]==(old[words[4]]^1),'frozen F8/F11 edit is not actual xor1')
            elif code not in (404,405):
                check(saved_rows==self.savedRows and saved_lists==self.savedLists,'owned copy changed without a copy/edit operation')
            else:
                bank=words[2];lists=(0,1) if code==404 else (2,)
                unrelated=lambda rows:{k:v for k,v in rows.items() if k[0]!=bank or k[1] not in lists}
                check(unrelated(saved_rows)==unrelated(self.savedRows) and unrelated(saved_lists)==unrelated(self.savedLists),'save changed unrelated owned bank')
        self.savedRows,self.savedLists=saved_rows,saved_lists
        old_worlds={int(p[3]) for tag,p in self.frame if tag=='W'}
                                                                            
                                                                               
        world_ids={int(p[4],16)-1:int(p[3]) for tag,p in self.frame if tag=='W'}
        expected_shapes={(world_ids[int(p[5],16)],int(p[4],16)-1) for tag,p in self.frame if tag=='S'}
        actual_shapes=[(int(p[3]),int(p[4])) for tag,p in self.frame if tag=='V17']
        check(set(worlds)==old_worlds and len(worlds)==tags['W17'],'missing/duplicate W17')
        check(set(actual_shapes)==expected_shapes and len(actual_shapes)==len(expected_shapes),'missing/duplicate V17')
        check({int(p[3]) for tag,p in self.frame if tag=='W16'}==old_worlds and tags['W16']==len(old_worlds),'missing/duplicate W16')
        for w in old_worlds:
            for kind in (0,1):check((b'0',str(w).encode(),str(kind).encode(),b'0') in seen_lists,'missing current event list')
        for tag,p in self.frame:
            if tag=='V17' and int(p[6],16):
                check((b'0',p[3],b'2',p[4]) in seen_lists,'missing sensor overlap list')
            if tag=='I16':
                values=[int(t,16) for t in p[4:]]
                check(values[0]==tags['R16'] and values[1]==tags['W16'] and values[2:7]==[0]*5 and values[7]==self.seq,'I16 record counts/ordinal')
        history=[p for tag,p in self.frame if tag=='J']
        if history or recipe and code==20 or not recipe and self.case==697:
            expected=self.recipes[self.case]
            repeat=expected[self.seq-1][1][3] if expected else 65536
            check(len(history)==2*repeat-1,'truncated/duplicated CHURN history')
            for i,p in enumerate(history):
                j,phase=(1,1) if i==0 else ((i+1)//2+1,0 if i%2 else 1)
                check((int(p[3]),int(p[4]))==(j,phase),'CHURN order')
                check(int(p[15],16)==0,'old game birth became valid')
            first,last=history[0],history[-1]
            birth=lambda p:int(p[12],16)|(int(p[13],16)<<32)
            check(birth(last)-birth(first)==repeat-1,'CHURN missing native tickets')
            if repeat==65536:check(int(last[14],16)==1,'missing natural raw generation collision')
        for w,a in worlds.items():
            check(a[0]==vcount[w] and a[1]==begins.get(w,0),'public W17 counts')
            if self.observer:check(a[6]==queries[w] and a[7]==tcount,'W17 query/list counts')
            else:check(a[2:]==[0]*6 and tags['Q17']==0 and tags['U17']==0,'OBS0 private state')
            for name,value in [('sensors',a[0]),('maxBegin',a[1]),('maxEnd',max(a[2],a[3])),('bits',a[5]),('queryMax',a[6])]:self.metrics[name]=max(self.metrics[name],value)
        if self.observer:
            for key,counts in declared_refs.items():check(counts==[refs[(key,1)],refs[(key,2)]],'U17 ref count')
            self.metrics['refs']=max(self.metrics['refs'],sum(sum(counts) for counts in declared_refs.values()))
        self.metrics['snapshotBytes']=max(self.metrics['snapshotBytes'],self.frameBytes)
        self.frame=[];self.frameBytes=0;self.frames+=1

    def line(self,raw):
        check(not self.ended,'trailing data after END');tag,p=parse(raw);self.tags[tag]+=1;self.totalBytes+=len(raw)
        if tag=='CASE':
            self.finish_frame();check(self.case is None,'nested CASE');self.case=int(p[1]);self.seq=0;self.guardPhase=0
            self.savedRows={};self.savedLists={}
            check(self.case>self.priorCase,'duplicate/out-of-order CASE');self.priorCase=self.case
            check(self.case in self.recipes and int(p[2])==len(self.recipes[self.case]),'case/M mismatch')
        elif tag in ('E14','E16','E17'):
            self.finish_frame();self.seq+=1;check(self.case is not None and int(p[1])==self.case and int(p[2])==self.seq,'echo case/seq')
            check(self.seq<=len(self.recipes[self.case]),'extra operation')
            expected=self.recipes[self.case][self.seq-1];code,words=expected[:2]
            check(int(p[3])==code and int(p[4])==len(words) and [int(x,16) for x in p[5:]]==words,'input echo differs')
            check(tag==('E17' if code>=400 else 'E16' if code>=300 else 'E14'),'wrong echo tag')
            self.frame.append((tag,p))
            self.frameBytes+=len(raw)
        elif tag=='ENDCASE':
            self.finish_frame();check(self.case==int(p[1]),'ENDCASE id')
            if not self.recipes[self.case]:check(self.guardPhase==2,'missing GUARD phase')
            else:check(self.seq==len(self.recipes[self.case]),'missing operation/ENDCASE')
            self.case=None;self.caseCount+=1
        elif tag=='END':
            check(self.case is None and int(p[1])==len(self.recipes) and self.caseCount==len(self.recipes),'END count');self.ended=True
        elif tag=='G17':
            self.finish_frame();check(self.case==int(p[1]) and int(p[2])==self.guardPhase and not self.recipes[self.case],'G17 phase/case');self.seq=self.guardPhase;self.guardPhase+=1
            check(int(p[5])==int(int(p[3])==0),'G17 accepted/status')
        elif tag=='PORT17':
            check(self.tags['PORT17']==1 and int(p[2])==len(self.recipes),'header N/duplicate');self.profile=p[1]
        else:
            check(self.case is not None and (self.seq>0 or self.guardPhase>0),'row outside operation');self.frame.append((tag,p));self.frameBytes+=len(raw)
        check(self.frameBytes<=148050944,'Q17 snapshot envelope')

    def finish(self):check(self.ended,'missing END');return {'cases':self.caseCount,'snapshots':self.frames,'bytes':self.totalBytes,'tags':dict(self.tags),'metrics':dict(self.metrics)}


def compare(c0,c1,recipes,d=None):
    checks=[G6(recipes,False),G6(recipes,True)];difference=None
    def validated(stream,validator,projection=False):
        for raw in stream:
            validator.line(raw)
            row=project(raw) if projection else raw
            if row is not None:yield row
        validator.finish()
    with open_stream(c0) as a,open_stream(c1) as b:
        for i,(x,y) in enumerate(zip_longest(validated(a,checks[0]),validated(b,checks[1],True)),1):
            if x!=y and difference is None:difference={'row':i,'C0':None if x is None else x[:30000].decode(),'projectionC1':None if y is None else y[:30000].decode()}
    result={'C0ProjectionC1':difference is None,'firstDifference':difference,'counts':[v.finish() for v in checks],'D':'NIEURUCHOMIONE'}
    if d is not None:
        validator=G6(recipes,True);diff=None
        with open_stream(c1) as a,open_stream(d) as b:
            for i,(x,y) in enumerate(zip_longest(a,validated(b,validator)),1):
                if x!=y and diff is None:diff={'row':i,'C1':None if x is None else x[:30000].decode(),'D':None if y is None else y[:30000].decode()}
        result.update(C1D=diff is None,firstDifferenceD=diff,countsD=validator.finish())
    return result
