pass                                                   

                                                                          
                                                                           
   
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sen_negative_fixtures', HERE / 'fixtury-sen.py')
f = importlib.util.module_from_spec(spec); sys.modules[spec.name] = f; spec.loader.exec_module(f)
ERRORS = dict(zip((f'F{i:02}' for i in range(1, 16)), (
    'HEADER', 'N_RANGE', 'SEQUENCE', 'WORDS', 'BOOL', 'UNUSED', 'OPCODE', 'MODE',
    'REGISTER', 'DOMAIN', 'PHASE', 'POPULATION', 'PROFILE', 'EOF', 'TRAILING_DATA')))


@dataclass(frozen=True)
class Negative:
    name: str
    error: str
    c: bytes
    duckling: bytes
    controls: tuple
    boundary: tuple

    @property
    def stderr(self):
        return ('PORT11: INPUT_' + ERRORS[self.error] + '\n').encode('ascii')


def variants():
    result = []

    def add(name, error, rows, change, boundary, profile='PORT11'):
        controls = tuple(f.public_bytes(rows, d, profile) for d in (False, True))
        data = tuple(change(control, d) for control, d in zip(controls, (False, True)))
        result.append(Negative(name, error, *data, controls, boundary))

    def word(seq, index, value):
        def edit(data, decimal):
            lines = data.decode('ascii').splitlines()
            line_index = 1 + seq
            words = lines[line_index].split(' ')
            words[3 + index] = str(value) if decimal else f'{value:08x}'
            lines[line_index] = ' '.join(words)
            return ('\n'.join(lines) + '\n').encode('ascii')
        return edit

    basic = (f.world(),)
    setup = (f.world(), f.body())
    for suffix, change in (
        ('tag', lambda b, d: b.replace(b'PORT11', b'PORT1X', 1)),
        ('ascii', lambda b, d: b'\xff' + b), ('bom', lambda b, d: b'\xef\xbb\xbf' + b),
        ('empty', lambda b, d: b'\n' + b), ('spacing', lambda b, d: b.replace(b' ', b'  ', 1)),
        ('leading-space', lambda b, d: b' ' + b),
        ('trailing-space', lambda b, d: b.replace(b'1\n', b'1 \n', 1)),
        ('tab', lambda b, d: b.replace(b' ', b'\t', 1)),
        ('cr', lambda b, d: b.replace(b'1\n', b'1\r', 1))):
        add('F01-' + suffix, 'F01', basic, change, ('header',))
                                                                             
    max_n=json.loads((HERE/'sen-przypadki.json').read_bytes())['N']
    for n in (b'0', str(max_n+1).encode('ascii')):
        add('F02-' + n.decode(), 'F02', basic,
            lambda b, d, n=n: b.replace(b'PORT11 1\n', b'PORT11 ' + n + b'\n'), ('header',))
    for suffix, old, new, boundary in (
        ('case-id', b'C 1 1', b'C 2 1', ('case',)),
        ('n-leading-zero', b'PORT11 1', b'PORT11 01', ('header',)),
        ('n-sign', b'PORT11 1', b'PORT11 +1', ('header',)),
        ('n-minus', b'PORT11 1', b'PORT11 -1', ('header',)),
        ('case-leading-zero', b'C 1 1', b'C 01 1', ('case',)),
        ('opcount-zero', b'C 1 1', b'C 1 0', ('case',)),
        ('opcount-large', b'C 1 1', b'C 1 1281', ('case',)),
        ('seq', b'O 1 56', b'O 2 56', ('operation', 1)),
        ('seq-leading-zero', b'O 1 56', b'O 01 56', ('operation', 1))):
        add('F03-' + suffix, 'F03', basic, lambda b, d, old=old, new=new: b.replace(old, new, 1), boundary)
    def token(value_c, value_d):
        def edit(b, d):
            lines = b.splitlines(); words = lines[-1].split(b' ')
            words[-1] = value_d if d else value_c
            lines[-1] = b' '.join(words)
            return b'\n'.join(lines) + b'\n'
        return edit
    for suffix, c, d in (('overflow', b'100000000', b'4294967296'),
                         ('bad-word', b'0000000g', b'x'), ('uppercase', b'0000000A', b'01'),
                         ('short', b'0', b'+0'), ('signed', b'-0000001', b'-1')):
        add('F04-' + suffix, 'F04', basic, token(c, d), ('operation', 1))
    add('F04-arity63', 'F04', basic, lambda b, d: b.rsplit(b' ', 1)[0] + b'\n', ('operation', 1))
    add('F04-arity65', 'F04', basic, lambda b, d: b.rstrip(b'\n') + (b' 0\n' if d else b' 00000000\n'), ('operation', 1))
    add('F04-line2049', 'F04', basic, lambda b, d: b.split(b'O ', 1)[0] + b'O 1 56 ' + b'0' * 2049 + b'\n', ('operation', 1))
    for seq, index, rows, label in ((1, 10, basic, 'warm'), (1, 11, basic, 'world-sleep'),
                                    (2, 14, setup, 'fixed'), (2, 15, setup, 'fast'),
                                    (2, 16, setup, 'body-sleep'), (2, 17, setup, 'awake')):
        add('F05-' + label, 'F05', rows, word(seq, index, 2), ('operation', seq))
    add('F06-unused-signzero', 'F06', basic, word(1, 12, 0x80000000), ('operation', 1))
    add('F06-body-unused', 'F06', setup, word(2, 19, 1), ('operation', 2))
    for opcode in (6, 20, 22, 63, 65):
        add(f'F07-opcode{opcode}', 'F07', basic,
            lambda b, d, opcode=opcode: b.replace(b'O 1 56 ', f'O 1 {opcode} '.encode(), 1), ('operation', 1))
    add('F08-world-mode', 'F08', basic, word(1, 1, 2), ('operation', 1))
    add('F08-body-mode', 'F08', setup, word(2, 2, 2), ('operation', 2))
    add('F09-empty-source', 'F09', basic,
        lambda b, d: f.public_bytes((f.op(62, 0, 0, 1),), d), ('operation', 1))
    add('F09-world-range', 'F09', basic, word(1, 0, 16), ('operation', 1))
    add('F09-body-range', 'F09', setup, word(2, 1, 256), ('operation', 2))
    add('F09-target-collision', 'F09', (f.world(), f.world(1)), word(2, 0, 0), ('operation', 2))
    raw = (*setup, f.op(60, 0, 0, 0, f.bits(.05)))
    add('F10-threshold-negative', 'F10', raw, word(3, 3, f.bits(-1)), ('operation', 3))
    add('F10-body-type', 'F10', setup, word(2, 3, 3), ('operation', 2))
    add('F10-rotation', 'F10', setup, word(2, 6, 0), ('operation', 2))
                                                                        
    result[-1] = _with_raw_body(result[-1], 2)
    add('F11-component-in-public', 'F11', (*setup, f.op(62, 0, 0, 1)),
        lambda b, d: f.public_bytes((*setup, f.op(64, 0, 3, 0, 0)), d), ('operation', 3))
    add('F12-world-population', 'F12', (f.world(), f.world(1), f.op(61, 0, 1, 1)),
        lambda b, d: f.public_bytes((f.world(), f.world(1), f.world(2)), d), ('operation', 3))
    for mask in (1, 2, 4, 8, 16, 32):
        rows = (*setup, f.op(64, 0, 3, 0, 0))
        add(f'F13-profile-{mask}', 'F13', rows, word(3, 3, mask), ('operation', 3), 'COMPONENT11')
    add('F14-operation-eof', 'F14', basic, lambda b, d: b.split(b'O ', 1)[0] + b'O 1 56', ('operation', 1))
    add('F14-case-eof', 'F14', basic, lambda b, d: b'PORT11 1\n', ('case',))
    for suffix, extra in (('blank', b'\n'), ('text', b'x'), ('operation', b'O 2 62\n')):
        add('F15-' + suffix, 'F15', setup, lambda b, d, extra=extra: b + extra, ('trailing',))
    add('F01-case-tag', 'F01', basic, lambda b, d: b.replace(b'\nC ', b'\nX ', 1), ('case',))
    add('F01-operation-tag', 'F01', basic, lambda b, d: b.replace(b'\nO ', b'\nX ', 1), ('operation', 1))
    add('F09-empty-copy', 'F09', basic,
        lambda b, d: f.public_bytes((f.op(37, 0),), d), ('operation', 1))
    add('F10-component-kind', 'F10', (*setup, f.op(64, 0, 3, 0, 0)),
        word(3, 1, 0), ('operation', 3), 'COMPONENT11')
    seed_setup = (f.world(), f.body(), f.body(1, position=(0, .9)),
                  f.g.shape(geometry=f.g.box()), f.g.shape(1, parent=1, geometry=f.g.box()),
                  *f.g.cycle(), f.g.save())
    seed_rows = (*seed_setup, f.op(51, 0, 0, *f.g.seed()))
    seq = len(seed_rows)
    add('F10-manifold-pointcount', 'F10', seed_rows, word(seq, 5, 3), ('operation', seq), 'COMPONENT11')
    add('F10-cache-count', 'F10', seed_rows, word(seq, 32, 4), ('operation', seq), 'COMPONENT11')
    result.extend(guard_variants())
    if len(result) > 256 or {p.error for p in result} != set(ERRORS):
        raise ValueError('fatal probe coverage/budget')
    return tuple(result)


