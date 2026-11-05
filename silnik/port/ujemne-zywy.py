pass                                                                     

                                                                               
                                                                            
                                                                            
   
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('zywy_negative_inputs11', HERE/'przypadki-sen.py')
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)
op, bits = g.op, g.bits

CLASSES = ('HEADER', 'N_RANGE', 'SEQUENCE', 'WORDS', 'OPCODE', 'MODE', 'BOOL', 'UNUSED',
           'REGISTER', 'COPY', 'DOMAIN', 'PROFILE', 'PHASE', 'POPULATION', 'EOF', 'TRAILING_DATA')


def operations(rows, decimal=False):
    fmt = str if decimal else lambda value: f'{value:08x}'
    for j, row in enumerate(rows, 1):
        if len(row) != 65 or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in row):
            raise ValueError('operation requires opcode and 64 u32 words')
        yield f'O {j} {row[0]} '+' '.join(map(fmt, row[1:]))+'\n'


def encode(rows, decimal=False, profile='GUARD12'):
    if profile == 'GUARD12':
        prefix = 'GUARD12 1\nG 1 0 0 '+str(len(rows))+'\nGA 1 '+' '.join(['0' if decimal else '00000000']*64)+'\n'
    else:
        prefix = profile+' 1\nC 1 '+str(len(rows))+'\n'
    return (prefix+''.join(operations(rows, decimal))).encode('ascii')


def body(slot=0, owner=0):
    old = g.body(slot=slot, owner=owner)
    return op(90, *old[1:20], 1, 0, *([0]*32), 0, 0, 0)


def setup():
    return (g.world(), body(), g.shape(0, parent=0, geometry=g.circle(r=1)))


def changed(row, index, value):
    result = list(row)
    result[1+index] = value
    return tuple(result)


def edit_token(data, tag, index, value, occurrence=-1):
    lines = data.decode('ascii').splitlines(keepends=True)
    locations = [j for j, line in enumerate(lines) if line.startswith(tag+' ')]
    at = locations[occurrence]
    words = lines[at].rstrip('\n').split(' ')
    words[index] = value
    lines[at] = ' '.join(words)+'\n'
    return ''.join(lines).encode('ascii')


@dataclass(frozen=True)
class Negative:
    name: str
    error: str
    c: bytes
    duckling: bytes
    controls: tuple
    completed: int
    boundary: str = 'operation'
    profile: str = 'GUARD12'
    subclass: str = ''
    priority: str = ''

    @property
    def stderr(self):
        return ('PORT12: INPUT_'+self.error+'\n').encode('ascii')


