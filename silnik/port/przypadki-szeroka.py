pass                                                                              
import argparse
from dataclasses import dataclass
from pathlib import Path
import importlib.util
import sys

from przypadki import bits, number

                                                                
_spec = importlib.util.spec_from_file_location('tree_inputs', Path(__file__).with_name('przypadki-drzewo.py'))
_tree = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _tree
_spec.loader.exec_module(_tree)
valid_box, contains, overlaps = _tree.valid_box, _tree.contains, _tree.overlaps
ALL = (1 << 64)-1
NULL = (1 << 32)-1
COUNT = 75


def halves(n):
    return n & NULL, n >> 32


def join(lo, hi):
    return lo | hi << 32


def signed(n):
    return n if n < 2**31 else n-2**32


def key_hash(key):
    pass                                                                  
    h = key
    h = ((h ^ (h >> 33))*0xff51afd7ed558ccd) & ALL
    h = ((h ^ (h >> 33))*0xc4ceb9fe1a85ec53) & ALL
    return (h ^ (h >> 33)) & NULL


def shape(body, category=ALL, mask=ALL, group=0, sensor=0, generation=1):
    return (body, *halves(category), *halves(mask), group & NULL, sensor, generation)


def op(kind, *args):
    if len(args) > 15:
        raise ValueError('Too many operation words')
    return (kind, *args, *(0 for _ in range(15-len(args))))


def create(n, box=(0, 0, 2, 2), force=0):
    return op(0, n, *map(bits, box), force)


def move(n, box, enlarge=False):
    return op(3 if enlarge else 2, n, *map(bits, box))


def query(tree=2, box=(-4096, -4096, 4096, 4096), mask=ALL):
    return op(10, tree, *map(bits, box), *halves(mask))


def set_op(kind, key=0):
    return op(kind, *halves(key)) if kind != 3 else op(3)


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    mode: int
    dump: int
    ops: tuple
    bodies: tuple = ()
    shapes: tuple = ()
    joints: tuple = ()
    custom: int = 0
    rules: tuple = ()
    world: int = 0
    capacity: int = 16

    @property
    def header(self):
        if self.mode:
            return (1, self.capacity, len(self.ops), self.dump)
        return (0, len(self.bodies), len(self.shapes), len(self.joints), self.custom,
                len(self.rules), len(self.ops), self.dump, self.world)

    @property
    def words(self):
        tables = ((*self.bodies,), *self.shapes, *self.joints, *self.rules) if not self.mode else ()
        return (*self.header, *(v for row in tables for v in row), *(v for row in self.ops for v in row))


def decision(case, a, b):
    if case.custom == 2:
        return 0
    if case.custom == 3:
        return next((d for x, y, d in case.rules if (x, y) == (a, b)), 1)
    return 1


def allowed(case, a, b):
    pass                                                                      
    sa, sb = case.shapes[a], case.shapes[b]
    ba, bb = sa[0], sb[0]
    if ba == bb or sa[6] or sb[6] or 2 not in (case.bodies[ba], case.bodies[bb]):
        return False
    ga, gb = signed(sa[5]), signed(sb[5])
    if ga and ga == gb:
        if ga < 0:
            return False
    elif not (join(*sa[1:3]) & join(*sb[3:5]) and join(*sb[1:3]) & join(*sa[3:5])):
        return False
    return not any({x, y} == {ba, bb} and not d for x, y, d in case.joints)


def candidates(case, live, moved, keys):
    pass                                                                         
    result = {}
    for a in live:
        for b in live:
            if b <= a or not overlaps(tuple(map(number, live[a])), tuple(map(number, live[b]))):
                continue
            ta, tb = case.bodies[case.shapes[a][0]], case.bodies[case.shapes[b][0]]
            if 2 not in (ta, tb) or not ({a, b} & moved):
                continue
            if ta == tb == 2:
                owner = min(({a, b} & moved), key=keys.__getitem__)
            else:
                dyn = a if ta == 2 else b
                owner = dyn if dyn in moved else (b if dyn == a else a)
            target = b if owner == a else a
            if join(*case.shapes[target][1:3]):
                result[a, b] = owner
    return result


