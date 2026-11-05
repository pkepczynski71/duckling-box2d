pass                                                                     

                                                                            
                                                                           
                                                                 
   
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location('polaczenia_branch_m', HERE / 'model-polaczenia.py')
m = importlib.util.module_from_spec(_s); sys.modules[_s.name] = m; _s.loader.exec_module(m)

                                                                      
SOURCE_RANGES = {
    'src/joint.h': ((19, 90), (247, 278)),
    'src/joint.c': ((24, 30), (101, 404), (702, 885), (887, 1128), (1130, 1521)),
    'src/distance_joint.c': ((20, 198), (215, 489)),
    'src/constraint_graph.c': ((214, 322),),
    'src/island.c': ((264, 425), (454, 460), (503, 527), (656, 663), (776, 832)),
    'src/solver_set.c': ((120, 131), (191, 191), (350, 396), (427, 613)),
    'src/solver.c': ((131, 180), (761, 807), (967, 1093), (1237, 1246), (1331, 1348),
                     (1361, 1363), (1410, 1415), (1432, 1440), (1498, 1511), (1537, 1569), (1578, 1675)),
    'src/world.c': ((168, 169), (321, 321), (344, 344), (1678, 1708)),
    'src/body.c': ((356, 368), (1064, 1088), (1106, 1139), (1170, 1217), (1248, 1276),
                   (1595, 1622), (1666, 1715), (1830, 1897)),
    'include/box2d/id.h': ((68, 73), (144, 155)),
    'include/box2d/types.h': ((514, 524), (533, 590)),
}


def source_operators(text):
    pass                                                                
    pattern = r'//[^\n]*|/\*[\s\S]*?\*/|\#[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|<<=|>>=|<<|>>|<=|>=|==|!=|->|\+=|-=|\*=|/=|\+\+|--|&&|\|\||[<>=?:]'
    result = []
    for found in re.finditer(pattern, text):
        token = found.group()
        if token.startswith(('//', '/*', '#', '"', "'")): continue
        kind = ('comparison' if token in ('<', '>', '<=', '>=', '==', '!=') else
                'shift' if token in ('<<', '>>', '<<=', '>>=') else
                'assignment' if token in ('=', '+=', '-=', '*=', '/=', '++', '--') else
                'predicate' if token in ('&&', '||', '?') else 'other')
        result.append({'token': token, 'start': found.start(), 'end': found.end(),
                       'line': text.count('\n', 0, found.start()) + 1, 'kind': kind})
    return result


def source_candidates(source):
    pass                                                                         
    source = Path(source); rows = []
    for name, ranges in SOURCE_RANGES.items():
        raw = (source / name).read_bytes(); text = raw.decode('utf-8')
        sha = hashlib.sha256(raw).hexdigest()
        found_tokens = source_operators(text)
                                                                              
                                                                         
        code = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"',
                      lambda x: ''.join('\n' if c == '\n' else ' ' for c in x.group()), text)
        for expression, kind in ((r'\bif\s*\(', 'branch'), (r'\bb2\w+\s*\(', 'call'), (r'\breturn\b[^;]*;', 'return')):
            for hit in re.finditer(expression, code):
                found_tokens.append({'token': hit.group().strip(), 'start': hit.start(), 'end': hit.end(),
                    'line': text.count('\n', 0, hit.start()) + 1, 'kind': kind})
        for found in sorted(found_tokens, key=lambda x: (x['start'], x['kind'])):
            if not any(lo <= found['line'] <= hi for lo, hi in ranges) or found['kind'] == 'other': continue
            rows.append({'id': f'C:{name}:{found['line']}:{found['start']}:{found['kind']}', 'c_file': name,
                'c_line': found['line'], 'source_sha256': sha, **found,
                'classification': 'candidate', 'state': 'open', 'atom_ids': [],
                'reason': 'Requires semantic classification (14a/shared/other type/debug/equivalent); not silently excluded'})
    return rows


def _dot(a, b): return m.add(m.mul(a[0], b[0]), m.mul(a[1], b[1]))
def _cross(a, b): return m.sub(m.mul(a[0], b[1]), m.mul(a[1], b[0]))
def _vsub(a, b): return tuple(m.sub(x, y) for x, y in zip(a, b))
def _vadd(a, b): return tuple(m.add(x, y) for x, y in zip(a, b))


