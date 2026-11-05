from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                          

                                                                           
                                                                            
                                                                
   
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=spec_from_file_location(name,HERE/file);m=module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('contact_branch_inputs','przypadki-kontakty.py')
f=g.g8.g7.w6.f32
def add(a,b):return f(f(a)+f(b))
def sub(a,b):return f(f(a)-f(b))
def mul(a,b):return f(f(a)*f(b))
def word(x):return f'{g.bits(x):08x}'

def input_predicates():
    result=[];rows=g.cases()
                                                                             
    spec=f(.02)
    for ident in (9,10,11,12):
        c=rows[ident-1];bs=[r for r in c.ops if r[0]==30];ss=[r for r in c.ops if r[0]==40]
        dx=sub(g.number(bs[1][4]),g.number(bs[0][4]));dy=sub(g.number(bs[1][5]),g.number(bs[0][5]))
        distance2=add(mul(dx,dx),mul(dy,dy));distance=f(math.sqrt(distance2))
        radius=add(g.number(ss[0][7]),g.number(ss[1][7]));maximum=add(radius,spec)
        separation=sub(distance,radius);reject=distance2>mul(maximum,maximum)
        result.append({'branch':'circle speculative squared > / separation','id':ident,'original':'src/manifold.c:43-76',
            'f32':{'dx':word(dx),'dy':word(dy),'distanceSquared':word(distance2),'radiusSum':word(radius),'maxDistance':word(maximum),
                   'maxSquared':word(mul(maximum,maximum)),'separation':word(separation),'speculativeDistance':word(spec)},
            'predicate':reject,'pointCount':0 if reject else 1,'after_removal':'id11: pointCount 0 -> 1; CS/CT/GB/GE differ'})
    assert [r['pointCount'] for r in result[:3]]==[1,1,0]
    assert [r['f32']['separation'] for r in result[:3]]==['3ca3d709','3ca3d70a','3ca3d70b']
    for dy in (.006,.009,.019):
        position=f(1+dy);separation=sub(position,1);threshold=mul(1.5,.005)
        first=separation>threshold
        result.append({'branch':'enableSpeculative=false first / literal repeated else-if','fixture':'speculative-false-'+str(g.bits(dy)),
            'original':'src/contact.c:515-532','f32':{'positionB.y':word(position),'separation':word(separation),'threshold':word(threshold)},
            'first':first,'second_when_reached':False,'pointCount':1 if first else 2,
            'proof':'The else-if repeats the same point0 predicate. On entry first is false, so second is false. Preserved original branch; no input can make it true.',
            'after_removal':'speculative-false native mutation restores pointCount 2 at .009/.019'})
                                                                      
    for ident in range(49,53):
        shapes=[r[1:] for r in rows[ident-1].ops if r[0]==40][:130]
        pairs=[]
        for j,a in enumerate(shapes):
            for b in shapes[j+1:]:
                if a[2]==b[2]:continue
                ac=a[50]|a[51]<<32;am=a[52]|a[53]<<32;bc=b[50]|b[51]<<32;bm=b[52]|b[53]<<32
                if ac&bm and bc&am:pairs.append((a[0],b[0]))
        assert len(pairs)==129,(ident,len(pairs))
        small=add(add(f(.05),f(.01)),spec);large=add(add(f(.05),f(.05)),spec);d2=mul(.09,.09)
        assert d2>mul(small,small) and d2<=mul(large,large)
        result.append({'branch':'129 filtered pairs / small stops / large remains','id':ident,'original':'src/world.c:548-657;src/bitset.h:25-59',
            'pairs':len(pairs),'contactIds':[31,32,63,64,127,128],'bodyIds':[63,64],'transfer_batches':[1,2,3,4,5],
            'f32':{'distanceSquared':word(d2),'smallMaxSquared':word(mul(small,small)),'largeMaxSquared':word(mul(large,large))},
            'predicate':{'smallDisjoint':True,'largeDisjoint':False},'after_removal':'CS/CT localIndex, CB high blocks, GB body64, counters differ'})
                                                                              
    for ident in range(17,21):
        bodies={r[1]:r[1:] for r in rows[ident-1].ops if r[0]==30}
        shapes=[r[1:] for r in rows[ident-1].ops if r[0]==40]
        offsets=[]
        for a in shapes:
            b=bodies[a[2]];cx,cy=(g.number(a[k]) for k in ((6,7) if a[3]==4 else (4,5)));qc,qs=(g.number(b[k]) for k in (5,6))
            rotated=(sub(mul(qc,cx),mul(qs,cy)),add(mul(qs,cx),mul(qc,cy)))
            offsets.append({'shapeRegister':a[0],'localCenter':[word(cx),word(cy)],'rotatedInputCenter':[word(x) for x in rotated]})
        result.append({'branch':'nonzero rotated COM input, both sides','id':ident,'original':'src/world.c:381-415;src/contact.c:549-585',
            'f32':offsets,'after_removal':'M20 six real native substitutions; TASK/CS anchorA/B differ'})
                                                                              
    result.extend([{'branch':'overflow RemoveSwap middle j1/3','id':39,'original':'src/constraint_graph.c:192-233',
                    'expected':{'contactId':11,'localIndex':1,'count':3},'after_removal':'M28 CT moved localIndex differs'},
                   {'branch':'overflow RemoveSwap first j0/2','id':42,'original':'src/constraint_graph.c:192-233',
                    'expected':{'contactId':11,'localIndex':0,'count':2},'after_removal':'M28 CT moved localIndex differs'}])
    hit_samples=[]
    for distance in (.9,1.04):
        separation=sub(distance,1);maximum=add(1,spec)
        hit_samples.append({'distance':word(distance),'separation':word(separation),
                            'distanceSquared':word(mul(distance,distance)),'maxSquared':word(mul(maximum,maximum)),
                            'pointCount':int(mul(distance,distance)<=mul(maximum,maximum))})
    result.append({'branch':'raw UpdateContact hit set then clear','fixture':'raw-hit-cycle','original':'src/contact.c:535-542',
                   'f32':hit_samples,'expected_task_sequences':[8,14],'expected_hit_bit':[True,False],
                   'expected_hit_buffer_count':0,'after_removal':'CS.simFlags bit 0x100000 differs; TASK and retained CS checked independently'})
    return result


