pass                                                                         
import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('zywy_positive_inputs',HERE/'przypadki-zywy.py')
g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)

class Frozen12a(unittest.TestCase):
    def test_complete72_ids_and_all28800_positive_steps(self):
        rows=g.verify();self.assertEqual([c.id for c in rows],list(range(1,73)))
        self.assertEqual(sum(r[0] in (31,32) and g.number(r[2])>0 for c in rows for r in c.ops),28800)
        for c in rows[48:]:
            self.assertFalse(any(r[0] in (31,32) and g.number(r[2])>0 for r in c.ops))

    def test_each_long_family_has_all_six_frozen_configs(self):
        for family in range(1,9):
            entries=[m for m in g.MANIFEST['przypadki'] if m['rodzina']=='A'+str(family)]
            self.assertEqual({(m['podkroki'],m['warm']) for m in entries},{(n,w) for n in (1,4,8) for w in (0,1)})
            self.assertTrue(all(m['dtH']=='3c888889' and m['liczbaKrokowDodatnich']==600 for m in entries))

    def test_C_and_D_share_all64_input_words_without_float_text_conversion(self):
        rows=g.verify();c=g.encode(rows).splitlines();d=g.encode(rows,True).splitlines()
        self.assertEqual(len(c),len(d))
        for a,b in zip(c,d):
            x,y=a.split(),b.split()
            if x[0]!='O':self.assertEqual(x,y);continue
            self.assertEqual(x[:3],y[:3]);self.assertEqual(len(x),67)
            self.assertEqual([int(v,16) for v in x[3:]],[int(v) for v in y[3:]])

    def test_90_reuses_all19_fields_of_57_before_the_extensions(self):
        before=g.g.body(slot=7,owner=1,p=(.25,-.5),q=(.8,.6),enable=0,awake=0)
        after=g.body(slot=7,owner=1,p=(.25,-.5),q=(.8,.6),enable=0,awake=0,enabled=0,name=b'A')
        self.assertEqual(after[1:20],before[1:20])
        self.assertEqual(after[20:23],(0,1,65))

    def test_math_axes_keep_all_four_signed_zero_inputs_and_fit32_fixture_limit(self):
        rows=g.math_components();self.assertLessEqual(len(rows),32)
        pairs={r[1:3] for r in rows if r[0]==100}
        self.assertTrue({(x,y) for x in (0,0x80000000) for y in (0,0x80000000)}<=pairs)
        self.assertTrue(any(r[0]==101 for r in rows))

if __name__=='__main__':unittest.main()
