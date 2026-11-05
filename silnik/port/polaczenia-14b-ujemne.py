pass                                                                       
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
A=load('negative14a_for_b','polaczenia-ujemne.py')
G=load('negative_recipes14b','przypadki-14b.py')

def cases():
    result=[]
                                                                              
                                                                           
    for item in A.cases():
        if item['variant'] not in ('PUBLIC','GUARD'):continue
        row=dict(item)
        for key in ('input','reference_input'):
            row[key]=row[key].replace(b'PORT14 A ',b'PORT14 B ').replace(b'PORT14  A ',b'PORT14  B ')
        row['stderr']=item['stderr'].replace(b'PORT14A:',b'PORT14B:')
        result.append(row)
    good=''.join(G.text(G.cases('DIRECT',1))).encode('ascii')
    lines=good.splitlines(keepends=True);first=next(i for i,l in enumerate(lines) if l.startswith(b'O '))
    def add(reason,changed,name,reference=good):
        result.append({'key':'DIRECT/'+name,'variant':'DIRECT','reason':'INPUT_'+reason,'input':changed,'reference_input':reference,'code':2,'stderr':('PORT14B: INPUT_'+reason+'\n').encode(),'failure_scope':'operation'})
    for reason,bad in [('ASCII',b'\xef\xbb\xbf'+good),('SPACING',good.replace(b'PORT14 B',b'PORT14  B',1)),('EMPTY_LINE',b'\n'+good),('CR',good.replace(b'\n',b'\r',1)),('TAG',good.replace(b'PORT14',b'PORT15',1)),('PROFILE',good.replace(b'PORT14 B',b'PORT14 A',1)),('N',good.replace(b'DIRECT 1\n',b'DIRECT 0\n',1)),('DECIMAL',good.replace(b'DIRECT 1\n',b'DIRECT 01\n',1)),('TRAILING_DATA',good+b'\n')]:add(reason,bad,reason)
    for reason,line in [('SEQ',b'O 2 210 3 00000000 00000000 00000000\n'),('PHASE',b'O 1 210 3 00000000 00000002 00000001\n'),('UNUSED',b'O 1 210 3 00000000 00000000 00000001\n'),('PROFILE',b'O 1 200 2 00000005 00000000\n'),('ENUM',b'O 1 210 3 00000003 00000000 00000000\n'),('BOOL',b'O 1 210 3 00000000 00000002 00000002\n')]:
        changed=list(lines);changed[first]=line;add(reason,b''.join(changed),'operation-'+reason)
    changed=list(lines);changed[first]=('O 1 31 '+' '.join(f'{x:08x}' for x in (0,G.bits(1/60),1,*([0]*61)))+'\n').encode();add('PROFILE',b''.join(changed),'inherited-Step-forbidden')
    for group,index,word,reason in [(0,2,b'00000002','BOOL'),(0,0,b'00000000','DOMAIN'),(3,2,b'00000000','ROTATION')]:
        changed=list(lines);at=next(i for i,l in enumerate(lines) if l.startswith(f'F14 1 0 {group} '.encode()));parts=changed[at].split();parts[5+index]=word;changed[at]=b' '.join(parts)+b'\n';add(reason,b''.join(changed),'fixture-'+reason)
                                                                           
    good_public=''.join(G.text((G.Case(1,'PARSER-R','PUBLIC','parser',tuple(G.pair(5))),))).encode()
    for reason,old,new in [('BOOL',b'O 4 200 2 00000005 00000000\n',b'O 4 200 2 00000005 00000000\nO 5 202 3 00000000 00000006 00000002\n')]:
        changed=good_public.replace(b'C 1 5\n',b'C 1 6\n').replace(old,new).replace(b'O 5 201',b'O 6 201')
        add(reason,changed,'revolute-field6-bool',good_public.replace(b'C 1 5\n',b'C 1 6\n').replace(old,new.replace(b'00000002\n',b'00000001\n')).replace(b'O 5 201',b'O 6 201'))
    return result

def decimal_transport(data):
    pass                                                                      
    output=[]
    for line in data.splitlines(keepends=True):
        tokens=list(re.finditer(rb'\S+',line));start=len(tokens)
        if tokens and tokens[0][0]==b'O' and len(tokens)>2:
            try:start=4 if int(tokens[2][0])>=200 else 3
            except ValueError:pass
        elif tokens and tokens[0][0]==b'F14':start=5
        elif tokens and tokens[0][0]==b'GA14':start=2
        elif tokens and tokens[0][0] in (b'P13B',b'U13B'):start=4
        for match in reversed(tokens[start:]):
            if re.fullmatch(rb'[0-9a-f]{8}',match[0]):line=line[:match.start()]+str(int(match[0],16)).encode()+line[match.end():]
        output.append(line)
    return b''.join(output)


