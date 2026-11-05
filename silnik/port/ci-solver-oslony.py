pass                                                                    

                                                                            
                                                                             
                                                                  
   
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


def output_directory():
    path=(ROOT/os.environ.get('RESULT_DIR','RESULT-PORT/lokalny-oslony')).resolve()
    if path.name!='krok10':path=path/'krok10'
    if not path.is_relative_to(ROOT.resolve()):raise ValueError('OSLONY results must stay inside this worktree')
    return path


def context(out):
    os.environ['RESULT_DIR']=str(out.relative_to(ROOT))
    if len(sys.argv)<2:sys.argv.append('solver-oslony')
    else:sys.argv[1]='solver-oslony'
    api=load('solver_oslony_existing_runner','ci.py')
    return SimpleNamespace(**vars(api))


def report_text(result):
    lines=['# Krok10 — osłony','','RESULT: '+('OK' if result['code']==0 else 'FAIL / UNMEASURED'),'',
           '| Etap | Wynik |','|---|---|']
    lines += [f'| {name} | {value} |' for name,value in (
        ('E2997dac7b8e6 E0b48557ab5c3',str(result.get('unit_tests','UNMEASURED'))),
        ('E6410ed3b85ca: E9f41e319c72c Ea238c6659de1 Eff651d1fb71c',str(result.get('single_hit','UNMEASURED'))),
        ('GUARD10: nazwane grupy / procesy',str(result.get('guard_counts','UNMEASURED'))),
        ('GUARD10 C/D',str(result.get('guards_ok','UNMEASURED'))),
        ('Eeb08ff3e4b31 F01–F29 E283ada7088c2 F26 Ede7d1b721a1e E03db0c4513e3 LF/CRLF/EOF',str(result.get('negatives_ok','UNMEASURED'))),
        ('Natywne mutacje',str(result.get('mutation_coverage','UNMEASURED'))),
        ('Ec56152fce412 E1a1d2e5d3ecb',str(result.get('equivalent_proofs','UNMEASURED'))),
        ('Trzy budowy C',str(result.get('c_probe','UNMEASURED'))))]
    lines+=['','## Luki / odmowy','']
    lines += ['- '+str(error) for error in result['errors']] or ['- Brak.']
    lines+=['','E1c45911567c2 Ec8cd7d137112 E01cf82a666a8 E003a8cb6dbd7 E7b684b07e77f E420e98542dbd Eb6a3fcb95ca2, E84ea7bf4bd60 E5165a53444c6 '
            'Ede7d1b721a1e E931794c54d4b Eac95c3bbeb07 E6b6b65ad9b4e Ea9fec58e15e1 Ee015828237b8 Eb5de7cc3735f E2a3e8cdee0c3. '
            'E8a9a8ae0414d E8864118b1838, E0dec4bf1026b, E55ea09e5715d Ea3fe81deb86e Ede7d1b721a1e E95642399a6d9 Eb17d45121150 Ecd5b158f21b7 E31ec1412a751 Ed22bb519e930.','',
            'Ec56152fce412 EQUIVALENT — E886ebea7a420: E283ada7088c2 Eaea440a813f6 Ede7d1b721a1e E283ada7088c2 Ea7e2d8645f7b Eac0b52a2ae6e Ebc024cfa6e2b Ea3ad92305e5c.','']
    return '\n'.join(lines)