def unresolved_classes():
    pass                                                                   
    return []


def step11_classes():
                                                                          
                                                                         
    return [{'class_id':'M12','status':'ZAMKNIETE_W_KROKU_11','decision':'D11-3',
             'native_recipe':'M12-LINK-REF','native_receipt_required':True}]


def m12_coverage(receipt):
    pass                                                                     
    errors=[];r=receipt or {};baseline=r.get('baseline',{});actual=r.get('mutant',{})
    if r.get('name')!='M12-LINK-REF' or r.get('class_id')!='M12':errors.append('wrong M12 recipe/class')
    if not all(r.get(k) is True for k in ('detected','native_compiled','recipe_single_hit')):errors.append('M12 requires real clean native mutation')
    source=(HERE.parent/'fizyka/swiat.dk').read_text(encoding='utf-8')
    native=load('contact_M12_current_product','mutacje-sen.py');recipe=native.m12_recipe(HERE.parents[1])
    expected=hashlib.sha256(native.base.apply(source,recipe).encode('utf-8')).hexdigest()
    if r.get('source_sha256')!=expected:errors.append('M12 changed source does not match current product')
    if not baseline.get('clean') or not baseline.get('models_ok') or baseline.get('difference') is not None:errors.append('M12 C/D/model baseline failed')
    for label in ('c','duckling'):
        side=baseline.get('sides',{}).get(label,{})
        if side.get('code')!=0 or side.get('stderr')!='' or not side.get('model_ok') or not side.get('replayed_before_compaction'):errors.append('M12 baseline process/replay missing: '+label)
    trigger=baseline.get('M12_trigger',{})
    required={'observed_pre_step_awake':1,'observed_pre_link_sleeping_body_count':1,
              'awake_bodies_before':1,'awake_bodies_after':2,'transferred_non_touching':2}
    if any(trigger.get(k)!=v for k,v in required.items()):errors.append('M12 actual singleton Link/wake/growth witness missing')
    changed=actual.get('sides',{}).get('duckling',{})
    if not actual.get('clean') or not actual.get('difference') or changed.get('code')!=0 or changed.get('stderr')!='' or not changed.get('replayed_before_compaction'):errors.append('M12 mutant must execute and differ without crash/timeout')
    if not changed.get('binary_sha256') or changed.get('binary_sha256')==baseline.get('sides',{}).get('duckling',{}).get('binary_sha256'):errors.append('M12 changed executable missing')
    return {'code':int(bool(errors)),'errors':errors,'detected':not errors,'class_id':'M12','status':'WYKRYTE_NATYWNIE' if not errors else 'MISSING_NATYWNEGO_DOWODU'}

                                                                         
