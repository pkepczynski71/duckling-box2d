pass                                                                      

                                                                           
                                                                            
                                                                              
                                                                        
   
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import traceback
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=spec_from_file_location(name,HERE/file);m=module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
base=load('contact_native_base','mutacje-ruch-swiata.py');apply=base.apply;function_span=base.function_span
g=load('contact_mutation_inputs','przypadki-kontakty.py');fixtures=load('contact_mutation_fixtures','fixtury-kontakty.py')
negative=load('contact_mutation_negative','ujemne-kontakty.py')

def recipes():return json.loads((HERE/'mutacje-kontakty.json').read_bytes())['native_mutations']
def probe_rows(recipe):
    ident=recipe['witness_id'];target=g.cases()[ident-1]
    if recipe.get('witness_variant')=='recreate-A':
        ops=list(target.ops)
        assert ident==61 and ops[12][0]==18 and ops[13][0]==40
        ops[12]=g.op(18,0,0)
        replacement=list(ops[13]);replacement[3]=0;ops[13]=tuple(replacement)
        target=g.Case(ident,target.category+' / recreate A',tuple(ops))
    if recipe.get('prefix_operations'):target=g.Case(ident,target.category,target.ops[:recipe['prefix_operations']])
    return tuple([g.Case(i,'isolated native witness padding',(g.world(gravity=(0,0)),)) for i in range(1,ident)]+[target])

def boundary_fixture(source,recipe):
    pass                                                                       
    lo,hi=function_span(source,recipe['scope']);block=source[lo:hi]
    old=recipe['guard_statement'];assert block.count(old)==1,recipe['name']
    condition=recipe['condition'];return_=recipe['boundary_return']
    observer=f'\n    if (inputOk and ({condition})) {{ io.writeStr("GUARD9 PASS {recipe['guard']}\\n"); failureCode = 0i64; inputOk = false; {return_} }}'
                                                                       
    observed='{ '+old+observer+'\n    }' if recipe['guard']=='F25' else old+observer
    block=block.replace(old,observed,1);baseline=source[:lo]+block+source[hi:]
                                                                           
    a,b=function_span(baseline,'main');main=baseline[a:b].replace('return 2i64;','return failureCode;');baseline=baseline[:a]+main+baseline[b:]
    if recipe['scope']=='main':
        old=old.replace('return 2i64;','return failureCode;')
    guard=old.find(condition);assert guard>=0
    mutated=old[:guard]+'false'+old[guard+len(condition):]
    mutant=apply(baseline,{'name':recipe['name'],'scope':recipe['scope'],'expression':old,'replacement':mutated})
    return baseline,mutant


def island_boundary(source):
    pass                                                                           
    old='if (good) good = world.islands.at(islandId as i64).localIndex == local;'
    new='''if (good) {
                        good = world.islands.at(islandId as i64).localIndex == local;
                        if (not good) {
                            io.writeStr("GUARD9 ISLAND"); outDec(wi); outDec(setIndex); outDec(local); outDec(islandId);
                            outDec(world.islands.at(islandId as i64).localIndex); newline();
                            failureCode = 0i64; inputOk = false; return false;
                        }
                    }'''
    return fixtures.apply_edit(source,'checkIslands',old,new,'island-localIndex-boundary')


def island_receipt(path,reference,p,rows):
    lines=path.read_text(encoding='ascii').splitlines(keepends=True)
    if not lines:return None
    words=lines[-1].rstrip('\n').split(' ')
    if len(words)!=7 or words[:2]!=['GUARD9','ISLAND']:return None
    if not all(g.g8.DEC.fullmatch(w) for w in words[2:]):return None
    wi,set_index,local,island,stored=map(int,words[2:])
    if wi<0 or set_index!=2 or local<0 or island<0 or stored<0 or stored==local:return None
                                                                        
                                                                          
    actual=[];expected=[];ident=rows[-1].id
    for line in lines[:-1]:
        tag,v=p.parse_record(line)
        if tag in ('PORT9B','CASE','E','R','Z9','ENDCASE','END'):actual.append((tag,v))
    with reference.open(encoding='ascii') as stream:
        for line in stream:
            tag,v=p.parse_record(line)
            if tag=='E' and v[:2]==(ident,49):break
            if tag in ('PORT9B','CASE','E','R','Z9','ENDCASE','END'):expected.append((tag,v))
    if actual!=expected:return None
    return {'boundary':'checkIslands.localIndex','case':ident,'seq':49,'world':wi,'set':set_index,
            'local':local,'island':island,'stored_localIndex':stored,'baseline_validated':True}

