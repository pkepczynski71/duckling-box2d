from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                   
import copy
import importlib.util
from pathlib import Path
import re
import sys
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sen_recovery_model',HERE/'model-sen.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)


def first_frame(case=1,corrupt=False):
    text=norm_text(HERE/'fixtures/norms/KONTRAKT-11.json')
    section=text.split('### 6.3.',1)[1].split('## 7.',1)[0]
    sample=next(s for s in re.findall(r'```text\n(.*?)```',section,re.S) if s.startswith('GUARD11 1\nG ') and '\nCASE ' in s)
    rows=[]
    for line in sample.splitlines(keepends=True):
        tag,value=m.parse(line)
        if tag not in m.RANK or value[:2]!=(1,1):continue
        value=(case,*value[1:])
        if corrupt and tag=='SS11' and value[3]==2:
            value=(*value[:6],1,*value[7:])                                     
        rows.append((tag,value))
        if tag=='Z11':break
    operation=next(v[2:] for t,v in rows if t=='E')
    return operation,rows


class CaseRecovery(unittest.TestCase):
    def test_healthy_boundaries_still_reject_ticket_reset(self):
        model=m.OwnershipModel();operation,rows=first_frame()
        model.check(1,1,operation,rows)
        operation,rows=first_frame(2)
        with self.assertRaisesRegex(ValueError,'ticket allocation order'):
            model.check(2,1,operation,rows)

    def test_failed_case_is_not_forgiven_and_next_case_is_checked(self):
        model=m.OwnershipModel();operation,rows=first_frame(corrupt=True)
        with self.assertRaises(ValueError):model.check(1,1,operation,rows)
        with self.assertRaisesRegex(ValueError,'already failed'):
            model.check(1,2,operation,rows)
        operation,rows=first_frame(2);model.check(2,1,operation,rows)
        self.assertEqual(len(model.case_failures),1)
        self.assertEqual(model.continuity_gaps,[{'after_case':1,'before_case':2,'last_verified_ticket':1}])
        operation,rows=first_frame(3,corrupt=True)
        with self.assertRaises(ValueError):model.check(3,1,operation,rows)
        self.assertEqual(len(model.case_failures),2)

    def test_recovery_does_not_disable_ownership_checks(self):
        model=m.OwnershipModel();operation,rows=first_frame(corrupt=True)
        with self.assertRaises(ValueError):model.check(1,1,operation,rows)
        operation,rows=first_frame(2,corrupt=True)
        with self.assertRaises(ValueError):model.check(2,1,operation,rows)
        self.assertEqual([r['case'] for r in model.case_failures],[1,2])


if __name__=='__main__':unittest.main()
