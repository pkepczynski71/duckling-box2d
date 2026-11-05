pass                                                            

                                                                             
                                                                     
   
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location('polaczenia_negative_data', HERE / 'polaczenia-oslony-dane.py')
d = importlib.util.module_from_spec(_s); sys.modules[_s.name] = d; _s.loader.exec_module(d)
m = d.m
REASONS = ('ASCII SPACING EMPTY_LINE CR EOF TAG N DECIMAL ARITY WORD ID OPCOUNT SEQ OPCODE '
           'REGISTER_RANGE REGISTER_UNINITIALIZED REGISTER_COLLISION BOOL ENUM UNUSED DOMAIN PROFILE '
           'TRAILING_DATA POINT MATERIAL CACHE ROTATION PHASE POPULATION COPY MODE').split()
VARIANTS = ('PUBLIC', 'DIRECT-common', 'DIRECT-solver', 'GUARD')


def fixtures():
    common = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, m.bits(60), m.bits(2), 0, m.bits(1), 0)
    distance = (m.bits(1), 0, 0, m.bits(.005), m.bits(100000), 0, 0,
                m.bits(1), m.bits(2), m.bits(3), m.bits(4), *(0 for _ in range(15)))
    a = (0, 0, m.bits(1), 0, 0, 0, 0, 0, 0, 0)
    b = (m.bits(2), 0, m.bits(1), 0, 0, 0, m.bits(2), 0, m.bits(1), 0)
    state = (0, 0, 0, 0, 0, 0, m.bits(1), 0)
    return ((m.bits(1 / 60), m.bits(60), 0, 0, 2), common, distance, (*a, *b), (*state, *state))


def encode(variant, ops, *, decimal=False, fixtures_override=None):
    word = str if decimal else lambda x: f'{x:08x}'
    profile = 'DIRECT' if variant.startswith('DIRECT') else variant
    ident = 65 if variant == 'DIRECT-solver' else 1
    lines = [f'PORT14 A {profile} {ident}']
    if ident == 65:
                                                                    
                                                                            
        for i in range(1, 65):
            lines += [f'C {i} 1', f'O 1 200 2 {word(0)} {word(0)}']
    if profile == 'GUARD':
        lines += [f'G14 1 0 0 {len(ops)}', 'GA14 1 ' + ' '.join([word(0)] * 64)]
    else: lines += [f'C {ident} {len(ops)}']
    if ident == 65:
        for group, words in enumerate(fixtures_override or fixtures()):
            lines.append(f'F14 65 0 {group} {len(words)} ' + ' '.join(map(word, words)))
    for seq, o in enumerate(ops, 1):
        code, a = o['opcode'], o['a']
        lines.append(f'O {seq} {code}' + (f' {len(a)}' if code >= 200 else '') + ' ' + ' '.join(map(word, a)))
        for index, point in enumerate(o.get('points', ())):
            lines.append(f'P13B {ident} {seq} {index} ' + ' '.join(map(word, point)))
        for index, material in enumerate(o.get('materials', ())):
            lines.append(f'U13B {ident} {seq} {index} ' + ' '.join(map(word, material)))
    return ('\n'.join(lines) + '\n').encode('ascii')


def catalogue():
    return [{'reason': 'INPUT_' + r, 'stderr': 'PORT14A: INPUT_' + r + '\n', 'exit': 2,
             'variants': [{'variant': v, 'state': 'unexecuted', 'proof': None} for v in VARIANTS]} for r in REASONS]


