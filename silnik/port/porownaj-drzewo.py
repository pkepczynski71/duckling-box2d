pass                                                                               
import argparse
import importlib.util
import math
from pathlib import Path
import re
import sys

spec = importlib.util.spec_from_file_location('przypadki_drzewo', Path(__file__).with_name('przypadki-drzewo.py'))
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)

DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)\Z', re.ASCII)
D_FIELDS = ('root', 'nodeCount', 'nodeCapacity', 'freeList', 'proxyCount', 'height', 'areaRatio',
            'bounds.lowerX', 'bounds.lowerY', 'bounds.upperX', 'bounds.upperY', 'liveCount')
LEAF_FIELDS = ('n', 'proxyId', 'lowerX', 'lowerY', 'upperX', 'upperY',
               'categoryLow', 'categoryHigh', 'userDataLow', 'userDataHigh')
NULL = 0xffffffff


def schedule(case):
    for k in range(1, len(case.ops)+1):
        yield 'O', k
        if case.dump_every or k == len(case.ops):
            yield 'D', k


def issue(case_id, k, tag, message):
    return (case_id, k, 0 if tag == 'O' else 1, message)


def parse_log(text, label, cases):
    rows, errors = {}, []
    lines = text.splitlines()
    if not lines or lines[0] != f'PORT4 {len(cases)}':
        return rows, [issue(0, 0, 'O', f'{label}: case 0, operation 0, field E1e0584a25d9f: expected PORT4 {len(cases)}')]
    position = 1
    for case in cases:
        for tag, k in schedule(case):
            location = f'{label}: case {case.id}, operation {k}, field '
            if position >= len(lines):
                return rows, errors+[issue(case.id, k, tag, location+f'wiersz {tag}: missing')]
            tokens = lines[position].split(' ')
            if tokens[:3] != [tag, str(case.id), str(k)]:
                return rows, errors+[issue(case.id, k, tag, location+f'wiersz {tag}: zla kolejnosc/id/k lub missing, wiersz {position + 1}')]
            if any(not DECIMAL.fullmatch(t) or len(t) > 10 or int(t) >= 2**32 for t in tokens[3:]):
                return rows, errors+[issue(case.id, k, tag, location+'format: expected kanoniczne u32')]
            values = tuple(map(int, tokens[3:]))
            op = case.ops[k-1]
            if tag == 'O':
                count = 8 + (1 if op[0] in (0, 6) else 0)
                if op[0] == 5:
                    if len(values) < 11 or values[10] > g.MAX_OPS:
                        return rows, errors+[issue(case.id, k, tag, location+'hitCount: missing/zakres')]
                    count = 11+3*values[10]
            else:
                if len(values) < 12 or values[11] > g.MAX_OPS:
                    return rows, errors+[issue(case.id, k, tag, location+'liveCount: missing/zakres')]
                count = 12+10*values[11]
            if len(values) != count:
                return rows, errors+[issue(case.id, k, tag, location+f'dlugosc {tag}: {len(values)}, expected {count}')]
            rows[tag, case.id, k] = values
            position += 1
    if position >= len(lines) or lines[position] != f'END {len(cases)}':
        errors.append(issue(len(cases)+1, 0, 'O', f'{label}: field E0301844ccd8e: missing/E61fb2a973397 END {len(cases)}'))
    elif position+1 != len(lines):
        errors.append(issue(len(cases)+1, 0, 'O', f'{label}: field footer: nadmiarowe wiersze po END'))
    return rows, errors


def fields(tag, op, values):
    if tag == 'D':
        return (*D_FIELDS, *(f'live[{i}].{f}' for i in range(values[11]) for f in LEAF_FIELDS))
    names = tuple('echo.w'+str(i) for i in range(8))
    if op[0] == 0:
        return (*names, 'proxyId')
    if op[0] == 6:
        return (*names, 'rebuildCount')
    if op[0] == 5:
        return (*names, 'nodeVisits', 'leafVisits', 'hitCount',
                *(f'hit[{i}].{f}' for i in range(values[10]) for f in ('proxyId', 'userDataLow', 'userDataHigh')))
    return names


def query_properties(op, values, live, proxies):
    errors = []
    a = tuple(map(g.number, op[1:5]))
    mask = op[5] | op[6] << 32
    wanted = {(proxies[n], user & 0xffffffff, user >> 32)
              for n, (box, category, user) in live.items()
              if category & mask and g.overlaps(tuple(map(g.number, box)), a) and n in proxies}
    if any(n not in proxies for n in live):
        errors.append('proxyId: missing mapowania z UTWORZ')
    hits = tuple(values[j:j+3] for j in range(11, len(values), 3))
    if len(set(hits)) != len(hits) or set(hits) != wanted:
        errors.append('hits: Ee83afdc95e70 Ecd5b158f21b7 Ea4a9a8cc7ceb E70f0b8e6e134 z E62afabe75d0c Eb7d1f94c2e64 E5b9c8db6d09a Eab194ade142c')
    if values[9] != len(hits):
        errors.append('leafVisits: callback zawsze true, expected hitCount')
    nodes = 2*len(live)-1 if live else 0
    if not (len(hits) <= values[8] <= nodes) or (live and values[8] < 1):
        errors.append('nodeVisits: poza granicami liczby wezlow')
    return errors


