pass                                                                           

                                                                        
                                                                           
                                                                      
   
import hashlib
import json
from pathlib import Path
import shutil
import sys
from importlib.util import spec_from_file_location,module_from_spec
HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=spec_from_file_location(name,HERE/file);m=module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=load('contact_fixture_inputs','przypadki-kontakty.py');mutator=load('contact_fixture_mutator','mutacje-ruch-swiata.py')
MATERIAL_ROUTE_ANCHOR='    return op;\n}'

def one(rows,name):return (g.Case(1,name,tuple(rows)),)
def definitions():
    items=[];geometries=(g.circle(),g.capsule(),g.segment(),g.box(r=.125))
    for a in range(4):
        for b in range(4):
            rows=[g.world(gravity=(0,0)),g.body(),g.body(1,p=(0,.2)),g.shape(geometry=geometries[a],rolling=.3,tangent=-.2),g.shape(1,parent=1,geometry=geometries[b],rolling=.7,tangent=.5),*g.cycle(),g.save(),g.get()]
            items.append({'name':f'registry-{a}-{b}','kind':'registry','types':[a,b],'rows':one(rows,f'registry {a},{b}')})
    for y in (.006,.009,.019):
        items.append({'name':'speculative-false-'+str(g.bits(y)),'kind':'speculative','rows':one(g.pair_scene(g.box(),g.box(),distance=1+y)+g.cycle()+[g.save(),g.get()],'speculative false')})
    setup=g.pair_scene(distance=.9)
    hit_rows=[g.world(gravity=(0,0)),g.body(),g.body(1,p=(0,.9)),
              g.shape(game=0,hit=1),g.shape(1,parent=1,game=0,hit=1),
              *g.cycle(),g.transform(0,1,(0,1.04)),*g.cycle()]
    items.append({'name':'raw-hit-cycle','kind':'raw-hit','rows':one(hit_rows,'raw hit set and clear; no solver hit events')})
    for name,last in (('carry-low',0xffffffff),('above-sign',0x80000000ffffffff),('near-max',g.U64-1)):
        items.append({'name':name,'kind':'ticket','seed_seq':7,'seed_last':last,'rows':one(setup+g.cycle()+[g.save(),g.get()],'ticket '+name)})
    batch=[g.world(gravity=(0,0)),g.body(),g.body(1,p=(0,.9)),g.body(2,p=(0,-.9)),
           g.shape(category=1,mask=2),g.shape(1,parent=1,category=2,mask=1),g.shape(2,parent=2,category=2,mask=1),g.op(41),g.op(42)]
    items.append({'name':'batch-one-left','kind':'ticket','seed_seq':9,'seed_last':g.U64-1,'rows':one(batch,'whole batch LIMIT'),'expected_last_status':3,'stop_after_seq':9})
    items.append({'name':'max-reads','kind':'ticket','seed_seq':12,'seed_last':g.U64,'rows':one(setup+g.cycle()+[g.save(),g.get(),g.op(48,0,0),g.event_copy(),g.op(18,0,1),g.get()],'MAX reads/delete')})
    items.append({'name':'max-empty-pairs','kind':'ticket','seed_seq':12,'seed_last':g.U64,'rows':one(setup+g.cycle()+[g.save(),g.op(41),g.op(42)],'MAX empty PAIRS'),'expected_last_status':0,'stop_after_seq':13})
    items.append({'name':'shape-at-max','kind':'ticket','seed_seq':3,'seed_last':g.U64,'rows':one([g.world(),g.body(),g.shape()],'shape LIMIT'),'expected_last_status':3})
    for kind,geo in (('capsule-short',g.capsule(p1=(0,0),p2=(.001,0))),('segment-short',g.segment(p1=(0,0),p2=(.001,0)))):
        items.append({'name':kind,'kind':'short','rows':one([g.world(),g.body(),g.shape(geometry=geo,game=0)],kind),'expected_last_status':4 if kind=='segment-short' else 0})
    invalid=[]
    for field in range(4):
        for word in (0x7fc00000,0x7f800000,0xff800000,*((0xbf800000,) if field<3 else ())):invalid.append((field,word))
    for group in range(2):
        rows=[g.world(),g.body()]
        for field,word in invalid[14*group:14*(group+1)]:
            o=list(g.shape());o[1+45+field]=word;rows.append(tuple(o))
        items.append({'name':f'material40-{group}','kind':'material40','rows':one(rows,'invalid material40'),'expected_last_status':5})
    for route in (16,17):
        for field,word in invalid:
            rows=[g.world()]
            if route==17:rows.append(g.body())
            rows.append(g.g7.pair() if route==16 else g.g7.shape(game=True))
            items.append({'name':f'material-route{route}-{field}-{word:08x}','kind':'material-route','route':route,'field':field,'word':word,'rows':one(rows,'shared material route'),'expected_last_status':5})
    items.append({'name':'bitset-branches','kind':'bitset-helper','rows':one([],'direct bitset helper boundaries; empty stdin')})
                                                                            
                                                                          
    for n,name in enumerate(('range','occupied','birth-low','birth-high','contact-id','owner','world'),1):
        items.append({'name':'guard-'+name,'kind':'guard-helper','helper':n,'rows':one(setup+g.cycle()+[g.save(),g.get()],'actual contactStatus '+name),
                      'expected_guard_status':2 if name=='owner' else 1})
    require_definitions(items);return items