def validate(case):
    if not 1 <= len(case.ops) <= 1024 or case.dump not in (0, 1) or case.mode not in (0, 1):
        raise ValueError('Bad mode/opCount/dumpEvery')
    if any(type(v) is not int or not 0 <= v <= NULL for v in case.words):
        raise ValueError('Bad u32')
    if case.mode:
        if case.capacity not in (16, 32, 64):
            raise ValueError('Unsafe capacity (B01)')
        for w in case.ops:
            if len(w) != 16 or w[0] not in range(4) or any(w[3:] if w[0] != 3 else w[1:]):
                raise ValueError('Bad set operation/unused words')
            if w[0] != 3 and (not join(*w[1:3]) or not key_hash(join(*w[1:3]))):
                raise ValueError('Zero key/hash (B02)')
        return
    if not (len(case.bodies) <= 128 and len(case.shapes) <= 128 and len(case.joints) <= 128
            and len(case.rules) <= 256 and case.custom in range(4) and case.world in range(4)):
        raise ValueError('Header limit')
    if case.custom != 3 and case.rules:
        raise ValueError('Rules without table mode')
    if any(t not in range(3) for t in case.bodies):
        raise ValueError('Body type')
    for s in case.shapes:
        if len(s) != 8 or s[0] >= len(case.bodies) or s[6] not in (0, 1) or not 1 <= s[7] <= 65535:
            raise ValueError('Shape descriptor')
    for a, b, d in case.joints:
        if a == b or max(a, b) >= len(case.bodies) or d not in (0, 1) or 2 not in (case.bodies[a], case.bodies[b]):
            raise ValueError('Invalid distance joint')
    if len({(a, b) for a, b, _ in case.rules}) != len(case.rules):
        raise ValueError('Duplicate ordered rule')
    for a, b, d in case.rules:
        if max(a, b) >= len(case.shapes) or d not in (0, 1):
            raise ValueError('Invalid custom rule')
    live, moved, pairs = {}, set(), set()
                                                                                
                                                                               
                                                       
    keys = {n: n*4+case.bodies[s[0]] for n, s in enumerate(case.shapes)}
    used = {0: 7, 1: 2, 2: 6, 3: 6, 4: 2, 5: 1, 6: 1, 7: 3, 8: 2, 9: 3, 10: 8}
    for k, w in enumerate(case.ops, 1):
        if len(w) != 16 or w[0] not in used or any(w[used[w[0]]:]):
            raise ValueError(f'Bad kind/unused operation {k}')
        t, n = w[:2]
        if t in (0, 1, 2, 3, 4, 7, 8, 9):
            if n >= len(case.shapes) or (t == 0) == (n in live):
                raise ValueError(f'Dead/active proxy operation {k}')
        if t in (7, 9) and w[2] not in live:
            raise ValueError('Second proxy not live')
        if t in (0, 2, 3, 10):
            box = valid_box(w[2:6])
            if t == 0 and (w[6] not in (0, 1) or not all(-100000 < v < 100000 for v in box)):
                raise ValueError('Create bounds/force')
            if t == 3 and (case.bodies[case.shapes[n][0]] == 0 or contains(tuple(map(number, live[n])), box)):
                raise ValueError('Invalid Enlarge')
            if t == 10 and n not in range(3):
                raise ValueError('Query tree')
        if t == 0:
            live[n] = w[2:6]
            if case.bodies[case.shapes[n][0]] or w[6]:
                moved.add(n)
        elif t == 1:
            if any(n in p for p in pairs):
                raise ValueError('Destroy with incident contact')
            del live[n]
            moved.discard(n)
        elif t in (2, 3):
            live[n] = w[2:6]
            moved.add(n)
        elif t == 4:
            moved.add(n)
        elif t == 5:
            for a, b in candidates(case, live, moved, keys):
                x, y = sorted((a, b), key=keys.__getitem__)
                if allowed(case, a, b) and decision(case, x, y):
                    pairs.add((a, b))
            moved.clear()
        elif t == 9:
            pair = tuple(sorted((n, w[2])))
            if pair not in pairs:
                raise ValueError('Release absent pair')
            pairs.remove(pair)