def variants(part='12c'):
    result = []
    maximum_public = {'12a': 72, '12b': 136, '12c': 160}[part]
    def add(name, error, rows, bad=None, *, completed=None, edit=None,
            boundary='operation', profile='GUARD12', prelude=True, priority=''):
                                                                              
                                                                                  
        for extra in ((False, True) if prelude else (False,)):
            before = (g.world(slot=1),) if extra else ()
            controls, values = [], []
            for decimal in (False, True):
                controls.append(encode((*before, *rows), decimal, profile))
                value = encode((*before, *(bad if bad is not None else rows)), decimal, profile)
                if edit:
                    value = edit(value, decimal)
                values.append(value)
            count = (len(rows)-1 if completed is None else completed)+len(before)
            result.append(Negative(name+('-after-O' if extra else ''), error, *values, tuple(controls),
                                   count, boundary, profile, name, priority))

    world = g.world()
    harmless = op(91, 0, 0, 0, 1)
    full = setup()
    body_mut = op(80, 0, 0, 1, 4, bits(.5))
    shape_mut = op(81, 0, 0, 0, 0, bits(.5))
    def word(index, value):
        return lambda data, dec: edit_token(data, 'O', 3+index, str(value) if dec else f'{value:08x}')

    for profile, maximum in (('PORT12', maximum_public), ('GUARD12', 1), ('COMPONENT12', 32)):
        for name, transform in (
            ('tag', lambda d: b'PORT1X 1\n'+d.split(b'\n',1)[1]),
            ('BOM', lambda d: b'\xef\xbb\xbf'+d),
            ('tab', lambda d: d.replace(b' 1\n', b'\t1\n', 1)),
            ('spacing', lambda d: d.replace(b' 1\n', b'  1\n', 1)),
            ('CR', lambda d: d.replace(b'\n', b'\r', 1)),
            ('nonASCII', lambda d: b'\xff'+d),
            ('overlong', lambda d: b'X'*2049+b'\n'+d),
            ('N-noncanonical', lambda d: d.replace(b' 1\n', b' 01\n', 1)),
        ):
            add(profile+'-'+name, 'HEADER', (world,), completed=0,
                edit=lambda d, dec, fn=transform: fn(d), boundary='header', profile=profile, prelude=False)
        for n in (0, maximum+1, 4294967296):
            add(profile+'-N-'+str(n), 'N_RANGE', (world,), completed=0,
                edit=lambda d, dec, n=n: d.replace(b' 1\n', (' '+str(n)+'\n').encode(), 1),
                boundary='header', profile=profile, prelude=False)

    for field, value in ((1, '2'), (1, '01'), (2, '0'), (2, '801'), (2, '4294967296')):
        add('C-structure-'+str(field)+'-'+value, 'SEQUENCE', (world,), completed=0,
            edit=lambda d, dec, f=field, v=value: edit_token(d, 'C', f, v),
            profile='PORT12', boundary='case', prelude=False)
    add('O-seq', 'SEQUENCE', (world, harmless), edit=lambda d, dec: edit_token(d, 'O', 1, '4'))
    add('O-seq-noncanonical', 'SEQUENCE', (world, harmless), edit=lambda d, dec: edit_token(d, 'O', 1, '02'))

    for name, transform in (
        ('63ai-LF', lambda d, dec: d.rsplit(b' ', 1)[0]+b'\n'),
        ('65ai', lambda d, dec: d[:-1]+b' '+(b'0' if dec else b'00000000')+b'\n'),
        ('u32-overflow', lambda d, dec: edit_token(d, 'O', 66, '4294967296' if dec else '100000000')),
        ('lexical-word', lambda d, dec: edit_token(d, 'O', 66, '-1' if dec else '0000000A')),
        ('spacing', lambda d, dec: d.replace(b'O 2 ', b'O  2 ', 1)),
        ('tab', lambda d, dec: d.replace(b'O 2 ', b'O\t2 ', 1)),
        ('BOM', lambda d, dec: d.replace(b'O 2 ', b'\xef\xbb\xbfO 2 ', 1)),
        ('CR', lambda d, dec: d[:-1]+b'\r'),
        ('nonASCII', lambda d, dec: d.replace(b'O 2 ', b'\xffO 2 ', 1)),
        ('overlong', lambda d, dec: d[:d.rindex(b'O ')]+b'O '+b'9'*2048+b'\n'),
    ):
        add('O-'+name, 'WORDS', (world, harmless), edit=transform, prelude=False)
    add('byte-name256', 'WORDS', (*full, op(84, 0, 0, 1, 0, 1, 97)), edit=word(5, 256))

    for code in (6, 63, 79, 93):
        add('opcode-'+str(code), 'OPCODE', (world, harmless),
            edit=lambda d, dec, code=code: edit_token(d, 'O', 2, str(code)))
    for code, index, kind in ((80, 3, 9), (81, 3, 9), (82, 2, 6), (86, 2, 4), (87, 1, 4), (92, 3, 6)):
        row = {80: body_mut, 81: shape_mut, 82: op(82, 0, 1, 0, 1),
               86: op(86, 0, 0, 0, 1), 87: op(87, 0, 0, 0), 92: op(92, 0, 0, 1, 0)}[code]
        add('kind-'+str(code), 'OPCODE', (*full, row), edit=word(index, kind))
    for code, row, index in ((80, body_mut, 2), (81, shape_mut, 2), (82, op(82,0,1,0,1),1)):
        add('mode-'+str(code), 'MODE', (*full, row), edit=word(index, 2))
    for name, row, index in (('enabled', op(80,0,0,1,1,1),4), ('event', op(83,0,1,0,1,0,1),5),
                             ('present',op(85,0,0,0,1,1,0,0),4)):
        add('bool-'+name, 'BOOL', (*full, row), edit=word(index, 2))
    for name, row, index, value in (
        ('minus-zero', body_mut,63,0x80000000),
        ('name-tail',op(84,0,0,1,0,0),5,97),
        ('null-name',op(84,0,0,1,1,0),4,1),
        ('absent-object',op(85,0,0,0,1,0),5,1),
        ('game-hook-function',op(86,0,1,0,1),4,1),
        ('clear-rule-data',op(87,0,0,0),3,1),
    ):
        add('unused-'+name, 'UNUSED', (*full,row), edit=word(index,value))
    add('unused-copy-read-world', 'UNUSED', (*full,harmless), (*full,op(89,2,1,0,0)))
    for name, row, index, value in (('world-range',body_mut,0,16), ('body-range',body_mut,1,256),
                                    ('shape-range',shape_mut,1,512)):
        add('register-'+name,'REGISTER',(*full,row),edit=word(index,value))
    add('register-uninitialized-world', 'REGISTER', (world,), (harmless,), completed=0,
        prelude=False)
    add('register-uninitialized-body', 'REGISTER', (world, harmless), (world, body_mut))
    add('register-uninitialized-shape', 'REGISTER', (world, harmless), (world, shape_mut))
    add('register-live-collision', 'REGISTER', (*full, harmless), (*full, body()))
    add('copy-uninitialized-K12', 'COPY', (world, harmless), (world, op(89,2,0,0,0)))
    add('copy-range-K12', 'REGISTER', (world, harmless), (world, op(89,2,0,0,4)))
    add('copy-old-K8-uninitialized', 'REGISTER', (world, harmless), (world, op(37,1,0)))
    for name, row in (
        ('raw-friction-negative',op(81,0,0,0,0,bits(-1))),
        ('raw-friction-inf',op(81,0,0,0,0,0x7f800000)),
        ('raw-maximum-zero',op(82,0,0,4,0)),
        ('type-enum',op(80,0,0,1,0,3)),
        ('target-enum',op(83,0,2,0,1,0,1)),
        ('event-enum',op(83,0,1,0,1,3,1)),
        ('fixture-combination',op(86,0,0,0,1,3)),
        ('fixture-id',op(86,0,0,0,1,6)),
    ):
        add('domain-'+name,'DOMAIN',(*full,harmless),(*full,row))
    add('body-preSolve-raw','PROFILE',(*full,harmless),(*full,op(83,0,0,0,0,2,1)))
                                                                        
                                                                         
    add('private-phase-64','PHASE',(world,body(),harmless),(world,body(),op(64,0,3,0,0)))
    add('third-live-world','POPULATION',(g.world(),g.world(slot=1),op(1,0)),
        (g.world(),g.world(slot=1),g.world(slot=2)),completed=2,prelude=False)

                                                                               
                                                                           
    add('EOF-no-header','EOF',(world,),completed=0,edit=lambda d, dec:b'',boundary='header',prelude=False)
    add('EOF-header-partial','EOF',(world,),completed=0,edit=lambda d, dec:b'GUARD12',boundary='header',prelude=False)
    add('EOF-before-G','EOF',(world,),completed=0,edit=lambda d, dec:b'GUARD12 1\n',boundary='frame',prelude=False)
    add('EOF-O-short','EOF',(world,harmless),edit=lambda d, dec:d.rsplit(b' ',1)[0],prelude=False)
    add('EOF-no-O','EOF',(world,harmless),edit=lambda d, dec:d[:d.rindex(b'O ')],prelude=False)
    for name, tail in (('LF',b'\n'),('word',b'x'),('operation',b'O 2 79\n')):
        add('trailing-'+name,'TRAILING_DATA',(world,),completed=1,
            edit=lambda d, dec, tail=tail:d+tail,boundary='trailing',prelude=False)

                                                                           
                                                                           
    def physical(tag,kind):
        def edit(data,decimal):
            lines=data.splitlines(keepends=True)
            i=next(i for i,line in enumerate(lines) if line.startswith(tag.encode()+b' '))
            line=lines[i]
            if kind=='tag':line=b'X'+line[len(tag):]
            elif kind=='BOM':line=b'\xef\xbb\xbf'+line
            elif kind=='tab':line=line.replace(b' ',b'\t',1)
            elif kind=='spacing':line=line.replace(b' ',b'  ',1)
            elif kind=='CR':line=line[:-1]+b'\r'
            elif kind=='nonASCII':line=b'\xff'+line
            elif kind=='overlong':line=tag.encode()+b' '+b'9'*2048+b'\n'
            elif kind=='arity-short':line=line.rsplit(b' ',1)[0]+b'\n'
            elif kind=='arity-long':line=line[:-1]+b' '+(b'0' if decimal else b'00000000')+b'\n'
            lines[i]=line;return b''.join(lines)
        return edit
    for tag,error in (('G','SEQUENCE'),('GA','WORDS')):
        for kind in ('tag','BOM','tab','spacing','CR','nonASCII','overlong','arity-short','arity-long'):
            add(tag+'-physical-'+kind,error,(world,),completed=0,edit=physical(tag,kind),boundary='frame',prelude=False)
    for field,value in ((1,'01'),(1,'4294967296'),(2,'00'),(3,'01'),(4,'01'),(4,'0'),(3,'2')):
        add('G-prefix-'+str(field)+'-'+value,'SEQUENCE',(world,),completed=0,
            edit=lambda d,dec,f=field,v=value:edit_token(d,'G',f,v),boundary='frame',prelude=False)
    for name,error,edit in (
        ('id-leading-zero','SEQUENCE',lambda d,dec:edit_token(d,'GA',1,'01')),
        ('id-wrong','SEQUENCE',lambda d,dec:edit_token(d,'GA',1,'2')),
        ('u32-overflow','WORDS',lambda d,dec:edit_token(d,'GA',65,'4294967296' if dec else '100000000')),
        ('word-canonical','WORDS',lambda d,dec:edit_token(d,'GA',65,'00' if dec else '0000000A')),
        ('unused','UNUSED',lambda d,dec:edit_token(d,'GA',65,'1' if dec else '00000001')),
    ):
        add('GA-'+name,error,(world,),completed=0,edit=edit,boundary='frame',prelude=False)
    for name,data in (('G-partial',b'GUARD12 1\nG 1'),('before-GA',b'GUARD12 1\nG 1 0 0 1\n'),
                      ('GA-partial',b'GUARD12 1\nG 1 0 0 1\nGA 1')):
        add('EOF-'+name,'EOF',(world,),completed=0,edit=lambda d,dec,data=data:data,boundary='frame',prelude=False)

                                                                           
    def math_input(decimal):
        return ('COMPONENT12 1\nF 1 100 '+' '.join(['0' if decimal else '00000000']*64)+'\n').encode('ascii')
    math_controls=tuple(math_input(decimal) for decimal in (False,True))
    def math_bad(name,error,edit):
        values=tuple(edit(data,decimal) for data,decimal in zip(math_controls,(False,True)))
        result.append(Negative(name,error,*values,math_controls,0,'math-frame','COMPONENT12',name,'§11 F physical before prefixes before ai'))
    for kind in ('tag','BOM','tab','spacing','CR','nonASCII','overlong','arity-short','arity-long'):
        math_bad('F-physical-'+kind,'WORDS',physical('F',kind))
    for field,value in ((1,'01'),(1,'2'),(2,'0100'),(2,'4294967296')):
        math_bad('F-prefix-'+str(field)+'-'+value,'SEQUENCE',lambda d,dec,f=field,v=value:edit_token(d,'F',f,v))
    math_bad('F-u32-overflow','WORDS',lambda d,dec:edit_token(d,'F',66,'4294967296' if dec else '100000000'))
    math_bad('F-unused','UNUSED',lambda d,dec:edit_token(d,'F',66,'1' if dec else '00000001'))
    math_bad('F-domain-infinite','DOMAIN',lambda d,dec:edit_token(d,'F',3,str(0x7f800000) if dec else '7f800000'))
    math_bad('F-EOF-partial','EOF',lambda d,dec:d.rsplit(b' ',1)[0])

    def combined(*edits):
        def edit(data,decimal):
            for change in edits:data=change(data,decimal)
            return data
        return edit
    precedences=(
        ('word-before-mode','WORDS',body_mut,combined(word(2,2),word(63,0x100000000))),
        ('opcode-before-word','OPCODE',body_mut,combined(word(63,0x100000000),lambda d,dec:edit_token(d,'O',2,'79'))),
        ('physical-before-opcode','WORDS',body_mut,combined(lambda d,dec:edit_token(d,'O',2,'79'),lambda d,dec:edit_token(d,'O',0,'X'))),
        ('mode-before-unused-register','MODE',body_mut,combined(word(2,2),word(63,1),word(1,256))),
        ('kind-before-unused','OPCODE',body_mut,combined(word(3,9),word(63,1))),
        ('bool-before-unused','BOOL',op(80,0,0,1,1,1),combined(word(4,2),word(63,1))),
        ('unused-before-register','UNUSED',body_mut,combined(word(1,256),word(63,1))),
        ('register-before-raw-domain','REGISTER',op(81,0,0,0,0,bits(.5)),combined(word(1,512),word(4,bits(-1)))),
    )
    for name,error,row,edit in precedences:
        add('priority-'+name,error,(*full,row),edit=edit,priority=name)

    if len(result)>256 or len({p.name for p in result})!=len(result):
        raise ValueError('negative fixture budget/identity')
    if set(CLASSES)!={p.error for p in result}:
        raise ValueError('missing fatal class')
    return tuple(result)