def dump_properties(values, live, proxies):
    errors = []
    root, nodes, capacity, free, count, height, ratio = values[:7]
    expected_nodes = max(0, 2*len(live)-1)
    if count != len(live) or values[11] != len(live):
        errors.append('proxyCount/liveCount: E1a8ede14b808 z E8dc44deebc2b E5b9c8db6d09a')
    if nodes != expected_nodes:
        errors.append('nodeCount: expected 2*liveCount-1 (albo 0)')
    possible_capacity = 16
    while possible_capacity < capacity:
        possible_capacity += possible_capacity // 2
    if capacity != possible_capacity or capacity < nodes:
        errors.append('nodeCapacity: poza ciagiem wzrostu puli / za mala')
    if (nodes == capacity and free != NULL) or (nodes < capacity and not free < capacity):
        errors.append('freeList: poza pula / zly NULL')
    if (not live and root != NULL) or (live and root >= capacity):
        errors.append('root: poza pula / zly NULL')
    minimum_height = (len(live)-1).bit_length() if live else 0
    if not minimum_height <= height <= max(0, len(live)-1):
        errors.append('height: poza ceil(log2(liveCount))..liveCount-1')
    area_ratio = g.number(ratio)
    bounds = tuple(map(g.number, values[7:11]))
                                                                           
                                                                               
    point_root = bool(live) and all(map(math.isfinite, bounds)) and bounds[0] == bounds[2] and bounds[1] == bounds[3]
    if (not math.isfinite(area_ratio) and not (point_root and math.isnan(area_ratio))) or area_ratio < 0:
        errors.append('areaRatio: NaN poza punktowym korzeniem/Inf/ujemny')
    if (not all(map(math.isfinite, bounds)) or bounds[0] > bounds[2] or bounds[1] > bounds[3]):
        errors.append('bounds: NaN/Inf/niepoprawne')
    elif any(not g.contains(bounds, tuple(map(g.number, box))) for box, _, _ in live.values()):
        errors.append('bounds: E914a2a97819a Ecd5b158f21b7 E6c8a51b339c4 Eb7d1f94c2e64 E5b9c8db6d09a Eab194ade142c')
    if not live and (height != 0 or ratio != 0 or any(values[7:11])):
        errors.append('E005d19e74411: Ee173478dc9c8/E7f0378674df6/E77e0ab75bed8 E1b718fda965b E81f59408111d +0')
    actual_ids = []
    for i, (n, (box, category, user)) in enumerate(live.items()):
        row = values[12+10*i:22+10*i]
        if len(row) != 10:
            errors.append(f'live[{i}]: missing')
            continue
        wanted = (n, proxies.get(n), *box, category & 0xffffffff, category >> 32,
                  user & 0xffffffff, user >> 32)
        for name, actual, expected in zip(LEAF_FIELDS, row, wanted):
            if actual != expected:
                errors.append(f'live[{i}].{name}: odczyt niezgodny z wejsciem/UTWORZ')
                break
        if row[1] >= capacity:
            errors.append(f'live[{i}].proxyId: poza pula')
        actual_ids.append(row[1])
    if len(set(actual_ids)) != len(actual_ids):
        errors.append('proxyId: powtorzone zywe identyfikatory')
    return errors


