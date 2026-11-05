pass                                                                                
import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import subprocess
import time

from przypadki import bits, number

BASE_COUNT = 240
COUNT = 252
CATEGORIES = ('brak', 'styk', 'przenikanie', 'wyprzedzajacy', 'prog', 'wierzcholki',
              'zaokraglone', 'rownolegle', 'zamiana', 'transformacje', 'skale', 'wspolny')
INPUT_FIELDS = tuple(
    name for side in ('A', 'B') for name in (
        f'{side}.count',
        *(f'{side}.vertices[{i}].{xy}' for i in range(8) for xy in ('x', 'y')),
        *(f'{side}.normals[{i}].{xy}' for i in range(8) for xy in ('x', 'y')),
        f'{side}.centroid.x', f'{side}.centroid.y', f'{side}.radius',
        *(f'xf{side}.{field}' for field in ('p.x', 'p.y', 'q.c', 'q.s'))))
IDENTITY = (0, 0, 1, 0)
ROTATIONS = ((1, 0), (0, 1), (-1, 0), (0, -1), (.6, .8), (.8, -.6))
                                                                            
OCTAGON = ((2, 0), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1))


@dataclass(frozen=True)
class Shape:
    kind: int = 0                                                           
    count: int = 4
    radius: float = 0
    hx: float = 1
    hy: float = 1
    cx: float = 0
    cy: float = 0
    c: float = 1
    s: float = 0
    points: tuple = ()

    def words(self):
        points = tuple(v for point in self.points for v in point)
        return (self.kind, self.count, *(bits(v) for v in (
            self.radius, self.hx, self.hy, self.cx, self.cy, self.c, self.s,
            *points, *([0] * (16 - len(points))))))


@dataclass(frozen=True)
class Parameters:
    id: int
    category: str
    a: Shape
    ta: tuple
    b: Shape
    tb: tuple

    @property
    def edge(self):
        return self.category == 'prog'

    @property
    def words(self):
        return (*self.a.words(), *map(bits, self.ta), *self.b.words(), *map(bits, self.tb))


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    words: tuple

    @property
    def edge(self):
        return self.category == 'prog'


