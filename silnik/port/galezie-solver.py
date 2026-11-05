pass                                                                     

                                                                          
                                                                           
   
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


native=load('solver_branch_native','mutacje-solver.py')
m=native.m;f=native.f;w=native.w


def rotate(q,v):return (m.add(m.mul(q[0],v[0]),-m.mul(q[1],v[1])),m.add(m.mul(q[1],v[0]),m.mul(q[0],v[1])))
def subtract(a,b):return (m.add(a[0],-b[0]),m.add(a[1],-b[1]))
def add2(a,b):return (m.add(a[0],b[0]),m.add(a[1],b[1]))
def dot(a,b):return m.add(m.mul(a[0],b[0]),m.mul(a[1],b[1]))


def trace_predicates(records):
    pass                                                                     

                                                                        
                                                                           
                                                                         
                                                              
       
    result=[];dense={};states={};settings={}
    for tag,v in records:
        if tag=='DN':dense[v[0],v[1],v[2],v[3]]=v[4]-1
        if tag=='BV10':states[v[:5]+(v[5],)]=v[6:]
        if tag=='W10':settings[v[:3]]=v[3:]
    def state(prefix,index):
        if index==m.NULL:return (0.,0.,0.,0.,0.,1.,0.)
        ident,seq,world,sub,phase=prefix
        body=dense.get((ident,seq,world,index),index)
        words=states.get((ident,seq,world,sub,phase,body))
        if words is None:return None
        return tuple(map(m.number,words))
    for tag,v in records:
        if tag!='SC10':continue
        ident,seq,world,sub,phase,color,packet,lane=v[:8];h=v[8:];c=h[2:]
        if phase!=7 or c[0]==m.NULL:continue
        a=state((ident,seq,world,sub,phase),c[1]);b=state((ident,seq,world,sub,phase),c[2])
        if a is None or b is None:continue
        fields=tuple(map(m.number,c));normal=fields[4:6]
        for point in range(c[3]):
            start=19+11*point;anchor_a=fields[start:start+2];anchor_b=fields[start+2:start+4]
            ds=add2(subtract(b[3:5],a[3:5]),subtract(rotate(b[5:7],anchor_b),rotate(a[5:7],anchor_a)))
            separation=m.add(fields[start+4],dot(ds,normal));relative=fields[start+5];total=fields[start+8]
            params=settings.get((ident,seq,world));rest=m.number(params[3]) if params else None;hit=m.number(params[4]) if params else None
            result.append({'case':ident,'seq':seq,'sub':sub,'phase':phase,'color':color,'packet':packet,'lane':lane,'contactId':c[0],'point':point,
                           'observed_at':'postStore; deltas unchanged since final Relax',
                           'H':{'separation':f'{m.bits(separation):08x}','relativeVelocity':f'{m.bits(relative):08x}',
                                'totalNormalImpulse':f'{m.bits(total):08x}'},
                           's_gt_zero':separation>0,'total_gt_zero':total>0,
                           'restitution_skip_velocity':None if rest is None else relative>-rest,
                           'wide_restitution_skip_velocity':None if rest is None else m.add(relative,rest)>0,
                           'hit_speed_gt_threshold':None if hit is None else -relative>hit})
    return result


