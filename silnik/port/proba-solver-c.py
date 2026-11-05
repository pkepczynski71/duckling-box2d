from norm_data import read_text as norm_text, read_bytes as norm_bytes
pass                                                         

                                                                              
                                                                           
                                                                            
   
import hashlib
import gzip
from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('solver_c_probe_inputs',HERE/'wejscia-solver-oslony.py')
inputs=importlib.util.module_from_spec(spec);spec.loader.exec_module(inputs)
f,g=inputs.f,inputs.g
COMMIT='8c661469c9507d3ad6fbd2fea3f1aa71669c2fe3'
PROFILES=('scalar-width4','SSE2-width4','AVX2-width8')


def flags(profile):
    result=['-std=c17','-O2','-DNDEBUG','-fno-fast-math','-ffp-contract=off','-D_POSIX_C_SOURCE=200809L']
    if profile==PROFILES[0]:result+=['-DBOX2D_DISABLE_SIMD']
    elif profile==PROFILES[1]:pass
    elif profile==PROFILES[2]:result+=['-DBOX2D_AVX2','-mavx2']
    else:raise ValueError('unknown C-only profile')
    return result


def definitions(argv):
    result={};undefined=set();cursor=0
    while cursor<len(argv):
        arg=argv[cursor]
        if arg in ('-D','-U'):
            cursor+=1
            if cursor>=len(argv):raise ValueError('missing preprocessor argument')
            arg=arg+argv[cursor]
        if arg.startswith('-D'):
            name,_,value=arg[2:].partition('=');result[name]=value or '1';undefined.discard(name)
        if arg.startswith('-U'):result.pop(arg[2:],None);undefined.add(arg[2:])
        cursor+=1
    return result


def validate_compile_commands(commands,profile):
    pass                                                                        
    if not commands:raise ValueError('empty compile_commands')
    original=[r['original'] for r in commands if r.get('original')]
    if len(original)!=35 or len(set(original))!=35:raise ValueError('every original C unit must occur once')
    if not any(not r.get('original') for r in commands):raise ValueError('missing driver/observer compile command')
    for row in commands:
        argv=row.get('arguments') or shlex.split(row['command'])
        if '-c' not in argv:raise ValueError('compile flags supplied only during linking')
        macros=definitions(argv)
        disabled='BOX2D_DISABLE_SIMD' in macros;avx='BOX2D_AVX2' in macros
        if (disabled,avx)!=(profile==PROFILES[0],profile==PROFILES[2]):raise ValueError('wrong defined macro profile')
        for option in ('-std=c17','-DNDEBUG','-fno-fast-math','-ffp-contract=off'):
            if option not in argv:raise ValueError('missing required compile flag '+option)
        if profile==PROFILES[2] and '-mavx2' not in argv:raise ValueError('AVX2 flag missing on a unit')
        if any(a in ('-ffast-math','-Ofast','-mfma','-fassociative-math','-ffp-contract=fast') or a.startswith('-flto') for a in argv):
            raise ValueError('forbidden floating-point/LTO flag')
        if 'B2_FORCE_OVERFLOW' in macros:raise ValueError('forced overflow does not change the source definition')
    return True


def validate_preprocess(macros,profile):
    width=8 if profile==PROFILES[2] else 4
    if int(macros.get('B2_SIMD_WIDTH','0'))!=width:raise ValueError('actual preprocessed width mismatch')
    if ('BOX2D_DISABLE_SIMD' in macros)!=(profile==PROFILES[0]):raise ValueError('actual DISABLE defined state mismatch')
    if ('BOX2D_AVX2' in macros)!=(profile==PROFILES[2]):raise ValueError('actual AVX2 defined state mismatch')
    return width


