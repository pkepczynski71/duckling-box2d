pass                                                                    

                                                                            
                                                                              
                                                                              
   
from collections import defaultdict


def stream(model, fixture, normative):
    records = [model.parse(line) for line in normative.splitlines(keepends=True)]
    first = [(t, v) for t, v in records if t not in ('GUARD11', 'G', 'GA', 'CASE', 'ENDCASE', 'END') and v[:2] == (1, 1)]
    second = [(t, v) for t, v in records if t not in ('GUARD11', 'G', 'GA', 'CASE', 'ENDCASE', 'END') and v[:2] == (1, 2)]
    def clone(seq):
        rows = defaultdict(list)
        for t, v in second: rows[t].append([1, seq, *v[2:]])
        return rows
    def one(rows, tag, tail): rows[tag] = [[1, rows['E'][0][1], *tail]]
    awake = clone(3); sleeping = clone(4)
    one(awake, 'E', fixture.op(58, 0, 0, 1, 1))
    awake['B'][0][27] = 1
    awake['GS11'][0][9:11] = [1, 0]
    awake['Y'][0][13] = 2
    awake['BS11'][0][9] = 1
    for v in awake['SS11']:
        if v[3] == 2: v[4:] = [1, 2, 1, 1, 0, 1]
        if v[3] == 3: v[4:] = [0, model.NULL, 0, 0, 0, 0]
    awake['SD11'][0][3] = 2; awake['SM11'][0][3] = 2
    awake['IS'][0][5] = 2
    for v in awake['IL']:
        if v[3] == 0: v[4] = 2
    one(awake, 'SP11', (0, 4, 1, 3))
    one(awake, 'SF11', (0, 0, 3))
    b = awake['B'][0]
    one(awake, 'DN', (0, 0, *b[3:6]))
    one(awake, 'TR11', (0, 0, 1, 3, 3, 2, 1, 0, 1))
    one(sleeping, 'E', fixture.op(32, 0, fixture.bits(.5), 1, 0))
    one(sleeping, 'R', (0, 0, 0, *([0]*9)))
    one(sleeping, 'K', (0, fixture.bits(.5), 1, 1, 1, 1))
    move = (*b[3:6], *b[13:17], *b[30:33], 1)
    one(sleeping, 'M', (0, 0, *move))
    number = sleeping['GS11'][0][4:9]
    one(sleeping, 'MCN', (0, 1))
    one(sleeping, 'MC', (0, 0, *number, *move[3:]))
    sleeping['BS11'][0][5] = fixture.bits(.5)
    one(sleeping, 'WS11', (0, 0, 1, model.NULL, model.NULL, 0))
    sleeping['WS11'].append([1, 4, 0, 1, 1, model.NULL, model.NULL, 0])
    one(sleeping, 'AB11', (0, 0, 1, 4, 0, 0))
    sleeping['AB11'].append([1, 4, 0, 1, 1, 4, 0, 0])
    one(sleeping, 'TR11', (0, 0, 2, 0, 2, 3, 1, 0, 1))
    one(sleeping, 'CX10', (0, fixture.bits(.5), fixture.bits(2), fixture.bits(.5), fixture.bits(2),
                         1, 0, 0, 0, 0, 0, 0, fixture.bits(1), fixture.bits(400), 1))
    one(sleeping, 'BV10', (0, 0, 7, 0, 0, 0, 0, 0, 0, fixture.bits(1), 0))
    sleeping['Z10'][0][-1] = 1
    sleeping['Z11'][0][-1] = 1
                                                                             
                                                                              
    for rows in (awake, sleeping):
        seq = rows['E'][0][1]
        for counter, tags in (
            ('I8', ('X', 'P', 'T', 'F', 'U', 'H', 'Y', 'DN', 'RT', 'JW')),
            ('I9', ('RQ', 'CP', 'CF', 'CT', 'CA', 'CS', 'GB', 'CB', 'BL9', 'IP', 'IF', 'IS', 'IL', 'EB', 'EE0', 'EE1', 'EN9', 'TASK')),
            ('I10', ('W10', 'CX10', 'SB10', 'PK10', 'SC10', 'BV10')),
            ('I11', model.COUNT_TAGS)):
            rows[counter][0][2:2+len(tags)] = [len(rows.get(t, ())) for t in tags]
        rows['Z8'][0][8:26] = [len(rows.get(t, ())) for t in model.m.legacy.p8.PUBLIC_COUNTS]
        rows['Z9'][0][12:14] = [seq, seq]
        rows['I9'][0][-2:] = [0, seq]
    order = ('E R V W B S G L A Q QGN QG SB K M MCN MC CD NC9 RC9 GV GL GE GC HN10 HR10 HC10 HG10 SW11 GS11 '
             'X P T F U H Y DN RT JW RQ CP CF CT CA CS GB CB BL9 IP IF IS IL EB EE0 EE1 EN9 W10 CX10 SB10 PK10 SC10 BV10 '
             'WS11 BS11 SS11 SD11 SM11 AB11 TR11 SP11 SF11 BP11 BF11 I8 I9 I10 I11 Z8 Z9 Z10 Z11').split()
    output = 'GUARD11 1\nG 1 0 0 4\nGA 1 ' + ' '.join(['00000000']*64) + '\nCASE 1 4\n'
    output += ''.join(model.format_record(t, v) for t, v in (*first, *second))
    for rows in (awake, sleeping):
        output += ''.join(model.format_record(t, v) for t in order for v in rows.get(t, ()))
    return output + 'ENDCASE 1\nEND 1\n'