class OutputError(ValueError):
    def __init__(self,path,side,number,line,error):
        super().__init__(str(error))
        self.context={'path':str(path),'side':side,'line_number':number,'line':line[:8192]}


def output_records(path,p,side,*,boundary=False,skip_guard=False):
    number=0;line=''
    try:
        with path.open(encoding='ascii',newline='') as stream:
            for number,line in enumerate(stream,1):
                if boundary and line=='GUARD9 BATCH\n':yield 'BOUNDARY',(),line;continue
                if skip_guard and line.startswith('GUARD9 '):continue
                tag,v=p.parse_record(line);yield tag,v,line
    except Exception as exc:raise OutputError(path,side,number,line,exc) from exc


def clean_records(path,p,rows,boundary=False,side='Duckling mutant'):
    pass                                                                            
    echoes=[];cases=[];ends=[];last=None;counts={}
    for tag,v,line in output_records(path,p,side,boundary=boundary):
        last=(tag,v)
        if tag=='BOUNDARY':continue
        counts[tag]=counts.get(tag,0)+1
        if tag=='E':echoes.append(v)
        if tag=='CASE':cases.append(v)
        if tag=='ENDCASE':ends.append(v)
    if cases!=[(c.id,len(c.ops)) for c in rows]:return False
    if boundary:
        if ends or last!=('BOUNDARY',()):return False
    elif ends!=[(c.id,) for c in rows] or last!=('END',(len(rows),)):return False
    return echoes==[(c.id,j,*r) for c in rows for j,r in enumerate(c.ops,1)]

def difference(recipe,left,right,p):
    wanted=set(recipe['expected_tags']);ident=recipe['witness_id'];before={};after={}
    for path,dest,side in ((left,before,'C baseline'),(right,after,'Duckling mutant')):
        for tag,v,line in output_records(path,p,side,skip_guard=True):
            if tag not in wanted or v[0]!=ident:continue
            d=p.SCHEMA[tag][0] if tag in p.SCHEMA else p.p8.DECIMALS[tag];key=(tag,v[:d]);dest[key]=(v[d:],line[:8192])
    for key in sorted(before.keys()|after.keys()):
        a=before.get(key);b=after.get(key)
        if a==b:continue
        if a is None or b is None:return {'tag':key[0],'prefix':key[1],'missing':a is None,'excess':b is None,'C':a,'Duckling':b}
        fields=recipe.get('expected_fields',range(max(len(a[0]),len(b[0]))))
        for field in fields:
            if field>=len(a[0]) or field>=len(b[0]) or a[0][field]!=b[0][field]:return {'tag':key[0],'prefix':key[1],'payload_field':field,
                'C':f'{a[0][field]:08x}' if field<len(a[0]) else None,'Duckling':f'{b[0][field]:08x}' if field<len(b[0]) else None,'left':a[1],'right':b[1]}
    return None

def compact_one(ci,path):
    storage=ci.C.world_module('zapis-kontakty.py','contact_mutant_storage');entry=storage.manifest(path);ci.save(path.name+'.manifest.json',entry);path.unlink();return entry


def framing(path,p,rows,boundary=False):
    pass                                                                               
    controls=[];markers=[];last=None
    with path.open(encoding='ascii',newline='') as stream:
        for line in stream:
            if boundary and line=='GUARD9 BATCH\n':last='BOUNDARY';continue
            if not line.endswith('\n') or '\r' in line or not line.isascii() or len(line)>131072:return None
            tag=line.split(' ',1)[0];last=tag
            if tag in ('PORT9B','CASE','E','ENDCASE','END'):
                controls.append(p.parse_record(line))
            if tag in ('R','Z9'):
                words=line.split(' ')
                if len(words)<3 or not all(g.g8.DEC.fullmatch(w) for w in words[1:3]):return None
                markers.append((tag,int(words[1]),int(words[2])))
    expected=[('PORT9B',(len(rows),))]
    for row in rows:
        expected.append(('CASE',(row.id,len(row.ops))))
        expected += [('E',(row.id,j,*op)) for j,op in enumerate(row.ops,1)]
        if not boundary:expected.append(('ENDCASE',(row.id,)))
    if not boundary:expected.append(('END',(len(rows),)))
    if controls!=expected or last!=('BOUNDARY' if boundary else 'END'):return None
    return markers


