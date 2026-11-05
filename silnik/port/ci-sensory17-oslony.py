pass                                                                               
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


inputs=load('guard_inputs17','przypadki-sensory.py')
campaign=load('guard_campaign17','ci-sensory17.py')
compare=campaign.compare


def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def run(work,output,ids=None):
    work,output=Path(work),Path(output);output.mkdir(parents=True,exist_ok=True);data=inputs.manifest()
    binary={o:work/'out'/f'c11-obs{o}-bin' for o in (0,1)}
    parser=output/'parser';pairs=inputs.parser_inputs(data,parser);results=[]
    for pair in pairs:
        if pair['side']!='C':continue
        r=subprocess.run([str(binary[1]),'--diagnostic',str(parser/pair['file'])],capture_output=True,timeout=30)
        fatal=pair['phase']=='negative'
                                                                             
        lines=r.stdout.splitlines();terminal=any(line.startswith(b'END ') for line in lines) if fatal else False
        row=dict(pair,actualExit=r.returncode,actualStderr=r.stderr.decode('ascii',errors='replace'),stdoutBytes=len(r.stdout),
                 passed=r.returncode==pair['exit'] and r.stderr==pair['stderr'].encode() and not terminal,
                 stdoutSHA=hashlib.sha256(r.stdout).hexdigest())
        results.append(row)
        (parser/(pair['file']+'.stdout')).write_bytes(r.stdout)
    save(parser/'results.json',results)
    selected={g['ordinal'] for g in data['guards'] if g['ordinal'] not in (630,633)}
    if ids is not None:selected &= ids
    guard=output/'guard';guard.mkdir(exist_ok=True)
    for side in ('C','D'):
        lines=inputs.guard_lines(data,side);next(lines);out=[f'PORT17 GUARD {len(selected)}\n'];current=0
        for line in lines:
            if line.startswith('C '):current=int(line.split()[1])
            if current in selected:out.append(line)
        (guard/(side+'.in')).write_bytes(''.join(out).encode('ascii'))
    runs=[]
    for obs in (0,1):runs.append(campaign.execute(binary[obs],guard/'C.in',guard/f'C{obs}.out.csv.gz',timeout=180))
    status=[];comparison=None
    if not any(r['exit'] or r['stderr'] for r in runs):
        comparison=compare.compare(guard/'C0.out.csv.gz',guard/'C1.out.csv.gz',{i:[] for i in selected})
        with compare.open_stream(guard/'C1.out.csv.gz') as f:
            for raw in f:
                tag,p=compare.parse(raw)
                if tag!='G17':continue
                ident,phase=map(int,p[1:3]);actual=list(map(int,p[3:6]));g=data['guards'][ident-1]
                e=g['expectedNegative' if phase==0 else 'expectedPositive'];expected=[e[k] for k in ('status','reason','accepted')]
                status.append(dict(id=g['id'],phase=phase,actual=actual,expected=expected,passed=actual==expected))
    summary=dict(base='f73852bfadb7ce396e1cb52d7febfe9374b07724',completePORT17=False,
        parser=dict(passed=sum(r['passed'] for r in results),total=len(results)),
        guards=dict(cases=len(selected),helperOnly=sum(data['guards'][i-1]['helperOnly'] for i in selected),
                    inputSHA={side:campaign.sha(guard/(side+'.in')) for side in ('C','D')},
                    runs=runs,comparison=comparison,phases=len(status),passed=sum(r['passed'] for r in status),results=status),
        unexecuted=[dict(id=f'G{i:03}',reason='mixed CCD B20 / 16b') for i in (630,633)],
        D='not supplied; all exact D inputs frozen',
        note='C statuses are the contract oracle. Helper-only C is not a native Duckling validator/binding proof.')
    save(output/'manifest.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ids');a=p.parse_args()
    result=run(a.work,a.output,None if not a.ids else {int(i) for i in a.ids.split(',')})
    ok=result['parser']['passed']==124 and result['guards']['phases']==2*result['guards']['cases'] and result['guards']['passed']==result['guards']['phases'] and result['guards']['comparison']['C0ProjectionC1']
    print(json.dumps(dict(parser=result['parser'],guardCases=result['guards']['cases'],guardPhases=result['guards']['phases'],passed=ok)))
    raise SystemExit(not ok)
