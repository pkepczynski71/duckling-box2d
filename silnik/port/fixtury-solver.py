pass                                                                        

                                                                        
                                                                              
   
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


g = load('solver_guard_legacy', 'przypadki-kontakty.py')
op, bits = g.op, g.bits
MANIFEST = json.loads((HERE / 'solver-przypadki.json').read_bytes())
WORLD = (0, 1, 0, bits(-10), bits(400), bits(30), bits(10), bits(3), bits(1), bits(1), 1)


def world(slot=0, game=1, gravity=(0, 0)):
    return op(54, slot, game, *map(bits, gravity), *WORLD[4:])


def step(raw=False, dt=1/60, count=1, owner=0):
    return g.g8.step(owner=owner, dt=dt, n=count, raw=raw)


def pair(owner=0, offset=0, hits=True):
    return [world(owner), g.body(offset, owner=owner, kind=0),
            g.body(offset+1, owner=owner, p=(0, .9), v=(0, -2)),
            g.shape(offset, parent=offset, owner=owner, hit=int(hits)),
            g.shape(offset+1, parent=offset+1, owner=owner, hit=int(hits)),
            step(owner=owner), g.save(offset, offset+1, owner=owner)]


def public(rows):
    return ('PORT10 1\nC 1 ' + str(len(rows)) + '\n', tuple(rows))


def operations(rows, decimal=False):
    fmt = str if decimal else lambda value: f'{value:08x}'
    return ''.join(f'O {j} {row[0]} ' + ' '.join(map(fmt, row[1:])) + '\n'
                   for j, row in enumerate(rows, 1))


def public_bytes(rows, decimal=False):
    head, rows = public(rows)
    return (head + operations(rows, decimal)).encode('ascii')


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
    gap: str | None = None

    def encode(self, decimal=False):
        if len(self.words) != 64 or len(self.rows) > 16:
            raise ValueError('GUARD10 arity/budget: ' + self.name)
        if any(not 0 <= w <= g.U32 for w in self.words):
            raise ValueError('GUARD10 word range: ' + self.name)
        fmt = str if decimal else lambda value: f'{value:08x}'
        head = f'GUARD10 1\nG 1 {self.kind} {self.seed} {len(self.rows)}\nGA 1 '
        return (head + ' '.join(map(fmt, self.words)) + '\n' + operations(self.rows, decimal)).encode('ascii')

    def expected_helper_output(self):
        if self.helper is None or self.rows:raise ValueError('not helper-only')
        words=' '.join(f'{w:08x}' for w in self.words)
        h=(self.status,int(self.status==0),self.value&g.U32,self.value>>32)
        return (f'GUARD10 1\nG 1 {self.kind} 0 0\nGA 1 {words}\nCASE 1 0\nGR10 1 0 {self.helper} '
                +' '.join(f'{w:08x}' for w in h)+'\nENDCASE 1\nEND 1\n').encode('ascii')


def fixture(name, group, kind, words=(), rows=(), **kwargs):
    return Fixture(name, group, kind, tuple(words) + (0,) * (64-len(words)), tuple(rows), **kwargs)


