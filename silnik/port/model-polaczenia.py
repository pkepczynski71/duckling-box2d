pass                                                                          

                                                                           
                                                                            
                                                                             
   
from collections import Counter, defaultdict
import importlib.util
import math
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
                                                                            
                                                                           
                                                                           
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))
_spec = importlib.util.spec_from_file_location('polaczenia_base13', HERE / 'model-lancuchy.py')
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)
NULL = 0xffffffff
H = re.compile(r'[0-9a-f]{8}\Z')
D = re.compile(r'(?:0|[1-9][0-9]*)\Z')
J_ARITY = (8, 21, 17, 26, 50, 6, 19, 2, 20, 2, 16, 4)
F_ARITY = (5, 17, 26, 20, 16)
MUTATOR_ARITY = {0: 2, 1: 2, 2: 1, 3: 2, 4: 1, 5: 3, 6: 0, 7: 2,
                 16: 1, 17: 2, 18: 1, 19: 1, 20: 1, 21: 1, 22: 1, 23: 1, 24: 1}
NEW_ARITY = {200: 2, 201: 6, 202: 3, 204: 3, 205: 3, 206: 5, 207: 3,
             208: 1, 209: 4, 210: 3, 211: 3, 212: 3}
PRIVATE_J = {1, 2, 3, 5, 7, 10}
PRIVATE_L = {1, 2, 3, 4}
J8_PRIVATE = {1, 2, 3, 5, 7, 9, 10, 11, 12, 13}
OPEN_MODEL_OBLIGATIONS = (
    'BASE13 world/body/shape/contact/chain life history',
    'BASE13 geometry, contacts, solver sets/islands and stored copies with joints',
    'BASE13 chain create/material/ghost topology and semantic copy phases',
    'DIRECT F4/J10 input history',
    'full14a scene/branch/threshold and1200-Step history witnesses',
)


def require(condition, message):
    if not condition:
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


def add(a, b): return f32(f32(a) + f32(b))
def sub(a, b): return f32(f32(a) - f32(b))
def mul(a, b): return f32(f32(a) * f32(b))


def div(a, b):
    a, b = f32(a), f32(b)
    if b == 0:
        return math.nan if a == 0 else math.copysign(math.inf, a * math.copysign(1, b))
    return f32(a / b)


def wide(words):
    require(len(words) == 2, 'Key64 requires two words')
    return words[0] | words[1] << 32


def direct_fixture_number(last_ticket, world_record):
    pass                                                                  
    require(type(last_ticket) is int and 0 <= last_ticket <= 0xffffffffffffffff - 4, 'DIRECT F four tickets fit')
    require(world_record is not None and world_record[2] == 0, 'DIRECT F live W0')
    owner, birth = last_ticket + 1, last_ticket + 4
    require(wide(world_record[8:10]) == owner, 'DIRECT F exactly W/A/B/J ticket sequence')
    return (1, world_record[3] - 1, 1, 0, birth & NULL, birth >> 32, owner & NULL, owner >> 32)


def joint_fit(count):
    require(type(count) is int and 0 <= count <= 0x7fffffffffffffff, 'Jupper nonnegative i64')
    return count <= 16 or count // 4 + 3 <= 32767


def block_plan(count):
    pass                                                               
    require(type(count) is int and 0 <= count <= 0x7fffffffffffffff, 'planner count')
    size = count // 4 if count > 16 else 4
    n = 4 if count > 16 else (count + 3) // 4
    return tuple((j * size, count - j * size if j == n - 1 else size) for j in range(n))


def default_description():
    result = [0] * 18
    result[4], result[10] = 0x3f800000, 0x47c35000
    return tuple(result)


def domain_predicates(description):
    pass                                                                       
    require(len(description) == 18, 'description width18')
    names = {0: 'anchorAx', 1: 'anchorAy', 2: 'anchorBx', 3: 'anchorBy',
             4: 'length', 6: 'hertz', 7: 'damping', 9: 'min', 10: 'max',
             12: 'maxForce', 13: 'speed'}
    result = {}
    for i, name in names.items():
        value = number(description[i])
        result[name + '.finite'] = math.isfinite(value)
        if i == 4:
            result['length.positive'] = value > 0
        elif i in (6, 7, 9, 10, 12):
            result[name + '.nonnegative'] = value >= 0
    result['range.ordered'] = number(description[9]) <= number(description[10])
    return result


