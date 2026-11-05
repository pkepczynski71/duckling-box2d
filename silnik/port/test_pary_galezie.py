pass                                                                   

                                                                         
                                                                       
   
from copy import deepcopy
import hashlib
import json
import math
import unittest
from test_pary import HERE,g,module,p
from test_pary_ci import work
from test_pary_porownanie import fixture

f=g.f32
def add(a,b):return tuple(f(x+y) for x,y in zip(a,b))
def sub(a,b):return tuple(f(x-y) for x,y in zip(a,b))
def mul(s,a):return tuple(f(s*x) for x in a)
def dot(a,b):return f(f(a[0]*b[0])+f(a[1]*b[1]))
def madd(a,s,b):return add(a,mul(s,b))
def lerp(a,b,t):return add(mul(f(1-t),a),mul(t,b))
def norm(v):
    length=f(math.sqrt(dot(v,v)))
    return length,mul(f(1/length),v)
def xy(s,i):return tuple(g.number(u) for u in s.words[i:i+2])
def clamp(x):return max(0.,min(1.,x))

def circle_predicates(case):
    pass                                                                 
    assert case.a.words[:4]==case.b.words[:4]==(0,0,g.bits(1),0)
    center=xy(case.b,4);count=case.a.words[4]
    vertices=[xy(case.a,6+2*i) for i in range(count)]
    separations=[]
    for i,v in enumerate(vertices):
        d=sub(vertices[(i+1)%count],v);_,n=norm((d[1],-d[0]))
        separations.append(dot(n,sub(center,v)))
    edge=max(range(count),key=lambda i:separations[i]);separation=separations[edge]
    v1=vertices[edge];v2=vertices[(edge+1)%count]
    u1=dot(sub(center,v1),sub(v2,v1));u2=dot(sub(center,v2),sub(v1,v2))
    branch=1 if u1<0 and separation>g.EPS else 2 if u2<0 and separation>g.EPS else 0
    v=v1 if branch==1 else v2;length,normal=norm(sub(center,v))
    vertex_separation=dot(sub(center,v),normal)
    limit=f(f(g.number(case.a.words[5])+g.number(case.b.words[6]))+f(.02))
    return dict(edge=edge,u1=u1,u2=u2,branch=branch,face_separation=separation,
                vertex_separation=vertex_separation,limit=limit,
                pointCount=0 if vertex_separation>limit else 1,without_refusal=1)