def guard_variants():
    pass                                                                 

                                                                            
                                                                   
       
    result = []
    item = next(p for p in f.definitions() if p.name == 'WORLD-FIN-4')
    def add(name, error, change, fixture=item):
        controls = (fixture.encode(False), fixture.encode(True))
        data = tuple(change(b, decimal) for b,decimal in zip(controls,(False,True)))
        result.append(Negative(name,error,*data,controls,('header',)))
    def frame(row, word, replacement):
        def edit(data, decimal):
            lines = data.splitlines(); fields = lines[row].split(b' ')
            fields[word] = replacement; lines[row] = b' '.join(fields)
            return b'\n'.join(lines)+b'\n'
        return edit
    for value in (b'0',b'2'):
        add('G-F02-N-'+value.decode(),'F02',frame(0,1,value))
    for suffix, row, field, value in (
        ('id',1,1,b'2'),('id-leading-zero',1,1,b'01'),('kind-leading-zero',1,2,b'01'),
        ('helper-opcount',1,4,b'1'),('helper-seed',1,3,b'1'),('GA-id',2,1,b'2')):
        add('G-F03-'+suffix,'F03',frame(row,field,value))
    for suffix,row in (('G-tag',1),('GA-tag',2)):
        add('G-F01-'+suffix,'F01',frame(row,0,b'X'))
    for suffix,c,d in (('overflow',b'100000000',b'4294967296'),
                       ('word',b'0000000g',b'x'),('canonical',b'0000000A',b'01')):
        add('G-F04-'+suffix,'F04',lambda b,dec,c=c,d=d: frame(2,65,d if dec else c)(b,dec))
    add('G-F04-arity63','F04',lambda b,d: b.rsplit(b' ',1)[0]+b'\n')
    add('G-F04-arity65','F04',lambda b,d: b.rstrip(b'\n')+(b' 0\n' if d else b' 00000000\n'))
    add('G-F05-warm','F05',lambda b,d: frame(2,12,b'2' if d else b'00000002')(b,d))
    add('G-F06-unused','F06',lambda b,d: frame(2,13,b'2147483648' if d else b'80000000')(b,d))
    add('G-F09-world-range','F09',lambda b,d: frame(2,2,b'16' if d else b'00000010')(b,d))
    add('G-F10-kind11','F10',frame(1,2,b'11'))
    route = next(p for p in f.definitions() if p.name == 'TH-0-inf')
    add('G-F10-route6','F10',lambda b,d: frame(2,2,b'6' if d else b'00000006')(b,d),route)
    add('G-F14-GA-eof','F14',lambda b,d: b.split(b'GA ',1)[0]+b'GA 1')
    return tuple(result)


