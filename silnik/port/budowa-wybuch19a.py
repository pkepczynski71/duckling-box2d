from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                 
                                                           
   
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, shutil, subprocess, sys, time

HERE=Path(__file__).resolve().parent
OWNER='T1-19A-0511-e7f996254'
PATCH_SHA='b193e8dbf34790aa9600652a27de42ffd82651e057e9ff65b44a4e4cc88fa3fc'
BFIX={'body.c':'61fd24f3f295716a1365516447db060a14cd19cd90517f98fcb5431b12d70e24','island.c':'d7e54a34c002b1dd759336ea3fb1d5c6ce94deda7643283f7b7591e0ebffee31','solver_set.c':'33868ea4d9c6445a3cb0edca187c6a05eb42e185cdb112748ff44298156ba1eb'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def prepare(source,work,variant='Bfix',coverage=False):
 source,work=Path(source).resolve(),Path(work).resolve()
 if not (work.parent/'OWNER').exists() or (work.parent/'OWNER').read_text()!=OWNER: raise ValueError('OWNER')
 if str(work).startswith('/mnt/'):raise ValueError('Linux workspace required')
 work.mkdir(exist_ok=True);b=load('wybuch19_base14',HERE/'budowa-polaczenia.py')
 before=b.source_sums(source)
 contract=norm_text(HERE/'fixtures/norms/KONTRAKT-7.json')
 if len(before)!=63 or any(f'{v}  {k}' not in contract for k,v in before.items()):raise ValueError('source pins')
 root=source
 if variant=='Bfix':
  patch=HERE/'19a-bfix.patch'
  if sha(patch)!=PATCH_SHA:raise ValueError('patch pin')
  root=work/'original'
  if not root.exists():
   shutil.copytree(source,root)
   subprocess.run(['patch','-p1','--batch','-i',str(patch)],cwd=root,check=True,capture_output=True)
  if any(sha(root/'src'/f)!=v for f,v in BFIX.items()):raise ValueError('Bfix source pins')
 out=work/'bin';b.project(root,work/'project',out);p=work/'project'
                                                                 
 cm=(p/'CMakeLists.csv').read_text().replace(str(HERE/'kontrola-polaczenia.c'),str(HERE/'kontrola-wybuch19a.c'))
 cm=cm.replace(' OBS=0)',' OBS=1 OBS19=0)').replace(' OBS=1)',' OBS=1 OBS19=1)')
 cm+='\n'+'\n'.join(f'target_compile_options(c11-{x}-bin PRIVATE -O2)' for x in ('obs0','obs1'))+'\n'
 if coverage:cm+='target_compile_options(sen11 PUBLIC --coverage -fno-inline -fno-inline-functions -fno-inline-small-functions)\ntarget_link_libraries(sen11 PUBLIC --coverage)\n'
 (p/'CMakeLists.csv').write_text(cm)
 (p/'wybuch19-base14.inc').write_text((HERE/'kontrola-polaczenia.c').read_text().replace('int main(int argc,char** argv)','int legacy_main19(int argc,char** argv)'))
                                                                              
 probe=(HERE/'19a-C-proba.c').read_text();helpers=probe[probe.index('static float f('):probe.index('typedef struct LockProbe')]
 for old,new in [('f','float19'),('u','bits19'),('geometry','geometry19'),('shapeInput','shapeInput19'),('state','state19')]:helpers=re.sub(r'\b'+old+r'\b',new,helpers)
 (p/'wybuch19-helpers.inc').write_text(helpers)
 m=json.loads((HERE/'wybuch-19a-przypadki.json').read_bytes())
 fixture=['static const uint32_t scene19[2][49][26]={']
 for key,n in [('direct',48),('public',32)]:
  fixture.append('{ {0},'+','.join('{'+','.join(map(str,c.get('sceneWords',m['baseSceneWords'])))+'}' for c in m[key])+'},')
 fixture+=['};'];(p/'wybuch19-fixtures.inc').write_text('\n'.join(fixture))
                                                                             
 lines=(root/'src/world.c').read_text().splitlines()
 hooks={2670:'port19Trace(0,shapeId,body->id,output.distance,b2Vec2_zero,b2Vec2_zero,0,0,0,b2Vec2_zero)',2677:'port19Trace(1,shapeId,body->id,output.distance,b2Vec2_zero,b2Vec2_zero,0,0,0,b2Vec2_zero)',2715:'port19Trace(2,shapeId,body->id,output.distance,closestPoint,direction,perimeter,scale,magnitude,impulse)'}
 for n in hooks:
  if 'return true;' not in lines[n-1]:raise ValueError('world hook anchor')
 head=[l for l in lines if l.startswith('#include ')]+['extern void port19Trace(int,int,int,float,b2Vec2,b2Vec2,float,float,float,b2Vec2);','#define C19_(a,b) a##b','#define C19(a,b) C19_(a,b)']
 head += [f'#define R19_{n} {hooks.get(n, '((void)0)')}' for n in range(1,len(lines)+1)]
 head+=['#define return C19(R19_,__LINE__); return']
 sw=(p/'sen-world.c').read_text();sw=sw.replace('#include "world.c"','\n'.join(head)+'\n#include "world.c"\n#undef return')
 (p/'sen-world.c').write_text(sw)
 return dict(variant=variant,source_before=before,source_after=b.source_sums(source),patch=PATCH_SHA if variant=='Bfix' else None,
             changed_source={x:sha(root/'src'/x) for x in ('body.c','island.c','solver_set.c')},base14_builder=sha(HERE/'budowa-polaczenia.py'),project=str(p),out=str(out))

def build(source,work,variant='Bfix',coverage=False):
 from wybuch19a import inventory,run
 before=inventory(source)
 adapters={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.c','.h','.py','.json','.dk','.md')}
 r=prepare(source,work,variant,coverage);r['inventory']=before;p=Path(r['project']);out=Path(r['out']);out.mkdir(exist_ok=True)
 r['adapters_before']=adapters
 r['commands']=[]
 for label,cmd in [('configure',['cmake','-S',str(p),'-B',str(p/'make'),'-G','Unix Makefiles','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DBOX2D_DISABLE_SIMD=ON','-DBOX2D_AVX2=OFF']),('compile',['cmake','--build',str(p/'make'),'--parallel','1'])]:
  result=run(cmd,None,Path(work)/(label+'.log'),180,2*1024**3)
  r['commands'].append(dict(label=label,**result));print(label,result['exit'],flush=True)
  (Path(work)/'build.json').write_text(json.dumps(r,indent=2)+'\n')
  if result['exit'] or result['failure']:raise RuntimeError(str(Path(work)/(label+'.log')))
 r['binaries']={x:dict(path=str(out/f'c11-{x}-bin'),sha256=sha(out/f'c11-{x}-bin')) for x in ('obs0','obs1')}
 r['inventory_after']=inventory(source)
 if before!=r['inventory_after']:raise ValueError('source changed during compilation')
 r['adapters_after']={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.c','.h','.py','.json','.dk','.md')}
 if adapters!=r['adapters_after']:raise ValueError('adapter changed during C0/C1 build')
                                                                              
 import shlex
 units=json.loads((p/'make/compile_commands.json').read_text())
 for unit in units:
  flags=shlex.split(unit['command'])
  if not all(x in flags for x in ('-std=c17','-DNDEBUG','-DBOX2D_DISABLE_SIMD','-DB2_VALIDATE=0','-fno-fast-math','-ffp-contract=off')):raise ValueError('flags '+unit['file'])
  if [x for x in flags if x.startswith('-O')][-1:]!=['-O2'] or '-ffast-math' in flags:raise ValueError('effective O2')
  if unit['file'].endswith('kontrola-wybuch19a.c') and '-DOBS=1' not in flags:raise ValueError('BASE13 must stay enabled')
 library=[x for x in units if 'CMakeFiles/sen11.dir' in x['command']]
 if len(library)!=36:raise ValueError('35 original units plus one transparent joint wrapper')
 mapping={'broad_phase.c':'kontrola-kontakty-broad.c','contact.c':'kontrola-lancuchy-contact.c','contact_solver.c':'kontrola-solver-contact.c','solver.c':'sen-solver.c','world.c':'sen-world.c'}
 expected=sorted([mapping.get(p.name,p.name) for p in Path(source).joinpath('src').glob('*.c')]+['kontrola-polaczenia-observer.c'])
 if sorted(Path(x['file']).name for x in library)!=expected:raise ValueError('original unit inventory mismatch')
 if coverage and any(not all(f in x['command'] for f in ('--coverage','-fno-inline','-fno-inline-functions','-fno-inline-small-functions')) for x in units):raise ValueError('coverage/no-inline flags')
 r['original_unit_mapping']=mapping;r['coverage_no_inline']=coverage
 r['original_units']=35;r['effective_flags_verified']=True
 if sum(x['seconds'] for x in r['commands'])>180:raise ValueError('combined compilation limit')
 r['compile_commands']=units
 gcc=Path(shutil.which('gcc'));r['gcc']=dict(path=str(gcc),sha256=sha(gcc),version=subprocess.check_output([gcc,'--version'],text=True))
 (Path(work)/'build.json').write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--work',required=True);a.add_argument('--variant',choices=['B0','Bfix'],default='Bfix');a.add_argument('--coverage',action='store_true');args=a.parse_args();build(args.source,args.work,args.variant,args.coverage)