def phase_variants():
    pass                                                                   

                                                                            
                                                                        
                                                                            
       
    result=[]
    touching=(*setup(),body(slot=1),g.shape(1,parent=1,geometry=g.circle(r=1)),
              g.step(),op(46,0,0,1,0))
    specifications=[(code,(g.world(),),op(code,0)) for code in range(41,46)]
    specifications.extend((
        (51,touching,op(51,0,0,bits(1),0,0,1)),
        (52,setup(),op(52,0,0,bits(.5),0,0,0,0)),
        (53,touching,op(53,0,0,0)),
    ))
    for code,prior,row in specifications:
        for extra in (False,True):
            before=(g.world(slot=1),) if extra else ()
            controls=tuple(encode((*before,*prior,op(91,0,0,0,1)),d) for d in (False,True))
            bad=tuple(encode((*before,*prior,row),d) for d in (False,True))
            name='private-phase-'+str(code)+('-after-O' if extra else '')
            result.append(Negative(name,'PHASE',*bad,controls,len(before)+len(prior),
                                   subclass='legal-source-private-'+str(code),
                                   priority='source/domain before profile PHASE'))
    return tuple(result)


def route_precedence_variants():
    pass                                                                

                                                                        
                                                                
       
    full=setup()
    specifications=[
        ('mode-83',op(83,0,1,0,1,0,1),'MODE',((3,2),)),
        ('mode-84',op(84,0,0,1,0,0),'MODE',((2,2),)),
        ('mode-85',op(85,0,0,0,1,0),'MODE',((3,2),)),
        ('mode-86',op(86,0,1,0,1),'MODE',((1,2),)),
        ('mode-88',op(88,0,1,0,0),'MODE',((1,2),)),
        ('mode-90',body(slot=1),'MODE',((2,2),)),
        ('mode-91',op(91,0,0,0,1),'MODE',((3,2),)),
        ('mode-92',op(92,0,0,1,0,0,0),'MODE',((2,2),)),
        ('mode-before-kind80',op(80,0,0,1,4,bits(.5)),'MODE',((2,2),(3,9))),
        ('mode-before-bool83',op(83,0,1,0,1,0,1),'MODE',((3,2),(5,2))),
        ('kind-before-bool86',op(86,0,1,0,1),'OPCODE',((2,4),(3,2))),
        ('unused-before-copy89',op(91,0,0,0,1),'UNUSED',()),
    ]
    result=[]
    for name,row,error,changes in specifications:
        bad=op(89,2,1,0,0) if name=='unused-before-copy89' else row
        for index,value in changes:bad=changed(bad,index,value)
        for extra in (False,True):
            prior=((g.world(slot=1),) if extra else ())+full
            controls=tuple(encode((*prior,row),d) for d in (False,True))
            values=tuple(encode((*prior,bad),d) for d in (False,True))
            result.append(Negative('route-priority-'+name+('-after-O' if extra else ''),
                error,*values,controls,len(prior),subclass=name,
                priority='mode -> kind/bool -> unused -> registers/copies'))
    return tuple(result)


