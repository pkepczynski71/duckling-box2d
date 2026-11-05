pass                                                                          

                                                
                                                     
   
from collections import Counter
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'zapytania-18a-przypadki.json'
PINS = {
    'fixtures/norms/KONTRAKT-18.json': 'a4b92d4c8f6d4ffab79697e9ec1645fd7835fd28b4b2a38e6316f47bbfa51447',
    'zapytania-18a-przypadki.json': '3355be855dd55e3223eff5ff4a8d42b6a695adc223540c0cb56740c2769e9cee',
    'zapytania-18a-wzory.csv': '1466647853040d45c422439a382c9cfb3ec631f663dc2b0950a6f2d7cea26b45',
    '18-zrodlo-sumy.json': '3b9d5a0d80b82ae919e709725f0a6b88a6c50af7906476adfe252c2278a5380f',
    '18a-C-POMIAR.json': '3b73578fb3526b0e773323d9e0d49e3e8043fb33c292485b8a4c1eeb16346fad',
    '18a-KONTROLA-DANYCH.json': '224fb99400eab9bad97161bcfdb7b919b1d0944d2ed6fcb2900b9fe180b4ace1',
}
DEC = re.compile(r'0|[1-9][0-9]{0,9}')
HEX = re.compile(r'[0-9a-f]{8}')
                                                                            
METADATA = {'CASE': 2, 'E18': 4, 'R18': 7, 'I18': 3,
            'V18': 5, 'G18': 4, 'GA18': 5, 'ENDCASE': 1, 'END': 1}
PAYLOAD = {'E18', 'R18', 'I18', 'V18', 'G18'}


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def manifest():
    for name, wanted in PINS.items():
        if digest(HERE / name) != wanted:
            raise ValueError('F18A SHA256 mismatch: ' + name)
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if (data['schema'], data['part']) != ('18A-GEOMETRY-1', 'A'):
        raise ValueError('manifest schema/part')
    for key, n in [('direct', 96), ('public', 96), ('guards', 821), ('parsers', 24)]:
        if [r['id'] for r in data[key]] != list(range(1, n + 1)):
            raise ValueError('manifest population ' + key)
    return data


def record(tag, metadata, payload=()):
    text = tag + ''.join(' ' + str(x) for x in metadata)
    text += ''.join(' ' + (x if isinstance(x, str) else f'{x:08x}') for x in payload)
    return text + '\n'


def parse_record(line):
    if not line.endswith('\n') or len(line) > 4096 or not line.isascii() or '\r' in line:
        raise ValueError('output ASCII/LF/length')
    tokens = line[:-1].split(' ')
    tag = tokens[0]
    if tag not in METADATA or '' in tokens:
        raise ValueError('output tag/spacing')
    m = METADATA[tag]
    if len(tokens) < 1 + m:
        raise ValueError('output metadata arity')
    if any(not DEC.fullmatch(t) or int(t) > 0xffffffff for t in tokens[1:1+m]):
        raise ValueError('output canonical metadata')
    meta = tuple(map(int, tokens[1:1+m]))
    payload = tokens[1+m:]
    if len(payload) != (meta[-1] if tag in PAYLOAD else 0):
        raise ValueError('output payload arity')
    if any(not HEX.fullmatch(t) for t in payload):
        raise ValueError('output H8')
    if tag in {'R18', 'V18'}:
        kind = meta[5] if tag == 'R18' else meta[3]
        if kind not in (0, 1, 2) or len(payload) != (0, 1, 7)[kind]:
            raise ValueError('result kind/arity')
        if payload and payload[0] not in ('00000000', '00000001'):
            raise ValueError('result boolean')
    return tag, meta, tuple(payload)