def parse(line):
    pass                                                                      
    raw = line.decode('ascii') if isinstance(line, bytes) else line
    require(raw.endswith('\n') and '\r' not in raw, 'output LF')
    require(re.fullmatch(r'[!-~]+(?: [!-~]+)*\n', raw) is not None, 'output ASCII/spacing')
    words = raw[:-1].split(' ')
    tag = words[0]
    if tag == 'PORT14':
        require(len(words) == 4 and words[1] == 'A' and words[2] in ('PUBLIC', 'DIRECT', 'GUARD'), 'PORT14 header')
        require(D.fullmatch(words[3]) is not None, 'header canonical N')
        require(1 <= int(words[3]) <= {'PUBLIC': 96, 'DIRECT': 128, 'GUARD': 156}[words[2]], 'header N')
        return tag, ('A', words[2], int(words[3]))
    if tag == 'Z13':
        require(len(words) == 21, 'Z13 arity18')
        require(all(D.fullmatch(w) and int(w) <= NULL for w in words[1:3]) and all(H.fullmatch(w) for w in words[3:]), 'Z13 canonical D/H8')
        return tag, (*map(int, words[1:3]), *(int(w, 16) for w in words[3:]))
    if tag not in {'E14', 'A14', 'J14', 'L14', 'T14', 'F14', 'EF14', 'G14', 'GA14'}:
        return base.parse13c(raw)
    fixed = {'A14': (4, 0), 'T14': (9, 0), 'G14': (4, 0), 'GA14': (1, 64)}
    if tag in fixed:
        d, n = fixed[tag]
    else:
        d = {'E14': 4, 'J14': 7, 'L14': 7, 'F14': 4, 'EF14': 4}[tag]
        require(len(words) > d and D.fullmatch(words[d]) is not None, tag + ' n')
        n = int(words[d])
    require(len(words) == 1 + d + n, tag + ' arity')
    values = []
    for i, word in enumerate(words[1:]):
        signed_color = tag == 'T14' and i == 4 and word == '-1'
        require(signed_color or (D if i < d else H).fullmatch(word) is not None, tag + ' canonical word')
        value = int(word, 10 if i < d else 16)
        require(value <= NULL, tag + ' u32')
        values.append(value)
    v = tuple(values)
    if tag == 'J14':
        require(v[5] < len(J_ARITY) and n == J_ARITY[v[5]], 'J14 group width')
        require(v[2] <= 5 and v[3] <= 16 and v[4] <= 255, 'J14 source/world/slot')
        g, source, world = v[5], v[2], v[3]
        require((g == 6 and source == 5 and world == 16) or
                (source in range(1, 5) and world == 16 and g in (0, 4)) or
                (source == 0 and g != 6 and (world < 16 or g in (8, 11))), 'J14 source/group/world')
    elif tag == 'L14':
        require(v[2] <= 4 and v[3] <= 16 and v[4] <= 4, 'L14 source/world/container')
        require((v[2] == 0 and v[3] < 16) or (v[2] in range(1, 5) and v[3] == 16 and v[4] == 0), 'L14 source/world')
        if v[4] == 0: require(n % 3 == 0, 'L0 raw triples')
        if v[4] == 4: require(v[5] == 0 and n >= 4, 'L4 header')
    elif tag in ('F14', 'EF14'):
        require(v[1] == 0 and v[2] < 5 and n == F_ARITY[v[2]], 'F14 fixture/group/arity')
    elif tag == 'E14':
        require((v[2] < 200 and n == 64) or v[2] in NEW_ARITY and n == NEW_ARITY[v[2]] or
                v[2] == 203 and n >= 4 and v[7] in MUTATOR_ARITY and n == 4 + MUTATOR_ARITY[v[7]], 'E14 opcode/arity')
    elif tag == 'A14':
        require(v[2] in range(8) and v[3] in (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 80, 81, 82, 83, 84, 85), 'A14 status/reason')
        require(v[2] != 0 or v[3] == 0, 'OK reason0')
    elif tag == 'T14':
        require(v[3] in range(4) and v[4] in range(-1, 12) and v[7] == 0 and v[8] in (0, 1), 'T14 fields')
        require((v[3] == 2) == bool(v[8]), 'T14 bias phase')
    return tag, v


def render(tag, values):
    if tag == 'PORT14': return 'PORT14 ' + ' '.join(map(str, values)) + '\n'
    if tag not in {'E14', 'A14', 'J14', 'L14', 'T14', 'F14', 'EF14', 'G14', 'GA14'}:
                                                                       
        if tag in base.SCHEMA13B or tag in base.SCHEMA13C:
            d = (base.SCHEMA13B | base.SCHEMA13C)[tag][0]
            return tag + ' ' + ' '.join(str(v) if i < d else f'{v:08x}' for i, v in enumerate(values)) + '\n'
        return base.base12_13b().format_record(tag, values)
    d = {'E14': 4, 'A14': 4, 'J14': 7, 'L14': 7, 'T14': 9, 'F14': 4, 'EF14': 4, 'G14': 4, 'GA14': 1}[tag]
    return tag + ' ' + ' '.join(str(v) if i < d else f'{v:08x}' for i, v in enumerate(values)) + '\n'


def project_line(line):
    tag, v = parse(line)
    if tag == 'T14' or tag == 'J14' and v[5] in PRIVATE_J or tag == 'L14' and v[4] in PRIVATE_L:
        return None
    if tag == 'J14' and v[5] == 8:
        return render(tag, (*v[:7], *(0 if i in J8_PRIVATE else x for i, x in enumerate(v[7:]))))
    if tag in {'Z13', 'PORT14', 'E14', 'A14', 'J14', 'L14', 'EF14', 'G14', 'GA14', 'CASE', 'ENDCASE', 'END'}:
        return line.decode('ascii') if isinstance(line, bytes) else line
    projected = base.projection13b_line(line.encode('ascii') if isinstance(line, str) else line)
    return projected.decode('ascii') if projected is not None else None


def _unique(rows, tag, key):
    found = {}
    for value in rows.get(tag, ()):
        k = key(value)
        require(k not in found, tag + ' duplicate key')
        found[k] = value
    return found


