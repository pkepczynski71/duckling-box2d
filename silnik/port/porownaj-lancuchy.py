pass                                                                        

                                                                          
                                                                            
   
import argparse,hashlib,importlib.util,json,math,re,struct,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('lancuchy_inputs','przypadki-lancuchy.py')
SCHEMA={'CASE':(2,0),'ENDCASE':(1,0),'END':(1,0),'E13A':(3,64),'A13':(2,2),'KI13':(2,7),'D13A':(2,9),'K13A':(2,7),
        'P13A':(2,None),'T13A':(3,1),'V13A':(4,10),'ZA13':(2,8)}
def require(condition,message):
    if not condition:raise ValueError(message)
def finite(u):return math.isfinite(struct.unpack('<f',struct.pack('<I',u))[0])
def parse(raw):
    require(raw.endswith(b'\n') and len(raw)<=2049,'output LF/line envelope')
    require(re.fullmatch(rb'[!-~]+(?: [!-~]+)*\n',raw) is not None,'output canonical ASCII spacing')
    words=raw[:-1].decode('ascii').split(' ');tag=words[0]
    require(tag in SCHEMA,'unknown output tag '+tag);p,k=SCHEMA[tag]
    require(len(words)>=1+p,'output prefix arity '+tag)
    require(all(re.fullmatch(r'0|[1-9][0-9]*',s) for s in words[1:1+p]),'output decimal '+tag)
    prefix=tuple(int(s) for s in words[1:1+p]);payload=words[1+p:]
    require(all(re.fullmatch('[0-9a-f]{8}',s) for s in payload),'output H8 '+tag)
    data=tuple(int(s,16) for s in payload)
    if tag=='P13A':require(len(data)>=2 and data[0]<=8,'proxy count');k=2+2*data[0]
    require(len(data)==k,'payload arity '+tag)
    return tag,prefix,data

class Reader:
    def __init__(self,stream,profile,N,label):
        self.stream=stream;self.profile=profile;self.N=N;self.label=label;self.pending=None;self.sha=hashlib.sha256();self.bytes=0;self.tags={};self.history=None;self.calls=0;self.cases=0
        raw=stream.readline(2050);require(raw==f'PORT13A {profile} {N}\n'.encode(),'exact header '+label);self.accept([raw])
    def read(self):
        if self.pending is not None:r=self.pending;self.pending=None;return r
        raw=self.stream.readline(2050);require(bool(raw),'truncated stream '+self.label)
        return raw,parse(raw)
    def accept(self,rows):
        for raw in rows:
            self.sha.update(raw);self.bytes+=len(raw);tag=raw.split(b' ',1)[0].strip().decode('ascii');self.tags[tag]=self.tags.get(tag,0)+1
        require(self.bytes<=8425472,'frozen stream byte envelope '+self.label)
    def case(self,case):
        raw,row=self.read();require(row==('CASE',(case.id,len(case.ops)),()),'CASE order/completeness '+self.label);self.accept([raw]);self.history=None
    def end_case(self,case):
        raw,row=self.read();require(row==('ENDCASE',(case.id,),()),'ENDCASE order '+self.label);self.accept([raw]);self.cases+=1
    def end(self):
        raw,row=self.read();require(row==('END',(self.N,),()),'global END '+self.label);require(not self.stream.read(1),'trailing stdout '+self.label);self.accept([raw])
    def operation(self,case,seq,operation):
        records=[];raws=[]
        def take(tag,prefix):
            raw,row=self.read();require(row[0]==tag and row[1]==prefix,f'{self.label} {case.id}/{seq}: expected {tag}{prefix}, got {row[:2]}');records.append(row);raws.append(raw);return row[2]
        kind,*a=operation;key=(case.id,seq)
        if kind==0 and case.memory=='ciepla' and seq==1:self.history=tuple(a[46:53])
        require(take('E13A',(*key,kind))==tuple(a),'exact input echo '+self.label)
        status,reason=take('A13',key)
        require(status in (0,4,5) and reason in (0,82),'13a status/reason')
        require(not status or a[0]==1,'raw call cannot have semantic refusal')
        require(reason!=82 or status==5,'cache reason status')
        require(status!=4 or reason==0,'geometry reason')
        counts=[1,1,0,0,0,0,0,0]
        if status==0 and kind==0:
            ki=take('KI13',key);counts[2]=1
            expected=tuple(a[46:53]) if case.memory!='ciepla' or seq==1 else self.history
            require(ki==expected,'own effective warm/input cache '+self.label)
            d=take('D13A',key);counts[3]=1
            require(all(finite(x) for x in d[:7]) and d[7]<=20 and d[8]<=23,'finite output/iterations/capacity')
            require(struct.unpack('<f',struct.pack('<I',d[6]))[0]>=0,'nonnegative distance')
            k=take('K13A',key);counts[4]=1
            require(k[0]<=3 and all(x<=255 for x in k[1:]),'cache physical domain')
            for i in range(3):
                if i<k[0]:require(k[1+i]<a[1] and k[4+i]<a[23],'active output cache index')
                else:require(k[1+i]==ki[1+i] and k[4+i]==ki[4+i],'inactive cache canary preserved')
            self.history=k
            ti=0
            while True:
                raw,row=self.read()
                if row[0]!='T13A':self.pending=(raw,row);break
                require(a[54]==1 and row[1]==(*key,ti),'trace index/mode')
                count=row[2][0];require(1<=count<=3,'active simplex count')
                records.append(row);raws.append(raw);counts[6]+=1
                for vi in range(count):
                    v=take('V13A',(*key,ti,vi));counts[7]+=1
                    require(v[0] in (0,1),'defined(a) bool');require(v[0]!=0 or v[7]==0,'undefined a encoded +0')
                    require(all(finite(x) for x in v[1:8]),'finite defined trace words')
                    require(v[8]<a[1] and v[9]<a[23],'trace source indices')
                ti+=1
            require(ti<=a[53] and (self.profile!='R' or ti<=1),'trace actual capacity/profile')
        elif status==0:
            p=take('P13A',key);counts[5]=1
            require(p[0]==min(a[1],8) and p[1]==a[2],'proxy clamp/radius bits')
            require(all(finite(x) for x in p[1:]),'finite proxy output')
            if kind==1:require(p[2:]==tuple(a[3:3+2*p[0]]),'MakeProxy copies exact point bits')
        require(take('ZA13',key)==tuple(counts),'exact per-call counters')
        self.calls+=1;return records,raws