def frozen_table(root,results=()):
    root=Path(root);manifest=native.recipes();receipts={r['name']:r for r in results}
    applicability={r['name']:r for r in native.applicability(root,manifest)}
    rows=[]
    for recipe in manifest['native_mutations']:
        probe=recipe['probe'];witness=None
        if probe=='reader-boundary':witness={'profile':'fatal-boundary','id':recipe['error']}
        elif probe=='guard-helper':witness={'profile':'GUARD10','id':recipe['guard_group']}
        elif probe=='inherited-guard':witness={'profile':'native fixture of actual inherited helper','id':recipe['legacy_recipe']}
        elif probe=='float-helper':witness={'profile':'COMPONENT10','id':1,'helperKind':recipe['helper_kind']}
        elif probe=='component':witness={'profile':'COMPONENT10','id':6*(recipe['component_fixture']-1)+4}
        else:
            ident,operations=w.operations_for(recipe);witness={'profile':'PUBLIC10 short native witness','id':ident,'operations':len(operations)}
        actual=receipts.get(recipe['name'],{});killed=bool(actual.get('detected') and actual.get('clean') and actual.get('replayed_before_compaction'))
        rows.append({'name':recipe['name'],'class_id':recipe.get('class_id'),'guards':recipe['guards'],
                     'port':recipe['source']+':'+str(recipe['port_line']),'scope':recipe['scope'],
                     'original':recipe['original_anchor'],'predicate_or_assignment':recipe['expression'],
                     'replacement':recipe['replacement'],'witness':witness,
                     'single_hit':applicability[recipe['name']]['single_hit'],
                     'native_status':'WYKRYTY NATYWNIE' if killed else 'GAP — UNMEASURED / MISSING CLEAN WITNESS',
                     'first_difference':actual.get('difference'),'actual_predicates':actual.get('predicate_receipts',[])})
    proof_source=root/'silnik/fizyka/gra.dk';proof_lines={}
    if proof_source.is_file():
        text=proof_source.read_text(encoding='utf-8')
        try:
            lo,hi=native.base.function_span(text,'validStepParameters');body=text[lo:hi]
            for key,literal in (('R-SP-FIN-DT','not finite(parameters.dt)'),('R-SP-NEG-DT','parameters.dt < 0.0f32'),
                                ('R-SP-POS-H','h > 0.0f32'),('R-SP-FIN-INV-DT','finite(inv_dt)'),('R-SP-FIN-H','finite(h)')):
                proof_lines[key]=text[:lo+body.index(literal)].count('\n')+1
        except ValueError:pass
    equivalent=[{**p,'current_scope':'silnik/fizyka/gra.dk:'+str(proof_lines.get(p['id'])),'native_status':'EQUIVALENT — dowód',
                 'witness':None,'counted_as_killed':False} for p in manifest['equivalent_proofs']]
    approved=[]
    for recipe in native.approved_replacements():
        match=native.applicability(root,{'native_mutations':[recipe]})[0]
        actual=receipts.get(recipe['name'],{})
        killed=bool(actual.get('detected') and actual.get('clean') and actual.get('replayed_before_compaction'))
        approved.append({'approval':recipe['solver_replacement'],'recipe':recipe['name'],'source':recipe['source'],
                         'scope':recipe['scope'],'expression':recipe['expression'],'replacement':recipe['replacement'],
                         'witness':'GUARD10 '+recipe['guard_group'],'single_hit':match['single_hit'],
                         'native_status':'WYKRYTY NATYWNIE' if killed else 'UNMEASURED; requires clean native successor receipt',
                         'first_difference':actual.get('difference')})
    return {'contract':'KONTRAKT-10/1','branches':rows,'equivalent':equivalent,
            'approved_replacements':approved,
            'input_predicates':json.loads(json.dumps(m.predicate_receipts())),'unresolved_recipes':manifest['unresolved_recipes'],
            'native_gaps':[r['name'] for r in rows if r['native_status']!='WYKRYTY NATYWNIE'],
            'source_gaps':[r['name'] for r in rows if not r['single_hit']]}


def markdown(table):
    output=['# Krok10: E947578d56c3f → case → Ed0214da571af E6199aecf23ab E832171ed9e98','',
            'E44b375c2e947 case Ecd5b158f21b7 E35e99f929e01 Ecca454ddcbde E33d277cf0ef5. Ef984d2ca7f1c z GAP E0f9e3d218af1 Ebae10bcdb3da Eddc1b687a5c2. Ec56152fce412 E1a1d2e5d3ecb E52b3d71a10fe Ea277b9950b3a E9564626bc31b Ebc024cfa6e2b Ea3ad92305e5c.','',
            '| Przepis / klasa / osłona | Port ↔ oryginał | Przypadek | Różnica / stan |',
            '|---|---|---|---|']
    for row in table['branches']:
        name=row['name']+' / '+str(row['class_id'] or ','.join(row['guards']) or 'fatal')
        where=row['port']+' ('+row['scope']+') ↔ '+row['original']
        witness=json.dumps(row['witness'],ensure_ascii=False,separators=(',',':'))
        difference=json.dumps(row['first_difference'],ensure_ascii=False,separators=(',',':')) if row['first_difference'] else row['native_status']
        output.append('| '+' | '.join(x.replace('|','\\|').replace('\n',' ') for x in (name,where,witness,difference))+' |')
    output += ['','## EQUIVALENT — dowód','']
    for proof in table['equivalent']:output += [f'- {proof['id']}, {proof['current_scope']}: {proof['dowod']} E5dc1c90633c4 Eaea440a813f6; Ecd5b158f21b7 E7592e8788246 E2ffe317df468 E3b3124f0cfd0 E137b58a5a3c1.']
    output+=['','## E7a09c51a5e35 Ea330395cc0a5 — W3','']
    for item in table['approved_replacements']:
        output.append(f'- {item['approval']}: {item['source']} / {item['scope']}; {item['recipe']}; {item['witness']}; E9f41e319c72c Ea238c6659de1 Eff651d1fb71c={item['single_hit']}; {item['native_status']}.')
    output += ['','## Predykaty f32 i bloki','', '```json',json.dumps(table['input_predicates'],ensure_ascii=False,indent=2),'```','',
               f'Luki natywne: {len(table['native_gaps'])}. E767b84493ea2 Ead856bcaa151 E1729fd361334: {len(table['source_gaps'])}.','']
    return '\n'.join(output)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    table=frozen_table(args.root)
    (HERE/'solver-galezie.json').write_text(json.dumps(table,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'SOLVER-GALEZIE.md').write_text(markdown(table),encoding='utf-8')
