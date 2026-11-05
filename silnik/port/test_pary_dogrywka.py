pass                                                                           
from dataclasses import replace
import io
import json
import unittest
from test_pary import HERE,g,p,module
from test_pary_ci import work
from test_pary_porownanie import fixture,mutate

class AnchorWitness(unittest.TestCase):
    def test_old_native_mutant_was_identical_to_the_original(self):
        evidence=json.loads((HERE/'dowod-pary-dogrywka1.json').read_bytes())
        self.assertEqual(evidence['C_sha256'],evidence['kk_anchorB']['sha256'])
        self.assertEqual(evidence['kk_anchorB']['records']['M'],448)
    def test_repaired_witness_has_contact_and_a_nonzero_anchor_offset(self):
        case=g.cases()[156];f=g.f32
        self.assertEqual((case.id,case.kind),(157,2))
        self.assertEqual(case.b.words[0],g.bits(.2))
                                                             
        axis_offset=f(g.number(case.b.words[0])-g.number(case.b.words[5]))
        radius=f(g.number(case.a.words[8])+g.number(case.b.words[8]))
        limit=f(radius+f(.02))
        self.assertLess(f(axis_offset*axis_offset),f(limit*limit))
        old_offset=f(f(-.4)-g.number(case.b.words[5]))
        self.assertGreater(f(old_offset*old_offset),f(limit*limit))
                                                                          
                                                                        
        anchor_a=f(axis_offset*.5);anchor_b=f(anchor_a-g.number(case.b.words[0]))
        self.assertEqual(g.bits(anchor_a),0xbdcccccd)
        self.assertEqual(g.bits(anchor_b),0xbe99999a)
        self.assertNotEqual(g.bits(anchor_a),g.bits(anchor_b))
        self.assertNotEqual(g.cases()[188].a.words[:2],g.cases()[188].b.words[:2])
    def test_repaired_cases_are_not_other_mutations_prescribed_witnesses(self):
        recipes=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']
        self.assertEqual(len(recipes),48)
        for recipe in recipes:
            if recipe['probe']=='physics' and recipe['name']!='kk-anchorB':
                self.assertTrue({157,189}.isdisjoint(recipe['witness_ids']),recipe['name'])

class FiniteRefusal(unittest.TestCase):
    def setUp(self):
        self.ci=module('pair_followup_detection','ci-pary.py');self.ci.p=p
        self.ci.negative=module('pair_followup_negative','ujemne-pary.py')
        recipes=json.loads((HERE/'mutacje-pary.json').read_bytes())['native_mutations']
        self.recipe=next(r for r in recipes if r['name']=='parser-finite')
        self.evidence=json.loads((HERE/'dowod-pary-dogrywka1.json').read_bytes())
        self.rows,self.legal=fixture(g.small_cases())
        lines=self.legal.splitlines(keepends=True)
                                                                               
        lines[1:3]=self.evidence['parser_finite']['head'][1:3]
        self.accepted=''.join(lines)
    def detect(self,text,code=0,stderr=b'',recipe=None):
        with work() as directory:
            out=directory/'out.csv';err=directory/'err.csv';reference=directory/'C.csv'
            out.write_bytes(text.encode('ascii'));err.write_bytes(stderr);reference.write_bytes(self.legal.encode('ascii'))
            return self.ci.detection(recipe or self.recipe,code,out,err,reference,self.rows)
    def test_native_missing_refusal_is_detected_despite_nonfinite_geometry(self):
        self.assertEqual(self.evidence['parser_finite_code'],0)
        self.assertEqual(self.evidence['parser_finite_stderr'],'')
        detected,detail=self.detect(self.accepted)
        self.assertTrue(detected);self.assertEqual(detail['cause'],'missing finite-input refusal')
        self.assertEqual(detail['expected_original_code'],3)
        self.assertEqual(detail['expected_stderr'],'BLAD: NaN/Inf.\n')
        self.assertIn('normal.x',detail['nonfinite_fields'])
        finite_frame=self.accepted.replace(self.evidence['parser_finite']['head'][2],self.legal.splitlines(keepends=True)[2],1)
        detected,detail=self.detect(finite_frame)
        self.assertTrue(detected);self.assertEqual(detail['nonfinite_fields'],[])
    def test_no_exception_for_physics_or_another_parser_mutation(self):
        legal_echo_bad_M=self.legal.replace(self.legal.splitlines(keepends=True)[2],self.evidence['parser_finite']['head'][2],1)
        physics={'probe':'physics','witness_ids':[1],'fields':['normal.x']}
        self.assertFalse(self.detect(legal_echo_bad_M,recipe=physics)[0])
        other={**self.recipe,'name':'another-parser-guard'}
        self.assertFalse(self.detect(self.accepted,recipe=other)[0])
        with self.assertRaisesRegex(ValueError,'NaN/Inf'):
            p.validate_output(io.StringIO(legal_echo_bad_M),self.rows)
    def test_bad_echo_other_case_or_initialized_field_cannot_use_the_exception(self):
                                                                        
        self.assertFalse(self.detect(self.accepted.replace(self.accepted.splitlines(keepends=True)[1],self.legal.splitlines(keepends=True)[1],1))[0])
        for field,value in ((3,3),(15,65536),(16,2),(2,0x7fc00001),(11,0x7fc00001),(17,0x7fc00001)):
            self.assertFalse(self.detect(mutate(self.accepted,'M',field+1,value))[0],field)
        lines=self.accepted.splitlines(keepends=True)
        second=next(i for i,line in enumerate(lines) if line.startswith('M 2 '))
        tag,words=p.parse_record(lines[second]);words=list(words);words[1]=0x7fc00001
        lines[second]=p.format_record(tag,words)
        self.assertFalse(self.detect(''.join(lines))[0])
    def test_crash_stderr_wrong_N_truncation_and_record_order_are_rejected(self):
        for code in (-6,3,4,124,125,126,127):self.assertFalse(self.detect(self.accepted,code=code)[0])
        self.assertFalse(self.detect(self.accepted,stderr=b'BLAD: NaN/Inf.\n')[0])
        self.assertFalse(self.detect(self.accepted.replace('PORT9A 7','PORT9A 6',1))[0])
        self.assertFalse(self.detect(self.accepted[:-8])[0])
        lines=self.accepted.splitlines(keepends=True);lines[1],lines[2]=lines[2],lines[1]
        self.assertFalse(self.detect(''.join(lines))[0])

if __name__=='__main__':unittest.main()
