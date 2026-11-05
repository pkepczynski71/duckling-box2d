pass                                                                         

                                                                         
                                                                            
   
import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
                                                                                
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
MANIFEST = json.loads((HERE / 'polaczenia-przypadki.json').read_text(encoding='utf-8'))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


legacy = load('polaczenia_inputs12', 'przypadki-zywy.py')
bits = legacy.bits
value = lambda u: struct.unpack('<f', struct.pack('<I', u))[0]
MUTATOR_ARITY = {0: 2, 1: 2, 2: 1, 3: 2, 4: 1, 5: 3, 6: 0,
                 7: 2, 16: 1, 17: 2, 18: 1, 19: 1, 20: 1,
                 21: 1, 22: 1, 23: 1, 24: 1}
NEW_ARITY = {200: 2, 201: 6, 202: 3, 204: 3, 205: 3, 206: 5,
             207: 3, 208: 1, 209: 4, 210: 3, 211: 3, 212: 3}
F_ARITY = (5, 17, 26, 20, 16)


def op(code, *words):
    words = tuple(words)
    if any(type(w) is not int or not 0 <= w <= 0xffffffff for w in words):
        raise ValueError('operation words must be u32 bits')
    if code < 200:
        if len(words) > 64:
            raise ValueError('inherited operation has more than 64 words')
        words += (0,) * (64 - len(words))
    elif code == 203:
        if len(words) < 4 or words[3] not in MUTATOR_ARITY or len(words) != 4 + MUTATOR_ARITY[words[3]]:
            raise ValueError('203 mutator arity/kind')
    elif code not in NEW_ARITY or len(words) != NEW_ARITY[code]:
        raise ValueError('new operation arity/opcode')
    return {'opcode': code, 'a': words}


def old(row):
    return op(row[0], *row[1:])


def default(dest=0): return op(200, 0, dest)
def field(index, word, dest=0): return op(202, dest, index, word)
def create(a=0, b=1, target=0, *, mode=1, owner=0, description=0):
    return op(201, mode, owner, a, b, target, description)
def mutate(kind, *words, mode=1, owner=0, target=0): return op(203, mode, owner, target, kind, *words)
def read(target=0, mode=1, owner=0): return op(204, mode, owner, target)
def destroy(target=0, mode=1, owner=0): return op(205, mode, owner, target)
def body_list(body=1, capacity=0, *, mode=1, owner=0, copy=0): return op(206, mode, owner, body, capacity, copy)
def view(target=0, dest=0, owner=0): return op(207, owner, target, dest)
def step(n=1, dt=1/60, *, raw=False, owner=0): return old(legacy.g.step(owner=owner, dt=dt, n=n, raw=raw))
def body(slot=0, **kwargs): return old(legacy.body(slot, **kwargs))
def shape(slot=0, parent=0, owner=0, **kwargs): return old(legacy.shape(slot, parent=parent, owner=owner, **kwargs))
def world(**kwargs): return old(legacy.g.world(**kwargs))


@dataclass(frozen=True)
class Case:
    id: int
    key: str
    profile: str
    family: str
    ops: tuple
    fixtures: tuple = ()
    guard_kind: int = 0
    seed_after: int = 0
    ga: tuple = (0,) * 64


def pair(*, kind_a=0, kind_b=2, awake_a=1, awake_b=1, enabled_a=1, enabled_b=1,
         shapes=False, warm=1, position_b=(2, 0)):
    rows = [world(warm=warm), body(0, kind=kind_a, awake=awake_a, enabled=enabled_a),
            body(1, kind=kind_b, p=position_b, awake=awake_b, enabled=enabled_b)]
    if shapes:
        rows += [shape(0, parent=0, geometry=legacy.circle(r=.5), events=1, hit=1),
                 shape(1, parent=1, geometry=legacy.circle(r=.5), events=1, hit=1)]
    return rows + [default()]


