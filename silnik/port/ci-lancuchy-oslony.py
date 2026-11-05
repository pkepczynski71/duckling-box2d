pass                                                               

                                                                             
                                                                          
   
from collections import Counter
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager, ExitStack
from itertools import zip_longest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


m = load('lancuchy_stage_model', 'model-lancuchy.py')
b = load('lancuchy_stage_branches', 'galezie-lancuchy.py')


def point_call():
    a = [0] * 64
    a[1] = a[23] = 1
    a[21] = a[43] = 0x3f800000
    a[25] = 0x40000000
    return 0, tuple(a)


def encode(operations, decimal=False, profile='R', guard=None):
    word = str if decimal else lambda v: f'{v:08x}'
    if guard is None:
        lines = [f'PORT13A {profile} 1', f'C 1 {len(operations)}']
    else:
        kind, ga = guard
        lines = ['GUARD13A 1', f'G 1 {kind} 0 {len(operations)}',
                 'GA 1 ' + ' '.join(map(word, ga))]
    for seq, (kind, a) in enumerate(operations, 1):
        lines.append(f'O {seq} {kind} ' + ' '.join(map(word, a)))
    return ('\n'.join(lines) + '\n').encode('ascii')


def render(records):
    lines = []
    for tag, values in records:
        if tag == 'PORT13A':
            lines.append(f'PORT13A {values[0]} {values[1]}')
            continue
        prefix = 2 if tag == 'P13A' else m.SCHEMA[tag][0]
        tokens = [str(v) if i < prefix else f'{v:08x}' for i, v in enumerate(values)]
        lines.append(' '.join([tag, *tokens]))
    return ('\n'.join(lines) + '\n').encode('ascii')


def normative_operation(a=None, ident=1, seq=1):
    pass                                                                            
    a = tuple(a or point_call()[1])
    incoming = a[46:53]
    outgoing = (1, 0, incoming[2], incoming[3], 0, incoming[5], incoming[6])
    return [('E13A', (ident, seq, 0, *a)), ('A13', (ident, seq, 0, 0)),
            ('KI13', (ident, seq, *incoming)),
            ('D13A', (ident, seq, 0, 0, 0x40000000, 0, 0x3f800000, 0, 0x40000000, 1, 0)),
            ('K13A', (ident, seq, *outgoing)),
            ('ZA13', (ident, seq, 1, 1, 1, 1, 1, 0, 0, 0))]


def normative_trace_operation(a, seq=1):
    pass                                                                     
    rows = normative_operation(a, seq=seq)
    rows[3] = ('D13A', (*rows[3][1][:-1], 1))
    rows[-1] = ('ZA13', (1, seq, 1, 1, 1, 1, 1, 0, 1, 1))
    rows[-1:-1] = [('T13A', (1, seq, 0, 1)),
                   ('V13A', (1, seq, 0, 0, 1, 0, 0, 0x40000000, 0, 0xc0000000, 0, 0x3f800000, 0, 0))]
    return rows


def guard_definitions():
    manifest = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    result = []
    for row in manifest['guardPrzypadki']:
        if row['czesc'] != '13a':
            continue
        name, kind = row['id'], row['Gkind']
        if kind == 103:
            a = [0] * 64
        elif kind in (101, 102):
            a = [0] * 64
            a[0], a[1], a[5] = 1, 2, 0x3f800000
            if kind == 102:
                a[25] = 0x3f800000
        else:
            a = list(point_call()[1])
            a[0], a[1], a[23] = 1, 2, 2
            a[5], a[27] = 0x3f800000, 0x40400000
        status = 0 if kind == 103 else 4 if name.startswith(('GA1', 'GA4')) else 5
        if name.startswith('GA1'):
            n = 23 if '-DISTANCE-B-' in name else 1
            a[n] = 0 if name.endswith('LOW') else 9
            start = 25 if n == 23 else 3
            length = 16 if kind == 100 else 20
            a[start:start + length] = [0] * length
            if a[n]:
                for j in range(min(a[n], 8 if kind == 100 else 10)):
                    a[start + 2 * j] = m.bits(float(j))
        elif name.startswith('GA2-RADIUS'):
            a[24 if '-B-' in name else 2] = 0x7f800000 if name.endswith('FINITE') else 0xbf800000
        elif name.startswith('GA2-XF'):
            start = 41 if '-B-' in name else 23 if '-OFFSET-' in name else 19
            a[start + int(name.endswith('-Y'))] = 0x7f800000
        elif name.startswith('GA2-ROT'):
            start = 43 if '-B-' in name else 25 if '-OFFSET-' in name else 21
            if name.endswith('EQUALITY'):
                a[start] = 0x3f000001
                a[start + 1] = 0x3f5d9d22 if '-LOW-' in name else 0x3f5dca89
            else:
                a[start] = 0 if name.endswith('LOW') else 0x40000000
                a[start + 1] = 0
        elif name == 'GA3-COUNT4':
            a[46] = 4
        elif name.startswith('GA3-INDEX'):
            a[46] = 1
            a[50 if name.endswith('-B') else 47] = 2
        elif name.startswith('GA4-POINT'):
            start = 27 if '-B-' in name else 5
            a[start + int(name.endswith('-Y'))] = 0x7f800000
        result.append({'name': name, 'kind': kind, 'a': tuple(a), 'status': status})
    m.require(len(result) == 38 and len({r['name'] for r in result}) == 38, 'all 38 frozen guards required')
    return result


class StandControls(unittest.TestCase):
    def setUp(self):
        self.a = list(point_call()[1])
        self.a[48:50], self.a[51:53] = [71, 72], [81, 82]
        self.a = tuple(self.a)
        self.rows = normative_operation(self.a)

    def test_normative_literal_and_canary(self):
        m.check_operation(self.rows, 1, 1, 0, self.a)
        data = render([('PORT13A', ('R', 1)), ('CASE', (1, 1)), *self.rows,
                       ('ENDCASE', (1,)), ('END', (1,))])
        self.assertTrue(m.validate(data, encode([(0, self.a)]))['validated'])

    def test_independent_stream_corruptions(self):
        for name, damage in (
                ('missing-KI', lambda r: r.pop(2)),
                ('duplicate-KI', lambda r: r.insert(2, r[2])),
                ('missing-K', lambda r: r.pop(4)),
                ('changed-KI', lambda r: r.__setitem__(2, ('KI13', (1, 1, 1, 0, 71, 72, 0, 81, 82)))),
                ('inactive-canary', lambda r: r.__setitem__(4, ('K13A', (1, 1, 1, 0, 70, 72, 0, 81, 82)))),
                ('counter21', lambda r: r.__setitem__(3, ('D13A', (*r[3][1][:-2], 21, 0)))),
                ('changed-echo', lambda r: r.__setitem__(0, ('E13A', (*r[0][1][:-1], 1)))),
                ('wrong-ZA', lambda r: r.__setitem__(-1, ('ZA13', (1, 1, 1, 1, 0, 1, 1, 0, 0, 0))))):
            with self.subTest(name=name):
                for side in ('C', 'D'):                                                   
                    changed = copy.deepcopy(self.rows)
                    damage(changed)
                    with self.assertRaises(ValueError, msg=side):
                        m.check_operation(changed, 1, 1, 0, self.a)

    def test_warm_own_history_and_cold(self):
        a = list(point_call()[1])
        history = (1, 0, 71, 72, 0, 81, 82)
        rows = normative_operation(tuple(a), seq=2)
        rows[2] = ('KI13', (1, 2, *history))
        rows[4] = ('K13A', (1, 2, *history))
        m.check_operation(rows, 1, 2, 0, a, history=history, memory='ciepla')
        with self.assertRaises(ValueError):
            m.check_operation(rows, 1, 2, 0, a, history=(1, 0, 70, 72, 0, 81, 82), memory='ciepla')
        with self.assertRaises(ValueError):
            m.check_operation(rows, 1, 2, 0, a, memory='zimna')

    def test_trace_slots_and_defined(self):
        a = list(point_call()[1])
        a[53], a[54] = 23, 1
        rows = normative_operation(a, ident=113)
        rows[3] = ('D13A', (*rows[3][1][:-1], 3))
        trace = []
        for i in range(3):
            trace += [('T13A', (113, 1, i, 1)),
                      ('V13A', (113, 1, i, 0, 1, 0, 0, 0x40000000, 0, 0xc0000000, 0, 0x3f800000, 0, 0))]
        rows[-1:] = [*trace, ('ZA13', (113, 1, 1, 1, 1, 1, 1, 0, 3, 3))]
        m.check_operation(rows, 113, 1, 0, a, profile='D')
        for index, payload_index, value in ((8, 4, 0), (6, 3, 1), (3, -1, 0)):
            changed = copy.deepcopy(rows)
            tag, words = changed[index]
            words = list(words)
            words[payload_index] = value
            changed[index] = (tag, tuple(words))
            with self.assertRaises(ValueError):
                m.check_operation(changed, 113, 1, 0, a, profile='D')
        changed = copy.deepcopy(rows)
        tag, words = changed[6]
        words = list(words)
        words[7], words[9] = 0x40400000, 0xc0400000                                       
        changed[6] = (tag, tuple(words))
        for side in ('C', 'D'):
            with self.assertRaises(ValueError, msg=side):
                m.check_operation(changed, 113, 1, 0, a, profile='D')

    def test_guards_independent_expected_status_and_boundaries(self):
        for row in guard_definitions():
            if row['kind'] == 103:
                continue
            with self.subTest(guard=row['name']):
                self.assertEqual(row['status'], m.checked_status(row['kind'] - 100, row['a'])[0])
                if row['name'].endswith('EQUALITY'):
                    start = 43 if '-B-' in row['name'] else 25 if '-OFFSET-' in row['name'] else 21
                    c, s = map(m.number, row['a'][start:start + 2])
                    self.assertEqual(m.bits(m.add(m.mul(s, s), m.mul(c, c))),
                                     0x3f7fd8ae if '-LOW-' in row['name'] else 0x3f8013a9)

    def test_empty_branch_ledger_cannot_pass(self):
        result = b.table()
        self.assertEqual(result['code'], 1)
        self.assertEqual(result['verified'], 0)
        self.assertIn('support-limit20', result['gaps'])

    def test_warm_first_refusal_keeps_seed(self):
        a = list(self.a)
        a[0], a[2], a[46] = 1, 0xbf800000, 1
        rows = [('E13A', (85, 1, 0, *a)), ('A13', (85, 1, 5, 0)),
                ('ZA13', (85, 1, 1, 1, 0, 0, 0, 0, 0, 0))]
        history = m.check_operation(rows, 85, 1, 0, a, memory='ciepla')
        self.assertEqual(history, tuple(a[46:53]))
        next_a = list(self.a)
        next_a[46:53] = [0] * 7
        next_rows = normative_operation(next_a, ident=85, seq=2)
        next_rows[2] = ('KI13', (85, 2, *history))
        next_rows[4] = ('K13A', (85, 2, *history))
        m.check_operation(next_rows, 85, 2, 0, next_a, history=history, memory='ciepla')


def selftest():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StandControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'ok': result.wasSuccessful()}


def negative_definitions():
    pass                                                                              
    operation = point_call()
    result = []
    for after in (False, True):
        good = encode([operation] * (2 if after else 1))
        lines = good.splitlines(keepends=True)
        index = 3 if after else 0
        def add(name, error, changed):
            result.append({'name': ('after-O/' if after else 'initial/') + name,
                           'error': error, 'data_C': changed, 'after': after})
        for label, prefix in (('BOM', b'\xef\xbb\xbf'), ('nonascii', b'\x80')):
            damaged = lines[:]
            damaged[index] = prefix + damaged[index]
            add(label, 'INPUT_ASCII', b''.join(damaged))
        for label, damage in (('double-space', lambda x: x.replace(b' ', b'  ', 1)),
                              ('leading-space', lambda x: b' ' + x),
                              ('trailing-space', lambda x: x.rstrip(b'\n') + b' \n'),
                              ('tab', lambda x: x.replace(b' ', b'\t', 1))):
            damaged = lines[:]
            damaged[index] = damage(damaged[index])
            add(label, 'INPUT_SPACING', b''.join(damaged))
        damaged = lines[:]
        damaged[index] = b'\n'
        add('empty-line', 'INPUT_EMPTY_LINE', b''.join(damaged))
        damaged = lines[:]
        damaged[index] = damaged[index].replace(b'\n', b'\r')
        add('CR', 'INPUT_CR', b''.join(damaged))
        add('EOF-missing', 'INPUT_EOF', b''.join(lines[:3] if after else lines[:1]))
        add('EOF-incomplete', 'INPUT_EOF', b''.join(lines[:3] if after else lines[:1]) + b'O 2 0')
        damaged = lines[:]
        damaged[index] = b'X' + damaged[index][1:]
        add('tag', 'INPUT_TAG', b''.join(damaged))
        if not after:
            for n in ('0', '129'):
                add('N' + n, 'INPUT_N', f'PORT13A R {n}\n'.encode())
            for n in ('01', '+1', '-1', '4294967296'):
                add('decimal-' + n, 'INPUT_DECIMAL', f'PORT13A R {n}\n'.encode())
        op_index = 3 if after else 2
        for count in (63, 65):
            damaged = lines[:]
            op = damaged[op_index].split()
            damaged[op_index] = b' '.join(op[:3] + (op[3:3 + count] if count == 63 else op[3:] + [b'00000000'])) + b'\n'
            add('arity' + str(count), 'INPUT_ARITY', b''.join(damaged))
        damaged = lines[:]
        damaged[op_index] = b'X' * 2049 + b'\n'
        add('line2049', 'INPUT_ARITY', b''.join(damaged))
        for word in ('0000000A', '0x000000', '0000000', '000000000', '-0000001'):
            damaged = lines[:]
            op = damaged[op_index].split()
            op[5] = word.encode()
            damaged[op_index] = b' '.join(op) + b'\n'
            add('word-' + word, 'INPUT_WORD', b''.join(damaged))
        for name, error, field, value in (
                ('seq0', 'INPUT_SEQ', 1, '0'), ('seq-gap', 'INPUT_SEQ', 1, '3'),
                ('kind3', 'INPUT_OPCODE', 2, '3'), ('mode2', 'INPUT_MODE', 3, '00000002'),
                ('bool2', 'INPUT_BOOL', 48, '00000002'), ('unused-minus0', 'INPUT_UNUSED', 66, '80000000'),
                ('raw-count0', 'INPUT_DOMAIN', 4, '00000000'), ('raw-count9', 'INPUT_DOMAIN', 4, '00000009'),
                ('cache4', 'INPUT_CACHE', 49, '00000004'), ('cache-u16', 'INPUT_CACHE', 49, '00010000'),
                ('cache-u8', 'INPUT_CACHE', 50, '00000100'), ('raw-rotation', 'INPUT_ROTATION', 24, '00000000')):
            damaged = lines[:]
            op = damaged[op_index].split()
            op[field] = value.encode()
            damaged[op_index] = b' '.join(op) + b'\n'
            add(name, error, b''.join(damaged))
        if not after:
            for name, error, row in (('id2', 'INPUT_ID', b'C 2 1\n'),
                                     ('opCount0', 'INPUT_OPCOUNT', b'C 1 0\n'),
                                     ('opCount33', 'INPUT_OPCOUNT', b'C 1 33\n')):
                damaged = lines[:]
                damaged[1] = row
                add(name, error, b''.join(damaged))
        if not after:
            for suffix in (b'\n', b'X', b'\x00', b'\r\n'):
                add('trailing-' + suffix.hex(), 'INPUT_TRAILING_DATA', good + suffix)
                                                                  
    corrected = {'initial/EOF-missing', 'initial/EOF-incomplete',
                 'initial/id2', 'initial/opCount0', 'initial/opCount33'}
    for definition in result:
        if definition['name'] in corrected:
            definition['expected'] = b'PORT13A R 1\n'
            if definition['name'] == 'initial/EOF-incomplete':
                definition['error'] = 'INPUT_TAG'
    return result


def decimal_negative(data):
    pass                                                                           
    result = []
    for line in data.splitlines(keepends=True):
        ending = b'\r\n' if line.endswith(b'\r\n') else b'\n' if line.endswith(b'\n') else b''
        tokens = (line[:-len(ending)] if ending else line).split(b' ')
        if tokens and tokens[0] in (b'O', b'GA'):
            start = 3 if tokens[0] == b'O' else 2
            for i in range(start, len(tokens)):
                value = tokens[i].decode('ascii', errors='ignore')
                if m.H.fullmatch(value):
                    tokens[i] = str(int(value, 16)).encode()
                elif value in ('0000000A', '0x000000', '0000000', '000000000', '-0000001'):
                    tokens[i] = {'0000000A': b'4294967296', '0x000000': b'0x0', '0000000': b'00',
                                 '000000000': b'+0', '-0000001': b'-1'}[value]
            line = b' '.join(tokens) + ending
        result.append(line)
    return b''.join(result)


def supplemental_negatives():
    pass                                                                          
    result = []
    op = point_call()
    def add(name, error, data, expected=b''):
        result.append({'name': 'supplement/' + name, 'error': error, 'data_C': data,
                       'after': False, 'expected': expected})
    for after in (False, True):
        count = 2 if after else 1
        good = encode([op] * count)
        lines = good.splitlines(keepends=True)
        index = 3 if after else 2
        prefix = render([('PORT13A', ('R', 1)), ('CASE', (1, count)),
                         *(normative_operation() if after else [])])
        for word in ('01', '+1', '-1', '4294967296'):
            damaged = lines[:]
            fields = damaged[index].split()
            fields[1] = word.encode()
            damaged[index] = b' '.join(fields) + b'\n'
            add(f'decimal-seq-{after}-{word}', 'INPUT_DECIMAL', b''.join(damaged), prefix)
        for name, error, changes in (
                ('trace-bool', 'INPUT_BOOL', {54: 2}),
                ('mode-before-bool', 'INPUT_MODE', {0: 2, 45: 2}),
                ('profile-trace', 'INPUT_PROFILE', {54: 1}),
                ('capacity24', 'INPUT_DOMAIN', {53: 24, 54: 1}),
                ('NULL-capacity', 'INPUT_UNUSED', {53: 1}),
                ('unused-point', 'INPUT_UNUSED', {5: 0x80000000}),
                ('cache-active-A', 'INPUT_CACHE', {46: 1, 47: 1}),
                ('cache-active-B', 'INPUT_CACHE', {46: 1, 50: 1}),
                ('cache-last-byte', 'INPUT_CACHE', {52: 256}),
                ('raw-radius-A', 'INPUT_DOMAIN', {2: 0xbf800000}),
                ('raw-radius-B', 'INPUT_DOMAIN', {24: 0x7f800000}),
                ('raw-point-X', 'INPUT_DOMAIN', {3: 0x7f800000}),
                ('raw-point-Y', 'INPUT_DOMAIN', {4: 0x7fc00000}),
                ('raw-xf-B', 'INPUT_ROTATION', {41: 0x7f800000}),
                ('raw-rotation-B', 'INPUT_ROTATION', {43: 0}),
                ('transport-count11', 'INPUT_DOMAIN', {1: 11})):
            a = list(op[1])
            for field, value in changes.items():
                a[field] = value
            damaged = lines[:]
            replacement = encode([(0, tuple(a))]).splitlines(keepends=True)[2]
            damaged[index] = replacement.replace(b'O 1 ', b'O 2 ', 1) if after else replacement
            add(f'{name}-{after}', error, b''.join(damaged), prefix)
                                                                   
        if after:
            before = encode([op]).replace(b'PORT13A R 1', b'PORT13A R 2', 1)
            expected = render([('PORT13A', ('R', 2)), ('CASE', (1, 1)),
                               *normative_operation(), ('ENDCASE', (1,))])
            for name, error, tail in (
                    ('case-id', 'INPUT_ID', b'C 3 1\n'),
                    ('case-count0', 'INPUT_OPCOUNT', b'C 2 0\n'),
                    ('case-count33', 'INPUT_OPCOUNT', b'C 2 33\n'),
                    ('case-decimal', 'INPUT_DECIMAL', b'C 02 1\n'),
                    ('case-EOF', 'INPUT_EOF', b'C 2'),
                    ('case-tag', 'INPUT_TAG', b'X 2 1\n')):
                add(name, error, before + tail, expected)
    add('header-profile', 'INPUT_PROFILE', b'PORT13A X 1\n')
    add('header-overfull-EOF', 'INPUT_ARITY', b'PORT13A R 1 extra')
    add('line2048', 'INPUT_TAG', b'X' * 2048 + b'\n')
    after = encode([op, op]).splitlines(keepends=True)
    prefix = render([('PORT13A', ('R', 1)), ('CASE', (1, 2)), *normative_operation()])
    add('O-overfull-EOF', 'INPUT_ARITY', b''.join(after[:3]) + after[3].rstrip(b'\n') + b' 00000000', prefix)
    guard = encode([], guard=(103, (0,) * 64))
    glines = guard.splitlines(keepends=True)
    for name, error, row in (
            ('G-id', 'INPUT_ID', b'G 2 103 0 0\n'),
            ('G-kind', 'INPUT_OPCODE', b'G 1 104 0 0\n'),
            ('G-phase', 'INPUT_PHASE', b'G 1 103 1 0\n'),
            ('G-calls', 'INPUT_OPCOUNT', b'G 1 103 0 1\n'),
            ('G-decimal', 'INPUT_DECIMAL', b'G 01 103 0 0\n'),
            ('G-arity', 'INPUT_ARITY', b'G 1 103 0\n'),
            ('G-EOF', 'INPUT_EOF', b'G 1 103')):
        add(name, error, glines[0] + row + (glines[2] if row.endswith(b'\n') else b''))
    for name, error, field, word in (('GA-id', 'INPUT_ID', 1, b'2'),
                                     ('GA-unused', 'INPUT_UNUSED', 2, b'80000000'),
                                     ('GA-word', 'INPUT_WORD', 2, b'0000000A')):
        fields = glines[2].split()
        fields[field] = word
        add(name, error, b''.join(glines[:2]) + b' '.join(fields) + b'\n')
    for value in (0, 2):
        add('GUARD-N' + str(value), 'INPUT_N', f'GUARD13A {value}\n'.encode())
                                                                            
    for index in (0, 1, 2):
        for name, error, change in (
                ('BOM', 'INPUT_ASCII', lambda x: b'\xef\xbb\xbf' + x),
                ('NUL', 'INPUT_ASCII', lambda x: b'\x00' + x),
                ('space', 'INPUT_SPACING', lambda x: x.replace(b' ', b'  ', 1)),
                ('tab', 'INPUT_SPACING', lambda x: x.replace(b' ', b'\t', 1)),
                ('empty', 'INPUT_EMPTY_LINE', lambda x: b'\n'),
                ('CR', 'INPUT_CR', lambda x: x[:-1] + b'\r'),
                ('tag', 'INPUT_TAG', lambda x: b'X' + x[1:]),
                ('limit', 'INPUT_ARITY', lambda x: b'X' * 2049 + b'\n')):
            damaged = glines[:]
            damaged[index] = change(damaged[index])
            add(f'guard-row{index}-{name}', error, b''.join(damaged))
    for calls in (0, 17):
        add('guard0-calls' + str(calls), 'INPUT_OPCOUNT', f'GUARD13A 1\nG 1 0 0 {calls}\n'.encode())
    for kind in (100, 101, 102):
        for mode in (0, 2):
            words = list(point_call()[1]) if kind == 100 else [0] * 64
            words[0], words[1] = mode, 1
            if kind == 102:
                words[25] = 0x3f800000
            add(f'guard-helper{kind}-mode{mode}', 'INPUT_MODE', encode([], guard=(kind, words)))
                                                                         
                                                                     
    main_prefix = b''.join(encode([op, op]).splitlines(keepends=True)[:3])
    guard_prefix = b''.join(encode([op, op], guard=(0, (0,) * 64)).splitlines(keepends=True)[:4])
    expected = render([('GUARD13A', (1,)), ('G', (1, 0, 0, 2)), ('GA', (1, *((0,) * 64))),
                       ('CASE', (1, 2)), *normative_operation()])
    for definition in negative_definitions():
        if definition['after']:
            m.require(definition['data_C'].startswith(main_prefix), 'guard after-O preparation prefix')
            add('guard-' + definition['name'], definition['error'],
                guard_prefix + definition['data_C'][len(main_prefix):], expected)
    a = list(op[1]); a[53:55] = [1, 1]
                                                                             
    traced = (0, tuple(a))
    trace_prefix = render([('GUARD13A', (1,)), ('G', (1, 0, 0, 2)),
                           ('GA', (1, *((0,) * 64))), ('CASE', (1, 2)),
                           *normative_trace_operation(tuple(a))])
    add('guard-two-traces', 'INPUT_OPCOUNT', encode([traced, traced], guard=(0, (0,) * 64)), trace_prefix)
    one = encode([op], guard=(0, (0,) * 64))
    one_prefix = render([('GUARD13A', (1,)), ('G', (1, 0, 0, 1)), ('GA', (1, *((0,) * 64))),
                           ('CASE', (1, 1)), *normative_operation(), ('ENDCASE', (1,))])
                                                                                   
    for suffix in (b'\n', b'X', b'\x00', b'\r\n'):
        add('guard-trailing-' + suffix.hex(), 'INPUT_TRAILING_DATA', one + suffix, one_prefix)
    return result