def expected(profile, data=None, observe=True):
    pass                                                                 

                                                                           
                                                                          
       
    data = data or manifest()
    raw = {r['id']: r for r in data['direct']}
    rows = data[{'DIRECT': 'direct', 'PUBLIC': 'public', 'GUARD': 'guards'}[profile]]
    for row in rows:
        cid = row['id']
        m = {'DIRECT': 1, 'PUBLIC': 8, 'GUARD': 0}[profile]
        yield record('CASE', (cid, m))
        if profile == 'GUARD':
            for phase, key in [(0, 'negativeH'), (1, 'positiveH')]:
                w = row[key]
                yield record('G18', (cid, phase, 500, len(w)), w)
                accepted, status, reason = ((row['negativeAccepted'], row['negativeStatus'], row['negativeReason'])
                                            if phase == 0 else (1, 0, 0))
                yield record('GA18', (cid, phase, accepted, status, reason))
        else:
            ops = ([dict(seq=1, opcode=500, payloadH=row['payloadH'])]
                   if profile == 'DIRECT' else row['operations'])
            banks = {}
            current = None
            for op in ops:
                seq, code, w = op['seq'], op['opcode'], op['payloadH']
                yield record('E18', (cid, seq, code, len(w)), w)
                status = reason = kind = 0
                values = []
                if code == 500:
                    kind = 1 if row['kind'] <= 3 else 2
                    if profile == 'PUBLIC' and (seq == 7 or seq == 6 and 'resultForSeq6' in row):
                        refusal = row['refusalSeq7'] if seq == 7 else row['resultForSeq6']
                        status, reason, values = refusal['status'], refusal['reason'], refusal['resultH']
                    else:
                        did = row.get('baselineDirectId', cid) if seq != 6 else row['differentQueryDirectId']
                        values = list(raw[did]['resultH'])
                    current = (kind, list(values))
                elif code == 516:
                    banks[int(w[0], 16)] = (current[0], list(current[1]))
                elif code == 518:
                    banks[int(w[0], 16)][1][int(w[1], 16)] = w[2]
                yield record('R18', (cid, seq, code, status, reason, kind, len(values)), values)
                if code == 500 and observe:
                    yield record('I18', (cid, seq, len(w)-2), w[2:])
                for bank, (bk, bv) in sorted(banks.items()):
                    yield record('V18', (cid, seq, bank, bk, len(bv)), bv)
        yield record('ENDCASE', (cid,))
    yield record('END', (len(rows),))


def compare(actual, wanted):
    pass                                                                         
    counts = Counter()
    words = 0
    for number, (a, b) in enumerate(zip_longest(actual, wanted), 1):
        if a is None or b is None:
            raise ValueError(f'line {number}: missing/extra record; actual={str(a)[:2048]!r}, expected={str(b)[:2048]!r}')
        tag, meta, payload = parse_record(a)
        parse_record(b)
        counts[tag] += 1
        words += len(payload)
        if a != b:
            at = next((i for i, (x, y) in enumerate(zip_longest(a.split(), b.split())) if x != y), 0)
            raise ValueError(f'line {number}, {tag}, metadata={meta}, token={at}:\nactual {a[:2048]}expected {b[:2048]}')
    return {'tags': dict(counts), 'payloadWords': words, 'records': sum(counts.values())}


def emit(profile, side, data=None):
    return (data or manifest())['literalInputs'][profile + side.upper()]


def example_input(example, side):
    w = example['payloadH']
    payload = w if side.upper() == 'C' else [str(int(x, 16)) for x in w]
    return 'PORT18 A DIRECT 1\nC 1 1\nO 1 500 ' + str(len(w)) + ' ' + ' '.join(payload) + '\n'


def example_expected(example):
    w, r = example['payloadH'], example['resultH']
    return [record('CASE', (1, 1)), record('E18', (1, 1, 500, len(w)), w),
            record('R18', (1, 1, 500, 0, 0, 2, len(r)), r),
            record('I18', (1, 1, len(w)-2), w[2:]), record('ENDCASE', (1,)), record('END', (1,))]


def additional_data(packet, baseline=None):
    pass                                                                    
    baseline = baseline or manifest()
    if packet['schema']!='N18A-GEOMETRY-1' or packet['f18a']!='c0f1934887895750ac4bce0ab1e0679add6481ba':
        raise ValueError('N18A schema/base')
    rows = packet['direct']
    if [r['id'] for r in rows]!=list(range(1,len(rows)+1)) or not 1<=len(rows)<=96:
        raise ValueError('N18A diagnostic IDs')
    return {'DIRECT':dict(baseline,direct=rows), 'PUBLIC':dict(baseline,public=packet['public'])}


def additional_input(packet, profile, side):
    rows=packet[{'DIRECT':'direct','PUBLIC':'public'}[profile]]
    lines=[f'PORT18 A {profile} {len(rows)}\n']
    for row in rows:
        ops=[dict(seq=1,opcode=500,payloadH=row['payloadH'])] if profile=='DIRECT' else row['operations']
        lines.append(f'C {row['id']} {len(ops)}\n')
        for op in ops:
            words=op['payloadH'] if side.upper()=='C' else [str(int(h,16)) for h in op['payloadH']]
            lines.append(f'O {op['seq']} {op['opcode']} {len(words)} '+' '.join(words)+'\n')
    return ''.join(lines)