def check_base13_structure(records, *, observer=True):
    pass                                                                   

                                                                                                                                        
                                                                            
                                                                              
       
    rows = defaultdict(list)
    for tag, value in records: rows[tag].append(value)

    def indexed(tag, width):
        keys = [v[2:2+width] for v in rows[tag]]
        require(keys == sorted(set(keys)), tag + ' BASE13 sparse order/duplicate')
        return {v[2:2+width]: v[2+width:] for v in rows[tag]}

    cn, valid = indexed('CN13', 1), indexed('V13', 1)
    require(cn.keys() == valid.keys(), 'chain validity registers exactly CN13')
    require(all(reg[0] < 16 for reg in cn), 'chain register range')
                                                                            
    blocks = [(t,v) for t,v in records if t in ('COPY13','CV13','CE13','ENDCOPY13')]
    offset = 0; keys = []
    while offset < len(blocks):
        tag, start = blocks[offset]
        require(tag == 'COPY13' and len(start) == 4, 'chain copy block start')
        require(start[2] < 4 and start[3] in (0,1,2), 'chain copy register/phase')
        keys.append(start[2:])
        require(offset+1 < len(blocks) and blocks[offset+1][0] == 'CV13', 'chain copy CV missing')
        cv = blocks[offset+1][1]
        require(len(cv) == 18 and cv[:4] == start and cv[-1] <= 128, 'chain copy CV identity/count')
        count = cv[-1]; children = blocks[offset+2:offset+2+count]
        require(len(children) == count and all(t == 'CE13' and v[:5] == (*start,j)
                    for j,(t,v) in enumerate(children)), 'chain copy complete ordered CE')
        end = offset+2+count
        require(end < len(blocks) and blocks[end] == ('ENDCOPY13',start), 'chain copy ENDCOPY')
        offset = end+1
    require(keys == sorted(set(keys)), 'chain copy sparse register/phase order')
    if observer:
        chains, meta = indexed('CH13',2), indexed('CG13',2)
        segments, materials = indexed('CI13',3), indexed('CM13',3)
        pools, heads = indexed('IP13',1), indexed('BH13',2)
        require(chains.keys() == meta.keys(), 'chain occupied full CH/CG slot range')
                                                                     
        require(set(pools) == {(v[2],) for v in rows['W']}, 'chain pool every live Wreg')
        for (world,), pool in pools.items():
            next_index, count, *free = pool
            require(next_index <= 16 and len(free) == count and len(set(free)) == count,
                    'chain pool free stack count/duplicates')
            require({slot for w,slot in chains if w == world} == set(range(next_index)), 'chain pool full sparse slots')
            require(set(free) == {slot for (w,slot),p in chains.items() if w == world and not p[0]},
                    'chain pool free/live partition')
        require(all((w,) in pools for w,slot in chains), 'chain pool missing world')
        segment_keys, material_keys = set(),set()
        for key, chain in chains.items():
            world, slot = key
            alive, body, nxt, count, material_count = chain
            require(alive in (0,1) and meta[key][0] == alive, 'chain occupied agrees with alive')
            if not alive:
                require(chain[1:] == (0,0,0,0), 'dead chain canonical payload / metadata retained separately')
                continue
            require(1 <= count <= 128, 'chain segment count')
            require(1 <= material_count <= 128, 'chain material count')
            segment_keys.update((world,slot,j) for j in range(count))
            material_keys.update((world,slot,j) for j in range(material_count))
            require((world,body) in heads, 'body chain head required')
        require(set(segments) == segment_keys, 'chain segment complete ordered indices')
        require(set(materials) == material_keys, 'chain material complete ordered indices')
        for key, child in segments.items():
            require(child[0] == child[3]+1, 'chain segment raw/Number slot')
        for (world,body),(head,) in heads.items():
            current = head; seen = set()
            while current != NULL:
                require(current not in seen and (world,current) in chains, 'body chain cycle/range')
                seen.add(current); p = chains[world,current]
                require(p[0] == 1 and p[1] == body, 'body chain alive/owner')
                current = p[2]
            require(seen == {s for (w,s),p in chains.items() if w == world and p[0] and p[1] == body},
                    'body chain complete from real head')
    return {'base_structure_checked': True, 'complete': False,
            'open': ['BASE13 full life/history/geometry and copy mutation semantics']}