def parameters():
    rows = []

    def add(category, a=Shape(), ta=IDENTITY, b=Shape(), tb=IDENTITY):
        rows.append(Parameters(len(rows) + 1, category, a, ta, b, tb))

    for i in range(20):
        add('brak', tb=(3 + i / 8, i / 32, 1, 0))
    for i in range(20):
        add('styk', a=Shape(hy=1 + i / 32), tb=(2, i / 32, 1, 0))
    for i in range(20):
        add('przenikanie', tb=(i / 32, -i / 64, 1, 0))
    for i in range(20):
        add('wyprzedzajacy', tb=(2 + (i + 1) / 2048, i / 64, 1, 0))
                                                                          
                                                                               
    thresholds = (number(0x3ca3d70a), number(bits(number(bits(.1)) * number(bits(.005)))))
    for t in thresholds:
        for delta in (-2, -1, 0, 1, 2):
            gap = number(bits(t) + delta)
            for swap in (False, True):
                h = 2**-18
                a, b = Shape(hx=h, hy=1/8), Shape(hx=h, hy=1/16)
                ta, tb = IDENTITY, (number(bits(2*h + gap)), 0, 1, 0)
                if swap:
                    a, ta, b, tb = b, tb, a, ta
                add('prog', a, ta, b, tb)
    for i in range(20):
        n = 3 + i % 6
        a = Shape(kind=2, count=n, points=OCTAGON[:n])
        m = 3 + (i + 2) % 6
        b = Shape(kind=2, count=m, points=OCTAGON[:m], radius=(i % 3) / 32)
        add('wierzcholki', a, IDENTITY, b, (i / 16, -i / 32, 1, 0))
    for i in range(20):
                                                                                  
        r = 1/8 + (i // 10) / 32
        a, b = Shape(radius=r), Shape(radius=r/2)
        if i % 5 == 0:
            tb = (2 + 1/16, i/64, 1, 0)
        elif i % 5 == 1:
            tb = (2 + 1/16, 2 + 1/16, 1, 0)
        elif i % 5 == 2:
            tb = (-2 - 1/16, 2 + 1/16, 1, 0)
        elif i % 5 == 3:
            tb = (-2 - 1/16, -2 - 1/16, 1, 0)
        else:
            tb = (2 + 1/16, -2 - 1/16, 1, 0)
        ta = (0, i / 1024, 1, 0)
        if i >= 10:
            a, ta, b, tb = b, tb, a, ta
        if i == 10:
                                                                        
            a, b = Shape(radius=1/8), Shape(radius=1/16)
            ta, tb = IDENTITY, (2.45, 0, .6, .8)
        elif i in (15, 16, 17):
                                                                                   
                                                                                 
            h = number(0x34000000+i-16)/2
            a = Shape(hx=h, hy=h, radius=1/64)
            b, ta, tb = a, IDENTITY, (1/128, 0, 1, 0)
        elif i in (18, 19):
            a = Shape(hx=2**-26, hy=2**-26, radius=1/64)
            b = Shape(hx=1/8, hy=1/8, radius=1/128)
            ta, tb = IDENTITY, (1/8+1/128, 0, 1, 0)
            if i == 19:
                a, ta, b, tb = b, tb, a, ta
        add('zaokraglone', a, ta, b, tb)
    for i in range(20):
        add('rownolegle', Shape(hx=2, hy=1/8), IDENTITY,
            Shape(hx=1/2 + i/64, hy=1/8), (i/64, 1/4 + (i-10)/2048, 1, 0))
    for i in range(10):
        a = Shape(kind=1, hx=1/2, hy=3/4, cx=1/8, cy=-1/4, c=0, s=1, radius=1/16)
        b = Shape(kind=2, count=3+i%6, points=OCTAGON[:3+i%6], radius=1/32)
        ta, tb = (1, -2, 0, 1), (1+i/16, -1, .6, .8)
        add('zamiana', a, ta, b, tb)
        add('zamiana', b, tb, a, ta)
    for i in range(20):
        a = Shape(kind=1, hx=1/2, hy=3/4, cx=1/4, cy=-1/8,
                  c=ROTATIONS[i%6][0], s=ROTATIONS[i%6][1])
        add('transformacje', a, (i/4, -i/8, *ROTATIONS[(i+1)%6]),
            Shape(hx=3/4, radius=1/32), (i/4+1/2, -i/8+1/4, *ROTATIONS[(i+2)%6]))
    for i in range(10):
        p = 2.0**(10+i)
        add('skale', ta=(p, -p, 1, 0), tb=(p+1+i/64, -p+1/4, 1, 0))
    for i in range(10):
        h = 2.0**(-18+i)
        add('skale', Shape(hx=h, hy=h), IDENTITY, Shape(hx=h, hy=h), (h, h/2, 1, 0))
    for i in range(20):
        a = Shape(kind=2, count=3+i%6, points=OCTAGON[:3+i%6], radius=i/256)
        add('wspolny', a, (i/8, -i/16, *ROTATIONS[i%4]),
            a, (i/8, -i/16, *ROTATIONS[i%4]))
    if len(rows) != BASE_COUNT:
        raise ValueError('Changed base population')
    for witness in mutation_data()['cases']:
        shapes, transforms = [], []
        for side in ('a', 'b'):
            data = witness[side]
            value = lambda word: number(int(word, 16))
            c, s = map(value, data['local_rotation'])
            shapes.append(Shape(kind=data['kind'], hx=value(data['hx']), hy=value(data['hy']),
                                radius=value(data['radius']), c=c, s=s))
            transforms.append(tuple(map(value, data['transform'])))
        add(witness['category'], shapes[0], transforms[0], shapes[1], transforms[1])
        if rows[-1].id != witness['id']:
            raise ValueError('Mutation witnesses must be appended consecutively')
    if len(rows) != COUNT or len({r.words for r in rows}) != COUNT:
        raise ValueError('Wrong count or duplicate parameters')
    return tuple(rows)


def mutation_data():
    return json.loads(Path(__file__).with_name('mutacje-wiel.json').read_text(encoding='utf-8'))


def read_inputs(path):
    lines = Path(path).read_text(encoding='ascii').splitlines()
    if len(lines) != COUNT:
        raise ValueError(f'Expected {COUNT} polygon inputs, got {len(lines)}')
    rows = []
    witnesses = {c['id']: tuple(c['words']) for c in mutation_data()['cases']}
    for expected, line in zip(parameters(), lines):
        tokens = line.split(' ')
        if (len(tokens) != 81 or tokens[0] != str(expected.id)
                or any(len(t) != 8 or any(c not in '0123456789abcdef' for c in t) for t in tokens[1:])):
            raise ValueError(f'Bad polygon input line {expected.id}')
        words = tuple(int(t, 16) for t in tokens[1:])
        for offset, shape in ((0, expected.a), (40, expected.b)):
            if words[offset] != shape.count or words[offset+35] != bits(shape.radius):
                raise ValueError(f'Unexpected shape/count/radius in case {expected.id}')
            if any(words[offset+1+2*shape.count:offset+17]) or any(words[offset+17+2*shape.count:offset+33]):
                raise ValueError(f'Nonzero unused fields in case {expected.id}')
            validate_shape(words[offset:offset+40], shape, expected.id)
        if words[36:40] != tuple(map(bits, expected.ta)) or words[76:80] != tuple(map(bits, expected.tb)):
            raise ValueError(f'Unexpected transform in case {expected.id}')
        if expected.id in witnesses and words != witnesses[expected.id]:
            raise ValueError(f'Native C constructor differs from mutation witness {expected.id}')
        rows.append(Case(expected.id, expected.category, words))
    if len({r.words for r in rows}) != COUNT:
        raise ValueError('Duplicate materialized input')
    return tuple(rows)


def validate_shape(words, shape, id):
    pass                                                                            

                                                                                       
                                                                                    
       
    values = tuple(map(number, words[1:]))
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f'Nonfinite input in case {id}')
    n = words[0]
    vertices = tuple((values[2*i], values[2*i+1]) for i in range(n))
    if shape.kind == 2:
        wanted = shape.points
    else:
        wanted = ((-shape.hx, -shape.hy), (shape.hx, -shape.hy),
                  (shape.hx, shape.hy), (-shape.hx, shape.hy))
        if shape.kind == 1:
            c, s = number(bits(shape.c)), number(bits(shape.s))
            wanted = tuple((c*x-s*y+shape.cx, s*x+c*y+shape.cy) for x, y in wanted)
    scale = max(2**-23, *(abs(v) for point in wanted for v in point))
    tolerance = 32*2**-23*scale
    if any(min(math.dist(v, w) for w in wanted) > tolerance for v in vertices) or len(set(vertices)) != n:
        raise ValueError(f'Constructor vertices mismatch in case {id}')
    for i, a in enumerate(vertices):
        b = vertices[(i+1)%n]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        if length == 0 or any(dx*(v[1]-a[1])-dy*(v[0]-a[0]) < -tolerance*length for v in vertices):
            raise ValueError(f'Nonconvex/clockwise input in case {id}')
        nx, ny = values[16+2*i:18+2*i]
        if math.dist((nx, ny), (dy/length, -dx/length)) > 32*2**-23:
            raise ValueError(f'Bad input normal in case {id}')
        cx, cy = values[32:34]
        if dx*(cy-a[1])-dy*(cx-a[0]) < -tolerance*length:
            raise ValueError(f'Centroid outside polygon in case {id}')