def cpu():
    text=Path('/proc/cpuinfo').read_text(encoding='ascii',errors='replace') if Path('/proc/cpuinfo').is_file() else ''
    features=set()
    for line in text.splitlines():
        if line.startswith(('flags','Features')):features.update(line.split(':',1)[-1].split())
    return {'os':platform.system(),'arch':platform.machine(),'cpu':platform.processor(),'features':sorted(features),
            'AVX2_confirmed':{'avx','avx2','xsave'}<=features,
            'required_platform':platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64')}


def scene(entry):
    scene_id=entry['scena'];steps=entry['kroki'];sub=entry['podkroki'];warm=entry['warm']
    family={1:1,2:2,3:4,4:5,5:7,6:13,7:15,8:16}[scene_id]
    rows=[]
    if scene_id in (1,2):
        rows=inputs.pair('box' if scene_id==2 else 'circle',warm,sub,velocity=(3 if scene_id==2 else 0,-1),restitution=.7)[:-4]
    elif scene_id==3:
        rows=[f.world(gravity=(0,-10)),g.body(kind=0),g.shape(geometry=g.box(h=(5,.5)))]
        for j in range(1,9):rows += [g.body(j,p=(.02*j,.99*j)),g.shape(j,parent=j,geometry=g.box())]
    elif scene_id==4:
        rows=[f.world(gravity=(0,-10)),g.body(kind=0),g.shape(geometry=g.box(h=(10,.5)))]
        for j in (1,2):rows += [g.body(j,p=(-3 if j==1 else 3,.9),v=(1,0),w=2),
                               g.shape(j,parent=j,rolling=.2*j,tangent=.5 if j==1 else -.5)]
    elif scene_id==5:
        rows=[f.world(gravity=(0,-10)),g.body(kind=1,v=(.2,0),w=.1),g.body(1,p=(0,.9)),
              g.shape(geometry=g.box(h=(4,.5))),g.shape(1,parent=1)]
    elif scene_id in (6,7):rows=inputs.packets(5 if scene_id==6 else 9,sub)[:-3]
    elif scene_id==8:rows=inputs.overflow(sub)[:-4]
                                                                          
    world=list(rows[0]);world[11]=warm;rows[0]=tuple(world)
    if scene_id in (6,7):rows[2]=g.shape(geometry=g.box(h=(3*(5 if scene_id==6 else 9)+8,.5)))
    def restore_shape(slot):
                                                                              
                                                                         
        return [g.transform(0,slot,(3*slot,.9)),g.g8.linear(slot,0,0),g.shape(slot,parent=slot,hit=1)]
    for index in range(steps):
        if scene_id==6:
            if index==1:rows += [f.op(18,0,j) for j in range(2,6)]
            if index==40:
                for j in (2,3):rows+=restore_shape(j)
            if index==80:
                for j in (4,5):rows+=restore_shape(j)
        if scene_id==7:
            if index==1:rows += [f.op(18,0,j) for j in (8,9)]
            if index==40:rows+=restore_shape(8)
            if index==80:rows+=restore_shape(9)
        rows.append(f.step(count=sub))
    ident=6*(family-1)+2*{1:0,4:1,8:2}[sub]+warm+1
    return ident,tuple(rows)


def probe_inputs():
    entries=f.MANIFEST['C_only']['przypadki']
    if len(entries)!=48 or sum(e['kroki'] for e in entries)!=8640:raise ValueError('C-only frozen scene/step budget')
    result=[]
    for entry in entries:
        ident,rows=scene(entry)
        if sum(row[0] in (31,32) for row in rows)!=entry['kroki']:raise ValueError('C-only Step count')
        if len(rows)>f.MANIFEST['przypadki'][ident-1]['opMax']:raise ValueError('C-only input operation budget')
        result.append((entry,ident,rows))
    return tuple(result)


def adapter_gaps(port):
    pass                                                                        
    path=Path(port)/'kontrola-solver-contact.c'
    if not path.is_file():return ['Original-function C observer is missing']
    text=path.read_text(encoding='utf-8');errors=[]
    if '_Static_assert(B2_SIMD_WIDTH==4,' in text:
        errors.append(f'{path.name}: explicit width4 static assertion rejects AVX2 width8')
    if 'contactSims.count+3)/4' in text:
        errors.append(f'{path.name}: COMPONENT task ranges support four lanes; width8 requires a C adapter')
    if 'memcpy(&a,words,16)' in text:
        line=text[:text.index('memcpy(&a,words,16)')].count('\n')+1
        errors.append(f'{path.name}:{line}: helper initializes only four lanes; AVX lane4..7 must repeat the four explicit inputs')
        errors.append(f'{path.name}:{line}: SIMD Blend needs a native logical mask; raw finite FLOATW mask words are not an intrinsic comparison mask')
    return errors


def audit(context):
    pass                                                                        
    info=cpu();compiler=shutil.which('cc');errors=[]
    if not info['required_platform']:errors.append('required Linux x86_64 is unavailable')
    if not compiler:errors.append('existing C compiler unavailable; no installation/download')
    gaps=adapter_gaps(context.PORT);errors+=gaps
    entries=probe_inputs()
    return {'contract':'KONTRAKT-10.md:10.2','box2d_commit':COMMIT,'CPU_OS':info,'compiler_path':compiler,
            'profiles':{p:{'flags':flags(p),'expected_width':8 if p==PROFILES[2] else 4,
                           'executed':False,'steps_required':8640} for p in PROFILES},
            'scenes':48,'steps_per_build':sum(e['kroki'] for e,ident,rows in entries),
            'max_steps_three_builds':25920,'limit_per_build':1<<30,
            'source63_before_after':'NOT_EXECUTED','helpers':'NOT_EXECUTED','errors':errors,
            'status':'UNMEASURED' if errors else 'READY_FOR_BUILD_NOT_EXECUTED','code':1}


def load(name,filename,port=HERE):
    spec=importlib.util.spec_from_file_location(name,Path(port)/filename)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


def helper_values(records,width,kind):
    pass                                                                       
    values={};seen=set()
    for tag,v in records:
        if tag!='FH10':continue
        case,helper,operation,lane,word=v
        if v[:4] in seen:raise ValueError('duplicate original-function helper lane')
        seen.add(v[:4])
        if lane>=width:raise ValueError('helper lane outside actual preprocessed width')
        if kind==0 and operation in (10,11,12):word=int(bool(word&0x7fffffff))
        key=(case,helper,operation,lane%4)
        if key in values and values[key]!=word:raise ValueError('AVX repeated helper lane differs from its explicit lane0..3')
        values[key]=word
    expected=({(1,0,op,lane) for op in range(14) for lane in range(4)}|{(1,0,14,0)}) if kind==0 else {
        (1,0,op,lane) for op in range(4) for lane in range(4)}
    if set(values)!=expected:raise ValueError('incomplete original-function helper output')
                                                                             
    if width==8:
        groups={(v[0],v[1],v[2]):set() for t,v in records if t=='FH10' and not(kind==0 and v[2]==14)}
        for t,v in records:
            if t=='FH10' and (v[0],v[1],v[2]) in groups:groups[v[:3]].add(v[3])
        if any(lanes!=set(range(8)) for lanes in groups.values()):raise ValueError('AVX helper did not observe all eight actual lanes')
    return values


def c_projection(records):
    removed=set('X P T F U H Y DN RT JW I8 RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 TASK I9 W10 CX10 SB10 PK10 SC10 BV10 I10'.split())
    return [(t,v) for t,v in records if t not in removed]


def contact_origins(records):
    pass                                                                       
    worlds={(v[0],v[1],v[3:6]):v[2] for t,v in records if t=='W'}
    shapes={}
    for tag,v in records:
        if tag=='S':
            owner=worlds.get((v[0],v[1],v[15:18]))
            if owner is not None:shapes[v[0],v[1],owner,v[3]]=v[3:6]
    result={}
    for tag,v in records:
        if tag!='CT':continue
        a=shapes.get((*v[:3],v[9]+1));b=shapes.get((*v[:3],v[10]+1))
        key=v[:4]
        origin=(v[3],v[4],(a,b)) if a is not None and b is not None else None
        result[key]=None if key in result else origin
    return result


def physical_values(records,rows_by_case,native,*,colors=None,origins=None):
    pass                                                                       

                                                                             
                                                           
       
    m=native.m
    public=c_projection(records)
    encoded=''.join(m.format_record(t,v) for t,v in public).encode('ascii')
    native.public_records(encoded,rows_by_case,private=False)
    step_keys={(case,seq) for case,ops in rows_by_case for seq,op in enumerate(ops,1) if op[0] in (31,32)}
    if any(v[3]!=0 for tag,v in public if tag=='R' and v[:2] in step_keys):raise ValueError('C-only Step refused; no executed-step proof')
    contacts=contact_origins(records) if origins is not None else {}
    values={};ordinal=defaultdict(int)
    for tag,v in public:
        if len(v)<2 or v[:2] not in step_keys:continue
        key=(v[0],v[1],tag,ordinal[v[:2],tag]);ordinal[v[:2],tag]+=1
        values[key]=v[2:]
    for tag,v in records:
        if tag!='SC10' or v[:2] not in step_keys:continue
        payload=v[8:];mask=payload[0]|payload[1]<<32;cid=payload[2]
        m.finite_words(tag,v[:8],payload)
        wanted=(1<<30)-1 if v[5]==11 and payload[5]==1 else (1<<41)-1
        if mask!=wanted:raise ValueError('C-only exact defined constraint mask')
        if cid==0xffffffff:
            if payload[3:6]!=(0xffffffff,0xffffffff,0):raise ValueError('C-only empty lane contains a body or point')
            continue
        key=(v[0],v[1],'constraint',v[2],v[3],v[4],cid)
        if key in values:raise ValueError('duplicate contactId at one substep/phase')
        values[key]=tuple((j,payload[j+2]) for j in range(41) if mask>>j&1)
        if colors is not None:colors[key]=v[5]
        if origins is not None:origins[key]=contacts.get((v[0],v[1],v[2],cid))
    return values


def first_difference(before,after):
    def hexadecimal(value):
        if isinstance(value,int):return f'{value:08x}'
        if isinstance(value,(tuple,list)):return [hexadecimal(v) for v in value]
        return value
    def field(a,b,path=()):
        if isinstance(a,(tuple,list)) and isinstance(b,(tuple,list)):
            for j in range(max(len(a),len(b))):
                x=a[j] if j<len(a) else None;y=b[j] if j<len(b) else None
                if x!=y:return field(x,y,(*path,j))
        return path
    for key in sorted(set(before)|set(after),key=repr):
        a,b=before.get(key),after.get(key)
        if a!=b:return {'build_case_step_field':key,'first_field':field(a,b),'scalar_H':hexadecimal(a),'candidate_H':hexadecimal(b)}
    return None


def word_differences(before,after):
    pass                                                                    
    def walk(a,b,path):
        if a==b:return
        if isinstance(a,(tuple,list)) or isinstance(b,(tuple,list)):
            aa=a if isinstance(a,(tuple,list)) else ()
            bb=b if isinstance(b,(tuple,list)) else ()
            for j in range(max(len(aa),len(bb))):
                yield from walk(aa[j] if j<len(aa) else None,bb[j] if j<len(bb) else None,(*path,j))
        else:yield path,a,b
    for key in sorted(set(before)|set(after),key=repr):
        for path,a,b in walk(before.get(key),after.get(key),()):yield key,path,a,b


def difference_source(kind,key,path,reference,colors=None,candidate_colors=None):
    pass                                                            

                                                                         
       
    base='src/contact_solver.c:'
    if kind==0 and len(key)==4 and not path:
        op=key[2]
        sites={7:('b2MinW','935-942','822-825','594-597'),
               8:('b2MaxW','945-952','827-830','599-602'),
               9:('b2SymClampW','956-964','833-842','605-608')}
        if op in sites:
            name,scalar,sse,avx=sites[op]
            source={'operation':name,'scalar':base+scalar,'SSE2':base+sse,'AVX2':base+avx}
            if op==9:source['scalar_clamp']='include/box2d/math_functions.h:144-147'
            return source
    if kind=='physical' and len(key)==7 and key[2]=='constraint' and len(path)==2 and path[1]==1:
                                                                        
                                                                         
        if colors is None or candidate_colors is None:return None
        if not (0<=colors.get(key,11)<11 and 0<=candidate_colors.get(key,11)<11):return None
        values=reference.get(key,())
        field=values[path[0]][0] if path[0]<len(values) else None
        sites={15:'1955',25:'1801,2016',36:'1853,2054',26:'1896',37:'1933'}
        if field in sites:
            source={'operation':'constraint Min/Max/clamp field '+str(field),'assignment':base+sites[field],
                    'scalar':base+'935-964','SSE2':base+'822-842','AVX2':base+'594-608'}
            if field==15:source['scalar_clamp']='include/box2d/math_functions.h:144-147'
            return source
    return None


def accepted_zero_difference(a,b,source):
                                                                             
    return source is not None and {a,b}=={0,0x80000000}


def observe_differences(table,seen,label,profile,before,after,kind,*,colors=None,candidate_colors=None,
                        origins=None,candidate_origins=None):
    seen.add((label,profile))
    changes=list(word_differences(before,after));wide_rolling=defaultdict(list);copies=defaultdict(int)
    def copy_key(key,path,a,b):
        value=before.get(key,())
        if kind=='physical' and len(key)==4 and key[2]=='CD' and path==(12,) and len(value)>12 and value[2]==1 and {a,b}=={0,0x80000000}:
            candidate=after.get(key,())
            pair=(value[4:7],value[7:10])
            if (len(candidate)>12 and candidate[0]==value[0] and candidate[2]==1
                    and (candidate[4:7],candidate[7:10])==pair
                    and all(len(s)==3 and s[0]>0 for s in pair)):
                return (key[0],key[1],value[0],pair,a,b)
    for key,path,a,b in changes:
        source=difference_source(kind,key,path,before,colors,candidate_colors)
        if (source and len(key)==7 and key[5]==7 and path==(15,1)
                and accepted_zero_difference(a,b,source) and origins is not None and candidate_origins is not None):
            origin=origins.get(key)
            if origin is not None and origin==candidate_origins.get(key) and origin[0]==key[6]:
                wide_rolling[key[0],key[1],key[3],origin[2],a,b].append((key,origin))
        context=copy_key(key,path,a,b)
        if context:copies[context]+=1
    for key,path,a,b in changes:
        ident=(label,key,path);source=difference_source(kind,key,path,before,colors,candidate_colors)
        context=copy_key(key,path,a,b)
        matches=wide_rolling.get(context,()) if context else ()
        if context and copies[context]==2 and len(matches)==1:
                                                                           
                                                                           
                                                                              
            source={'operation':'bit copy of proven wide rolling clamp',
                    'clamp':'src/contact_solver.c:1955','store':'src/contact_solver.c:2090,2105',
                    'getter':'src/body.c:474-489','transport':'kontrola-kontakty9.h:48,176-178',
                    'scalar':'src/contact_solver.c:956-964','SSE2':'src/contact_solver.c:833-842',
                    'AVX2':'src/contact_solver.c:605-608','scalar_clamp':'include/box2d/math_functions.h:144-147',
                    'constraint_key':list(matches[0][0]),'contact_origin':matches[0][1]}
        row=table.setdefault(ident,{'case':label,'key':list(key),'field_path':list(path),
            'scalar':a,'candidates':{},'source_C':source,'classifications':{}})
        row['candidates'][profile]=b
        row['classifications'][profile]='KNOWN_ZERO_MINMAX' if accepted_zero_difference(a,b,source) else 'UNEXPECTED'
        if kind=='physical' and len(key)==7 and key[2]=='constraint':
            origin=row.setdefault('origin_colors',{})
            origin[PROFILES[0]]=colors.get(key) if colors is not None else None
            origin[profile]=candidate_colors.get(key) if candidate_colors is not None else None


def difference_table(table,seen):
    result=[]
    def h(v):return None if v is None else f'{v:08x}'
    for row in table.values():
        words={PROFILES[0]:h(row['scalar'])}
        for profile in PROFILES[1:]:
            words[profile]=h(row['candidates'].get(profile,row['scalar'])) if (row['case'],profile) in seen else 'NOT_MEASURED'
        result.append({k:v for k,v in row.items() if k not in ('scalar','candidates')}|
            {'words':words,'classification':'KNOWN_ZERO_MINMAX' if all(v=='KNOWN_ZERO_MINMAX' for v in row['classifications'].values()) else 'UNEXPECTED'})
    return result


def filter_stream():
    pass                                                                        
    native=load('solver_c_filter_native','mutacje-solver.py');m=native.m
    for line in sys.stdin.buffer:
        tag,value=m.parse(line.decode('ascii'))
        if tag=='CP' and value[-1]>33:raise ValueError('C-only actual live contacts exceed33')
        if tag=='Z8' and (value[6]>18 or value[7]>34):raise ValueError('C-only actual live bodies/shapes exceed18/34')
        if c_projection([(tag,value)]) or tag=='CT' or (tag=='SC10' and value[4]==7):sys.stdout.buffer.write(line)



def build_profile(C, profile_index, profile, work, detail):
    out=Path(C.OUT);port=Path(C.PORT);source=Path(C.base.TEMP)/'box2d'
    build=load('solver_c_profile_builder','budowa-solver.py',port)
    def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def execute(name,argv,seconds=60):
        C.base.need(name,argv,seconds=seconds)
        return (out/(name+'.csv')).read_bytes()
    label='c-only-'+str(profile_index);directory=work/label;directory.mkdir(parents=True)
                                                                     
                                                                        
    population_limits=tuple(max(e[k] for e in f.MANIFEST['C_only']['przypadki']) for k in ('maxB','maxS','maxC'))
    detail['population_limits']=population_limits
    detail['adapter_sha256']=build.adapter(port,directory,population_limits=population_limits)
    commands=build.commands(port,source,directory)
    for row in commands:
        argv=row['arguments'];argv=[a for a in argv if a not in build.FLAGS]
        row['arguments']=[argv[0],*flags(profile),*argv[1:]]
    includes=['-I'+str(directory),'-I'+str(port),'-I'+str(source/'include'),'-I'+str(source/'src')]
    drivers=[]
    for mode,defines in (('public',()),('helper',('-DCOMPONENT10_MAIN',))):
        obj=directory/(mode+'.o');drivers.append(obj)
        commands.append({'file':str(port/'kontrola-solver.c'),'original':None,'output':str(obj),
            'arguments':['cc',*flags(profile),'-DOBS=1',*defines,*includes,'-c',str(port/'kontrola-solver.c'),'-o',str(obj)]})
    validate_compile_commands(commands,profile);save(label+'-compile_commands.json',commands)
    macros={}
    for line in execute(label+'-preprocess',['cc',*flags(profile),*includes,'-dM','-E',port/'kontrola-solver-contact.c'],30).decode('ascii').splitlines():
        words=line.split(maxsplit=2)
        if len(words)>=2 and words[0]=='#define':macros[words[1]]=words[2] if len(words)>2 else ''
    width=validate_preprocess(macros,profile);detail['actual_macros']=macros
    simd_macro=('B2_SIMD_NONE','B2_SIMD_SSE2','B2_SIMD_AVX2')[profile_index]
    if simd_macro not in macros or macros.get('B2_VALIDATE')!='0':raise ValueError('actual SIMD/Release preprocessing differs from frozen profile')
    failures=[]
    for j,row in enumerate(commands):
        try:execute(label+'-unit'+str(j),row['arguments'])
        except Exception as exc:failures.append(str(exc))
    if failures:raise ValueError('; '.join(failures))
    archive=directory/'libprobe.a'
    execute(label+'-archive',['ar','rcs',archive,*[r['output'] for r in commands if r.get('original')]],180)
    symbols=execute(label+'-symbols',['nm','--defined-only',archive],180).decode('ascii').splitlines()
    for symbol in ('b2World_Step','b2UpdateBroadPhasePairs','b2Solve','b2PrepareContactsTask','port10OriginalCreateContact'):
        if sum(line.split()[-1:]==[symbol] for line in symbols)!=1:raise ValueError('not exactly one linked original symbol: '+symbol)
    detail['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();detail['units']=commands;detail['symbols']=symbols
    programs=[]
    for j,obj in enumerate(drivers):
        binary=directory/('probe'+str(j));programs.append(binary)
        execute(label+'-link'+str(j),['cc',*flags(profile),obj,archive,'-lm','-o',binary])
    detail['driver_sha256']={str(j):hashlib.sha256(p.read_bytes()).hexdigest() for j,p in enumerate(programs)}
    binaries=[]
    for j,binary in enumerate(programs):
        target=out/('c-only-'+str(profile_index)+'-probe'+str(j)+'-bin')
        shutil.copy2(binary,target);binaries.append(target)
    detail['built']=True
    return binaries,width


def build_only(context):
    result=audit(context);out=Path(context.OUT)
    work=Path(context.base.TEMP)/'c-only-build'
    if work.exists():raise ValueError('C-only build workspace already exists')
    work.mkdir(parents=True)
    try:
        if result['errors']:return result
        for index,profile in enumerate(PROFILES):
            try:build_profile(context,index,profile,work,result['profiles'][profile])
            except Exception as exc:result['errors'].append(profile+': '+type(exc).__name__+': '+str(exc))
        result['code']=int(bool(result['errors']))
        (out/'c-only-build.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        return result
    finally:
        if work.resolve().is_relative_to(Path(context.base.TEMP).resolve()):shutil.rmtree(work)

def run(context):
    pass                                                                       

                                                                        
                                                                            
       
    result=audit(context)
    if result['errors']:return result
    C=context;out=Path(C.OUT);port=Path(C.PORT);work=Path(C.ROOT)/'.solver-c-probe-work'
    native=load('solver_c_probe_native','mutacje-solver.py',port)
    build=load('solver_c_probe_builder','budowa-solver.py',port)
    source=Path(C.base.TEMP)/'box2d';before=build.source_sums(source)
    contract=norm_text(port/'fixtures/norms/KONTRAKT-7.json')
    if any(f'{digest}  {name}' not in contract for name,digest in before.items()):
        result['errors'].append('original63 source hashes differ from accepted7');return result
    if work.exists():raise ValueError('C-only owned workspace already exists')
    work.mkdir();reference={};reference_size=0;helper_reference={};raw=[];differences={};seen=set()
    def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def execute(name,argv,seconds=60):
        C.base.need(name,argv,seconds=seconds)
        return (out/(name+'.csv')).read_bytes()
    def probe(name,binary,data,remaining,filtered=False):
        input_=work/(name+'.csv');input_.write_bytes(data);output=out/(name+'.raw.csv');raw.append(output)
                                                                        
                                                                            
        units=remaining//1024
        if units<=0:raise ValueError('C-only1GiB/build budget exhausted')
        script='ulimit -f "$1" || exit 125; exec "$2" "$3"'
        if filtered:script='set -o pipefail; ulimit -f "$1" || exit 125; "$2" "$3" | "$4" "$5" --filter'
        argv=['bash','-c',script,'c-only-limit',str(units),binary,input_,sys.executable,Path(__file__).resolve()]
        code=C.base.run(name,argv,stdout=output,seconds=180)
        stderr=(out/(name+'-stderr.csv')).read_bytes()
        if code or stderr:raise ValueError(f'{name}: process failed code={code}; no physical comparison')
        data=output.read_bytes()
        if len(data)>remaining:raise ValueError('C-only actual stream exceeds remaining build budget')
        return data,output
    try:
        result['compiler_version']=execute('c-only-compiler-version',['cc','--version'],15).decode('utf-8')
        import re
        if not re.search(r'^#define\s+B2_FORCE_OVERFLOW\s+0\s*$',(source/'src/constraint_graph.c').read_text(),re.M):
            raise ValueError('natural overflow definition changed')
        result['source63_before']=before
        archive=Path(C.base.TEMP)/('box2d-'+COMMIT+'.tar.gz')
        result['sourcearchiveSHA']=hashlib.sha256(archive.read_bytes()).hexdigest() if archive.is_file() else None
        for profile_index,profile in enumerate(PROFILES):
            detail=result['profiles'][profile]
            if profile_index==2 and not result['CPU_OS']['AVX2_confirmed']:
                result['errors'].append('AVX2 CPU support not confirmed; AVX binary not executed');continue
            try:
                label='c-only-'+str(profile_index)
                if getattr(C,'petla_prebuilt',False):
                    built=json.loads((out/'c-only-build.json').read_bytes())
                    detail.update(built['profiles'][profile])
                    if not detail.get('built'):raise ValueError('missing verified C-only profile: '+profile)
                    programs=[out/('c-only-'+str(profile_index)+'-probe'+str(j)+'-bin') for j in (0,1)]
                    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=detail['driver_sha256'][str(j)] for j,p in enumerate(programs)):
                        raise ValueError('C-only binary changed after build')
                    width=validate_preprocess(detail['actual_macros'],profile)
                else:
                    programs,width=build_profile(C,profile_index,profile,work,detail)
                used=0;steps=0;receipts=[]
                for kind in (0,1):
                    data,path=probe(label+'-helper'+str(kind),programs[1],inputs.component_helper(kind=kind),detail.get('limit',1<<30)-used)
                    used+=len(data);records=native.component_records(data);actual=helper_values(records,width,kind)
                    if profile_index==0:helper_reference[kind]=actual
                    else:
                        observe_differences(differences,seen,'helper'+str(kind),profile,helper_reference[kind],actual,kind)
                    receipts.append({'helper':kind,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'validated':True});path.unlink();raw.remove(path)
                detail['helpers_executed']=True
                for entry,ident,operations in probe_inputs():
                    name=label+'-'+entry['id'];rows=[(j,operations if j==ident else (f.world(),)) for j in range(1,ident+1)]
                    data,path=probe(name,programs[0],inputs.encode(ident,operations),((1<<30)-used),filtered=True);used+=len(data)
                    records=native.public_records(data,rows,properties=False);actual_colors={};actual_origins={}
                    actual=physical_values(records,rows,native,colors=actual_colors,origins=actual_origins)
                    contact_sets=defaultdict(set);overflow_observed=False
                    for tag,v in records:
                        if tag=='SC10' and v[0]==ident and v[10]!=0xffffffff:
                            contact_sets[v[1]].add(v[10]);overflow_observed|=v[5]==11
                    observed_counts={len(ids) for ids in contact_sets.values()}
                    required_counts={1,3,5} if entry['scena']==6 else {7,8,9} if entry['scena']==7 else set()
                    if not required_counts<=observed_counts:raise ValueError('C-only actual contact counts do not witness '+str(sorted(required_counts)))
                    if entry['scena']==8 and not overflow_observed:raise ValueError('C-only natural overflow was not observed')
                    if profile_index==0:
                        reference[entry['id']]=work/(entry['id']+'.gz')
                        reference[entry['id']].write_bytes(gzip.compress(data,mtime=0));reference_size+=reference[entry['id']].stat().st_size
                        if reference_size>1<<30:raise ValueError('scalar reference exceeds1GiB working allocation')
                    else:
                        original=gzip.decompress(reference[entry['id']].read_bytes())
                        expected_colors={};expected_origins={}
                        expected=physical_values(native.public_records(original,rows,properties=False),rows,native,colors=expected_colors,origins=expected_origins)
                        observe_differences(differences,seen,entry['id'],profile,expected,actual,'physical',colors=expected_colors,candidate_colors=actual_colors,
                                            origins=expected_origins,candidate_origins=actual_origins)
                    steps+=entry['kroki'];receipts.append({'case':entry['id'],'steps':entry['kroki'],'bytes':len(data),
                        'sha256':hashlib.sha256(data).hexdigest(),'validated_before_compaction':True,
                        'actual_contact_counts':sorted(observed_counts),'natural_overflow_observed':overflow_observed})
                    save(label+'-streams.json',receipts);path.unlink();raw.remove(path)
                detail.update(executed=True,actual_steps=steps,actual_bytes=used,expected_width=width)
                if steps!=8640:raise ValueError('C-only actual Step count differs from8640')
            except Exception as exc:
                result['errors'].append(profile+': '+type(exc).__name__+': '+str(exc))
        result['helpers']='EXECUTED' if all(v.get('helpers_executed') for v in result['profiles'].values()) else 'INCOMPLETE'
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        after=build.source_sums(source);result['source63_after']=after
        result['source63_before_after']='UNCHANGED' if before==after else 'CHANGED'
        if before!=after:result['errors'].append('protected original C/H source changed')
                                                                           
                                                         
        for path in raw:
            if path.is_file():save(path.stem+'-failure-stream.json',{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'validated':False});path.unlink()
        if work.resolve().is_relative_to(Path(C.ROOT).resolve()):shutil.rmtree(work)
    result['differences']=difference_table(differences,seen)
    result['difference_count']=len(result['differences'])
    unexpected=[r for r in result['differences'] if r['classification']=='UNEXPECTED']
    result['unexpected_differences']=len(unexpected)
    if unexpected:result['errors'].append('D3: '+str(len(unexpected))+' unexpected difference keys; all measured differences retained')
    result['code']=int(bool(result['errors']) or not all(p.get('executed') for p in result['profiles'].values()))
    result['status']=('ZNANA ROZNICA ORYGINALU -0/+0' if result['differences'] else 'OK') if result['code']==0 else 'FAIL / UNMEASURED'
    save('D3-roznice.json',result['differences'])
    lines=['# D3: wszystkie roznice trzech oryginalnych C','',
           '| Scena / klucz / field | scalar | SSE2 | AVX2 | Zrodlo C | Klasyfikacja |',
           '|---|---|---|---|---|---|']
    for row in result['differences']:
        key=str((row['case'],row['key'],row['field_path']))
        lines.append('| '+' | '.join([key,*[str(row['words'][p]) for p in PROFILES],
            json.dumps(row['source_C'],ensure_ascii=False),row['classification']])+' |')
    (out/'D3-ROZNICE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    if sys.argv[1:]!=['--filter']:raise SystemExit('Use ci-solver-oslony.stage(); --filter is its bounded stream projection.')
    filter_stream()
