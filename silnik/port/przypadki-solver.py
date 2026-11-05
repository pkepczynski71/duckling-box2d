pass                                                                               
import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value

g9 = load('solver_contact_inputs', 'przypadki-kontakty.py')
g8 = g9.g8
Case, op, bits, number = g9.Case, g9.op, g9.bits, g9.number
body, shape = g9.body, g9.shape
circle, box, capsule, segment = g9.circle, g9.box, g9.capsule, g9.segment
U32 = (1 << 32) - 1
MANIFEST = json.loads((HERE / 'solver-przypadki.json').read_bytes())
USED = {**g9.USED, 54: 11, 55: 2}
PUBLIC = set(USED) - set(range(41, 46)) - {51, 52, 53}
                                                                           
STAR10 = (
    (0x408e6666, 0x00000000, 0xbe99999a, 0x80000000),
    (0x407c2d89, 0x40045a69, 0xbe88018c, 0xbe0ec351),
    (0x4021c8eb, 0x406a62c4, 0xbe2e826e, 0xbe7cd216),
    (0x3f0950bd, 0x408d5c9b, 0xbd141d90, 0xbe987ae7),
    (0xbfc9fba2, 0x40852575, 0x3dd9de87, 0xbe8f9e56),
    (0xc0552d05, 0x403cdb7a, 0x3e65f148, 0xbe4bb616),
    (0xc08a431a, 0x3f885070, 0x3e9522fc, 0xbd930919),
    (0xc08a431a, 0xbf885070, 0x3e9522fc, 0x3d930919),
    (0xc0552d05, 0xc03cdb7a, 0x3e65f148, 0x3e4bb616),
    (0xbfc9fba2, 0xc0852575, 0x3dd9de87, 0x3e8f9e56),
    (0x3f0950bd, 0xc08d5c9b, 0xbd141d90, 0x3e987ae7),
    (0x4021c8eb, 0xc06a62c4, 0xbe2e826e, 0x3e7cd216),
    (0x407c2d89, 0xc0045a69, 0xbe88018c, 0x3e0ec351),
)

def world(slot=0, mode=1, gravity=(0, -10), speed=400, hertz=30,
          damping=10, push=3, restitution=1, hit=1, warm=1):
    return op(54, slot, mode, *map(bits, (*gravity, speed, hertz, damping,
                                      push, restitution, hit)), warm)

def floor(width=12, y=-.5, owner=0, slot=0, parent=0, **material):
    return [body(parent, owner=owner, kind=0, p=(0, y)),
            shape(slot, owner=owner, parent=parent, geometry=box(h=(width, .5)), **material)]

def separated(count, *, warm=1, mode=1, round_=False, mixed=False):
    rows = [world(warm=warm, mode=mode), *floor(width=max(12, count + 2))]
    for j in range(count):
        x = 2 * j - count + 1
        rows += [body(j + 1, p=(x, .49), v=(.1 * (j % 3), -2 if round_ else -.5)),
                 shape(j + 1, parent=j + 1, geometry=circle(r=.5) if round_ or mixed and j % 2 else box(h=(.4, .5)),
                       friction=.2 + .1 * (j % 3), restitution=.2 * (j % 2), hit=1)]
    return rows