def short_public(ident):
    pass                                                                    
    if ident <= 8:
        rows = pair()
        if ident == 2: rows += [field(4, bits(.001))]
        elif ident == 3: rows += [field(9, 0), field(10, 0)]
        elif ident == 4: rows += [field(9, bits(.25)), field(10, bits(.125))]
        elif ident == 5: rows += [field(4, bits(value(bits(.005) - 1)))]
        elif ident == 6: rows += [field(4, bits(value(bits(.005) + 1)))]
        rows += [create()]
        if ident != 4: rows += [read(), body_list(mode=0, capacity=(ident-1) % 3)]
        if ident == 4:                                                            
            rows += [field(10, bits(.5)), create(), read()]
        if ident >= 7:
            rows += [step(), read(), step(dt=0, raw=True), read(), step(dt=-1/60, raw=True), read()]
        if ident in (2, 3, 5, 6): rows += [mutate(17, bits(2), bits(1), mode=0), read()]
    elif ident <= 16:
        rows = pair(kind_a=2, shapes=True)
        rows += [body(2, p=(4, 0)), body(3, p=(6, 0))]
        rows += [create(0, 1, 0), create(1, 2, 1), create(1, 3, 2), create(0, 1, 3),
                 body_list(mode=0, capacity=128), body_list(copy=0), body_list(copy=1)]
        victim = (2, 1, 0, 3)[(ident-9) % 4]
        rows += [destroy(victim), body_list(mode=0, capacity=(0, 1, 128)[ident % 3]),
                 create(0, 1, 4), op(212, 1, 0, victim), read(4), op(208, 0)]
        if ident in (13, 16): rows += [step(), read(4), op(208, 1)]
    elif ident <= 24:
        variant = ident - 17
        args = ({'kind_a': 0, 'kind_b': 0}, {'kind_a': 0}, {'kind_a': 2, 'kind_b': 0},
                {'kind_a': 1}, {'enabled_b': 0}, {'kind_a': 2, 'awake_a': 0},
                {'kind_a': 2, 'awake_a': 0, 'awake_b': 0},
                {'kind_a': 2, 'awake_a': 0, 'awake_b': 0})[variant]
        rows = pair(**args)
        if variant >= 6:
                                                                            
            target = 0 if variant == 6 else 1
            rows += [body(2, p=(4, 0), awake=0), create(target, 2, 1)]
        rows += [create(1, 0) if variant in (2, 7) else create(), read(), body_list(0), body_list(1)]
    elif ident <= 32:
        rows = pair(kind_a=2, shapes=True, position_b=(.75, 0))
        extra = (ident - 25) % 3
        if extra:
            rows += [shape(2, parent=0 if extra == 1 else 1, geometry=legacy.circle((0, .2), .25), events=1)]
        rows += [step(), field(14, int(ident % 2 == 0)), create(), read(),
                 mutate(4, 1), mutate(4, 1), mutate(4, 0), mutate(4, 0),
                 body_list(), destroy(), op(212, 1, 0, 0)]
    elif ident <= 40:
        rows = pair(kind_a=2, shapes=True) + [create()]
        variant = ident - 33
        if variant < 3:
            rows += [old(legacy.bmut(0, variant, mode=0)), read()]
        elif variant == 3:
            rows += [old(legacy.bmut(1, 0, mode=0)), read(), old(legacy.bmut(1, 1, mode=0)), read()]
        elif variant == 4:
            rows += [old(legacy.bmut(0, 0)), read()]
        elif variant == 5:
            rows += [old(legacy.bmut(1, 0)), read()]
        elif variant == 6:
            rows += [old(legacy.bmut(0, 2)), old(legacy.bmut(1, 1)), read()]
        else:
            rows += [destroy(), old(legacy.bmut(0, 1)), old(legacy.bmut(1, 0)), old(legacy.bmut(1, 0)), old(legacy.bmut(1, 1))]
    else:
        rows = pair(kind_a=2, shapes=True) + [create(), view(dest=0), view(dest=1),
                body_list(copy=2), body_list(copy=3), step(), read()]
        variant = ident - 41
        if variant == 0:
            rows += [op(209, 0, 4, 38, bits(7)), op(208, 0), op(208, 1), read()]
        elif variant == 1:
            rows += [op(209, 2, 0, 0, 17), op(208, 2), op(208, 3), body_list(mode=0, capacity=128)]
        elif variant == 2:
            rows += [destroy(), create(target=1), op(212, 1, 0, 0), read(1), op(208, 0)]
        elif variant == 3:
            rows += [op(3, 0, 1), op(212, 1, 0, 0), op(208, 0), op(208, 2)]
        elif variant == 4:
            rows += [op(1, 0), op(208, 0), op(208, 1), op(208, 2), op(208, 3)]
        elif variant == 5:
            rows += [world(slot=1), op(212, 1, 1, 0), read(owner=1), read()]
        elif variant == 6:
            rows += [old(legacy.g.awake(1, 0)), mutate(19, bits(2)), read(), mutate(6), read()]
        else:
            rows += [op(1, 0), world(), body(2, kind=0), body(3, p=(2, 0)), create(2, 3, 1),
                     op(212, 1, 0, 0), read(1), op(208, 0), op(208, 2)]
    return tuple(rows)