def check_base13_counts(records, ident, seq, *, observer=True, positive=0, ordinal=None):
    pass                                                                 

                                                            
                                                         
                                                                
       
    ordinal = seq if ordinal is None else ordinal
    old = base.base12_13b(); rows = defaultdict(list)
    for tag, value in records:
        require(value[:2] == (ident, seq), tag + ' BASE13 id/seq'); rows[tag].append(value)
    counts = Counter({tag: len(value) for tag, value in rows.items()})
    counts['E'] = counts['E14']                                                  
    for tag in ('Z8', 'Z9', 'Z10', 'Z11', 'I12', 'Z12', 'Z13'):
        require(len(rows[tag]) == 1, tag + ' required BASE13 record')
    require(rows['Z8'][0][8:26] == tuple(counts[t] for t in old.p11.p10.p9.p8.PUBLIC_COUNTS), 'Z8 all BASE public counts with E14')
    require(rows['Z9'][0][5:12] == tuple(counts[t] for t in old.p11.p10.p9.PUBCOUNTS), 'Z9 all BASE public counts')
    require(rows['Z9'][0][12:14] == (ordinal, ordinal), 'Z9 exact ordinals')
    require(rows['Z10'][0][2:6] == tuple(counts[t] for t in old.p11.p10.HIT_COUNTS), 'Z10 actual hit counts')
    require(rows['Z11'][0][2:] == (counts['SW11'], counts['GS11'], positive), 'Z11 counts/positive')
    names = ('AP12', 'WS12', 'NM12', 'UD12', 'HC12', 'HR12', 'HT12', 'CL12', 'CV12', 'VR12', 'EF12')
    require(rows['I12'][0][2:] == tuple(counts[t] for t in names), 'I12 every count including EF12')
    require(rows['Z12'][0][2:] == (positive, ordinal), 'Z12 counters')
    for tag, target in (('WS12', 'W'), ('HC12', 'W'), ('NM12', 'B'), ('EF12', 'S'), ('G', 'S')):
        require([v[2] for v in rows[tag]] == [v[2] for v in rows[target]], tag + ' every live register exactly once')
    require([v[2:4] for v in rows['UD12']] == [(kind, v[2]) for kind, tag in enumerate(('W', 'B', 'S')) for v in rows[tag]], 'UD12 all live objects/order')
    for tag in ('W', 'B', 'S', 'G', 'WS12', 'NM12', 'EF12', 'HC12'):
        keys = [v[2] for v in rows[tag]]
        require(keys == sorted(set(keys)), tag + ' BASE13 sparse order/uniqueness')
    z = rows['Z13'][0][2:]
    require(len(z) == 18, 'Z13 width18')
    require(z[0] == counts['A13'] and z[17] == counts['E14'], 'Z13 actual A13/E14 counts')
    require(rows['Z9'][0][14] == 14, 'PORT14 Z9 profile14')
    counted = 'CN13 CQ13 QL13 CS13 PC13 COPY13 CV13 CE13 ENDCOPY13'.split()
    require(z[1:10] == tuple(counts[t] for t in counted), 'Z13 independent fields h1..9')
    require(z[10] == counts['CN13'] and z[12:14] == (positive, ordinal), 'Z13 saved/positive/ordinal')
    require(z[14:17] == tuple(counts[t] for t in ('EP13B', 'EU13B', 'V13')), 'Z13 point/material/validity counts')
    if observer:
        for tag in ('I8', 'I9', 'I10', 'I11', 'IP12', 'I13'):
            require(len(rows[tag]) == 1, tag + ' BASE13 private required')
        for tag, names in (('I8', old.p11.I8_TAGS), ('I10', old.p11.p10.NEW_COUNTS), ('I11', old.p11.NEW_PRIVATE)):
            require(rows[tag][0][2:] == tuple(counts[t] for t in names), tag + ' private exact counts')
        require(rows['I9'][0][2:20] == tuple(counts[t] for t in old.p11.p10.p9.PRIVCOUNTS), 'I9 all private counts')
        require(rows['IP12'][0][2:] == (counts['NP12'],), 'IP12 every cold name')
        require(rows['I13'][0][2:] == tuple(counts[t] for t in ('CH13', 'CI13', 'CM13', 'BH13', 'IP13', 'CG13')), 'I13 all private chain groups')
        require(z[11] == sum(v[4] for v in rows['CH13']), 'Z13 actual live chain count')
    else:
        require(z[11] == sum(v[4] for v in rows['V13']), 'Z13 public live chain count')
        require(not any(rows[t] for t in base.PRIVATE13B), 'OBS0 exact inherited private exclusion')
        require(all(v[6:9] == (0, 0, 0) for v in rows['WS12']), 'OBS0 BASE tuning projection')
    structure = check_base13_structure(records, observer=observer)
    return {'base_counts_checked': True, 'base_structure_checked': structure['base_structure_checked'],
            'complete': False, 'full_ownership_ready': False,
            'unresolved': ['full BASE13 history/ownership model remains open']}


