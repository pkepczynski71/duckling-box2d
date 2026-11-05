pass                                                                       

                                                                          
                                                                           
                                                                          
   
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location('polaczenia_guard_model', HERE / 'model-polaczenia.py')
m = importlib.util.module_from_spec(_s); sys.modules[_s.name] = m; _s.loader.exec_module(m)
MANIFEST_SHA256 = 'd727b175f6514919979087b99113453a7f348b91fc39f5a6622bb86ce32bbc08'
_manifest_bytes = (HERE / 'polaczenia-przypadki.json').read_bytes()
m.require(hashlib.sha256(_manifest_bytes).hexdigest() == MANIFEST_SHA256, 'frozen14a manifest bytes changed')
MANIFEST = json.loads(_manifest_bytes.decode('utf-8'))


def op(code, *words):
    m.require(all(type(x) is int and 0 <= x <= 0xffffffff for x in words), 'input u32 words')
    if code < 200:
        m.require(len(words) <= 64, 'inherited width'); words = (*words, *(0 for _ in range(64 - len(words))))
    else:
        n = 4 + m.MUTATOR_ARITY[words[3]] if code == 203 else m.NEW_ARITY[code]
        m.require(len(words) == n, 'new op arity')
    return {'opcode': code, 'a': tuple(words)}


def body(reg, body_type=2, *, x=0, enabled=True):
    a = [0] * 56
    a[:8] = (0, reg, 0, body_type, m.bits(x), 0, m.bits(1), 0)
    a[13], a[17], a[18], a[19] = m.bits(1), 1, m.bits(.05), int(enabled)
    return op(90, *a)


def circle(reg, owner):
    a = [0] * 59
    a[:7] = (reg, 0, owner, 0, 0, 0, m.bits(1))
    a[44], a[45], a[50], a[52], a[53], a[55] = m.bits(1), m.bits(.6), 1, 0xffffffff, 0xffffffff, 1
    return op(40, *a)


def setup(*, contact=False, body_type=2, disabled=False, joint=True):
    operations = [op(0, 0, 0, 0, m.bits(200)), body(0, 0), body(1, body_type, x=.5 if contact else 2, enabled=not disabled)]
    if contact: operations += [circle(0, 0), circle(1, 1)]
    operations += [op(200, 0, 0)]
    if contact: operations += [op(202, 0, 14, 1)]
    if joint: operations += [op(201, 1, 0, 0, 1, 0, 0)]
    return operations


MUTATOR_ARGUMENTS = {0: (0, 0), 1: (0, 0), 2: (0,), 3: (m.bits(1), 0), 4: (1,),
    5: (1, 7, 9), 6: (), 7: (m.bits(60), m.bits(2)), 16: (m.bits(1),),
    17: (0, m.bits(100000)), 18: (1,), 19: (m.bits(2),), 20: (m.bits(1),),
    21: (1,), 22: (1,), 23: (m.bits(-3),), 24: (m.bits(1),)}
CREATE_FIELDS = {'anchorAx': 0, 'anchorAy': 1, 'anchorBx': 2, 'anchorBy': 3,
    'length': 4, 'hertz': 6, 'damping': 7, 'min': 9, 'max': 10, 'maxForce': 12, 'speed': 13}
SET_FIELDS = {0: {'x': 0, 'y': 1}, 1: {'x': 0, 'y': 1},
    7: {'hertz': 0, 'damping': 1}, 16: {'length': 0}, 17: {'min': 0, 'max': 1},
    19: {'hertz': 0}, 20: {'damping': 0}, 23: {'speed': 0}, 24: {'maxForce': 0}}


