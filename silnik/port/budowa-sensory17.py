pass                                                                         
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent


def load(path):
    spec=importlib.util.spec_from_file_location('sensory_base14_builder',path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m


def build(source,work,base,coverage=False):
    source,work,base=map(lambda p:Path(p).resolve(),(source,work,base))
    if platform.system()!='Linux' or str(work).startswith('/mnt/'):raise ValueError('Linux filesystem build required')
    work.mkdir(parents=True,exist_ok=True);out=work/'out';out.mkdir(exist_ok=True)
    frozen=json.loads((HERE/'sensory-przypadki.json').read_bytes())
    for item in frozen['sourceHashes']:
        if hashlib.sha256((source/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('original source SHA mismatch: '+item['path'])
    (work/'sensory-counts17.inc').write_text('static const unsigned frozenCounts17[2][96]={\n'+',\n'.join(
        '{'+','.join(str(c['operationCountExact']) for c in frozen[profile])+'}' for profile in ('public','direct'))+'\n};\n')
    (work/'sensory-guard-schema.inc').write_text('static const unsigned guardSchema17[697][4]={\n'+',\n'.join(
        '{'+','.join(map(str,(g['routeId'],64+len(g['negativePayloadH']),64+len(g['positivePayloadH']),int(g['helperOnly']))))+'}' for g in frozen['guards'])+'\n};\n')
    b=load(base/'budowa-polaczenia.py')
    before=b.source_sums(source)
    b.project(source,work,out)
    text=(base/'kontrola-polaczenia.c').read_text(encoding='utf-8')
    text=text.replace('int main(int argc,char** argv)','int unused_entry14_for17(int argc,char** argv)')
    text=text.replace('commit14();','commit17();').replace('putchar(\'\\n\');commit17();','putchar(\'\\n\');observe17(o);commit17();')
                                                                               
    text=text.replace('if(!strcmp(tag,"E14"))rank=0;',
        'if(!strcmp(tag,"E17")||!strcmp(tag,"E16")||!strcmp(tag,"G17"))rank=0;'
        'else if(!strcmp(tag,"Q17"))rank=90;'
        'else if(!strcmp(tag,"J"))rank=1;'
        'else if(!strcmp(tag,"R17")||!strcmp(tag,"R16"))rank=199;'
        'else if(!strcmp(tag,"W16"))rank=350;'
        'else if(!strcmp(tag,"V17")||!strcmp(tag,"L17")||!strcmp(tag,"T17"))rank=1280;'
        'else if(!strcmp(tag,"U17"))rank=1281;'
        'else if(!strcmp(tag,"W17"))rank=1282;'
        'else if(!strcmp(tag,"I16"))rank=1600;'
        'else if(!strcmp(tag,"E14"))rank=0;')
    text='static void commit17(void);\nstruct Operation;static void observe17(const struct Operation*);\nstatic void port17PreSolveRoute(void);\nstatic int port17LockGate(int);static int port17PairGate(int,int);static int port17InstallGate(int,int);\n'+text
    text=text.replace('if(outputSize9>13833216u)','if(outputSize9>148050944u)')
    text=text.replace('rows[n]=(Output14){p,rank,n};','rank*=2;if(!strcmp(tag,"W16"))rank=2*(300+rank10("WS12"))+1;rows[n]=(Output14){p,rank,n};')
    (work/'sensory-base14.inc').write_text(text,encoding='utf-8')
    p=work/'sen-solver10.inc';s=p.read_text()
    s=s.replace('    if(o->code==32&&!valid_step(dt,n))return PARAM;',
                '    if(o->code==32){int locked=port17LockGate(owner);if(locked)return locked;}\n    if(o->code==32&&!valid_step(dt,n))return PARAM;')
    s=s.replace('    if(dt!=0&&o->code==32){',
                '    if(o->code==32&&dt>0){int gate=port17PairGate(owner,1);if(gate)return gate;}\n    if(dt!=0&&o->code==32){')
    p.write_text(s)
    p=work/'kontrola-zywy-haki.h';s=p.read_text()
    s=s.replace('case 6:port14PreSolveRoute();break;', 'case 6:port14PreSolveRoute();break;\n            case 9:port17PreSolveRoute();break;')
    needle='    Hooks12* h=hooks12+owner;h->installed[kind]=a[3];'
    s=s.replace(needle,'    if(a[1]&&kind==0){int gate=port17InstallGate(owner,a[3]);if(gate)return gate;}\n'+needle)
    p.write_text(s)
                                                                            
    unit='''#include "box2d/box2d.h"
#include "box2d/collision.h"
#include "world.h"
#include "sensor.h"
#include "shape.h"
#include "body.h"
extern void port17Query(b2World*,int,int,int,float);
static int treeType17;
static b2DistanceOutput distance17(const b2DistanceInput* a,b2SimplexCache* b,b2Simplex* c,int d,b2World* w,int s,int v){
 b2DistanceOutput r=b2ShapeDistance(a,b,c,d);
#if OBS
 port17Query(w,s,v,treeType17,r.distance);
#endif
 return r;
}
#define b2ShapeDistance(a,b,c,d) distance17(a,b,c,d,queryContext->world,sensorShapeId,shapeId)
#define b2DynamicTree_Query(t,...) (treeType17=(int)((t)-world->broadPhase.trees),b2DynamicTree_Query(t,__VA_ARGS__))
#define b2OverlapSensors port17OriginalOverlapSensors
#include "sensor.c"
int port17Compare(const void* a,const void* b){return b2CompareShapeRefs(a,b);}
'''
    (work/'sensor17-unit.c').write_text(unit)
    cmake=(work/'CMakeLists.csv').read_text()
                                                                                
                                                                   
    cmake=cmake.replace(str(source/'src/sensor.c'),str(work/'sensor17-unit.c'))
    cmake=cmake.replace(str(base/'kontrola-polaczenia.c'),str(HERE/'kontrola-sensory.c'))
    cmake+='\nset_source_files_properties("'+str(work/'sensor17-unit.c')+'" PROPERTIES COMPILE_DEFINITIONS "OBS=1")\n'
    if coverage:cmake+='target_compile_options(sen11 PUBLIC --coverage)\ntarget_link_options(sen11 INTERFACE --coverage)\n'
    (work/'CMakeLists.csv').write_text(cmake)
    p=work/'solver-base10.inc';s=p.read_text();s=s.replace('PORT14A:','PORT17:').replace('PORT14:','PORT17:')
    s=s.replace('if(n>=2048)fail("INPUT_ARITY");','if(n>=2048)fail("INPUT_LINE_LENGTH");')
    p.write_text(s)
    (work/'solver-limity10.inc').write_text('static const int limits10[697][4]={\n'+',\n'.join(['{64,128,256,2048}']*697)+'\n};\n')
    commands=[]
    for name,args in [('configure',['cmake','-S',str(work),'-B',str(work/'make'),'-DCMAKE_BUILD_TYPE=Release','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF']),('build',['cmake','--build',str(work/'make'),'--parallel','4'])]:
        t=time.monotonic()
        with (out/(name+'.log')).open('wb') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
        commands.append({'command':args,'exit':r.returncode,'seconds':time.monotonic()-t})
        if r.returncode:raise RuntimeError(name+' failed: '+str(out/(name+'.log')))
    bins={}
    for obs in (0,1):
        p=out/f'c11-obs{obs}-bin';bins[str(obs)]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    receipt={'base':'f73852bfadb7ce396e1cb52d7febfe9374b07724','binaries':bins,'commands':commands,'sourceHashes':before,'sourceUnchanged':before==b.source_sums(source)}
    (out/'build17.json').write_text(json.dumps(receipt,indent=2));return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--work',required=True,type=Path);p.add_argument('--base',required=True,type=Path);p.add_argument('--coverage',action='store_true');a=p.parse_args()
    print(json.dumps(build(a.source,a.work,a.base,a.coverage),indent=2))