def compare(c_text, duck_text, exit_code, cases, c_exit_code=0):
    cases = tuple(cases)
    crows, errors = parse_log(c_text, 'C', cases)
    drows, other = parse_log(duck_text, 'Duckling', cases)
    errors.extend(other)
    for label, code in (('C', c_exit_code), ('Duckling', exit_code)):
        if code:
            errors.append(issue(0, 0, 'O', f'{label}: code exit {code}, expected 0'))
    matched = echoed = same_rows = 0
    properties = {'C': 0, 'Duckling': 0}
    table = ['| E12156e921bdb | E6c1dd2e531d4 | O Ede7d1b721a1e D E13991feb1b0c | E931647da0d5b |', '|---:|---|---:|---|']
    for case in cases:
        before = len(errors)
        proxies = {'C': {}, 'Duckling': {}}
        property_ok = {'C': True, 'Duckling': True}
        case_echo = True
        case_same = 0
        created = 0
        for k, (op, live) in enumerate(zip(case.ops, g.states(case)), 1):
            tags = ('O', 'D') if case.dump_every or k == len(case.ops) else ('O',)
            for tag in tags:
                a, b = (rows.get((tag, case.id, k)) for rows in (crows, drows))
                if a is not None and b is not None:
                    if a == b:
                        case_same += 1
                    else:
                        names = fields(tag, op, a)
                        index = next((i for i, (left, right) in enumerate(zip(a, b)) if left != right), min(len(a), len(b)))
                        name = names[index] if index < len(names) else 'dlugosc'
                        left = f'0x{a[index]:08x}' if index < len(a) else 'MISSING'
                        right = f'0x{b[index]:08x}' if index < len(b) else 'MISSING'
                        errors.append(issue(case.id, k, tag, f'case {case.id}, operation {k}, field {tag}.{name}: C={left}, Duckling={right}'))
                for label, row in (('C', a), ('Duckling', b)):
                    location = f'{label}: case {case.id}, operation {k}, field {tag}.'
                    if row is None:
                        errors.append(issue(case.id, k, tag, location+'wiersz: missing'))
                        property_ok[label] = False
                        case_echo = False
                        continue
                    failures = []
                    if tag == 'O':
                        for i, (actual, wanted) in enumerate(zip(row[:8], op)):
                            if actual != wanted:
                                errors.append(issue(case.id, k, tag, location+f'echo.w{i}: 0x{actual:08x}, wejscie 0x{wanted:08x}'))
                                case_echo = False
                                property_ok[label] = False
                                break
                        if op[0] == 0:
                            proxy = row[8]
                            if proxy >= 2*g.MAX_OPS or any(proxies[label].get(n) == proxy for n in live if n != created):
                                failures.append('proxyId: zakres/powtorzenie zywego identyfikatora')
                            proxies[label][created] = proxy
                        elif op[0] == 5:
                            failures += query_properties(op, row, live, proxies[label])
                        elif op[0] == 6:
                            expected = len(live) if op[1] or not live else None
                            if (expected is not None and row[8] != expected) or (live and not 1 <= row[8] <= len(live)):
                                failures.append('rebuildCount: E9f6e664b314e E8dc44deebc2b Eab194ade142c')
                    else:
                        failures += dump_properties(row, live, proxies[label])
                    if failures:
                        property_ok[label] = False
                        errors.extend(issue(case.id, k, tag, location+'independent '+f) for f in failures)
            if op[0] == 0:
                created += 1
        for label in properties:
            properties[label] += property_ok[label]
        has_parse_error = any(e[0] == case.id for e in errors[:before])
        good = len(errors) == before and not has_parse_error
        matched += good
        echoed += case_echo
        same_rows += case_same
        table.append(f'| {case.id} | {case.category} | {case_same}/{sum((1 for _ in schedule(case)))} | {('OK' if good else 'BLAD')} |')
    errors.sort(key=lambda e: e[:3])
    total_rows = sum(sum(1 for _ in schedule(c)) for c in cases)
    report = '\n'.join(['# COMPARISON DRZEWA', '', 'RESULT: '+('FAIL' if errors else 'OK'), '',
        'PIERWSZY ROZJAZD: '+(errors[0][3] if errors else 'brak'), '',
        f'E3e1ae1d296eb E279cf128155b: {matched}/{len(cases)}; echo: {echoed}/{len(cases)}; O i D: {same_rows}/{total_rows}.',
        f'independent E50ca5bc0fbba: C {properties['C']}/{len(cases)}; Duckling {properties['Duckling']}/{len(cases)}.',
        'hits: E3bbf7a46fa40 Eb7d1f94c2e64 E5b9c8db6d09a Eab194ade142c E50e721e49c01 f64; E77e0ab75bed8, E828c68d0f522, Ee173478dc9c8 Ede7d1b721a1e E5886b07cc9a5 E99320f5fdd8d.',
        'Ec53d3253eca9, E79d0deec2515 E8206ecfd83a0 Ede7d1b721a1e E092c79e8f80e: E4a1a2bec026e 0. NOT E74a814645db2 exit.', '', *table, '',
        f'Bledy: {len(errors)} (Ed836b617be1c E1f9ad7941b0d 200)', *('- '+e[3] for e in errors[:200]), ''])
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
        texts = tuple(p.read_text(encoding='ascii') if p.is_file() else '' for p in (args.c, args.duckling))
        code, report = compare(*texts, args.kod_wyjscia, cases, args.kod_c)
    except (OSError, ValueError, UnicodeError) as exc:
        code, report = 1, f'# COMPARISON DRZEWA\n\nRESULT: FAIL\n\n{exc}\n'
    args.raport.parent.mkdir(parents=True, exist_ok=True)
    args.raport.write_text(report, encoding='utf-8')
    print(f'Drzewo: code {code}; raport {args.raport}')
    return code


if __name__ == '__main__':
    sys.exit(main())