def cases():
    rows = []

    def add(category, bodies=(), shapes=None, ops=(), joints=(), custom=0, rules=(), world=0, dump=1):
        c = Case(len(rows)+1, category, 0, dump, tuple(ops), tuple(bodies),
                 tuple(shape(i) for i in range(len(bodies))) if shapes is None else tuple(shapes),
                 tuple(joints), custom, tuple(rules), world)
        validate(c)
        rows.append(c)

    add('puste', ops=[op(5), op(6), query(0), query(1), query(2), op(5)])
    for t in range(3):
        add('pojedynczy', [t], ops=[create(0), op(8, 0), op(7, 0, 0), op(5), op(5), op(6), query(t)])
                                                                                 
    combos = [(a, b) for a in range(3) for b in range(3)]
    for i in range(8):
        chosen = combos[i:i+1] if i < 7 else combos[7:]
        bodies, ops = [], []
        for a, b in chosen:
            n = len(bodies)
            bodies += [a, b]
            for reverse in (False, True):
                order = (n+1, n) if reverse else (n, n+1)
                ops += [create(order[0], force=i % 2), create(order[1], force=i % 2),
                        op(7, n, n+1), op(4, n), op(5)]
                if 2 in (a, b):
                    ops += [op(9, n, n+1)]
                ops += [op(1, n), op(1, n+1), op(5)]
        add('typy-9-kombinacji', bodies, ops=ops)
    for count, removed in ((5, 0), (5, 2), (5, 4), (17, 8), (33, 16), (65, 32), (12, 1), (12, 10)):
        bodies = [i % 3 for i in range(count)]
        ops = [create(i, (i*3, 0, i*3+1, 1), 1) for i in range(count)]
        target = next(i for i, t in enumerate(bodies) if t == 2)
        ops += [op(4, target)]*5
        ops += [move(target, (200, 0, 201, 1)), move(target, (199, -1, 202, 2), True),
                op(1, removed), create(removed, (-20, 0, -19, 1), 1), op(8, removed), op(5), op(5)]
        add('bufor-remove-swap-wzrost', bodies, ops=ops, dump=int(count < 17))
    for i in range(6):
        bodies = ([2, 2, 2, 0, 1, 2] if i < 4 else [0, 1, 2, 2, 2, 2])
        order = list(range(6)) if i % 2 == 0 else list(reversed(range(6)))
        ops = [create(n, (0, 0, 2, 2) if n < 5 else (10, 10, 11, 11), 1) for n in order]
        ops += [op(5)]
        if i == 0:
                                                                             
                                                                
            ops += [op(9, 0, 3), op(4, 3), op(5), op(9, 0, 4), op(4, 4), op(5)]
                                                                                                 
        ops += [move(5, (0, 0, 2, 2)), op(4, i % 5), op(5), op(5)]
        add('wlasciciel-deduplikacja', bodies, ops=ops)
    configs = [
        [shape(0, 0, 0, 7), shape(1, ALL, 0, 7)],
        [shape(0, ALL, 0, 7), shape(1, 0, 0, 7)],
        [shape(0, 1 << 31, 1 << 32), shape(1, 1 << 32, 1 << 31)],
        [shape(0, 1 << 63, ALL), shape(1, ALL, 0)],
        [shape(0, 1, 0, 70000), shape(1, 2, 0, 70000)],
        [shape(0, ALL, ALL, -70000), shape(1, ALL, ALL, -70000)],
        [shape(0, ALL, ALL, -1), shape(1, ALL, ALL, 1)],
        [shape(0, 1 << 32, 1 << 63), shape(1, 1 << 63, 1 << 32)],
    ]
    for i, ss in enumerate(configs):
        ops = [create(1), create(0), op(5), op(4, 0), op(5), op(4, 1), op(5),
               query(mask=0), query(mask=1 << 31), query(mask=1 << 32), query(mask=1 << 63)]
        add('filtry-grupy-kategorie', [2, 2], ss, ops)
    for i in range(6):
        ss = [shape(0), shape(0 if i < 2 else 1, sensor=int(i in (2, 4))),
              shape(2 if i == 4 else 1, sensor=int(i in (3, 4))), shape(2)]
        add('cialo-sensory-geometria', [2, 2, 0], ss,
            [*(create(n, force=1) for n in range(4)), op(5), op(7, 0, 1), query(), op(5)])
    joint_sets = [((0, 1, 1),), ((0, 1, 0),), ((0, 2, 0),),
                  ((0, 1, 1), (0, 1, 0), (0, 1, 1)),
                  ((0, 2, 1), (0, 3, 1), (1, 2, 1), (0, 1, 0)),
                  ((1, 2, 1), (1, 3, 1), (0, 1, 0))]
    for joints in joint_sets:
        add('polaczenia', [2]*4, ops=[*(create(n) for n in reversed(range(4))), op(5), op(5)], joints=joints)
    for i in range(6):
        ss = [shape(0, generation=65535), shape(1, generation=1), shape(1, sensor=1),
              shape(2, mask=0), shape(3), shape(4)]
        custom = (0, 1, 2, 3, 3, 1)[i]
        rules = ((1, 0, 0), (0, 1, 1), (5, 4, 0), (4, 5, 1)) if custom == 3 else ()
        add('wlasny-filtr-identyfikatory', [2]*5, ss,
            [*(create(n) for n in reversed(range(6))), op(5), op(4, 0), op(5)],
            joints=((0, 3, 0),), custom=custom, rules=rules, world=i % 4)
    for i in range(4):
        ops = [create(1), create(0), op(5), op(5), op(4, i % 2), op(5),
               move(1, (10, 10, 11, 11)), op(5), op(9, 0, 1), op(5),
               move(1, (0, 0, 2, 2)), op(5), op(9, 1, 0), op(1, 0), op(1, 1), op(5)]
        add('zycie-pary', [2, 2], ops=ops, custom=1)
    for i in range(2):
        count = 1 if i == 0 else 24
        ops = [create(n, (n*4, 0, n*4+1, 1)) for n in range(count)]
        for j in range(240):
            n = j % count
            ops += [move(n, (n*4, (j % 2)*2, n*4+1, (j % 2)*2+1)), query()]
        ops += [op(5), op(5)]
        add('464-duzo-ruchow', [2]*count, ops=ops, dump=0)
    for count in (1, 4):
        ops = [create(n, (n*4, 0, n*4+1, 1)) for n in range(count)]
        if count > 1:
                                                                              
            ops += [move(1, (3, -1, 6, 2), True)]
        ops += [op(5), move(0, (-1, -1, 2, 2), True), op(1, 0), query(), op(5), op(6),
                create(0, (0, 0, 1, 1)), op(5), op(6), query()]
        add('1105-powieksz-usun', [2]*count, ops=ops)
    add('przebudowa-trzech-drzew', [i % 3 for i in range(18)],
        ops=[*(create(n, (n % 3*8, n//3*4, n % 3*8+1, n//3*4+1), 1) for n in range(18)),
             move(0, (-1, -1, 2, 2)), move(1, (7, -1, 10, 2), True),
             move(2, (15, -1, 18, 2), True), op(6), query(0), query(1), query(2), op(5), op(6)])
    add('styk-bok-naroznik', [2]*4, ops=[create(0, (-0.0, -0.0, 1, 1)), create(1, (1, 0, 2, 1)),
        create(2, (1, 1, 2, 2)), create(3, (number(bits(1)+1), 0, 3, 1)),
        op(7, 0, 1), op(7, 0, 2), op(7, 0, 3), op(5), query()])
    add('2080-par-heap', [2]*65, ops=[*(create(n) for n in reversed(range(65))), op(5), op(5)], dump=0)
    add('kolejnosc-list-kilku-ruchow', [0, 1, 2, 2, 0, 1, 2],
        ops=[*(create(n, force=1) for n in (6, 3, 0, 5, 1, 4, 2)), op(5),
             *(op(4, n) for n in (5, 0, 3, 6, 2)), op(5), op(6), query()])
    assert len(rows) == 64

    def add_set(category, operations, capacity=16, dump=1):
        c = Case(len(rows)+1, category, 1, dump, tuple(operations), capacity=capacity)
        validate(c)
        rows.append(c)

    add_set('zbior-podstawy', [set_op(t, k) for t, k in ((2, 1), (1, 1), (0, 1), (0, 1), (2, 1), (1, 1), (1, 1))]
            + [set_op(3), set_op(0, 2), set_op(3), set_op(2, 2)])
    for capacity in (16, 32):
        operations = []
        for i in range(1, 2*capacity+2):
            operations.append(set_op(0, i))
            if i in (capacity//2, capacity, 2*capacity):
                operations.append(set_op(0, i))                                      
        operations += [set_op(3), set_op(0, 99), set_op(2, 99)]
        add_set('zbior-progi-wzrostu', operations, capacity, dump=1)
    cluster = [k for k in range(1, 20000) if key_hash(k) & 15 == 15][:7]
    for removed in (0, 3, 6):
        add_set('zbior-klaster-koniec-tablicy', [*(set_op(0, k) for k in cluster), set_op(1, cluster[removed]),
            *(set_op(2, k) for k in cluster), set_op(0, cluster[removed]),
            *(set_op(1, k) for k in reversed(cluster)), set_op(3)])
    high = [1 << 63, ALL, 0xffffffff00000001, 0x8000000180000001, 0x1234567887654321,
            (2 << 32) | 9, (9 << 32) | 2, (1 << 32) | 127]
    add_set('zbior-u64-logiczne-przesuniecie', [*(set_op(0, k) for k in high),
        *(set_op(2, k) for k in high), *(set_op(1, k) for k in high), set_op(3)], 32)
    pair_keys = [(min(a, b) << 32) | max(a, b) for a, b in ((1, 2), (2, 1), (0, 127), (127, 0), (17, 65), (65, 17))]
    add_set('zbior-klucz-pary-obie-kolejnosci', [*(set_op(0, k) for k in pair_keys),
        *(set_op(2, k) for k in pair_keys), *(set_op(1, k) for k in pair_keys), set_op(3), set_op(0, ALL)], 64)
    assert len(rows) == 72
                                                                             
                                                             
    for groups in ((32768, 32768), (-32769, -32769), (1, 65537)):
        add('R5-W1-grupa-i32', [2, 2],
            [shape(0, 1, 0, groups[0]), shape(1, 2, 0, groups[1])],
            [create(0), create(1), op(5)])
    assert len(rows) == COUNT
                                                                                            
    assert all(key_hash((a << 32) | b) for a in range(128) for b in range(a+1, 128))
    assert all(key_hash(k) for k in range(1, 1025))
    return tuple(rows)


def load(path):
    result = []
    for line in Path(path).read_text(encoding='ascii').splitlines():
        tokens = line.split(' ')
        if not tokens or tokens[0] != str(len(result)+1) or any(len(t) != 8 or any(c not in '0123456789abcdef' for c in t) for t in tokens[1:]):
            raise ValueError('Noncanonical input')
        w = [int(t, 16) for t in tokens[1:]]
        if not w:
            raise ValueError('Missing mode')
        if w[0] == 0:
            if len(w) < 9:
                raise ValueError('Short header')
            _, bc, sc, jc, custom, rc, oc, dump, world = w[:9]
            if bc > 128 or sc > 128 or jc > 128 or rc > 256 or not 1 <= oc <= 1024:
                raise ValueError('Header limits before tables')
            p = 9
            bodies = tuple(w[p:p+bc]); p += bc
            def table(width, count):
                nonlocal p
                out = tuple(tuple(w[p+i*width:p+(i+1)*width]) for i in range(count)); p += width*count
                return out
            shapes, joints, rules, ops = table(8, sc), table(3, jc), table(3, rc), table(16, oc)
            c = Case(len(result)+1, '', 0, dump, ops, bodies, shapes, joints, custom, rules, world)
        elif w[0] == 1 and len(w) >= 4:
            _, cap, oc, dump = w[:4]
            if not 1 <= oc <= 1024:
                raise ValueError('Set operation count')
            p = 4+16*oc
            c = Case(len(result)+1, '', 1, dump, tuple(tuple(w[i:i+16]) for i in range(4, p, 16)), capacity=cap)
        else:
            raise ValueError('Bad input mode')
        if p != len(w):
            raise ValueError('Input length')
        validate(c)
        result.append(c)
    if len(result) != COUNT:
        raise ValueError(f'Expected {COUNT} cases')
    return tuple(result)


def output_bound(rows):
    pass                                                                           
    total = 2*32
    for c in rows:
                                                                                             
        total += 32+11*len(c.header)+sum(32+11*(len(s)+1) for s in c.shapes)
        total += (32+22)*len(c.bodies)+(32+44)*(len(c.joints)+len(c.rules))
        live, moving, set_keys = set(), set(), set()
        cap = c.capacity if c.mode else 16
        for k, w in enumerate(c.ops, 1):
            total += 32+11*17                               
            if c.mode:
                key = join(*w[1:3])
                if w[0] == 0:
                    if key not in set_keys and 2*len(set_keys) >= cap:
                        cap *= 2
                    set_keys.add(key)
                elif w[0] == 1:
                    set_keys.discard(key)
                elif w[0] == 3:
                    set_keys.clear()
                if c.dump or k == len(c.ops):
                    total += 32+11*(3+3*cap)
                continue
            t, n = w[:2]
            if t == 0:
                live.add(n)
                if c.bodies[c.shapes[n][0]] or w[6]:
                    moving.add(n)
            elif t == 1:
                live.remove(n); moving.discard(n)
            elif t in (2, 3, 4):
                moving.add(n)
            elif t == 5:
                                                                                                   
                total += len(moving)*3*(32+11*(8+2*len(live)))
                total += len(moving)*len(live)*(32+11*8 + 32+11*4)
                total += 32+11*6
                moving.clear()
            elif t == 10:
                total += 32+11*(8+2*len(live))
            if c.dump or k == len(c.ops):
                                                                                        
                pair_cap = 32
                max_pairs = len(c.shapes)*(len(c.shapes)-1)//2
                while pair_cap < 2*max_pairs:
                    pair_cap *= 2
                move_cap = 16
                while move_cap < 2*len(c.shapes):
                    move_cap *= 2
                total += 32+11*6 + 32+11*(1+len(live)) + 3*(32+11*12)
                total += len(live)*(32+11*9)
                total += 2*(32+11*3)+33*(move_cap+pair_cap)
                total += 32+11*(1+2*max_pairs)
    return 2*total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--katalog', type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    rows = cases()
    bound = output_bound(rows)
    if bound > 20*1024**2:
        raise ValueError(f'Output bound exceeds 20 MiB: {bound}')
    args.katalog.mkdir(parents=True, exist_ok=True)
    for suffix, fmt in (('.csv', lambda w: f'{w:08x}'), ('-stdin.csv', str)):
        content = ''.join(str(c.id)+' '+ ' '.join(fmt(w) for w in c.words)+'\n' for c in rows)
        (args.katalog / ('przypadki-szeroka'+suffix)).write_text(content, encoding='ascii', newline='\n')
    print(f'{len(rows)} cases (67 broad + 8 set), {sum((len(c.ops) for c in rows))} operations; C+Duckling bound {bound} B')


if __name__ == '__main__':
    main()
