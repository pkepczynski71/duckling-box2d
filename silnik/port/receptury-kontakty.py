pass                                                                         

                                                                              
   
import json
from pathlib import Path
import re
import sys
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
spec=spec_from_file_location('contact_recipe_scopes',HERE/'mutacje-ruch-swiata.py');base=module_from_spec(spec);spec.loader.exec_module(base)

def freeze(root):
    items=[]
    def save():
        manifest=json.loads((HERE/'kontakty-przypadki.json').read_bytes())
        result={'contract':'KONTRAKT-9B/1','status':'NATIVE_EXECUTION_REQUIRED','recipe_count':len(items),'class_count':40,'guard_groups':34,'fatal_kinds':29,
            'native_mutations':items,'unresolved_classes':[{'class_id':'M12','status':'ZAMKNIETE_W_KROKU_11','decision':'D11-3','native_recipe':'M12-LINK-REF','native_receipt_required':True}],
            'test_modules':{p:sorted(f.name for f in HERE.glob(p)) for p in ('test_kontakty*.py','test_pary*.py')},
            'required_class_ids':[f'M{i:02}' for i in range(1,41)],'required_guard_ids':[x['id'] for x in manifest['oslony']]}
        (HERE/'mutacje-kontakty.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def add(cls,scope,old,new,witness,tags,source='swiat',suffix='',guards=(),fixture=None,prefix=None,fields=None):
        path='silnik/fizyka/'+source+'.dk';text=(root/path).read_text(encoding='utf-8');name=cls.lower()+'-'+scope+suffix
        row={'name':name,'class_id':cls if cls.startswith('M') else None,'guards':list(guards or ([cls] if cls.startswith('G-') else [])),
             'probe':'product','source':path,'scope':scope,'expression':old,'replacement':new,'witness_id':witness,'expected_tags':tags,
             'port_line':text[:text.index('fun '+scope+'(')].count('\n')+1}
        if fixture:row['fixture']=fixture
        if prefix:row['prefix_operations']=prefix
        if fields is not None:row['expected_fields']=fields
        base.apply(text,row);items.append(row);save()
    def S(*a,**k):return add(*a,**k)
    def G(*a,**k):return add(*a,source='gra',**k)
    S('M01','b2UpdateContact','contactManifold(entry.kind, a, xfA, b, xfB)','contactManifold(0i32, a, xfA, b, xfB)',6,['CS','GV'])
    S('M02','b2CreateContact','let a: i32 = if entry.primary then inputA else inputB;\n    let b: i32 = if entry.primary then inputB else inputA;','let a: i32 = inputA;\n    let b: i32 = inputB;',6,['RQ','CT','CS'])
    S('M03','b2CreateContact','if (entry.kind == -1i32) return -1i32;','if (false) return -1i32;',48,['RQ','CP','CT'])
    S('M04','b2CreateContact','    return id;','    emitContactBegin(world, a, b, Manifold());\n    return id;',5,['EB','GE'])
    S('M05','b2CollideTask','let touching: bool = b2UpdateContact(world, sim, a, xfA, offsetA, b, xfB, offsetB);','let touching: bool = b2UpdateContact(world, sim, a, xfA, offsetA, b, xfB, offsetB);\n    if (not touching) { sim.simFlags = sim.simFlags | 131072u32; bits.b2SetBit(&world.contactStateBitSet, sim.contactId); }',11,['CP','CT'])
    S('M06','b2DestroyContact','b2RemoveKey(&world.broadPhase.pairSet, B2_SHAPE_PAIR_KEY(record.shapeIdA, record.shapeIdB));','# omitted by native mutation',25,['H'])
    for side,cls in ((0,'M07'),(1,'M08')):
        old='if (edge.nextKey != -1i32) contactEdge(world.contacts.at((edge.nextKey >> 1i32) as i64), edge.nextKey & 1i32).prevKey = edge.prevKey;'
        S(cls,'b2DestroyContact',old,old.replace('if (','if (side != '+str(side)+'i32 and ',1),25+side,['CT'])
        old='if (edge.prevKey != -1i32) contactEdge(world.contacts.at((edge.prevKey >> 1i32) as i64), edge.prevKey & 1i32).nextKey = edge.nextKey;'
        S(cls,'b2DestroyContact',old,old.replace('if (','if (side != '+str(side)+'i32 and ',1),25+side,['CT'],suffix='-prev-next')
    for cls,fn,wit in (('M09','b2RemoveNonTouchingContact',25),('M10','b2RemoveContactFromGraph',29)):
        S(cls,fn,'world.contacts.at(moved.contactId as i64).localIndex = local;','# omitted by native mutation',wit,['CT'],fields=[4])
    source=(root/'silnik/fizyka/swiat.dk').read_text(encoding='utf-8');lo,hi=base.function_span(source,'b2CollideChanges');block=source[lo:hi]
    old='var id: i32 = 0i32;\n    while (id < world.contactIdPool.nextIndex) {'
    dense='''var order: List[i32]; var color: i32 = 0i32;
    while (color < 12i32) { var c: i32 = 0i32; while (c < world.constraintGraph.colors[color].contactCount) { order.push(world.constraintGraph.colors[color].contactSims.at(c as i64).contactId); c = c + 1i32; } color = color + 1i32; }
    var n: i32 = 0i32; while (n < b2GetSolverSet(world, 2i32).contactCount) { order.push(b2GetSolverSet(world, 2i32).contactSims.at(n as i64).contactId); n = n + 1i32; }
    var ordinal: i64 = 0i64;
    while (ordinal < order.length()) { let id: i32 = order.at(ordinal);'''
    S('M11','b2CollideChanges',block,block.replace(old,dense).replace('id = id + 1i32;','ordinal = ordinal + 1i64;'),49,['EB','EE0','EE1','CS','CT'])
                                                                             
                                                                               
                                                                       
    S('M13','b2UpdateContact','if (previous.id == point.id)','if (j == i)',21,['CS','GV'])
    S('M13','b2UpdateContact','while (j < old.pointCount and not found)','while (j < old.pointCount)',24,['CS','GV'],suffix='-last-id')
    S('M14','b2UpdateContact','        i = i + 1i32;','        if (not found) { point.normalImpulse = old.point0.normalImpulse; point.tangentImpulse = old.point0.tangentImpulse; }\n        i = i + 1i32;',23,['CS','GV'])
    for cls,field in (('M15','totalNormalImpulse'),('M16','normalVelocity')):
        S(cls,'b2UpdateContact',f'point.{field} = 0.0f32;',f'point.{field} = old.point0.{field};',21,['CS','GV'])
    S('M17','b2UpdateContact','point.persisted = false;','point.persisted = true;',23,['CS','GV'])
    S('M18','b2UpdateContact','if (count > 0i32) sim.manifold.rollingImpulse = old.rollingImpulse;','if (count > 0i32) sim.manifold.rollingImpulse = 0.0f32;',23,['CS','GV'])
    S('M19','b2UpdateContact','var old: Manifold = sim.manifold;','var old: Manifold = sim.manifold; sim.cache = distance.SimplexCache();',23,['CS','GV'])
    S('HIT','b2UpdateContact','if (touching and (a.enableHitEvents or b.enableHitEvents))','if (false)',1,['CS'],suffix='-set',fixture='raw-hit-cycle',fields=[13])
    S('HIT','b2UpdateContact','else sim.simFlags = sim.simFlags & (4294967295u32 ^ 1048576u32);','else sim.simFlags = sim.simFlags;',1,['CS'],suffix='-clear',fixture='raw-hit-cycle',fields=[13])
    for side in ('A','B'):
        for suffix,expr in (('local',f'bodySim{side}.localCenter'),('position',f'xf{side}.p'),('zero','Vec2()')):
            S('M20','b2CollideTask',f'b2RotateVector(xf{side}.q, bodySim{side}.localCenter)',expr,17,['CS','GV'],suffix='-'+side+'-'+suffix)
    for field,expr in (('friction','math.sqrt(a.friction * b.friction)'),('restitution','tree.b2MaxFloat(a.restitution, b.restitution)'),('tangentSpeed','a.tangentSpeed + b.tangentSpeed')):
        S('M21','b2UpdateContact',f'sim.{field} = {expr};',f'sim.{field} = sim.{field};',17,['CS'],suffix='-'+field)
    S('M21','b2UpdateContact','sim.rollingResistance = tree.b2MaxFloat(a.rollingResistance, b.rollingResistance) * maxRadius;','sim.rollingResistance = sim.rollingResistance;',18,['CS'],suffix='-rolling-positive')
    S('M21','b2UpdateContact','else sim.rollingResistance = 0.0f32;','else sim.rollingResistance = sim.rollingResistance;',19,['CS'],suffix='-rolling-zero')
    for shape_type,field,fixture in ((0,'circle','registry-0-0'),(1,'capsule','registry-1-1'),(3,'polygon','registry-3-3')):
        S('M21','b2GetShapeRadius',f'return shape.{field}.radius;','return 0.0f32;',1,['CS'],suffix='-radius-'+field,fixture=fixture,fields=[11])
    S('M21','b2GetShapeRadius','return 0.0f32;','return 1.0f32;',1,['CS'],suffix='-radius-segment',fixture='registry-2-0',fields=[11])
    S('M21','b2UpdateContact','if (not world.enableSpeculative and count == 2i32)','if (false)',1,['TASK','CS','GV'],suffix='-speculative-false',fixture='speculative-false-1007908028')
    start='var i: i32 = if staticA or staticB then 1i32 else 0i32;'
    S('M22','b2AddContactToGraph',start,'var i: i32 = 0i32;',37,['CT','GB'])
    S('M23','b2AddContactToGraph','if (not staticA) bits.b2SetBitGrow(&color.bodySet, a.id);','bits.b2SetBitGrow(&color.bodySet, a.id);',38,['GB'])
    S('M24','b2AddContactToGraph','let staticA: bool = a.setIndex == 0i32;','let staticA: bool = a.setIndex == 0i32 or a.bodyType == 1i32;',46,['CT','GB'])
    S('M25','b2AddContactToGraph','let local: i32 = world.constraintGraph.colors[selected].contactCount;','if (selected == 11i32) return;\n    let local: i32 = world.constraintGraph.colors[selected].contactCount;',37,['CA','CT','CS'])
    S('M26','b2AddContactToGraph',start,'var i: i32 = 11i32;',41,['CA','CT','GB'])
    S('M27','b2RemoveContactFromGraph','if (colorIndex != 11i32) { bits.b2ClearBit(&color.bodySet, a); bits.b2ClearBit(&color.bodySet, b); }','if (false) { bits.b2ClearBit(&color.bodySet, a); bits.b2ClearBit(&color.bodySet, b); }',31,['GB','CT'])
    for w in (39,42):S('M28','b2RemoveContactFromGraph','world.contacts.at(moved.contactId as i64).localIndex = local;','if (colorIndex != 11i32) world.contacts.at(moved.contactId as i64).localIndex = local;',w,['CT'],suffix='-'+str(w),fields=[4])
    S('M29','b2LinkContact','world.islands.at(rootB as i64).parentIsland = rootA;','world.islands.at(rootA as i64).parentIsland = rootB;',33,['IS','IL'])
    S('M30','contactIslandRoot','if (grand != -1i32) world.islands.at(id as i64).parentIsland = grand;','if (false) world.islands.at(id as i64).parentIsland = grand;',33,['IS'])
    S('M31','b2UnlinkContact','island.constraintRemoveCount = island.constraintRemoveCount + 1i32;','island.constraintRemoveCount = island.constraintRemoveCount;',35,['IS'])
    lo,hi=base.function_span(source,'b2MergeAwakeIslands');block=source[lo:hi]
    S('M32','b2MergeAwakeIslands',block,block.replace('var j: i32 = count - 1i32;','var j: i32 = 0i32;').replace('while (j >= 0i32)','while (j < b2GetSolverSet(world, 2i32).islandCount)').replace('j = j - 1i32;','j = j + 1i32;'),33,['IS','IL','IF'])
    for field,var in (('bodies','body'),('contacts','contact')):S('M33','b2MergeIsland',f'world.{field}.at({var} as i64).islandId = root;','# omitted by native mutation',33,['BL9','CT'],suffix='-'+field,prefix=50)
    S('M34','b2DestroyIsland','world.islands.at(movedId as i64).localIndex = local;','# omitted by native mutation',33,['GUARD9'],prefix=50)
    items[-1]['island_boundary']=True
    S('M35','b2RemoveBodyFromIsland','world.bodies.at(id as i64).islandId = -1i32;','if (island.bodyCount > 0i32) b2DestroyIsland(world, body.islandId);\n    world.bodies.at(id as i64).islandId = -1i32;',54,['IP','IS','IL'],prefix=28)
    S('M36','b2DestroyShapeContacts','if (record.shapeIdA == shapeId or record.shapeIdB == shapeId)','if (true)',53,['CP','CT','GE'])
    S('M37','b2GetContactEndEvents','if (world.endEventArrayIndex == 0i32)','if (world.endEventArrayIndex != 0i32)',61,['GE','GC'],guards=['G-END-SIDE'])
    G('M38','cloneContactEvents','    return result;','    if (source.begin.length() > 0i64) source.begin.at(0i64).shapeA.birthTicket.low = source.begin.at(0i64).shapeA.birthTicket.low ^ 1u32;\n    return result;',62,['GC'],guards=['G-COPY-EVENTS'])
    G('M39','copyContactEvents','ended.birthA, ended.ownerTicket','world.shapes.at((ended.shapeA.index1 - 1i32) as i64).birthTicket, ended.ownerTicket',61,['GE','GC'],guards=['G-EVENT-NUMBER'])
    items[-1]['witness_variant']='recreate-A'
    G('M40','cloneContactEvents','result.begin.push(begin);','var late: ContactBegin = begin; let now: ContactLookup = findContact(WorldNumber(0i32, begin.shapeA.ownerTicket), begin.shapeA, begin.shapeB); if (now.status == OK and now.has) late.manifold = now.value.manifold; result.begin.push(late);',63,['GC'],guards=['G-EVENT-MANIFOLD'])
    for cls,old,new,fixture in (
        ('G-W47','if (worldStatus(owner) != OK) return STALE;','if (false) return STALE;','guard-world'),
        ('G-OWNER47','if (not equalKey(owner.birthTicket, number.ownerTicket)) return FOREIGN;','if (false) return FOREIGN;','guard-owner'),
        ('G-RANGE','if (number.slot < 0i32 or number.slot >= world.contactIdPool.nextIndex) return STALE;','if (false) return STALE;','guard-range'),
        ('G-OCCUPIED','if (record.setIndex == -1i32 or record.contactId == -1i32) return STALE;','if (false) return STALE;','guard-occupied'),
        ('G-BIRTH-LOW','if (not equalKey(record.birthTicket, number.birthTicket)) return STALE;','if (record.birthTicket.high != number.birthTicket.high) return STALE;','guard-birth-low'),
        ('G-BIRTH-HIGH','if (not equalKey(record.birthTicket, number.birthTicket)) return STALE;','if (record.birthTicket.low != number.birthTicket.low) return STALE;','guard-birth-high'),
        ('G-CONTACT-ID','if (record.contactId != number.slot) return STALE;','if (false) return STALE;','guard-contact-id')):
        G(cls,'contactStatus',old,new,1,[],fixture=fixture)
    G('G-W48','bodyStatus','if (worldStatus(owner) != OK) return STALE;','if (false) return STALE;',57,['R','GL'])
    G('G-OWNER48','bodyStatus','if (not equalKey(owner.birthTicket, number.ownerTicket)) return FOREIGN;','if (false) return FOREIGN;',58,['R','GL'])
    G('G-W49','copyContactEvents','result.status = worldStatus(owner);','result.status = OK;',57,['R','GE','GC'])
    G('G-CARRY','nextTicket','return Key64(0u32, last.high + 1u32);','return Key64(0u32, last.high);',1,['CT','Z9'],fixture='carry-low')
    G('G-MAX-READ','lookupContact','result.status = contactStatus(owner, number);','result.status = contactStatus(owner, number); if (ticketLimit(lastIssued)) result.status = LIMIT;',1,['RC9','GV'],fixture='max-reads')
    G('G-MAX-READ','contacts','result.status = bodyStatus(owner, number);','result.status = bodyStatus(owner, number); if (ticketLimit(lastIssued)) result.status = LIMIT;',1,['R','GL'],fixture='max-reads')
    G('G-MAX-READ','copyContactEvents','result.status = worldStatus(owner);','result.status = worldStatus(owner); if (ticketLimit(lastIssued)) result.status = LIMIT;',1,['R','GE','GC'],fixture='max-reads')
    G('G-MAX-READ','updateContactPairs','result.status = worldStatus(owner);','result.status = worldStatus(owner); if (ticketLimit(lastIssued)) result.status = LIMIT;',1,['R','RQ','CP','Z9'],fixture='max-empty-pairs')
    G('G-LEGACY-LIMIT','createShapeRaw','if (ticketLimit(lastIssued))','if (false)',1,['R','S','Z9'],fixture='shape-at-max')
    G('G-COPY-LOOKUP','lookupContact','    return result;','    raw.b2GetContactSim(world, world.contacts.at(number.slot as i64)).manifold.normal.x = -result.value.manifold.normal.x;\n    return result;',32,['GV','CD'])
    G('G-COPY-LIST','contacts','result.values.push(found.value);','result.values.push(found.value); raw.b2GetContactSim(world, world.contacts.at(id as i64)).manifold.normal.x = -found.value.manifold.normal.x;',32,['GL','CD'])
    G('G-READ-PURE','copyContactEvents','    return result;','    world.contactBeginEvents.clear();\n    return result;',64,['GE','GC','EB'])
    for suffix,replacement in (('', 'prepared.requests.length() != 0i64'),('-negative','prepared.requests.length() != 0i64 or (dt > 0.0f32 and firstContact != -1i32)')):
        S('G-STEP','b2World_Step','if (prepared.requests.length() != 0i64 or firstContact != -1i32)','if ('+replacement+')',60,['R','K','UP'],suffix=suffix)
    for guard,field,part in (('G-MAT-F-FIN','friction','finite(shape.friction)'),('G-MAT-F-NONNEG','friction','shape.friction >= 0.0f32'),('G-MAT-R-FIN','restitution','finite(shape.restitution)'),('G-MAT-R-NONNEG','restitution','shape.restitution >= 0.0f32'),('G-MAT-ROLL-FIN','rollingResistance','finite(shape.rollingResistance)'),('G-MAT-ROLL-NONNEG','rollingResistance','shape.rollingResistance >= 0.0f32'),('G-MAT-T-FIN','tangentSpeed','finite(shape.tangentSpeed)')):
        G(guard,'validContactMaterial',part,'true',1,['R','S'],fixture='material40-0' if field!='tangentSpeed' else 'material40-1')
        if field!='tangentSpeed':items[-1]['fixture_prefix_operations']={('friction',True):4,('friction',False):6,('restitution',True):8,('restitution',False):10,('rollingResistance',True):12,('rollingResistance',False):14}[field,guard.endswith('FIN')]
    G('G-BATCH','updateContactPairs','if (ticketLimit(reserved))','if (ticketLimit(lastIssued))',1,['R','CP','CT','H','Z9'],fixture='batch-one-left')
    game_units(root,items,G);reader_recipes(root,items)
    bitset_recipes(root,items)
                                                                                
                                                                     
    for row in items:
        if row.get('replacement')=='# omitted by native mutation':row['replacement']='if (false) { '+row['expression']+' }'
        text=(root/row['source']).read_text(encoding='utf-8')
        lo,hi=base.function_span(text,row['scope'])
        where=text.find(row.get('expression',row.get('guard_statement','')),lo,hi)
        row['port_line']=text[:where if where>=0 else lo].count('\n')+1
        comments=[x.strip('# ') for x in text[max(0,lo-800):lo].splitlines() if 'Box2D' in x]
        row['original_anchor']=comments[-1] if comments else 'Game/transport guard: KONTRAKT-9B sections 4/8/9.1'
        if row['name'].endswith('-prev-next'):
            row['original_anchor']='Box2D 8c661469, src/contact.c:'+('368-372 (A)' if row['class_id']=='M07' else '393-397 (B)')
        if row['name'].startswith('hit-'):
            row['original_anchor']='Box2D 8c661469, src/contact.c:'+('535-537' if row['name'].endswith('-set') else '539-541')
        if row['name']=='material-route-createBodyWithBox':row['original_anchor']='Game guard: KONTRAKT-9B:1145; opcode16/tag4 -> createBodyWithBox'
    save();return items

def bitset_recipes(root,items):
    text=(root/'silnik/fizyka/bitset.dk').read_text(encoding='utf-8')
    def add(name,scope,old,new):
        row={'name':'bitset-'+name,'probe':'bitset-helper','class_id':None,'guards':[],
             'source':'silnik/fizyka/bitset.dk','scope':scope,'expression':old,'replacement':new,
             'witness_id':1,'fixture':'bitset-branches','expected_tags':['BIT9']}
        base.apply(text,row);items.append(row)
    for index in (31,32,63,64,127,128):
        add('index-'+str(index),'b2SetBit','    let blk:',f'    if (index == {index}i32) return;\n    let blk:')
    for side in ('low','high'):
        add('union-'+side,'b2InPlaceUnion',f'a.bits.at(i as i64).{side} = a.bits.at(i as i64).{side} | b.bits.at(i as i64).{side};','# omitted by native mutation')
        add('clear-'+side,'b2ClearBit',f'set.bits.at(blk).{side} & mask',f'set.bits.at(blk).{side}')
    add('clear-bounds','b2ClearBit','if (index / 64i32 >= set.blockCount) return;','# omitted by native mutation')
    add('get-bounds','b2GetBit','if (index / 64i32 >= set.blockCount) return false;','# omitted by native mutation')
    add('clear-count','b2SetBitCountAndClear','set.bits.at(i as i64) = Key64();','# omitted by native mutation')
    add('grow-capacity','b2GrowBitSet','let capacity: i32 = blockCount + blockCount / 2i32;','let capacity: i32 = blockCount + blockCount;')

def game_units(root,items,G):
    source=(root/'silnik/fizyka/gra.dk').read_text(encoding='utf-8')
    def edit(scope,old,new,name):
        row={'name':name,'scope':scope,'expression':old,'replacement':new};base.apply(source,row);return row
    sentinel=edit('addPreparedShape','return createShapeRaw(owner, parent, checked, true, invoke);','result.status = PARAM; return result;','unit-return-before-allocation')
    disable_s12=edit('addPreparedShape','not preflight(owner, parent.slot, 0i32, -1i32, checked, 0.0f32)','false','isolate-geometry-from-mass')
    def unit(name,guard,scope,old,new,seed,geometry='circle',edits=(),baseline=4,parent=None):
        row={'name':name,'class_id':None,'guards':[guard],'probe':'game-boundary','source':'silnik/fizyka/gra.dk','scope':scope,'expression':old,'replacement':new,
             'witness_id':1,'expected_tags':['R'],'geometry':geometry,'specimen_seed':seed,'fixture_edits':[sentinel,*edits],
             'baseline_status':baseline,'seed_description':'Isolated input of the real helper; boundary returns PARAM5 after the tested guard; no allocation.',
             'port_line':source[:source.index('fun '+scope+'(')].count('\n')+1}
        if parent:row['parent_expression']=parent
        text=source
        for change in row['fixture_edits']:text=base.apply(text,change)
        base.apply(text,row);items.append(row)
                                                                                       
    status_guard='if (result.status != OK) return result;'
    observe=edit('addPreparedShape',status_guard,status_guard+'\n    if (result.status != OK) { result.status = PARAM; return result; }','observe-status-guard')
    for name,guard,field in (('life','G-LEGACY-LIFE','birthTicket'),('owner','G-LEGACY-OWNER','ownerTicket')):
        parent=f'game.BodyNumber(reg.bodies[op.c].number.slot, '+('words64.Key64(reg.bodies[op.c].number.birthTicket.low ^ 1u32, reg.bodies[op.c].number.birthTicket.high)' if field=='birthTicket' else 'reg.bodies[op.c].number.birthTicket')+', '+('words64.Key64(reg.bodies[op.c].number.ownerTicket.low ^ 1u32, reg.bodies[op.c].number.ownerTicket.high)' if field=='ownerTicket' else 'reg.bodies[op.c].number.ownerTicket')+')'
        unit('route40-'+name,guard,'addPreparedShape',status_guard,'if (false) return result;','',edits=(observe,),baseline=1 if field=='birthTicket' else 2,parent=parent)
    lo,hi=base.function_span(source,'validShapeGeometry');block=source[lo:hi]
    def statement(part):
        candidates=[s for c,s in if_sites(block) if part in c and 'return false' in s]
        if len(candidates)!=1:raise ValueError(('geometry guard',part,len(candidates)))
        return candidates[0]
                                                                            
                                                                                
    inf='3.0e38f32 * 3.0e38f32'
    predicates=[
      ('density-finite','finite(shape.density)',f'specimen.density = {inf};','circle'),
      ('density-sign','shape.density < 0.0f32','specimen.density = -1.0f32;','circle'),
      ('circle-center','finiteVector(shape.circle.center)',f'specimen.circle.center.x = {inf};','circle'),
      ('circle-radius-finite','finite(shape.circle.radius)',f'specimen.circle.radius = {inf};','circle'),
      ('circle-radius-positive','shape.circle.radius > 0.0f32','specimen.circle.radius = 0.0f32;','circle'),
      ('capsule-end1','finiteVector(shape.capsule.center1)',f'specimen.capsule.center1.x = {inf};','capsule'),
      ('capsule-end2','finiteVector(shape.capsule.center2)',f'specimen.capsule.center2.y = {inf};','capsule'),
      ('capsule-radius-finite','finite(shape.capsule.radius)',f'specimen.capsule.radius = {inf};','capsule'),
      ('capsule-radius-positive','shape.capsule.radius > 0.0f32','specimen.capsule.radius = 0.0f32;','capsule'),
      ('capsule-length','finite(capsuleLength)','specimen.capsule.center1.x = -1.0e20f32; specimen.capsule.center2.x = 1.0e20f32;','capsule'),
      ('segment-end1','finiteVector(shape.segment.point1)',f'specimen.segment.point1.x = {inf};','segment'),
      ('segment-end2','finiteVector(shape.segment.point2)',f'specimen.segment.point2.y = {inf};','segment'),
      ('segment-length-finite','finite(segmentLength)','specimen.segment.point1.x = -1.0e20f32; specimen.segment.point2.x = 1.0e20f32;','segment'),
      ('segment-length-min','segmentLength > B2_LINEAR_SLOP * B2_LINEAR_SLOP','specimen.segment.point2 = specimen.segment.point1;','segment'),
      ('polygon-type','shape.shapeType != 3i32','specimen.shapeType = 4i32;','polygon'),
      ('polygon-count-min','shape.polygon.count < 3i32','specimen.polygon.count = 2i32;','polygon'),
      ('polygon-count-max','shape.polygon.count > 8i32','specimen.polygon.count = 9i32;','polygon'),
      ('polygon-radius-finite','finite(shape.polygon.radius)',f'specimen.polygon.radius = {inf};','polygon'),
      ('polygon-radius-sign','shape.polygon.radius < 0.0f32','specimen.polygon.radius = -1.0f32;','polygon'),
      ('polygon-centroid','finiteVector(shape.polygon.centroid)',f'specimen.polygon.centroid.x = {inf};','polygon'),
      ('polygon-vertex','finiteVector(shape.polygon.vertices[i])',f'specimen.polygon.vertices[0].x = {inf};','polygon'),
      ('polygon-normal','finiteVector(shape.polygon.normals[i])',f'specimen.polygon.normals[0].y = {inf};','polygon')]
    for name,part,seed,geometry in predicates:
        clauses=[disable_s12]
        if name.startswith('capsule-end'):clauses.append(edit('validShapeGeometry','finite(capsuleLength)','true','isolate-capsule-end'))
        if name.startswith('segment-end'):clauses.append(edit('validShapeGeometry','finite(segmentLength)','true','isolate-segment-end'))
                                                                                
        if part in ('finiteVector(shape.circle.center)','finite(shape.circle.radius)','shape.circle.radius > 0.0f32'):
            old=next(line.strip() for line in block.splitlines() if line.strip().startswith('if (shape.shapeType == 0i32)'))
        elif part.startswith('finiteVector(shape.capsule') or part in ('finite(shape.capsule.radius)','shape.capsule.radius > 0.0f32','finite(capsuleLength)'):
            start=block.index('return finiteVector(shape.capsule');end=block.index(';',start)+1;old=block[start:end]
        elif part.startswith('finiteVector(shape.segment') or part.startswith('finite(segmentLength)') or part.startswith('segmentLength >'):
            start=block.index('return finiteVector(shape.segment');end=block.index(';',start)+1;old=block[start:end]
        else:old=statement(part)
        if name=='polygon-count-max':
            clauses.append(edit('validShapeGeometry',old,old+'\n    if (shape.polygon.count > 8i32) return true;','bounded-polygon-unit'))
        if name.startswith('capsule-end'):old=old.replace('finite(capsuleLength)','true')
        if name.startswith('segment-end'):old=old.replace('finite(segmentLength)','true')
        new=old.replace(part,'false' if part in ('shape.density < 0.0f32','shape.shapeType != 3i32','shape.polygon.count < 3i32','shape.polygon.count > 8i32','shape.polygon.radius < 0.0f32') else 'true',1)
        unit('geometry-'+name,'G-LEGACY-GEOMETRY','validShapeGeometry',old,new,seed,geometry,clauses)
    for axis in ('x','y'):
        unit('geometry-vector-'+axis,'G-LEGACY-GEOMETRY','finiteVector',f'finite(value.{axis})','true',f'specimen.circle.center.{axis} = {inf};',edits=(disable_s12,))
                                                                             
                                                                               
    fields=('mass','inertia','originInertia','sim.invMass','sim.invInertia','sim.localCenter','sim.center','state.linearVelocity','state.angularVelocity','sim.minExtent','sim.maxExtent')
    for field in fields:
        vector=field in ('sim.localCenter','sim.center','state.linearVelocity')
        for axis in (('x','y') if vector else ('',)):
            part=('finiteVector' if vector else 'finite')+'(computed.'+field+')'
            lo,hi=base.function_span(source,'safeMass');mass=source[lo:hi]
            old=next(s for c,s in if_sites(mass) if part in c)
            start=mass.index('let computed: raw.BodyMassResult =');end=mass.index(';',start)+1;decl=mass[start:end]
            seeded=decl.replace('let computed:','var computed:')+f'\n    computed.{field}'+('.'+axis if axis else '')+f' = {inf};'
            fixture=edit('safeMass',decl,seeded,'seed-mass-input-'+field+axis)
            unit('mass-'+field.replace('.','-')+axis,'G-LEGACY-S12','safeMass',old,old.replace(part,'true',1),'',edits=(fixture,))
    lo,hi=base.function_span(source,'safeMass');mass=source[lo:hi]
    old=next(s for c,s in if_sites(mass) if 'computed.inertia <= 0.0f32' in c)
    start=mass.index('let computed: raw.BodyMassResult =');end=mass.index(';',start)+1;decl=mass[start:end]
    unit('mass-inertia-positive','G-LEGACY-S12','safeMass',old,old.replace('computed.inertia <= 0.0f32','false'),' ',edits=(edit('safeMass',decl,decl.replace('let computed:','var computed:')+'\n    computed.inertia = 0.0f32;','seed-inertia-zero'),))
                                                                             
    disable_geo=edit('addPreparedShape','not validShapeGeometry(&checked)','false','isolate-mass-geometry')
    for name,part,seed_decl,seed_code,extra in (
        ('shape-geometry','not validShapeGeometry(&shape)',None,'specimen.circle.radius = 0.0f32;',[disable_geo]),
        ('bounds-lower','not finiteVector(bounds.lowerBound)','bounds','bounds.lowerBound.x = '+inf+';',[]),
        ('bounds-upper','not finiteVector(bounds.upperBound)','bounds','bounds.upperBound.y = '+inf+';',[]),
        ('extent-min','not finite(extent.minExtent)','extent','extent.minExtent = '+inf+';',[]),
        ('extent-max','not finite(extent.maxExtent)','extent','extent.maxExtent = '+inf+';',[])):
        old=next(s for c,s in if_sites(mass) if part in c)
        clauses=list(extra)+[edit('safeMass',old,old+'\n        return true;','observe-mass-'+name)]
        if seed_decl:
            decl=next(line.strip() for line in mass.splitlines() if line.strip().startswith('let '+seed_decl+':'))
            clauses.append(edit('safeMass',decl,decl.replace('let '+seed_decl+':','var '+seed_decl+':')+'\n        '+seed_code,'seed-'+name))
        unit('mass-'+name,'G-LEGACY-S12','safeMass',old,old.replace(part,'false'),' ' if seed_decl else seed_code,edits=clauses)
                                                                              
                                                                              
    entries={
        'addPreparedShape':'game.addPreparedShape(reg.worlds[op.b].number, reg.bodies[op.c].number, specimen, op.invoke)',
        'addShape':'game.addShape(reg.worlds[op.b].number, reg.bodies[op.c].number, specimen, op.invoke)',
        'addBox':'game.addBox(reg.worlds[op.b].number, reg.bodies[op.c].number, boxGeometry, specimen, op.invoke)',
        'createBodyWithBox':'game.createBodyWithBox(reg.worlds[op.b].number, raw.BodyDef(), boxGeometry, specimen, op.invoke, false, words64.Key64())',
        'createBodyWithShape':'game.createBodyWithShape(reg.worlds[op.b].number, raw.BodyDef(), specimen, op.invoke, false, words64.Key64())',
        'createBodyWithPreparedShape':'game.createBodyWithPreparedShape(reg.worlds[op.b].number, raw.BodyDef(), specimen, op.invoke, false, words64.Key64())'}
    for scope,call in entries.items():
        lo,hi=base.function_span(source,scope);c,old=next((c,s) for c,s in if_sites(source[lo:hi]) if 'validContactMaterial(' in c)
        observer=edit(scope,old,old+'\n    if ('+c+') { result.status = GEOMETRY; return result; }','observe-material-'+scope)
                                                                     
        row={'name':'material-route-'+scope,'class_id':None,'guards':['G-MAT-ROUTES'],'probe':'game-boundary','source':'silnik/fizyka/gra.dk','scope':scope,
             'expression':old,'replacement':old.replace(c,'false',1),'fixture_edits':[observer],'specimen_seed':'specimen.friction = -1.0f32;',
             'geometry':'circle','entry_call':call,'baseline_status':5,'mutant_status':4,'witness_id':1,'expected_tags':['R'],
             'seed_description':'Invalid material to real constructor; stop after its own guard before redundant next stage.',
             'port_line':source[:source.index('fun '+scope+'(')].count('\n')+1}
        if scope.startswith('createBody'):row['result_type']='game.PairResult'
        if scope=='createBodyWithBox':
                                                                            
                                                                             
                                                                       
            row['fixture_edits']=[]
            row['specimen_seed']='specimen.friction = -1.0f32; boxGeometry.halfWidth = 0.0f32;'
            row['seed_description']='KONTRAKT-9B:1145; invalid material plus invalid box: PARAM before GEOMETRY, no allocation.'
        text=base.apply(source,observer);base.apply(text,row);items.append(row)
    boolean_units(root,items,edit)

def boolean_units(root,items,edit):
    source=(root/'silnik/fizyka/gra.dk').read_text(encoding='utf-8');inf='3.0e38f32 * 3.0e38f32'
    def add(name,scope,part,seed,call,extra=(),false_clause=False):
        lo,hi=base.function_span(source,scope);block=source[lo:hi]
        if block.count(part)!=1:raise ValueError((scope,part,block.count(part)))
        row={'name':name,'class_id':None,'guards':['G-LEGACY-GEOMETRY'],'probe':'game-boundary','source':'silnik/fizyka/gra.dk','scope':scope,
             'expression':part,'replacement':'false' if false_clause else 'true','fixture_edits':list(extra),'specimen_seed':seed,'boolean_call':call,
             'geometry':'polygon','baseline_status':4,'witness_id':1,'expected_tags':['R'],'seed_description':'Native Boolean helper, controlled input, no shape allocation.',
             'port_line':source[:source.index('fun '+scope+'(')].count('\n')+1}
        text=source
        for e in extra:text=base.apply(text,e)
        base.apply(text,row);items.append(row)
    for name,part,seed in (
        ('width-finite','finite(geometry.halfWidth)','boxGeometry.halfWidth = '+inf+';'),
        ('width-positive','geometry.halfWidth > 0.0f32','boxGeometry.halfWidth = 0.0f32;'),
        ('height-finite','finite(geometry.halfHeight)','boxGeometry.halfHeight = '+inf+';'),
        ('height-positive','geometry.halfHeight > 0.0f32','boxGeometry.halfHeight = 0.0f32;'),
        ('center','finiteVector(geometry.center)','boxGeometry.center.x = '+inf+';'),
        ('radius-finite','finite(geometry.radius)','boxGeometry.radius = '+inf+';'),
        ('radius-sign','geometry.radius >= 0.0f32','boxGeometry.radius = -1.0f32;'),
        ('rotation-c','finite(geometry.rotation.c)','boxGeometry.rotation.c = '+inf+';'),
        ('rotation-s','finite(geometry.rotation.s)','boxGeometry.rotation.s = '+inf+';'),
        ('rotation-min','1.0f32 - 0.0006f32 < norm','boxGeometry.rotation.c = 0.0f32; boxGeometry.rotation.s = 0.0f32;'),
        ('rotation-max','norm < 1.0f32 + 0.0006f32','boxGeometry.rotation.c = 2.0f32;')):
        extra=[]
        if name in ('rotation-c','rotation-s'):extra=[edit('validBox','norm < 1.0f32 + 0.0006f32','true','isolate-rotation-finite')]
        add('box-'+name,'validBox',part,seed,'game.validBox(boxGeometry)',extra)
    lo,hi=base.function_span(source,'validPolygonPoints');block=source[lo:hi]
    top=next(s for c,s in if_sites(block) if 'shape.count < 3i32' in c)
    for name,part,seed,false_ in (
        ('count-min','shape.count < 3i32','specimen.polygon.count = 2i32;',True),
        ('count-max','shape.count > 8i32','specimen.polygon.count = 9i32;',True),
        ('radius-finite','finite(shape.radius)','specimen.polygon.radius = '+inf+';',False),
        ('radius-sign','shape.radius < 0.0f32','specimen.polygon.radius = -1.0f32;',True)):
        extra=[]
        if 'count' in name:extra=[edit('validPolygonPoints',top,top+'\n    if (shape.count < 3i32 or shape.count > 8i32) return true;','bounded-points-unit')]
                                                                             
        rowpart=top if extra else part
        rownew=top.replace(part,'false',1) if extra else ('false' if false_ else 'true')
        if extra:
            row={'name':'points-'+name,'class_id':None,'guards':['G-LEGACY-GEOMETRY'],'probe':'game-boundary','source':'silnik/fizyka/gra.dk','scope':'validPolygonPoints',
                'expression':rowpart,'replacement':rownew,'fixture_edits':extra,'specimen_seed':seed,'boolean_call':'game.validPolygonPoints(&specimen.polygon)',
                'geometry':'polygon','baseline_status':4,'witness_id':1,'expected_tags':['R'],'seed_description':'Bounded count guard before vertex access.'}
            text=base.apply(source,extra[0]);base.apply(text,row);items.append(row)
        else:add('points-'+name,'validPolygonPoints',part,seed,'game.validPolygonPoints(&specimen.polygon)',false_clause=false_)
    for name,part,seed in (
        ('vertex','not finiteVector(shape.vertices[i])','specimen.polygon.vertices[0].x = '+inf+';'),
        ('edge-finite','not finite(edgeSqr)','specimen.polygon.vertices[0].x = -1.0e20f32; specimen.polygon.vertices[1].x = 1.0e20f32;'),
        ('edge-min','edgeSqr <= FLT_EPSILON * FLT_EPSILON','specimen.polygon.vertices[1] = specimen.polygon.vertices[0];'),
        ('convex','not raw.b2ValidateHull(shape)','specimen.polygon.vertices[2] = math2.Vec2(0.0f32, -0.4f32);')):
        old=next(s for c,s in if_sites(block) if part in c);observe=edit('validPolygonPoints',old,old+'\n        return true;','observe-points-'+name)
        row={'name':'points-'+name,'class_id':None,'guards':['G-LEGACY-GEOMETRY'],'probe':'game-boundary','source':'silnik/fizyka/gra.dk','scope':'validPolygonPoints',
             'expression':old,'replacement':old.replace(part,'false',1),'fixture_edits':[observe],'specimen_seed':seed,'boolean_call':'game.validPolygonPoints(&specimen.polygon)',
             'geometry':'polygon','baseline_status':4,'witness_id':1,'expected_tags':['R'],'seed_description':'Original predicate, observed before dependent hull/area checks.'}
        base.apply(base.apply(source,observe),row);items.append(row)
    for name,part,value in (('finite','finite(area)',inf),('min','area > FLT_EPSILON','0.0f32')):
        seed=edit('validPolygonPoints','return finite(area) and area > FLT_EPSILON;','area = '+value+';\n    return finite(area) and area > FLT_EPSILON;','seed-area-'+name)
        add('points-area-'+name,'validPolygonPoints',part,'','game.validPolygonPoints(&specimen.polygon)',[seed])
    for name,part,assignment in (('centroid','not finiteVector(shape.centroid)','shape.centroid.x = '+inf+';'),('normal','not finiteVector(shape.normals[i])','shape.normals[0].y = '+inf+';')):
        seed=edit('preparePolygon','raw.b2MakePolygon(shape);','raw.b2MakePolygon(shape); '+assignment,'seed-prepared-'+name)
        add('prepare-'+name,'preparePolygon',part,'','game.preparePolygon(&specimen.polygon)',[seed],false_clause=True)
    guard='if (not validPolygonPoints(shape)) return false;'
    observe=edit('preparePolygon',guard,guard+'\n    return true;','prepare-input-boundary')
    add('prepare-input','preparePolygon','not validPolygonPoints(shape)','specimen.polygon.count = 2i32;',
        'game.preparePolygon(&specimen.polygon)',[observe],false_clause=True)

def if_sites(block):
    for m in re.finditer(r'\bif\s*\(',block):
        start=m.start();lp=block.index('(',start);depth=1;k=lp+1
        while depth:
            if block[k]=='(':depth+=1
            if block[k]==')':depth-=1
            k+=1
        cond=block[lp+1:k-1];j=k
        while block[j].isspace():j+=1
        if block[j]=='{':
            depth=1;end=j+1
            while depth:
                if block[end]=='{':depth+=1
                if block[end]=='}':depth-=1
                end+=1
        else:end=block.index(';',j)+1
        yield cond,block[start:end]

def reader_recipes(root,items):
    text=(root/'silnik/port/kontakty.dk').read_text(encoding='utf-8')
    config=[('readRow','c == 0i32','return;'),('readRow','i > 0i32 and rowBytes[i]','return;'),('readRow','rowLength == 0i32','return;'),('readRow','rowBytes[i] == 13i32','return;'),('readRow','c < 0i32','return;'),
      ('main','rowLength < 6i32','return 0i64;'),('main','count < 1u32','return 0i64;'),('readWord','value > 4294967295u64','return 0u32;'),('checkArity','count != expected','return;'),('readWord','value > 4294967295u64','return 0u32;'),
      ('main','id != caseIndex','return 0i64;'),('main','opCount < 1u32','return 0i64;'),('readOperation','seq != expectedSeq','return op;'),('readOperation','opcode > 53u32','return op;'),
      ('prevalidateWords','w[field] >= bound','return false;'),('validOperation9','not sourceGood','return false;'),('validOperation9','collision','return false;'),('prevalidateWords','w[flag] > 1u32','return false;'),
      ('prevalidateWords','tagIndex != -1i32','return false;'),('prevalidateWords','w[i] != 0u32','return false;'),('decodeRot','not (1.0f32','return q;'),('readOperation','w[2] > 256u32','return op;'),
      ('decodeManifold','w[offset + 3i32] > 2u32','return result;'),('decodeContactOperation','w[32] > 3u32','return 39i32;'),('validOperation9','op.opcode != reg.phase + 41i32 or op.a != reg.phaseOwner','return false;'),
      ('prevalidateWords','code == 40u32 and w[58]','return false;'),('checkPopulation','worlds > 2i32','return false;'),('checkEnd','c >= 0i32','return;'),('main','not capturesClosed','return 0i64;')]
    for i,(scope,needle,ret) in enumerate(config,1):
        lo,hi=base.function_span(text,scope);candidates=[(c,s) for c,s in if_sites(text[lo:hi]) if needle in c and 'invalid(' in s]
        if len(candidates)!=1:raise ValueError((i,scope,needle,len(candidates)))
        condition,statement=candidates[0];guard=f'F{i:02}'
        items.append({'name':'reader-'+guard,'class_id':None,'guards':[guard],'guard':guard,'probe':'reader-boundary','source':'silnik/port/kontakty.dk','scope':scope,
            'condition':condition,'guard_statement':statement,'boundary_return':ret,'port_line':text[:text.index(statement,lo,hi)].count('\n')+1,'witness_id':1,'expected_tags':['GUARD9']})

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE.parents[1]
    rows=freeze(root);print('native recipes:',len(rows))