def structure_proof(exc,ci,path,stderr,actual,rows,reference,baseline_validated,boundary=False):
    if not (isinstance(exc,OutputError) and isinstance(exc.__cause__,ValueError) and
            exc.context['side']=='Duckling mutant' and actual==0 and stderr is not None and
            not stderr.read_bytes() and reference is not None and baseline_validated):return None
    before=fixtures.output_signature(path)
    c=framing(reference,ci.p,rows,boundary);d=framing(path,ci.p,rows,boundary)
    if c is None or d is None or c!=d:return None
    try:clean_records(path,ci.p,rows,boundary=boundary)
    except OutputError as replay:
        if replay.context!=exc.context or str(replay)!=str(exc):return None
    else:return None
    if fixtures.output_signature(path)!=before:return None
    return {'detected_by':'struktura','error':{**exc.context,'type':type(exc.__cause__).__name__,'message':str(exc)},
            'baseline':fixtures.output_signature(reference),'mutant':before,'framing_replayed':True}


def detection_counts(results):
    return {'roznica':sum(r.get('detected') is True and r.get('detected_by','roznica')=='roznica' for r in results),
            'struktura':sum(r.get('detected') is True and r.get('detected_by')=='struktura' for r in results),
            'NIEWYKRYTY':sum(r.get('status')=='NIEWYKRYTY' for r in results),
            'ERROR':sum(r.get('detected') is not True and r.get('status')!='NIEWYKRYTY' for r in results)}

def record_error(ci,results,index,recipe,exc,actual,data,side):
    cause=exc.__cause__ if isinstance(exc,OutputError) else exc
    location=traceback.extract_tb(cause.__traceback__)[-1]
    detail={'type':type(cause).__name__,'message':str(cause)[:8192],
            'file':location.filename,'source_line':location.lineno,'function':location.name,'side':side}
    tb=exc.__traceback__
    while tb is not None:
        frame=tb.tb_frame
        if frame.f_globals.get('__file__')==__file__ and frame.f_code.co_name=='run':
            output=frame.f_locals.get('bp' if side.endswith('baseline') else 'path')
            if isinstance(output,Path):detail['path']=str(output)
        if isinstance(frame.f_locals.get('line'),str):detail['line']=frame.f_locals['line'][:8192]
        if frame.f_globals.get('__file__')!=__file__ and frame.f_code.co_name in ('compile_duck','build_c_adapter','run') and isinstance(frame.f_locals.get('name'),str):
            command=frame.f_locals['name'];detail['command']=command
            detail['side']='C baseline' if command.endswith('-c') or '-c-kompilacja' in command else 'Duckling baseline' if '-baseline' in command else 'Duckling mutant'
        tb=tb.tb_next
    if isinstance(exc,OutputError):detail.update(exc.context)
    elif detail.get('path') and detail.get('line'):
        detail['line_number']=0
        try:
            with Path(detail['path']).open(encoding='ascii',newline='') as stream:
                for number,line in enumerate(stream,1):
                    if line[:8192]==detail['line']:detail['line_number']=number;break
        except (OSError,UnicodeError):pass
    row=results[index] if len(results)>index else {'name':recipe['name'],'class':recipe.get('class_id'),
        'guards':recipe.get('guards',[]),'probe':recipe['probe'],'stream':None}
    row.update(status='ERROR',detected=False,detected_by=None,code=actual,replayed_before_compaction=False,
               input_sha256=hashlib.sha256(data).hexdigest() if data is not None else None,difference=None)
    row.setdefault('errors',[]).append(detail);results[index:index+1]=[row]
    print('BLAD receptury '+recipe['name']+': '+json.dumps(detail,ensure_ascii=True),flush=True)
    for name,value in (('mutacja9-'+recipe['name']+'-blad.json',row),('mutacje-kontakty-wynik.json',results)):
        try:ci.save(name,value)
        except Exception as save_exc:print('BLAD zapisu '+name+': '+str(save_exc),flush=True)



