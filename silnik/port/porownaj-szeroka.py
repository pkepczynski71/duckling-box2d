pass                                                                 

                                                                              
                                                                               
   
import argparse
import importlib.util
import math
from pathlib import Path
import re
import sys

_spec = importlib.util.spec_from_file_location('broad_inputs', Path(__file__).with_name('przypadki-szeroka.py'))
g = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = g
_spec.loader.exec_module(g)


class Invalid(ValueError):
    pass


def require(condition, case, k, field, detail=''):
    if not condition:
        raise Invalid(f'case {case}, operation {k}, field {field}' + (f': {detail}' if detail else ''))


class Reader:
    def __init__(self, text):
        normalized = text.replace('\r\n', '\n')
        require(text.isascii() and '\r' not in normalized, 0, 0, 'zapis', 'dozwolone tylko ASCII, LF lub CRLF')
        self.lines = normalized.split('\n') if normalized else []
        if self.lines and self.lines[-1] == '':
            self.lines.pop()
        self.pos = 0
        self.records = []

    def peek(self):
        return self.lines[self.pos].split(' ', 1)[0] if self.pos < len(self.lines) else None

    def take(self, tag, case=0, k=0, length=None, prefix=()):
        require(self.pos < len(self.lines), case, k, tag, 'missing wiersza')
        tokens = self.lines[self.pos].split(' ')
        self.pos += 1
        require(tokens[0] == tag, case, k, tag, f'wiersz {self.pos}: otrzymano {tokens[0]!r}')
        require(all(re.fullmatch(r'0|[1-9][0-9]{0,9}', t) for t in tokens[1:]), case, k, tag, 'niekanoniczna liczba / spacja')
        values = tuple(map(int, tokens[1:]))
        require(all(v <= g.NULL for v in values), case, k, tag, 'poza u32')
        if length is not None:
            require(len(values) == length, case, k, tag+'.długość', f'{len(values)} zamiast {length}')
        require(values[:len(prefix)] == tuple(prefix), case, k, tag+'.prefiks', f'{values[:len(prefix)]} zamiast {tuple(prefix)}')
        self.records.append((tag, values))
        return values


def hash_set(reader, case, k, kind, expected, initial, previous_capacity):
    v = reader.take('HS', case, k, prefix=(case, k, kind))
    require(len(v) >= 5, case, k, 'HS.nagłówek')
    capacity, count = v[3:5]
    require(capacity >= initial and capacity & (capacity-1) == 0 and capacity >= previous_capacity,
            case, k, 'HS.capacity')
    require(capacity <= max(initial, 4*max(1, len(expected), 8128)), case, k, 'HS.capacity', 'E4dae9a1553e6 E13512bb12c29')
    require(len(v) == 5+3*capacity, case, k, 'HS.sloty.długość')
    found = set()
    for i in range(capacity):
        lo, hi, hashed = v[5+3*i:8+3*i]
        key = g.join(lo, hi)
        require((key == 0) == (hashed == 0), case, k, f'HS.slot[{i}].pusty')
        if hashed:
            require(key not in found, case, k, f'HS.slot[{i}].duplikat')
            found.add(key)
    require(count == len(expected) == len(found) and found == expected, case, k, 'HS.zbiór')
    require(2*count <= capacity, case, k, 'HS.obciążenie')
    return capacity