def long_scene(family, n, warm):
    rows = [world(warm=warm)]
    extra = {}
    if family in (1, 2, 9):
        rows += floor(restitution=.7 if family == 1 else 0, friction=.4)
        rows += [body(1, p=(0, 2 if family == 1 else .51 if family == 9 else .49),
                      v=(4 if family == 2 else 0, -.3 if family == 9 else -2)),
                 shape(1, parent=1, geometry=circle(r=.5) if family == 1 else box(h=(.6, .5)),
                       restitution=.7 if family == 1 else 0, friction=.4, hit=1)]
    elif family in (3, 4, 10):
        count = 8 if family == 4 else 2
        rows += floor()
        for j in range(count):
            rows += [body(j + 1, p=(.03 * (j % 2), .49 + j)),
                     shape(j + 1, parent=j + 1, geometry=box(h=(.5, .5)),
                           density=10000 if family == 10 and j == 0 else 1)]
    elif family in (5, 6, 7):
        rows += [body(0, kind=1 if family == 7 else 0, p=(0, -.5),
                      v=(.2, 0) if family == 7 else (0, 0), w=.03 if family == 7 else 0),
                 shape(0, parent=0, geometry=box(h=(12, .5)), rolling=.2 if family == 5 else 0,
                       tangent=1 if family == 6 else 0)]
        for j in range(2):
            rows += [body(j + 1, p=(-3 + 6 * j, .5), w=2 if j == 0 else -2, fixed=j if family == 5 else 0),
                     shape(j + 1, parent=j + 1,
                           geometry=circle(r=.5) if j == 0 else capsule(p1=(-.3, 0), p2=(.3, 0), r=.5),
                           rolling=.3 * j if family == 5 else 0, tangent=-2 * j if family == 6 else 0)]
    elif family == 8:
        rows = separated(3, warm=warm)
    elif family in (11, 12):
        rows += floor(width=8)
        for j in range(1, 4):
            rows += [body(j, p=(-4 + 4 * (j - 1), 1), v=(.3 * (-1 if j == 2 else 1), 0),
                          w=.2 * (j - 2), fixed=int(family == 12 and j == 3)),
                     shape(j, parent=j, geometry=box(h=(.55, .5), c=(.15, .1)))]
        rows += [shape(4, parent=1, geometry=circle((-.6, .2), .2)),
                 shape(5, parent=2, geometry=circle((.6, .2), .2))]
    elif family in (13, 17):
        rows = separated(5 if family == 13 else 69, warm=warm, mixed=family==13)
    elif family == 14:
        rows = [world(warm=warm, gravity=(0, 0)), body(0),
                shape(0, parent=0, geometry=circle(r=4), density=20, category=1, mask=2, hit=1)]
        for j, words in enumerate(STAR10):
            px,py,vx,vy = map(number,words)
            rows += [body(j + 1, p=(px,py), v=(vx,vy)),
                     shape(j + 1, parent=j + 1, geometry=circle(r=.5), category=2, mask=1, hit=1)]
    elif family == 15:
        rows += floor(width=22)
        rows += [body(1, p=(0, .49)), shape(1, parent=1, geometry=box(h=(17, .5)), density=20)]
        for j in range(16):
            rows += [body(j + 2, p=(1.8 * (j - 7.5), 1.48)),
                     shape(j + 2, parent=j + 2, geometry=box(h=(.4, .5)), rolling=.05, restitution=.2)]
    elif family == 16:
        rows += floor(width=4)
        rows += [body(1, p=(0, .09), v=(.2, -1))]
        for j in range(13):
            rows.append(shape(j + 1, parent=1, geometry=circle((.14 * (j - 6), 0), .1),
                              rolling=.1, restitution=.4, hit=1))
        extra[600] = [g8.force(1, kind=4, value=(0, -2))]
    elif family == 18:
        rows = separated(3, warm=warm, round_=True)
        extra[0] = [g9.save(0, 1), g9.event_copy(0), g9.event_copy(1), op(50, 0, 1), op(50, 1)]
        extra[1] = [op(50, 0), op(50, 1)]
        extra[2] = [op(50, 0), op(50, 1), g9.get()]
        extra[600] = [op(18, 0, 1), shape(4, parent=1, geometry=circle(r=.5), hit=1), op(50, 0)]
    steps = 600 if family <= 12 else 1200
    for j in range(steps):
        rows += [g8.step(n=n)]
        rows += extra.get(j, [])
    if family == 18:
        rows += [op(1, 0), op(50, 0), op(50, 1), op(49, 0, 0), op(50, 0)]
    return rows

