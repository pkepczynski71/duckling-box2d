pass                                                            

                                                           
                                                                         
   
import importlib.util
from pathlib import Path
import sys
spec=importlib.util.spec_from_file_location('pair_negative_inputs',Path(__file__).with_name('przypadki-pary.py'))
g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)

def variants():
    bases=tuple(g.encode(g.small_cases(),d) for d in (False,True))
    items=[]
    def add(name,pair,cause,duck):
        items.append((name,*pair,('PORT9A: '+cause+'\n').encode('ascii'),('BLAD: '+duck+('\n' if len(duck)==13 and duck[0]=='E' and all(c in '0123456789abcdef' for c in duck[1:]) else '.\n')).encode('ascii')))
    def change(line,token,h,d=None,base=bases):
        result=[]
        for dec,text in enumerate(base):
            rows=text.splitlines();ts=rows[line].split(' ')
            ts[token]=(str(int(h,16)) if d is None else d) if dec else h
            rows[line]=' '.join(ts);result.append(('\n'.join(rows)+'\n').encode('ascii'))
        return tuple(result)
                                                                            
                                                                          
    add('N-zero',(b'PORT9A 0\n',b'PORT9A 0\n'),'N','E8dc44deebc2b E7ef3142429d2')
    over=[]
    for dec in (False,True):
        sides=g.encode(g.cases()[:1],dec).splitlines()[2:]
        lines=['PORT9A 449']
        for ident in range(1,450):lines.extend([f'P {ident} 0',*sides])
        over.append(('\n'.join(lines)+'\n').encode('ascii'))
    add('N-over',tuple(over),'N','E8dc44deebc2b E7ef3142429d2')
    add('id-zero',change(1,1,'0','0'),'id','naglowek pary')
    add('id-skip',change(1,1,'2','2'),'id','naglowek pary')
    add('id-leading-zero',change(1,1,'01','01'),'canonical decimal','niekanoniczne u32')
    add('kind',change(1,2,'7','7'),'kind','naglowek pary')
    add('tag',change(2,1,'5','5'),'tag','tag geometrii')
    add('pair-types',change(1,2,'1','1'),'pair types','typy pary')
    add('unused',change(2,11,'00000001'),'unused geometry','nieuzywane slowo')
    add('unused-minus-zero',change(2,45,'80000000'),'unused geometry','nieuzywane slowo')
    add('NaN-position',change(2,2,'7fc00001'),'NaN / Inf','NaN/Inf')
    add('Inf-circle',change(3,6,'7f800000'),'NaN / Inf','NaN/Inf')
    add('NaN-rotation',change(2,4,'7fc00001'),'NaN / Inf','NaN/Inf')
    add('rotation',change(2,4,'00000000'),'rotation','obrot')
    add('circle-radius',change(3,8,'be800000'),'geometry','promien')
    add('capsule-radius',change(2,10,'be800000'),'geometry','promien')
                                        
    add('length-A',change(2,8,'bf800000'),'geometry','dlugosc A')
                                                  
    add('length-B',change(9,8,'bf400000'),'geometry','dlugosc B')
    add('polygon-count-small',change(5,6,'00000002'),'geometry','liczba wierzcholkow')
    add('polygon-count-large',change(5,6,'00000009'),'geometry','liczba wierzcholkow')
    add('polygon-count-u32-pattern',change(5,6,'7fc00001'),'geometry','liczba wierzcholkow')
    add('polygon-radius',change(5,7,'be800000'),'geometry','promien')
    add('polygon-hull',change(5,8,'00000000'),'geometry','otoczka')
    add('polygon-unused-point',change(5,16,'00000001'),'unused geometry','nieuzywany punkt')
    add('polygon-unused-tail',change(5,24,'00000001'),'unused geometry','nieuzywane slowo')
                                                                             
    one=g.small_cases()[5]
    from dataclasses import replace
    w=list(one.b.words);w[4]=g.bits(0);w[5]=g.bits(1.2);w[6]=g.bits(2**-12);w[7]=g.bits(1.2)
    short=replace(one,id=1,b=replace(one.b,words=tuple(w)))
                                                                              
    def raw(c,d):
        lines=['PORT9A 1',f'P 1 {c.kind}']
        for label,s in zip(('A','B'),(c.a,c.b)):
            lines.append(label+' '+str(s.tag)+' '+' '.join(str(u) if d else f'{u:08x}' for u in s.words))
        return ('\n'.join(lines)+'\n').encode('ascii')
    first=g.small_cases()[0];w=list(first.a.words);w[4]=g.bits(0);w[6]=g.bits(g.EPS)
    boundary=replace(first,id=1,a=replace(first.a,words=tuple(w)))
    add('length-A-equality',tuple(raw(boundary,d) for d in (False,True)),'geometry','dlugosc A')
    third=g.small_cases()[2];w=list(third.b.words);w[4]=g.bits(0);w[5]=g.bits(.8);w[6]=g.bits(g.EPS);w[7]=g.bits(.8)
    boundary=replace(third,id=1,b=replace(third.b,words=tuple(w)))
    add('length-B-equality',tuple(raw(boundary,d) for d in (False,True)),'geometry','dlugosc B')
    polygon=g.small_cases()[1];w=list(polygon.a.words)
    coords=[w[6+2*i:8+2*i] for i in range(4)]
    w[6:14]=[u for xy in reversed(coords) for u in xy]
    clockwise=replace(polygon,id=1,a=replace(polygon.a,words=tuple(w)))
    add('polygon-clockwise',tuple(raw(clockwise,d) for d in (False,True)),'geometry','otoczka')
    add('constructor-length-B',tuple(raw(short,d) for d in (False,True)),'geometry','dlugosc B')
    original=g.small_cases()[6];w=list(original.a.words);w[4]=g.bits(0);w[5]=g.bits(0);w[6]=g.bits(2**-12);w[7]=g.bits(0)
    short=replace(original,id=1,a=replace(original.a,words=tuple(w)))
    add('constructor-length-A',tuple(raw(short,d) for d in (False,True)),'geometry','dlugosc A')
    for name,h,d,cd,dd in (
        ('over-u32','100000000','4294967296','single space required','niekanoniczne u32'),
        ('short-word','0000000','00','canonical hex','niekanoniczne u32'),
        ('upper-or-sign','0000000A','+0','canonical hex','missing liczby u32')):
        add(name,change(2,2,h,d),cd,dd)
    for name,old,new,cd,dd in (
        ('header','PORT9A','PORT9B','header','naglowek PORT9A'),
        ('marker','A 1','X 1','marker','znacznik wiersza'),
        ('lone-CR','\n','\r','line ending / length','samotny CR'),
        ('empty-line','\n','\n\n','line ending / length','pusty lub brakujacy wiersz'),
        ('double-space','P 1','P  1','canonical decimal','missing liczby u32'),
        ('tab','A 1 ','A 1\t','single space required','wymagana pojedyncza spacja'),
        ('trailing-space','PORT9A 7\n','PORT9A 7 \n','N','nadmiar danych w wierszu'),
        ('NUL','PORT9A 7','PORT9A 7\x00','ASCII / line length','ASCII / dlugosc wiersza'),
        ('long-line','PORT9A 7','P'*2050,'ASCII / line length','ASCII / dlugosc wiersza')):
        add(name,tuple(b.replace(old,new,1).encode('ascii') for b in bases),cd,dd)
    add('trailing-data',tuple((b+'x').encode('ascii') for b in bases),'trailing data','E5659622a1b7e')
    add('truncated',tuple((b.splitlines()[0]+'\n').encode('ascii') for b in bases),'truncated input / read error','pusty lub brakujacy wiersz')
                                                                             
    boxwords=tuple([g.bits(x) for x in (0,0,1,0,1,1,0,0,1,0,.125)]+[0]*33)
    good=replace(g.small_cases()[5],id=1,a=g.Shape(4,boxwords))
    base=tuple(g.encode((good,),d) for d in (False,True))
    add('box-width',change(2,6,'00000000',base=base),'geometry','box')
    add('box-rotation',change(2,10,'00000000',base=base),'rotation','obrot')
    return tuple(items)
