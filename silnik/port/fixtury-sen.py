pass                                                                    

                                                                           
                                                                        
   
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


old = load('sen_guard_legacy', 'fixtury-solver.py')
g = old.g
op, bits = g.op, g.bits
U32 = 0xffffffff


def world(slot=0, game=1, sleeping=1):
    return op(56, slot, game, 0, 0, bits(400), bits(30), bits(10),
              bits(3), bits(1), bits(1), 1, sleeping)


def body(slot=0, owner=0, game=1, kind=2, awake=1, sleep=1,
         threshold=0.05, position=(0, 0), velocity=(0, 0)):
    return op(57, owner, slot, game, kind, *map(bits, position), bits(1), 0,
              *map(bits, velocity), 0, 0, 0, bits(1), 0, 0, sleep, awake,
              bits(threshold))


def replace(row, index, value):
    result = list(row)
    result[index + 1] = value
    return tuple(result)


def operations(rows, decimal=False):
    return old.operations(rows, decimal)


def public_bytes(rows, decimal=False, profile='PORT11'):
    if profile not in ('PORT11', 'COMPONENT11'):
        raise ValueError('unknown step11 input profile')
    return (f'{profile} 1\nC 1 {len(rows)}\n' + operations(rows, decimal)).encode('ascii')


@dataclass(frozen=True)
class Fixture:
    name: str
    group: str
    kind: int
    words: tuple
    rows: tuple = ()
    seed: int = 0
    helper: int | None = None
    status: int | None = None
    value: int = 0
    last_status: int | None = None
    status_at: tuple = ()

    def encode(self, decimal=False):
        if len(self.words) != 64 or any(type(w) is not int or not 0 <= w <= U32 for w in self.words):
            raise ValueError(self.name + ': GA requires 64 u32 words')
        if self.kind not in range(11) or len(self.rows) > 16 or not 0 <= self.seed <= len(self.rows):
            raise ValueError(self.name + ': GUARD11 domain/budget')
        if self.kind in (1, 2, 3, 5, 6, 9, 10) and (self.rows or self.seed):
            raise ValueError(self.name + ': helper-only cannot contain O')
        if self.kind in (0, 4, 8) and not self.rows:
            raise ValueError(self.name + ': setup required')
        fmt = str if decimal else lambda w: f'{w:08x}'
        return (f'GUARD11 1\nG 1 {self.kind} {self.seed} {len(self.rows)}\nGA 1 '
                + ' '.join(map(fmt, self.words)) + '\n' + operations(self.rows, decimal)).encode('ascii')

    def helper_record(self):
        if self.helper is None or self.status is None:
            raise ValueError(self.name + ': no helper observation specified')
        return (1, len(self.rows) + int(self.kind == 7), self.helper, self.status,
                int(self.status == 0), self.value & U32, self.value >> 32)

    def expected_helper_output(self):
        if self.rows:
            raise ValueError('helper-only output requested for full setup')
        frame = self.encode(False).decode('ascii')
        h = self.helper_record()
        return (frame + 'CASE 1 0\nGR11 ' + ' '.join(map(str, h[:3])) + ' '
                + ' '.join(f'{w:08x}' for w in h[3:]) + '\nENDCASE 1\nEND 1\n').encode('ascii')


def fixture(name, group, kind, words=(), rows=(), **kwargs):
    if len(words) > 64:
        raise ValueError('GA overflow')
    return Fixture(name, group, kind, tuple(words) + (0,) * (64 - len(words)), tuple(rows), **kwargs)