def project(records):
    result=[]
    for tag,p,h in records:
        if tag in ('T13A','V13A','ZA13'):continue
        result.append((tag,p,h[:8] if tag=='D13A' else h))
    return result

def independent_model_checker():
    pass                                                                     
    model=load('lancuchy_independent_model','model-lancuchy.py');histories={}
    def check(label,case,seq,operation,records):
        key=(label,case.id)
        flattened=[(tag,(*prefix,*payload)) for tag,prefix,payload in records]
        histories[key]=model.check_operation(flattened,case.id,seq,operation[0],operation[1:],
                profile='D' if label.endswith('_d') else 'R',history=histories.get(key),memory=case.memory)
    return check

def compare_streams(streams,cases,*,model_check=None,diagnostic=False):
    start=time.monotonic();labels={'c_r':'R','d_r':'R','c_d':'D','d_d':'D'}
    require(set(streams)==set(labels),'four R/D streams required')
    readers={name:Reader(streams[name],profile,len(cases),name) for name,profile in labels.items()}
    result={'N':len(cases),'completed_cases':0,'calls_per_side':0,'models_checked':model_check is not None,'diagnostic_only':diagnostic,'first_difference':None,'errors':[],'model_errors':[],'cases':[]}
    try:
        for case in cases:
            for r in readers.values():r.case(case)
            for seq,op in enumerate(case.ops,1):
                groups={name:r.operation(case,seq,op) for name,r in readers.items()}
                if model_check:
                    for label,(records,_) in groups.items():
                        try:model_check(label,case,seq,op,records)
                        except Exception as exc:result['model_errors'].append({'label':label,'id':case.id,'seq':seq,'error':str(exc)})
                for a,b in (('c_r','d_r'),('c_d','d_d')):
                    require(groups[a][0]==groups[b][0],f'full words differ {a}/{b} id{case.id} seq{seq}')
                for a,b in (('c_r','c_d'),('d_r','d_d')):
                    require(project(groups[a][0])==project(groups[b][0]),f'R/D physics projection differs {a}/{b} id{case.id} seq{seq}')
                for name,(_,raws) in groups.items():readers[name].accept(raws)
                result['calls_per_side']+=1
            for r in readers.values():r.end_case(case)
            result['completed_cases']+=1;result['cases'].append({'id':case.id,'family':case.family,'calls':len(case.ops),'full_words':True,'projection':True,'models':model_check is not None})
        for r in readers.values():r.end()
        result['global_END_checked']=True
        if model_check is None and not diagnostic:result['errors'].append('independent13a model missing; fields-only diagnostic is not acceptance')
        if result['model_errors']:result['errors'].append('independent model failures: '+str(len(result['model_errors'])))
    except Exception as exc:
        result['errors'].append(str(exc));result['global_END_checked']=False
        result['first_difference']={'case':case.id if 'case' in locals() else None,'seq':seq if 'seq' in locals() else None,'reason':str(exc)}
        if 'groups' in locals():
                                                                      
            window={name:[raw.decode('ascii',errors='replace').rstrip() for raw in rows[1][:16]] for name,rows in groups.items()}
            require(sum(len(x) for lines in window.values() for x in lines)<=65536,'diagnostic window limit')
            result['first_difference']['window']=window
    result['streams']={name:{'sha256':r.sha.hexdigest(),'bytes':r.bytes,'tags':r.tags,'cases':r.cases,'calls':r.calls} for name,r in readers.items()}
    result['seconds']=time.monotonic()-start
    result['comparison_ok']=not result['errors'] and result.get('global_END_checked',False) and model_check is not None and not diagnostic
    result['full_acceptance']=False
    result['acceptance_scope']='Comparison only; guards, mutations, branch coverage and regression checks are separate requirements'
    return result

