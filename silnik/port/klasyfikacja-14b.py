pass                                                                     

                                                                              
                                                                            
   
import argparse
from collections import Counter
import gzip
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile


@lru_cache(maxsize=None)
def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def canonical(path):
    for anchor in ('/include/box2d/', '/src/'):
        if anchor in path:
            return path[path.rindex(anchor)+1:]
    return None


def records(data):
    for file in data['files']:
        name = canonical(file['file'])
        if name is None:
            continue
        for line in file['lines']:
            function = line.get('function_name', '<unknown>')
            number = line['line_number']
            yield (name, function, number, 'line'), line['count']
            for i, branch in enumerate(line.get('branches', [])):
                yield (name, function, number, 'edge'+str(i)), branch['count']


def counters(directory):
    result = Counter()
    witnesses = {}
                                                                                 
    for p in sorted(directory.rglob('*.gcov.json.gz')):
        if 'CMakeFiles' not in p.parts:
            continue
        data = json.load(gzip.open(p, 'rt'))
        for key, count in records(data):
            result[key] += count
            witnesses.setdefault(key, []).append({'path': str(p), 'rawSHA': sha(p), 'count': count})
    return result, witnesses


def historical(directory, wanted, source):
    result = {}
    source_identity = json.loads((directory/'original-pins.json').read_text())['pins']
    matching = {f for f, _, _, _ in wanted if f in source_identity and (source/f).is_file() and sha(source/f) == source_identity[f]}
                                                                      
    candidates = sorted(directory.glob('gcov-*/*/**/*.gcov.json.gz'))
    candidates += sorted(directory.glob('P2/*gcov/**/*.gcov.json.gz'))
    for p in candidates:
        try:
            data = json.load(gzip.open(p, 'rt'))
        except (OSError, ValueError):
            continue
        for key, count in records(data):
            if count > 0 and key in wanted and key[0] in matching and key not in result:
                result[key] = {'path': str(p), 'rawSHA': sha(p), 'count': count, 'sourceSHA': source_identity[key[0]]}
    for p in sorted((directory/'P3').glob('*gcov.zip')):
        with zipfile.ZipFile(p) as z:
            for member in z.namelist():
                if not member.endswith('.gcov.json.gz'):
                    continue
                raw = z.read(member)
                for key, count in records(json.loads(gzip.decompress(raw))):
                    if count > 0 and key in wanted and key[0] in matching and key not in result:
                        result[key] = {'archive': str(p), 'archiveSHA': sha(p), 'entry': member,
                                       'rawSHA': hashlib.sha256(raw).hexdigest(), 'count': count, 'sourceSHA': source_identity[key[0]]}
    return result, matching


def port_map(repo):
    result = {}
    for p in (repo/'silnik/fizyka').glob('*.dk'):
        for number, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            match = re.search(r'\bfun\s+(b2\w+)\s*\(', line)
            if match:
                result.setdefault(match[1], []).append(p.relative_to(repo).as_posix()+':'+str(number))
    return result


def renamed(function):
    if function.startswith('port11Original'):
        return 'b2'+function.removeprefix('port11Original')
    for prefix, typ in [('R', 'Revolute'), ('P', 'Prismatic'), ('', 'Distance')]:
        for suffix, phase in [('Prepare', 'Prepare'), ('Warm', 'WarmStart'), ('Solve', 'Solve')]:
            if function == 'port14Original'+prefix+suffix:
                return 'b2'+phase+typ+'Joint'
    return function


