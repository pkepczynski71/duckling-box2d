pass                                                                              
import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re

from przypadki import bits, number

COUNT = 64
TOTAL = 72
LEGACY_SHA256 = {
    'przypadki-swiat.csv': '137769ee1a8fe95a5d7f17529a3e35e66480a0be8653abb40e5f5cb079a3b6d1',
    'przypadki-swiat-stdin.csv': 'e04f4d31463f492f42856fe9f75b5ba79231dde8913b141c1237fc98231d8290',
}
INPUT_NAMES = (*LEGACY_SHA256, 'przypadki-swiat-pelne.csv', 'przypadki-swiat-pelne-stdin.csv')
U32 = (1 << 32)-1
U64 = (1 << 64)-1
USED = (4, 1, 11, 2, 6, 2, 4)
HEX = re.compile(r'[0-9a-f]{8}\Z')
DEC = re.compile(r'(?:0|[1-9][0-9]{0,9})\Z')


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    ops: tuple


def op(code, *words):
    if len(words) > 24:
        raise ValueError('too many words')
    return (code, *words, *(0 for _ in range(24-len(words))))


def world(slot=0, gravity=(0, -10), speed=400):
    return op(0, slot, *map(bits, gravity), bits(speed))


def body(slot=0, owner=0, kind=2, p=(0, 0), q=(1, 0), v=(0, 0), w=0, fixed=0):
    return op(2, slot, owner, kind, *map(bits, (*p, *q, *v, w)), fixed)


def transform(owner, slot, p, q=(1, 0)):
    return op(4, owner, slot, *map(bits, (*p, *q)))


def f32(value):
    try:
        return number(bits(value))
    except OverflowError:
        return math.copysign(math.inf, value)


def norm_squared(c, s):
                                                         
    c, s = f32(c), f32(s)
    return f32(f32(s*s) + f32(c*c))


ROT_LOWER = f32(1.0-f32(0.0006))
ROT_UPPER = f32(1.0+f32(0.0006))


def valid_rotation(c, s):
    return ROT_LOWER < norm_squared(c, s) < ROT_UPPER


def rotation_boundary_words():
    pass                                                                 
    lower = upper = 0x3f800000
    while norm_squared(number(lower), 0.0) >= ROT_LOWER:
        lower -= 1
    while norm_squared(number(upper), 0.0) <= ROT_UPPER:
        upper += 1
    return lower, upper


def validate_operation(row):
    if len(row) != 25 or any(type(v) is not int or not 0 <= v <= U32 for v in row):
        raise ValueError('operation length / u32')
    code, *a = row
    if code > 6 or any(a[USED[code]:]):
        raise ValueError('opcode / nonzero unused word')
    if code == 0:
        if a[0] > 15 or not all(math.isfinite(number(a[i])) for i in (1, 2, 3)) or number(a[3]) <= 0:
            raise ValueError('world definition')
    elif code == 2:
        if a[0] > 255 or a[1] > 15 or a[2] > 2 or a[10] > 1:
            raise ValueError('body definition')
        if not all(math.isfinite(number(a[i])) for i in range(3, 10)):
            raise ValueError('nonfinite body')
    elif a[0] > 15 or (code != 1 and a[1] > 255):
        raise ValueError('register range')
    if code in (2, 4):
        i = 5 if code == 2 else 4
        if code == 4 and not all(math.isfinite(number(a[j])) for j in (2, 3, 4, 5)):
            raise ValueError('nonfinite transform')
        c, s = map(number, a[i:i+2])
        if not valid_rotation(c, s):
            raise ValueError('rotation')
    if code == 6 and (not 1 <= a[2] <= 65536 or a[3] > 255 or a[1] == a[3]):
        raise ValueError('CHURN arguments')