def sleeping_contact_rows(model, fixture, normative):
    pass                                                                      

                                                                           
                                                                             
                                                                            
       
    rows = defaultdict(list)
    for line in normative.splitlines(keepends=True):
        tag, value = model.parse(line)
        if tag in model.RANK and value[:2] == (1, 2): rows[tag].append(list(value))
    N = model.NULL
    def one(tag, prefix, payload): rows[tag] = [[1, 2, *prefix, *payload]]
    for value in rows['SS11']:
        if value[3] == 3: value[6] = 2; value[8] = 1
    rows['SD11'].append([1, 2, 0, 3, 1, 1])
    one('CP', (0,), (1, 0, 1))
    one('CT', (0, 0), (1, 0, 3, N, 0, 0, 1, 0, N, N, 1, N, N, 0, N, N, 1, 0, 10, 0))
    for value in rows['CA']:
        if value[2:5] == [0, 0, 3]: value[5] = 1
    hot = [0]*52
    hot[:5] = [0, N, N, 0, 1]
    hot[9:13] = list(map(fixture.bits, (.5, .25, .125, -.25)))
    hot[14:21] = [1, 0, 1, 0, 0, 0, 0]
    hot[21:25] = [fixture.bits(1), 0, fixture.bits(.25), 1]
    hot[32:36] = [fixture.bits(.5), fixture.bits(.125), fixture.bits(.5), fixture.bits(-1)]
    hot[36:38] = [3, 1]
    hot[51] = 1
    one('CS', (0, 0, 3, 0), hot)
    one('BL9', (0, 0), (0, 1, 0, N, 1, 0, 0))
    rows['BL9'].append([1, 2, 0, 1, 1, 1, 0, 0, N, 0, 1])
    island = rows['IS'][0]
    island[9:14] = [1, 2, 0, 0, 1]
    rows['IL'] = [
        [1, 2, 0, 0, 3, 0, 0],
        [1, 2, 0, 1, 0, 0, 0], [1, 2, 0, 1, 0, 1, 1],
        [1, 2, 0, 2, 0, 0, 0],
    ]
    rows = defaultdict(list, {tag: list(map(tuple, values)) for tag, values in rows.items()})
    return rows, {t: model.index(rows, t) for t in model.COUNT_TAGS if t not in ('WS11', 'AB11', 'TR11')}, {(0, 0): 2, (0, 1): 2}


def contact_public_rows(model, fixture, normative):
    pass                                                                 
    rows, _, _ = sleeping_contact_rows(model, fixture, normative)
    rows['E'] = [(1, 2, *fixture.op(49, 0, 0))]
    verifier = model.OwnershipModel()
    verifier.live_registers['W'] = {0}; verifier.identities['W'][0] = (0,1,0,0,0)
    raw = ((1,0,1), (2,0,1)); numbers = ((0,3,0,1,0), (1,4,0,1,0))
    verifier.raw_shape_numbers = dict(zip(raw, numbers)); verifier.known_shapes = set(numbers)
    shape_rows = []
    for reg, (handle, number) in enumerate(zip(raw,numbers)):
        value = [0]*43; value[:3] = [1,2,reg]; value[3:6] = handle
        value[8:12] = [1,0,number[1],0]; shape_rows.append(tuple(value))
    rows['S'] = shape_rows
    body = list(rows['B'][0]); body[2] = 1; body[3] = 2
    rows['B'].append(tuple(body))
    manifold = rows['CS'][0][27:57]
    rows['CD'] = []
    for bid in (0,1):
        rows['CD'] += [(1,2,0,bid,0,0,1,1), (1,2,0,bid,1,0,*raw[0],*raw[1],*manifold)]
    rows['EB'] = [(1,2,0,0,*raw[0],*raw[1],*manifold)]
    rows['EN9'] = [(1,2,0,1,0,0,0,0)]
    rows['GE'] = [(1,2,0,0,0,0,0,1,0,0), (1,2,0,0,1,0,*numbers[0],*numbers[1],*manifold)]
    rows['GC'] = [(1,2,0,*v[3:]) for v in rows['GE']]
    value = list(rows['Z9'][0]); value[3] = 1; value[4] = 1; rows['Z9'][0] = tuple(value)
    return rows, verifier
