pass                                                                          
import importlib.util,json,sys
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('inputs13c_w2','przypadki-lancuchy.py')
def corpus():return g.cases13c()

def test_manifest_complete_and_step_count(corpus):
    assert [c.id for c in corpus]==list(range(1,433))
    assert sum(c.id<=384 for c in corpus)==384 and sum(c.id>384 for c in corpus)==48
    assert sum(o['opcode'] in (31,32) for c in corpus for o in c.ops)==32400
    assert sum(len(c.ops) for c in corpus[384:])<=38160
    assert sum(len(c.ops) for c in corpus)<=50448
    meta={x['id']:x for x in g.MANIFEST['przypadki'] if x['profil']=='PORT13C'}
    assert all(c.family==meta[c.id]['rodzina'] and len(c.ops)<=meta[c.id]['opMax'] for c in corpus)

def test_invalid_N_rejected(N):
    with unittest.TestCase().assertRaises(ValueError):g.cases13c(N)

def test_direct_literal_and_own_history_seeds(corpus):
    a=[0]*64;a[2:10]=[0x40000000,0,0x3f800000,0,0xbf800000,0,0xc0000000,0]
    a[12]=a[16]=0x3f800000;a[18:22]=[1,0x3f000000,0,0xc0000000]
    assert corpus[0].ops[0]['a']==tuple(a)                                                            
    for c in corpus[:384]:
        assert len(c.ops)==32
        kind=(c.id-1)//128;warm=(c.id-1)%128>=64
        assert all(o['opcode']==120 and o['a'][0]==kind and len(o['a'])==64 and not any(o['a'][43:]) for o in c.ops)
        if warm:
            assert all(o['a'][36:43]==(0,)*7 for o in c.ops[1:])
            if kind==0:assert c.ops[0]['a'][36:43]==(3,0,1,2,2,1,0)
        elif kind==0:assert all(o['a'][36:43]==(0,)*7 for o in c.ops)

def test_each_world_keeps_all_positive_steps_and_exact_dt(corpus):
    for c in corpus[384:]:
        steps=[o['a'] for o in c.ops if o['opcode'] in (31,32)]
        variant=(c.id-385)%6
        assert len(steps)==(1200 if 421<=c.id<=426 else 600)
        assert all(a[1]==0x3c888889 and a[2]==(1,4,8,1,4,8)[variant] for a in steps)

def test_W3_actual_terrain_creation_order(corpus):
    for c in corpus[396:402]:
        chain=next(i for i,o in enumerate(c.ops) if o['opcode']==100)
        moving=next(i for i,o in enumerate(c.ops) if o['opcode']==57 and o['a'][3]==2)
        assert (chain<moving)==((c.id-397)%2==0)

def test_W7_current_replacement_is_shared_literal_and_friction(corpus):
    recipe=json.loads((HERE/'lancuchy-sceny13c.json').read_text(encoding='utf-8'))
    for v,c in enumerate(corpus[420:426]):
        last=next(o for o in reversed(c.ops) if o['opcode']==57)
        assert last['a'][4:6]==tuple(int(x,16) for x in recipe['W7']['replacementPositionBitsByVariant'][v])
        assert all(o['a'][45]==0x3f19999a for o in c.ops if o['opcode']==40)
        assert len([o for o in c.ops if o['opcode']==106])==2

def test_W8_708_and_all_13_checked_refusals(corpus):
    for c in corpus[426:432]:
        assert len(c.ops)==708
        phase=0;after={}
        for o in c.ops:
            if o['opcode'] in (31,32):phase+=1
            else:after.setdefault(phase,[]).append(o)
        refused=after[420]
        assert [(o['opcode'],o['a'][3]) for o in refused]==[(80,0),(80,0),(18,0),(19,0)]+[(81,j) for j in range(9)]
        assert [o['a'][4] for o in refused[:2]]==[1,2]
        assert all(o['a'][2]==1 for o in refused if o['opcode']==81)
        assert [o['opcode'] for o in after[1]][:2]==[101,100]
        assert [o['opcode'] for o in after[2]][:2]==[101,100]
        assert len(after[35])==len(after[36])==4

def test_compare_refuses_nonprefix_case_ids():
    c=load('compare13c_w2','porownaj-lancuchy.py')
    from io import BytesIO
    with unittest.TestCase().assertRaisesRegex(ValueError,'prefix'):
        c.compare13c_streams({'c0':BytesIO(),'c1':BytesIO()},(g.ChainCase(2,'C1',()),),require_history=False)

                                                                          
                                                                               
class Corpus13CW2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.items=corpus()
    def test_manifest(self):check_manifest_complete_and_step_count(self.items)
    def test_invalid_N(self):
        for N in (0,433,-1):
            with self.subTest(N=N):check_invalid_N_rejected(N)
    def test_direct(self):check_direct_literal_and_own_history_seeds(self.items)
    def test_steps(self):check_each_world_keeps_all_positive_steps_and_exact_dt(self.items)
    def test_W3(self):check_W3_actual_terrain_creation_order(self.items)
    def test_W7(self):check_W7_current_replacement_is_shared_literal_and_friction(self.items)
    def test_W8(self):check_W8_708_and_all_13_checked_refusals(self.items)
    def test_prefix(self):check_compare_refuses_nonprefix_case_ids()

                                                                                
for _name in tuple(globals()):
    if _name.startswith('test_'):globals()['check_'+_name[5:]]=globals().pop(_name)
