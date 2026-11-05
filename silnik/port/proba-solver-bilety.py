pass                                                                       
from pathlib import Path

ID = 'W1-BILETY-PUBLIC10'

def case(g, path=None):
    path=Path(path) if path else Path(__file__).with_suffix('.csv')
    lines=path.read_text(encoding='ascii').splitlines()
    if lines[:2]!=['PORT10 1','C 1 13']:raise ValueError('W1 exact header/opcount')
    rows=[]
    for seq,line in enumerate(lines[2:],1):
        words=line.split(' ')
        if len(words)!=67 or words[:2]!=['O',str(seq)]:raise ValueError('W1 operation framing')
        row=(int(words[2]),*[int(x,16) for x in words[3:]])
        g.validate_operation(row);rows.append(row)
    if len(rows)!=13:raise ValueError('W1 exact scene length')
    return g.Case(1,ID,tuple(rows))

def check(stream, c, p):
    pass                                                                         
    records=[p.parse_record(line) for line in stream]
    positive=[seq for seq,op in enumerate(c.ops,1) if op[0]==32 and op[1]==0 and op[2]==0x3e800000]
    if len(positive)!=2:raise ValueError('W1 two positive owner0 Steps')
    for index,seq in enumerate(positive,1):
        rows={tag:[v for t,v in records if t==tag and len(v)>1 and v[:2]==(1,seq)] for tag in ('R','K','M','JW','Y')}
        if len(rows['R'])!=1 or rows['R'][0][3]!=0:raise ValueError('W1 real Step success')
        if len(rows['K'])!=1 or rows['K'][0][5:]!=(4,1,2) or len(rows['M'])!=2:raise ValueError('W1 two actual moves/Step')
        jw=[v for v in rows['JW'] if v[2]==0]
        if len(jw)!=1 or jw[0][3:5]!=(index,0) or jw[0][6]!=0:raise ValueError('W1 stepIndex/locked')
        force=[v for v in rows['Y'] if v[2]==0]
        if len(force)!=1 or force[0][3:5]!=(0,0):raise ValueError('W1 force finalized after each Step')
                                                                           
    last=len(c.ops)
    if [v[3] for t,v in records if t=='R' and v[:2]==(1,last)]!=[0]:raise ValueError('W1 other world succeeds')
    if [v[3:5] for t,v in records if t=='JW' and v[:3]==(1,last,0)]!=[(2,0)]:raise ValueError('W1 world isolation')
    return {'id':ID,'transport_id':1,'owner0_steps':2,'owner1_empty_steps':1,'full_C_D_and_OBS_required':True}