def short_scene(ident):
    if 109 <= ident <= 113:
        return separated(ident - 108) + [g8.step(n=1)] * 4
    if ident in (114, 115):
        rows = [world(gravity=(0, 0)), *floor(restitution=1, hit=0),
                body(1, p=(-2, .5)), shape(1, parent=1, geometry=box(h=(.5, .5)), restitution=1, hit=1),
                body(2, p=(2, .49)), shape(2, parent=2, geometry=circle(r=.5), restitution=0, hit=0)]
        speeds = [0x3f7fffff, 0x3f800000, 0x3f800001]
        for j in range(6 if ident == 114 else 8):
            for bid, pos in ((1, (-2, .5)), (2, (2, .49))):
                rows += [g9.transform(0, bid, pos), g8.linear(bid, 0, -number(speeds[j % 3]))]
            rows += [g8.angular(1,0)]
            rows += [g8.step(n=1)]
        if ident == 115:rows += [g9.event_copy(), op(50, 0, 1)]
        return rows
    if ident == 116:
        return separated(1, round_=True) + [g8.step(n=4), g8.force(1), g8.step(dt=0, n=4),
                                            g8.step(dt=-0.0, n=4), g8.step(n=4)]
    if ident == 117:
        rows = [world(mode=0, gravity=(0, 0)), body(), body(1, p=(0, .9)),
                shape(geometry=circle(r=.5)), shape(1, parent=1, geometry=circle(r=.5))]
        return rows + [g8.step(dt=-1/60, n=1, raw=True), g9.save(), g8.step(n=1, raw=True),
                       g8.step(dt=-1/60, n=1, raw=True), g8.step(dt=-1/60, n=1)]
    if ident == 118:
        return [world(), g8.step(n=1), *floor(), g8.step(n=1)]
    if ident == 119:
        return separated(1, mode=0) + [g8.step(n=4, raw=True), op(55, 0, 0),
                                       g8.step(n=4, raw=True), op(55, 0, 1), g8.step(n=4, raw=True)]
    if ident == 120:
        return [world(mode=0, hertz=0), *floor(), body(1, p=(0, 1)), shape(1, parent=1),
                g8.step(n=4, raw=True), op(1, 0), world(1, mode=0, hertz=1000),
                body(2, owner=1), shape(2, owner=1, parent=2), g8.step(owner=1, dt=.5, n=4, raw=True)]
    if ident == 121:
        return separated(1) + [g8.step(n=1), g9.save(), g9.event_copy(), op(50, 0),
                               g9.get(), g8.step(n=1), op(50, 0), g8.step(n=1)]
    if ident == 122:
        return separated(2) + [g8.force(1), g8.step(n=1)]
    if ident == 123:
        return separated(1, round_=True) + [world(1), g8.step(n=1), g9.save(), g9.event_copy(),
                  g9.event_copy(1), op(50, 0, 1), g9.get(owner=1), g8.step(n=1), op(18, 0, 1),
                  shape(2, parent=1, geometry=circle(r=.5)), op(1, 0), op(50, 0), g9.get(),
                  op(49, 0, 0), op(50, 0), g9.get(owner=1)]
    if ident == 124:
        return [world(gravity=(0, 0)), body(), body(1), shape(geometry=segment()),
                shape(1, parent=1, geometry=segment()), g8.step(n=1), g8.step(n=1)]
    raise ValueError(ident)

def validate_operation(row):
    if len(row) != 65 or any(type(x) is not int or not 0 <= x <= U32 for x in row):
        raise ValueError('operation words/u32')
    code, *a = row
    if code not in PUBLIC:raise ValueError('PUBLIC10 opcode')
    if any(a[USED[code]:]):raise ValueError('unused words')
    if code < 40:
        g8.validate_operation(row)
    elif code == 40:
        if a[0] > 511 or a[1] > 15 or a[2] > 255 or a[3] not in (0, 1, 2, 3, 4):
            raise ValueError('shape registers/type')
        if any(a[i] > 1 for i in (55, 56, 57, 58)):
            raise ValueError('shape bool')
    elif code in (46, 47, 48, 49, 50):
        if code == 50:
            if a[0] > 3 or a[1] > 1:raise ValueError('copy/mutate')
        elif a[0] > 15:raise ValueError('world register')
    elif code == 54:
        if a[0] > 15 or a[1] > 1 or a[10] > 1:raise ValueError('world register/bool')
        if not a[1] and (not all(math.isfinite(number(x)) for x in a[2:10]) or
                        number(a[4]) <= 0 or any(number(x) < 0 for x in a[5:10])):
            raise ValueError('raw world domain')
    elif a[0] > 15 or a[1] > 1:raise ValueError('warm register/bool')

def cases():
    rows = []
    for m in MANIFEST['przypadki']:
        ident = m['id']
        ops = long_scene(m['rodzina'], m['podkroki'], m['warm']) if ident <= 108 else short_scene(ident)
        rows.append(Case(ident, m['nazwa'], tuple(ops)))
    return tuple(rows)

