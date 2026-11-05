pass                                                                            
from collections import defaultdict
import hashlib
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


f=load('solver_native_fixtures','fixtury-solver.py')
m=load('solver_native_model','model-solver.py')
n=load('solver_native_negatives','ujemne-solver.py')
w=load('solver_native_witnesses','wejscia-solver-oslony.py')
base=load('solver_native_scope','mutacje-ruch-swiata.py')
apply=base.apply


def recipes():return json.loads((HERE/'mutacje-solver.json').read_bytes())


def applicability(root,manifest=None):
    manifest=manifest or recipes();result=[]
    for recipe in manifest['native_mutations']:
        try:
            text=(Path(root)/recipe['source']).read_text(encoding='utf-8')
            for edit in recipe.get('fixture_edits',[]):text=apply(text,edit)
            changed=apply(text,recipe)
            if changed==text:raise ValueError('source mutation did not change bytes')
            result.append({'name':recipe['name'],'single_hit':True})
        except (OSError,ValueError) as exc:result.append({'name':recipe['name'],'single_hit':False,'error':str(exc)})
    return result


def reader_fixture(source,recipe):
    lo,hi=base.function_span(source,recipe['scope']);block=source[lo:hi]
    old=recipe['guard_statement'];condition=recipe['condition']
    if block.count(old)!=1:raise ValueError('reader boundary must match exactly once')
    observer='\n    if (inputOk and ('+condition+')) { io.writeStr("GUARD10 PASS '+recipe['error']+'\\n"); failureCode = 0i64; inputOk = false; '+recipe['boundary_return']+' }'
    baseline=source[:lo]+block.replace(old,old+observer,1)+source[hi:]
                                                                          
    baseline=baseline.replace('return 2i64;','return failureCode;')
    anchor=old.replace('return 2i64;','return failureCode;')
    changed=anchor.replace(condition,'false',1)
    mutant=apply(baseline,{'name':recipe['name'],'scope':recipe['scope'],'expression':anchor,'replacement':changed})
    return baseline,mutant


def public_records(data,rows_by_case,*,guard=None,properties=True,private=True):
    pass                                                                  

                                                                          
                                                                          
       
    records=[m.parse(line) for line in data.decode('ascii').splitlines(keepends=True)]
    require=m.require
    expected_header=('GUARD10',(1,)) if guard else ('PORT10',(len(rows_by_case),))
    require(records and records[0]==expected_header,'native output header')
    model=m.OwnershipModel();cursor=1
    if guard:
        require(records[cursor]==('G',(1,guard.kind,guard.seed,len(guard.rows))),'GUARD G echo');cursor+=1
        require(records[cursor]==('GA',(1,*guard.words)),'GUARD GA bit echo');cursor+=1
        model.allow_contact_speed_inf=guard.group=='G10-PUBLIC-STEP'
    for ident,operations in rows_by_case:
        require(records[cursor]==('CASE',(ident,len(operations))),'native CASE');cursor+=1
        model.begin_case();model.case=ident
        for seq,operation in enumerate(operations,1):
            snapshot=defaultdict(list)
            while cursor<len(records) and records[cursor][0]!='Z10':
                tag,value=records[cursor];cursor+=1
                require(tag not in ('END','ENDCASE','GR10'),'native truncated snapshot')
                snapshot[tag].append(value)
            require(cursor<len(records),'native missing Z10')
            tag,value=records[cursor];cursor+=1;snapshot[tag].append(value)
            require(snapshot['E']==[(ident,seq,*operation)],'native exact E')
            require(len(snapshot['R'])==(2 if operation[0]==16 else 1),'native R count')
            if guard and properties:
                require(len(snapshot['Z9'])==1,'GUARD Z9 required')
                z9=snapshot['Z9'][0]
                seeded=guard.kind in (4,8) and seq>guard.seed
                require(z9[14:16]==(4,int(seeded)),'GUARD profile/FIXTURE_INPUT after seed')
                require(z9[-2:]==snapshot['Z8'][0][-2:],'GUARD Z9/Z8 ticket agreement')
            if properties:model.check(ident,seq,operation,[(t,v) for t,values in snapshot.items() for v in values],private)
            if guard and seq==guard.seed:
                if guard.kind==4:model.last_ticket=guard.words[1]|guard.words[2]<<32
                elif guard.kind==8:
                    require(cursor<len(records) and records[cursor][0]=='GR10','missing actual seeded status helper');cursor+=1
        require(records[cursor]==('ENDCASE',(ident,)),'native ENDCASE');cursor+=1
    require(records[cursor:]==[('END',(len(rows_by_case),))],'native exact END/no tail')
    if properties and guard and guard.helper is not None:m.guard_result(guard,records)
    if properties and guard and guard.last_status is not None:
        require([v for t,v in records if t=='R'][-1][3]==guard.last_status,guard.name+' expected final semantic status')
    if properties and guard and guard.name in ('G10-LEGACY-LIMIT','G10-HIT-READ-PURE'):
        require(all(v[-2:]==(0xffffffff,0xffffffff) for t,v in records if t=='Z8' and v[1]>guard.seed),'MAX seed/read-only counter')
        if guard.name=='G10-HIT-READ-PURE':
            require(any(t=='HR10' for t,v in records) and any(t=='HG10' for t,v in records),'MAX read-pure needs a nonempty actual hit/copy')
    return records