def long_public(entry):
    family = (entry['id'] - 49) // 6
    variant = entry['wariant']
    rows = [world(warm=int(entry['warmStarting'])), body(0, kind=0)]
    nbody, njoint = (14, 12) if family == 4 else (4, 3)
    for i in range(1, nbody):
        rows += [body(i, p=(2, i), fixed=int(family == 0 and variant % 2 == 1 and i == 2)),
                 shape(i-1, parent=i, geometry=legacy.circle(r=.5), density=2 if family == 0 and i == 2 else 1,
                       events=1, hit=1)]
    rows += [default(), field(5, int(1 <= family <= 3)), field(6, bits(2 if family == 1 else 0)),
             field(7, bits(.7)), field(8, int(family == 2)), field(9, bits(.75)), field(10, bits(1.25)),
             field(11, int(family == 3)), field(12, bits(0 if variant % 3 == 0 else 12)),
             field(13, bits((0, 3, -3)[variant % 3]))]
    for i in range(njoint):
        if family == 4: rows += [field(4, bits(i+1))]
        rows += [create(1 if family == 4 else i, i+2 if family == 4 else i+1, i)]
    if family <= 2: rows += [old(legacy.g.linear(3, 1 if variant % 2 else -1, 1))]
    rows += [view(dest=0), view(dest=1), body_list(copy=2), body_list(copy=3)]
    for frame in range(1, 1201):
        if frame == 601:
            if family == 5: rows += [mutate(6, target=2)]
            elif family == 6: rows += [destroy(1)]
            elif family == 7: rows += [op(3, 0, 3)]
        if frame in (1, 600, 900, 1200): rows += [op(208, 0), op(208, 2)]
        rows += [step(entry['subSteps'])]
    rows += [read(), op(208, 1), op(208, 3)]
    return tuple(rows)


def solver_fixture(ident):
    pass                                                                     
    v = (ident-65) % 16
    family = (ident-65) // 16
    warm = int(v >= 8)
    set_a, set_b = (0, 2) if v % 4 == 0 else (2, 2)
    common = [0, 0, 1, 0, *map(bits, (.125 if v & 1 else 0, .25 if v & 2 else 0, -.125 if v & 1 else 0, 0)),
              *map(bits, (7, 11, 13, 17, 60, 2, 0, 1, 0))]
    lengths = (.5, .75, 1, 1.25, 1.5, 0, 1, 2)
    separation = lengths[v % 8]
    spring = int(family >= 2 and v % 4 != 0 or family == 3)
    limit = int(family == 3 or family == 2 and v % 3 == 0)
    motor = int(family == 3)
    distance = [*map(bits, (1, 0 if v % 3 == 0 else 2, .7, .75, 1.25,
                            0 if v % 4 == 0 else 12, (0, 3, -3)[v % 3], 1, 2, 3, 4)),
                0, 0, *map(bits, (0, 0, 0, 0, 0, 0, 0, 1, 0, 0)), spring, limit, motor]
    inv_a = 0 if set_a == 0 or v in (6, 14) else 1
    inv_b = 0 if v in (6, 14) else .5
    sim = tuple(map(bits, (0, 0, 1, 0, 0, 0, 0, 0, inv_a, 0 if v % 2 else inv_a,
                           separation, 0, 1, 0, 0, 0, separation, 0, inv_b, 0 if v % 2 else inv_b)))
    states = tuple(bits(x) if i % 8 != 3 else 0 for i, x in enumerate((.25, -.5, .125, 0, 0, 0, 1, 0,
                                                                              -.25, .5, -.125, 0, 0, 0, 1, 0)))
    if set_a == 0: states = (0, 0, 0, 0, 0, 0, bits(1), 0) + states[8:]
    fixture = (tuple((bits(1/60), bits(60), warm, set_a, set_b)), tuple(common), tuple(distance), sim, states)
    if tuple(map(len, fixture)) != F_ARITY: raise ValueError('F0..4 schema')
    operations = [op(210, 0, 0, 0)]
    if family >= 1: operations += [op(210, 0, 1, 0)]
    if family >= 2: operations += [op(210, 0, 2, 1), op(210, 0, 2, 0)]
    return fixture, tuple(operations)