HISTORICAL_STEP9B_PROOFS = [{'class_id': 'M12',
  'status': 'ODROCZONE_DO_KROKU_11',
  'detected': False,
  'decision': 'fixtures/norms/DECYZJA-M12.json',
  'original': 'src/world.c:649-658; wake/awake-set growth in b2LinkContact',
  'proof': [{'port': 'silnik/fizyka/swiat.dk:2231',
             'scope': 'b2LinkContact',
             'expression': 'b2AddContactToIsland(world, target, id);',
             'reason': 'Link only links islands/records; no awake sim push or wake path.'},
            {'port': 'silnik/fizyka/swiat.dk:2202',
             'scope': 'b2AddContactToIsland',
             'expression': 'world.contacts.at(id as i64).islandId = islandId;',
             'reason': 'Island membership only; no sim storage changes.'},
            {'port': 'silnik/fizyka/swiat.dk:2451',
             'scope': 'b2CollideChanges',
             'expression': 'let transfer: ContactSim = fresh;',
             'reason': 'Value snapshot from non-touching owner before the graph destination grows.'},
            {'port': 'silnik/fizyka/swiat.dk:2142',
             'scope': 'b2AddContactToGraph',
             'expression': 'source: ContactSim',
             'reason': 'Value parameter; graph storage is distinct from the awake non-touching array.'},
            {'port': 'silnik/fizyka/swiat.dk:2176',
             'scope': 'b2AddContactToGraph',
             'expression': 'world.constraintGraph.colors[selected].contactSims.push(sim);',
             'reason': 'Only destination grows; no retained reference into this destination is read '
                       'afterwards.'},
            {'port': 'silnik/fizyka/swiat.dk:2460',
             'scope': 'b2CollideChanges',
             'expression': 'let stoppedCopy: ContactSim = stopped;',
             'reason': 'Reverse transfer snapshots graph sim before the distinct non-touching destination '
                       'grows.'},
            {'port': 'silnik/fizyka/swiat.dk:2010',
             'scope': 'b2AddNonTouchingContact',
             'expression': 'b2GetSolverSet(world, setIndex).contactSims.push(sim);',
             'reason': 'Reverse transfer grows only its destination; source was copied by value.'}]}]


