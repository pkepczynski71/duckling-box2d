pass                                                                      

                                                                           
                                                                        
                                                                             
                                                                            
   
from collections import Counter, defaultdict
import importlib.util
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('sen_model_legacy', HERE / 'model-solver.py')
m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)
require, f32, number, bits, add, mul, div = m.require, m.f32, m.number, m.bits, m.add, m.mul, m.div
NULL = 0xffffffff
SCHEMA = {
    'PORT11': (1, 0), 'COMPONENT11': (1, 0), 'GUARD11': (1, 0), 'GR11': (3, 4),
    'SW11': (3, 2), 'GS11': (3, 10), 'WS11': (4, 4), 'BS11': (4, 6),
    'SS11': (4, 6), 'SD11': (5, 1), 'SM11': (5, 28), 'AB11': (4, None),
    'TR11': (4, 7), 'SP11': (3, 3), 'SF11': (4, 1), 'BP11': (3, 3),
    'BF11': (4, 1), 'I11': (2, 11), 'Z11': (2, 3),
}
COUNT_TAGS = ('WS11', 'BS11', 'SS11', 'SD11', 'SM11', 'AB11', 'TR11', 'SP11', 'SF11', 'BP11', 'BF11')
PRIVATE = frozenset(COUNT_TAGS + ('I11',))
ALL_PRIVATE = m.legacy.PRIVATE | PRIVATE | frozenset('W10 CX10 SB10 PK10 SC10 BV10 I10'.split())
ORDER = [
    ('E',), ('R',), ('V',), ('W',), ('B',), ('S', 'G'), ('L', 'A', 'Q'),
    ('QGN', 'QG'), ('SB',), ('K', 'M', 'MCN', 'MC'), ('CD',),
    *[(t,) for t in 'NC9 RC9 GV GL GE GC'.split()], ('HN10', 'HR10'),
    ('HC10', 'HG10'), ('SW11',), ('GS11',),
    *[(t,) for t in 'X P T F U H Y DN RT JW RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 TASK W10 CX10 SB10 PK10 SC10 BV10 WS11 BS11 SS11 SD11 SM11 AB11 TR11 SP11 SF11 BP11 BF11 I8 I9 I10 I11 Z8 Z9 Z10 Z11'.split()],
]
RANK = {tag: rank for rank, group in enumerate(ORDER) for tag in group}
                                                                    
RANK['TASK'] = -1


def parse(line):
    tag = line.split(' ', 1)[0]
    if tag not in SCHEMA:
        return m.parse(line)
    require(line.isascii() and line.endswith('\n') and '\r' not in line, tag + ': canonical ASCII/LF')
    words = line[:-1].split(' '); d, k = SCHEMA[tag]
    require(len(words) >= 1 + d, tag + ': prefix arity')
    values = []
    for i, word in enumerate(words[1:]):
        require((m.DEC if i < d else m.HEX).fullmatch(word) is not None, tag + ': canonical word')
        value = int(word, 10 if i < d else 16)
        require(value <= NULL, tag + ': u32'); values.append(value)
    if tag == 'AB11':
        require(len(values) >= d + 2, 'AB11 header')
        k = 2 + 2 * values[d]
        require(values[d] <= values[d + 1], 'AB11 count/capacity')
    require(len(values) == d + k, tag + ': payload arity')
    return tag, tuple(values)


def format_record(tag, values):
    if tag not in SCHEMA:
        return m.format_record(tag, values)
    d, _ = SCHEMA[tag]
    text = tag + ' ' + ' '.join(str(v) if j < d else f'{v:08x}' for j, v in enumerate(values)) + '\n'
    parse(text)
    return text


def index(rows, tag):
    d = SCHEMA.get(tag, m.SCHEMA.get(tag, m.legacy.SCHEMA.get(tag, (None,))))[0]
    if d is None:
        d = m.legacy.p8.DECIMALS[tag]
    out = {}
    for v in rows.get(tag, ()):
        key = v[2:d]
        require(key not in out, tag + ': duplicate prefix')
        out[key] = v[d:]
    require(list(out) == sorted(out), tag + ': prefix order')
    return out


