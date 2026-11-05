pass                                                                       
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST_SHA = 'e3fc31793007ebb2251061657426e7be680045744c39bd91aacd08a3edfc02d2'
CONTRACT_SHA = '886047d352e90c2b61cb1b69cfe238fa07e470f5f410343e634bab0ff77ae400'


def manifest():
    for name, sha in [('sensory-przypadki.json', MANIFEST_SHA), ('fixtures/norms/KONTRAKT-17.json', CONTRACT_SHA)]:
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest() != sha:
            raise ValueError(f'frozen bytes changed: {name}')
    return json.loads((HERE/'sensory-przypadki.json').read_bytes())


def c18a_cases(data):
    pass                                                                           
    for kind, name in enumerate(('public', 'direct')):
        for case in data[name]:
            yield {'id': case['id'], 'kind': kind, 'ordinal': case['ordinal'],
                   'family': case['family'], 'expected': case['c18a']}
    extra = data['c18a']['extraLock']
    yield {'id': extra['id'], 'kind': extra['kind'], 'ordinal': extra['ordinal'],
           'family': 'lock', 'expected': extra}


def parser_inputs(data, output):
    pass                                                                         
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for case in data['parserCases']:
        for side in ('C', 'D'):
            for phase in ('negative', 'positive'):
                path = output/f'{case['id']}-{side}-{phase}.in'
                raw = case[phase+side].encode('utf-8')
                path.write_bytes(raw)
                result.append({'id': case['id'], 'side': side, 'phase': phase,
                               'file': path.name, 'bytes': len(raw),
                               'sha256': hashlib.sha256(raw).hexdigest(),
                               'exit': case['exit'] if phase == 'negative' else case['positiveExit'],
                               'stderr': case['stderr'] if phase == 'negative' else case['positiveStderr']})
    (output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


def guard_lines(data, side):
    if side not in ('C', 'D'):
        raise ValueError('side must be C or D')
    yield 'PORT17 GUARD 697\n'
    for case in data['guards']:
        ordinal = case['ordinal']
        yield f'C {ordinal} 0\n'
        for phase, name in enumerate(('negative', 'positive')):
            words = case[name+'ContextH']+case[name+'PayloadH']
            if side == 'D':
                words = [str(int(w, 16)) for w in words]
            line = f'G {ordinal} {ordinal} {phase} {case['routeId']} {len(words)} '+ ' '.join(words)+'\n'
            if len(line.encode('ascii'))-1 > 2048:
                raise ValueError(f'{case['id']}: frozen input line exceeds contract')
            yield line


def guard_inputs(data, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for side in ('C', 'D'):
        path = output/f'GUARD-{side}.in'
        with path.open('wb') as stream:
            for line in guard_lines(data, side):
                stream.write(line.encode('ascii'))
        result.append({'side': side, 'file': path.name, 'cases': 697, 'phases': 1394,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
                       'executed': False})
    (output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parser-inputs', type=Path)
    parser.add_argument('--guard-inputs', type=Path)
    args = parser.parse_args()
    data = manifest()
    if args.guard_inputs:
        print(json.dumps(guard_inputs(data, args.guard_inputs), indent=2))
    elif args.parser_inputs:
        print(json.dumps({'materialized': len(parser_inputs(data, args.parser_inputs)),
                          'executed': 0, 'completePORT17': False}))
    else:
        print(json.dumps([dict(id=x['id'], kind=x['kind'], ordinal=x['ordinal'], family=x['family'])
                          for x in c18a_cases(data)], indent=2))