def check_joint_snapshot(records, ident, seq, operation, *, observer=True, positive=0, ordinal=None):
    pass                                                                     
    ordinal = seq if ordinal is None else ordinal
    rows = defaultdict(list)
    for tag, v in records:
        require(v[:2] == (ident, seq), tag + ' id/seq')
        rows[tag].append(v)
    code, a = operation['opcode'], tuple(operation['a'])
    require(rows['E14'] == [(ident, seq, code, len(a), *a)], 'exact E14 input echo')
                                                                   
    require(rows['A14'] and (len(rows['A14']) == 1 or rows['HT12']), 'A14 result/callback provenance')
    j = _unique(rows, 'J14', lambda v: v[2:6])
    l = _unique(rows, 'L14', lambda v: v[2:6])
    for group in range(12):
        keys = [v[2:5] for v in rows['J14'] if v[5] == group]
        require(keys == sorted(keys), 'J14 source/world/sparse order')
    for kind in range(5):
        keys = [(v[2], v[3], v[5]) for v in rows['L14'] if v[4] == kind]
        require(keys == sorted(keys), 'L14 source/world/parent order')
    summary = [v for v in rows['J14'] if v[5] == 8]
    require(len(summary) == 1 and summary[0][2:7] == (0, 16, 0, 8, 20), 'single J8 summary')
    h = summary[0][7:]
    jc = Counter(v[5] for v in rows['J14'])
    lc = Counter(v[4] for v in rows['L14'])
    require(h[:8] == tuple(jc[g] for g in range(8)), 'J8 all J0..7 counts')
    require(h[8:13] == tuple(lc[g] for g in range(5)) and h[13] == len(rows['T14']), 'J8 L/T counts')
    require(h[14:16] == (positive, ordinal), 'J8 positiveSteps/snapshotOrdinal')
    require(jc[9] == int(code == 212) and jc[10] == int(observer and code == 210), 'J9/J10 operation completeness')
    require(jc[11] <= 1, 'one helper result')
    require(h[17] == jc[6] and h[18] == len({v[2] for v in rows['J14'] if v[2] in range(1, 5)} | {v[2] for v in rows['L14'] if v[2]}), 'description/copy count')
    require(h[19] in (0, 1), 'fixtureApplied bool')
    for v in rows['J14']:
        g, payload = v[5], v[7:]
        if g == 0:
            require(payload[1] < 16 and payload[2] <= 65535, 'raw joint world/generation')
        if g == 6:
            require(payload[0] == 0, 'distance description type')
        if g == 9: require(all(x in (0, 1) for x in payload), 'validity bools')
        if g == 11: require(payload[0] in range(8) and payload[1] in (0, 1), 'helper status/accepted')
    ordinals = defaultdict(int)
    for v in rows['T14']:
        key = v[2:5]
        require(v[5] == ordinals[key], 'T14 ordinal from0 per phase/color')
        ordinals[key] += 1
    if not observer:
        require(not any(jc[g] for g in PRIVATE_J) and not any(lc[g] for g in PRIVATE_L) and not rows['T14'], 'OBS0 excludes exact private groups')
        require(all(h[i] == 0 for i in J8_PRIVATE), 'OBS0 J8 projection')
        return {'rows': rows, 'live': None, 'full_ownership_ready': False}
    sparse = {(v[3], v[4]): v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 5}
    joints = {(v[3], v[4]): v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 1}
    common = {(v[3], v[4]): v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 2}
    distance = {(v[3], v[4]): v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 3}
    heads = {(v[3], v[4]): v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 7}
    alive = {k for k, p in sparse.items() if p[0]}
    require(set(joints) == set(common) == set(distance) == alive, 'J1/J2/J3 exactly occupied sparse slots')
    require(h[16] == len(alive), 'J8 actual live joints')
    worlds = {v[3] - 1 for v in rows['W']}
    require({v[3] for v in rows['L14'] if v[4] == 4} == worlds, 'L4 every live world')
    require(all(w in worlds for w, slot in sparse), 'sparse belongs to live world')
    bodies = {(v[4], v[3] - 1): v[12] for v in rows['B']}
    require(set(heads) == set(bodies), 'J7 every live body')
    edge_seen = set()
    for (w, body), (head, count) in heads.items():
        seen, previous, key = [], NULL, head
        while key != NULL:
            slot, side = key >> 1, key & 1
            require((w, slot) in joints and key not in seen, 'joint body edge dead/cycle')
            p = joints[w, slot]; i = 6 + 3 * side
            require(p[i] == body and p[i + 1] == previous, 'joint edge owner/prev reciprocity')
            seen.append(key); edge_seen.add((w, key)); previous, key = key, p[i + 2]
        require(len(seen) == count, 'joint body head/count')
        require(set(seen) == {2 * s + side for (ww, s), p in joints.items() if ww == w for side in (0, 1) if p[6 + 3 * side] == body}, 'joint body edge complete')
    require(edge_seen == {(w, 2 * s + side) for w, s in alive for side in (0, 1)}, 'both joint edges reached')
    for (w, slot), p in joints.items():
        require(p[12] == slot and p[17] == 0 and p[18] == sparse[w, slot][1], 'joint id/type/generation reciprocity')
        require(p[19] in (0, 1) and p[20] in (0, 1), 'joint mark/collide bool')
        require(common[w, slot][:4] == (slot, p[6], p[9], 0), 'common joint endpoints/type')
    island_seen, set_seen, graph_seen = [], [], []
    for v in rows['L14']:
        source, w, kind, parent, n = v[2:7]; payload = v[7:]
        if source: continue
        if kind == 4:
            next_index, free_count, low, high, *free = payload
            require(free_count == len(free) and len(set(free)) == len(free), 'pool free count/duplicates')
            require({s for ww, s in sparse if ww == w} == set(range(next_index)), 'all sparse pool slots')
            require(set(free) == {s for (ww, s), p in sparse.items() if ww == w and p[0] == 0}, 'pool free/live partition')
            require(all(sparse[w, s][0] in (0, 1) and sparse[w, s][1] <= 65535 for s in range(next_index)), 'pool occupied/generation')
            continue
        if kind == 0: continue
        require(len(set(payload)) == len(payload), 'dense membership duplicates')
        for index, slot in enumerate(payload):
            require((w, slot) in joints, 'dense/list dead joint')
            p = joints[w, slot]
            if kind == 1:
                require(p[13] == parent and p[14] == (payload[index - 1] if index else NULL) and p[15] == (payload[index + 1] if index + 1 < n else NULL), 'island joint prev/next/order')
                island_seen.append((w, slot))
            if kind == 2:
                require(p[3] == parent and parent != 2 and p[4] == NULL and p[5] == index, 'set/local joint reciprocity')
                set_seen.append((w, slot))
            if kind == 3:
                require(parent < 12 and p[3:6] == (2, parent, index), 'color/local joint reciprocity')
                graph_seen.append((w, slot))
    require(len(set(set_seen + graph_seen)) == len(set_seen + graph_seen), 'joint dense uniqueness')
    require(set(set_seen + graph_seen) == alive, 'joint set/color partition')
    require(len(set(island_seen)) == len(island_seen) and set(island_seen) == {k for k, p in joints.items() if p[13] != NULL}, 'joint island partition')
    for w in worlds:
        require({v[5] for v in rows['L14'] if v[2] == 0 and v[3] == w and v[4] == 3} == set(range(12)), 'all twelve joint color lists')
    _occupation(rows, joints, bodies)
    return {'rows': rows, 'live': joints, 'sparse': sparse, 'full_ownership_ready': False}