def helper_records(item,data,expected=True):
    records=[m.parse(line) for line in data.decode('ascii').splitlines(keepends=True)]
    frozen=[m.parse(line) for line in item.expected_helper_output().decode('ascii').splitlines(keepends=True)]
    m.require(len(records)==len(frozen),'helper complete framing')
    for actual,wanted in zip(records,frozen):
        if actual[0]=='GR10' and not expected:
            m.require(actual[1][:3]==wanted[1][:3],'helper response prefix')
            status,accepted,*value=actual[1][3:]
            m.require(status in ((0,3) if item.kind==3 else (0,5)) and accepted==int(status==0),'helper status/accepted')
        else:m.require(actual==wanted,'helper exact echo/framing/result')
    return records


def component_records(data):
    records=[m.parse(line) for line in data.decode('ascii').splitlines(keepends=True)]
    m.require(records and records[0][0]=='COMPONENT10','component header')
    m.require(records[-1]==('END',records[0][1]),'component END/no tail')
                                                                       
                                                                            
    frames=[v for t,v in records if t=='F'];ends=[v for t,v in records if t=='ENDCASE']
    m.require(len(frames)==records[0][1][0] and ends==[(v[0],) for v in frames],'component frame completion')
    for frame in frames:
        ident,fixture,substeps,warm,bodies,contacts,helpers,phases=frame
        m.require(phases==5*substeps+3,'component phase count')
        fp=[v for t,v in records if t=='FP' and v[0]==ident]
        expected=[(ident,0,0,0)];ordinal=1
        for sub in range(1,substeps+1):
            for phase in range(1,6):expected.append((ident,ordinal,sub,phase));ordinal+=1
        expected += [(ident,ordinal,0,6),(ident,ordinal+1,0,7)]
        m.require(fp==expected,'component exact phase cycle')
        m.require(len([1 for t,v in records if t=='CX10' and v[0]==ident])==phases,'component CX completeness')
        fi=[v for t,v in records if t=='FI10' and v[0]==ident]
        m.require(len(fi)==1,'component one FI')
        counts=[sum(t==tag and v[0]==ident for t,v in records) for tag in ('SC10','BV10','SB10','PK10','FH10','FM10')]
        m.require(fi[0]==(ident,phases,*counts),'component exact FI counters')
    return records


def first_difference(before,after,tags):
    left=[(t,v) for t,v in before if t in tags];right=[(t,v) for t,v in after if t in tags]
    for j in range(max(len(left),len(right))):
        a=left[j] if j<len(left) else None;b=right[j] if j<len(right) else None
        if a==b:continue
        if a is None or b is None or a[0]!=b[0]:return {'ordinal':j,'before':a,'after':b}
        field=next((k for k,(x,y) in enumerate(zip(a[1],b[1])) if x!=y),None)
        return {'tag':a[0],'ordinal':j,'word':field,'before':a[1],'after':b[1]}
    return None


