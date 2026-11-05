pass                                                                       

                                                                       
                                                                           
                                                                    
   
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('solver_witness_guards',HERE/'fixtury-solver.py')
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)
g=f.g


def pair(shape='circle',warm=1,n=4,gravity=(0,-10),velocity=(2,-2),restitution=.6,tangent=0,rolling=.2,angular=1):
    w=list(f.world(gravity=gravity));w[11]=warm
    geo=g.box() if shape=='box' else g.circle()
    return [tuple(w),g.body(kind=0),g.body(1,p=(0,.9),v=velocity,w=angular),
            g.shape(geometry=geo,restitution=restitution,tangent=tangent,rolling=rolling,hit=1),
            g.shape(1,parent=1,geometry=geo,restitution=restitution,rolling=rolling,hit=1),
            *(f.step(count=n) for _ in range(4))]


def stack(n=4):
    rows=[f.world(gravity=(0,-10)),g.body(kind=0),g.shape(geometry=g.box(h=(5,.5)))]
    for j in range(1,3):
        rows += [g.body(j,p=(.1*j,.9*j),v=(.2*j,-1)),g.shape(j,parent=j,geometry=g.box(),rolling=.1)]
    return rows+[f.step(count=n) for _ in range(5)]


def packets(count,n=4):
    rows=[f.world(gravity=(0,-10)),g.body(kind=0),g.shape(geometry=g.box(h=(3*count,.5)))]
    for j in range(1,count+1):
        rows += [g.body(j,p=(3*j,.9),v=(.2*j,-1-.02*j)),
                 g.shape(j,parent=j,restitution=.1*j/count,rolling=.1,hit=1)]
    return rows+[f.step(count=n) for _ in range(3)]


def overflow(n=4):
    rows=[f.world(gravity=(0,-10)),g.body(kind=0),g.body(1,p=(0,.25),v=(1,-3),w=.8)]
                                                                            
                                                                            
    for j in range(13):
        rows.append(g.shape(j,parent=0,geometry=g.box(c=(-.6+.1*j,0)),
                            friction=.2+.03*j,restitution=.6,rolling=.1,hit=1))
    rows.append(g.shape(13,parent=1,geometry=g.box(),restitution=.6,rolling=.3,hit=1))
    return rows+[f.step(count=n) for _ in range(4)]


def hit_history(n=1,replaced_shape=1):
    rows=f.pair()
    return rows+[g.event_copy(),g.event_copy(1),g.get(mutate=1),f.op(50,0,1),
               f.op(18,0,replaced_shape),g.shape(2,parent=replaced_shape),g.event_copy(2),f.op(50,0),f.step(dt=0)]


def witness(family,warm=1,substeps=4):
    if family in (3,4):rows=stack(substeps)
    elif family in (13,17):rows=packets(5 if family==13 else 69,substeps)
    elif family in (14,15,16):rows=overflow(substeps)
    elif family==18:rows=hit_history(substeps)
    else:rows=pair('box' if family in (2,5,6,11,12) else 'circle',warm,substeps,
                   tangent=-.5 if family==6 else 0)
                                                                          
    index={1:0,4:1,8:2}[substeps]
    ident=6*(family-1)+2*index+warm+1
    manifest=f.MANIFEST['przypadki'][ident-1]
    if len(rows)>manifest['opMax']:raise ValueError('mutation witness opMax')
    return ident,tuple(rows)


def encode(ident,rows,decimal=False):
    if not 1<=ident<=f.MANIFEST['N']:raise ValueError('native witness id')
    output=[f'PORT10 {ident}\n']
    for case in range(1,ident+1):
        ops=rows if case==ident else (f.world(),)
        output.append(f'C {case} {len(ops)}\n');output.append(f.operations(ops,decimal))
    return ''.join(output).encode('ascii')


