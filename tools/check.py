import argparse,json,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('suite',choices=['physics','image']);p.add_argument('--out',type=Path,default=Path('public-results.json'));a=p.parse_args()
 paths=sorted((ROOT/'silnik/port').glob('test*.py'))+[ROOT/'silnik/port/18a-test-tools.py'] if a.suite=='physics' else [ROOT/'silnik/sprawdz/test_sprawdz.py']
 results=[]
 for i,path in enumerate(paths,1):
  start=time.monotonic()
  try:
   r=subprocess.run([sys.executable,'-B',str(path)],cwd=ROOT,capture_output=True,timeout=180);code=r.returncode;log=(r.stdout+r.stderr).decode('utf8',errors='replace');n=re.search(r'Ran ([0-9]+) tests?',log);count=int(n[1]) if n else 0
  except subprocess.TimeoutExpired:code=124;count=0
  results.append([i,code,count,round(time.monotonic()-start,3)]);print(json.dumps(results[-1]),flush=True)
 a.out.write_text(json.dumps(results)+'\n',encoding='utf8');return int(any(x[1] for x in results))
if __name__=='__main__':raise SystemExit(main())