def stage(ctx=None):
    started=time.monotonic();out=Path(ctx.OUT) if ctx else output_directory();out.mkdir(parents=True,exist_ok=True)
    result={'code':1,'errors':[],'native_executed':False};runtime=None
    def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def diagnose(stage,name,row):
        if row.get('diagnosed'):return
        callback=getattr(ctx,'petla_receipt',None)
        if callback:callback(stage,name,row)
    (out/'OSLONY.md').write_text('# Krok10 — Ef4465733b96b\n\nW TOKU; missing E365fff9ed60f Eb63e47faf17f.\n',encoding='utf-8')
    try:
        native=load('solver_oslony_mutations','mutacje-solver.py')
        branches=load('solver_oslony_branches','galezie-solver.py')
        probe=load('solver_oslony_c_probe','proba-solver-c.py')
        manifest=native.recipes();fixtures=native.f.definitions()
        result['equivalent_proofs']=len(manifest['equivalent_proofs'])
        result['guard_counts']={'groups':len({x.group for x in fixtures}),'processes':len(fixtures)}
        applicability=native.applicability(ROOT,manifest);save('oslony-receptury-dopasowania.json',applicability)
        result['single_hit']={'ok':sum(row['single_hit'] for row in applicability),'required':len(applicability)}
        if any(not row['single_hit'] for row in applicability):result['errors'].append('Mutation recipe does not match exactly one product source location.')
        if manifest['unresolved_recipes']:result['errors'].append('E654decb61d52 E1463e492c26e E0840f545c010: '+str(len(manifest['unresolved_recipes'])))
        tests=unittest.defaultTestLoader.discover(str(HERE),pattern='test_solver*.py')
        tested=unittest.TextTestRunner(verbosity=1).run(tests)
        result['unit_tests']={'run':tested.testsRun,'failures':len(tested.failures),'errors':len(tested.errors),'skipped':len(tested.skipped)}
        if not tested.wasSuccessful():result['errors'].append('E2997dac7b8e6 E0b48557ab5c3 kroku10 E31ec1412a751 E21febe96fdfe.')
        c_audit=probe.audit(ctx or SimpleNamespace(PORT=HERE));save('PROBA-TRZECH-C.json',c_audit)
        if not c_audit['errors']:
            try:
                ctx=ctx or context(out)
                c_audit=probe.run(ctx)
            except Exception as exc:
                c_audit['errors'].append(type(exc).__name__+': '+str(exc));c_audit['code']=1;c_audit['status']='FAIL / UNMEASURED'
            save('PROBA-TRZECH-C.json',c_audit)
        result['c_probe']=c_audit['status']
        result['errors']+=['Ee7ae321ba8dc E66a1a48ae5aa C: '+error for error in c_audit['errors']]
        if c_audit['code']:result['errors'].append('Ee7ae321ba8dc E66a1a48ae5aa C Ecd5b158f21b7 E3c44c3e1b8b7 Eb46d2b5dbabf E420e98542dbd E574440889a40 E33d277cf0ef5 8640 E2db1fbdaf6e9/E3837be541497 Ede7d1b721a1e E429cfb98fa17.')
                                                                            
                                                                          
        available=probe.cpu()['required_platform'] and bool(shutil.which('cc')) and (HERE/'solver-swiata.dk').is_file()
        if not available:
            result['errors'].append('Native solver checks require x86_64 Linux, a C compiler and the product driver.')
        else:
            ctx=ctx or context(out);runtime=native.Runtime(ctx);result['native_executed']=True
            kind4=[]
            for item in fixtures:
                if item.name in ('G10-LEGACY-LIMIT','G10-HIT-READ-PURE'):
                    try:kind4.append(runtime.guard(item,both=False))
                    except Exception as exc:kind4.append({'name':item.name,'ok':False,'error':str(exc)})
                    save('zatwierdzone-kind4-K.json',kind4)
                    diagnose('kind4',item.name,kind4[-1])
                    if kind4[-1].get('error'):result['errors'].append(item.name+': '+kind4[-1]['error'])
            result['approved_kind4_K']={'required':2,'ok':sum(r['ok'] for r in kind4)}
            if result['approved_kind4_K']['ok']!=2:
                result['errors'].append('Required kind4 guard checks did not both pass.')
            approved=[]
            for old in native.approved_replacements():
                try:row=runtime.mutation(native.replacement_recipe(old))
                except Exception as exc:row={'name':old['name'],'detected':False,'error':str(exc)}
                row['approval']=old['solver_replacement'];approved.append(row)
                save('zatwierdzone-zastepstwa-wynik.json',approved)
                diagnose('zastepstwa',old['name'],row)
            result['approved_replacements']={'required':3,'detected':sum(bool(r['detected'] and r.get('replayed_before_compaction')) for r in approved)}
            if result['approved_replacements']['detected']!=3:result['errors'].append('W3: E968ae514e354 Ee25cfe1677ca E9ef9a822cf9e E66a1a48ae5aa Eb24ffcb82fc2 Eba10b0c0c0fe.')
            guard_results=[]
            for item in fixtures:
                try:guard_results.append(runtime.guard(item))
                except Exception as exc:guard_results.append({'name':item.name,'group':item.group,'ok':False,'error':str(exc)})
                save('guard-solver-wynik.json',guard_results)
                diagnose('fixtury',item.name,guard_results[-1])
                if guard_results[-1].get('error'):result['errors'].append(item.name+': '+guard_results[-1]['error'])
            result['guards_ok']={'ok':sum(row['ok'] for row in guard_results),'required':len(fixtures)}
            if not all(row['ok'] for row in guard_results):result['errors'].append('NOT E03b382aabe85 GUARD10 E02e32ef17962 E4fc2a55cab31 C/D Ede7d1b721a1e Eba8c75cc1b33 E903a1d34bcab.')
            try:
                negatives=runtime.negatives();result['negatives_ok']={'ok':sum(row['ok'] for row in negatives),'required':len(negatives)}
                if not all(row['ok'] for row in negatives):result['errors'].append('Eee231b9c5292 Eb042c7642310/E03db0c4513e3 E31ec1412a751 E21febe96fdfe.')
            except Exception as exc:result['errors'].append('Eee231b9c5292 Eb042c7642310: '+str(exc))
            receipts=[]
            for recipe in manifest['native_mutations']:
                try:row=runtime.mutation(recipe)
                except Exception as exc:
                    row={'name':recipe['name'],'class_id':recipe.get('class_id'),'guards':recipe['guards'],
                         'code':None,'clean':False,'detected':False,'replayed_before_compaction':False,'error':str(exc)}
                receipts.append(row);save('mutacje-solver-wynik.json',receipts)
                diagnose('mutacje',recipe['name'],row)
                print(recipe['name']+': '+('WYKRYTY' if row['detected'] else 'GAP'),flush=True)
            covered=native.coverage(receipts,manifest);save('mutacje-solver-pokrycie.json',covered)
            result['mutation_coverage']={key:covered[key] for key in ('recipes','cleanly_detected','classes','guards')}
            if covered['code']:result['errors'].append('E871d041ffc74 Ee25cfe1677ca E9ef9a822cf9e E0840f545c010; E666970385790 E50e721e49c01 E417ddba2a19e-Eb8789db0c2da-pokrycie.json.')
            table=branches.frozen_table(ROOT,[*receipts,*approved])
            save('solver-galezie-wynik.json',table)
            (out/'SOLVER-GALEZIE.md').write_text(branches.markdown(table),encoding='utf-8')
        if runtime is None:
            table=branches.frozen_table(ROOT);save('solver-galezie-wynik.json',table)
        if table['native_gaps']:result['errors'].append('E5d3015b63d8a E947578d56c3f → case E3c44c3e1b8b7 '+str(len(table['native_gaps']))+' niepotwierdzonych wierszy.')
        result['code']=int(bool(result['errors']))
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc));result['code']=1
    finally:
        if runtime:
            try:runtime.close()
            except Exception as exc:result['errors'].append('E5d8b2e7c563c/E45ea38b289f8 E1729fd361334: '+str(exc));result['code']=1
        result['seconds']=time.monotonic()-started
        save('oslony-wynik.json',result)
        (out/'OSLONY.md').write_text(report_text(result),encoding='utf-8')
        (out/'etap-port-oslony-solver-kod.csv').write_bytes((str(result['code'])+'\n').encode('ascii'))
        print(report_text(result),flush=True)
    return result['code']


if __name__=='__main__':sys.exit(stage())