def tree_state(reader, c, k, t, live, keys):
    v = reader.take('T', c.id, k, length=13, prefix=(c.id, k, t))
    root, nodes, capacity, free, count, height = v[3:9]
    ns = [n for n in live if c.bodies[c.shapes[n][0]] == t]
    require(count == len(ns) and nodes == (2*count-1 if count else 0), c.id, k, 'T.count')
    capacities = [16]
    while capacities[-1] < 512:
        capacities.append(capacities[-1]+capacities[-1]//2)
    require(capacity in capacities and capacity >= nodes, c.id, k, 'T.nodeCapacity')
    require(free == g.NULL or free < capacity, c.id, k, 'T.freeList')
    if count:
        require(root < capacity and (count-1).bit_length() <= height <= max(0, count-1), c.id, k, 'T.root/height')
        box = tuple(map(g.number, v[9:13]))
        require(all(map(math.isfinite, box)) and box[0] <= box[2] and box[1] <= box[3], c.id, k, 'T.bounds')
        require(all(g.contains(box, tuple(map(g.number, live[n]))) for n in ns), c.id, k, 'T.bounds.zawieranie')
        require(all(keys[n] >> 2 < capacity for n in ns), c.id, k, 'T.proxyId')
    else:
        require(root == g.NULL and height == 0 and v[9:13] == (0, 0, 0, 0), c.id, k, 'T.puste')


def query_record(reader, c, k, q, move, key, tree, box, mask, live, keys):
    v = reader.take('Q', c.id, k, prefix=(c.id, k, q, move, key, tree))
    require(len(v) >= 9, c.id, k, 'Q.nagłówek')
    visits, leaves, count = v[6:9]
    require(len(v) == 9+2*count, c.id, k, 'Q.trafienia.długość')
    expected = {n for n in live if c.bodies[c.shapes[n][0]] == tree
                and g.join(*c.shapes[n][1:3]) & mask
                and g.overlaps(tuple(map(g.number, live[n])), tuple(map(g.number, box)))}
    got = set()
    for i in range(count):
        proxy, n = v[9+2*i:11+2*i]
        require(n in expected and n not in got and keys[n] >> 2 == proxy, c.id, k, f'Q.hit[{i}]')
        got.add(n)
    require(got == expected and leaves == count, c.id, k, 'Q.zbiór/leafVisits')
    total = sum(c.bodies[c.shapes[n][0]] == tree for n in live)
    require((visits == 0 if not total else 1 <= visits <= 2*total-1) and visits >= count, c.id, k, 'Q.nodeVisits')


def validate_output(text, rows, plain=False):
    r = Reader(text)
    r.take('PORT5', length=1, prefix=(len(rows),))
    for c in rows:
        r.take('I', c.id, length=1+len(c.header), prefix=(c.id, *c.header))
        if not c.mode:
            for n, t in enumerate(c.bodies):
                r.take('EB', c.id, length=3, prefix=(c.id, n, t))
            for n, s in enumerate(c.shapes):
                r.take('ES', c.id, length=10, prefix=(c.id, n, *s))
            for tag, table in (('EJ', c.joints), ('EF', c.rules)):
                for n, triple in enumerate(table):
                    r.take(tag, c.id, length=5, prefix=(c.id, n, *triple))
        live, keys, moved, pairs, direct = {}, {}, set(), set(), set()
        pair_capacity, pair_index = 0, 0
        capacities = {0: 16, 1: 32, 2: c.capacity}
        for k, w in enumerate(c.ops, 1):
            t, n = w[:2]
            has_result = t in ((0, 1, 2) if c.mode else (0, 7, 8))
            v = r.take('O', c.id, k, length=18+int(has_result), prefix=(c.id, k))
            for i, (got, wanted) in enumerate(zip(v[2:18], w)):
                require(got == wanted, c.id, k, f'O.echo.w{i}', f'{got} zamiast {wanted}')
            result = v[18] if has_result else None
            if c.mode:
                key = g.join(*w[1:3])
                if t in (0, 1, 2):
                    require(result == int(key in direct), c.id, k, 'O.wynik-zbioru')
                    if t == 0:
                        direct.add(key)
                    elif t == 1:
                        direct.discard(key)
                else:
                    direct.clear()
                if c.dump or k == len(c.ops):
                    capacities[2] = hash_set(r, c.id, k, 2, direct, c.capacity, capacities[2])
                continue
            if t == 0:
                body_type = c.bodies[c.shapes[n][0]]
                require(result != g.NULL and result & 3 == body_type and result not in keys.values(), c.id, k, 'O.proxyKey')
                keys[n] = result
                live[n] = w[2:6]
                if body_type or w[6]:
                    moved.add(n)
            elif t == 1:
                require(not any(n in p for p in pairs), c.id, k, 'DESTROY.incydentne-pary')
                del live[n]; del keys[n]; moved.discard(n)
            elif t in (2, 3):
                live[n] = w[2:6]; moved.add(n)
            elif t == 4:
                moved.add(n)
            elif t == 7:
                require(result == int(g.overlaps(tuple(map(g.number, live[n])), tuple(map(g.number, live[w[2]])))),
                        c.id, k, 'O.TestOverlap')
            elif t == 8:
                require(result == n, c.id, k, 'O.GetShapeIndex')
            elif t == 9:
                pair = tuple(sorted((n, w[2])))
                require(pair in pairs, c.id, k, 'RELEASE.istnienie')
                pairs.remove(pair)
            elif t == 10:
                query_record(r, c, k, 0, g.NULL, g.NULL, n, w[2:6], g.join(*w[6:8]), live, keys)
            elif t == 5:
                before = len(moved)
                                                                               
                all_candidates = g.candidates(c, live, moved, keys)
                eligible = {p: owner for p, owner in all_candidates.items() if p not in pairs and g.allowed(c, *p)}
                expected_filters = {tuple(sorted(p, key=keys.__getitem__)) for p in eligible}
                expected = {p: owner for p, owner in eligible.items()
                            if g.decision(c, *sorted(p, key=keys.__getitem__))}
                move_indices = {}
                if not plain:
                    q = 0
                    seen_movers = set()
                    for move_index in range(before):
                                                                                      
                        require(r.peek() == 'Q', c.id, k, 'Q.brak-ruchu')
                        tokens = r.lines[r.pos].split(' ')
                        require(len(tokens) >= 6 and re.fullmatch(r'0|[1-9][0-9]{0,9}', tokens[5]), c.id, k, 'Q.queryProxyKey')
                        key = int(tokens[5])
                        owners = [x for x in moved if keys[x] == key]
                        require(len(owners) == 1 and owners[0] not in seen_movers, c.id, k, 'Q.ruch')
                        owner = owners[0]; seen_movers.add(owner); move_indices[owner] = move_index
                        trees = (1, 0, 2) if c.bodies[c.shapes[owner][0]] == 2 else (2,)
                        for tree in trees:
                            query_record(r, c, k, q, move_index, key, tree, live[owner], g.ALL, live, keys)
                            q += 1
                    got_filters = set()
                    for f in range(len(expected_filters) if c.custom else 0):
                        v = r.take('F', c.id, k, length=10, prefix=(c.id, k, f))
                        a, world_a, gen_a, b, world_b, gen_b, answer = v[3:10]
                        pair = (a-1, b-1)
                        require(pair in expected_filters and pair not in got_filters, c.id, k, 'F.para/kolejność-argumentów')
                        require(world_a == world_b == c.world and gen_a == c.shapes[a-1][7]
                                and gen_b == c.shapes[b-1][7] and answer == g.decision(c, a-1, b-1), c.id, k, 'F.id/decyzja')
                        got_filters.add(pair)
                    got_requests = set()
                    for j in range(len(expected)):
                        v = r.take('C', c.id, k, length=6, prefix=(c.id, k, j))
                        move_index, a, b = v[3:6]
                        pair = tuple(sorted((a, b)))
                        require(pair in expected and pair not in got_requests and keys[a] < keys[b], c.id, k, 'C.para')
                        require(move_index == move_indices[expected[pair]], c.id, k, 'C.moveIndex')
                        got_requests.add(pair)
                if before:
                    pair_capacity, pair_index = 16*before, len(expected)
                expected_u = (int(before != 0), before, pair_capacity, pair_index,
                              max(0, len(expected)-pair_capacity) if before else 0, len(expected))
                r.take('U', c.id, k, length=8, prefix=(c.id, k, *expected_u))
                pairs.update(expected)
                moved.clear()
            if c.dump or k == len(c.ops):
                r.take('D', c.id, k, length=8, prefix=(c.id, k, len(moved), len(moved), len(pairs), len(live), pair_capacity, pair_index))
                m = r.take('M', c.id, k, prefix=(c.id, k, len(moved)))
                require(len(m) == 3+len(moved) and len(set(m[3:])) == len(moved)
                        and set(m[3:]) == {keys[x] for x in moved}, c.id, k, 'M.skład/duplikaty')
                for tree in range(3):
                    tree_state(r, c, k, tree, live, keys)
                for shape in sorted(live):
                    r.take('P', c.id, k, length=11,
                           prefix=(c.id, k, shape, keys[shape], *live[shape], *c.shapes[shape][1:3], shape))
                capacities[0] = hash_set(r, c.id, k, 0, {keys[x]+1 for x in moved}, 16, capacities[0])
                pair_keys = {(a << 32) | b for a, b in pairs}
                capacities[1] = hash_set(r, c.id, k, 1, pair_keys, 32, capacities[1])
                                                                                             
                ps = tuple(v for p in sorted(pairs) for v in p)
                r.take('PS', c.id, k, length=3+2*len(pairs), prefix=(c.id, k, len(pairs), *ps))
    r.take('END', length=1, prefix=(len(rows),))
    require(r.pos == len(r.lines), 0, 0, 'END', 'nadmiar wierszy')
    return r.records


def field_name(tag, i):
    names = {
        'Q': ('id', 'k', 'q', 'moveIndex', 'queryProxyKey', 'treeType', 'nodeVisits', 'leafVisits', 'hitCount'),
        'F': ('id', 'k', 'f', 'index1A', 'worldA', 'generationA', 'index1B', 'worldB', 'generationB', 'decision'),
        'C': ('id', 'k', 'c', 'moveIndex', 'shapeIndexA', 'shapeIndexB'),
        'U': ('id', 'k', 'hadWork', 'moveCountAtEntry', 'movePairCapacity', 'movePairIndex', 'heapPairCount', 'requestCount'),
        'D': ('id', 'k', 'moveCount', 'moveSetCount', 'pairSetCount', 'liveCount', 'movePairCapacity', 'movePairIndex'),
        'HS': ('id', 'k', 'setKind', 'capacity', 'count'),
        'T': ('id', 'k', 'type', 'root', 'nodeCount', 'nodeCapacity', 'freeList', 'proxyCount', 'height', 'lowerX', 'lowerY', 'upperX', 'upperY'),
    }
    if tag == 'O':
        return ('id', 'k')[i] if i < 2 else (f'echo.w{i - 2}' if i < 18 else 'wynik')
    if tag == 'Q' and i >= 9:
        return f'hit[{(i - 9) // 2}].'+('proxyId' if (i-9) % 2 == 0 else 'shapeIndex')
    if tag == 'M' and i >= 3:
        return f'proxyKey[{i - 3}]'
    if tag == 'HS' and i >= 5:
        return f'slot[{(i - 5) // 3}].'+('keyLow', 'keyHigh', 'hash')[(i-5) % 3]
    return names.get(tag, ())[i] if i < len(names.get(tag, ())) else f'słowo[{i}]'


def first_difference(a, b, label):
    for row in range(max(len(a), len(b))):
        if row >= min(len(a), len(b)):
            tag, values = (a if row < len(a) else b)[row]
            case = values[0] if tag not in ('PORT5', 'END') and values else 0
            k = values[1] if tag in ('O', 'Q', 'F', 'C', 'U', 'D', 'M', 'T', 'P', 'HS', 'PS') and len(values) > 1 else 0
            return f'{label}: case {case}, operation {k}, field record: missing/E71c5f077b5b7 E924ffcababf8 {row + 1}'
        ta, va = a[row]; tb, vb = b[row]
        if (ta, va) == (tb, vb):
            continue
        case = va[0] if ta not in ('PORT5', 'END') and va else 0
        k = va[1] if ta in ('O', 'Q', 'F', 'C', 'U', 'D', 'M', 'T', 'P', 'HS', 'PS') and len(va) > 1 else 0
        if ta != tb:
            return f'{label}: case {case}, operation {k}, field record: {ta} / {tb}'
        for i in range(max(len(va), len(vb))):
            if i >= min(len(va), len(vb)) or va[i] != vb[i]:
                x = va[i] if i < len(va) else 'MISSING'; y = vb[i] if i < len(vb) else 'MISSING'
                return f'{label}: case {case}, operation {k}, field {ta}.{field_name(ta, i)}: {x} / {y}'
    return None


def compare(c_text, duck_text, plain_text, rows, codes=(0, 0, 0)):
    errors, parsed = [], []
    for name, code in zip(('C', 'Duckling', 'C E283ada7088c2 Eae242858339f'), codes):
        if code:
            errors.append(f'{name}: code wykonania {code} (oczekiwano 0)')
    for name, text, plain in (('C', c_text, False), ('Duckling', duck_text, False), ('C E283ada7088c2 Eae242858339f', plain_text, True)):
        try:
            parsed.append(validate_output(text, rows, plain))
        except (Invalid, ValueError, IndexError, KeyError) as exc:
            errors.append(f'{name}: {exc}')
            parsed.append(None)
    if parsed[0] is not None and parsed[1] is not None:
        error = first_difference(parsed[0], parsed[1], 'C / Duckling')
        if error:
            errors.append(error)
    if parsed[0] is not None and parsed[2] is not None:
                                                                              
        direct_queries = {(c.id, k) for c in rows if not c.mode
                          for k, w in enumerate(c.ops, 1) if w[0] == 10}
        def common(rs):
            return [(tag, values) for tag, values in rs if tag not in ('F', 'C')
                    and (tag != 'Q' or values[:2] in direct_queries)]
        error = first_difference(common(parsed[0]), common(parsed[2]), 'C / C E283ada7088c2 Eae242858339f')
        if error:
            errors.append(error)
    return errors


def main():
    parser = argparse.ArgumentParser()
    for name in ('c', 'duckling', 'c-bez', 'wejscie', 'raport'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('kod-c', 'kod-wyjscia', 'kod-c-bez'):
        parser.add_argument('--'+name, type=int, default=0)
    args = parser.parse_args()
    try:
        rows = g.load(args.wejscie)
        def read(path):
            return path.read_bytes().decode('ascii') if path.is_file() else ''
        errors = compare(read(args.c), read(args.duckling), read(args.c_bez), rows,
                         (args.kod_c, args.kod_wyjscia, args.kod_c_bez))
    except (OSError, ValueError) as exc:
        errors = [f'Wejście/odczyt: {exc}']
    lines = ['# Ecc4c18509694 E434f66e44101 5', '', 'RESULT: '+('FAIL' if errors else 'OK'), '']
    if errors:
        lines += ['Pierwszy rozjazd: '+errors[0], '', *errors[1:]]
    else:
        lines += [f'{len(rows)}/{len(rows)} E279cf128155b; E092c79e8f80e Ede7d1b721a1e E03b382aabe85 E2b114cbf1f18 Ed0013c2e0a38 E50e721e49c01 Ed0013c2e0a38.',
                  f'E86031a23dbd0 E903a1d34bcab C: {len(rows)}/{len(rows)}, Duckling: {len(rows)}/{len(rows)}, C E283ada7088c2 Eae242858339f: {len(rows)}/{len(rows)}.',
                  'C / C E283ada7088c2 Eae242858339f: E2d6c9a90dd38 E0967115f2813 E65bb7eaa2651 Ede7d1b721a1e Eb5b2babb1a82; E5a6df127ff40 Ea09b5116269e E15a205acbc24 E50e721e49c01 C.']
    args.raport.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