def compare_files(c_r,d_r,c_d,d_d,cases,**kw):
    from contextlib import ExitStack
    with ExitStack() as stack:
        streams={name:stack.enter_context(Path(path).open('rb')) for name,path in zip(('c_r','d_r','c_d','d_d'),(c_r,d_r,c_d,d_d))}
        return compare_streams(streams,cases,**kw)

def c_projection(r_path,d_path,cases):
    pass                                                                       
    from contextlib import ExitStack
    with ExitStack() as stack:
        readers={p:Reader(stack.enter_context(Path(path).open('rb')),p,len(cases),'C-'+p) for p,path in (('R',r_path),('D',d_path))}
        result={'C_only':True,'Duckling_compared':False,'models_checked':False,'full_acceptance':False,'N':len(cases),'completed_cases':0,'calls':0,'cases':[]}
        for case in cases:
            for r in readers.values():r.case(case)
            item={'id':case.id,'family':case.family,'calls':len(case.ops),'maxA':0,'maxB':0,'maxIterations':0,'maxTrace':0,'maxSimplex':0,'maxCache':0,'undefinedTraceVertices':0,'positiveSteps':0,'worldBSCChain':[0,0,0,0]}
            for seq,op in enumerate(case.ops,1):
                groups={p:r.operation(case,seq,op) for p,r in readers.items()}
                require(project(groups['R'][0])==project(groups['D'][0]),f'C R/D projection {case.id}/{seq}')
                for p,(_,raws) in groups.items():readers[p].accept(raws)
                item['maxA']=max(item['maxA'],op[2]);item['maxB']=max(item['maxB'],op[24] if op[0]==0 else 0)
                rows=groups['D'][0]
                item['maxTrace']=max(item['maxTrace'],sum(row[0]=='T13A' for row in rows))
                for tag,_,h in rows:
                    if tag=='D13A':item['maxIterations']=max(item['maxIterations'],h[7])
                    if tag=='K13A':item['maxCache']=max(item['maxCache'],h[0])
                    if tag=='T13A':item['maxSimplex']=max(item['maxSimplex'],h[0])
                    if tag=='V13A':item['undefinedTraceVertices']+=h[0]==0
                result['calls']+=1
            for r in readers.values():r.end_case(case)
            item['C_R_D_projection']=True;item['full_case_executed_in_C']=True
            item['limit20_observed']=item['maxIterations']==20
            result['cases'].append(item);result['completed_cases']+=1
        for r in readers.values():r.end()
        result['global_END_checked']=True
        result['streams']={p:{'sha256':r.sha.hexdigest(),'bytes':r.bytes,'tags':r.tags} for p,r in readers.items()}
        return result

def dependencies13b():
    pass                                                                          
    import inspect
    base=load('lancuchy_base12_compare','porownaj-zywy.py')
    model=load('lancuchy_model13b','model-lancuchy.py')
    source=inspect.getsource(base.check_snapshot)
    source=source.replace('def check_snapshot(', 'def check_base13b(')
    source=source.replace('(1 if code>=80 else 0)','(1 if 80<=code<=92 else 0)')
    source=source.replace('if code>=80:', 'if 80<=code<=92:')
    source=source.replace("status=rows['R'][0][3] if rows['R'] else rows['AP12'][0][2]",
                          "status=0 if code>=100 else rows['R'][0][3] if rows['R'] else rows['AP12'][0][2]")
    namespace=dict(vars(base));exec(compile(source,'<BASE12 separate PORT13B specialization>','exec'),namespace)
    return base,model,namespace['check_base13b']

