from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                         

                                                                            
                                                                             
   
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module); return module


native = load('sen_branch_native', 'mutacje-sen.py')
m = load('sen_branch_model', 'model-sen.py')


def cells(section):
    return [[part.strip() for part in line.strip().strip('|').split('|')]
            for line in section.splitlines() if line.startswith('|') and not line.startswith('|---')]


def obligations():
    text = norm_text(HERE / 'fixtures/norms/KONTRAKT-11.json')
    manifest = json.loads((HERE / 'sen-przypadki.json').read_bytes())
    guard = text.split('## Dodatek D.', 1)[1].split('E60d24b83ba49 E403eb30cae85', 1)[0]
    result = []
    for fields in cells(guard)[1:]:
        if len(fields) != 5: raise ValueError('appendix D table shape')
        ident, predicate, witness, difference, mutation = fields
        result.append({'id': ident, 'kind': 'guard', 'predicate': predicate, 'planned_witness': witness,
                       'required_difference': difference, 'required_mutation': mutation})
    if len(result) != manifest['guard']['rozwinieteWierszeOslon']:
        raise ValueError('appendix D guard obligations changed: ' + str(len(result)))
    core = text.split('## Dodatek E.', 1)[1]
    for fields in cells(core)[1:]:
        if len(fields) != 4: raise ValueError('appendix E table shape')
        ident, branch, families, mutations = fields
        result.append({'id': ident, 'kind': 'core', 'predicate': branch, 'planned_witness': families,
                       'required_difference': mutations, 'required_mutation': mutations})
    if sum(x['kind'] == 'core' for x in result) != 24: raise ValueError('24 sleep core classes required')
    result.append({'id': 'M12', 'kind': 'debt9b', 'predicate': 'reacquire current started sim after Link/wake grows awake',
                   'planned_witness': 'A4 / C09: actual started contact, sleeping body, awake growth',
                   'required_mutation': 'Use actual ContactSim value copied before Link instead of reacquiring it afterwards',
                   'required_difference': 'first actual CS/CT/graph difference after Link; baseline must pass; no crash/timeout'})
    for row in result:
        families = set(re.findall(r'\b[AB]\d+\b', row['planned_witness']))
        row['proposed_case_ids'] = [c['id'] for c in manifest['przypadki'] if c['rodzina'] in families]
        row.update(port=None, actual_case=None, actual_seq=None, predicate_receipts=[], first_difference=None,
                   status='GAP — UNVERIFIED', counted_as_killed=False)
    return result


