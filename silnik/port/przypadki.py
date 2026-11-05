pass                                                                                            
import argparse
from dataclasses import dataclass
from pathlib import Path
import struct

COUNT = 180
INPUT_FIELDS = (
    'A.center.x', 'A.center.y', 'A.radius', 'xfA.p.x', 'xfA.p.y', 'xfA.q.c', 'xfA.q.s',
    'B.center.x', 'B.center.y', 'B.radius', 'xfB.p.x', 'xfB.p.y', 'xfB.q.c', 'xfB.q.s',
)
CATEGORIES = ('brak', 'stycznosc', 'przenikanie', 'wyprzedzajacy', 'prog',
              'wspolny', 'promienie', 'zamiana', 'transformacje', 'skale')


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def number(word):
    return struct.unpack('<f', struct.pack('<I', word))[0]


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    words: tuple

    @property
    def edge(self):
        return self.category == 'prog'


def pair(a=(0, 0, 1), ta=(0, 0, 1, 0), b=(0, 0, 1), tb=(0, 0, 1, 0)):
    return tuple(bits(x) for x in (*a, *ta, *b, *tb))


def cases():
    rows = []

    def add(category, words):
        rows.append(Case(len(rows) + 1, category, words))

    for i in range(18):
        add('brak', pair(tb=(3 + i / 8, (-1)**i / 4, 1, 0)))
    for i in range(18):
        ra, rb = (i + 1) / 16, (19 - i) / 16
        add('stycznosc', pair(a=(0, 0, ra), ta=(i / 8, -i / 16, 1, 0),
                             b=(0, 0, rb), tb=(i / 8 + ra + rb, -i / 16, 1, 0)))
    for i in range(18):
        add('przenikanie', pair(a=(1 / 4, -1 / 8, 1), b=(-1 / 8, 1 / 4, 3 / 4),
                               tb=(i / 32, 1 / 8, 1, 0)))
    for i in range(18):
        add('wyprzedzajacy', pair(tb=(2 + (i + 1) / 1024, 0, 1, 0)))
                                                                                   
    for offset in range(-8, 10):
        if offset in (-1, 0, 1):                                                            
            threshold = number(0x3ca3d70a)
            radius_a = threshold / 2
                                                                               
                                                                              
            radius_b = number(bits(radius_a) - 2 * offset)
            add('prog', pair(a=(0, 0, radius_a), b=(0, 0, radius_b),
                             tb=(2 * threshold, 0, 1, 0)))
        else:
            row = list(pair())
            row[10] = bits(2.02) + offset
            add('prog', tuple(row))
    for i in range(18):
                                                                             
        add('wspolny', pair(a=(0, 0, (i + 1) / 16), ta=(i / 8, -i / 8, 0, 1),
                           b=(0, 0, (19 - i) / 16), tb=(i / 8, -i / 8, -1, 0)))
    for i in range(18):
        ra, rb = 2.0**(i % 6 + 3), 2.0**(-18 - (i % 6))
        if i % 2:
            ra, rb = rb, ra
        add('promienie', pair(a=(0, 0, ra), ta=(0, i / 16, 1, 0), b=(0, 0, rb),
                             tb=(ra + rb - 1 / 4, i / 16, 1, 0)))
    for i in range(9):
        row = pair(a=(1 / 4, -1 / 8, (i + 2) / 8), ta=(1, -2, 0, 1),
                   b=(-1 / 8, 1 / 4, 1), tb=(1 + i / 8, -1, 1, 0))
        add('zamiana', row)
        add('zamiana', row[7:] + row[:7])
    rotations = ((1, 0), (0, 1), (-1, 0), (0, -1), (0.6, 0.8), (0.8, -0.6))
    for i in range(18):
        ca, sa = rotations[i % 6]
        cb, sb = rotations[(i + 2) % 6]
        add('transformacje', pair(a=(1 / 4, -1 / 2, 1), ta=(i / 2 - 4, -i / 4, ca, sa),
                                 b=(-1 / 2, 1 / 8, 3 / 4),
                                 tb=(i / 2 - 3, -i / 4 + (i % 3) / 4, cb, sb)))
    for i in range(9):
        base = 2.0**(10 + i)
        add('skale', pair(a=(1 / 4, -1 / 2, 1), ta=(base, -base, 0, 1),
                          b=(-1 / 4, 1 / 2, 1), tb=(base + 1, -base, -1, 0)))
    for i in range(9):
        if i in (4, 5, 6):                                                              
            length = number(0x34000000 + i - 5)
            add('skale', pair(tb=(length, 0, 1, 0)))
            continue
        scale = 2.0**(-30 + i * 2)
        add('skale', pair(a=(-0.0, 0, scale), b=(0, -0.0, scale / 2),
                          tb=(scale, scale / 2, 1, 0)))
    assert len(rows) == COUNT
    assert all(sum(c.category == name for c in rows) == 18 for name in CATEGORIES)
    assert len({c.words for c in rows}) == COUNT, 'Duplicate input'
    return tuple(rows)


def write_inputs(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rows = cases()
    (directory / 'przypadki.csv').write_text(''.join(
        f'{c.id} ' + ' '.join(f'{x:08x}' for x in c.words) + '\n' for c in rows), encoding='ascii')
                                                                                 
    (directory / 'przypadki-stdin.csv').write_text(''.join(
        f'{c.id} ' + ' '.join(str(x) for x in c.words) + '\n' for c in rows), encoding='ascii')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--katalog', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    write_inputs(args.katalog)