def scope(file, function, number, source):
    if file == 'src/revolute_joint.c':
        return 'main' if number <= 465 else 'later-draw19'
    if file == 'src/prismatic_joint.c':
        return 'main' if number <= 608 else 'later-draw19'
    if file == 'src/joint.c':
        if number >= 1523:
            return 'later-draw19'
        if re.search(r'(Motor|Mouse|Filter|Weld|Wheel|Explosion)', function):
            return 'later-typed'
                                                                    
        text = source[file]
        if 887 <= number <= 1470:
            label = None
            for line in text[:number]:
                m = re.search(r'case\s+(b2_\w+Joint)\s*:', line)
                if m:
                    label = m[1]
                elif re.match(r'\s*(?:default\s*:|(?:void|float|b2Vec2)\s+b2\w+\s*\()', line):
                    label = None
            if label in ('b2_motorJoint', 'b2_mouseJoint', 'b2_filterJoint', 'b2_weldJoint', 'b2_wheelJoint'):
                return 'later-typed'
        return 'common14a' if number < 507 or 702 <= number < 887 or 979 <= number <= 1060 or number >= 1472 else 'main'
    if file in ('src/constraint_graph.c', 'src/island.c', 'src/solver_set.c'):
        joint_functions = ('Joint', 'Island', 'SolverSet')
        return 'credit14a' if any(x in function for x in joint_functions) else None
    if file in ('include/box2d/math_functions.h', 'src/math_functions.c'):
        if function == 'b2InvTransformPoint' and function not in MATH_USED:
            return 'later-typed'
        return 'math' if function in MATH_USED else None
    if file.endswith('.h') and (file, function) in HEADER_USED:
        return 'inline-credit14a'
    return None


SWITCH_LATER = {895: (2,), 920: (2,), 945: (1,), 966: (1,),
                1067: (1, 2, 3, 6, 7), 1105: (0, 1, 4, 5),
                1150: (1, 4, 5), 1267: (3,),
                1354: (1, 2, 5, 6, 7), 1394: (1, 2, 5, 6, 7), 1434: (1, 2, 5, 6, 7)}