def proofs(root):
    text = norm_text(HERE / 'fixtures/norms/KONTRAKT-11.json')
    eq = text.split('### 9.2.', 1)[1].split('E10cae49c850f E054a5c91e77c NOT', 1)[0]
    memory = text.split('### 9.3.', 1)[1].split('## 10.', 1)[0]
    result = []
    for category, section in (('EQUIVALENT — dowód', eq), ('MEMORY_GUARD MEMORY — E886ebea7a420 Ec94d7a942184', memory)):
        for fields in cells(section)[1:]:
            literal, origin, explanation = fields[:3]
            result.append({'classification': category, 'literal': literal, 'original': origin,
                           'proof': explanation, 'witness': None, 'counted_as_killed': False,
                           'current_source_review': 'UNVERIFIED — recenzja wymagana'})
    if sum(x['classification'].startswith('EQUIVALENT') for x in result) != 9 or len(result) != 11:
        raise ValueError('nine equivalent proofs and TWO separate memory guards required')
    source = (Path(root) / 'silnik/fizyka/gra.dk').read_text(encoding='utf-8')
    raw = (Path(root) / 'silnik/fizyka/swiat.dk').read_text(encoding='utf-8')
    reviewed = {}
    for function, text, filename in (('validStepParameters',source,'gra.dk'),('validBodyDef',source,'gra.dk'),
                                     ('bodyStatus',source,'gra.dk'),('b2Body_IsValid',raw,'swiat.dk'),('b2MakeBodyId',raw,'swiat.dk')):
        lo,hi=native.base.function_span(text,function)
        reviewed[function]={'port':'silnik/fizyka/'+filename+':'+str(text[:lo].count('\n')+1),
                            'sha256':hashlib.sha256(text[lo:hi].encode()).hexdigest()}
    for i,row in enumerate(result[:9]):
        functions=('validStepParameters',) if i<5 else ('bodyStatus','b2Body_IsValid','b2MakeBodyId') if i<7 else ('validBodyDef',)
        row['reviewed_functions']={name:reviewed[name] for name in functions}
        row['current_source_review']='Eb69646cf6184 E6b6b65ad9b4e Ed0dea1df95b8: Eb71df6c3c957 E574440889a40 E631f494748f8; binary32 E283ada7088c2 FTZ, E947f187506f7 E87eba76e7f31 Ede7d1b721a1e E956cb3b1ab25 Eeeba72c45a26 z Ed64c7c1f7f02. E30094e0bec00 Eec1a1c40a1a2 E0c162970a870 R-11 (D11-3).'
    lo, hi = native.base.function_span(source, 'bodyStatus'); body = source[lo:hi]
    lower, upper, access = ('number.slot < 0i32', 'number.slot as i64 >= world.bodies.length()',
                            'world.bodies.at(number.slot as i64)')
    if all(body.count(x) == 1 for x in (lower, upper, access)) and body.index(lower) < body.index(upper) < body.index(access):
        for row, expression in zip(result[-2:], (lower, upper)):
            row['current_anchor'] = 'silnik/fizyka/gra.dk:' + str(source[:lo+body.index(expression)].count('\n')+1)
            row['access_anchor'] = 'silnik/fizyka/gra.dk:' + str(source[:lo+body.index(access)].count('\n')+1)
            row['current_source_review'] = 'E956cb3b1ab25 Ee015828237b8 Ed8c67c16da3b E966e4215dee1; E886ebea7a420 Ec94d7a942184 E003a8cb6dbd7 E0c162970a870'
            row['reviewed_functions']={'bodyStatus':reviewed['bodyStatus']}
    return result


                                                                           
                                                                              
                                                                            
CORE_VARIANTS = {
 'M11-01': ('M11-01-ANGULAR','W2-M01-ABS-W','M11-01-DELTAS','W2-M01-FACTOR','W2-M01-INVH','W2-M01-SUM','W2-M01-PARENS','W2-M01-ANGLE'),
 'M11-02': ('M11-02-GE','M11-02-HALF','M11-02-SUBSTEP','W2-M02-RESET'),
 'M11-03': ('M11-03-WORLD','M11-03-BODY','M11-03-WAKE-SETS','W2-M03-REPEAT'),
 'M11-04': ('M11-04-LOCAL','W2-M04-ID'),
 'M11-05': ('M11-05-FORWARD','W2-M05-ORDER'),
 'M11-06': ('M11-06-A','M11-06-B','W2-M06-GRAPH-FIRST'),
 'M11-07': ('M11-07-DISABLED','W2-M07-SLEEPING','M12-LINK-REF'),
 'M11-08': ('M11-08-TIMER','M11-08-IDENTITY','W2-M08-REUSE'),
 'M11-09': ('M11-09-TRANSFER','M11-09-MOVED','W2-M09-DUPLICATE'),
 'M11-10': ('M11-10-STATE','M11-10-LOCAL','M11-10-FORCE'),
 'M11-11': ('M11-11-OTHER','W2-M11-SET','W2-M11-MOVED'),
 'M11-12': ('M11-12-MASK','M11-12-BITSET','M11-12-LOCAL','W2-M12-OVERFLOW','W2-M12-CACHE','W2-M12-IMPULSE'),
 'M11-13': ('M11-13-MASK','W2-M13-INDEX','W2-M13-MASS','W2-M13-IMPULSE','W3-M13-OLD-COLOR'),
 'M11-14': ('M11-14-POOL','M11-14-LOCAL','W2-M14-RECYCLE'),
 'M11-15': ('M11-15-FELL','M11-15-INDEX','M11-15-OLD-MOVE','W2-M15-SPURIOUS'),
 'M11-16': ('M11-16-NOWAKE','M11-16-TOUCH','M11-16-NONTOUCH','W2-M16-WRONG-SET','W2-M16-WAKE-FIRST'),
 'M11-17': ('M11-17-ZERO','M11-17-REACQUIRE','M11-17-WAKE','M11-17-FIXED'),
 'M11-18': ('M11-18-SLEEP','M11-18-CLEAN'),
 'M11-19': ('M11-19-SEEDS','W2-M19-CLEAR-BODY','W2-M19-CLEAR-CONTACT','W2-M19-FIRST','W2-M19-LAST','W2-M19-FIFO','W2-M19-MARK-POP'),
 'M11-20': ('M11-20-KINEMATIC','W2-M20-NONTOUCH','W2-M20-STATIC','W2-M20-DUPLICATE',
              *('W2-M20-'+kind+'-'+field for kind in ('BODY','CONTACT') for field in ('COUNT','HEAD','TAIL','PREV','NEXT'))),
 'M11-21': ('M11-21-RECYCLE','W2-M21-ALLOC-FIRST','W2-M21-PARENT'),
 'M11-22': ('M11-22-TIE','M11-22-NEXT','W2-M22-DESTROY','W2-M22-IMMEDIATE','W2-M22-MULTIPLE'),
 'M11-23': ('M11-23-OLD','W2-M23-ALL'),
 'M11-24': ('M11-24-CHILD','M11-24-PARENT'),
}

                                                                          
                                                                                 