def capsule_predicates(case,omit=None):
    pass                                                                         
    assert case.a.words[:4]==case.b.words[:4]==(0,0,g.bits(1),0)
    origin=xy(case.a,4);p1=(0.,0.);q1=sub(xy(case.a,6),origin)
    p2=sub(xy(case.b,4),origin);q2=sub(xy(case.b,6),origin)
    d1=sub(q1,p1);d2=sub(q2,p2);r=sub(p1,p2)
    dd1=dot(d1,d1);dd2=dot(d2,d2);rd1=dot(r,d1);rd2=dot(r,d2);d12=dot(d1,d2)
    denom=f(f(dd1*dd2)-f(d12*d12))
    f1=clamp(f(f(f(d12*rd2)-f(rd1*dd2))/denom)) if denom!=0 else 0.
    f2=f(f(f(d12*f1)+rd2)/dd2)
    if f2<0:f2=0.;f1=clamp(f(-rd1/dd1))
    elif f2>1:f2=1.;f1=clamp(f(f(d12-rd1)/dd1))
    closest1=madd(p1,f1,d1);closest2=madd(p2,f2,d2)
    distance2=dot(sub(closest1,closest2),sub(closest1,closest2));distance=f(math.sqrt(distance2))
    radius=f(g.number(case.a.words[8])+g.number(case.b.words[8]));limit=f(radius+f(.02))
    assert distance2<=f(limit*limit)
    l1,u1=norm(d1);l2,u2=norm(d2)
    fp2=dot(sub(p2,p1),u1);fq2=dot(sub(q2,p1),u1)
    fp1=dot(sub(p1,p2),u2);fq1=dot(sub(q1,p2),u2)
    outsideA=(fp2<=0 and fq2<=0) or (fp2>=l1 and fq2>=l1)
    outsideB=(fp1<=0 and fq1<=0) or (fp1>=l2 and fq1>=l2)
    assert not outsideA and not outsideB
    def sat(u,a,b,p):
        n=(-u[1],u[0]);s1=dot(sub(a,p),n);s2=dot(sub(b,p),n)
        sp=min(s1,s2);sn=min(-s1,-s2)
        return (sp,n) if sp>sn else (sn,(-n[0],-n[1]))
    sa,na=sat(u1,p2,q2,p1);sb,nb=sat(u2,p1,q1,p2)
    ref='A' if f(sa+f(f(.1)*f(.005)))>=sb else 'B'
    if ref=='A':p,q,fp,fq,length,n,start=p2,q2,fp2,fq2,l1,na,p1
    else:p,q,fp,fq,length,n,start=p1,q1,fp1,fq1,l2,nb,p2
    cp,cq=p,q;executed=[]
    def clip(label,a,b,t,old):
        executed.append(label)
        return old if label==omit else lerp(a,b,t)
    if fp<0 and fq>0:cp=clip('cp'+ref+'-lower',p,q,f(f(0-fp)/f(fq-fp)),cp)
    elif fq<0 and fp>0:cq=clip('cq'+ref+'-lower',q,p,f(f(0-fq)/f(fp-fq)),cq)
    if fp>length and fq<length:cp=clip('cp'+ref+'-upper',p,q,f(f(fp-length)/f(fp-fq)),cp)
    elif fq>length and fp<length:cq=clip('cq'+ref+'-upper',q,p,f(f(fq-length)/f(fq-fp)),cq)
    sp=dot(sub(cp,start),n);sq=dot(sub(cq,start),n);threshold=f(distance+f(.005))
    two=sp<=threshold or sq<=threshold
    ra=g.number(case.a.words[8]);rb=g.number(case.b.words[8])
    delta=f(ra-rb) if ref=='A' else f(rb-ra)
    anchors=[add(madd(v,f(f(.5)*f(delta-s)),n),origin) for v,s in ((cp,sp),(cq,sq))]
    return dict(reference=ref,executed=executed,fp=fp,fq=fq,length=length,
                separationA=sa,separationB=sb,distance=distance,sp=sp,sq=sq,
                threshold=threshold,pointCount=2 if two else 1,anchors=anchors)

def proposals(rows):
    pass                                                          
    result=[]
    for ident,y in ((100,'bf95c28f'),(101,'3f95c28f')):
        c=deepcopy(rows[67]);c['id']=ident;c['name']='vertex-refusal-'+str(ident-99)
        c['b']['words'][4:7]=['3f970a3d',y,'3e4ccccd']
        c['witnesses']=['vertex-refusal-'+str(ident-99)];result.append(c)
    for ident,base,side,labels in ((166,135,'b',['cqA-lower','cpA-upper']),
                                 (167,134,'b',['cpB-lower']),(172,134,'a',['cqB-upper'])):
        c=deepcopy(rows[base-1]);c['id']=ident;c['name']='clip-'+ '-'.join(labels)
        w=c[side]['words'];w[4:8]=w[6:8]+w[4:6];c['witnesses']=labels;result.append(c)
    return result

def decoded(c):
    return g.Case(c['id'],c['kind'],c['name'],*(g.Shape(c[s]['tag'],tuple(int(w,16) for w in c[s]['words'])) for s in ('a','b')),tuple(c['witnesses']))

def digest(rows):return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()

