pass                                                                                  
import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import subprocess

from przypadki import bits, number

COUNT = 70
DT_WORDS = (0x3c888889, 0x3d088889, 0x3b888889)
DT = tuple(map(number, DT_WORDS))
ROTATIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
INPUT_FIELDS = (
    'gravity.x', 'gravity.y', 'maximumLinearSpeed', 'timeStep', 'subStepCount', 'stepCount',
    'position.x', 'position.y', 'rotation.c', 'rotation.s', 'linearVelocity.x', 'linearVelocity.y',
    'angularVelocity', 'linearDamping', 'angularDamping', 'gravityScale', 'fixedRotation',
    'allowFastRotation', 'shapeCount',
    *(f'shape[{i}].{f}' for i in range(2) for f in ('type', 'density', *(f'p{j}' for j in range(7)))),
    'commandCount',
    *(f'command[{i}].{f}' for i in range(8) for f in ('step', 'type', 'a', 'b', 'c', 'd')))


def f32(value):
    return number(bits(value))


def angular_limit(dt):
                                                                                  
    return f32(f32(.25*f32(math.pi))*f32(1/dt))


def constants():
    return (*DT_WORDS, *(bits(angular_limit(dt)) for dt in DT))


def circle(density=1, center=(0, 0), radius=1):
    return (0, *map(bits, (density, *center, radius, 0, 0, 0, 0)))


def box(density=1, half=(1, .5), center=(0, 0), rotation=(1, 0), radius=0):
    return (1, *map(bits, (density, *half, *center, *rotation, radius)))


def command(step, kind, a=0, b=0, c=0, d=0):
    return (step, kind, *map(bits, (a, b, c, d)))


@dataclass(frozen=True)
class Case:
    id: int
    category: str
    words: tuple