class Reader13b:
    def __init__(self,stream,N,label,dependencies,*,observer,history=True):
        from collections import Counter
        self.stream,self.N,self.label,self.observer=stream,N,label,observer
        self.base,self.model,self.base_check=dependencies
        self.sha=hashlib.sha256();self.size=0;self.tags=Counter();self.tag_bytes=Counter();self.completed=0;self.positive=0
        self.timing={'read_parse_wait_seconds':0.,'base12_validation_seconds':0.,'new_groups_validation_seconds':0.,'history_validation_seconds':0.}
        self.max_snapshot_bytes=0;self.max_line_bytes=0
        self.order=list(self.base.ORDER);self.order[0:1]=[('E13B',),('EP13B',),('EU13B',),('A13',)]
        at=self.order.index(('X',));self.order[at:at]=[('CN13',),('V13',),('CQ13','QL13'),('CS13',),('PC13',),('COPY13','CV13','CE13','ENDCOPY13')]
        at=self.order.index(('I8',));self.order[at:at]=[(x,) for x in ('CH13','CI13','CM13','BH13','IP13','CG13')]
        self.order += [('I13',),('Z13',)];self.rank={t:i for i,group in enumerate(self.order) for t in group}
        self.new=(set(self.model.SCHEMA13B)|{'IP13'})-{'G'}
        self.history=None
        if history and hasattr(self.model,'Model13B'):self.history=self.model.Model13B(observer=observer)
        self.take(('PORT13B',(N,)))
    def take(self,expected=None):
        raw=self.stream.readline(131073)
        self.max_line_bytes=max(self.max_line_bytes,len(raw))
        require(raw and len(raw)<=131072,'13b truncated/row envelope '+self.label)
        tag=raw.split(b' ',1)[0].strip().decode('ascii')
        record=self.model.parse13b(raw) if tag in self.new else self.base.parse_record(raw.decode('ascii'))
        if expected is not None:require(record==expected,'13b framing '+self.label+': '+repr(record))
        self.sha.update(raw);self.size+=len(raw);self.tags[tag]+=1;self.tag_bytes[tag]+=len(raw)
        require(self.size<=4934991872,'13b frozen per-side envelope')
        return raw,record
    def case(self,case):
        self.take(('CASE',(case.id,len(case.ops))));self.completed=self.positive=0
        self.maxima={'liveWorlds':0,'B':0,'S':0,'C':0,'Chain':0,'materials':0,'copies':0,'P':0,'U':0}
        self.pools={'B':{},'S':{},'Chain':{}}
        if self.history is not None and hasattr(self.history,'reset'):self.history.reset(case.id)
    def operation(self,case,seq,operation):
        records=[];raws=[];size=0;rank=-1;started=time.monotonic()
        while True:
            raw,record=self.take();tag,v=record;size+=len(raw)
            require(size<=1204576,'13b snapshot envelope')
            require(v[:2]==(case.id,seq),'13b case/sequence '+tag)
            require(tag in self.rank and self.rank[tag]>=rank,'13b group order '+tag);rank=self.rank[tag]
            records.append(record);raws.append(raw)
            if tag=='Z13':break
        self.timing['read_parse_wait_seconds']+=time.monotonic()-started;self.max_snapshot_bytes=max(self.max_snapshot_bytes,size)
                                                                          
                                                                            
        inherited=[('E' if t=='E13B' else t,v) for t,v in records if t not in self.new or t=='E13B']
        started=time.monotonic();self.completed,self.positive=self.base_check(case.id,seq,(operation['opcode'],*operation['a']),
            inherited,self.observer,self.completed,self.positive,profile=11)
        self.timing['base12_validation_seconds']+=time.monotonic()-started
        raw_world_map={v[3]-1:v[2] for t,v in records if t=='W'}
        new=[r for r in records if r[0] in self.new and r[0] not in ('CASE','ENDCASE','END')]
        started=time.monotonic();self.model.check13b_groups(new,operation,case.id,seq,raw_world_map,observer=self.observer)
        self.timing['new_groups_validation_seconds']+=time.monotonic()-started
        started=time.monotonic()
        if self.history is not None:self.history.check(case.id,seq,operation,records,self.observer)
        self.timing['history_validation_seconds']+=time.monotonic()-started
                                                                        
                                                                             
                                                                            
        for tag,values in records:
            if tag in ('B','S'):
                owner=values[8]|values[9]<<32;key=owner
                self.pools[tag][key]=max(self.pools[tag].get(key,0),values[3])
            if tag=='CN13':
                owner=values[9]|values[10]<<32
                self.pools['Chain'][owner]=max(self.pools['Chain'].get(owner,0),values[3])
        from collections import Counter
        counts=Counter(t for t,v in records)
        for k in self.pools:self.maxima[k]=max(self.maxima[k],sum(self.pools[k].values()))
        for k,value in (('liveWorlds',counts['W']),('materials',counts['CM13']),('copies',sum(t=='COPY13' and v[3]==0 for t,v in records)),('P',len(operation['points'])),('U',len(operation['materials']))):
            self.maxima[k]=max(self.maxima[k],value)
        require(self.maxima['liveWorlds']<=2 and self.maxima['B']<=16 and self.maxima['S']<=128 and self.maxima['Chain']<=16,'13b historical population bounds')
        require(not counts['NC9'] and self.positive==0,'13b no contacts/positive Step')
        require(self.maxima['materials']<=256 and self.maxima['copies']<=4,'13b materials/copies bounds')
        return raws,records
    def end_case(self,case):self.take(('ENDCASE',(case.id,)))
    def end(self):
        self.take(('END',(self.N,)));require(not self.stream.read(1),'13b trailing output '+self.label)
        return {'sha256':self.sha.hexdigest(),'bytes':self.size,'tags':dict(self.tags),'bytes_per_tag':dict(self.tag_bytes),'END_EOF':True,
                'base12_and_new_groups_checked':True,'history_model_checked':self.history is not None,
                'full_ownership_ready':bool(self.history is not None and getattr(self.history,'full_ownership_ready',False)),
                'validation_timing':self.timing,'max_snapshot_bytes':self.max_snapshot_bytes,'max_line_bytes':self.max_line_bytes}