def verify():
                                                                          
                                                                       
    for item in MANIFEST['przypadki']:
        b,s,c=(item[k] for k in ('maxB','maxS','maxC'))
        cap=lambda n,minimum:max(minimum,1<<(max(1,4*n)-1).bit_length())
        q=32768+3072*b+2048*s+10240*c+27*(cap(c,32)+cap(s,16))
        assert item['qSnapshotBytes']==q,(item['id'],'snapshot envelope')
        assert item['limitWyjsciaNaStrone']==item['opMax']*q
        assert item['limitParyOBS1D']==2*item['opMax']*q
    long_bytes=sum(m['opMax']*m['qSnapshotBytes'] for m in MANIFEST['przypadki'][:108])
    assert MANIFEST['objetosc']['dlugieBytesNaStrone']==long_bytes
    assert MANIFEST['objetosc']['trzyGlowneBytesMax']==3*(long_bytes+
        MANIFEST['objetosc']['krotkieBytesNaStrone']+MANIFEST['objetosc']['componentBytesNaStrone'])
    rows = cases()
    assert len(rows) == 124 and [c.id for c in rows] == list(range(1, 125))
    for c, m in zip(rows, MANIFEST['przypadki']):
        assert 0 < len(c.ops) <= m['opMax'], (c.id, len(c.ops), m['opMax'])
        for row in c.ops:validate_operation(row)
                                                                     
        steps = [r for r in c.ops if r[0] in (31, 32) and not (r[0] == 32 and number(r[2]) < 0)]
        assert len(steps) == m['kroki'], (c.id, len(steps), m['kroki'])
    assert sum(m['kroki'] for m in MANIFEST['przypadki'][:108]) == 86400
    return rows

def encode(rows, duckling=False):
    lines = [f'PORT10 {len(rows)}']
    for c in rows:
        lines.append(f'C {c.id} {len(c.ops)}')
        for seq, (code, *a) in enumerate(c.ops, 1):
            lines.append(f'O {seq} {code} ' + ' '.join(str(v) if duckling else f'{v:08x}' for v in a))
    return '\n'.join(lines) + '\n'

@dataclass(frozen=True)
class Component:
    id: int
    fixture: int
    substeps: int
    warm: int
    fw: tuple
    bodies: tuple
    contacts: tuple
    helpers: tuple
    @property
    def phases(self):
        return ((0, 0), *( (sub, phase) for sub in range(1, self.substeps + 1) for phase in range(1, 6)), (0, 6), (0, 7))