def rotate(q, v):
    c, s = q; x, y = v
    return m.sub(m.mul(c, x), m.mul(s, y)), m.add(m.mul(s, x), m.mul(c, y))


def separation_predicates(common, distance, states, *, phase='solve', body_sims=None):
    pass                                                                   

                                                                       
                                                                       
                                                                     
       
    m.require(len(common) == 17 and len(distance) == 26 and len(states) == 16, 'predicate input widths')
    c, d, s = [list(map(m.number, x)) for x in (common, distance, states)]
    if phase == 'prepare':
        m.require(body_sims is not None and len(body_sims) == 20, 'prepare needs actual F3/body sims')
        b = list(map(m.number, body_sims))
        r_a = rotate(b[2:4], _vsub(c[4:6], b[4:6]))
        r_b = rotate(b[12:14], _vsub(c[6:8], b[14:16]))
        delta = _vsub(b[16:18], b[6:8]); mass = (b[8], b[18], b[9], b[19])
        sep = _vadd(_vsub(r_b, r_a), delta)
    else:
                                                                            
        for start, index in ((0, distance[11]), (8, distance[12])):
            if index == m.NULL: s[start:start + 8] = (0., 0., 0., 0., 0., 0., 1., 0.)
        r_a, r_b = rotate(s[6:8], d[13:15]), rotate(s[14:16], d[15:17])
        ds = _vadd(_vsub(s[12:14], s[4:6]), _vsub(r_b, r_a))
        sep = _vadd(d[17:19], ds); mass = c[8:12]
    ll = _dot(sep, sep); length = m.f32(ll ** .5)
    normalizable = length >= m.number(0x34000000)                                     
    inv = m.div(1., length) if normalizable else 0.
    axis = tuple(m.mul(inv, v) for v in sep) if normalizable else (0., 0.)
                                                                        
    cr_a, cr_b = _cross(r_a, axis), _cross(r_b, axis)
    k = m.add(m.add(m.add(mass[0], mass[1]), m.mul(m.mul(mass[2], cr_a), cr_a)), m.mul(m.mul(mass[3], cr_b), cr_b))
    values = {'separation.x': sep[0], 'separation.y': sep[1], 'lengthSquared': ll,
              'length': length, 'k': k, 'lowerC': m.sub(length, d[3]),
              'upperC': m.sub(d[4], length), 'rigidC': m.sub(length, d[0]),
              'axialImpulse': m.add(m.sub(m.add(d[7], d[8]), d[9]), d[10])}
    return {'H': {name: f'{m.bits(v):08x}' for name, v in values.items()},
            'predicates': {'k>0': k > 0, 'normalizeZero': not normalizable,
                'spring': bool(distance[23]) and (d[3] < d[4] or not distance[24]),
                'hertz>0': d[1] > 0, 'limit': bool(distance[24]), 'motor': bool(distance[25]),
                **{name + relation: (v < 0 if relation == '<0' else v == 0 if relation == '=0' else v > 0)
                   for name, v in (('lowerC', values['lowerC']), ('upperC', values['upperC']))
                   for relation in ('<0', '=0', '>0')}},
            'phase': phase, 'oracle': 'branch inputs only; no physics acceptance'}


