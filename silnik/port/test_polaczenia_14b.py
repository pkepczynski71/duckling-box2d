pass                                                                           
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('functional14b_test',HERE/'odbior-14b.py')
T=importlib.util.module_from_spec(spec);sys.modules[spec.name]=T;spec.loader.exec_module(T)

class Formats14B(unittest.TestCase):
    def test_manifest_is_exact_received_bytes(self):
        self.assertEqual(hashlib.sha256(T.G.MANIFEST_BYTES).hexdigest(),'e04bd8e4c37ceda58236b42f5efef1b6f548f07723cd1b756189ebfc323fe6f0')

    def test_all_typed_direct_inputs_are_initial_fixtures(self):
        cases=T.G.cases('DIRECT')
        self.assertEqual(len(cases),128)
        self.assertEqual(sum(len(c.fixtures) for c in cases),660)
        self.assertEqual(sum(len(c.fixtures)==6 for c in cases),20)
        for i,case in enumerate(cases):
            self.assertEqual(case.fixtures[1][3],5 if i<64 else 4)
            self.assertEqual(len(case.fixtures[2]),30 if i<64 else 34)
            self.assertEqual([op['a'] for op in case.ops[:4]],[(0,0,0),(0,1,0),(0,2,1),(0,2,0)])

    def test_all_guards_and_positive_steps(self):
        cases=T.G.cases('GUARD')
        self.assertEqual(len(cases),221)
        self.assertEqual(sum(op['opcode'] in (31,32) and T.G.value(op['a'][1])>0 for c in cases for op in c.ops),26)

    def test_active_payload_and_view_lengths(self):
        for group,length,type in ((3,30,None),(3,34,None),(4,50,5),(4,51,4),(6,21,5),(6,22,4),(12,1,None),(12,2,None)):
            payload=[0]*length
            if type is not None:payload[0]=type
            raw=(f'J14 1 1 0 16 0 {group} {length} '+' '.join(f'{x:08x}' for x in payload)+'\n').encode()
            self.assertEqual(T.C.parse(raw)[0],'J14')
        raw=b'J14 1 1 0 16 0 6 21 00000004 '+b' '.join([b'00000000']*20)+b'\n'
        with self.assertRaisesRegex(ValueError,'active'):T.C.parse(raw)

    def test_profile_is_B_and_axis_reason_is_9(self):
        self.assertEqual(T.C.parse(b'PORT14 B DIRECT 128\n'),('PORT14',('DIRECT',128)))
        self.assertEqual(T.C.parse(b'A14 1 6 5 9\n'),('A14',(1,6,5,9)))
        with self.assertRaises(ValueError):T.C.parse(b'PORT14 A DIRECT 128\n')

    def test_math_fixture_domains(self):
        self.assertEqual(T.C.parse(b'EF14 1 1 5 1 40490fdc\n')[0],'EF14')
        self.assertEqual(T.C.parse(b'EF14 1 2 5 6 '+b' '.join([b'00000000']*6)+b'\n')[0],'EF14')
        with self.assertRaises(ValueError):T.C.parse(b'EF14 1 1 5 2 00000000 00000000\n')

    def test_bits_have_identical_C_and_D_inputs(self):
        cases=T.G.cases('DIRECT')
        c=list(T.G.text(cases));d=list(T.G.text(cases,True))
        self.assertEqual(len(c),len(d))
        for h,decimal in zip(c,d):
            hp,dp=h.split(),decimal.split()
            start=5 if hp[0]=='F14' else 4 if hp[0]=='O' else len(hp)
            self.assertEqual(hp[:start],dp[:start])
            self.assertEqual([int(v,16) for v in hp[start:]],[int(v) for v in dp[start:]])

    def test_short_public_allocation(self):
        cases=T.G.cases('PUBLIC',24)
        self.assertEqual(len(cases),24)
        self.assertTrue(all(len(c.ops)<=128 for c in cases))

    def test_public_has_no_private_phase_or_seed_opcode(self):
                                                                       
        forbidden={41,42,43,44,45,51,52,53,64,120,210,211}
        for case in T.G.cases('PUBLIC'):
            self.assertFalse(any(o['opcode'] in forbidden for o in case.ops),case.key)

    def test_bridge_annex_only_six_case_bounds(self):
                                                                     
        entries=T.G.MANIFEST['przypadki']
        self.assertEqual(sum(e['opMax'] for e in entries),103008)
        self.assertEqual([e['id'] for e in entries if e['opMax']==2048],list(range(49,55)))
        for case in T.G.cases('PUBLIC')[48:54]:
            self.assertGreater(len(case.ops),1328)
            self.assertLessEqual(len(case.ops),2048)
            self.assertEqual(sum(o['opcode']==90 for o in case.ops),47)
            self.assertEqual(sum(o['opcode']==40 for o in case.ops),46)
            self.assertEqual(sum(o['opcode']==201 for o in case.ops),42)
            self.assertEqual(sum(o['opcode'] in (31,32) for o in case.ops),1200)

if __name__=='__main__':unittest.main()