def receipt(recipe,baseline,mutant,*,baseline_code,mutant_code,baseline_stderr,mutant_stderr,clean):
    difference=first_difference(baseline,mutant,recipe['expected_tags']) if clean else None
    return {'name':recipe['name'],'class_id':recipe.get('class_id'),'guards':recipe['guards'],
            'baseline_code':baseline_code,'code':mutant_code,'clean':bool(clean),
            'detected':bool(baseline_code==0 and mutant_code==0 and not baseline_stderr and not mutant_stderr and clean and difference),
            'difference':difference,'replayed_before_compaction':False}


def group_for(recipe):
    fixtures=f.definitions();name=recipe.get('guard_group')
    if name:
        candidates=[x for x in fixtures if x.name==name or x.group==name]
    else:
        guard=recipe['guards'][0]
        entry=next(x for x in f.MANIFEST['oslony'] if x['id']==guard)
        name=entry.get('fixture')
        if name and name.startswith('G10-54-'):
            _,_,kind,index=name.split('-');name=f'G54-{index}-'+('7f800000' if kind=='FIN' else 'bf800000')
        candidates=[x for x in fixtures if x.name==name or x.group==name]
    if not candidates:raise ValueError('missing explicit GUARD input for '+recipe['name'])
                                                                          
    selected=next((x for x in candidates if x.name.endswith('7f800000')),
                  next((x for x in candidates if x.status not in (None,0)),candidates[0]))
    if recipe.get('guard_copy_read'):
        m.require(selected.kind==4 and 0<selected.seed<=len(selected.rows),'copy read requires the actual MAX seed')
                                                                            
                                                                           
        selected=replace(selected,rows=(*selected.rows[:selected.seed],f.g.event_copy()))
    return selected


def approved_replacements():
    return [r for filename in ('mutacje-ruch-swiata.json','mutacje-kontakty.json')
            for r in json.loads((HERE/filename).read_bytes())['native_mutations'] if r.get('solver_replacement')]


def replacement_recipe(recipe):
    if recipe.get('solver_replacement') not in ('A8-27','A9-08','A9-09'):
        raise ValueError('replacement outside the W3 recipe set')
    return {**recipe,'probe':'guard-helper','guards':recipe.get('guards',[]),'profile':4}


def run_replacement(context,recipe):
    pass                                                                      

                                                                          
                                                                            
       
    actual=replacement_recipe(recipe)
    runtime=Runtime(context)
    try:
        row=runtime.mutation(actual)
        row.update({'class':recipe.get('class_id'),'class_id':recipe.get('class_id'),'probe':recipe['probe'],
                    'approval':recipe['solver_replacement'],'witness':recipe['guard_group']})
        row['detected']=bool(row['detected'] and row['replayed_before_compaction'])
        return row
    finally:runtime.close()


def boundary_driver(source,legacy_recipe):
    pass                                                                     

                                                                        
                                                                            
                                                              
       
    scanner=load('solver_boundary_sites','receptury-kontakty.py')
    lo,hi=base.function_span(source,'runContactOperation');block=source[lo:hi]
    sites=[statement for condition,statement in scanner.if_sites(block) if condition=='op.opcode == 40i32']
    if len(sites)!=1:raise ValueError('one real opcode40 dispatch required')
    r=legacy_recipe;parent=r.get('parent_expression','reg.bodies[op.c].number')
    call=r.get('entry_call','game.addPreparedShape(reg.worlds[op.b].number, '+parent+', specimen, op.invoke)')
    result_type=r.get('result_type','game.ShapeResult')
    new='''if (op.opcode == 40i32) {
        var specimen: raw.ShapeRecord = op.source;
        if (op.tag == 4i32) specimen.polygon = mass2.b2MakeOffsetRoundedBox(op.halfWidth, op.halfHeight, op.localCenter, op.localRotation, op.radius);
        var boxGeometry: game.BoxGeometry = game.BoxGeometry(op.halfWidth, op.halfHeight, op.localCenter, op.localRotation, op.radius);
        '''+r.get('specimen_seed','')+'''
        let measured: '''+result_type+' = '+call+''';
        execution.status = measured.status; return true;
    }'''
    if r.get('boolean_call'):
        new=new.replace('let measured: '+result_type+' = '+call+';\n        execution.status = measured.status;',
                        'let allowed: bool = '+r['boolean_call']+';\n        execution.status = if allowed then game.PARAM else game.GEOMETRY;')
    return apply(source,{'name':'native-boundary-'+r['name'],'scope':'runContactOperation','expression':sites[0],'replacement':new})


