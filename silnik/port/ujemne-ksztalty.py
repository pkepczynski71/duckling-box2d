pass                                                                            
import importlib.util
from pathlib import Path
import sys
_spec=importlib.util.spec_from_file_location('shape_negative_inputs',Path(__file__).with_name('przypadki-ksztalty.py'))
g=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=g;_spec.loader.exec_module(g)


def small_cases():
    return g.small_cases()


def variants():
    bases=[g.encode(small_cases(),decimal).replace('\r\n','\n') for decimal in (False,True)]
    def change(line,token,h,d=None):
        out=[]
        for decimal,base in enumerate(bases):
            rows=base.splitlines();ts=rows[line].split(' ')
            ts[token]=(str(int(h,16)) if d is None else d) if decimal else h
            rows[line]=' '.join(ts);out.append('\n'.join(rows).encode('ascii'))
        return tuple(out)
    items=[
        ('N-zero',tuple(b.replace('1\n','0\n',1).encode('ascii') for b in bases),'N','E8dc44deebc2b E7ef3142429d2.'),
        ('N-over',tuple(b.replace('1\n','97\n',1).encode('ascii') for b in bases),'N','E8dc44deebc2b E7ef3142429d2.'),
        ('nan',change(2,4,'7fc00000'),'NaN / Inf','NaN/Inf.'),
        ('inf',change(2,5,'7f800000'),'NaN / Inf','NaN/Inf.'),
        ('speed-zero',change(2,6,'00000000'),'world definition','maximumLinearSpeed.'),
        ('unused',change(2,7,'00000001'),'unused','nieuzywane slowo.'),
        ('unused-sign-zero',change(2,66,'80000000'),'unused','nieuzywane slowo.'),
        ('over-u32',change(2,3,'100000000','4294967296'),'single space required','niekanoniczne u32.'),
        ('leading-zero',change(2,3,'0000000','00'),'canonical hex','niekanoniczne u32.'),
        ('sign',change(2,3,'0000000A','+0'),'canonical hex','missing liczby u32.'),
        ('seq',change(2,1,'2','2'),'seq','seq.'),
        ('seq-zero',change(2,1,'01','01'),'canonical decimal','niekanoniczne u32.'),
        ('opcode',change(2,2,'6','6'),'opcode','opcode.'),
        ('body-type',change(3,5,'00000003'),'body definition','typ ciala.'),
        ('body-bool',change(3,13,'00000002'),'bool','fixedRotation.'),
        ('rotation-zero',change(3,8,'00000000'),'rotation','obrot.'),
        ('rotation-at-lower',change(3,8,'3f7fec56'),'rotation','obrot.'),
        ('rotation-at-upper',change(3,8,'3f8009d4'),'rotation','obrot.'),
        ('shape-tag',change(4,6,'00000005'),'tag','tag geometrii.'),
        ('shape-bool',change(4,8,'00000002'),'bool','updateMass.'),
        ('shape-nan',change(4,7,'7fc00000'),'NaN / Inf','NaN/Inf.'),
        ('raw-density',change(4,7,'bf800000'),'raw density','density raw.'),
        ('raw-radius',change(4,20,'bf800000'),'raw geometry','geometria raw.'),
        ('geometry-unused',change(4,21,'00000001'),'unused geometry','E296098d67338 Ec2dbf4ab3469 E8886cbca14d1.'),
    ]
    for name,old,new,cdiag,ddiag in (
        ('lone-cr','\n','\r','line ending / length','samotny CR.'),
        ('empty-line','\n','\n\n','line ending / length','pusty lub brakujacy wiersz.'),
        ('double-space','O 1 0','O  1 0','canonical decimal','missing liczby u32.'),
        ('tab','O 1 0','O\t1 0','single space required','wymagana pojedyncza spacja.'),
        ('trailing-space','\n',' \n','N','nadmiar danych w wierszu.'),
        ('nul','1\n','1\x00hidden\n','ASCII / line length','ASCII / dlugosc wiersza.'),
    ):
        items.append((name,tuple(b.replace(old,new,1).encode('ascii') for b in bases),cdiag,ddiag))
                                                                             
    items.append(('truncated',tuple(b[:-4].encode('ascii') for b in bases),'canonical hex','wymagana pojedyncza spacja.'))
    return tuple((name,c,d,('PORT7: '+cd+'\n').encode('ascii'),('BLAD: '+dd+'\n').encode('ascii')) for name,(c,d),cd,dd in items)