def compare13b_streams(streams,cases,*,require_history=True,diagnostic=False):
    pass                                                                         
    from itertools import zip_longest
    require(set(streams)=={'c0','c1','d'},'three PORT13B streams required')
    dependencies=dependencies13b();start=time.monotonic()
    readers={name:Reader13b(stream,len(cases),name,dependencies,observer=name!='c0',history=not diagnostic) for name,stream in streams.items()}
    result={'N':len(cases),'snapshots':0,'cases':[],'errors':[],'first_difference':None,'global_END_checked':False,
            'comparison_ok':False,'full_acceptance':False,'models_checked':False,'diagnostic_only':diagnostic,'comparison_seconds':0.}
    for case in cases:
        for r in readers.values():r.case(case)
        row={'id':case.id,'family':case.family,'operations':len(case.ops),'guard_required':case.guard_required,'validated':{}}
        for seq,operation in enumerate(case.ops,1):
            snapshots={};validation_errors={}
            for name,r in readers.items():
                try:snapshots[name]=r.operation(case,seq,operation)
                except Exception as exc:validation_errors[name]=str(exc)
            if validation_errors:
                result['errors'].append({'id':case.id,'seq':seq,'validation':validation_errors})
                                                                              
                                                                                
                return result
            c0,c1,d=(snapshots[k][0] for k in ('c0','c1','d'))
            comparison_start=time.monotonic()
            projected=[x for raw in c1 if (x:=dependencies[1].projection13b_line(raw)) is not None]
            for name,left,right in (('C0=projection(C1)',c0,projected),('C1=D',c1,d)):
                mismatch=next(((i,a,b) for i,(a,b) in enumerate(zip_longest(left,right),1) if a!=b),None)
                if mismatch:
                    i,a,b=mismatch;error={'id':case.id,'seq':seq,'comparison':name,'record':i,'left':None if a is None else a.decode('ascii'),'right':None if b is None else b.decode('ascii')}
                    result['errors'].append(error)
                    if result['first_difference'] is None:
                        lo=max(0,i-5);hi=i+5
                        error['window_left']=[x.decode('ascii') for x in left[lo:hi]]
                        error['window_right']=[x.decode('ascii') for x in right[lo:hi]]
                        result['first_difference']=error
            result['comparison_seconds']+=time.monotonic()-comparison_start
            result['snapshots']+=1
        for name,r in readers.items():
            r.end_case(case);row['validated'][name]=True
        row['maxima']={name:dict(r.maxima) for name,r in readers.items()};result['cases'].append(row)
    result['streams']={name:r.end() for name,r in readers.items()};result['global_END_checked']=True
    result['word_comparison_ok']=not result['errors']
    result['models_checked']=all(r.history is not None for r in readers.values())
    result['full_ownership_models_ready']=all(r.history is not None and getattr(r.history,'full_ownership_ready',False) for r in readers.values())
    if require_history and not result['models_checked']:result['errors'].append('Model13B history checker is missing; group grammar alone is insufficient')
    if require_history and result['models_checked'] and not all(getattr(r.history,'full_ownership_ready',False) for r in readers.values()):
        result['errors'].append('Model reports full_ownership_ready=False; semantic checks remain incomplete')
    result['comparison_ok']=not result['errors'];result['seconds']=time.monotonic()-start
    return result