def cases(decimal=False):
    pass                                                                        

                                                                           
                                                                             
       
    result = []
    for variant in VARIANTS:
        solver = variant == 'DIRECT-solver'
        ident = 65 if solver else 1
        ops = [d.op(210, 0, 0, 0)] if solver else d.setup()
        good = encode(variant, ops, decimal=decimal)
        lines = good.splitlines(keepends=True)
                                                                          
                                                                           
        oi = len(lines) - 1
        seq = len(ops)
        word = str if decimal else lambda x: f'{x:08x}'
        def operation(code, words, n=None, at_seq=seq):
            return (f'O {at_seq} {code}' + (f' {(len(words) if n is None else n)}' if code >= 200 else '') +
                    ' ' + ' '.join(map(word, words)) + '\n').encode('ascii')
        def add(reason, data, prefix_ops=0, suffix='', reference=None, scope=None):
            if scope is None:
                scope = ('header' if reason in ('ASCII', 'SPACING', 'EMPTY_LINE', 'CR', 'TAG', 'N', 'DECIMAL') else
                         'case' if reason in ('ID', 'OPCOUNT') else 'trailing' if reason == 'TRAILING_DATA' else 'operation')
            result.append({'key': variant + '/' + reason + suffix, 'variant': variant,
                'reason': 'INPUT_' + reason, 'input': data, 'code': 2,
                'stderr': ('PORT14A: INPUT_' + reason + '\n').encode('ascii'),
                'prefix_operations': prefix_ops, 'native_state': 'unexecuted',
                'reference_input': good if reference is None else reference, 'failure_scope': scope})
        def replace(reason, line, prefix=None):
            changed = list(lines); changed[oi] = line
            add(reason, b''.join(changed), 64 if solver else seq - 1 if prefix is None else prefix)
        for reason, bad in (
            ('ASCII', b'\xef\xbb\xbf' + good), ('SPACING', good.replace(b'PORT14 A', b'PORT14  A', 1)),
            ('EMPTY_LINE', b'\n' + good), ('CR', good.replace(b'\n', b'\r', 1)),
            ('TAG', good.replace(b'PORT14', b'PORT15', 1)),
            ('N', good.replace(lines[0], f'PORT14 A {('DIRECT' if solver or variant == 'DIRECT-common' else variant)} 0\n'.encode(), 1)),
            ('DECIMAL', good.replace(lines[0], lines[0].rstrip(b'\n') + b'0\n', 1))):
                                                                    
            if reason == 'DECIMAL': bad = good.replace(lines[0], lines[0].rsplit(b' ', 1)[0] + b' 01\n', 1)
            add(reason, bad)
        add('EOF', good[:good.rfind(b'\n', 0, len(good) - 1) + 1], 64 if solver else seq - 1)
        replace('ARITY', operation(204, (1, 0), n=3))
                                                                         
                                                                       
                                                                   
        prefix = f'O {seq} 200 2 {word(0)} '.encode('ascii')
        for length, reason in ((2048, 'WORD'), (2049, 'ARITY')):
            changed = list(lines); changed[oi] = prefix + b'0' * (length - len(prefix)) + b'\n'
            add(reason, b''.join(changed), 64 if solver else seq - 1, '/line' + str(length), scope='operation')
        replace('WORD', (f'O {seq} 204 3 ' + ('4294967296' if decimal else '0000000A') + ' ' + word(0) + ' ' + word(0) + '\n').encode())
        replace('SEQ', operation(210 if solver else 204, (0, 0, 0) if solver else (1, 0, 0), at_seq=seq + 1))
        replace('OPCODE', f'O {seq} 199 0\n'.encode())
                                                                              
        replace('MODE', operation(201, (2, 0, 0, 1, 0, 0)))
        replace('ENUM', operation(203, (1, 0, 0, 25)))
                                                                    
        replace('PROFILE', operation(201 if solver else 210, (0, 0, 0, 1, 0, 0) if solver else (0, 0, 0)))
        if solver:
            replace('PHASE', operation(210, (0, 2, 1)))
                                                                           
                                                                           
            replace('REGISTER_RANGE', operation(200, (0, 16)))
            replace('REGISTER_UNINITIALIZED', operation(205, (1, 0, 255)))
            replace('COPY', operation(208, (3,)))
            replace('UNUSED', operation(210, (0, 0, 1)))
            for reason, group, index, value in (('BOOL', 0, 2, 2), ('DOMAIN', 0, 0, 0), ('ROTATION', 3, 2, 0)):
                groups = [list(g) for g in fixtures()]; groups[group][index] = value
                add(reason, encode(variant, ops, decimal=decimal, fixtures_override=groups), 64, scope='fixture')
        else:
            replace('REGISTER_RANGE', operation(200, (0, 16)))
            replace('REGISTER_UNINITIALIZED', operation(205, (1, 0, 255)))
            replace('BOOL', operation(202, (0, 5, 2)))
            replace('UNUSED', operation(5, (*[0] * 63, 0x80000000)))
            replace('DOMAIN', operation(209, (0, 0, 0, 0)))                                        
            result.pop()                                                        
            replace('COPY', operation(208, (3,)))
            replace('ROTATION', operation(4, (0, 1, 0, 0, 0, 0, *([0] * 58))))
            replace('PHASE', operation(43, (0,) * 64))
                                                                                
            collision_ops = [*ops, d.op(201, 1, 0, 0, 1, 0, 0)]
            add('REGISTER_COLLISION', encode(variant, collision_ops, decimal=decimal), len(ops),
                reference=encode(variant, [*ops, d.op(201, 1, 0, 0, 1, 1, 0)], decimal=decimal))
            domain_ops = [*ops[:-1], d.op(202, 0, 4, 0), d.op(201, 0, 0, 0, 1, 0, 0)]
            add('DOMAIN', encode(variant, domain_ops, decimal=decimal), len(domain_ops) - 1,
                reference=encode(variant, [*domain_ops[:-1], d.op(201, 1, 0, 0, 1, 0, 0)], decimal=decimal))
            population = [*ops, d.op(0, 1, 0, 0, m.bits(200)), d.op(0, 2, 0, 0, m.bits(200))]
            add('POPULATION', encode(variant, population, decimal=decimal), len(population) - 1,
                reference=encode(variant, [*population[:-1], d.op(200, 0, 1)], decimal=decimal))
            chain = d.op(100, 1, 0, 0, 0, 4, 0, 1, 0, 0, 0, 1, 0, 0xffffffff, 0xffffffff, 0, 0)
            chain['points'] = tuple((m.bits(x), 0) for x in (0, 1, 2, 3))
            chain['materials'] = ((m.bits(.6), 0, 0, 0, 0, 0),)
            chain_input = encode(variant, [*ops, chain], decimal=decimal)
            chain_seq = len(ops) + 1
            add('POINT', chain_input.replace(f'P13B 1 {chain_seq} 0 '.encode(), f'P13B 1 {chain_seq} 1 '.encode(), 1), len(ops), reference=chain_input)
            add('MATERIAL', chain_input.replace(f'U13B 1 {chain_seq} 0 '.encode(), f'U13B 1 {chain_seq} 1 '.encode(), 1), len(ops), reference=chain_input)
                                                                         
        ci = next(i for i, line in enumerate(lines) if line.startswith(b'G14 ' if variant == 'GUARD' else f'C {ident} '.encode()))
        changed = list(lines); ws = changed[ci].split(); ws[1] = str(ident + 1).encode(); changed[ci] = b' '.join(ws) + b'\n'
        add('ID', b''.join(changed), 64 if solver else 0)
        changed = list(lines); ws = changed[ci].split(); ws[-1] = b'65' if variant == 'GUARD' else b'33' if solver else b'0'; changed[ci] = b' '.join(ws) + b'\n'
        add('OPCOUNT', b''.join(changed), 64 if solver else 0)
        if not solver: add('TRAILING_DATA', good + b'\n', len(ops))
                                                                             
                                                                           
    m.require(len(result) <= 256 and len({r['key'] for r in result}) == len(result), 'bounded unique parser corpus')
    m.require(all(r['prefix_operations'] <= 64 for r in result), 'at most64 preceding O')
    return tuple(result)