def common_direct(entry):
    ident = entry['id']; name = entry['commonVariant']
    if ident == 1:
        return (op(211, 17, 0x0000ffff, 0x80000001), op(211, 17, 0x000fffff, 0x7fffffff))
    if ident <= 16:
        rows = pair(kind_a=2) + [body(2, p=(4, 0)), body(3, p=(6, 0)),
                create(0, 1, 0, mode=0), create(1, 2, 1, mode=0), create(1, 3, 2, mode=0)]
        if ident == 3: rows += [destroy(mode=0), op(211, 18, 0, 0)]
        elif ident == 4: rows += [destroy(mode=0), create(0, 1, 3, mode=0), op(212, 0, 0, 0)]
        elif ident in (5, 6, 7): rows += [body_list(mode=0, capacity=(0, 1, 128)[ident-5])]
        elif ident in (8, 9, 10, 12, 13): rows += [destroy((2, 1, 0)[(ident-8) % 3], mode=0), body_list(mode=0, capacity=128)]
        elif ident == 11: rows += [create(0, 1, 3, mode=0), body_list(mode=0, capacity=128)]
        elif ident == 14: rows += [destroy(mode=0), op(212, 0, 0, 0)]
        elif ident == 15: rows += [op(3, 0, 1), op(212, 0, 0, 0)]
        elif ident == 16: rows += [op(1, 0), op(212, 0, 0, 0)]
        else: rows += [op(212, 0, 0, 0), read(mode=0)]
        return tuple(rows)
    if ident <= 32:
        args = {'kind_a': 2, 'kind_b': 2}
        if ident == 17: args['enabled_a'] = 0
        if ident == 18: args['enabled_b'] = 0
        if ident in (19, 20, 25): args['kind_a'] = 0
        if ident in (19, 21, 26): args['kind_b'] = 0
        if ident in (23, 26) or 27 <= ident <= 30: args['awake_a'] = 0
        if ident in (24, 25) or 27 <= ident <= 30: args['awake_b'] = 0
        rows = pair(**args)
        if 27 <= ident <= 30:
            rows += [body(2, p=(4, 0), awake=0)]
            larger = 0 if ident in (27, 29) else 1
            rows += [create(larger, 2, 1, mode=0)]
            if ident >= 29: rows += [body(3, p=(6, 0), awake=0), create(1-larger, 3, 2, mode=0)]
        if ident >= 31:
            rows += [shape(0, parent=0, geometry=legacy.circle(r=2), events=1),
                     shape(1, parent=1, geometry=legacy.circle(r=2), events=1), step(dt=0, raw=True)]
        rows += [create(mode=0), read(mode=0), body_list(mode=0, capacity=128)]
        if ident == 32: rows += [mutate(4, 1, mode=0)]
        return tuple(rows)
    if ident <= 48:
        count = ident-32 if ident <= 44 else 5 if ident <= 47 else 1
        rows = [world(), body(0), default()]
        for i in range(1, count+1): rows += [body(i, p=(i, 0)), create(0, i, i-1, mode=0)]
        if ident in (45, 46, 47): rows += [destroy((0, 2, 4)[ident-45], mode=0)]
        rows += [body_list(0, mode=0, capacity=128)]
        return tuple(rows)
    rows = [world(), default(), body(0, kind=0)]
    count = 4 if ident in (54, 55, 56) else 3
    for i in range(1, count+1): rows += [body(i, p=(i, 0))]
    for i in range(count): rows += [create(i, i+1, i, mode=0)]
    rows += [op(211, 8, 0, 0), old(legacy.g.awake(1, 0))]
    if ident in (50, 51, 53): rows += [mutate(6, mode=0, target=0 if ident == 50 else count-1)]
    elif ident in (57, 58, 60):
        if ident == 58: rows += [create(1, 3, count, mode=0)]
        rows += [destroy(1, mode=0), op(64, 0, 3, 0, 1)]
    elif ident == 59: rows += [destroy(0, mode=0), op(64, 0, 3, 0, 1)]
    elif ident == 61: rows += [op(3, 0, count)]
    elif ident == 62:
        rows += [shape(0, parent=1, geometry=legacy.circle(r=1)), shape(1, parent=2, geometry=legacy.circle(r=1)), step(dt=0, raw=True)]
    elif ident == 64: rows += [destroy(0, mode=0), create(0, 1, count, mode=0)]
    elif ident in (54, 55, 56):
        rows += [mutate(6, mode=0), read(mode=0)]
    rows += [body_list(1, mode=0, capacity=128)]
    return tuple(rows)


