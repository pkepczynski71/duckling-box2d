pass                                                                  

                                                                     
                                                                          
   
from collections import Counter, defaultdict
import argparse
from contextlib import ExitStack
import hashlib
import importlib.util
from itertools import zip_longest
import json
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


legacy = load('polaczenia_compare13', 'model-lancuchy.py')
base = legacy.base12_13b()
generator = load('polaczenia_compare_inputs', 'przypadki-polaczenia.py')
PART_B = False
DEC = re.compile(rb'(?:0|[1-9][0-9]*)\Z')
HEX = re.compile(rb'[0-9a-f]{8}\Z')
J_ARITY = {0: 8, 1: 21, 2: 17, 3: 26, 4: 50, 5: 6, 6: 19, 7: 2, 8: 20, 9: 2, 10: 16, 11: 4}
PRIVATE_J = {1, 2, 3, 5, 7, 10}
ZERO_J8 = (1, 2, 3, 5, 7, 9, 10, 11, 12, 13)
COUNTERS = frozenset(('I8 I9 I10 I11 I12 IP12 I13 Z8 Z9 Z10 Z11 Z12 Z13').split())
legacy_order = list(base.ORDER)
legacy_order[1:1]=[('EP13B',),('EU13B',)]
at = legacy_order.index(('X',))
legacy_order[at:at] = [(t,) for t in ('CN13', 'V13')] + [('CQ13', 'QL13'), ('CS13',), ('PC13',), ('COPY13', 'CV13', 'CE13', 'ENDCOPY13')]
at = legacy_order.index(('I8',))
legacy_order[at:at] = [(t,) for t in ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13')]
legacy_order += [('I13',), ('Z13',)]
LEGACY_RANK = {t: i for i, group in enumerate(legacy_order) for t in group}
LEGACY_RANK['A13'] = -1


def require(ok, message):
    if not ok: raise ValueError(message)


def decimal(token, signed=False):
    if signed and token == b'-1': return -1
    require(DEC.fullmatch(token) is not None, 'noncanonical decimal')
    n = int(token); require(n <= 0xffffffff, 'decimal outside u32'); return n


def parse(raw):
    require(isinstance(raw, bytes) and 0 < len(raw) <= 131072 and raw.endswith(b'\n'), 'output line envelope/LF')
    require(re.fullmatch(rb'[!-~]+(?: [!-~]+)*\n', raw) is not None, 'canonical ASCII/spacing')
    p = raw[:-1].split(b' '); tag = p[0].decode('ascii')
    if tag == 'PORT14':
        require(len(p) == 4 and p[1] == (b'B' if PART_B else b'A') and p[2] in (b'PUBLIC', b'DIRECT', b'GUARD'), 'PORT14 profile/arity')
        return tag, (p[2].decode(), decimal(p[3]))
    if tag == 'Z13':
        require(len(p) == 21 and all(HEX.fullmatch(w) for w in p[3:]), 'Z13 arity18/H8')
        return tag, (decimal(p[1]), decimal(p[2]), *(int(w, 16) for w in p[3:]))
    if tag in ('CASE', 'ENDCASE', 'END', 'A14', 'T14', 'G14'):
        arity = {'CASE': 2, 'ENDCASE': 1, 'END': 1, 'A14': 4, 'T14': 9, 'G14': 4}[tag]
        require(len(p) == arity+1, tag+' arity')
        v = tuple(decimal(w, signed=tag=='T14' and i==4) for i, w in enumerate(p[1:]))
        if tag == 'T14':
            require(v[2] in range(8) and v[3] in range(4) and -1 <= v[4] <= 11 and v[7] in ((0,4,5) if PART_B else (0,)) and v[8] in (0, 1), 'T14 domain')
            require(v[8] == int(v[3] == 2), 'T14 bias/phase')
        if tag == 'A14': require(v[2] <= 7 and v[3] in ((0, 1, 6, 7, 8, 10, 80, 81, 82, 83, 84, 85)+(9,) if PART_B else (0, 1, 6, 7, 8, 10, 80, 81, 82, 83, 84, 85)), 'A14 status/reason')
        return tag, v
    if tag in ('E14', 'F14', 'EF14', 'GA14', 'J14', 'L14'):
        d = {'E14': 4, 'F14': 4, 'EF14': 4, 'GA14': 1, 'J14': 7, 'L14': 7}[tag]
        require(len(p) >= 1+d, tag+' prefix')
        v = [decimal(w) for w in p[1:1+d]]
        for w in p[1+d:]:
            require(HEX.fullmatch(w) is not None, tag+' canonical H8'); v.append(int(w, 16))
        payload = len(v)-d
        if tag == 'GA14': require(payload == 64, 'GA14 arity')
        else: require(payload == v[d-1], tag+' declared n')
        if tag == 'J14':
            require(v[2] <= 5 and v[3] <= 16 and (v[5] in J_ARITY or PART_B and v[5]==12), 'J14 source/world/group'); allowed=({3:(26,30,34),4:(50,51),6:(19,21,22),12:(1,2)}.get(v[5],(J_ARITY.get(v[5]),)) if PART_B else (J_ARITY[v[5]],)); require(payload in allowed, 'J14 arity');
            if PART_B and (v[5]==6 or v[5]==4 and v[2]==0) and v[d] in (0,4,5) and (v[5]==6 or any(v[d:])):require(payload==(19 if v[d]==0 else 21 if v[d]==5 else 22) if v[5]==6 else payload==(51 if v[d]==4 else 50), 'active view/description type arity')
        if tag == 'L14': require(v[2] <= 4 and v[3] <= 16 and v[4] <= 4, 'L14 source/world/container')
        if tag in ('F14', 'EF14'):
            if PART_B:require((v[1]==0 and v[2] in range(5) and payload in ((30,34) if v[2]==2 else ((5,17,0,20,16)[v[2]],))) or (v[2]==5 and (v[1],payload) in ((1,1),(2,6))),tag+' B group arity')
            else:require(v[1] == 0 and v[2] in range(5) and payload == (5,17,26,20,16)[v[2]], tag+' group arity')
        if tag == 'E14':
            code = v[2]
            if code < 200: require(payload == 64, 'inherited E14 n64')
            elif code == 203: require(payload >= 4 and v[d+3] in generator.MUTATOR_ARITY and payload == 4+generator.MUTATOR_ARITY[v[d+3]], 'mutator E14 arity')
            else: require(code in generator.NEW_ARITY and payload == generator.NEW_ARITY[code], 'E14 opcode arity')
        return tag, tuple(v)
    return legacy.parse_world13b(raw)


def project(raw, record=None):
    tag, v = parse(raw) if record is None else record
    if tag == 'T14' or tag == 'J14' and v[5] in (PRIVATE_J|({12} if PART_B else set())) or tag == 'L14' and v[4] in (1,2,3,4): return None
    if tag == 'J14' and v[5] == 8:
        p = raw[:-1].split(b' ')
        for i in ZERO_J8: p[8+i] = b'00000000'
        return b' '.join(p)+b'\n'
    return raw if tag == 'Z13' else legacy.projection13b_line(raw)


def rank(record):
    tag, v = record
    if tag == 'E14': return (0,)
    if tag == 'A14': return (2,)
    if tag == 'J14':
        source,w,slot,group = v[2:6]
        if group == 8: return (12,)
        if source: return (7,source,0 if group==0 else 1,slot)
        if group == 0: return (4,slot)
        if group in (4,9,11,12) if PART_B else group in (4,9,11): return (5,)
        return (10,group,w,slot)
    if tag == 'L14':
        source,w,container,parent = v[2:6]
        return (7,source,2,parent) if source else (6,) if container==0 else (11,container,w,parent)
    if tag == 'T14': return (8,)
    require(tag in LEGACY_RANK, 'record absent from BASE13 order: '+tag)
    if tag in ('EP13B','EU13B'): return (1,0,LEGACY_RANK[tag])
    if tag == 'A13': return (1,1)
    if tag in ('R','AP12','HT12','HR12'): return (1,2,LEGACY_RANK[tag])
    if tag in COUNTERS: return (13,LEGACY_RANK[tag])
    return (3 if LEGACY_RANK[tag] < LEGACY_RANK['X'] else 9,LEGACY_RANK[tag])


def difference_context(raw, token):
    if raw is None:return {'field':'missing-row'}
    p=raw[:-1].split(b' ');tag=p[0].decode('ascii');context={'tag':tag,'field':'token'+str(token)}
    if tag in ('J14','L14'):
        context.update(W=int(p[4]),slot=int(p[5]) if tag=='J14' else int(p[6]),
                       group=int(p[6]) if tag=='J14' else int(p[5]),field='h'+str(token-8) if token>=8 else 'metadata'+str(token))
        if tag=='J14' and p[6]==b'1':context.update(set=p[11].decode(),local=p[13].decode())
    if tag=='T14':context.update(subStep=int(p[3]),phase=int(p[4]),color=int(p[5]),slot=int(p[7]))
    return context


def snapshot_check(records, case, seq, operation, observer, *, helper_kind=None):
    code = operation['opcode'] if operation is not None else None
    if operation is not None: require(records and records[0] == ('E14', (case.id,seq,operation['opcode'],len(operation['a']),*operation['a'])), 'missing/wrong E14 echo')
    tags = Counter(t for t,v in records); grouped = defaultdict(list)
    previous = (-1,); seen=set()
    for t,v in records:
        require(v[:2] == (case.id,seq), t+' wrong case/seq')
        current = rank((t,v)); require(current >= previous, t+' group order'); previous=current
        grouped[t].append(v)
        if t in ('J14','L14'):
            key = (t,*v[2:6]); require(key not in seen, t+' duplicate identity'); seen.add(key)
        if not observer:
            require(t not in legacy.PRIVATE13B and t != 'T14', 'private tag in OBS0')
            require(not (t == 'J14' and v[5] in (PRIVATE_J|({12} if PART_B else set())) or t == 'L14' and v[4]), 'private joint group in OBS0')
    callback=PART_B and case.profile=='GUARD' and case.guard_kind==5 and code==32
    require(tags['E14']==int(operation is not None) and (tags['A14']>=2 if callback else tags['A14']==1),'E14/A14 completeness')
    if callback:
        require(any(v[4]==1 for v in grouped['HT12']),'real preSolve HT12 provenance')
        require(all(v[2:]==(7,1) for v in grouped['A14'][:-1]) and grouped['A14'][-1][2:]==(0,0),'real callback refusal then successful Step')
    if operation is None:
        helpers = [v for v in grouped['J14'] if v[5] == 11]
        require(helper_kind in range(1,11) and len(helpers) == 1 and helpers[0][2:7] == (0,16,helper_kind,11,4), 'helper frame kind/source/world/arity')
    require(all(tags[t] == 1 for t in ('Z8','Z9','Z10','Z11','I12','Z12','Z13')), 'BASE13 counter completeness')
    summaries = [v for v in grouped['J14'] if v[5] == 8]
    require(len(summaries) == 1, 'one J8 per snapshot'); summary=summaries[0][7:]
    require(summaries[0][2:5] == (0,16,0), 'J8 identity')
    for i in range(8): require(summary[i] == sum(v[5]==i for v in grouped['J14']), 'J8 J'+str(i)+' count')
    for i in range(5): require(summary[8+i] == sum(v[4]==i for v in grouped['L14']), 'J8 L'+str(i)+' count')
    require(summary[13] == tags['T14'] and summary[15] == seq, 'J8 trace count/ordinal')
    z = grouped['Z13'][0][2:]
    require(z[0] == tags['A13'] and z[17] == tags['E14'], 'Z13 actual A13/E14 counts')
    require(grouped['Z9'][0][14] == 14, 'PORT14 Z9 profile14')
    require(tags['A13'] == int(code is not None and code < 200), 'A13 only inherited operation')
    require(sum(v[5] == 9 for v in grouped['J14']) == int(code==212 or operation is None and helper_kind==1), 'J9 exact applicability')
    require(sum(v[5] == 10 for v in grouped['J14']) == int(observer and code==210 and (not PART_B or operation['a'][0]==0)), 'J10 exact applicability')
    require(sum(v[5] == 4 and v[2]==0 for v in grouped['J14']) == int(code==204), 'READ J4 completeness')
    if observer:
        occupied = {(v[3],v[4]) for v in grouped['J14'] if v[5] == 5 and v[7]}
        for group in (1,2,3): require({(v[3],v[4]) for v in grouped['J14'] if v[5]==group} == occupied, 'full private joint payload set')
    else: require(all(summary[i] == 0 for i in ZERO_J8), 'OBS0 zero private counts')
    if PART_B:
        if operation is None:
            helper=next(v for v in grouped['J14'] if v[5]==11);status=grouped['A14'][-1][2]
            require(helper[7:9]==(status,int(status==0)),'helper status/accepted')
            if helper_kind==10:require(helper[9:11]==(1,0),'owned copy helper success1')
        common={(v[3],v[4]):v[10] for v in grouped['J14'] if v[5]==2}
        for v in grouped['J14']:
            if v[5]==3:require(v[6]=={0:26,5:30,4:34}[common[(v[3],v[4])]], 'J3 active type arity')
        math=operation is not None and code==210 and operation['a'][0]!=0
        result=[v for v in grouped['J14'] if v[5]==12]
        require(len(result)==int(observer and math), 'J12 exact applicability')
        if result:require(result[0][2:7]==(0,16,0,12,1 if operation['a'][0]==1 else 2),'J12 math identity/arity')
        if operation is None or case.profile=='GUARD' and not case.guard_kind and seq==len(case.ops):
            expected=next(x for x in generator.MANIFEST['guards'] if x['key']==case.key)
            status=next(v for t,v in records if t=='A14')
            require(status[2:]==(expected['status'],expected['reason']), 'frozen GUARD expected status/reason')
    return summary


class Reader:
    def __init__(self, stream, label, cases, checker=None):
        self.stream,self.label,self.cases,self.checker=stream,label,cases,checker
        self.observer=label!='c0'; self.bytes=0;self.tags=Counter();self.sha=hashlib.sha256();self.max_snapshot=0
        self.pending=None;self.positive=0;self.words=0;self.case_sha=None;self.case_words=0;self.case_tags=Counter();self.case_bytes=0;self.case_maxima={}
        self.take(('PORT14',(cases[0].profile,len(cases))))

    def take(self, expected=None):
        if self.pending is not None: raw,record=self.pending;self.pending=None
        else:
            raw=self.stream.readline(131073);record=parse(raw);self.sha.update(raw);self.bytes+=len(raw);self.tags[record[0]]+=1
            self.words+=len(record[1])
            if self.case_sha is not None:
                self.case_sha.update(raw);self.case_bytes+=len(raw);self.case_tags[record[0]]+=1;self.case_words+=len(record[1])
        if expected is not None: require(record == expected, self.label+' expected '+repr(expected)+' got '+repr(record))
        return raw,record

    def start(self, case):
        self.case_sha=hashlib.sha256();self.case_bytes=0;self.case_words=0;self.case_tags=Counter();self.case_maxima={'snapshotBytes':0,'liveJoints':0,'rowsPerTag':{}};self.case_started=time.monotonic()
        self.take(('CASE',(case.id,len(case.ops)))); self.positive=0
        for group,words in enumerate(case.fixtures): self.take(('EF14',(case.id,0,group,len(words),*words)))
        if self.checker is not None and hasattr(self.checker,'reset'): self.checker.reset(case.id)

    def operation(self, case, seq, operation):
        if PART_B:self.last_records=None
        raws=[];records=[];size=0
        while True:
            raw,record=self.take()
            if record[0] in ('E14','ENDCASE','END','CASE') and records:
                self.pending=(raw,record);break
            records.append(record);raws.append(raw);size+=len(raw)
            require(size<=13833216,'Q14 snapshot envelope')
                                                                              
            if record[0]=='Z13': break
        summary=snapshot_check(records,case,seq,operation,self.observer)
        self.case_maxima['snapshotBytes']=max(self.case_maxima['snapshotBytes'],size)
        self.case_maxima['liveJoints']=max(self.case_maxima['liveJoints'],summary[16])
        counts=Counter(t for t,v in records)
        for tag,count in counts.items():self.case_maxima['rowsPerTag'][tag]=max(self.case_maxima['rowsPerTag'].get(tag,0),count)
        self.positive+=int(operation['opcode'] in (31,32) and generator.value(operation['a'][1])>0 and ([v[2] for t,v in records if t=='A14'][-1] if PART_B else next(v[2] for t,v in records if t=='A14'))==0)
        require(summary[14]==self.positive,'J8 exact successful positive Steps')
        if self.checker is not None: self.checker.check(case.id,seq,operation,records,self.observer)
        self.max_snapshot=max(self.max_snapshot,size)
        if PART_B:self.last_records=records
        return raws

    def finish(self, case):
        self.take(('ENDCASE',(case.id,)))
        expected=sum(o['opcode'] in (31,32) and generator.value(o['a'][1])>0 for o in case.ops)
        require(self.positive==expected,self.label+' successful positive Step count differs from input allocation')
        result={'bytes':self.case_bytes,'sha256':self.case_sha.hexdigest(),'words':self.case_words,'tags':dict(self.case_tags),
                'maxima':self.case_maxima,'positiveSteps':self.positive,'seconds':time.monotonic()-self.case_started}
        self.case_sha=None
        return result

    def end(self):
        self.take(('END',(len(self.cases),)));require(not self.stream.read(1),self.label+' trailing output')
        return {'bytes':self.bytes,'words':self.words,'sha256':self.sha.hexdigest(),'tags':dict(self.tags),'maxSnapshotBytes':self.max_snapshot,'END_EOF':True,'modelChecked':self.checker is not None}


def compare_streams(streams, cases, *, checker_factory=None, error_sink=None):
    require(set(streams) in ({'c0','c1'},{'c0','c1','d'}),'C0/C1 and optional D required')
    readers={k:Reader(v,k,cases,None if checker_factory is None else checker_factory(observer=k!='c0')) for k,v in streams.items()}
    result={'profile':cases[0].profile,'N':len(cases),'snapshots':0,'cases':[],'errors':[],'errorCount':0,'word_comparison_ok':False,'full_acceptance':False}
    window_bytes=0
    for case in cases:
        for reader in readers.values():reader.start(case)
        for seq,operation in enumerate(case.ops,1):
            snapshots={};failures={}
                                                                           
                                                                    
            for label,reader in readers.items():
                try:snapshots[label]=reader.operation(case,seq,operation)
                except (ValueError,AssertionError) as e:failures[label]=str(e)
            if failures:
                error={'case':case.id,'key':case.key,'seq':seq,'validation':failures};result['errors'].append(error);result['errorCount']+=1
                if error_sink:error_sink.write(json.dumps(error)+'\n')
                return result
            projected=[x for raw in snapshots['c1'] if (x:=project(raw)) is not None]
            pairs=[('C0=projection(C1)',snapshots['c0'],projected)]
            if 'd' in readers:pairs.append(('C1=D',snapshots['c1'],snapshots['d']))
            for label,left,right in pairs:
                for i,(a,b) in enumerate(zip_longest(left,right),1):
                    if a==b:continue
                    for token,(av,bv) in enumerate(zip_longest(a.split() if a else (),b.split() if b else ())):
                        if av==bv:continue
                        error={'case':case.id,'key':case.key,'seq':seq,'comparison':label,'row':i,
                               **difference_context(a or b,token),'left':None if av is None else av.decode('ascii'),
                               'right':None if bv is None else bv.decode('ascii')}
                        result['errorCount']+=1
                        if error_sink:error_sink.write(json.dumps(error)+'\n')
                        if len(result['errors'])<64:
                            size=len(json.dumps(error).encode())
                            if window_bytes+size<=65536:result['errors'].append(error);window_bytes+=size
            result['snapshots']+=1
        metrics={label:reader.finish(case) for label,reader in readers.items()}
        result['cases'].append({'id':case.id,'key':case.key,'opCount':len(case.ops),'positiveSteps':readers['c1'].positive,'streams':metrics})
    result['streams']={k:r.end() for k,r in readers.items()}
    result['word_comparison_ok']=result['errorCount']==0
    result['modelChecked']=checker_factory is not None
    result['DucklingChecked']='d' in readers
                                                                              
    result['full_ownership_ready']=all(getattr(r.checker,'full_ownership_ready',False) for r in readers.values())
    result['full_acceptance']=result['word_comparison_ok'] and result['full_ownership_ready'] and result['DucklingChecked']
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',choices=('PUBLIC','DIRECT'),required=True);p.add_argument('--N',type=int)
    for name in ('c0','c1'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--d',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    with ExitStack() as stack:
        streams={k:stack.enter_context(path.open('rb')) for k in ('c0','c1','d') if (path:=getattr(a,k)) is not None}
        errors=stack.enter_context(a.out.with_suffix('.errors.jsonl').open('w',encoding='utf-8'))
        result=compare_streams(streams,generator.cases(a.profile,a.N),error_sink=errors)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');sys.exit(not result['full_acceptance'])