def require_definitions(items):
    assert len({x['name'] for x in items})==len(items)
    assert sum(x['kind']!='guard-helper' for x in items)<=64
    for x in items:
        assert len(x['rows'])==1 and len(x['rows'][0].ops)<=16,(x['name'],len(x['rows'][0].ops))
        assert sum(o[0] in (2,30,16) for o in x['rows'][0].ops)<=4

def apply_edit(source,scope,old,new,name):return mutator.apply(source,{'name':name,'scope':scope,'expression':old,'replacement':new})
def duck_driver(source,fixture):
    old='const CONTACT_PROFILE: i32 = 1i32;';assert source.count(old)==1;source=source.replace(old,'const CONTACT_PROFILE: i32 = 2i32;',1)
    if fixture['kind']=='bitset-helper':
        body='''fun main() -> i64 = {
    var a: bits.BitSet = bits.b2CreateBitSet(16i32);
    var b: bits.BitSet = bits.b2CreateBitSet(16i32);
    io.writeStr("BIT9 0"); outBitSet(&a); newline();
    bits.b2SetBitCountAndClear(&a, 129i32); bits.b2SetBitCountAndClear(&b, 129i32);
    bits.b2SetBit(&a, 31i32); bits.b2SetBit(&a, 32i32); bits.b2SetBit(&a, 63i32);
    bits.b2SetBit(&b, 64i32); bits.b2SetBit(&b, 127i32); bits.b2SetBit(&b, 128i32);
    bits.b2InPlaceUnion(&a, &b);
    io.writeStr("BIT9 1"); outBitSet(&a); newline();
    io.writeStr("BIT9 2"); outHex(if bits.b2GetBit(&a, 31i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 32i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 63i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 64i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 127i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 128i32) then 1u32 else 0u32);
    outHex(if bits.b2GetBit(&a, 255i32) then 1u32 else 0u32); newline();
    bits.b2ClearBit(&a, 31i32); bits.b2ClearBit(&a, 32i32); bits.b2ClearBit(&a, 63i32);
    bits.b2ClearBit(&a, 64i32); bits.b2ClearBit(&a, 127i32); bits.b2ClearBit(&a, 128i32);
    bits.b2ClearBit(&a, 255i32); io.writeStr("BIT9 3"); outBitSet(&a); newline();
    bits.b2SetBitGrow(&a, 255i32); bits.b2SetBitGrow(&a, 256i32); bits.b2SetBit(&a, 0i32);
    io.writeStr("BIT9 4"); outBitSet(&a); newline();
    bits.b2SetBitCountAndClear(&a, 65i32); io.writeStr("BIT9 5"); outBitSet(&a);
    outHex(if bits.b2GetBit(&a, 255i32) then 1u32 else 0u32); newline();
    bits.b2ClearBit(&a, 255i32); bits.b2GrowBitSet(&a, 4i32);
    io.writeStr("BIT9 6"); outBitSet(&a); newline();
    bits.b2SetBitCountAndClear(&a, 0i32); io.writeStr("BIT9 7"); outBitSet(&a); newline();
    bits.b2DestroyBitSet(&a); bits.b2DestroyBitSet(&b);
    io.writeStr("BIT9 8"); outBitSet(&a); newline(); return 0i64;
}'''
        lo,hi=mutator.function_span(source,'main');return source[:lo]+body+source[hi:]
    if fixture['kind']=='ticket':
        lo=fixture['seed_last']&g.U32;hi=fixture['seed_last']>>32;old='let op: Operation = readOperation(seq);'
        new=old+f'\n            if (seq == {fixture['seed_seq']}u32) game.lastIssued = words64.Key64({lo}u32, {hi}u32);'
        source=apply_edit(source,'main',old,new,fixture['name'])
    if fixture.get('stop_after_seq'):
        old='if (runOperation(&reg, id, seq, op, true) < 0i32) { cleanup(&reg); return failureCode; }'
        new=old+f'\n            if (seq == {fixture['stop_after_seq']}u32) {{ io.writeStr("GUARD9 BATCH\\n"); cleanup(&reg); return 0i64; }}'
        source=apply_edit(source,'main',old,new,fixture['name'])
    if fixture['kind']=='material-route':
        field=('friction','restitution','rollingResistance','tangentSpeed')[fixture['field']]
                                                                         
                                                                     
        old=MATERIAL_ROUTE_ANCHOR
        new=f'    op.source.{field} = fromBits({fixture['word']}u32);\n'+old
        source=apply_edit(source,'readOperation',old,new,fixture['name'])
    if fixture['kind']=='guard-helper':
        n=fixture['helper'];old='execution.contact = game.lookupContact(owner, reg.contacts[op.b].number); execution.status = execution.contact.status; return true;'
        prefix='var witness: game.ContactNumber = reg.contacts[op.b].number;\n        '
        if n==1:prefix+='raw.worlds.at(owner.slot as i64).contactIdPool.nextIndex = witness.slot;\n        '
        if n==2:prefix+='raw.worlds.at(owner.slot as i64).contacts.at(witness.slot as i64).setIndex = -1i32;\n        '
        if n==3:prefix+='witness.birthTicket.low = witness.birthTicket.low ^ 1u32;\n        '
        if n==4:prefix+='witness.birthTicket.high = witness.birthTicket.high ^ 1u32;\n        '
        if n==5:prefix+='raw.worlds.at(owner.slot as i64).contacts.at(witness.slot as i64).contactId = witness.slot + 1i32;\n        '
        if n==6:prefix+='witness.ownerTicket.low = witness.ownerTicket.low ^ 1u32;\n        '
        who='game.WorldNumber(owner.slot, words64.Key64(owner.birthTicket.low ^ 1u32, owner.birthTicket.high))' if n==7 else 'owner'
        new=prefix+f'let measured: i32 = game.contactStatus({who}, witness);\n        io.writeStr("GUARD9"); outDec(measured); newline(); failureCode = 0i64; inputOk = false; return false;'
        source=apply_edit(source,'runContactOperation',old,new,fixture['name'])
    return source

