pass                                                                       

                                                                             
                                                                            
   
import importlib.util
import io
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('test14_comparison',HERE/'porownaj-polaczenia.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)


def hrow(tag,*words):return (tag+' '+' '.join(f'{x:08x}' for x in words)+'\n').encode()


def fixture():
    case=c.generator.Case(1,'helper-only','PUBLIC','format',(c.generator.op(200,0,0),))
    summary=[0]*20;summary[6]=1;summary[15]=1;summary[17]=1
    body=[b'E14 1 1 200 2 00000000 00000000\n',b'A14 1 1 0 0\n',
          b'J14 1 1 5 16 0 6 19 '+b' '.join(f'{x:08x}'.encode() for x in (0,0,0,0,0,0x3f800000,0,0,0,0,0,0x47c35000,0,0,0,0,0,0,0))+b'\n',
          b'J14 1 1 0 16 0 8 20 '+b' '.join(f'{x:08x}'.encode() for x in summary)+b'\n']
    for tag,n in (('Z8',26),('Z9',16),('Z10',5),('Z11',3),('I12',11),('Z12',2),('Z13',18)):
        words=[0]*n
        if tag=='Z12':words[1]=1
        if tag=='Z9':words[12]=14
        if tag=='Z13':words[13]=1;words[17]=1                                    
        body.append(f'{tag} 1 1 '.encode()+b' '.join(f'{x:08x}'.encode() for x in words)+b'\n')
    return case,b'PORT14 A PUBLIC 1\nCASE 1 1\n'+b''.join(body)+b'ENDCASE 1\nEND 1\n'


class Comparison14(unittest.TestCase):
    def compare(self,data,**kwargs):
        case,_=fixture();return c.compare_streams({'c0':io.BytesIO(data),'c1':io.BytesIO(data)},[case],**kwargs)

    def test_identical_complete_format_is_not_full_acceptance(self):
        _,data=fixture();r=self.compare(data)
        self.assertTrue(r['word_comparison_ok']);self.assertEqual(r['snapshots'],1)
        self.assertFalse(r['full_acceptance']);self.assertFalse(r['full_ownership_ready'])

    def test_same_missing_summary_on_both_sides_is_red(self):
        _,data=fixture();data=b'\n'.join(x for x in data.split(b'\n') if not x.startswith(b'J14 1 1 0 16 0 8'))
        r=self.compare(data);self.assertFalse(r['word_comparison_ok']);self.assertIn('validation',r['errors'][0])

    def test_same_wrong_count_on_both_sides_is_red(self):
        _,data=fixture();data=data.replace(b'J14 1 1 5 16 0 6 19 ',b'J14 1 1 5 16 0 6 18 ')
        self.assertFalse(self.compare(data)['word_comparison_ok'])

    def test_same_duplicate_or_order_change_is_red(self):
        _,data=fixture();row=next(x+b'\n' for x in data.splitlines() if x.startswith(b'J14 1 1 5 '))
        self.assertFalse(self.compare(data.replace(row,row+row))['word_comparison_ok'])
        a=b'A14 1 1 0 0\n';self.assertFalse(self.compare(data.replace(a,b'').replace(row,row+a))['word_comparison_ok'])

    def test_echo_payload_compared_to_input_even_when_both_equal(self):
        _,data=fixture();data=data.replace(b'E14 1 1 200 2 00000000 00000000',b'E14 1 1 200 2 00000000 00000001')
        self.assertFalse(self.compare(data)['word_comparison_ok'])

    def test_truncation_and_extra_global_end_fail(self):
        _,data=fixture()
        for bad in (data[:-6],data+b'END 1\n'):
            with self.assertRaises(ValueError):self.compare(bad)

    def test_ascii_h8_decimal_arity_and_q14_line_envelope(self):
        for raw in (b'A14 01 1 0 0\n',b'A14 1 1 0 9\n',b'E14 1 1 200 2 0000000A 00000000\n',
                    b'A14 1 1 0 0\r\n',b'A14 1 1 0 0 \n',b'X'*131073+b'\n'):
            with self.subTest(raw=raw[:60]):
                with self.assertRaises(ValueError):c.parse(raw)

    def test_partial_model_cannot_grant_full_ownership(self):
        class Partial:
            full_ownership_ready=False
            def __init__(self,**kwargs):pass
            def check(self,*args):return {'joint_structure_checked':True}
        case,data=fixture();r=c.compare_streams({s:io.BytesIO(data) for s in ('c0','c1','d')},[case],checker_factory=Partial)
        self.assertTrue(r['word_comparison_ok']);self.assertTrue(r['DucklingChecked']);self.assertFalse(r['full_acceptance'])

    def test_exact_obs_projection_groups_and_public_preservation(self):
        for group in c.PRIVATE_J:
            words=[0]*c.J_ARITY[group]
            raw=f'J14 1 1 0 0 0 {group} {len(words)} '.encode()+b' '.join(b'00000000' for x in words)+b'\n'
            self.assertIsNone(c.project(raw))
        for raw in (b'J14 1 1 0 0 0 0 8 '+b' '.join([b'00000000']*8)+b'\n',
                    b'L14 1 1 0 0 0 0 1 00000000\n'):
            self.assertEqual(c.project(raw),raw)
        raw=b'J14 1 1 0 16 0 8 20 '+b' '.join(f'{i + 1:08x}'.encode() for i in range(20))+b'\n'
        projected=c.parse(c.project(raw))[1][7:]
        self.assertEqual(projected,tuple(0 if i in c.ZERO_J8 else i+1 for i in range(20)))

    def test_full_word_error_ledger_outlives_bounded_window(self):
                                                                               
                                                                            
        from dataclasses import replace
        case,data=fixture();bodies=[];changed=[]
        for ident in range(1,5):
            lines=[]
            for raw in data.splitlines():
                p=raw.split()
                if p[0] in (b'PORT14',b'END'):continue
                p[1]=str(ident).encode();lines.append(b' '.join(p)+b'\n')
            original=b''.join(lines);bodies.append(original)
            modified=[]
            for raw in lines:
                p=raw.split()
                if p[0]==b'J14' and p[6]==b'6':p[8:]=[b'00000001']*19
                modified.append(b' '.join(p)+b'\n')
            changed.append(b''.join(modified))
        header=b'PORT14 A PUBLIC 4\n';end=b'END 4\n';sink=io.StringIO()
        r=c.compare_streams({'c0':io.BytesIO(header+b''.join(bodies)+end),'c1':io.BytesIO(header+b''.join(changed)+end)},[replace(case,id=i) for i in range(1,5)],error_sink=sink)
        self.assertEqual(r['errorCount'],76);self.assertEqual(len(sink.getvalue().splitlines()),76)
        self.assertEqual(len(r['errors']),64);self.assertLessEqual(len(str(r['errors']).encode()),65536)
        self.assertTrue(all('field' in e and 'W' in e and 'left' in e and 'right' in e for e in r['errors']))


if __name__=='__main__':unittest.main()