def run(binary,out,decimal=False):
    results=[]
    inherited_decimal={r['key']:r for r in A.cases(True) if r['variant'] in ('PUBLIC','GUARD')} if decimal else {}
    for item in cases():
        if decimal:
            if item['key'] in inherited_decimal:
                native=inherited_decimal[item['key']]
                item={**item,**{key:native[key].replace(b'PORT14 A ',b'PORT14 B ').replace(b'PORT14  A ',b'PORT14  B ') for key in ('input','reference_input')}}
            else:item={**item,'input':decimal_transport(item['input']),'reference_input':decimal_transport(item['reference_input'])}
        good=subprocess.run([str(binary)],input=item['reference_input'],capture_output=True,timeout=15)
        bad=subprocess.run([str(binary)],input=item['input'],capture_output=True,timeout=15)
        terminal=not any(l.startswith(b'END ') for l in bad.stdout.splitlines())
        header_bad=item['reason'] in ('INPUT_ASCII','INPUT_SPACING','INPUT_EMPTY_LINE','INPUT_CR','INPUT_TAG','INPUT_N','INPUT_DECIMAL')
        ok=good.returncode==0 and not good.stderr and bad.returncode==2 and bad.stderr==item['stderr'] and terminal and (not header_bad or not bad.stdout)
        results.append({'key':item['key'],'reason':item['reason'],'ok':ok,'exit':bad.returncode,'stderr':bad.stderr.decode(errors='replace'),'bytes':len(bad.stdout),'sha256':hashlib.sha256(bad.stdout).hexdigest(),'inputSHA':hashlib.sha256(item['input']).hexdigest(),'goodSHA':hashlib.sha256(item['reference_input']).hexdigest(),'goodExit':good.returncode,'goodStderr':good.stderr.decode(errors='replace'),'noEND':terminal,'badSnapshots':bad.stdout.count(b'Z13 '),'goodSnapshots':good.stdout.count(b'Z13 ')})
    neighbours=[]
    for profile,count in (('PUBLIC',1),('DIRECT',1),('GUARD',1)):
        good=''.join(G.text(G.cases(profile,count),decimal)).encode('ascii')
        for form,data in (('CRLF',good.replace(b'\n',b'\r\n')),('complete-EOF',good[:-1])):
            run=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
            neighbours.append({'profile':profile,'form':form,'exit':run.returncode,'stderr':run.stderr.decode(errors='replace'),'ok':run.returncode==0 and not run.stderr,'inputSHA':hashlib.sha256(data).hexdigest(),'snapshots':run.stdout.count(b'Z13 ')})
    reasons=sorted({r['reason'] for r in results if r['ok']})
    cache=[]
    for byte in (0,256):
        words=[0]*64;words[47]=byte
        data=('PORT14 B PUBLIC 1\nC 1 1\nO 1 120 '+' '.join(f'{x:08x}' for x in words)+'\n').encode('ascii')
        if decimal:data=decimal_transport(data)
        native=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
        cache.append({'cacheByte':byte,'input':data.decode('ascii'),'exit':native.returncode,'stderr':native.stderr.decode(errors='replace'),'stdoutSHA':hashlib.sha256(native.stdout).hexdigest(),'ok':native.returncode==2 and native.stderr==b'PORT14B: INPUT_PROFILE\n' and not any(l.startswith(b'END ') for l in native.stdout.splitlines())})
    unavailable={'reason':'INPUT_CACHE','executed_as_cache':False,'why':'Legacy O120 is refused by PORT13C before raw-cache validation; B DIRECT permits only O210 and its frozen fields have no cache byte.',
                 'source':[{'path':name,'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()} for name in ('kontrola-lancuchy.c','kontrola-polaczenia.c','kontrola-14b.h')],
                 'native_public_boundary':cache,'boundary_proved':all(r['ok'] for r in cache) and cache[0]['stdoutSHA']==cache[1]['stdoutSHA']}
    receipt={'transport':'D-u32' if decimal else 'C-H8','trials_complete':all(r['ok'] for r in results) and all(r['ok'] for r in neighbours),'complete':False,'neighbours':neighbours,'trials':len(results),'passed':sum(r['ok'] for r in results),'classes_executed':reasons,'results':results,'unavailable':[unavailable],'unexecuted':['INPUT_CACHE reachability proof required by the full14b gate'],'binarySHA':hashlib.sha256(binary.read_bytes()).hexdigest()}
    out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--decimal',action='store_true');args=parser.parse_args()
    result=run(args.binary,args.out,args.decimal);print(json.dumps({k:result[k] for k in ('complete','trials','passed','classes_executed')}));sys.exit(not result['complete'])
