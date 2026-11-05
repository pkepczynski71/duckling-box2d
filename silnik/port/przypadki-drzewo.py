pass                                                                             
import argparse
from dataclasses import dataclass
import math
from pathlib import Path

from przypadki import bits, number

COUNT = 50
MAX_OPS = 200
ALL = (1 << 64) - 1


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    dump_every: int
    ops: tuple

    @property
    def words(self):
        return (len(self.ops), self.dump_every, *(w for op in self.ops for w in op))


def create(box, category=ALL, user=0):
    return (0, *map(bits, box), category & 0xffffffff, category >> 32, user)


def delete(n):
    return (1, n, 0, 0, 0, 0, 0, 0)


def move(n, box, enlarge=False):
    return (3 if enlarge else 2, n, *map(bits, box), 0, 0)


def categories(n, category):
    return (4, n, category & 0xffffffff, category >> 32, 0, 0, 0, 0)


def query(box=(-4096, -4096, 4096, 4096), mask=ALL):
    return (5, *map(bits, box), mask & 0xffffffff, mask >> 32, 0)


def rebuild(full):
    return (6, full, 0, 0, 0, 0, 0, 0)


def box_at(x, y=0, size=1):
    return (x, y, x+size, y+size)


def contains(a, b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3]


def overlaps(a, b):
                                                                               
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def valid_box(words):
    a = tuple(map(number, words))
    if (len(a) != 4 or not all(map(math.isfinite, a))
            or not (a[0] <= a[2] and a[1] <= a[3])
            or not (a[2]-a[0] < 100000 and a[3]-a[1] < 100000)):
        raise ValueError('Invalid AABB / extent >= B2_HUGE')
    return a


def states(case):
    pass                                                                           
    if not 1 <= len(case.ops) <= MAX_OPS or case.dump_every not in (0, 1):
        raise ValueError('Bad opCount/dumpEvery')
    live = {}
    created = 0
    for k, w in enumerate(case.ops, 1):
        if len(w) != 8 or any(type(v) is not int or not 0 <= v < 2**32 for v in w):
            raise ValueError(f'Bad u32 operation {k}')
        kind = w[0]
        unused = {0: (), 1: range(2, 8), 2: (6, 7), 3: (6, 7),
                  4: range(4, 8), 5: (7,), 6: range(2, 8)}
        if kind not in unused or any(w[i] for i in unused[kind]):
            raise ValueError(f'Bad type/unused word at operation {k}')
        if kind == 0:
            a = valid_box(w[1:5])
            if not all(-100000 < x < 100000 for x in a):
                raise ValueError('Create coordinates outside B2_HUGE')
            live[created] = (w[1:5], w[5] | w[6] << 32, w[7])
            created += 1
        elif kind in (1, 2, 3, 4):
            n = w[1]
            if n not in live:
                raise ValueError(f'Dead/unknown n at operation {k}')
            old, category, user = live[n]
            if kind == 1:
                del live[n]
            elif kind in (2, 3):
                a = valid_box(w[2:6])
                if kind == 3 and contains(tuple(map(number, old)), a):
                    raise ValueError('Enlarge: old AABB contains new AABB')
                live[n] = (w[2:6], category, user)
            else:
                live[n] = (old, w[2] | w[3] << 32, user)
        elif kind == 5:
            valid_box(w[1:5])
        elif w[1] not in (0, 1):
            raise ValueError('Bad fullBuild')
        yield dict(live)