def guard_definition(row):
    key = row['key']; family = row['rodzina']; ga = [0] * 64
    ops = setup(); kind = 0; expected = (0, 0)
    if family == 'G1':
        kind, expected = 2, (1, 0)
        defect = row['defect']
        if defect == 'world-alive': ops += [op(211, 13, 0, 0)]
        elif defect.startswith('world-birth-'):
            ops += [op(211, 12, *( (1, 1) if defect.endswith('high') else (2, 0) ))]
        elif defect.startswith('owner-'):
            ops += [op(211, 2, *( (1, 1) if defect.endswith('high') else (2, 0) ))]; expected = (2, 0)
        elif defect.startswith('birth-'):
            ops += [op(211, 3, *( (4, 1) if defect.endswith('high') else (5, 0) ))]
        elif defect == 'range': ops += [op(211, 6, 0, 0), op(211, 4, 1, 0)]
        elif defect == 'alive': ops += [op(211, 5, 0, 0)]
        else:
            m.require(key == 'G1-wrap', 'known G1 key'); kind, ops = 1, []
    elif family == 'G2':
        kind, expected = 3, (2, 0); ga[2], ga[3] = 201, 1; ga[4:22] = m.default_description()
        end = 0 if '-A-' in key else 1
        ops += [op(211, 10 + end, *( (1, 1) if key.endswith('high') else (99, 0) ))]
    elif family == 'G3':
        kind, expected = 3, (5, 7); ga[2], ga[3] = 201, 1; ga[4:22] = m.default_description()
        ops += [op(211, 9, 0, 0)]
    elif family == 'G4':
        expected = (5, 6)
        if key.startswith('G4-203-'):
            k = int(key.rsplit('-', 1)[1]); ops += [op(203, 1, 0, 0, k, *MUTATOR_ARGUMENTS[k])]
        else:
            kind = 4; ga[2] = int(key.endswith('AxisA'))
    elif family == 'G5':
        kind, expected = 5, (7, 1); ops = setup(contact=True)
        route = key.split('-')[1:]; code = int(route[0]); k = int(route[1]) if len(route) > 1 else 0
        ga[2], ga[3] = code, k
        if code == 203: ga[4:4 + len(MUTATOR_ARGUMENTS[k])] = MUTATOR_ARGUMENTS[k]
        if code == 201: ga[4:7] = (0, 1, 0)
        if code == 207: ga[4] = 0
        ops += [op(83, 0, 1, 1, 0, 2, 1), op(86, 0, 0, 1, 1, 6, 0, 0), op(32, 0, m.bits(1 / 60), 1, 0)]
    elif family == 'G6':
        kind, expected = 6, (5, 10)
        ga[2] = int(row['route'].split('/')[0])
        if ga[2] == 201:
            desc = list(m.default_description()); defect = row['defect'].split(':')
            field, predicate = defect
            if field == 'range': desc[9:11] = (m.bits(2), m.bits(1))
            else: desc[CREATE_FIELDS[field]] = int(row['inputWord'], 16) if 'inputWord' in row else 0 if predicate == 'positive' else m.bits(-1)
            ga[4:22] = desc
        else:
            k = int(row['route'].split('/')[1]); ga[3] = k; args = list(MUTATOR_ARGUMENTS[k])
            field, predicate = row['defect'].split('.')
            if field == 'range': args = [m.bits(2), m.bits(1)]
            else: args[SET_FIELDS[k][field]] = int(row['inputWord'], 16) if 'inputWord' in row else 0 if predicate == 'positive' else m.bits(-1)
            ga[4:4 + len(args)] = args
    elif family == 'G8':
        kind = 7; ga[2] = 1; ga[3] = 1; expected = (3, 0)
        if key == 'G8-lastMAX': ga[:2] = (0xffffffff, 0xffffffff)
        elif key == 'G8-lastMAXminus1-one': ga[:2] = (0xfffffffe, 0xffffffff); expected = (0, 0)
        elif key == 'G8-carry': ga[:2] = (0xffffffff, 0); expected = (0, 0)
        elif key == 'G8-slot-overflow': ga[3] = 0x80000000
        else:
            kind = 3; ops = setup(contact=True, joint=False)
            ops += [op(31, 0, m.bits(1 / 60), 1), op(211, 0, 0xffffffff, 0xffffffff)]
            ga[2], ga[3] = 201, 1; ga[4:22] = m.default_description()
    elif family == 'G9':
        kind = 8; ga[1] = 1; expected = (5, 8)
        if 'positive-same-type' in key: ga[3] = 2; expected = (0, 0)
        elif 'positive-already-disabled' in key:
            ops = setup(disabled=True); ga[2] = 1; expected = (0, 0)
        elif 'positive-after-last-destroy' in key:
            ops += [op(205, 1, 0, 0)]; ga[3] = 1; expected = (0, 0)
        elif key.endswith('false'): ga[2] = 1
        else:
            target = {'static': 0, 'kinematic': 1, 'dynamic': 2}[key.rsplit('-', 1)[1]]
            if target == 2: ops = setup(body_type=1)
            ga[3] = target
    elif family == 'G10':
        kind, ops = 9, []; ga[0] = int(key.rsplit('-', 1)[1])
        ga[1] = 2 if '-Step-' in key else int('-per-color-' in key)
        expected = (3, 1) if ga[1] == 2 and ga[0] == 131060 else (0, 0)
    elif family == 'G11':
        kind = 10; ga[0] = 1 if 'bodyJoints' in key else 2 if 'description' in key else 0
                                                                              
                                                                              
                                                                            
                                                                             
        ops += [op(207, 0, 0, 0), op(207, 0, 0, 1), op(206, 1, 0, 1, 0, 2), op(32, 0, m.bits(1 / 60), 1, 0)]
    else: raise ValueError('unknown frozen guard family ' + family)
    m.require(len(ops) <= row['opMax'], 'guard opMax')
    return {'id': row['id'], 'key': key, 'kind': kind, 'ga': tuple(ga), 'ops': tuple(ops),
            'seedAfterSeq': 0, 'expected_status': expected[0], 'expected_reason': expected[1],
            'source': row, 'native_reachability': 'UNEXECUTED',
            'route_gap': 'G10 compact Step is internal helper, G11 distinct entrypoints need native routing proof' if family in ('G10', 'G11') else None}


def guards():
    result = tuple(guard_definition(r) for r in MANIFEST['guard'])
    m.require(len(result) == 156 and [x['id'] for x in result] == list(range(1, 157)), 'all frozen156')
    by_id = {r['id']: r for r in result}
    return tuple({**by_id[source], 'sourceId': source, 'sourceKey': by_id[source]['key'], 'localId': local}
                 for local, source in enumerate((*range(1,84), *range(85,157), 84), 1))


def encode_guard(items, *, decimal=False):
    pass                                                                       
    word = str if decimal else lambda x: f'{x:08x}'
    lines = [f'PORT14 A GUARD {len(items)}']
    for local, item in enumerate(items, 1):
        lines += [f'G14 {local} {item['kind']} {item['seedAfterSeq']} {len(item['ops'])}',
                  f'GA14 {local} ' + ' '.join(map(word, item['ga']))]
        for seq, operation in enumerate(item['ops'], 1):
            code, a = operation['opcode'], operation['a']
            prefix = f'O {seq} {code}' + (f' {len(a)}' if code >= 200 else '')
            lines.append(prefix + ' ' + ' '.join(map(word, a)))
    return ('\n'.join(lines) + '\n').encode('ascii')
