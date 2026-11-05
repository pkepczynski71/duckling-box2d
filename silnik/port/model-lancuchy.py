pass                                                                     

                                                                                
                                                                           
   
from collections import Counter
import json
import math
from pathlib import Path
import re
import struct
import hashlib
import importlib.util
import sys
from collections import defaultdict

HERE = Path(__file__).resolve().parent
H = re.compile(r'[0-9a-f]{8}\Z')
D = re.compile(r'(?:0|[1-9][0-9]*)\Z')
SCHEMA = {'E13A': (3, 64), 'A13': (2, 2), 'KI13': (2, 7),
          'D13A': (2, 9), 'K13A': (2, 7), 'T13A': (3, 1),
          'V13A': (4, 10), 'ZA13': (2, 8), 'GA': (1, 64),
          'GR13': (3, 4), 'G': (4, 0), 'CASE': (2, 0),
          'ENDCASE': (1, 0), 'END': (1, 0), 'GUARD13A': (1, 0)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def f32(value):
    try:
        return struct.unpack('<f', struct.pack('<f', value))[0]
    except OverflowError:
        return math.copysign(math.inf, value)


def number(word):
    return struct.unpack('<f', struct.pack('<I', word))[0]


def bits(value):
    return struct.unpack('<I', struct.pack('<f', f32(value)))[0]


def add(a, b):
    return f32(a + b)


def mul(a, b):
    return f32(a * b)


def sub(a, b):
    return f32(a - b)


def transform(words, point):
    px, py, c, s = map(number, words)
    x, y = map(number, point)
    return (bits(add(sub(mul(c, x), mul(s, y)), px)),
            bits(add(add(mul(s, x), mul(c, y)), py)))


def valid_rotation(words):
    c, s = map(number, words)
    qq = add(mul(s, s), mul(c, c))
    return sub(1., f32(.0006)) < qq < add(1., f32(.0006))


def relative_transform(a, b):
    ax, ay, ac, ass = map(number, a)
    bx, by, bc, bs = map(number, b)
    dx, dy = sub(bx, ax), sub(by, ay)
    return tuple(map(bits, (add(mul(ac, dx), mul(ass, dy)),
                            add(mul(-ass, dx), mul(ac, dy)),
                            add(mul(ac, bc), mul(ass, bs)),
                            sub(mul(ac, bs), mul(ass, bc)))))


def parse(line):
    if isinstance(line, bytes):
        line = line.decode('ascii')
    require(line.endswith('\n') and not line.endswith('\r\n'), 'output must end in LF')
    line = line[:-1]
    require(line and all(32 <= ord(c) <= 126 for c in line), 'output ASCII/empty/control')
    tokens = line.split(' ')
    require(all(tokens), 'output spacing')
    tag = tokens[0]
    if tag == 'PORT13A':
        require(len(tokens) == 3 and tokens[1] in ('R', 'D'), 'PORT13A header')
        require(bool(D.fullmatch(tokens[2])), 'header canonical N')
        return tag, (tokens[1], int(tokens[2]))
    if tag == 'P13A':
        require(len(tokens) >= 5 and bool(H.fullmatch(tokens[3])), 'P13A count')
        count = int(tokens[3], 16)
        require(count <= 8, 'P13A count range')
        prefix, payload = 2, 2 + 2 * count
    else:
        require(tag in SCHEMA, 'unexpected tag ' + tag)
        prefix, payload = SCHEMA[tag]
    require(len(tokens) == 1 + prefix + payload, tag + ' arity')
    require(all(D.fullmatch(t) for t in tokens[1:1 + prefix]), tag + ' canonical D')
    require(all(H.fullmatch(t) for t in tokens[1 + prefix:]), tag + ' canonical H8')
    values = tuple(int(t) for t in tokens[1:1 + prefix])
    values += tuple(int(t, 16) for t in tokens[1 + prefix:])
    require(all(0 <= v <= 0xffffffff for v in values), tag + ' u32 range')
    return tag, values


def decode_input(data, decimal=False):
    pass                                                                           
    lines = data.decode('ascii').splitlines()
    first = lines.pop(0).split(' ')
    guard = first[0] == 'GUARD13A'
    if guard:
        require(first == ['GUARD13A', '1'], 'input guard N')
        g = tuple(map(int, lines.pop(0).split(' ')[1:]))
        require(len(g) == 4 and g[0] == 1, 'input G')
        ga = lines.pop(0).split(' ')
        require(ga[:2] == ['GA', '1'] and len(ga) == 66, 'input GA')
        ga = tuple(int(t, 10 if decimal else 16) for t in ga[2:])
        header = ('GUARD13A', (1,))
        cases = [(1, g[3])]
    else:
        require(len(first) == 3 and first[0] == 'PORT13A' and first[1] in ('R', 'D'), 'input header')
        require(1 <= int(first[2]) <= 128, 'input N')
        header = ('PORT13A', (first[1], int(first[2])))
        g = ga = None
        cases = []
    result = []
    while lines or guard and not result:
        if guard:
            ident, count = cases[0]
        else:
            case = lines.pop(0).split(' ')
            require(len(case) == 3 and case[0] == 'C', 'input C')
            ident, count = map(int, case[1:])
        operations = []
        for _ in range(count):
            op = lines.pop(0).split(' ')
            require(len(op) == 67 and op[0] == 'O', 'input O')
            operations.append((int(op[1]), int(op[2]),
                               tuple(int(t, 10 if decimal else 16) for t in op[3:])))
        result.append((ident, operations))
        if guard:
            break
    require(not lines, 'input trailing rows')
    require([c[0] for c in result] == list(range(1, header[1][-1] + 1)), 'input cases/N')
    return header, result, g, ga


def checked_status(kind, a):
    pass                                                                          
    if not a[0]:
        return 0, 0
    radii = [2, 24] if kind == 0 else [2]
    transforms = [19, 41] if kind == 0 else [23] if kind == 2 else []
    for i in radii:
        radius = number(a[i])
        if not math.isfinite(radius) or radius < 0:
            return 5, 0
    for i in transforms:
        if not all(math.isfinite(number(v)) for v in a[i:i + 4]) or not valid_rotation(a[i + 2:i + 4]):
            return 5, 0
    if kind == 0:
        if a[46] > 3:
            return 5, 82
                                                                         
        if 1 <= a[1] <= 8 and 1 <= a[23] <= 8:
            for j in range(a[46]):
                if a[47 + j] >= a[1] or a[50 + j] >= a[23]:
                    return 5, 82
    proxies = [(1, 3), (23, 25)] if kind == 0 else [(1, 3)]
    for n, points in proxies:
        if not 1 <= a[n] <= 8:
            return 4, 0
        if not all(math.isfinite(number(v)) for v in a[points:points + 2 * a[n]]):
            return 4, 0
    return 0, 0


def cache_check(cache, a, label):
    require(len(cache) == 7 and cache[0] <= 3 and all(v <= 255 for v in cache[1:]), label + ' physical cache')
    for j in range(cache[0]):
        require(cache[1 + j] < a[1] and cache[4 + j] < a[23], label + ' active cache index')


def check_operation(records, ident, seq, kind, a, profile='R', history=None, memory='jawna'):
    pass                                                                    
    require(len(a) == 64 and kind in (0, 1, 2), 'operation kind/64 words')
    require(records and records[0] == ('E13A', (ident, seq, kind, *a)), 'exact E13A/input echo')
    effective = list(a)
    if kind == 0 and memory == 'ciepla' and seq > 1:
        require(tuple(a[46:53]) == (0,) * 7 and history is not None, 'warm history source/unused seed')
        effective[46:53] = history
    status, reason = checked_status(kind, effective)
    require(len(records) >= 3 and records[1] == ('A13', (ident, seq, status, reason)), 'A13 preflight/status/reason')
    tags = Counter(t for t, _ in records)
    counted = tuple(tags[t] for t in ('E13A', 'A13', 'KI13', 'D13A', 'K13A', 'P13A', 'T13A', 'V13A'))
    require(records[-1] == ('ZA13', (ident, seq, *counted)), 'ZA13 exact counts')
    for tag, values in records:
        require(values[:2] == (ident, seq), tag + ' id/seq')
    if status:
        require([t for t, _ in records] == ['E13A', 'A13', 'ZA13'], 'refused operation emitted a result')
        if kind == 0 and memory == 'ciepla' and seq == 1:
            return tuple(a[46:53])
        return history
    if kind:
        require([t for t, _ in records] == ['E13A', 'A13', 'P13A', 'ZA13'], 'proxy order/completeness')
        count = min(a[1], 8)
        expected = [count, a[2]]
        for j in range(count):
            point = a[3 + 2 * j:5 + 2 * j]
            expected.extend(transform(a[23:27], point) if kind == 2 else point)
        require(records[2][1] == (ident, seq, *expected), 'proxy count/radius/value/offset order')
        return history
    require([t for t, _ in records[:5]] == ['E13A', 'A13', 'KI13', 'D13A', 'K13A'], 'distance result order')
    require(tags['KI13'] == tags['D13A'] == tags['K13A'] == 1 and tags['P13A'] == 0, 'distance multiplicity')
    seed = tuple(a[46:53])
    if memory == 'ciepla' and seq > 1:
        require(seed == (0,) * 7 and history is not None, 'warm history source/unused seed')
        seed = history
    elif memory == 'zimna':
        require(seed == (0,) * 7, 'cold seed must be zero')
    incoming = records[2][1][2:]
    output = records[3][1][2:]
    outgoing = records[4][1][2:]
    require(incoming == seed, 'KI13 own explicit/warm/cold source')
    cache_check(incoming, a, 'KI13')
    cache_check(outgoing, a, 'K13A')
    require(all(math.isfinite(number(v)) for v in output[:7]), 'distance defined fields finite')
    require(number(output[6]) >= 0 and output[7] <= 20 and output[8] <= 23, 'distance/counters bounds')
    early = output[7] == 0
    if early:
        require(output[4:7] == (0, 0, 0) and output[8] == 0, 'early-return output zero counters/normal/distance')
        require(outgoing == incoming, 'early-return must preserve all cache words')
    else:
        for j in range(outgoing[0], 3):
            require(outgoing[1 + j] == incoming[1 + j] and outgoing[4 + j] == incoming[4 + j], 'inactive cache canary changed')
    trace = []
    relative = relative_transform(a[19:23], a[41:45])
    pos = 5
    while pos < len(records) - 1:
        tag, values = records[pos]
        require(tag == 'T13A' and values[2] == len(trace) and 1 <= values[3] <= 3, 'trace index/count/order')
        count = values[3]
        vertices = []
        pos += 1
        for j in range(count):
            require(pos < len(records) - 1, 'truncated trace')
            tag, vertex = records[pos]
            require(tag == 'V13A' and vertex[:4] == (ident, seq, len(trace), j), 'trace vertex order/count')
            v = vertex[4:]
            require(v[0] in (0, 1) and (v[0] or v[7] == 0), 'defined(a)/masked +0')
            require(v[8] < a[1] and v[9] < a[23], 'trace active support index')
            require(v[5:7] == (bits(sub(number(v[1]), number(v[3]))), bits(sub(number(v[2]), number(v[4])))), 'trace w=wA-wB')
            require(v[1:3] == tuple(a[3 + 2 * v[8]:5 + 2 * v[8]]), 'trace wA/point index')
            require(v[3:5] == transform(relative, a[25 + 2 * v[9]:27 + 2 * v[9]]), 'trace local wB/point index')
            vertices.append(v)
            pos += 1
        trace.append(vertices)
    require(a[53] <= 23 and len(trace) <= a[53], 'trace capacity')
    if not a[54]:
        require(a[53] == 0 and not trace, 'NULL trace emitted slots')
    elif a[53]:
        require(bool(trace), 'missing initial trace slot')
        if profile == 'D' and early and incoming[0] <= 2:
            require(len(trace) >= min(2, a[53]), 'missing D afterSolve before degenerate return')
    if profile == 'R':
        require(len(trace) == int(bool(a[54] and a[53])), 'R initial slot completeness')
    elif not early:
        require(len(trace) == (min(a[53], output[7] + 2) if a[54] else 0), 'D initial/afterSolve/final slot completeness')
    if not early:
        require(output[8] == len(trace), 'simplexCount normal-return actual slots')
    if trace:
        initial = trace[0]
        require(len(initial) == max(1, incoming[0]), 'initial cache/simplex count')
        for j, v in enumerate(initial):
            pair = (incoming[1 + j], incoming[4 + j]) if incoming[0] else (0, 0)
            require(v[0] == 1 and v[7] == (0xbf800000 if incoming[0] else 0x3f800000) and v[8:] == pair, 'initial defined(a)/weight/cache indices')
        for i, vertices in enumerate(trace[1:], 1):
                                                                              
                                                                             
            final_at_limit = not early and output[7] == 20 and i == len(trace) - 1 and len(trace) == output[8]
            if not final_at_limit:
                require(all(v[0] == 1 for v in vertices), 'afterSolve/duplicate erased old defined(a)')
    return outgoing


def validate(data, expected_input, decimal=False):
    header, cases, g, ga = decode_input(expected_input, decimal)
    records = [parse(line) for line in data.splitlines(keepends=True)]
    require(records and records[0] == header, 'output/input header')
    pos = 1
    guard = header[0] == 'GUARD13A'
    if guard:
        require(g[1] in (0, 100, 101, 102, 103), 'GUARD13A helper kind')
        require(records[pos:pos + 2] == [('G', g), ('GA', (1, *ga))], 'exact G/GA echo')
        pos += 2
    descriptors = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    manifest = {r['id']: r for r in descriptors['przypadki'] if r['profil'] == 'PORT13A'}
    calls = 0
    for ident, operations in cases:
        require(pos < len(records) and records[pos] == ('CASE', (ident, len(operations))), 'CASE/input opCount')
        pos += 1
        history = None
        for seq, kind, a in operations:
            start = pos
            while pos < len(records) and records[pos][0] != 'ZA13':
                pos += 1
            require(pos < len(records), 'missing ZA13/truncated operation')
            pos += 1
            history = check_operation(records[start:pos], ident, seq, kind, a,
                                      header[1][0] if not guard else 'R', history,
                                      manifest[ident]['pamiec'] if not guard else 'jawna')
            calls += 1
        if guard and g[1] != 0:
            status = checked_status(g[1] - 100, ga)[0] if g[1] in (100, 101, 102) else 0
            value = (2, 3) if g[1] == 103 else (0, 0)
            expected = ('GR13', (1, 0, g[1], status, int(status == 0), *value))
            require(pos < len(records) and records[pos] == expected, 'GR13 helper/preflight/copy result')
            pos += 1
        require(pos < len(records) and records[pos] == ('ENDCASE', (ident,)), 'ENDCASE')
        pos += 1
    require(records[pos:] == [('END', (len(cases),))], 'global END/EOF/trailing output')
    return {'cases': len(cases), 'calls': calls, 'tags': dict(Counter(t for t, _ in records)), 'validated': True}


def projection(data):
    pass                                                                            
    result = []
    for line in data.splitlines(keepends=True):
        tag, values = parse(line)
        if tag in ('T13A', 'V13A', 'ZA13'):
            continue
        if tag == 'PORT13A':
            values = ('PHYSICS', values[1])
        if tag == 'D13A':
            values = values[:-1]
        result.append((tag, values))
    return result


check = validate
validate_stream = validate


                                                                          
                                                                             
SCHEMA13B = {
    'PORT13B': (1, 0), 'GUARD13B': (1, 0), 'E13B': (3, 64),
    'EP13B': (3, 2), 'EU13B': (3, 6), 'A13': (2, 2),
    'CN13': (3, 8), 'V13': (3, 2), 'CQ13': (3, 19),
    'QL13': (4, 8), 'CH13': (4, 5), 'CI13': (5, 8),
    'CM13': (5, 6), 'CS13': (4, 9), 'BH13': (4, 1),
    'CG13': (4, 6), 'PC13': (3, 10), 'COPY13': (4, 0),
    'CV13': (4, 14), 'CE13': (5, 8), 'ENDCOPY13': (4, 0),
    'I13': (2, 6), 'Z13': (2, 17), 'GR13': (3, 4),
    'G': (4, 0), 'GA': (1, 64), 'CASE': (2, 0),
    'ENDCASE': (1, 0), 'END': (1, 0),
}
PRIVATE13B = frozenset(('X P T F U H Y DN RT JW I8 RQ CP CF CT CA CS GB CB BL9 '
    'IP IF IS IL EB EE0 EE1 EN9 TASK I9 W10 CX10 SB10 PK10 SC10 BV10 I10 '
    'WS11 BS11 SS11 SD11 SM11 AB11 TR11 SP11 SF11 BP11 BF11 I11 NP12 IP12 '
    'CH13 CI13 CM13 BH13 IP13 CG13 I13').split())


def parse13b(line):
    pass                                                                         
    if isinstance(line, bytes):
        line = line.decode('ascii')
    require(line.endswith('\n') and not line.endswith('\r\n'), '13b output LF')
    require(line[:-1] and all(32 <= ord(c) <= 126 for c in line[:-1]), '13b ASCII')
    tokens = line[:-1].split(' ')
    require(all(tokens), '13b output spacing')
    tag = tokens[0]
    if tag == 'IP13':
        require(len(tokens) >= 6 and H.fullmatch(tokens[5]), 'IP13 freeCount')
        count = int(tokens[5], 16)
        require(count <= 16, 'IP13 pool population')
        prefix, payload = 3, 2 + count
    else:
        require(tag in SCHEMA13B, 'unknown NEW 13b tag ' + tag)
        prefix, payload = SCHEMA13B[tag]
    require(len(tokens) == 1 + prefix + payload, tag + ' arity')
    require(all(D.fullmatch(t) for t in tokens[1:1 + prefix]), tag + ' canonical D')
    require(all(H.fullmatch(t) for t in tokens[1 + prefix:]), tag + ' canonical H8')
    values = tuple(int(t) for t in tokens[1:1 + prefix])
    values += tuple(int(t, 16) for t in tokens[1 + prefix:])
    require(all(v <= 0xffffffff for v in values), tag + ' u32')
    return tag, values


def projection13b_line(line):
    pass                                                                    
    require(isinstance(line, bytes) and line.endswith(b'\n'), 'projection bytes/LF')
    tag = line.split(b' ', 1)[0].decode('ascii')
    if tag in PRIVATE13B:
        return None
    if tag == 'WS12':
        tokens = line[:-1].split(b' ')
                                                     
        require(len(tokens) == 15, 'WS12 arity before projection')
        tokens[7:10] = [b'00000000'] * 3
        return b' '.join(tokens) + b'\n'
    return line


def distance_predicate13b(a, b):
    pass                                                                    
    ax, ay = map(number, a)
    bx, by = map(number, b)
    dx, dy = sub(bx, ax), sub(by, ay)
    xx, yy = mul(dx, dx), mul(dy, dy)
    d2 = add(xx, yy)
    slop2 = mul(f32(.005), f32(.005))
    values = (dx, dy, xx, yy, d2)
    return {'H': [f'{bits(v):08x}' for v in values],
            'finite': [math.isfinite(v) for v in values],
            'slop2H': f'{bits(slop2):08x}',
            'above': d2 > slop2, 'equal': d2 == slop2}


def orient_predicate13b(a, b, c):
    ax, ay = map(number, a)
    bx, by = map(number, b)
    cx, cy = map(number, c)
    dx, dy, ex, ey = sub(bx, ax), sub(by, ay), sub(cx, ax), sub(cy, ay)
    left, right = mul(dx, ey), mul(dy, ex)
    value = sub(left, right)
    values = (dx, dy, ex, ey, left, right, value)
    return {'H': [f'{bits(v):08x}' for v in values],
            'finite': [math.isfinite(v) for v in values],
            'sign': int(value > 0) - int(value < 0)}


def edge_predicate13b(a, b, c, d, adjacent):
    pass                                                                     
    orientations = [orient_predicate13b(*t) for t in
                    ((a, b, c), (a, b, d), (c, d, a), (c, d, b))]
    signs = [r['sign'] for r in orientations]
    af, bf, cf, df = [tuple(map(number, p)) for p in (a, b, c, d)]
    def within(p, q, r):
        return all(min(x, y) <= z <= max(x, y) for x, y, z in zip(p, q, r))
    on = [signs[0] == 0 and within(af, bf, cf),
          signs[1] == 0 and within(af, bf, df),
          signs[2] == 0 and within(cf, df, af),
          signs[3] == 0 and within(cf, df, bf)]
    proper = ((signs[0] < 0 < signs[1] or signs[1] < 0 < signs[0]) and
              (signs[2] < 0 < signs[3] or signs[3] < 0 < signs[2]))
    axis = int(abs(sub(bf[0], af[0])) < abs(sub(bf[1], af[1])))
    lo = max(min(af[axis], bf[axis]), min(cf[axis], df[axis]))
    hi = min(max(af[axis], bf[axis]), max(cf[axis], df[axis]))
    collinear = all(s == 0 for s in signs)
    overlap = collinear and hi > lo
    rejected = overlap if adjacent else proper or any(on)
    return {'orientations': orientations, 'adjacent': adjacent, 'axis': axis,
            'collinear': collinear, 'positive_overlap': overlap,
            'proper': proper, 'on_segment': on,
            'finite': all(all(r['finite']) for r in orientations),
            'rejected': rejected,
            'cause': ('adjacent_overlap' if adjacent else
                      'proper_cross' if proper else 'collinear' if collinear else 'touch')
                     if rejected else None}


def geometry_predicates13b(points, closed=False):
    pass                                                               

                                                                         
                                                                         
       
    require(type(closed) is bool, 'closed bool')
    require(len(points) <= 128 and all(len(p) == 2 and all(
        type(w) is int and 0 <= w <= 0xffffffff for w in p) for p in points),
        'physical point words')
    pairs, edges, errors = [], [], []
    if len(points) < 4:
        errors.append({'kind': 'count', 'status': 4, 'reason': 84})
    for i, point in enumerate(points):
        if not all(math.isfinite(number(w)) for w in point):
            errors.append({'kind': 'point_finite', 'i': i, 'status': 4, 'reason': 84})
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            r = {'i': i, 'j': j, **distance_predicate13b(points[i], points[j])}
            pairs.append(r)
            if not all(r['finite']) or not r['above']:
                errors.append({'kind': 'distance', 'i': i, 'j': j,
                               'status': 4, 'reason': 84})
    count = len(points) if closed else max(0, len(points) - 1)
    for i in range(count):
        for j in range(i + 1, count):
            adjacent = j == i + 1 or closed and i == 0 and j == count - 1
            r = {'i': i, 'j': j, **edge_predicate13b(
                points[i], points[(i + 1) % len(points)],
                points[j], points[(j + 1) % len(points)], adjacent)}
            edges.append(r)
            if not r['finite']:
                errors.append({'kind': 'orient_finite', 'i': i, 'j': j,
                               'status': 4, 'reason': 84})
            elif r['rejected']:
                errors.append({'kind': r['cause'], 'i': i, 'j': j,
                               'status': 4, 'reason': 85})
    first = errors[0] if errors else {'status': 0, 'reason': 0}
    return {'status': first['status'], 'reason': first['reason'],
            'distance_pairs': pairs, 'edge_pairs': edges, 'refusals': errors}


def description_status13b(a, points, materials, body_type=0):
    pass                                                                   
    require(len(a) == 64 and len(points) == a[4] and len(materials) == a[6],
            'description physical counts')
    require(all(len(row) == 6 for row in materials), 'physical material fields')
    if body_type != 0:
        return 5, 80
    if a[6] != 1 and a[6] != a[4]:
        return 5, 83
    for row in materials:
        for i in range(4):
            v = number(row[i])
            if not math.isfinite(v) or i < 3 and v < 0:
                return 5, 0
    g = geometry_predicates13b(points, bool(a[5]))
    return g['status'], g['reason']


def topology13b(points, closed, material_count):
    pass                                                                 
    n = len(points)
    require(n >= 4 and material_count in (1, n), 'legal raw chain description')
    return [{'points': tuple(points[k % n] for k in
                            ((i - 1, i, i + 1, i + 2) if closed else
                             (i, i + 1, i + 2, i + 3))),
             'material': 0 if material_count == 1 else i if closed else i + 1}
            for i in range(n if closed else n - 3)]


def ticket_batch13b(low, high, segments):
    require(all(type(v) is int and 0 <= v <= 0xffffffff for v in (low, high)),
            'physical ticket')
    require(type(segments) is int and 0 <= segments <= 128, 'physical segment count')
    needed = 1 + segments
    last = low | high << 32
    return (0 if needed <= 0xffffffffffffffff - last else 3), needed


def check13b_groups(records, operation, ident, seq, raw_world_map, observer=True, *, positive_steps=0):
    pass                                                                     

                                                                        
                                                                        
       
    require(records and records[0] == ('E13B', (ident, seq, operation['opcode'], *operation['a'])),
            'exact E13B/input echo')
    require(all(v[:2] == (ident, seq) for _, v in records), '13b id/seq')
    opcode, a = operation['opcode'], operation['a']
    by_tag = {}
    for tag, v in records:
        by_tag.setdefault(tag, []).append(v)
    require(len(by_tag.get('A13', [])) == 1, 'one A13')
    status, reason = by_tag['A13'][0][2:]
    require(status in range(8) and reason in (0, 1, 80, 81, 82, 83, 84, 85), 'A13 domain')
    require(records[-1][0] == 'Z13' and len(by_tag.get('Z13', [])) == 1, 'one final Z13')
    counted = ('A13 CN13 CQ13 QL13 CS13 PC13 COPY13 CV13 CE13 ENDCOPY13').split()
    z = records[-1][1][2:]
    require(len(z) == 17 and z[:10] == tuple(len(by_tag.get(t, [])) for t in counted), 'Z13 tag counts')
    require(z[10] == len(by_tag.get('CN13', [])) and z[12] == positive_steps and z[13] == seq,
            'Z13 saved/positiveSteps/ordinal')
    require(z[14:] == tuple(len(by_tag.get(t, [])) for t in ('EP13B', 'EU13B', 'V13')), 'Z13 echo/V counts')
    pos = 1
    for tag, source in (('EP13B', operation['points']), ('EU13B', operation['materials'])):
        expected = [(tag, (ident, seq, j, *row)) for j, row in enumerate(source)] if opcode == 100 else []
        require(records[pos:pos + len(expected)] == expected, tag + ' whole exact input group')
        pos += len(expected)
    require(records[pos][0] == 'A13', 'A13 follows complete EP/EU group')
    order = {'CN13': 0, 'V13': 1, 'CQ13': 2, 'QL13': 2, 'CS13': 3,
             'PC13': 4, 'COPY13': 5, 'CV13': 5, 'CE13': 5, 'ENDCOPY13': 5,
             'CH13': 6, 'CI13': 7, 'CM13': 8, 'BH13': 9, 'IP13': 10,
             'CG13': 11, 'I13': 12, 'Z13': 13}
    tail = records[pos + 1:]
    require(all(t in order for t, _ in tail), 'unexpected/new duplicate E/EP/EU/A')
    require([order[t] for t, _ in tail] == sorted(order[t] for t, _ in tail), 'new group order')
    def indexed(tag, width):
        rows = by_tag.get(tag, [])
        keys = [v[2:2 + width] for v in rows]
        require(keys == sorted(set(keys)), tag + ' sparse order/duplicate slot')
        return {v[2:2 + width]: v[2 + width:] for v in rows}
    cn, vv = indexed('CN13', 1), indexed('V13', 1)
    require(cn.keys() == vv.keys(), 'CN/V same registers')
    require(all(k[0] < 16 for k in cn), 'chain register range')
    cq, ql, pc = indexed('CQ13', 1), indexed('QL13', 2), indexed('PC13', 1)
    require(len(cq) == int(opcode == 102), 'CQ13 required exactly for102')
    require(len(pc) == int(opcode == 104), 'PC13 required exactly for104')
    if opcode == 102:
        require(set(cq) == {(a[2],)}, 'CQ requested register')
        query = cq[(a[2],)]
        require(query[0] == status, 'CQ status/A')
        if status:
            require(query[1:] == (0,) * 18 and not ql, 'refused CQ all zero/no QL')
        else:
            count, returned = query[14:16]
            require(1 <= count <= 128 and returned == (count if a[0] else min(count, a[3])), 'CQ full/returned/capacity')
            require(set(ql) == {(a[2], i) for i in range(returned)}, 'QL full ordered returned list')
    else:
        require(not ql, 'QL without CQ')
    if opcode == 104:
        require(set(pc) == {(a[2],)}, 'PC requested register')
        parent = pc[(a[2],)]
        require(parent[0] == status and parent[1] in (0, 1), 'PC status/has')
        if status or not parent[1]:
            require(parent[1:] == (0,) * 9, 'PC absent/refused zeros')
                                                                             
    copy_rows = [(t, v) for t, v in records if t in ('COPY13', 'CV13', 'CE13', 'ENDCOPY13')]
    copies, offset = {}, 0
    while offset < len(copy_rows):
        t, v = copy_rows[offset]
        require(t == 'COPY13' and len(v) == 4, 'COPY block start')
        key = v[2:]
        require(key not in copies and key[0] < 4 and key[1] in (0, 1, 2), 'copy slot/phase/duplicate')
        require(offset + 1 < len(copy_rows) and copy_rows[offset + 1][0] == 'CV13', 'copy CV missing')
        cv = copy_rows[offset + 1][1]
        require(cv[:4] == v and len(cv) == 18 and cv[-1] <= 128, 'copy CV identity/count')
        count = cv[-1]
        children = copy_rows[offset + 2:offset + 2 + count]
        require(len(children) == count and all(t == 'CE13' and x[:5] == (*v, i)
            for i, (t, x) in enumerate(children)), 'copy complete CE order')
        end = offset + 2 + count
        require(end < len(copy_rows) and copy_rows[end] == ('ENDCOPY13', v), 'copy ENDCOPY')
        copies[key] = (cv[4:], tuple(x[5:] for _, x in children))
        offset = end + 1
    require(list(copies) == sorted(copies), 'copy register/phase order')
    if opcode == 108:
        selected = a[0]
        require(all((selected, p) in copies for p in range(3)), '108 all three phases')
        before, changed, after = [copies[(selected, p)] for p in range(3)]
        require(before == after and before != changed, 'copy phases0=2 and1 differs')
        require(a[1] < len(before[1]) and before[0] == changed[0], 'copy item/view metadata')
        expected = [list(x) for x in before[1]]
        expected[a[1]][3] = a[2]
        require(tuple(tuple(x) for x in expected) == changed[1], '108 changes ONLY selected ShapeNumber.slot')
    require(all(phase == 0 or opcode == 108 and reg == a[0] for reg, phase in copies), 'unexpected copy phase')
    ch, ci, cm = indexed('CH13', 2), indexed('CI13', 3), indexed('CM13', 3)
    bh, ip, cg = indexed('BH13', 2), indexed('IP13', 1), indexed('CG13', 2)
    cs = indexed('CS13', 2)
    if observer:
        require(ch.keys() == cg.keys(), 'CH/CG same slot range')
        require(len(by_tag.get('I13', [])) == 1, 'I13 required in OBS1')
        require(by_tag['I13'][0][2:] == tuple(len(by_tag.get(t, [])) for t in
            ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13')), 'I13 exact private counts')
        require(z[11] == sum(v[0] for v in ch.values()), 'Z13 liveChains')
        for (world,), pool in ip.items():
            next_index, count, *free = pool
            require(next_index <= 16 and len(free) == count and len(set(free)) == count,
                    'IP13 free stack count/duplicate')
            require({k for k in ch if k[0] == world} == {(world, i) for i in range(next_index)}, 'full CH pool slots')
            require(set(free) == {slot for (w, slot), v in ch.items() if w == world and not v[0]}, 'IP free/dead exact set')
        require(all((w,) in ip for w, _ in ch), 'CH world has IP')
        expected_ci, expected_cm, expected_cs = set(), set(), set()
        for (world, slot), chain in ch.items():
            alive, body, nxt, count, material_count = chain
            require(alive in (0, 1) and cg[(world, slot)][0] == alive, 'CH/CG occupied')
            if not alive:
                require(chain[1:] == (0,) * 4, 'dead CH canonical zeros')
                continue
            require(1 <= count <= 128 and 1 <= material_count <= 128, 'live chain counts')
            expected_ci.update((world, slot, j) for j in range(count))
            expected_cm.update((world, slot, j) for j in range(material_count))
            require((world, body) in bh, 'chain body BH missing')
            for j in range(count):
                child = ci.get((world, slot, j))
                require(child is not None and child[0] == child[3] + 1, 'CI child raw/number slot')
                child_key = (world, child[3])
                require(child_key not in expected_cs, 'child belongs to exactly one chain')
                expected_cs.add(child_key)
                require(child_key in cs and cs[child_key][-1] == slot, 'CS child/parent/last child')
        require(set(ci) == expected_ci and set(cm) == expected_cm and set(cs) == expected_cs,
                'complete CI/CM/CS, no last material/child omitted')
        if opcode == 100 and not status:
            require((a[3],) in cn, 'successful create target CN')
            chain_slot = cn[(a[3],)][3]
            key = (a[1], chain_slot)
            require(key in ch, 'successful create target CH')
            topology = topology13b(operation['points'], bool(a[5]), a[6])
            require(ch[key][3:] == (len(topology), len(operation['materials'])), 'create chain/material count')
            require([cm[(*key, j)] for j in range(a[6])] == list(operation['materials']), 'create material values/last entry')
            for j, expected in enumerate(topology):
                child_slot = ci[(*key, j)][3]
                values = tuple(w for point in expected['points'] for w in point)
                require(cs[(a[1], child_slot)] == (*values, chain_slot), 'create all ghost/endpoints/order')
        for (world, body), (head,) in bh.items():
            seen, current = set(), head
            while current != 0xffffffff:
                require(current not in seen and (world, current) in ch, 'body chain list cycle/range')
                seen.add(current)
                chain = ch[(world, current)]
                require(chain[0] == 1 and chain[1] == body, 'body chain list owner/alive')
                current = chain[2]
            require(seen == {s for (w, s), v in ch.items() if w == world and v[0] and v[1] == body},
                    'body chain list complete')
        for (reg,), stored in cn.items():
            raw, number5 = stored[:3], stored[3:]
            require(number5[0] == (raw[0] - 1) & 0xffffffff, 'CN raw/typed slot')
            world = raw_world_map.get(raw[1])
            meta = cg.get((world, number5[0]))
            raw_valid = bool(meta and meta[0] and meta[1] == raw[2])
            game_valid = bool(raw_valid and number5[1:] == meta[2:])
            require(vv[(reg,)] == (int(raw_valid), int(game_valid)), 'V13 actual life/owner/birth')
    else:
        require(not any(t in by_tag for t in ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13', 'I13')), 'OBS0 private13 tags')
    return {'new_groups_checked': True, 'complete_snapshot': False,
            'scope': 'BASE12, history and native equality still required'}


_BASE12_13B = None


def base12_13b():
    pass                                                                       
    global _BASE12_13B
    if _BASE12_13B is None:
        path = HERE / 'porownaj-zywy.py'
        require(path.is_file(), 'BASE12 comparator missing from integration: ' + str(path))
        spec = importlib.util.spec_from_file_location('chain13b_base12', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _BASE12_13B = module
    return _BASE12_13B


def parse_world13b(raw):
    tag = raw.split(b' ', 1)[0].decode('ascii') if isinstance(raw, bytes) else raw.split(' ', 1)[0]
                                                                           
    if tag in SCHEMA13B and not (tag == 'G' and len(raw.split()) != 5) or tag == 'IP13':
        return parse13b(raw)
    return base12_13b().parse_record(raw.decode('ascii') if isinstance(raw, bytes) else raw)


def decode_input13b(data, decimal=False):
    pass                                                                           
    lines = iter(data.decode('ascii').splitlines())
    first = next(lines).split(' ')
    require(len(first) == 2 and first[0] in ('PORT13B', 'GUARD13B'), '13b input header')
    count = int(first[1]); require(1 <= count <= (1 if first[0] == 'GUARD13B' else 64), '13b N')
    guard = first[0] == 'GUARD13B'; g = ga = None
    if guard:
        row = next(lines).split(' '); require(row[0] == 'G' and len(row) == 5, '13b G')
        g = tuple(map(int, row[1:])); require(g[0] == 1, '13b G id')
        row = next(lines).split(' '); require(row[:2] == ['GA', '1'] and len(row) == 66, '13b GA')
        ga = tuple(int(x, 10 if decimal else 16) for x in row[2:])
    def group(ident, seq, n, count):
        result = []
        for tag, size, width in (('P13B', n, 2), ('U13B', count, 6)):
            part = []
            for j in range(size):
                row = next(lines).split(' ')
                require(row[:4] == [tag, str(ident), str(seq), str(j)] and len(row) == 4 + width,
                        '13b complete physical input group')
                part.append(tuple(int(x, 10 if decimal else 16) for x in row[4:]))
            result.append(tuple(part))
        return tuple(result)
    helper_points = helper_materials = ()
    if guard and g[1] == 200:
        helper_points, helper_materials = group(1, 0, ga[4], ga[6])
    cases = []
    for ident in range(1, count + 1):
        if guard:
            opcount = g[3]
        else:
            row = next(lines).split(' '); require(row[:2] == ['C', str(ident)] and len(row) == 3, '13b C')
            opcount = int(row[2]); require(1 <= opcount <= 64, '13b opCount')
        operations = []
        for seq in range(1, opcount + 1):
            row = next(lines).split(' ')
            require(len(row) == 67 and row[:2] == ['O', str(seq)], '13b O/64 words')
            code = int(row[2]); a = tuple(int(x, 10 if decimal else 16) for x in row[3:])
            points, materials = group(ident, seq, a[4], a[6]) if code == 100 else ((), ())
            operations.append({'opcode': code, 'a': a, 'points': points, 'materials': materials})
        cases.append((ident, operations))
    require(next(lines, None) is None, '13b input trailing data')
    return {'profile': first[0], 'N': count, 'cases': cases, 'g': g, 'ga': ga,
            'points': helper_points, 'materials': helper_materials}


def base12_snapshot13b(records, operation, ident, seq, observer, positive=0, completed=0, profile=11):
    pass                                                                    

                                                                        
                                                                                
                                                                             
       
    base = base12_13b()
    order = list(base.ORDER)
    order[0:1] = [('E13B',),('EP13B',),('EU13B',),('A13',)]
    index = order.index(('X',))
    order[index:index] = [('CN13',),('V13',),('CQ13','QL13'),('CS13',),('PC13',),
                         ('COPY13','CV13','CE13','ENDCOPY13')]
    index = order.index(('I8',))
    order[index:index] = [(t,) for t in ('CH13','CI13','CM13','BH13','IP13','CG13')]
    order += [('I13',),('Z13',)]
    ranks = {tag:i for i,group in enumerate(order) for tag in group}
    last = -1
    for tag,v in records:
        require(tag in ranks and ranks[tag] >= last, tag + ' complete BASE12/13b global group order')
        last = ranks[tag]
    rows = defaultdict(list)
    inherited = []
    for tag, v in records:
        rows[tag].append(v)
        if tag not in SCHEMA13B and tag != 'IP13' or tag == 'G' and len(v) != 4:
            inherited.append((tag, v))
    rank = -1
    for tag, v in inherited:
        require(v[:2] == (ident, seq), tag + ' inherited id/seq')
        require(tag in base.RANK and base.RANK[tag] >= rank, tag + ' inherited group order')
        rank = base.RANK[tag]
    counts = Counter(t for t, _ in records); counts['E'] = counts['E13B']
    code = operation['opcode']
    expected_r = 2 if code == 16 else 1 if code < 80 or code == 90 else 0
    require(len(rows['R']) == expected_r, 'BASE12 exact R multiplicity')
    require(len(rows['AP12']) == int(80 <= code <= 92), 'BASE12 exact AP12 multiplicity')
    statuses = [v[3] for v in rows['R']] + [v[2] for v in rows['AP12']]
    require(all(x in range(8) for x in statuses), 'BASE12 status range')
    if code < 100:
        expected = next((s for s in statuses if s), 0)
        require(rows['A13'][0][2] == expected, 'A13 inherited status aggregate')
    if code in (31, 32) and not rows['A13'][0][2]:
        completed += 1; positive += number(operation['a'][1]) > 0
    for tag in ('Z8', 'Z9', 'Z10', 'Z11', 'I12', 'Z12'):
        require(len(rows[tag]) == 1, tag + ' inherited mandatory record')
    require(rows['Z8'][0][8:26] == tuple(counts[t] for t in base.p11.p10.p9.p8.PUBLIC_COUNTS), 'Z8 all public counts')
    require(rows['Z9'][0][5:12] == tuple(counts[t] for t in base.p11.p10.p9.PUBCOUNTS), 'Z9 all public counts')
    require(rows['Z9'][0][12:15] == (seq, seq, profile), 'Z9 ordinal/profile13b')
    require(rows['Z10'][0][2:] == (*[counts[t] for t in base.p11.p10.HIT_COUNTS], completed), 'Z10 actual counts/completed')
    require(rows['Z11'][0][2:] == (counts['SW11'], counts['GS11'], positive), 'Z11 counts/positive')
    names = ('AP12', 'WS12', 'NM12', 'UD12', 'HC12', 'HR12', 'HT12', 'CL12', 'CV12', 'VR12', 'EF12')
    require(rows['I12'][0][2:] == tuple(counts[t] for t in names), 'I12 every count including EF12')
    require(rows['Z12'][0][2:] == (positive, seq), 'Z12 counters')
    for tag, target in (('WS12', 'W'), ('HC12', 'W'), ('NM12', 'B'), ('EF12', 'S'), ('G', 'S')):
        require([v[2] for v in rows[tag]] == [v[2] for v in rows[target]], tag + ' exact live registers')
    require([v[2:4] for v in rows['UD12']] == [(k, v[2]) for k, tag in enumerate(('W', 'B', 'S')) for v in rows[tag]],
            'UD12 all live objects/order')
    for tag in ('W', 'B', 'S', 'G', 'WS12', 'NM12', 'EF12', 'HC12'):
        keys = [v[2] for v in rows[tag]]
        require(keys == sorted(set(keys)), tag + ' duplicate/sparse ordering')
    if observer:
        for tag in ('I8', 'I9', 'I10', 'I11', 'IP12'):
            require(len(rows[tag]) == 1, tag + ' inherited private mandatory')
        for tag, names in (('I8', base.p11.I8_TAGS), ('I10', base.p11.p10.NEW_COUNTS), ('I11', base.p11.NEW_PRIVATE)):
            require(rows[tag][0][2:] == tuple(counts[t] for t in names), tag + ' exact private counts')
        require(rows['I9'][0][2:20] == tuple(counts[t] for t in base.p11.p10.p9.PRIVCOUNTS), 'I9 private counts')
        require(rows['IP12'][0][2:] == (counts['NP12'],), 'IP12 exact NP12 count')
        require(counts['NP12'] == sum(v[5] for v in rows['BP11']), 'NP12 every cold live body')
        require([v[2:4] for v in rows['NP12']] == sorted(set(v[2:4] for v in rows['NP12'])), 'NP12 sparse order')
    else:
        require(not any(rows[t] for t in PRIVATE13B), 'OBS0 excludes only exact private tags')
        require(all(v[6:9] == (0, 0, 0) for v in rows['WS12']), 'OBS0 tuning fields')
    return rows, positive, completed


class History13B:
    pass                                                                      
    def __init__(self):
        self.last_ticket = 0
        self.reset_case()

    def reset_case(self):
        self.previous = defaultdict(list)
        self.copies = {}
        self.saved_bodies = {}
        self.saved_shapes = {}
        self.chain_values = {}
        self.positive = self.completed = 0
        self.maxima = Counter()

    def check(self, records, operation, ident, seq, observer=True, profile=11):
        rows, self.positive, self.completed = base12_snapshot13b(
            records, operation, ident, seq, observer, self.positive, self.completed, profile)
        raw_world_map = {v[3] - 1: v[2] for v in rows['W']}
        new = [(t, v) for t, v in records if (t in SCHEMA13B and not (t == 'G' and len(v) != 4)) or t == 'IP13']
        check13b_groups(new, operation, ident, seq, raw_world_map, observer,
                        positive_steps=self.positive if profile in (13,14,15) else 0)
        old = self.previous; code, a = operation['opcode'], operation['a']
        worlds = {v[2]: v for v in old['W']}
        cn = {v[2]: v[3:] for v in old['CN13']}
        def life(kind, reg, wreg):
            if wreg not in worlds: return 1
            owner = worlds[wreg][8:10]
            saved = cn.get(reg) if kind == 'chain' else self.saved_bodies.get(reg) if kind == 'body' else self.saved_shapes.get(reg)
            if saved is None: return 1
            ticket = saved[6:8] if kind == 'chain' else saved[8:10]
            if tuple(ticket) != tuple(owner): return 2
            if kind == 'chain':
                valid = next((v[4] for v in old['V13'] if v[2] == reg), 0)
                return 0 if valid else 1
            return 0 if any(v[2] == reg for v in old['B' if kind == 'body' else 'S']) else 1
        status, reason = rows['A13'][0][2:]
        current_cn = {v[2]: v[3:] for v in rows['CN13']}
        permitted_target = a[3] if code == 100 and not status else None
        require(set(current_cn) == set(cn) | ({permitted_target} if permitted_target is not None else set()),
                'all saved CN registers persist, including dead numbers')
        for reg, value in cn.items():
            if reg != permitted_target:
                require(current_cn[reg] == value, 'saved chain identity must not be restamped')
        if code in range(100, 107):
            kind = 'body' if code == 100 else 'shape' if code in (104, 105) else 'chain'
            wreg, reg = (a[0], a[1]) if code == 106 else (a[1], a[2])
            expected = life(kind, reg, wreg)
            expected_reason = 0
            if expected == 0 and code == 100:
                body_type = self.saved_bodies[reg][12]
                expected, expected_reason = description_status13b(a, operation['points'], operation['materials'], body_type)
                if not expected:
                    expected, _ = ticket_batch13b(self.last_ticket & 0xffffffff, self.last_ticket >> 32,
                        len(operation['points']) if a[5] else len(operation['points']) - 3)
            elif expected == 0 and code == 103 and a[3] < 2:
                if not math.isfinite(number(a[4])) or number(a[4]) < 0: expected = 5
            elif expected == 0 and code == 105:
                if self.saved_shapes[reg][18] != 4: expected = 5
            if code == 106 or a[0]:
                require((status, reason) == (expected, expected_reason), '13b independent life/description/status priority')
            else:
                require(status == 0, 'raw operation status')
        if code in (18,19) or code == 81 and a[2] == 1:
            expected = life('shape',a[1],a[0])
            saved = self.saved_shapes.get(a[1])
            if expected == 0 and saved[18] == 4:
                require((status,reason) == (5,81), 'existing child mutator must refuse before ordinary-shape preflight')
        if code == 80 and a[2] == 1 and a[3] == 0 and a[4] != 0:
            expected = life('body',a[1],a[0])
            body = self.saved_bodies.get(a[1])
            if expected == 0 and body is not None:
                active = any(v[2:4] == (a[0],body[3]-1) and v[4] != 0xffffffff for v in old['BH13'])
                if active: require((status,reason) == (5,80), 'SetType chain parent must stay static')
        if status and (code >= 100 or code in (18,19,80,81)):
                                                                              
                                                                              
            immutable = (PRIVATE13B - {'I8','I9','I10','I11','I13','IP12'}) | {
                'W','B','S','G','V','CN13','V13','CS13','EF12','WS12','NM12','UD12','HC12','HR12','SW11','GS11'}
            for tag in immutable:
                require([v[2:] for v in rows[tag]] == [v[2:] for v in old[tag]], 'refusal mutated ' + tag)
        if observer and code in (101,3) and not status:
            wreg = a[1] if code == 101 else a[0]
            previous_ch = {v[2:4]:v[4:] for v in old['CH13']}
            removed = [cn[a[2]][3]] if code == 101 else []
            if code == 3:
                body_slot = self.saved_bodies[a[1]][3]-1
                current = next(v[4] for v in old['BH13'] if v[2:4] == (wreg,body_slot))
                while current != 0xffffffff:
                    removed.append(current); current = previous_ch[(wreg,current)][2]
            before_pool = next(v[3:] for v in old['IP13'] if v[2] == wreg)
            after_pool = next(v[3:] for v in rows['IP13'] if v[2] == wreg)
            require(after_pool == (before_pool[0],before_pool[1]+len(removed),*before_pool[2:],*removed),
                    'destroy chain/body releases chain IDs in exact LIFO order')
            current_meta = {v[2:4]:v[4:] for v in rows['CG13']}
            for value in old['CG13']:
                if value[2] == wreg and value[3] in removed:
                    require(current_meta[value[2:4]] == (0,*value[5:]), 'destroy preserves generation and birth metadata')
        ticket = rows['Z8'][0][-2] | rows['Z8'][0][-1] << 32
        if code in range(100, 110):
            needed = 1 + (a[4] if a[5] else a[4] - 3) if code == 100 and not status else 0
            require(ticket == self.last_ticket + needed, 'whole 1+s reservation/no read/refusal ticket')
        require(ticket >= self.last_ticket, 'process-global ticket monotonicity')
        if code == 100 and not status:
            created = next(v[3:] for v in rows['CN13'] if v[2] == a[3])
            require(created[4:6] == (self.last_ticket + 1 & 0xffffffff, (self.last_ticket + 1) >> 32), 'chain gets first reserved ticket')
            require(created[6:8] == worlds[a[1]][8:10], 'created ChainNumber owner is actual WorldNumber birth')
            topology = topology13b(operation['points'], bool(a[5]), a[6])
            available = (i for i in range(512) if i not in self.saved_shapes)
            registered = {v[2]:v for v in rows['S']}
            child_numbers = []
            body = self.saved_bodies[a[2]]
            geometries = {v[2]:v[3:] for v in rows['G']}
            flags = {v[2]:v[3:] for v in rows['EF12']}
            for j, segment in enumerate(topology):
                reg = next(available)
                require(reg in registered, 'child bound to lowest never-initialized S register')
                shape = registered[reg]
                wanted = self.last_ticket + 2 + j
                require(shape[10:12] == (wanted & 0xffffffff, wanted >> 32), 'child S birth in creation order')
                require(shape[8:10] == worlds[a[1]][8:10], 'child owner ticket')
                require(shape[12:15] == body[3:6], 'child parent raw BodyId')
                material = operation['materials'][segment['material']]
                require(shape[18:26] == (4, bits(1.), *material), 'child type/density and exact selected material')
                require(shape[26:32] == (*a[10:15], 0), 'child filter/non-sensor')
                require(shape[32:36] == (0,)*4, 'chain child contributes zero mass including raw dynamic owner')
                require(shape[40:43] == a[7:10], 'child object value')
                require(shape[6:8] == (shape[4]<<16 | shape[5],shape[3]), 'child packed raw ID high/low')
                p1,p2 = segment['points'][1:3]
                centre = tuple(bits(add(mul(.5,number(x)),mul(.5,number(y)))) for x,y in zip(p1,p2))
                require(geometries[reg] == (4,2,0,0,0,*p1,*p2,*((0,)*31)), 'G40 endpoints; non-polygon centroid fields are zero')
                if observer:
                    private_shape = next(v for v in rows['P'] if v[2]==reg)
                    require(private_shape[8:10] == centre, 'private localCentroid is rounded endpoint midpoint, not ghosts')
                wp1,wp2 = transform(body[13:17],p1),transform(body[13:17],p2)
                margin=f32(.02)
                expected_aabb=tuple(bits(sub(min(number(x),number(y)),margin)) for x,y in zip(wp1,wp2))
                expected_aabb+=tuple(bits(add(max(number(x),number(y)),margin)) for x,y in zip(wp1,wp2))
                                                                            
                                                                    
                if not body[28]: expected_aabb=(0,)*4
                require(shape[36:40] == expected_aabb, 'child AABB excludes both ghosts, includes speculative distance')
                require(flags[reg] == (0,0,0), 'chain default contact/hit/preSolve flags')
                child_numbers.append((*shape[3:6], shape[3]-1, *shape[10:12], *shape[8:10]))
            body_number = (body[3]-1,*body[10:12],*body[8:10])
            self.chain_values[created[3:]] = {'number':created,'body':body_number,
                'children':tuple(child_numbers),'materials':list(operation['materials']),
                'points':topology,'world_reg':a[1]}
            if observer:
                before_pool = next((v for v in old['IP13'] if v[2] == a[1]), (ident, seq, a[1], 0, 0))
                allocated = before_pool[-1] if before_pool[4] else before_pool[3]
                require(created[3] == allocated, 'chain pool LIFO/reuse')
                previous_generation = next((v[5] for v in old['CG13'] if v[2:4]==(a[1],allocated)),0)
                require(created[2] == (previous_generation+1)&0xffff, 'chain generation increments/wraps as u16')
                children = [v[5:] for v in rows['CI13'] if v[2:4] == (a[1], created[3])]
                for j, child in enumerate(children):
                    wanted = self.last_ticket + 2 + j
                    require(child[4:6] == (wanted & 0xffffffff, wanted >> 32), 'all children ordered reserved tickets')
        if observer and not status and code == 103:
            previous_cm = {v[2:5]: v[5:] for v in old['CM13']}
            target = (a[1], cn[a[2]][3]); field = (0, 1, 4)[a[3]]
            for value in rows['CM13']:
                key, material = value[2:5], list(previous_cm[value[2:5]])
                if key[:2] == target: material[field] = a[4]
                require(value[5:] == tuple(material), 'setter every material/preserve all other fields')
                                                              
            slots = {v[8] for v in old['CI13'] if v[2:4] == target}
            previous_s = {v[2]: v for v in old['S']}
            for value in rows['S']:
                old_shape = previous_s[value[2]]
                if value[3] - 1 in slots and value[4] == worlds[a[1]][3] - 1:
                    require(value[(20,21,24)[a[3]]] == a[4], 'setter every child shape loop')
        if not status and code == 103:
            value = self.chain_values[cn[a[2]][3:]]
            field = (0,1,4)[a[3]]
            value['materials'] = [tuple(a[4] if i==field else w for i,w in enumerate(material))
                                  for material in value['materials']]
                                                                      
                                                                           
        if observer:
            material_rows = {v[2:5]:v[5:] for v in rows['CM13']}
            for reg, stored in current_cn.items():
                valid = next(v[4] for v in rows['V13'] if v[2] == reg)
                if not valid: continue
                expected_value = self.chain_values[stored[3:]]
                wreg = expected_value['world_reg']
                for j, material in enumerate(expected_value['materials']):
                    require(material_rows[(wreg,stored[3],j)] == material, 'material history/owned input109')
        public_segments = {v[2:4]:v[4:] for v in rows['CS13']}
        for reg, stored in current_cn.items():
            valid = next(v[4] for v in rows['V13'] if v[2] == reg)
            if not valid: continue
            expected_value = self.chain_values[stored[3:]]
            for child, segment in zip(expected_value['children'],expected_value['points']):
                expected_segment = tuple(w for point in segment['points'] for w in point) + (stored[3],)
                require(public_segments[(expected_value['world_reg'],child[3])] == expected_segment,
                        'ghost/point history and owned input109')
        if code == 102 and not status:
            value = self.chain_values[cn[a[2]][3:]]
            world = worlds[a[1]]
            returned = len(value['children']) if a[0] else min(a[3],len(value['children']))
            query = next(v[3:] for v in rows['CQ13'] if v[2] == a[2])
            require(query == (0,*world[3:6],world[3]-1,*world[8:10],0,0,*value['body'],
                    len(value['children']),returned,*[value['materials'][0][i] for i in (0,1,4)]),
                    'CQ13 actual world/body/material0/getter values')
            require([v[4:] for v in rows['QL13']] == list(value['children'][:returned]), 'QL13 saved ordered child identity')
        if code == 104 and not status:
            shape=self.saved_shapes[a[2]]
            expected_parent=(0,0,*((0,)*8))
            if shape[18]==4:
                shape_number=(*shape[3:6],shape[3]-1,*shape[10:12],*shape[8:10])
                matches=[value for value in self.chain_values.values() if shape_number in value['children']]
                require(len(matches)==1,'child has exactly one historical parent')
                expected_parent=(0,1,*matches[0]['number'])
            require(rows['PC13'][0][3:] == expected_parent, 'parentChain actual child parent/ordinary absence')
        blocks = {}
        for t, v in records:
            if t == 'CV13': blocks[v[2:4]] = [v[4:], []]
            elif t == 'CE13': blocks[v[2:4]][1].append(v[5:])
        expected_copies = set(self.copies) | ({a[2]} if code==106 and not status else set())
        require({reg for reg,phase in blocks if phase==0} == expected_copies,
                'all historical copies remain present, even after destroyWorld')
        for (reg, phase), value in blocks.items():
            value = (value[0], tuple(value[1]))
            if phase == 0:
                if code == 106 and reg == a[2] and not status:
                    source = self.chain_values[cn[a[1]][3:]]
                    require(value == ((*source['number'],*source['body'],len(source['children'])),source['children']),
                            '106 owns complete lookup/segments values')
                if reg in self.copies and not (code == 106 and reg == a[2]):
                    require(value == self.copies[reg], 'historical copy unchanged after setter/destroy/reuse')
                self.copies[reg] = value
        self.saved_bodies.update({v[2]: v for v in rows['B']})
        self.saved_shapes.update({v[2]: v for v in rows['S']})
        if profile == 11:
            totals = {'worlds': len(rows['W']), 'bodies': len(rows['B']), 'shapes': len(rows['S']),
                      'chains': rows['Z13'][0][13], 'materials': len(rows['CM13'])}
            for key, limit in (('worlds',2),('bodies',16),('shapes',128),('chains',16),('materials',256)):
                require(totals[key] <= limit, 'whole-history population ' + key)
                self.maxima[key] = max(self.maxima[key], totals[key])
            require(not self.positive and not rows['NC9'], 'PUBLIC13B no live contacts/positive Step')
        self.last_ticket = ticket; self.previous = rows
        return {'new_history_checked': True, 'BASE12_structure_checked': True,
                'full_ownership_ready': False,
                'remaining': 'BASE12 semantic model gaps require separate native evidence',
                'maxima': dict(self.maxima)}


class Model13B(History13B):
    pass                                                                   
    full_ownership_ready = False

    def __init__(self, observer=True):
        self.observer = observer
        super().__init__()

    def reset(self, ident):
        self.ident = ident
        self.reset_case()

    def check(self, ident, seq, operation, records, private=None):
        return super().check(records, operation, ident, seq,
                             self.observer if private is None else private)


SCHEMA13C = {'PORT13C': (1, 0), 'GUARD13C': (1, 0), 'COMPONENT13C': (1, 0),
             'E13C': (3, 64), 'KI13': (2, 7), 'M13C': (2, 30), 'K13C': (2, 7), 'DC13': (2, 5)}


def parse13c(line):
    pass                                                                  
    raw = line.decode('ascii') if isinstance(line, bytes) else line
    tag = raw.split(' ', 1)[0]
    if tag not in SCHEMA13C:
        return parse_world13b(line)
    require(raw.endswith('\n') and '\r' not in raw, '13c canonical LF')
    require(re.fullmatch(r'[!-~]+(?: [!-~]+)*\n', raw) is not None, '13c ASCII/spacing')
    words = raw[:-1].split(' '); d, h = SCHEMA13C[tag]
    require(len(words) == 1+d+h, tag+' arity')
    values = []
    for j, word in enumerate(words[1:]):
        require((D if j < d else H).fullmatch(word) is not None, tag+' word')
        value = int(word, 10 if j < d else 16)
        require(value <= 0xffffffff, tag+' u32')
        values.append(value)
    return tag, tuple(values)


def vsub13c(a, b): return tuple(sub(x, y) for x, y in zip(a, b))
def dot13c(a, b): return add(mul(a[0], b[0]), mul(a[1], b[1]))
def cross13c(a, b): return sub(mul(a[0], b[1]), mul(a[1], b[0]))


def rotate13c(words,v):
    c,s=map(number,words)
    return sub(mul(c,v[0]),mul(s,v[1])),add(mul(s,v[0]),mul(c,v[1]))


def normalize13c(v):
    length = f32(math.sqrt(dot13c(v, v)))
    return (0., 0.) if length < number(0x34000000) else tuple(mul(f32(1./length), x) for x in v)


def hull_status13c(points):
    pass                                                                    
    p = [tuple(map(number, x)) for x in points]; n = len(p)
    if not 3 <= n <= 8: return False
    for i in range(n):
        j = (i+1) % n; edge = normalize13c(vsub13c(p[j], p[i]))
        if any(cross13c(vsub13c(p[k], p[i]), edge) >= 0 for k in range(n) if k not in (i, j)):
            return False
    for i in range(n):
        edge = normalize13c(vsub13c(p[(i+2) % n], p[i]))
        if cross13c(vsub13c(p[(i+1) % n], p[i]), edge) <= f32(.005): return False
    return True


def direct_status13c(a, cache=None):
    pass                                                                       
    kind, mode, count, radius = a[0], a[1], a[18], number(a[19])
    cache = tuple(a[36:43]) if cache is None else tuple(cache)
    if not math.isfinite(radius) or radius < 0: return 5, 0
    for start in (10, 14):
        if not all(math.isfinite(number(x)) for x in a[start:start+4]) or not valid_rotation(a[start+2:start+4]):
            return 5, 0
    if not 0 <= cache[0] <= 3 or any(not 0 <= x <= 255 for x in cache[1:]): return 5, 82
    count_ok = count == 1 if kind == 0 else count == 2 if kind == 1 else 3 <= count <= 8
                                                                  
                                                                  
    if kind and count_ok and any(cache[1+j] >= 2 or cache[4+j] >= count for j in range(cache[0])): return 5, 82
    if not count_ok: return 4, 84
    chain = tuple(tuple(a[j:j+2]) for j in range(2, 10, 2))
    geometry = geometry_predicates13b(chain)
    if geometry['reason']: return 4, geometry['reason']
    points = tuple(tuple(a[20+2*j:22+2*j]) for j in range(count))
    if any(not math.isfinite(number(x)) for p in points for x in p): return 4, 84
    if kind == 1:
        delta = vsub13c(tuple(map(number, points[1])), tuple(map(number, points[0])))
        length2 = dot13c(delta, delta)
        if not math.isfinite(length2) or not length2 > number(0x34000000): return 4, 84
    if kind == 2 and not hull_status13c(points): return 4, 84
    return 0, 0


def circle_predicates13c(a):
    pass                                                                     

                                                                          
       
    xf = relative_transform(a[10:14], a[14:18])
    p = tuple(map(number, transform(xf, a[20:22])))
    g1,p1,p2,g2 = [tuple(map(number, a[j:j+2])) for j in range(2,10,2)]
    edge = vsub13c(p2,p1); offset = dot13c((edge[1],f32(-edge[0])),vsub13c(p,p1))
    values = {'offset':offset}; reached = ['circle/offset<0']; region = 'back';expected=[0]*30
    if offset < 0: return {'region':region,'pointCount':0,'reached':reached,'values_H':{k:f'{bits(v):08x}' for k,v in values.items()},'manifold_H':tuple(expected)}
    u=dot13c(edge,vsub13c(p2,p)); v=dot13c(edge,vsub13c(p,p1)); values.update(u=u,v=v)
    reached.append('circle/v<=0')
    if v <= 0:
        up=dot13c(vsub13c(p1,g1),vsub13c(p,p1));values['uPrev']=up;reached.append('circle/uPrev<=0')
        if up <= 0: region='previous'
        else: region='point1'; pa=p1
    else:
        reached.append('circle/u<=0')
        if u <= 0:
            vn=dot13c(vsub13c(g2,p2),vsub13c(p,p2));values['vNext']=vn;reached.append('circle/vNext>0')
            if vn > 0: region='next'
            else: region='point2';pa=p2
        else:
            region='interior';ee=dot13c(edge,edge);values['ee']=ee;reached.append('circle/ee>0')
            pa=tuple(add(mul(u,x),mul(v,y)) for x,y in zip(p1,p2))
            pa=tuple(mul(f32(1./ee),x) for x in pa) if ee>0 else p1
    if region in ('previous','next'): count=0
    else:
        delta=vsub13c(p,pa);length=f32(math.sqrt(dot13c(delta,delta)));sep=sub(length,number(a[19]))
        values.update(length=length,separation=sep);reached += ['circle/length<epsilon','circle/separation>speculative']
        count=int(not sep>f32(.02))
        if count:
            reached += ['circle/normal','circle/anchorA','circle/anchorB','circle/point','circle/id0']
            normal=(0.,0.) if length<number(0x34000000) else tuple(mul(f32(1./length),x) for x in delta)
            radius=number(a[19]);cB=tuple(add(x,mul(f32(-radius),n)) for x,n in zip(p,normal))
            contact=tuple(add(mul(.5,x),mul(.5,y)) for x,y in zip(pa,cB))
            normalA=rotate13c(a[12:14],normal);anchorA=rotate13c(a[12:14],contact)
            originA=tuple(map(number,a[10:12]));originB=tuple(map(number,a[14:16]))
            anchorB=tuple(add(x,sub(y,z)) for x,y,z in zip(anchorA,originA,originB))
            point=tuple(add(x,y) for x,y in zip(originA,anchorA))
            expected[:2]=map(bits,normalA);expected[3]=1
            expected[4:11]=map(bits,(*point,*anchorA,*anchorB,sep))
    return {'region':region,'pointCount':count,'reached':reached,
            'values_H':{k:f'{bits(v):08x}' for k,v in values.items()},'manifold_H':tuple(expected)}


def check_direct13c(records, ident, seq, a, *, history=None, warm=False, semantic=True):
    require(records and records[0] == ('E13C',(ident,seq,120,*a)), 'exact direct13c echo')
    require(all(v[:2] == (ident,seq) for _,v in records), 'direct13c id/seq')
    require(len(records)>=3 and records[1][0]=='A13', 'direct13c one A after E')
    status,reason=records[1][1][2:];cache=tuple(history) if warm and seq>1 else tuple(a[36:43])
    require(not warm or seq==1 or a[36:43]==(0,)*7, 'warm later seed bitwise+0')
    require(status in (0,4,5) and reason in (0,82,84,85), 'direct13c status domain')
    if semantic and a[1]:require((status,reason)==direct_status13c(a,cache), 'direct13c PARAM before GEOMETRY')
    if not a[1]:require((status,reason)==(0,0), 'raw direct success')
    tags=['E13C','A13']+([] if status else ['KI13','M13C','K13C'])+['DC13']
    require([t for t,_ in records]==tags, 'direct13c exact tags/count/order')
    require(records[-1][1][2:]==(1,1,int(not status),int(not status),int(not status)), 'direct13c counters')
    if status:return {'cache':cache,'status':status,'reason':reason,'refused_cache_preserved':True}
    ki,manifold,out=(v[2:] for _,v in records[2:5]);require(ki==cache,'direct13c own KI history7')
    for value in (ki,out):require(len(value)==7 and value[0]<=3 and all(x<=255 for x in value[1:]),'physical cache7')
    require(len(manifold)==30 and manifold[3] in range(3), 'direct13c M30/count')
    require(all(math.isfinite(number(x)) for x in manifold[:3]), 'direct normal/rolling finite')
    require(manifold[2]==0, 'fresh direct rolling impulse+0')
    for j in range(2):
        point=manifold[4+13*j:17+13*j]
        if j>=manifold[3]:require(point==(0,)*13,'unused direct point all+0')
        else:
            require(all(math.isfinite(number(x)) for x in point[:11]), 'active direct point finite')
            require(point[7:11]==(0,)*4 and point[12]==0 and point[11]<=65535,'fresh impulses/persisted/ID')
    predicates=None
    if a[0]==0:
        require(out==ki,'circle preserves all7 cache words')
        require(manifold[3]<=1,'circle max1point')
        if semantic:
            predicates=circle_predicates13c(a);require(manifold[3]==predicates['pointCount'],'circle reached Voronoi/side/separation')
            require(manifold==predicates['manifold_H'],'circle f32 normal/point/both anchors/separation/ID all30 words')
        if manifold[3]:require(manifold[15]==0,'circle ID0')
    elif out[0]:
        require(all(out[1+j]<2 and out[4+j]<a[18] for j in range(out[0])),'active direct cache indices')
    return {'cache':out,'status':status,'reason':reason,'predicates':predicates,'pointCount':manifold[3]}


def polygon_initial_predicates13c(a):
    pass                                                                   
    p=[tuple(map(number,a[20+2*j:22+2*j])) for j in range(a[18])]
    if a[0]==1:centroid=tuple(add(mul(.5,x),mul(.5,y)) for x,y in zip(p[0],p[1]))
    else:
        origin=p[0];center=(0.,0.);area=0.;inv3=f32(1./3.)
        for j in range(1,len(p)-1):
            e1=vsub13c(p[j],origin);e2=vsub13c(p[j+1],origin);tri=mul(.5,cross13c(e1,e2));scale=mul(tri,inv3)
            center=tuple(add(x,mul(scale,add(y,z))) for x,y,z in zip(center,e1,e2));area=add(area,tri)
        require(area>0,'finite valid polygon centroid area')
        centroid=tuple(add(o,mul(f32(1./area),x)) for o,x in zip(origin,center))
    xf=relative_transform(a[10:14],a[14:18]);center=tuple(map(number,transform(xf,tuple(map(bits,centroid)))))
    ghost,p1,p2,head=[tuple(map(number,a[j:j+2])) for j in range(2,10,2)]
    e0=normalize13c(vsub13c(p1,ghost));e1=normalize13c(vsub13c(p2,p1));e2=normalize13c(vsub13c(head,p2))
    n0,n1,n2=[(e[1],f32(-e[0])) for e in (e0,e1,e2)]
    c1,c2=cross13c(e0,e1),cross13c(e1,e2);convex1=c1>=f32(.01);convex2=c2>=f32(.01)
    b1=dot13c(n1,vsub13c(center,p1));b0=dot13c(n0,vsub13c(center,p1)) if convex1 else None
    b2=dot13c(n2,vsub13c(center,p2)) if convex2 else None
    behind=b1<0 and (b0 is None or b0<0) and (b2 is None or b2<0)
    values={'convex1':c1,'convex2':c2,'behind1':b1}
    if convex1:values['behind0']=b0
    if convex2:values['behind2']=b2
    return {'values_H':{key:f'{bits(value):08x}' for key,value in values.items()},
            'convex1':convex1,'convex2':convex2,'all_behind':behind,
            'GJK_reached':not behind,'post_GJK_branches':'UNVERIFIED without actual reached-feature evidence'}


class Model13C(History13B):
    pass                                                                      
    full_ownership_ready=False

    def __init__(self,observer=True):
        self.observer=observer;super().__init__();self.reset(1)

    def reset(self,ident):
        self.ident=ident;self.cache=None;self.direct_observations=[];self.reset_case()
        self.scene={'crossings':set(),'contact_bodies':set(),'cache_nonzero':False,'cache_changed':False,
                    'previous_cache':{},'loop79':False,'loop79to0':False,'B_survives':False,
                    'sleep':False,'wake_destroy':False,'end_destroy':False,'refusals':set(),
                    'category63':False,'groups':set(),'hooks':set()}

    def check(self,ident,seq,operation,records,private=None):
        observer=self.observer if private is None else private
        if ident<=384:
            warm=ident in range(65,129) or ident in range(193,257) or ident in range(321,385)
            result=check_direct13c(records,ident,seq,operation['a'],history=self.cache,warm=warm)
            self.cache=result['cache'];self.direct_observations.append({'seq':seq,**result});return result
                                                                               
                                                                          
        mapped=[('E13B' if t=='E13C' else t,v) for t,v in records]
        before=self.previous
        result=super().check(mapped,operation,ident,seq,observer,profile=13)
        rows=self.previous;family=(ident-385)//6+1;code=operation['opcode'];a=operation['a'];scene=self.scene
        status,reason=rows['A13'][0][2:];old_b={v[2]:v for v in before['B']};now_b={v[2]:v for v in rows['B']}
        if code in (31,32) and not status and number(a[1])>0:
            for reg in (1,):
                if reg in old_b and reg in now_b:
                    x0,x1=number(old_b[reg][13]),number(now_b[reg][13])
                    for threshold in (-2.,0.,2.,4.):
                        if x0<threshold<=x1:scene['crossings'].add((threshold,1))
                        if x0>threshold>=x1:scene['crossings'].add((threshold,-1))
        if family==7 and self.positive<=720 and all(j in now_b for j in (1,2,3)):
            if all(not now_b[j][27] for j in (1,2,3)):scene['sleep']=True
        if code==101 and not status and family==7 and self.positive==720:
            scene['wake_destroy']=all(j in now_b and now_b[j][27] for j in (1,2,3))
            if observer:scene['end_destroy']=bool(rows['EE0'] or rows['EE1'])
        if code==101 and not status and family==5:
            scene['B_survives']=any(v[2]==1 and v[4] for v in rows['V13'])
        if family==8 and self.positive==420:
            if code==80 and a[2]==1 and a[3]==0 and a[4] in (1,2):
                require((status,reason)==(5,80),'W8 both real SetType child guards')
                scene['refusals'].add(('type',a[4]))
            if code in (18,19) or code==81:
                require((status,reason)==(5,81),'W8 every checked child route')
                scene['refusals'].add((code,a[3] if code==81 else 0))
        for v in rows['S']:
            scene['category63']|=bool(v[27]&0x80000000);scene['groups'].add(v[30])
        scene['hooks'].update(v[4] for v in rows['HT12'])
        if observer:
                                                                               
                                                                               
            if code in (102,103,104,105,106,107,108,109) and not status:
                require([v[2:] for v in rows['CS']]==[v[2:] for v in before['CS']],
                        'getter/copy/chain setter must not refresh cached ContactSim')
            body_by_raw={(v[4],v[3]):v[2] for v in rows['B']}
            shapes={}
            for v in rows['S']:
                                                                   
                shapes[(v[4],v[3]-1)]=body_by_raw.get((v[4],v[12]))
            world_raw={v[2]:v[3]-1 for v in rows['W']}
            loop_index={(v[2],v[5]-1):v[4] for v in rows['CI13']}
            for v in rows['CS']:
                w=world_raw.get(v[2]);sa,sb=v[9],v[10];cache=tuple(v[20:27]);key=(v[2],v[6])
                if cache[0]:scene['cache_nonzero']=True
                if key in scene['previous_cache'] and scene['previous_cache'][key]!=cache:scene['cache_changed']=True
                scene['previous_cache'][key]=cache
                if v[30]>0:
                    bodies={shapes.get((w,sa)),shapes.get((w,sb))};scene['contact_bodies'].update(x for x in bodies if x is not None)
                    if family==4:
                        require(2 not in bodies,'W4 back circle has no touching manifold')
                        if self.positive>=301 and 1 in bodies:
                            indexes={loop_index.get((v[2],s)) for s in (sa,sb)}
                            if 79 in indexes:scene['loop79']=True
                            if scene['loop79'] and 0 in indexes:scene['loop79to0']=True
            if family==4:
                for v in rows['EB']:
                    w=world_raw.get(v[2]);bodies={shapes.get((w,v[4]-1)),shapes.get((w,v[7]-1))}
                    require(2 not in bodies,'W4 back circle has no begin event')
        expected=1200 if family==7 else 600
        if self.positive==expected:
            validate_scene13c(family,scene,observer=observer)
        result['scene_checked']=family;return result


def validate_scene13c(family,scene,*,observer=True):
    pass                                                                          
    if family==1:require({(0.,1),(4.,1),(0.,-1),(4.,-1)}<=scene['crossings'],'W1 must pass x0/x4 both directions')
    if family==2 and observer:require(scene['cache_nonzero'] and scene['cache_changed'],'W2 real own nonzero changing cache')
    if family==3:
        require(len({x for x,direction in scene['crossings'] if x in (-2.,0.,2.,4.)})>=2,'W3 box crosses two joins')
        if observer:require({1,2,3}<=scene['contact_bodies'],'W3 box/polygon3/polygon8 all touch')
    if family==4 and observer:require(scene['loop79to0'],'W4 actual contact79 to0 after second start')
    if family==5:require(scene['B_survives'],'W5 B survives destroy A')
    if family==7:
        require(scene['sleep'],'W7 three boxes sleep before720')
        require(scene['wake_destroy'],'W7 DestroyChain wakes real bodies')
        if observer:require(scene['end_destroy'],'W7 real end event on destruction')
    if family==8:
        wanted={('type',1),('type',2),(18,0),(19,0)}|{(81,k) for k in range(9)}
        require(scene['refusals']==wanted,'W8 all13 checked refusals after420')
        require(scene['category63'] and {0xffffffff,1}<=scene['groups'],'W8 bit63 and both signed groups')
        require({0,1}<=scene['hooks'],'W8 real filter and preSolve callbacks')
    return True


def seed_history13b(history, decoded):
    pass                                                                       
    kind=decoded['g'][1];ga=decoded['ga']
    if kind==4:
        history.last_ticket=ga[1] | ga[2]<<32
    elif kind==11:
        wreg,reg,generation=ga[:3]
        cn=next(v for v in history.previous['CN13'] if v[2]==reg)
        slot=cn[6]
        for i,v in enumerate(history.previous['CN13']):
            if v[2]==reg:history.previous['CN13'][i]=(*v[:5],generation,*v[6:])
        for i,v in enumerate(history.previous['CG13']):
            if v[2:4]==(wreg,slot):history.previous['CG13'][i]=(*v[:5],generation,*v[6:])
        value=history.chain_values[cn[6:]]
        value['number']=(*value['number'][:2],generation,*value['number'][3:])


def snapshots13b(source, decoded, observer=True, semantic=True):
    pass                                                                    
    digest = hashlib.sha256(); total = 0; tags = Counter(); history = History13B()
    def take():
        nonlocal total
        raw = source.readline(131073)
        if isinstance(raw, str): raw = raw.encode('ascii')
        require(raw and len(raw) <= 131072, '13b truncated/oversized output row')
        value = parse_world13b(raw); digest.update(raw); total += len(raw); tags[value[0]] += 1
        return raw, value
    require(take()[1] == (decoded['profile'], (decoded['N'],)), '13b output exact header')
    if decoded['g']:
        require(take()[1] == ('G', decoded['g']), 'exact G echo')
        require(take()[1] == ('GA', (1, *decoded['ga'])), 'exact GA echo')
        if decoded['g'][1] == 200:
            for tag, values in (('EP13B', decoded['points']), ('EU13B', decoded['materials'])):
                for j, row in enumerate(values):
                    require(take()[1] == (tag, (1, 0, j, *row)), 'whole G200 group echo')
    for ident, operations in decoded['cases']:
        history.reset_case()
        require(take()[1] == ('CASE', (ident, len(operations))), '13b CASE exact opcount')
        for seq, operation in enumerate(operations, 1):
            records = []; raw_rows = []; size = 0
            while True:
                raw, value = take(); size += len(raw)
                require(size <= 1204576, 'q13B snapshot envelope')
                records.append(value); raw_rows.append(raw)
                if value[0] == 'Z13': break
            if semantic:
                result = history.check(records, operation, ident, seq, observer,
                    12 if decoded['profile'] == 'GUARD13B' else 11)
            else:
                rows,history.positive,history.completed = base12_snapshot13b(records,operation,ident,seq,
                    observer,history.positive,history.completed,12 if decoded['profile']=='GUARD13B' else 11)
                require(records[0] == ('E13B',(ident,seq,operation['opcode'],*operation['a'])), 'mutant exact E13B')
                require(records[-1][0]=='Z13','mutant complete Z13 snapshot')
                counted=('A13 CN13 CQ13 QL13 CS13 PC13 COPY13 CV13 CE13 ENDCOPY13').split()
                require(records[-1][1][2:12] == tuple(len(rows[t]) for t in counted), 'mutant actual tag counts')
                result = {'syntax_and_counts_checked':True,'maxima':{},'full_ownership_ready':False}
            yield ident, seq, records, raw_rows, result
            if semantic and decoded['g'] and decoded['g'][2]==seq and decoded['g'][1] in (4,11):
                seed_history13b(history,decoded)
        if decoded['g'] and decoded['g'][1] not in (0,4,11):
            raw, value = take(); require(value[0] == 'GR13', 'GUARD helper GR13')
            yield ident, 0, [value], [raw], {'helper': True}
        require(take()[1] == ('ENDCASE', (ident,)), '13b ENDCASE')
    require(take()[1] == ('END', (decoded['N'],)), '13b END N')
    require(not source.read(1), '13b trailing output')
    yield None, None, None, None, {'sha256': digest.hexdigest(), 'bytes': total,
        'tags': dict(tags), 'END_EOF': True, 'full_ownership_ready': False}