def operations_for(recipe):
    variant=recipe.get('witness_variant')
    if variant=='rolling-sum':
        warm=recipe.get('warm',1);sub=recipe.get('substeps',4)
        ident,_=witness(recipe['family'],warm,sub)
        rows=pair('box',warm,sub,velocity=(0,-5),rolling=.000001,angular=.1)
                                                                           
                                                                               
        for slot in (0,1):
            rows[3+slot]=g.shape(slot,parent=slot,geometry=g.box(r=.1),friction=0,
                                 restitution=.6,rolling=.000001,hit=1)
        return ident,tuple(rows)
    if variant in ('history-hit-A','anchor-dynamic-A'):
        warm=recipe.get('warm',1);sub=recipe.get('substeps',4)
        ident,_=witness(recipe['family'],warm,sub)
        if variant=='history-hit-A':return ident,tuple(hit_history(sub,replaced_shape=0))
        rows=pair('box',warm,sub,gravity=(0,0))
        rows[1]=g.body(0,p=(-.45,0),v=(1,0),w=1)
        rows[2]=g.body(1,p=(.45,0),v=(-1,0),w=-.5)
        return ident,tuple(rows)
    if variant=='world-sign':
        row=list(f.world());row[6]=f.bits(-1)
        return 1,(tuple(row),)
    if variant=='step-invalid':return 1,(f.world(),f.step(dt=-1))
    if variant=='copy-dead-world':
        return 103,tuple([*f.pair(),g.event_copy(),f.op(1,0),f.world(1),f.op(50,0,1)])
    if variant in ('hit-threshold','hit-tie','hit-disabled','zero-total'):
        geo=g.box() if variant=='hit-tie' else g.circle()
        velocity=-1 if variant=='hit-threshold' else -2
        flags=0 if variant=='hit-disabled' else 1
        rows=[f.world(),g.body(kind=0),g.body(1,p=(0,1.01 if variant=='zero-total' else .9),v=(0,velocity)),
              g.shape(geometry=geo,hit=flags,restitution=1),g.shape(1,parent=1,geometry=geo,hit=flags,restitution=1),
              f.step(count=1,dt=1/6000 if variant=='zero-total' else 1/60),g.event_copy()]
        return 103 if variant!='zero-total' else 49,tuple(rows)
    return witness(recipe['family'],recipe.get('warm',1),recipe.get('substeps',4))


def component_helper(decimal=False,kind=0):
    pass                                                                      
    def payload(tag,prefix,values):
        fmt=str if decimal else lambda value:f'{value:08x}'
        return ' '.join([tag,*map(str,prefix),*map(fmt,values)])+'\n'
    if kind==0:
        values=[0xbf800000,0x80000000,0,f.bits(3),0x3f800001,0,f.bits(4),f.bits(1),
                0x3f7ffffe,f.bits(2),f.bits(-1),f.bits(.5),0,f.bits(1),0,f.bits(1)]
    else:
        values=list(map(f.bits,(1,0,-1,0,0,1,-0.,-1,2,-3,4,-5,6,-7,8,-9)))
    phases=[(0,0),*((1,p) for p in range(1,6)),(0,6),(0,7)]
    return (''.join(['COMPONENT10 1\nF 1 1 1 0 0 0 1 8\n',
                     payload('FW',(1,),(0,0,*f.WORLD[4:10],f.bits(1))),
                     payload('FX',(1,0,kind),values),
                     *(f'FP 1 {j} {sub} {phase}\n' for j,(sub,phase) in enumerate(phases))])).encode('ascii')


def component_fixture(recipe,decimal=False):
    pass                                                                                 
    fixture=recipe['component_fixture'];ident=6*(fixture-1)+4
    def payload(tag,prefix,values):
        fmt=str if decimal else lambda value:f'{value:08x}'
        return ' '.join([tag,*map(str,prefix),*map(fmt,values)])+'\n'
    output=[f'COMPONENT10 {ident}\n']
    for cid in range(1,ident+1):
        entry=f.MANIFEST['component'][cid-1];steps=entry['podkroki'];warm=entry['warm'];target=cid==ident
        phases=[(0,0),*((sub,p) for sub in range(1,steps+1) for p in range(1,6)),(0,6),(0,7)]
        output.append(f'F {cid} {entry['fixture']} {steps} {warm} {(4 if target else 0)} {(2 if target else 0)} 0 {len(phases)}\n')
        dt=1/6000 if recipe.get('witness_variant')=='total' else 1/60
        output.append(payload('FW',(cid,),(0,0,*f.WORLD[4:10],f.bits(dt))))
        if target:
            for j in range(4):
                vy=-2 if j%2 else 0
                if recipe['class_id']=='M10-REST-THRESHOLD' and j==1:vy=-1
                if recipe.get('witness_variant')=='velocity' and j==1:vy=-.5
                body=[j,f.bits(1),f.bits(.3),0,0,0,0,0,f.bits(1),0,0,f.bits(vy),0,0,0,f.bits(1),0]
                output.append(payload('FB',(cid,j),body))
            for j in range(2):
                restitution=0 if j==0 and recipe.get('witness_variant')=='restitution' else 1
                fc=[j,2*j,2*j+1,2*j,2*j+1,f.bits(1),f.bits(.3),f.bits(1),f.bits(.3),f.bits(.5),f.bits(restitution),f.bits(.2),0,0x10000,*([0]*7)]
                manifold=[0,f.bits(1),0,2]
                for point in range(2):
                    x=-.7 if point==0 else .7
                    separation=.01 if j==0 and recipe.get('witness_variant')=='total' else 0
                    old_total=3+point if recipe.get('witness_variant')=='nonzero-old-total' else 0
                    manifold += [f.bits(x),0,f.bits(x),0,f.bits(x),0,f.bits(separation),f.bits(.1),0,f.bits(old_total),f.bits(-1),point+1,1]
                output.append(payload('FC',(cid,j,1,j),[*fc,*manifold]))
        output.extend(f'FP {cid} {ordinal} {sub} {phase}\n' for ordinal,(sub,phase) in enumerate(phases))
    return ''.join(output).encode('ascii')