def coverage(results,manifest=None):
    manifest=manifest or recipes();expected={r['name']:r for r in manifest['native_mutations']}
    errors=[];seen={}
    for row in results:
        if row['name'] in seen:errors.append('duplicate native receipt '+row['name'])
        if row['name'] not in expected:errors.append('foreign native receipt '+row['name'])
        seen[row['name']]=row
    for name in expected:
        row=seen.get(name,{})
        if not (row.get('detected') and row.get('clean') and row.get('replayed_before_compaction') and row.get('code')==0):
            errors.append('native recipe not cleanly detected/replayed: '+name)
    killed={name for name,row in seen.items() if row.get('detected') and row.get('clean') and row.get('replayed_before_compaction') and row.get('code')==0}
    classes={expected[name]['class_id'] for name in killed if name in expected and expected[name].get('class_id')}
    guards={guard for name in killed if name in expected for guard in expected[name]['guards']}
    for cls in set(manifest['required_class_ids'])-classes:errors.append('missing class '+cls)
    for guard in set(manifest['required_guard_ids'])-guards:errors.append('missing guard '+guard)
    if manifest['unresolved_recipes']:errors.append('unresolved source recipes')
    return {'code':int(bool(errors)),'recipes':len(expected),'cleanly_detected':len(killed),'classes':len(classes),
            'guards':len(guards),'equivalent_proofs':len(manifest['equivalent_proofs']),'equivalent_counted_as_killed':0,'errors':errors}


def guard_predicates(item, output):
    pass                                                                       
    predicates=[]
    def compare(name,expected,actual):
        predicates.append(dict(name=name,ok=expected==actual,expected=expected,actual=actual))
    records=defaultdict(list)
    for index,line in enumerate(output.decode('ascii',errors='replace').splitlines(keepends=True)):
        try:
            tag,value=m.parse(line);records[tag].append(value)
        except Exception as exc:compare('frame.'+str(index),'canonical record',str(exc))
    compare('GUARD10.header',[(1,)],records['GUARD10'])
    compare('G.echo',[(1,item.kind,item.seed,len(item.rows))],records['G'])
    compare('GA.echo',[(1,*item.words)],records['GA'])
    compare('CASE.frame',[(1,len(item.rows))],records['CASE'])
    compare('ENDCASE.frame',[(1,)],records['ENDCASE'])
    compare('END.frame',[(1,)],records['END'])
    if item.helper is not None:
        expected=(1,len(item.rows),item.helper,item.status,int(item.status==0),item.value&0xffffffff,item.value>>32)
        actual=records['GR10']
        compare('GR10.count',1,len(actual))
        for index,name in enumerate(('case','seq','helper','status','accepted','value.low','value.high')):
            wanted=expected[index];got=actual[0][index] if len(actual)==1 and len(actual[0])>index else None
            if index>=3:
                wanted=f'{wanted:08x}';got=f'{got:08x}' if got is not None else None
            compare('GR10.'+name,wanted,got)
    if item.last_status is not None:
        compare('R.last_status',item.last_status,records['R'][-1][3] if records['R'] else None)
    return predicates