def cases():
    rows = []

    def add(category, gravity=(0, 0), maximum=400, dt=DT[0], sub=4, steps=600,
            position=(0, 0), rotation=(1, 0), velocity=(0, 0), angular=0,
            damping=(0, 0), scale=1, fixed=0, fast=0, shapes=None, commands=()):
        shapes = shapes or (circle(),)
        words = (*map(bits, (*gravity, maximum, dt)), sub, steps,
                 *map(bits, (*position, *rotation, *velocity, angular, *damping, scale)),
                 fixed, fast, len(shapes), *shapes[0],
                 *(shapes[1] if len(shapes) == 2 else (0,)*9), len(commands),
                 *(v for cmd in commands for v in cmd), *((0,)*(6*(8-len(commands)))))
        validate(words)
        rows.append(Case(len(rows)+1, category, words))

    for i, rotation in enumerate(ROTATIONS):
        add('spoczynek', position=(i/8, -i/4), rotation=rotation,
            shapes=(box(density=1+i/4),))
    for i, dt in enumerate(DT):
        for sub in (1, 4, 8):
            add('grawitacja', gravity=(.25*i, -10), dt=dt, sub=sub,
                velocity=(.5, -.25), position=(1, -2), shapes=(box(),))
    for i in range(6):
        add('tlumienie', steps=240, velocity=(3, -4), angular=2,
            gravity=(.25, -1) if i >= 3 else (0, 0),
            damping=((.125, 0), (0, .25), (.5, .75))[i % 3], sub=(1, 4, 8)[i % 3])
    for scale in (0, -1, 2.5):
        add('skala-grawitacji', gravity=(1, -2), scale=scale, velocity=(.125, .25))
    for i in range(4):
        add('staly-obrot', steps=300, fixed=1, rotation=ROTATIONS[i],
            velocity=(.25, -.5), shapes=(box(center=(.25, -.125)),),
            commands=(command(1, 2, 5), command(150, 5, -3), command(300, 3, 1, 2, 3, 4)))
    for maximum in (2, 400):
        for delta in (-1, 0, 1):
            add('prog-liniowy', steps=60, maximum=maximum,
                velocity=(number(bits(maximum)+delta), 0), sub=8)
    for sub in (1, 8):
        for fast in (0, 1):
            for delta in (-1, 0, 1):
                add('prog-obrotowy', steps=60, sub=sub, fast=fast,
                    angular=number(bits(angular_limit(DT[0]))+delta))
    offset_shapes = (
        (circle(center=(.5, -.25)),),
        (box(center=(.25, -.5), rotation=(0, 1)),),
        (box(center=(-.5, .25), rotation=(0, -1), radius=.125),),
        (circle(density=.75, center=(.375, -.125), radius=.7),
         box(density=2.3, half=(.65, .35), center=(-.2, .45), rotation=(0, 1))),
        (box(density=2.3, half=(.65, .35), center=(-.2, .45), rotation=(0, 1)),
         circle(density=.75, center=(.375, -.125), radius=.7)),
        (box(density=.3, center=(.3, -.7), radius=.2),
         box(density=3.1, half=(.4, .6), center=(-.6, .2), rotation=(-1, 0))))
    for i, shapes in enumerate(offset_shapes):
        add('srodek-masy', shapes=shapes, angular=.375+i/16, velocity=(.5, -.25),
            rotation=ROTATIONS[i % 4], gravity=(.125, -.25), sub=(1, 4, 8)[i % 3])
    for kind in range(6):
        args = (1.25, -.5, 2, -1) if kind in (0, 3) else (1.25, -.5, 0, 0) if kind in (1, 4) else (1.25, 0, 0, 0)
        add('polecenia', shapes=(box(density=2),), commands=tuple(
            command(step, kind, *args) for step in (1, 300, 600)))
    add('polecenia', shapes=(box(),), commands=(command(1, 1, 2**24),
        command(1, 1, 1), command(1, 1, -2**24), command(300, 4, .125, -.25),
        command(600, 0, 1, 2, 3, -4)))
    add('polecenia', maximum=2, commands=(command(1, 4, 10000, -20000),
        command(300, 5, 10000), command(600, 4, -20000, 10000)))
    for i, magnitude in enumerate((2**-12, 2**-8, 2**12, 2**16)):
        add('wspolrzedne', steps=300, position=(magnitude, -magnitude),
            velocity=(.125, -.0625), rotation=ROTATIONS[i], sub=(1, 4, 8, 4)[i],
            shapes=(box(half=(.25, .5)),))
    for i in range(4):
        add('polaczenia', steps=400, dt=DT[i % 3], sub=(1, 4, 8, 8)[i],
            gravity=(.5, -3), scale=(-.5, 0, 2, 1)[i], damping=(.125, .25),
            maximum=3, angular=-60, fast=i % 2, shapes=offset_shapes[3],
            commands=(command(1, 0, 7, -2, 3, -4), command(200, 3, -5, 2, -1, 3),
                      command(400, 5, -8)))
                                                                               
    add('staly-obrot-w0', fixed=1, angular=.75, velocity=(.125, -.25),
        shapes=(box(center=(.25, -.125)),),
        commands=(command(1, 2, 5), command(300, 5, -3)))
    add('osiem-polecen', steps=120, shapes=(box(),), commands=(
        command(1, 0, 1, .5, 1, 2), command(1, 1, .5, -.25),
        command(30, 2, .75), command(30, 3, .25, -.5, 1, -1),
        command(60, 4, -.125, .25), command(60, 5, .5),
        command(60, 0, -.25, .5, -1, 2), command(120, 2, -.5)))
    add('kwadrat-limitu-zero', steps=8, maximum=2**-80, velocity=(2**-81, 0),
        shapes=(box(),))
    add('kwadrat-limitu-zero-impuls', steps=8, maximum=2**-80,
        velocity=(2**-81, 0), shapes=(box(),), commands=(command(1, 4, 2**-81),))
    if len(rows) != COUNT or len({c.words for c in rows}) != COUNT:
        raise ValueError('Wrong/duplicate motion population')
    if sum(c.words[5] for c in rows) > 30000:
        raise ValueError('Too many S rows')
    return tuple(rows)