class Runtime:
    def __init__(self, out):
        self.out = out
        self.full_controls = {}
        run = os.environ.get('GITHUB_RUN_ID', 'lokalny') + '_' + os.environ.get('GITHUB_RUN_ATTEMPT', '1')
        self.first_half = ROOT / 'RESULT-PORT13' / run
        receipt = self.first_half / 'manifest.json'
        binaries = json.loads(receipt.read_text(encoding='utf-8')).get('binaries', {}) if receipt.is_file() else {}
        self.paths = {'C': Path(os.environ.get('LANCUCHY_C_R_BIN', binaries.get('R', out / 'c13a-R-bin'))),
                      'C_D': Path(os.environ.get('LANCUCHY_C_D_BIN', binaries.get('D', out / 'c13a-D-bin'))),
                      'D': Path(os.environ.get('LANCUCHY_D_BIN', binaries.get('duckling', out / 'duckling-lancuchy-bin')))}

    def compiler(self):
        if os.environ.get('LANCUCHY_DUCKC'):
            return Path(os.environ['LANCUCHY_DUCKC'])
        receipt = self.first_half / ('duckling-build.json' if self.first_half.name in ('13b', '13c') else '13a/duckling-build.json')
        if receipt.is_file():
            return Path(json.loads(receipt.read_text(encoding='utf-8'))['argv'][0])
        return Path('missing-official-native-duckc')

    def run(self, side, data, executable=None):
        path = Path(executable) if executable else self.paths[side]
        if not sys.platform.startswith('linux') or not path.is_file():
            raise ValueError('Missing Linux native binary ' + str(path))
        with tempfile.TemporaryDirectory(prefix='.13a-input-', dir=self.out) as folder:
            source = Path(folder) / 'input.csv'
            source.write_bytes(data)
            command = [str(path), str(source)] if side.startswith('C') else [str(path)]
            attempts = []
            for attempt in range(2):
                started = time.monotonic()
                try:
                    process = subprocess.run(command, input=data if side == 'D' else None,
                                             capture_output=True, timeout=60)
                    meta = {'code': process.returncode, 'seconds': time.monotonic() - started,
                            'argv': command, 'input_sha256': hashlib.sha256(data).hexdigest(),
                            'binary_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'attempts': attempts}
                    return process.returncode, process.stdout, process.stderr, meta
                except subprocess.TimeoutExpired:
                    attempts.append({'attempt': attempt + 1, 'timeout': True, 'seconds': time.monotonic() - started})
            raise ValueError('Two isolated native timeouts; not a mutation kill: ' + json.dumps(attempts))


def first_difference(left, right):
    a, c = left.splitlines(), right.splitlines()
    for i in range(max(len(a), len(c))):
        x, y = a[i] if i < len(a) else b'', c[i] if i < len(c) else b''
        if x != y:
            return {'line': i + 1, 'baseline': x[:2048].decode('ascii', errors='replace'),
                    'actual': y[:2048].decode('ascii', errors='replace')}
    return None


def guard_stage(runtime):
    rows = []
    for definition in guard_definitions():
        row = {'name': definition['name'], 'sides': {}, 'ok': False}
        outputs = {}
        for side in ('C', 'D'):
            data = encode([], side == 'D', guard=(definition['kind'], definition['a']))
            try:
                code, stdout, stderr, meta = runtime.run(side, data)
                m.require(code == 0 and stderr == b'', 'guard process exit/stderr')
                checked = m.validate(stdout, data, decimal=side == 'D')
                row['sides'][side] = {'ok': True, 'run': meta, 'model': checked}
                outputs[side] = stdout
            except Exception as exc:
                row['sides'][side] = {'ok': False, 'error': str(exc)}
        row['ok'] = len(outputs) == 2 and outputs['C'] == outputs['D']
        if len(outputs) == 2:
            row['difference'] = first_difference(outputs['C'], outputs['D'])
        rows.append(row)
    return rows


def negative_stage(runtime):
    rows = []
                                                                              
    op = normative_operation()
    prefix = render([('PORT13A', ('R', 1)), ('CASE', (1, 2)), *op])
    for definition in [*negative_definitions(), *supplemental_negatives()]:
        row = {'name': definition['name'], 'error': definition['error'], 'sides': {}}
        for side in ('C', 'D'):
            data = definition['data_C'] if side == 'C' else decimal_negative(definition['data_C'])
            try:
                code, stdout, stderr, meta = runtime.run(side, data)
                expected = prefix if definition['after'] else b''
                                                                               
                                                                             
                if not definition['after'] and data.startswith(b'PORT13A R 1\nC 1 1\n'):
                    expected = b'PORT13A R 1\nCASE 1 1\n'
                if definition['error'] == 'INPUT_TRAILING_DATA':
                    expected = render([('PORT13A', ('R', 1)), ('CASE', (1, 1)), *op, ('ENDCASE', (1,))])
                if 'expected' in definition:
                    expected = definition['expected']
                ok = code == 2 and stderr == ('PORT13A: ' + definition['error'] + '\n').encode() and stdout == expected
                row['sides'][side] = {'ok': ok, 'run': meta, 'stdout_bytes': len(stdout),
                                      'stderr': stderr[:2048].decode('ascii', errors='replace'),
                                      'difference': first_difference(expected, stdout)}
            except Exception as exc:
                row['sides'][side] = {'ok': False, 'error': str(exc)}
        row['ok'] = all(r['ok'] for r in row['sides'].values())
        rows.append(row)
    return rows


def parser_reachability(rows):
    pass                                                                       
    names = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))['parserOdmowy']
    absent = {
        'INPUT_REGISTER_RANGE': 'Only kind0/1/2 and G100..103; no register fields or lookup.',
        'INPUT_REGISTER_UNINITIALIZED': 'No register lookup in PORT13A/GUARD13A.',
        'INPUT_REGISTER_COLLISION': 'No register allocation in PORT13A/GUARD13A.',
        'INPUT_ENUM': 'Distance bools/mode have BOOL/MODE; proxy kind and Gkind use OPCODE; no enum field.',
        'INPUT_POINT': 'Points are ai payload; no separate P13B input row in 13a.',
        'INPUT_MATERIAL': 'No material or U13B input row in 13a.',
        'INPUT_POPULATION': '128 cases: 112*32+16*1=3600<4096; GUARD<=16; no world population.',
        'INPUT_COPY': 'No saved-copy input selector; G103 owns two local value copies.',
        'INPUT_FIXTURE_MANIFOLD': 'No COMPONENT51/manifold fixture in 13a.',
        'INPUT_CAPTURE_UNCLOSED': 'No capture open/close operations in 13a.',
    }
    result = []
    for index, name in enumerate(names, 1):
        controls = [r for r in rows if r['error'] == name]
        reachable = name not in absent
        good = bool(controls) and all(r['ok'] for r in controls)
        result.append({'id': f'F13-{index:02}', 'error': name, 'reachable': reachable,
                       'proof': absent.get(name, 'PORT13A O/preflight or framing; GUARD G/GA; actual named controls below'),
                       'controls': [r['name'] for r in controls],
                       'both_parsers_ok': good if reachable else None,
                       'ok': good if reachable else not controls})
    return result


def positive_parser_stage(runtime):
    rows = []
    data = encode([point_call()])
    expected = render([('PORT13A', ('R', 1)), ('CASE', (1, 1)), *normative_operation(),
                       ('ENDCASE', (1,)), ('END', (1,))])
    for name, variant in (('CRLF', data.replace(b'\n', b'\r\n')), ('complete-EOF', data[:-1])):
        row = {'name': name, 'sides': {}}
        for side in ('C', 'D'):
            try:
                control = decimal_negative(variant) if side == 'D' else variant
                code, stdout, stderr, meta = runtime.run(side, control)
                row['sides'][side] = {'ok': code == 0 and stderr == b'' and stdout == expected, 'run': meta,
                                       'difference': first_difference(expected, stdout)}
            except Exception as exc:
                row['sides'][side] = {'ok': False, 'error': str(exc)}
        row['ok'] = all(s['ok'] for s in row['sides'].values())
        rows.append(row)
                                                                             
    traced = list(point_call()[1]); traced[53:55] = [1, 1]
    data = encode([point_call(), (0, tuple(traced))], guard=(0, (0,) * 64))
    expected = render([('GUARD13A', (1,)), ('G', (1, 0, 0, 2)),
                       ('GA', (1, *((0,) * 64))), ('CASE', (1, 2)),
                       *normative_operation(), *normative_trace_operation(tuple(traced), seq=2),
                       ('ENDCASE', (1,)), ('END', (1,))])
    row = {'name': 'GUARD-two-O-one-trace-legal', 'sides': {}}
    for side in ('C', 'D'):
        try:
            control = decimal_negative(data) if side == 'D' else data
            code, stdout, stderr, meta = runtime.run(side, control)
            row['sides'][side] = {'ok': code == 0 and stderr == b'' and stdout == expected,
                                   'run': meta, 'stderr': stderr.decode('ascii', errors='replace'),
                                   'difference': first_difference(expected, stdout)}
        except Exception as exc:
            row['sides'][side] = {'ok': False, 'error': str(exc)}
    row['ok'] = all(v['ok'] for v in row['sides'].values()); rows.append(row)
    return rows


def semantic_refusal_stage(runtime, generator):
    pass                                                                
    from dataclasses import replace
    rows = []
    for name, changes, warm in (
            ('cache-count4', {46: 4}, False), ('cache-active-index', {46: 1, 47: 1}, False),
            ('radius-u32max', {2: 0xffffffff}, False), ('radius-negative', {2: 0xbf800000}, False),
            ('point-last-used', {4: 0x7f800000}, False),
            ('warm-first-refusal', {2: 0xbf800000, 46: 1, 48: 71, 49: 72, 51: 81, 52: 82}, True)):
        first = list(point_call()[1]); first[0] = 1
        for field, value in changes.items(): first[field] = value
        second = list(point_call()[1]); second[0] = 1
        if warm:
            cases = [replace(c, ops=c.ops[:1]) for c in generator.cases(84)]
            descriptor = generator.cases(85)[-1]
            cases.append(replace(descriptor, ops=((0, *first), (0, *second))))
        else:
            cases = [replace(generator.cases(1)[0], ops=((0, *first), (0, *second)))]
        row = {'name': name, 'sides': {}}
        outputs = {}
        for side in ('C', 'D'):
            data = ''.join(generator.text(cases, 'R', side == 'D')).encode('ascii')
            try:
                code, stdout, stderr, meta = runtime.run(side, data)
                m.require(code == 0 and stderr == b'', 'semantic refusal process')
                checked = m.validate(stdout, data, decimal=side == 'D')
                outputs[side] = stdout
                row['sides'][side] = {'ok': True, 'run': meta, 'model': checked}
            except Exception as exc:
                row['sides'][side] = {'ok': False, 'reason': str(exc)}
        row['ok'] = len(outputs) == 2 and outputs['C'] == outputs['D']
        row['difference'] = first_difference(outputs['C'], outputs['D']) if len(outputs) == 2 else None
        rows.append(row)
    return rows


def full_stage(runtime, generator):
    pass                                                                       
    cases = generator.cases(128)
    outputs = {}
    result = {'profiles': {}, 'witnesses': [], 'case_observations': {}, 'ok': False}
    for profile in ('R', 'D'):
        sides = {}
        for side in ('C', 'D'):
            data = ''.join(generator.text(cases, profile, side == 'D')).encode('ascii')
            try:
                code, stdout, stderr, meta = runtime.run('C_D' if side == 'C' and profile == 'D' else side, data)
                m.require(code == 0 and stderr == b'', profile + '/' + side + ' exit/stderr')
                checked = m.validate(stdout, data, decimal=side == 'D')
                sides[side] = {'ok': True, 'run': meta, 'model': checked, 'bytes': len(stdout),
                               'sha256': hashlib.sha256(stdout).hexdigest()}
                outputs[profile, side] = stdout
                runtime.full_controls[profile, side] = {'data': data, 'stdout': stdout, 'run': meta}
            except Exception as exc:
                sides[side] = {'ok': False, 'reason': str(exc)}
        complete = all(s['ok'] for s in sides.values())
        difference = first_difference(outputs[profile, 'C'], outputs[profile, 'D']) if complete else None
        result['profiles'][profile] = {'sides': sides, 'equal': complete and difference is None, 'difference': difference}
    result['projection'] = {side: ('R', side) in outputs and ('D', side) in outputs
                            and m.projection(outputs['R', side]) == m.projection(outputs['D', side])
                            for side in ('C', 'D')}
    result['ok'] = all(r['equal'] for r in result['profiles'].values()) and all(result['projection'].values())
    for profile in ('R', 'D'):
        observations = {}
        for tag, values in (m.parse(line) for line in outputs.get((profile, 'C'), b'').splitlines(keepends=True)):
            if tag == 'CASE':
                observations[values[0]] = {'calls_expected': values[1], 'calls': 0, 'kinds': set(), 'statuses': set(),
                                          'max_supports': 0, 'trace_slots': 0, 'trace_vertices': 0,
                                          'active_undefined_a': 0, 'complete': False}
            elif tag == 'ENDCASE':
                observations[values[0]]['complete'] = True
            elif tag in ('E13A', 'A13', 'D13A', 'K13A', 'T13A', 'V13A'):
                row = observations[values[0]]
                if tag == 'E13A':
                    row['calls'] += 1
                    row['kinds'].add(values[2])
                elif tag == 'A13':
                    row['statuses'].add((values[2], values[3]))
                elif tag == 'D13A':
                    row['max_supports'] = max(row['max_supports'], values[9])
                    row.setdefault('first_D_H', [f'{v:08x}' for v in values[2:]])
                    row['last_D_H'] = [f'{v:08x}' for v in values[2:]]
                elif tag == 'K13A':
                    row.setdefault('first_K_H', [f'{v:08x}' for v in values[2:]])
                    row['last_K_H'] = [f'{v:08x}' for v in values[2:]]
                elif tag == 'T13A':
                    row['trace_slots'] += 1
                elif tag == 'V13A':
                    row['trace_vertices'] += 1
                    row['active_undefined_a'] += values[4] == 0
        for row in observations.values():
            row['kinds'], row['statuses'] = sorted(row['kinds']), sorted(row['statuses'])
        result['case_observations'][profile] = observations
                                                                            
    operations = {(case.id, seq): row for case in cases for seq, row in enumerate(case.ops, 1)}
    input_words = None
    for tag, values in (m.parse(line) for line in outputs.get(('D', 'C'), b'').splitlines(keepends=True)):
        if tag == 'E13A':
            input_words = values[3:] if values[2] == 0 else None
        elif tag == 'KI13' and input_words is not None:
            ident, seq = values[:2]
            result['witnesses'].append({'case': ident, 'seq': seq,
                                        'input_sha256': hashlib.sha256((' '.join(f'{v:08x}' for v in operations[ident, seq])).encode()).hexdigest(),
                                        'KI_H': [f'{v:08x}' for v in values[2:]], 'mode': input_words[0],
                                        'first_solve': b.initial_predicates(input_words, values[2:])})
        elif tag in ('D13A', 'K13A') and result['witnesses']:
            observed = result['witnesses'][-1]
            if (observed['case'], observed['seq']) == values[:2]:
                observed['D_H' if tag == 'D13A' else 'K_H'] = [f'{v:08x}' for v in values[2:]]
    result['constructor_data'] = b.constructor_data(generator, guard_definitions())
    result['checked_constructor_calls'] = [
        {'case': case.id, 'seq': seq, 'kind': kind, 'mode': words[0],
         'status': m.checked_status(kind, words), 'observed_by': 'full C/D input echoes and independently validated A/P records'}
        for case in cases for seq, (kind, *words) in enumerate(case.ops, 1)
        if kind in (1, 2) and words[0] == 1]
                                                                                
    return result, cases