SHARED_MATERIAL_WITNESSES = ('material-route-addPreparedShape','material-route-addShape',
    'material-route-addBox','material-route-createBodyWithBox','material-route-createBodyWithShape',
    'material-route-createBodyWithPreparedShape')


def shared_material_children(recipe):
    if tuple(w['name'] for w in recipe.get('witnesses',[])) != SHARED_MATERIAL_WITNESSES:
        raise ValueError('six exact material witnesses required')
    children=[]
    for witness in recipe['witnesses']:
        child={k:v for k,v in recipe.items() if k!='witnesses'}
        child.update(witness);child['probe']='game-boundary'
                                                                           
                                                                                
        child['fixture_edits']=[dict(name=e['name'],scope=recipe['scope'],
            expression=recipe['expression'],replacement=recipe['expression']+'\n    '+
            recipe['expression'].replace('result.status = PARAM','result.status = GEOMETRY'))
            for e in witness.get('fixture_edits',[])]
        children.append(child)
    return children


def shared_material_complete(recipe,rows):
    try:
        children=shared_material_children(recipe)
        if [r['name'] for r in rows]!=list(SHARED_MATERIAL_WITNESSES):return False
        for witness,row in zip(children,rows):
            detail=row.get('difference') or {}
            if not (row.get('detected') is True and row.get('code')==0 and
                    row.get('replayed_before_compaction') is True and row.get('detected_by')=='roznica' and
                    row.get('input_sha256')==witness['input_sha256'] and
                    detail.get('baseline_ok') is True and detail.get('baseline_code')==0 and
                    detail.get('baseline_status')==witness['baseline_status'] and
                    detail.get('mutant_status')==[witness['mutant_status']]):return False
        return True
    except (KeyError,TypeError,ValueError):return False


def run_shared_material(C,ci,recipe,directory):
    children=shared_material_children(recipe)
    manifest=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
    manifest={**manifest,'recipe_count':6,'native_mutations':children}
    prior_temp=C.base.TEMP;prior_compiler=C.world_duckc;compiler=prior_compiler()
    directory.mkdir();C.base.TEMP=directory;C.world_duckc=lambda:compiler
    try:
        run(C,ci,manifest)
        rows=json.loads((ci.OUT/'mutacje-kontakty-wynik.json').read_bytes())
    finally:C.base.TEMP=prior_temp;C.world_duckc=prior_compiler
    ci.save('material-shared-witnesses.json',rows)
    complete=shared_material_complete(recipe,rows)
    return dict(name=recipe['name'],probe=recipe['probe'],
        **{'class':recipe.get('class_id')},guards=recipe.get('guards',[]),
        detected=complete,status='DETECTED' if complete else 'ERROR',detected_by='roznica' if complete else None,
        code=0 if complete else 1,replayed_before_compaction=complete,
        difference={'six_material_routes':rows} if complete else None,witness_results=rows,stream=None)