def check_trace(records, operation, before=(), *, observer=True):
    trace = [v[2:] for t, v in records if t == 'T14']
    if not observer:
        require(not trace, 'OBS0 has no trace'); return
    code, a = operation['opcode'], operation['a']
    status = next(v[2] for t, v in reversed(records) if t == 'A14')
    if code == 210:
        phase = 3 if a[1] == 2 and a[2] == 0 else a[1]
        require(trace == [(0, phase, -1 if phase == 0 else 0, 0, 0, 0, a[2])], 'DIRECT one actual phase call')
        return
    if code not in (31, 32) or status or number(a[1]) <= 0:
        require(not trace, 'read/refusal/dt0 has no solver trace'); return
    worlds = {v[2]: v[3] - 1 for t, v in records if t == 'W'}
    require(a[0] in worlds, 'Step target live world')
    world = worlds[a[0]]
                                                                            
                                                                         
                                                          
    colors = [[] for _ in range(12)]; seen = set()
    for rr in (before, records):
        for tag, v in rr:
            if tag != 'L14' or v[2:5] != (0, world, 3): continue
            for slot in v[7:]:
                if slot not in seen: colors[v[5]].append(slot); seen.add(slot)
    expected = []
    for color in (-1, 11):
        slots = [s for c in range(11) for s in colors[c]] if color == -1 else colors[11]
        expected += [(0, 0, color, j, slot, 0, 0) for j, slot in enumerate(slots)]
    for substep in range(a[2]):
        for phase in (1, 2, 3):
            for color in (11, *range(11)):
                expected += [(substep, phase, color, j, slot, 0, int(phase == 2)) for j, slot in enumerate(colors[color])]
    require(trace == expected, 'actual joint prepare/warm/solve/relax completeness/order/substeps')


def _occupation(rows, joints, body_types):
    pass                                                                        
    world_map = {v[2]: v[3] - 1 for v in rows['W']}
    occupied = defaultdict(set)
    for (w, slot), p in joints.items():
        if p[3] != 2 or p[4] == 11: continue
        require(p[4] < 11, 'ordinary joint color')
        for body in (p[6], p[9]):
            require((w, body) in body_types, 'joint endpoint live')
            if body_types[w, body] != 0:
                require(body not in occupied[w, p[4]], 'joint/contact color conflict')
                occupied[w, p[4]].add(body)
                                                                        
    for v in rows['CT']:
        w, p = world_map[v[2]], v[4:]
        if p[2] != 2 or p[3] == 11: continue
                                                                            
        if p[3] == NULL: continue
        require(p[3] < 11, 'contact graph color')
        for body in (p[7], p[10]):
            require((w, body) in body_types, 'contact endpoint live')
            if body_types[w, body] != 0:
                require(body not in occupied[w, p[3]], 'joint/contact color conflict')
                occupied[w, p[3]].add(body)
    bitsets = {}
    for v in rows['GB']:
        w, color, p = world_map[v[2]], v[3], v[4:]
        require((w, color) not in bitsets, 'GB duplicate')
        if color == 11:
            require(p == (0, 0, 0), 'overflow has no bitset'); bitsets[w, color] = set(); continue
        require(p[0] == 1 and p[1] <= p[2] and len(p) == 3 + 2 * p[1], 'GB bitset framing')
        bitsets[w, color] = {64 * i + k for i in range(p[1]) for k in range(64) if wide(p[3 + 2*i:5 + 2*i]) >> k & 1}
        require(bitsets[w, color] == occupied[w, color], 'occupation contacts plus joints')
    require(set(bitsets) == {(w, c) for w in world_map.values() for c in range(12)}, 'all graph occupation records')


