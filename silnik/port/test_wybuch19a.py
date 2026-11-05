pass                                                                  
                                                                                          
   
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,shutil,sys,tarfile,tempfile,unittest
from unittest import mock
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from wybuch19a import manifest,sha
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
C=load('test19_compare','porownaj-wybuch19a.py');CI=load('test19_ci','ci-wybuch19a.py')
COV=load('test19_cov','19a-coverage.py')
FROZEN=HERE/'wybuch19a-frozen'
def case_bytes(profile,cid):
 result=[];active=False
 with gzip.open(FROZEN/(profile+'-C1.out.csv.gz'),'rb') as f:
  for row in f:
   if row.startswith(b'CASE '):active=int(row.split()[1])==cid
   if active:result.append(row)
   if active and row.startswith(b'ENDCASE '):break
 if not result:raise ValueError('missing frozen case')
 return b''.join(result)+b'END 1\n'
def case_input(profile,cid):
 cases=C.operations(manifest()['literalInputs'][profile+'C']);c=next(x for x in cases if x['id']==cid)
 rows=[f'PORT19 A {profile} 1',f'C {cid} {c['count']}']
 for op in c['ops']:rows.append(f'O {op['seq']} {op['code']} {op['n']}'+''.join(f' {x:08x}' for x in op['a']))
 return '\n'.join(rows)+'\n'