def run(C,ci,manifest=None):
    if manifest is None:manifest=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
    items=manifest['native_mutations']
    if len(items)!=manifest['recipe_count']:raise ValueError('native recipe count changed')
    directory=C.base.TEMP/'kontakty-mutacje'
    if directory.exists():raise ValueError('native mutation directory exists')
    directory.mkdir();results=[];baseline_cache={};validated_baselines=set()
    protected={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [*(ci.ROOT/'silnik/fizyka').glob('*.dk'),ci.PORT/'kontakty.dk']}
    ci.save('produkt-kontakty-przed-sha256.json',protected)
    try:
        for recipe in items:
            if recipe.get('solver_replacement') in ('A9-08','A9-09'):
                successor=load('contact_solver_successor','mutacje-solver.py')
                row=successor.run_replacement(C,recipe)
                results.append(row);ci.save('mutacje-kontakty-wynik.json',results)
                continue
            work=directory/recipe['name'];name='mutacja9-'+recipe['name'];index=len(results);actual=None;data=None;path=None;bp=None;stderr=None;rows=None;reference=None;baseline_validated=False;fixture=None;completed=False;side='recipe preparation'
            try:
                work.mkdir();physics=work/'fizyka';shutil.copytree(ci.ROOT/'silnik/fizyka',physics)
                driver=work/'kontakty.dk';source=(ci.PORT/'kontakty.dk').read_text(encoding='utf-8');name='mutacja9-'+recipe['name']
                if recipe['probe']=='material-shared':
                    row=run_shared_material(C,ci,recipe,work/'shared-runtime')
                    results.append(row);ci.save('mutacje-kontakty-wynik.json',results)
                    continue
                if recipe['probe']=='bitset-helper':
                    fixture=next(f for f in fixtures.definitions() if f['name']==recipe['fixture'])
                    driver.write_text(fixtures.duck_driver(source,fixture),encoding='utf-8')
                    target=physics/'bitset.dk';target.write_text(apply(target.read_text(encoding='utf-8'),recipe),encoding='utf-8')
                    side='Duckling mutant'
                    binary=ci.compile_duck(name,driver,physics)
                    data=fixtures.input_data(fixture,True)
                    side='Duckling mutant'
                    actual,path,stderr=ci.run(name,binary,data)
                    lines=path.read_text(encoding='ascii').splitlines()
                    clean=len(lines)==9 and all(line.startswith('BIT9 '+str(j)+' ') and all(g.g8.HEX.fullmatch(x) for x in line.split(' ')[2:]) for j,line in enumerate(lines))
                    detected=actual==0 and not stderr.read_bytes() and clean and path.read_bytes()!=fixtures.bitset_expected()
                    completed=clean
                    detail={'integer_helper_expected_sha256':hashlib.sha256(fixtures.bitset_expected()).hexdigest(),'clean':bool(clean)}
                elif recipe['probe']=='reader-boundary':
                    original,mutant=boundary_fixture(source,recipe)
                    side='Duckling baseline'
                    driver.write_text(original,encoding='utf-8');baseline=ci.compile_duck(name+'-baseline',driver,physics)
                    data=next(d for ident,c,d,diag in negative.variants() if ident==recipe['guard']);diag=negative.ERRORS[recipe['guard']]
                    side='Duckling baseline'
                    bc,bp,be=ci.run(name+'-baseline',baseline,data,expected_code=2,expected_stderr=diag);baseline_ok=bc==2 and be.read_bytes()==diag
                    side='Duckling mutant'
                    driver.write_text(mutant,encoding='utf-8');binary=ci.compile_duck(name,driver,physics)
                    side='Duckling mutant'
                    actual,path,stderr=ci.run(name,binary,data);detected=baseline_ok and actual==0 and not stderr.read_bytes() and path.read_bytes().splitlines()[-1:]==[f'GUARD9 PASS {recipe['guard']}'.encode('ascii')]
                    completed=baseline_ok and bool(detected)
                    detail={'boundary_scope':recipe['scope'],'guard':recipe['guard'],'baseline_code':bc,'baseline_exact_stderr':baseline_ok,'PASS':bool(detected)}
                elif recipe['probe']=='game-boundary':
                                                                                
                                                                                 
                    source=source.replace('const CONTACT_PROFILE: i32 = 1i32;','const CONTACT_PROFILE: i32 = 2i32;',1)
                                                                              
                                                                            
                    lo,hi=function_span(source,'runContactOperation');block=source[lo:hi]
                    generator=load('contact_unit_scanner','receptury-kontakty.py')
                    old=next(s for condition,s in generator.if_sites(block) if condition=='op.opcode == 40i32')
                    parent=recipe.get('parent_expression','reg.bodies[op.c].number')
                    call=recipe.get('entry_call','game.addPreparedShape(reg.worlds[op.b].number, '+parent+', specimen, op.invoke)')
                    result_type=recipe.get('result_type','game.ShapeResult')
                    new='''if (op.opcode == 40i32) {
            var specimen: raw.ShapeRecord = op.source;
            if (op.tag == 4i32) specimen.polygon = mass2.b2MakeOffsetRoundedBox(op.halfWidth, op.halfHeight, op.localCenter, op.localRotation, op.radius);
            var boxGeometry: game.BoxGeometry = game.BoxGeometry(op.halfWidth, op.halfHeight, op.localCenter, op.localRotation, op.radius);
            '''+recipe.get('specimen_seed','')+'''
            let measured: '''+result_type+' = '+call+''';
            execution.status = measured.status; return true;
        }'''
                    if recipe.get('boolean_call'):
                        new=new.replace('let measured: '+result_type+' = '+call+';\n            execution.status = measured.status;',
                            'let allowed: bool = '+recipe['boolean_call']+';\n        execution.status = if allowed then game.PARAM else game.GEOMETRY;')
                    source=fixtures.apply_edit(source,'runContactOperation',old,new,recipe['name'])
                    driver.write_text(source,encoding='utf-8');target=physics/'gra.dk'
                    original=target.read_text(encoding='utf-8')
                    for edit in recipe.get('fixture_edits',[]):original=apply(original,edit)
                    side='Duckling baseline'
                    target.write_text(original,encoding='utf-8');baseline=ci.compile_duck(name+'-baseline',driver,physics)
                    geo=g.box() if recipe.get('geometry')=='polygon' else g.capsule() if recipe.get('geometry')=='capsule' else g.segment() if recipe.get('geometry')=='segment' else g.circle()
                    rows=(g.Case(1,'isolated real game guard',(g.world(),g.body(),g.shape(geometry=geo))),);data=g.encode(rows,True).encode('ascii')
                    side='Duckling baseline'
                    bc,bp,be=ci.run(name+'-baseline',baseline,data)
                    statuses=lambda file:[int(line.split()[4]) for line in file.read_text(encoding='ascii').splitlines() if line.startswith('R ')]
                    wanted=recipe.get('baseline_status',4);baseline_ok=bc==0 and not be.read_bytes() and statuses(bp)[-1:]==[wanted] and clean_records(bp,ci.p,rows,side='Duckling baseline')
                    side='Duckling mutant'
                    target.write_text(apply(original,recipe),encoding='utf-8');binary=ci.compile_duck(name,driver,physics)
                    side='Duckling mutant'
                    actual,path,stderr=ci.run(name,binary,data)
                    detected=baseline_ok and actual==0 and not stderr.read_bytes() and statuses(path)[-1:]==[recipe.get('mutant_status',5)] and clean_records(path,ci.p,rows)
                    completed=baseline_ok and clean_records(path,ci.p,rows)
                    detail={'actual_guard':recipe['scope'],'baseline_status':wanted,'mutant_status':statuses(path)[-1:],'isolated_guard_seed':recipe.get('seed_description'),
                            'baseline_code':bc,'baseline_ok':baseline_ok,'boundary_observer':'PARAM5 before allocation'}
                else:
                    fixture=None
                    if recipe.get('fixture'):
                        fixture=next(f for f in fixtures.definitions() if f['name']==recipe['fixture']);source=fixtures.duck_driver(source,fixture)
                        fixtures.prepare_physics(physics,fixture)
                    if recipe.get('island_boundary'):source=island_boundary(source)
                    driver.write_text(source,encoding='utf-8')
                    baseline_binary=None
                    if recipe.get('island_boundary') or fixture and fixture['kind']=='speculative':
                        side='Duckling baseline'
                        baseline_binary=ci.compile_duck(name+'-baseline',driver,physics)
                    target=driver if recipe['source']=='silnik/port/kontakty.dk' else physics/Path(recipe['source']).name
                    text=target.read_text(encoding='utf-8');target.write_text(apply(text,recipe),encoding='utf-8')
                    side='Duckling mutant'
                    binary=ci.compile_duck(name,driver,physics)
                    rows=fixture['rows'] if fixture else probe_rows(recipe);data=g.encode(rows,True).encode('ascii');key=hashlib.sha256(g.encode(rows).encode('ascii')+str(recipe.get('fixture')).encode('ascii')).hexdigest()
                    if recipe.get('fixture_prefix_operations'):
                        rows=tuple(g.Case(c.id,c.category,c.ops[:recipe['fixture_prefix_operations']]) for c in rows);data=g.encode(rows,True).encode('ascii');key=hashlib.sha256(g.encode(rows).encode('ascii')+str(recipe.get('fixture')).encode('ascii')).hexdigest()
                    if key not in baseline_cache:
                        side='C baseline'
                        cb=ci.build_c_adapter(name+'-c',guard=True,defines=fixtures.c_defines(fixture)) if fixture else ci.OUT/'c9b-obs1-bin'
                        side='C baseline'
                        bc,bp,be=ci.run(name+'-c',cb,g.encode(rows).encode('ascii'),c_side=True)
                        if bc or be.read_bytes():raise ValueError('native mutation C baseline failed')
                        if not fixture:
                            with bp.open(encoding='ascii',newline='') as stream:ci.p.validate_output(stream,rows)
                            validated_baselines.add(bp)
                        elif fixture['kind']!='guard-helper':
                            receipt=fixtures.side_receipt({**fixture,'rows':rows},bp,be,bc,ci.p)
                            if not receipt['conditions'].get('model_valid'):raise ValueError('native mutation C fixture model failed')
                            validated_baselines.add(bp)
                        baseline_cache[key]=bp
                    reference=baseline_cache[key];baseline_validated=reference in validated_baselines
                    if baseline_binary is not None:
                        side='Duckling baseline'
                        bc,bp,be=ci.run(name+'-baseline',baseline_binary,data)
                        if bc or be.read_bytes() or not baseline_validated:raise ValueError('fixture positive control failed')
                        with bp.open(encoding='ascii',newline='') as stream:ci.p.validate_output(stream,rows,guard=bool(fixture))
                        if fixtures.output_signature(bp)!=fixtures.output_signature(reference):raise ValueError('fixture positive control differs from C')
                        compact_one(ci,bp)
                    side='Duckling mutant'
                    actual,path,stderr=ci.run(name,binary,data)
                    if fixture and fixture['kind']=='guard-helper':
                        expected=f'GUARD9 {fixture['expected_guard_status']}'.encode('ascii');tail=path.read_bytes().splitlines()[-1:]
                        detected=actual==0 and not stderr.read_bytes() and tail and tail[0]!=expected and tail[0] in (b'GUARD9 0',b'GUARD9 1',b'GUARD9 2')
                        detail={'expected':expected.decode(),'actual':tail[0].decode('ascii') if tail else None}
                        completed=bool(tail and tail[0] in (b'GUARD9 0',b'GUARD9 1',b'GUARD9 2'))
                    elif recipe.get('island_boundary'):
                        detail=island_receipt(path,reference,ci.p,rows)
                        completed=bool(detail) or clean_records(path,ci.p,rows)
                        detected=actual==0 and not stderr.read_bytes() and bool(detail)
                    else:
                        clean=clean_records(path,ci.p,rows,boundary=bool(fixture and fixture.get('stop_after_seq')))
                        clean=actual==0 and not stderr.read_bytes() and clean
                        detail=difference(recipe,reference,path,ci.p) if clean else None;detected=bool(clean and detail)
                        completed=clean
                entry=ci.C.world_module('zapis-kontakty.py','contact_mutation_digest').manifest(path)
                                                                                
                                                                     
                replayed=False
                if actual==0 and not stderr.read_bytes():
                    if recipe['probe']=='reader-boundary':
                        replayed=baseline_ok and path.read_bytes().splitlines()[-1:]==[f'GUARD9 PASS {recipe['guard']}'.encode('ascii')]
                    elif recipe['probe']=='game-boundary':
                        replayed=baseline_ok and clean_records(path,ci.p,rows) and statuses(path)[-1:]==[recipe.get('mutant_status',5)]
                    elif recipe['probe']=='bitset-helper':
                        replayed=clean and path.read_bytes()!=fixtures.bitset_expected()
                    elif fixture and fixture['kind']=='guard-helper':
                        replayed=path.read_bytes().splitlines()[-1:]==tail and bool(tail and tail[0]!=expected)
                    elif recipe.get('island_boundary'):
                        replayed=island_receipt(path,reference,ci.p,rows)==detail and detail is not None
                    else:
                        replayed=clean_records(path,ci.p,rows,boundary=bool(fixture and fixture.get('stop_after_seq'))) and difference(recipe,reference,path,ci.p)==detail and detail is not None
                detected=bool(detected and replayed)
                row={'name':recipe['name'],'class':recipe.get('class_id'),'guards':recipe.get('guards',[]),'probe':recipe['probe'],'detected':bool(detected),
                     'status':'DETECTED' if detected else 'NIEWYKRYTY' if actual==0 and not stderr.read_bytes() and completed else 'ERROR','detected_by':'roznica' if detected else None,
                     'code':actual,'replayed_before_compaction':bool(replayed),'input_sha256':hashlib.sha256(data).hexdigest(),'difference':detail,'stream':entry}
                results.append(row);ci.save('mutacje-kontakty-wynik.json',results)
                if not detected:ci.save(name+'-blad.json',{'result':row,'reason':'process/stream/baseline invalid or required difference absent'})
                                                                                  
                if path.exists() and row['status']!='ERROR':compact_one(ci,path)
            except Exception as exc:
                try:
                    proof=structure_proof(exc,ci,path,stderr,actual,rows,reference,baseline_validated,bool(fixture and fixture.get('stop_after_seq')))
                    if proof is None:record_error(ci,results,index,recipe,exc,actual,data,side)
                    else:
                        entry=ci.C.world_module('zapis-kontakty.py','contact_structure_digest').manifest(path)
                        row={'name':recipe['name'],'class':recipe.get('class_id'),'guards':recipe.get('guards',[]),'probe':recipe['probe'],
                             'status':'DETECTED','detected':True,'detected_by':'struktura','code':actual,'replayed_before_compaction':True,
                             'input_sha256':hashlib.sha256(data).hexdigest(),'difference':proof,'stream':entry}
                        results[index:index+1]=[row];ci.save(name+'-struktura.json',proof);ci.save('mutacje-kontakty-wynik.json',results)
                        print('WYKRYTY struktura '+recipe['name']+': '+json.dumps(proof['error'],ensure_ascii=True),flush=True)
                        compact_one(ci,path)
                except Exception as classification_error:
                    record_error(ci,results,index,recipe,exc,actual,data,side)
                    record_error(ci,results,index,recipe,classification_error,actual,data,side)
            finally:
                try:
                    if len(results)>index and results[index].get('status')=='ERROR' and path is not None and path.exists():
                        ci.save(path.name+'.manifest.json',{**fixtures.output_signature(path),'validated':False,'records':{},'error':'recipe ERROR; stream not validated'});path.unlink()
                                                                                      
                                                                            
                    for artifact in ci.OUT.glob(name+'*-bin'):
                        ci.save(artifact.name+'-sha256.json',{'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'bytes':artifact.stat().st_size})
                        artifact.unlink()
                    if work.resolve().is_relative_to(directory.resolve()):shutil.rmtree(work)
                except Exception as exc:
                    record_error(ci,results,index,recipe,exc,actual,data,side)
    finally:
        after={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in protected};ci.save('produkt-kontakty-po-sha256.json',after)
        if protected!=after:raise ValueError('native mutation changed protected product')
        if directory.resolve().is_relative_to(C.base.TEMP.resolve()):shutil.rmtree(directory)
    ci.save('mutacje-kontakty-wynik.json',results)
    counts=detection_counts(results);ci.save('mutacje-kontakty-podsumowanie.json',counts)
    print('Mutacje: '+json.dumps(counts,ensure_ascii=True),flush=True)
    branches=C.world_module('galezie-kontakty.py','contact_mutation_coverage')
    coverage=branches.mutation_coverage(results,manifest)
    ci.save('mutacje-kontakty-odroczenia.json',coverage['deferred_classes'])
    ci.save('mutacje-kontakty-pokrycie.json',coverage)
    if coverage['errors']:print('Odmowa pokrycia mutacji: '+str(coverage['errors']),flush=True)
    else:print('39 lokalnych klas wykrytych; odroczenia9b=0; M12 wymaga natywnej bramki kroku11 (D11-3).',flush=True)
    return coverage['code']