class JointModel:
    full_ownership_ready = False
    full_model_ready = False

    def __init__(self, observer=True, base_check=None):
        self.observer = observer
        self.base_check = base_check
        self.case = None
        self.previous = None
        self.positive = 0
        self.ordinal = 0
        self.saved = {}
        self.descriptions = {}
        self.numbers = {}
        self.fixture_applied = False
        self.last_ticket = None

    def check(self, ident, seq, operation, records, observer=None, *, private=None):
        pass                                                                    

                                                                           
                                                                            
                                                                            
           
        if ident != self.case:
            self.case = ident; self.previous = None; self.positive = 0; self.ordinal = 0; self.saved = {}
            self.descriptions = {}; self.numbers = {}
            self.fixture_applied = False
        require(observer is None or private is None or observer == private, 'conflicting observer arguments')
        observer = self.observer if observer is None and private is None else private if observer is None else observer
        records = tuple(records)
        result = next((v for t, v in reversed(records) if t == 'A14'), None)
        require(result is not None, 'missing A14')
        self.ordinal += 1
        a, code = tuple(operation['a']), operation['opcode']
        if code in (31, 32) and result[2] == 0 and number(a[1]) > 0: self.positive += 1
        checked = check_joint_snapshot(records, ident, seq, operation, observer=observer, positive=self.positive, ordinal=self.ordinal)
        rows = checked['rows']
        if code in (210, 211): self.fixture_applied = True
        summary = next(v[7:] for v in rows['J14'] if v[5] == 8)
        require(summary[19] == int(self.fixture_applied), 'fixtureApplied exact monotonic input history')
        check_trace(records, operation, self.previous or (), observer=observer)
        if code == 210 and self.previous is None:
                                                                          
                                                                            
                                                                               
            require(seq == 1 and ident >= 65 and self.last_ticket is not None, 'DIRECT F requires prior process ticket history')
            world = next((v for v in rows['W'] if v[2] == 0), None)
            require(world is not None, 'DIRECT F live W0')
            self.numbers[0] = direct_fixture_number(self.last_ticket, world)
            require(wide(rows['Z8'][0][-2:]) == self.last_ticket + 4, 'DIRECT F lastIssued advances exactly four')
        if code == 200 and result[2] == 0: self.descriptions[a[1]] = default_description()
        if code == 202 and result[2] == 0:
            require(a[0] in self.descriptions, 'description initialized before field update')
            desc = list(self.descriptions[a[0]]); desc[a[1]] = a[2]; self.descriptions[a[0]] = tuple(desc)
        observed_desc = {v[4]: v[8:] for v in rows['J14'] if v[2] == 5 and v[5] == 6}
        require(observed_desc == self.descriptions, 'all descriptions exactly own input history')
        identities = {v[4]: v[7:] for v in rows['J14'] if v[2] == 0 and v[5] == 0}
        if code == 201 and result[2] == 0:
            require(a[4] in identities, 'create target number present')
            fresh = identities[a[4]]
            require(rows['Z8'] and wide(fresh[4:6]) == wide(rows['Z8'][0][-2:]), 'joint birth is shared lastIssued')
            world = next((v for v in rows['W'] if v[2] == a[1]), None)
            require(world is not None and fresh[6:8] == world[8:10] and fresh[1] == world[3] - 1, 'joint owner is captured world ticket')
            self.numbers[a[4]] = fresh
            if self.previous:
                old_z = next((v for t, v in self.previous if t == 'Z8'), None)
                require(old_z is not None and wide(fresh[4:6]) == wide(old_z[-2:]) + 1, 'create exactly one shared ticket')
        elif code == 211 and a[0] in (1, 2, 3, 4) and 0 in self.numbers:
            changed = list(self.numbers[0])
            if a[0] == 1: changed[2] = a[1]
            if a[0] == 2: changed[6:8] = a[1:3]
            if a[0] == 3: changed[4:6] = a[1:3]
            if a[0] == 4: changed[3] = a[1]
            self.numbers[0] = tuple(changed)
        require(identities == self.numbers, 'Jreg historical raw/birth/owner identity / no restamp')
        live_views = [v for v in rows['J14'] if v[2] == 0 and v[5] == 4]
        require(len(live_views) == int(code == 204), 'READ exactly one J4, other operations none')
        if live_views and result[2] != 0:
            require(live_views[0][7:] == (0,) * 50, 'refused READ has zero view without getter')
        if observer and self.previous is not None:
            self._allocator_transition(code, a, result, checked)
        own = {source: tuple((t, v[3:]) for t, v in records if t in ('J14', 'L14') and v[2] == source)
               for source in range(1, 5)}
        initialized = set(self.saved)
        if result[2] == 0 and code in (206, 207) and (code == 207 or a[0] == 1):
            initialized.add((a[2] if code == 207 else a[4]) + 1)
        require({source for source, values in own.items() if values} == initialized, 'all and only initialized own copies')
                                                                            
                                                                            
        if code == 207 and result[2] == 0:
            source = a[2] + 1
            copied = [v for t, v in own[source] if t == 'J14' and v[2] == 0]
            require(len(copied) == 1 and copied[0] == (16, 0, 0, 8, *self.numbers[a[1]]), 'SAVE_VIEW exact historical number')
            require(len(own[source]) == 2 and own[source][1][0] == 'J14' and own[source][1][1][2:4] == (4, 50), 'SAVE_VIEW owns one identity and one view')
        self._copy_lists(rows, checked, code, a, result, observer)
        for source, before in self.saved.items():
            replacing = result[2] == 0 and (code == 207 and a[2] + 1 == source or code == 206 and a[0] == 1 and a[4] + 1 == source)
            editing = code == 209 and a[0] + 1 == source
            if not replacing and not editing: require(own[source] == before, 'historical own copy changed/omitted')
        if code == 209:
            source = a[0] + 1
            require(source in self.saved, 'edit initialized copy')
            group, field, word = a[1:]
            before = list(self.saved[source]); changed = False; offset = field
            for i, (t, v) in enumerate(before):
                if t != 'J14' or v[2] != group: continue
                width = len(v) - 4
                if offset >= width: offset -= width; continue
                require(v[4 + offset] != word, 'edit must change one word')
                p = list(v); p[4 + offset] = word; before[i] = (t, tuple(p)); changed = True; break
            require(changed and tuple(before) == own[source], 'copy edit exact field / other words stable')
        if result[2] != 0 and self.previous is not None:
                                                                               
                                                                        
            def state(rr):
                return tuple((t, v[2:]) for t, v in rr if t in ('J14', 'L14') and not (t == 'J14' and v[5] in (4, 8, 9, 10, 11)) and not (t == 'L14' and v[2] == 0 and v[4] == 0))
            require(state(records) == state(self.previous), 'semantic refusal changed joint world/copies')
            if code in range(200,213):
                                                                              
                                                                             
                                                                          
                                                                             
                retained = {'W','B','S','G','WS12','NM12','UD12','EF12','HC12','HR12',
                            'CN13','V13','CS13','CH13','CI13','CM13','BH13','IP13','CG13'}
                def base_state(rr):
                    return tuple((t,v[2:]) for t,v in rr if t in retained or
                                 t in ('COPY13','CV13','CE13','ENDCOPY13') and v[3] == 0 or
                                 t in ('CL12','CV12') and v[2] == 2 and v[4] == 0)
                require(base_state(records) == base_state(self.previous), 'semantic refusal changed BASE13 retained state')
                                                                            
                                                                               
                                                                             
        base_counts = (check_base13_counts(records, ident, seq, observer=observer,
                       positive=self.positive, ordinal=self.ordinal)
                       if any(t == 'Z8' for t,v in records) else None)
        base_result = self.base_check(ident, seq, operation, records, observer) if self.base_check is not None else None
        self.saved = {k: v for k, v in own.items() if v}; self.previous = records
        if rows['Z8']: self.last_ticket = wide(rows['Z8'][0][-2:])
        return {'joint_structure_checked': True,
                'base_checked': isinstance(base_result, dict) and base_result.get('complete') is True,
                'base_counts_checked': bool(base_counts) or isinstance(base_result, dict) and base_result.get('base_counts_checked') is True,
                'base_structure_checked': bool(base_counts and base_counts.get('base_structure_checked')),
                'complete': False, 'full_model_ready': False,
                'open_obligations': list(OPEN_MODEL_OBLIGATIONS),
                'full_ownership_ready': False, 'positive_steps': self.positive}

    def _copy_lists(self, rows, checked, code, a, result, observer):
        current = [v for v in rows['L14'] if v[2] == 0 and v[4] == 0]
        require(len(current) == int(code == 206), 'BODY_JOINTS exactly one current L0')
        if code != 206: return
        value = current[0]
        require(value[6] % 3 == 0, 'body list raw triples')
        if result[2]:
            require(value[6] == 0, 'refused BODY_JOINTS empty list'); return
        if observer:
                                                                        
            body = next((v for v in rows['B'] if v[2] == a[2]), None)
            require(body is not None, 'body list target register live')
            w, slot = body[4], body[3] - 1
            require(value[3] == w and value[5] == slot, 'body list target world/slot')
            head = next(v[7:] for v in rows['J14'] if v[2:6] == (0, w, slot, 7))
            key = head[0]; expected = []
            capacity = a[3] if a[0] == 0 else head[1]
            while key != NULL and len(expected) // 3 < capacity:
                joint_slot, side = key >> 1, key & 1
                p = checked['live'][w, joint_slot]
                expected += [joint_slot + 1, w, p[18]]
                key = p[8 + 3 * side]
            require(value[7:] == tuple(expected), 'body list exact head order/capacity/raw identity')
        if a[0] == 1:
            source = a[4] + 1
            listings = [v for v in rows['L14'] if v[2] == source]
            require(len(listings) == 1 and listings[0][3:] == (16, 0, value[5], value[6], *value[7:]), 'own list exact raw order and values')
            copies = [v for v in rows['J14'] if v[2] == source]
            require(len(copies) * 3 == value[6], 'own list one number per returned joint')
            for index, v in enumerate(copies):
                require(v[3:7] == (16, index, 0, 8), 'own list J0 framing/order')
                raw = value[7 + 3 * index:10 + 3 * index]
                require(v[7:10] == raw and v[10] + 1 == raw[0], 'own list raw/number slot')
                if observer:
                    meta = checked['sparse'][raw[1], raw[0] - 1]
                    require(v[7:] == (*raw, raw[0] - 1, *meta[2:]), 'own list current birth/owner despite raw generation wrap')
                matches = [p for p in self.numbers.values() if p[:3] == raw]
                if matches: require(v[7:] in matches, 'own list historical birth/owner')

    def _allocator_transition(self, code, a, result, checked):
        before = {v[3]: v[7:] for t, v in self.previous if t == 'L14' and v[2] == 0 and v[4] == 4}
        after = {v[3]: v[7:] for v in checked['rows']['L14'] if v[2] == 0 and v[4] == 4}
        sparse_before = {(v[3], v[4]): v[7:] for t, v in self.previous if t == 'J14' and v[2] == 0 and v[5] == 5}
        if code == 201 and result[2] == 0:
            fresh = self.numbers[a[4]]; w = fresh[1]
            require(w in before and w in after, 'create pool transition world')
            old, new = before[w], after[w]; slot = old[-1] if old[1] else old[0]
            require(fresh[0] == slot + 1 and fresh[3] == slot, 'free stack LIFO allocation slot')
            require(new[0] == old[0] + int(old[1] == 0) and new[1] == max(0, old[1] - 1) and new[4:] == (old[4:-1] if old[1] else ()), 'pool allocate next/free order')
            generation = ((sparse_before[w, slot][1] + 1) & 0xffff) if (w, slot) in sparse_before else 1
            require(checked['sparse'][w, slot] == (1, generation, *fresh[4:8]) and fresh[2] == generation, 'raw generation/new birth/owner')
        if code == 205 and result[2] == 0:
            number = self.numbers[a[2]]; w, slot = number[1], number[3]
            old, new = before[w], after[w]
            require(new[0] == old[0] and new[1] == old[1] + 1 and new[4:] == (*old[4:], slot), 'destroy appends free stack / no sort')
            p = sparse_before[w, slot]
            require(checked['sparse'][w, slot] == (0, *p[1:]), 'free slot retains birth/owner/generation')
        if code in (200, 202, 203, 204, 206, 207, 208, 209, 212) or result[2]:
            require(before == after, 'read/setter/copy/refusal changes no joint allocator/ticket')


                                                                        
                                                                  
Model14A = JointModel
