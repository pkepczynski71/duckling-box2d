pass                                                                              
import importlib.util
import json
import re
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
base=load('new11_mutator','mutacje-ruch-swiata.py')
f=load('new11_witnesses','fixtury-sen11.py')


def apply_recipe(source,recipe):
    changed=base.apply(source,recipe)
    for edit in recipe.get('scoped_edits',()):
        changed=base.apply(changed,{'name':recipe['name'],'scope':edit['scope'],
                                  'expression':edit['expression'],'replacement':edit['replacement']})
    for edit in recipe.get('file_edits',()):
        if changed.count(edit['expression'])!=1:raise ValueError('file edit must match once: '+recipe['name'])
        changed=changed.replace(edit['expression'],edit['replacement'],1)
    return changed


def planned():
    rows=[]
    def add(name,klass,scope,old,new,fixture,source='swiat.dk'):
        rows.append({'name':name,'class_id':klass,'scope':scope,'expression':old,'replacement':new,
            'fixture':fixture,'source':'silnik/fizyka/'+source,'proof_scope':'new11 actual product',
            'original_anchor':'KONTRAKT-11 Dodatek E / '+klass})
    add('M11-01-ANGULAR','M11-01','b2FinalizeBody','mass2.b2AbsFloat(state.angularVelocity) * sim.maxExtent','0.0f32','ANGULAR')
    add('M11-01-DELTAS','M11-01','b2FinalizeBody','0.5f32 * world.finalizeInvDt * maxDeltaPosition','0.0f32','DELTAS')
    add('M11-02-GE','M11-02','b2FinalizeBody','sleepVelocity > body.sleepThreshold','sleepVelocity >= body.sleepThreshold','ZERO-THRESHOLD')
    add('M11-02-HALF','M11-02','b2FinalizeBody','sleepTime < 0.5f32','sleepTime <= 0.5f32','SLEEP4')
    add('M11-02-SUBSTEP','M11-02','b2Solve','world.finalizeDt = context.dt;','world.finalizeDt = context.h;','SLEEP4-N4')
    add('M11-03-WORLD','M11-03','b2FinalizeBody','not world.enableSleep or ','','WORLD-NOSLEEP')
    add('M11-03-BODY','M11-03','b2FinalizeBody','not body.enableSleep or ','','BODY-NOSLEEP')
    add('M11-03-WAKE-SETS','M11-03','b2World_EnableSleeping','if (not flag)','if (false)','WORLD-DISABLE')
    add('M11-04-LOCAL','M11-04','b2FinalizeBody','world.islands.at(body.islandId as i64).localIndex','body.id','DELTAS')
    source=(HERE.parents[1]/'silnik/fizyka/swiat.dk').read_text(encoding='utf-8')
    lo,hi=base.function_span(source,'b2World_StepPreparedCounter12');function=source[lo:hi]
    reverse=re.search(r'var sleepIndex: i32 = .*?sleepIndex = sleepIndex - 1i32;\n            }',function,re.S)
    if reverse is None:raise ValueError('actual reverse sleep loop required')
    old=reverse.group();new=old.replace('b2GetSolverSet(world, 2i32).islandCount - 1i32','0i32').replace('sleepIndex >= 0i32','sleepIndex < b2GetSolverSet(world, 2i32).islandCount').replace('sleepIndex - 1i32','sleepIndex + 1i32')
    reverse_sleep_loop=old
    add('M11-05-FORWARD','M11-05','b2World_StepPreparedCounter12',old,new,'MANY-SLEEP')
    add('M11-06-A','M11-06','b2LinkContact','setA == 2i32 and setB >= 3i32','false','LINK-A')
    add('M11-06-B','M11-06','b2LinkContact','setB == 2i32 and setA >= 3i32','false','LINK-B')
    add('M11-07-DISABLED','M11-07','b2CreateContact','record.contactId = id; record.setIndex = 1i32;','record.contactId = id; record.setIndex = 2i32;','C04')
    add('M11-08-TIMER','M11-08','b2WakeSolverSet','world.bodies.at(bodyId as i64).sleepTime = 0.0f32;','','WAKE-TIMER')
    add('M11-08-IDENTITY','M11-08','b2WakeSolverSet','b2GetSolverSet(world, 2i32).bodyCount = target + 1i32;',
        'b2GetSolverSet(world, 2i32).bodyCount = target + 1i32; b2GetSolverSet(world, 2i32).bodyStates.at(target as i64).deltaRotation = Rot(0.0f32, 0.0f32);','C01')
    add('M11-09-TRANSFER','M11-09','b2WakeSolverSet','record.setIndex == 1i32','false','C04')
    add('M11-09-MOVED','M11-09','b2RemoveNonTouchingContact','world.contacts.at(moved.contactId as i64).localIndex = local;','','C05-FIRST')
    add('M11-10-STATE','M11-10','b2TrySleepIsland','b2GetSolverSet(world, 2i32).bodyStates.at(body.localIndex as i64) = movedState;','','SWAP-STATES')
    add('M11-10-LOCAL','M11-10','b2TrySleepIsland','world.bodies.at(moved.bodyId as i64).localIndex = body.localIndex;','','LOCAL-PROBE')
    add('M11-10-FORCE','M11-10','b2TrySleepIsland',
        'let sim: BodySim = b2GetSolverSet(world, 2i32).bodySims.at(body.localIndex as i64);',
        'var sim: BodySim = b2GetSolverSet(world, 2i32).bodySims.at(body.localIndex as i64); sim.force = Vec2();','FORCE-SLEEP')
    add('M11-11-OTHER','M11-11','b2TrySleepIsland','world.bodies.at(otherBodyId as i64).setIndex != 2i32','world.bodies.at(otherBodyId as i64).setIndex == 2i32','C06-FIRST')
    add('M11-12-MASK','M11-12','b2TrySleepIsland',
        'let source: ContactSim = world.constraintGraph.colors[contactRecord.colorIndex].contactSims.at(contactRecord.localIndex as i64);',
        'var source: ContactSim = world.constraintGraph.colors[contactRecord.colorIndex].contactSims.at(contactRecord.localIndex as i64); source.rollingDefined = false;','C07')
    add('M11-12-BITSET','M11-12','b2RemoveContactFromGraph','bits.b2ClearBit(&color.bodySet, a);','','C08')
    add('M11-12-LOCAL','M11-12','b2RemoveContactFromGraph','world.contacts.at(moved.contactId as i64).localIndex = local;','','C08')
    add('M11-13-MASK','M11-13','b2WakeSolverSet',
        'let contactSim: ContactSim = b2GetSolverSet(world, setIndex).contactSims.at(ci as i64);',
        'var contactSim: ContactSim = b2GetSolverSet(world, setIndex).contactSims.at(ci as i64); contactSim.rollingDefined = false;','C07')
    add('M11-14-POOL','M11-14','b2DestroySolverSet','b2FreeId(&world.solverSetIdPool, setIndex);','','C01')
    add('M11-14-LOCAL','M11-14','b2TrySleepIsland','world.islands.at(movedIsland as i64).localIndex = island.localIndex;','','LOCAL-PROBE')
    add('M11-15-FELL','M11-15','b2TrySleepIsland','.fellAsleep = true;','.fellAsleep = false;','SLEEP4')
    add('M11-15-INDEX','M11-15','b2TrySleepIsland','world.bodies.at(bodyId as i64).bodyMoveIndex = -1i32;','','C03')
    add('M11-15-OLD-MOVE','M11-15','b2TrySleepIsland','world.bodyMoveEvents.at(body.bodyMoveIndex as i64).fellAsleep','world.bodyMoveEvents.at(body.localIndex as i64).fellAsleep','TOUCH-SLEEP')
    add('M11-16-NOWAKE','M11-16','b2DestroyContact','wakeBodies and (record.flags & 1u32) != 0u32','(record.flags & 1u32) != 0u32','DESTROY-TOUCH-NOWAKE')
    add('M11-16-TOUCH','M11-16','b2DestroyContact','wakeBodies and (record.flags & 1u32) != 0u32','false','DESTROY-TOUCH-WAKE')
    add('M11-16-NONTOUCH','M11-16','b2DestroyContact','wakeBodies and (record.flags & 1u32) != 0u32','wakeBodies','DESTROY-NONTOUCH')
    add('M11-17-ZERO','M11-17','b2Body_SetLinearVelocity','mass2.b2LengthSquared(velocity) > 0.0f32','true','LINEAR-ZERO')
    add('M11-17-REACQUIRE','M11-17','b2Body_SetLinearVelocity','let current: BodyRecord = world.bodies.at(body.id as i64);','let current: BodyRecord = body;','LINEAR-WAKE')
    add('M11-17-WAKE','M11-17','b2Body_ApplyAction','if (wake)','if (false)','FORCE-WAKE')
    add('M11-17-FIXED','M11-17','b2Body_SetAngularVelocity',' or body.fixedRotation','','ANGULAR-FIXED')
    add('M11-24-CHILD','M11-24','b2MergeIsland','target.constraintRemoveCount = target.constraintRemoveCount + child.constraintRemoveCount;',
        'target.constraintRemoveCount = target.constraintRemoveCount;','MERGE-CHILD')
    add('M11-24-PARENT','M11-24','b2MergeIsland','target.constraintRemoveCount = target.constraintRemoveCount + child.constraintRemoveCount;',
        'target.constraintRemoveCount = child.constraintRemoveCount;','MERGE-PARENT')
                                                                               
    for route in range(6):
        for kind,old,new,suffix in [('FIN','finite(threshold)','true','inf'),('SIGN','threshold >= 0.0f32','true','negative'),('ZERO','threshold >= 0.0f32','threshold > 0.0f32','plus-zero')]:
            add(f'TH-{kind}-{route}',f'TH-{kind}-{route}','validSleepThreshold',old,new,f'GUARD:TH-{route}-{suffix}','gra.dk')
    for opcode,scope in ((58,'setAwake'),(59,'setSleepEnabled'),(60,'setSleepThreshold'),(62,'getSleepState')):
        if opcode==62:old='result.status = bodyStatus(owner, number);';new='result.status = OK;'
        else:old='let status: i32 = bodyMutationStatus(owner, number);';new='let status: i32 = OK;'
        add(f'CALL-{opcode}',f'CALL-{opcode}',scope,old,new,f'GUARD:FOREIGN-CALL-{opcode}','gra.dk')
    add('BUPPER-REMAINDER','BREMAINDER','sleepBodyUpperBlocksFit','count / 4i64 + 3i64','count / 4i64','GUARD:BUPPER-131060','gra.dk')
    add('BUPPER-AWAKE','BUPPER','sleepBodyUpperFit','while (setIndex < world.solverSetIdPool.nextIndex)','while (setIndex < 3i32)','GUARD:BUPPER-SUM-1-131059','gra.dk')
    add('BUPPER-ARITH','BARITH','checkedSleepBodySum','count > 9223372036854775807i64 - added','false','GUARD:BUPPER-SUM-9223372036854775807-1','gra.dk')
    legacy=load('new11_source_guards','mutacje-sen.py')
    for old in legacy.recipes()['native_mutations']:
        if not old['name'].startswith('WORLD-'):continue
        add('ROUTE56-'+old['name'],old['name'],old['scope'],old['expression'],old['replacement'],'ROUTE56-'+old['fixture'],'gra.dk')
    add('WORLD-ROUTE','WORLD-ROUTE','createSolverWorld','not validSolverWorldParameters(parameters)','false','WORLD-ROUTE','gra.dk')
    add('STEP-CALL','STEP-CALL','step','not validStepParameters(parameters)','false','STEP-INVALID','gra.dk')
                                                                            
                                                                                
    debt=legacy.m12_recipe(HERE.parents[1]);debt.update(name='M12-LINK-REF',fixture='LINK-B',proof_scope='new11 actual Link wake/growth')
    rows.append(debt)
    for route in (58,59,60,62):
        add('W-'+str(route),'W-'+str(route),'bodyStatus','worldStatus(owner) != OK','false','GUARD:WORLD-PRIORITY-'+str(route),'gra.dk')
        for half,field in (('low',1),('high',2)):
            remaining='high' if half=='low' else 'low'
            add(f'OWNER-{route}-{half}',f'OWNER-{route}-{half}','bodyStatus',
                'not equalKey(owner.birthTicket, number.ownerTicket)',f'owner.birthTicket.{remaining} != number.ownerTicket.{remaining}',
                'GUARD:BODY-STATUS-'+str(field),'gra.dk')
        add(f'BODY-{route}-id',f'BODY-{route}-id','bodyStatus','body.id == -1i32','false','GUARD:BODY-STATUS-6','gra.dk')
        for half,field in (('low',3),('high',4)):
            remaining='high' if half=='low' else 'low'
            add(f'BODY-{route}-birth.{half}',f'BODY-{route}-birth.{half}','bodyStatus',
                'not equalKey(body.birthTicket, number.birthTicket)',f'body.birthTicket.{remaining} != number.birthTicket.{remaining}',
                'GUARD:BODY-STATUS-'+str(field),'gra.dk')
    add('W-57','W-57','worldStatus','not equalKey(world.birthTicket, number.birthTicket)','false','GUARD:WORLD-57-MAX','gra.dk')
    add('W-61','W-61','setSleepingEnabled','let status: i32 = worldMutationStatus(owner);','let status: i32 = OK;','GUARD:WORLD-STALE-61','gra.dk')
    add('SETINDEX-NE','SETINDEX-NE','bodyStatus','body.setIndex == -1i32','body.setIndex != -1i32','GUARD:BODY-STATUS-0','gra.dk')
    add('RAW-NOT','RAW-NOT','bodyStatus','not raw.b2Body_IsValid(raw.b2MakeBodyId(world, number.slot))','raw.b2Body_IsValid(raw.b2MakeBodyId(world, number.slot))','GUARD:BODY-STATUS-0','gra.dk')
    for old in legacy.recipes()['native_mutations']:
        if old['name'] in ('STEP-N','STEP-INVH'):
            add(old['name'],old['name'],old['scope'],old['expression'],old['replacement'],'GUARD:'+old['fixture'],'gra.dk')
    add('CCOUNT','CCOUNT','contactBlocksFit','upper / 4i64 + 3i64 <= 32767i64','true','GUARD:COUNT-1-131060-0','gra.dk')
    add('CREQUEST','CREQUEST','checkedContactSum','value = count + added;','value = count;','GUARD:COUNT-2-131059-1','gra.dk')
    add('CARITH','CARITH','checkedContactSum','count > 9223372036854775807i64 - added','false','GUARD:COUNT-2-9223372036854775807-1','gra.dk')
    add('BATCH','BATCH','solverStep','ticketLimit(reserved)','i == 0i64 and ticketLimit(reserved)','GUARD:MAX-BATCH','gra.dk')
    add('MAX-WAKE','MAX-WAKE','setAwake','raw.b2Body_SetAwake(raw.b2MakeBodyId(world, number.slot), awake);',
        'if (ticketLimit(lastIssued)) return LIMIT; raw.b2Body_SetAwake(raw.b2MakeBodyId(world, number.slot), awake);','GUARD:MAX-WAKE','gra.dk')
                                                                             
                                                                   
    add('M11-18-SLEEP','M11-18','b2SplitIsland','setIndex != 2i32','false','SPLIT-SLEEP-DIRTY')
    add('M11-18-CLEAN','M11-18','b2SplitIsland','base.constraintRemoveCount == 0i32','false','C12')
    add('M11-19-SEEDS','M11-19','b2SplitIsland','let seedId: i32 = bodyIds.at(seedOrdinal);',
        'let seedId: i32 = bodyIds.at(bodyIds.length() - 1i64 - seedOrdinal);','C13')
    add('M11-20-KINEMATIC','M11-20','b2SplitIsland','world.bodies.at(otherId as i64).setIndex != 0i32',
        'world.bodies.at(otherId as i64).bodyType == 2i32','SPLIT-KINEMATIC')
    add('M11-21-RECYCLE','M11-21','b2CreateIsland','var island = Island();',
        'var island = Island(); if (id as i64 < world.islands.length()) island.constraintRemoveCount = world.islands.at(id as i64).constraintRemoveCount;','C13')
    add('M11-22-TIE','M11-22','b2FinalizeBody','sleepTime > world.taskSplitSleepTime','sleepTime >= world.taskSplitSleepTime','SPLIT-TIE')
    add('M11-22-NEXT','M11-22','b2Solve','if (world.splitIslandId != -1i32) b2SplitIsland(world, world.splitIslandId);','','SPLIT-NEXT')
    add('M11-23-OLD','M11-23','b2Body_SetAwake','b2TrySleepIsland(world, world.bodies.at(body.id as i64).islandId);',
        'b2TrySleepIsland(world, body.islandId);','C16')
    add('W2-M01-ABS-W','M11-01','b2FinalizeBody','mass2.b2AbsFloat(state.angularVelocity)','state.angularVelocity','ANGULAR-NEGATIVE')
    add('W2-M02-RESET','M11-02','b2FinalizeBody','body.sleepTime + world.finalizeDt','world.finalizeDt','SLEEP4')
    add('W2-M03-REPEAT','M11-03','b2World_EnableSleeping','world.enableSleep == flag','false','WORLD-REPEAT-FALSE')
    add('W2-M04-ID','M11-04','b2FinalizeBody','world.islands.at(body.islandId as i64).localIndex','body.islandId','ISLAND-SPARSE')
    add('W2-M05-ORDER','M11-05','b2World_StepPreparedCounter12',reverse_sleep_loop,'','MOVING-SLEEP')
    rows[-1]['edits']=[{'expression':reverse_sleep_loop,'replacement':''},
        {'expression':'var ei: i32 = 0i32;','replacement':'if (world.enableSleep) { '+reverse_sleep_loop+' }\n        var ei: i32 = 0i32;'}]
    add('W2-M07-SLEEPING','M11-07','b2CreateContact','record.contactId = id; record.setIndex = 1i32;',
        'record.contactId = id; record.setIndex = world.bodies.at(shapeA.bodyId as i64).setIndex;','C04')
    add('W2-M08-REUSE','M11-08','b2WakeSolverSet','else b2GetSolverSet(world, 2i32).bodyStates.at(target as i64) = BodyState();','else { }','WAKE-MOVING')
    add('W2-M09-DUPLICATE','M11-09','b2WakeSolverSet','b2RemoveNonTouchingContact(world, record.localIndex, 1i32);','','C04')
    add('W2-M11-MOVED','M11-11','b2RemoveNonTouchingContact','world.contacts.at(moved.contactId as i64).localIndex = local;','','C06')
    add('W2-M12-OVERFLOW','M11-12','b2RemoveContactFromGraph','bits.b2ClearBit(&color.bodySet, a);',
        'bits.b2ClearBit(&world.constraintGraph.colors[11].bodySet, a);','C08')
    add('W2-M01-FACTOR','M11-01','b2FinalizeBody','0.5f32 * world.finalizeInvDt * maxDeltaPosition','1.0f32 * world.finalizeInvDt * maxDeltaPosition','DELTA-FACTOR')
    add('W2-M01-INVH','M11-01','b2Solve','world.finalizeInvDt = context.inv_dt;','world.finalizeInvDt = context.inv_h;','DELTA-INVH')
    add('W2-M01-SUM','M11-01','b2FinalizeBody','tree.b2MaxFloat(maxVelocity, 0.5f32 * world.finalizeInvDt * maxDeltaPosition)',
        'maxVelocity + 0.5f32 * world.finalizeInvDt * maxDeltaPosition','MAX-SUM')
    add('W2-M01-PARENS','M11-01','b2FinalizeBody','math.sqrt(mass2.b2LengthSquared(state.linearVelocity)) + mass2.b2AbsFloat(state.angularVelocity) * sim.maxExtent',
        '(math.sqrt(mass2.b2LengthSquared(state.linearVelocity)) + mass2.b2AbsFloat(state.angularVelocity)) * sim.maxExtent','VELOCITY-PARENS')
    add('W2-M01-ANGLE','M11-01','b2FinalizeBody','mass2.b2AbsFloat(state.deltaRotation.s)',
        'mass2.b2AbsFloat(math.libm_forward.trig_funcs.atan2f(state.deltaRotation.s, state.deltaRotation.c))','ANGLE-CORRECTION')
    add('W2-M11-SET','M11-11','b2TrySleepIsland','b2AddNonTouchingContact(world, contactId, contactSim, 1i32);',
        'b2AddNonTouchingContact(world, contactId, contactSim, setIndex);','C06')
    add('W2-M13-INDEX','M11-13','b2WakeSolverSet','b2AddContactToGraph(world, contactSim.contactId, contactSim);',
        'b2AddContactToGraph(world, contactSim.contactId, contactSim); world.constraintGraph.colors[world.contacts.at(contactSim.contactId as i64).colorIndex].contactSims.at(world.contacts.at(contactSim.contactId as i64).localIndex as i64).bodySimIndexA = -1i32;','C07')
    add('W2-M13-MASS','M11-13','b2WakeSolverSet','b2AddContactToGraph(world, contactSim.contactId, contactSim);',
        'b2AddContactToGraph(world, contactSim.contactId, contactSim); world.constraintGraph.colors[world.contacts.at(contactSim.contactId as i64).colorIndex].contactSims.at(world.contacts.at(contactSim.contactId as i64).localIndex as i64).invMassA = 0.0f32;','C07')
    add('W2-M13-IMPULSE','M11-13','b2WakeSolverSet','let contactSim: ContactSim = b2GetSolverSet(world, setIndex).contactSims.at(ci as i64);',
        'var contactSim: ContactSim = b2GetSolverSet(world, setIndex).contactSims.at(ci as i64); contactSim.manifold.rollingImpulse = 0.0f32;','C07')
    add('W2-M14-RECYCLE','M11-14','b2CreateSleepingSet','stored = move value;','if (not recycled) stored = move value;','SET-RECYCLE-PROBE')
    rows[-1]['edits']=[{'expression':'let id: i32 = b2AllocId(&world.solverSetIdPool);',
        'replacement':'let recycled: bool = world.solverSetIdPool.freeCount > 0i32; let id: i32 = b2AllocId(&world.solverSetIdPool);'},
        {'expression':'stored = move value;','replacement':'if (not recycled) stored = move value;'}]
    add('W2-M19-CLEAR-BODY','M11-19','b2SplitIsland','world.bodies.at(nextBody as i64).isMarked = false;','','C13')
    add('W2-M19-CLEAR-CONTACT','M11-19','b2SplitIsland','world.contacts.at(nextContact as i64).isMarked = false;','','C13')
    add('W2-M19-FIRST','M11-19','b2SplitIsland','var seedOrdinal: i64 = 0i64;','var seedOrdinal: i64 = 1i64;','C13')
    add('W2-M19-LAST','M11-19','b2SplitIsland','seedOrdinal < bodyIds.length()','seedOrdinal + 1i64 < bodyIds.length()','SPLIT-ISOLATED-LAST')
    add('W2-M19-FIFO','M11-19','b2SplitIsland','let bodyId: i32 = stack.at(stackCount);',
        'let bodyId: i32 = stack.at(0i64); var shift: i64 = 0i64; while (shift < stackCount) { stack.at(shift) = stack.at(shift + 1i64); shift = shift + 1i64; }','C13')
    add('W2-M20-NONTOUCH','M11-20','b2SplitIsland','not contact.isMarked and (contact.flags & 1u32) != 0u32','not contact.isMarked','SPLIT-NONTOUCH')
    add('W2-M20-STATIC','M11-20','b2SplitIsland',' and world.bodies.at(otherId as i64).setIndex != 0i32','','C14')
    add('W2-M21-ALLOC-FIRST','M11-21','b2SplitIsland','b2DestroyIsland(world, baseId);',
        'let firstIsland: i32 = b2CreateIsland(world, setIndex); b2DestroyIsland(world, baseId);','C13')
    rows[-1]['edits']=[{'expression':'b2DestroyIsland(world, baseId);','replacement':rows[-1]['replacement']},
        {'expression':'let islandId: i32 = b2CreateIsland(world, setIndex);',
         'replacement':'let islandId: i32 = if seedOrdinal == 0i64 then firstIsland else b2CreateIsland(world, setIndex);'}]
    add('W2-M21-PARENT','M11-21','b2CreateIsland','var island = Island();',
        'var island = Island(); if (id as i64 < world.islands.length()) island.parentIsland = world.islands.at(id as i64).parentIsland;','ISLAND-RECYCLE-PARENT')
    add('W2-M22-DESTROY','M11-22','b2DestroyIsland','if (world.splitIslandId == id) world.splitIslandId = -1i32;','','CANDIDATE-DESTROY')
    add('W2-M23-ALL','M11-23','b2Body_SetAwake','b2TrySleepIsland(world, world.bodies.at(body.id as i64).islandId);',
        'var sleepAll: i32 = b2GetSolverSet(world, 2i32).islandCount - 1i32; while (sleepAll >= 0i32) { b2TrySleepIsland(world, b2GetSolverSet(world, 2i32).islandSims.at(sleepAll as i64)); sleepAll = sleepAll - 1i32; }','C16')
    add('W2-M22-IMMEDIATE','M11-22','b2Solve','world.finalizedTaskSplitSleepTime = world.taskSplitSleepTime;',
        'world.finalizedTaskSplitSleepTime = world.taskSplitSleepTime; if (world.taskSplitIslandId != -1i32) b2SplitIsland(world, world.taskSplitIslandId);','SPLIT-TIE')
    add('W2-M22-MULTIPLE','M11-22','b2Solve','if (world.splitIslandId != -1i32) b2SplitIsland(world, world.splitIslandId);',
        'if (world.splitIslandId != -1i32) { var splitIds: List[i32]; var si: i32 = 0i32; while (si < b2GetSolverSet(world, 2i32).islandCount) { let sid: i32 = b2GetSolverSet(world, 2i32).islandSims.at(si as i64); if (world.islands.at(sid as i64).constraintRemoveCount > 0i32) splitIds.push(sid); si = si + 1i32; } var sj: i64 = 0i64; while (sj < splitIds.length()) { b2SplitIsland(world, splitIds.at(sj)); sj = sj + 1i64; } }','SPLIT-NEXT')
    add('W2-M19-MARK-POP','M11-19','b2SplitIsland','world.bodies.at(otherId as i64).isMarked = true;','','SPLIT-CYCLE')
    rows[-1]['edits']=[{'expression':'world.bodies.at(otherId as i64).isMarked = true;','replacement':''},
        {'expression':'world.bodies.at(seedId as i64).isMarked = true;','replacement':''},
        {'expression':'let bodyId: i32 = stack.at(stackCount);','replacement':'let bodyId: i32 = stack.at(stackCount); world.bodies.at(bodyId as i64).isMarked = true;'}]
    sleep_source='let source: ContactSim = world.constraintGraph.colors[contactRecord.colorIndex].contactSims.at(contactRecord.localIndex as i64);'
    for label,change in (('CACHE','source.cache.count = 0i32;'),('IMPULSE','manifoldPoint(&source.manifold, 0i32).normalImpulse = 0.0f32;')):
        add('W2-M12-'+label,'M11-12','b2TrySleepIsland',sleep_source,
            sleep_source.replace('let source:','var source:')+' '+change,'C07')
    for label,expression in (
        ('BODY-COUNT','world.islands.at(islandId as i64).bodyCount = world.islands.at(islandId as i64).bodyCount + 1i32;'),
        ('BODY-HEAD','if (world.islands.at(islandId as i64).headBody == -1i32) world.islands.at(islandId as i64).headBody = bodyId;'),
        ('BODY-TAIL','world.islands.at(islandId as i64).tailBody = bodyId;'),
        ('BODY-PREV','world.bodies.at(bodyId as i64).islandPrev = tailBody;'),
        ('BODY-NEXT','world.bodies.at(bodyId as i64).islandNext = -1i32;'),
        ('CONTACT-COUNT','world.islands.at(islandId as i64).contactCount = world.islands.at(islandId as i64).contactCount + 1i32;'),
        ('CONTACT-HEAD','if (world.islands.at(islandId as i64).headContact == -1i32) world.islands.at(islandId as i64).headContact = contactId;'),
        ('CONTACT-TAIL','world.islands.at(islandId as i64).tailContact = contactId;'),
        ('CONTACT-PREV','world.contacts.at(contactId as i64).islandPrev = tailContact;'),
        ('CONTACT-NEXT','world.contacts.at(contactId as i64).islandNext = -1i32;')):
        add('W2-M20-'+label,'M11-20','b2SplitIsland',expression,'','SPLIT-TWO-PAIRS' if label.endswith('-NEXT') or label=='CONTACT-PREV' else 'C13-FIRST')
    add('W2-M20-DUPLICATE','M11-20','b2SplitIsland','not contact.isMarked and (contact.flags & 1u32) != 0u32',
        '(contact.flags & 1u32) != 0u32','SPLIT-TWO-PAIRS')
    lo,hi=base.function_span(source,'b2TrySleepIsland');body=source[lo:hi]
    event_start=body.index('if (body.bodyMoveIndex != -1i32) {')
    event_end=body.index('        let sim: BodySim',event_start)
    event_guard=body[event_start:event_end].rstrip()
    add('W2-M15-SPURIOUS','M11-15','b2TrySleepIsland',event_guard,
        event_guard+' else { var spurious = BodyMoveEvent(); spurious.bodyId = b2MakeBodyId(world, body.id); spurious.fellAsleep = true; world.bodyMoveEvents.push(spurious); }','C02')
    add('W2-M06-GRAPH-FIRST','M11-06','b2CollideChanges','b2LinkContact(world, id);','','LINK-B')
    rows[-1]['edits']=[{'expression':'b2LinkContact(world, id);','replacement':''},
        {'expression':'b2AddContactToGraph(world, id, transfer);','replacement':'b2AddContactToGraph(world, id, transfer); b2LinkContact(world, id);'}]
    add('W2-M16-WRONG-SET','M11-16','b2DestroyContact','b2RemoveNonTouchingContact(world, record.localIndex, record.setIndex);',
        'b2RemoveNonTouchingContact(world, record.localIndex, 2i32);','DESTROY-MIXED-SETS')
    wake_block='if (wakeBodies and (record.flags & 1u32) != 0u32) {\n        b2WakeBody(world, record.edgeA.bodyId);\n        b2WakeBody(world, record.edgeB.bodyId);\n    }'
    add('W2-M16-WAKE-FIRST','M11-16','b2DestroyContact',wake_block,'','DESTROY-TOUCH-WAKE')
    rows[-1]['edits']=[{'expression':wake_block,'replacement':''},
        {'expression':'let record: ContactRecord = world.contacts.at(id as i64);',
         'replacement':'var record: ContactRecord = world.contacts.at(id as i64); '+wake_block+' record = world.contacts.at(id as i64);'}]
                                                                            
                                                                            
                                                                               
    allocate='let allocated: raw.BodyId = raw.b2CreateBody(raw.WorldId((owner.slot + 1i32) as u16, raw.worlds.at(owner.slot as i64).generation), def); '
    for route,scope in enumerate(('createBody','createBody8','createBodyWithShape','createBodyWithPreparedShape','createBodyWithBox')):
        guard='not validBodyDef(def)' if route==1 else 'not validSleepThreshold(def.sleepThreshold)'
        old='if ('+guard+') { result.status = PARAM; return result; }'
        new='if ('+guard+') { '+allocate+'result.status = PARAM; return result; }'
        add('TH-ROUTE-'+str(route),'TH-ROUTE-'+str(route),scope,old,new,'TH-ROUTE-PROBE','gra.dk')
                                                                               
                                                                          
    add('W3-MOVE-SHALLOW','MOVE-COPY','step','var result = StepResult(); result.status = worldMutationStatus(owner);',
        'var result = StepResult(); result = copy result; result.status = worldMutationStatus(owner);','GUARD:MOVE-COPY','gra.dk')
    rows[-1]['file_edits']=[{'expression':'class StepResult {','replacement':'''class StepResult {
    StepResult.copy(other: const ref StepResult) = {
        var result = StepResult(); result.status = other.status;
        result.shapeA = other.shapeA; result.shapeB = other.shapeB;
        result.effectiveSubSteps = other.effectiveSubSteps; result.didSolve = other.didSolve; result.reason = other.reason;
        result.values.pointer = other.values.pointer; result.values.len = other.values.len; result.values.cap = 0i64;
        return result;
    }'''}]
    for field,typ,index,fixture,klass in (('begin','ContactBegin','i','COPY-BEGIN','CONTACT-COPY'),
                                       ('end','ContactEnd','j','COPY-END','CONTACT-COPY'),
                                       ('hits','ContactHit','k','COPY-HIT','HIT-COPY')):
        original=f'while ({index} < source.{field}.length()) {{ let '+('begin' if field=='begin' else 'end' if field=='end' else 'hit')+f': {typ} = source.{field}.at({index}); result.{field}.push('+('begin' if field=='begin' else 'end' if field=='end' else 'hit')+f'); {index} = {index} + 1i64; }}'
        mask={'begin':1,'end':2,'hits':4}[field]
        replacement=f'source.{field}.reserve(source.{field}.length() + 1i64); result.{field}.pointer = source.{field}.pointer; result.{field}.len = source.{field}.len; result.{field}.cap = source.{field}.cap; result.w3Borrowed = {mask}i32;'
        add('W3-'+field.upper()+'-SHALLOW',klass,'cloneContactEvents',original,replacement,fixture,'gra.dk')
        rows[-1]['file_edits']=[{'expression':'class ContactEvents {','replacement':'''class ContactEvents {
    w3Borrowed: i32 = 0i32;
    ContactEvents.destroy() = {
        if ((w3Borrowed & 1i32) != 0i32) { begin.len = 0i64; begin.cap = 0i64; }
        if ((w3Borrowed & 2i32) != 0i32) { end.len = 0i64; end.cap = 0i64; }
        if ((w3Borrowed & 4i32) != 0i32) { hits.len = 0i64; hits.cap = 0i64; }
    }'''}]
                                                                             
                                                                           
    add('W3-M13-OLD-COLOR','M11-13','b2AddContactToGraph',
        'var i: i32 = if staticA or staticB then 1i32 else 0i32;',
        'var i: i32 = if staticA or staticB then 1i32 else 0i32; if (source.w3OldColor >= 0i32) i = source.w3OldColor;','C08')
    old_source='let source: ContactSim = world.constraintGraph.colors[contactRecord.colorIndex].contactSims.at(contactRecord.localIndex as i64);'
    rows[-1]['scoped_edits']=[{'scope':'b2TrySleepIsland','expression':old_source,
        'replacement':old_source.replace('let source:','var source:')+' source.w3OldColor = contactRecord.colorIndex;'}]
    rows[-1]['file_edits']=[{'expression':'class ContactSim {','replacement':'class ContactSim {\n    w3OldColor: i32 = -1i32;'}]
    add('W3-STATE-SHARED','STATE-COPY','getSleepState','var result = SleepState(); result.number = number; result.status = bodyStatus(owner, number);',
        'var result = SleepState(); result.number = number; result.status = bodyStatus(owner, number);','COPY-PROBE:STATE','gra.dk')
    rows[-1]['file_edits']=[{'expression':'class SleepState {','replacement':'var w3SleepFlag: bool = false;\nvar w3SleepThreshold: f32 = 0.0f32;\nclass SleepState {'},
        {'expression':'isSleeping: bool = false;','replacement':'isSleeping: ref bool = &w3SleepFlag;'},
        {'expression':'sleepThreshold: f32 = 0.0f32;','replacement':'sleepThreshold: ref f32 = &w3SleepThreshold;'}]
    add('W3-HISTORY-MC','HISTORY','createBody','result.number = BodyNumber(slot, reserved, owner.birthTicket);',
        'result.number = BodyNumber(slot, reserved, owner.birthTicket); w3MoveNumber = result.number;','HISTORY-MC','gra.dk')
    rows[-1]['file_edits']=[{'expression':'class BodyMove {\n    number: BodyNumber = BodyNumber();',
        'replacement':'var w3MoveNumber: BodyNumber = BodyNumber();\nclass BodyMove {\n    number: ref BodyNumber = &w3MoveNumber;'}]
    owner_mc=dict(rows[-1]);owner_mc.update(name='W3-HISTORY-MC-OWNER',fixture='HISTORY-MC-OWNER');rows.append(owner_mc)
    add('W3-HISTORY-M','HISTORY','b2CreateBody','return b2MakeBodyId(world, id);',
        'w3MoveId = b2MakeBodyId(world, id); return w3MoveId;','HISTORY-MOVE-PROBE')
    rows[-1]['file_edits']=[{'expression':'class BodyMoveEvent {','replacement':'var w3MoveId: BodyId = BodyId();\nclass BodyMoveEvent {'},
        {'expression':'bodyId: BodyId = BodyId();','replacement':'bodyId: ref BodyId = &w3MoveId;'}]
    for field,typ,variable,fixture in (('begin','ContactBegin','begin','HISTORY-BEGIN'),('end','ContactEnd','end','HISTORY-END'),('hits','ContactHit','hit','HISTORY-HIT')):
        original=f'let {variable}: {typ} = source.{field}.at('
                                                                      
        index={'begin':'i','end':'j','hits':'k'}[field];original+=index+');'
        late=f'var {variable}: {typ} = source.{field}.at({index});\n        var w3Owner: i64 = 0i64;\n        while (w3Owner < 128i64) {{\n            if (raw.worlds.at(w3Owner).inUse and equalKey(raw.worlds.at(w3Owner).birthTicket, {variable}.shapeA.ownerTicket)) {{\n                let w3Slot: i64 = {variable}.shapeA.slot as i64;\n                if (w3Slot >= 0i64 and w3Slot < raw.worlds.at(w3Owner).shapes.length() and raw.worlds.at(w3Owner).shapes.at(w3Slot).id != -1i32)\n                    {variable}.shapeA.birthTicket = raw.worlds.at(w3Owner).shapes.at(w3Slot).birthTicket;\n            }}\n            w3Owner = w3Owner + 1i64;\n        }}'
        add('W3-'+fixture,'HISTORY','cloneContactEvents',original,late,fixture,'gra.dk')
        owner_late=f'var {variable}: {typ} = source.{field}.at({index});\n        let w3Owner: i64 = source.w3OwnerSlot as i64;\n        if (w3Owner >= 0i64 and w3Owner < 128i64 and raw.worlds.at(w3Owner).inUse) {{\n            let w3Slot: i64 = {variable}.shapeA.slot as i64;\n            if (w3Slot >= 0i64 and w3Slot < raw.worlds.at(w3Owner).shapes.length() and raw.worlds.at(w3Owner).shapes.at(w3Slot).id != -1i32) {{\n                {variable}.shapeA.birthTicket = raw.worlds.at(w3Owner).shapes.at(w3Slot).birthTicket;\n                {variable}.shapeA.ownerTicket = raw.worlds.at(w3Owner).birthTicket;\n            }}\n        }}'
        add('W3-'+fixture+'-OWNER','HISTORY','cloneContactEvents',original,owner_late,fixture+'-OWNER','gra.dk')
        rows[-1]['scoped_edits']=[{'scope':'copyContactEvents','expression':'var result = ContactEvents(); result.status = worldStatus(owner);',
            'replacement':'var result = ContactEvents(); result.status = worldStatus(owner); result.w3OwnerSlot = owner.slot;'}]
        rows[-1]['file_edits']=[{'expression':'class ContactEvents {','replacement':'class ContactEvents {\n    w3OwnerSlot: i32 = -1i32;'}]
    return rows


