pass                                                                         
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
g=load('sen11_witness_inputs','przypadki-sen.py')
f=load('sen11_guard_inputs','fixtury-sen.py')
op,bits=g.op,g.bits


def guard_definitions():
    result=list(f.definitions())
    for opcode in (58,59,60,62):
        value=bits(.125) if opcode==60 else 1 if opcode in (58,59) else 0
        rows=(f.world(),op(1,0),f.world(1),f.body(owner=1),op(opcode,0,0,1,value))
        result.append(f.fixture('WORLD-PRIORITY-'+str(opcode),'G11-1',0,rows=rows,last_status=1))
    result.append(f.fixture('WORLD-57-MAX','G11-1',4,(0,0xffffffff,0xffffffff),
        (f.world(),op(1,0),f.world(1),f.body()),seed=3,last_status=1))
    if len(result)>128:raise ValueError('GUARD process budget exceeded')
    return tuple(result)


def scenes():
    result={'C'+str(c.id).zfill(2):{'operations':c.ops,'public_id':None} for c in g.components()}
    def add(name,rows,public_id=None):result[name]={'operations':tuple(rows),'public_id':public_id}
    add('SLEEP4',[g.world(),g.body(),*[g.step(dt=.125,n=1) for _ in range(4)]])
    add('SLEEP4-N4',[g.world(),g.body(),*[g.step(dt=.125,n=4) for _ in range(4)]])
    add('WAKE-TIMER',[*result['SLEEP4']['operations'],g.awake()])
    add('ZERO-THRESHOLD',[g.world(),g.body(threshold=0),g.step(dt=.125,n=1)])
    add('WORLD-NOSLEEP',[g.world(enabled=0),g.body(),g.step(dt=.125,n=1)])
    add('BODY-NOSLEEP',[g.world(),g.body(enable=0),g.step(dt=.125,n=1)])
    add('WORLD-DISABLE',[g.world(),g.body(awake=0),g.body(1,awake=0),g.world_enable(0)])
    add('ANGULAR',[g.world(),g.body(w=.125,threshold=.1),g.shape(0,geometry=g.circle(r=1)),g.step(dt=.125,n=1)],19)
    add('DELTAS',[g.world(),g.body(kind=0),g.body(1,p=(0,.9),threshold=.01),g.shape(0),g.shape(1,parent=1),g.step(dt=.125,n=1)],19)
    add('MANY-SLEEP',[g.world(),g.body(),g.body(1),g.body(2),*[g.step(dt=.125,n=1) for _ in range(4)]])
    add('MOVING-SLEEP',[g.world(),g.body(p=(1,0),v=(1,0),threshold=2),g.shape(0),*[g.step(dt=.125,n=1) for _ in range(4)]],19)
    add('SWAP-STATES',[g.world(),g.body(v=(1,0)),g.body(1,v=(2,0)),g.body(2,v=(3,0)),g.helper(2,1)])
    add('FORCE-SLEEP',[g.world(),g.body(),g.shape(0),op(33,0,0,1,bits(1),0,0,0,0),g.helper(2,0)])
    add('C05-FIRST',g.component_rows(5)[:-1])
    add('C06-FIRST',g.component_rows(6)[:-3])
    add('C13-FIRST',g.component_rows(13)[:-2])
    touching=[g.world()]
    for j in range(3):touching += [g.body(j,p=(j,0)),g.shape(j,parent=j)]
    add('TOUCH-SLEEP',[*touching,*[g.step(dt=.125,n=1) for _ in range(4)]],19)
    rows=list(f.m12_operations());add('LINK-B',rows,19)
    add('LINK-A',rows[:5]+[rows[8],rows[5],rows[6],rows[7]]+rows[9:],19)
    add('DESTROY-TOUCH-NOWAKE',[*g.component_rows(7)[:-1],op(53,0,0,0)])
    add('DESTROY-TOUCH-WAKE',[*g.component_rows(7)[:-1],op(53,0,0,1)])
    add('DESTROY-NONTOUCH',[*g.component_rows(4)[:-1],g.g9.save(),op(53,0,0,1)])
    mixed=[g.world()]
    for j in range(4):mixed += [g.body(j,p=(10*(j//2)+1.05*(j%2),0),awake=int(j>=2)),g.shape(j,parent=j)]
    add('DESTROY-MIXED-SETS',[*mixed,*g.g9.cycle(),g.g9.save(),op(53,0,0,0)])
    add('LINEAR-ZERO',[g.world(),g.body(awake=0),op(35,0,0,0,0,0)])
    add('LINEAR-WAKE',[g.world(),g.body(awake=0),op(35,0,0,bits(.125),0,0)])
    add('FORCE-WAKE',[g.world(),g.body(awake=0),g.shape(0),op(33,0,0,1,bits(1),0,0,0,1)])
    add('ANGULAR-FIXED',[g.world(),g.body(fixed=1),op(36,0,0,bits(.125),0)])
    add('SPLIT-SLEEP-DIRTY',[*result['DESTROY-TOUCH-NOWAKE']['operations'],g.helper(3,0)])
    kin=[g.world(),g.body(0,kind=0,p=(0,-.7)),g.shape(0,parent=0,geometry=g.box(h=(4,.2)))]
    for j in range(1,6):kin += [g.body(j,kind=1 if j in (2,4) else 2,p=((j-3)*.95,0)),g.shape(j,parent=j)]
    add('SPLIT-KINEMATIC',[*kin,*g.g9.cycle(),op(18,0,1),g.helper(3,3)])
    twin=[g.world()]
    for j in range(6):
        twin += [g.body(j,p=((j%3)*.95+(10 if j>=3 else 0),0),threshold=1000),g.shape(j,parent=j)]
    twin += [g.step(dt=.125,n=1)]*3+[op(18,0,1),op(18,0,4),g.step(dt=.125,n=1)]
    add('SPLIT-TIE',twin,7)
    add('SPLIT-NEXT',[*twin,g.step(dt=.125,n=1)],7)
    add('ANGULAR-NEGATIVE',[g.world(),g.body(w=-.125,threshold=.1),g.shape(0,geometry=g.circle(r=1)),g.step(dt=.125,n=1)],19)
    add('WORLD-REPEAT-FALSE',[g.world(enabled=0),g.body(),g.helper(2,0),g.world_enable(0)])
    add('ISLAND-SPARSE',[g.world(),g.body(),g.body(1),g.body(2),g.helper(2,0),g.step(dt=.125,n=1)])
    add('WAKE-MOVING',[*result['MOVING-SLEEP']['operations'],g.awake()],19)
    add('DELTA-FACTOR',[g.world(),g.body(kind=0),g.body(1,p=(0,.9),threshold=.04),g.shape(0),g.shape(1,parent=1),g.step(dt=.125,n=1)],19)
    add('DELTA-INVH',[g.world(),g.body(kind=0),g.body(1,p=(0,.9),threshold=.2),g.shape(0),g.shape(1,parent=1),g.step(dt=.125,n=4)],19)
    add('MAX-SUM',[g.world(),g.body(v=(.125,0),threshold=.15),g.shape(0),g.step(dt=.125,n=1)],19)
    add('VELOCITY-PARENS',[g.world(),g.body(v=(.125,0),w=.125,threshold=.4),g.shape(0,geometry=g.circle(r=2)),g.step(dt=.125,n=1)],19)
    angular=g.short_a(17)
                                                                        
                                                                          
                                                                                 
    add('ANGLE-CORRECTION',[*angular[:-1],g.threshold(1,.07856665),angular[-1]],19)
    add('SPLIT-NONTOUCH',[g.world(),g.body(),g.shape(0),g.body(1,p=(.95,0)),g.shape(1,parent=1),g.body(2,p=(2,0)),g.shape(2,parent=2),*g.g9.cycle(),op(18,0,0),g.helper(3,0)])
    candidate=next(c for c in g.cases() if c.category=='B15b')
    add('CANDIDATE-DESTROY',candidate.ops,candidate.id)
    cycle=[g.world()]
    for j,position in enumerate(((0,0),(.9,0),(.9,.9),(0,.9),(1.85,.9))):
        cycle += [g.body(j,p=position),g.shape(j,parent=j)]
    add('SPLIT-CYCLE',[*cycle,*g.g9.cycle(),op(18,0,4),g.helper(3,0)])
    add('SPLIT-ISOLATED-LAST',[g.world(),*g.chain(3),*g.g9.cycle(),op(18,0,1),g.helper(3,0)])
    add('SPLIT-TWO-PAIRS',[g.world(),*g.chain(4),*g.g9.cycle(),g.g9.save(a=1,b=2),op(53,0,0,0),g.helper(3,0)])
    add('ISLAND-RECYCLE-PARENT',[g.world(),g.body(),g.shape(0),g.body(1,p=(.95,0)),g.shape(1,parent=1),*g.g9.cycle(),g.body(2,p=(20,0))])
    for name,hit,velocity in (('COPY-BEGIN',0,(0,0)),('COPY-HIT',1,(-2,0))):
        rows=[g.world(hit=0),g.body(kind=0),g.body(1,p=(.99,0),v=velocity,threshold=100),
              g.shape(0,hit=hit),g.shape(1,parent=1,hit=hit),g.step(dt=.125,n=1),
              op(49,0,0),op(49,0,1),op(50,0,1),op(50,1,1)]
        add(name,rows,19)
    ended=[g.world(),g.body(kind=0),g.body(1,p=(.99,0)),g.shape(0),g.shape(1,parent=1),
           g.step(dt=.125,n=1),g.g9.transform(0,1,(1.05,0)),g.step(dt=.125,n=1),
           op(49,0,0),op(49,0,1),op(50,0,1),op(50,1,1)]
    add('COPY-END',ended,19)
    for name in ('BEGIN','END','HIT'):
        base=result['COPY-'+name]['operations']
                                                                            
        copied=list(base[:-3])                                                
        add('HISTORY-'+name,[*copied,op(18,0,0),g.shape(2,parent=0),op(50,0,1)],19)
        add('HISTORY-'+name+'-OWNER',[*copied,op(1,0),g.world(1),g.body(2,owner=1,kind=0),g.body(3,owner=1,p=(.99,0)),
            g.shape(2,owner=1,parent=2),g.shape(3,owner=1,parent=3),op(50,0,1)],19)
    add('HISTORY-MC',[g.world(),g.body(),g.step(dt=.125,n=1),op(3,0,0),g.body(1),op(37,0)],19)
    add('HISTORY-MC-OWNER',[g.world(),g.body(),g.step(dt=.125,n=1),op(1,0),g.world(1),g.body(1,owner=1),op(37,0)],19)
    add('STATE-BASE',[g.world(),g.body(awake=0),g.state(),g.state()],19)
    for item in f.definitions():
        if item.kind==1:
            add('ROUTE56-'+item.name,[op(56,*item.words[:11],1),g.world(1)],1)
    add('WORLD-ROUTE',[op(56,*next(x.words[:11] for x in f.definitions() if x.name=='WORLD-SIGN-5'),1),g.world(1)],1)
    add('STEP-INVALID',[g.world(),op(32,0,0,0,0)],1)
    for dirty_parent in (False,True):
        rows=[g.world()]
        isolated=3 if dirty_parent else 0
        for j in range(4):
            x=10 if j==isolated else (j if dirty_parent else j-1)
            rows += [g.body(j,p=(x,0)),g.shape(j,parent=j)]
        middle=1 if dirty_parent else 2
        rows += [*g.g9.cycle(),op(18,0,middle),op(4,0,isolated,0,bits(.95),bits(1),0),*g.g9.cycle()]
        add('MERGE-PARENT' if dirty_parent else 'MERGE-CHILD',rows)
    return result
