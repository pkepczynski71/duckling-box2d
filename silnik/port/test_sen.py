from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                            
from collections import Counter
import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('sen_test_inputs','przypadki-sen.py');p=load('sen_test_compare','porownaj-sen.py')


class FrozenInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=g.verify()[:128]                                          

    def test_all128_and16_exact_steps_from_frozen_manifest(self):
        self.assertEqual([c.id for c in self.rows],list(range(1,129)))
        self.assertEqual(len(g.components()),16)
        actual=Counter()
        for c,m in zip(self.rows,g.MANIFEST['przypadki']):
            for r in c.ops:
                if r[0] not in (31,32):continue
                if g.number(r[2])>0:actual['long' if m['opMax']==1280 else 'short']+=1
                elif r[0]==31:actual['other_raw']+=1
        self.assertEqual(actual,Counter(long=115200,short=64,other_raw=2))
        self.assertEqual({(m['podkroki'],m['warm']) for m in g.MANIFEST['przypadki'] if m['rodzina']=='A1'},
                         {(n,w) for n in (1,4,8) for w in (0,1)})

    def test_decimal_and_hex_input_are_the_same64_u32_words(self):
        rows=self.rows[:1]
        for c,d in zip(g.encode(rows).splitlines(),g.encode(rows,True).splitlines()):
            a,b=c.split(' '),d.split(' ')
            if a[0]!='O':self.assertEqual(a,b);continue
            self.assertEqual(a[:3],b[:3]);self.assertEqual(len(a),67)
            self.assertEqual(tuple(int(x,16) for x in a[3:]),tuple(map(int,b[3:])))


class LiteralExamples(unittest.TestCase):
    def test_every_new_frozen_record_roundtrips_with_its_exact_width(self):
        text=norm_text(HERE/'fixtures/norms/KONTRAKT-11.json');inside=False;seen=set()
        expected=set(p.NEW_PRIVATE)|{'SW11','GS11','I11','Z11'}
        for line in text.splitlines():
            if line.startswith('```'):inside=line=='```text';continue
            if inside and line.split(' ',1)[0] in expected:
                tag,v=p.parse_record(line+'\n');self.assertEqual(p.format_record(tag,v),line+'\n');seen.add(tag)
        self.assertEqual(seen,expected)


class SupervisorDecisions(unittest.TestCase):
    def test_D11_2_appends_B15b_without_renumbering_the_frozen_prefix(self):
        rows=g.verify()
        self.assertEqual(len(rows),129)
        self.assertEqual((rows[-1].id,g.MANIFEST['przypadki'][-1]['rodzina']),(129,'B15b'))
        self.assertEqual(sum(r[0] in (31,32) for r in rows[-1].ops),5)


if __name__=='__main__':unittest.main()
