pass                                                                      

                                                                              
                                                                              
                                                                        
   
import importlib.util
import json
from pathlib import Path
import sys
import math
import re
import hashlib

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('zywy_table_f32', HERE / 'model-solver.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def predicate_receipts():
    pass                                                                       
    pi = m.number(0x40490fdb)
    center = m.number(0x46000000)
    square = m.mul(center, center)
    origin = m.mul(pi, m.add(.5, square))
    inverse = m.div(1, pi)
    weighted = m.mul(pi, center)
    local = m.mul(inverse, weighted)
    subtracted = m.mul(pi, m.mul(local, local))
    inertia = m.add(origin, -subtracted)
    target = m.number(0x7f7fffff)
    length_squared = m.add(m.mul(target, target), m.mul(0., 0.))
    norm_lower = m.add(1., -m.f32(.0006))
    norm_upper = m.add(1., m.f32(.0006))
    normal_tolerance = m.mul(100., m.number(0x34000000))
    slop_squared = m.mul(.005, .005)
    def h(value):
        return f'{m.bits(value):08x}'
    angles = []
    for y, x in ((0., 0.), (-0., 0.), (0., -0.), (-0., -0.),
                 (1., 0.), (-1., 0.), (0., 1.), (0., -1.),
                 (1., 1.), (1., -1.), (-1., 1.), (-1., -1.),
                 (2., 1.), (1., 2.), (-2., 1.), (1., -2.)):
        angles.append({'y': h(y), 'x': h(x), 'x_eq_zero_and_y_eq_zero': x == 0 and y == 0,
                       'abs_y_gt_abs_x': abs(y) > abs(x), 'x_lt_zero': x < 0, 'y_lt_zero': y < 0,
                       'source': 'src/math_functions.c:61-101', 'native_result': None})
    return {
        'status': 'RACHUNEK MODELU — NOT NATYWNE WYKONANIE',
        'S12': {'mass': h(pi), 'invMass': h(inverse), 'weightedCenter': h(weighted),
                'localCenter': h(local), 'originInertia': h(origin),
                'subtracted': h(subtracted), 'inertia': h(inertia),
                'source': 'src/geometry.c:222-229;src/body.c:592-597'},
        'target_derived': {'dt': h(1.), 'v.x': h(target), 'v.y': h(0.), 'w': h(0.),
                           'v.x_finite': True, 'lengthSquared': h(length_squared),
                           'finite_maxVelocity': False, 'source': 'src/body.c:830-843'},
        'target_rotation': {'lower_strict': h(norm_lower), 'upper_strict': h(norm_upper),
                            'order': 'f32(f32(s*s)+f32(c*c)); both inequalities strict',
                            'port': None},
        'replacement_normal': {'tolerance_strict': h(normal_tolerance),
                               'order': 'f32(abs(f32(1-f32(f32(nx*nx)+f32(ny*ny))))) < tolerance',
                               'source': 'include/box2d/math_functions.h:310-314'},
        'segment': {'linearSlop': h(.005), 'lengthSquared_equal': h(slop_squared),
                    'accepted_at_equality': False, 'port': None},
        'Atan2': angles,
        'Bupper11': {str(n): {'lastWidthBound': n//4+3, 'accepted': n//4+3 <= 32767}
                     for n in (131059, 131060)},
        'checkedSum': {'count': '7fffffffffffffff', 'add': 1, 'accepted': False},
        'tickets': {'last': ['ffffffff', '80000000'], 'next': ['00000000', '80000001'],
                    'last_MAX_minus_1_two_pairs': 'LIMIT3, no partial allocation'},
    }


def route_plan(root):
    pass                                                                     

                                                                              
                                                                         
       
    spec=importlib.util.spec_from_file_location('zywy_route_inputs',HERE/'wejscia-zywy-oslony.py')
    guards=importlib.util.module_from_spec(spec);sys.modules[spec.name]=guards;spec.loader.exec_module(guards)
    manifest=json.loads((Path(root)/'silnik/port/zywy-mapa.json').read_bytes())
    inventory=manifest['original_functions']
    functions={}
    for path in sorted((Path(root)/'silnik/fizyka').glob('*.dk')):
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        declarations=[(i,re.match(r'^fun ([A-Za-z0-9_]+)\(',line)) for i,line in enumerate(lines)]
        declarations=[(i,match.group(1)) for i,match in declarations if match]
        for j,(start,name) in enumerate(declarations):
            end=declarations[j+1][0] if j+1<len(declarations) else len(lines)
            functions.setdefault(name,[]).append({'file':str(path.relative_to(root)).replace('\\','/'),'line':start+1,
                'guard_statements':[{'line':i+1,'text':lines[i].strip()} for i in range(start,end)
                                    if not lines[i].lstrip().startswith('#') and any(s in lines[i] for s in ('MutationStatus(','valid','safe','preflight(','prepareReplacement('))]})
    body=('setType','setEnabled','setMassData','applyMass','setLinearDamping','setAngularDamping','setGravityScale','setFixedRotation','setTargetTransform')
    raw_body=('b2Body_SetType','b2Body_Enable','b2Body_SetMassData','b2Body_ApplyMassFromShapes','b2Body_SetLinearDamping','b2Body_SetAngularDamping','b2Body_SetGravityScale','b2Body_SetFixedRotation','b2Body_SetTargetTransform')
    shape=('setFriction','setRestitution','setMaterial','setSurfaceMaterial','setFilter',*(['replaceGeometry']*4))
    raw_shape=('b2Shape_SetFriction','b2Shape_SetRestitution','b2Shape_SetMaterial','b2Shape_SetSurfaceMaterial','b2Shape_SetFilter','b2Shape_SetCircle','b2Shape_SetCapsule','b2Shape_SetSegment','b2Shape_SetPolygon')
    result=[]
    for fixture in guards.definitions()+guards.history_routes()+guards.core_routes()+guards.transfer_routes()+guards.name_routes():
        code=fixture.kind-200 if fixture.kind>=200 else fixture.kind-100 if fixture.kind>=100 else fixture.rows[-1][0] if fixture.rows else None
        words=fixture.words if fixture.kind>=100 else fixture.rows[-1][1:] if fixture.rows else fixture.words
        subkind=words[3] if code in (80,81,92) else words[2] if code==82 else None
        game_name=raw_name=None
        if code==80 and subkind<len(body):
            game_name,raw_name=body[subkind],raw_body[subkind]
            if subkind==1 and not fixture.words[4]:raw_name='b2Body_Disable'
        elif code==81 and subkind<len(shape):game_name,raw_name=shape[subkind],raw_shape[subkind]
        elif code==82:
            subkind=words[2]
            game_name=('enableWarmStarting','setRestitutionThreshold','setHitEventThreshold',
                       'setContactTuning','setMaximumLinearSpeed','setGravity')[subkind]
            raw_name=('b2World_EnableWarmStarting','b2World_SetRestitutionThreshold','b2World_SetHitEventThreshold',
                      'b2World_SetContactTuning','b2World_SetMaximumLinearSpeed','b2World_SetGravity')[subkind]
        elif code==92:
            game_name=('getLocalPoint','getWorldPoint','getLocalVector','getWorldVector',
                       'getLocalPointVelocity','getWorldPointVelocity')[subkind]
            raw_name=('b2Body_GetLocalPoint','b2Body_GetWorldPoint','b2Body_GetLocalVector','b2Body_GetWorldVector',
                      'b2Body_GetLocalPointVelocity','b2Body_GetWorldPointVelocity')[subkind]
        elif fixture.rows:
            game_name='copyContactEvents' if fixture.group in ('G11','G12') else 'setTargetTransform' if fixture.expected_awake is not None else None
            if fixture.expected_awake is not None:raw_name='b2Body_SetTargetTransform'
            if fixture.name.startswith('G12-TRANSFER-'):game_name='setType';raw_name='b2TransferBody'
            if fixture.name.startswith('G12-NAME-create-'):game_name='createBody8';raw_name='b2CreateBody'
        elif fixture.name.startswith('G12-LOCK-'):game_name=fixture.name[len('G12-LOCK-'):]
        if fixture.name.startswith('G12-TRANSFER-'):game_name='setType';raw_name='b2TransferBody'
        trace=[]
        if fixture.field_word is not None:
            word=fixture.words[fixture.field_word];value=m.number(word)
            trace=[{'step':'decode exact binary32','GA_word':fixture.field_word,'bits':f'{word:08x}'},
                   {'step':'finite','value':math.isfinite(value)}]
            if fixture.sign_rule:
                trace.append({'step':'>0' if fixture.sign_rule=='positive' else '>=0',
                              'value':value>0 if fixture.sign_rule=='positive' else value>=0})
        if 'TARGET-norm-' in fixture.name:
            c,s=map(m.number,fixture.words[6:8]);ss=m.mul(s,s);cc=m.mul(c,c);norm=m.add(ss,cc)
            lower=m.add(1.,-m.f32(.0006));upper=m.add(1.,m.f32(.0006))
            trace=[{'step':'s*s','bits':f'{m.bits(ss):08x}'},{'step':'c*c','bits':f'{m.bits(cc):08x}'},
                   {'step':'f32(s*s+c*c)','bits':f'{m.bits(norm):08x}'},
                   {'step':'strict lower','bits':f'{m.bits(lower):08x}','passes':lower<norm},
                   {'step':'strict upper','bits':f'{m.bits(upper):08x}','passes':norm<upper}]
        if fixture.kind==3 and fixture.words[0] in (0,1):
            upper=fixture.words[1];blocks=upper//4+3
            trace=[{'step':'floor(upper/4)+3','upper':upper,'blocks':blocks,'limit':32767,'passes':blocks<=32767}]
        if fixture.name=='G12-TARGET-derived-maxVelocity':trace=[predicate_receipts()['target_derived']]
        if fixture.name=='G12-S12-GEOMETRY':trace=[predicate_receipts()['S12']]
        if fixture.expected_awake is not None:
            delta=fixture.rows[-1][5];square=m.mul(m.number(delta),m.number(delta));speed=m.f32(math.sqrt(square))
            trace=[{'step':'dx','bits':f'{delta:08x}'},{'step':'f32(dx*dx)','bits':f'{m.bits(square):08x}'},
                   {'step':'sqrt rounded f32','bits':f'{m.bits(speed):08x}'},
                   {'step':'return when maxVelocity < sleepThreshold','threshold':'3d4ccccd','passes':speed<m.number(0x3d4ccccd),
                    'expected_awake':fixture.expected_awake}]
        byte_trace=None
        if fixture.name.startswith('G12-NAME-create-'):
            row=fixture.rows[-1];data=bytes(row[22:22+row[21]])
            try:data.decode('utf-8');valid_utf8=True
            except UnicodeDecodeError:valid_utf8=False
            byte_trace={'length_bytes':len(data),'length_le31':len(data)<=31,'no_internal_NUL':0 not in data,
                        'valid_UTF8_scalar_sequence':valid_utf8,'raw_bypasses_game_name_policy':row[3]==0}
        result.append({'id':fixture.name,'group':fixture.group,'input_G_kind':fixture.kind,'input_GA64':list(fixture.words),
            'operations':[list(row) for row in fixture.rows],'opcode':code,'subkind':subkind,
            'phase':'actual raw preSolve' if fixture.kind>=200 else 'last ordinary O' if fixture.rows else 'real helper seq0',
            'port_functions':functions.get(game_name,[]) if game_name else [],
            'original_functions':[{'file':f['file'],'line':f['line'],'function':f['function']} for f in inventory if f['function']==raw_name],
            'predicate':fixture.predicate,'f32_steps':trace,'expected_base_status':fixture.status if not fixture.rows else fixture.last_status,
            'byte_predicates':byte_trace,
            'case_id':1,'seq':len(fixture.rows),'helper':fixture.helper,
            'manifest_candidate_ids':sorted({int(value) for requirement in manifest['guard_requirements'] if requirement['predicate_source'].startswith(fixture.group+' ')
                                             for value in re.findall(r'id(\d+)',requirement['witness_full'])}),
            'baseline_only':True,'native_mutation_status':'UNVERIFIED','deletion_effect':None,
            'remaining':'per-predicate C/port branch pairing and native mutant/proof, not just function binding'})
    return result


def frozen_table(root=None, receipts=()):
    pass                                                                  

                                                                            
                                                                             
                                                                          
       
    root = Path(root) if root is not None else HERE.parents[1]
    data = json.loads((root / 'silnik/port/zywy-mapa.json').read_bytes())
    rows = []
    for name, ids in data['classes'].items():
        rows.append({'id': name, 'kind': 'manifest_class', 'candidate_ids': ids,
                     'original': [f'{f['file']}:{f['line']} {f['function']}'
                                  for f in data['original_functions'] if name in f['classes']],
                     'port': None, 'operation': None, 'phase': None,
                     'actual_predicates': [], 'native_status': 'GAP — UNVERIFIED',
                     'first_difference': None})
    for j, requirement in enumerate(data['guard_requirements'], 1):
        rows.append({'id': f'P12-{j:03}', 'kind': 'guard_requirement', **requirement,
                     'port': None, 'operation': None, 'phase': None,
                     'actual_predicates': [], 'native_status': 'GAP — UNVERIFIED',
                     'first_difference': None})
    return {'version': 1, 'rows': rows, 'native_gaps': [r['id'] for r in rows],
            'route_plan':route_plan(root),
            'predicate_receipts': predicate_receipts(),
            'original_line_inventory': data['original_functions'],
            'receipt_count': len(tuple(receipts)), 'accepted_receipts': 0,
            'errors': ['No executable step12 recipes/port witnesses yet; source inventory is not branch coverage.'],
            'code': 1}


def measured_table(root,parameters=None,mutation=None):
    pass                                                                      

                                                                             
                                                                             
       
    root=Path(root);table=frozen_table(root)
    table['measured_parameter_routes']=[];table['measured_native_branches']=[]
    table['native_verified_recipes']=0;table['measurement_errors']=[]
    if parameters and parameters.get('code')==0 and parameters.get('planned',0)>0:
        routes=parameters.get('routes',())
        if len(routes)==parameters['planned']==parameters.get('native_ok') and all(r.get('ok') for r in routes):
            table['measured_parameter_routes']=routes
    if mutation and mutation.get('code')==0:
        try:
            require=m.require
            require(mutation.get('native_product_mutants')==mutation.get('clean_native_kills')==1,'one actual product mutant')
            require(mutation.get('routes_detecting')==4 and len(mutation.get('routes',()))==4,'all four native routes')
            for path,key in (('silnik/fizyka/gra.dk','source_before'),('silnik/port/model-zywy.py','model_sha256'),
                             ('silnik/port/mutacje-zywy-2a.py','owner_source_sha256')):
                require(hashlib.sha256((root/path).read_bytes()).hexdigest()==mutation.get(key),'current source binding '+path)
            predicate=mutation['C_oracle_predicate']
            require(predicate['file']=='silnik/port/kontrola-zywy.c','exact C game-oracle file')
            require(hashlib.sha256((root/predicate['file']).read_bytes()).hexdigest()==predicate['sha256'],'current C oracle')
            guard=mutation['port_guard'];require(guard['file']=='silnik/fizyka/gra.dk' and guard['scope']=='safeMass','exact owner target')
            lines=(root/guard['file']).read_text(encoding='utf-8').splitlines()
            require(lines[guard['line']-1].strip()==mutation['recipe']['expression'],'same current scoped guard')
            for route in mutation['routes']:
                require(route['baseline_status_reason']==[4,0] and route['mutant_status_reason']==[0,0],'D12-4 statuses')
                require(route['first_difference'] is not None,'clean actual first difference')
                require(all(v['code']==0 and v['stderr_bytes']==0 and v['END_EOF'] for v in route['runs'].values()),'clean native processes/EOF')
                require(set(route['independent_models'])=={'C','C0','D'} and all(v['ok'] for v in route['independent_models'].values()),'separate model rejection/history')
            table['native_verified_recipes']=1
            table['measured_native_branches']=[{**r,'port_guard':guard,'port_predicate':mutation['port_predicate'],
                'C_oracle_predicate':predicate,'shared_native_mutant':mutation['recipe']['name']}
                for r in mutation['routes']]
            table['errors']=['Full branch coverage incomplete; one measured recipe does not cover all93 obligations.']
        except (KeyError,IndexError,TypeError,ValueError) as exc:table['measurement_errors'].append(str(exc))
                                                                             
    return table


def markdown(table):
    lines = ['# Krok12 — E2738e1f7f179 E947578d56c3f → case', '',
             'UNVERIFIED. E12156e921bdb z E64e3632b1b91 E31ec1412a751 E0292a9fa0ce5. E0ab06d24be91/E3d955dd15599/Ef8d397a33fcb Ede7d1b721a1e Ebc2e4bea2e33 Ee0851795318b E7e67c6148bf5 E574440889a40.', '',
             '| E87d38643c2eb | E6ff1a4ce9dfd / Ef642844c3fd8 | E12156e921bdb E03f2777bec78 / Ebae10bcdb3da E45be1cb66c09 | E931647da0d5b |',
             '|---|---|---|---|']
    for row in table['rows']:
        source = ', '.join(row['original']) if row['kind'] == 'manifest_class' else row['predicate_source']
        candidate = ', '.join(map(str, row['candidate_ids'])) if row['kind'] == 'manifest_class' else row['witness_full']
        escape = lambda value: str(value).replace('|', '\\|').replace('\n', ' ')
        lines.append('| '+' | '.join(map(escape, (row['id'], source, candidate, row['native_status'])))+' |')
    lines += ['', 'E5a6105745367 E3f90df4e6aa8 C Ecd5b158f21b7 E35e99f929e01 Ecc6c0049b1c4 Ee8f902f1fc88 E2e1d8cc82ab7 E33dcc1a09b95 E07faf1595531 E6b87efc7ae59.',
              'Ed1be5e44bae6 binary32 Ecd5b158f21b7 E31ec1412a751 E99cf5e2ab940 Ec31fa422f9a7 Ea3ad92305e5c.', '']
    lines+=['## E011e70b6be12 E483e3af025d5 E6b87efc7ae59 E3d9fc4bde7ce Ea47f6d13afa6','',
            'Ef4b06ef6d3c8 Ed108722dfc00 Ed0dea1df95b8 Ede7d1b721a1e E40e0b797efb6, E283ada7088c2 Ebf0c3648fafd E3603fa1262db E70368d34b80b E480601539f49 Ed0afe5ed2bd6 E0840f545c010. Eff624a4b9cdb64E0fbc26485e23 Ede7d1b721a1e O E31ec1412a751 E50e721e49c01 E8a84e406c08a_E64879f7d6b96 JSON.',
            '','| Świadek | Opcode/faza | Port ↔ C (funkcje) | Predykat / rachunek |','|---|---|---|---|']
    for row in table.get('route_plan',()):
        port=', '.join(f'{f['file']}:{f['line']}' for f in row['port_functions']) or 'MISSING BINDING'
        original=', '.join(f'{f['file']}:{f['line']}' for f in row['original_functions']) or 'MISSING BINDING'
        trace=json.dumps(row['f32_steps'],ensure_ascii=False,separators=(',',':'))
        lines.append('| '+row['id']+' | '+str(row['opcode'])+'/'+str(row['subkind'])+' '+row['phase']+' | '+port+' ↔ '+original+' | '+row['predicate']+' '+trace+' |')
    if table.get('measured_parameter_routes'):
        lines+=['## Ed1c7232fcf5c Ef0786b32909d Ea47f6d13afa6 Ec895df08bc34 E499c7f91d861','',
                'E74935925bd4d Ef762defcd219 Ede7d1b721a1e E4b3a70f6e20f Ee863a373cd49; Ed0214da571af E6199aecf23ab E832171ed9e98 Ef4465733b96b NIEZWERYFIKOWANA. NOT E31ec1412a751 E663ea1bfffe5 E15dc7a5f44fa Ea54a898eaedf.','',
                '| Przypadek osobnego GUARD/O | Port ↔ C | Predykaty binary32 | Wynik |','|---|---|---|---|']
        for r in table['measured_parameter_routes']:
            port=', '.join(f'{f['file']}:{f['line']}' for f in r['port_functions']) or 'GAP'
            original=', '.join(f'{f['file']}:{f['line']}' for f in r['original_functions']) or 'GAP'
            lines.append('| '+r['name']+' /1/'+str(r['seq'])+' | '+port+' ↔ '+original+' | '+
                         json.dumps(r['f32_steps'],ensure_ascii=False)+' | C=D PARAM5/reason0, E1a5e497a2bfa E283ada7088c2 E669673d4ce6c |')
    if table.get('measured_native_branches'):
        lines+=['','## D12-4 — jeden natywny mutant, cztery drogi','',
                'E87fe40a12d67 COMPONENT12; Ea56145270ce6 E10371f3dd9091..4, E4f7ece44048d Ef39441f51b35 E3d9fc4bde7ce E4e1353eee89b E977ee5cf9e9f id1. E973d0c649aa9 E036a8a704eee E09c95f41f84f E8e6a6cca7aae.','',
                '| E14c3f1e2bd43 port ↔ C Ee8488b58c398 E499c7f91d861 | case/E037aeaeaf4bb/E3d955dd15599 | E2f93ec95c9e5 f32 | Efcb52aadf9cf Ed0214da571af E640ce62fcbca |','|---|---|---|---|']
        for r in table['measured_native_branches']:
            g=r['port_guard'];c=r['C_oracle_predicate']
            lines.append('| '+g['file']+':'+str(g['line'])+' ↔ '+c['file']+':'+str(c['line'])+
                ' | '+r['route']+'/O'+str(r['seq'])+' po RAW81r0 | '+json.dumps(r['f32_steps'])+
                ' | AP4/reason0 → AP0/reason0; '+json.dumps(r['first_difference'],ensure_ascii=False)+' |')
    return '\n'.join(lines)


if __name__ == '__main__':
    print(markdown(frozen_table()), end='')