class Station19(unittest.TestCase):
 def test_native_step_full_state_then_empty_world(self):
  rows=self.check(case_bytes('PUBLIC',23),'PUBLIC',23)
  self.assertIn(b'Z19 23 1 1 2 2 0 0\n',rows);self.assertIn(b'Z19 23 1 0 0 0 0 0\n',rows)
  self.assertLess(rows.index(b'Z19 23 1 1 2 2 0 0\n'),rows.index(b'Z19 23 1 0 0 0 0 0\n'))
 def test_native_step_missing_full_block_red(self):
  rows=case_bytes('PUBLIC',23).splitlines(keepends=True);start=next(i for i,r in enumerate(rows) if r.startswith(b'S19 23 1 1 '));end=rows.index(b'Z19 23 1 1 2 2 0 0\n');self.red(b''.join(rows[:start]+rows[end+1:]),'PUBLIC',23)
 def test_native_step_missing_private_sim_red(self):
  rows=case_bytes('PUBLIC',23).splitlines(keepends=True);self.red(b''.join(r for r in rows if not r.startswith(b'SM11 ')),'PUBLIC',23)
 def test_native_step_missing_empty_final_block_red(self):
  rows=case_bytes('PUBLIC',23).splitlines(keepends=True);end=rows.index(b'Z19 23 1 1 2 2 0 0\n');self.red(b''.join(rows[:end+1]+[b'ENDCASE 23\n',b'END 1\n']),'PUBLIC',23)
 def test_native_step_wrong_tick_red(self):
  self.red(case_bytes('PUBLIC',23).replace(b'S19 23 1 1 ',b'S19 23 1 0 '),'PUBLIC',23)
 @classmethod
 def setUpClass(cls):cls.good=case_bytes('DIRECT',1);cls.compound=case_bytes('DIRECT',47)
 def setUp(self):self.temp=tempfile.TemporaryDirectory(prefix='.19a-test-',dir=HERE);self.dir=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def check(self,data,profile='DIRECT',cid=1):
  path=self.dir/'candidate.out';path.write_bytes(data);return list(C.validated(path,profile,True,case_input(profile,cid)))
 def red(self,data,profile='DIRECT',cid=1):
  with self.assertRaises(ValueError):self.check(data,profile,cid)
 def replace_row(self,tag,fn):
  rows=self.good.splitlines(keepends=True);i=next(i for i,r in enumerate(rows) if r.startswith(tag+b' '));rows[i]=fn(rows[i]);return b''.join(rows)
 def test_real_C_fixture_green(self):self.assertGreater(len(self.check(self.good)),90)
 def test_changed_H8_and_negative_zero_red(self):
  changed=self.replace_row(b'S19',lambda r:r.replace(b'00000000',b'80000000',1));a=self.dir/'a';b=self.dir/'b';a.write_bytes(self.good);b.write_bytes(changed)
  with self.assertRaises(ValueError):C.compare(a,b,'DIRECT',input_text=case_input('DIRECT',1))
 def test_missing_END_red(self):self.red(self.good.rsplit(b'END 1\n',1)[0])
 def test_duplicate_END_red(self):self.red(self.good+b'END 1\n')
 def test_missing_body_red(self):self.red(b''.join(r for r in self.good.splitlines(keepends=True) if not r.startswith(b'S19 ')))
 def test_missing_BASE13_body_red(self):self.red(b''.join(r for r in self.good.splitlines(keepends=True) if not r.startswith(b'B ')))
 def test_missing_private_sim_red(self):self.red(b''.join(r for r in self.good.splitlines(keepends=True) if not r.startswith(b'SM11 ')))
 def test_missing_counter_red(self):self.red(b''.join(r for r in self.good.splitlines(keepends=True) if not r.startswith(b'I8 ')))
 def test_duplicate_body_red(self):self.red(self.replace_row(b'S19',lambda r:r+r))
 def test_duplicate_private_record_red(self):self.red(self.replace_row(b'SM11',lambda r:r+r))
 def test_wrong_order_red(self):
  rows=self.good.splitlines(keepends=True);rows[2],rows[3]=rows[3],rows[2];self.red(b''.join(rows))
 def test_wrong_arity_red(self):self.red(self.replace_row(b'S19',lambda r:b' '.join(r.rstrip().split(b' ')[:-1])+b'\n'))
 def test_wrong_H8_red(self):self.red(self.replace_row(b'S19',lambda r:r.replace(b'00000000',b'0000000Z',1)))
 def test_wrong_echo_red(self):self.red(self.good.replace(b'E19 1 1 601',b'E19 1 1 607',1))
 def test_callback_order_red(self):
  rows=self.compound.splitlines(keepends=True);ix=[i for i,r in enumerate(rows) if r.startswith(b'X19 ')];self.assertGreaterEqual(len(ix),2);rows[ix[0]],rows[ix[1]]=rows[ix[1]],rows[ix[0]];self.red(b''.join(rows),cid=47)
 def test_missing_callback_red(self):
  rows=self.compound.splitlines(keepends=True);i=next(i for i,r in enumerate(rows) if r.startswith(b'X19 '));rows.pop(i);self.red(b''.join(rows),cid=47)
 def test_C0_projection_preserves_every_old_private_row(self):
  c1=self.dir/'c1';c0=self.dir/'c0';c1.write_bytes(self.good);c0.write_bytes(b''.join(C.project(iter(self.good.splitlines(keepends=True)))))
  r=C.compare(c0,c1,'DIRECT',True,case_input('DIRECT',1));self.assertTrue(r['ok']);self.assertIn(b'SM11 ',c0.read_bytes())
 def test_old_projection_is_rejected(self):
  c1=self.dir/'c1';c0=self.dir/'c0';c1.write_bytes(self.good);c0.write_bytes(b''.join(r for r in C.project(iter(self.good.splitlines(keepends=True))) if not r.startswith(b'SM11 ')))
  with self.assertRaises(ValueError):C.compare(c0,c1,'DIRECT',True,case_input('DIRECT',1))
 def test_missing_step_red(self):
  data=case_bytes('PUBLIC',25);rows=data.splitlines(keepends=True);start=next(i for i,r in enumerate(rows) if r.startswith(b'S19 25 9 1 '));end=next(i for i in range(start,len(rows)) if rows[i].startswith(b'Z19 25 9 1 '));del rows[start:end+1];self.red(b''.join(rows),'PUBLIC',25)
 def test_step_fixture_positive(self):self.assertGreater(len(self.check(case_bytes('PUBLIC',25),'PUBLIC',25)),1000)
 def test_foreign_input_and_binary_rejected(self):
  binary=self.dir/'binary';inp=self.dir/'input';binary.write_bytes(b'fixture-ELF');inp.write_bytes(b'input-A');r=dict(binarySHA256=sha(binary),inputSHA256=sha(inp),exit=0,stderr='',failure=None)
  expected=(sha(binary),sha(inp));self.assertTrue(CI.bind(r,binary,inp,*expected));inp.write_bytes(b'input-B')
  with self.assertRaises(ValueError):CI.bind(r,binary,inp,*expected)
  inp.write_bytes(b'input-A');binary.write_bytes(b'foreign-ELF')
  with self.assertRaises(ValueError):CI.bind(r,binary,inp,*expected)
  r.update(binarySHA256=sha(binary))
  with self.assertRaises(ValueError):CI.bind(r,binary,inp,*expected)
 def test_nonzero_exit_and_stderr_not_green(self):
  b=self.dir/'bin';i=self.dir/'in';b.write_bytes(b'x');i.write_bytes(b'y');r=dict(binarySHA256=sha(b),inputSHA256=sha(i),exit=2,stderr='',failure=None)
  with self.assertRaises(ValueError):CI.bind(r,b,i,sha(b),sha(i))
  r.update(exit=0,stderr='diagnostic')
  with self.assertRaises(ValueError):CI.bind(r,b,i,sha(b),sha(i))
 def test_frozen_source_and_receipt_inventory(self):
  m=manifest();self.assertEqual([len(m[k]) for k in ('direct','public','guards','parsers')],[48,32,48,24]);r=json.loads((FROZEN/'campaign.json').read_bytes());self.assertTrue(r['reference_ready']);self.assertFalse(r['full_acceptance'])
  for name,info in r['frozen'].items():self.assertEqual(sha(FROZEN/name),info['sha256'])
  self.assertEqual(r['stages']['C18-reproduced-by-PORT19']['value']['failures'],[])
 def test_C_D_literal_words_equal(self):
  m=manifest()
  for profile in ('DIRECT','PUBLIC','GUARD'):
   c=m['literalInputs'][profile+'C'].splitlines();d=m['literalInputs'][profile+'D'].splitlines();self.assertEqual(len(c),len(d))
   for a,b in zip(c,d):
    aa,bb=a.split(),b.split();self.assertEqual(aa[:4],bb[:4])
    if aa[0] in ('O','G'):self.assertEqual([int(x,16) for x in aa[4:]],[int(x) for x in bb[4:]])
 def test_all_parser_pairs_executed(self):
  rows=json.loads((FROZEN/'parsers-C.json').read_bytes());self.assertEqual(len(rows),24);self.assertTrue(all(x['ok'] for x in rows))
 def test_frozen_replay_does_not_read_mutable_campaign(self):
  frozen=self.dir/'frozen';frozen.mkdir();shutil.copy2(FROZEN/'REFERENCE.json',frozen);shutil.copy2(FROZEN/'DIRECT-C1.out.csv.gz',frozen)
  (frozen/'campaign.json').write_text('{"stages":{}}');actual=self.dir/'actual';actual.write_bytes(gzip.decompress((frozen/'DIRECT-C1.out.csv.gz').read_bytes()))
  self.assertGreater(CI.replay_frozen(actual,'DIRECT',frozen)['comparedRows'],5000)
  actual.write_bytes(actual.read_bytes().replace(b'CASE 1 1',b'CASE 2 1',1))
  with self.assertRaises(ValueError):CI.replay_frozen(actual,'DIRECT',frozen)
 def test_gcov_does_not_overwrite_C1_with_unexecuted_C0(self):
  for folder in ('c11-obs0-bin.dir','c11-obs1-bin.dir','sen11.dir'):
   p=self.dir/'c-coverage/project/make/CMakeFiles'/folder/'same-name.gcno';p.parent.mkdir(parents=True);p.touch()
  selected=COV.selected_gcno(self.dir);self.assertEqual(len(selected),2);self.assertFalse(any('c11-obs0-bin.dir' in p.parts for p in selected))
 def test_sequential_D_tasks_share_one_time_envelope(self):
  compiler=self.dir/'duckc';compiler.write_bytes(b'compiler fixture');archive=self.dir/'toolchain.tar.gz'
  with tarfile.open(archive,'w:gz') as t:t.add(compiler,arcname='bin/duckc')
  driver=self.dir/'driver.dk';driver.write_text('fixture');calls=[]
  def execute(argv,inp,dest,seconds,rss):
   task=json.loads(Path(argv[2]).read_bytes());self.assertEqual(len(task['tasks']),1);calls.append((task['tasks'][0]['package'],seconds,rss))
   artifacts=Path(argv[4]);artifacts.mkdir(exist_ok=True);name=task['tasks'][0]['output_file'];(artifacts/name).write_bytes(b'\x7fELF' if name=='wybuch19a-bin' else b'archive')
   return dict(exit=0,failure=None,peakTreeRSS=1,seconds=0)
  with mock.patch.object(CI,'ARCHIVE',sha(archive)),mock.patch.object(CI,'run',side_effect=execute),mock.patch.object(CI.time,'monotonic',side_effect=[100,101,104,105,109,110]):binary,receipt=CI.compile_d(archive,compiler,driver,self.dir/'build')
  self.assertEqual([c[0] for c in calls],['fizyka','wybuch19a']);self.assertTrue(0<calls[1][1]<calls[0][1]<=180);self.assertEqual([c[2] for c in calls],[2*1024**3]*2);self.assertEqual(len(receipt['commands']),2)
  self.assertEqual([c[1] for c in calls],[179,175])
                                                                              
  CI.save(self.dir/'stage.json',{'value':(binary,receipt)});saved=json.loads((self.dir/'stage.json').read_bytes());self.assertIsInstance(saved['value'][0],str)
 def test_byte_equal_empty_and_single_sided_files(self):
  a=self.dir/'a';b=self.dir/'b';a.write_bytes(b'');b.write_bytes(b'');self.assertEqual(CI.byte_equal(a,b),0)
  a.write_bytes(b'row\n')
  with self.assertRaises(ValueError):CI.byte_equal(a,b)
  with self.assertRaises(ValueError):CI.byte_equal(b,a)
  b.write_bytes(a.read_bytes());self.assertEqual(CI.byte_equal(a,b),1)
 def test_gcov_relative_work_resolves_notes_before_changing_cwd(self):
  note=self.dir/'c-coverage/project/make/CMakeFiles/sen11.dir/test.gcno';note.parent.mkdir(parents=True);note.touch();relative=os.path.relpath(self.dir,Path.cwd());calls=[]
  def execute(argv,**kwargs):
   self.assertTrue(Path(argv[-1]).is_absolute());self.assertTrue(Path(kwargs['cwd']).is_absolute());self.assertEqual(Path(argv[-1]),note.resolve());calls.append(argv)
   return COV.subprocess.CompletedProcess(argv,0,'','')
  with mock.patch.object(COV.subprocess,'run',side_effect=execute):self.assertEqual(COV.collect(relative),{})
  self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main()
