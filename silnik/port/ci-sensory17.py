pass                                                                            
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


tape=load('tape17',HERE/'sensory-tasmy.py')
compare=load('compare17',HERE/'porownaj-sensory17.py')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def execute(binary,input_file,output,timeout=120,stdin=False):
    start=time.monotonic();error=output.with_suffix('.stderr');timing=output.with_suffix('.time')
    command=['/usr/bin/time','-f','%e %M','-o',str(timing),str(binary),'--diagnostic']+([] if stdin else [str(input_file)])
    with error.open('wb') as err,output.open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as dst:
            source=Path(input_file).open('rb') if stdin else None
            try:proc=subprocess.Popen(command,stdin=source,stdout=subprocess.PIPE,stderr=err,start_new_session=True)
            finally:
                if source is not None:source.close()
            old=signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('native timeout')))
            signal.setitimer(signal.ITIMER_REAL,timeout)
            try:
                while True:
                    chunk=proc.stdout.read(65536)
                    if not chunk:break
                    dst.write(chunk)
                code=proc.wait()
            except BaseException:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise
            finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old);proc.stdout.close()
    return {'command':command,'stdin':str(input_file) if stdin else None,'exit':code,'stderr':error.read_text(errors='replace')[:65536],
            'seconds':time.monotonic()-start,'time':timing.read_text(),'gzipBytes':output.stat().st_size,'sha256':sha(output)}


def _job(args):return run(*args,jobs=1,write_manifest=False)


def run(work,output,profiles,ids=None,jobs=1,write_manifest=True):
    work,output=Path(work),Path(output);output.mkdir(parents=True,exist_ok=True)
    data=json.loads((HERE/'sensory-przypadki.json').read_bytes());results=[];unexecuted=[]
    binary={str(obs):work/'out'/f'c11-obs{obs}-bin' for obs in (0,1)}
    binaries={k:{'path':str(v),'sha256':sha(v)} for k,v in binary.items()}
    if jobs>1:
        if jobs>8:raise ValueError('at most 8 workers')
        tasks=[(work,output,[profile],{case['ordinal']}) for profile in profiles for case in data[profile.lower()]
               if ids is None or case['ordinal'] in ids]
        with ProcessPoolExecutor(max_workers=jobs) as pool:parts=list(pool.map(_job,tasks))
        results=[r for part in parts for r in part['results']];unexecuted=[r for part in parts for r in part['unexecuted']]
        summary=dict(base='f73852bfadb7ce396e1cb52d7febfe9374b07724',binaries=binaries,mode='independent diagnostic cases; original IDs; no renumbering',
            completePORT17=False,cases=len(results),passed=sum(r['passed'] for r in results),failed=[r['id'] for r in results if not r['passed']],
            unexecuted=unexecuted,GUARD697='separate ci-sensory17-oslony.py stage',D='not supplied; exact inputs frozen before D',results=results)
        save(output/'manifest.json',summary);return summary
    for profile in profiles:
        for case in data[profile.lower()]:
            ident=case['ordinal'];key=case['id']
            if ids is not None and ident not in ids:continue
            reason='mixed14b-16b' if key in [f'P{i:03}' for i in range(79,85)]+['D060'] else None
            if reason:unexecuted.append({'id':key,'reason':reason});continue
            out=output/key;out.mkdir(exist_ok=True)
            try:
                recipes={ident:(tape.public if profile=='PUBLIC' else tape.direct)(case)}
                for side in ('C','D'):
                    path=out/(side+'.in')
                    path.write_text(''.join(tape.materialize(profile,side,data,{ident})),encoding='ascii',newline='\n')
                executions=[]
                for obs in (0,1):executions.append(execute(binary[str(obs)],out/'C.in',out/f'C{obs}.out.csv.gz'))
                row={'id':key,'profile':profile,'inputSHA':{s:sha(out/(s+'.in')) for s in ('C','D')},'runs':executions,'operations':len(recipes[ident])}
                if any(x['exit'] or x['stderr'] for x in executions):row.update(passed=False,error='native exit/stderr')
                else:
                    row['comparison']=compare.compare(out/'C0.out.csv.gz',out/'C1.out.csv.gz',recipes)
                    row['passed']=row['comparison']['C0ProjectionC1']
                    measured=row['comparison']['counts'][1]['metrics'];expected=case['c18a'].get('metrics',{})
                    row['frozenC18aMaxima']={k:{'expected':expected.get(k),'actual':measured.get(k,0)} for k in ('sensors','refs','maxBegin','maxEnd','bits','queryMax') if k in expected}
                    row['maximaDifferences']=[k for k,v in row['frozenC18aMaxima'].items() if v['expected']!=v['actual']]
                    row['passed']=row['passed'] and not row['maximaDifferences']
            except Exception as exc:row={'id':key,'profile':profile,'passed':False,'error':str(exc)}
            save(out/'receipt.json',row);results.append(row)
            print(key,'PASS' if row['passed'] else 'FAIL',row.get('error',row.get('comparison',{}).get('firstDifference')),flush=True)
    summary={'base':'f73852bfadb7ce396e1cb52d7febfe9374b07724','binaries':binaries,'mode':'independent diagnostic cases; original case IDs; no renumbering',
             'completePORT17':False,'cases':len(results),'passed':sum(r['passed'] for r in results),'failed':[r['id'] for r in results if not r['passed']],
             'unexecuted':unexecuted,'GUARD697':'not yet executed','D':'not yet supplied; inputs already frozen',
             'results':results}
    if write_manifest:save(output/'manifest.json',summary)
    return summary