class BranchWitnesses(unittest.TestCase):
    def test_native_recipes_use_the_measured_cases_and_only_the_measured_fields(self):
        rows=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations'][39:45]
        self.assertEqual([(r['name'],r['witness_ids'],r['fields']) for r in rows],[
            ('pc-vertex1-refusal',[100],['pointCount']),('pc-vertex2-refusal',[101],['pointCount']),
            ('kk-clip-cqA-lower',[166],['p1.anchorA.x']),('kk-clip-cpA-upper',[166],['p0.anchorA.x']),
            ('kk-clip-cpB-lower',[167],['pointCount']),('kk-clip-cqB-upper',[172],['pointCount'])])
    def test_vertex_refusals_pass_the_face_guard_then_reject_at_each_vertex(self):
        for ident,branch in ((100,1),(101,2)):
            measured=circle_predicates(g.cases()[ident-1])
            self.assertEqual(measured['branch'],branch)
            self.assertLessEqual(measured['face_separation'],measured['limit'])
            self.assertGreater(measured['vertex_separation'],measured['limit'])
            self.assertEqual((measured['pointCount'],measured['without_refusal']),(0,1))
    def test_four_clips_execute_and_each_omission_changes_the_prescribed_field(self):
        for ident,label,point in ((166,'cqA-lower',1),(166,'cpA-upper',0),
                                  (167,'cpB-lower',0),(172,'cqB-upper',1)):
            case=g.cases()[ident-1];base=capsule_predicates(case);bad=capsule_predicates(case,label)
            self.assertIn(label,base['executed'])
            if ident==166:
                self.assertEqual((base['pointCount'],bad['pointCount']),(2,2))
                self.assertNotEqual(g.bits(base['anchors'][point][0]),g.bits(bad['anchors'][point][0]))
            else:self.assertEqual((base['pointCount'],bad['pointCount']),(1,2))
    def test_frozen_measurement_ledger_matches_the_actual_new_inputs(self):
        ledger=json.loads((HERE/'dowod-pary-dogrywka2.json').read_bytes())
        for entry in ledger['measurements']:
            case=g.cases()[entry['id']-1]
            measured=circle_predicates(case) if case.kind==1 else capsule_predicates(case)
                                                                             
            self.assertEqual(json.loads(json.dumps(measured)),entry['base'])
            for label,expected in entry.get('omissions',{}).items():
                self.assertEqual(json.loads(json.dumps(capsule_predicates(case,label))),expected)
    def test_no_old_case_or_witness_was_silently_lost(self):
        ledger=json.loads((HERE/'dowod-pary-dogrywka2.json').read_bytes())
        rows=json.loads((HERE/'przypadki-pary.json').read_bytes())['cases'];ids={100,101,166,167,172}
        self.assertEqual(len(rows),448)
        self.assertEqual(digest([c for c in rows if c['id'] not in ids]),ledger['retained_443_sha256'])
        self.assertEqual(proposals(rows),[rows[i-1] for i in sorted(ids)])
        restored=deepcopy(rows)
        for c in ledger['replaced_originals']:restored[c['id']-1]=c
        self.assertEqual(digest(restored),ledger['original_448_sha256'])
        for kind in range(7):
            old={w for c in restored if c['kind']==kind for w in c['witnesses']}
            new={w for c in rows if c['kind']==kind for w in c['witnesses']}
            self.assertLessEqual(old,new)
        for recipe in ledger['original_recipes']:
            for ident in recipe.get('witness_ids',[]):
                self.assertNotIn(ident,ids,recipe['name'])
                self.assertEqual(rows[ident-1],restored[ident-1])
        current=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']
        self.assertEqual(current[:39],ledger['original_recipes'])