def definitions():
    result = []
    for entry in MANIFEST['guardPrzypadki']:
        name, kind = entry['id'], entry['kind']
        if kind == 1:
            words = list(WORLD)
            words[entry['pole']] = int(entry['H'], 16)
            result.append(fixture(name, name, kind, words, helper=0, status=5))
        elif kind == 2:
                                                                             
                                                                             
            for suffix, dt, count, status in (
                ('n0', 0, 0, 5), ('inv-h', 0x00400000, 4, 5),
                ('nan', 0x7fc00000, 1, 5), ('inf', 0x7f800000, 1, 5),
                ('negative', bits(-1), 1, 5), ('plus-zero', 0, 1, 0),
                ('minus-zero', 0x80000000, 1, 0)):
                result.append(fixture(name+'-'+suffix, name, kind, (dt, count), helper=1, status=status))
        elif kind == 3:
            if name == 'G10-B13-BODY':
                for count in (131064, 131065, 131066, 131067, 131068):
                    result.append(fixture(f'{name}-{count}', name, kind, (0, count, 0, 0, 0),
                                          helper=2, status=0 if count in (131064,131065,131068) else 3, value=count))
            elif name == 'G10-B13-ARITH':
                result.append(fixture(name, name, kind, (2, 0xffffffff, 0x7fffffff, 1, 0), helper=4, status=3))
            elif name == 'G10-B13-REQUESTS':
                                                                             
                result.append(fixture(name, name, kind, (2, 131059, 0, 1, 0), helper=4, status=0, value=131060))
            else:
                for count in (131059, 131060):
                    result.append(fixture(f'{name}-{count}', name, kind, (1, count, 0, 0, 0),
                                          helper=3, status=0 if count == 131059 else 3, value=count))
        elif kind == 6:
            field = 0 if '-F-' in name else 1 if '-R-' in name else 2 if '-ROLL-' in name else 3
            for word in ((0x7fc00000, 0x7f800000, 0xff800000) if name.endswith('FIN') else (bits(-1),)):
                words = [bits(.6), 0, 0, 0]; words[field] = word
                result.append(fixture(f'{name}-{word:08x}', name, kind, words, helper=9, status=5))
        elif kind == 8:
            source = 0
            selector, field, replacement, status = 3, 0, 0, 1
            if name == 'G10-OWNER47': field, replacement, status = 1, 0, 2
            elif name in ('G10-OWNER48', 'G10-LEGACY-OWNER'): selector, source, field, replacement, status = 1, 1, 1, 0, 2
            elif name == 'G10-RANGE': field, replacement = 5, 1
            elif name == 'G10-OCCUPIED': field, replacement = 7, g.U32
            elif name == 'G10-BIRTH-LOW': field, replacement = 3, 0
            elif name == 'G10-BIRTH-HIGH': field, replacement = 4, 1
            elif name == 'G10-CONTACT-ID': field, replacement = 6, 1
            else: raise ValueError('unhandled kind8: '+name)
            rows = pair()
            result.append(fixture(name, name, kind, (selector, 0, source, field, replacement), rows,
                                  seed=len(rows), helper=10+selector, status=status))
        elif kind == 4:
            rows = pair()
            last = g.U64
            if name == 'G10-LEGACY-LIMIT':
                result.append(fixture(name,name,kind,(0,g.U32,g.U32),
                                      [world(),g.body(),g.shape()],seed=2,last_status=3))
                continue
            if name == 'G10-HIT-READ-PURE':
                tail=[g.get(),op(48,0,1),g.event_copy(),g.event_copy(1),op(50,0),op(50,0),step()]
                result.append(fixture(name,name,kind,(0,g.U32,g.U32),[*rows,*tail],seed=len(rows),last_status=0))
                continue
            if name == 'G10-CARRY':
                rows = [world(), g.body()]
                result.append(fixture(name, name, kind, (0, g.U32, 0x80000000),
                                      [*rows, g.shape()], seed=2, last_status=0))
                continue
            if name == 'G10-BATCH':
                                                                              
                rows = [world(), g.body(kind=0), g.body(1, p=(0,.9)), g.body(2,p=(0,-.9)),
                        g.shape(category=1,mask=2),g.shape(1,parent=1,category=2,mask=1),
                        g.shape(2,parent=2,category=2,mask=1)]
                last = g.U64-1
                tail = [step()]
            else: tail = [g.get(), op(48,0,1), g.event_copy(), op(50,0)]
            result.append(fixture(name, name, kind, (0, last & g.U32, last >> 32),
                                  [*rows, *tail], seed=len(rows), last_status=3 if name == 'G10-BATCH' else 0))
        elif kind == 0:
            rows, expected = public_guard(name)
            result.append(fixture(name, name, kind, (), rows, last_status=expected))
        else: raise ValueError('unhandled GUARD kind')
    if len(result) > 128 or {f.group for f in result} != {r['id'] for r in MANIFEST['guardPrzypadki']}:
        raise ValueError('GUARD10 manifest coverage/budget')
    if len({f.name for f in result}) != len(result): raise ValueError('duplicate GUARD fixture')
    return tuple(result)