def cases(profile='PUBLIC', N=None):
    if profile not in ('PUBLIC', 'DIRECT'): raise ValueError('GUARD inputs require the guard generator')
    entries = MANIFEST['przypadki' if profile == 'PUBLIC' else 'direct']
    N = len(entries) if N is None else N
    if type(N) is not int or not 1 <= N <= len(entries): raise ValueError('legal prefix required')
    result = []
    for entry in entries[:N]:
        fixtures = ()
        if profile == 'PUBLIC': operations = short_public(entry['id']) if entry['id'] <= 48 else long_public(entry)
        elif entry['id'] <= 64: operations = common_direct(entry)
        else: fixtures, operations = solver_fixture(entry['id'])
        if not 1 <= len(operations) <= entry['opMax']: raise ValueError(entry['key'] + ' operation bound')
        positive = sum(o['opcode'] in (31, 32) and value(o['a'][1]) > 0 for o in operations)
        minimum, maximum = entry.get('positiveStepsMin', entry['positiveSteps']), entry.get('positiveStepsMax', entry['positiveSteps'])
        if not minimum <= positive <= maximum: raise ValueError(entry['key'] + ' positive Step count')
        result.append(Case(entry['id'], entry['key'], profile, entry['rodzina'], tuple(operations), fixtures))
    return tuple(result)


def text(items, decimal=False):
    if not items or [c.id for c in items] != list(range(1, len(items)+1)):
        raise ValueError('transport requires prefix ids1..N; isolate explicitly first')
    profile = items[0].profile
    if profile not in ('PUBLIC', 'DIRECT', 'GUARD') or any(c.profile != profile for c in items):
        raise ValueError('one profile per stream')
    word = str if decimal else lambda x: f'{x:08x}'
    yield f'PORT14 A {profile} {len(items)}\n'
    for case in items:
        if profile == 'GUARD':
            yield f'G14 {case.id} {case.guard_kind} {case.seed_after} {len(case.ops)}\n'
            if len(case.ga) != 64: raise ValueError('GA64')
            yield f'GA14 {case.id} ' + ' '.join(map(word, case.ga)) + '\n'
        else: yield f'C {case.id} {len(case.ops)}\n'
        for group, words in enumerate(case.fixtures):
            yield f'F14 {case.id} 0 {group} {len(words)} ' + ' '.join(map(word, words)) + '\n'
        for seq, call in enumerate(case.ops, 1):
            code, words = call['opcode'], call['a']
            prefix = f'O {seq} {code} ' + (f'{len(words)} ' if code >= 200 else '')
            yield prefix + ' '.join(map(word, words)) + '\n'
            for tag, key in (('P13B', 'points'), ('U13B', 'materials')):
                for i, row in enumerate(call.get(key, ())):
                    yield f'{tag} {case.id} {seq} {i} ' + ' '.join(map(word, row)) + '\n'


def execution_manifest(items):
    result = []
    for case in items:
        h = [hashlib.sha256(), hashlib.sha256()]
        sizes = [0, 0]
        for side in range(2):
            from dataclasses import replace
                                                                             
            encoded = iter(text((replace(case, id=1),), decimal=bool(side)))
            next(encoded)                                                           
            for line in encoded:
                parts = line.split(' ')
                if parts[0] in ('C', 'F14', 'G14', 'GA14', 'P13B', 'U13B'): parts[1] = str(case.id)
                line = ' '.join(parts)
                raw = line.encode('ascii')
                if len(raw.rstrip(b'\n')) > 2048: raise ValueError(case.key + ' input line envelope')
                h[side].update(raw); sizes[side] += len(raw)
        steps = [o for o in case.ops if o['opcode'] in (31, 32) and value(o['a'][1]) > 0]
        result.append({'case': case.id, 'key': case.key, 'profile': case.profile, 'family': case.family,
                       'opCount': len(case.ops), 'positiveSteps': len(steps),
                       'subSteps': sorted({o['a'][2] for o in steps}),
                       'warmStarting': next((bool(o['a'][10]) for o in case.ops if o['opcode'] in (54, 56)), None),
                       'inputSHA': {'c': h[0].hexdigest(), 'd': h[1].hexdigest()},
                       'inputBytes': {'c': sizes[0], 'd': sizes[1]},
                       'hashScope': 'canonical C/F/O case block with original id, no profile header; concatenate after PORT14 A profile N' ,
                       'actualMaxima': None, 'observations': None, 'reachability': 'UNVERIFIED: native observer/port not yet measured'})
    return {'schema': 1, 'protocol': 'PORT14A', 'cases': result,
            'frozenManifestSHA': hashlib.sha256((HERE/'polaczenia-przypadki.json').read_bytes()).hexdigest(),
            'generatorSHA': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=('PUBLIC', 'DIRECT'), required=True)
    parser.add_argument('--N', type=int)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    items = cases(args.profile, args.N); args.out.mkdir(parents=True, exist_ok=True)
    for decimal, side in ((False, 'c'), (True, 'd')):
        with (args.out/(args.profile.lower()+'-'+side+'.input')).open('w', encoding='ascii', newline='\n') as stream:
            stream.writelines(text(items, decimal))
    (args.out/'manifest.json').write_text(json.dumps(execution_manifest(items), indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