def direct_boundaries(ident, source_key, fixtures, operations, snapshots=None):
    pass                                                                   

                                                                             
                                                                        
                                                                            
                                                                      
       
    m.require(len(fixtures) == 5 and tuple(map(len, fixtures)) == m.F_ARITY, 'five exact F groups')
    rows = []; previous = None
    for seq, operation in enumerate(operations, 1):
        m.require(operation['opcode'] == 210, 'DIRECT distance operations only210')
        a = operation['a']; phase = ('prepare', 'warm', 'solve' if a[2] else 'relax')[a[1]]
        row = {'id': ident, 'sourceKey': source_key, 'seq': seq, 'substep': 0, 'phase': phase,
               'state': 'unexecuted', 'receipt': None, 'native_witness': False}
        if seq == 1:
            m.require(a[1:] == (0, 0) or tuple(a[1:]) == (0, 0), 'prepare first')
            common, distance, states = fixtures[1], fixtures[2], fixtures[4]
        elif previous is not None:
            def group(g):
                values = [v[7:] for t, v in previous if t == 'J14' and v[2:6] == (0, 0, 0, g)]
                m.require(len(values) == 1, 'own prior DIRECT group ' + str(g)); return values[0]
            common, distance, states = group(2), group(3), group(10)
        else:
            rows.append(row)
            previous = None if snapshots is None else snapshots.get(seq)
            continue
        receipt = separation_predicates(common, distance, states, phase='prepare' if phase == 'prepare' else phase,
                                        body_sims=fixtures[3] if phase == 'prepare' else None)
        p = receipt['predicates']; active = ['normalizeZero']
        if phase == 'prepare': active += ['k>0']
        if phase in ('solve', 'relax'):
            active += ['spring']
            if p['spring']:
                active += ['hertz>0', 'limit', 'motor']
                if p['limit']: active += [name + relation for name in ('lowerC', 'upperC') for relation in ('<0', '=0', '>0')]
        call_proven = snapshots is not None and seq in snapshots
        if call_proven: m.check_trace(snapshots[seq], operation)
        row.update(state='input-calculated' if seq == 1 else 'own-native-prior-state', receipt=receipt,
                   active_predicates=active, native_witness=call_proven,
                   before_words={'common': list(common), 'distance': list(distance), 'states': list(states)})
        rows.append(row); previous = None if snapshots is None else snapshots.get(seq)
    return rows


                                                                            
                                                                          
SEMANTIC_GROUPS = {
    'create': ('disabled', 'static-static', 'awake', 'sleep', 'merge-A', 'merge-B', 'merge-tie-A', 'reacquire',
               'pool-allocate', 'generation', 'head-A', 'prev-A', 'next-A', 'count-A', 'head-B', 'prev-B', 'next-B', 'count-B'),
    'destroy': ('head', 'middle', 'tail', 'prev-repair', 'next-repair', 'count-A', 'count-B', 'remove-swap', 'swap-local-repair', 'free-stack'),
    'collide': ('create-false', 'destroy-contact-wakefalse', 'true-smaller-A', 'true-smaller-B', 'true-tie-B', 'no-op', 'destroy-no-proxy-move'),
    'graph': (*('color-' + str(i) for i in range(12)), 'mixed-contact-joint-occupation', 'nonstatic-A', 'nonstatic-B', 'joint-only-color', 'swap-repair'),
    'sets': ('sleep-copy', 'wake-copy', 'transfer-to-graph', 'transfer-from-graph', 'merge-A', 'merge-B', 'merge-tie', 'reacquire', 'impulse-preserve'),
    'island': ('link', 'unlink-head', 'unlink-tail', 'merge', 'split-LIFO', 'split-mark', 'split-cycle', 'split-static-anchor'),
    'prepare': ('index-A-awake', 'index-A-static', 'index-B-awake', 'index-B-static', 'invMassA', 'invMassB', 'invIA', 'invIB',
                'anchor-A', 'anchor-B', 'deltaCenter', 'k-positive', 'k-zero', 'normalize-zero', 'axialMass', 'softness',
                'warmfalse-impulse', 'warmfalse-lower', 'warmfalse-upper', 'warmfalse-motor', 'warmtrue-preserve'),
    'warm': ('static-A', 'static-B', 'rotate-A', 'rotate-B', 'separation', 'four-impulse-order', 'velocity-A', 'angular-A', 'velocity-B', 'angular-B'),
    'solve': ('spring-true', 'spring-false', 'min-less', 'min-equal', 'limit-off', 'Hz-zero', 'Hz-positive',
              'lower-C-negative', 'lower-C-zero', 'lower-C-positive', 'lower-bias', 'lower-relax', 'lower-clamp-zero', 'lower-impulse',
              'upper-C-negative', 'upper-C-zero', 'upper-C-positive', 'upper-bias', 'upper-relax', 'upper-clamp-zero', 'upper-impulse',
              'motor-zero-force', 'motor-speed-zero', 'motor-speed-positive', 'motor-speed-negative', 'motor-clamp-positive', 'motor-clamp-negative',
              'motor-LAST', 'rigid-bias', 'rigid-relax', 'velocity-A', 'angular-A', 'velocity-B', 'angular-B'),
    'setter': ('length-reset-impulse', 'length-reset-lower', 'length-reset-upper', 'length-preserve-motor',
               'range-clamp-A', 'range-clamp-B', 'range-order', 'range-reset-impulse', 'range-reset-lower', 'range-reset-upper',
               'range-preserve-motor', 'spring-preserve4', 'limit-preserve4', 'motor-same-preserve', 'motor-change-reset'),
    'getters': ('force-sum-order', 'torque-zero', 'current-length-transform', 'weak-GetWorld', 'store-low', 'store-high', 'load-world', 'load-generation', 'load-index'),
    'planner-global': ('zero', 'one', 'four', 'five', 'sixteen', 'seventeen', 'block-size', 'block-count', 'tail', 'joint-before-contact'),
    'planner-color': ('zero', 'one', 'four', 'five', 'sixteen', 'seventeen', 'block-size', 'block-count', 'tail', 'joint-before-contact'),
}