def cases():
    rows = []

    def add(category, ops, dump=1):
        case = Case(len(rows)+1, category, dump, tuple(ops))
        list(states(case))
        rows.append(case)

                                                         
    add('puste', [query(), rebuild(0), rebuild(1), query(mask=0)])
    add('puste', [rebuild(1), query(mask=1 << 63), rebuild(0)])
    add('puste', [query((0, 0, 0, 0)), query(mask=ALL)], dump=0)
                                                                                  
    for i in range(4):
        a = (-1, -2, 2, 3)
        add('jeden', [create(a, (1, 1 << 32, 1 << 63, ALL)[i], 0xffffffff-i),
            query(a), query((2, 3, 4, 5)), query((3, 4, 5, 6)), rebuild(i % 2),
            move(0, (-3, -4, 4, 5), True), query(), delete(0), query(),
            create(a, 1, 0x80000000+i), rebuild(1), query()])
                                                               
    for count in (9, 16, 24, 40, 64):
        ops = [create(box_at((i % 8)*3, (i // 8)*3), 1 << (i % 64), i) for i in range(count)]
        ops += [query(), query(mask=1 << 63), rebuild(1), query(), rebuild(0), query()]
        add('wzrost-puli', ops)
                                                                                 
    for mode in range(5):
        order = (list(range(12)), list(reversed(range(12))),
                 list(range(0, 12, 2))+list(range(1, 12, 2)),
                 [5, 0, 11, 3, 8, 1, 10, 4, 7, 2, 9, 6], list(range(12)))[mode]
        ops = [create(box_at(i*2), user=i) for i in range(12)]
        for j, n in enumerate(order):
            ops += [delete(n), query()]
            if mode == 4:
                ops += [create(box_at(-j*3, 4), user=100+j), query()]
        ops += [create(box_at(-i*2, -4), user=200+i) for i in range(12)]
        ops += [query(), rebuild(mode % 2), query()]
        add('wolne-miejsca', ops)
                                                                                
    for mode in range(6):
        ops = []
        for i in range(32):
            x, y = ((i*2, 0), (-i*2, 0), (0, i*2), (0, -i*2),
                    (i*2, i*2), ((-1)**i*i*2, (i % 3)*.5))[mode]
            ops += [create(box_at(x, y), user=i+1), query()]
        ops += [query((7, -2, 31, 31)), rebuild(1), query()]
        add('obroty', ops)
                                                                                
    for mode in range(4):
        ops = [create(box_at(i*3, mode), user=i) for i in range(12)]
        for i in range(12):
            a = box_at(-i*2, 10+mode, .5)
            b = (a[0]-.25, a[1]-.5, a[2]+.75, a[3]+.5)
            if mode == 3 and i == 0:
                b = (a[0], a[1], number(bits(a[2])+1), a[3])
            ops += [move(i, a), query(a), move(i, b, True), query(b)]
        ops += [rebuild(0), query(), rebuild(1), query()]
        add('przesun-powieksz', ops)
                                                                                 
    cats = (0, 1, 2, 1 << 31, 1 << 32, 1 << 63, ALL, 0x8000000180000001)
    for mode in range(4):
        ops = [create(box_at(i % 3, i // 3, 2), cat, 0xffffffff-i) for i, cat in enumerate(cats)]
        for mask in cats:
            ops.append(query(mask=mask))
        for i in range(8):
            ops += [categories(i, cats[(i+mode+1) % 8]), query(mask=cats[i]), query()]
        ops += [rebuild(mode % 2), query(mask=1 << 63)]
        add('kategorie-maski', ops)
                                                                              
    for mode in range(4):
        shift = (-16, 0, .125, 1024)[mode]
        a = (shift, shift, shift+1, shift+1)
        edge = shift+1
        ops = [create(a, user=0), create((edge, shift, edge+1, edge), user=0),
               create((shift, edge, edge, edge+1), user=0x80000000)]
        for x in (number(bits(edge)-1) if edge > 0 else edge-.0001,
                  edge, number(bits(edge)+1) if edge > 0 else edge+.0001):
            ops += [query((x, edge, x, edge)), query((x, shift, x, edge))]
        ops += [query((shift-2, shift-2, shift-1, shift-1)), query(), rebuild(1), query()]
        add('styk', ops)
                                                                             
                                                                                 
    for mode in range(4):
        ops = [create(box_at(i % 6*4, i // 6*4), 1 << (i % 64), i+1) for i in range(24)]
        ops += [rebuild(0), query(), rebuild(1), query()]
        for i in range(mode, 24, 4):
            x, y = i % 6*4, i // 6*4
            ops += [move(i, (x-1, y-2, x+2, y+3), True), query()]
        ops += [rebuild(0), query(), rebuild(0), rebuild(1), query()]
        for i in range(6):
            ops += [delete(i), create(box_at(-i*4, -4), ALL, 100+i),
                    move(6+i, box_at(40+i*2, 40)), query()]
        ops += [rebuild(0), rebuild(1), query()]
        add('przebudowa', ops)
                                                                             
    add('200-obszarow', [create(box_at(i % 20*2, i // 20*2), 1 << (i % 64), i)
                        for i in range(200)], dump=0)
                                                                           
    for mode in range(2):
        ops = []
        for i in range(24):
            a = (-1, -1, 1, 1) if mode == 0 else box_at((i % 2)*4-2, (i // 2 % 2)*4-2)
            ops += [create(a, ALL, i+1), query()]
        ops += [rebuild(0), query(), rebuild(1), query()]
        add('remisy-sasiada', ops)
                                                                            
    for boxes in (
            ((12, -3, 28, -2.5), (12, 14, 20, 22), (-1, 12, -.5, 12.5), (-7, 1, -3, 17)),
            ((-15, 2, -7, 10), (-12, -4, -11.5, 0), (-17, 0, -1, .5), (-19, -11, -11, -3))):
        add('obroty-B-lisc', [*(create(a, 1, i+1) for i, a in enumerate(boxes)), query()])
                                                                        
    add('obszar-punkt', [create((0, 0, 0, 0), 1, 45), query((0, 0, 0, 0)),
        rebuild(0), rebuild(1), query(), delete(0), query()])
    add('obszar-punkt', [create((-1, -1, 1, 1), 1, 46), create((0, 0, 0, 0), 1, 47),
        query((0, 0, 0, 0)), delete(0), query(), rebuild(0), rebuild(1), delete(1), query()])
                                                                       
    add('znaczniki-przodkow', [*rows[26].ops[:15], rebuild(0), query()])
                                                                               
    add('powieksz-usun-przebuduj', [create((0, 0, 1, 1), 1, 1),
        create((4, 0, 5, 1), 1, 2), create((8, 0, 9, 1), 1, 3),
        move(0, (-1, -2, 2, 3), True), delete(0), query(), rebuild(0),
        create((0, 0, 1, 1), 1, 4), query(), delete(1), delete(2), delete(3),
        query(), rebuild(0), create((2, 2, 3, 3), 1, 5), query()])
    add('powieksz-usun-przebuduj', [create((0, 0, 1, 1), 1, 1),
        move(0, (-1, -1, 2, 2), True), delete(0), query(), rebuild(0),
        create((3, 3, 4, 4), 1, 2), query(), delete(1), query(), rebuild(0)])
                                                                             
                                                                            
                                                                                   
    boxes = (
        (-.003813724033534527, -.002376841614022851, -.003325442783534527, -.001888560364022851),
        (-.00338149955496192, .0033046079333871603, -.00325942924246192, .0033122373279184103),
        (.001985627692192793, .0035366991069167852, .0019856574945151806, .003536706557497382),
        (.0011386675760149956, .001480043982155621, .005044917576014996, .0014805208193138242))
    point = (-.002429010346531868, .008595490828156471, -.002429010346531868, .008595490828156471)
    add('nawiasowanie-kosztu', [*(create(a, 1, i+1) for i, a in enumerate(boxes)),
        create(boxes[0], 1, 5), rebuild(1), move(4, point), query(point), query()])
    if len(rows) != COUNT:
        raise ValueError('Case count differs from contract')
    return tuple(rows)


def read_inputs(path):
    lines = Path(path).read_text(encoding='ascii').splitlines()
    expected = cases()
    if len(lines) != COUNT:
        raise ValueError(f'Expected {COUNT} tree inputs, got {len(lines)}')
    for case, line in zip(expected, lines):
        tokens = line.split(' ')
        if (len(tokens) != 1+len(case.words) or tokens[0] != str(case.id)
                or any(len(t) != 8 or any(c not in '0123456789abcdef' for c in t) for t in tokens[1:])):
            raise ValueError(f'Bad input format: case {case.id}')
        if tuple(int(t, 16) for t in tokens[1:]) != case.words:
            raise ValueError(f'Input differs from recipe: case {case.id}')
    return expected


def output_size_bound(rows):
    pass                                                                 

                                                                            
                                                                            
                                                                           
       
    def size(values):
        return sum(1+len(str(v)) for v in values)

    byte_bound = len(f'PORT4 {len(rows)}\nEND {len(rows)}\n')
    lines = 2
    dumps = 0
    operations = 0
    for case in rows:
        for k, (op, live) in enumerate(zip(case.ops, states(case)), 1):
            byte_bound += len(f'O {case.id} {k}\n')+size(op)
            if op[0] in (0, 6):
                byte_bound += 4                        
            elif op[0] == 5:
                a = tuple(map(number, op[1:5]))
                mask = op[5] | op[6] << 32
                users = [user for box, cat, user in live.values()
                         if cat & mask and overlaps(tuple(map(number, box)), a)]
                byte_bound += 12+sum(size((999, user, 0)) for user in users)
            operations += 1
            lines += 1
            if case.dump_every or k == len(case.ops):
                byte_bound += len(f'D {case.id} {k}\n')
                byte_bound += size((0xffffffff, 999, 999, 0xffffffff, 999, 999,
                                    0xffffffff, *([0xffffffff]*4), 999))
                byte_bound += sum(size((n, 999, *box, cat & 0xffffffff, cat >> 32, user, 0))
                                  for n, (box, cat, user) in live.items())
                dumps += 1
                lines += 1
    return {'operations': operations, 'dumps': dumps, 'lines': lines,
            'bytes_at_most': byte_bound, 'both_outputs_at_most': 2*byte_bound}


def write_inputs(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rows = cases()
    if output_size_bound(rows)['both_outputs_at_most'] > 5_000_000:
        raise ValueError('Output exceeds 5 MB bound')
    for suffix, render in (('.csv', lambda v: f'{v:08x}'), ('-stdin.csv', str)):
        (directory / ('przypadki-drzewo'+suffix)).write_text(''.join(
            f'{c.id} '+' '.join(map(render, c.words))+'\n' for c in rows), encoding='ascii', newline='\n')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--katalog', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    rows = write_inputs(args.katalog)
    print(f'Drzewo: {len(rows)} przypadkow; {output_size_bound(rows)}')


if __name__ == '__main__':
    main()