def positives():
    data = encode((g.world(),))
    decimal = encode((g.world(),),True)
    return (('LF', data, decimal), ('CRLF', data.replace(b'\n',b'\r\n'),decimal.replace(b'\n',b'\r\n')),
            ('last-O-without-LF',data[:-1],decimal[:-1]))


def expected_prefix(probe, control):
    if probe.boundary=='header':
        return b''
    if probe.completed:
        marker=f'Z12 1 {probe.completed} '.encode('ascii')
        lines=control.splitlines(keepends=True)
        at=next((i for i,line in enumerate(lines) if line.startswith(marker)),None)
        if at is None:
            raise ValueError('negative control missing completed Z12')
        return b''.join(lines[:at+1])
    if probe.boundary=='case':
        return control.split(b'CASE ',1)[0]
    if probe.boundary=='math-frame':
        return control.split(b'CASE ',1)[0]
    if probe.boundary=='frame':
                                                                           
                                                                               
        return b''
    return control.split(b'E 1 1 ',1)[0]


def check(probe, code, output, stderr, control):
    if code!=2 or stderr!=probe.stderr:
        raise ValueError(probe.name+': expected code2/stderr '+repr(probe.stderr)+
                         ', actual code='+str(code)+' stderr='+repr(stderr[:2048]))
    expected=expected_prefix(probe,control)
    if output!=expected:
        at=next((i for i,(a,b) in enumerate(zip(output,expected)) if a!=b),min(len(output),len(expected)))
        raise ValueError(probe.name+': fatal stdout differs at byte '+str(at)+
                         '; expected='+repr(expected[max(0,at-128):at+512])+', actual='+repr(output[max(0,at-128):at+512]))


UNREACHABLE_AFTER_O = {
    'INPUT_HEADER':'NIEOSIAGALNE — D12-1(2); C main validates header before its id/seq loops; D main/guardMain/componentMain12 likewise enter header only once.',
    'INPUT_N_RANGE':'NIEOSIAGALNE — D12-1(2); initial N is checked before the first case/O; later id/opCount errors are INPUT_SEQUENCE.',
}

LIMITATIONS = (
    'G/GA/F frame subclasses are supplied; additional composite prefix/word precedences still require audit.',
    'Private41..45/51..53 have separate legal-source PHASE controls; composite source/domain/phase precedence intersections still need audit.',
    'Every parser first-error precedence intersection must be audited; this initial corpus is incomplete.',
    'No native parser run is implied by fixture generation or all16 class names.',
)