def validate(w):
    if len(w) != 86 or any(type(v) is not int or not 0 <= v < 2**32 for v in w):
        raise ValueError('Expected 86 u32')
    integers = {4, 5, 16, 17, 18, 19, 28, 37,
                *(38+6*i+j for i in range(8) for j in (0, 1))}
    if any(not math.isfinite(number(v)) for i, v in enumerate(w) if i not in integers):
        raise ValueError('Nonfinite input')
    if not (1 <= w[4] <= 8 and 1 <= w[5] <= 600 and w[16] <= 1 and w[17] <= 1
            and 1 <= w[18] <= 2 and w[37] <= 8 and number(w[2]) > 0 and number(w[3]) > 0
            and number(w[13]) >= 0 and number(w[14]) >= 0):
        raise ValueError('Bad body/world range')
    if abs(math.hypot(*map(number, w[8:10]))-1) > 2**-20:
        raise ValueError('Bad rotation')
    for i in range(2):
        s = w[19+9*i:28+9*i]
        if i >= w[18]:
            if any(s):
                raise ValueError('Nonzero unused shape')
            continue
        if s[0] not in (0, 1) or number(s[1]) <= 0:
            raise ValueError('Bad shape type/density')
        if s[0] == 0:
            if number(s[4]) <= 0 or any(s[5:]):
                raise ValueError('Bad circle')
        elif (number(s[2]) <= 0 or number(s[3]) <= 0 or number(s[8]) < 0
              or abs(math.hypot(*map(number, s[6:8]))-1) > 2**-20):
            raise ValueError('Bad box')
    for i in range(8):
        cmd = w[38+6*i:44+6*i]
        if i >= w[37]:
            if any(cmd):
                raise ValueError('Nonzero unused command')
            continue
        if not 1 <= cmd[0] <= w[5] or cmd[1] > 5:
            raise ValueError('Bad command step/type')
        if cmd[1] in (1, 4) and any(cmd[4:]) or cmd[1] in (2, 5) and any(cmd[3:]):
            raise ValueError('Nonzero unused command fields')


def read_inputs(path):
    lines = Path(path).read_text(encoding='ascii').splitlines()
    expected = cases()
    if len(lines) != COUNT:
        raise ValueError(f'Expected {COUNT} motion inputs, got {len(lines)}')
    for case, line in zip(expected, lines):
        tokens = line.split(' ')
        if (len(tokens) != 87 or tokens[0] != str(case.id)
                or any(len(t) != 8 or any(c not in '0123456789abcdef' for c in t) for t in tokens[1:])):
            raise ValueError(f'Bad input format: case {case.id}')
        words = tuple(int(t, 16) for t in tokens[1:])
        validate(words)
        if words != case.words:
            raise ValueError(f'Input differs from recipe: case {case.id}')
    return expected


def write_inputs(directory, kontrola=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if kontrola is not None:
        result = subprocess.run([str(kontrola), '--stale'], capture_output=True,
                                text=True, encoding='ascii', timeout=15)
        (directory / 'stale-ruch-c.csv').write_text(result.stdout, encoding='ascii')
        (directory / 'stale-ruch-c-stderr.csv').write_text(result.stderr, encoding='ascii')
        if result.returncode or result.stdout.strip() != ' '.join(f'{v:08x}' for v in constants()):
            raise ValueError(f'Native C f32 constants disagree (code {result.returncode}): {result.stdout!r}')
    rows = cases()
    for suffix, render in (('.csv', lambda v: f'{v:08x}'), ('-stdin.csv', str)):
        (directory / ('przypadki-ruch'+suffix)).write_text(''.join(
            f'{c.id} '+ ' '.join(map(render, c.words))+'\n' for c in rows), encoding='ascii', newline='\n')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--katalog', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--kontrola', type=Path)
    args = parser.parse_args()
    rows = write_inputs(args.katalog, args.kontrola)
    print(f'Ruch: {len(rows)} przypadkow; S: {sum((c.words[5] for c in rows))}; stale C: {('zweryfikowane' if args.kontrola else 'do weryfikacji w CI')}')


if __name__ == '__main__':
    main()
