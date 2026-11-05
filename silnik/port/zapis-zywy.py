pass                                                                           
import argparse
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from collections import Counter,defaultdict
import re

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
p=load('zywy_storage_compare','porownaj-zywy.py');g=p.g

def prepare_publication(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);errors=[]
    for name in ('c12-obs0-bin','c12-obs1-bin','duckling-zywy-bin','duckling-zywy-guard-bin','duckling-zywy-component-bin'):
        (directory/name).unlink(missing_ok=True)
    for path in directory.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(directory).as_posix()
        with path.open('rb') as source:magic=source.read(4)
        if path.suffix in ('.o','.a','.so','.tar','.gz') or magic==b'\x7fELF':
            errors.append(relative+': build payload');continue
        if path.suffix=='.csv':
            with path.open('rb') as source:head=source.read(256)
            if re.match(rb'(?:PORT12|COMPONENT12|GUARD12|CASE|E|WS12|SC10) ',head):errors.append(relative+': full input/output stream')
        if path.stat().st_size>16*1024*1024:errors.append(relative+': exceeds compact evidence limit')
    (directory/'PUBLIKACJA.md').write_text('\n'.join(['# D-B krok12','',*errors,'',
        'RESULT: '+('FAIL' if errors else 'OK'),'']),encoding='utf-8')
    if errors:raise ValueError('; '.join(errors))
    return {'errors':errors}

def run(commands,cases,out,models=None,stdin_paths=None,component=False):
    pass                                                                        

                                                                          
                                                                               
       
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    labels=tuple(commands);processes={};streams={};start=time.monotonic()
    result={'N':len(cases),'errors':[],'first_difference':None,'streams':{},'commands':{},
            'completed_cases':0,'completed_snapshots':0,'full_acceptance':False}
    per_case={};population={}
    with ExitStack() as stack:
        try:
            for label,argv in commands.items():
                stderr=stack.enter_context((out/(label+'-stderr.csv')).open('wb'))
                stdin=stack.enter_context(Path(stdin_paths[label]).open('rb')) if stdin_paths and label in stdin_paths else subprocess.DEVNULL
                proc=subprocess.Popen(list(map(str,argv)),stdin=stdin,stdout=subprocess.PIPE,stderr=stderr,text=True,encoding='ascii',bufsize=65536)
                processes[label]=proc;result['commands'][label]=list(map(str,argv))
                streams[label]=p.snapshots(proc.stdout,cases,label!='obs0',(models or {}).get(label),component)
            while True:
                snapshots={label:next(stream) for label,stream in streams.items()}
                identity={packet[:2] for packet in snapshots.values()}
                p.require(len(identity)==1,'process case/seq synchronization')
                case,seq=next(iter(identity))
                if case is None:
                    result['streams']={label:packet[2] for label,packet in snapshots.items()};break
                first=snapshots['obs1'][2]
                measurement=per_case.setdefault(case,{'id':case,'snapshots':0,'tags':{},'bytes_by_tag':{},
                    'maxima':dict.fromkeys(('B','S','C','H','R'),0),'max_overflow':0,'max_snapshot_bytes':0})
                measurement['snapshots']+=1
                snapshot_bytes=0
                tag_counts=Counter(t for t,v in first)
                for tag,v in first:
                    measurement['tags'][tag]=measurement['tags'].get(tag,0)+1
                    row_bytes=len(p.format_record(tag,v));snapshot_bytes+=row_bytes
                    measurement['bytes_by_tag'][tag]=measurement['bytes_by_tag'].get(tag,0)+row_bytes
                measurement['max_snapshot_bytes']=max(measurement['max_snapshot_bytes'],snapshot_bytes)
                worlds={v[2]:(v[8]|v[9]<<32) for t,v in first if t=='W'}
                history=population.setdefault(case,{'B':{},'S':{},'C':{}})
                for tag,v in first:
                    if tag=='BP11':
                        key=worlds[v[2]];history['B'][key]=max(history['B'].get(key,0),v[3])
                    if tag=='CP':
                        key=worlds[v[2]];history['C'][key]=max(history['C'].get(key,0),v[3])
                    if tag=='S':
                        key=v[8]|v[9]<<32;history['S'][key]=max(history['S'].get(key,0),v[3])
                    if tag=='CA' and v[3:5]==(1,11):measurement['max_overflow']=max(measurement['max_overflow'],v[5])
                measured={k:sum(values.values()) for k,values in history.items()}
                measured['H']=tag_counts['HT12'];measured['R']=sum(sum(v[12:16]) for t,v in first if t=='HC12')
                for key,value in measured.items():measurement['maxima'][key]=max(measurement['maxima'][key],value)
                for other in labels:
                    if other=='obs1':continue
                    difference=p.first_difference(p.projection(first) if other=='obs0' else first,snapshots[other][2])
                    if difference:
                        result['first_difference']=result['first_difference'] or {'case':case,'seq':seq,'other_process':other,**difference}
                        raise ValueError(f'full word difference case{case}/seq{seq}/{other}')
                result['completed_snapshots']+=1
                if seq==len(cases[case-1].ops):result['completed_cases']+=1
                if seq==len(cases[case-1].ops):
                    (out/'postep.json').write_text(json.dumps({'completed_cases':result['completed_cases'],
                        'completed_snapshots':result['completed_snapshots'],'seconds':time.monotonic()-start})+'\n',encoding='utf-8')
        except Exception as exc:
            result['errors'].append(type(exc).__name__+': '+str(exc))
        finally:
            for label,proc in processes.items():
                if proc.poll() is None and result['errors']:proc.terminate()
                try:code=proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();code=proc.wait(timeout=5)
                proc.stdout.close();result.setdefault('codes',{})[label]=code
                if code:result['errors'].append(label+' exit '+str(code))
            for label in labels:
                path=out/(label+'-stderr.csv');size=path.stat().st_size if path.exists() else None
                result.setdefault('stderr_bytes',{})[label]=size
                if size:result['errors'].append(label+' nonempty stderr')
            result['seconds']=time.monotonic()-start
            result['cases']=list(per_case.values())
            result['maxrss_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            result['projection_checked']=not result['errors'] and 'obs0' in labels
            result['C_D_checked']=not result['errors'] and 'duckling' in labels
            result['models_checked']=bool(models and all(label in models and result['streams'].get(label,{}).get('models_checked') for label in labels) and not result['errors'])
            for label,receipt in result['streams'].items():
                if receipt.get('model_error_count'):result['errors'].append(label+' independent model errors '+str(receipt['model_error_count']))
            result['full_acceptance']=result['projection_checked'] and result['C_D_checked'] and result['models_checked']
            (out/'porownanie-zywy.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--publikacja':
        prepare_publication(sys.argv[2]);raise SystemExit(0)
    parser=argparse.ArgumentParser();parser.add_argument('--obs1',type=Path,required=True);parser.add_argument('--obs0',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--n',type=int,default=1)
    args=parser.parse_args();cases=g.verify(args.n)
    result=run({'obs1':[args.obs1,args.input],'obs0':[args.obs0,args.input]},cases,args.out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('streams','cases','commands')},ensure_ascii=False))
    raise SystemExit(bool(result['errors']))