def _with_raw_body(probe, seq):
    def raw(b, decimal):
        lines = b.splitlines(); words = lines[seq + 1].split(b' ')
        words[5] = b'0' if decimal else b'00000000'
        lines[seq + 1] = b' '.join(words)
        return b'\n'.join(lines) + b'\n'
    return Negative(probe.name, probe.error, raw(probe.c, False), raw(probe.duckling, True), probe.controls, probe.boundary)


def expected_prefix(probe, control):
    mode = probe.boundary[0]
    if mode == 'header':
        return b''
                                                                         
    if mode == 'case':
        return probe.controls[0].splitlines(keepends=True)[0]
    output = []
    for line in control.splitlines(keepends=True):
        words = line.split()
                                                                         
                                                                            
        if words[0] == b'END' or words[0] == b'ENDCASE' and mode != 'trailing':
            break
        if mode == 'operation' and words[0] == b'E' and int(words[2]) >= probe.boundary[1]:
            break
        output.append(line)
    return b''.join(output)


def check(probe, code, stdout, stderr, control):
    if code != 2 or stderr != probe.stderr:
        raise ValueError(probe.name + ': expected code2 and exact one-line stderr')
    if stdout != expected_prefix(probe, control):
        raise ValueError(probe.name + ': invalid complete-output boundary')


def positives():
    data = tuple(f.public_bytes((f.world(), f.body(), f.op(62, 0, 0, 1)), d) for d in (False, True))
    return tuple((name, *(fn(b) for b in data)) for name, fn in (
        ('LF', lambda b: b), ('CRLF', lambda b: b.replace(b'\n', b'\r\n')),
        ('EOF', lambda b: b.rstrip(b'\n'))))
