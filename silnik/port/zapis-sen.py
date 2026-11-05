pass                                                                         

                                                                               
                                                                             
   
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def case_streams(directory,comparator,cases,commands,*,models,component=False,seconds=14400):
    root=Path(directory);root.mkdir(parents=True,exist_ok=True)
    required={'obs1':'C OBS1','duckling':'Duckling','obs0':'C OBS0'}
    if set(commands)!=set(required) or not models or any(label not in models for label in required.values()):
        raise ValueError('three commands and three independent models required before starting native streams')
    started=time.monotonic();prefix='component11' if component else 'public11';tag='COMPONENT11' if component else 'PORT11'
    header=f'{tag} {len(cases)}\n'.encode('ascii');end=f'END {len(cases)}\n'.encode('ascii')
    processes={};process_started={};native_wall={};read_wall={name:0.0 for name in commands}
    codes={};digests={name:hashlib.sha256() for name in commands};byte_counts={name:0 for name in commands}
    results=[];errors=[];closed=False;stderr_bytes={};receipt={}
    def checked_line(name):
        line=processes[name].stdout.readline(131073)
        if not line or len(line)>131072:raise ValueError(name+' truncated/overlong stream')
        return line
    try:
        with ExitStack() as stack,tempfile.TemporaryDirectory(prefix='.sen-stream-',dir=root) as temporary:
            temporary=Path(temporary)
            for name,argv in commands.items():
                stderr=stack.enter_context((root/(prefix+'-'+name+'-stderr.csv')).open('wb'))
                command=['timeout','--kill-after=5s',str(seconds)+'s',*map(str,argv)]
                process_started[name]=time.monotonic()
                processes[name]=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=stderr)
            for name in commands:
                if checked_line(name)!=header:raise ValueError(name+' exact global header')
                digests[name].update(header);byte_counts[name]+=len(header)
            for c in cases:
                paths={};case_start=time.monotonic();body_bytes={}
                max_bytes=(next(m['limitWyjsciaNaStrone'] for m in comparator.g.MANIFEST['component' if component else 'przypadki']
                                if (int(m['id'][1:]) if component else m['id'])==c.id))
                for name in commands:
                    read_started=time.monotonic()
                    path=temporary/(name+'.raw');paths[name]=path
                    first=checked_line(name)
                    if first!=f'CASE {c.id} {len(c.ops)}\n'.encode('ascii'):raise ValueError(name+' CASE echo')
                    size=len(first)
                    with path.open('wb') as target:
                        target.write(header);target.write(first)
                        while True:
                            line=checked_line(name);size+=len(line)
                            if size>max_bytes:raise ValueError(name+f' case{c.id} frozen byte envelope exceeded')
                            target.write(line)
                            if line==f'ENDCASE {c.id}\n'.encode('ascii'):break
                        target.write(end)
                    body_bytes[name]=size
                    read_wall[name]+=time.monotonic()-read_started
                compare_start=time.monotonic()
                item=comparator.compare_files(paths['obs1'],paths['duckling'],paths['obs0'],(c,),
                    header_n=len(cases),component=component,models=models)
                item.update(id=c.id,seconds=time.monotonic()-case_start,model_and_compare_seconds=time.monotonic()-compare_start,
                            actual_stream_body_bytes=body_bytes,synthetic_single_case_envelope=True)
                                                                                      
                for name,path in paths.items():
                    byte_counts[name]+=body_bytes[name]
                    if not item['errors']:
                        with path.open('rb') as source:
                            source.read(len(header));remaining=body_bytes[name]
                            while remaining:
                                data=source.read(min(1048576,remaining));digests[name].update(data);remaining-=len(data)
                    path.unlink()
                results.append(item)
                save(root/(prefix+'-postep.json'),{'seen_cases':len(results),'last_case':c.id,'accepted_cases':sum(not r['errors'] for r in results)})
                print(f'{prefix} id{c.id}: '+('OK' if not item['errors'] else 'BLAD'),flush=True)
            for name in commands:
                if checked_line(name)!=end or processes[name].stdout.read(1):raise ValueError(name+' exact real global END/EOF')
                digests[name].update(end);byte_counts[name]+=len(end)
            closed=True
    except Exception as exc:errors.append(str(exc))
    finally:
        for name,process in processes.items():
            if not closed and process.poll() is None:process.terminate()
        for name,process in processes.items():
            try:codes[name]=process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();codes[name]=process.wait(timeout=10)
            native_wall[name]=time.monotonic()-process_started[name]
            if process.stdout:process.stdout.close()
            path=root/(prefix+'-'+name+'-stderr.csv');stderr_bytes[name]=path.stat().st_size if path.exists() else -1
        if any(codes.values()):errors.append('native exit codes: '+str(codes))
        if any(stderr_bytes.values()):errors.append('nonempty/missing native stderr: '+str(stderr_bytes))
        if any(item['errors'] for item in results):errors.append('one or more complete cases failed full-row validation/comparison/model')
        receipt={'profile':prefix,'N':len(cases),'seen_cases':len(results),'completed_cases':sum(not r['errors'] for r in results),
                 'global_END_checked':closed,'process_codes':codes,'stderr_bytes':stderr_bytes,'cases':results,'errors':errors,
                 'native_wall_with_pipe_backpressure_seconds':native_wall,'read_and_temporary_write_wall_seconds':read_wall,
                 'model_and_compare_seconds':sum(r['model_and_compare_seconds'] for r in results),
                 'seconds':time.monotonic()-started,'original_streams':{name:{
                    'sha256':digests[name].hexdigest() if closed and len(results)==len(cases) and not errors else None,
                    'bytes':byte_counts[name],'complete':closed and len(results)==len(cases) and not errors} for name in commands}}
        save(root/(prefix+'-manifest.json'),receipt)
    if errors or not closed or len(results)!=len(cases):raise ValueError('11 full stream incomplete/invalid; see '+prefix+'-manifest.json')
    return receipt


def prepare_publication(directory):
    pass                                                                         
    root=Path(directory);removed={}
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        with path.open('rb') as source:magic=source.read(4);source.seek(0);first=source.readline(128);second=source.readline(128)
        raw=first.startswith((b'PORT11 ',b'COMPONENT11 ',b'GUARD11 '))
        binary=magic==b'\x7fELF' or magic[:2]==b'MZ' or path.suffix in ('.o','.a','.so','.exe','.dll')
        if raw or binary or path.suffix=='.raw':
            digest=hashlib.sha256()
            with path.open('rb') as source:
                for chunk in iter(lambda:source.read(1048576),b''):digest.update(chunk)
            removed[path.relative_to(root).as_posix()]={'bytes':path.stat().st_size,'sha256':digest.hexdigest(),'validated':False,'reason':'payload excluded; validation belongs to native comparison receipt'}
            path.unlink()
    save(root/'PUBLIKACJA-SEN.json',removed);return removed


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--publikacja',type=Path,required=True)
    args=parser.parse_args();print('Removed payloads:',len(prepare_publication(args.publikacja)))