def component_seed(fixture, n, warm, ident):
    fw = tuple(map(bits, (0, -10, 400, 30, 10, 3, 1, 1, 1/60)))
    bodies = []
    contacts = []
    helpers = []
    if fixture == 1:
        helpers = [(0, tuple(map(bits, (-0., 0., 1., -2., 0., -0., 1., 2., 0., 1., -1., 2., 0., 1., 1., 0.)))),
                   (0, (0xbf800000, bits(.25), bits(-.5), bits(.75), 0x3f800001, bits(1), bits(1), bits(1),
                        0x3f7ffffe, bits(0), bits(0), bits(0), bits(1), bits(0), bits(1), bits(0)))]
    elif fixture == 2:
        helpers = [(1, tuple(map(bits, (1., 0., 0., -1., 0., 1., -1., -0., 1., 2., -3., 4., -1., .5, 2., -4.))))]
    elif fixture == 16:
        for unit, counts in ((0, (0, 128, 129, 131064, 131065, 131066, 131067, 131068)),
                             (1, (0, 1, 4, 5, 16, 17, 131064, 131065, 131066, 131067, 131068)),
                             (2, (0, 1, 4, 5, 16, 17, 131064, 131065, 131066, 131067, 131068))):
            helpers += [(2, (count, 0, unit, *([0] * 13))) for count in counts]
    if fixture not in (1, 16):
        for j in range(4):
            inv = 0 if fixture == 3 and j % 2 == 0 or fixture == 4 and j == 0 else 1
            inertia = 0 if fixture == 3 or fixture in (4,11,13) and j % 2 == 0 else 1
            if fixture == 13 and j % 2 == 0:inv = 0
            vx = (-12,12,-8,8)[j] if fixture == 10 else .25 * j
            vy = 2+j if fixture == 9 and j % 2 else -2-j
            if fixture == 13:vy = (-2,-.5,-4,-3)[j]
            bodies.append((j, *map(bits, (inv, inertia, .2, -.3, .1, .02, .03, 1)),
                           0, *map(bits, (vx, vy, 0 if fixture == 13 else .2 * j, 0, 0, 1, 0))))
        for j, color in enumerate((0, 0, 11, 11)):
            a, b = (-1, j) if j < 2 else (j - 2, j)
            sim = [0] * 51
            sim[:5] = [j, a & U32, b, 2*j, 2*j+1]
            sim[5:9] = [0 if a == -1 else bodies[a][1], 0 if a == -1 else bodies[a][2], bodies[b][1], bodies[b][2]]
            sim[9:13] = list(map(bits, (.3, 0 if fixture == 12 else .7, .2 if fixture in (6, 11, 15) else 0, -.5 if j % 2 else .5)))
            sim[13] = 0x10000
            m = [0] * 30
            m[1] = bits(1)
            m[2] = bits(.25 if fixture in (6, 11, 15) else 0)
            m[3] = 1 if j % 2 else 2
            for point in range(m[3]):
                k = 4 + 13 * point
                sep = -.01
                if fixture == 7:sep = ((.001,-.001)[point] if j % 2 == 0 else -0. if j == 1 else 0.)
                if fixture == 8:sep = (-4,-.01,-4,.1)[j]
                m[k:k+13] = [*map(bits, ((-.5 if point == 0 else .5), 0, -.5 if point == 0 else .5, -.5,
                                         -.5 if point == 0 else .5, .5, sep, .5 if fixture in (6, 15) else 0,
                                         -.1 if fixture in (6, 10, 15) else 0, 0, 0)), point + 1, 1]
            sim[21:] = m
            contacts.append((color, j if color == 0 else j - 2, tuple(sim)))
    return Component(ident, fixture, n, warm, fw, tuple(bodies), tuple(contacts), tuple(helpers))

def components():
    return tuple(component_seed(m['fixture'], m['podkroki'], m['warm'], m['id']) for m in MANIFEST['component'])

def encode_components(rows, duckling=False):
    def words(v):return ' '.join(str(x) if duckling else f'{x:08x}' for x in v)
    lines = [f'COMPONENT10 {len(rows)}']
    for c in rows:
        lines.append(f'F {c.id} {c.fixture} {c.substeps} {c.warm} {len(c.bodies)} {len(c.contacts)} {len(c.helpers)} {len(c.phases)}')
        lines.append(f'FW {c.id} ' + words(c.fw))
        lines += [f'FB {c.id} {j} ' + words(v) for j, v in enumerate(c.bodies)]
        lines += [f'FC {c.id} {j} {color} {local} ' + words(v) for j, (color, local, v) in enumerate(c.contacts)]
        lines += [f'FX {c.id} {j} {kind} ' + words(v) for j, (kind, v) in enumerate(c.helpers)]
        lines += [f'FP {c.id} {j} {sub} {phase}' for j, (sub, phase) in enumerate(c.phases)]
    return '\n'.join(lines) + '\n'

def write(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rows = verify()
    comp = components()
    hashes = {};outputs = {}
    for stem, values, encoder in (('przypadki-solver', rows, encode), ('proba-solver', rows[:1], encode),
                                 ('component-solver', comp, encode_components), ('proba-component-solver', comp[:1], encode_components)):
        for decimal in (False, True):
            name = stem + ('-stdin' if decimal else '') + '.csv'
            data = encoder(values, decimal).encode('ascii')
            outputs[name] = data
            hashes[name] = hashlib.sha256(data).hexdigest()
    pin=HERE/'wejscia-solver-sha256.json'
    if pin.is_file() and json.loads(pin.read_bytes())!=hashes:
        raise ValueError('frozen 10/1 input hashes changed')
    for name,data in outputs.items():(directory / name).write_bytes(data)
    (directory / 'wejscia-solver-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n', encoding='ascii')
    return {'N':len(rows), 'component':len(comp), 'steps':86456, 'phases':sum(len(c.phases) for c in comp),
            'operations':[len(c.ops) for c in rows], 'sha256':hashes}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--katalog', type=Path, default=HERE)
    args = parser.parse_args()
    print(json.dumps(write(args.katalog)))
