pass                                                                        
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import importlib.util
from itertools import zip_longest
import json
from pathlib import Path
import subprocess
import io
import sys
import tempfile
import threading
import time

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
G=load('recipes14b','przypadki-14b.py')
C=load('compare14a_for_b','porownaj-polaczenia.py')
C.PART_B=True;C.generator=G

class Reader(C.Reader):
    def start(self,case):
        self.definition_types={};self.joint_types={};self.copy_lengths={};self.physical=None;self.callback_seen=False
        if case.fixtures:self.joint_types[0]=case.fixtures[1][3]
        self.case_sha=hashlib.sha256();self.case_bytes=0;self.case_words=0;self.case_tags=Counter();self.case_maxima={'snapshotBytes':0,'liveJoints':0,'rowsPerTag':{}};self.case_started=time.monotonic()
        if case.profile=='GUARD':
            self.take(('G14',(case.id,case.guard_kind,case.seed_after,len(case.ops))))
            self.take(('GA14',(case.id,*case.ga)))
        self.take(('CASE',(case.id,len(case.ops))));self.positive=0
        for group,words in enumerate(case.fixtures):
            fixture=0 if group<5 else next(o['a'][0] for o in case.ops if o['opcode']==210 and o['a'][0])
            self.take(('EF14',(case.id,fixture,group,len(words),*words)))

    def check_history(self,records,case,operation):
        status=[v[2:] for t,v in records if t=='A14'][-1]
        if operation is not None:
            code,a=operation['opcode'],operation['a']
            if code==200:self.definition_types[a[1]]=a[0]
            if code==201 and status[0]==0:self.joint_types[a[4]]=self.definition_types[a[5]]
            if code==207 and status[0]==0:self.copy_lengths[a[2]]=51 if self.joint_types[a[1]]==4 else 50
            for t,v in records:
                if t!='J14' or v[5]!=4:continue
                if v[2]:expected=self.copy_lengths[v[2]-1]
                else:expected=51 if self.joint_types[v[4]]==4 else 50
                C.require(v[6]==expected,'READ/copy retained own type arity')
        if any(t=='HT12' and v[4]==1 for t,v in records):self.callback_seen=True
        physical=[(t,v[2:]) for t,v in records if t in ('B','S','W') or t=='J14' and v[2]==0 and v[5] in (1,2,3,5,7) or t=='L14' and v[2]==0 and v[4] in (1,2,3,4)]
        if status[0] and self.physical is not None:C.require(physical==self.physical,'denied operation changed bodies/joints/lists')
        self.physical=physical
        for t,v in records:
            if t=='T14':
                self.case_maxima.setdefault('traceTypes',{})[str(v[7])]=self.case_maxima.get('traceTypes',{}).get(str(v[7]),0)+1
                if v[4]==11:self.case_maxima['overflowTraceRows']=self.case_maxima.get('overflowTraceRows',0)+1
            if t=='J14' and v[5]==1 and v[10]>=3:self.case_maxima['sleepingJointRows']=self.case_maxima.get('sleepingJointRows',0)+1

    def operation(self,case,seq,operation):
        raws=super().operation(case,seq,operation)
        self.check_history(self.last_records,case,operation)
        return raws

    def helper(self,case):
        raws=[];records=[];size=0
        while True:
            raw,record=self.take();raws.append(raw);records.append(record);size+=len(raw)
            C.require(size<=13833216,'helper snapshot bound')
            if record[0]=='Z13':break
        summary=C.snapshot_check(records,case,len(case.ops)+1 if case.ops else 0,None,self.observer,helper_kind=case.guard_kind)
        self.case_maxima['snapshotBytes']=max(self.case_maxima['snapshotBytes'],size)
        self.case_maxima['liveJoints']=max(self.case_maxima['liveJoints'],summary[16])
        for tag,count in Counter(t for t,v in records).items():self.case_maxima['rowsPerTag'][tag]=max(self.case_maxima['rowsPerTag'].get(tag,0),count)
        C.require(summary[14]==self.positive,'helper Step counter')
        self.check_history(records,case,None)
        self.last_records=records
        if case.guard_kind==5:C.require(self.callback_seen,'real callback before helper5')
        self.max_snapshot=max(self.max_snapshot,size)
        return raws