def c_defines(fixture):
    flags=[]
    if fixture['kind']=='bitset-helper':flags.append('-DBITSET9_HELPER=1')
    if fixture['kind']=='ticket':flags += [f'-DSEED9_SEQ={fixture['seed_seq']}',f'-DSEED9_LAST=UINT64_C({fixture['seed_last']})']
    if fixture['kind']=='speculative':flags.append('-DSPEC9_FALSE=1')
    if fixture['kind']=='guard-helper':flags.append('-DHELPER9='+str(fixture['helper']))
    if fixture['kind']=='material-route':flags += [f'-DMATERIAL9_FIELD={fixture['field']}',f'-DMATERIAL9_BITS=UINT32_C({fixture['word']})']
    if fixture.get('stop_after_seq'):flags.append('-DSTOP9_SEQ='+str(fixture['stop_after_seq']))
    return flags

def prepare_physics(physics,fixture):
    pass                                                                      
    if fixture['kind']=='speculative':
        file=physics/'swiat.dk';text=file.read_text(encoding='utf-8');old='enableSpeculative: bool = true;'
        if text.count(old)!=1:raise ValueError('speculative default single hit missing')
        file.write_text(text.replace(old,'enableSpeculative: bool = false;',1),encoding='utf-8')

def native_copy(C,ci,fixture,directory,name):
    physics=directory/'fizyka';shutil.copytree(ci.ROOT/'silnik/fizyka',physics)
    driver=directory/'kontakty.dk';source=(ci.PORT/'kontakty.dk').read_text(encoding='utf-8');source=duck_driver(source,fixture)
    prepare_physics(physics,fixture)
    driver.write_text(source,encoding='utf-8')
    return ci.compile_duck(name,driver,physics),driver,physics

def input_data(fixture,decimal):
    return b'' if fixture['kind']=='bitset-helper' else g.encode(fixture['rows'],decimal).encode('ascii')