def c_projection13b(c0,c1,cases):
    pass                                                                       
    dep=dependencies13b();readers=[Reader13b(stream,len(cases),name,dep,observer=obs)
        for stream,name,obs in ((c0,'C0',False),(c1,'C1',True))]
    result={'scope':'C-only','Duckling_checked':False,'full_acceptance':False,'errors':[],'cases':[],'snapshots':0}
    for case in cases:
        for r in readers:r.case(case)
        for seq,operation in enumerate(case.ops,1):
            a=readers[0].operation(case,seq,operation)[0];b=readers[1].operation(case,seq,operation)[0]
            p=[x for raw in b if (x:=dep[1].projection13b_line(raw)) is not None]
            if a!=p:result['errors'].append({'id':case.id,'seq':seq,'error':'C0 != projection(C1)'})
            result['snapshots']+=1
        for r in readers:r.end_case(case)
        result['cases'].append({'id':case.id,'family':case.family,'maxima':readers[1].maxima.copy(),'operations':len(case.ops),'guard_required':case.guard_required})
    result['streams']={r.label:r.end() for r in readers};result['comparison_ok']=not result['errors']
    return result

SCHEMA13C={'PORT13C':(1,0),'E13C':(3,64),'KI13':(2,7),'M13C':(2,30),'K13C':(2,7),'DC13':(2,5)}

