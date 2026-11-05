pass                                                                          
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = {'fixtures/norms/KONTRAKT-16a.json': 'c264a5ecc8e3b5179a1c887a919c4f28f637408c871a1f3d4c7e180bfdd47ca0',
        'ccd-16a-przypadki.json': '091d7c5a608673e431bed764e89d251450bb56101a13f6e75f5835b05b5a51f0'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest():
    for name, expected in PINS.items():
        if sha(HERE / name) != expected:
            raise ValueError('Frozen file changed: ' + name)
    return json.loads((HERE / 'ccd-16a-przypadki.json').read_text(encoding='utf-8'))


def operations(case):
    result = []
    for sample in case['samples']:
        for mode in ((0, 1) if sample['opcode'] in (300, 301) else (0,)):
            words = list(sample['wordsH'])
            words[0] = f'{mode:08x}'
            result.append((sample['opcode'], words))
    if len(result) != case['operationCount']:
        raise ValueError('Frozen operation count mismatch')
    return result


def input_bytes(profile, side='C', ids=None):
    m = manifest()
    rows = m['cases' if profile == 'DIRECT' else 'guards']
    if ids is not None:
        rows = [row for row in rows if row['ordinal'] in ids]
    if not rows:
        raise ValueError('Empty selection')
    lines = [f'PORT16 A {profile} {len(rows)}']
    def payload(words):
        return ' '.join(words if side == 'C' else [str(int(w, 16)) for w in words])
    for row in rows:
        i = row['ordinal']
        if profile == 'DIRECT':
            ops = operations(row)
            lines.append(f'C {i} {len(ops)}')
            lines.extend(f'O {seq} {op} {len(words)} {payload(words)}'
                         for seq, (op, words) in enumerate(ops, 1))
        else:
            lines.append(f'C {i} 0')
            for key in ('negativePayloadH', 'positivePayloadH'):
                words = row[key]
                lines.append(f'G {i} {i} {row['opcode']} {len(words)} {payload(words)}')
    return ('\n'.join(lines) + '\n').encode('ascii')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--profile', choices=('DIRECT', 'GUARD'), required=True)
    p.add_argument('--side', choices=('C', 'D'), default='C')
    p.add_argument('--ids', help='comma separated diagnostic IDs')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.write_bytes(input_bytes(a.profile, a.side, None if not a.ids else set(map(int, a.ids.split(',')))))
