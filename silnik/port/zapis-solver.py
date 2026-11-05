pass                                                                        
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import time

def manifest(path):
    digest=hashlib.sha256();counts=Counter();size=0;head=[];tail=[]
    with Path(path).open('rb') as stream:
        for line in stream:
            size+=len(line);digest.update(line);counts[line.split(b' ',1)[0].decode('ascii',errors='backslashreplace')]+=1
            bounded=line[:8192].decode('ascii',errors='backslashreplace')
            if len(head)<3:head.append(bounded)
            tail=(tail+[bounded])[-3:]
    return {'bytes':size,'sha256':digest.hexdigest(),'records':dict(sorted(counts.items())),
            'head':head,'tail':tail}

def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def case_streams(context, compare, cases, commands, *, component=False, models=None, seconds=7200):
    pass                                                                 

                                                                          
                                                                           
                                                                             
       
    root=context.OUT.resolve();temporary=context.base.TEMP/'solver-pipes'
    temporary.mkdir(parents=True,exist_ok=True)
    prefix='component10' if component else 'public10'
    fifos={name:temporary/(prefix+'-'+name+'.fifo') for name in commands}
    created=[]
    try:
        for path in fifos.values():
            if path.exists():raise ValueError('owned FIFO path already exists: '+str(path))
            os.mkfifo(path);created.append(path)
    except BaseException:
        for path in created:path.unlink()
        if temporary.exists() and not any(temporary.iterdir()):temporary.rmdir()
        raise
    counts=len(cases);header=('COMPONENT10' if component else 'PORT10')+f' {counts}\n'
    open_streams={};results=[];process_codes={};started=time.monotonic();closed=False
    digests={name:hashlib.sha256() for name in commands}
    byte_counts=Counter();record_counts={name:Counter() for name in commands}
    def observed(name,line):
        encoded=line.encode('ascii');digests[name].update(encoded);byte_counts[name]+=len(encoded)
        record_counts[name][line.split(' ',1)[0].rstrip('\n')]+=1
    with ThreadPoolExecutor(max_workers=len(commands)) as pool:
        workers={name:pool.submit(context.base.run,prefix+'-'+name,argv,
                                  seconds=seconds,stdout=fifos[name]) for name,argv in commands.items()}
        try:
            for name,path in fifos.items():
                open_streams[name]=path.open('r',encoding='ascii',newline='')
            for name,stream in open_streams.items():
                actual=stream.readline(131073)
                observed(name,actual)
                if actual!=header:raise ValueError(name+' missing/wrong global header: '+repr(actual[:200]))
            for case in cases:
                paths={name:root/(prefix+f'-case-{case.id:03}-'+name+'.raw.csv') for name in commands}
                case_digests={name:hashlib.sha256() for name in commands};case_bytes=Counter();case_records={name:Counter() for name in commands}
                for name,stream in open_streams.items():
                    with paths[name].open('w',encoding='ascii',newline='\n') as out:
                        out.write(header)
                                                                                   
                                                                                 
                        while True:
                            line=stream.readline(131073)
                            if not line:raise ValueError(name+f' truncated at case {case.id}')
                            observed(name,line);encoded=line.encode('ascii');case_digests[name].update(encoded);case_bytes[name]+=len(encoded)
                            case_records[name][line.split(' ',1)[0].rstrip('\n')]+=1
                            out.write(line)
                            if line.startswith('ENDCASE '):break
                        out.write(f'END {counts}\n')                                               
                result=compare.compare_files(paths['obs1'],paths['duckling'],paths.get('obs0'),(case,),
                    component=component,header_n=counts,models=models)
                result['case']=case.id;result['framed_case_slice']=True
                result['models_checked']=bool(models) if not component else False
                result['payloads']={name:manifest(path) for name,path in paths.items()}
                for name in paths:
                    result['payloads'][name]['original_case_slice']={'sha256':case_digests[name].hexdigest(),
                        'bytes':case_bytes[name],'records':dict(case_records[name])}
                save(root/(prefix+f'-case-{case.id:03}.json'),result)
                results.append(result)
                                                                                  
                                                                                
                if result['errors']:raise ValueError('case comparison failed: '+json.dumps(result['first_difference'] or result['errors'],ensure_ascii=False))
                if not component and not models:raise ValueError('independent T2b model required before PUBLIC10 compaction')
                for path in paths.values():path.unlink()
            for name,stream in open_streams.items():
                tail=stream.readline(131073)
                observed(name,tail)
                if tail!=f'END {counts}\n' or stream.read(1):raise ValueError(name+' missing/trailing global END')
            closed=True
        finally:
                                                                                 
                                                                                  
            for stream in open_streams.values():stream.close()
            for name,future in workers.items():
                try:process_codes[name]=future.result()
                except BaseException as exc:
                    process_codes[name]=127
                    (root/(prefix+'-'+name+'-runner-stderr.csv')).write_text(repr(exc)+'\n',encoding='utf-8')
            stderr_bytes={name:(root/(prefix+'-'+name+'-stderr.csv')).stat().st_size
                          if (root/(prefix+'-'+name+'-stderr.csv')).is_file() else -1 for name in commands}
            for path in fifos.values():
                if path.exists():path.unlink()
            if temporary.exists() and not any(temporary.iterdir()):temporary.rmdir()
            receipt={'profile':prefix,'N':counts,'completed_cases':len(results),'global_END_checked':closed,
                     'process_codes':process_codes,'stderr_bytes':stderr_bytes,'seconds':time.monotonic()-started,'cases':results,
                     'original_streams':{name:{'sha256':digests[name].hexdigest(),'bytes':byte_counts[name],
                         'records':dict(record_counts[name]),'complete':closed} for name in commands}}
            save(root/(prefix+'-manifest.json'),receipt)
    if not closed or any(process_codes.values()) or any(stderr_bytes.values()):
        raise ValueError('native process failed, stderr nonempty or missing END: '+repr(process_codes))
    return receipt