COPY_HISTORY_VARIANTS = {
 'MOVE-COPY':('W3-MOVE-SHALLOW',),
 'STATE-COPY':('W3-STATE-SHARED',),
 'CONTACT-COPY':('W3-BEGIN-SHALLOW','W3-END-SHALLOW'),
 'HIT-COPY':('W3-HITS-SHALLOW',),
 'HISTORY':('W3-HISTORY-M','W3-HISTORY-MC','W3-HISTORY-MC-OWNER',
            'W3-HISTORY-BEGIN','W3-HISTORY-END','W3-HISTORY-HIT',
            'W3-HISTORY-BEGIN-OWNER','W3-HISTORY-END-OWNER','W3-HISTORY-HIT-OWNER'),
}


def crequest_decision(root, proof=None):
    pass                                                                     
    try:
        if proof is None:proof=json.loads((HERE/'sen-d11-4-crequest.json').read_bytes())
        if proof['decision']!='D11-4(2)':return None
        if hashlib.sha256((Path(root)/proof['c_helper']).read_bytes()).hexdigest()!=proof['c_helper_sha256']:return None
        source=(Path(root)/'silnik/fizyka/gra.dk').read_text(encoding='utf-8')
        a,b=native.base.function_span(source,'checkedContactSum')
        if hashlib.sha256(source[a:b].encode()).hexdigest()!=proof['d_function_sha256']:return None
        fixture=next(x for x in load('sen_branch_crequest_f','fixtury-sen11.py').guard_definitions() if x.name=='COUNT-2-131059-1')
        for side,decimal,tag in (('c',False,'10'),('duckling',True,'11')):
            item=proof[side];process=item['process'];data=fixture.encode(decimal)
            if side=='c':data=data.replace(b'GUARD11',b'GUARD10')
            if item['input'].encode()!=data or process['code']!=0 or process['stderr']!='':return None
            if process['sha256']!=hashlib.sha256(item['stdout'].encode()).hexdigest():return None
            if process['input_sha256']!=hashlib.sha256(data).hexdigest() or process['bytes']!=len(item['stdout'].encode()):return None
            if not process['replayed_before_compaction'] or not re.fullmatch('[0-9a-f]{64}',process['binary_sha256']):return None
            echo=fixture.encode(False).replace(b'GUARD11',('GUARD'+tag).encode()).decode()
            if item['stdout']!=echo+'CASE 1 0\nGR'+tag+' 1 0 4 00000000 00000001 0001fff4 00000000\nENDCASE 1\nEND 1\n':return None
        if proof['c']['stdout'].replace('GUARD10','GUARD11').replace('GR10','GR11')!=proof['duckling']['stdout']:return None
        accepted='|CREQUEST|G11-7/8/9/10/11|GUARD3 selector2,live131059+new1|OK0,suma131060→OK0,suma131059|NOT Eb13f1dcf4053 Eec72420df5df.|'
        rows=[line for line in norm_text(HERE/'fixtures/norms/KONTRAKT-11.json').splitlines() if '|CREQUEST|' in line]
        if rows!=[accepted] or proof['proposed_row']!=accepted:return None
        if proof['proposed_row']!=proof['old_row'].replace('LIMIT3→OK0','OK0,suma131060→OK0,suma131059'):return None
        return proof
    except (KeyError,ValueError,StopIteration,OSError,TypeError):return None