CACHE_PATH = 'polaczenia-z5/cache-proof.json'
CACHE_SHA = 'ce5f5893a43044a60070aff2e26a86ba89d3b455b45dee225feea5bf1bbd0c7e'


def inherited_cache():
    pass                                                                       
    try:
        raw = (HERE / CACHE_PATH).read_bytes()
    except FileNotFoundError:
        return None
    if hashlib.sha256(raw).hexdigest() != CACHE_SHA:
        return None
    return json.loads(raw)


def route_gaps():
    actual = {(r['variant'], r['reason']) for r in cases()}
    cache = inherited_cache()
    rows = []
    for v in VARIANTS:
        for reason in REASONS:
            if (v, 'INPUT_' + reason) in actual: continue
            proof = None
            if reason == 'CACHE' and cache is not None:
                rows.append({'variant': v, 'reason': 'INPUT_CACHE', 'state': 'inherited',
                    'proof': {'path': CACHE_PATH, 'receipt_sha256': CACHE_SHA},
                    'why': 'one prior PORT13A initial/cache-u8 trial, not a PORT14 execution'})
                continue
            if v == 'DIRECT-solver':
                proof = {
                    'REGISTER_COLLISION': 'KONTRAKT14 §7: fixed F initializes one raw joint, no D register. Only210 is legal; it never creates a destination register. A colliding201 needs an initialized Dsource, which no legal solver prefix can create.',
                    'TRAILING_DATA': 'KONTRAKT14 §4/7/10: first solver CASE is65; each prior64 common CASE needs at least1 O and solver CASE needs at least1 prepare O. A trailing fault therefore follows at least65 O, exceeding the negative-corpus bound64; not a relaxation of that bound.',
                    'POINT': 'KONTRAKT14 §7: solver CASE65..128 accepts only five F groups and210; P13B exists only in inherited100 chain input. No legal solver operation reads P13B.',
                    'MATERIAL': 'KONTRAKT14 §7: solver CASE65..128 accepts only five F groups and210; U13B exists only in inherited100 chain input. No legal solver operation reads U13B.',
                    'POPULATION': 'KONTRAKT14 §7/9: solver population is fixed B2/S0/C0/J1 by F; F has no population-count field and210 allocates no bodies/shapes/contacts/joints. Any allocating opcode is rejected PROFILE before final population checks; N overflow is INPUT_N.',
                }.get(reason)
            rows.append({'variant': v, 'reason': 'INPUT_' + reason, 'state': 'unavailable' if proof else 'missing',
                'proof': proof, 'why': proof or ('prior PORT13A cache proof missing/altered; no14a input, no120/new seam allowed' if reason == 'CACHE' else 'needs native reachability/priority proof; not a skip/pass')})
    return rows