def preflight(rows, expected_count=COUNT):
    if len(rows) != expected_count or [c.id for c in rows] != list(range(1, len(rows)+1)):
        raise ValueError('case count / ids')
    for c in rows:
        if not 1 <= len(c.ops) <= 256:
            raise ValueError('opCount')
        worlds, bodies = {}, {}
        serial = 0
        for seq, row in enumerate(c.ops, 1):
            validate_operation(row)
            code, *a = row
            if code == 0:
                if worlds.get(a[0], [False])[0]:
                    raise ValueError('replace live world')
                serial += 1
                worlds[a[0]] = [True, serial]
            else:
                w = a[1] if code == 2 else a[0]
                if w not in worlds:
                    raise ValueError('unsaved world')
                wl, owner = worlds[w]
                if code == 1 and wl:
                    worlds[w][0] = False
                    for b in bodies.values():
                        if b[1] == owner:
                            b[0] = False
                elif code == 2:
                    if bodies.get(a[0], [False])[0]:
                        raise ValueError('replace live body')
                    if wl:
                        bodies[a[0]] = [True, owner]
                elif code in (3, 4, 5):
                    if a[1] not in bodies:
                        raise ValueError('unsaved body')
                    if code == 3 and wl and bodies[a[1]][1] == owner:
                        bodies[a[1]][0] = False
                elif code == 6:
                    if not wl or bodies.get(a[1], [False])[0] or a[3] not in bodies or bodies[a[3]][0]:
                        raise ValueError('CHURN lifecycle')
                    if bodies[a[3]][1] != owner:
                        raise ValueError('CHURN old owner')
                    bodies[a[1]] = [True, owner]
            if sum(w[0] for w in worlds.values()) > 4 or sum(b[0] for b in bodies.values()) > 256:
                raise ValueError('corpus live limits')
    return rows