def verified_native_receipt(root, recipe, receipt, hit, mutator):
    if not (receipt.get('detected') and receipt.get('native_compiled')
            and receipt.get('recipe_single_hit') and hit.get('ok')):return False
    source=(Path(root)/recipe['source']).read_text(encoding='utf-8')
    changed=mutator.apply_recipe(source,recipe)
    if receipt.get('source_sha256')!=hashlib.sha256(changed.encode()).hexdigest():return False
    baseline=receipt.get('baseline',{});mutant=receipt.get('mutant',{})
    if not (baseline.get('clean') and baseline.get('models_ok') and baseline.get('difference') is None
            and mutant.get('clean') and mutant.get('difference')):return False
    def process(row):
        return bool(row.get('code')==0 and row.get('stderr')=='' and row.get('replayed_before_compaction')
                    and row.get('bytes',0)>0 and re.fullmatch('[0-9a-f]{64}',row.get('binary_sha256','')))
    if 'sides' in baseline:
        if set(baseline['sides'])!={'c','duckling'} or not all(process(v) and v.get('model_ok') for v in baseline['sides'].values()):return False
        control=baseline['sides']['duckling']
    else:control=receipt.get('control',baseline.get('receipt',{}))
    if 'sides' in mutant:
        if set(mutant['sides'])!={'c','duckling'} or not all(process(v) for v in mutant['sides'].values()):return False
        actual=mutant['sides']['duckling']
    else:actual=mutant.get('receipt',{})
    if recipe['fixture'] in ('COPY-PROBE:STATE','HISTORY-MOVE-PROBE'):
                                                                               
        control=receipt.get('control',{})
        if not process(control):return False
        difference=mutant['difference']
        for key,process_row in (('baseline',control),('mutant',actual)):
            raw=difference.get(key,'').encode()
            if not raw or process_row.get('sha256')!=hashlib.sha256(raw).hexdigest() or process_row.get('bytes')!=len(raw):return False
    return bool(process(control) and process(actual) and control['binary_sha256']!=actual['binary_sha256'])