def prepare_publication(directory):
    pass                                                                        
    root=Path(directory).resolve();removed={}
    inputs={stem+suffix+'.csv' for stem in ('przypadki-solver','proba-solver','proba6-solver','component-solver','proba-component-solver')
            for suffix in ('','-stdin')}
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(root);name=path.name
        log_name=name.endswith(('-stderr.csv','-kod.csv','-polecenie.csv','-console.csv','-czas.csv','-kompilacja.csv'))
        with path.open('rb') as stream:
            magic=stream.read(4);stream.seek(0);first=stream.readline(128);second=stream.readline(128)
        binary=name.endswith('-bin') or path.suffix in ('.o','.a','.so','.dll','.exe') or magic in (b'\x7fELF',) or magic[:2]==b'MZ'
        input_=name in inputs or name=='input.csv' or rel.parts[0] in ('wejscia-swiat','wejscia-solver','ujemne-solver','zrodla')
        raw=name.endswith('.raw.csv') or (first.startswith(b'PORT10 ') and second.startswith(b'CASE '))
        raw|=name.startswith(('c10-obs','duckling-solver','component10-')) and path.suffix=='.csv' and not log_name
        raw|=first.startswith((b'GUARD10 ',b'COMPONENT10 ',b'FH10 ',b'GR10 ')) and not input_
        if not binary and not raw and log_name:continue
        metadata=path.suffix in ('.json','.md','.sha256') or name in ('start-unix.csv','zrodla-sha256.csv')
        command_log=path.suffix=='.csv' and path.with_name(path.stem+'-kod.csv').is_file()
        if not binary and not raw and (input_ or metadata or command_log):continue
        entry=manifest(path) if not binary else {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        entry['validated']=False;entry['reason']='publication filter: payload excluded, see comparison receipt'
        save(path.with_name(name+'.publication.json'),entry);path.unlink();removed[rel.as_posix()]=entry
    report=root/'PUBLIKACJA-SOLVER.json'
    if removed or not report.exists():save(report,removed)
    return removed

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--publikacja',type=Path,required=True)
    args=parser.parse_args();print('Removed payloads:',len(prepare_publication(args.publikacja)))
