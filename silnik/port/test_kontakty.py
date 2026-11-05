from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                                      
from collections import Counter
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from importlib.util import spec_from_file_location,module_from_spec
import sys

HERE=Path(__file__).resolve().parent
def module(name,file):
    spec=spec_from_file_location(name,HERE/file);m=module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
p=module('contacts_test_compare','porownaj-kontakty.py');g=p.g
@contextmanager
def work():
    root=HERE.parents[1]/'_kontakty-tests';root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as name:yield Path(name)
    if not any(root.iterdir()):root.rmdir()

class Inputs(unittest.TestCase):
    def test_64_explicit_individual_scenes_and_operation_budgets(self):
        rows=g.verify();self.assertEqual(len({c.ops for c in rows}),64)
        self.assertEqual(Counter((c.id-1)//4+1 for c in rows),Counter({k:4 for k in range(1,17)}))
        self.assertEqual(sum(len(c.ops) for c in rows),3092)
    def test_frozen_manifest_is_not_replaced_by_generated_metadata(self):
        m=json.loads((HERE/'kontakty-przypadki.json').read_bytes())
        self.assertEqual(m['sumaOpMax'],8448);self.assertEqual(m['N'],64)
        self.assertEqual(len(m['oslony']),34);self.assertEqual(len(m['klasyMutacji']),40)
    def test_words_match_both_committed_encodings(self):
        rows=g.cases();hashes=json.loads((HERE/'wejscia-kontakty-sha256.json').read_bytes())
        for n,name in ((64,'przypadki'),(49,'proba')):
            for dec in (False,True):
                file=name+'-kontakty'+('-stdin' if dec else '')+'.csv';data=(HERE/file).read_bytes()
                self.assertEqual(data,g.encode(rows[:n],dec).encode('ascii'));self.assertEqual(hashes[file],hashlib.sha256(data).hexdigest())
    def test_prototype_includes_family13_with_id49_and_full_population(self):
        c=g.cases()[48];self.assertEqual(c.id,49)
        self.assertEqual(sum(o[0]==30 for o in c.ops),65);self.assertEqual(sum(o[0]==40 for o in c.ops),130)
    def test_negative_raw31_live_contact_witness_is_present(self):
        rows=g.cases()[59].ops;self.assertIn(g.g8.step(raw=True,dt=-1/60,n=1),rows)
        self.assertLess(rows.index(g.op(45)),rows.index(g.g8.step(raw=True,dt=-1/60,n=1)))
    def test_all_scenes_close_capture_and_do_not_mutate_inside(self):
        for c in g.cases():
            phase=0;owner=None
            for code,*a in c.ops:
                if code in range(46,51):continue
                if code==41:self.assertEqual(phase,0);owner=a[0];phase=1
                elif code in range(42,46):
                    self.assertEqual(a[0],owner);self.assertEqual(code,41+phase);phase=(phase+1)%5
                else:self.assertEqual(phase,0,(c.id,code))
            self.assertEqual(phase,0)

class Protocol(unittest.TestCase):
    def test_all_output_examples_parse_and_roundtrip_exactly(self):
        text=norm_text(HERE/'fixtures/norms/KONTRAKT-9B.json');inside=False;count=0
        for line in text.splitlines():
            if line.startswith('```'):inside=line=='```text';continue
            if inside and line.startswith(('C ','O ')):
                ts=line.split(' ');d=2
                self.assertEqual(len(ts),3 if ts[0]=='C' else 67)
                self.assertTrue(all(g.g8.DEC.fullmatch(t) for t in ts[1:3]))
                self.assertTrue(all(g.g8.HEX.fullmatch(t) for t in ts[3:]) or all(g.g8.DEC.fullmatch(t) and int(t)<=g.U32 for t in ts[3:]))
                count+=1;continue
            if inside and line.split(' ',1)[0] in (set(p.SCHEMA)|set(p.p8.FIELDS)):
                tag,v=p.parse_record(line+'\n');self.assertEqual(p.format_record(tag,v),line+'\n');count+=1
        self.assertEqual(count,100)
    def test_projection_preserves_exact_bytes_and_counts(self):
        lines=['PORT9B 1\n',p.format_record('CP',(1,1,0,0,0,0)),p.format_record('Z9',(1,1,*([0]*16))),'END 1\n']
        self.assertEqual(list(p.projection(lines)),[lines[0],lines[2],lines[3]])
    def test_shape_of_each_new_variable_record_is_checked(self):
        fixtures={
            'CD':(1,1,0,0,0,0,0,0),'GL':(1,1,0,0,0,0,0),
            'GE':(1,1,0,0,0,0,0,0,0,0),'GC':(1,1,0,0,0,0,0,0,0,0),
            'GB':(1,1,0,0,1,1,1,0,0),'CB':(1,1,0,0,0,16),
            'BL9':(1,1,0,0,p.NULL,0,p.NULL,p.NULL,p.NULL),'TASK':(1,1,0,0,0,0,0,1,1,1,16,1,0)}
        for tag,v in fixtures.items():
            line=p.format_record(tag,v);self.assertEqual(p.parse_record(line),(tag,v))
            with self.assertRaises(ValueError):p.parse_record(line.rstrip('\n')+' 00000000\n')
    def test_noncanonical_output_and_unknown_tags_are_rejected(self):
        for line in ('PORT9B 01\n','PORT9B 1\r\n','PORT9B 1','PORT9B  1\n','PORT9X 1\n','END 1\n\n'):
            with self.assertRaises(ValueError):p.parse_record(line)
    def test_equal_truncated_streams_are_rejected_before_comparison(self):
        for text in ('','PORT9B 1\n','PORT9B 1\nCASE 1 7\nENDCASE 1\nEND 1\n'):
            with self.assertRaises(ValueError):p.validate_output(text,g.cases()[:1])
    def test_difference_names_contact_field_and_both_words(self):
        a=[1,1,0,1,0,0]+[0]*52;b=a.copy();b[6]=1
        diff=p.first_difference([p.format_record('CS',a)],[p.format_record('CS',b)])
        self.assertEqual(diff['field'],'contactId');self.assertEqual(diff['C'],'00000000');self.assertEqual(diff['Duckling'],'00000001')

class Pools(unittest.TestCase):
    def test_lifo_reuse_and_partition_independent_of_stream_equality(self):
        pool=p.Pool();self.assertEqual([pool.allocate() for _ in range(3)],[0,1,2]);pool.release(1);pool.release(0)
        pool.check((3,2,1),[1,0],{0:(0,),1:(0,),2:(1,)})
        self.assertEqual(pool.allocate(),0)
        with self.assertRaises(ValueError):pool.check((3,1,2),[0],{0:(1,),1:(0,),2:(1,)})
    def test_manifold_inactive_point_is_still_validated(self):
        words=[0]*30;p.manifold(words,'M')
        for index,value in ((28,65536),(29,2),(17,0x7f800000)):
            bad=words.copy();bad[index]=value
            with self.assertRaises(ValueError):p.manifold(bad,'M')
    def test_seeded_first_id_transfer_detects_feature_impulse_and_reset_damage(self):
        from collections import defaultdict
        old=[0]*52;old[0]=0;old[14:21]=g.seed(0)[30:];old[21:51]=g.seed(0)[:30]
        new=old.copy();new[36]=0x201;new[49]=0x300
        for j,source_j in ((0,1),(1,0)):
            k=21+4+13*j;q=21+4+13*source_j
            new[k+7:k+9]=old[q+7:q+9];new[k+9:k+11]=[0,0];new[k+12]=1
        model=p.Model();prior=defaultdict(list);prior['CS']=[(1,1,0,1,0,0,*old)];model.previous=(g.op(51),prior,[])
        model.transfers(0,defaultdict(list),[],{}, {0:((0,1,0,0),tuple(new))})
        duplicate=new.copy();duplicate[49]=duplicate[36];duplicate[45:47]=[0,0]
        model.transfers(0,defaultdict(list),[],{}, {0:((0,1,0,0),tuple(duplicate))})
        duplicate[45]=g.bits(2)
        with self.assertRaises(ValueError):model.transfers(0,defaultdict(list),[],{}, {0:((0,1,0,0),tuple(duplicate))})
        for field in (14,21+2,21+4+7,21+4+8,21+4+9,21+4+10,21+4+11,21+4+12):
            bad=new.copy();bad[field]^=1
            with self.subTest(payload_field=field):
                with self.assertRaises(ValueError):model.transfers(0,defaultdict(list),[],{}, {0:((0,1,0,0),tuple(bad))})

def empty_world_fixture():
                                                                              
    row=g.world(gravity=(0,0));wh=(1,0,0,0x10000,0,0,0,1,0)
    r=[('E',(1,1,*row)),('R',(1,1,0,0,1,*wh)),('V',(1,1,1,0,1,1)),
       ('W',(1,1,0,*wh[:5],1,0,0,0,g.bits(400),0,0,0)),('GE',(1,1,0,0,0,0,0,0,0,0)),
       ('F',(1,1,0,0,0,0,0,0)),('H',(1,1,0,0,16,0,*([0]*48))),('H',(1,1,0,1,32,0,*([0]*96)))]
    r += [('RT',(1,1,0,t,p.NULL,0,16,0,0,0,0,0,0,0,0)) for t in range(3)]
    r += [('JW',(1,1,0,0,0,0,0,0,0,0,0)),('CP',(1,1,0,0,0,0))]
    r += [('CA',(1,1,0,d,i,0)) for d in range(2) for i in range(12 if d else 3)]
    r += [('GB',(1,1,0,c,1,1,1,0,0)) for c in range(11)]
    r += [('GB',(1,1,0,11,0,0,0)),('CB',(1,1,0,0,0,16)),('IP',(1,1,0,0,0,0)),('EN9',(1,1,0,0,0,0,0,0))]
    counts=Counter(t for t,v in r)
    r += [('I8',(1,1,*(counts[t] for t in ('X','P','T','F','U','H','Y','DN','RT','JW')))),
          ('I9',(1,1,*(counts[t] for t in p.PRIVCOUNTS),0,1)),
          ('Z8',(1,1,1,0,0,1,0,0,*(counts[t] for t in p.p8.PUBLIC_COUNTS),1,0)),
          ('Z9',(1,1,0,0,0,*(counts[t] for t in p.PUBCOUNTS),1,1,1,0,1,0))]
    records=[('PORT9B',(1,)),('CASE',(1,1)),*r,('ENDCASE',(1,)),('END',(1,))]
    return (g.Case(1,'independent empty world', (row,)),),records

class IndependentModel(unittest.TestCase):
    def test_complete_snapshot_and_obs0_projection(self):
        rows,records=empty_world_fixture();text=''.join(p.format_record(t,v) for t,v in records)
        self.assertEqual(p.validate_output(text,rows)['Z9'],1)
        self.assertEqual(p.validate_output(''.join(p.projection(text.splitlines(keepends=True))),rows,False)['Z9'],1)
    def test_identical_corruption_is_rejected_without_comparison(self):
        rows,records=empty_world_fixture()
        for tag,index in [('CP',3),('CA',5),('GB',7),('IP',3),('EN9',6),('GE',8),('I8',5),('I9',2),('Z8',8),('Z9',16)]:
            with self.subTest(tag=tag):
                bad=[];changed=False
                for t,v in records:
                    if t==tag and not changed:v=list(v);v[index]^=1;changed=True
                    bad.append(p.format_record(t,v))
                with self.assertRaises(ValueError):p.validate_output(''.join(bad),rows)
    def test_contact_graph_sparse_pool_and_island_fixture(self):
        model,rows=contact_fixture()
        model.private(1,1,g.save(),rows,[],0)
    def test_contact_corruption_has_independent_detectors(self):
        from copy import deepcopy
        corruptions=[('CT',None),('CS',None),('CF',None),('CS',10),('CT',8),('GB',7),('IS',16),('IL',6)]
        for tag,index in corruptions:
            with self.subTest(tag=tag,index=index):
                model,rows=contact_fixture();rows=deepcopy(rows)
                if index is None:rows[tag].pop()
                else:
                    v=list(rows[tag][0]);v[index]^=1;rows[tag][0]=tuple(v)
                with self.assertRaises(ValueError):model.private(1,1,g.save(),rows,[],0)

def contact_fixture():
    from collections import defaultdict
    model=p.Model();model.worlds={0:{'live':True,'birth':1}}
    model.bodies={i:{'slot':i,'live':True,'world':0,'owner':1,'type':2} for i in range(2)}
    pool=p.Pool();pool.allocate();pool.allocate();pool.release(1);model.contact_pools={0:pool};model.owner_meta={(0,0):6}
    islands=p.Pool();islands.allocate();islands.allocate();islands.release(1);model.island_pools={0:islands}
    model.bitmeta={0:{'colors':[[1,1] for _ in range(11)],'changed':[0,16]}}
    r=defaultdict(list);prefix=(1,1,0)
    r['CP']=[(*prefix,2,1,1)];r['CF']=[(*prefix,0,1)]
    c=(1,0,2,11,0,0,1,0,p.NULL,p.NULL,1,p.NULL,p.NULL,0,p.NULL,p.NULL,5,0,6,0)
    dead=(0,p.NULL,p.NULL,p.NULL,p.NULL,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
    r['CT']=[(*prefix,0,*c),(*prefix,1,*dead)]
    m=[0]*30;m[1]=g.bits(1);m[3]=1
    sim=(0,0,1,0,1,0,0,0,0,g.bits(.6),0,0,0,0x10000,*([0]*7),*m,1)
    r['CA']=[(*prefix,d,i,int(d==1 and i==11)) for d in range(2) for i in range(12 if d else 3)]
    r['CS']=[(*prefix,1,11,0,*sim)]
    r['GB']=[(*prefix,i,1,1,1,0,0) for i in range(11)]+[(*prefix,11,0,0,0)]
    r['CB']=[(*prefix,0,0,16)]
    r['BL9']=[(*prefix,i,i,1,0,p.NULL if i==0 else 0,1 if i==0 else p.NULL,0,i) for i in range(2)]
    r['H']=[(*prefix,1,32,1,1,0,1,*([0]*93))]
    r['IP']=[(*prefix,2,1,1)];r['IF']=[(*prefix,0,1)]
    live=(1,2,0,0,0,1,2,0,0,1,p.NULL,p.NULL,0,p.NULL,0)
    deadisland=(0,p.NULL,p.NULL,p.NULL,*([0]*11))
    r['IS']=[(*prefix,0,*live),(*prefix,1,*deadisland)]
    r['IL']=[(*prefix,0,2,0,0),(*prefix,1,0,0,0),(*prefix,1,0,1,1),(*prefix,2,0,0,0)]
    return model,r

if __name__=='__main__':unittest.main()