def compare_prefix(actual, reference, item):
    pass                                                                    

                                                                             
                                                                           
                                                                            
       
    scope, count = item['failure_scope'], item['prefix_operations']
    target_id = 65 if item['variant'] == 'DIRECT-solver' else 1
    emitted = size = lines = 0; sha = hashlib.sha256()
    if scope != 'header':
        for raw in reference:
            words = raw.split(); tag = words[0] if words else b''
            case_tag = b'G14' if item['variant'] == 'GUARD' else b'CASE'
            if scope == 'case' and tag == case_tag and int(words[1]) == target_id: break
            if scope == 'operation' and tag == b'E14' and emitted == count: break
            if scope == 'fixture' and tag == b'EF14' and int(words[1]) == target_id: break
            if scope == 'trailing' and tag == b'END': break
            m.require(tag != b'END', 'legal reference ended before intended fatal point')
            m.require(actual.readline() == raw, 'fatal prefix bytes differ at line ' + str(lines + 1))
            if tag == b'E14': emitted += 1
            sha.update(raw); size += len(raw); lines += 1
        m.require(emitted == count, 'fatal prefix actual operation count')
    m.require(actual.read(1) == b'', 'fatal output after exact legal prefix')
    return {'prefix_bytes_compared': True, 'prefix_equal': True,
            'prefix_bytes': size, 'prefix_lines': lines, 'prefix_sha256': sha.hexdigest()}


def semantic_domain_cases(decimal=False):
    pass                                                                       

                                                                          
                                                                           
       
    result = []
    for item in d.guards():
        if item['source']['rodzina'] != 'G6': continue
        ga = item['ga']
        if ga[2] == 201:
            ops = d.setup(joint=False)
            for field, (old, word) in enumerate(zip(m.default_description(), ga[4:22])):
                if word != old: ops.append(d.op(202, 0, field, word))
            ops.append(d.op(201, 1, 0, 0, 1, 0, 0))
            refused_seq = len(ops)
            ops += [d.op(200, 0, 1), d.op(201, 1, 0, 0, 1, 1, 1), d.op(212, 1, 0, 1)]
        else:
            kind = ga[3]; ops = d.setup()
            ops.append(d.op(203, 1, 0, 0, kind, *ga[4:4 + m.MUTATOR_ARITY[kind]]))
            refused_seq = len(ops); ops.append(d.op(212, 1, 0, 0))
        result.append({'key': item['key'], 'source_id': item['id'], 'ops': tuple(ops),
                       'input': encode('PUBLIC', ops, decimal=decimal), 'refused_seq': refused_seq,
                       'expected_status': (5, 10), 'continuation_seq': len(ops), 'native_state': 'unexecuted'})
    m.require(len(result) == 88, 'all frozen88 G6 semantic word histories')
    return tuple(result)
