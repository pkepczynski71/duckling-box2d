from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
def check(t):
 flows={n:(ROOT/'.github/workflows'/n).read_text() for n in ['port.yml','silnik.yml','port18.yml']}
 for text in flows.values():
  t.assertIn('contents: read',text)
  t.assertNotIn('secrets.',text)
  t.assertNotIn('repository:',text)
  t.assertIn('if: always()',text)
  t.assertIn('path: public-results.json',text)
  actions=re.findall(r'uses: ([^\s]+)',text)
  t.assertTrue(actions)
  t.assertTrue(all(re.fullmatch(r'actions/[A-Za-z/-]+@[0-9a-f]{40}',a) for a in actions))
 t.assertIn('tools/check.py physics',flows['port.yml'])
 t.assertIn('tools/check.py image',flows['silnik.yml'])
 native=flows['port18.yml']
 for token in ['sha256sum --check','806f8a182643c4913c86a20f525a359098dabe80380d777a37feefd288058805','oryginal.tar.gz','18a-run.py','--box2d','--archive','tools/numbers.py']:
  t.assertIn(token,native)
 code=(ROOT/'silnik/port/18a-run.py').read_text()
 for profile in ['DIRECT','PUBLIC','GUARD','parser24']:
  t.assertIn(profile,code)
 t.assertIn("self.stage(v+'-'+p",code)
 t.assertIn("self.stage(v+'-parser24'",code)
 t.assertIn('not any(s[',code)

 import importlib.util,tempfile
 from types import SimpleNamespace
 spec=importlib.util.spec_from_file_location('public_native18',ROOT/'silnik/port/18a-run.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 with tempfile.TemporaryDirectory() as folder:
  campaign=module.Campaign.__new__(module.Campaign)
  campaign.args=SimpleNamespace(c_only=False,no_inline=False,build_only=False,additional=None)
  campaign.out=Path(folder);campaign.stages=[];campaign.processes=[]
  campaign.meta={'binaries':{v:{} for v in ['c0','c1','gcov','d']},'unexecuted':[]}
  campaign.flush=lambda:None
  def stage(name,action):
   campaign.stages.append({'name':name,'code':int(name=='c1-PUBLIC')})
   return name!='c1-PUBLIC'
  campaign.stage=stage
  t.assertEqual(campaign.all(),1)
  called=[x['name'] for x in campaign.stages]
  for name in ['c1-GUARD','c1-parser24','gcov-DIRECT','d-DIRECT','d-GUARD','d-parser24']:
   t.assertIn(name,called)