def obligations(manifest=None):
    if manifest is None:
        raw = (HERE / 'polaczenia-przypadki.json').read_bytes()
        m.require(hashlib.sha256(raw).hexdigest() == 'd727b175f6514919979087b99113453a7f348b91fc39f5a6622bb86ce32bbc08', 'frozen14a obligation manifest changed')
        manifest = json.loads(raw.decode('utf-8'))
    atoms = [{'id': group + '/' + name, 'classification': 'native-target', 'state': 'unexecuted',
              'c': None, 'port': None, 'witness': None, 'receipt': None,
              'independent': None, 'alias_of': None}
             for group, names in SEMANTIC_GROUPS.items() for name in names]
    guards = []
    for row in manifest['guard']:
        classes = row['mutationClasses']
        classification = 'equivalent' if row.get('classification', '').startswith('EQUIVALENT') else 'control' if not classes else 'aggregate'
        guard_atoms = []
        if classification == 'aggregate':
            for klass in classes:
                atom_id = 'guard/' + row['key'] + '/' + klass
                guard_atoms.append(atom_id)
                atoms.append({'id': atom_id, 'classification': 'native-target', 'state': 'unexecuted',
                    'c': None, 'port': None, 'witness': {'profile': 'GUARD', 'case': row['id'], 'sourceKey': row['key'], 'route': row['route']},
                    'receipt': None, 'independent': None, 'alias_of': None,
                    'recipe': {'operation': klass, 'route': row['route'], 'defect': row['defect'],
                               'before': row['expected'], 'after': 'defined acceptance/status/state difference; no illegal raw'}})
        guards.append({'id': row['key'], 'classification': classification, 'state': 'unexecuted',
                       'profile': 'GUARD', 'case': row['id'], 'route': row['route'], 'defect': row['defect'],
                       'inputWord': row.get('inputWord'), 'expected': row['expected'], 'classes': classes,
                       'atom_ids': guard_atoms, 'proof': 'KONTRAKT-14/1 §11.1: min>=0, min<=max, finite(max)' if classification == 'equivalent' else None})
    aggregates = []
    for profile, key in (('PUBLIC', 'przypadki'), ('DIRECT', 'direct')):
        for row in manifest[key]:
            for klass in row['mutationClasses']:
                aggregates.append({'id': row['key'] + '/' + klass, 'classification': 'aggregate',
                    'state': 'open', 'profile': profile, 'case': row['id'], 'class': klass, 'atom_ids': []})
    return {'schema': 1, 'contract': 'KONTRAKT-14/1 14a', 'atoms': atoms, 'guards': guards,
            'manifest_classes': aggregates, 'source_candidates': [], 'full_acceptance': False,
            'denominator_state': 'OPEN: semantic targets independent; candidates and guard aliasing still require classification'}


