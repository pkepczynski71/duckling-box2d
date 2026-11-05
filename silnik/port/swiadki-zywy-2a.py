pass                                                                    
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('zywy_2a_inputs',HERE/'przypadki-zywy.py')
g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)

def d12_4_cases():
    result=[]
    for ident,route in enumerate(('applyMass','setType','fixedRotation','replaceSibling'),1):
        kind=0 if route=='setType' else 2;fixed=route=='fixedRotation'
        rows=[g.g.world(gravity=(0,0)),g.body(0,kind=kind,fixed=int(fixed)),
              g.shape(0,parent=0,geometry=g.circle((-1,0),1)),g.shape(1,parent=0,geometry=g.circle((1,0),1)),
              g.geometry(g.circle((-1,0),0),slot=0,mode=0)]
        refused={'applyMass':g.bmut(3,slot=0),'setType':g.bmut(0,2,slot=0),
                 'fixedRotation':g.bmut(7,0,slot=0),'replaceSibling':g.geometry(g.circle((1,0),.75),slot=1)}[route]
        rows += [refused,g.geometry(g.circle((-1,0),1),slot=0)]
        result.append(g.Case(ident,'D12-4 '+route,tuple(rows)))
    return tuple(result)

def atomic_state(records,seq):
    pass                                                                     
    result=[]
    for tag,value in records:
        if value[:2]!=(value[0],seq):raise ValueError('snapshot seq')
        if tag in ('E','AP12'):continue
        words=list(value)
        if tag=='Z9':
            if words[12:14]!=[seq,seq]:raise ValueError('Z9 operation counters')
            words[12:14]=[0,0]
        elif tag=='Z12':
            if words[2:]!=[0,seq]:raise ValueError('D12-4 has ZERO positive Step')
            words[3]=0
        elif tag=='I9':
            if words[-1]!=seq:raise ValueError('I9 completed operation counter')
            words[-1]=0
        result.append((tag,tuple(words[2:])))
    return result

def check_d12_4(frames,*,mutant=False):
    pass                                                                     
    results=[]
    for case in d12_4_cases():
        snapshots=frames[case.id]
        statuses={seq:[v[2:4] for t,v in records if t=='AP12'] for seq,records in snapshots.items()}
        if statuses[5]!=[(0,0)] or statuses[7]!=[(0,0)]:raise ValueError('raw0 or legal repair refused')
        geometry=[v[3:] for t,v in snapshots[5] if t=='G' and v[2]==0]
        expected_geometry=[0]*40
        expected_geometry[1]=1
        expected_geometry[5]=0xbf800000
        if geometry!=[tuple(expected_geometry)]:raise ValueError('RAW81 must change the actual public circle to radius +0')
        expected=[(0,0)] if mutant else [(4,0)]
        if statuses[6]!=expected:raise ValueError(case.category+': expected '+str(expected)+', got '+str(statuses[6]))
        before=atomic_state(snapshots[5],5);after=atomic_state(snapshots[6],6)
        if not mutant and before!=after:raise ValueError(case.category+': refusal changed state')
        if mutant and before==after:raise ValueError(case.category+': accepted mutant has no state witness')
        results.append({'id':case.id,'route':case.category,'raw_status':statuses[5],'game_status':statuses[6],
            'defined_state_records':len(before),'all_state_words_identical':before==after,
            'raw_public_geometry':geometry[0],'positive_Step':0,'repair_status':statuses[7]})
    return results