def run(C,ci):
    items=definitions();manifest=[];results=[];directory=C.base.TEMP/'kontakty-fixtury'
    if directory.exists():raise ValueError('fixture directory exists')
    directory.mkdir()
    try:
        for fixture in items:
            name='fixture9-'+fixture['name'];work=directory/fixture['name'];work.mkdir()
            cb=ci.build_c_adapter(name+'-c',guard=True,defines=c_defines(fixture))
            db,_,_=native_copy(C,ci,fixture,work,name+'-duckling')
            paths=[];receipts=[]
            for side,binary,dec in (('c',cb,False),('duckling',db,True)):
                data=input_data(fixture,dec);result=ci.run(name+'-'+side,binary,data,c_side=side=='c');actual,path,stderr=result;paths.append(path)
                receipt=side_receipt(fixture,path,stderr,actual,ci.p);receipts.append(receipt)
                if 'model_error' in receipt['fields']:ci.save(name+'-'+side+'-model-error.json',{'error':receipt['fields']['model_error']})
                manifest.append({'fixture':fixture['name'],'side':side,'kind':fixture['kind'],'input_sha256':hashlib.sha256(data).hexdigest(),'operations':len(fixture['rows'][0].ops),'profile':2,'code':actual})
            signatures=[output_signature(path) for path in paths]
            difference=None if signatures[0]==signatures[1] else {'outputs':signatures}
            for receipt,signature in zip(receipts,signatures):
                receipt['conditions']['outputs_equal']=difference is None;receipt['fields']['output']=signature
                receipt['ok']=all(receipt['conditions'].values())
            ok=all(all(r['conditions'].values()) for r in receipts)
            if not ok:
                for side,receipt in zip(('c','duckling'),receipts):
                    receipt['fields']['difference']=difference
                    ci.save(name+'-'+side+'-odbior.json',receipt)
            results.append({'name':fixture['name'],'ok':bool(ok)});ci.save('kontakty-fixtury-wynik.json',results)
            for binary in (cb,db):
                ci.save(binary.name+'-sha256.json',{'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'bytes':binary.stat().st_size});binary.unlink()
            if work.resolve().is_relative_to(directory.resolve()):shutil.rmtree(work)
    finally:
        ci.save('kontakty-fixtury-manifest.json',manifest)
        if directory.resolve().is_relative_to(C.base.TEMP.resolve()):shutil.rmtree(directory)
    return int(not all(r['ok'] for r in results) or len(results)!=len(items))


def output_signature(path):
    with path.open('rb') as stream:return {'bytes':path.stat().st_size,'sha256':hashlib.file_digest(stream,'sha256').hexdigest()}


def side_receipt(fixture,path,stderr,actual,p):
    pass                                                                              
    fields={'code':actual,'stderr_bytes':stderr.stat().st_size};conditions={'code_zero':actual==0,'stderr_empty':not fields['stderr_bytes']}
    try:
        if fixture['kind']=='guard-helper':
            last=path.read_bytes().splitlines()[-1:];fields.update(last_line=[v.decode('ascii') for v in last],expected_guard_status=fixture['expected_guard_status'])
            conditions['guard_status']=last==[f'GUARD9 {fixture['expected_guard_status']}'.encode('ascii')]
        elif fixture['kind']=='bitset-helper':
            data=path.read_bytes();fields.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),expected_sha256=hashlib.sha256(bitset_expected()).hexdigest())
            conditions['bitset_words']=data==bitset_expected()
            fields['words']=[[int(v,16) for v in line.split()[2:]] for line in data.splitlines()]
            fields['expected_words']=[[int(v,16) for v in line.split()[2:]] for line in bitset_expected().splitlines()]
        elif fixture['kind']=='raw-hit':
            with path.open(encoding='ascii',newline='') as stream:hit=hit_receipt(stream,p)
            fields.update(hit['fields']);conditions.update(hit['conditions'])
        elif 'expected_last_status' in fixture:
            rs=[line.split() for line in path.read_text(encoding='ascii').splitlines() if line.startswith('R ')]
            last=int(rs[-1][4]) if rs else None;fields.update(last_status=last,expected_last_status=fixture['expected_last_status'])
            conditions['last_status']=last==fixture['expected_last_status']
    except (ValueError,IndexError,KeyError) as exc:conditions['literal_parse']=False;fields['literal_error']=str(exc)
    if fixture['kind'] not in ('guard-helper','bitset-helper'):
        seeds={fixture['seed_seq']:fixture['seed_last']} if fixture['kind']=='ticket' else None
        conditions['model_valid']=True
        try:
            if fixture.get('stop_after_seq'):
                text=path.read_text(encoding='ascii').replace('GUARD9 BATCH\n','ENDCASE 1\nEND 1\n')
                p.validate_output(text,fixture['rows'],guard=True,seed_last=seeds)
            else:
                with path.open(encoding='ascii',newline='') as stream:p.validate_output(stream,fixture['rows'],guard=True,seed_last=seeds)
        except (ValueError,IndexError,KeyError) as exc:conditions['model_valid']=False;fields['model_error']=str(exc)
    return {'conditions':conditions,'fields':fields}