def write_inputs(directory, kontrola=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    params = directory / 'przypadki-wiel-parametry.csv'
    params.write_text(''.join(f'{c.id} ' + ' '.join(f'{w:08x}' for w in c.words) + '\n'
                              for c in parameters()), encoding='ascii')
    if kontrola is None:
        return ()                                                                           
    command = [str(kontrola), '--generuj', str(params)]
    started = time.monotonic()
    result = subprocess.run(command,
                            capture_output=True, text=True, encoding='ascii', timeout=20)
    (directory / 'generator-wiel-c.json').write_text(json.dumps({
        'command': command, 'cwd': str(Path.cwd()), 'code': result.returncode,
        'seconds': time.monotonic()-started,
    }, indent=2)+'\n', encoding='utf-8')
    (directory / 'generator-wiel-c-stderr.csv').write_text(result.stderr, encoding='ascii')
    if result.returncode:
        raise ValueError(f'Generator C: code {result.returncode}: {result.stderr}')
    target = directory / 'przypadki-wiel.csv'
    target.write_text(result.stdout, encoding='ascii')
    rows = read_inputs(target)
    (directory / 'przypadki-wiel-stdin.csv').write_text(''.join(
        f'{c.id} ' + ' '.join(map(str, c.words)) + '\n' for c in rows), encoding='ascii')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--katalog', type=Path, default=Path(__file__).resolve().parent)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--kontrola', type=Path)
    mode.add_argument('--parametry-only', action='store_true')
    args = parser.parse_args()
    rows = write_inputs(args.katalog, args.kontrola)
    print(f'Parametry: {COUNT}; gotowe struktury C: {len(rows)}')


if __name__ == '__main__':
    main()
