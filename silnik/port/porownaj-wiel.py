pass                                                                          
import argparse
import importlib.util
import math
from pathlib import Path
import sys

from porownaj import RESULT_FIELDS, UINT, EPS, SPECULATIVE

spec = importlib.util.spec_from_file_location('przypadki_wiel', Path(__file__).with_name('przypadki-wiel.py'))
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)
ALL_FIELDS = tuple('echo.' + f for f in g.INPUT_FIELDS) + RESULT_FIELDS
LIMITS = tuple(2 if f == 'pointCount' else 65535 if f.endswith('.id') else
               1 if f.endswith('.persisted') else 2**32-1 for f in ALL_FIELDS)


def parse_log(text, label):
    lines = text.replace('\r\n', '\n').removesuffix('\n').split('\n') if text else []
    rows, errors = {}, []
    if not lines or lines[0] != f'PORT2 {g.COUNT}':
        errors.append(f'{label}: missing/zly naglowek PORT2 {g.COUNT}')
    if not lines or lines[-1] != f'END {g.COUNT}':
        errors.append(f'{label}: missing/zly koniec END {g.COUNT}')
    records = lines[1:-1] if len(lines) >= 2 else []
    if len(records) != g.COUNT:
        errors.append(f'{label}: E8dc44deebc2b E7ef3142429d2 {len(records)}, expected {g.COUNT}')
    for line_no, line in enumerate(records, 2):
        tokens = line.split(' ')
        if (len(tokens) != 112 or tokens[0] != 'R'
                or not all(len(t) <= 10 and UINT.fullmatch(t) for t in tokens[1:])):
            errors.append(f'{label}: format linii {line_no}: expected R id + 110 u32')
            continue
        id = int(tokens[1])
        row = tuple(map(int, tokens[2:]))
        if not 1 <= id <= g.COUNT or id in rows or id != line_no-1:
            errors.append(f'{label}: id/kolejnosc/powtorzenie w linii {line_no}: {id}')
        for field, word, limit in zip(ALL_FIELDS, row, LIMITS):
            if word > limit:
                errors.append(f'{label}: {id} {field}: poza typem/zakresem: {word}')
        rows[id] = row
    missing = sorted(set(range(1, g.COUNT+1)) - rows.keys())
    if missing:
        errors.append(f'{label}: brakujace przypadki: {missing}')
    return rows, errors


def world_polygon(words, offset):
    n = words[offset]
    values = tuple(map(g.number, words[offset+1:offset+40]))
    px, py, c, s = values[35:39]
    vertices = tuple((c*values[2*i]-s*values[2*i+1]+px,
                      s*values[2*i]+c*values[2*i+1]+py) for i in range(n))
    return vertices, values[34], (px, py)


def edges(vertices):
    return zip(vertices, (*vertices[1:], vertices[0]))