def build():
    rows = []
    def add(category, operations):
        rows.append(Case(len(rows)+1, category, tuple(operations)))
    add('E9617961b221b E98fc34a4e5dc', [world(), op(1, 0)])
                                                                           
    add('E8c586909c59a E1bf61810dc30 E054a5c91e77c', [world(), body(), op(3, 0, 0), body(1), op(5, 0, 0), op(5, 0, 1), op(1, 0)])
    add('Eda05cc46a520 E95731edd551e / Ed44ecc64cccb E8d3d1fea3b1b', [world(i, (i, -i-1)) for i in range(4)] + [op(1, 1), world(4), op(1, 0), world(5)])
    add('E95731edd551e Ebf76bbb1a487 E4b0beae6fb74', [world(i) for i in range(4)] + [op(1, i) for i in (3, 1, 2, 0)])
    add('E01be30bb4a27 E4d3de6062df4 z E9a01250a069e', [world(), body(), body(1, kind=0), op(1, 0), world(1), body(2, 1), op(5, 1, 0), op(5, 0, 2)])
    add('E9e73e72eecc5 E98fc34a4e5dc', [world(), op(1, 0), world(1), op(1, 0), body(0, 0), body(1, 1), op(5, 0, 1)])
    add('Ea108f54afae7 E7b05c294cef2', [world(2), world(0), world(3), op(1, 0), world(4), op(1, 2), world(5), op(1, 3)])
    add('Ef718a7a58dd7 E80b4e95db3b2 E4d3de6062df4', [world(), body(), op(1, 0), world(), body(1), op(3, 0, 0), transform(0, 1, (7, -9))])
    sets = [((0, 0), (1, 0), (0, 0), 0, 0), ((3, -7), (0, 1), (9, -11), 5, 0),
            ((-2, 6), (-1, 0), (500, -700), -13, 1), ((-0.0, 0.0), (0, -1), (-0.0, 21), 17, 1)]
    for kind in range(3):
        for p, q, v, w, fixed in sets:
            add('typ / definicja', [world(speed=10), body(kind=kind, p=p, q=q, v=v, w=w, fixed=fixed),
                                   op(5, 0, 0), transform(0, 0, (13, -15), q), op(5, 0, 0), op(3, 0, 0)])
    for variant in range(12):
        kinds = [variant//3 % 3]*5 if variant < 9 else [0, 1, 2, 1, 2]
        ops = [world()] + [body(i, kind=t, p=(i*3+1, -i-2), v=(i+1, -i-1), w=i+1) for i, t in enumerate(kinds)]
        removed = variant % 3 * 2
        ops += [op(3, 0, removed)]
        moved = 4 if removed != 4 else 3
        ops += [transform(0, moved, (101+variant, -103-variant), (0, -1)), op(5, 0, moved)]
        free = [i for i in (0, 2, 4) if i != removed]
        ops += [op(3, 0, i) for i in free]
        ops += [body(10+i, kind=kinds[n], p=(201+i, -211-i)) for i, n in enumerate([*reversed(free), removed])]
        ops += [op(3, 0, i) for i in sorted(set(range(5))-{removed, *free})]
        ops += [op(3, 0, i) for i in (11, 10, 12)] + [body(20), transform(0, 20, (303, -307))]
        add('usuwanie / LIFO / przeniesiony', ops)
    for variant in range(8):
        ops = [world(0), world(1, (2, -3)), body(0, 0, p=(1, 2)), body(1, 1, p=(3, 4))]
        ops += [op(5, 1, 0), transform(1, 0, (90, 91)), op(3, 1, 0), op(5, 0, 1), op(3, 0, 1)]
        ops += [op(1, 0), world(2), body(2, 2, p=(5+variant, 6)), op(5, 0, 0), op(5, 2, 0),
                transform(2, 0, (99, 98)), op(3, 2, 0), transform(2, 2, (11, -12)), op(5, 1, 1)]
        if variant % 2:
            ops += [op(1, 1), world(1), body(3, 1), op(5, 1, 1), op(3, 1, 1)]
        add('Eb2d4dbdd6e3b / E5884ec40704e E60059b7d1b8f', ops)
    for variant in range(8):
        ops = [world()]
        for i in range(65):
            if i == 31 and variant % 2:
                ops += [op(3, 0, 9), transform(0, 30, (701, -703), (0, 1))]
            ops += [body(i, kind=(i+variant)%3, p=(i*7+variant+1, -i*5-variant-1),
                         q=((1, 0), (0, 1), (-1, 0), (0, -1))[i%4], v=(i+1, -i-2), w=i+3, fixed=i%2)]
        if variant % 2:
            ops += [body(65, kind=(65+variant)%3, p=(65*7+variant+1, -65*5-variant-1), v=(66, -67), w=68, fixed=1)]
        ops += [op(3, 0, 32), transform(0, 64, (901, -907), (0, -1)), body(100, p=(911, -919)),
                transform(0, 15, (-929, 937)), op(5, 0, 0), op(5, 0, 63)]
        add('wzrost 16/32/64/65', ops)
    for variant in range(8):
        q = ((1, 0), (0, 1), (-1, 0), (0, -1))[variant%4]
        ops = [world(gravity=(-0.0, 0.0)), body(0, kind=variant%3, p=(-0.0, 0.0), q=q, v=(11, -13)),
               body(1, kind=(variant+1)%3, p=(0.0, -0.0), q=q, v=(-17, 19))]
        for p in ((-0.0, -0.0), (23, -29), (0.0, -0.0), (-31, 37)):
            ops += [transform(0, variant%2, p, q), op(5, 0, 1-variant%2)]
        add('bity transformacji / missing kroku', ops)
    add('E2300eca14adb E8bdf9cae947b', [world(), body(), op(3, 0, 0), op(6, 0, 1, 7, 0), op(5, 0, 0), op(3, 0, 0), op(5, 0, 1)])
    add('pakowanie world0', [world(), world(1), body(0, 1), op(3, 1, 0), op(6, 1, 1, 11, 0), op(5, 1, 0)])
                                                                    
    add('pokolenie zero', [world(), body(), op(3, 0, 0), op(6, 0, 1, 65535, 0), op(5, 0, 0), transform(0, 1, (41, -43))])
                                                                   
    add('Ef0786b32909d E272548baa36c', [world(), body(), op(3, 0, 0), op(6, 0, 1, 65536, 0),
                           transform(0, 0, (999, 999)), op(3, 0, 0), op(5, 0, 0),
                           transform(0, 1, (47, -53)), op(5, 0, 1)])
    for variant in range(4):
        add('E6694ea807500 / E0366d9e50b40 E38fce4306bcb', [world(), body(p=(61+variant, -67)), op(3, 0, 0), body(1),
                                           op(1, 0), world(1), body(2, 1), op(5, 1, 0), op(5, 1, 1), op(5, 1, 2)])
    return tuple(preflight(rows))


def encode(rows, decimal=False):
    lines = [str(len(rows))]
    for c in rows:
        lines.append(f'C {c.id} {len(c.ops)}')
        for seq, (code, *a) in enumerate(c.ops, 1):
            words = ' '.join(str(v) if decimal else f'{v:08x}' for v in a)
            lines.append(f'O {seq} {code} {words}')
                                                                            
    return ''.join(line + ('\r\n' if i%3 == 1 else '\n') for i, line in enumerate(lines[:-1])) + lines[-1]


def cases():
    rows = list(build())
    for name, digest in LEGACY_SHA256.items():
        if hashlib.sha256(encode(rows, name.endswith('-stdin.csv')).encode('ascii')).hexdigest() != digest:
            raise ValueError('zmieniono first 64 przypadki: '+name)
    lo, hi = rotation_boundary_words()
    rotations = ((0.6, 0.8), (-0.6, 0.8), (-0.8, -0.6), (f32(2**-0.5), f32(2**-0.5)),
                 (number(0x3f800400), 0), (number(lo+2), 0), (number(hi-2), 0), (0.8, -0.6))
    for i, q in enumerate(rotations):
        assert valid_rotation(*q)
        rows.append(Case(65+i, 'K1 E45b39e23b6af E04703b8e49fd / E2de7df7eee3a Ef81ff9d56cdf',
                         (world(), body(kind=i%3, p=(i+1, -i-3), q=q, v=(7, -11), w=13, fixed=i%2),
                          transform(0, 0, (-17-i, 19+i), rotations[(i+1)%len(rotations)]),
                          op(5, 0, 0), op(3, 0, 0), op(1, 0))))
    return tuple(preflight(rows, TOTAL))


def verify_input_hashes(directory, manifest):
    sums = json.loads(Path(manifest).read_bytes())
    if set(sums) != set(INPUT_NAMES):
        raise ValueError('Ef5cd2c5d69b8 manifest E989eb0d5a480')
    for name, digest in sums.items():
        if hashlib.sha256((Path(directory)/name).read_bytes()).hexdigest() != digest:
            raise ValueError('E1a8ede14b808 bytes E5422e223df9f: '+name)
    for name, digest in LEGACY_SHA256.items():
        if sums[name] != digest:
            raise ValueError('E58e397f42095 Ecebe1b171d0e 64 E279cf128155b: '+name)
    for name, legacy in (('przypadki-swiat-pelne.csv', 'przypadki-swiat.csv'),
                         ('przypadki-swiat-pelne-stdin.csv', 'przypadki-swiat-stdin.csv')):
        lines = (Path(directory)/name).read_bytes().splitlines(keepends=True)
        boundary = next((i for i, line in enumerate(lines) if line.startswith(b'C 65 ')), None)
        if boundary is None:
            raise ValueError('missing E036a8a704eee E1f28d2f749ee: '+name)
                                                                              
                                                                                
        prefix = b'64\n'+b''.join(lines[1:boundary]).rstrip(b'\r\n')
        if hashlib.sha256(prefix).hexdigest() != LEGACY_SHA256[legacy]:
            raise ValueError('E58e397f42095 first 64 E50e721e49c01 E1cc2f793db32 E955d97fab269: '+name)


def read_input(text, decimal=False, expected_count=COUNT):
    normalized = text.replace('\r\n', '\n')
    if not text.isascii() or '\r' in normalized:
        raise ValueError('ASCII / line endings')
    lines = normalized.split('\n')
    if lines[-1] == '':
        lines.pop()
    def tokens(index):
        if index >= len(lines):
            raise ValueError('truncated input')
        return lines[index].split(' ')
    def dec(t):
        if not DEC.fullmatch(t) or int(t) > U32:
            raise ValueError('canonical decimal u32')
        return int(t)
    first = tokens(0)
    if len(first) != 1 or dec(first[0]) != expected_count:
        raise ValueError('N')
    pos, rows = 1, []
    for case_id in range(1, expected_count+1):
        t = tokens(pos); pos += 1
        if len(t) != 3 or t[0] != 'C' or dec(t[1]) != case_id or not 1 <= dec(t[2]) <= 256:
            raise ValueError('C header')
        count, ops = dec(t[2]), []
        for seq in range(1, count+1):
            t = tokens(pos); pos += 1
            if len(t) != 27 or t[0] != 'O' or dec(t[1]) != seq:
                raise ValueError('O / seq / length')
            if decimal:
                a = tuple(dec(v) for v in t[3:])
            else:
                if not all(HEX.fullmatch(v) for v in t[3:]):
                    raise ValueError('canonical hex u32')
                a = tuple(int(v, 16) for v in t[3:])
            ops.append((dec(t[2]), *a))
        rows.append(Case(case_id, '', tuple(ops)))
    if pos != len(lines):
        raise ValueError('extra input')
    return tuple(preflight(rows, expected_count))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--katalog', type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    rows = cases()
    args.katalog.mkdir(parents=True, exist_ok=True)
    sums = {}
    for name in INPUT_NAMES:
        decimal = name.endswith('-stdin.csv')
        selected = rows[:64] if name in LEGACY_SHA256 else rows
        text = encode(selected, decimal)
        assert read_input(text, decimal, len(selected)) == tuple(Case(c.id, '', c.ops) for c in selected)
        data = text.encode('ascii')
        (args.katalog/name).write_bytes(data)
        sums[name] = hashlib.sha256(data).hexdigest()
    (args.katalog/'wejscia-swiat-sha256.json').write_bytes((json.dumps(sums, indent=2)+'\n').encode('ascii'))
    verify_input_hashes(args.katalog, args.katalog/'wejscia-swiat-sha256.json')
    print(f'PORT6: {len(rows)} scenariuszy, {sum((len(c.ops) for c in rows))} operacji')


if __name__ == '__main__':
    main()