def mutation_stage(runtime, generator, bindings_path, full_result, out, only_ids=None):
    pass                                                                       

                                                                              
                                                                               
       
    manifest = json.loads(bindings_path.read_text(encoding='utf-8'))
    m.require(manifest.get('anchor_owner') == 'T-13a-2a', 'Anchor binding profile mismatch')
    recipes = manifest.get('recipes', [])
    m.require(recipes and len({r['id'] for r in recipes}) == len(recipes), 'empty/duplicate mutation recipes')
    if only_ids is not None:
        m.require(set(only_ids).issubset({r['id'] for r in recipes}), 'retry must use the same existing bound recipe ids')
        recipes = [r for r in recipes if r['id'] in only_ids]
        m.require(bool(recipes), 'empty native retry is not success')
    duckc = runtime.compiler()
    m.require(sys.platform.startswith('linux') and duckc.is_file(), 'existing official native duckc required')
    driver = ROOT / 'silnik/port/lancuchy.dk'
    m.require(driver.is_file() and full_result['ok'], 'healthy full native baseline required before mutations')
    guards = {r['name']: r for r in guard_definitions()}
    receipts = []
    with tempfile.TemporaryDirectory(prefix='.13a-mutants-', dir=out) as directory:
        directory = Path(directory)
        physics = directory / 'fizyka'
        shutil.copytree(ROOT / 'silnik/fizyka', physics)
        for recipe in recipes:
            receipt = {'id': recipe['id'], 'requirement': recipe['requirement'],
                       'clean': False, 'detected': False, 'native_executed': False,
                       'baseline_ok': False, 'single_hit': False, 'anchor_owner': manifest['anchor_owner'],
                       'port': recipe.get('source', '') + ':' + str(recipe.get('line', ''))}
            path = (ROOT / recipe['source']).resolve()
            changed = None
            original = None
            try:
                m.require(recipe['source'].startswith('silnik/fizyka/') and path.resolve().is_relative_to((ROOT / 'silnik/fizyka').resolve()), 'mutations may alter product physics only')
                changed = physics / path.relative_to((ROOT / 'silnik/fizyka').resolve())
                original = path.read_text(encoding='utf-8')
                m.require(hashlib.sha256(path.read_bytes()).hexdigest() == recipe['source_sha256'], 'Stale source-bound anchor SHA')
                anchor = recipe['anchor']
                m.require(anchor and original.count(anchor) == 1, 'mutation anchor is not exactly one actual hit')
                receipt['single_hit'] = True
                profile = recipe.get('profile', 'R')
                main_control = profile == 'D' or (85 <= recipe.get('case', 0) <= 88 and recipe.get('seq', 1) > 1)
                guard_name = recipe.get('guard') or (recipe['requirement'] if recipe['requirement'] in guards else None)
                if guard_name:
                    fixture = guards[guard_name]
                    controls = [(False, encode([], guard=(fixture['kind'], fixture['a']))),
                                (True, encode([], True, guard=(fixture['kind'], fixture['a'])))]
                elif main_control:
                                                                            
                                                                        
                    prefix = generator.cases(recipe['case'])
                    controls = [(False, ''.join(generator.text(prefix, profile, False)).encode('ascii')),
                                (True, ''.join(generator.text(prefix, profile, True)).encode('ascii'))]
                else:
                    case = next(c for c in generator.cases(128) if c.id == recipe['case'])
                    op = case.ops[recipe.get('seq', 1) - 1]
                    controls = [(False, encode([(op[0], tuple(op[1:]))], guard=(0, (0,) * 64))),
                                (True, encode([(op[0], tuple(op[1:]))], True, guard=(0, (0,) * 64)))]
                base_outputs = {}
                for decimal, data in controls:
                    side = 'D' if decimal else 'C'
                    code, stdout, stderr, meta = runtime.run('C_D' if side == 'C' and profile == 'D' else side, data)
                    m.require(code == 0 and stderr == b'', 'mutation baseline native process')
                    m.validate(stdout, data, decimal=decimal)
                    base_outputs[side] = stdout
                    receipt['baseline_' + side] = meta
                m.require(base_outputs['C'] == base_outputs['D'], 'mutation baseline C/D differs')
                receipt['baseline_ok'] = True
                changed.write_text(original.replace(anchor, recipe['replacement'], 1), encoding='utf-8')
                artifacts = directory / 'build'
                config = {'packages': [{'id': 'fizyka', 'name': 'fizyka', 'path': str(physics)},
                                        {'id': 'probe', 'name': 'probe', 'path': str(driver), 'dependencies': [{'id': 'fizyka'}]}],
                          'tasks': [{'package': 'fizyka', 'strategy': 'lib', 'output_file': 'libfizyka.a'},
                                    {'package': 'probe', 'strategy': 'native', 'output_file': 'probe',
                                     'linking_options': {'additional_link_options': [str(artifacts / 'libfizyka.a'), '-lm'],
                                                         'link_c_standard_library': True}}]}
                config_path = directory / 'manifest.json'
                config_path.write_text(json.dumps(config), encoding='utf-8')
                start = time.monotonic()
                timeouts = []
                for attempt in range(2):
                    try:
                        compiled = subprocess.run([str(duckc), 'compile_packages', str(config_path), '-a', str(artifacts), '-O', '0'],
                                                  capture_output=True, timeout=180)
                        break
                    except subprocess.TimeoutExpired:
                        timeouts.append({'attempt': attempt + 1, 'timeout': True})
                else:
                    raise ValueError('Two isolated build timeouts; not a kill: ' + json.dumps(timeouts))
                receipt['build'] = {'code': compiled.returncode, 'seconds': time.monotonic() - start,
                                    'stderr': compiled.stderr[-8192:].decode(errors='replace'), 'timeouts': timeouts}
                m.require(compiled.returncode == 0, 'mutation build failure is not a kill')
                binaries = [p for p in artifacts.rglob('*') if p.is_file() and os.access(p, os.X_OK)
                            and p.read_bytes()[:4] == b'\x7fELF']
                m.require(len(binaries) == 1, 'one native mutation executable required')
                candidates = [(controls[1][1], base_outputs['D'], main_control,
                               recipe.get('case') if main_control else 1, False, profile)]
                                                                          
                                                                               
                                                                                
                if not guard_name:
                    full_control = runtime.full_controls[profile, 'D']
                    if full_control['data'] != candidates[0][0]:
                        candidates.append((full_control['data'], full_control['stdout'], True, 128, True, profile))
                    if profile == 'R':
                        debug_control = runtime.full_controls['D', 'D']
                        candidates.append((debug_control['data'], debug_control['stdout'], True, 128, True, 'D'))
                receipt['attempts'] = []
                selected = None
                for data, baseline, main, expected_n, reused, observed_profile in candidates:
                    attempt = {'full_baseline_reused': reused, 'main_control': main, 'profile': observed_profile, 'N': expected_n}
                    try:
                        code, stdout, stderr, meta = runtime.run('D', data, executable=binaries[0])
                        receipt['native_executed'] = True
                        attempt['run'] = meta
                        m.require(code == 0 and stderr == b'', 'mutation panic/exit/stderr is not a kill')
                        parsed = [m.parse(line) for line in stdout.splitlines(keepends=True)]
                        m.require(parsed and parsed[-1] == ('END', (expected_n,)), 'mutation truncated result')
                                                                                
                                                                                
                                                                                
                        difference_hint = first_difference(baseline, stdout)
                        prefix_n = None
                        if main and expected_n == 128 and difference_hint:
                            try:
                                hint_tag, hint_words = m.parse(difference_hint['actual'] + '\n')
                                first_unsafe = next((v[0] for t, v in parsed if t == 'D13A' and v[9] >= 20), None)
                                if hint_tag in ('D13A', 'K13A', 'T13A', 'V13A', 'ZA13') and first_unsafe and 1 <= hint_words[0] < first_unsafe:
                                    prefix_n = hint_words[0]
                            except ValueError:
                                pass
                        if prefix_n is not None:
                            prefix_cases = generator.cases(prefix_n)
                            healthy = {}
                            prefix_data = {}
                            for prefix_side in ('C', 'D'):
                                pd = ''.join(generator.text(prefix_cases, observed_profile, prefix_side == 'D')).encode('ascii')
                                pc, po, pe, pm = runtime.run('C_D' if prefix_side == 'C' and observed_profile == 'D' else prefix_side, pd)
                                m.require(pc == 0 and pe == b'', 'frozen prefix baseline exit/stderr')
                                m.validate(po, pd, decimal=prefix_side == 'D')
                                healthy[prefix_side] = po
                                prefix_data[prefix_side] = pd
                                attempt.setdefault('prefix_baselines', {})[prefix_side] = pm
                            m.require(healthy['C'] == healthy['D'], 'frozen prefix baseline C/D differs')
                            candidates.append((prefix_data['D'], healthy['D'], True, prefix_n, False, observed_profile))
                            attempt['added_frozen_prefix_N'] = prefix_n
                        for tag, values in parsed:
                            if tag == 'D13A':
                                m.require(all(__import__('math').isfinite(m.number(v)) for v in values[2:9]), 'mutation nonfinite result')
                                m.require(values[9] < 20, 'mutation reached20: independent proof of all read weights still required; not a kill')
                            if tag == 'V13A':
                                m.require(values[4] in (0, 1) and (values[4] or values[11] == 0), 'mutation undefined a read')
                                m.require(all(__import__('math').isfinite(m.number(v)) for v in values[5:11])
                                          and (not values[4] or __import__('math').isfinite(m.number(values[11]))), 'mutation nonfinite trace field')
                        difference = first_difference(baseline, stdout)
                        attempt.update(clean=True, detected=difference is not None, difference=difference)
                        selected = (data, main, meta, difference, reused, observed_profile, expected_n)
                    except Exception as exc:
                        attempt.update(clean=False, detected=False, error=str(exc))
                    receipt['attempts'].append(attempt)
                    if attempt.get('detected'):
                        break
                m.require(selected is not None, 'no clean native mutation result; see attempts')
                data, main_control, meta, difference, reused, observed_profile, selected_n = selected
                receipt['run'] = meta
                receipt['profile'] = observed_profile
                receipt['observed_control_N'] = selected_n
                for earlier in receipt['attempts']:
                    if earlier.get('added_frozen_prefix_N') == selected_n and earlier['profile'] == observed_profile:
                        receipt['baseline_C'] = earlier['prefix_baselines']['C']
                        receipt['baseline_D'] = earlier['prefix_baselines']['D']
                        receipt['frozen_prefix_baseline_revalidated'] = True
                if reused:
                    receipt['baseline_C'] = runtime.full_controls[observed_profile, 'C']['run']
                    receipt['baseline_D'] = runtime.full_controls[observed_profile, 'D']['run']
                    receipt['full_baseline_reused'] = True
                receipt['difference'] = difference
                receipt['clean'] = True
                receipt['detected'] = difference is not None
                observed_case, observed_seq = recipe.get('case'), recipe.get('seq', 1)
                if guard_name:
                    observed_case, observed_seq = None, 0
                if main_control and difference:
                    for line in (difference['baseline'], difference['actual']):
                        try:
                            tag, words = m.parse(line + '\n')
                            if tag in ('E13A', 'A13', 'KI13', 'D13A', 'K13A', 'P13A', 'T13A', 'V13A', 'ZA13'):
                                observed_case, observed_seq = words[:2]
                                break
                        except ValueError:
                            pass
                predicates = None if guard_name else next((r['first_solve'] for r in full_result['witnesses']
                                   if (r['case'], r['seq']) == (observed_case, observed_seq)), None)
                receipt['witness'] = {'guard': guard_name, 'case': observed_case, 'seq': observed_seq,
                                       'requested_case': recipe.get('case'), 'requested_seq': recipe.get('seq', 1),
                                       'main_control': main_control, 'first_solve': predicates,
                                       'input_sha256': hashlib.sha256(data).hexdigest()}
            except Exception as exc:
                receipt['error'] = str(exc)
            finally:
                if changed is not None and changed.is_file() and original is not None:
                    changed.write_text(original, encoding='utf-8')
            receipts.append(receipt)
            (out / '13a-mutations.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(recipe['id'] + ': ' + ('NATIVE_DETECTED' if receipt['detected'] else 'GAP'), flush=True)
    return receipts


def op13b(opcode, *values, points=(), materials=()):
    pass                                                                       
    m.require(len(values) <= 64, '13b O width')
    return {'opcode': opcode, 'a': tuple(values) + (0,) * (64 - len(values)),
            'points': tuple(tuple(p) for p in points),
            'materials': tuple(tuple(u) for u in materials)}


def chain_op13b(points=None, materials=None, closed=False, target=0):
    if points is None:
        points = [(2., 0.), (1., 0.), (-1., 0.), (-2., 0.)]
    points = [tuple(map(m.bits, p)) for p in points]
    if materials is None:
        materials = [(m.bits(.6), 0, 0, 0, 0, 0)]
    return op13b(100, 1, 0, 0, target, len(points), int(closed), len(materials),
                 0, 0, 0, 1, 0, 0xffffffff, 0xffffffff, 0, 0,
                 points=points, materials=materials)


def setup13b():
                                                                     
    return [op13b(0, 0, 0, 0, m.bits(100.)),
            op13b(2, 0, 0, 0, 0, 0, m.bits(1.)), chain_op13b()]


def guard_definitions13b():
    pass                                                                   

                                                                              
                                                                         
       
    manifest = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    descriptors = [r for r in manifest['guardPrzypadki'] if r['czesc'] == '13b']
    m.require(len(descriptors) == 96 and len({r['id'] for r in descriptors}) == 96,
              'all 96 frozen guard ids required')
    controls = {'GB4-GHOST-X', 'GB4-GHOST-Y', 'GB4-LOOP-REPEAT', 'GB4-DERIVED-ORIENT'}
    m.require({r['id'] for r in descriptors if not r['liczonyJakoZabicie']} == controls,
              '13b control refusals are not mutation kills')
    result = []
    geometries = {
        'GB4-DISTANCE': ([(0, 0), (2, 0), (2, 2), (0, .0025)], False),
        'GB4-SLOP': ([(0, 0), (2, 0), (2, 2), (0, m.f32(.005))], False),
        'GB4-LOOP-REPEAT': ([(0, 0), (2, 0), (2, 2), (0, 0)], True),
        'GB4-DERIVED-D2': ([(0, 0), (1.5e19, 0), (1.5e19, 1.5e19), (0, 1.5e19)], True),
        'GB4-DERIVED-ORIENT': ([(0, 0), (1.5e19, 0), (1.5e19, 1.5e19), (0, 1.5e19)], True),
        'GB5-CROSS': ([(-2, -1), (2, 1), (-2, 1), (2, -1)], False),
        'GB5-COLLINEAR': ([(0, 0), (4, 0), (4, 2), (1, 0), (3, 0)], False),
        'GB5-TOUCH': ([(0, 0), (4, 0), (4, 2), (2, 0), (1, 2)], False),
        'GB5-ADJACENT': ([(0, 0), (3, 0), (1, 0), (1, 2)], False),
        'GB5-CLOSE': ([(0, 0), (4, 0), (0, 4), (4, 4)], True),
        'GB5-ALLOW-STRAIGHT': ([(0, 0), (1, 0), (2, 0), (3, 0)], False),
    }
    for descriptor in descriptors:
        name, kind = descriptor['id'], descriptor['Gkind']
        ga, operations, points, materials = [0] * 64, [], (), ()
        status, reason, helper = 0, 0, None
        seed, gap, assertions = 0, None, []
        if kind == 200:
            call = chain_op13b()
            if name == 'GB3-N3':
                call = chain_op13b([(0, 0), (1, 0), (2, 0)])
            elif name == 'GB3-MCOUNT':
                call = chain_op13b(materials=[(m.bits(.6), 0, 0, 0, 0, 0)] * 2)
            elif name.startswith('GB3-MAT-'):
                material = [m.bits(.6), 0, 0, 0, 0, 0]
                field = {'FRICTION': 0, 'RESTITUTION': 1, 'ROLLING': 2, 'TANGENT': 3}[name.split('-')[2]]
                material[field] = 0x7f800000 if name.endswith('FINITE') else m.bits(-1.)
                call = chain_op13b(materials=[(m.bits(.6), 0, 0, 0, 0, 0)] * 3 + [tuple(material)])
            elif name.startswith('GB4-GHOST-'):
                call = chain_op13b()
                pp = list(call['points'])
                pp[0] = (0x7f800000, 0) if name.endswith('X') else (m.bits(2.), 0x7f800000)
                call['points'] = tuple(pp)
            elif name in geometries:
                pp, closed = geometries[name]
                call = chain_op13b(pp, closed=closed)
            elif name.startswith('GB6-CREATE-'):
                                                                            
                                                                           
                kind = 0
                operations = setup13b()[:2]
                body = list(operations[1]['a'])
                body[2] = 2 if name.endswith('DYNAMIC') else 1
                operations[1]['a'] = tuple(body)
                operations.append(call)
                status, reason = 5, 80
            else:
                raise ValueError('Unmapped frozen G200 ' + name)
            ga, points, materials = list(call['a']), call['points'], call['materials']
            if kind == 200:
                status, reason = m.description_status13b(ga, points, materials)
            else:
                ga, points, materials = [0] * 64, (), ()
            helper = 200 if kind == 200 else None
        elif kind == 203:
            ga[:5] = [1, 0, 0, int('RESTITUTION' in name),
                      0x7f800000 if name.endswith('FINITE') else m.bits(-1.)]
            helper, status = 203, 5
        elif kind in (218, 219, 281, 280):
            helper, status, reason = kind, 5, 80 if kind == 280 else 81
            if kind == 219:
                ga[2] = m.bits(2.)
            elif kind == 280:
                ga[:5] = [0, 0, 1, 0, 2 if name.endswith('DYNAMIC') else 1]
            elif kind == 281:
                field = {'FRICTION': 0, 'RESTITUTION': 1, 'MATERIAL': 2, 'SURFACE': 3,
                         'FILTER': 4, 'CIRCLE': 5, 'CAPSULE': 6, 'SEGMENT': 7, 'POLYGON': 8}[name.split('-')[-1]]
                ga[:4] = [0, 0, 1, field]
                if field in (0, 1):
                    ga[4] = m.bits(.5)
                elif field == 2:
                    ga[4] = 0xfffffff9
                elif field == 3:
                    ga[4:10] = [m.bits(.5), m.bits(.25), m.bits(.125), m.bits(-.5), 0xfffffff9, 0x12345678]
                elif field == 4:
                    ga[4:9] = [1, 0x80000000, 0xffffffff, 0xffffffff, 0]
                elif field == 5:
                    ga[4:7] = [0, 0, m.bits(.5)]
                elif field == 6:
                    ga[4:9] = [m.bits(-1.), 0, m.bits(1.), 0, m.bits(.5)]
                elif field == 7:
                    ga[4:8] = [m.bits(-1.), 0, m.bits(1.), 0]
                else:
                    ga[4:12] = [3, 0, 0, 0, m.bits(1.), 0, 0, m.bits(1.)]
        elif kind in (300, 301, 303):
            helper, status, reason = kind, 7, 1
            if kind == 300:
                call = chain_op13b(target=1)
                                                                        
                ga = list(call['a'])
            elif kind == 301:
                ga[:3] = [1, 0, 0]
            else:
                subkind = int(name.rsplit('-', 1)[1])
                ga[:5] = [1, 0, 0, subkind, m.bits(.5) if subkind < 2 else 0xfffffff9]
            assertions.append('real preSolve12 on TWO CIRCLES, live chain on static B0; no patched lock bool')
        elif kind == 8:
            operations = setup13b()
            ga[:3] = [4, 0, 0]
            helper, status = 14, 1
            fields = {'OWNER-LOW': (1, 0), 'OWNER-HIGH': (2, 1),
                      'BIRTH-LOW': (3, 0), 'BIRTH-HIGH': (4, 1),
                      'OCCUPIED': (6, 0xffffffff), 'RANGE': (5, 1)}
            tail = name[4:]
            if tail in fields:
                ga[3:5] = fields[tail]
                if tail.startswith('OWNER'):
                    status = 2
            elif tail == 'WORLD':
                ga[:5] = [0, 0, 0, 3, 0]
                helper = 10
            elif tail == 'AFTER-BODY':
                operations.append(op13b(3, 0, 0))
            elif tail == 'AFTER-WORLD':
                operations.append(op13b(1, 0))
            else:
                raise ValueError('Unmapped status-only ' + name)
            seed = len(operations)
            if tail == 'RANGE':
                assertions += ['physical chain record slot1 exists; pool.nextIndex remains1; status-only before raw',
                               'also measure slot ffffffff as a refusal control, never an OOB mutation kill']
        elif kind == 12:
            helper = 112
            low, high, segments = {
                'GB7-PARTIAL': (0xfffffffc, 0xffffffff, 3),
                'GB7-EXACT': (0xfffffffb, 0xffffffff, 3),
                'GB7-EMPTY-MAX': (0xffffffff, 0xffffffff, 0),
                'GB7-CARRY': (0xffffffff, 0, 3),
            }[name]
            ga[:3] = [low, high, segments]
            status, _ = m.ticket_batch13b(low, high, segments)
            assertions.append('helper reservation is not a world snapshot; full refusal/next-smaller operation still needs G4 history')
        elif kind == 13:
            ga[:3] = [0x80000001, 0x8000, 0xffff]
            helper = 113
            assertions.append('Store/Load only; never lookup these high-bit raw values')
        elif kind == 0:
            operations = setup13b()
            if name.startswith('GB1-ROUTE-'):
                suffix = name[len('GB1-ROUTE-'):]
                route, failure = suffix.rsplit('-', 1)
                opcode = int(route.split('-')[0])
                if failure == 'WORLD':
                    operations.append(op13b(1, 0))
                    status = 1
                elif failure == 'OWNER':
                    operations.append(op13b(0, 1, 0, 0, m.bits(100.)))
                    status = 2
                else:
                    operations.append(op13b(3, 0, 0) if opcode == 100 else op13b(101, 1, 0, 0))
                    status = 1
                w = int(failure == 'OWNER')
                if opcode == 100:
                    call = chain_op13b(target=1)
                    aa = list(call['a']); aa[1] = w; call['a'] = tuple(aa)
                elif opcode == 103:
                    subkind = int(route.split('-')[1])
                    call = op13b(103, 1, w, 0, subkind, m.bits(.5) if subkind < 2 else 0xfffffff9)
                elif opcode == 106:
                    call = op13b(106, w, 0, 0)
                else:
                    call = op13b(opcode, 1, w, 0)
                operations.append(call)
                assertions.append('Life validation stops before invalid raw access; native probe not measured')
            elif name == 'GB5-ALLOW-TWO-CHAINS':
                operations = setup13b()[:2]
                operations += [chain_op13b([(x, 0) for x in (12, 10, 8, 6, 4, 2, 0, -2)]),
                               chain_op13b([(x, 0) for x in (2, 0, -2, -4, -6, -8, -10, -12)], target=1)]
            elif name == 'GB7-READ-CHAIN':
                operations += [op13b(102, 0, 0, 0, capacity) for capacity in (0, 1, 128)]
                operations.append(op13b(102, 1, 0, 0))
            elif name == 'GB7-PARENT':
                operations.append(op13b(104, 1, 0, 0))
            elif name == 'GB7-READ-SEGMENT':
                operations.append(op13b(105, 1, 0, 0))
            elif name == 'GB7-COPY':
                operations += [op13b(106, 0, 0, 0), op13b(107, 0)]
            elif name.startswith('GB8-INPUT-'):
                field = int(name.endswith('MATERIALS'))
                operations += [op13b(109, field, 0), op13b(109, field, 1)]
                assertions.append('compare world before release0, after mutation0, then release1; no crash-based kill')
            elif name in ('GB8-TWO-VIEWS', 'GB8-VIEW-AFTER-WORLD'):
                operations += [op13b(106, 0, 0, 0), op13b(106, 0, 0, 1)]
                if name.endswith('WORLD'):
                    operations.append(op13b(1, 0))
                operations += [op13b(108, 0, 0, 123), op13b(107, 1)]
                assertions.append('copy phases0=2 and1 differs; second copy and world unchanged')
            else:
                raise ValueError('Unmapped public guard ' + name)
            if name.startswith('GB7-'):
                assertions.append('all reads preserve lastIssued and next successful birth')
        else:
            raise ValueError('Unmapped frozen Gkind ' + str(kind))
        limit = 16 if name.startswith('GB6-CREATE-') else descriptor['opMax']
        m.require(len(operations) <= limit, name + ' accepted fixture opMax')
        result.append({**descriptor, 'kind': kind, 'ga': tuple(ga), 'seedAfterSeq': seed,
                       'operations': operations, 'points': points, 'materials': materials,
                       'expected_status': status, 'expected_reason': reason,
                       'helper': helper, 'assertions': assertions,
                       'control_only': name == 'GB5-ADJACENT' or not descriptor['liczonyJakoZabicie'],
                       'materialized': gap is None, 'gap': gap, 'native_verified': False})
    return result


def encode_guard13b(definition, decimal=False):
    pass                                                                   
    m.require(definition['materialized'], definition.get('gap'))
    word = str if decimal else lambda v: f'{v:08x}'
    lines = ['GUARD13B 1', 'G 1 %d %d %d' % (
        definition['kind'], definition['seedAfterSeq'], len(definition['operations'])),
        'GA 1 ' + ' '.join(map(word, definition['ga']))]
    def group(seq, points, materials):
        for tag, rows in (('P13B', points), ('U13B', materials)):
            for i, row in enumerate(rows):
                lines.append(f'{tag} 1 {seq} {i} ' + ' '.join(map(word, row)))
    if definition['kind'] == 200:
        group(0, definition['points'], definition['materials'])
    for seq, call in enumerate(definition['operations'], 1):
        lines.append(f'O {seq} {call['opcode']} ' + ' '.join(map(word, call['a'])))
        if call['opcode'] == 100:
            group(seq, call['points'], call['materials'])
    return ('\n'.join(lines) + '\n').encode('ascii')


def parser_reachability13b():
    manifest = json.loads((HERE / 'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    absent = {
        'INPUT_CACHE': '13b has no direct GJK/cache input; O51 is rejected by PHASE before fixture cache.',
        'INPUT_FIXTURE_MANIFOLD': 'No COMPONENT13B and no legal O51 manifold path in PORT/GUARD13B.',
        'INPUT_CAPTURE_UNCLOSED': 'No legal open-capture path in PORT/GUARD13B; O41..45 gives PHASE.',
    }
    routes = {
        'INPUT_POINT': 'O100/G200 P13B arity/id/seq/i',
        'INPUT_MATERIAL': 'O100/G200 U13B arity/id/seq/i',
        'INPUT_REGISTER_RANGE': '100 target ChainReg16',
        'INPUT_REGISTER_UNINITIALIZED': '101 before any chain create',
        'INPUT_REGISTER_COLLISION': '100 target already live',
        'INPUT_COPY': '107 before106,108 item range,109 no description/released input',
        'INPUT_ROTATION': 'inherited O4 rotation=(0,0)',
        'INPUT_PROFILE': 'PORT: positive31/32; GUARD: inherited raw body+preSolve83',
        'INPUT_PHASE': 'O41..45/51..53/64 are not public operations13b',
        'INPUT_POPULATION': 'Npoints/materials129 or third live world',
        'INPUT_MODE': '100.a0=2 before bool interpretation',
        'INPUT_N': 'first PORT13B/GUARD13B header only',
        'INPUT_ID': 'PORT C id; GUARD G/GA id (before first O)',
        'INPUT_OPCOUNT': 'PORT C count0/65; GUARD kind0 G count0/17 (before first O)',
    }
    rows = []
    for i, name in enumerate(manifest['parserOdmowy'], 1):
        row = {'id': f'F13-{i:02}', 'error': name, 'route': routes.get(name, '§9.2 lexical/framing/O field'),
               'sides': {'C': 'UNVERIFIED', 'D': 'UNVERIFIED'}}
        for profile in ('PORT13B', 'GUARD13B'):
            row[profile] = {'reachable': name not in absent,
                            'reason': absent.get(name), 'native_verified': False,
                            'after_legal_O': name not in absent and name != 'INPUT_N' and not (
                                profile == 'GUARD13B' and name in ('INPUT_ID', 'INPUT_OPCOUNT'))}
        if name in ('INPUT_ID', 'INPUT_OPCOUNT'):
            row['decision'] = ('ODBIOR 3c: GUARD ID/OPCOUNT only before O; repeated G/CASE after a '
                               'complete input is TRAILING_DATA. Late ID/OPCOUNT only in PUBLIC C2.')
        rows.append(row)
    m.require(len(rows) == 33, 'full F13 catalogue')
    return rows


def input13b(operations, decimal=False, profile='PORT13B'):
    pass                                                                         
    word = str if decimal else lambda v: f'{v:08x}'
    if profile == 'GUARD13B':
        definition = {'materialized': True, 'kind': 0, 'seedAfterSeq': 0,
                      'ga': (0,) * 64, 'operations': operations}
        return encode_guard13b(definition, decimal)
    m.require(profile == 'PORT13B', '13b control profile')
    lines = [f'PORT13B 1', f'C 1 {len(operations)}']
    for seq, call in enumerate(operations, 1):
        lines.append(f'O {seq} {call['opcode']} ' + ' '.join(map(word, call['a'])))
        if call['opcode'] == 100:
            for tag, rows in (('P13B', call['points']), ('U13B', call['materials'])):
                for i, values in enumerate(rows):
                    lines.append(f'{tag} 1 {seq} {i} ' + ' '.join(map(word, values)))
    return ('\n'.join(lines) + '\n').encode('ascii')


def negative_definitions13b():
    pass                                                                          

                                                                           
                                                                            
       
    result = []
    def add(profile, name, error, builder, prefix=False, prefix_kind='none'):
        result.append({'name': profile + '/' + name, 'profile': profile, 'error': error,
                       'after_legal_O': prefix, 'prefix_kind': prefix_kind,
                       'data_C': builder(False), 'data_D': builder(True),
                       'native_verified': False,
                       'expected_stderr': ('PORT13B: ' + error + '\n').encode('ascii')})
    for profile in ('PORT13B', 'GUARD13B'):
        control = [op13b(0, 0, 0, 0, m.bits(100.))]
        for label, malformed, error in (
            ('bom', lambda x: b'\xef\xbb\xbf' + x, 'INPUT_ASCII'),
            ('non-ascii', lambda x: b'\x80' + x, 'INPUT_ASCII'),
            ('nul', lambda x: b'\x00' + x, 'INPUT_ASCII'),
            ('del', lambda x: b'\x7f' + x, 'INPUT_ASCII'),
            ('double-space', lambda x: x.replace(b' ', b'  ', 1), 'INPUT_SPACING'),
            ('tab', lambda x: x.replace(b' ', b'\t', 1), 'INPUT_SPACING'),
            ('leading-space', lambda x: b' ' + x, 'INPUT_SPACING'),
            ('trailing-space', lambda x: x[:-1] + b' \n', 'INPUT_SPACING'),
            ('empty', lambda x: b'\n', 'INPUT_EMPTY_LINE'),
            ('bare-cr', lambda x: x[:-1] + b'\rX\n', 'INPUT_CR'),
            ('wrong-tag', lambda x: b'X' + x[1:], 'INPUT_TAG'),
        ):
            for after in (False, True):
                def build(decimal, after=after, malformed=malformed):
                    rows = input13b(setup13b() + [op13b(102, 1, 0, 0)], decimal, profile).splitlines(keepends=True)
                    at = max(i for i, x in enumerate(rows) if x.startswith(b'O ')) if after else 0
                    rows[at] = malformed(rows[at])
                    return b''.join(rows)
                add(profile, label + ('/after' if after else '/initial'), error, build, after,
                    'validated native setup snapshots' if after else 'bad first header: stdout0B')
        for n in ((0, 65) if profile == 'PORT13B' else (0, 2)):
            add(profile, f'N{n}', 'INPUT_N', lambda decimal, n=n: f'{profile} {n}\n'.encode())
        for count in ((0, 65) if profile == 'PORT13B' else (0, 17)):
            def build(decimal, count=count):
                if profile == 'PORT13B':
                    return f'PORT13B 1\nC 1 {count}\n'.encode()
                return (f'GUARD13B 1\nG 1 0 0 {count}\nGA 1 ' +
                        ' '.join(['0' if decimal else '00000000'] * 64) + '\n').encode()
            add(profile, f'opCount{count}', 'INPUT_OPCOUNT', build,
                prefix_kind='valid header emitted; no O yet')
                                                                           
                                                                              
        for extra in (False, True):
            setup = setup13b()
            if extra:
                setup.append(op13b(102, 1, 0, 0))
            last = len(setup) + 1
            tests = []
            tests.append(('register-range', 'INPUT_REGISTER_RANGE', chain_op13b(target=16)))
            tests.append(('register-uninitialized', 'INPUT_REGISTER_UNINITIALIZED', op13b(101, 1, 0, 1)))
            tests.append(('register-collision', 'INPUT_REGISTER_COLLISION', chain_op13b()))
            tests.append(('mode', 'INPUT_MODE', op13b(101, 2, 0, 0)))
            call = chain_op13b(); aa = list(call['a']); aa[5] = 2; call['a'] = tuple(aa)
            tests.append(('bool', 'INPUT_BOOL', call))
            tests.append(('enum', 'INPUT_ENUM', op13b(103, 1, 0, 0, 3, 0)))
            call = op13b(103, 1, 0, 0, 0, m.bits(.5)); aa = list(call['a']); aa[63] = 0x80000000; call['a'] = tuple(aa)
            tests.append(('unused-minus-zero', 'INPUT_UNUSED', call))
            tests.append(('raw-domain', 'INPUT_DOMAIN', op13b(103, 0, 0, 0, 0, m.bits(-1.))))
            tests.append(('rotation', 'INPUT_ROTATION', op13b(4, 0, 0, 0, 0, 0, 0)))
            tests.append(('phase', 'INPUT_PHASE', op13b(43, 0)))
            tests.append(('copy-uninitialized', 'INPUT_COPY', op13b(107, 0)))
            tests.append(('population-points129', 'INPUT_POPULATION', chain_op13b([(i, 0) for i in range(129)], target=1)))
            tests.append(('profile', 'INPUT_PROFILE', op13b(31, 0, m.bits(.125), 1) if profile == 'PORT13B' else
                          op13b(83, 0, 0, 0, 0, 2, 1)))
            for label, error, call in tests:
                add(profile, label + ('/extra-prefix' if extra else '/setup'), error,
                    lambda decimal, ops=setup + [call]: input13b(ops, decimal, profile), True,
                    'validated native setup + optional getter')
            for label, error in (('seq', 'INPUT_SEQ'), ('decimal', 'INPUT_DECIMAL'),
                                 ('opcode', 'INPUT_OPCODE'), ('arity-short', 'INPUT_ARITY'),
                                 ('arity-long', 'INPUT_ARITY'), ('arity-2049', 'INPUT_ARITY'),
                                 ('word', 'INPUT_WORD'), ('eof-incomplete', 'INPUT_EOF')):
                def build(decimal, label=label, setup=setup, last=last):
                    rows = input13b(setup + [op13b(102, 1, 0, 0)], decimal, profile).splitlines(keepends=True)
                    at = max(i for i, x in enumerate(rows) if x.startswith(b'O '))
                    fields = rows[at].split()
                    if label == 'seq': fields[1] = str(last + 1).encode()
                    elif label == 'decimal': fields[1] = b'0' + str(last).encode()
                    elif label == 'opcode': fields[2] = b'120'
                    elif label == 'arity-short': fields.pop()
                    elif label == 'arity-long': fields.append(b'0' if decimal else b'00000000')
                    elif label == 'arity-2049':
                        rows[at] = b'O ' + b'1' * 2047 + b'\n'; return b''.join(rows)
                    elif label == 'word': fields[3] = b'4294967296' if decimal else b'0000000A'
                    elif label == 'eof-incomplete':
                        rows[at] = b'O ' + str(last).encode() + b' 102 1'; return b''.join(rows[:at + 1])
                    rows[at] = b' '.join(fields) + b'\n'
                    return b''.join(rows)
                add(profile, label + ('/extra-prefix' if extra else '/setup'), error, build, True,
                    'validated native setup + optional getter')
                                                                            
                                                                            
        for tag, error in (('P13B', 'INPUT_POINT'), ('U13B', 'INPUT_MATERIAL')):
            for field in ('arity', 'id', 'seq', 'i', 'tag', 'word', 'eof'):
                def build(decimal, tag=tag, field=field):
                    rows = input13b(setup13b()[:2] + [chain_op13b()], decimal, profile).splitlines(keepends=True)
                    at = next(i for i, x in enumerate(rows) if x.startswith(tag.encode() + b' '))
                    fields = rows[at].split()
                    if field == 'arity': fields.pop()
                    elif field in ('id', 'seq', 'i'): fields[{'id': 1, 'seq': 2, 'i': 3}[field]] = b'9'
                    elif field == 'tag': fields[0] = b'X13B'
                    elif field == 'word': fields[4] = b'4294967296' if decimal else b'0000000A'
                    elif field == 'eof': return b''.join(rows[:at])
                    rows[at] = b' '.join(fields) + b'\n'
                    return b''.join(rows)
                code = {'tag': 'INPUT_TAG', 'word': 'INPUT_WORD', 'eof': 'INPUT_EOF'}.get(field, error)
                add(profile, tag + '/' + field, code, build, True,
                    'two legal O; no EP/EU echo until entire following group is valid')
        add(profile, 'EOF-no-next-O', 'INPUT_EOF',
            lambda decimal: input13b(control, decimal, profile).split(b'O ', 1)[0], False,
            'valid header/CASE only; no completed O')
        add(profile, 'trailing-LF', 'INPUT_TRAILING_DATA',
            lambda decimal: input13b(control, decimal, profile) + b'\n', True,
            'complete legal case, ENDCASE retained, no END after fatal trailing')
        if profile == 'GUARD13B':
            for suffix in (b'G 1 0 0 1\n', b'CASE 1 1\n'):
                add(profile, 'trailing-' + suffix.split()[0].decode(), 'INPUT_TRAILING_DATA',
                    lambda decimal, suffix=suffix: input13b(control, decimal, profile) + suffix,
                    True, 'ODBIOR 3c: second G/CASE is trailing, never late ID/OPCOUNT')
        def wrong_id(decimal):
            rows = input13b(control, decimal, profile).splitlines(keepends=True)
            at = 1
            fields = rows[at].split(); fields[1] = b'2'; rows[at] = b' '.join(fields) + b'\n'
            return b''.join(rows)
        add(profile, 'id-before-O', 'INPUT_ID', wrong_id, False, 'valid first header emitted')
        add(profile, 'copy-input-no-description', 'INPUT_COPY',
            lambda decimal: input13b(setup13b()[:2] + [op13b(109, 0, 1)], decimal, profile), True,
            'W/B setup without successful100')
        for selected in (0, 1):
            add(profile, 'copy-input-released-' + str(selected), 'INPUT_COPY',
                lambda decimal, selected=selected: input13b(setup13b() + [
                    op13b(109, selected, 0), op13b(109, selected, 1), op13b(109, selected, 1)], decimal, profile),
                True, 'separate release0 then release1; repeat use of released input')
        for item, slot, error in ((1, 123, 'INPUT_COPY'), (0, 0, 'INPUT_DOMAIN')):
            add(profile, f'copy-item{item}-slot{slot}', error,
                lambda decimal, item=item, slot=slot: input13b(setup13b() + [
                    op13b(106, 0, 0, 0), op13b(108, 0, item, slot)], decimal, profile),
                True, 'successful106; item range or equal-slot mutation')
        if profile == 'GUARD13B':
            fixture = next(r for r in guard_definitions13b() if r['id']=='GB5-ALLOW-STRAIGHT')
            for tag,diagnostic in (('P13B','INPUT_POINT'),('U13B','INPUT_MATERIAL')):
                for field in ('arity','id','seq','i','tag','word','eof'):
                    def build(decimal,tag=tag,field=field,fixture=fixture):
                        rows=encode_guard13b(fixture,decimal).splitlines(keepends=True)
                        at=next(i for i,row in enumerate(rows) if row.startswith(tag.encode()+b' '))
                        values=rows[at].split()
                        if field=='arity':values.pop()
                        elif field in ('id','seq','i'):values[{'id':1,'seq':2,'i':3}[field]]=b'9'
                        elif field=='tag':values[0]=b'X13B'
                        elif field=='word':values[4]=b'4294967296' if decimal else b'0000000A'
                        elif field=='eof':return b''.join(rows[:at])
                        rows[at]=b' '.join(values)+b'\n';return b''.join(rows)
                    error={'tag':'INPUT_TAG','word':'INPUT_WORD','eof':'INPUT_EOF'}.get(field,diagnostic)
                    add(profile,'G200/'+tag+'/'+field,error,build,False,
                        'helper-only seq0; complete P/U read before echo; no legal preparatory O')
        if profile == 'PORT13B':
            for error in ('INPUT_ID', 'INPUT_OPCOUNT'):
                def late_case(decimal, error=error):
                    data = input13b(control, decimal, profile)
                    data = data.replace(b'PORT13B 1\n', b'PORT13B 2\n', 1)
                    return data + (b'C 3 1\n' if error == 'INPUT_ID' else b'C 2 0\n')
                add(profile, 'late-case/' + error, error, late_case, True,
                    'legal case1 incl ENDCASE; fatal case2 header')
    m.require(all(sum(r['profile'] == p for r in result) <= 256 for p in ('PORT13B', 'GUARD13B')),
              'frozen per-profile negative limit')
    return result


class Runtime13B:
    pass                                                                         
    compiler = Runtime.compiler
    def __init__(self, out):
        self.out = Path(out)
        run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
        self.first_half=ROOT/'RESULT-PORT13'/run/'13b'
        manifest=self.first_half/'manifest.json'
        binaries=json.loads(manifest.read_text(encoding='utf-8')).get('binaries',{}) if manifest.is_file() else {}
        self.paths = {side: Path(os.environ.get(key, binaries.get(label,self.out/default))) for side,key,label,default in (
            ('C', 'LANCUCHY_C_B1_BIN', 'obs1','c13b-obs1-bin'),
            ('C0', 'LANCUCHY_C_B0_BIN', 'obs0','c13b-obs0-bin'),
            ('D', 'LANCUCHY_D_BIN', 'duckling','duckling-lancuchy-bin'))}

    def output_limit(self,data):
        return 4934991872 if data.startswith(b'PORT13B ') else 20*1024*1024

    @contextmanager
    def run(self, side, data, executable=None):
        binary = Path(executable) if executable else self.paths[side]
        m.require(sys.platform.startswith('linux') and binary.is_file(), 'Missing Linux native13b ' + str(binary))
        with tempfile.TemporaryDirectory(prefix='.13b-', dir=self.out) as directory:
            folder = Path(directory); source = folder / 'input'; source.write_bytes(data)
            output = folder / 'stdout'; err = folder / 'stderr'
            argv = [str(binary), str(source)] if side.startswith('C') else [str(binary)]
            attempts = []
            for attempt in range(2):
                start = time.monotonic()
                with source.open('rb') as stdin, output.open('wb') as stdout, err.open('wb') as stderr:
                    try:
                        result = subprocess.run(argv, stdin=stdin if side == 'D' else subprocess.DEVNULL,
                                                stdout=stdout, stderr=stderr, timeout=180)
                        break
                    except subprocess.TimeoutExpired:
                        attempts.append({'attempt': attempt + 1, 'seconds': time.monotonic() - start, 'timeout': True})
            else:
                raise ValueError('Two isolated native13b timeouts, NOT a mutation kill: ' + json.dumps(attempts))
            limit=self.output_limit(data)
            m.require(output.stat().st_size <= limit, 'native13b output exceeds frozen profile envelope')
            with err.open('rb') as f: errors = f.read(16385)
            m.require(len(errors) <= 16384, 'native stderr exceeds bounded log')
            meta = {'code': result.returncode, 'seconds': time.monotonic() - start,
                    'argv': argv, 'input_sha256': hashlib.sha256(data).hexdigest(),
                    'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'stdout_bytes': output.stat().st_size, 'stderr_bytes': err.stat().st_size,
                    'attempts': attempts}
            yield result.returncode, output, errors, meta


def compare_files13b(left, right, project=False):
    pass                                                                       
    def rows(path, projection):
        with Path(path).open('rb') as stream:
            for line in stream:
                line = m.projection13b_line(line) if projection else line
                if line is not None: yield line
    for number, (a, c) in enumerate(zip_longest(rows(left, project), rows(right, False)), 1):
        if a != c:
            return {'line': number, 'baseline': (a or b'')[:2048].decode('ascii', errors='replace'),
                    'actual': (c or b'')[:2048].decode('ascii', errors='replace')}
    return None


def validate_file13b(path, data, decimal=False, observer=True, expected_guard=None, semantic=True):
    decoded = m.decode_input13b(data, decimal)
    helpers = []; snapshots = 0; final = None; observations = []
    with Path(path).open('rb') as stream:
        for ident, seq, records, _, result in m.snapshots13b(stream, decoded, observer, semantic):
            if ident is None: final = result
            elif seq == 0: helpers.extend(records)
            else:
                snapshots += 1
                observations.append({'id': ident, 'seq': seq, 'maxima': result['maxima']})
    m.require(final and final['END_EOF'], 'native13b complete framing required')
    if expected_guard is not None:
        row = expected_guard
        if row['helper'] is None:
            m.require(not helpers, 'G0 must not emit GR13')
        else:
            value = ((1 + row['ga'][2], 0) if row['helper'] == 112 else
                     (0x8000ffff, 0x80000001) if row['helper'] == 113 else (0, 0))
            seq = len(row['operations']) + 1 if row['operations'] else 0
            wanted = ('GR13', (1, seq, row['helper'], row['expected_status'],
                               int(row['expected_status'] == 0), *value))
            m.require(helpers == [wanted], 'exact GR13 native preflight/accepted/value')
        if row['helper'] is None and row['operations'] and row.get('check_named_final',True):
                                                                              
            final_op = None
            with Path(path).open('rb') as stream:
                for raw in stream:
                    if raw.startswith(b'A13 '): final_op = m.parse13b(raw)[1][2:]
            m.require(final_op == (row['expected_status'], row['expected_reason']), 'named guard final A13 expectation')
    return {**final, 'snapshots': snapshots, 'observations': observations}


def guard_stage13b(runtime, definitions=None):
    result = []
    for definition in guard_definitions13b() if definitions is None else definitions:
        row = {'id': definition['id'], 'Gkind': definition['kind'], 'sides': {},
               'control_only': definition['control_only'], 'native_mutation': False}
        try:
            with runtime.run('C', encode_guard13b(definition)) as crun:
                with runtime.run('D', encode_guard13b(definition, True)) as drun:
                    for side, run, decimal in (('C', crun, False), ('D', drun, True)):
                        code, path, stderr, meta = run
                        try:
                            m.require(code == 0 and stderr == b'', 'guard exit/stderr')
                            checked = validate_file13b(path, encode_guard13b(definition, decimal), decimal,
                                                      expected_guard=definition)
                            row['sides'][side] = {'ok': True, 'run': meta, 'model': checked}
                        except Exception as exc:
                            row['sides'][side] = {'ok': False, 'run': meta, 'error': str(exc),
                                                  'stderr': stderr.decode('ascii', errors='replace')}
                    row['difference'] = compare_files13b(crun[1], drun[1])
                    row['ok'] = all(x['ok'] for x in row['sides'].values()) and row['difference'] is None
        except Exception as exc:
            row.update(ok=False, error=str(exc))
        result.append(row)
    return result


def supplemental_guards13b():
    pass                                                                           
    result=[]
    ga=[0]*64;ga[:3]=[0,0xfffffffc,0xffffffff]
    operations=setup13b()+[chain_op13b([(i,0) for i in range(6)],target=1),chain_op13b(target=1)]
    result.append({'id':'SUPPLEMENT-G4-CHAIN-BATCH','kind':4,'ga':tuple(ga),'seedAfterSeq':3,
        'operations':operations,'materialized':True,'helper':None,'expected_status':0,'expected_reason':0,'control_only':True})
    ga=[0]*64;ga[2]=65535
    operations=setup13b()+[op13b(101,1,0,0),chain_op13b(target=1),op13b(102,1,0,1)]
    result.append({'id':'SUPPLEMENT-G11-CHAIN-WRAP','kind':11,'ga':tuple(ga),'seedAfterSeq':3,
        'operations':operations,'materialized':True,'helper':None,'expected_status':0,'expected_reason':0,'control_only':True})
    return result


def supplemental_stage13b(runtime):
                                                                            
    result=[]
    for definition in supplemental_guards13b():
        row={'id':definition['id'],'sides':{},'control_only':True}
        try:
            with runtime.run('C',encode_guard13b(definition)) as crun, runtime.run('D',encode_guard13b(definition,True)) as drun:
                for side,run in (('C',crun),('D',drun)):
                    try:
                        m.require(run[0]==0 and not run[2],'supplemental guard native exit/stderr')
                        checked=validate_file13b(run[1],encode_guard13b(definition,side=='D'),side=='D',expected_guard=definition)
                        row['sides'][side]={'ok':True,'run':run[3],'model':checked}
                    except Exception as exc:row['sides'][side]={'ok':False,'run':run[3],'error':str(exc)}
                row['difference']=compare_files13b(crun[1],drun[1])
                row['ok']=all(v['ok'] for v in row['sides'].values()) and row['difference'] is None
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def metadata_stage13b(runtime):
    generator=load('lancuchy_metadata_inputs13b','przypadki-lancuchy.py')
    definitions=[]
    for name,fixture in generator.metadata_fixtures13b().items():
        definitions.append({**fixture,'id':'metadata/'+name,'materialized':True,
            'helper':None,'check_named_final':False,'control_only':True})
    return guard_stage13b(runtime,definitions)


def history_selfcontrols13b(runtime):
    pass                                                                          
    answer=[]
    call=chain_op13b([(i,0) for i in range(5)],materials=[(m.bits(.6),0,0,0,0,0)]*5)
    operations=setup13b()[:2]+[call,op13b(102,1,0,0),op13b(106,0,0,0),
        op13b(1,0),op13b(107,0),op13b(108,0,1,123)]
    def fixture(ops,tests):
        inputs={side:input13b(ops,side=='D','GUARD13B') for side in ('C','D')}
        with runtime.run('C',inputs['C']) as crun,runtime.run('D',inputs['D']) as drun:
            m.require(crun[0]==drun[0]==0 and not crun[2] and not drun[2],'history self-control native baseline')
            baseline={side:validate_file13b(run[1],inputs[side],side=='D') for side,run in (('C',crun),('D',drun))}
            m.require(compare_files13b(crun[1],drun[1]) is None,'history self-control healthy C/D baseline differs')
            m.require(crun[1].stat().st_size<=1204576,'small self-control fixture envelope')
            with crun[1].open('rb') as f:original=[m.parse_world13b(raw) for raw in f]
            for name,mutate in tests:
                changed=mutate(copy.deepcopy(original))
                with tempfile.TemporaryDirectory(prefix='.13b-selfcontrol-',dir=runtime.out) as directory:
                    path=Path(directory)/'identical-C-D'
                    with path.open('wb') as f:
                        for tag,v in changed:
                            if tag=='IP13' or tag in m.SCHEMA13B and not(tag=='G' and len(v)!=4):
                                prefix=3 if tag=='IP13' else m.SCHEMA13B[tag][0]
                                f.write((tag+' '+' '.join(str(w) if i<prefix else f'{w:08x}' for i,w in enumerate(v))+'\n').encode('ascii'))
                            else:f.write(m.base12_13b().format_record(tag,v).encode('ascii'))
                    row={'id':name,'identical_corruption_both_sides':True,'sides':{},'native_product_mutant':False}
                    for side in ('C','D'):
                        try:
                            validate_file13b(path,inputs[side],side=='D')
                            row['sides'][side]={'rejected':False}
                        except (ValueError,IndexError,KeyError) as exc:
                            row['sides'][side]={'rejected':True,'reason':str(exc)}
                    row['ok']=all(v['rejected'] for v in row['sides'].values())
                    row['baseline_input_SHA']={s:hashlib.sha256(inputs[s]).hexdigest() for s in inputs}
                    row['baseline_binary_SHA']={'C':crun[3]['binary_sha256'],'D':drun[3]['binary_sha256']}
                    answer.append(row)
    frames={'GUARD13B','PORT13B','G','GA','CASE','ENDCASE','END'}
    def at(tag,v,seq):return len(v)>1 and v[:2]==(1,seq) and (tag not in frames or tag=='G' and len(v)!=4)
    def recount(rows,seq):
        count=Counter(t for t,v in rows if at(t,v,seq));result=[]
        for tag,v in rows:
            if at(tag,v,seq):
                if tag=='I12':v=(*v[:2],*(count[t] for t in ('AP12','WS12','NM12','UD12','HC12','HR12','HT12','CL12','CV12','VR12','EF12')))
                elif tag=='IP12':v=(*v[:2],count['NP12'])
                elif tag=='I13':v=(*v[:2],*(count[t] for t in ('CH13','CI13','CM13','BH13','IP13','CG13')))
                elif tag=='Z13':v=(*v[:2],*(count[t] for t in ('A13','CN13','CQ13','QL13','CS13','PC13','COPY13','CV13','CE13','ENDCOPY13')),count['CN13'],*v[13:16],count['EP13B'],count['EU13B'],count['V13'])
            result.append((tag,v))
        return result
    def remove(tags,seq,last=False):
        def mutate(rows):
            indices=[i for i,(t,v) in enumerate(rows) if t in tags and at(t,v,seq)]
            m.require(indices,'self-control requires an actually present group')
            gone={indices[-1]} if last else set(indices)
            return recount([row for i,row in enumerate(rows) if i not in gone],seq)
        return mutate
    tests=[]
    for tag,seq in (('EF12',3),('NP12',3),('CQ13',4),('QL13',4),('CS13',3),('CG13',3)):
        tests.append(('remove-'+tag+'-repair-counts',remove({tag},seq)))
    tests += [('remove-COPY-repair-counts',remove({'COPY13','CV13','CE13','ENDCOPY13'},5)),
              ('remove-last-material',remove({'CM13'},3,True)),('remove-last-child',remove({'CI13'},3,True)),
              ('truncated-history',lambda rows:[(t,v) for t,v in rows if not at(t,v,1)])]
    def flip(seq,fields):
        def mutate(rows):
            result=[]
            for t,v in rows:
                if at(t,v,seq) and t in fields:
                    w=list(v);w[fields[t]]^=1;v=tuple(w)
                result.append((t,v))
            return result
        return mutate
    tests += [('wrong-owner-CN-and-CG',flip(3,{'CN13':9,'CG13':8})),
              ('wrong-birth-CN-and-CG',flip(3,{'CN13':7,'CG13':6})),
              ('wrong-lastIssued',flip(3,{'Z8':26})),('changed-copy-after-world',flip(7,{'CE13':9}))]
    fixture(operations,tests)
    def swap_free(rows):
        result=[]
        for t,v in rows:
            if t=='IP13' and at(t,v,6):
                m.require(v[4]==2,'self-control needs two freed chain slots')
                v=(*v[:5],*reversed(v[5:]))
            result.append((t,v))
        return result
    fixture(setup13b()+[chain_op13b(target=1),op13b(101,1,0,0),op13b(101,1,0,1),chain_op13b(target=2)],
            [('changed-LIFO-order',swap_free)])
    return answer


def negative_prefix_control13b(definition, decimal=False):
    pass                                                              

                                                                          
                                                                             
       
    data = definition['data_D' if decimal else 'data_C']
    profile = definition['profile']; rows = data.splitlines(keepends=True)
    if not definition['after_legal_O']:
        if '/G200/' in definition['name']:
            return None,b'GUARD13B 1\n',None
        if '/opCount' in definition['name'] or '/id-before-O' in definition['name']:
            return None, (profile + ' 1\n').encode(), None
        if 'EOF-no-next-O' in definition['name']:
            prefix = (profile + ' 1\n').encode()
            if profile == 'GUARD13B': prefix += rows[1] + rows[2]
            return None, prefix + b'CASE 1 1\n', None
        return None, b'', None
    late = '/late-case/' in definition['name']
    trailing = definition['error'] == 'INPUT_TRAILING_DATA'
    op_indices = [i for i, row in enumerate(rows) if row.startswith(b'O ')]
    header_fields = rows[1].split()
    original_count = int(header_fields[4 if profile == 'GUARD13B' else 2])
    good = original_count if late or trailing else original_count - 1
    m.require(good >= 1, 'negative must have a completed legal prefix')
    cut = len(rows) if late or trailing else (op_indices[-1] if len(op_indices) == original_count else len(rows) - 1)
    selected = rows[:cut]
    if trailing: selected = selected[:-1]
    if late: selected = selected[:-1]
    selected[0] = (profile + ' 1\n').encode()
    if profile == 'GUARD13B':
        fields = selected[1].split(); fields[4] = str(good).encode()
        selected[1] = b' '.join(fields) + b'\n'
    else:
        fields = selected[1].split(); fields[2] = str(good).encode()
        selected[1] = b' '.join(fields) + b'\n'
    return b''.join(selected), None, {'good': good, 'original_count': original_count,
                                    'keep_endcase': late or trailing, 'profile': profile,
                                    'N': 2 if late else 1}


def negative_stage13b(runtime):
    result = []
    for definition in negative_definitions13b():
        row = {'name': definition['name'], 'error': definition['error'], 'sides': {}}
        control, literal, framing = negative_prefix_control13b(definition)
        try:
            with ExitStack() as stack:
                prefix_ok = True
                prefix_path = None
                if control is not None:
                    code, prefix_path, stderr, meta = stack.enter_context(runtime.run('C', control))
                    m.require(code == 0 and stderr == b'', 'legal negative-prefix C control failed')
                    try:
                        checked = validate_file13b(prefix_path, control)
                        row['prefix_control'] = {'run': meta, 'model': checked}
                    except Exception as exc:
                        prefix_ok = False
                        row['prefix_control'] = {'run': meta, 'model_error': str(exc)}
                def expected_lines():
                    if literal is not None:
                        yield from literal.splitlines(keepends=True)
                        return
                    with prefix_path.open('rb') as stream:
                        yield from prefix_output_lines13b(stream,framing)
                prefix_bytes = sum(map(len, expected_lines()))
                for side in ('C','D'):
                    data = definition['data_C' if side == 'C' else 'data_D']
                    with runtime.run(side, data) as (code, path, stderr, meta):
                        difference = None
                        with path.open('rb') as stream:
                            for number, (wanted, actual) in enumerate(zip_longest(expected_lines(), stream), 1):
                                if wanted != actual and difference is None:
                                    difference = {'line':number,
                                        'baseline':(wanted or b'')[:2048].decode('ascii',errors='replace'),
                                        'actual':(actual or b'')[:2048].decode('ascii',errors='replace')}
                        fatal_ok = code == 2 and stderr == definition['expected_stderr']
                        row['sides'][side] = {'ok': fatal_ok and difference is None and prefix_ok,
                            'fatal_diagnostic_ok':fatal_ok,'prefix_equal':difference is None,'run': meta,
                            'stderr':stderr.decode('ascii',errors='replace'),
                            'prefix_bytes':prefix_bytes,'difference':difference}
                row['ok'] = all(x['ok'] for x in row['sides'].values())
        except Exception as exc:
            row.update(ok=False, error=str(exc))
        result.append(row)
    return result


def prefix_output_lines13b(source,framing):
    pass                                                                      
    for raw in source:
        if raw==b'END 1\n' or raw==b'ENDCASE 1\n' and not framing['keep_endcase']:continue
        if raw.startswith(b'CASE '):raw=f'CASE 1 {framing['original_count']}\n'.encode()
        elif raw.startswith(b'G ') and len(raw.split())==5:
            raw=f'G 1 0 0 {framing['original_count']}\n'.encode()
        elif raw.startswith(b'PORT13B '):raw=f'PORT13B {framing['N']}\n'.encode()
        yield raw


def parser_results13b(results):
    pass                                                                    
    actual={r['name']:r for r in results}
    m.require(len(actual)==len(results),'duplicate negative13b result')
    definitions=negative_definitions13b();names={r['name'] for r in definitions}
    m.require(set(actual)<=names,'unexpected negative13b result')
    catalogue=parser_reachability13b()
    for item in catalogue:
        for profile in ('PORT13B','GUARD13B'):
            scope=item[profile]
            expected=[r for r in definitions if r['profile']==profile and r['error']==item['error']]
            if not scope['reachable']:
                m.require(not expected,'unreachable class has invented input')
                scope.update(status='UNREACHABLE_IN_THIS_PROFILE',planned=0,executed=0,native_verified=False)
                continue
            m.require(expected,'reachable class has no input')
            scope['variants']=[r['name'] for r in expected]
            scope['planned']=len(expected)
            scope['executed']=sum(r['name'] in actual and bool(actual[r['name']].get('sides')) for r in expected)
            scope['sides']={side:{'required':len(expected),'ok':sum(bool(actual.get(r['name'],{}).get('sides',{}).get(side,{}).get('ok')) for r in expected)} for side in ('C','D')}
            scope['native_verified']=all(r['name'] in actual and actual[r['name']].get('ok') for r in expected)
            scope['status']='NATIVE_VERIFIED' if scope['native_verified'] else 'GAP_NATIVE_VARIANTS'
        item['ok']=all(not item[p]['reachable'] or item[p]['native_verified'] for p in ('PORT13B','GUARD13B'))
    return catalogue


def positive_definitions13b():
    pass                                                                   
    result=[]
    for n in range(1,65):
        data={}
        for decimal in (False,True):
            one=input13b(setup13b()[:1],decimal).splitlines(keepends=True)
            rows=[f'PORT13B {n}\n'.encode()]
            for ident in range(1,n+1):rows += [f'C {ident} 1\n'.encode(),one[2]]
            data[decimal]=b''.join(rows)
        result.append({'name':'PORT13B/N'+str(n),'C':data[False],'D':data[True]})
    for profile,maximum in (('PORT13B',64),('GUARD13B',16)):
        for count in range(1,maximum+1):
            operations=setup13b()[:count]
            operations += [op13b(102,1,0,0)]*(count-len(operations))
            result.append({'name':profile+'/opCount'+str(count),
                'C':input13b(operations,False,profile),'D':input13b(operations,True,profile)})
    for profile in ('PORT13B','GUARD13B'):
        result.append({'name':profile+'/CRLF','C':input13b(setup13b(),False,profile).replace(b'\n',b'\r\n'),
                       'D':input13b(setup13b(),True,profile).replace(b'\n',b'\r\n')})
    return result


def positive_stage13b(runtime):
    result=[]
    for definition in positive_definitions13b():
        row={'name':definition['name'],'sides':{}}
        try:
            with runtime.run('C',definition['C']) as crun, runtime.run('D',definition['D']) as drun:
                for side,run in (('C',crun),('D',drun)):
                    try:
                        m.require(run[0]==0 and not run[2],'positive native process/stderr')
                        checked=validate_file13b(run[1],definition[side],side=='D')
                        row['sides'][side]={'ok':True,'run':run[3],'model':checked}
                    except Exception as exc:row['sides'][side]={'ok':False,'run':run[3],'error':str(exc)}
                row['difference']=compare_files13b(crun[1],drun[1])
                row['ok']=all(r['ok'] for r in row['sides'].values()) and row['difference'] is None
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def mutation_stage13b(runtime, bindings_path, full_result, out, only_ids=None):
    pass                                                                         
    manifest = json.loads(Path(bindings_path).read_text(encoding='utf-8'))
    m.require(manifest.get('anchor_owner13b',manifest.get('anchor_owner')) == 'T-13b-2a',
              '13b anchor binding profile mismatch')
    recipes = manifest.get('recipes13b', manifest.get('recipes', []))
    m.require(recipes and len({r['id'] for r in recipes}) == len(recipes), 'empty/duplicate native13b recipe list')
    if only_ids is not None:
        selected=set(only_ids)
        m.require(selected and selected <= {r['id'] for r in recipes}, 'unknown/empty native13b pilot selection')
        recipes=[r for r in recipes if r['id'] in selected]
                                                                            
                                                                               
                                                                    
    duckc = runtime.compiler()
    m.require(sys.platform.startswith('linux') and duckc.is_file(), 'existing official native duckc required')
    guards = {r['id']:r for r in guard_definitions13b()}
    receipts=[]
    with tempfile.TemporaryDirectory(prefix='.13b-mutants-',dir=out) as directory:
        directory=Path(directory);physics=directory/'fizyka'
        shutil.copytree(ROOT/'silnik/fizyka',physics)
        for recipe in recipes:
            receipt={'id':recipe['id'],'requirement':recipe['requirement'],'anchor_owner':'T-13b-2a',
                'native_executed':False,'baseline_ok':False,'single_hit':False,'clean':False,'detected':False,
                'port':recipe['source']+':'+str(recipe['line'])}
            changed=None;original=None
            try:
                source=(ROOT/recipe['source']).resolve()
                m.require(source.is_relative_to((ROOT/'silnik/fizyka').resolve()),'only product physics may mutate')
                original=source.read_bytes()
                m.require(hashlib.sha256(original).hexdigest()==recipe['source_sha256'],'Stale product source SHA')
                text=original.decode('utf-8');anchor=recipe['anchor']
                m.require(anchor and text.count(anchor)==1,'exactly one actual anchor hit required')
                receipt['single_hit']=True
                guard=None
                if recipe.get('guard'):
                    guard=guards[recipe['guard']]
                    m.require(not guard['control_only'],'control/equivalence cannot be counted as a native kill')
                    cdata,ddata=encode_guard13b(guard),encode_guard13b(guard,True)
                else:
                    generator=load('lancuchy_13b_mutation_inputs','przypadki-lancuchy.py')
                    if recipe.get('fixture'):
                        fixture=generator.metadata_fixtures13b()[recipe['fixture']]
                        cdata=''.join(generator.text_fixture13b(fixture)).encode('ascii')
                        ddata=''.join(generator.text_fixture13b(fixture,True)).encode('ascii')
                    else:
                        cases=generator.cases13b(recipe['case'])
                        cdata=''.join(generator.text13b(cases)).encode('ascii')
                        ddata=''.join(generator.text13b(cases,True)).encode('ascii')
                with runtime.run('C',cdata) as crun, runtime.run('D',ddata) as drun:
                    for side,run,data,decimal in (('C',crun,cdata,False),('D',drun,ddata,True)):
                        m.require(run[0]==0 and not run[2],'mutation baseline process/stderr')
                        validate_file13b(run[1],data,decimal,expected_guard=guard)
                        receipt['baseline_'+side]=run[3]
                    m.require(compare_files13b(crun[1],drun[1]) is None,'native mutation baseline C/D differs')
                    receipt['baseline_ok']=True
                    changed=physics/source.relative_to((ROOT/'silnik/fizyka').resolve())
                    edited=text.replace(anchor,recipe['replacement'],1)
                    changed.write_text(edited,encoding='utf-8')
                    receipt['product_sha256']=hashlib.sha256(changed.read_bytes()).hexdigest()
                    build=directory/'build';build.mkdir(exist_ok=True)
                    executable=build/'probe';executable.unlink(missing_ok=True)
                    config={'packages':[{'id':'fizyka','name':'fizyka','path':str(physics)},
                        {'id':'probe','name':'probe','path':str(ROOT/'silnik/port/lancuchy.dk'),'dependencies':[{'id':'fizyka'}]}],
                        'tasks':[{'package':'fizyka','strategy':'lib','output_file':'libfizyka.a'},
                            {'package':'probe','strategy':'native','output_file':'probe','linking_options':
                                {'additional_link_options':[str(build/'libfizyka.a'),'-lm'],'link_c_standard_library':True}}]}
                    config_path=directory/'packages.json';config_path.write_text(json.dumps(config),encoding='utf-8')
                    argv=[str(duckc),'compile_packages',str(config_path),'-a',str(build),'-O','0']
                    attempts=[]
                    for attempt in range(2):
                        started=time.monotonic()
                        try:
                            compiled=subprocess.run(argv,capture_output=True,timeout=180)
                            break
                        except subprocess.TimeoutExpired:
                            attempts.append({'attempt':attempt+1,'timeout':True})
                    else:raise ValueError('Two isolated build timeouts, NOT a kill')
                    receipt['build']={'code':compiled.returncode,'seconds':time.monotonic()-started,
                        'argv':argv,'timeouts':attempts,'stderr':compiled.stderr[-8192:].decode(errors='replace')}
                    m.require(compiled.returncode==0 and executable.is_file(),'build failure/missing ELF is not a kill')
                    with executable.open('rb') as f:m.require(f.read(4)==b'\x7fELF','native ELF required')
                    with runtime.run('D',ddata,executable) as mutated:
                        receipt['native_executed']=True;receipt['run']=mutated[3]
                        m.require(mutated[0]==0 and not mutated[2],'crash/fatal/stderr is not a native kill')
                        validate_file13b(mutated[1],ddata,True,semantic=False)
                        difference=compare_files13b(drun[1],mutated[1])
                        receipt.update(clean=True,detected=difference is not None,difference=difference)
            except Exception as exc:
                receipt['error']=str(exc)
            finally:
                if changed is not None and original is not None:changed.write_bytes(original)
            receipts.append(receipt)
            (Path(out)/'mutations.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipts


def stage13b(ctx=None):
    started=time.monotonic()
    run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    out = Path(getattr(ctx,'LANCUCHY_13B_OUT',ROOT/os.environ.get('LANCUCHY_13B_RESULT_DIR','RESULT-PORT13/'+run)))
    out = (out / '13b').resolve()
    m.require(out.is_relative_to(ROOT.resolve()), '13b evidence must stay inside this worktree')
    out.mkdir(parents=True, exist_ok=True)
    result = {'code': 1, 'full_acceptance': False, 'stages': {}, 'errors': [], 'native_product_mutants': 0}
    controls=unittest.defaultTestLoader.discover(str(HERE),'test_lancuchy_13b*.py')
    log=io.StringIO();checked=unittest.TextTestRunner(stream=log,verbosity=2).run(controls)
    (out/'selftests.csv').write_text(log.getvalue(),encoding='utf-8')
    result['stages']['stand_controls']={'run':checked.testsRun,'failures':len(checked.failures),
        'errors':len(checked.errors),'skips':len(checked.skipped)}
    if not checked.wasSuccessful() or checked.skipped:result['errors'].append('13b stand controls failed/skipped')
    runtime = Runtime13B(out)
    guard_evidence=[]
    for label, function in (('guards', guard_stage13b), ('negative_parsers', negative_stage13b),
                            ('positive_parsers', positive_stage13b), ('supplemental_guards', supplemental_stage13b),
                            ('metadata_fixtures',metadata_stage13b),('history_selfcontrols',history_selfcontrols13b)):
        try:
            rows = function(runtime)
            if label=='guards':guard_evidence=rows
            (out / (label + '.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            result['stages'][label] = {'required': len(rows), 'ok': sum(bool(r.get('ok')) for r in rows)}
            if label=='negative_parsers':
                catalogue=parser_results13b(rows)
                (out/'F13.json').write_text(json.dumps(catalogue,indent=2)+'\n',encoding='utf-8')
                result['stages']['F13']={'required':33,'ok':sum(r['ok'] for r in catalogue)}
            if not all(r.get('ok') for r in rows): result['errors'].append(label + ': native failures/missing evidence')
        except Exception as exc:
            result['stages'][label] = {'ok': False, 'error': str(exc)}
            result['errors'].append(label + ': ' + str(exc))
    receipts=[]
    bindings=os.environ.get('LANCUCHY_13B_BINDINGS')
    candidate=HERE/'lancuchy-kotwice.json'
    if bindings is None and candidate.is_file():
        anchor_data=json.loads(candidate.read_text(encoding='utf-8'))
        if anchor_data.get('anchor_owner13b',anchor_data.get('anchor_owner'))=='T-13b-2a':bindings=str(candidate)
    full_path=os.environ.get('LANCUCHY_13B_FULL_RESULT',str(runtime.first_half/'full.json'))
    full={}
    if Path(full_path).is_file():full=json.loads(Path(full_path).read_text(encoding='utf-8'))
    if bindings and full_path:
        try:
            receipts=mutation_stage13b(runtime,bindings,full,out)
            result['native_product_mutants']=sum(bool(r['detected'] and r['clean']) for r in receipts)
        except Exception as exc:result['errors'].append('native_mutations: '+str(exc))
    guards = guard_definitions13b()
    processes_ok=bool(full.get('process_codes')) and all(x==0 for x in full['process_codes'].values()) and not any(full.get('stderr_bytes',{}).values())
    observations=[{**row,'END_EOF':full.get('global_END_checked',False),
                   'native_processes_ok':processes_ok} for row in full.get('cases',[])]
    equivalences=b.equivalence_proofs13b(ROOT)
    for proof in equivalences:
        proof['native_baseline_verified']=bool(processes_ok and full.get('global_END_checked') and full.get('word_comparison_ok'))
    (out/'equivalence-proofs.json').write_text(json.dumps(equivalences,indent=2)+'\n',encoding='utf-8')
    carried=b.accounting_spec13b().get('carried_receipts',[])
    result['stages']['carried_native_evidence']={'count':len(carried),'origin':'ZAKRES-13b measured pilots; not executed in this job'}
    ledger = b.table13b(guards, receipts+carried, observations, product_root=ROOT,
                       equivalences=equivalences,controls=guard_evidence)
    (out/'galezie.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    result['stages']['branches'] = {'required': ledger['required'], 'verified': ledger['verified']}
    if not receipts:result['errors'].append('Once-bound native13b product mutation receipts missing')
    elif not all(r['detected'] and r['clean'] for r in receipts):result['errors'].append('Native13b mutations incomplete/unclean/undetected')
    if ledger['gaps']:result['errors'].append('Unverified13b branch obligations: '+str(len(ledger['gaps'])))
    if not full.get('comparison_ok'):result['errors'].append('Full64/BASE12 acceptance missing/red: '+str(full.get('errors','no full result')))
    result['code']=int(bool(result['errors']))
    result['seconds']=time.monotonic()-started
    (out/'13b-oslony-wynik.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result['code']


def direct_call13c(kind=0, *, mode=1):
    a=[0]*64;a[0:2]=[kind,mode]
    a[2:10]=map(m.bits,(2.,0.,1.,0.,-1.,0.,-2.,0.))
    a[12]=a[16]=m.bits(1.);a[18]=1 if kind==0 else 2 if kind==1 else 4
    a[19]=m.bits(.5)
    points=(((0.,.5),) if kind==0 else ((-.5,.5),(.5,.5)) if kind==1 else
            ((-.5,.25),(.5,.25),(.5,1.25),(-.5,1.25)))
    for j,p in enumerate(points):a[20+2*j:22+2*j]=map(m.bits,p)
    return tuple(a)


def guard_definitions13c():
    pass                                                                    
    manifest=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))
    result=[]
    for spec in manifest['guardPrzypadki']:
        if spec['czesc']!='13c':continue
        name=spec['id'];kind=0 if '-CIRCLE-' in name else 1 if '-CAPSULE-' in name else 2
        a=list(direct_call13c(kind))
        if name.endswith('-POINT'):a[20 if kind==0 else 22 if kind==1 else 26]=0x7f800000
        elif name.endswith('-RADIUS-FINITE'):a[19]=0x7f800000
        elif name.endswith('-RADIUS-SIGN'):a[19]=m.bits(-1.)
        elif name.endswith('-ROTATION'):a[12]=0
        elif name.endswith('-CACHE-COUNT'):a[36]=4
        elif name.endswith('-CACHE-A'):a[36]=1;a[37]=2
        elif name.endswith('-CACHE-B'):a[36]=1;a[40]=a[18]
        elif name.endswith('-EPSILON'):
            a[20:24]=[0,0,{'GD-CAPSULE-BELOW-EPSILON':0x397fffff,
                'GD-CAPSULE-EQUAL-EPSILON':0x39800000,'GD-CAPSULE-ABOVE-EPSILON':0x39800001}[name],0x39800000]
        else:raise ValueError('Unknown frozen13c guard '+name)
        status,reason=m.direct_status13c(tuple(a))
        result.append({'id':name,'name':name,'kind':320,'a':tuple(a),'status':status,'reason':reason,
                       'control_only':not spec['liczonyJakoZabicie'],'counted_as_kill':spec['liczonyJakoZabicie'],
                       'mutation_classes':spec['swiadczyKlasyMutacji']})
    m.require(len(result)==22 and len({r['id'] for r in result})==22,'exact22 frozen guard keys')
    return result


def encode_guard13c(definition,decimal=False):
    word=str if decimal else lambda v:f'{v:08x}'
    return ('GUARD13C 1\nG 1 320 0 0\nGA 1 '+' '.join(map(word,definition['a']))+'\n').encode('ascii')


def validate_helper13c(path,definition):
    expected=[('GUARD13C',(1,)),('G',(1,320,0,0)),('GA',(1,*definition['a'])),
              ('CASE',(1,0)),('GR13',(1,0,320,definition['status'],int(definition['status']==0),0,0)),
              ('ENDCASE',(1,)),('END',(1,))]
    digest=hashlib.sha256();count=0
    with Path(path).open('rb') as stream:
        for row,wanted in zip_longest(stream,expected):
            m.require(row is not None and wanted is not None,'helper13c complete framing')
            m.require(m.parse13c(row)==wanted,'helper13c exact native validator result')
            digest.update(row);count+=1
    return {'END_EOF':True,'rows':count,'sha256':digest.hexdigest(),'status':definition['status']}


class Runtime13C(Runtime13B):
    def output_limit(self,data):
        return 104365340672 if data.startswith(b'PORT13C ') else super().output_limit(data)

    def __init__(self,out):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
        run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
        self.first_half=ROOT/'RESULT-PORT13'/run/'13c';manifest=self.first_half/'manifest.json'
        binaries=json.loads(manifest.read_text(encoding='utf-8')).get('binaries',{}) if manifest.is_file() else {}
        self.paths={side:Path(os.environ.get(key,binaries.get(label,self.out/default))) for side,key,label,default in (
            ('C','LANCUCHY_C_C1_BIN','obs1','c13c-obs1-bin'),('C0','LANCUCHY_C_C0_BIN','obs0','c13c-obs0-bin'),
            ('D','LANCUCHY_D_BIN','duckling','duckling-lancuchy-bin'))}


def guard_stage13c(runtime,definitions=None):
    result=[]
    for definition in definitions if definitions is not None else guard_definitions13c():
        row={k:v for k,v in definition.items() if k!='a'};row['sides']={}
        try:
            with ExitStack() as stack:
                paths={}
                for side in ('C','D'):
                    data=encode_guard13c(definition,side=='D')
                    code,path,stderr,meta=stack.enter_context(runtime.run(side,data));paths[side]=path
                    item={'run':meta,'ok':False,'stderr':stderr.decode('ascii',errors='replace')}
                    try:
                        m.require(code==0 and not stderr,'helper13c native exit/stderr')
                        item['model']=validate_helper13c(path,definition);item['ok']=True
                    except Exception as exc:item['error']=str(exc)
                    row['sides'][side]=item
                row['difference']=compare_files13b(paths['C'],paths['D'])
                row['ok']=all(s['ok'] for s in row['sides'].values()) and row['difference'] is None
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def supplementary_guards13c():
    pass                                                                
    rows=[]
    for kind,name in enumerate(('CIRCLE','CAPSULE','POLYGON')):
        for start,xf in ((10,'A'),(14,'B')):
            for field,label,value in ((0,'position-X',0x7f800000),(1,'position-Y',0x7f800000),
                (2,'norm-low',0),(2,'norm-high',m.bits(2.))):
                a=list(direct_call13c(kind));a[start+field]=value;status,reason=m.direct_status13c(tuple(a))
                parent='GD-'+name+'-ROTATION'
                rows.append({'id':parent+'/'+xf+'/'+label,'parent_id':parent,'name':parent+'/'+xf+'/'+label,
                    'kind':320,'a':tuple(a),'status':status,'reason':reason,'control_only':False,'counted_as_kill':False})
            for label,sine in (('norm-low-equality',0x3f5d9d22),('norm-high-equality',0x3f5dca89)):
                a=list(direct_call13c(kind));a[start+2:start+4]=(0x3f000001,sine);status,reason=m.direct_status13c(tuple(a));parent='GD-'+name+'-ROTATION'
                rows.append({'id':parent+'/'+xf+'/'+label,'parent_id':parent,'name':parent+'/'+xf+'/'+label,
                    'kind':320,'a':tuple(a),'status':status,'reason':reason,'control_only':False,'counted_as_kill':False})
        for count in (0,2 if kind==0 else 1 if kind==1 else 2):
            a=list(direct_call13c(kind));a[18]=count
            for j in range(min(count,8),8):a[20+2*j:22+2*j]=(0,0)
            status,reason=m.direct_status13c(tuple(a));parent='GD-'+name+'-POINT';label=parent+'/count-'+str(count)
            rows.append({'id':label,'parent_id':parent,'name':label,'kind':320,'a':tuple(a),
                'status':status,'reason':reason,'control_only':False,'counted_as_kill':False})
        for point in range(4):
            for component in range(2):
                a=list(direct_call13c(kind));a[2+point*2+component]=0x7f800000;status,reason=m.direct_status13c(tuple(a))
                parent='GD-'+name+'-POINT';label=parent+'/terrain-finite-'+str(point)+'-'+str(component)
                rows.append({'id':label,'parent_id':parent,'name':label,'kind':320,'a':tuple(a),
                    'status':status,'reason':reason,'control_only':True,'counted_as_kill':False})
        for label,points in (('GB4-slop-equal',((1.,m.f32(.005)),(1.,0.),(-1.,0.),(-2.,0.))),
                            ('GB4-derived-d2',((0.,0.),(1.5e19,0.),(1.5e19,1.5e19),(0.,1.5e19)))):
            a=list(direct_call13c(kind));a[2:10]=map(m.bits,(v for p in points for v in p));status,reason=m.direct_status13c(tuple(a))
            parent='GD-'+name+'-POINT';label=parent+'/'+label
            rows.append({'id':label,'parent_id':parent,'name':label,'kind':320,'a':tuple(a),
                         'status':status,'reason':reason,'control_only':False,'counted_as_kill':False})
    return rows


def inherited_routes13c(runtime):
    pass                                                                      
    chosen=[g for g in guard_definitions13b() if g['id'].startswith(('GB2-','GB6-'))
            or g['id'] in ('GB5-ADJACENT','GB5-COLLINEAR')]
    result=[]
    for guard in chosen:
        row={'id':guard['id'],'inherited_from':'GUARD13B/'+guard['id'],'kind':guard['kind'],
             'control_only':guard['control_only'],'counted_as_kill':False,'sides':{}}
        try:
            with ExitStack() as stack:
                paths={}
                for side in ('C','D'):
                    original=encode_guard13b(guard,side=='D');data=original.replace(b'GUARD13B',b'GUARD13C')
                    code,path,stderr,meta=stack.enter_context(runtime.run(side,data));paths[side]=path
                    item={'ok':False,'run':meta,'stderr':stderr.decode('ascii',errors='replace')}
                    try:
                        m.require(code==0 and not stderr,'inherited13c native route exit/stderr')
                        mapped=path.with_suffix('.mapped')
                        with path.open('rb') as source,mapped.open('wb') as target:
                            for raw in source:
                                if raw==b'GUARD13C 1\n':raw=b'GUARD13B 1\n'
                                elif raw.startswith(b'E13C '):raw=raw.replace(b'E13C ',b'E13B ',1)
                                elif raw.startswith(b'Z9 '):
                                    parts=raw.rstrip(b'\n').split(b' ');m.require(parts[15]==b'0000000e','new GUARD profile14 before inherited validation')
                                    parts[15]=b'0000000c';raw=b' '.join(parts)+b'\n'
                                target.write(raw)
                        item['model']=validate_file13b(mapped,original,side=='D',expected_guard=guard);item['ok']=True
                        mapped.unlink()
                    except Exception as exc:item['error']=str(exc)
                    row['sides'][side]=item
                row['difference']=compare_files13b(paths['C'],paths['D']);row['ok']=all(s['ok'] for s in row['sides'].values()) and row['difference'] is None
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def warm_refusal_input13c(decimal=False):
    word=str if decimal else lambda v:f'{v:08x}'
    lines=['PORT13C 65\n']
    for ident in range(1,65):lines += [f'C {ident} 1\n','O 1 120 '+' '.join(map(word,direct_call13c()))+'\n']
    a=direct_call13c(1);bad=list(a);bad[19]=0x7f800000
    lines.append('C 65 3\n')
    for seq,words in enumerate((a,tuple(bad),a),1):lines.append(f'O {seq} 120 '+' '.join(map(word,words))+'\n')
    return ''.join(lines).encode('ascii')


def semantic_stage13c(runtime):
    definitions=[]
    for guard in guard_definitions13c():
        definitions.append({'id':guard['id'],'data_C':direct_input13c((guard['a'],direct_call13c())),
            'data_D':direct_input13c((guard['a'],direct_call13c()),True),'profile':'DIRECT'})
    a=list(direct_call13c(1));a[18]=0;a[20:36]=[0]*16;a[36]=1
    definitions.append({'id':'PARAM-cache-before-GEOMETRY-count0','data_C':direct_input13c((tuple(a),direct_call13c())),
        'data_D':direct_input13c((tuple(a),direct_call13c()),True),'profile':'DIRECT'})
    definitions.append({'id':'warm-own-cache-after-refusal','data_C':warm_refusal_input13c(),
        'data_D':warm_refusal_input13c(True),'profile':'DIRECT'})
    result=[]
    for definition in definitions:
        row={'id':definition['id'],'sides':{}}
        try:
            with ExitStack() as stack:
                runs={s:stack.enter_context(runtime.run(s,definition['data_'+s])) for s in ('C','D')}
                for side,(code,path,stderr,meta) in runs.items():
                    item={'run':meta,'ok':False,'stderr':stderr.decode('ascii',errors='replace')}
                    try:
                        m.require(code==0 and not stderr,'semantic refusal process0/stderr0')
                                                                              
                                                                             
                        item['model']=validate_control13c(path,definition['data_C'],definition['profile']);item['ok']=True
                    except Exception as exc:item['error']=str(exc)
                    row['sides'][side]=item
                row['difference']=compare_files13b(runs['C'][1],runs['D'][1]);row['ok']=all(s['ok'] for s in row['sides'].values()) and row['difference'] is None
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def direct_input13c(operations,decimal=False,*,N=1):
    word=str if decimal else lambda v:f'{v:08x}'
    rows=[f'PORT13C {N}\n',f'C 1 {len(operations)}\n']
    rows += ['O '+str(j)+' 120 '+' '.join(map(word,a))+'\n' for j,a in enumerate(operations,1)]
    return ''.join(rows).encode('ascii')


def validate_direct_file13c(path,operations,*,semantic=True):
    cache=None;observations=[];sha=hashlib.sha256();tags=Counter()
    with Path(path).open('rb') as stream:
        def take():
            raw=stream.readline(65537);m.require(raw and len(raw)<=65536,'direct13c row envelope')
            sha.update(raw);record=m.parse13c(raw);tags[record[0]]+=1;return record
        m.require(take()==('PORT13C',(1,)),'direct13c header')
        m.require(take()==('CASE',(1,len(operations))),'direct13c CASE')
        for seq,a in enumerate(operations,1):
            records=[]
            while not records or records[-1][0]!='DC13':
                m.require(len(records)<6,'direct13c exact row bound');records.append(take())
            observed=m.check_direct13c(records,1,seq,a,history=cache,semantic=semantic)
            cache=observed['cache'];observations.append({'id':1,'seq':seq,**observed})
        m.require(take()==('ENDCASE',(1,)) and take()==('END',(1,)) and not stream.read(1),'direct13c END/EOF')
    return {'END_EOF':True,'operations':len(operations),'observations':observations,'sha256':sha.hexdigest(),'tags':dict(tags)}


_PARSER_DIRECT_PREFIX13C=None


def profile_input13c(profile,operations,decimal=False):
    pass                                                                    
    global _PARSER_DIRECT_PREFIX13C
    word=str if decimal else lambda v:f'{v:08x}'
    if profile=='DIRECT':return direct_input13c([x['a'] for x in operations],decimal)
    ident=385 if profile=='PUBLIC' else 1
    rows=[]
    if profile=='PUBLIC':
        rows=['PORT13C 385\n']
                                                                         
        for j in range(1,385):
            a=direct_call13c((j-1)//128)
            rows += [f'C {j} 1\n','O 1 120 '+' '.join(map(word,a))+'\n']
    elif profile=='GUARD':
        rows=['GUARD13C 1\n',f'G 1 0 0 {len(operations)}\n','GA 1 '+' '.join([word(0)]*64)+'\n']
    elif profile=='COMPONENT':rows=['COMPONENT13C 1\n']
    else:raise ValueError('Unknown parser profile '+profile)
    if profile!='GUARD':rows.append(f'C {ident} {len(operations)}\n')
    for seq,op in enumerate(operations,1):
        rows.append(f'O {seq} {op['opcode']} '+' '.join(map(word,op['a']))+'\n')
        if op['opcode']==100:
            for tag,group in (('P13B',op['points']),('U13B',op['materials'])):
                rows += [f'{tag} {ident} {seq} {j} '+' '.join(map(word,p))+'\n' for j,p in enumerate(group)]
    return ''.join(rows).encode('ascii')


def negative_definitions13c():
    pass                                                                    
    result=[]
    def add(profile,label,error,builder,control_ops=None,framing=None,literal=None):
        row={'name':profile+'/'+label,'profile':profile,'error':error,'expected_stderr':('PORT13C: '+error+'\n').encode(),
             'data_C':builder(False),'data_D':builder(True),'framing':framing,'literal':literal}
        if control_ops is not None:
            row['control_C']=profile_input13c(profile,control_ops)
            row['control_D']=profile_input13c(profile,control_ops,True)
        result.append(row)
    physical=(
        ('bom',lambda x:b'\xef\xbb\xbf'+x,'INPUT_ASCII'),('high-byte',lambda x:b'\x80'+x,'INPUT_ASCII'),
        ('nul',lambda x:b'\x00'+x,'INPUT_ASCII'),('del',lambda x:b'\x7f'+x,'INPUT_ASCII'),
        ('double-space',lambda x:x.replace(b' ',b'  ',1),'INPUT_SPACING'),
        ('tab',lambda x:x.replace(b' ',b'\t',1),'INPUT_SPACING'),
        ('leading-space',lambda x:b' '+x,'INPUT_SPACING'),
        ('trailing-space',lambda x:x[:-1]+b' \n','INPUT_SPACING'),
        ('empty',lambda x:b'\n','INPUT_EMPTY_LINE'),
        ('bare-CR',lambda x:x[:-1]+b'\rX\n','INPUT_CR'),
        ('wrong-tag',lambda x:b'X'+x[1:],'INPUT_TAG'),
        ('line2049',lambda x:b'X'*2049+b'\n','INPUT_ARITY'))
    for profile in ('DIRECT','PUBLIC','GUARD','COMPONENT'):
        setup=[op13b(120,*direct_call13c())] if profile=='DIRECT' else setup13b()
        good=setup[-1] if profile=='DIRECT' else op13b(102,1,0,0)
        ident=385 if profile=='PUBLIC' else 1
        for label,damage,error in physical:
            for later in (False,True):
                def builder(decimal,damage=damage,later=later,profile=profile,setup=setup,good=good):
                    rows=profile_input13c(profile,setup+[good],decimal).splitlines(keepends=True)
                    at=max(j for j,x in enumerate(rows) if x.startswith(b'O ')) if later else 0
                    rows[at]=damage(rows[at]);return b''.join(rows)
                add(profile,label+('/after' if later else '/initial'),error,builder,
                    setup if later else None,{'count':len(setup)+1,'ident':ident,'drop_endcase':True} if later else None,
                    b'' if not later else None)
        header='PORT13C' if profile in ('DIRECT','PUBLIC') else profile+'13C'
        for n in (0,433 if header=='PORT13C' else 33 if header=='COMPONENT13C' else 2):
            add(profile,'N'+str(n),'INPUT_N',lambda d,n=n,h=header:f'{h} {n}\n'.encode(),literal=b'')
        add(profile,'decimal-N01','INPUT_DECIMAL',lambda d,h=header:(h+' 01\n').encode(),literal=b'')
                                                                
        def field_case(label,error,mutate):
            def builder(decimal):
                rows=profile_input13c(profile,setup+[good],decimal).splitlines(keepends=True)
                at=max(j for j,x in enumerate(rows) if x.startswith(b'O '));rows[at]=mutate(rows[at],decimal)
                return b''.join(rows)
            add(profile,label,error,builder,setup,{'count':len(setup)+1,'ident':ident,'drop_endcase':True})
        field_case('seq','INPUT_SEQ',lambda x,d:x.replace(('O '+str(len(setup)+1)+' ').encode(),b'O 99 ',1))
        field_case('word','INPUT_WORD',lambda x,d:x.replace(b' 0 ',b' 4294967296 ',1) if d else x.replace(b'00000000',b'0000000A',1))
        field_case('arity63','INPUT_ARITY',lambda x,d:b' '.join(x.rstrip(b'\n').split(b' ')[:-1])+b'\n')
        field_case('EOF-incomplete','INPUT_EOF',lambda x,d:b' '.join(x.rstrip(b'\n').split(b' ')[:-1]))
        field_case('opcode','INPUT_OPCODE',lambda x,d:b' '.join(x.split(b' ')[:2]+[b'99']+x.split(b' ')[3:]))
        field_case('decimal-seq','INPUT_DECIMAL',lambda x,d:x.replace(b'O ',b'O +',1))
        if profile=='DIRECT':
            for label,error,field,value in (('kind','INPUT_ENUM',0,3),('mode','INPUT_MODE',1,2),
                ('unused-minus0','INPUT_UNUSED',63,0x80000000),('cache-count65536','INPUT_CACHE',36,65536),
                ('cache-index256','INPUT_CACHE',37,256),('rotation','INPUT_ROTATION',12,0)):
                a=list(direct_call13c(mode=0));a[field]=value;bad=op13b(120,*a)
                add(profile,label,error,lambda d,bad=bad:profile_input13c(profile,setup+[bad],d),setup,
                    {'count':len(setup)+1,'ident':ident,'drop_endcase':True})
            a=list(direct_call13c(mode=0));a[18]=0;a[20:36]=[0]*16
            add(profile,'raw-count0','INPUT_DOMAIN',lambda d:profile_input13c('DIRECT',setup+[op13b(120,*a)],d),setup,
                {'count':2,'ident':1,'drop_endcase':True})
        else:
            wrong_bool=chain_op13b(target=1);aa=list(wrong_bool['a']);aa[5]=2;wrong_bool={**wrong_bool,'a':tuple(aa)}
            unused=op13b(103,1,0,0,0,m.bits(.5));aa=list(unused['a']);aa[63]=0x80000000;unused={**unused,'a':tuple(aa)}
            tests=[('range','INPUT_REGISTER_RANGE',op13b(101,1,0,16)),
                ('uninitialized','INPUT_REGISTER_UNINITIALIZED',op13b(101,1,0,1)),
                ('collision','INPUT_REGISTER_COLLISION',chain_op13b()),('bool','INPUT_BOOL',wrong_bool),
                ('enum','INPUT_ENUM',op13b(103,1,0,0,3)),('unused','INPUT_UNUSED',unused),
                ('raw-domain','INPUT_DOMAIN',op13b(103,0,0,0,0,m.bits(-1.))),
                ('rotation','INPUT_ROTATION',op13b(4,0,0,0,0,0,0)),('copy','INPUT_COPY',op13b(107,0)),
                ('mode','INPUT_MODE',op13b(103,2,0,0,0,m.bits(.5))),
                ('population','INPUT_POPULATION',chain_op13b([(j,0) for j in range(129)],target=1)),
                ('phase','INPUT_PHASE',op13b(45,0) if profile=='COMPONENT' else op13b(43,0))]
            if profile=='PUBLIC':tests.append(('O120-public','INPUT_PROFILE',op13b(120,*direct_call13c())))
            for label,error,bad in tests:
                add(profile,label,error,lambda d,bad=bad,p=profile,s=setup:profile_input13c(p,s+[bad],d),setup,
                    {'count':len(setup)+1,'ident':ident,'drop_endcase':True})
            for tag,error in (('P13B','INPUT_POINT'),('U13B','INPUT_MATERIAL')):
                def builder(decimal,tag=tag,profile=profile,setup=setup):
                    data=profile_input13c(profile,setup+[chain_op13b(target=1)],decimal);rows=data.splitlines(keepends=True)
                                                                             
                    indexes=[j for j,x in enumerate(rows) if x.startswith((tag+' ').encode())]
                    at=indexes[-(4 if tag=='P13B' else 1)];fields=rows[at].split();fields[3]=b'1';rows[at]=b' '.join(fields)+b'\n'
                    return b''.join(rows)
                add(profile,tag+'-index',error,builder,setup,{'count':len(setup)+1,'ident':ident,'drop_endcase':True})
                                                                            
        add(profile,'trailing-LF','INPUT_TRAILING_DATA',lambda d,p=profile,s=setup:profile_input13c(p,s,d)+b'\n',setup,
            {'count':len(setup),'ident':ident,'drop_endcase':False})
        if profile=='GUARD':
            add(profile,'second-G','INPUT_TRAILING_DATA',lambda d:profile_input13c('GUARD',setup,d)+b'G 1 0 0 1\n',setup,
                {'count':len(setup),'ident':1,'drop_endcase':False})
                                                                                
        for count in (0,33 if profile=='DIRECT' else 17 if profile=='GUARD' else 65 if profile=='COMPONENT' else 721):
            def builder(d,p=profile,count=count):
                data=profile_input13c(p,setup,d);rows=data.splitlines(keepends=True)
                at=1 if p=='GUARD' else max(j for j,x in enumerate(rows) if x.startswith(b'C '))
                fields=rows[at].split();fields[4 if p=='GUARD' else 2]=str(count).encode();rows[at]=b' '.join(fields)+b'\n'
                return b''.join(rows[:at+1])
            if profile=='PUBLIC':
                add(profile,'opCount'+str(count),'INPUT_OPCOUNT',builder,setup,
                    {'public_before_case':True,'header_N':385})
            else:add(profile,'opCount'+str(count),'INPUT_OPCOUNT',builder,
                literal=(header+' 1\n').encode())
        if profile!='PUBLIC':
            def wrong_id(d,p=profile):
                data=profile_input13c(p,setup,d)
                return data.replace(b'G 1 ',b'G 2 ',1) if p=='GUARD' else data.replace(b'C 1 ',b'C 2 ',1)
            add(profile,'initial-ID','INPUT_ID',wrong_id,literal=(header+' 1\n').encode())
        else:
            for error,tail in (('INPUT_ID',b'C 387 1\n'),('INPUT_OPCOUNT',b'C 386 0\n')):
                add(profile,'late-case-'+error,error,
                    lambda d,tail=tail,s=setup:profile_input13c('PUBLIC',s,d).replace(b'PORT13C 385\n',b'PORT13C 386\n',1)+tail,
                    setup,{'count':len(setup),'ident':385,'drop_endcase':False,'header_N':386})
        field_case('EOF-no-row','INPUT_EOF',lambda x,d:b'')
                                                                           
    legacy=load('negative13c_legacy12','ujemne-zywy.py')
    touching=(*legacy.setup(),legacy.body(slot=1),legacy.g.shape(1,parent=1,geometry=legacy.g.circle(r=1)),
              legacy.g.step(),legacy.op(46,0,0,1,0))
    prepared=[op13b(x[0],*x[1:]) for x in touching]
    malformed=op13b(51,0,0,m.bits(1.),0,0,3)
    add('COMPONENT','fixture-pointCount3','INPUT_FIXTURE_MANIFOLD',
        lambda d:profile_input13c('COMPONENT',prepared+[malformed],d),prepared,
        {'count':len(prepared)+1,'ident':1,'drop_endcase':True})
    capture=setup13b()+[op13b(41,0)]
    closed=capture+[op13b(k,0) for k in (42,43,44,45)]
    add('COMPONENT','capture-unclosed','INPUT_CAPTURE_UNCLOSED',
        lambda d:profile_input13c('COMPONENT',capture,d),closed,
        {'count':len(capture),'ident':1,'drop_endcase':True,'stop_after_seq':len(capture)})
    for label,field,value,error in (('physical-cache-count',36,65536,'INPUT_CACHE'),
        ('physical-cache-index',37,256,'INPUT_CACHE'),('helper-mode',1,2,'INPUT_MODE')):
        a=list(direct_call13c());a[field]=value;definition={'a':tuple(a)}
        add('GUARD',label,error,lambda d,definition=definition:encode_guard13c(definition,d),literal=b'GUARD13C 1\n')
                                                                            
    inherited=next(x for x in negative_definitions13b() if x['profile']=='GUARD13B' and x['error']=='INPUT_PROFILE')
    control,_,_=negative_prefix_control13b(inherited)
    inherited_row={'name':'GUARD/inherited-body-preSolve-profile','profile':'GUARD','error':'INPUT_PROFILE',
        'expected_stderr':b'PORT13C: INPUT_PROFILE\n','data_C':inherited['data_C'].replace(b'GUARD13B',b'GUARD13C'),
        'data_D':inherited['data_D'].replace(b'GUARD13B',b'GUARD13C'),
        'control_C':control.replace(b'GUARD13B',b'GUARD13C'),'control_D':negative_prefix_control13b(inherited,True)[0].replace(b'GUARD13B',b'GUARD13C'),
        'literal':None,'framing':{'count':4,'ident':1,'drop_endcase':True}}
    result.append(inherited_row)
    per=Counter(x['profile'] for x in result);m.require(all(n<=256 for n in per.values()),'F13 <=256 inputs per profile')
    return result


def negative_prefix_lines13c(path,framing):
    pass                                                                         
    ident=framing.get('ident',385)
    with Path(path).open('rb') as stream:
        for raw in stream:
            if raw.startswith(b'END '):continue
            if framing.get('header_N') and raw.startswith(b'PORT13C '):raw=f'PORT13C {framing['header_N']}\n'.encode()
            if framing.get('public_before_case'):
                if raw.startswith(b'CASE 385 '):break
                yield raw;continue
            if framing.get('drop_endcase') and raw==f'ENDCASE {ident}\n'.encode():continue
            if raw.startswith(b'G 1 ') and len(raw.split())==5:
                                                                          
                                                                        
                fields=raw.rstrip(b'\n').split(b' ');fields[4]=str(framing['count']).encode()
                raw=b' '.join(fields)+b'\n'
            if raw.startswith(f'CASE {ident} '.encode()):raw=f'CASE {ident} {framing['count']}\n'.encode()
            yield raw
            if framing.get('stop_after_seq') and raw.startswith(f'Z13 {ident} {framing['stop_after_seq']} '.encode()):break


def validate_control13c(path,data,profile):
    pass                                                                      
    source=data.decode('ascii').splitlines();header=source[0].split();N=int(header[1]);guard=profile=='GUARD'
    cases=[];at=1
    if guard:
        g=tuple(map(int,source[1].split()[1:]));ga=tuple(int(x,16) for x in source[2].split()[2:]);at=3
        case_specs=[(1,g[3])]
    else:case_specs=None
    while at<len(source) or guard and not cases:
        if guard:ident,count=case_specs[0]
        else:
            c=source[at].split();m.require(c[0]=='C','control input C');ident,count=map(int,c[1:]);at+=1
        ops=[]
        for seq in range(1,count+1):
            words=source[at].split();at+=1;m.require(words[:2]==['O',str(seq)],'control seq')
            code=int(words[2]);a=tuple(int(x,16) for x in words[3:]);points=[];materials=[]
            if code==100:
                for tag,amount,target in (('P13B',a[4],points),('U13B',a[6],materials)):
                    for j in range(amount):
                        words=source[at].split();at+=1;m.require(words[:4]==[tag,str(ident),str(seq),str(j)],'control group order')
                        target.append(tuple(int(x,16) for x in words[4:]))
            ops.append({'opcode':code,'a':a,'points':tuple(points),'materials':tuple(materials)})
        cases.append((ident,ops))
        if guard:break
    history=m.History13B();observations=[]
    with Path(path).open('rb') as stream:
        def take():
            raw=stream.readline(131073);m.require(raw and len(raw)<=131072,'control line envelope');return m.parse13c(raw)
        m.require(take()==(header[0],(N,)),'control output header')
        if guard:
            m.require(take()==('G',g) and take()==('GA',(1,*ga)),'control G/GA')
        for ident,ops in cases:
            m.require(take()==('CASE',(ident,len(ops))),'control CASE/count');cache=None;history.reset_case()
            direct=profile=='DIRECT' or profile=='PUBLIC' and ident<=384
            for seq,op in enumerate(ops,1):
                records=[];end='DC13' if direct else 'Z13'
                while not records or records[-1][0]!=end:
                    records.append(take());m.require(len(records)<=200000,'control snapshot row envelope')
                if direct:
                    checked=m.check_direct13c(records,ident,seq,op['a'],history=cache,
                        warm=ident in range(65,129) or ident in range(193,257) or ident in range(321,385))
                    cache=checked['cache']
                else:
                    mapped=[('E13B' if t=='E13C' else t,v) for t,v in records]
                    history.check(mapped,op,ident,seq,True,profile={'PUBLIC':13,'GUARD':14,'COMPONENT':15}[profile])
            m.require(take()==('ENDCASE',(ident,)),'control ENDCASE')
            observations.append({'id':ident,'operations':len(ops)})
        m.require(take()==('END',(N,)) and not stream.read(1),'control END/EOF')
    return {'END_EOF':True,'complete_prefix_models_checked':True,'cases':len(cases),'operations':sum(len(x[1]) for x in cases)}


def negative_stage13c(runtime,definitions=None):
    result=[]
    for definition in definitions if definitions is not None else negative_definitions13c():
        row={k:definition[k] for k in ('name','profile','error')};row['sides']={}
        try:
            with ExitStack() as stack:
                prefix_path=None
                if 'control_C' in definition:
                    code,prefix_path,error,meta=stack.enter_context(runtime.run('C',definition['control_C']))
                    m.require(code==0 and not error,'13c legal prefix C failed')
                                                                            
                                                                                
                    row['prefix_control']={'run':meta,'model':validate_control13c(prefix_path,definition['control_C'],definition['profile'])}
                def expected():
                    if definition['literal'] is not None:yield from definition['literal'].splitlines(keepends=True)
                    else:yield from negative_prefix_lines13c(prefix_path,definition['framing'])
                for side in ('C','D'):
                    code,path,error,meta=stack.enter_context(runtime.run(side,definition['data_'+side]))
                    difference=None
                    with path.open('rb') as stream:
                        for line,(wanted,actual) in enumerate(zip_longest(expected(),stream),1):
                            if wanted!=actual and difference is None:difference={'line':line,'expected':(wanted or b'')[:1024].decode('ascii',errors='replace'),'actual':(actual or b'')[:1024].decode('ascii',errors='replace')}
                    row['sides'][side]={'ok':code==2 and error==definition['expected_stderr'] and difference is None,
                        'run':meta,'stderr':error.decode('ascii',errors='replace'),'difference':difference}
                row['ok']=all(s['ok'] for s in row['sides'].values())
        except Exception as exc:row.update(ok=False,error=str(exc))
        result.append(row)
    return result


def parser_reachability13c(results=()):
    names=json.loads((HERE/'lancuchy-przypadki.json').read_text(encoding='utf-8'))['parserOdmowy']
    definitions=negative_definitions13c();observed={r['name']:r for r in results}
    return [{'id':'F13-'+str(j).zfill(2),'error':error,'profiles':{
        profile:{'reachable':any(d['profile']==profile and d['error']==error for d in definitions),
                 'variants':[{'name':d['name'],'both_native_ok':observed.get(d['name'],{}).get('ok',False)} for d in definitions if d['profile']==profile and d['error']==error],
                 'unverified_reason':None if any(d['profile']==profile and d['error']==error for d in definitions) else
                    'No physical field/route or required COMPONENT fixture still missing; not a green unreachable proof'}
        for profile in ('DIRECT','PUBLIC','GUARD','COMPONENT')}} for j,error in enumerate(names,1)]


def defined_nonhelper_mutation13c(recipe,anchor):
    pass                                                                         
    circle_edits=(('offset < 0.0f32','offset <= 0.0f32'),('if (v <= 0.0f32)','if (v < 0.0f32)'),
                  ('u <= 0.0f32','u < 0.0f32'),('uPrev <= 0.0f32','uPrev < 0.0f32'),
                  ('vNext > 0.0f32','vNext >= 0.0f32'),
                  ('separation > B2_SPECULATIVE_DISTANCE','separation >= B2_SPECULATIVE_DISTANCE'),
                  ('segmentA.ghost1','segmentA.ghost2'),
                  ('manifold.point0.anchorA = b2RotateVector(xfA.q, contactPointA);','manifold.point0.anchorA = Vec2();'),
                  ('manifold.point0.anchorB = b2Add(manifold.point0.anchorA, b2Sub(xfA.p, xfB.p));','manifold.point0.anchorB = Vec2();'),
                  ('manifold.point0.anchorB = b2Add(manifold.point0.anchorA, b2Sub(xfA.p, xfB.p));','manifold.point0.anchorB = manifold.point0.anchorA;'),
                  ('manifold.point0.point = b2Add(xfA.p, manifold.point0.anchorA);','manifold.point0.point = Vec2();'))
    if anchor.startswith('fun b2CollideChainSegmentAndCircle(') and 1<=recipe.get('case',0)<=128:
        if any(anchor.count(old)==1 and recipe['replacement']==anchor.replace(old,new,1) for old,new in circle_edits):
            return 'Circle-only legal prefix: fixed field/threshold edits, no arrays/cache/lifetime change; finite f32 geometry remains in domain'
    old='sim.manifold = contactManifold(entry.kind, a, xfA, b, xfB, &sim.cache);'
    if anchor.startswith('fun b2UpdateContact(') and 385<=recipe.get('case',0)<=432:
        if anchor.count(old)==1 and recipe['replacement']==anchor.replace(old,'sim.cache = distance.SimplexCache(); '+old,1):
            return 'Only zero cache initialization before unchanged contact call: count0 is the defined cold GJK path, no index/lifetime/ownership changes'
    functions={'b2ClipSegments','b2ClassifyNormal','b2CollideChainSegmentAndPolygon'}
    if 1<=recipe.get('case',0)<=384:
        for proposal in b.mutation_proposals13c():
            if proposal['function'] not in functions or not anchor.startswith('fun '+proposal['function']+'('):continue
            needle=proposal['needle']
            if anchor.count(needle)==1 and recipe['replacement']==anchor.replace(needle,proposal['replacement'],1):
                return ('Frozen direct domain: unchanged proxy counts2..8 and GJK indices; only threshold/axis/valid incident index0 or sentinel-1/ID1 or pointCount2->1 edits. '
                        'No buffer size, ownership, address, cache write or clip denominator changed; existing branch-local index bounds and wraps remain.')
    return None


def mutation_stage13c(runtime,bindings_path,out,*,pilot_only=False):
    pass                                                                          
    bindings_path=Path(bindings_path).resolve();m.require(bindings_path.is_relative_to(ROOT.resolve()),'13c recipes inside repo')
    manifest=json.loads(bindings_path.read_text(encoding='utf-8'))
    if not pilot_only:m.require(manifest.get('anchor_owner13c')=='T-13c-2a','13c anchor binding profile mismatch')
    recipes=manifest.get('recipes13c',[])
    m.require(recipes and len({r['id'] for r in recipes})==len(recipes),'nonempty unique13c native mutation list')
    duckc=runtime.compiler();m.require(sys.platform.startswith('linux') and duckc.is_file(),'official existing native compiler')
    guards={r['id']:r for r in guard_definitions13c()+supplementary_guards13c()};receipts=[]
    packing_guard=next(r for r in guard_definitions13b() if r['id']=='GB6-ID-PACKING')
    with tempfile.TemporaryDirectory(prefix='.13c-mutants-',dir=out) as temporary:
        directory=Path(temporary);physics=directory/'fizyka';shutil.copytree(ROOT/'silnik/fizyka',physics)
        witness_file=HERE/'lancuchy-receptury-13c.json'
        witness_data=json.loads(witness_file.read_text(encoding='utf-8'))
        witnesses=witness_data.get('witnesses13c',{})
        for original_recipe in recipes:
            recipe=dict(original_recipe);witness_overlay=witnesses.get(recipe['id'])
            if not recipe.get('guard') and not recipe.get('guard13b') and not recipe.get('case') and witness_overlay:
                recipe['case']=witness_overlay['case'];recipe['seq']=witness_overlay.get('seq')
            receipt={'id':recipe['id'],'requirement':recipe.get('requirement'),'port':recipe.get('port'),
                'changed_atom':recipe.get('changed_atom'),'anchor_owner':None if pilot_only else 'T-13c-2a',
                'pilot_only':pilot_only,'counted_as_final_kill':False,'baseline_ok':False,'single_hit':False,
                'native_executed':False,'clean':False,'definedness_verified':False,
                'detected':False,'witness':recipe.get('guard') or recipe.get('case')}
            if witness_overlay:
                receipt['witness_overlay']={'file':'silnik/port/lancuchy-receptury-13c.json','sha256':hashlib.sha256(witness_file.read_bytes()).hexdigest(),
                    'case':recipe.get('case'),'seq':recipe.get('seq'),'source_binding_unchanged':all(recipe.get(k)==original_recipe.get(k) for k in ('source','source_sha256','anchor','replacement','requirement','port','changed_atom'))}
            changed=None;original=None
            try:
                source=(ROOT/recipe['source']).resolve();m.require(source.is_relative_to((ROOT/'silnik/fizyka').resolve()),'physics product only')
                original=source.read_bytes();receipt['source_sha256']=hashlib.sha256(original).hexdigest()
                m.require(receipt['source_sha256']==recipe['source_sha256'],'exact final product SHA')
                text=original.decode('utf-8');anchor=recipe['anchor'];m.require(anchor and text.count(anchor)==1,'one exact product anchor hit')
                receipt['single_hit']=True
                legacy_packing=recipe.get('guard13b')=='GB6-ID-PACKING'
                guard=packing_guard if legacy_packing else guards.get(recipe.get('guard'))
                if legacy_packing:
                    m.require(guard['kind']==13,'only pure helper113 arithmetic')
                    cdata=encode_guard13b(guard).replace(b'GUARD13B',b'GUARD13C')
                    ddata=encode_guard13b(guard,True).replace(b'GUARD13B',b'GUARD13C')
                    receipt['witness']=guard['id'];receipt['definedness_scope']='helper113: pure fixed-width integer packing; no world/array/raw dereference'
                elif guard is not None:cdata,ddata=encode_guard13c(guard),encode_guard13c(guard,True)
                else:
                    generator=load('mutation13c_inputs','przypadki-lancuchy.py');cases=generator.cases13c(recipe['case'])
                    cdata=''.join(generator.text13c(cases)).encode('ascii');ddata=''.join(generator.text13c(cases,True)).encode('ascii')
                receipt['input_sha256']={'C':hashlib.sha256(cdata).hexdigest(),'D':hashlib.sha256(ddata).hexdigest()}
                with runtime.run('C',cdata) as crun,runtime.run('D',ddata) as drun:
                    for side,run,data in (('C',crun,cdata),('D',drun,ddata)):
                        m.require(run[0]==0 and not run[2],'healthy mutation baseline native exit/stderr')
                        if legacy_packing:
                            mapped=run[1].with_suffix('.13b')
                            m.require(run[1].stat().st_size<=65536,'pure helper113 output envelope')
                            mapped.write_bytes(run[1].read_bytes().replace(b'GUARD13C 1\n',b'GUARD13B 1\n',1))
                            validate_file13b(mapped,encode_guard13b(guard,side=='D'),side=='D',expected_guard=guard)
                            mapped.unlink()
                        elif guard is not None:validate_helper13c(run[1],guard)
                        else:validate_control13c(run[1],cdata,'PUBLIC' if recipe['case']>384 else 'DIRECT')
                        receipt['baseline_'+side]=run[3]
                    m.require(compare_files13b(crun[1],drun[1]) is None,'healthy mutation baseline C=D')
                    receipt['baseline_ok']=True
                    changed=physics/source.relative_to(ROOT/'silnik/fizyka');edited=text.replace(anchor,recipe['replacement'],1)
                    m.require(edited!=text,'mutation must change product');changed.write_text(edited,encoding='utf-8')
                    receipt['mutant_sha256']=hashlib.sha256(changed.read_bytes()).hexdigest()
                    build=directory/'build';build.mkdir(exist_ok=True);binary=build/'probe';binary.unlink(missing_ok=True)
                    config={'packages':[{'id':'fizyka','name':'fizyka','path':str(physics)},
                        {'id':'probe','name':'probe','path':str(ROOT/'silnik/port/lancuchy.dk'),'dependencies':[{'id':'fizyka'}]}],
                        'tasks':[{'package':'fizyka','strategy':'lib','output_file':'libfizyka.a'},
                            {'package':'probe','strategy':'native','output_file':'probe','linking_options':{'additional_link_options':[str(build/'libfizyka.a'),'-lm'],'link_c_standard_library':True}}]}
                    entry=ROOT/'silnik/port/lancuchy13c.dk'
                    if entry.is_file():
                                                                            
                                                                             
                        adapter=directory/'lancuchy-adapter.dk';body=(ROOT/'silnik/port/lancuchy.dk').read_text(encoding='utf-8')
                        old_entry='fun main() -> i64 = { return transportMain13(); }'
                        new_entry='fun legacyEntry13() -> i64 = { return transportMain13(); }'
                        m.require(body.count(old_entry)==1,'D4 one legacy entry')
                        adapter.write_text(body.replace(old_entry,new_entry,1),encoding='utf-8')
                        config['packages'].insert(1,{'id':'lancuchy_adapter','name':'lancuchy_adapter','path':str(adapter),'dependencies':[{'id':'fizyka'}]})
                        config['packages'][-1].update(path=str(entry),dependencies=[{'id':'fizyka'},{'id':'lancuchy_adapter'}])
                        config['tasks'].insert(1,{'package':'lancuchy_adapter','strategy':'lib','output_file':'liblancuchy_adapter.a'})
                        config['tasks'][-1]['linking_options']['additional_link_options']=[str(build/'liblancuchy_adapter.a'),str(build/'libfizyka.a'),'-lm']
                        receipt['driver_derivation']={'source_sha256':hashlib.sha256(body.encode()).hexdigest(),'replacements':1,'transport_body_unchanged':adapter.read_text(encoding='utf-8').replace(new_entry,old_entry,1)==body}
                    config_path=directory/'packages.json';config_path.write_text(json.dumps(config),encoding='utf-8')
                    argv=[str(duckc),'compile_packages',str(config_path),'-a',str(build),'-O','0'];started=time.monotonic()
                    attempts=[]
                    for attempt in range(2):
                        try:
                            compiled=subprocess.run(argv,capture_output=True,timeout=180);break
                        except subprocess.TimeoutExpired:attempts.append({'attempt':attempt+1,'timeout':True})
                    else:raise ValueError('Two isolated13c build timeouts; not a kill')
                    receipt['build']={'argv':argv,'code':compiled.returncode,'seconds':time.monotonic()-started,
                                      'stderr':compiled.stderr[-8192:].decode(errors='replace'),'timeout_attempts':attempts}
                    m.require(compiled.returncode==0 and binary.is_file(),'build failure is not a kill')
                    with binary.open('rb') as stream:m.require(stream.read(4)==b'\x7fELF','native ELF')
                    with runtime.run('D',ddata,binary) as mutant:
                        receipt['native_executed']=True;receipt['run']=mutant[3]
                        m.require(mutant[0]==0 and not mutant[2],'fatal/crash/stderr is not a clean kill')
                                                                             
                                                                             
                                                                           
                        with mutant[1].open('rb') as stream:
                            last=None
                            for raw in stream:
                                m.require(len(raw)<=131072,'mutant row envelope');last=m.parse13c(raw)
                            m.require(last is not None and last[0]=='END','mutant complete END/EOF')
                        difference=compare_files13b(drun[1],mutant[1])
                        if difference:
                            fields=difference['baseline'].split()
                            if len(fields)>=3 and fields[1].isdecimal() and fields[2].isdecimal():
                                receipt['first_difference_at']={'tag':fields[0],'id':int(fields[1]),'seq':int(fields[2])}
                                                                             
                                                                              
                                                                          
                        source_proof=defined_nonhelper_mutation13c(recipe,anchor)
                        defined=guard is not None or source_proof is not None
                        if source_proof:receipt['definedness_scope']=source_proof
                        receipt.update(clean=defined,definedness_verified=defined,
                                       detected=difference is not None,difference=difference)
                        if not defined:receipt['error']='World/direct mutation needs a definedness validator/proof beyond parse/exit; not a kill'
                        receipt['counted_as_final_kill']=bool(not pilot_only and defined and difference is not None)
            except Exception as exc:receipt['error']=str(exc)
            finally:
                if changed is not None and original is not None:changed.write_bytes(original)
            receipts.append(receipt)
            (Path(out)/('pilot-mutations13c.json' if pilot_only else 'mutations13c.json')).write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
    return receipts


def validate_population13c(full):
    pass                                                                  
    cases=full.get('cases',[])
    m.require([r['id'] for r in cases]==list(range(1,433)),'all432 ordered distinct case receipts')
    for row in cases:
        ident=row['id'];expected=0 if ident<=384 else 1200 if 421<=ident<=426 else 600
        for side in ('c0','c1','d'):
            m.require(row.get('streams',{}).get(side,{}).get('positive_steps')==expected,
                      f'case{ident}/{side} all{expected} positive Step')
    m.require(full.get('positive_steps')==32400,'all32400 positive Step')
    return True


def stage13c(ctx=None):
    started=time.monotonic();run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    out=ROOT/'RESULT-PORT13'/run/'13c';out.mkdir(parents=True,exist_ok=True)
    result={'code':1,'full_acceptance':False,'stages':{},'errors':[],'native_product_mutants':0}
    controls=unittest.defaultTestLoader.discover(str(HERE),'test_lancuchy_13c*.py')
    log=io.StringIO();checked=unittest.TextTestRunner(stream=log,verbosity=2).run(controls)
    (out/'selftests13c.csv').write_text(log.getvalue(),encoding='utf-8')
    result['stages']['stand_controls']={'run':checked.testsRun,'failures':len(checked.failures),'errors':len(checked.errors),'skips':len(checked.skipped)}
    if not checked.testsRun or not checked.wasSuccessful() or checked.skipped:result['errors'].append('13c self-controls missing/red/skipped')
    runtime=Runtime13C(out)
    guard_rows=[]
    for label,fn in (('guards22',guard_stage13c),('supplementary_GA2_GA3_GB4',lambda r:guard_stage13c(r,supplementary_guards13c())),
                     ('inherited_GB2_GB6',inherited_routes13c),
                     ('semantic_refusals',semantic_stage13c),('negative_parsers',negative_stage13c)):
        try:
            rows=fn(runtime);(out/(label+'.json')).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
            if label=='guards22':guard_rows=rows
            if label=='negative_parsers':(out/'F13.json').write_text(json.dumps(parser_reachability13c(rows),indent=2)+'\n',encoding='utf-8')
            result['stages'][label]={'required':len(rows),'ok':sum(r['ok'] for r in rows)}
            if not all(r['ok'] for r in rows):result['errors'].append(label+' missing/red native evidence')
        except Exception as exc:result['stages'][label]={'ok':False,'error':str(exc)};result['errors'].append(label+': '+str(exc))
    try:
        generator=load('audit13c_inputs','przypadki-lancuchy.py')
        audit=b.predicate_audit13c(generator.cases13c(),ROOT)
        (out/'predicate-audit13c.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
        result['stages']['predicate_audit']={'sites':len(audit['sites']),'direct_cases':len(audit['cases']),'post_GJK_verified':False}
    except Exception as exc:result['errors'].append('Predicate audit13c: '+str(exc))
                                                                              
                                                                            
    full_path=Path(os.environ.get('LANCUCHY_13C_FULL_RESULT',runtime.first_half/'full.json')).resolve()
    m.require(full_path.is_relative_to(ROOT.resolve()),'13c full evidence must be in this committed repository result tree')
    full=json.loads(full_path.read_text(encoding='utf-8')) if full_path.is_file() else {}
    population_ok=False
    try:population_ok=validate_population13c(full)
    except Exception as exc:result['errors'].append('Full population13c: '+str(exc))
    full_ok=bool(population_ok and full.get('word_comparison_ok') and full.get('global_END_checked') and
                 full.get('N')==432 and full.get('DIRECT')==384 and full.get('PUBLIC')==48 and
                 full.get('positive_steps')==32400 and full.get('models_checked') and
                 set(x['id'] for x in full.get('cases',[]))==set(range(1,433)))
    if not full_ok:result['errors'].append('Full432/DIRECT384/PUBLIC48/32400Step native model/words evidence missing/red')
    result['stages']['full_comparison']={'words_and_new_models_ok':full_ok,'full_ownership_ready':False,'path':str(full_path)}
    observations=[]
    processes_ok=bool(full.get('process_codes')) and all(x==0 for x in full['process_codes'].values()) and not any(full.get('stderr_bytes',{}).values())
    for row in full.get('cases',[]):observations.append({**row,'END_EOF':full.get('global_END_checked',False),
        'native_processes_ok':processes_ok,'independent_model_checked':full.get('models_checked',False)})
    source_bound=False
    for build_path in (runtime.first_half/'duckling-build.json',runtime.first_half.parent/'13a/duckling-build.json',runtime.first_half.parent/'13b/duckling-build.json'):
        if not build_path.is_file():continue
        build=json.loads(build_path.read_text(encoding='utf-8'))
        source_bound=bool(build.get('sources')) and all((ROOT/p).is_file() and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in build['sources'].items())
        source_bound=source_bound and build.get('sha256')==full.get('inputs',{}).get('d',{}).get('binary_sha256')
        if source_bound:break
    full['native_source_verified']=source_bound
    result['stages']['full_comparison']['native_source_verified']=source_bound
    if not source_bound:result['errors'].append('Full432 receipt is from another native binary/source snapshot')
    proofs=b.equivalence_proofs13c(ROOT,full)
    (out/'equivalence-proofs13c.json').write_text(json.dumps(proofs,indent=2)+'\n',encoding='utf-8')
    receipts=[];binding_path=Path(os.environ.get('LANCUCHY_13C_BINDINGS',HERE/'lancuchy-kotwice.json'))
    bound=json.loads(binding_path.read_text(encoding='utf-8')) if binding_path.is_file() else {}
    if bound.get('anchor_owner13c')=='T-13c-2a':
        try:
            receipts=mutation_stage13c(runtime,binding_path,out)
            result['stages']['native_mutations']={'required':len(receipts),'clean':sum(r['clean'] for r in receipts),'detected':sum(r['detected'] for r in receipts)}
            if not all(r['clean'] and r['detected'] for r in receipts):result['errors'].append('Final native13c mutations survived/unclean/missing')
        except Exception as exc:result['errors'].append('Final native13c mutations: '+str(exc))
    else:
        result['stages']['native_mutations']={'executed':False,'reason':'Final bound anchor manifest not supplied'}
        result['errors'].append('Final once-bound13c native mutation recipes missing')
    ledger=b.table13c(receipts,controls=guard_rows,observations=observations,product_root=ROOT,equivalences=proofs)
    (out/'galezie13c.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    result['stages']['branches']={'required':ledger['required'],'verified':ledger['verified'],'native_target_rows':ledger['native_target_rows'],
        'independent_native_count':ledger['independent_native_count']}
    if ledger['gaps']:result['errors'].append('13c branch gaps='+str(len(ledger['gaps'])))
    if not full.get('comparison_ok'):result['errors'].append('Inherited BASE12/full ownership acceptance remains red')
    result['native_product_mutants']=sum(r['clean'] and r['detected'] for r in receipts)
    result['code']=int(bool(result['errors']))
    result['seconds']=time.monotonic()-started
    (out/'13c-oslony-wynik.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result['code']


def stage(ctx=None):
    if '--13c' in sys.argv or os.environ.get('LANCUCHY_PART')=='13c' or getattr(ctx,'LANCUCHY_PART',None)=='13c':
        return stage13c(ctx)
    if '--13b' in sys.argv or os.environ.get('LANCUCHY_PART') == '13b' or getattr(ctx, 'LANCUCHY_PART', None) == '13b':
        return stage13b(ctx)
                                                                             
                                                                           
    run=os.environ.get('GITHUB_RUN_ID','lokalny')+'_'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    b13=ROOT/'RESULT-PORT13'/run/'13b/manifest.json'
                                                                    
    explicit13a = os.environ.get('LANCUCHY_PART') == '13a' or getattr(ctx, 'LANCUCHY_PART', None) == '13a'
    code13b=stage13b(ctx) if b13.is_file() and not explicit13a else None
    started = time.monotonic()
    out = Path(ctx.OUT) if ctx is not None else ROOT / os.environ.get('RESULT_DIR', 'RESULT-PORT/lokalny-lancuchy')
    if out.name != 'krok13':
        out = out / 'krok13'
    out = out.resolve()
    m.require(out.is_relative_to(ROOT.resolve()), 'results must remain in this worktree')
    out.mkdir(parents=True, exist_ok=True)
    result = {'code': 1, 'errors': [], 'native_product_mutants': 0, 'stages': {}}
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    controls = selftest()
    result['stages']['stand_controls'] = controls
    if not controls['ok']:
        result['errors'].append('Stand self-controls failed')
    runtime = Runtime(out)
    for label, function in (('guards', guard_stage), ('negative_parsers', negative_stage), ('positive_parsers', positive_parser_stage)):
        try:
            rows = function(runtime)
            save('13a-' + label + '.json', rows)
            result['stages'][label] = {'required': len(rows), 'ok': sum(r['ok'] for r in rows)}
            if not all(r['ok'] for r in rows):
                result['errors'].append(label + ': native failures/missing binaries')
            if label == 'negative_parsers':
                reachability = parser_reachability(rows)
                save('13a-F13-reachability.json', reachability)
                result['stages']['F13_reachability'] = {'required': 33, 'ok': sum(r['ok'] for r in reachability)}
                if not all(r['ok'] for r in reachability):
                    result['errors'].append('F13 catalogue incomplete/red')
        except Exception as exc:
            result['stages'][label] = {'ok': False, 'reason': str(exc)}
            result['errors'].append(label + ': ' + str(exc))
    full = None
    generator = None
    try:
        generator = load('lancuchy_stage_inputs', 'przypadki-lancuchy.py')
        semantic = semantic_refusal_stage(runtime, generator)
        save('13a-semantic-refusals.json', semantic)
        result['stages']['semantic_refusals'] = {'required': len(semantic), 'ok': sum(r['ok'] for r in semantic)}
        if not all(r['ok'] for r in semantic):
            result['errors'].append('Semantic refusal/next legal O failed')
        full, _ = full_stage(runtime, generator)
        save('13a-full-native.json', full)
        result['stages']['full_R_D_projection'] = {k: v for k, v in full.items() if k not in ('witnesses', 'case_observations')}
        if not full['ok']:
            result['errors'].append('Full C/D or R/D projection differs')
    except Exception as exc:
        result['stages']['full_R_D_projection'] = {'ok': False, 'reason': str(exc)}
        result['errors'].append('Full R/D/C native unavailable: ' + str(exc))
    receipts = []
    bindings = os.environ.get('LANCUCHY_BINDINGS')
    if bindings is None and (HERE / 'lancuchy-kotwice.json').is_file():
        bindings = 'silnik/port/lancuchy-kotwice.json'
    if bindings and full and full['ok']:
        try:
            bindings_path = (ROOT / bindings).resolve()
            m.require(bindings_path.is_relative_to(ROOT.resolve()), 'bindings must be committed inside repo')
            receipts = mutation_stage(runtime, generator, bindings_path, full, out)
            result['stages']['native_mutations'] = {'required': len(receipts), 'ok': sum(r['detected'] for r in receipts)}
        except Exception as exc:
            result['stages']['native_mutations'] = {'ok': False, 'reason': str(exc)}
    else:
        result['stages']['native_mutations'] = {'ok': False, 'reason': 'Missing product or bound mutation recipes'}
    witnesses = [{'requirement': r['requirement'], **r['witness']} for r in receipts if r.get('witness')]
    ledger = b.table(receipts, witnesses, full_result=full)
    save('13a-galezie.json', ledger)
    result['stages']['branches'] = {'required': ledger['required'], 'verified': ledger['verified'],
                                  'equivalent_proven': ledger['equivalent_proven'], 'gaps': ledger['gaps']}
    limit20 = next(r for r in ledger['rows'] if r['id'] == 'support-limit20')
    result['stages']['limit20'] = {'ok': limit20['verified'], 'status': limit20['status'],
                                 'classification': b.classification()['Q-20'], 'reason': limit20['gap_reason']}
    if ledger['code']:
        result['errors'].append('Unverified branch ledger: ' + str(len(ledger['gaps'])) + ' gaps')
    result['native_product_mutants'] = sum(r.get('detected', False) for r in receipts)
    equivalent_ids = {r['id'] for r in ledger['rows'] if r['status'] == 'EQUIVALENT_PROVEN'}
    result['equivalent_mutants_not_kills'] = sorted(equivalent_ids)
    if not receipts or not all(r.get('native_executed') and r.get('baseline_ok') and r.get('single_hit')
                               and r.get('clean') and (r['detected'] or r['requirement'] in equivalent_ids)
                               for r in receipts):
        result['errors'].append('Native product mutation evidence incomplete')
    if not result['stages']['limit20']['ok']:
        result['errors'].append('Q-20 GAP_UNVERIFIED: no legal witness20 or unreachability proof; joint12+13 acceptance remains open')
    result['seconds'] = time.monotonic() - started
    result['code'] = int(bool(result['errors']))
    save('13a-oslony-wynik.json', result)
    lines = ['# Krok13a — osłony', '', 'RESULT: ' + ('OK' if not result['code'] else 'FAIL / UNVERIFIED'), '',
             '| Etap | Wynik |', '|---|---|']
    lines += ['| ' + k + ' | ' + json.dumps(v, ensure_ascii=False).replace('|', '/') + ' |'
              for k, v in result['stages'].items()]
    lines += ['', '## Braki', ''] + ['- ' + e for e in result['errors']]
    (out / 'OSLONY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (out / 'etap-port-oslony-lancuchy-kod.csv').write_text(str(result['code']) + '\n', encoding='ascii')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if code13b is not None:
        return int(bool(result['code'] or code13b))
    return result['code']


if __name__ == '__main__':
    sys.exit(0 if selftest()['ok'] else 1) if '--self-test' in sys.argv else sys.exit(stage())