def hit_receipt(lines,p):
    pass                                                                               
    tasks={};sims={};events={};private={};parse_error=None
    for line in lines:
        try:tag,v=p.parse_record(line)
        except (ValueError,IndexError,KeyError) as exc:parse_error=str(exc);break
        if tag=='TASK' and v[3]==1:tasks.setdefault(v[1],[]).append({'flags':v[21],'pointCount':v[32]})
        if tag=='CS':sims.setdefault(v[1],[]).append({'flags':v[19],'pointCount':v[30]})
        if tag=='GE' and v[4]==0:events[v[1]]={'begin':v[7],'end':v[8],'hit':v[9]}
        if tag=='EN9':private[v[1]]={'begin':v[3],'end0':v[4],'end1':v[5],'index':v[6],'hit':v[7]}
                                                                         
                                                                          
    checks={'task_sequences':set(tasks)=={8,14},'event_sequences':set(events)==set(range(1,17)),
            'private_sequences':set(private)==set(range(1,17)),
            'public_hit_empty':all(v['hit']==0 for v in events.values()),'private_hit_empty':all(v['hit']==0 for v in private.values())}
    for label,rows in (('tasks',tasks),('sims',sims)):
        for seq,hit,points in ((8,True,1),(14,False,0)):
            values=rows.get(seq,[]);checks[f'{label}_{seq}_count']=len(values)==1
            checks[f'{label}_{seq}_hit']=len(values)==1 and bool(values[0]['flags']&0x100000)==hit
            checks[f'{label}_{seq}_points']=len(values)==1 and values[0]['pointCount']==points
                                                                        
    checks['public_private_counts']=set(events)==set(private) and all(
        v['begin']==private[s]['begin'] and private[s]['index'] in (0,1) and
        v['end']==private[s]['end'+str(1-private[s]['index'])] for s,v in events.items())
    fields={'tasks':tasks,'sims':sims,'events':events,'private':private}
    if parse_error is not None:checks['parse_valid']=False;fields['parse_error']=parse_error
    return {'conditions':checks,'fields':fields}


def check_hit_trace(lines,p):
    return all(hit_receipt(lines,p)['conditions'].values())

def bitset_expected():
                                                                                  
    states=[(0,[0,1]),(1,[3,4,0x80000000,0x80000001,1,0x80000000,1,0]),
            (2,[1,1,1,1,1,1,0]),(3,[3,4,0,0,0,0,0,0]),
            (4,[5,7,1,0,0,0,0,0,0,0x80000000,1,0]),
            (5,[2,7,0,0,0,0,0]),(6,[4,7,0,0,0,0,0,0,0,0x80000000]),(7,[0,7]),(8,[0,0])]
    return ''.join('BIT9 '+str(i)+''.join(f' {x:08x}' for x in words)+'\n' for i,words in states).encode('ascii')


def profile_driver(source):
    old='const CONTACT_PROFILE: i32 = 1i32;'
    changed,hits=mutator.edit_sequence(source,[{'expression':old,'replacement':'const CONTACT_PROFILE: i32 = 2i32;'}])
    if hits!=[1]:raise ValueError('CONTACT_PROFILE 1i32: expected single hit, got '+str(hits[0]))
    return changed


def check_anchors(root,*,report=False):
    pass                                                                     
    checks=[]
    for fixture in definitions():
        row={'name':fixture['name'],'file':'silnik/port/kontakty.dk','scope':'duck_driver / CONTACT_PROFILE','ok':True}
        try:
            source=(Path(root)/row['file']).read_text(encoding='utf-8')
            duck_driver(source,fixture)
            if fixture['kind']=='speculative':
                text=(Path(root)/'silnik/fizyka/swiat.dk').read_text(encoding='utf-8')
                if text.count('enableSpeculative: bool = true;')!=1:
                    raise ValueError('speculative default single hit missing')
        except (OSError,ValueError,AssertionError) as exc:
            row.update(ok=False,error=str(exc) or type(exc).__name__)
        checks.append(row)
    bad=[row for row in checks if not row['ok']]
    if bad and not report:
        raise AssertionError('Niepasujace przygotowania ('+str(len(bad))+'):\n'+'\n'.join(row['name']+': '+row['error'] for row in bad))
    return checks