def compare(streams,cases,error_sink=None):
    result={'N':len(cases),'profile':cases[0].profile,'complete':False,'unexecuted':[c.key for c in cases],
            'errors':[],'errorCount':0,'snapshots':0,'cases':[],'DucklingChecked':'d' in streams}
    try:readers={label:Reader(stream,label,cases) for label,stream in streams.items()}
    except (ValueError,AssertionError) as exc:
        result.update(validationError=str(exc),errorCount=1,word_comparison_ok=False,functional_C_D_ok=False,full_acceptance=False);return result
    def compare_rows(label,left,right,case,seq):
        for row,(a,b) in enumerate(zip_longest(left,right),1):
            if a==b:continue
            for token,(av,bv) in enumerate(zip_longest(a.split() if a else (),b.split() if b else ())):
                if av==bv:continue
                error={'key':case.key,'seq':seq,'comparison':label,'row':row,**C.difference_context(a or b,token),
                       'left':None if av is None else av.decode('ascii'),'right':None if bv is None else bv.decode('ascii')}
                result['errorCount']+=1
                if len(result['errors'])<64:result['errors'].append(error)
                if error_sink and error_sink.tell()<16*1024*1024:error_sink.write(json.dumps(error)+'\n')
    try:
        for case in cases:
            for reader in readers.values():reader.start(case)
            for seq,operation in enumerate(case.ops,1):
                snapshots={label:reader.operation(case,seq,operation) for label,reader in readers.items()}
                projected=[x for raw,record in zip(snapshots['c1'],readers['c1'].last_records,strict=True) if (x:=C.project(raw,record)) is not None]
                compare_rows('C0=projection(C1)',snapshots['c0'],projected,case,seq)
                if 'd' in snapshots:compare_rows('C1=D',snapshots['c1'],snapshots['d'],case,seq)
                result['snapshots']+=1
            if case.guard_kind:
                snapshots={label:reader.helper(case) for label,reader in readers.items()}
                projected=[x for raw,record in zip(snapshots['c1'],readers['c1'].last_records,strict=True) if (x:=C.project(raw,record)) is not None]
                compare_rows('C0=projection(C1)',snapshots['c0'],projected,case,len(case.ops)+1)
                if 'd' in snapshots:compare_rows('C1=D',snapshots['c1'],snapshots['d'],case,len(case.ops)+1)
                result['snapshots']+=1
            metrics={label:reader.finish(case) for label,reader in readers.items()}
            result['cases'].append({'key':case.key,'streams':metrics})
            result['unexecuted'].remove(case.key)
        result['streams']={label:reader.end() for label,reader in readers.items()}
        result['complete']=True
    except (ValueError,AssertionError,KeyError) as exc:
        result['validationError']=str(exc)
        result['errorCount']+=1
    result['word_comparison_ok']=result['complete'] and result['errorCount']==0
    result['functional_C_D_ok']=result['word_comparison_ok'] and result['DucklingChecked']
                                                                                 
    result['full_acceptance']=False
    return result

def verify_binary(binary,expected):
    actual=hashlib.sha256(Path(binary).read_bytes()).hexdigest()
    if actual!=expected:raise ValueError('binary SHA mismatch: '+str(binary))
    with Path(binary).open('rb') as stream:
        if stream.read(4)!=b'\x7fELF':raise ValueError('native ELF required')
    return actual

def binding(binaries):
    receipts={};source=None
    for label,binary in binaries.items():
        binary=Path(binary).resolve()
        path=binary.parent.parent/'build.json' if label=='d' else binary.parent/'budowa-14b.json'
        receipt=json.loads(path.read_text(encoding='utf-8'))
        if label=='d':
            if receipt.get('code')!=0 or not all(receipt.get(key) for key in ('fresh','ELF','sources_unchanged')):raise ValueError('incomplete D build')
            if receipt.get('archiveSHA256')!='f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519':raise ValueError('D compiler pin mismatch')
            product={name:sha for name,sha in receipt['sources'].items() if name.startswith('silnik/fizyka/') or name=='silnik/port/polaczenia.dk'}
            if not product or 'silnik/port/polaczenia.dk' not in product:raise ValueError('D product source pins missing')
            for name,sha in product.items():
                if hashlib.sha256((HERE.parents[1]/name).read_bytes()).hexdigest()!=sha:raise ValueError('D product source changed '+name)
            expected=receipt['binarySHA256']
        else:
            if not receipt.get('complete') or not receipt.get('source_unchanged') or not receipt.get('apparatus_unchanged') or receipt.get('protocol')!='PORT14B':raise ValueError('incomplete C B build')
            current=receipt['source_before']
            if source is not None and source!=current:raise ValueError('C0/C1 source pin differs')
            source=current;expected=receipt['binaries']['obs0' if label=='c0' else 'obs1']['sha256']
        verify_binary(binary,expected)
        receipts[label]={'receiptSHA':hashlib.sha256(path.read_bytes()).hexdigest(),'binarySHA':expected,'source_kind':receipt.get('source_kind'),'path':str(path)}
    return receipts