def main(args):
    global MATH_USED, HEADER_USED
    repo, source, evidence = args.repo, args.source, args.evidence
    source_lines = {p: (source/p).read_text().splitlines() for p in
                    ('src/joint.c', 'src/revolute_joint.c', 'src/prismatic_joint.c', 'include/box2d/math_functions.h')}
    shared_lines = [line for n, line in enumerate(source_lines['src/joint.c'][:1522], 1)
                    if not (33 <= n <= 58 or 76 <= n <= 99 or 406 <= n <= 505 or 609 <= n <= 700)]
    initial = source_lines['src/revolute_joint.c'][:465]+source_lines['src/prismatic_joint.c'][:608]+shared_lines
    used = set(re.findall(r'\b(b2\w+)\s*\(', '\n'.join(line for line in initial if 'B2_ASSERT' not in line)))
    header = '\n'.join(source_lines['include/box2d/math_functions.h'])
    changed = True
    while changed:
        changed = False
        for name in list(used):
            match = re.search(r'\b'+name+r'\s*\([^;{}]*\)\s*\{', header)
            if not match:
                continue
            depth, end = 1, match.end()
            while depth and end < len(header):
                depth += (header[end] == '{')-(header[end] == '}')
                end += 1
            children = set(re.findall(r'\b(b2\w+)\s*\(', header[match.end():end]))
            if children-used:
                used |= children
                changed = True
    MATH_USED = used
    HEADER_USED = set()
    for unit in ('joint.c', 'revolute_joint.c', 'prismatic_joint.c'):
        for path in (evidence/'gcov-before').rglob(unit+'.gcov.json.gz'):
            if 'CMakeFiles' not in path.parts:
                continue
            for file in json.load(gzip.open(path, 'rt'))['files']:
                name = canonical(file['file'])
                if name and name.endswith('.h') and name != 'include/box2d/math_functions.h':
                    HEADER_USED |= {(name, r['function_name']) for r in file['lines'] if 'function_name' in r}
    before, before_raw = counters(evidence/'gcov-before')
    after, after_raw = counters(evidence/'gcov-after')
    supplement_path = evidence/'14b-nowe-sytuacje-uzupelnienie.json'
    supplements = json.loads(supplement_path.read_text())['cases'] if supplement_path.exists() else []
    supplement_counts = {}
    for trial in supplements:
        counts, _ = counters(evidence/('gcov-'+trial['key']))
        supplement_counts[trial['key']] = counts
        after += counts
    assert before and after
    wanted = {k for k in before if not before[k] and scope(k[0], k[1], k[2], source_lines)}
    previous_map = evidence/'14b-pokrycie.json'
    if previous_map.exists():
        prior = json.loads(previous_map.read_text())
        old = {(r['file'], r['function'], r['line'], r['kind']): r['historical'] for r in prior['rows'] if 'historical' in r}
        matching = set(prior['summary']['historicalMatchingSourceFiles'])
        assert all(sha(source/k[0]) == v['sourceSHA'] for k, v in old.items())
    else:
        old, matching = historical(args.historical, wanted, source)
    a_counts, a_raw = counters(evidence/'gcov-A') if (evidence/'gcov-A').exists() else (Counter(), {})
    a_cd = (evidence/'regression-A-D.json').exists()
    prior_counts, prior_raw = counters(evidence/'gcov-A-prior') if (evidence/'gcov-A-prior').exists() else (Counter(), {})
    prior_cd = (evidence/'prior-D.json').exists()
    prior_witnesses = {}
    previous_prior = a_counts
    if (evidence/'prior-C.json').exists():
        for trial in json.loads((evidence/'prior-C.json').read_text()):
            current, raw = counters(evidence/('gcov-prior-'+trial['key']))
            for key in current:
                if current[key] > previous_prior[key] and key not in prior_witnesses:
                    prior_witnesses[key] = {'case': trial['key'], 'count': current[key]-previous_prior[key],
                                            'raw': raw[key], 'inputSHA': trial['result']['inputSHA']['left']}
            previous_prior = current
    legacy_rows = json.loads((args.historical/'P3/classification/gaps.json').read_text())
    legacy = {(r['file'], r['function'], r['line'], r['kind']): r for r in legacy_rows}
    ports = port_map(repo)
    aliases = {'b2CreateJoint': 'b2CreateJoint', 'b2PrepareJoint': 'b2JointPhase14',
               'b2WarmStartJoint': 'b2JointPhase14', 'b2SolveJoint': 'b2JointPhase14',
               'b2PrepareOverflowJoints': 'b2JointPhase14', 'b2WarmStartOverflowJoints': 'b2JointPhase14', 'b2SolveOverflowJoints': 'b2JointPhase14',
               'b2AssignJointColor': 'b2AddJointToGraph', 'b2CreateJointInGraph': 'b2AddJointToGraph',
               'b2GetPrismaticJointForce': 'b2Joint_GetConstraintForce', 'b2GetRevoluteJointForce': 'b2Joint_GetConstraintForce',
               'b2GetPrismaticJointTorque': 'b2Joint_GetConstraintTorque', 'b2GetRevoluteJointTorque': 'b2Joint_GetConstraintTorque',
               'b2SplitIslandTask': 'b2SplitIsland', 'b2MaxInt': 'b2CreateJoint',
               'b2IntArray_Push': 'b2FreeId', 'b2BodyArray_Get': 'b2CreateJoint', 'b2BodySimArray_Get': 'b2GetBodySim',
               'b2ContactArray_Get': 'b2DestroyContactsBetweenBodies', 'b2ShapeArray_Get': 'b2Joint_SetCollideConnected',
               'b2SolverSetArray_Get': 'b2GetSolverSet', 'b2JointArray_Get': 'b2GetJointFullId',
               'b2JointSimArray_Get': 'b2GetJointSim', 'b2JointArray_Push': 'b2CreateJoint',
               'b2JointSimArray_Add': 'b2AppendJointToSet', 'b2JointSimArray_RemoveSwap': 'b2RemoveJointFromSet',
               'b2ValidateIsland': 'b2MergeIsland'}
    manifest = json.loads((evidence/'14b-nowe-sytuacje.json').read_text())
    deltas = {}
    previous = before
    for case in manifest['cases']:
        current, _ = counters(evidence/('gcov-'+case['key']))
        deltas[case['key']] = {k: current[k]-previous[k] for k in current if current[k] > previous[k]}
        previous = current
    deltas.update(supplement_counts)
    cd_path = evidence/'new-C-D.json'
    cd_ok = set(r['key'] for r in json.loads(cd_path.read_text()) if r['frozenCEqualsEveryByteD']) if cd_path.exists() else set()
    supplement_cd = evidence/'supplement-C-D.json'
    if supplement_cd.exists():
        cd_ok |= {r['key'] for r in json.loads(supplement_cd.read_text()) if r['frozenCEqualsEveryByteD']}
    rows = []
    for key in sorted(before):
        file, function, number, kind = key
        area = scope(file, function, number, source_lines)
        if area is None:
            continue
        if file == 'src/joint.c' and kind.startswith('edge') and int(kind[4:]) in SWITCH_LATER.get(number, ()):
            area = 'later-typed'
        name = renamed(function)
        mapped_name = aliases.get(name, name)
        mechanism = 'named function' if name == mapped_name else 'integrated helper or observer rename, source call checked'
        if re.match(r'b2(?:Joint|JointSim|Island|IslandSim|SolverSet)Array_(?:Create|Reserve|Destroy)', name):
            if name.startswith('b2JointSim'):
                mapped_name = 'b2TrySleepIsland' if name.endswith('Create') else 'b2AppendJointToSet'
            elif name.startswith('b2Island'):
                mapped_name = 'b2CreateIsland' if not name.endswith('Destroy') else 'b2DestroyIsland'
            else:
                mapped_name = 'b2CreateWorld' if not name.endswith('Destroy') else 'b2DestroyWorld'
            mechanism = 'C allocation helper maps to owned List storage at the named D caller; no standalone C-style allocation API required'
        if name == 'b2ValidateIsland':
            mechanism = 'B2_VALIDATE=0 inline no-op; named D caller retains the actual island operation'
        row = {'file': file, 'sourceSHA': sha(source/file), 'function': function, 'line': number, 'kind': kind,
               'scope': area, 'before': before[key], 'after': after[key], 'port': ports.get(mapped_name, []), 'portMechanism': mechanism,
               'newWitnesses': [{'case': c, 'count': d[key], 'C_D': c in cd_ok} for c, d in deltas.items() if key in d]}
        if before[key] > 0:
            row.update(classification='HIT', reason='Own full PUBLIC96/DIRECT128/GUARD221 union', closed=True)
        elif area.startswith('later'):
            row.update(classification='LATER', reason='Explicit later scope ODBIOR-14B §1/7 and K14b §2, kept in full source inventory', closed=True)
        elif a_counts[key] > 0:
            row.update(classification='P', reason='Own full existing A96/D128/G156 regression on exactly the same current Bfix source SHA, byte-neutral gcov; full C/D receipt regression-A-D.json',
                       historical={'sourceSHA': sha(source/file), 'raw': a_raw[key], 'count': a_counts[key],
                                   'C_D': 'regression-A-D.json', 'neutrality': 'regression-A-C.json'}, closed=a_cd)
        elif prior_counts[key] > 0:
            row.update(classification='P', reason='Own rerun of accepted older tape on exact current Bfix source SHA, C before D and byte-neutral gcov; prior-D.json compares every byte',
                       historical={'sourceSHA': sha(source/file), 'raw': prior_raw[key], 'count': prior_counts[key],
                                   'witness': prior_witnesses.get(key), 'C_D': 'prior-D.json', 'neutrality': 'prior-C.json'}, closed=prior_cd)
        elif key in old:
            row.update(classification='P', reason='Positive raw counter and identical C/H source SHA; retained C/D receipts.', historical=old[key],
                       historicalClassification=legacy.get(key), closed=True)
        elif key in legacy and legacy[key]['class'] == 'S' and file in matching:
            row.update(classification='S', reason=legacy[key]['evidence'], historicalClassification=legacy[key], closed=True)
        elif after[key] > 0:
            row.update(classification='N', reason='New literal C frozen before D; positive per-case gcov counter', closed=any(w['C_D'] for w in row['newWitnesses']))
        elif function.endswith(('_Create', '_Reserve')) and re.match(r'b2(?:Joint|JointSim|Island|IslandSim|SolverSet)Array_', function):
            row.update(classification='S', reason='14b-domeny-S.json scans all native C and runtime callsites: Create uses positive constant capacities only; IslandSimArray_Create has no caller. Reserve is reached only by Add/Push with strictly larger capacity; no Resize or standalone Reserve caller exists for these array types in this profile. Internal macro helpers are not public 14b input entrypoints.', closed=True)
        elif function in ('b2IntArray_Push', 'b2JointArray_Push') and kind == 'edge3':
            row.update(classification='S', reason='Small-capacity growth arm is outside the reachable container state: joint array starts at16 (world.c:169); int arrays start at32 in id_pool.c:9 or16 in broad_phase.c:38. Capacity only grows. No public Resize/Reserve can reduce it. All compiled callers retained in 14b-domeny-S.json.', closed=True)
        elif file == 'src/solver_set.c' and number in (253, 256):
            row.update(classification='S', reason='14b-domeny-S.json disabledContactInvariant: a contact between two island bodies can transfer to disabled only on its second endpoint visit; a contact to a body outside this island is visited once. Awake bodies have no initially disabled contacts because WakeSolverSet restores them. Thus the already-disabled path cannot occur in a valid graph. Public raw-state seeding is unavailable, existing parser INPUT_PROFILE refusal retained.', closed=True)
        elif file == 'src/island.c' and number in (610, 616):
            row.update(classification='S', reason='Split callsite invariant: Body_SetAwake calls only awake islands with removalCount>0; queued candidates come from FinalizeBodies under the same condition. Any intervening island destruction clears world.splitIslandId (island.c:60-62), so the task cannot use a stale sleeping/already-split island. Both public interleavings are exercised by T2-PENDING-*-at30; WS11 records candidate 0 -> ffffffff before the next Step.', closed=True)
        elif file == 'src/math_functions.c' and function == 'b2Atan2' and number == 64:
            row.update(classification='S', reason='The missing (0,0) atan2 branch cannot be produced by relative angles of valid normalized rotations. Header math_functions.h:471-477 computes dot/cross of two unit rotations. DIRECT invalid zero rotation is refused INPUT_ROTATION in the existing negative corpus; generic standalone atan2(0,0) is outside the 14b helper profile.', closed=True)
        elif file == 'src/joint.c' and (number in (518, 520, 568, 570, 128, 982) or number in (1093, 1095, 1248)):
            row.update(classification='S', reason='Locked/raw-invalid route excluded before raw by contract §4; real game LOCKED/TYPE refusal in full GUARD221. Invalid dispatcher type cannot be created in 0/4/5 profile.', closed=True)
        else:
            row.update(classification='U', reason='No positive same-source historical counter or established domain proof yet', closed=False)
        if before[key] == 0:
            row['rawCounters'] = before_raw[key]
        rows.append(row)
    summary = {'scopes': {}, 'classesOfInitialGaps': dict(Counter(r['classification'] for r in rows if not r['before'])),
               'openN': sum(r['classification'] == 'N' and not r['closed'] for r in rows),
               'openP': sum(r['classification'] == 'P' and not r['closed'] for r in rows),
               'U': sum(r['classification'] == 'U' for r in rows), 'newSituationCount': len(manifest['cases'])+len(supplements),
               'historicalMatchingSourceFiles': sorted(matching)}
    summary['unmappedInCurrentScope'] = sum(not r['port'] and not r['scope'].startswith('later') for r in rows)
    summary['scopeCorrections'] = [{'function': 'b2InvTransformPoint', 'scope': 'later-typed',
                                    'proof': 'Only joint.c:466-467 mouse constructor calls it in these units; mouse is explicitly later 14c. Four previously provisional math U rows remain listed as LATER, not S.'}]
    for area in sorted({r['scope'] for r in rows}):
        selected = [r for r in rows if r['scope'] == area]
        summary['scopes'][area] = {kind: {'denominator': sum(r['kind'].startswith(kind) for r in selected),
                                        'beforeHit': sum(r['kind'].startswith(kind) and r['before'] > 0 for r in selected),
                                        'afterHit': sum(r['kind'].startswith(kind) and r['after'] > 0 for r in selected)} for kind in ('line', 'edge')}
    summary['files'] = {}
    for file in sorted({r['file'] for r in rows}):
        selected = [r for r in rows if r['file'] == file and not r['scope'].startswith('later')]
        summary['files'][file] = {kind: {'denominator': sum(r['kind'].startswith(kind) for r in selected),
                                        'beforeHit': sum(r['kind'].startswith(kind) and r['before'] > 0 for r in selected),
                                        'afterHit': sum(r['kind'].startswith(kind) and r['after'] > 0 for r in selected)} for kind in ('line', 'edge')}
    save(evidence/'14b-pokrycie.json', {'summary': summary, 'rows': rows})
    save(evidence/'U.json', [r for r in rows if r['classification'] == 'U'])
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repo', 'source', 'evidence', 'historical'):
        parser.add_argument('--'+name, type=Path, required=True)
    main(parser.parse_args())
