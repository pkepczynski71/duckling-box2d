pass                                                                               

                                                                              
                                                                              
                                                                  
   
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

SCOPE = {
 'src/joint.h':[(19,90),(247,278)],
 'src/joint.c':[(24,30),(101,404),(702,885),(887,977),(979,1521)],
 'src/distance_joint.c':[(20,198),(215,489)],
 'src/constraint_graph.c':[(214,322)],
 'src/island.c':[(264,425),(454,460),(503,527),(656,663),(776,832)],
 'src/solver_set.c':[(120,131),(191,191),(350,396),(427,613)],
 'src/body.c':[(356,368),(1064,1088),(1106,1139),(1170,1217),(1248,1276),(1595,1622),(1666,1715),(1830,1897)],
 'src/world.c':[(168,169),(321,321),(344,344),(1678,1708)],
 'src/solver.c':[(131,180),(761,807),(967,1093),(1237,1246),(1331,1348),(1361,1363),(1410,1415),(1432,1440),(1498,1511),(1537,1569),(1578,1675)],
}


def original_name(path):
    path = path.replace('\\','/')
    if '/box2d-' not in path:
        return None
    if '/include/box2d/' in path:
        return 'include/box2d/' + path.split('/include/box2d/',1)[1]
    if '/src/' in path:
        return 'src/' + path.split('/src/',1)[1]
    return None


def in_scope(name, line):
    if name in SCOPE:
        return any(lo <= line <= hi for lo,hi in SCOPE[name])
                                                                              
    return name.endswith('.h')


def default_class(row):
    return None if sum(row['hits'].values()) > 0 else 'U'


def add_file(rows, data, profile, name):
    for line in data['lines']:
        function = line.get('function_name','<unknown>')
        pairs = [('line',line['count'])]
        pairs += [('edge'+str(i),edge['count']) for i,edge in enumerate(line.get('branches',[]))]
        for kind,count in pairs:
            key = name,function,line['line_number'],kind
            row = rows.setdefault(key, {'file':name,'function':function,'line':line['line_number'],
                                        'kind':kind,'hits':{}})
            row['hits'][profile] = row['hits'].get(profile,0) + count


def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    return {'files':len(files),'directories':sum(p.is_dir() for p in root.rglob('*')),
            'extensions':dict(Counter(p.suffix for p in files)),
            'paths':{p.relative_to(root).as_posix():{'bytes':p.stat().st_size,
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}


def collect(root, required_profiles=None):
    root=Path(root)
    required_profiles=set(required_profiles or ('PUBLIC','DIRECT','GUARD'))
    inv=inventory(root)                                                    
    index=json.loads((root/'index.json').read_text(encoding='utf-8'))
    rows={}; functions={}; files_seen=set(); receipts=[]
    for entry in index['entries']:
                                                                                    
        relative=entry['raw'].split(root.name+'/',1)[1]
        path=root/relative
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('gcov SHA mismatch: '+relative)
        profile=entry.get('profile',Path(relative).parts[0])
        if profile not in required_profiles|{'no-data'}:
            raise ValueError('unknown profile '+profile)
        data=json.loads(gzip.decompress(path.read_bytes()))
        receipts.append({'path':relative,'sha256':entry['sha256'],'gcc_version':data['gcc_version']})
        for f in data['files']:
            name=original_name(f['file'])
            if name is None:continue
            files_seen.add(name)
            add_file(rows,f,profile,name)
            for fun in f['functions']:
                key=(name,fun['name'],fun['start_line'],fun['end_line'])
                row=functions.setdefault(key,{'file':name,'function':fun['name'],
                    'start':fun['start_line'],'end':fun['end_line'],'hits':{}})
                row['hits'][profile]=row['hits'].get(profile,0)+fun['execution_count']
    profiles={p for row in rows.values() for p in row['hits'] if p!='no-data'}
    if profiles != required_profiles:
        raise ValueError('missing full profile: '+str(profiles))
    for row in rows.values():
        row['in_scope']=in_scope(row['file'],row['line'])
        row['class']=default_class(row)
        row['evidence']=[]
        row['case_attribution']='profile-union; exact case not yet measured'
    return {'inventory':inv,'receipts':receipts,'files':sorted(files_seen),
            'rows':sorted(rows.values(),key=lambda x:(x['file'],x['function'],x['line'],x['kind'])),
            'functions':sorted(functions.values(),key=lambda x:(x['file'],x['start'],x['function']))}


def summarize(data):
    result={}
    for label,subset in [('scope',[r for r in data['rows'] if r['in_scope']]),('all_original',data['rows'])]:
        result[label]={}
        for kind in ('line','edge'):
            rows=[r for r in subset if r['kind'].startswith(kind)]
            result[label][kind]={'denominator':len(rows),'hit':sum(sum(r['hits'].values())>0 for r in rows),
                                'unhit':sum(sum(r['hits'].values())==0 for r in rows)}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--gcov',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();data=collect(a.gcov);data['summary']=summarize(data)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'coverage.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data['summary']))


if __name__=='__main__':main()