def frozen_table():
    recipes=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
    rows=[]
    for r in recipes['native_mutations']:
        witness=('F input '+r['guard'] if r['probe']=='reader-boundary' else
                 'native helper '+r['name'] if r['probe']=='game-boundary' else
                 'fixture '+r['fixture'] if r.get('fixture') else 'N64 id '+str(r['witness_id']))
        if r.get('solver_replacement'):
            witness='GUARD10 '+r['guard_group']+'; retained legacy witness id '+str(r['witness_id'])
        rows.append({'recipe':r['name'],'port':r['source']+':'+str(r['port_line']),'original':r['original_anchor'],
            'scope':r['scope'],'branch_or_assignment':r.get('expression',r.get('condition')),
            'witness':witness,'id':r['witness_id'],'classes':[r['class_id']] if r.get('class_id') else [],'guards':r['guards'],
            'difference_after_removal':r.get('replacement','guard -> false')+'; observe '+','.join(r['expected_tags']),
            'native_status':'REQUIRES_NATIVE_RUN'})
        if r['name']=='material-route-createBodyWithBox':
            rows[-1]['difference_after_removal']='R.status PARAM(5) -> GEOMETRY(4), invalid material and box; actual validBox is reached, no observer and no allocation.'
        elif r['name']=='hit-b2UpdateContact-set':
            rows[-1]['difference_after_removal']='seq8 TASK and CS: hit bit 0x100000 missing; retained CS.simFlags 0x110000 -> 0x10000; hit buffer remains empty.'
        elif r['name']=='hit-b2UpdateContact-clear':
            rows[-1]['difference_after_removal']='seq14 TASK and CS: hit bit 0x100000 retained after pointCount becomes 0; retained CS.simFlags 0 -> 0x100000; hit buffer remains empty.'
        elif r['name'].endswith('-prev-next'):
            rows[-1]['difference_after_removal']='CT of previous edge: nextKey remains deleted 2*contactId+side instead of edge.nextKey; edge list/count reciprocity fails.'
        if r.get('witness_variant'):
            rows[-1]['witness']+=' / '+r['witness_variant']+' (seq13 destroy shape0; seq14 create shape2 on body0)'
        if r.get('island_boundary'):
            rows[-1]['witness']+=' / checkIslands.localIndex boundary before fatal exit, healthy control equals validated C'
            rows[-1]['difference_after_removal']='MERGE seq49: actual localIndex comparison fails; GUARD9 ISLAND names world/set/local/island/stored localIndex; code0, empty stderr, exact C prefix through seq48.'
    fixture_module=load('contact_branch_fixture_definitions','fixtury-kontakty.py')
    source=(HERE/'kontakty.dk').read_text(encoding='utf-8')
    lo,hi=fixture_module.mutator.function_span(source,'readOperation')
    anchor=fixture_module.MATERIAL_ROUTE_ANCHOR
    if source[lo:hi].count(anchor)!=1:raise ValueError('material fixture successful decoder exit is not single-hit')
    site={'port':'silnik/port/kontakty.dk:'+str(source[:source.index(anchor,lo,hi)].count('\n')+1),
          'scope':'readOperation','anchor':anchor,'guards':['G-MAT-ROUTES'],
          'fixtures':[f['name'] for f in fixture_module.definitions() if f['kind']=='material-route'],
          'purpose':'Seed the same material field after successful decoding; preserve all early input refusals and the actual material guard.'}
    return {'profile':'COMPONENT_A9','recipe_count':recipes['recipe_count'],'replaced_native_mutations':recipes.get('replaced_native_mutations',[]),'input_predicates':input_predicates(),'branches':rows,
            'unresolved_classes':unresolved_classes(),'step11_classes':step11_classes(),'fixture_injections':[site],
            'historical_step9b_proofs':HISTORICAL_STEP9B_PROOFS}

