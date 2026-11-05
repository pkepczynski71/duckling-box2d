import json,sys,re
from pathlib import Path
def numbers(x):
 if isinstance(x,bool):return int(x)
 if isinstance(x,(int,float)):return x
 if isinstance(x,str) and re.fullmatch('[0-9a-f]{8}',x):return int(x,16)
 if isinstance(x,list):return [y for v in x if (y:=numbers(v)) is not None]
 if isinstance(x,dict):return {k:y for k,v in x.items() if (y:=numbers(v)) is not None}
root=Path(sys.argv[1]);data={str(i):numbers(json.loads(p.read_text())) for i,p in enumerate(sorted(root.glob('*.json')),1)}
Path(sys.argv[2]).write_text(json.dumps(data)+'\n')
