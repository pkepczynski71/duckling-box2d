pass                                                                         

                                                                                
                                                                             
   
import importlib.util
import hashlib
import json
import hashlib
import re
import difflib
import subprocess
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('lancuchy_branch_model', HERE / 'model-lancuchy.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def source_operators13(text):
    pass                                                                     
    pattern=r'\#[^\n]*|"(?:\\.|[^"\\])*"|<<=|>>=|<<|>>|<=|>=|==|!=|->|\+=|-=|\*=|/=|[<>=|]'
    rows=[]
    for match in re.finditer(pattern,text):
        token=match.group()
        if token.startswith(('#','"')):continue
        kind=('comparison' if token in ('<','>','<=','>=','==','!=') else
              'shift' if token in ('<<','>>','<<=','>>=') else
              'assignment' if token=='=' else 'other')
        rows.append({'token':token,'start':match.start(),'end':match.end(),'kind':kind})
    return rows


def vec_sub(a, b):
    return tuple(m.sub(x, y) for x, y in zip(a, b))


def dot(a, b):
    return m.add(m.mul(a[0], b[0]), m.mul(a[1], b[1]))


def cross(a, b):
    return m.sub(m.mul(a[0], b[1]), m.mul(a[1], b[0]))


def initial_predicates(a, incoming):
    pass                                                                     
    ax, ay, ac, ass = map(m.number, a[19:23])
    bx, by, bc, bs = map(m.number, a[41:45])
    dx, dy = m.sub(bx, ax), m.sub(by, ay)
    relative = tuple(map(m.bits, (m.add(m.mul(ac, dx), m.mul(ass, dy)),
                                 m.add(m.mul(-ass, dx), m.mul(ac, dy)),
                                 m.add(m.mul(ac, bc), m.mul(ass, bs)),
                                 m.sub(m.mul(ac, bs), m.mul(ass, bc)))))
    w = []
    for j in range(max(1, incoming[0])):
        ia, ib = (incoming[1 + j], incoming[4 + j]) if incoming[0] else (0, 0)
        pa = tuple(map(m.number, a[3 + 2 * ia:5 + 2 * ia]))
        pb = tuple(map(m.number, m.transform(relative, a[25 + 2 * ib:27 + 2 * ib])))
        w.append(vec_sub(pa, pb))
    predicates = {}
    if len(w) == 1:
        predicates['d2'] = dot(w[0], w[0])
        region = 'point'
    elif len(w) == 2:
        e = vec_sub(w[1], w[0])
        predicates = {'d12_2': m.f32(-dot(w[0], e)), 'd12_1': dot(w[1], e)}
        region = 'w1' if predicates['d12_2'] <= 0 else 'w2' if predicates['d12_1'] <= 0 else 'e12'
    else:
        e12, e13, e23 = vec_sub(w[1], w[0]), vec_sub(w[2], w[0]), vec_sub(w[2], w[1])
        n = cross(e12, e13)
        predicates = {'d12_1': dot(w[1], e12), 'd12_2': m.f32(-dot(w[0], e12)),
                      'd13_1': dot(w[2], e13), 'd13_2': m.f32(-dot(w[0], e13)),
                      'd23_1': dot(w[2], e23), 'd23_2': m.f32(-dot(w[1], e23)),
                      'd123_1': m.mul(n, cross(w[1], w[2])),
                      'd123_2': m.mul(n, cross(w[2], w[0])),
                      'd123_3': m.mul(n, cross(w[0], w[1]))}
        p = predicates
        if p['d12_2'] <= 0 and p['d13_2'] <= 0:
            region = 'w1'
        elif p['d12_1'] > 0 and p['d12_2'] > 0 and p['d123_3'] <= 0:
            region = 'e12'
        elif p['d13_1'] > 0 and p['d13_2'] > 0 and p['d123_2'] <= 0:
            region = 'e13'
        elif p['d12_1'] <= 0 and p['d23_2'] <= 0:
            region = 'w2'
        elif p['d13_1'] <= 0 and p['d23_1'] <= 0:
            region = 'w3'
        elif p['d23_1'] > 0 and p['d23_2'] > 0 and p['d123_1'] <= 0:
            region = 'e23'
        else:
            region = 'triangle'
    return {'count': len(w), 'region': region,
            'w_H': [[f'{m.bits(x):08x}', f'{m.bits(y):08x}'] for x, y in w],
            'predicates_H': {k: f'{m.bits(v):08x}' for k, v in predicates.items()},
            'equal_zero': [k for k, v in predicates.items() if v == 0]}


                                                                                  
                                                                           
TARGETS = [
    ('proxy-clamp', '110', (1, 16)), ('proxy-copy', '113-117', (1, 16)),
    ('proxy-count', '116', (1, 16)), ('proxy-radius', '117', (1, 16)),
    ('offset-clamp', '123', (1, 16)), ('offset-transform', '131', (1, 16)),
    ('offset-count', '133', (1, 16)), ('offset-radius', '134', (1, 16)),
    ('weight2-x', '140', (33, 48)), ('weight2-y', '140', (33, 48)),
    ('weight3-left-x', '145', (49, 64)), ('weight3-left-y', '145', (49, 64)),
    ('support-first', '153-154', (17, 32)), ('support-strict-tie', '158', (17, 32)),
    ('cache-in-count', '174', (81, 84)), ('cache-in-A', '180', (81, 84)),
    ('cache-in-B', '181', (81, 84)), ('cache-w-sign', '184', (17, 32)),
    ('cache-weight-minus1', '187', (81, 84)), ('cache-zero-seed', '191-201', (81, 81)),
    ('cache-out-count', '208', (81, 96)), ('cache-active-bound', '210', (81, 96)),
    ('cache-out-A', '212', (81, 96)), ('cache-out-B', '213', (81, 96)),
    ('zero-sign', '284', (33, 48)),
    ('witness1-A', '222', (33, 48)), ('witness1-B', '223', (33, 48)),
    ('witness2-A', '227', (33, 48)), ('witness2-B', '228', (33, 48)),
    ('witness3-A', '232', (49, 64)), ('witness3-B-equals-A', '235', (49, 64)),
]

                                                                           
                                                                           
ATOM_C_LINES = {}
for prefix, atoms in (
        ('solve2-w1', {'d12_2<=0': 279, 'a1': 282, 'count1': 283, 'direction': 284}),
        ('solve2-w2', {'d12_1<=0': 289, 'a2': 292, 'count1': 293, 'v1=v2': 294, 'direction': 295}),
        ('solve2-e12', {'inv': 299, 'a1': 300, 'a2': 301, 'count2': 302, 'direction': 303}),
        ('solve3-w1', {'a1': 352, 'count1': 353, 'direction': 354}),
        ('solve3-e12', {'inv': 360, 'a1': 361, 'a2': 362, 'count2': 363, 'direction': 364}),
        ('solve3-e13', {'inv': 370, 'a1': 371, 'a3': 372, 'count2': 373, 'v2=v3': 374, 'direction': 375}),
        ('solve3-w2', {'a2': 381, 'count1': 382, 'v1=v2': 383, 'direction': 384}),
        ('solve3-w3', {'a3': 390, 'count1': 391, 'v1=v3': 392, 'direction': 393}),
        ('solve3-e23', {'inv': 399, 'a2': 400, 'a3': 401, 'count2': 402, 'v1=v3': 403, 'keep-v2': '400-404', 'direction': 404}),
        ('solve3-triangle', {'inv-left': 408, 'a1': 409, 'a2': 410, 'a3': 411, 'count3': 412, 'direction0': 415})):
    ATOM_C_LINES.update({prefix + '/' + atom: str(line) for atom, line in atoms.items()})

                                                                               
                                                                               
ADDITIONAL_TARGETS = [
    ('support-initial-value', '154', 'b2FindSupport'),
    ('support-start-index1', '155', 'b2FindSupport'),
    ('support-loop-count', '155', 'b2FindSupport'),
    ('support-best-index-update', '160', 'b2FindSupport'),
    ('support-best-value-update', '161', 'b2FindSupport'),
    ('cache-in-loop-count', '177', 'b2MakeSimplexFromCache'),
    ('cache-in-pointA', '182', 'b2MakeSimplexFromCache'),
    ('cache-in-pointB', '183', 'b2MakeSimplexFromCache'),
    ('seed0-indexA', '194', 'b2MakeSimplexFromCache'),
    ('seed0-indexB', '195', 'b2MakeSimplexFromCache'),
    ('seed0-pointA', '196', 'b2MakeSimplexFromCache'),
    ('seed0-pointB', '197', 'b2MakeSimplexFromCache'),
    ('seed0-w-sign', '198', 'b2MakeSimplexFromCache'),
    ('seed0-count1', '200', 'b2MakeSimplexFromCache'),
    ('localB-count', '437', 'shapeDistanceKernel'),
    ('localB-radius', '438', 'shapeDistanceKernel'),
    ('localB-loop-count', '439', 'shapeDistanceKernel'),
    ('localB-point-transform', '441', 'shapeDistanceKernel'),
    ('trace-reset-stored', '448', 'shapeDistanceKernel'),
    ('vertex-slot0', '456', 'simplexVertex'),
    ('vertex-slot1', '456', 'simplexVertex'),
    ('vertex-slot2', '456', 'simplexVertex'),
    ('normal-initial-zero', '458', 'shapeDistanceKernel'),
    ('dispatch-count1-direction', '479-481', 'shapeDistanceKernel'),
    ('dispatch-count2-Solve2', '483-485', 'shapeDistanceKernel'),
    ('dispatch-count3-Solve3', '487-489', 'shapeDistanceKernel'),
    ('early-pointA-transform', '501/526', 'overlapOutput'),
    ('early-pointB-transform', '502/527', 'overlapOutput'),
    ('early-zero-normal-x', '428/503/528', 'DistanceOutput'),
    ('early-zero-normal-y', '428/503/528', 'DistanceOutput'),
    ('early-zero-distance', '428/503/528', 'DistanceOutput'),
    ('early-zero-iterations', '428/503/528', 'DistanceOutput'),
    ('early-zero-simplexCount', '428/503/528', 'DistanceOutput'),
    ('checked-distance-R-wiring', 'KONTRAKT §4/11', 'shapeDistanceCached'),
    ('checked-distance-D-wiring', 'KONTRAKT §4/11', 'shapeDistanceCachedDebug'),
    ('checked-refusal-cache-preserved', 'KONTRAKT §4/9/11', 'shapeDistanceCached'),
    ('checked-proxy-wiring', 'KONTRAKT §4/11', 'makeProxy'),
    ('checked-offset-wiring', 'KONTRAKT §4/11', 'makeOffsetProxy'),
    ('public-R-selects-no-debug', '506/567 #ifndef', 'b2ShapeDistance'),
    ('fixture-D-selects-debug', '506/567 #ifndef', 'b2ShapeDistanceDebug'),
]
for label, line, ids, atoms in (
        ('solve2-w1', 279, (33, 36), ('d12_2<=0', 'a1', 'count1', 'direction')),
        ('solve2-w2', 289, (34, 37), ('d12_1<=0', 'a2', 'count1', 'v1=v2', 'direction')),
        ('solve2-e12', 299, (35, 48), ('inv', 'a1', 'a2', 'count2', 'direction')),
        ('solve3-w1', 350, (49, 56), ('d12_2<=0', 'd13_2<=0', 'a1', 'count1', 'direction')),
        ('solve3-e12', 358, (50, 57), ('d12_1>0', 'd12_2>0', 'd123_3<=0', 'inv', 'a1', 'a2', 'count2', 'direction')),
        ('solve3-e13', 368, (51, 58), ('d13_1>0', 'd13_2>0', 'd123_2<=0', 'inv', 'a1', 'a3', 'count2', 'v2=v3', 'direction')),
        ('solve3-w2', 379, (52, 59), ('d12_1<=0', 'd23_2<=0', 'a2', 'count1', 'v1=v2', 'direction')),
        ('solve3-w3', 388, (53, 60), ('d13_1<=0', 'd23_1<=0', 'a3', 'count1', 'v1=v3', 'direction')),
        ('solve3-e23', 397, (54, 61), ('d23_1>0', 'd23_2>0', 'd123_1<=0', 'inv', 'a2', 'a3', 'count2', 'v1=v3', 'keep-v2', 'direction')),
        ('solve3-triangle', 408, (55, 62), ('inv-left', 'a1', 'a2', 'a3', 'count3', 'direction0'))):
    TARGETS.extend((label + '/' + atom, str(line), ids) for atom in atoms)
TARGETS += [
    ('B-local-transform', '436-443', (17, 32)), ('trace-initial-null', '449', (113, 128)),
    ('trace-initial-capacity', '449', (113, 128)), ('trace-initial-copy', '451-452', (113, 128)),
    ('support-limit20', '464-466', (80, 80)), ('save-count', '469', (65, 80)),
    ('save-A', '472', (65, 80)), ('save-B', '473', (65, 80)),
    ('overlap-return-cache', '496-503', (49, 80)), ('trace-afterSolve-null', '507', (113, 128)),
    ('trace-afterSolve-capacity', '507', (113, 128)), ('trace-afterSolve-copy', '509-510', (113, 128)),
    ('epsilon-strict', '515', (66, 68)), ('epsilon-return-cache', '524-528', (66, 79)),
    ('save-normal', '532', (17, 80)), ('support-A-index', '537', (17, 32)),
    ('support-A-point', '538', (17, 32)), ('support-B-index', '539', (17, 32)),
    ('support-B-point', '540', (17, 32)), ('support-w-sign', '541', (17, 32)),
    ('support-keeps-old-defined-a', '536-541', (113, 128)), ('support-count', '544', (65, 80)),
    ('duplicate-A', '550', (65, 80)), ('duplicate-B', '550', (65, 80)),
    ('duplicate-break', '558-561', (65, 80)), ('append-count', '564', (65, 80)),
    ('trace-final-null', '568', (113, 128)), ('trace-final-capacity', '568', (113, 128)),
    ('trace-final-copy', '570-571', (113, 128)), ('normal-normalize-then-rotate', '576-578', (17, 32)),
    ('output-normal', '582', (17, 32)), ('output-distance-b-minus-a', '583', (17, 32)),
    ('output-pointA', '584', (17, 32)), ('output-pointB', '585', (17, 32)),
    ('output-iterations', '586', (65, 80)), ('output-simplexCount', '587', (113, 128)),
    ('normal-end-writes-cache', '590', (81, 96)), ('useRadii', '593', (97, 97)),
    ('radii-strict-threshold', '593', (98, 100)), ('radii-clamp', '597', (100, 112)),
    ('radii-left-subtract', '597', (100, 112)), ('radii-pointA-even-zero', '600', (100, 112)),
    ('radii-pointB-even-zero', '601', (100, 112)),
]


def requirements():
    rows = [{'id': key, 'original': 'src/distance.c:' + ATOM_C_LINES.get(key, line),
             'candidate_ids': list(range(ids[0], ids[1] + 1)), 'kind': 'algorithm'}
            for key, line, ids in TARGETS]
    rows.extend({'id': key, 'original': ('src/distance.c:' + line if line[0].isdigit() else line),
                 'kind': 'additional-source-gap', 'port_function': function,
                 'candidate_ids': [], 'gap': 'No separate final native recipe/equivalence acceptance'}
                for key, line, function in ADDITIONAL_TARGETS)
    manifest = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    rows.extend({'id': r['id'], 'original': 'KONTRAKT-13/1 §4/11', 'kind': 'guard',
                 'helper': r['Gkind'], 'candidate_ids': [r['id']]}
                for r in manifest['guardPrzypadki'] if r['czesc'] == '13a')
    for kind in (101, 102):
        for predicate in ('radius-finite', 'radius-sign', 'point-X-finite', 'point-Y-finite'):
            rows.append({'id': f'constructor-{kind}/{predicate}', 'kind': 'route-gap',
                         'original': 'KONTRAKT-13/1 §4/11', 'helper': kind,
                         'port_function': 'makeProxy' if kind == 101 else 'makeOffsetProxy',
                         'candidate_ids': [], 'gap': 'E5dc1c90633c4 Ebfb4f99c641f E50e721e49c01 E4d4f5985df07 E40e0b797efb6: GUARD38 Ecd5b158f21b7 E6c8a51b339c4 E36984836e1a8 Ea47f6d13afa6 Ecbb5ba19b8c1; D13a-1 pkt3, E283ada7088c2 E036a8a704eee G'})
    return rows


def proposals():
    pass                                                                   

                                                                           
                                                                          
       
    result = []
    def add(ident, function, needle, replacement, requirement=None, block=None, guard=None):
        result.append({'id': ident, 'source': 'silnik/fizyka/odleglosc.dk',
                       'function': function, 'block': block, 'needle': needle,
                       'replacement': replacement, 'requirement': requirement or ident,
                       'guard': guard, 'anchor_owner': 'T-13a-2a',
                       'status': 'PROPOSAL_NOT_BOUND_NOT_EXECUTED'})
    for function, prefix in (('b2MakeProxy', 'proxy'), ('b2MakeOffsetProxy', 'offset')):
        add(prefix + '-clamp', function, 'if (used > 8i32) used = 8i32;',
            'if (used > 8i32) used = 7i32;')                                    
        add(prefix + '-count', function, 'result.count = used;', 'result.count = 0i32;')
        add(prefix + '-radius', function, 'result.radius = radius;', 'result.radius = 0.0f32;')
    add('proxy-copy', 'b2MakeProxy', 'result.points[i] = points[i];', 'result.points[i] = Vec2();')
    add('offset-transform', 'b2MakeOffsetProxy', 'b2TransformPoint(transform, points[i])', 'points[i]')
    for dimension in ('x', 'y'):
        add('weight2-' + dimension, 'b2Weight2', f'a1 * w1.{dimension} + a2 * w2.{dimension}', f'a1 * w1.{dimension}')
        add('weight3-left-' + dimension, 'b2Weight3',
            f'a1 * w1.{dimension} + a2 * w2.{dimension} + a3 * w3.{dimension}',
            f'a1 * w1.{dimension} + (a2 * w2.{dimension} + a3 * w3.{dimension})')
    add('support-first', 'b2FindSupport', 'var bestIndex: i32 = 0i32;', 'var bestIndex: i32 = proxy.count - 1i32;')
    add('support-strict-tie', 'b2FindSupport', 'value > bestValue', 'value >= bestValue')
    for field in ('A', 'B'):
        add('cache-in-' + field, 'b2MakeSimplexFromCache', 'vertex.index' + field + ' = cache.index' + field + '[i];',
            'vertex.index' + field + ' = 0i32;')
        add('cache-out-' + field, 'b2MakeSimplexCache',
            'cache.index' + field + '[i] = simplexVertex(simplex, i).index' + field + ';',
            'cache.index' + field + '[i] = 0i32;')
    add('cache-in-count', 'b2MakeSimplexFromCache', 's.count = cache.count;', 's.count = 0i32;')
    add('cache-w-sign', 'b2MakeSimplexFromCache', 'b2Sub(vertex.wA, vertex.wB)', 'b2Sub(vertex.wB, vertex.wA)')
    add('cache-weight-minus1', 'b2MakeSimplexFromCache', 'vertex.a = -1.0f32;', 'vertex.a = 0.0f32;')
    add('cache-zero-seed', 'b2MakeSimplexFromCache', 's.v1.a = 1.0f32;', 's.v1.a = 0.0f32;')
    add('cache-out-count', 'b2MakeSimplexCache', 'cache.count = simplex.count;', 'cache.count = 0i32;')
    add('cache-active-bound', 'b2MakeSimplexCache', 'while (i < simplex.count)', 'while (i < 3i32)')
                                                                             
                                                                            
    for count in (1, 2, 3):
        block = f'if (s.count == {count}i32)'
        if count == 1:
            add('witness1-A', 'b2ComputeSimplexWitnessPoints', 'a = s.v1.wA;', 'a = Vec2();', block=block)
            add('witness1-B', 'b2ComputeSimplexWitnessPoints', 'b = s.v1.wB;', 'b = Vec2();', block=block)
        elif count == 2:
            for side in ('A', 'B'):
                lhs = 'a' if side == 'A' else 'b'
                add('witness2-' + side, 'b2ComputeSimplexWitnessPoints',
                    f'{lhs} = b2Weight2(s.v1.a, s.v1.w{side}, s.v2.a, s.v2.w{side});',
                    f'{lhs} = s.v1.w{side};', block=block)
        else:
            add('witness3-A', 'b2ComputeSimplexWitnessPoints',
                'a = b2Weight3(s.v1.a, s.v1.wA, s.v2.a, s.v2.wA, s.v3.a, s.v3.wA);', 'a = s.v1.wA;', block=block)
            add('witness3-B-equals-A', 'b2ComputeSimplexWitnessPoints', 'b = a;', 'b = s.v1.wB;', block=block)
    solve = [
        ('solve2-w1', 'b2SolveSimplex2', 'd12_2 <= 0.0f32', (('a1', 's.v1.a = 1.0f32;', 's.v1.a = 0.0f32;'),
          ('count1', 's.count = 1i32;', 's.count = 0i32;'), ('direction', 'poly.b2Neg( w1 )', 'w1'))),
        ('solve2-w2', 'b2SolveSimplex2', 'd12_1 <= 0.0f32', (('a2', 's.v2.a = 1.0f32;', 's.v2.a = 0.0f32;'),
          ('count1', 's.count = 1i32;', 's.count = 0i32;'), ('v1=v2', 's.v1 = s.v2;', 's.v1 = s.v1;'),
          ('direction', 'poly.b2Neg( w2 )', 'w2'))),
        ('solve3-w1', 'b2SolveSimplex3', 'd12_2 <= 0.0f32 and d13_2 <= 0.0f32',
          (('a1', 's.v1.a = 1.0f32;', 's.v1.a = 0.0f32;'), ('count1', 's.count = 1i32;', 's.count = 0i32;'), ('direction', 'poly.b2Neg( w1 )', 'w1'))),
        ('solve3-w2', 'b2SolveSimplex3', 'd12_1 <= 0.0f32 and d23_2 <= 0.0f32',
          (('a2', 's.v2.a = 1.0f32;', 's.v2.a = 0.0f32;'), ('count1', 's.count = 1i32;', 's.count = 0i32;'),
           ('v1=v2', 's.v1 = s.v2;', 's.v1 = s.v1;'), ('direction', 'poly.b2Neg( w2 )', 'w2'))),
        ('solve3-w3', 'b2SolveSimplex3', 'd13_1 <= 0.0f32 and d23_1 <= 0.0f32',
          (('a3', 's.v3.a = 1.0f32;', 's.v3.a = 0.0f32;'), ('count1', 's.count = 1i32;', 's.count = 0i32;'),
           ('v1=v3', 's.v1 = s.v3;', 's.v1 = s.v1;'), ('direction', 'poly.b2Neg( w3 )', 'w3'))),
    ]
    add('zero-sign', 'b2SolveSimplex2', 'poly.b2Neg( w1 )',
        'Vec2(0.0f32 - w1.x, 0.0f32 - w1.y)', block='if ( d12_2 <= 0.0f32 )')
    for label, function, condition, assignments in solve:
        block = 'if ( ' + condition + ' )'
        for atom in condition.split(' and '):
            add(label + '/' + atom.replace('0.0f32', '0').replace(' ', ''), function, atom, atom.replace('<=', '<'), block=block)
        for atom, old, new in assignments:
            add(label + '/' + atom, function, old, new, block=block)
    for edge, d1, d2, d3 in (('e12', 'd12_1', 'd12_2', 'd123_3'),
                             ('e13', 'd13_1', 'd13_2', 'd123_2'),
                             ('e23', 'd23_1', 'd23_2', 'd123_1')):
        label = 'solve3-' + edge
        condition = f'{d1} > 0.0f32 and {d2} > 0.0f32 and {d3} <= 0.0f32'
        block = 'if ( ' + condition + ' )'
        for atom in condition.split(' and '):
            add(label + '/' + atom.replace('0.0f32', '0').replace(' ', ''), 'b2SolveSimplex3', atom,
                atom.replace('<=', '<') if '<=' in atom else atom.replace('>', '>='), block=block)
        den = edge[1:]
        add(label + '/inv', 'b2SolveSimplex3', f'1.0f32 / ( d{den}_1 + d{den}_2 )', '1.0f32', block=block)
        slots = {'e12': ((1, d1), (2, d2)), 'e13': ((1, d1), (3, d2)), 'e23': ((2, d1), (3, d2))}[edge]
        for slot, weight in slots:
            add(label + f'/a{slot}', 'b2SolveSimplex3', f's.v{slot}.a = {weight} * inv_d{den};',
                f's.v{slot}.a = 0.0f32;', block=block)
        add(label + '/count2', 'b2SolveSimplex3', 's.count = 2i32;', 's.count = 0i32;', block=block)
        if edge == 'e13':
            add(label + '/v2=v3', 'b2SolveSimplex3', 's.v2 = s.v3;', 's.v2 = s.v2;', block=block)
        if edge == 'e23':
            add(label + '/v1=v3', 'b2SolveSimplex3', 's.v1 = s.v3;', 's.v1 = s.v1;', block=block)
            add(label + '/keep-v2', 'b2SolveSimplex3', 's.v1 = s.v3;', 's.v1 = s.v3; s.v2 = s.v3;', block=block)
        add(label + '/direction', 'b2SolveSimplex3',
            f'poly.b2CrossSV( motion.b2Cross( b2Add( w{edge[1]}, w{edge[2]} ), {edge} ), {edge} )', 'Vec2()', block=block)
    add('solve2-e12/inv', 'b2SolveSimplex2', '1.0f32 / ( d12_1 + d12_2 )', '1.0f32')
    for slot in (1, 2):
        add(f'solve2-e12/a{slot}', 'b2SolveSimplex2', f's.v{slot}.a = d12_{slot} * inv_d12;', f's.v{slot}.a = 0.0f32;')
    add('solve2-e12/count2', 'b2SolveSimplex2', 's.count = 2i32;', 's.count = 0i32;')
    add('solve2-e12/direction', 'b2SolveSimplex2',
        'poly.b2CrossSV( motion.b2Cross( b2Add( w1, w2 ), e12 ), e12 )', 'Vec2()')
    add('solve3-triangle/inv-left', 'b2SolveSimplex3', 'd123_1 + d123_2 + d123_3', 'd123_1 + (d123_2 + d123_3)')
    for slot in (1, 2, 3):
        add(f'solve3-triangle/a{slot}', 'b2SolveSimplex3', f's.v{slot}.a = d123_{slot} * inv_d123;', f's.v{slot}.a = 0.0f32;')
    add('solve3-triangle/count3', 'b2SolveSimplex3', 's.count = 3i32;', 's.count = 0i32;')
                                                                            
                                                                           
    kernel = 'shapeDistanceKernel'
    for label, old, new in (
            ('trace-initial-copy', 'storeSimplex(trace, simplex, capacity, storeTrace);\n    var nonUnitNormal', 'var nonUnitNormal'),
            ('trace-afterSolve-copy', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n        if (poly.b2Dot', 'if (poly.b2Dot'),
            ('trace-final-copy', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n    var normal', 'var normal'),
            ('trace-initial-null', 'storeSimplex(trace, simplex, capacity, storeTrace);\n    var nonUnitNormal', 'storeSimplex(trace, simplex, capacity, false);\n    var nonUnitNormal'),
            ('trace-afterSolve-null', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n        if (poly.b2Dot', 'if (debugTrace) storeSimplex(trace, simplex, capacity, false);\n        if (poly.b2Dot'),
            ('trace-final-null', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n    var normal', 'if (debugTrace) storeSimplex(trace, simplex, capacity, false);\n    var normal'),
            ('trace-initial-capacity', 'storeSimplex(trace, simplex, capacity, storeTrace);\n    var nonUnitNormal', 'storeSimplex(trace, simplex, 23i32, storeTrace);\n    var nonUnitNormal'),
            ('trace-afterSolve-capacity', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n        if (poly.b2Dot', 'if (debugTrace) storeSimplex(trace, simplex, 23i32, storeTrace);\n        if (poly.b2Dot'),
            ('trace-final-capacity', 'if (debugTrace) storeSimplex(trace, simplex, capacity, storeTrace);\n    var normal', 'if (debugTrace) storeSimplex(trace, simplex, 23i32, storeTrace);\n    var normal'),
            ('overlap-return-cache', 'if (simplex.count == 3i32) return overlapOutput(input, &simplex);',
             'if (simplex.count == 3i32) { b2MakeSimplexCache(cache, &simplex); return overlapOutput(input, &simplex); }'),
            ('epsilon-return-cache', 'if (poly.b2Dot(direction, direction) < FLT_EPSILON * FLT_EPSILON) return overlapOutput(input, &simplex);',
             'if (poly.b2Dot(direction, direction) < FLT_EPSILON * FLT_EPSILON) { b2MakeSimplexCache(cache, &simplex); return overlapOutput(input, &simplex); }'),
            ('save-count', 'let saveCount: i32 = simplex.count;', 'let saveCount: i32 = 0i32;'),
            ('save-A', 'saveA[si] = simplexVertex(&simplex, si).indexA;', 'saveA[si] = 0i32;'),
            ('save-B', 'saveB[si] = simplexVertex(&simplex, si).indexB;', 'saveB[si] = 0i32;'),
            ('support-A-point', 'vertex.wA = proxyA.points[vertex.indexA];', 'vertex.wA = Vec2();'),
            ('support-B-point', 'vertex.wB = localProxyB.points[vertex.indexB];', 'vertex.wB = Vec2();'),
            ('duplicate-break', 'if (duplicate) searching = false; else simplex.count = simplex.count + 1i32;',
             'if (duplicate) { searching = false; iteration = iteration + 1i32; } else simplex.count = simplex.count + 1i32;'),
            ('append-count', 'else simplex.count = simplex.count + 1i32;', 'else searching = false;'),
            ('normal-normalize-then-rotate', 'motion.b2Normalize(nonUnitNormal); normal = b2RotateVector(input.transformA.q, normal)',
             'motion.b2Normalize(b2RotateVector(input.transformA.q, nonUnitNormal))'),
            ('radii-clamp', 'tree.b2MaxFloat(0.0f32, output.distance - radiusA - radiusB)', 'output.distance - radiusA - radiusB')):
        add(label, kernel, old, new)
    for ident, old, new in (
            ('B-local-transform', 'b2InvMulTransforms(input.transformA, input.transformB)', 'b2InvMulTransforms(input.transformB, input.transformA)'),
            ('epsilon-strict', 'poly.b2Dot(direction, direction) < FLT_EPSILON * FLT_EPSILON', 'poly.b2Dot(direction, direction) <= FLT_EPSILON * FLT_EPSILON'),
            ('save-normal', 'nonUnitNormal = direction;', 'nonUnitNormal = Vec2();'),
            ('support-A-index', 'vertex.indexA = b2FindSupport(&proxyA, direction);', 'vertex.indexA = 0i32;'),
            ('support-B-index', 'vertex.indexB = b2FindSupport(&localProxyB, poly.b2Neg(direction));', 'vertex.indexB = 0i32;'),
            ('support-w-sign', 'vertex.w = b2Sub(vertex.wA, vertex.wB);', 'vertex.w = b2Sub(vertex.wB, vertex.wA);'),
            ('support-keeps-old-defined-a', 'vertex.w = b2Sub(vertex.wA, vertex.wB);', 'vertex.w = b2Sub(vertex.wA, vertex.wB); vertex.aDefined = false;'),
            ('support-count', 'iteration = iteration + 1i32;', 'iteration = iteration + 2i32;'),
            ('duplicate-A', 'vertex.indexA == saveA[di]', 'true'),
            ('duplicate-B', 'vertex.indexB == saveB[di]', 'true'),
            ('output-normal', 'output.normal = normal;', 'output.normal = Vec2();'),
            ('output-distance-b-minus-a', 'output.distance = b2Distance(localPointA, localPointB);', 'output.distance = 0.0f32;'),
            ('output-pointA', 'output.pointA = b2TransformPoint(input.transformA, localPointA);', 'output.pointA = Vec2();'),
            ('output-pointB', 'output.pointB = b2TransformPoint(input.transformA, localPointB);', 'output.pointB = Vec2();'),
            ('output-iterations', 'output.iterations = iteration;', 'output.iterations = 0i32;'),
            ('output-simplexCount', 'output.simplexCount = trace.stored;', 'output.simplexCount = 0i32;'),
            ('normal-end-writes-cache', 'b2MakeSimplexCache(cache, &simplex);', ''),
            ('useRadii', 'input.useRadii and output.distance', 'true and output.distance'),
            ('radii-strict-threshold', 'output.distance > 0.1f32 * B2_LINEAR_SLOP', 'output.distance >= 0.1f32 * B2_LINEAR_SLOP'),
            ('radii-left-subtract', 'output.distance - radiusA - radiusB', 'output.distance - (radiusA + radiusB)'),
            ('radii-pointA-even-zero', 'output.pointA = b2MulAdd(output.pointA, radiusA, normal);', ''),
            ('radii-pointB-even-zero', 'output.pointB = b2MulSub(output.pointB, radiusB, normal);', '')):
        add(ident, kernel, old, new)
    for side in ('A', 'B'):
        call = f'not validRadius(input.proxy{side}.radius)'
        add(f'GA2-RADIUS-{side}-FINITE', 'validateDistance', call, f'input.proxy{side}.radius < 0.0f32', guard=f'GA2-RADIUS-{side}-FINITE')
        add(f'GA2-RADIUS-{side}-SIGN', 'validateDistance', call, f'not finite(input.proxy{side}.radius)', guard=f'GA2-RADIUS-{side}-SIGN')
    for axis in ('x', 'y'):
        add('transform-finite-' + axis, 'validTransform', f'not finite(transform.p.{axis})', 'false',
            requirement='GA2-XF-A-' + axis.upper())
        add('point-finite-' + axis, 'validProxyPoints', f'not finite(points[i].{axis})', 'false',
            requirement='GA4-POINT-A-' + axis.upper())
                                                                         
                                                                       
    for side in ('A', 'B'):
        for label, old in (
                ('GA1-DISTANCE-' + side + '-LOW', f'not validProxyCount(input.proxy{side}.count)'),
                ('GA1-DISTANCE-' + side + '-HIGH', f'not validProxyCount(input.proxy{side}.count)'),
                ('GA4-POINT-' + side + '-X', f'not validProxyPoints(&input.proxy{side}.points, input.proxy{side}.count)'),
                ('GA4-POINT-' + side + '-Y', f'not validProxyPoints(&input.proxy{side}.points, input.proxy{side}.count)')):
            add(label, 'validateDistance', old, 'false', guard=label)
    for label in ('GA1-OFFSET-LOW', 'GA1-OFFSET-HIGH'):
        add(label, 'validateProxy', 'not validProxyCount(count)', 'false', guard=label)
    for side, expression in (('A', 'input.transformA'), ('B', 'input.transformB'), ('OFFSET', 'transform')):
        for suffix in ('X', 'Y'):
            label = 'GA2-XF-' + side + '-' + suffix
            add(label, 'validateDistance' if side != 'OFFSET' else 'validateProxy',
                'not validTransform(' + expression + ')', 'false', guard=label)
        for suffix in ('LOW', 'HIGH', 'LOW-EQUALITY', 'HIGH-EQUALITY'):
            label = 'GA2-ROT-' + side + '-' + suffix
            add(label, 'validTransform',
                '1.0f32 - 0.0006f32 < qq' if suffix.startswith('LOW') else 'qq < 1.0f32 + 0.0006f32',
                ('1.0f32 - 0.0006f32 <= qq' if suffix.startswith('LOW') else 'qq <= 1.0f32 + 0.0006f32') if suffix.endswith('EQUALITY') else 'true',
                guard=label)
    add('count-low', 'validProxyCount', 'count >= 1i32', 'true', requirement='GA1-LOW', guard='GA1-LOW')
    add('count-high', 'validProxyCount', 'count <= 8i32', 'true', requirement='GA1-HIGH', guard='GA1-HIGH')
    add('GA3-COUNT4', 'validCache', 'cache.count > 3i32', 'false', guard='GA3-COUNT4')
    for side, count in (('A', 'countA'), ('B', 'countB')):
        add('GA3-INDEX-' + side, 'validCache', f'cache.index{side}[i] >= {count}', 'false', guard='GA3-INDEX-' + side)
    for label, old, new in (
            ('LOW', '1.0f32 - 0.0006f32 < qq', 'true'),
            ('HIGH', 'qq < 1.0f32 + 0.0006f32', 'true'),
            ('LOW-EQUALITY', '1.0f32 - 0.0006f32 < qq', '1.0f32 - 0.0006f32 <= qq'),
            ('HIGH-EQUALITY', 'qq < 1.0f32 + 0.0006f32', 'qq <= 1.0f32 + 0.0006f32')):
        add('rotation-' + label, 'validTransform', old, new, requirement='GA2-ROT-A-' + label,
            guard='GA2-ROT-A-' + label)
                                                                         
                                                                              
    for ident, function, old, new in (
        ('support-initial-value', 'b2FindSupport', 'poly.b2Dot(proxy.points[0i32], direction)', '0.0f32'),
        ('support-start-index1', 'b2FindSupport', 'var i: i32 = 1i32;', 'var i: i32 = 2i32;'),
        ('support-loop-count', 'b2FindSupport', 'i < proxy.count', 'i < proxy.count - 1i32'),
        ('support-best-index-update', 'b2FindSupport', 'bestIndex = i;', 'bestIndex = 0i32;'),
        ('support-best-value-update', 'b2FindSupport', 'bestValue = value;', 'bestValue = bestValue;'),
        ('cache-in-loop-count', 'b2MakeSimplexFromCache', 'i < s.count', 'i < s.count - 1i32'),
        ('cache-in-pointA', 'b2MakeSimplexFromCache', 'vertex.wA = proxyA.points[vertex.indexA];', 'vertex.wA = Vec2();'),
        ('cache-in-pointB', 'b2MakeSimplexFromCache', 'vertex.wB = proxyB.points[vertex.indexB];', 'vertex.wB = Vec2();'),
        ('seed0-indexA', 'b2MakeSimplexFromCache', 's.v1.indexA = 0i32;', 's.v1.indexA = proxyA.count - 1i32;'),
        ('seed0-indexB', 'b2MakeSimplexFromCache', 's.v1.indexB = 0i32;', 's.v1.indexB = proxyB.count - 1i32;'),
        ('seed0-pointA', 'b2MakeSimplexFromCache', 's.v1.wA = proxyA.points[0i32];', 's.v1.wA = Vec2();'),
        ('seed0-pointB', 'b2MakeSimplexFromCache', 's.v1.wB = proxyB.points[0i32];', 's.v1.wB = Vec2();'),
        ('seed0-w-sign', 'b2MakeSimplexFromCache', 'b2Sub(s.v1.wA, s.v1.wB)', 'b2Sub(s.v1.wB, s.v1.wA)'),
        ('seed0-count1', 'b2MakeSimplexFromCache', 's.count = 1i32;', 's.count = 0i32;'),
        ('localB-count', 'shapeDistanceKernel', 'localProxyB.count = input.proxyB.count;', 'localProxyB.count = 1i32;'),
        ('localB-radius', 'shapeDistanceKernel', 'localProxyB.radius = input.proxyB.radius;', 'localProxyB.radius = 0.0f32;'),
        ('localB-loop-count', 'shapeDistanceKernel', 'pi < localProxyB.count', 'pi < localProxyB.count - 1i32'),
        ('localB-point-transform', 'shapeDistanceKernel', 'localProxyB.points[pi] = b2TransformPoint(transform, input.proxyB.points[pi]);', 'localProxyB.points[pi] = input.proxyB.points[pi];'),
        ('trace-reset-stored', 'shapeDistanceKernel', 'trace.stored = 0i32;', 'trace.stored = 1i32;'),
        ('vertex-slot0', 'simplexVertex', 'if (index == 0i32) return &s.v1;', 'if (index == 0i32) return &s.v2;'),
        ('vertex-slot1', 'simplexVertex', 'if (index == 1i32) return &s.v2;', 'if (index == 1i32) return &s.v1;'),
        ('vertex-slot2', 'simplexVertex', 'return &s.v3;', 'return &s.v1;'),
        ('normal-initial-zero', 'shapeDistanceKernel', 'var nonUnitNormal = Vec2();', 'var nonUnitNormal = Vec2(1.0f32, 1.0f32);'),
        ('dispatch-count1-direction', 'shapeDistanceKernel', 'direction = poly.b2Neg(simplex.v1.w);', 'direction = Vec2();'),
        ('dispatch-count2-Solve2', 'shapeDistanceKernel', 'direction = b2SolveSimplex2(&simplex);', 'direction = Vec2();'),
        ('dispatch-count3-Solve3', 'shapeDistanceKernel', 'direction = b2SolveSimplex3(&simplex);', 'direction = Vec2();'),
        ('early-pointA-transform', 'overlapOutput', 'result.pointA = b2TransformPoint(input.transformA, localPointA);', 'result.pointA = localPointA;'),
        ('early-pointB-transform', 'overlapOutput', 'result.pointB = b2TransformPoint(input.transformA, localPointB);', 'result.pointB = localPointB;'),
        ('early-zero-normal-x', 'DistanceOutput', 'normal: Vec2 = Vec2();', 'normal: Vec2 = Vec2(1.0f32, 0.0f32);'),
        ('early-zero-normal-y', 'DistanceOutput', 'normal: Vec2 = Vec2();', 'normal: Vec2 = Vec2(0.0f32, 1.0f32);'),
        ('early-zero-distance', 'DistanceOutput', 'distance: f32 = 0.0f32;', 'distance: f32 = 1.0f32;'),
        ('early-zero-iterations', 'DistanceOutput', 'iterations: i32 = 0i32;', 'iterations: i32 = 1i32;'),
        ('early-zero-simplexCount', 'DistanceOutput', 'simplexCount: i32 = 0i32;', 'simplexCount: i32 = 1i32;'),
        ('checked-distance-R-wiring', 'shapeDistanceCached', 'let check: Validation = validateDistance(input, cache);', 'let check: Validation = Validation();'),
        ('checked-distance-D-wiring', 'shapeDistanceCachedDebug', 'let check: Validation = validateDistance(input, cache);', 'let check: Validation = Validation();'),
        ('checked-refusal-cache-preserved', 'shapeDistanceCached', 'if (check.status != 0i32) return DistanceResult(check.status, check.reason, DistanceOutput());', 'if (check.status != 0i32) { cache.count = 0i32; return DistanceResult(check.status, check.reason, DistanceOutput()); }'),
        ('checked-proxy-wiring', 'makeProxy', 'let check: Validation = validateProxy(points, count, radius, Transform(), false);', 'let check: Validation = Validation();'),
        ('checked-offset-wiring', 'makeOffsetProxy', 'let check: Validation = validateProxy(points, count, radius, Transform(position, rotation), true);', 'let check: Validation = Validation();'),
        ('public-R-selects-no-debug', 'b2ShapeDistance', 'storeTrace, false)', 'storeTrace, true)'),
        ('fixture-D-selects-debug', 'b2ShapeDistanceDebug', 'storeTrace, true)', 'storeTrace, false)')):
        add(ident, function, old, new)
    return result


def constructor_data(generator, guards):
    pass                                                                          
    calls = [(kind, tuple(words), {'case': c.id, 'seq': seq})
             for c in generator.cases(128) for seq, (kind, *words) in enumerate(c.ops, 1)]
    calls += [(g['kind'] - 100, tuple(g['a']), {'guard': g['name']}) for g in guards if g['kind'] in (101, 102)]
    finite = lambda word: math.isfinite(m.number(word))
    result = []
    for kind in (1, 2):
        for predicate in ('radius-finite', 'radius-sign', 'point-X-finite', 'point-Y-finite'):
            candidates = []
            for opcode, a, key in calls:
                if opcode != kind or a[0] != 1 or not 1 <= a[1] <= 8:
                    continue
                if kind == 2 and (not all(finite(v) for v in a[23:27]) or not m.valid_rotation(a[25:27])):
                    continue
                bad = []
                if not finite(a[2]): bad.append('radius-finite')
                elif m.number(a[2]) < 0: bad.append('radius-sign')
                for axis, label in ((0, 'point-X-finite'), (1, 'point-Y-finite')):
                    if any(not finite(a[3 + 2*j + axis]) for j in range(a[1])): bad.append(label)
                if bad == [predicate]:
                    candidates.append({**key, 'model_status': m.checked_status(kind, a),
                                       'payload_sha256': __import__('hashlib').sha256((' '.join(f'{v:08x}' for v in a)).encode()).hexdigest()})
            result.append({'requirement': f'constructor-{kind + 100}/{predicate}', 'candidates': candidates,
                           'scope': 'frozen main128/all3600 operations plus existing GUARD38; no invented input'})
    return result


def execution_witness(ident, full):
    pass                                                                      
    rows = full.get('witnesses', [])
    if ident in ('checked-proxy-wiring', 'checked-offset-wiring'):
        kind = 1 if ident == 'checked-proxy-wiring' else 2
        calls = [r for r in full.get('checked_constructor_calls', []) if r['kind'] == kind]
        return next((r for r in calls if r['status'][0]), next(iter(calls), None))
    selected = None
    if ident.startswith(('solve2-', 'solve3-')):
        label = ident.split('/')[0]
        count, region = int(label[5]), label.split('-', 1)[1]
        matches = [r for r in rows if r['first_solve']['count'] == count
                   and r['first_solve']['region'] == region]
        atom = ident.split('/')[-1].split('<')[0].split('>')[0]
        selected = next((r for r in matches if atom in r['first_solve']['equal_zero']),
                        next(iter(matches), None))
    elif ident == 'zero-sign':
        selected = next((r for r in rows if r['first_solve']['count'] == 2
                         and r['first_solve']['region'] == 'w1'
                         and any(v in ('00000000', '80000000') for v in r['first_solve']['w_H'][0])), None)
    elif ident.startswith('seed0-'):
        selected = next((r for r in rows if int(r['KI_H'][0], 16) == 0), None)
    elif ident.startswith('cache-in-'):
        selected = next((r for r in rows if int(r['KI_H'][0], 16) > 0), None)
    elif ident.startswith('vertex-slot'):
        slot = int(ident[-1])
        selected = next((r for r in rows if int(r['KI_H'][0], 16) > slot), None)
    elif ident.startswith('dispatch-count'):
        count = int(ident[len('dispatch-count')])
        selected = next((r for r in rows if r['first_solve']['count'] == count), None)
    elif ident.startswith('early-'):
        selected = next((r for r in rows if r.get('D_H') and int(r['D_H'][7], 16) == 0), None)
    elif ident in ('support-best-index-update', 'support-best-value-update'):
        selected = next((r for r in rows if int(r['KI_H'][0], 16) == 0 and r.get('K_H')
                         and any(int(v, 16) > 0 for v in r['K_H'][1:1+int(r['K_H'][0],16)]
                                 + r['K_H'][4:4+int(r['K_H'][0],16)])), None)
    elif ident.startswith('support-') and ident != 'support-limit20':
        selected = next((r for r in rows if r.get('D_H') and int(r['D_H'][7],16) > 0), None)
    elif ident in ('checked-distance-R-wiring', 'checked-distance-D-wiring'):
        selected = next((r for r in rows if r.get('mode') == 1), None)
    elif ident in ('localB-count', 'localB-radius', 'localB-loop-count', 'localB-point-transform',
                   'trace-reset-stored', 'normal-initial-zero', 'public-R-selects-no-debug', 'fixture-D-selects-debug'):
        selected = next(iter(rows), None)
    if not selected:
        return None
    return {'predicate_source': 'actual C-D first KI; full physics projection R=D checked',
            **{k: selected[k] for k in ('case', 'seq', 'input_sha256', 'KI_H', 'first_solve', 'D_H', 'K_H', 'mode')
               if k in selected}}


def classification():
    pass                                                                   

                                                                            
                                                                               
       
    policy = json.loads((HERE / 'lancuchy-klasyfikacja.json').read_text(encoding='utf-8'))
    current = {
        'source_sha256': hashlib.sha256((HERE.parent / 'fizyka/odleglosc.dk').read_bytes()).hexdigest(),
        'bindings_sha256': hashlib.sha256((HERE / 'lancuchy-kotwice.json').read_bytes()).hexdigest(),
    }
    policy['scope_matches'] = all(policy.get(k) == v for k, v in current.items())
    return policy


def table(receipts=(), witnesses=(), full_result=None):
    policy = classification()
    bindings = {}
    for receipt in receipts:
        ident = receipt['requirement']
        previous = bindings.get(ident)
        if previous is None or not (previous.get('clean') and previous.get('detected')):
            bindings[ident] = receipt
    evidence = {r['requirement']: r for r in witnesses}
    source = HERE.parent / 'fizyka/odleglosc.dk'
    functions = {}
    source_text = source.read_text(encoding='utf-8') if source.is_file() else ''
    if source.is_file():
        for line, text in enumerate(source_text.splitlines(), 1):
            match = re.match(r'(?:fun|class) ([A-Za-z0-9_]+)', text)
            if match:
                functions[match[1]] = 'silnik/fizyka/odleglosc.dk:' + str(line)
    intents = {p['requirement']: p for p in proposals()}
    rows = []
    for requirement in requirements():
        ident = requirement['id']
        receipt = bindings.get(ident)
        witness = receipt.get('witness') if receipt and receipt.get('witness') else evidence.get(ident)
        if witness and witness.get('guard'):
                                                                           
                                                                        
            witness = {**witness, 'case': None, 'seq': 0, 'local_id': 1,
                       'first_solve': None, 'helper_only': True}
        good = bool(receipt and witness and receipt.get('clean') and receipt.get('detected')
                    and receipt.get('native_executed') and receipt.get('baseline_ok')
                    and receipt.get('single_hit') and receipt.get('anchor_owner') == 'T-13a-2a')
        intent = intents.get(ident)
        location = receipt.get('port') if receipt else functions.get(requirement.get('port_function'))
        location_kind = 'bound-native-line' if receipt else 'function-start'
        if intent and not receipt:
            location = functions.get(intent['function'])
            begin = re.search(r'^(?:fun|class) ' + re.escape(intent['function']) + r'\b', source_text, re.M)
            if begin:
                following = re.search(r'^(?:fun|class) \w+', source_text[begin.start()+1:], re.M)
                end = begin.start()+1+following.start() if following else len(source_text)
                body = source_text[begin.start():end]
                if body.count(intent['needle']) == 1:
                    line = source_text[:begin.start()+body.index(intent['needle'])].count('\n')+1
                    location = 'silnik/fizyka/odleglosc.dk:' + str(line)
                    location_kind = 'read-only-source-location-not-anchor'

        execution = execution_witness(ident, full_result) if full_result else None
        reason = None
        if not good:
            if requirement['kind'] == 'route-gap':
                data = next((r for r in (full_result or {}).get('constructor_data', [])
                             if r['requirement'] == ident), None)
                reason = ('Dane istnieja, ale missing osobnego native tej drogi: ' + str(data['candidates'])
                          if data and data['candidates'] else requirement['gap'])
            elif receipt and receipt.get('native_executed'):
                reason = ('No clean defined result: ' + str(receipt.get('error', 'see native attempts'))
                          if not receipt.get('clean') else
                          'missing Ebfb4f99c641f E50e721e49c01 E07faf1595531 E4d4f5985df07 Eb715bde7beef; E956cb3b1ab25 E4a6bcefc0ce6 E50e721e49c01 native.attempts; missing E39319e9dea17, Ecd5b158f21b7 E6b50ba3fbd32')
            elif ident == 'support-limit20':
                reason = 'Q20: missing E75ea2d3dbab3 swiadka20; NOT_FOUND Ecd5b158f21b7 E955abb4765cc Ebd2dc90fea6d'
            elif ident == 'checked-refusal-cache-preserved':
                reason = 'E5dc1c90633c4 Ec09b5e76a85d E503a10e6d9bc Ed54dc313906d Ed32cef4de28c: missing KI/K, E874900292abe E5f0b3f1e182b E4a32c3c6b097 E6199aecf23ab E1dff3d4cfb44; E0b75fea156f7 O Ecd5b158f21b7 E140103883838 Ead7e92df0fe3 Ed32cef4de28c'
            elif ident == 'GA5-COPY':
                reason = 'GUARD103 sprawdza kopie wartosci; missing oddzielnego wykonanego mutanta aliasu produktu'
            else:
                reason = 'missing E6f8e155e0a3b Eeaf5afe71f3c Ede7d1b721a1e Ebef32d2c315a E36984836e1a8 Eec1a1c40a1a2 E3268fef5c876; E92c64e90e189 E81083029a924 wlasciciel2a'
        equivalence = {
            'solve3-triangle/direction0': 'Only current13a kernel caller: count3 returns overlapOutput before reading direction; no claim about arbitrary direct helper callers.',
            'localB-radius': 'Current kernel copies localProxyB.radius, but cache/support/witness read only count/points; radii branch reads input.proxyB.radius directly.',
            'normal-initial-zero': 'Every path to final Normalize has passed nonUnitNormal=direction before support count increment; earlier paths return overlapOutput without reading nonUnitNormal.'
        }.get(ident)
        proof = policy['equivalences'].get(ident) if policy['scope_matches'] else None
        if proof and receipt and receipt.get('clean') and receipt.get('detected'):
                                                                          
                                                                       
            good, proof = False, None
            reason = 'Equivalence claim contradicted by a clean native difference'
                                                                              
        if proof:
            good, witness, reason = False, None, None
        rows.append({**requirement, 'port': location, 'witness': witness, 'execution_observation': execution,
                     'native': receipt, 'verified': good, 'gap_reason': reason,
                     'proposal_available': intent is not None, 'port_location_kind': location_kind,
                     'equivalence_argument_pending_review': None if proof else equivalence,
                     'equivalence_proof': proof,
                     'classification_authority': policy['authority'] if proof else None,
                     'status': 'EQUIVALENT_PROVEN' if proof else 'NATIVE_VERIFIED' if good else 'GAP_UNVERIFIED'})
    return {'rows': rows, 'required': len(rows), 'verified': sum(r['verified'] for r in rows),
            'equivalent_proven': sum(r['status'] == 'EQUIVALENT_PROVEN' for r in rows),
            'gaps': [r['id'] for r in rows if r['status'] == 'GAP_UNVERIFIED'],
            'classification_scope_matches': policy['scope_matches'],
            'code': int(any(r['status'] == 'GAP_UNVERIFIED' for r in rows))}


def markdown(result):
    lines = ['# Gałąź → case 13a', '', '| Wymaganie | C | Port | Przypadek/seq | Wynik | Powod luki |',
             '|---|---|---|---|---|---|']
    for r in result['rows']:
        lines.append('| ' + ' | '.join(str(r.get(k) or 'UNVERIFIED').replace('|', '/')
                                     for k in ('id', 'original', 'port', 'witness', 'status', 'gap_reason')) + ' |')
    return '\n'.join(lines) + '\n'


def requirements13b():
    pass                                                                     

                                                                             
                                                              
       
    manifest = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    cases = [r for r in manifest['przypadki'] if r['profil'] == 'PORT13B']
    m.require([r['id'] for r in cases] == list(range(1, 65)), 'complete frozen B64')
    rows = []
    def add(ident, original, mutation_class, difference, function=None, candidates=None):
        ids = candidates if candidates is not None else [r['id'] for r in cases
            if mutation_class in r['swiadczyKlasyMutacji']]
        rows.append({'id': ident, 'original': original, 'class': mutation_class,
                     'candidate_ids': ids, 'difference_required': difference,
                     'port_function': function, 'kind': 'algorithm'})
    for branch, first in (('loop-main', 409), ('loop-tail1', 424),
                          ('loop-tail2', 438), ('open', 460)):
        loop = branch.startswith('loop')
        cls = 'M-LOOP-WRAP' if loop else 'M-OPEN-GHOST'
        for field, offset in (('ghost1', 0), ('point1', 1), ('point2', 2), ('ghost2', 3)):
            add(branch + '/' + field, f'src/shape.c:{first + offset}', cls,
                f'CS13.{field} or child G40 endpoints differ', 'b2CreateChain')
        line = 416 if branch == 'loop-main' else 430 if branch == 'loop-tail1' else 444 if branch == 'loop-tail2' else 467
        for count in ('one', 'N'):
            add(branch + '/material-' + count, f'src/shape.c:{line}',
                'M-CHAIN-MATERIAL-INDEX' if loop else 'M-OPEN-MATERIAL',
                'child S material differs, whole-chain materials[0] unchanged', 'b2CreateChain')
        add(branch + '/child-allocation-order', 'src/shape.c:' + str(first + (10 if branch == 'loop-main' else 9 if loop else 10)),
            'M-CREATE-ORDER' if loop else 'M-OPEN-COUNT',
            'CI13/QL13 ordered ShapeNumber, pool or body list differs', 'b2CreateChain')
    for ident, line, cls, diff in (
        ('create/loop-count', 401, 'M-LOOP-WRAP', 'segmentCount=N'),
        ('create/open-count', 453, 'M-OPEN-COUNT', 'segmentCount=N-3'),
        ('create/list-growth', 356, 'M-LIST-REF-GROW', 'all existing/new chains and children retained after growth'),
        ('create/id', 367, 'M-POOL-LIFO', 'chain slot and occupied metadata'),
        ('create/parent-body', 368, 'M-DESTROY-LINK', 'CH13.bodyId and CQ13 BodyNumber'),
        ('create/next', 369, 'M-DESTROY-LINK', 'CH13.nextChainId and BH13 head'),
        ('create/generation', 370, 'M-GENERATION-WRAP', 'CG13 generation wraps65535 to0 in explicit fixture'),
        ('create/material-count', 373, 'M-SET-MATERIALS-LOOP', 'all CM13 entries, including last'),
        ('create/material-copy', 384, 'M-INPUT-ALIAS', 'CM13 unchanged after109 release0 then1'),
        ('create/body-head', 387, 'M-DESTROY-LINK', 'BH13 new head and full chain list'),
        ('create/object', 390, 'M-CREATE-ORDER', 'all child object tokens match description'),
        ('create/filter', 391, 'M-CREATE-ORDER', 'all child category/mask/group exact'),
        ('create/sensor-events', 392, 'M-CREATE-ORDER', 'all child sensor flags exact'),
        ('create/contact-events', 393, 'M-CREATE-ORDER', 'child initial contact=false'),
        ('create/hit-events', 394, 'M-CREATE-ORDER', 'child initial hit=false'),
        ('destroy/link-match', 505, 'M-DESTROY-LINK', 'head/middle/tail/sole chain unlink, other shapes retained'),
        ('destroy/unlink-next', 507, 'M-DESTROY-LINK', 'BH13/CH13 next link differs'),
        ('destroy/list-advance', 512, 'M-DESTROY-LINK', 'middle/tail chain removal differs'),
        ('destroy/children-loop', 522, 'M-DESTROY-ORDER', 'all children removed in CI creation order'),
        ('destroy/child-index', 524, 'M-DESTROY-ORDER', 'shape LIFO and remaining shapes differ'),
        ('destroy/wake', 526, 'M-DESTROY-ORDER', 'wake flag propagated; contact wake/end itself belongs to13c'),
        ('destroy/free-chain', 533, 'M-POOL-LIFO', 'IP13 LIFO/reuse differs'),
        ('destroy/dead-id', 534, 'M-CHAIN-LIFE', 'CG13 occupied false, V13 false'),
        ('get/world', 542, 'M-CHAIN-LIFE', 'CQ13 world.raw3 and WorldNumber5'),
        ('get/segment-count', 554, 'M-CAPACITY', 'CQ13 segmentCount'),
        ('get/capacity', 567, 'M-CAPACITY', 'CQ13 returnedCount=min(count,capacity)'),
        ('get/segment-order', 570, 'M-CAPACITY', 'QL13 order and child identity'),
        ('get/segment-generation', 572, 'M-STALE-RESTAMP', 'QL13 child generation from actual live record'),
        ('parent/type', 1462, 'M-PARENT', 'PC13 hasParent false for ordinary shape'),
        ('parent/nonempty', 1465, 'M-PARENT', 'PC13 current chain raw/typed number'),
        ('parent/generation', 1468, 'M-STALE-RESTAMP', 'PC13 actual generation and birth'),
    ):
        add(ident, f'src/shape.c:{line}', cls, diff)
    for setter, field, lines in (
        ('friction', 'friction', (1489, 1491, 1496, 1500, 1508)),
        ('restitution', 'restitution', (1524, 1526, 1531, 1535, 1543)),
        ('material', 'materialId', (1556, 1558, 1563, 1567, 1575)),
    ):
        for site, line, cls, diff in zip(
            ('materials-bound', 'materials-assignment', 'shapes-bound', 'shapes-assignment', 'getter0'),
            lines,
            ('M-SET-MATERIALS-LOOP', 'M-SET-MATERIALS-LOOP', 'M-SET-SHAPES-LOOP', 'M-SET-SHAPES-LOOP', 'M-GETTER-MATERIAL0'),
            ('last CM13 changed', 'every CM13 field exact', 'last child S changed', 'every child S field exact', 'CQ13 reads materials[0] even for open first child material1')):
            add('set/' + setter + '/' + site, f'src/shape.c:{line}', cls, diff)
        add('set/' + setter + '/preserve-other-fields', 'src/shape.c:' + str(lines[1]),
            'M-SET-MATERIALS-LOOP', 'rolling/tangent/color and other material fields unchanged')
    for ident, original, cls, diff in (
        ('raw/restitution-negative', 'src/shape.c:1513', 'M-RAW-RESTITUTION', 'finite negative restitution accepted only by raw setter'),
        ('child/default-density1', 'src/types.c:59;src/shape.c:389', 'M-CHAIN-MASS', 'S.density=3f800000, massData four+0'),
        ('child/zero-mass', 'src/shape.c:717', 'M-CHAIN-MASS', 'massData four+0 for raw dynamic/kinematic too'),
        ('child/centroid', 'src/shape.c:614', 'M-GHOST-AABB', 'midpoint only p1/p2; ghost excluded'),
        ('child/AABB', 'src/shape.c:591', 'M-GHOST-AABB', 'AABB from solid endpoints, with speculative margin'),
        ('child/minExtent', 'src/shape.c:778', 'M-GHOST-AABB', 'minExtent=+0'),
        ('child/maxExtent', 'src/shape.c:779-781', 'M-GHOST-AABB', 'extent from p1/p2 relative to localCenter'),
        ('child/static-move-buffer', 'src/types.c:62;src/shape.c:419,433,447,470', 'M-DISABLED-PROXY', 'static invokeContactCreation retains moveBuffer'),
        ('world/initial-chain-list', 'src/world.c:163', 'M-WORLD-FREE', 'world starts with empty chain list/pool'),
        ('world/free-live-loop', 'src/world.c:294-299', 'M-WORLD-FREE', 'three live chains freed, one previously dead skipped'),
        ('world/skip-dead', 'src/world.c:297-304', 'M-WORLD-FREE', 'no freed list dereference'),
        ('world/list-destroy', 'src/world.c:319', 'M-WORLD-FREE', 'chain storage released; historical copies unchanged'),
        ('body/destroy-chain-loop', 'src/body.c:395-405', 'M-BODY-NEXT-CHAIN', 'all three+ chains released without a second shape destroy'),
        ('body/destroy-next', 'src/body.c:405', 'M-BODY-NEXT-CHAIN', 'stored next link survives free/id change'),
        ('id/store-high', 'include/box2d/id.h:134', 'M-ID-PACKING', 'helper113 low8000ffff/high80000001'),
        ('id/load-fields', 'include/box2d/id.h:140', 'M-ID-PACKING', 'all index1/world0/generation roundtrip'),
        ('valid/world-range', 'src/world.c:1648', 'M-CHAIN-LIFE', 'raw validity false for invalid world'),
        ('valid/world-live', 'src/world.c:1654', 'M-CHAIN-LIFE', 'raw validity false for dead world'),
        ('valid/chain-range', 'src/world.c:1661', 'M-CHAIN-LIFE', 'raw validity false outside chain array'),
        ('valid/chain-occupied', 'src/world.c:1667', 'M-CHAIN-LIFE', 'raw validity false for freed chain'),
        ('valid/chain-generation', 'src/world.c:1675', 'M-CHAIN-LIFE', 'raw validity compares all16 generation bits'),
    ):
        add(ident, original, cls, diff)
    guards = [r for r in manifest['guardPrzypadki'] if r['czesc'] == '13b']
    for r in guards:
        rows.append({'id': r['id'], 'original': 'KONTRAKT-13/1 §3/5/6/11.2',
                     'class': list(r['swiadczyKlasyMutacji']), 'candidate_ids': [r['id']],
                     'helper': r['Gkind'], 'kind': 'guard',
                     'counted_as_kill': r['liczonyJakoZabicie'],
                     'difference_required': 'defined different native result' if r['liczonyJakoZabicie'] else
                                            'baseline refusal + explicit equivalence/control proof; no kill'})
                                                                            
    for site, candidates in (
        ('proper/opposite-sign-o1o2', ['GB5-CROSS', 'GB5-CLOSE']),
        ('proper/opposite-sign-o3o4', ['GB5-CROSS', 'GB5-CLOSE']),
        ('adjacent/j=i+1', ['GB5-ADJACENT', 'GB5-ALLOW-STRAIGHT']),
        ('adjacent/loop-0-last', ['GB5-CLOSE']),
        ('overlap/strict-positive', ['GB5-ADJACENT', 'GB5-ALLOW-STRAIGHT']),
        ('axis/abs-dx-vs-dy', ['GB5-ADJACENT', 'GB5-COLLINEAR']),
        ('axis/tie-uses-x', ['GB5-CLOSE']),
        ('closed/final-edge', ['GB5-CLOSE']),
    ):
        add('intersection/' + site, 'KONTRAKT-13/1 §6', 'M-GUARD-INTERSECTION',
            'A13 or GR13 accept/refuse changes; all other predicates retained', candidates=candidates)
                                                                          
                                                                            
                                               
    for coordinate in ('x','y'):
        for bound in ('min-inclusive','max-inclusive'):
            add(f'intersection/onSegment/{coordinate}/{bound}',
                'KONTRAKT-13/1 §6','M-GUARD-INTERSECTION',
                'single shared closed bound has a non-shadowed native witness',
                candidates=['GB5-COLLINEAR','GB5-TOUCH'])
    for orientation in range(4):
        add(f'intersection/onSegment-call{orientation}','KONTRAKT-13/1 §6',
            'M-GUARD-INTERSECTION','single call route removed, all other routes retained',
            candidates=['GB5-COLLINEAR','GB5-TOUCH'])
                                                                              
                                                                    
    classes = sorted({c for row in cases for c in row['swiadczyKlasyMutacji']})
    for cls in classes:
        add('manifest-class/' + cls, 'lancuchy-przypadki.json PORT13B', cls,
            'every assigned function/observation covered by clean native mutations')
    m.require(len({r['id'] for r in rows}) == len(rows), '13b requirement ids unique')
    return rows


def predicate_audit13b(guards):
    pass                                                                      
    result = []
    for row in guards:
        if row['kind'] != 200 or row['id'].startswith('GB6-'):
            continue
        g = m.geometry_predicates13b(row['points'], bool(row['ga'][5]))
        disabled = {'GB5-COLLINEAR': 'collinear', 'GB5-ADJACENT': 'adjacent_overlap',
                    'GB5-CROSS': 'proper_cross', 'GB5-TOUCH': 'touch',
                    'GB5-CLOSE': 'closing_edge'}.get(row['id'])
        remaining = None
        if disabled:
            remaining = [x for x in g['refusals'] if (
                x.get('j') != len(row['points']) - 1 if disabled == 'closing_edge' else
                x['kind'] != disabled)]
        result.append({'id': row['id'], 'geometry': g,
                       'disabled_predicate_class': disabled,
                       'remaining_refusals': remaining,
                       'shadowed': bool(remaining) if remaining is not None else None,
                       'native_mutation': False})
    return result


def accounting_spec13b():
    pass                                                                        
    data=json.loads((HERE/'lancuchy-rozliczenie-13b.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    m.require(digest=='d54a60a44d508c0d25b1c336a74bff40f17099cfb2d9cbdf5371e184823ed6aa',
              'accounting population/operand links changed; explicit reviewed reconciliation required')
    m.require(data.get('not_an_anchor_inventory') is True,'Accounting data is not a source-bound anchor inventory')
    for row in data['rows']:
        if row.get('kind')=='atomic_predicate' and row.get('predicate_token') in ('<','>','<=','>=','==','!='):
            m.require(any(t['kind']=='comparison' and t['start']==row['source_column']-row.get('source_leading_columns',0) and t['token']==row['predicate_token'] for t in source_operators13(row['source_text'])),
                      'comparison atom is not a maximal lexical comparison: '+row['id'])
    m.require(len(data['rows'])==531 and len(set(data['original_row_ids']))==775,
              'complete pinned W1 population required')
    return data


def product_sites13b(root=None):
    pass                                                                    

                                                                               
                                                                              
       
    data=accounting_spec13b();root=Path(root) if root else HERE.parents[1]
    actual={}
    for relative,expected in data['sources'].items():
        path=root/relative
        actual[relative]=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                                                                             
                                                                              
    game=root/'silnik/fizyka/gra.dk';world=root/'silnik/fizyka/swiat.dk'
    if game.is_file() and world.is_file() and not world.read_bytes():
        text=game.read_text(encoding='utf-8')
        if re.fullmatch(r'fun chainOnSegment\([^\n]+\{[^\n]+\}\s*',text) and len(text)<256:
            fixture={'id':'fixture/chainOnSegment','function':'chainOnSegment','source_text':text.strip(),
                     'candidate_ids':['GB5-COLLINEAR','GB5-TOUCH'],'native_verified':False}
            return {'sources':data['sources'],'actual_sources':actual,'source_matches':False,
                    'rows':[fixture],'supplemental_rows':[],'required':1,'native_verified':0,
                    'complete':False,'fixture_only':True,'final_K':False}
    return {'sources':data['sources'],'actual_sources':actual,'source_matches':actual==data['sources'],
            'rows':data['rows'],'supplemental_rows':data.get('supplemental_rows',[]),
            'required':len(data['rows']),'native_verified':0,'final_K':data['final_K'],
            'complete':False,'denominator_source':'versioned accounting graph; no Git invocation'}


def table13b(guards, receipts=(), observations=(), product_root=None, equivalences=(), controls=()):
    pass                                                                      

                                                                              
                                                                             
                                                                            
       
    spec=accounting_spec13b();inventory=product_sites13b(product_root)
                                                                             
    requirements=requirements13b()+spec['rows']+spec.get('supplemental_rows',[])
    ids=[r['id'] for r in requirements]
    m.require(len(set(ids))==len(ids) and set(ids)==set(spec['relations']),
              'complete accounting population/relations required')
    m.require(len({r['id'] for r in guards})==96,'all 96 guard rows required')
    m.require({r['id'] for r in guards}=={r['id'] for r in requirements if r.get('kind')=='guard'},
              'exact frozen guard IDs required')
    receipts=list(receipts);by_id={}
    for receipt in receipts:
        m.require(receipt.get('requirement') in ids,'unknown native13b requirement')
        key=receipt.get('id',receipt['requirement'])
        m.require(key not in by_id,'duplicate native13b receipt')
        by_id[key]=receipt
    control_map={r['id']:r for r in controls}
    m.require(len(control_map)==len(controls),'duplicate control13b receipt')
    proof_map={r['id']:r for r in equivalences}
    m.require(len(proof_map)==len(equivalences),'duplicate equivalence13b proof')
    obs={r['id']:r for r in observations}
    full_baseline=(set(obs)==set(range(1,65)) and all(
        r.get('native_processes_ok') is True and r.get('END_EOF') is True and
        all(r.get('validated',{}).get(k) is True for k in ('c0','c1','d')) for r in obs.values()))
    credited={};rejected=[]
    def clean_run(run):
        return (run.get('code')==0 and run.get('stderr_bytes')==0 and run.get('stdout_bytes',0)>0 and
                re.fullmatch('[0-9a-f]{64}',run.get('binary_sha256','')) is not None)
    for receipt in receipts:
        link=spec['receipt_links'].get(receipt.get('id'))
        clean=all(receipt.get(k) is True for k in ('native_executed','baseline_ok','single_hit','clean','detected'))
        difference=receipt.get('difference',{}) or {}
        authority=(receipt.get('anchor_owner')=='T-13b-2a' if link and not link.get('native_authority') else
                   bool(link) and receipt.get('native_authority')==link.get('native_authority') and
                   receipt.get('citation')==link.get('citation'))
        clean=clean and authority and bool(difference)
        clean=clean and difference.get('baseline')!=difference.get('actual')
        clean=clean and (product_root is None or inventory['source_matches'])
        if link:
            clean=clean and receipt.get('requirement')==link['owner_requirement'] and receipt.get('port')==link['port']
            clean=clean and receipt.get('product_sha256')==link['mutant_sha256']
            clean=clean and receipt.get('build',{}).get('code')==0 and clean_run(receipt.get('run',{}))
            for side in ('C','D'):
                baseline=receipt.get('baseline_'+side,{})
                clean=clean and clean_run(baseline)
                clean=clean and baseline.get('input_sha256')==link['input_sha256'][side]
            clean=clean and receipt.get('run',{}).get('input_sha256')==link['input_sha256']['D']
                                                                          
                                                                      
            target=link['target']
            clean=clean and spec['relations'][target]['type']=='native_target'
            if clean:credited.setdefault(target,[]).append((receipt,link))
        else:clean=False
        if not clean:rejected.append({'id':receipt.get('id'),'reason':'No matching complete atomic proof; survived/compound/stale/unclean or unknown rotation'})
    result={}
    def resolve(ident,stack=()):
        m.require(ident not in stack,'cyclic aggregate13b')
        if ident in result:return result[ident]
        relation=spec['relations'][ident];kind=relation['type'];refs=[];verified=False
        if kind=='native_target':
            for receipt,link in credited.get(ident,[]):
                refs.append({'type':'native_target','receipt_id':receipt['id'],
                             'source_sha256':link['source_sha256'],'mutant_sha256':link['mutant_sha256'],
                             'changed_operand_and_field':link['changed_statements'],'rotation':link['rotation'],
                             'sharing_rule':link['sharing_rule']})
            verified=bool(refs)
        elif kind=='control_trial':
            control=control_map.get(relation['control'],{});valid=control.get('ok') is True and control.get('control_only') is True
            valid=valid and (product_root is None or inventory['source_matches'])
            for side in ('C','D'):
                data=control.get('sides',{}).get(side,{});run=data.get('run',{});model=data.get('model',{})
                valid=valid and data.get('ok') is True and clean_run(run)
                valid=valid and run.get('input_sha256')==spec['control_inputs'][ident][side]
                valid=valid and model.get('END_EOF') is True and bool(model.get('sha256'))
            verified=bool(valid)
            if verified:refs=[{'type':'control_trial','guard':ident,'citation':relation['citation'],
                              'counted_as_native_kill':False}]
        elif kind=='equivalence_proof':
            proof=proof_map.get(relation['proof'],{})
            valid=(full_baseline and inventory['source_matches'] and proof.get('conditions_present') is True and
                   proof.get('native_baseline_verified') is True and proof.get('counted_as_kill') is False and
                   proof.get('source_sha256')==inventory['sources'].get(proof.get('source')) and bool(proof.get('proof')))
            verified=bool(valid)
            if verified:refs=[{'type':'equivalence_proof','id':relation['proof'],'citation':relation['citation'],
                              'source_sha256':proof['source_sha256'],'conditions':proof['proof'],
                              'native_full64_baseline':True,'counted_as_native_kill':False}]
        elif kind=='aggregate':
            components=relation.get('components',[])
            m.require(components and len(components)==len(set(components)),'empty/duplicate aggregate13b')
                                                            
            states=[resolve(child,stack+(ident,)) for child in components]
            verified=all(r['verified'] for r in states)
            refs=[{'type':'aggregate','component':child,'verified':state['verified']} for child,state in zip(components,states)]
        else:raise ValueError('unknown accounting13b type '+kind)
        status=('NATIVE_VERIFIED' if kind=='native_target' else 'CONTROL_VERIFIED' if kind=='control_trial' else
                'EQUIVALENCE_VERIFIED' if kind=='equivalence_proof' else 'AGGREGATE_VERIFIED') if verified else 'GAP_'+kind.upper()
        state={'verified':verified,'status':status,'accounting_type':kind,'accounting':relation,'evidence_refs':refs}
        result[ident]=state;return state
    rows=[]
    for row in requirements:
        state=resolve(row['id']);native=next((r for r in receipts if r.get('requirement')==row['id']),None)
        rows.append({**row,**state,'native':native,'scope':'13b','inherited_model12':False,
                     'counted_as_kill':False if state['accounting_type'] in ('control_trial','equivalence_proof','aggregate') else row.get('counted_as_kill',True),
                     'gap_reason':None if state['verified'] else 'Required '+state['accounting_type']+' evidence incomplete'})
    cases=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))['przypadki']
    reachability=[{**{k:r[k] for k in ('id','rodzina','celSzczegolny','swiadczyKlasyMutacji')},
        'status':'NATIVE_OBSERVED_PARTIAL_MODEL' if obs.get(r['id'],{}).get('native_processes_ok') and
           obs.get(r['id'],{}).get('END_EOF') and all(obs.get(r['id'],{}).get('validated',{}).get(k) is True for k in ('c0','c1','d')) else 'UNVERIFIED',
        'observation':obs.get(r['id']),'reason':'Full BASE12 acceptance is deferred, not waived'} for r in cases if r['profil']=='PORT13B']
    remaining=[{'id':r['id'],'port':r.get('port'),'source_text':r.get('source_text'),
        'identity':r['accounting'].get('identity',r.get('difference_required',r.get('source_text'))),
        'candidate_ids':r.get('candidate_ids',[]),'scope':'13b','inherited_model12':False}
        for r in rows if r['accounting_type']=='native_target' and not r['verified']]
    gaps=[r['id'] for r in rows if not r['verified']]
    from collections import Counter
    return {'rows':rows,'product_inventory':inventory,'required':len(rows),'verified':sum(r['verified'] for r in rows),
        'gaps':gaps,'reachability':reachability,'native_receipts':len(receipts),'rejected_atomic_credits':rejected,
        'accounting_types':dict(Counter(r['accounting_type'] for r in rows)),
        'remaining_native_targets':remaining,'remaining_native_count':len(remaining),
        'inherited_dependencies':spec['inherited_dependencies'],'full_ownership_ready':False,
        'code':int(bool(gaps) or not inventory['source_matches']),
        'matrix_complete_after_final_K':not gaps and inventory['source_matches'],
        'denominator_independent_of_git':True,'full_acceptance_includes_BASE12':False}


def accounting_spec13c():
    pass                                                                  
    spec=json.loads((HERE/'lancuchy-rozliczenie-13c.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256(json.dumps(spec,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    m.require(digest=='5dc9e7f40e76ee24659b505c377749b0af876d7cf3711414a0e3aa9e96cbfcf8','13c accounting population/links changed; explicit reconciliation required')
    ids=[r['id'] for r in spec['rows']]
    m.require(ids and len(ids)==len(set(ids)),'13c complete unique inventory')
    allowed={'native_target','equivalence_proof','control_trial','aggregate'}
    m.require(all(r['type'] in allowed for r in spec['rows']),'13c four explicit accounting types')
    for row in spec['rows']:
        if row['type']=='aggregate':
            refs=row['components'];m.require(refs and len(refs)==len(set(refs)) and set(refs)<=set(ids),'13c aggregate references')
    manifest=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    classes={k for row in manifest['przypadki'] if row['profil']=='PORT13C' for k in row['swiadczyKlasyMutacji']}
    classes|={k for row in manifest['guardPrzypadki'] if row['czesc']=='13c' for k in row['swiadczyKlasyMutacji']}
    m.require(classes==set(spec['mutation_classes'])=={r['mutation_class'] for r in spec['rows'] if 'mutation_class' in r},'every manifest13c mutation class')
    return spec


def mutation_proposals13c(root=None):
    pass                                                                    
    data=json.loads((HERE/'lancuchy-receptury-13c.json').read_text(encoding='utf-8'))
    rows=data['proposals'];m.require(rows and len({r['id'] for r in rows})==len(rows),'nonempty unique13c intentions')
    return rows


def predicate_audit13c(cases,product_root=None):
    pass                                                                    
    root=Path(product_root) if product_root is not None else HERE.parents[1]
    source=(root/'silnik/fizyka/swiat.dk').read_text(encoding='utf-8')
    sites={
        'offset':('offset < 0.0f32','manifold.c:1105',0.),
        'v':('v <= 0.0f32','manifold.c:1117',0.),
        'u':('u <= 0.0f32','manifold.c:1130',0.),
        'uPrev':('uPrev <= 0.0f32','manifold.c:1123',0.),
        'vNext':('vNext > 0.0f32','manifold.c:1137',0.),
        'ee':('ee > 0.0f32','manifold.c:1148',0.),
        'length':('b2GetLengthAndNormalize','math_functions.h:321',m.number(0x34000000)),
        'separation':('separation > B2_SPECULATIVE_DISTANCE','manifold.c:1156',m.f32(.02)),
        'convex1':('smoothParams.convex1 =','manifold.c:1340',m.f32(.01)),
        'convex2':('smoothParams.convex2 =','manifold.c:1344',m.f32(.01)),
        'behind1':('let behind1: bool','manifold.c:1348',0.),
        'behind0':('if (smoothParams.convex1) behind0','manifold.c:1353',0.),
        'behind2':('if (smoothParams.convex2) behind2','manifold.c:1358',0.)}
    result={};counts={};percase=[];assignments={}
    for name,needle,original,slots in (
        ('normal','manifold.normal =','manifold.c:1165',(0,1)),
        ('anchorA','manifold.point0.anchorA =','manifold.c:1168',(6,7)),
        ('anchorB','manifold.point0.anchorB =','manifold.c:1169',(8,9)),
        ('point','manifold.point0.point =','manifold.c:1170',(4,5)),
        ('separation','manifold.point0.separation =','manifold.c:1171',(10,)),
        ('ID','manifold.point0.id =','manifold.c:1172',(15,)),
        ('pointCount','manifold.pointCount =','manifold.c:1173',(3,))):
        start=source.index('fun b2CollideChainSegmentAndCircle(');end=source.index('\nfun ',start+1);at=source.find(needle,start,end)
        assignments[name]={'port':'silnik/fizyka/swiat.dk:'+str(source[:at].count('\n')+1) if at>=0 else None,'original':original,
                           'M30_slots':slots,'reached_calls':0,'examples':[],'native_removal_verified':False}
    for key,(needle,original,threshold) in sites.items():
        function='b2CollideChainSegmentAndPolygon' if key.startswith(('convex','behind')) else 'b2CollideChainSegmentAndCircle'
        start=source.index('fun '+function+'(');end=source.find('\nfun ',start+1)
        at=source.find(needle,start,end if end>=0 else len(source))
        result[key]={'port':'silnik/fizyka/swiat.dk:'+str(source[:at].count('\n')+1) if at>=0 else None,
            'original':original,'threshold_H':f'{m.bits(threshold):08x}','below':[],'equal':[],'above':[],
            'native_difference':None,'status':'PREDICATE_ONLY_NATIVE_REMOVAL_MISSING'};counts[key]={'below':0,'equal':0,'above':0}
    for case in cases:
        if case.id>384:continue
        reached=set();refused=0;gjk=0
        for seq,op in enumerate(case.ops,1):
            a=op['a']
            if a[1] and m.direct_status13c(a)[0]:refused+=1;continue
            pred=m.circle_predicates13c(a) if a[0]==0 else m.polygon_initial_predicates13c(a)
            if a[0]==0 and pred['pointCount']:
                for name,row in assignments.items():
                    if row['port'] is None:continue
                    row['reached_calls']+=1
                    if len(row['examples'])<8:row['examples'].append({'id':case.id,'seq':seq,'words_H':[f'{pred['manifold_H'][slot]:08x}' for slot in row['M30_slots']]})
            gjk+=bool(pred.get('GJK_reached'))
            for key,word in pred['values_H'].items():
                if key not in sites:continue
                                                                        
                                                                           
                                                     
                if a[0]==0 and key=='u' and 'circle/u<=0' not in pred['reached']:continue
                value=m.number(int(word,16));threshold=sites[key][2]
                relation='below' if value<threshold else 'above' if value>threshold else 'equal'
                reached.add(key+'/'+relation);counts[key][relation]+=1
                if len(result[key][relation])<8:result[key][relation].append({'id':case.id,'seq':seq,'value_H':word})
        percase.append({'id':case.id,'reached_predicate_relations':sorted(reached),'checked_refusals':refused,
                        'GJK_reached_calls':gjk,'post_GJK_features_verified':False})
    for key,row in result.items():row['reached_counts']=counts[key]
    return {'arithmetic':'Every add/sub/mul/div/sqrt is rounded to binary32 in the model; C remains the bitwise oracle',
            'sites':result,'circle_result_assignments':assignments,'cases':percase,'unverified':'C4/C6-C11 post-GJK feature decisions, remaining assignments, native removals and exact class reconciliation remain open'}


def equivalence_proofs13c(product_root=None,baseline=None):
    root=Path(product_root) if product_root is not None else HERE.parents[1]
    baseline=baseline or {};healthy=(baseline.get('native_source_verified') is True and baseline.get('word_comparison_ok') is True and baseline.get('global_END_checked') is True
        and baseline.get('N')==432 and baseline.get('positive_steps')==32400 and
        baseline.get('process_codes') and all(v==0 for v in baseline['process_codes'].values()) and
        baseline.get('stderr_bytes') and not any(baseline['stderr_bytes'].values()))
    explanations={
        'EQ13C-ROT-FINITE':('Nie-finite c/s gives NaN/+Inf in qq=f32(s*s+c*c), rejected by BOTH preserved strict norm bounds. Direct xfA and xfB call the same validTransform.',
                           ['transform.q.s * transform.q.s + transform.q.c * transform.q.c','1.0f32 - 0.0006f32 < qq','qq < 1.0f32 + 0.0006f32']),
        'EQ13C-DIST-INTERMEDIATE':('With preserved finite(d2) of EVERY pair, any nonfinite dx/dy/xx/yy propagates to NaN/+Inf in d2=f32(dx*dx+dy*dy); finite(d2) rejects it.',
                                 ['let dx: f32 = b.x-a.x','let xx: f32 = dx*dx','let d2: f32 = xx+yy','not finite(d2)']),
        'EQ13C-TERRAIN-POINT':('N>=4 and EVERY pair finite(d2) includes every endpoint/ghost with another point; NaN/Inf point cannot survive. This is confined to terrain geometry, not arbitrary proxy/circle finite checks.',
                             ['n < 4i64','while (pi < n)','while (pj < n)','not finite(d2)']),
        'EQ13C-ORIENTATION':('Given all three rounded pair distances finite, each side has norm<=sqrt(FLT_MAX) with binary32 rounding margin. Product bound ((2+sqrt(3))/4)L²<.934L² and determinant bound sqrt(3)/2 L²<.867L² leave >.06 FLT_MAX margin; rounding error<1e-5 FLT_MAX. Differences/products/determinant stay finite. Requires unchanged all-pair finite(d2), not its removal.',
                            ['let dx: f32 = b.x-a.x','let first: f32 = dx*cy','let second: f32 = dy*cx','result = first-second']),
        'EQ13C-CAPSULE-ENDPOINT':('With finite(lengthSquared) preserved, nonfinite capsule endpoint yields nonfinite difference/square/checksum and is rejected. Count2 and strict lengthSquared>FLT_EPSILON remain independent guards.',
                                ['finiteVector(points[pi])','let delta: Vec2 = b2Sub(points[1],points[0])','not finite(lengthSquared)','lengthSquared <= FLT_EPSILON']),
        'EQ13C-CHAIN-RAW-VALIDITY':('Live world, matching owner, unsigned slot range, occupied record.id==slot and matching birth are preserved. b2MakeChainId uses CURRENT generation, so terminal b2Chain_IsValid follows. This does not excuse occupied/birth or extend Q-RANGEbody to chain.',
                                  ['worldStatus(owner)','number.ownerTicket','number.slot as u32','world.chainShapes.at(number.slot as i64).id != number.slot','number.birthTicket','raw.b2Chain_IsValid(raw.b2MakeChainId(world, number.slot))'])}
    result=[]
    for row in accounting_spec13c()['rows']:
        if row['type']!='equivalence_proof':continue
        path=row['port'].rsplit(':',1)[0];file=root/path;text=file.read_text(encoding='utf-8') if file.is_file() else ''
        proof,needles=explanations[row['id']]
        conditions=all(needle in text for needle in needles)
        if row['id'] in ('EQ13C-ORIENTATION','EQ13C-TERRAIN-POINT','EQ13C-DIST-INTERMEDIATE'):
            conditions=conditions and 'not finite(d2)' in text and 'while (pj < n)' in text
        result.append({'id':row['id'],'proof':proof,'port':row['port'],'citation':'KONTRAKT-13/1 §11.1',
            'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None,
            'conditions_present':conditions,'native_baseline_verified':bool(healthy),'counted_as_kill':False})
    return result


def table13c(receipts=(),controls=(),observations=(),*,product_root=None,equivalences=()):
    spec=accounting_spec13c();root=Path(product_root) if product_root is not None else HERE.parents[1]
    actual={path:hashlib.sha256((root/path).read_bytes()).hexdigest() if (root/path).is_file() else None for path in spec['source_sha256']}
    source_matches=actual==spec['source_sha256']
    by_id={r['id']:r for r in spec['rows']};proofs={};control_map={r['id']:r for r in controls}
    m.require(len(control_map)==len(controls),'13c duplicate control receipts')
    proof_map={r['id']:r for r in equivalences};m.require(len(proof_map)==len(equivalences),'13c duplicate equivalence proofs')
    receipts=list(receipts);keys=[r['id'] for r in receipts];m.require(len(keys)==len(set(keys)),'13c duplicate native receipts')
    rejected=[]
    for receipt in receipts:
        target=receipt.get('requirement');row=by_id.get(target)
        valid=bool(row) and row['type']=='native_target' and source_matches
        valid=valid and all(receipt.get(k) is True for k in ('native_executed','baseline_ok','single_hit','clean','definedness_verified','detected'))
        valid=valid and receipt.get('anchor_owner')=='T-13c-2a'
        valid=valid and receipt.get('source_sha256')==row.get('source_sha256') if row else False
        valid=valid and receipt.get('port')==row.get('port') and receipt.get('changed_atom')==row.get('atom') if row else False
        difference=receipt.get('difference') or {}
        valid=valid and difference.get('baseline') is not None and difference.get('actual') is not None and difference.get('baseline')!=difference.get('actual')
        run=receipt.get('run',{});build=receipt.get('build',{})
        valid=valid and build.get('code')==0 and run.get('code')==0 and run.get('stderr_bytes')==0 and run.get('stdout_bytes',0)>0
        valid=valid and bool(receipt.get('input_sha256')) and bool(receipt.get('mutant_sha256')) and bool(receipt.get('witness'))
        if valid:proofs.setdefault(target,[]).append(receipt)
        else:rejected.append({'id':receipt['id'],'requirement':target,'reason':'Missing/stale/unclean native proof or wrong exact operand/owner'})
    resolved={}
    def resolve(ident,trail=()):
        m.require(ident not in trail,'cyclic13c accounting references')
        if ident in resolved:return resolved[ident]
        row=by_id[ident];kind=row['type'];refs=[];verified=False
        if kind=='native_target':
            refs=[{'receipt':r['id'],'witness':r['witness'],'difference':r['difference']} for r in proofs.get(ident,[])]
            verified=bool(refs)
        elif kind=='control_trial':
            control=control_map.get(ident,{});verified=source_matches and control.get('ok') is True and control.get('control_only') is True
            verified=verified and all(control.get('sides',{}).get(s,{}).get('ok') is True and
                control['sides'][s].get('model',{}).get('END_EOF') is True for s in ('C','D'))
            if verified:refs=[{'control':ident,'counted_as_kill':False}]
        elif kind=='equivalence_proof':
                                                                               
            proof=proof_map.get(ident,{})
            verified=source_matches and proof.get('conditions_present') is True and proof.get('native_baseline_verified') is True and bool(proof.get('proof'))
            verified=verified and proof.get('source_sha256')==row.get('source_sha256') and proof.get('counted_as_kill') is False
            if verified:refs=[{'proof':ident,'counted_as_kill':False}]
        else:
            states=[resolve(x,trail+(ident,)) for x in row['components']]
            verified=all(x['verified'] for x in states) and not row.get('unresolved_mapping',False)
            refs=[{'component':x,'verified':s['verified']} for x,s in zip(row['components'],states)]
        state={**row,'accounting_type':kind,'verified':bool(verified),'evidence_refs':refs,
               'counted_as_kill':kind=='native_target' and bool(verified),
               'status':('VERIFIED_' if verified else 'GAP_')+kind.upper()}
        resolved[ident]=state;return state
    rows=[resolve(r['id']) for r in spec['rows']]
    obs={r['id']:r for r in observations};m.require(len(obs)==len(observations),'duplicate13c percase observations')
    manifest=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    reachability=[]
    for r in manifest['przypadki']:
        if r['profil']!='PORT13C':continue
        evidence=obs.get(r['id'],{});valid=all(evidence.get(k) is True for k in ('native_processes_ok','END_EOF','independent_model_checked'))
        reachability.append({'id':r['id'],'family':r['rodzina'],'mutation_classes':r['swiadczyKlasyMutacji'],
            'functions_and_observations':'Direct pair→M30/KI7/K7/DC' if r['id']<=384 else 'CreateChain→Step→primary→Update→GJK→solver/sleep→events/copies',
            'status':'UNVERIFIED','native_path_observed':valid,
            'evidence':evidence,'all_requested_branches_verified':False})
    gaps=[r['id'] for r in rows if not r['verified']]
    return {'rows':rows,'required':len(rows),'verified':sum(r['verified'] for r in rows),'gaps':gaps,
        'accounting_types':dict(__import__('collections').Counter(r['type'] for r in rows)),
        'native_target_rows':sum(r['type']=='native_target' for r in rows),
        'independent_native_count':None,'count_reconciliation':'Exact operand/field sharing, C lines and manifest-class mappings remain gaps; row count is not an independent mutant count',
        'remaining_native_targets':[r['id'] for r in rows if r['type']=='native_target' and not r['verified']],
        'unresolved_class_mappings':[r['mutation_class'] for r in rows if r.get('unresolved_mapping')],
        'source_matches':source_matches,'source_expected':spec['source_sha256'],'source_actual':actual,
        'denominator_independent_of_git':True,'matrix_complete_after_final_K':not gaps and source_matches,
        'reachability':reachability,'rejected_receipts':rejected,'full_ownership_ready':False,
        'inherited_debts':['BASE12 full_ownership_ready=False','13a Q20/four headers/remaining mutations','13b remaining targets/survivors'],
        'code':int(bool(gaps) or not source_matches)}


def mutation_proposals13b(root=None):
    pass                                                                   

                                                                          
                                                                              
                                                                           
       
    root=Path(root) if root else HERE.parents[1]
    specs=[
        ('spacing-bound','validateChainGeometry','d2 <= B2_LINEAR_SLOP*B2_LINEAR_SLOP','false',['GB4-DISTANCE','GB4-SLOP']),
        ('distance-sum-finite','validateChainGeometry',' or not finite(d2)','',['GB4-DERIVED-D2']),
        ('point-minimum','validateChainGeometry','n < 4i64','false',['GB3-N3']),
        ('material-count','validateChainDescription','count != 1i64 and count != n','false',['GB3-MCOUNT']),
        ('onSegment-closed-x-low','chainOnSegment','p.x >= poly.b2MinFloat(a.x,b.x)','p.x > poly.b2MinFloat(a.x,b.x)',['GB5-COLLINEAR','GB5-TOUCH']),
        ('onSegment-closed-x-high','chainOnSegment','p.x <= tree.b2MaxFloat(a.x,b.x)','p.x < tree.b2MaxFloat(a.x,b.x)',['GB5-COLLINEAR','GB5-TOUCH']),
        ('onSegment-closed-y-low','chainOnSegment','p.y >= poly.b2MinFloat(a.y,b.y)','p.y > poly.b2MinFloat(a.y,b.y)',['GB5-COLLINEAR','GB5-TOUCH']),
        ('onSegment-closed-y-high','chainOnSegment','p.y <= tree.b2MaxFloat(a.y,b.y)','p.y < tree.b2MaxFloat(a.y,b.y)',['GB5-COLLINEAR','GB5-TOUCH']),
        ('shared-onSegment-enabled','chainOnSegment','orientation == 0.0f32 and','false and',['GB5-COLLINEAR','GB5-TOUCH']),
        ('static-create','chainCreatePreflight','.bodyType != 0i32', '.bodyType == -99i32',['GB6-CREATE-DYNAMIC','GB6-CREATE-KINEMATIC']),
        ('chain-range','chainStatus','(number.slot as u32) >= (world.chainIdPool.nextIndex as u32)','false',['GB1-RANGE']),
        ('chain-occupied','chainStatus','world.chainShapes.at(number.slot as i64).id != number.slot','false',['GB1-OCCUPIED']),
        ('chain-owner','chainStatus','not equalKey(owner.birthTicket, number.ownerTicket)','false',['GB1-OWNER-LOW','GB1-OWNER-HIGH']),
        ('chain-birth','chainStatus','not equalKey(world.chainShapes.at(number.slot as i64).birthTicket, number.birthTicket)','false',['GB1-BIRTH-LOW','GB1-BIRTH-HIGH']),
        ('setter-nonnegative','chainSetPreflight','kind != 2i32 and not validNonnegative(value)','false',
            ['GB3-SET-FRICTION-FINITE','GB3-SET-FRICTION-SIGN','GB3-SET-RESTITUTION-FINITE','GB3-SET-RESTITUTION-SIGN']),
        ('shared-scalar-finite','validNonnegative','finite(value)','true',
            ['GB3-SET-FRICTION-FINITE','GB3-SET-RESTITUTION-FINITE','GB3-MAT-FRICTION-FINITE','GB3-MAT-RESTITUTION-FINITE','GB3-MAT-ROLLING-FINITE']),
        ('shared-scalar-sign','validNonnegative','value >= 0.0f32','true',
            ['GB3-SET-FRICTION-SIGN','GB3-SET-RESTITUTION-SIGN','GB3-MAT-FRICTION-SIGN','GB3-MAT-RESTITUTION-SIGN','GB3-MAT-ROLLING-SIGN']),
        ('material-friction-route','validSurfaceMaterial','validNonnegative(value.friction)','true',
            ['GB3-MAT-FRICTION-FINITE','GB3-MAT-FRICTION-SIGN']),
        ('material-restitution-route','validSurfaceMaterial','validNonnegative(value.restitution)','true',
            ['GB3-MAT-RESTITUTION-FINITE','GB3-MAT-RESTITUTION-SIGN']),
        ('material-rolling-route','validSurfaceMaterial','validNonnegative(value.rollingResistance)','true',
            ['GB3-MAT-ROLLING-FINITE','GB3-MAT-ROLLING-SIGN']),
        ('material-tangent-route','validSurfaceMaterial','finite(value.tangentSpeed)','true',['GB3-MAT-TANGENT-FINITE']),
        ('chain-lock','chainMutationStatus','raw.worlds.at(owner.slot as i64).locked','false',
            ['GB2-ROUTE-101','GB2-ROUTE-103-0','GB2-ROUTE-103-1','GB2-ROUTE-103-2']),
        ('child-shared-preflight','chainChildStatus','raw.worlds.at(owner.slot as i64).shapes.at(number.slot as i64).shapeType == 4i32','false',
            ['GB6-CHILD-DESTROY','GB6-CHILD-DENSITY','GB6-CHILD-FRICTION']),
        ('whole-batch','chainTicketReservation','i < 1i32 + segments','i < segments',['GB7-PARTIAL']),
        ('loop-main-ghost1','b2CreateChain','ChainSegment(def.points.at(previous as i64), Segment',
            'ChainSegment(def.points.at(i as i64), Segment',list(range(1,9))),
        ('loop-tail-ghost2','b2CreateChain','def.points.at(0i64), chainSlot);',
            'def.points.at(1i64), chainSlot);',list(range(1,9))),
        ('open-ghost1','b2CreateChain','ChainSegment(def.points.at(j as i64), Segment',
            'ChainSegment(def.points.at((j+1i32) as i64), Segment',list(range(9,17))),
        ('generation-increment','b2CreateChain','.generation + 1u16','.generation + 0u16',[64]),
    ]
    for setter,field in (('Friction','friction'),('Restitution','restitution'),('Material','userMaterialId')):
        for variable,bound,label in (('i','materialCount','materials'),('j','count','shapes')):
            before=variable+' < world.chainShapes.at(slot).'+bound
            specs.append(('raw-'+setter.lower()+'-'+label,'b2Chain_Set'+setter,before,before+' - 1i32',list(range(33,41))))
        before='worlds.at(id.world0 as i64).chainShapes.at((id.index1-1i32) as i64).materials.at(0i64).'+field
        specs.append(('raw-'+setter.lower()+'-getter0','b2Chain_Get'+setter,before,
                      '0i32' if setter=='Material' else '0.0f32',list(range(33,41))))
    contents={name:(root/'silnik/fizyka'/name).read_text(encoding='utf-8') for name in ('gra.dk','swiat.dk')}
    inventory=product_sites13b(root)['rows']
    result=[]
    for ident,function,before,after,guards in specs:
        filename='swiat.dk' if function.startswith('b2') else 'gra.dk'
        content=contents[filename];sha=hashlib.sha256((root/'silnik/fizyka'/filename).read_bytes()).hexdigest()
        match=re.search(r'^fun '+re.escape(function)+r'\([^\n]*(?:\n(?!fun ).*)*',content,re.M)
        body=match.group() if match else ''
        hits=body.count(before)
        position=match.start()+body.find(before) if hits==1 else -1
        line=content.count('\n',0,position)+1 if position>=0 else None
        column=position-content.rfind('\n',0,position)-1 if position>=0 else None
        sites=[r for r in inventory if r['function']==function and r['port']=='silnik/fizyka/'+filename+':'+str(line)]
        atomic=[r for r in sites if r.get('source_column') is not None and column<=r['source_column']<column+len(before)] if column is not None else []
        site=(atomic[0] if atomic else sites[0]) if sites else None
        result.append({'id':'13b/'+ident,'file':'silnik/fizyka/'+filename,'function':function,
            'before':before,'after':after,'function_hits':hits,'source_sha256':sha,
            'line':line,'requirement':site['id'] if site else None,
            'candidate_guards':[v for v in guards if isinstance(v,str)],
            'candidate_cases':[v for v in guards if isinstance(v,int)],
            'candidate_fixture':'generation-wrap' if ident=='generation-increment' else None,
            'binding_owner':'T-13b-2a','anchor_refreshed':False,
            'ready_for_binding':hits==1,'native_executed':False,
            'safety':('Read-only helper/preflight; no raw invocation after mutant helper acceptance' if any(isinstance(v,str) for v in guards)
                      else 'Frozen PUBLIC prefix or explicit metadata fixture; bounded indices, shorter setter loops/scalar getters, no positive Step; clean native END/EOF required')})
    return result


def equivalence_proofs13b(root=None):
    pass                                                              
    root=Path(root) if root else HERE.parents[1]
    source=root/'silnik/fizyka/gra.dk';content=source.read_text(encoding='utf-8')
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    def body(name):
        match=re.search(r'^fun '+re.escape(name)+r'\([^\n]*(?:\n(?!fun ).*)*',content,re.M)
        return match.group() if match else ''
    geometry=body('validateChainGeometry');status=body('chainStatus')
    rows=[]
    for ident,function,checks,proof in (
        ('point-finite','validateChainGeometry',('while (pi < n)','pj: i64 = pi+1i64','not finite(d2)'),
         'N>=4 and every unordered pair is tested. A nonfinite coordinate necessarily makes a rounded difference/square/checksum nonfinite in a pair containing that point. Removing only point finite cannot accept it while finite(d2) remains.'),
        ('distance-components-finite','validateChainGeometry',('let xx: f32 = dx*dx','let yy: f32 = dy*dy','let d2: f32 = xx+yy','not finite(d2)'),
         'Rounded squares are nonnegative or NaN/+Inf. A nonfinite dx,dy,xx or yy cannot produce a finite checksum of these squares. Keep the single finite(d2) guard and all other predicates.'),
        ('orientation-finite','validateChainGeometry',('while (pi < n)','not finite(d2)','chainOrientation(a1,a2,b1'),
         'All three squared pair distances of each orientation triangle are finite first. Section11.1 bounds the determinant by sqrt(3)/2*FLT_MAX, with a margin exceeding binary32 rounding error; intermediate differences/products are likewise bounded. This does not justify removing distance-checksum finite.'),
        ('chain-raw-validity-current-generation','chainStatus',('worldStatus(owner)','owner.birthTicket, number.ownerTicket',
            '(number.slot as u32) >= (world.chainIdPool.nextIndex as u32)',
            '.id != number.slot','.birthTicket, number.birthTicket',
            'raw.b2Chain_IsValid(raw.b2MakeChainId(world, number.slot))'),
         'Earlier world/range/occupied/birth checks hold. MakeChainId reads CURRENT record generation; IsValid immediately compares that same generation to the same occupied record. Saved generation is never substituted. This proof does not waive the unsigned chain range check or any public route.'),
    ):
        text=geometry if function=='validateChainGeometry' else status
        applicable=all(check in text for check in checks)
        offset=content[:content.find(text)].count('\n') if text else 0
        lines=[offset+i for i,line in enumerate(text.splitlines(),1) if any(check in line for check in checks)]
        rows.append({'id':ident,'function':function,'source':'silnik/fizyka/gra.dk','source_sha256':sha,
            'source_lines':lines,'conditions_present':applicable,'proof':proof,
            'native_baseline_verified':False,'counted_as_kill':False,
            'status':'PROOF_PINNED_NEEDS_FINAL_K_BASELINE' if applicable else 'GAP_CHANGED_PRECONDITIONS'})
    return rows


if __name__ == '__main__':
    print(json.dumps(proposals() if '--proposals' in sys.argv else table(), ensure_ascii=False, indent=2))
    sys.exit(0 if '--proposals' in sys.argv else 1)