def definitions():
    result = []
                                                                              
    for route in range(6):
        for suffix, word, status in (('inf', 0x7f800000, 5), ('nan', 0x7fc00000, 5),
                                     ('minus-inf', 0xff800000, 5), ('negative', bits(-1), 5),
                                     ('plus-zero', 0, 0), ('minus-zero', 0x80000000, 0)):
            result.append(fixture(f'TH-{route}-{suffix}', 'G11-4/5', 5,
                                  (route, word), helper=20 + route, status=status))
    for count in (0, 1, 128, 129, 131059, 131060):
        result.append(fixture(f'BUPPER-{count}', 'G11-7', 3, (0, count, 0),
                              helper=2, status=0 if count <= 131059 else 3, value=count))
    for selector, count, add, status, value in ((1, 131059, 0, 0, 131059),
                                               (1, 131060, 0, 3, 131060),
                                               (2, 131059, 1, 0, 131060),
                                               (2, 0x7fffffffffffffff, 1, 3, 0)):
        result.append(fixture(f'COUNT-{selector}-{count}-{add}', 'G11-7', 3,
                              (selector, count & U32, count >> 32, add, 0),
                              helper=2 + selector, status=status, value=value))
    for awake, asleep, status, value in ((1, 131058, 0, 131059), (1, 131059, 3, 131060),
                                         (0x7fffffffffffffff, 1, 3, 0)):
        result.append(fixture(f'BUPPER-SUM-{awake}-{asleep}', 'G11-7', 7,
                              (0, awake & U32, awake >> 32, asleep & U32, asleep >> 32),
                              (world(),), seed=1, helper=30, status=status, value=value))
    for suffix, dt, n, status in (('n0', 0, 0, 5), ('inv-h', 0x00400000, 4, 5),
                                  ('nan', 0x7fc00000, 1, 5), ('inf', 0x7f800000, 1, 5),
                                  ('negative', bits(-1), 1, 5), ('plus-zero', 0, 1, 0),
                                  ('minus-zero', 0x80000000, 1, 0)):
        result.append(fixture('STEP-' + suffix, 'G11-11', 2, (dt, n), helper=1, status=status))
    for field in range(2, 10):
        words = list(old.WORLD)
        words[field] = 0xff800000 if field < 4 else 0x7f800000
        result.append(fixture(f'WORLD-FIN-{field}', 'G11-11', 1, words, helper=0, status=5))
    for field in range(4, 10):
        words = list(old.WORLD); words[field] = bits(-1)
        result.append(fixture(f'WORLD-SIGN-{field}', 'G11-11', 1, words, helper=0, status=5))
    for field, replacement, status in ((0, 0, 0), (1, 0, 2), (2, 1, 2), (3, 0, 1),
                                        (4, 1, 1), (6, U32, 1), (7, U32, 1)):
        result.append(fixture(f'BODY-STATUS-{field}', 'G11-2/3', 8,
                              (1, 0, 0, field, replacement), (world(), body()),
                              seed=2, helper=11, status=status))
    result += [fixture('MOVE-COPY', 'G11-9', 9, helper=40, status=0, value=2 | (3 << 32)),
               fixture('STATE-COPY', 'G11-9', 10, helper=41, status=0, value=1 | (3 << 32))]
    rows = (world(), body(awake=0), op(58, 0, 0, 1, 1))
    result.append(fixture('MAX-WAKE', 'G11-8', 4, (0, U32, U32), rows,
                          seed=2, last_status=0))
                                                                              
    batch = (world(), body(kind=0), body(1, position=(0, .9)), body(2, position=(0, -.9)),
             g.shape(category=1, mask=2), g.shape(1, parent=1, category=2, mask=1),
             g.shape(2, parent=2, category=2, mask=1), old.step())
    result.append(fixture('MAX-BATCH', 'G11-8', 4, (0, U32 - 1, U32), batch,
                          seed=7, last_status=3))
    for opcode in range(57, 63):
        tail = (replace(body(1), 0, 0) if opcode == 57 else
                op(61, 0, 1, 0) if opcode == 61 else
                op(opcode, 0, 0, 1, bits(.05) if opcode == 60 else 1 if opcode in (58, 59) else 0))
                                                                            
                                                                              
        rows = (world(), body(), op(1, 0), world(1), tail)
        result.append(fixture(f'WORLD-STALE-{opcode}', 'G11-1', 0, rows=rows, last_status=1))
    for suffix, word in (('nan', 0x7fc00000), ('inf', 0x7f800000), ('negative', bits(-1))):
        rows = (world(), body(), op(60, 0, 0, 1, word), op(62, 0, 0, 1))
        result.append(fixture('PARAM-CONTINUES-' + suffix, 'G11-4/6', 0, rows=rows, last_status=0,
                              status_at=((3, 5), (4, 0))))
    for opcode in (58, 59, 60, 62):
        tail = op(opcode, 1, 0, 1, bits(.125) if opcode == 60 else 0)
        rows = (world(), body(), world(1), body(1, owner=1), tail)
        result.append(fixture(f'FOREIGN-CALL-{opcode}', 'G11-2', 0, rows=rows, last_status=2,
                              status_at=((5, 2),)))
    rows = (world(), body(), g.shape(geometry=g.circle(r=-1)), op(62, 0, 0, 1))
    result.append(fixture('GEOMETRY-CONTINUES', 'G11-11', 0, rows=rows, last_status=0, status_at=((3, 4), (4, 0))))
    result.append(fixture('M12-WAKE-GROWTH', 'M12', 0, rows=m12_operations(), last_status=0))
    if len(result) > 128 or len({item.name for item in result}) != len(result):
        raise ValueError('GUARD11 fixture budget/duplicates')
    for item in result:
        item.encode(False); item.encode(True)
    return tuple(result)


def m12_operations():
    pass                                                              

                                                                          
                                                                             
                                                                         
                                                                      
       
    return (world(), body(0, awake=0), body(1, awake=0, position=(1.05, 0)),
            body(2, awake=0, position=(-1.05, 0)), body(3, position=(0, 1)),
            g.shape(0, parent=0, category=1, mask=14),
            g.shape(1, parent=1, category=2, mask=1),
            g.shape(2, parent=2, category=4, mask=1),
            g.shape(3, parent=3, category=8, mask=1), old.step(dt=.125, count=1))


def inherited_helper_driver(source):
    pass                                                          

                                                                          
                                                                             
                                                                              
       
    prepared = old.native_driver(source, 4)
    for literal, expected in (('GUARD10', 2), ('GR10', 1)):
                                                                            
        if prepared.count(literal) != expected:
            raise ValueError('inherited helper fixture anchor: ' + literal)
    return prepared.replace('GUARD10', 'GUARD11').replace('GR10', 'GR11')