def freeze():
    table=frozen_table();(HERE/'kontakty-galezie.json').write_text(json.dumps(table,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 9b: E947578d56c3f → case → Ed0214da571af E6199aecf23ab E832171ed9e98','',
        'E58519cd1daa6 f32 Ede7d1b721a1e Ebdf72e0df12f Eac8859ccf949 E31ec1412a751 Ed573b0f927e4. Efda0af643d1f Ed13d233ad06c C/Ee6b67ce8a51d Ede7d1b721a1e E9ef9a822cf9e E0840f545c010 E003a8cb6dbd7 Ed763a792f268 E5a55cf01f822; missing Ed54dc313906d E8418de96e63e Ecd5b158f21b7 E35e99f929e01 E9a8b4158edde E01cf82a666a8.','',
        '| E72e9a59f5a1d ↔ Ebc34da44d8b8 | E14c3f1e2bd43/E70e3810812fe | Ea5738fa01df3 | E461218622f66 E6199aecf23ab E832171ed9e98 |','|---|---|---|---|']
    esc=lambda x:str(x).replace('|','&#124;').replace('\n','<br>')
    for r in table['branches']:lines.append('| '+' | '.join(esc(x) for x in (r['port']+' ↔ '+r['original'],r['scope']+': '+r['branch_or_assignment'],r['witness'],r['difference_after_removal']))+' |')
    lines+=['','## M12 — zamkniecie natywne w kroku11 (D11-3)','',
            'E5e77e1785d57 odroczen9b E35e99f929e01 E04e1f855f747.39 E6169bb6a6469 Ee726e9a8ef66 wymaga203 E0840f545c010 (202 Ea300cda82300 +1 Ee992589a7014 z6 Ea41c8ab22485). M12-LINK-REF E003a8cb6dbd7 E94ab2897b4fc, Edd76283a7989 E420e98542dbd ELF, E8ba8496a2525 C/D Ede7d1b721a1e E736fb3c13477, E01667a4d81ad E9968d6517a62 Eec63bddd7c50/E89ad823ffb3e Ef245940166d1 Ecf37c87714d0 Ed36f65fba4fd E39319e9dea17 E283ada7088c2 Ecdb2e0d0f873/Ef77d1bb58da8. m12_coverage Ecd5b158f21b7 Eb7c274ed084f E8297024f513a E672a88ae5d89 E85a5525683c9 E33dcc1a09b95 Ee04b973f7576 Efea72193e109 E507a9a8be3d1.',
            '', '| Port ↔ oryginał | Dowód |','|---|---|']
    lines += ['', 'M12: source bindings and native checks.', '']
    for item in table['unresolved_classes'] + table['historical_step9b_proofs']:
        for site in item['proof']:lines.append('| '+esc(site['port']+' ↔ '+item['original'])+' | '+esc(site['reason']+' '+site['expression'])+' |')
    lines+=['','## E7c20a491c437 E40e0b797efb6 E4195d5cf3bdd E99498ce6617a','',
            'Ef4b06ef6d3c8 E2bf037652e16 Eb07b138c5f71 E8c43111c3ad0 Eac0b52a2ae6e E1ea199638e25 Ef4465733b96b G-MAT-ROUTES, E283ada7088c2 E3268fef5c876 E372262c3dc76 E537728d2b5af. E11366eeda268 E7e059e4c7eb8 E7a323a683c72 Efbebfb383bb5 E52b3d71a10fe Efa13149d723c.',
            '', '| Port source location | Exact anchor | Fixtures |','|---|---|---|']
    for site in table['fixture_injections']:
        lines.append('| '+' | '.join(esc(x) for x in (site['port']+' / '+site['scope'],site['anchor'],', '.join(site['fixtures'])))+' |')
    lines+=['','E2f93ec95c9e5 f32, E1364b62d3782 E92dae624f48b, 129 Ec9d9d2c4be97 Ede7d1b721a1e Ec3fff4181c95 E94fa3e5538d5: `kontakty-galezie.json.input_predicates`.','']
    (HERE/'KONTAKTY-GALEZIE.md').write_text('\n'.join(lines),encoding='utf-8')
    return table

def observed(path):
    p=load('contact_branch_compare','porownaj-kontakty.py');hits={};previous={};rows=defaultdict(list);case=seq=0
    def hit(name,proof):hits.setdefault(name,{'id':case,'seq':seq,'proof':proof})
    with Path(path).open(encoding='ascii',newline='') as source:
        for line in source:
            tag,v=p.parse_record(line)
            if tag=='CASE':previous={};rows=defaultdict(list);case=v[0];continue
            if tag not in p.RANK and tag!='TASK':continue
            rows[tag].append(v)
            if tag!='Z9':continue
            seq=v[1];op=rows['E'][0][2:];code=op[0]
            for t in rows['TASK']:
                if t[3]!=1:continue
                s=t[8:];cid=s[0]
                for mask,name in ((0x20000,'disjoint'),(0x40000,'started'),(0x80000,'stopped'),(0x10000,'touching')):
                    if s[13]&mask:hit('task-'+name,{'contactId':cid,'flags':s[13]})
                hit('pointCount-'+str(s[24]),{'contactId':cid,'count':s[24]})
            if case in (39,42) and code==3 and op[2]==12:
                cs=[v for v in previous['CT'] if v[4] and v[7]==11]
                count=3 if case==39 else 2;local=1 if case==39 else 0
                target=[v for v in cs if v[11]==12 or v[14]==12]
                if len(cs)!=count or len(target)!=1 or target[0][3]!=11 or target[0][8]!=local:raise ValueError(f'B{case} literal overflow witness missing: {cs}')
                hit('overflow-'+str(case),{'id':11,'localIndex':local,'count':count})
            if case in (25,26) and code==53:
                                                                             
                side=case-25;numbers={v[2]:v[3] for v in rows['NC9']}
                target=numbers[op[2]];owner=op[1]
                before=next(v for v in previous['CT'] if v[2:4]==(owner,target))
                prevkey,nextkey=before[12+3*side:14+3*side]
                if prevkey!=p.NULL:
                    preceding=next(v for v in rows['CT'] if v[2:4]==(owner,prevkey>>1))
                    if preceding[13+3*(prevkey&1)]!=nextkey:raise ValueError('DestroyContact prev.next not repaired')
                    hit('prev-next-'+('A' if side==0 else 'B'),{'contactId':target,'prevKey':prevkey,'nextKey':nextkey,
                        'middle':nextkey!=p.NULL,'expected_previous_nextKey':nextkey,'without_repair':2*target+side})
            if case in (49,50,51,52):
                for cb in rows['CB']:
                    for index in (31,32,63,64,127,128):
                        block=index//64;shift=index%64
                        if cb[4]>block and p.wide(cb[6+2*block:8+2*block])>>shift&1:hit('contact-bit-'+str(index),{'block':block,'shift':shift})
                for gb in rows['GB']:
                    for index in (63,64):
                        block=index//64;shift=index%64
                        if gb[4] and gb[5]>block and p.wide(gb[7+2*block:9+2*block])>>shift&1:hit('body-bit-'+str(index),{'color':gb[3],'block':block,'shift':shift})
            previous=rows;rows=defaultdict(list)
    required={'task-'+x for x in ('disjoint','started','stopped','touching')}|{'pointCount-'+str(i) for i in range(3)}|{'overflow-39','overflow-42','prev-next-A','prev-next-B'}|{'contact-bit-'+str(i) for i in (31,32,63,64,127,128)}|{'body-bit-63','body-bit-64'}
    missing=sorted(required-set(hits))
    return {'hits':hits,'required':sorted(required),'missing':missing}

def mutation_coverage(results,manifest=None,deferrals=None,*,m12_receipt=None,require_step11=False):
    pass                                                                        
    if manifest is None:manifest=json.loads((HERE/'mutacje-kontakty.json').read_bytes())
    canonical=unresolved_classes()
    if deferrals is None:deferrals=canonical
    errors=[];recipes=manifest['native_mutations'];expected={f'M{i:02}' for i in range(1,41)}-{'M12'}
    metadata=step11_classes()
    if manifest.get('unresolved_classes')!=metadata:errors.append('unauthorized or unproved manifest deferral')
    if deferrals!=canonical:errors.append('D11-3: no 9b class may remain deferred')
    if json.loads((HERE/'kontakty-galezie.json').read_bytes()).get('unresolved_classes')!=canonical:errors.append('frozen M12 proof missing or changed')
    try:
        digest=hashlib.sha256(norm_bytes(HERE/'fixtures/norms/DECYZJA-M12.json').replace(b'\r\n',b'\n')).hexdigest()
        if digest!='2d2416a7575327ab686252bed0cdc79d97ef0035e844ad97ecaf572530b0ecb5':errors.append('M12 specification data changed')
    except OSError:errors.append('M12 specification data missing')
    if manifest.get('class_count')!=40 or len(manifest['required_class_ids'])!=40 or set(manifest['required_class_ids'])!=expected|{'M12'}:errors.append('required classes changed')
    if manifest.get('recipe_count')!=203 or len(recipes)!=203 or len({r['name'] for r in recipes})!=203:errors.append('expected exactly 203 unique executable recipes')
    if {r['class_id'] for r in recipes if r.get('class_id')}!=expected:errors.append('expected exactly 39 executable classes, excluding M12')
    if [r['name'] for r in results]!=[r['name'] for r in recipes]:errors.append('native recipe results missing, reordered or excessive')
    detected=set()
    for row,recipe in zip(results,recipes):
        valid=row.get('class')==recipe.get('class_id') and row.get('detected') is True and row.get('code')==0 and bool(row.get('difference')) and row.get('replayed_before_compaction') is True
        if recipe.get('probe')=='material-shared':
            shared=load('contact_shared_gate','mutacje-kontakty.py')
            valid=valid and shared.shared_material_complete(recipe,row.get('witness_results',[]))
        if not valid:errors.append('native recipe not detected cleanly: '+recipe['name'])
        elif row.get('class'):detected.add(row['class'])
    if detected!=expected:errors.append('not all 39 executable classes detected')
    external=m12_coverage(m12_receipt) if require_step11 or m12_receipt is not None else None
    if external is not None:
        errors.extend(external['errors'])
        if external['detected']:detected.add('M12')
    return {'code':int(bool(errors)),'errors':errors,'detected_classes':sorted(detected),'executable_class_count':39,
            'deferred_classes':deferrals,'deferred_class_count':len(deferrals),'required_class_count':40,
            'step11_classes':metadata,'M12':external,'scope':'full11' if require_step11 else 'local9b; M12 requires separate native step11 gate'}

def native_receipts(results,observations,m12_receipt=None,require_step11=False):
    table=frozen_table();byname={r['name']:r for r in results}
    receipts=[]
    for r in table['branches']:
        actual=byname.get(r['recipe']);ok=bool(actual and actual['detected'] and actual['code']==0 and actual['difference'])
        receipts.append({**r,'native_status':'DETECTED' if ok else 'GAP','actual_difference':actual['difference'] if actual else None})
    coverage=mutation_coverage(results,deferrals=table['unresolved_classes'],m12_receipt=m12_receipt,require_step11=require_step11)
    closure=m12_coverage(m12_receipt)
                                                                          
                                                                              
                                                                
    external_gaps=[] if closure['detected'] else ['M12']
    return {'branches':receipts,'input_predicates':table['input_predicates'],'observed':observations,'coverage':coverage,
            'unresolved_classes':table['unresolved_classes'],
            'step11_closure':closure,'scope':'203 local9b recipes; full40 requires current step11 M12 receipt',
            'blocking_gaps':[r['recipe'] for r in receipts if r['native_status']=='GAP']+observations['missing']+coverage['errors'],
            'gaps':[r['recipe'] for r in receipts if r['native_status']=='GAP']+observations['missing']+external_gaps}

if __name__=='__main__':
    print('branches',len(freeze()['branches']))