def settle(ledger, receipts):
    pass                                                                 

                                                                            
                                                                   
       
    result = json.loads(json.dumps(ledger)); by_id = {r['id']: r for r in receipts}
    m.require(len(by_id) == len(receipts), 'duplicate mutation receipt')
    required_ledger = obligations()
    required = {r['id'] for r in required_ledger['atoms']}
    actual = [row['id'] for row in result['atoms']]
    m.require(len(actual) == len(set(actual)), 'duplicate atomic obligation')
    result['missing_atom_ids'] = sorted(required - set(actual))
    result['unknown_atom_ids'] = sorted(set(actual) - required)
    result['unmatched_receipt_ids'] = sorted(set(by_id) - set(actual))
    result['missing_guard_ids'] = sorted({r['id'] for r in required_ledger['guards']} - {r['id'] for r in result['guards']})
    result['missing_manifest_classes'] = sorted({r['id'] for r in required_ledger['manifest_classes']} - {r['id'] for r in result['manifest_classes']})
    known = set(actual)
    for row in (*result['guards'], *result['manifest_classes'], *result['source_candidates']):
                                                                        
                                                                          
        m.require(set(row.get('atom_ids', ())) <= required, 'aggregate/candidate references unknown atom')
    for row in result['atoms']:
        r = by_id.get(row['id'])
        if row.get('alias_of'):
            m.require(row['alias_of'] in known and row['alias_of'] != row['id'], 'alias target must be another required atom')
            row['state'] = 'alias' if row.get('alias_proof') else 'alias-unproved'
            continue
        if r is None: row['state'] = 'missing'; continue
        row['receipt'] = r
        if not r.get('executed'): row['state'] = 'unexecuted'
        elif not r.get('baseline_validated'): row['state'] = 'baseline-red'
        elif r.get('anchor_hits') != 1: row['state'] = 'anchor-error'
        elif r.get('build_code') != 0: row['state'] = 'build-error'
        elif r.get('timeout'): row['state'] = 'timeout'
        elif r.get('crash') or r.get('unsafe_memory'): row['state'] = 'unsafe'
        elif r.get('process_code') != 0 or r.get('stderr_bytes') != 0: row['state'] = 'execution-error'
        elif not r.get('defined_difference'): row['state'] = 'survived'
        elif (r.get('native_product') is not True or r.get('same_target') is not True or not r.get('expected_difference') or
              row.get('independent') is not True or not row.get('c') or not row.get('port') or not row.get('witness')):
            row['state'] = 'unverified'
        else: row['state'] = 'killed'
    result['counts'] = dict(Counter(r['state'] for r in result['atoms']))
    result['counts'].update({'required_native_intents': len(required),
        'independent_native_targets': sum(r.get('independent') is True and not r.get('alias_of') for r in result['atoms']),
        'unresolved_native_intents': sum(r.get('independent') is None for r in result['atoms']),
        'missing_atomic_obligations': len(result['missing_atom_ids']),
        'aliases': sum(bool(r.get('alias_of')) for r in result['atoms']),
        'equivalent': sum(r['classification'] == 'equivalent' for r in result['guards']),
        'control': sum(r['classification'] == 'control' for r in result['guards']),
        'aggregate': len(result['manifest_classes']) + sum(r['classification'] == 'aggregate' for r in result['guards']),
        'candidate': len(result['source_candidates']),
        'open_candidates': sum(r.get('state') == 'open' or r.get('classification') == 'candidate' for r in result['source_candidates']),
        'open': sum(not r.get('atom_ids') for r in result['manifest_classes']) + sum(not r.get('atom_ids') and r['classification'] == 'aggregate' for r in result['guards'])})
                                                                             
                                                            
    by_atom = {r['id']: r for r in result['atoms']}
    aliases_valid = all(not r.get('alias_of') or r['state'] == 'alias' and by_atom[r['alias_of']]['state'] == 'killed'
                        for r in result['atoms'])
    result['full_acceptance'] = (bool(result['atoms']) and not any(result[k] for k in
        ('missing_atom_ids', 'unknown_atom_ids', 'unmatched_receipt_ids', 'missing_guard_ids', 'missing_manifest_classes')) and
        all(r['state'] in ('killed', 'alias') for r in result['atoms']) and aliases_valid and result['counts']['open'] == 0 and
        result['counts']['unresolved_native_intents'] == 0 and bool(result['source_candidates']) and result['counts']['open_candidates'] == 0)
    return result