def compare_frozen(root,d_binary,output):
    pass                                                                            
    root,output=Path(root),Path(output);output.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((root/'manifest.json').read_bytes());data=json.loads((HERE/'sensory-przypadki.json').read_bytes());rows=[]
    for old in frozen['results']:
        key=old['id'];source=root/key;dest=output/key;dest.mkdir(exist_ok=True)
        if not old.get('passed'):
            rows.append(dict(id=key,passed=False,error='C stage failed; dependent D not run'));continue
        for side,expected in old['inputSHA'].items():
            if sha(source/(side+'.in'))!=expected:raise ValueError('frozen input changed: '+key+'/'+side)
        for obs in (0,1):
            if sha(source/f'C{obs}.out.csv.gz')!=old['runs'][obs]['sha256']:raise ValueError('frozen C changed: '+key)
        ident=int(key[1:]);case=data[old['profile'].lower()][ident-1]
        recipes={ident:(tape.public if old['profile']=='PUBLIC' else tape.direct)(case)}
        row=dict(id=key,inputSHA=old['inputSHA'])
        try:
            execution=execute(d_binary,source/'D.in',dest/'D.out.csv.gz',stdin=True);row['run']=execution
            if execution['exit'] or execution['stderr']:row.update(passed=False,error='D exit/stderr')
            else:
                result=compare.compare(source/'C0.out.csv.gz',source/'C1.out.csv.gz',recipes,dest/'D.out.csv.gz')
                row.update(comparison=result,passed=result['C0ProjectionC1'] and result['C1D'])
        except (OSError,subprocess.SubprocessError,ValueError,TimeoutError) as exc:row.update(passed=False,error=str(exc)[:2000])
        save(dest/'receipt.json',row);rows.append(row);print(key,'PASS' if row['passed'] else 'FAIL',flush=True)
    result=dict(completePORT17=False,base=frozen['base'],D={'path':str(d_binary),'sha256':sha(d_binary)},results=rows,
                passed=sum(r['passed'] for r in rows),cases=len(rows),unexecuted=frozen['unexecuted'])
    save(output/'manifest.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--profile',choices=['PUBLIC','DIRECT','BOTH'],default='BOTH');p.add_argument('--ids');p.add_argument('--compare-frozen',type=Path);p.add_argument('--d-binary',type=Path);p.add_argument('--jobs',type=int,default=1);a=p.parse_args()
    if a.compare_frozen:
        if not a.d_binary:p.error('--compare-frozen requires --d-binary')
        result=compare_frozen(a.compare_frozen,a.d_binary,a.output)
        raise SystemExit(result['passed']!=result['cases'])
    if not a.work:p.error('--work is required for C')
    ids=None if not a.ids else {int(i) for i in a.ids.split(',')}
    result=run(a.work,a.output,['PUBLIC','DIRECT'] if a.profile=='BOTH' else [a.profile],ids,a.jobs)
    raise SystemExit(1 if result['failed'] else 0)