class Reader13c:
    pass                                                                       

                                                                           
                                                                           
                                                                      
       
    def __init__(self,stream,N,label,dependencies,observer=True):
        from collections import Counter
        self.stream,self.N,self.label,self.observer=stream,N,label,observer
        self.base,self.model,self.base_check=dependencies
        self.sha=hashlib.sha256();self.size=0;self.tags=Counter();self.tag_bytes=Counter();self.positive=0;self.completed=0
        self.max_line_bytes=0;self.max_snapshot_bytes=0;self.history=None
        if hasattr(self.model,'Model13C'):self.history=self.model.Model13C(observer=observer)
        self.order=list(self.base.ORDER);self.order[0:1]=[('E13C',),('EP13B',),('EU13B',),('A13',)]
        at=self.order.index(('X',));self.order[at:at]=[('CN13',),('V13',),('CQ13','QL13'),('CS13',),('PC13',),('COPY13','CV13','CE13','ENDCOPY13')]
        at=self.order.index(('I8',));self.order[at:at]=[(x,) for x in ('CH13','CI13','CM13','BH13','IP13','CG13')]
        self.order += [('I13',),('Z13',)];self.rank={t:i for i,group in enumerate(self.order) for t in group}
        self.new=((set(self.model.SCHEMA13B)|{'IP13','E13C'})-{'G'})
        self.take(('PORT13C',(N,)))
    def take(self,expected=None):
        raw=self.stream.readline(131073);self.max_line_bytes=max(self.max_line_bytes,len(raw))
        require(raw and len(raw)<=131072 and raw.endswith(b'\n'),'13c output LF/line envelope '+self.label)
        tag=raw.split(b' ',1)[0].decode('ascii')
        if tag in SCHEMA13C:
            require(re.fullmatch(rb'[!-~]+(?: [!-~]+)*\n',raw) is not None,'13c canonical ASCII/spacing')
            parts=raw[:-1].split(b' ');d,k=SCHEMA13C[tag];require(len(parts)==1+d+k,tag+' arity')
            vals=[]
            for j,part in enumerate(parts[1:]):
                require(re.fullmatch(rb'(?:0|[1-9][0-9]*)' if j<d else rb'[0-9a-f]{8}',part) is not None,tag+' canonical word')
                val=int(part,10 if j<d else 16);require(val<=0xffffffff,tag+' u32');vals.append(val)
            record=tag,tuple(vals)
        elif tag in self.new:record=self.model.parse13b(raw)
        else:record=self.base.parse_record(raw.decode('ascii'))
        if expected is not None:require(record==expected,'13c '+self.label+' expected '+repr(expected)+' got '+repr(record))
        self.sha.update(raw);self.size+=len(raw);self.tags[tag]+=1;self.tag_bytes[tag]+=len(raw)
        return raw,record
    def case(self,case):
        self.case_bytes=self.size;self.case_tag_start=self.tags.copy()
        raw,_=self.take(('CASE',(case.id,len(case.ops))));self.positive=self.completed=0;self.cache=None
        self.case_sha=hashlib.sha256(raw)
        if self.history is not None and hasattr(self.history,'reset'):self.history.reset(case.id)
    def operation(self,case,seq,operation):
        raws=[];records=[]
        if case.id<=384:
            def expect(tag,payload=None):
                raw,row=self.take();require(row[0]==tag and row[1][:2]==(case.id,seq),'direct '+tag+' framing')
                if payload is not None:require(row[1][2:]==payload,tag+' exact words')
                raws.append(raw);records.append(row);return row[1][2:]
            a=operation['a'];expect('E13C',(120,*a));status,reason=expect('A13')
            require(status in (0,4,5) and reason in (0,82,84,85),'direct status/reason domain')
            require(not status or a[1]==1,'raw direct cannot return checked refusal')
            if not status:
                ki=expect('KI13');warm=case.id in range(65,129) or case.id in range(193,257) or case.id in range(321,385)
                expected=self.cache if warm and seq>1 else tuple(a[36:43]);require(ki==expected,'own previous K / cold explicit seed')
                m=expect('M13C');k=expect('K13C');require(len(m)==30 and m[3] in range(3),'M30 count')
                require(a[0]!=0 or m[3]<=1,'circle max1point')
                require(k[0]<=3 and all(x<=255 for x in k[1:]),'physical cache words')
                if a[0]==0:require(k==ki,'circle ignores and preserves cache7')
                for point in range(2):
                    q=m[4+13*point:17+13*point]
                    require(all(finite(u) for u in q[:11]),'manifold finite')
                    require(q[11]<=65535 and q[12] in (0,1),'manifold id/persisted domain')
                    if point>=m[3]:require(q==(0,)*13,'unused manifold point bitwise+0')
                require(all(finite(u) for u in m[:3]),'normal/rolling finite');self.cache=k
            expect('DC13',(1,1,int(not status),int(not status),int(not status)))
        else:
            rank=-1;size=0
            while True:
                raw,record=self.take();tag,v=record;size+=len(raw)
                require(v[:2]==(case.id,seq),'public case/seq '+tag)
                require(tag in self.rank and self.rank[tag]>=rank,'public13c group order '+tag);rank=self.rank[tag]
                raws.append(raw);records.append(record)
                if tag=='Z13':break
            inherited=[('E' if t=='E13C' else t,v) for t,v in records if t not in self.new or t=='E13C']
            self.completed,self.positive=self.base_check(case.id,seq,(operation['opcode'],*operation['a']),inherited,self.observer,self.completed,self.positive,profile=13)
            z=records[-1][1];require(z[14]==self.positive and z[15]==seq,'Z13 exact positive Step count and ordinal')
            new=[]
            for t,v in records:
                if t not in self.new or t in ('CASE','ENDCASE','END'):continue
                if t=='E13C':t='E13B'
                if t=='Z13':v=(*v[:14],0,*v[15:])
                new.append((t,v))
            world_map={v[3]-1:v[2] for t,v in records if t=='W'}
            self.model.check13b_groups(new,operation,case.id,seq,world_map,observer=self.observer)
        if self.history is not None:self.history.check(case.id,seq,operation,records,self.observer)
        for raw in raws:self.case_sha.update(raw)
        self.max_snapshot_bytes=max(self.max_snapshot_bytes,sum(map(len,raws)))
        return raws,records
    def end_case(self,case):
        raw,_=self.take(('ENDCASE',(case.id,)));self.case_sha.update(raw)
        return dict(bytes=self.size-self.case_bytes,sha256=self.case_sha.hexdigest(),tags=dict(self.tags-self.case_tag_start),positive_steps=self.positive)
    def end(self):
        self.take(('END',(self.N,)));require(not self.stream.read(1),'13c trailing output '+self.label)
        return dict(bytes=self.size,sha256=self.sha.hexdigest(),tags=dict(self.tags),bytes_per_tag=dict(self.tag_bytes),END_EOF=True,max_line_bytes=self.max_line_bytes,max_snapshot_bytes=self.max_snapshot_bytes,history_model_checked=self.history is not None,full_ownership_ready=bool(self.history is not None and getattr(self.history,'full_ownership_ready',False)))