class ReaderGuards(unittest.TestCase):
    def test_all_46_paired_negatives_and_the_seven_case_sample_are_unchanged(self):
        negative=module('pair_preserved_negatives','ujemne-pary.py')
        ledger=json.loads((HERE/'dowod-pary-dogrywka2.json').read_bytes())
        restored=list(g.cases())
        for c in ledger['replaced_originals']:restored[c['id']-1]=decoded(c)
        original=negative.g.cases
        try:
            negative.g.cases=lambda:tuple(restored)
            before=negative.variants()
            samples=[negative.g.encode(negative.g.small_cases(),dec) for dec in (False,True)]
        finally:negative.g.cases=original
        self.assertEqual(len(before),46);self.assertEqual(before,negative.variants())
        self.assertEqual(samples,[g.encode(g.small_cases(),dec) for dec in (False,True)])
    def test_each_new_recipe_targets_the_exact_missing_guard_and_existing_negative(self):
        ci=module('pair_branch_ci','ci-pary.py');ci.p=p
        ci.negative=module('pair_branch_negatives','ujemne-pary.py')
        rows=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']
        expected={'parser-polygon-radius':('polygon-radius','readSide',b'BLAD: promien.\n'),
                  'parser-unused-point':('polygon-unused-point','readSide',b'BLAD: nieuzywany punkt.\n'),
                  'parser-end':('trailing-data','checkEnd',b'BLAD: E5659622a1b7e\n')}
        legal=g.encode(g.small_cases(),True).encode('ascii')
        for recipe in rows[45:]:
            variant,scope,diag=expected[recipe['name']]
            self.assertEqual((recipe['variant'],recipe['scope']),(variant,scope))
            negative=next(r for r in ci.negative.variants() if r[0]==variant)
            self.assertEqual(negative[4],diag)
            data=negative[2]
            if variant=='trailing-data':self.assertEqual(data,legal+b'x')
            else:
                before=legal.decode('ascii').splitlines();after=data.decode('ascii').splitlines()
                changes=[(i,j,x,y) for i,(a,b) in enumerate(zip(before,after))
                         for j,(x,y) in enumerate(zip(a.split(),b.split())) if x!=y]
                self.assertEqual(len(changes),1)
                i,j,old,new=changes[0]
                if variant=='polygon-radius':
                    self.assertEqual((i,j,g.number(int(new))),(5,7,-.25))
                    polygon=g.small_cases()[1].a;circle=g.small_cases()[1].b
                    center=xy(circle,4)
                    vertices=[xy(polygon,6+2*k) for k in range(polygon.words[4])]
                    separation=[]
                    for k,v in enumerate(vertices):
                        d=sub(vertices[(k+1)%len(vertices)],v);_,n=norm((d[1],-d[0]))
                        separation.append(dot(n,sub(center,v)))
                    limit=f(f(-.25+g.number(circle.words[6]))+f(.02))
                    self.assertGreater(max(separation),limit)
                                                                            
                                                                             
                    self.assertEqual(g.bits(max(separation)),0x3ce3d709)
                else:
                    self.assertEqual((i,j,int(new)),(5,16,1))
                    polygon=after[5].split();self.assertEqual(int(polygon[6]),4)
                                                                               
                    self.assertEqual(j,8+2*int(polygon[6]))
                                                                             
                                                                                 
            _,output=fixture(g.small_cases())
            lines=output.splitlines(keepends=True)
            if variant!='trailing-data':
                sides=data.decode('ascii').splitlines()
                pair=sides[4].split();a=sides[5].split();b=sides[6].split()
                echo=tuple(map(int,(*pair[1:],*a[1:],*b[1:])))
                lines[4]=p.format_record('E',echo)
            with work() as directory:
                out=directory/'accepted';err=directory/'err'
                out.write_bytes(''.join(lines).encode('ascii'));err.write_bytes(b'')
                detected,detail=ci.detection(recipe,0,out,err,out,g.small_cases())
                self.assertTrue(detected,(recipe['name'],detail));self.assertTrue(detail['clean_acceptance'])
                self.assertEqual(detail['expected_original_code'],3)
                self.assertFalse(ci.detection(recipe,3,out,err,out,g.small_cases())[0])
                err.write_bytes(diag)
                self.assertFalse(ci.detection(recipe,0,out,err,out,g.small_cases())[0])

if __name__=='__main__':unittest.main()