def public_guard(name):
    rows = pair()
    if name in ('G10-W47','G10-W48','G10-W49'):
                                                                        
        rows = [world(), op(1,0), *pair(owner=1, offset=2)]
        rows += [g.get(owner=0)] if name.endswith('47') else [op(48,0,3)] if name.endswith('48') else [g.event_copy(owner=0)]
        return rows, 1
    if name == 'G10-PUBLIC-STEP': return [*rows, step(), step(raw=True,dt=-1/60), step(dt=-1/60)], 5
    if name == 'G10-COPY-LOOKUP': return [*rows,g.get(mutate=1),g.get()],0
    if name == 'G10-COPY-LIST':
                                                                       
        rows = [world(),g.body(kind=0),g.body(1,p=(0,.9)),g.body(2,p=(0,-.9)),
                g.shape(category=1,mask=2),g.shape(1,parent=1,category=2,mask=1),
                g.shape(2,parent=2,category=2,mask=1),step(),op(48,0,0,1),op(48,0,0,0)]
        return rows,0
    if name in ('G10-COPY-EVENTS','G10-COPY-HITS'):
        return [*rows,g.event_copy(),g.event_copy(1),op(50,0,1),op(50,1),op(50,0)],0
    if name == 'G10-EVENT-NUMBER':
                                                                          
                                                                              
                                                                           
        return [*rows,g.event_copy(),op(18,0,0),op(18,0,1),g.shape(2,parent=0),
                g.shape(3,parent=1),step(dt=0),g.event_copy(1),op(50,0,1)],0
    if name == 'G10-HIT-HISTORY':
        return [*rows,g.event_copy(),op(18,0,1),g.shape(2,parent=1),op(50,0)],0
    if name == 'G10-EVENT-MANIFOLD':
        return [*rows,g.event_copy(),g.transform(0,1,(.2,.9)),step(),op(50,0,1)],0
    if name in ('G10-END-SIDE','G10-READ-PURE'):
        return [*rows,g.transform(0,1,(0,4)),step(),g.event_copy(),step(dt=0),g.event_copy(1),op(50,0),op(50,0)],0
    if name == 'G10-COPY-DEAD-WORLD': return [*rows,g.event_copy(),op(1,0),world(1),op(50,0,1)],0
    if name == 'G10-LEGACY-LIFE':
        return [world(),g.body(),op(3,0,0),g.shape()],1
    if name == 'G10-LEGACY-GEOMETRY':
        return [world(),g.body(),g.shape(geometry=g.circle(r=-1))],4
    if name == 'G10-LEGACY-S12':
        return [world(),g.body(),g.shape(density=g.number(0x7f7fffff),geometry=g.circle(r=2))],4
    if name == 'G10-MAT-ROUTES':
        return [world(),g.body(),g.shape(friction=-1)],5
    raise ValueError('unhandled public GUARD: '+name)


def native_driver(source, profile):
    pass                                                                     
    if profile not in (3, 4, 5):raise ValueError('unknown native solver profile')
    anchor='const CONTACT_PROFILE: i32 = 3i32;'
    if source.count(anchor)!=1:raise ValueError('expected exactly one PUBLIC10 profile constant')
    return source.replace(anchor,'const CONTACT_PROFILE: i32 = '+str(profile)+'i32;',1)


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
    args.directory.mkdir(parents=True,exist_ok=True)
    for item in definitions():
        for decimal,side in ((False,'c'),(True,'duckling')):
            (args.directory/(item.name+'-'+side+'.csv')).write_bytes(item.encode(decimal))