def frozen_table(root, results=(), new_results=(), component_receipt=None):
    rows = obligations(); receipts = {r['name']: r for r in results}
    recipes = {r['name']: r for r in native.recipes()['native_mutations']}
    hits = {r['name']: r for r in native.applicability(root)}
    shared = []
    component_ok=bool(component_receipt and component_receipt.get('N')==16
                      and component_receipt.get('completed_cases')==16
                      and component_receipt.get('global_END_checked')
                      and not component_receipt.get('errors') and not component_receipt.get('intermediate_only'))
    for row in rows:
        if row['id'] not in recipes: continue
        name = row['id']; receipt = receipts.get(name, {}); anchor = hits[name]
        row['port'] = recipes[name]['source'] + ':' + str(anchor.get('port_line', 'UNVERIFIED'))
        if receipt.get('detected') and receipt.get('mutant', {}).get('replayed_before_compaction'):
                                                                            
            row['shared_helper_native'] = {'fixture': recipes[name]['fixture'], 'first_difference': receipt['difference']}
            row['status'] = 'HELPER WYKRYTY; GAP Ec1a78613530c Ec1b717ab8233 / Eb46d2b5dbabf Eaea440a813f611'
            shared.append(name)
    actual = load('sen_branch_new_actual', 'mutacje-sen11.py')
    planned = {r['name']: r for r in actual.planned()}
    new_hits = {r['name']: r for r in actual.applicability(root)}
    evidence = []
    for receipt in new_results:
        name = receipt['name']; recipe = planned.get(name)
        if recipe is None: raise ValueError('unknown native11 receipt: ' + name)
        difference = receipt.get('mutant', {}).get('difference')
        if difference and difference.get('tag')=='GR11':
                                                                           
                                                                         
            difference={**difference,'helper_kind':difference.get('seq'),'seq':0}
        native_ok = verified_native_receipt(root,recipe,receipt,new_hits[name],actual)
        obligation=next((r for r in rows if r['id']==recipe['class_id']),None)
        original=re.findall(r'\b[a-z_]+\.c:[0-9,–−-]+',obligation['predicate'] if obligation else '')
        if recipe['class_id']=='M12':original=['world.c:649–658']
        original={
          'CREQUEST':['silnik/port/kontrola-solver-guard.h:14–18,105–111'],
          'MOVE-COPY':['world.c:1491','silnik/port/kontrola-solver.c:88–96'],
          'STATE-COPY':['body.c:1476,1531','silnik/port/kontrola-sen.c:69–73'],
          'CONTACT-COPY':['world.c:1529','silnik/port/kontrola-kontakty9.h:153–160'],
          'HIT-COPY':['world.c:1529','silnik/port/kontrola-solver.c:100–106'],
          'HISTORY':['world.c:1491,1529','silnik/port/kontrola-solver.c:83–96,100–106','silnik/port/kontrola-kontakty9.h:153–160'],
        }.get(recipe['class_id'],original)
        entry = {'name': name, 'class_id': recipe['class_id'], 'fixture': recipe['fixture'],
                 'port': recipe['source'] + ':' + str(new_hits[name].get('port_line')),
                 'all_edits':new_hits[name].get('all_edits',[]),
                 'original': ', '.join(original) if original else 'KONTRAKT-11 dodatek D / '+recipe['class_id']+' (oslona API gry)', 'difference': difference,
                 'native_killed': native_ok, 'case': difference.get('case',difference.get('id')) if difference else None,
                 'seq': difference.get('seq') if difference else None,
                 'f32': receipt.get('baseline', {}).get('predicates', []),
                 'baseline_failed': receipt.get('baseline_failed', False)}
        evidence.append(entry)
        if difference and difference.get('tag')=='LOCAL11':
            entry.update(case='LOCAL11/'+name,seq=0,baseline_bridge='full C03 id1/seq6 plus native control equal to C fields')
    by_name={e['name']:e for e in evidence}
    for row in rows:
        found = [e for e in evidence if e['class_id'] == row['id']]
        if not found: continue
        row['native_evidence'] = found
        killed = [e for e in found if e['native_killed']]
        if not killed: continue
        first = killed[0]
        row.update(port=first['port'], actual_case=first['case'], actual_seq=first['seq'],
                   first_difference=first['difference'])
                                                                             
                                                                             
        if row['kind'] == 'core':
            variants=[]
            for name in CORE_VARIANTS[row['id']]:
                entry=by_name.get(name)
                variants.append({'obligation':name,'verified':bool(entry and entry['native_killed']),
                                 'evidence':entry,'missing':None if entry and entry['native_killed'] else name})
            row['branch_variants']=variants
            row['remaining_variants']=[v['obligation'] for v in variants if not v['verified']]
            row['private_C01_C16_verified']=component_ok
            if not row['remaining_variants'] and component_ok:
                row.update(status='WYKRYTE NATYWNIE — wszystkie wymienione warianty E i COMPONENT16',counted_as_killed=True)
            else:
                row['status']='NATYWNE MUTACJE: '+str(len(killed))+'; LUKI: '+', '.join(row['remaining_variants'])
                if not component_ok:row['status']+='; missing pelnego potwierdzenia C01-C16 w tym biegu'
        elif row['id']=='CREQUEST':
            row['status']='NATYWNA ROZNICA checksum; GAP oczekiwanej roznicy LIMIT3 -> OK0 z dodatku D (GUARD3 selector2 sprawdza sama sume)'
        elif row['id'] in COPY_HISTORY_VARIANTS:
            row['branch_variants']=[{'obligation':name,'verified':bool(by_name.get(name,{}).get('native_killed')),
                                    'evidence':by_name.get(name)} for name in COPY_HISTORY_VARIANTS[row['id']]]
            row['remaining_variants']=[v['obligation'] for v in row['branch_variants'] if not v['verified']]
            row.update(status='WYKRYTE NATYWNIE — wszystkie warianty kopii/historii' if not row['remaining_variants'] else 'LUKI: '+', '.join(row['remaining_variants']),
                       counted_as_killed=not row['remaining_variants'])
        elif row['id'].startswith('TH-ZERO-') and not any(r.get('minus_zero_detected') for r in new_results if r['name'] == first['name']):
            row['status'] = 'NATYWNY +0; GAP swiadka -0'
        else:
            row.update(status='WYKRYTE NATYWNIE', counted_as_killed=True)
    decision=crequest_decision(root)
    if decision:
        row=next(r for r in rows if r['id']=='CREQUEST')
        row.update(status='D11-4(2): FAIL DODATKU D; C == D: OK0, suma131060. Ee746286fa0fc E3268fef5c876 E924ffcababf8, E283ada7088c2 E3268fef5c876 Ed64c7c1f7f02.',
                   closed_by_decision=True,decision=decision,counted_as_killed=False)
    return {'rows': rows, 'proofs': proofs(root), 'shared_helpers_detected': shared,
            'native_recipe_evidence': evidence,
            'native_gaps': [r['id'] for r in rows if not r['counted_as_killed'] and not r.get('closed_by_decision')],
            'complete': False, 'M12': 'WYKRYTE NATYWNIE' if any(r['id']=='M12' and r['counted_as_killed'] for r in rows) else 'ODROCZONE_DO_KROKU_11',
            'boundary11a': 'D11-3: oddzielny odbior11a uchylony; wymagany pelny PUBLIC129 i COMPONENT16',
            'component16_verified':component_ok,
            'core_variant_gaps':{r['id']:r.get('remaining_variants',list(CORE_VARIANTS[r['id']])) for r in rows if r['kind']=='core' and not r['counted_as_killed']}}


