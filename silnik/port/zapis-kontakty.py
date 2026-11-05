pass                                                                       
from collections import Counter
import hashlib
import json
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
spec=spec_from_file_location('contact_storage_base',HERE/'zapis-strumieni.py');base=module_from_spec(spec);spec.loader.exec_module(base)

def manifest(path):
    value=base.manifest(path);cases={};current=None
    with Path(path).open('rb') as stream:
        for line in stream:
            fields=line.split(b' ',2);tag=fields[0].decode('ascii',errors='backslashreplace')
            if tag=='CASE' and len(fields)==3:
                ident=fields[1].decode('ascii',errors='backslashreplace');current=cases.setdefault(ident,{'bytes':0,'records':Counter()})
            if current is not None:current['bytes']+=len(line);current['records'][tag]+=1
            if tag=='ENDCASE':current=None
    value['cases']={key:{'bytes':item['bytes'],'records':dict(sorted(item['records'].items()))} for key,item in cases.items()}
    return value

def prepare_publication(directory):
    pass                                                                       

                                                                             
                                                                            
       
    root=Path(directory).resolve();removed={}
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(root);name=path.name
        with path.open('rb') as stream:magic=stream.read(4)
        binary=name.endswith('-bin') or path.suffix in ('.o','.a','.so','.dll','.exe') or magic[:4]==b'\x7fELF' or magic[:2]==b'MZ'
        diagnostic=name.endswith(('-stderr.csv','-kod.csv','-polecenie.csv','-console.csv','-czas.csv','-kompilacja.csv'))
        if diagnostic:continue
        input_=relative.parts[0] in ('wejscia-swiat','ujemne-kontakty','zrodla') or name=='input.csv' or name.startswith(('przypadki-kontakty','proba-kontakty'))
        command_log=path.suffix=='.csv' and path.with_name(path.stem+'-kod.csv').is_file()
        metadata=path.suffix in ('.json','.md','.sha256') or name in ('start-unix.csv','zrodla-sha256.csv')
        if not binary and (diagnostic or input_ or command_log or metadata):continue
        digest=hashlib.sha256();size=0
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk);size+=len(chunk)
        entry={'sha256':digest.hexdigest(),'bytes':size,'kind':'binary' if binary else 'raw/unregistered output',
               'validated':False,'reason':'publication excludes payload even after failed compaction'}
        path.with_name(name+'.publication.json').write_text(json.dumps(entry,indent=2)+'\n',encoding='ascii')
        path.unlink();removed[relative.as_posix()]=entry
    report=root/'PUBLIKACJA-KONTAKTY.json'
    if removed or not report.exists():report.write_text(json.dumps(removed,indent=2)+'\n',encoding='ascii')
    return removed

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--publikacja',type=Path,required=True)
    args=parser.parse_args();removed=prepare_publication(args.publikacja)
    print(f'Publikacja 9b: usunieto {len(removed)} E565c805f45f1 E397d50b4e4b3/E7ec1d226e3a2; Ebe0281080332 Ede7d1b721a1e E95d3b17f0fb1 E631f494748f8.')