class Runtime:
    pass                                                                    
    def __init__(self,context):
        self.C=context;self.root=Path(context.ROOT);self.out=Path(context.OUT)
        self.source=(HERE/'solver-swiata.dk').read_text(encoding='utf-8')
        self.work=self.root/'.solver-oslony-work'
        if self.work.exists():raise ValueError('owned mutation workspace already exists')
        self.work.mkdir();self.profile_bins={};self.results=[]
        self.protected={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
                        [*(self.root/'silnik/fizyka').glob('*.dk'),HERE/'solver-swiata.dk']}
        self.save('oslony-produkt-przed-sha256.json',self.protected)

    def save(self,name,value):
        (self.out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def compile(self,name,source,physics):
        driver=self.work/(name+'.dk');driver.write_text(source,encoding='utf-8')
        binary=self.C.compile_world_fixture(self.C.world_duckc(),name,driver,physics)
        self.save(name+'-binary.json',{'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'bytes':binary.stat().st_size})
                                                                         
                                                                         
        if name in ('mutation10-g-step-b2World_Step','mutation10-g-step-b2World_Step-negative'):
            shutil.copy2(binary,self.C.base.TEMP/(name+'-odbior-bin'))
        artifacts=self.C.base.TEMP/(name+'-build')
        if artifacts.is_dir() and artifacts.resolve().is_relative_to(self.C.base.TEMP.resolve()):shutil.rmtree(artifacts)
        return binary

    def profile(self,profile):
        if profile not in self.profile_bins:
            if getattr(self.C,'petla_prebuilt',False):
                binary=self.out/('oslony-profile'+str(profile)+'-bin')
                if not binary.is_file():raise ValueError('missing verified profile '+str(profile))
                self.profile_bins[profile]=binary
            else:
                self.profile_bins[profile]=self.compile('oslony-profile'+str(profile),f.native_driver(self.source,profile),self.root/'silnik/fizyka')
        return self.profile_bins[profile]

    def run(self,name,binary,data,c_side=False):
        code,output=self.C.run_world_fixture(name,binary,data,file_argument=c_side)
        stderr=(self.out/(name+'-wykonanie-stderr.csv')).read_bytes()
        return code,output,stderr

    def compact(self,name,validation='failed or incomplete; not counted'):
        path=self.out/(name+'.csv')
        if path.exists():
            digest=hashlib.sha256();size=0;counts=defaultdict(int)
            with path.open('rb') as stream:
                for line in stream:size+=len(line);digest.update(line);counts[line.split(b' ',1)[0].decode('ascii',errors='replace')]+=1
            self.save(name+'-stream.json',{'bytes':size,'sha256':digest.hexdigest(),'records':dict(counts),
                                        'validation_before_compaction':validation})
                                                                         
                                                                 
            retained={'mutation10-'+recipe+suffix for recipe in ('g-step-b2World_Step','g-step-b2World_Step-negative') for suffix in ('-base','')}
            if name not in retained:path.unlink()

    def close(self):
        after={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in self.protected}
        self.save('oslony-produkt-po-sha256.json',after)
        unchanged=after==self.protected
        for binary in self.profile_bins.values():
            if binary.parent.resolve()==self.out.resolve() and binary.exists():binary.unlink()
        if self.work.resolve().is_relative_to(self.root.resolve()):shutil.rmtree(self.work)
        if not unchanged:raise ValueError('native mutation changed protected product')

    def guard(self,item,*,both=True):
        if item.gap:return {'name':item.name,'ok':False,'error':item.gap}
        results={};outputs={};predicates=[]
        for side in (('c','duckling') if both else ('duckling',)):
            name='guard10-'+item.name+'-'+side
            try:
                binary=self.out/'c10-obs1-bin' if side=='c' else self.profile(4)
                name='guard10-'+item.name+'-'+side
                code,output,stderr=self.run(name,binary,item.encode(side=='duckling'),side=='c')
                predicates += [{**pred,'name':side+'-'+pred['name']} for pred in guard_predicates(item,output)]
                error=None
                try:
                    m.require(code==0 and not stderr,'GUARD process code/stderr')
                    if item.helper is not None and not item.rows:m.require(output==item.expected_helper_output(),'exact helper output')
                    else:public_records(output,[(1,item.rows)],guard=item)
                except (ValueError,IndexError,KeyError,UnicodeError) as exc:error=str(exc)
                results[side]={'code':code,'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'error':error}
                outputs[side]=output
            except Exception as exc:
                results[side]={'code':1,'error':type(exc).__name__+': '+str(exc)}
                outputs[side]=b''
        equal=len(outputs)==1 or outputs['c']==outputs['duckling']
        ok=all(r['error'] is None for r in results.values()) and equal
        row={'name':item.name,'group':item.group,'ok':ok,'equal':equal,'processes':results,
             'predicates':predicates,'input_sha256':{side:hashlib.sha256(item.encode(side=='duckling')).hexdigest() for side in outputs}}
        callback=getattr(self.C,'petla_receipt',None)
        if callback:
            callback('fixtury' if both else 'kind4',item.name,row)
            row['diagnosed']=True
        for side in outputs:
            try:self.compact('guard10-'+item.name+'-'+side,'full schema, properties and C/D equality' if ok else 'failed GUARD; not counted')
            except Exception as exc:
                                                                                
                                                                    
                row.setdefault('compaction_errors', {})[side]=type(exc).__name__+': '+str(exc)
                row['error']='; '.join(k+': '+v for k,v in row['compaction_errors'].items())
                row['ok']=False
        return row

    def negatives(self):
        results=[]
        def run(name,binary,data,c_side):
            try:
                code,output,stderr=self.run(name,binary,data,c_side)
                return output,stderr,self.C.process_diagnosis(code,stderr)
            except Exception as exc:
                tag=name+'-wykonanie'
                if not (self.out/(tag+'-polecenie.csv')).exists():
                    self.C.record_process_exception(tag,[binary],exc,stdout=self.out/(name+'.csv'))
                stderr=(self.out/(tag+'-stderr.csv')).read_bytes()
                return b'',stderr,self.C.process_diagnosis(1,stderr,type(exc).__name__+': '+str(exc))
        def failed(exc):
            return self.C.process_diagnosis(1,exception=type(exc).__name__+': '+str(exc))
        def compact(name,row):
            try:self.compact(name,'full validation and C/D equality' if row['ok'] else 'failed probe; not counted')
            except Exception as exc:
                row.setdefault('compaction_errors', {})[name]=type(exc).__name__+': '+str(exc)
                row['ok']=False
        for probe in n.variants():
            side_results={};controls={}
            for index,side in enumerate(('c','duckling')):
                try:
                    profile=5 if probe.error in ('F23','F24','F25','F29') else 3
                    binary=self.out/('c10-component-bin' if profile==5 else 'c10-obs1-bin') if side=='c' else self.profile(profile)
                    name='negative10-'+probe.name+'-'+side
                    control,control_stderr,control_process=run(name+'-control',binary,probe.controls[index],side=='c')
                    output,stderr,process=run(name,binary,probe.c if side=='c' else probe.duckling,side=='c')
                    error=None
                    try:
                        m.require(control_process['code']==0 and not control_process['stderr'] and not control_process['exception'],'negative control failed')
                        if profile==5:component_records(control)
                        else:
                            records=[m.parse(line) for line in control.decode('ascii').splitlines(keepends=True)]
                            rows=tuple(value[2:] for tag,value in records if tag=='E')
                            public_records(control,[(1,rows)])
                    except (ValueError,IndexError,KeyError,UnicodeError) as exc:
                        control_process['validation_error']=str(exc);error=str(exc)
                    try:
                        m.require(process['exception'] is None,'negative process failed')
                        n.check(probe,process['code'],output,stderr,control)
                    except (ValueError,IndexError,KeyError,UnicodeError) as exc:
                        process['validation_error']=str(exc);error=error or str(exc)
                    side_results[side]={**process,'control_code':control_process['code'],'control':control_process,'ok':error is None,'error':error}
                    controls[side]=control
                except Exception as exc:
                    side_results[side]={**failed(exc),'control_code':1,'ok':False,'error':type(exc).__name__+': '+str(exc)}
                    controls[side]=b''
            equal=controls['c']==controls['duckling']
            row={'name':probe.name,'ok':all(r['ok'] for r in side_results.values()) and equal,
                 'controls_equal':equal,'sides':side_results}
            for side in side_results:
                for suffix in ('','-control'):compact('negative10-'+probe.name+'-'+side+suffix,row)
            results.append(row);self.save('ujemne-solver-wynik.json',results)
        for name,c,d in n.positives():
            outputs={};side_results={}
            for side,data in (('c',c),('duckling',d)):
                try:
                    tag='positive10-'+name+'-'+side
                    output,stderr,process=run(tag,self.out/'c10-obs1-bin' if side=='c' else self.profile(3),data,side=='c')
                    error=None
                    try:
                        m.require(process['code']==0 and not process['stderr'] and not process['exception'],'positive process code/stderr')
                        parsed=[m.parse(line) for line in output.decode('ascii').splitlines(keepends=True)]
                        rows=tuple(v[2:] for t,v in parsed if t=='E');public_records(output,[(1,rows)])
                    except (ValueError,IndexError,KeyError,UnicodeError) as exc:error=str(exc)
                    process['validation_error']=error
                    side_results[side]={**process,'ok':error is None,'error':error};outputs[side]=output
                except Exception as exc:
                    side_results[side]={**failed(exc),'ok':False,'error':type(exc).__name__+': '+str(exc)};outputs[side]=b''
            equal=outputs['c']==outputs['duckling']
            row={'name':'positive-'+name,'ok':all(r['ok'] for r in side_results.values()) and equal,
                 'equal':equal,'sides':side_results}
            for side in side_results:compact('positive10-'+name+'-'+side,row)
            results.append(row);self.save('ujemne-solver-wynik.json',results)
        return results

    def mutation(self,recipe):
        name='mutation10-'+recipe['name'];directory=self.work/recipe['name'];directory.mkdir()
        physics=directory/'fizyka';shutil.copytree(self.root/'silnik/fizyka',physics)
        binaries=[];runs=[];row=None
        try:
            profile=recipe.get('profile',3)
            source=f.native_driver(self.source,profile)
            target=physics/Path(recipe['source']).name if recipe['source'].startswith('silnik/fizyka/') else None
            baseline_expected=None;baseline_records=None;boundary=False;guard=None
            legacy_recipe=None
            if recipe['probe']=='reader-boundary':
                original,changed=reader_fixture(source,recipe)
                probe=next(p for p in n.variants() if p.error==recipe['error']);data=probe.duckling
                baseline=self.compile(name+'-base',original,physics);binaries.append(baseline)
                bc,bout,be=self.run(name+'-base',baseline,data);runs.append(name+'-base')
                                                                          
                                                                              
                m.require(bc==2 and be==probe.stderr,'reader baseline did not reject exact catalog error')
                mutant=self.compile(name,changed,physics);binaries.append(mutant)
                code,output,stderr=self.run(name,mutant,data);runs.append(name)
                clean=code==0 and not stderr and output.splitlines()[-1:]==[('GUARD10 PASS '+recipe['error']).encode('ascii')]
                row={'name':recipe['name'],'class_id':None,'guards':[],'baseline_code':bc,'code':code,'clean':bool(clean),
                     'detected':bool(clean),'difference':{'boundary':recipe['scope'],'PASS':recipe['error']} if clean else None,
                     'replayed_before_compaction':bool(clean and (self.out/(name+'.csv')).read_bytes()==output)}
            else:
                if recipe['probe']=='inherited-guard':
                    legacy_recipe=next(r for r in json.loads((HERE/'mutacje-kontakty.json').read_bytes())['native_mutations'] if r['name']==recipe['legacy_recipe'])
                if legacy_recipe and legacy_recipe['probe']=='game-boundary':
                    boundary=True;source=boundary_driver(source,legacy_recipe)
                    geometry=legacy_recipe.get('geometry')
                    geo=f.g.box() if geometry=='polygon' else f.g.capsule() if geometry=='capsule' else f.g.segment() if geometry=='segment' else f.g.circle()
                    rows=(f.world(),f.g.body(),f.g.shape(geometry=geo));ident=1
                    data=f.public_bytes(rows,True)
                    for edit in recipe.get('fixture_edits',[]):target.write_text(apply(target.read_text(encoding='utf-8'),edit),encoding='utf-8')
                    baseline=self.compile(name+'-base',source,physics);binaries.append(baseline)
                    bc,bout,be=self.run(name+'-base',baseline,data);runs.append(name+'-base')
                    baseline_records=public_records(bout,[(1,rows)])
                    m.require(bc==0 and not be,'native guard boundary baseline process failed')
                    status=[v[3] for t,v in baseline_records if t=='R'][-1]
                    m.require(status==legacy_recipe.get('baseline_status',4),'native boundary did not reach the actual guard')
                elif recipe['probe']=='guard-helper' or (legacy_recipe and recipe['guards']):
                    guard=group_for(recipe);m.require(not guard.gap,'unresolved kind0 MAX witness')
                    profile=4;source=f.native_driver(self.source,profile);data=guard.encode(True)
                    bc,bout,be=self.run(name+'-base',self.profile(4),data);runs.append(name+'-base')
                    if guard.helper is not None and not guard.rows:
                        m.require(bout==guard.expected_helper_output(),'exact helper baseline result')
                        baseline_records=helper_records(guard,bout)
                    else:baseline_records=public_records(bout,[(1,guard.rows)],guard=guard)
                elif recipe['probe'] in ('float-helper','component'):
                    profile=5;source=f.native_driver(self.source,profile)
                    data=w.component_helper(True,recipe.get('helper_kind',0)) if recipe['probe']=='float-helper' else w.component_fixture(recipe,True)
                    cdata=w.component_helper(False,recipe.get('helper_kind',0)) if recipe['probe']=='float-helper' else w.component_fixture(recipe,False)
                    bc,bout,be=self.run(name+'-base',self.out/'c10-component-bin',cdata,True);runs.append(name+'-base')
                    baseline_records=component_records(bout)
                else:
                    ident,rows=w.operations_for(recipe);data=w.encode(ident,rows,True)
                    bc,bout,be=self.run(name+'-base',self.out/'c10-obs1-bin',w.encode(ident,rows),True);runs.append(name+'-base')
                    rows_by_case=[(case,rows if case==ident else (f.world(),)) for case in range(1,ident+1)]
                    baseline_records=public_records(bout,rows_by_case)
                m.require(bc==0 and not be,'native mutation baseline process failed')
                if target is None:source=apply(source,recipe)
                else:target.write_text(apply(target.read_text(encoding='utf-8'),recipe),encoding='utf-8')
                mutant=self.compile(name,source,physics);binaries.append(mutant)
                code,output,stderr=self.run(name,mutant,data);runs.append(name)
                clean=code==0 and not stderr;actual=[];error=None
                if clean:
                    try:
                        if guard:
                            if guard.helper is not None and not guard.rows:actual=helper_records(guard,output,expected=False)
                            else:actual=public_records(output,[(1,guard.rows)],guard=guard,properties=False)
                        elif profile==5:actual=component_records(output)
                        else:actual=public_records(output,[(1,rows)] if boundary else rows_by_case,properties=False)
                    except (ValueError,IndexError,KeyError,UnicodeError) as exc:clean=False;error=str(exc)
                row=receipt(recipe,baseline_records,actual,baseline_code=bc,mutant_code=code,baseline_stderr=be,mutant_stderr=stderr,clean=clean)
                if boundary and row['detected']:
                    wanted=legacy_recipe.get('mutant_status',5)
                    row['detected']=[v[3] for t,v in actual if t=='R'][-1]==wanted
                if error:row['error']=error
                                                                            
                if row['detected']:
                    replay=(self.out/(name+'.csv')).read_bytes()
                    row['replayed_before_compaction']=replay==output and first_difference(baseline_records,
                        [m.parse(line) for line in replay.decode('ascii').splitlines(keepends=True)],recipe['expected_tags'])==row['difference']
            row['input_sha256']=hashlib.sha256(data).hexdigest()
            if baseline_records:
                predicates=load('solver_native_predicates','galezie-solver.py')
                row['predicate_receipts']=predicates.trace_predicates(baseline_records)
            return row
        finally:
            for run in runs:self.compact(run,'native clean difference replayed from disk' if row and row.get('detected') and row.get('replayed_before_compaction') else 'failed or incomplete; not counted')
            for binary in binaries:
                if binary.parent.resolve()==self.out.resolve() and binary.exists():binary.unlink()
            if directory.resolve().is_relative_to(self.work.resolve()):shutil.rmtree(directory)