def sleep_body_fit(count):
    return type(count) is int and 0 <= count <= 0x7fffffffffffffff and (count <= 128 or count // 4 + 3 <= 32767)


def world_parameters_valid(words):
    values = tuple(map(number, words[2:10]))
    return all(map(math.isfinite, values)) and values[2] > 0 and all(v >= 0 for v in values[3:])


def body_parameters_valid(words):
    values = tuple(map(number, words[4:14])); threshold = number(words[18])
    rotation_c, rotation_s = values[2:4]
    norm = add(mul(rotation_s, rotation_s), mul(rotation_c, rotation_c))
    return (words[3] in (0, 1, 2) and all(map(math.isfinite, values)) and
            values[7] >= 0 and values[8] >= 0 and math.isfinite(threshold) and threshold >= 0 and
            add(1, -f32(.0006)) < norm < add(1, f32(.0006)))


def sleep_velocity(velocity, angular, extent, delta, delta_s, inv_dt):
    pass                                                                       

                                                                          
       
    length = lambda v: f32(math.sqrt(add(mul(v[0], v[0]), mul(v[1], v[1]))))
    absolute = lambda x: -x if x < 0 else x                                       
    v = add(length(velocity), mul(absolute(angular), extent))
    d = add(length(delta), mul(absolute(delta_s), extent))
    correction = mul(mul(.5, inv_dt), d)
    return v if v > correction else correction


def pool(header, free, slots, label):
    require(header is not None and len(header) == 3, label + ': pool required')
    n, nf, nl = header
    require(nf <= n and nl == n - nf, label + ': logical pool counts')
    require(n == len(slots), label + ': sparse count before expansion')
    require(all(h[0] in (0,1) for h in slots.values()), label + ': alive is bool')
    require(len(free) == nf and len(set(free)) == nf and all(x < n for x in free), label + ': free stack')
    require(set(slots) == set(range(n)), label + ': all sparse slots')
    require({k for k, h in slots.items() if h[0]} == set(range(n)) - set(free), label + ': live/free partition')


def allocator_transition(before, after, allocations, releases, label):
    pass                                                                   
    n, free = before[0], list(before[1])
    for action, ident in (*allocations, *releases):
        if action == 'alloc':
            expected = free.pop() if free else n
            if expected == n: n += 1
            require(ident == expected, label + ': LIFO allocation')
        else:
            require(ident not in free and 0 <= ident < n, label + ': free live slot')
            free.append(ident)
    require((n, tuple(free)) == after, label + ': allocator transition')


def dfs_plan(seeds, edges, body_types):
    pass                                                                

                                                                           
                                                                           
                                                                    
       
    require(len(set(seeds)) == len(seeds), 'DFS unique seeds')
    seen_bodies, seen_contacts, result = set(), set(), []
    for seed in seeds:
        if seed in seen_bodies: continue
        require(body_types.get(seed) in (1, 2), 'DFS nonstatic seed')
        stack, bodies, contacts = [seed], [], []
        seen_bodies.add(seed)
        while stack:
            bid = stack.pop(); bodies.append(bid)
            for cid, other, touching in edges.get(bid, ()):
                if cid in seen_contacts or not touching: continue
                seen_contacts.add(cid); contacts.append(cid)
                require(other in body_types, 'DFS edge to live body')
                if body_types[other] != 0 and other not in seen_bodies:
                    require(other in seeds, 'DFS touching nonstatic body outside base island')
                    seen_bodies.add(other); stack.append(other)
        result.append((tuple(bodies), tuple(contacts)))
    return tuple(result)


class OwnershipModel(m.OwnershipModel):
    def __init__(self, fixture=None):
        self.fixture = fixture
        self.case_failures = []; self.continuity_gaps = []
        super().__init__()

    def begin_case(self):
        super().begin_case()
        self.positive = 0; self.next_seq = 1; self.prior_rows = None
        self.identities = {'W': {}, 'B': {}, 'S': {}}
        self.live_registers = {'W': set(), 'B': set(), 'S': set()}
        self.thresholds = {}; self.sleep_enabled = {}; self.world_sleep = {}; self.shape_parent = {}
        self.last_copies = {}; self.known_bodies = set(); self.known_shapes = set()
        self.raw_shape_numbers = {}; self.saved_contact_numbers = {}; self.event_copies = {}
        self.raw_handles = {'W': {}, 'B': {}, 'S': {}}
        self.case_failed = False

    def check(self, case, seq, operation, observations, private=True):
        if self.case != case:
            interrupted = self.case_failed
            previous_case, previous_ticket = self.case, self.last_ticket
            self.begin_case(); self.case = case
            if interrupted:
                                                                              
                                                                           
                                                                          
                self.continuity_gaps.append({'after_case':previous_case,'before_case':case,
                                             'last_verified_ticket':previous_ticket})
                self.last_ticket = None
            if case == 1 and self.last_ticket is None: self.last_ticket = 0
        try:
            require(not self.case_failed, 'model CASE already failed; cannot resume inside an unverified history')
            if self.fixture is not None and self.fixture.kind == 4 and seq == self.fixture.seed + 1:
                self.last_ticket = self.fixture.words[1] | self.fixture.words[2] << 32
            require(seq == self.next_seq, 'missing/duplicate/reordered snapshot')
            self.next_seq += 1
            rows = defaultdict(list)
            previous_rank = -1
            for tag, value in observations:
                require(value[:2] == (case, seq), tag + ': case/seq')
                                                                                   
                parse(format_record(tag, value))
                require(tag in RANK and RANK[tag] >= previous_rank, tag + ': snapshot group order')
                previous_rank = RANK[tag]
                rows[tag].append(value)
            require(rows['E'] == [(case, seq, *operation)], 'exact operation echo')
            self.allow_contact_speed_inf = (case == 61)
            self.snapshot(rows, private)
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            if not self.case_failed:self.case_failures.append({'case':case,'seq':seq,'error':repr(exc)})
            self.case_failed = True
            raise

    def snapshot(self, rows, private=True):
        require(len(rows.get('E', ())) == 1 and len(rows.get('R', ())) >= 1, 'E/R required')
                                                                              
                                                        
        legacy_rows = defaultdict(list, {k: v for k, v in rows.items() if k != 'Z8'})
        super().snapshot(legacy_rows, private)
        e = rows['E'][0]; opcode, a = e[2], e[3:]; status = rows['R'][0][3]
        require(all(v[3] in range(6) for v in rows['R']), 'game status domain')
        if opcode in (31, 32) and status == 0 and number(a[1]) > 0:
            self.positive += 1
        require(len(rows.get('Z11', ())) == 1, 'one Z11')
        require(rows['Z11'][0][2:] == (len(rows.get('SW11', ())), len(rows.get('GS11', ())), self.positive), 'Z11 completeness/positive Step count')
        require(len(rows.get('Z8', ())) == 1 and len(rows.get('Z9', ())) == 1, 'legacy public counters required')
        z8, z9 = rows['Z8'][0][2:], rows['Z9'][0][2:]
        require(z8[6:24] == tuple(len(rows.get(t, ())) for t in m.legacy.p8.PUBLIC_COUNTS), 'Z8 exact row counts')
        require(z9[3:10] == tuple(len(rows.get(t, ())) for t in ('NC9', 'RC9', 'CD', 'GV', 'GL', 'GE', 'GC')), 'Z9 exact row counts')
        require(z9[10:12] == (e[1], e[1]) and z9[12] in (5, 6, 7), 'Z9 snapshots/operations/profile')
        if private:
            for counter, tags in (('I8', ('X', 'P', 'T', 'F', 'U', 'H', 'Y', 'DN', 'RT', 'JW')),
                                  ('I9', ('RQ', 'CP', 'CF', 'CT', 'CA', 'CS', 'GB', 'CB', 'BL9', 'IP', 'IF', 'IS', 'IL', 'EB', 'EE0', 'EE1', 'EN9', 'TASK'))):
                require(len(rows.get(counter, ())) == 1, counter + ': required')
                require(rows[counter][0][2:2+len(tags)] == tuple(len(rows.get(t, ())) for t in tags), counter + ': exact record counts')
            task_headers = sum(v[3] == 0 for v in rows.get('TASK', ()))
            require(rows['I9'][0][-2:] == (task_headers, e[1]), 'I9 taskBlocks/completedSnapshots')
        sw, gs = index(rows, 'SW11'), index(rows, 'GS11')
        for h in sw.values():
            require(h[0] in (0, 1) and h[1] in (0, 1) and (h[0] == 0 or h[1] == 0), 'SW11 status/flag')
        for h in gs.values():
            require(h[0] in range(6) and all(x in (0, 1) for x in h[6:9]), 'GS11 flags/status')
            require(all(x == 0 for x in h[6:]) if h[0] else math.isfinite(number(h[9])) and number(h[9]) >= 0, 'GS11 refusal values/threshold')
            if not h[0]: require(not (h[6] and h[7]), 'awake and sleeping exclusive')
        self.history(rows)
        self.public_values(rows, private)
        if private:
            require(len(rows.get('I11', ())) == 1, 'one I11')
            require(rows['I11'][0][2:] == tuple(len(rows.get(t, ())) for t in COUNT_TAGS), 'I11 record completeness')
            self.ownership(rows)
            self.temporal(rows)
        else:
            require(not any(rows.get(t) for t in ALL_PRIVATE), 'OBS0 contains private records')
        self.prior_rows = rows

    def history(self, rows):
        e = rows['E'][0]; opcode, a = e[2], e[3:]; status = rows['R'][0][3]
        def body_status(owner, reg):
            if owner not in self.live_registers['W']: return 1
            if self.identities['B'][reg][3:5] != self.identities['W'][owner][1:3]: return 2
            return 0 if reg in self.live_registers['B'] else 1
        if opcode in (58, 59, 60, 62):
            expected = body_status(a[0], a[1])
            if expected == 0 and opcode == 60 and (not math.isfinite(number(a[3])) or number(a[3]) < 0): expected = 5
            require(status == expected, 'new body API world/owner/life/PARAM precedence')
        if opcode == 61: require(status == (0 if a[0] in self.live_registers['W'] else 1), 'world sleep setter lifetime')
        if opcode == 56:
            expected = 5 if not world_parameters_valid(a) else 3 if self.last_ticket == (1 << 64) - 1 else 0
            require(status == expected, 'createSleepWorld PARAM before ticket allocation')
        if opcode == 57:
            expected = 1 if a[0] not in self.live_registers['W'] else 5 if not body_parameters_valid(a) else 3 if self.last_ticket == (1 << 64) - 1 else 0
            require(status == expected, 'createSleepBody world then PARAM then LIMIT')
        creates = {0: ('W', 0), 54: ('W', 0), 56: ('W', 0), 2: ('B', 0),
                   30: ('B', 0), 57: ('B', 1), 10: ('S', 0), 17: ('S', 0), 40: ('S', 0)}
        if status == 0 and opcode in creates and rows['R'][0][4] in (1, 2, 3):
            tag, target = creates[opcode]; r = rows['R'][0]
            num = (r[5] - 1, *r[12:14], *r[10:12])
            self.identities[tag][a[target]] = num
            self.raw_handles[tag][a[target]] = tuple(r[5:8])
            self.live_registers[tag].add(a[target]); self.issue(num[1] | num[2] << 32)
            if tag == 'W': self.world_sleep[a[target]] = a[11] if opcode == 56 else 0
            if tag == 'B':
                self.thresholds[a[target]] = a[18] if opcode == 57 else 0x3d4ccccd
                self.sleep_enabled[a[target]] = a[16] if opcode == 57 else 0
            if tag == 'S': self.shape_parent[a[target]] = self.identities['B'].get(a[2])
            if tag == 'S': self.raw_shape_numbers[tuple(r[5:8])] = num
            if tag == 'B': self.known_bodies.add(num)
            if tag == 'S': self.known_shapes.add(num)
        if status == 0 and opcode == 16:
            for tag, target, r in zip(('B', 'S'), (a[0], a[1]), rows['R']):
                num = (r[5] - 1, *r[12:14], *r[10:12])
                self.identities[tag][target] = num
                self.raw_handles[tag][target] = tuple(r[5:8])
                self.live_registers[tag].add(target); self.issue(num[1] | num[2] << 32)
                if tag == 'B': self.thresholds[target] = 0x3d4ccccd; self.sleep_enabled[target] = 0
                else: self.shape_parent[target] = self.identities['B'][a[0]]
                if tag == 'S': self.raw_shape_numbers[tuple(r[5:8])] = num
                (self.known_bodies if tag == 'B' else self.known_shapes).add(num)
        if status == 0 and opcode == 1:
            self.live_registers['W'].discard(a[0]); birth = self.identities['W'][a[0]][1:3]
            for tag in ('B', 'S'):
                self.live_registers[tag] = {reg for reg in self.live_registers[tag] if self.identities[tag][reg][3:5] != birth}
        if status == 0 and opcode == 3:
            self.live_registers['B'].discard(a[1]); body_number = self.identities['B'][a[1]]
            self.live_registers['S'] = {reg for reg in self.live_registers['S'] if self.shape_parent.get(reg) != body_number}
        if status == 0 and opcode in (11, 18): self.live_registers['S'].discard(a[1])
        if status == 0 and opcode == 59: self.sleep_enabled[a[1]] = a[3]
        if status == 0 and opcode == 60: self.thresholds[a[1]] = a[3]
        if status == 0 and opcode == 61: self.world_sleep[a[0]] = a[2]
        for tag in ('W', 'B', 'S'):
            require({v[2] for v in rows.get(tag, ())} == self.live_registers[tag], tag + ': independent live register completeness')
            require(len(rows.get(tag, ())) == len(self.live_registers[tag]), tag + ': no duplicate live register')
            for v in rows.get(tag, ()):
                require(v[3:6] == self.raw_handles[tag][v[2]], tag + ': historical raw handle')
                identity = self.identities[tag][v[2]]
                if tag == 'W': require(v[8:10] == identity[1:3], 'world historical ticket')
                else: require(v[8:12] == (*identity[3:5], *identity[1:3]), tag + ': historical owner/birth')
                if tag == 'S':
                    parent = [reg for reg in self.live_registers['B'] if self.identities['B'][reg] == self.shape_parent[v[2]]]
                    require(len(parent) == 1 and v[12:15] == self.raw_handles['B'][parent[0]], 'shape live parent historical raw handle')
        require(set(index(rows, 'SW11')) == {(r,) for r in self.identities['W']}, 'SW11 initialized register completeness')
        require(set(index(rows, 'GS11')) == {(r,) for r in self.identities['B']}, 'GS11 initialized register completeness')
        for (reg,), h in index(rows, 'GS11').items():
            require(h[1:6] == self.identities['B'][reg], 'GS11 historical Number5')
            expected = body_status(a[0], reg) if opcode == 62 and reg == a[1] else (0 if reg in self.live_registers['B'] else 1)
            require(h[0] == expected, 'GS11 requested/ordinary lifetime status')
            if h[0] == 0:
                require(h[8:10] == (self.sleep_enabled[reg], self.thresholds[reg]), 'GS11 independently prescribed sleep flag/threshold bits')
                body = next(v for v in rows['B'] if v[2] == reg)
                require(h[6:8] == (body[27], int(body[28] and body[12] != 0 and not body[27])), 'GS11 awake/sleeping agrees with public body')
        for (reg,), h in index(rows, 'SW11').items():
            require(h == ((0, self.world_sleep[reg]) if reg in self.live_registers['W'] else (1, 0)), 'SW11 independent world lifetime/flag')
        if rows.get('CT'):
            ct = index(rows, 'CT')
            for reg in self.live_registers['W']:
                owner = self.identities['W'][reg][1:3]; key = owner[0] | owner[1] << 32
                old_contacts = self.contacts.get(key, {})
                live = {cid: h[18] | h[19] << 32 for (w, cid), h in ct.items() if w == reg and h[0]}
                issued = set()
                for rq in rows.get('RQ', ()):
                    if rq[2] != reg or not rq[9]: continue
                    cid = rq[10]
                    require(cid in live, 'created request has live ContactRecord')
                    if live[cid] != old_contacts.get(cid) and cid not in issued:
                        self.issue(live[cid]); issued.add(cid)
                require(all(old_contacts.get(cid) == birth or cid in issued for cid, birth in live.items()), 'contact allocation must follow consumed requests')
                self.contacts[key] = live
        last = rows['Z8'][0][-2] | rows['Z8'][0][-1] << 32
        require(rows['Z8'][0][2:8] == tuple(len(self.identities[t]) for t in ('W','B','S')) + tuple(len(self.live_registers[t]) for t in ('W','B','S')), 'Z8 independent saved/live counts')
        require(rows['Z9'][0][-2:] == rows['Z8'][0][-2:], 'Z9 same lastIssued')
        if rows.get('I11'): require(last == self.last_ticket, 'lastIssued exact independent allocations')
        elif opcode in (31, 32, 42) and status == 0:
            require(last >= self.last_ticket, 'public ticket monotonicity')
        else: require(last == self.last_ticket, 'read/refusal/transfer cannot issue ticket')
        self.last_ticket = last
        for v in rows.get('MC', ()):
            require(tuple(v[4:9]) in self.known_bodies, 'MC historical Number5')
        for v in rows.get('HG10', ()):
            if v[3] != 1:
                require(tuple(v[5:10]) in self.known_shapes and tuple(v[10:15]) in self.known_shapes, 'HG10 historical Number5')
        current = defaultdict(list)
        for v in rows.get('MC', ()): current[v[2]].append(tuple(v[4:]))
        for v in rows.get('MCN', ()):
            require(len(current[v[2]]) == v[3], 'MC count')
            if v[2] in self.last_copies and not (opcode == 32 and status == 0 and a[3] == v[2]):
                require(tuple(current[v[2]]) == self.last_copies[v[2]], 'MC changed outside successful copy')
            self.last_copies[v[2]] = tuple(current[v[2]])

    def public_values(self, rows, private):
        pass                                                                
        e = rows['E'][0]; opcode, a = e[2], e[3:]; status = rows['R'][0][3]
        nc = index(rows, 'NC9')
        require(len(rows.get('RC9', ())) == int(opcode in (46, 47)), 'RC9 presence')
        if opcode in (46, 47):
            r = rows['RC9'][0]
            require(r[2] == status and r[3] in (0, 1), 'RC9 status/has')
            if opcode == 46 and status == 0: self.saved_contact_numbers[a[3]] = tuple(r[4:9])
            if opcode == 46 and status: require(r[3:] == (0, NULL, 0, 0, 0, 0), '46 refusal empty value')
            if opcode == 47:
                require(r[4:9] == self.saved_contact_numbers[a[1]], 'lookup preserves historical ContactNumber')
                expected = 1 if a[0] not in self.live_registers['W'] else 2 if r[7:9] != self.identities['W'][a[0]][1:3] else None
                if expected is None and private:
                    c = index(rows, 'CT').get((a[0], r[4]))
                    expected = 0 if c and c[0] and c[18:20] == r[5:7] else 1
                if expected is not None: require(status == expected, 'contact lookup world/owner/lifetime precedence')
        require(nc == {(reg,): value for reg, value in self.saved_contact_numbers.items()}, 'NC9 historical completeness')
        require(bool(rows.get('GV')) == bool(opcode == 47 and status == 0), 'GV presence')
        for tag in ('GV', 'GL', 'GC'):
            grouped = defaultdict(list)
            for value in rows.get(tag, ()): grouped[value[2] if tag == 'GC' else 0].append(value)
            for values in grouped.values():
                p = 3 if tag == 'GC' else 2; phases = sorted({v[p] for v in values})
                mutate = opcode == {'GV':47, 'GL':48, 'GC':50}[tag] and bool(a[2] if tag != 'GC' else a[1])
                if tag == 'GC': mutate = mutate and values[0][2] == a[0]
                require(phases == ([0, 1, 2] if mutate and status == 0 else [0]), tag + ': exact phases')
                if len(phases) == 3:
                    norm = lambda phase: [v[:p] + v[p+1:] for v in values if v[p] == phase]
                    require(norm(0) == norm(2), tag + ': separate owned result')
                    if tag == 'GV' or len(norm(0)) > 1: require(norm(0) != norm(1), tag + ': nonempty mutation witness')
        blocks = {}
        for tag in ('GE', 'GC'):
            grouped = defaultdict(list)
            for v in rows.get(tag, ()):
                if v[3] == 0: grouped[v[2]].append(v)
                if v[4] in (1, 2) and v[3] != 1:
                    require(v[6:11] in self.known_shapes and v[11:16] in self.known_shapes, tag + ': historical ShapeNumbers')
            dest = {}
            for reg, values in grouped.items():
                head = values[0]
                require(head[4:6] == (0, 0) and len(head) == 10 and head[6] in range(6), tag + ': header')
                require(len(values) == 1 + head[7] + head[8], tag + ': actual event count before expansion')
                require([(v[4], v[5]) for v in values[1:]] == [(1,j) for j in range(head[7])] + [(2,j) for j in range(head[8])], tag + ': count/order')
                dest[reg] = tuple(v[4:] for v in values)
            blocks[tag] = dest
        expected_worlds = self.live_registers['W'] | ({a[0]} if opcode == 49 and status else set())
        require(set(blocks['GE']) == expected_worlds, 'GE live worlds and requested stale world')
        if opcode == 49 and status == 0: self.event_copies[a[1]] = blocks['GE'][a[0]]
        require(blocks['GC'] == self.event_copies, 'all retained event copies, including destroy/recycle')
        z9 = rows['Z9'][0][2:]
        require(z9[0] == len(nc) and z9[2] == len(self.event_copies), 'Z9 saved contacts/event copies')
        for value in rows.get('HG10', ()):
            if value[3] != 1: require(value[5:10] in self.known_shapes and value[10:15] in self.known_shapes, 'hit historical numbers')
        if opcode == 49 and status == 0:
            raw = [v[4:] for v in rows.get('HR10', ()) if v[2] == a[0]]
            copied = [v[5:] for v in rows.get('HG10', ()) if v[2:4] == (a[1], 0)]
            require(len(raw) == len(copied), 'fresh hit-copy count')
            for event, hit in zip(raw, copied):
                require(hit[:5] == self.raw_shape_numbers.get(event[:3]) and hit[5:10] == self.raw_shape_numbers.get(event[3:6]), 'hit stamped at emission before recycle')
                require(hit[10:] == event[6:], 'fresh hit-copy values')
        if not private: return
        ct = {k: h for k, h in index(rows, 'CT').items() if h[0]}
        cs = {(w, h[0]): h for (w, _, _, _), h in index(rows, 'CS').items()}
        require(z9[1] == len(ct), 'Z9 complete live contacts')
        require(sum(v[6] for v in rows.get('CD', ()) if v[4] == 0) == 2*len(ct), 'public capacities cover contacts twice')
        live_bodies = {(next(w for w in self.live_registers['W'] if self.identities['W'][w][1:3] == v[8:10]), v[3]-1) for v in rows.get('B', ())}
        cd_headers = {(v[2], v[3]): v[6:] for v in rows.get('CD', ()) if v[4] == 0}
        require(set(cd_headers) == live_bodies, 'CD each live body')
        for key, header in cd_headers.items():
            w, bid = key; bl = index(rows, 'BL9')[key]
            touching = [cid for cid in bl[5::2] if ct[w, cid][16] & 1]
            require(header == (bl[1], len(touching)), 'CD contact capacity/touching count')
            actual = [v[6:] for v in rows.get('CD', ()) if v[2:5] == (w, bid, 1)]
            expected = []
            def raw_shape(slot):
                matches = [v[3:6] for v in rows.get('S', ()) if v[3]-1 == slot and v[8:10] == self.identities['W'][w][1:3]]
                require(len(matches) == 1, 'current contact shape owner/slot')
                return matches[0]
            for cid in touching:
                c = ct[w, cid]; expected.append((*raw_shape(c[5]), *raw_shape(c[6]), *cs[w,cid][21:51]))
            require(actual == expected, 'CD actual touching edge order/cached manifold from owning set')
        def contact_value(w, cid):
            c = ct.get((w, cid)); require(c is not None, 'game contact view requires live contact')
            shapes = []
            for sid in c[5:7]:
                matches = [v for v in rows.get('S', ()) if v[3]-1 == sid and v[8:10] == self.identities['W'][w][1:3]]
                require(len(matches) == 1, 'game contact shape owner')
                shapes.extend(self.raw_shape_numbers[matches[0][3:6]])
            return (cid, *c[18:20], *self.identities['W'][w][1:3], *shapes, int(bool(c[16]&1)), *cs[w,cid][21:51])
        if opcode == 46 and status == 0:
            owner = self.identities['W'][a[0]][1:3]
            shape_ids = {self.identities['S'][reg][0] for reg in (a[1], a[2])}
            matches = [(cid, c) for (w,cid),c in ct.items() if w == a[0] and {c[5],c[6]} == shape_ids and len(shape_ids) == 2]
            require(len(matches) <= 1 and rows['RC9'][0][3] == bool(matches), 'find actual contact pair')
            wanted = (matches[0][0], *matches[0][1][18:20], *owner) if matches else (NULL,0,0,0,0)
            require(self.saved_contact_numbers[a[3]] == wanted, 'find exact ContactNumber')
        if opcode == 47 and status == 0:
            require([v[3:] for v in rows['GV'] if v[2] == 0] == [(0, *contact_value(a[0], self.saved_contact_numbers[a[1]][0]))], 'GV actual owning sim/manifold')
        if opcode == 48:
            values = [v for v in rows.get('GL', ()) if v[2] == 0]
            require(bool(values) and values[0][3:5] == (0,0), 'GL header')
            if status: require(len(values) == 1 and values[0][5:] == (status,0), 'GL refusal empty')
            else:
                bl = index(rows, 'BL9')[a[0], self.identities['B'][a[1]][0]]
                touching = [cid for cid in bl[5::2] if ct[a[0],cid][16]&1]
                require(values[0][5:] == (0,len(touching)), 'GL exact count')
                require([(v[3],v[4]) for v in values[1:]] == [(1,j) for j in range(len(touching))], 'GL dense order')
                require([v[5:] for v in values[1:]] == [contact_value(a[0],cid) for cid in touching], 'GL owning sim/contact edge order')
        for w in self.live_registers['W']:
            heads = index(rows, 'EN9'); hn = index(rows, 'HN10'); h = heads[w,]
            raw_begin = [v[4:] for v in rows.get('EB', ()) if v[2] == w]
            raw_end = [v[4:] for v in rows.get('EE'+str(1-h[3]), ()) if v[2] == w]
            require(h[:3] == (len(raw_begin), len([v for v in rows.get('EE0', ()) if v[2] == w]), len([v for v in rows.get('EE1', ()) if v[2] == w])) and h[3] in (0,1), 'raw event headers')
            wanted = [(0, 0, 0, len(raw_begin), len(raw_end), hn[w,][0])]
            for part, events in ((1, raw_begin), (2, raw_end)):
                for j, event in enumerate(events):
                    na, nb = self.raw_shape_numbers.get(event[:3]), self.raw_shape_numbers.get(event[3:6])
                    require(na is not None and nb is not None, 'raw event historical shape')
                    wanted.append((part, j, *na, *nb, *event[6:]))
            require(blocks['GE'][w] == tuple(wanted), 'GE historical emission manifold/previous end side')

    def ownership(self, rows):
        maps = {t: index(rows, t) for t in COUNT_TAGS if t not in ('TR11', 'WS11', 'AB11')}
        ss, sd, sm, bs = (maps[t] for t in ('SS11', 'SD11', 'SM11', 'BS11'))
        worlds = {v[2]: v for v in rows.get('W', ())}
        for tag in (*COUNT_TAGS, 'CP','CF','CT','CA','CS','GB','CB','BL9','IP','IF','IS','IL','EB','EE0','EE1','EN9','HN10','HR10','W10'):
            require(all(v[2] in worlds for v in rows.get(tag, ())), tag + ': only live owning worlds')
        for tag in ('CP','IP','EN9','HN10','W10'):
            require(set(index(rows, tag)) == {(w,) for w in worlds}, tag + ': complete live worlds')
        require({k[0] for k in ss} == set(worlds), 'SS11 live world completeness')
        for t in ('SP11', 'BP11'):
            require(set(maps[t]) == {(w,) for w in worlds}, t + ': live world completeness')
        bodies = {}; body_types = {}; public = {}
        y = {v[2]: v[3:] for v in rows.get('Y', ())}
        for v in rows.get('B', ()):
            owner = v[8:10]
            match = [w for w, wh in worlds.items() if wh[8:10] == owner]
            require(len(match) == 1, 'body world owner')
            w, bid = match[0], v[3] - 1
            require(v[2] in y, 'body Y required'); h = y[v[2]]
            require((w, bid) not in bodies, 'body sparse duplicate')
            bodies[w, bid] = (h[10], h[11]); body_types[w, bid] = v[12]; public[w, bid] = v
        require(set(bs) == set(bodies), 'BS11 live sparse completeness')
        for w in worlds:
            slots = {s: h for (owner, s), h in ss.items() if owner == w}
            sf = [h[0] for (owner, _), h in maps['SF11'].items() if owner == w]
            require([j for owner, j in maps['SF11'] if owner == w] == list(range(len(sf))), 'SF11 freeArray ordinals')
            pool(maps['SP11'][w,], sf, slots, 'solver sets')
            require(set(slots) >= {0, 1, 2} and all(slots[s][0:2] == (1, s) for s in range(3)), 'reserved sets alive')
            bf = [h[0] for (owner, _), h in maps['BF11'].items() if owner == w]
            require([j for owner, j in maps['BF11'] if owner == w] == list(range(len(bf))), 'BF11 freeArray ordinals')
            n, nf, nl = maps['BP11'][w,]
            require(n == nf + nl and len(bf) == nf and len(set(bf)) == nf, 'body pool counts/free uniqueness')
            require(n == len([b for owner,b in bodies if owner == w]) + len(bf), 'body pool sparse count before expansion')
            require({b for owner, b in bodies if owner == w} == set(range(n)) - set(bf), 'body pool live/free partition')
            dense_seen = set()
            for s, h in slots.items():
                if not h[0]:
                    require(h == (0, NULL, 0, 0, 0, 0), 'free solver-set canonical payload')
                else:
                    require(h[1] == s and h[3] == (h[2] if s == 2 else 0), 'stateCount only awake')
                    require(s != 1 or h[2] == 0, 'disabled body outside profile')
                    if s == 0: require(h[4:6] == (0, 0), 'static set has no contacts/islands')
                    if s == 1: require(h[5] == 0, 'disabled set has no islands')
                keys = [(owner, sid, j) for owner, sid, j in sd if (owner, sid) == (w, s)]
                require(len(keys) == h[2], 'SD11 actual dense count before expansion')
                require(keys == [(w, s, j) for j in range(h[2])], 'SD11 dense count/order')
                require({k for k in sm if k[:2] == (w, s)} == set(keys), 'SM11/SD11 completeness')
                for key in keys:
                    bid = sd[key][0]; sim = sm[key]
                    require(bid not in dense_seen and bodies.get((w, bid)) == (s, key[2]), 'body sparse/dense reciprocity')
                    require((s == 0) == (body_types[w, bid] == 0), 'static/nonstatic owning set')
                    dense_seen.add(bid)
                    require(sim[22] == bid and all(math.isfinite(number(x)) for x in sim[:22]), 'SM11 body/finite fields')
                    require(all(x in (0, 1) for x in sim[23:]), 'SM11 flags')
                    bh = bs[w, bid]
                    require(bh[5] == int(s == 2), 'BS11 BodyState ownership')
                    require(bh[2] in (0,1) and bh[3] in (0,1), 'BS11 flags')
                    require(math.isfinite(number(bh[0])) and number(bh[0]) >= 0 and math.isfinite(number(bh[1])) and number(bh[1]) >= 0, 'BS11 threshold/timer')
                    require(public[w, bid][27] == int(s == 2), 'B isAwake from owning set')
                    if s != 2:
                        require(public[w, bid][19:22] == (0, 0, 0), 'sleep/static velocity is +0')
            require(dense_seen == {b for owner, b in bodies if owner == w}, 'dense body completeness')
        dn = index(rows, 'DN')
        require({k for k in dn} == {(w, j) for (w, s, j) in sd if s == 2}, 'DN only current awake dense')
        for (w, j), raw in dn.items():
            require(raw[0] - 1 == sd[w, 2, j][0], 'DN/SD11 same awake order')
        for (reg,), h in index(rows, 'GS11').items():
            if h[0]: continue
            matches = [(key, v) for key, v in public.items() if v[2] == reg]
            require(len(matches) == 1, 'GS11 live public body')
            (w, bid), v = matches[0]
            require(h[6:9] == (v[27], int(v[28] and v[12] != 0 and not v[27]), bs[w, bid][2]), 'GS11 derived awake/sleeping/enable')
            require(h[9] == bs[w, bid][0], 'GS11/BS11 threshold bits including sign0')
        self.contacts_and_lists(rows, maps, body_types)
        self.moves_before_sleep(rows, bodies, public, maps)

    def moves_before_sleep(self, rows, bodies, public, maps):
        e = rows['E'][0]; opcode, a = e[2], e[3:]
        if opcode not in (31, 32) or rows['R'][0][3] != 0 or number(a[1]) <= 0: return
        moves = index(rows, 'M'); headers = index(rows, 'K')
        for (w,), h in headers.items():
            entries = [(j, value) for (ow, j), value in moves.items() if ow == w]
            require(len(entries) == h[-1], 'M actual count before expansion')
            require([j for j, _ in entries] == list(range(h[-1])), 'M count/dense finalization order')
            final_ids = {v[5] for v in rows.get('BV10', ()) if v[2:5] == (w, 0, 7)}
            require({value[0] - 1 for _, value in entries} == final_ids, 'M contains all pre-sleep finalized bodies')
            if self.prior_rows is not None:
                before = index(self.prior_rows, 'SD11')
                order = [v[0] for (ow, s, _), v in before.items() if ow == w and s == 2]
                for (ow, _), tr in index(rows, 'TR11').items():
                    if ow == w and tr[0] == 1 and tr[6]:
                        order.extend(v[0] for (bw, s, _), v in before.items() if bw == w and s == tr[2])
                require([value[0] - 1 for _, value in entries] == order, 'M order before wake/sleep RemoveSwap')
            for j, value in entries:
                bid = value[0] - 1; current = public[w, bid]; bh = maps['BS11'][w, bid]
                s, _ = bodies[w, bid]
                require(value[:3] == current[3:6] and value[3:7] == current[13:17], 'M raw identity/transform')
                require(value[-1] == int(s >= 3), 'M fellAsleep true after actual sleep')
                require(bh[4] == (NULL if s >= 3 else j), 'bodyMoveIndex from finalization before sleep')
            if opcode == 32 and a[0] == w:
                copy = [v[4:] for v in rows.get('MC', ()) if v[2] == a[3]]
                expected = []
                for _, value in entries:
                    current = public[w, value[0] - 1]
                    expected.append((current[3]-1, *current[10:12], *current[8:10], *value[3:]))
                require(copy == expected, 'MC faithful owned copy of finalized M')

    def contacts_and_lists(self, rows, maps, body_types):
        ct, cs, ca, islands = (index(rows, t) for t in ('CT', 'CS', 'CA', 'IS'))
        ss = maps['SS11']; occupied = defaultdict(set)
        for (w,cid),h in ct.items():
            if not h[0]: require(h == (0,NULL,NULL,NULL,NULL,*([0]*15)), 'free CT canonical payload')
            else:
                require(h[1] == cid and h[7] != h[10] and all((w,b) in body_types for b in (h[7],h[10])), 'CT sparse id and live distinct endpoints')
        for h in islands.values():
            if not h[0]: require(h == (0,NULL,NULL,NULL,*([0]*11)), 'free IS canonical payload')
        for (w,), header in maps['SP11'].items():
            require({(dom, idx) for ow, dom, idx in ca if ow == w} ==
                    {(0, s) for s in range(header[0])} | {(1, c) for c in range(12)}, 'all owning CA arrays')
        found = {}
        for (w, domain, owner, local), h in cs.items():
            cid = h[0]; require((w, cid) not in found, 'duplicate contact sim'); found[w, cid] = h
            c = ct.get((w, cid)); require(c is not None and c[0] == 1, 'CS requires live CT')
            require((domain, owner, local) == (int(c[3] != NULL), c[3] if c[3] != NULL else c[2], c[4]), 'contact sparse/dense reciprocity')
            require(h[3:5] == c[5:7] and h[51] in (0, 1) and (h[51] or h[11] == 0), 'CS identities/rolling defined')
            if c[16] & 1: require(h[51] == 1, 'touching contact has actually defined rolling material')
            m.legacy.manifold(h[21:51], 'sen current manifold')
            if domain == 0:
                require((w, owner) in ss and ss[w, owner][0] == 1, 'CS live owning set')
                require(owner != 0, 'contact cannot belong to static set')
                require((owner >= 3) == bool(c[16] & 1), 'sleeping touching / awake-disabled non-touching')
            else:
                require(c[2] == 2 and c[16] & 1, 'graph contact is awake/touching')
            if domain == 1 and owner < 11:
                for bid in (c[7], c[10]):
                    if body_types.get((w, bid)) == 0: continue
                    require(bid not in occupied[w, owner], 'ordinary graph color conflict')
                    occupied[w, owner].add(bid)
        require(set(found) == {k for k, h in ct.items() if h[0]}, 'all live contacts have exactly one sim')
        for (w, domain, owner), count in ca.items():
            require([j for ow, d, s, j in cs if (ow, d, s) == (w, domain, owner)] == list(range(count[0])), 'CS dense count/order')
            if domain == 0: require(count[0] == ss[w, owner][4], 'SS11 contactCount')
        for w in {k[0] for k in ss}:
            for header_tag, free_tag, slots, label in (('CP', 'CF', ct, 'contact'), ('IP', 'IF', islands, 'island')):
                header = index(rows, header_tag).get((w,))
                free = [h[0] for (ow, _), h in index(rows, free_tag).items() if ow == w]
                pool(header, free, {s: h for (ow, s), h in slots.items() if ow == w}, label)
            gb = index(rows, 'GB')
            require({c for ow, c in gb if ow == w} == set(range(12)), 'all graph colors')
            for c in range(12):
                h = gb[w, c]
                if c == 11: require(h == (0, 0, 0), 'overflow has no bodySet'); continue
                require(h[0] == 1 and h[1] <= h[2], 'graph bitset header')
                present = {64*j+k for j in range(h[1]) for k in range(64) if (h[3+2*j] | h[4+2*j] << 32) >> k & 1}
                require(present == occupied[w, c], 'graph bodySet exact occupancy')
            self.island_lists(w, rows, islands, ct, ss, body_types)

    def island_lists(self, w, rows, islands, contacts, sets, body_types):
        il = defaultdict(list)
        for v in rows.get('IL', ()):
            if v[2] != w: continue
            require(v[5] == len(il[v[3:5]]), 'IL dense ordinal')
            il[v[3:5]].append(v[6])
        live = {s: h for (ow, s), h in islands.items() if ow == w and h[0]}
        bl = {b: h for (ow, b), h in index(rows, 'BL9').items() if ow == w}
        require(set(bl) == {b for ow, b in body_types if ow == w}, 'all body edge headers')
        for bid, h in bl.items():
            current, previous, edges = h[0], NULL, []
            while current != NULL:
                cid, side = current >> 1, current & 1
                require((w, cid) in contacts and contacts[w, cid][0] and current not in edges, 'body edge cycle/dead')
                value = contacts[w, cid]; k = 7 + 3*side
                require(value[k:k+2] == (bid, previous), 'body edge owner/prev')
                edges.append(current); previous, current = current, value[k+2]
            require(h[1] == len(edges) and h[5:] == tuple(x for edge in edges for x in (edge >> 1, edge & 1)), 'body edge count/order')
            require({edge >> 1 for edge in edges} == {cid for (ow, cid), c in contacts.items() if ow == w and c[0] and bid in (c[7], c[10])}, 'body edge completeness')
        seen_islands = []
        for (ow, s), h in sets.items():
            if ow != w or not h[0]: continue
            require(len(il[0, s]) == h[5], 'SS11 islandCount')
            for j, ident in enumerate(il[0, s]):
                require(ident in live and live[ident][1:4] == (s, j, ident), 'island sparse/dense')
                seen_islands.append(ident)
        require(len(set(seen_islands)) == len(live) == len(seen_islands), 'island sim partition')
        body_seen, contact_seen = [], []
        body_sets = {h[0]: s for (ow, s, _), h in index(rows, 'SD11').items() if ow == w}
        for ident, h in live.items():
            require(h[10:13] == (NULL, NULL, 0), 'no joints')
            path = {ident}; parent = h[13]
            while parent != NULL:
                require(parent in live and parent not in path, 'island parent cycle/dead')
                path.add(parent); parent = live[parent][13]
            for kind, head, tail, count, source, pf, nf, of in (
                (1, h[4], h[5], h[6], bl, 3, 4, 2),
                (2, h[7], h[8], h[9], {c: v for (ow, c), v in contacts.items() if ow == w and v[0]}, 14, 15, 13)):
                seq = []; current = head; previous = NULL
                while current != NULL:
                    require(current in source and current not in seq, 'island list cycle/dead')
                    value = source[current]
                    require(value[pf] == previous and value[of] == ident, 'island list prev/owner')
                    seq.append(current); previous, current = current, value[nf]
                require(len(seq) == count and previous == tail and il[kind, ident] == seq, 'island list head/tail/count/order')
                if kind == 1: require(all(body_sets.get(bid) == h[1] for bid in seq), 'island/body same owning set')
                (body_seen if kind == 1 else contact_seen).extend(seq)
        require(len(body_seen) == len(set(body_seen)) and set(body_seen) == {b for (ow, b), t in body_types.items() if ow == w and t != 0}, 'nonstatic island body partition')
        require(len(contact_seen) == len(set(contact_seen)) and set(contact_seen) == {c for (ow, c), h in contacts.items() if ow == w and h[0] and h[16] & 1}, 'touching island contact partition')

    def temporal(self, rows):
        ws, ab, tr = (index(rows, t) for t in ('WS11', 'AB11', 'TR11'))
        worlds = {v[2] for v in rows.get('W', ())}
        require({(w, phase) for w, phase in ws if phase == 1} == {(w, 1) for w in worlds}, 'phase1 each live world')
        require(set(ab) == set(ws), 'AB11/WS11 phases')
        for (w, phase), h in ws.items():
            require(phase in (0, 1) and h[0] in (0, 1) and math.isfinite(number(h[3])), 'WS11 domain')
            if phase == 0: require(ab[w, 0] == ab[w, 1], 'phase1 retains pre-sleep activity bits')
        self.finalization(rows, ws)
        for w in worlds:
            entries = [(j, h) for (ow, j), h in tr.items() if ow == w]
            require([j for j, _ in entries] == list(range(len(entries))), 'TR11 ordinal')
            for _, h in entries:
                kind, obj, source, target, nb, nc, did = h
                require(kind in (1, 2, 3) and did in (0, 1), 'TR11 kind/didWork')
                if not did: require(source == target, 'TR11 no-op same set')
                elif kind == 1: require(source >= 3 and target == 2, 'wake owning sets')
                elif kind == 2: require(source == 2 and target >= 3, 'sleep owning sets')
                else: require(source == target == 2, 'split owning sets')
                                                                          
                                                                              
        if self.prior_rows is not None and rows['R'][0][3] != 0:
            stable = ('W', 'B', 'S', 'Y', 'BS11', 'SS11', 'SD11', 'SM11', 'SP11', 'SF11', 'BP11', 'BF11', 'CP', 'CF', 'CT', 'CA', 'CS', 'GB', 'IP', 'IF', 'IS', 'IL', 'MCN', 'MC')
            for tag in stable:
                strip = lambda rr: [v[2:] for v in rr.get(tag, ())]
                require(strip(rows) == strip(self.prior_rows), 'refusal atomicity: ' + tag)
        if self.prior_rows is not None:
            self.allocators(rows)
            self.merge_history(rows)
            self.transfer_values(rows)
            self.split_order(rows)
            e = rows['E'][0]
            if e[2] == 64 and e[4] == 3:
                old = index(self.prior_rows, 'IS').get((e[3], e[5]))
                if old is not None and old[0] and (old[1] != 2 or old[14] == 0):
                    called = [h for (w, _), h in tr.items() if w == e[3] and h[0] == 3]
                    require(len(called) == 1 and called[0][6] == 0, 'private Split early return really called once')
                    for tag in ('BS11', 'SS11', 'SD11', 'SM11', 'SP11', 'SF11', 'BP11', 'BF11', 'IP', 'IF', 'IS', 'IL', 'CT', 'CS', 'BL9'):
                        require([v[2:] for v in rows.get(tag, ())] == [v[2:] for v in self.prior_rows.get(tag, ())], 'private Split no-op state: '+tag)

    def split_order(self, rows):
        e = rows['E'][0]; opcode, a = e[2], e[3:]
        if rows['R'][0][3] != 0: return
        old = self.prior_rows
                                                                             
                                                                               
                                                                 
        if opcode == 64 and a[1] == 3:
            w, base_id = a[0], a[2]
        elif opcode == 58 and a[3] == 0:
            w = a[0]
            body = next((b for b in old.get('B', ()) if b[2] == a[1]), None)
            if body is None: return
            header = index(old, 'BL9').get((w, body[3]-1))
            if header is None: return
            base_id = header[2]
        else: return
        base_island = index(old, 'IS').get((w, base_id))
        if base_island is None or base_island[1] != 2 or base_island[14] == 0: return
        tr = [h for (ow, _), h in index(rows, 'TR11').items() if ow == w and h[0] == 3]
        require(len(tr) == 1 and tr[0][1:3] == (base_id, 2) and tr[0][4:7] == (base_island[6], base_island[9], 1), 'dirty Split actually executed once')
        def linked(rr, kind, owner):
            return tuple(v[6] for v in rr.get('IL', ()) if v[2:5] == (w, kind, owner))
        seeds = linked(old, 1, base_id); ct = index(old, 'CT'); edges = {}
        types = {b[3]-1: b[12] for b in old.get('B', ()) if b[8:10] == next(v[8:10] for v in old['W'] if v[2] == w)}
        for bid in seeds:
            h = index(old, 'BL9')[w, bid]; edges[bid] = []
            for cid, side in zip(h[5::2], h[6::2]):
                c = ct[w, cid]; other = c[10 if side == 0 else 7]
                edges[bid].append((cid, other, bool(c[16] & 1)))
        components = dfs_plan(seeds, edges, types)
        ip = index(old, 'IP')[w,]; n = ip[0]
        free = [h[0] for (ow, _), h in index(old, 'IF').items() if ow == w]
        free.append(base_id); ids = []
        for _ in components:
            ident = free.pop() if free else n
            if ident == n: n += 1
            ids.append(ident)
        require(index(rows, 'IP')[w,][0] == n, 'Split island nextIndex after destroy-before-allocate')
        require([h[0] for (ow, _), h in index(rows, 'IF').items() if ow == w] == free, 'Split island LIFO free order')
        current = index(rows, 'IS'); marks = index(rows, 'BS11'); contacts = index(rows, 'CT')
        for ident, (bodies, contact_ids) in zip(ids, components):
            require(linked(rows, 1, ident) == bodies and linked(rows, 2, ident) == contact_ids, 'Split DFS bodies/contacts exact linked order')
            require(current[w, ident][13:15] == (NULL, 0), 'Split recycled parent/removeCount initialized')
            require(all(marks[w, bid][3] == 1 for bid in bodies), 'Split body marks at push')
            require(all(contacts[w, cid][17] == 1 for cid in contact_ids), 'Split contact marks')
        awake = list(linked(old, 0, 2)); position = awake.index(base_id)
        awake[position] = awake[-1]; awake.pop(); awake.extend(ids)
        for (ow, _), h in index(rows, 'TR11').items():
            if ow == w and h[0] == 2 and h[6]:
                position = awake.index(h[1]); awake[position] = awake[-1]; awake.pop()
        require(linked(rows, 0, 2) == tuple(awake), 'Split/late sleep islandSim RemoveSwap order')

    def finalization(self, rows, ws):
        cx = index(rows, 'CX10')
        require({w for w, phase in ws if phase == 0} == {w for (w,) in cx}, 'phase0 only after real finalization')
        if not cx: return
        e = rows['E'][0]; require(e[2] in (31, 32) and number(e[4]) > 0, 'finalization requires positive Step')
        bs = index(rows, 'BS11'); sims = {(w, h[22]): h for (w, _, _), h in index(rows, 'SM11').items()}
        bv = index(rows, 'BV10'); bl = index(rows, 'BL9'); islands = index(rows, 'IS')
        require(self.prior_rows is not None, 'finalization needs previous complete snapshot')
        previous_bs = index(self.prior_rows, 'BS11'); previous_sd = index(self.prior_rows, 'SD11')
        moves = index(rows, 'M')
        for (w,), context in cx.items():
            candidate, best = NULL, 0.
            woken = set()
            for (ow, _), tr in index(rows, 'TR11').items():
                if ow == w and tr[0] == 1 and tr[6]:
                    woken.update(h[0] for (bw, s, _), h in previous_sd.items() if bw == w and s == tr[2])
            for (ow, _), event in moves.items():
                if ow != w: continue
                bid = event[0] - 1; state = bv.get((w, 0, 7, bid))
                require(state is not None and (w, bid) in sims, 'finalization body state/sim')
                threshold, timer, enabled = bs[w, bid][:3]
                value = tuple(map(number, state)); extent = number(sims[w, bid][18])
                speed = sleep_velocity(value[:2], value[2], extent, value[3:5], value[6], number(context[1]))
                if not ws[w, 0][0] or not enabled or speed > number(threshold): expected = 0.
                else:
                    require((w, bid) in previous_bs, 'previous sleep timer body')
                    start = 0. if bid in woken else number(previous_bs[w, bid][1])
                    expected = add(start, number(e[4]))
                require(timer == bits(expected), 'sleepTime reset / += whole dt in f32')
                island_id = bl[w, bid][2]; island = islands[w, island_id]
                if expected >= .5 and island[14] > 0 and expected > best:
                    candidate, best = island_id, expected
            require(ws[w, 0][2:] == (candidate, bits(best)), 'split candidate strict > tie / phase0')
            if ws[w,0][0]:
                for (ow,ident),island in islands.items():
                    if ow!=w or not island[0] or island[1]!=2 or island[14]!=0:continue
                    members=[v[6] for v in rows.get('IL',()) if v[2:5]==(w,1,ident)]
                    require(not members or any(number(bs[w,bid][1])<.5 for bid in members), 'eligible clean island must sleep after finalization')
            old_islands = index(self.prior_rows, 'IS'); current_islands = index(rows, 'IS')
            old_live = {i for (ow, i), h in old_islands.items() if ow == w and h[0]}
            current_live = {i for (ow, i), h in current_islands.items() if ow == w and h[0]}
            split = any(ow == w and h[0] == 3 and h[6] for (ow, _), h in index(rows, 'TR11').items())
            if old_live == current_live and not split:
                                                                             
                                                                              
                                                                                
                awake = [v[6] for v in self.prior_rows.get('IL', ()) if v[2:5] == (w, 0, 2)]
                for (ow, _), h in index(rows, 'TR11').items():
                    if ow == w and h[0] == 1 and h[6]:
                        awake.extend(v[6] for v in self.prior_rows.get('IL', ()) if v[2:5] == (w, 0, h[2]))
                active = {bl[w, bid][2] for (ow, bid), h in bs.items() if ow == w and number(h[1]) < .5 and bl[w, bid][2] != NULL}
                n = (len(awake)+63)//64; words = [0]*(2*n)
                for local, ident in enumerate(awake):
                    if ident in active: words[local//32] |= 1 << (local % 32)
                observed = index(rows, 'AB11')[w, 0]
                require(observed[0] == n and observed[2:] == tuple(words), 'phase0 activity uses island localIndex')

    def allocators(self, rows):
        old = self.prior_rows; e = rows['E'][0]; opcode, a = e[2], e[3:]
        before_worlds = {v[2]: v[8:10] for v in old.get('W', ())}
        for v in rows.get('W', ()):
            w = v[2]
            if before_worlds.get(w) != v[8:10]: continue
            def state(rr, header, free):
                return (index(rr, header)[w,][0], tuple(h[0] for (ow, _), h in index(rr, free).items() if ow == w))
            actions = []
            if rows['R'][0][3] == 0 and opcode in (2, 16, 30, 57):
                target = a[1] if opcode == 57 else a[0]
                body = next((b for b in rows.get('B', ()) if b[2] == target and b[8:10] == v[8:10]), None)
                if body is not None:
                    y = next(h for h in rows['Y'] if h[2] == target)
                    if y[13] >= 3: actions.append(('alloc', y[13]))
            for (ow, _), h in index(rows, 'TR11').items():
                if ow != w or not h[6]: continue
                if h[0] == 1: actions.append(('free', h[2]))
                if h[0] == 2: actions.append(('alloc', h[3]))
                                                                            
                                                                              
            if opcode == 3 and rows['R'][0][3] == 0 and w == a[0]:
                previous_y = next((h for h in old.get('Y', ()) if h[2] == a[1]), None)
                if previous_y is not None and previous_y[13] >= 3:
                    sid = previous_y[13]
                    current = index(rows, 'SS11').get((w, sid))
                    if current is not None and not current[0] and ('free', sid) not in actions:
                        actions.append(('free', sid))
            allocator_transition(state(old, 'SP11', 'SF11'), state(rows, 'SP11', 'SF11'), actions, [], 'solver set')
            previous_ids = {b[3]-1 for b in old.get('B', ()) if b[8:10] == v[8:10]}
            current_ids = {b[3]-1 for b in rows.get('B', ()) if b[8:10] == v[8:10]}
            created, removed = current_ids - previous_ids, previous_ids - current_ids
            require(len(created) <= 1 and len(removed) <= 1, 'body operation population delta')
            actions = [('alloc', b) for b in created] + [('free', b) for b in removed]
            allocator_transition(state(old, 'BP11', 'BF11'), state(rows, 'BP11', 'BF11'), actions, [], 'body')
            previous_contacts = {cid for (ow,cid),h in index(old, 'CT').items() if ow == w and h[0]}
            current_contacts = {cid for (ow,cid),h in index(rows, 'CT').items() if ow == w and h[0]}
            contact_allocations = [('alloc', r[10]) for r in rows.get('RQ', ()) if r[2] == w and r[9]]
            removed_contacts = previous_contacts - current_contacts
            if opcode in (31,32,43):
                                                                                
                release_order = sorted(removed_contacts)
            elif opcode in (3,11,18,53):
                if w != a[0]: release_order = []
                elif opcode == 53: release_order = [self.saved_contact_numbers[a[1]][0]]
                else:
                    bid = self.identities['B'][a[1]][0] if opcode == 3 else self.shape_parent[a[1]][0]
                    release_order = list(index(old, 'BL9')[w,bid][5::2])
                release_order = [cid for cid in release_order if cid in removed_contacts]
            else: release_order = []
            require(set(release_order) == removed_contacts and len(release_order) == len(removed_contacts), 'contact releases follow actual destroy traversal')
            allocator_transition(state(old, 'CP', 'CF'), state(rows, 'CP', 'CF'), contact_allocations,
                                 [('free', cid) for cid in release_order], 'contact')
            if opcode in (2,16,30,57,3) and rows['R'][0][3]==0:
                island_actions=[]
                if created:
                    bid=next(iter(created));body=next(b for b in rows['B'] if b[3]-1==bid and b[8:10]==v[8:10])
                    if body[12]!=0:island_actions.append(('alloc',index(rows,'BL9')[w,bid][2]))
                if removed:
                    bid=next(iter(removed));ident=index(old,'BL9')[w,bid][2]
                    if ident!=NULL and index(old,'IS')[w,ident][6]==1:island_actions.append(('free',ident))
                allocator_transition(state(old,'IP','IF'),state(rows,'IP','IF'),island_actions,[],'island create/destroy body')

    def merge_history(self, rows):
        pass                                                               
        old=self.prior_rows;e=rows['E'][0];opcode=e[2]
        if rows['R'][0][3] or opcode not in (31,32,44):return
        if opcode in (31,32) and number(e[4])<=0:return
        w=e[3];before=index(old,'IS');after=index(rows,'IS')
        if any(ow==w and h[0]==3 and h[6] for (ow,_),h in index(rows,'TR11').items()):return
        expected=defaultdict(int)
        if opcode==44:
            def root(ident):
                seen=set()
                while before[w,ident][13]!=NULL:
                    require(ident not in seen,'Merge parent cycle');seen.add(ident);ident=before[w,ident][13]
                return ident
            live={i:h for (ow,i),h in before.items() if ow==w and h[0]}
            for ident,h in live.items():expected[root(ident)]+=h[14]
            awake=[v[6] for v in old.get('IL',()) if v[2:5]==(w,0,2)]
            releases=[ident for ident in reversed(awake) if live[ident][13]!=NULL]
            prior_free=[h[0] for (ow,_),h in index(old,'IF').items() if ow==w]
            free=[h[0] for (ow,_),h in index(rows,'IF').items() if ow==w]
            require(free==prior_free+releases and index(old,'IP')[w,][0]==index(rows,'IP')[w,][0], 'Merge island pool release/LIFO order')
            lists={(kind,ident):[v[6] for v in old.get('IL',()) if v[2:5]==(w,kind,ident)] for kind in (1,2) for ident in live}
            for ident in releases:
                target=root(ident)
                for kind in (1,2):lists[kind,target].extend(lists[kind,ident])
                j=awake.index(ident);awake[j]=awake[-1];awake.pop()
            require([v[6] for v in rows.get('IL',()) if v[2:5]==(w,0,2)]==awake,'Merge islandSim RemoveSwap')
            for ident in set(live)-set(releases):
                for kind in (1,2):require([v[6] for v in rows.get('IL',()) if v[2:5]==(w,kind,ident)]==lists[kind,ident], 'Merge linked append order')
        else:
            current_bodies=index(rows,'BL9')
            for (ow,ident),h in before.items():
                if ow!=w or not h[0]:continue
                members=[v[6] for v in old.get('IL',()) if v[2:5]==(w,1,ident)]
                roots={current_bodies[w,bid][2] for bid in members}
                require(len(roots)==1,'Step without Split cannot separate an old island')
                expected[next(iter(roots))]+=h[14]
            current_contacts=index(rows,'CT')
            for (ow,cid),h in index(old,'CT').items():
                if ow!=w or not h[0] or not h[16]&1:continue
                current=current_contacts.get((w,cid))
                if current and current[0] and current[18:20]==h[18:20] and current[16]&1:continue
                candidates=[current_bodies[w,b][2] for b in (h[7],h[10]) if current_bodies[w,b][2]!=NULL]
                require(bool(candidates),'Unlink old touching contact has nonstatic owner')
                expected[candidates[0]]+=1
        require(set(expected)=={i for (ow,i),h in after.items() if ow==w and h[0]},'Merge live root partition')
        for ident,count in expected.items():require(after[w,ident][14]==count,'Merge removeCount sums parent/children and actual Unlink')

    def transfer_values(self, rows):
        e = rows['E'][0]; opcode = e[2]
        if rows['R'][0][3] != 0 or opcode not in (58, 59, 61, 64): return
        before, after = {}, {}
        for rr, dest in ((self.prior_rows, before), (rows, after)):
            for (w, _, _), h in index(rr, 'SM11').items(): dest[w, h[22]] = h
        require(before == after, 'pure sleep/wake preserves complete BodySim')
        cold_before, cold_after = index(self.prior_rows, 'CT'), index(rows, 'CT')
        hot_before = {(w, h[0]): h for (w, _, _, _), h in index(self.prior_rows, 'CS').items()}
        hot_after = {(w, h[0]): h for (w, _, _, _), h in index(rows, 'CS').items()}
        require(set(hot_before) == set(hot_after), 'pure transfer preserves contact identity')
        for key in hot_before:
            require(cold_before[key][18:20] == cold_after[key][18:20], 'transfer preserves ContactNumber ticket')
            require(hot_before[key][9:13] == hot_after[key][9:13] and hot_before[key][14:] == hot_after[key][14:], 'transfer preserves material/cache/manifold/rolling mask')
        for tag in ('EB', 'EE0', 'EE1', 'EN9', 'HR10'):
            require([v[2:] for v in rows.get(tag, ())] == [v[2:] for v in self.prior_rows.get(tag, ())], 'no contact event from pure transfer: '+tag)


def guard_result(item, records):
    if item.helper is not None:
        require([v for tag, v in records if tag == 'GR11'] == [item.helper_record()], item.name + ': exact GR11')


def validate_guard_stream(source, fixture, private=True, code=0, stderr=b'', build_code=0):
    pass                                                                    

                                                                              
                                                                               
                                                                             
                                                                   
       
    import hashlib
    import io
    require(build_code == 0 and code == 0 and stderr == b'', 'native build/process code/stderr')
    stream = io.StringIO(source) if isinstance(source, str) else source
    digest = hashlib.sha256(); count = Counter(); total = 0
    def take():
        nonlocal total
        line = stream.readline(65537)
        require(bool(line) and len(line) <= 65536, 'GUARD11 EOF / excessive line')
        raw = line.encode('ascii'); digest.update(raw); total += len(raw)
        record = parse(line); count[record[0]] += 1
        return record
    require(take() == ('GUARD11', (1,)), 'GUARD11 exact header')
    require(take() == ('G', (1, fixture.kind, fixture.seed, len(fixture.rows))), 'GUARD11 exact G')
    require(take() == ('GA', (1, *fixture.words)), 'GUARD11 exact GA echo')
    require(take() == ('CASE', (1, len(fixture.rows))), 'GUARD11 CASE')
    instance = OwnershipModel(fixture)
    statuses = {}; helper_seen = False
    for seq, operation in enumerate(fixture.rows, 1):
        records = []
        while True:
            record = take(); records.append(record)
            require(record[0] not in ('CASE', 'ENDCASE', 'END', 'GR11'), 'GUARD11 truncated snapshot')
            if record[0] == 'Z11': break
        instance.check(1, seq, operation, records, private)
        statuses[seq] = next(v[3] for t, v in records if t == 'R')
        if fixture.kind == 8 and seq == fixture.seed:
            require(take() == ('GR11', fixture.helper_record()), fixture.name + ': status-only GR11')
            helper_seen = True
    if fixture.helper is not None and not helper_seen:
        require(take() == ('GR11', fixture.helper_record()), fixture.name + ': exact GR11')
    if fixture.last_status is not None:
        require(statuses.get(len(fixture.rows)) == fixture.last_status, fixture.name + ': last game status')
    for seq, expected in fixture.status_at:
        require(statuses.get(seq) == expected, fixture.name + ': game status at ' + str(seq))
    require(take() == ('ENDCASE', (1,)) and take() == ('END', (1,)), 'GUARD11 ENDCASE/END')
    require(stream.read(1) == '', 'GUARD11 trailing output')
    return {'bytes': total, 'sha256': digest.hexdigest(), 'records': dict(count),
            'snapshots': len(fixture.rows), 'models_checked': True, 'fixture': fixture.name}


def validate_stream(source, cases, private=True, code=0, stderr=b'', build_code=0):
    pass                                                             

                                                                             
                                                                                
                                                                               
       
    import hashlib
    import io
    require(build_code == 0 and code == 0 and stderr == b'', 'native build/process code/stderr')
    stream = io.StringIO(source) if isinstance(source, str) else source
    digest = hashlib.sha256(); count = Counter(); total = 0
    def take():
        nonlocal total
        line = stream.readline(65537)
        require(bool(line) and len(line) <= 65536, 'EOF / excessive line')
        raw = line.encode('ascii'); digest.update(raw); total += len(raw)
        record = parse(line); count[record[0]] += 1
        return record
    tag, h = take()
    require(tag in ('PORT11', 'COMPONENT11', 'GUARD11') and h == (len(cases),), 'stream header/N')
    if tag == 'GUARD11':
        require(len(cases) == 1, 'GUARD11 one case')
        gtag, gh = take(); atag, ah = take()
        require(gtag == 'G' and gh == (1, 0, 0, len(cases[0])) and atag == 'GA' and ah == (1, *([0]*64)), 'GUARD11 kind0 exact frame')
    instance = OwnershipModel()
    for ident, operations in enumerate(cases, 1):
        require(take() == ('CASE', (ident, len(operations))), 'CASE input operation count/order')
        for seq, operation in enumerate(operations, 1):
            records = []
            while True:
                record = take(); records.append(record)
                require(record[0] not in ('END', 'ENDCASE', 'CASE'), 'truncated snapshot')
                if record[0] == 'Z11': break
            instance.check(ident, seq, operation, records, private)
        require(take() == ('ENDCASE', (ident,)), 'ENDCASE')
    require(take() == ('END', (len(cases),)), 'END/N')
    require(stream.read(1) == '', 'trailing output')
    return {'bytes': total, 'sha256': digest.hexdigest(), 'records': dict(count),
            'snapshots': sum(map(len, cases)), 'models_checked': True}