def trace_predicates(records):
    pass                                                                       
    rows = {}
    for tag, v in records: rows.setdefault(tag, []).append(v)
    sim = {(w, h[22]): h for (w, _, _), h in m.index(rows, 'SM11').items()}
    bs = m.index(rows, 'BS11'); cx = m.index(rows, 'CX10'); ws = m.index(rows, 'WS11')
    result = []
    for v in rows.get('BV10', ()):
        w, sub, phase, bid = v[2:6]
        if sub != 0 or phase != 7 or (w, bid) not in sim or (w,) not in cx: continue
        velocity = tuple(map(m.number, v[6:8])); angular = m.number(v[8])
        delta = tuple(map(m.number, v[9:11])); delta_s = m.number(v[12])
        extent = m.number(sim[w, bid][18]); inv_dt = m.number(cx[w,][1])
        m.require((w,0) in ws or (w,1) in ws, 'predicate receipt needs real WS11 sleep flag')
        measured = m.sleep_velocity(velocity, angular, extent, delta, delta_s, inv_dt)
                                                                        
                                                                             
        vx2,vy2=m.mul(velocity[0],velocity[0]),m.mul(velocity[1],velocity[1])
        v2=m.add(vx2,vy2);vlen=m.f32(math.sqrt(v2))
        abs_w=-angular if angular<0 else angular;wr=m.mul(abs_w,extent)
        max_v=m.add(vlen,wr)
        dx2,dy2=m.mul(delta[0],delta[0]),m.mul(delta[1],delta[1])
        d2=m.add(dx2,dy2);dlen=m.f32(math.sqrt(d2))
        abs_s=-delta_s if delta_s<0 else delta_s;sr=m.mul(abs_s,extent)
        max_d=m.add(dlen,sr);half_inv_dt=m.mul(.5,inv_dt);correction=m.mul(half_inv_dt,max_d)
        arithmetic={'vx':velocity[0],'vy':velocity[1],'w':angular,'delta.x':delta[0],'delta.y':delta[1],'deltaRotation.c':m.number(v[11]),'deltaRotation.s':delta_s,
                    'vx*vx':vx2,'vy*vy':vy2,'v2':v2,'sqrtf(v2)':vlen,'abs(w)':abs_w,'abs(w)*extent':wr,'maxVelocity':max_v,
                    'dx*dx':dx2,'dy*dy':dy2,'delta2':d2,'sqrtf(delta2)':dlen,'abs(delta.s)':abs_s,'abs(delta.s)*extent':sr,
                    'maxDeltaPosition':max_d,'0.5*inv_dt':half_inv_dt,'correction':correction,'sleepVelocity':measured}
        threshold, timer, enabled = bs[w, bid][:3]
        result.append({'case': v[0], 'seq': v[1], 'world': w, 'body': bid,
                       'original': 'solver.c:587–596,621,655,660',
                       'H': {'sleepVelocity': f'{m.bits(measured):08x}', 'threshold': f'{threshold:08x}',
                             'sleepTime': f'{timer:08x}', 'maxExtent': f'{sim[w, bid][18]:08x}',
                             'inv_dt': f'{cx[w,][1]:08x}'},
                       'f32_steps_H':{key:f'{m.bits(value):08x}' for key,value in arithmetic.items()},
                       'maxVelocity_gt_correction':max_v>correction,
                       'sleepVelocity_gt_threshold': measured > m.number(threshold),
                       'sleepVelocity_eq_threshold': measured == m.number(threshold),
                       'sleepTime_lt_half': m.number(timer) < .5,
                       'sleepTime_eq_half': m.number(timer) == .5, 'body_enableSleep': bool(enabled),
                       'world_enableSleep': bool(ws.get((w, 0), ws.get((w, 1), (0,)))[0])})
    return result


