pass                                                                         

                                                                            
                                                                       
   
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('w2_base13_model',HERE/'model-polaczenia.py')
m = importlib.util.module_from_spec(spec);sys.modules[spec.name] = m;spec.loader.exec_module(m)
DATA = json.loads((HERE/'polaczenia-w2-base13-chain.json').read_text(encoding='utf-8'))


def native(binary, side, out):
    out = Path(out).resolve()
    if not out.is_relative_to(ROOT.resolve()): raise ValueError('output outside assigned tree')
    out.mkdir(parents=True,exist_ok=True)
    data = DATA['input_d' if side == 'd' else 'input_c'].encode('ascii')
    start = time.monotonic()
    run = subprocess.run([str(binary)],input=data,capture_output=True,timeout=60)
    model = m.Model14A(observer=True);records=[];results=[];seen_end=False
    def flush():
        if not records:return
        seq = records[0][1][1]
        try:
            result = model.check(1,seq,DATA['operations'][seq-1],records,True)
            results.append({'seq':seq,'ok':True,'model':result})
        except Exception as exc:
            results.append({'seq':seq,'ok':False,'error':type(exc).__name__+': '+str(exc)})
        records.clear()
    for line in run.stdout.splitlines(keepends=True):
        tag,v = m.parse(line)
        if tag in ('PORT14','CASE'): continue
        if tag in ('E14','ENDCASE','END'): flush()
        if tag == 'END':seen_end=True
        if tag not in ('ENDCASE','END'):records.append((tag,v))
    rows = [m.parse(line) for line in run.stdout.splitlines(keepends=True)]
    last_seq = len(DATA['operations'])
    final_status = [list(v[2:]) for t,v in rows if t == 'A14' and v[1] == last_seq]
    final_chains = [v for t,v in rows if t == 'CH13' and v[1] == last_seq]
    runtime_ok = run.returncode == 0 and run.stderr == b'' and seen_end
    ok = runtime_ok and len(results) == last_seq and all(r['ok'] for r in results) and final_status == [[0,0]]
    receipt = {'argv':[str(binary)],'side':side,'exit':run.returncode,'stderr':run.stderr.decode('ascii',errors='backslashreplace'),
        'sourceSHA256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
                        ('model-polaczenia.py','kontrola-polaczenia.c','polaczenia.dk')},
        'inputSHA256':hashlib.sha256(data).hexdigest(),'outputSHA256':hashlib.sha256(run.stdout).hexdigest(),
        'binarySHA256':hashlib.sha256(Path(binary).read_bytes()).hexdigest(),'stdoutBytes':len(run.stdout),
        'seconds':time.monotonic()-start,'native_product':True,'runtime_ok':runtime_ok,
        'snapshots':results,'final_status':final_status,'final_CH13':final_chains,'ok':ok,
        'scope':'partial BASE13+14 model on native output, not full acceptance','full_acceptance':False}
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'side':side,'snapshots':len(results),'model_passed':sum(r['ok'] for r in results),'ok':ok,'full_acceptance':False}))
    return int(not ok)


class PortableBase13Witness(unittest.TestCase):
    def test_existing_legal_prefix_contains_joint_before_chain(self):
        codes = [r['opcode'] for r in DATA['operations']]
        self.assertEqual(codes[-1],100)
        self.assertIn(201,codes[:-1])
        self.assertEqual(DATA['input_c'].splitlines()[0],'PORT14 A PUBLIC 1')
        self.assertEqual(DATA['expected_final_status'],[0,0])
        self.assertFalse(DATA['full_model_ready'])

    def test_both_encodings_carry_identical_bits_and_points(self):
        c = DATA['input_c'].splitlines();d = DATA['input_d'].splitlines()
        self.assertEqual(len(c),len(d))
        for left,right in zip(c,d):
            a,b = left.split(),right.split()
            if a[0] in ('PORT14','C'): self.assertEqual(a,b);continue
            width = 4 if a[0] in ('P13B','U13B') or int(a[2])>=200 else 3
            self.assertEqual(a[:width],b[:width])
            self.assertEqual([int(x,16) for x in a[width:]],[int(x) for x in b[width:]])


if __name__ == '__main__':
    if '--native' in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--native',required=True,type=Path)
        parser.add_argument('--side',required=True,choices=('c1','d'));parser.add_argument('--out',required=True,type=Path)
        args=parser.parse_args();sys.exit(native(args.native,args.side,args.out))
    unittest.main()