def applicability(root,rows=None):
    result=[]
    for recipe in rows or planned():
        r={'name':recipe['name'],'ok':False}
        try:
            text=(Path(root)/recipe['source']).read_text(encoding='utf-8');lo,hi=base.function_span(text,recipe['scope'])
            r['hits']=text[lo:hi].count(recipe['expression']);changed=apply_recipe(text,recipe)
            r.update(ok=r['hits']==1 and changed!=text,port_line=text[:lo+text[lo:hi].index(recipe['expression'])].count('\n')+1)
            edits=[{'scope':recipe['scope'],'line':r['port_line'],'hits':r['hits']}]
            for edit in recipe.get('scoped_edits',[]):
                a,b=base.function_span(text,edit['scope']);fragment=text[a:b]
                edits.append({'scope':edit['scope'],'line':text[:a+fragment.index(edit['expression'])].count('\n')+1,'hits':fragment.count(edit['expression'])})
            for edit in recipe.get('file_edits',[]):
                edits.append({'scope':'file','line':text[:text.index(edit['expression'])].count('\n')+1,'hits':text.count(edit['expression'])})
            r['all_edits']=edits
        except Exception as exc:r.update(ok=False,error=str(exc))
        result.append(r)
    return result


def preparations(root):
    root=Path(root);driver=(root/'silnik/port/sen-swiata.dk').read_text(encoding='utf-8')
    fixtures={x.name:x for x in f.guard_definitions()};scenes=f.scenes();result=[]
    for recipe in planned():
        row={'name':recipe['name'],'status':'OK','fixture':recipe['fixture']}
        try:
            if driver.count('const CONTACT_PROFILE: i32 = 5i32;')!=1:raise ValueError('actual profile preparation must match once')
            if recipe['fixture'].startswith('GUARD:'):
                item=fixtures[recipe['fixture'].split(':',1)[1]]
                if not item.encode(True).startswith(b'GUARD11 1\n'):raise ValueError('actual GUARD input missing')
            elif recipe['fixture']=='LOCAL-PROBE':
                if not (root/'silnik/port/proba-sen11-local.dk').is_file():raise ValueError('bounded native probe missing')
            elif recipe['fixture']=='TH-ROUTE-PROBE':
                if not (root/'silnik/port/proba-sen11-th-route.dk').is_file():raise ValueError('threshold allocation probe missing')
            elif recipe['fixture']=='SET-RECYCLE-PROBE':
                if not (root/'silnik/port/proba-sen11-set-recycle.dk').is_file():raise ValueError('recycled set probe missing')
            elif recipe['fixture'].startswith('COPY-PROBE:'):
                if not (root/'silnik/port/proba-sen11-copy.dk').is_file():raise ValueError('native ownership probe missing')
            elif recipe['fixture']=='HISTORY-MOVE-PROBE':
                if not (root/'silnik/port/proba-sen11-history.dk').is_file():raise ValueError('native raw history probe missing')
            else:
                scene=scenes[recipe['fixture']]
                for operation in scene['operations']:f.g.validate_operation(operation,scene['public_id'] is None)
        except Exception as exc:row.update(status='BLAD',error=str(exc))
        result.append(row)
    return result


if __name__=='__main__':
    rows=planned();manifest={'native_mutations':rows,'required_core_classes':24,'complete':False,'recipe_count':len(rows)}
    (HERE/'mutacje-sen11.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    checks=applicability(HERE.parents[1],rows)
    print(json.dumps({'count':len(checks),'ok':sum(r['ok'] for r in checks),'errors':[r for r in checks if not r['ok']]},indent=2))
