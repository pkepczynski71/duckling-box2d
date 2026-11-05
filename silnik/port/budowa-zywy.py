pass                                                                            
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('zywy_build11',HERE/'budowa-sen.py')
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
original_project=old.cmake_project
once=old.once

def function(text,signature):
    start=text.index(signature);opening=text.index('{',start);depth=1;end=opening+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

def cmake_project(port,source,directory,output):
    port,source,directory,output=map(Path,(port,source,directory,output))
    original_project(port,source,directory,output)
    base=(directory/'solver-base10.inc').read_text(encoding='utf-8')
    base=base.replace('PORT11','PORT12')
    base=once(base,'static FILE* output9;','static FILE* output9;\nstatic const char* physical12="INPUT_HEADER";')
    base=once(base,'    const char* code=message;','    const char* code=message;\n'
        '    if(!strcmp(message,"INPUT_ASCII")||!strcmp(message,"INPUT_CR")||!strcmp(message,"INPUT_EMPTY_LINE")||!strcmp(message,"INPUT_SPACING")||!strcmp(message,"INPUT_TAG"))code=physical12;')
    base=once(base,'static uint32_t hex_word(char** cursor)\n{',
        'static uint32_t hex_word(char** cursor)\n{\n    if(strlen(*cursor)<8)fail(rowEof11?"INPUT_EOF":"INPUT_WORDS");')
    base=once(base,'if(n>=2048)fail("INPUT_ARITY");','if(n>=2048)fail(physical12);')
    base=once(base,'    word(live[1]);\n    word(live[2]);\n    word(live[2]);\n    word(live[0]);',
        '    word(live[1]);\n    word(live[2]);\n    uint32_t actualProxies12=0;\n'
        '    for(int i=0;i<SHAPES;++i)if(shapes[i].live){b2ShapeId raw=shapes[i].raw;'
        'b2World* w=b2GetWorld(raw.world0);actualProxies12+=w->shapes.data[raw.index1-1].proxyKey!=-1;}\n'
        '    word(actualProxies12);\n    word(live[0]);')
                                                                             
    base=once(base,'    if ((added && !(density>=0))',
        '    badMassGeometry12=false;\n'
        '    if(added&&!valid_mass_geometry12(added)){badMassGeometry12=true;return false;}\n'
        '    for(int i=0;i<count;++i){\n'
        '        bool match=b2StoreShapeId(list[i])==b2StoreShapeId(changed);if(match&&remove)continue;\n'
        '        Geometry g=public_geometry(list[i]);\n'
        '        float density12=match?newDensity:b2Shape_GetDensity(list[i]);\n'
        '        if(!valid_mass_geometry12(&g)||!isfinite(density12)||density12<0){badMassGeometry12=true;return false;}\n'
        '    }\n    if ((added && !(density>=0))')
    (directory/'solver-base10.inc').write_text(base,encoding='utf-8',newline='\n')
    contact=(directory/'solver-contact9.inc').read_text(encoding='utf-8')
    contact=once(contact,'CONTACTS9=256, EVENTS9=516','CONTACTS9=512, EVENTS9=2048')
    (directory/'solver-contact9.inc').write_text(contact,encoding='utf-8',newline='\n')
    main=(directory/'sen-solver10.inc').read_text(encoding='utf-8')
    main=once(main,'value=profile11;','value=profile12;')
                                                                          
                                                                           
                                                             
    main=once(main,'if(!strcmp(tag,"TASK")&&profile11==7)return 0;',
        'if(!strcmp(tag,"TASK")&&profile12==10&&opcode9==43)return 0;')
    main=once(main,'if(!strcmp(tag,"TASK")&&profile11!=7){p=end+1;continue;}',
        'if(!strcmp(tag,"TASK")&&!(profile12==10&&opcode9==43)){p=end+1;continue;}')
    main=once(main,'if(profile11!=7&&!strcmp(tokens[0],"I9")&&(i==20||i==21))',
        'if(!(profile12==10&&opcode9==43)&&!strcmp(tokens[0],"I9")&&(i==20||i==21))')
    main=once(main,'static const int guardBounds[]={8,16,8};','static const int guardBounds[]={4,8,8};')
                                                                              
                                                                             
    step=function(main,'static int step10(')
    new_step=once(step,'if(dt!=0){','if(dt!=0&&o->code==32){')
    new_step=once(new_step,'port9Prepare(w,&x,&y,true);','port12Prepare(w,&x,&y,true);')
    main=once(main,step,new_step)
    main=once(main,'"SW11","GS11","X"','"SW11","GS11","AP12","WS12","NM12","UD12","EF12","HC12","HR12","HT12","CL12/CV12","VR12","X"')
    main=once(main,'"BF11","I8"','"BF11","NP12","I8"')
    main=once(main,'"Z11"};','"Z11","I12","IP12","Z12"};')
    main=main.replace('tokens[4096]','tokens[32768]').replace('count==4096','count==32768')
    (directory/'sen-solver10.inc').write_text(main,encoding='utf-8',newline='\n')
    driver=(port/'kontrola-sen.c').read_text(encoding='utf-8')
    driver=once(driver,'int main(int argc,char** argv)','int unused_main11(int argc,char** argv)')
    (directory/'zywy-sen11.inc').write_text(driver,encoding='utf-8',newline='\n')
    manifest=json.loads((port/'zywy-przypadki.json').read_bytes())
    limits='static const int limits10[160][4]={\n'+',\n'.join(
        '{'+','.join(map(str,(*(c['maksima'][k] for k in ('B','S','C')),c['opMax'])))+'}'
        for c in manifest['przypadki'])+'\n};\n'
    (directory/'solver-limity10.inc').write_text(limits,encoding='ascii')
                                                                          
                                                                              
    preflight=function(base,'static bool preflight(')
    preflight=once(preflight,'static bool preflight(','static bool preflight12(')
    preflight=once(preflight,'float newDensity)','float newDensity, int targetType, int targetFixed, const Geometry* replacement)')
    preflight=once(preflight,'type=b2Body_GetType(id);','type=targetType<0?b2Body_GetType(id):(b2BodyType)targetType;')
    preflight=once(preflight,'fixed=b2Body_IsFixedRotation(id);','fixed=targetFixed<0?b2Body_IsFixedRotation(id):targetFixed!=0;')
    preflight=once(preflight,'angular=b2Body_GetAngularVelocity(id);','angular=targetFixed==1?0:b2Body_GetAngularVelocity(id);')
    preflight=preflight.replace('Geometry g=public_geometry(list[i]);',
        'Geometry g=replacement&&b2StoreShapeId(list[i])==b2StoreShapeId(changed)?*replacement:public_geometry(list[i]);')
    (directory/'zywy-preflight.inc').write_text(preflight+'\n',encoding='utf-8',newline='\n')
    seed=function((port/'kontrola-solver-guard.h').read_text(encoding='utf-8'),'static void seed_guard10(')
    seed=seed.replace('seed_guard10','seed_base12').replace('guard_result10','guard_result12')
    (directory/'zywy-seed.inc').write_text(seed+'\n',encoding='utf-8',newline='\n')
    spec=importlib.util.spec_from_file_location('zywy_legacy_words',port/'przypadki-sen.py')
    legacy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=legacy;spec.loader.exec_module(legacy)
    (directory/'zywy-used.inc').write_text('static const unsigned char used_legacy12[65]={' +
        ','.join(str(legacy.USED.get(j,0)) for j in range(65))+'};\n',encoding='ascii')
    project=(directory/'CMakeLists.csv').read_text(encoding='utf-8')
    project=project.replace(str(port/'kontrola-sen.c'),str(port/'kontrola-zywy.c'))
    (directory/'CMakeLists.csv').write_text(project,encoding='utf-8',newline='\n')
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.inc')}

def build(source,directory,output):
    directory,output=map(Path,(directory,output));output.mkdir(parents=True,exist_ok=True)
    for label in ('obs0','obs1'):(output/('c12-'+label+'-bin')).unlink(missing_ok=True)
    old.cmake_project=cmake_project
    try:
        receipt=old.build(source,directory,output)
        for label in ('obs0','obs1'):
            (output/('c11-'+label+'-bin')).replace(output/('c12-'+label+'-bin'))
        receipt.update(protocol='PORT12',implemented_part='12a/12b/12c — acceptance requires native receipts',accepted_N_max=160)
        return receipt
    finally:
        path=output/'budowa-sen.json'
        if path.exists():
            data=json.loads(path.read_bytes());data['protocol']='PORT12/GUARD12/COMPONENT12'
            data['accepted_N_max']=160
            data['adapter12_sources']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
                ('budowa-zywy.py','kontrola-zywy.c','kontrola-zywy-haki.h','kontrola-zywy-guard.h')}
            (output/'budowa-zywy.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
            path.unlink()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.source,args.build,args.out)