def distance_to_edge(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length2 = dx*dx+dy*dy
    if length2 == 0:
        raise ValueError('Degenerate polygon edge')
    t = max(0, min(1, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2))
    return math.hypot(point[0]-a[0]-t*dx, point[1]-a[1]-t*dy)


def boundary_distance(point, polygon):
    return min(distance_to_edge(point, a, b) for a, b in edges(polygon))


def sat_gap(a, b):
    pass                                                                              
    gaps = []
    for polygon in (a, b):
        for p, q in edges(polygon):
            nx, ny = q[1]-p[1], p[0]-q[0]
            length = math.hypot(nx, ny)
            nx, ny = nx/length, ny/length
            aa = [x*nx+y*ny for x, y in a]
            bb = [x*nx+y*ny for x, y in b]
            gaps.append(max(min(bb)-max(aa), min(aa)-max(bb)))
    return max(gaps)


def geometry(case):
    a, ra, pa = world_polygon(case.words, 0)
    b, rb, pb = world_polygon(case.words, 40)
    gap = sat_gap(a, b)
    if gap > 0:
                                                                                     
                                                                                 
        core_distance = min(*(boundary_distance(v, b) for v in a),
                            *(boundary_distance(v, a) for v in b))
    else:
        core_distance = gap
                                                                               
                                                                      
    local = [abs(g.number(case.words[o+j])) for o in (0, 40) for j in (*range(1, 17), 33, 34, 35)]
    scale = max(2**-23, *local, abs(pb[0]-pa[0]), abs(pb[1]-pa[1]))
    tolerance = 128*EPS*scale
    world_tolerance = tolerance + 8*EPS*max(*map(abs, pa), *map(abs, pb))
    return a, ra, pa, b, rb, pb, core_distance-ra-rb, tolerance, world_tolerance


def normal_direction(case, result, label):
    pass                                                                        

                                                                                
                                                                              
                                                                             
                                                                               
       
    if result[0] == 0:
        return [], 'missing kontaktu'
    nx, ny = map(g.number, result[1:3])
    length = math.hypot(nx, ny)
    if not math.isfinite(length) or length == 0:
        return [f'{label}: independent Ec33e30d88d15 Ef1be686a60cf: missing E07e80e7da3c9'], 'blad'
    nx, ny = nx/length, ny/length
    a, _, pa = world_polygon(case.words, 0)
    b, _, pb = world_polygon(case.words, 40)
    local = [abs(g.number(case.words[o+j])) for o in (0, 40) for j in (*range(1, 17), 33, 34, 35)]
    scale = max(EPS, *local, abs(pb[0]-pa[0]), abs(pb[1]-pa[1]))
                                                                              
    aa = [(x-pa[0])*nx+(y-pa[1])*ny for x,y in a]
    bb = [(x-pa[0])*nx+(y-pa[1])*ny for x,y in b]
    margin = (min(bb)-max(aa))-(min(aa)-max(bb))
    tolerance = 256*EPS*scale + 32*sys.float_info.epsilon*max(*map(abs, pa), *map(abs, pb))
    if margin < -tolerance:
        return [f'{label}: independent kierunek normalnej A->B: margines={margin:.9g}, tolerancja={tolerance:.9g}'], 'blad'
    return [], 'remis' if abs(margin) <= tolerance else 'rozstrzygniety'


def independent(case, result, label):
    direction_errors, _ = normal_direction(case, result, label)
    if case.edge:
        return direction_errors
    errors = direction_errors
    a, ra, pa, b, rb, pb, separation, tolerance, world_tolerance = geometry(case)
    if abs(separation-SPECULATIVE) <= tolerance:
        errors.append(f'{label}: independent E09e39e6e9eff E7b57ae0c9d03 E59645de7bf77; case E003a8cb6dbd7 E20428480c3b6 Ea85d9e7fcd35 E3d1f2ae627a3')
    count = result[0]
    if count not in (0, 1, 2):
        return [f'{label}: independent pointCount poza 0..2: {count}']
    if case.category != 'prog-T' and (separation < SPECULATIVE-tolerance and count == 0
            or separation > SPECULATIVE+tolerance and count != 0):
        errors.append(f'{label}: independent SAT/odleglosc: separation={separation:.9g}, pointCount={count}')
    if count == 0:
        if any(result):
            errors.append(f'{label}: independent missing E09ae6811958c E003a8cb6dbd7 30 E2d15cb5f4011')
        return errors
    values = dict(zip(RESULT_FIELDS, (w if f == 'pointCount' or f.endswith(('.id', '.persisted'))
                                     else g.number(w) for f, w in zip(RESULT_FIELDS, result))))
    if not all(math.isfinite(v) for v in values.values()):
        return errors + [f'{label}: independent NaN/Inf']
    length = math.hypot(values['normal.x'], values['normal.y'])
    if abs(length-1) > 128*EPS:
        errors.append(f'{label}: independent normalna jednostkowa: {length:.9g}')
    for f, w in zip(RESULT_FIELDS, result):
        if (f == 'rollingImpulse' or f.endswith(('.normalImpulse', '.tangentImpulse',
                '.totalNormalImpulse', '.normalVelocity', '.persisted'))) and w != 0:
            errors.append(f'{label}: independent field initialized zero: {f}')
    for i in range(count):
        prefix = f'p{i}.'
        p = (values[prefix+'point.x'], values[prefix+'point.y'])
        sep = values[prefix+'separation']
        for polygon, radius, origin, anchor in ((a, ra, pa, 'anchorA'), (b, rb, pb, 'anchorB')):
                                                                                 
                                                                                  
            bound = abs(sep)/2 + radius + world_tolerance
            if boundary_distance(p, polygon) > bound:
                errors.append(f'{label}: independent {prefix}point poza brzegiem {anchor}: d={boundary_distance(p, polygon):.9g}, granica={bound:.9g}')
            for axis, coordinate, translation in zip(('x', 'y'), p, origin):
                actual = values[prefix+anchor+'.'+axis]
                if abs(actual-(coordinate-translation)) > world_tolerance:
                    errors.append(f'{label}: independent {prefix}{anchor}.{axis}')
    if min(values[f'p{i}.separation'] for i in range(count)) > SPECULATIVE+tolerance:
        errors.append(f'{label}: independent separation wszystkich punktow ponad progiem')
    return errors


def compare(c_text, duck_text, exit_code, cases, c_exit_code=0):
    c_rows, errors = parse_log(c_text, 'C')
    d_rows, other = parse_log(duck_text, 'Duckling')
    errors.extend(other)
    for label, code in (('C', c_exit_code), ('Duckling', exit_code)):
        if code != 0:
            errors.append(f'{label}: code exit {code}, expected 0')
    if len(cases) != g.COUNT or tuple(c.id for c in cases) != tuple(range(1, g.COUNT+1)):
        raise ValueError('Niepelny zbior odniesienia')
    matched = echoes = 0
    checked = {'C': 0, 'Duckling': 0}
    directions = {label: {'rozstrzygniety': 0, 'remis': 0, 'missing kontaktu': 0, 'blad': 0}
                  for label in checked}
    independent_total = sum(not c.edge for c in cases)
    witnesses = {c['id']: c for c in g.mutation_data()['cases']}
    table = ['| Id | Rodzaj | Wynik | Szczegoly |', '|---:|---|---|---|']
    for case in cases:
        issues = []
        c, d = c_rows.get(case.id), d_rows.get(case.id)
        for label, row in (('C', c), ('Duckling', d)):
            if row is None:
                issues.append(f'{label}: missing wyniku')
                continue
            for f, word, limit in zip(ALL_FIELDS, row, LIMITS):
                if word > limit:
                    issues.append(f'{label}: {f}: poza typem/zakresem: {word}')
            for f, actual, wanted in zip(g.INPUT_FIELDS, row[:80], case.words):
                if actual != wanted:
                    issues.append(f'{label}: echo {f}: 0x{actual:08x}, wejscie 0x{wanted:08x}')
            if case.id in witnesses and case.words == tuple(witnesses[case.id]['words']):
                                                                                   
                                                                                    
                for f, actual, wanted in zip(RESULT_FIELDS, row[80:], witnesses[case.id]['expected']):
                    if actual != wanted:
                        issues.append(f'{label}: swiadek mutacji {f}: 0x{actual:08x}, oczekiwano 0x{wanted:08x}')
            if all(0 <= w <= limit for w, limit in zip(row, LIMITS)):
                _, direction_status = normal_direction(case, row[80:], label)
                directions[label][direction_status] += 1
                failures = independent(case, row[80:], label)
                issues.extend(failures)
                if not case.edge and not failures:
                    checked[label] += 1
        if c is not None and d is not None:
            echoes += c[:80] == d[:80] == case.words
            for f, left, right in zip(ALL_FIELDS, c, d):
                if left != right:
                    issues.append(f'{f}: C=0x{left:08x}, Duckling=0x{right:08x}')
        if issues:
            errors.extend(f'Przypadek {case.id}: {issue}' for issue in issues)
        else:
            matched += 1
        table.append(f'| {case.id} | {case.category} | {('ROZNY' if issues else 'ZGODNY')} | '
                     + ('; '.join(issues) if issues else 'bity zgodne; geometria '+('pominieta: prog' if case.edge else 'OK'))+' |')
    report = '\n'.join(['# COMPARISON Efe03ba99697f', '', 'RESULT: '+('FAIL' if errors else 'OK'), '',
        f'E3e1ae1d296eb E279cf128155b: {matched}/{g.COUNT}; echo: {echoes}/{g.COUNT}.',
        f'independent Ecb29468a107b E13991feb1b0c: C {checked['C']}/{independent_total}; Duckling {checked['Duckling']}/{independent_total}.',
        f'Ostrze progu: {len(cases) - independent_total}; pomijane tylko we wlasnosciach f64 poza kierunkiem.',
        'E12156e921bdb 247: Eeaac2ece89f8 Ee5a4d416e55f E4a32c3c6b097 E46418b2eb8b9 E49773b3db27b E09ae6811958c E944d936358d6 E526ad5f91f71 T (1 case).',
        'E808c293d6b71 Ef1be686a60cf: E283ada7088c2 Ef65efa9e8831 E3d9fc4bde7ce Ef2f92dbcc8d7; Ef84e9e86f84a Ee34cfe5aca31 Ecd5b158f21b7 Ed37666485fff Ea7f03184d68d.',
        *(f'{label}: kierunek rozstrzygniety {d['rozstrzygniety']}, remisy {d['remis']}, missing kontaktu {d['missing kontaktu']}, bledy {d['blad']}.' for label,d in directions.items()), '', *table, '',
        f'Błędy: {len(errors)}', *('- '+e for e in errors), ''])
    return int(bool(errors)), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('c', 'duckling', 'wejscie', 'raport'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--kod-wyjscia', type=int, required=True)
    parser.add_argument('--kod-c', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        cases = g.read_inputs(args.wejscie)
        texts = []
        for path in (args.c, args.duckling):
            texts.append(path.read_text(encoding='ascii') if path.is_file() else '')
        code, report = compare(*texts, args.kod_wyjscia, cases, args.kod_c)
    except (OSError, ValueError, UnicodeError) as exc:
        code, report = 1, f'# COMPARISON Efe03ba99697f\n\nRESULT: FAIL\n\n{exc}\n'
    args.raport.parent.mkdir(parents=True, exist_ok=True)
    args.raport.write_text(report, encoding='utf-8')
    print(f'Wielokaty: code {code}; raport {args.raport}')
    return code


if __name__ == '__main__':
    sys.exit(main())