def compare13c_streams(streams,cases,*,require_history=True,error_sink=None,progress=None):
    pass                                                                       
    from itertools import zip_longest
    if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
    require(set(streams) in ({'c0','c1'},{'c0','c1','d'}),'C0/C1 and optional native D required')
    require([c.id for c in cases]==list(range(1,len(cases)+1)),'PORT13C legal prefix ids1..N')
    dep=dependencies13b();readers={k:Reader13c(s,len(cases),k,dep,observer=k!='c0') for k,s in streams.items()}
    result=dict(N=len(cases),DIRECT=0,PUBLIC=0,snapshots=0,positive_steps=0,cases=[],errors=[],error_count=0,word_comparison_ok=False,comparison_ok=False,full_acceptance=False,global_END_checked=False)
    diagnostic_bytes=0
    for case in cases:
        for r in readers.values():r.case(case)
        for seq,o in enumerate(case.ops,1):
            snapshots={};errors={}
            for k,r in readers.items():
                try:snapshots[k]=r.operation(case,seq,o)[0]
                except Exception as exc:errors[k]=str(exc)
            if errors:result['errors'].append(dict(id=case.id,seq=seq,validation=errors));return result
            projected=[x for raw in snapshots['c1'] if (x:=dep[1].projection13b_line(raw)) is not None]
            pairs=[('C0=projection(C1)',snapshots['c0'],projected)]
            if 'd' in readers:pairs.append(('C1=D',snapshots['c1'],snapshots['d']))
            for name,left,right in pairs:
                mismatch=next(((i,a,b) for i,(a,b) in enumerate(zip_longest(left,right),1) if a!=b),None)
                if mismatch:
                    i,a,b=mismatch;error=dict(id=case.id,seq=seq,comparison=name,row=i,left_sha256=None if a is None else hashlib.sha256(a).hexdigest(),right_sha256=None if b is None else hashlib.sha256(b).hexdigest())
                    result['error_count']+=1
                    if error_sink is not None:error_sink.write(json.dumps(error,separators=(',',':'))+'\n')
                    if len(result['errors'])<64:
                        detail=dict(error,left=None if a is None else a[:4096].decode(),right=None if b is None else b[:4096].decode());size=len(json.dumps(detail).encode())
                        if diagnostic_bytes+size<=65536:result['errors'].append(detail);diagnostic_bytes+=size
            result['snapshots']+=1
        per={k:r.end_case(case) for k,r in readers.items()};result['cases'].append(dict(id=case.id,family=case.family,operations=len(case.ops),streams=per))
        result['DIRECT' if case.id<=384 else 'PUBLIC']+=1;result['positive_steps']+=readers['c1'].positive
        if progress is not None:progress(result['cases'][-1],result)
    result['streams']={k:r.end() for k,r in readers.items()};result['global_END_checked']=True
    result['word_comparison_ok']=not result['error_count'] and not result['errors'];result['Duckling_checked']='d' in readers
    result['models_checked']=all(r.history is not None for r in readers.values())
    if require_history and not result['models_checked']:result['errors'].append('Model13C unavailable; grammar and word equality do not establish semantic/history coverage')
    if require_history and not all(r.history is not None and getattr(r.history,'full_ownership_ready',False) for r in readers.values()):result['errors'].append('full_ownership_ready=False inherited12 remains explicit')
    result['comparison_ok']=not result['errors'];return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('c-r','d-r','c-d','d-d'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--N',type=int,default=128);p.add_argument('--diagnostic',action='store_true');p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    result=compare_files(a.c_r,a.d_r,a.c_d,a.d_d,g.cases(a.N),model_check=None if a.diagnostic else independent_model_checker(),diagnostic=a.diagnostic)
    a.manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('cases','streams','first_difference')},ensure_ascii=False));sys.exit(bool(result['errors']))