def markdown(table):
    lines = ['# Sen — gałąź → case', '',
             'E317ecd32308a Edcbe25a9c311. E33d528172a3d E8d04310ae7da Ecd5b158f21b7 E35e99f929e01 E7069227ea676 Ecc85eb437513. Eb9478cafd212 E886ebea7a420 E1a1d2e5d3ecb E33dcc1a09b95 E14a587d16185 E410d30bd98bb Ecd5b158f21b7 E35e99f929e01 E7ced67c2595c E2db12a085e85.', '',
             '| E12156e921bdb | E14c3f1e2bd43 / Ebc34da44d8b8 | E72e9a59f5a1d | E627d017fc783 E45be1cb66c09 | Eef9d9d56185e Ea56145270ce6/E4f5260d71c7e | E8cc24dfe921c Ed0214da571af E6199aecf23ab E832171ed9e98 | E931647da0d5b |',
             '|---|---|---|---|---|---|---|']
    if table.get('source_commit'):lines.insert(2,'Kod tabeli: '+table['source_commit']+'; historia dowodow w oddzielnych receptach.\n')
    if table.get('evidence_provenance'):
        lines.insert(3,'Pochodzenie: '+json.dumps(table['evidence_provenance'],ensure_ascii=False)+'. E1f965d7d73ad Eddc1b687a5c211: UNVERIFIED.\n')
    for row in table['rows']:
        actual = str(row['actual_case']) + '/' + str(row['actual_seq']) if row['actual_case'] is not None else 'UNVERIFIED'
        status = row['status']
        if row.get('shared_helper_native'):
            shared = row['shared_helper_native']
            status += '; helper ' + shared['fixture'] + ': ' + json.dumps(shared['first_difference'], separators=(',', ':'))
        values = (row['id'], row['predicate'], row['port'] or 'UNVERIFIED', row['planned_witness'],
                  actual, row['required_difference'], status)
        lines.append('| ' + ' | '.join(str(v).replace('|', '&#124;').replace('\n', ' ') for v in values) + ' |')
    lines += ['', 'M12: ' + table['M12'], '', '## Natywne przepisy: port i pierwsza difference', '',
              '| Przepis / klasa | Port / oryginal | Swiadek, id/seq | Pierwsza difference | Wynik |',
              '|---|---|---|---|---|']
    for entry in table.get('native_recipe_evidence', []):
        locations=', '.join(str(e['line']) for e in entry.get('all_edits',[]))
        values = (entry['name'] + ' / ' + entry['class_id'], entry['port'] + ('; kotwice '+locations if locations else '') + ' / ' + str(entry['original']),
                  entry['fixture'] + ': ' + str(entry['case']) + '/' + str(entry['seq']),
                  json.dumps(entry['difference'], ensure_ascii=False), 'WYKRYTE' if entry['native_killed'] else 'UNVERIFIED')
        lines.append('| ' + ' | '.join(str(v).replace('|','&#124;').replace('\n',' ') for v in values) + ' |')
    lines += ['',
              '## Dowody (poza licznikiem zabitych)', '']
    lines += ['- ' + p['classification'] + ': ' + p['literal'] + '. ' + p['proof'] for p in table['proofs']]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    root = HERE.parents[1]; table = frozen_table(root)
    (HERE / 'sen-galezie.json').write_text(json.dumps(table, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (HERE / 'SEN-GALEZIE.md').write_text(markdown(table), encoding='utf-8')