def run(binaries,cases,out,seconds=2100):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result={'complete':False,'unexecuted':[c.key for c in cases]};processes={};files=[]
    started=time.monotonic();timer=None;expired=threading.Event()
    try:bound=binding(binaries)
    except (ValueError,KeyError,FileNotFoundError) as exc:
        result.update(validationError=str(exc),errorCount=1,word_comparison_ok=False,functional_C_D_ok=False,full_acceptance=False);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
    with tempfile.TemporaryDirectory(prefix='input-',dir=out) as temp:
        try:
            inputs={}
            for side,decimal in (('c',False),('d',True)):
                path=Path(temp)/(side+'.input');sha=hashlib.sha256();size=0
                with path.open('wb') as stream:
                    for line in G.text(cases,decimal):raw=line.encode('ascii');sha.update(raw);size+=len(raw);stream.write(raw)
                inputs[side]={'path':path,'sha256':sha.hexdigest(),'bytes':size}
            for label,binary in binaries.items():
                inp=inputs['d' if label=='d' else 'c']['path'].open('rb');err=(out/(label+'.stderr')).open('wb');files += [inp,err]
                processes[label]=subprocess.Popen([str(Path(binary).resolve())],stdin=inp,stdout=subprocess.PIPE,stderr=err)
            def timeout():
                expired.set()
                for process in list(processes.values()):
                    if process.poll() is None:process.kill()
            timer=threading.Timer(seconds,timeout);timer.start()
            with (out/'errors.jsonl').open('w',encoding='utf-8') as errors:
                result=compare({label:p.stdout for label,p in processes.items()},cases,errors)
            result['builds_bound']=bound
            result['inputs']={side:{k:v for k,v in data.items() if k!='path'} for side,data in inputs.items()}
        finally:
            if timer:timer.cancel()
            for process in processes.values():
                if process.poll() is None and not result.get('complete'):process.terminate()
            codes={label:p.wait(timeout=30) for label,p in processes.items()}
            for file in files:file.close()
            result['exitCodes']=codes
            result['stderrBytes']={label:(out/(label+'.stderr')).stat().st_size for label in processes}
            result['binarySHA']={label:hashlib.sha256(Path(binary).read_bytes()).hexdigest() for label,binary in binaries.items()}
            result['seconds']=time.monotonic()-started
            result['secondsLimit']=seconds;result['timeout']=expired.is_set()
            result['word_comparison_ok']=result.get('word_comparison_ok',False) and all(code==0 for code in codes.values()) and not any(result['stderrBytes'].values())
            result['functional_C_D_ok']=result['word_comparison_ok'] and 'd' in binaries
            (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

def selftest(binaries,out):
    out.mkdir(parents=True,exist_ok=True);case=G.cases('DIRECT',1)[0]
    data=''.join(G.text((case,))).encode('ascii');raw={}
    for label,binary in binaries.items():
        result=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
        if result.returncode or result.stderr:raise ValueError('selftest native C failed')
        raw[label]=result.stdout
    def check(candidate):return compare({'c0':io.BytesIO(raw['c0']),'c1':io.BytesIO(raw['c1']),'d':io.BytesIO(candidate)},(case,))
    checks={'unmodified_transport':check(raw['c1'])['word_comparison_ok']}
    lines=raw['c1'].splitlines(keepends=True)
    at=next(i for i,l in enumerate(lines) if l.startswith(b'J14 ') and l.split()[6]==b'3')
    bad=list(lines);parts=bad[at].split();parts[8]=b'3f000000' if parts[8]!=b'3f000000' else b'40000000';bad[at]=b' '.join(parts)+b'\n'
    checks['wrong_private_word']=not check(b''.join(bad))['word_comparison_ok']
    checks['missing_END']=not check(b''.join(lines[:-1]))['word_comparison_ok']
    checks['duplicate_row']=not check(b''.join(lines[:at]+[lines[at]]+lines[at:]))['word_comparison_ok']
    bad=list(lines);bad[at],bad[at+1]=bad[at+1],bad[at]
    checks['wrong_order']=not check(b''.join(bad))['word_comparison_ok']
    bad=list(lines);bad[at]=bad[at].replace(b'00000000',b'0000000A',1)
    checks['malformed_word']=not check(b''.join(bad))['word_comparison_ok']
    try:verify_binary(binaries['c1'],'0'*64);checks['wrong_binary_SHA']=False
    except ValueError:checks['wrong_binary_SHA']=True
    receipt={'scope':'apparatus selftest; third stream is a deliberate copy of native C1, not a D physics result','checks':checks,'passed':sum(checks.values()),'total':len(checks),'complete':all(checks.values()),'inputSHA':hashlib.sha256(data).hexdigest()}
    (out/'selftest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=('PUBLIC','DIRECT','GUARD'));parser.add_argument('--N',type=int)
    for label in ('c0','c1'):parser.add_argument('--'+label,type=Path,required=True)
    parser.add_argument('--selftest',action='store_true');parser.add_argument('--d',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();binaries={k:getattr(args,k) for k in ('c0','c1','d') if getattr(args,k) is not None}
    if args.selftest:
        result=selftest(binaries,args.out);print(json.dumps(result));sys.exit(not result['complete'])
    if not args.profile:parser.error('--profile required')
    result=run(binaries,G.cases(args.profile,args.N),args.out)
    print(json.dumps({k:result.get(k) for k in ('complete','N','snapshots','errorCount','validationError','word_comparison_ok','functional_C_D_ok','seconds')}))
    sys.exit(0 if result['word_comparison_ok'] else 1)
