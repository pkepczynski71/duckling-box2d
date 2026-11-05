pass                                                                      
from dataclasses import replace
import io
import tempfile
import unittest
from pathlib import Path
from test_pary import HERE,g,p,module

def fixture(rows=None):
    rows=rows or (replace(g.cases()[1],id=1),)
    lines=[p.format_record('PORT9A',(len(rows),))]
    for c in rows:
        words=[0]*30
                                                                         
        if c.kind==0 and c.name=='spec-equal':
            y=g.bits(g.f32(g.number(c.b.words[5])*.5))
                                                                    
            words[1]=0x3f7fffff;words[3]=1
            for i in (5,7,9):words[i]=y
            words[10]=g.bits(.02)
        lines += [p.format_record('E',p.echo(c)),p.format_record('M',(c.id,*words)),p.format_record('ENDCASE',(c.id,))]
    lines.append(p.format_record('END',(len(rows),)))
    return tuple(rows),''.join(lines)

def mutate(text,tag,index,value):
    lines=text.splitlines(keepends=True)
    for i,line in enumerate(lines):
        t,values=p.parse_record(line)
        if t==tag:
            values=list(values);values[index]=value;lines[i]=p.format_record(tag,values);return ''.join(lines)
    raise AssertionError('missing tag')

class Completeness(unittest.TestCase):
    def test_hand_ledger_exact_equality_case(self):
        rows,text=fixture();model=p.validate_output(io.StringIO(text),rows)
        self.assertEqual(model['N'],1);self.assertEqual(model['manifolds'][1][3],1)
        self.assertEqual(model['records'],{'PORT9A':1,'E':1,'M':1,'ENDCASE':1,'END':1})
    def test_all_448_ids_and_all_echo_words_are_checked(self):
        rows,text=fixture(g.cases());self.assertEqual(p.validate_output(io.StringIO(text),rows)['N'],448)
        for index in range(92):
            bad=mutate(text,'E',index,p.parse_record(text.splitlines(keepends=True)[1])[1][index]^1)
            with self.assertRaises(ValueError):p.validate_output(io.StringIO(bad),rows)
    def test_missing_duplicate_extra_or_reordered_records_fail_independently(self):
        rows,text=fixture();lines=text.splitlines(keepends=True)
        variants=[ ''.join(lines[:i]+lines[i+1:]) for i in range(len(lines))]
        variants += [text+lines[-1],''.join(lines[:2]+[lines[2]]+lines[2:]),''.join([lines[0],lines[2],lines[1],*lines[3:]])]
        for bad in variants:
            with self.assertRaises(ValueError):p.validate_output(io.StringIO(bad),rows)
    def test_counters_and_ids_cannot_be_forged_on_both_sides(self):
        rows,text=fixture()
        for tag,index,value in (('PORT9A',0,2),('M',0,2),('ENDCASE',0,2),('END',0,2),('M',4,3)):
            bad=mutate(text,tag,index,value)
            with self.assertRaises(ValueError):p.validate_output(io.StringIO(bad),rows)
    def test_each_of_thirty_result_words_is_compared_without_epsilon(self):
        rows,text=fixture()
        words=p.validate_output(io.StringIO(text),rows)['manifolds'][1]
        for index in range(30):
            value=words[index]^1
            bad=mutate(text,'M',index+1,value)
            difference=p.first_difference(io.StringIO(text),io.StringIO(bad))
            self.assertEqual(difference['id'],1);self.assertEqual(difference['field'],p.FIELDS[index])
    def test_sign_of_zero_is_a_bit_difference(self):
        rows,text=fixture();bad=mutate(text,'M',1,0x80000000)
        p.validate_output(io.StringIO(bad),rows)
        self.assertEqual(p.first_difference(io.StringIO(text),io.StringIO(bad))['field'],'normal.x')
    def test_strict_syntax_and_bounded_lines(self):
        for line in ('M 01 '+'00000000 '*29+'00000000\n','M 1 '+'0000000A '*29+'00000000\n',
                     'X 1\n','P'*2049+'\n','END 1\r\n','END 1','END 1 \n','END\t1\n'):
            with self.assertRaises(ValueError):p.parse_record(line)
    def test_failed_execution_or_equal_bad_streams_never_pass(self):
        rows,text=fixture()
        with tempfile.TemporaryDirectory(prefix='_pair-test-',dir=HERE) as directory:
            left=Path(directory)/'c.csv';right=Path(directory)/'d.csv';left.write_bytes(text.encode('ascii'));right.write_bytes(text.encode('ascii'))
            self.assertTrue(p.compare_files(left,right,rows,c_code=1)['errors'])
            self.assertFalse(p.compare_files(left,right,rows)['errors'])
            bad=mutate(text,'M',1,0x7fc00001);left.write_bytes(bad.encode('ascii'));right.write_bytes(bad.encode('ascii'))
            errors=p.compare_files(left,right,rows)['errors'];self.assertEqual(len(errors),2)
            self.assertTrue(all('NaN/Inf' in error for error in errors))

class Negatives(unittest.TestCase):
    def test_N_guard_witnesses_have_complete_bodies_for_their_invalid_counts(self):
        negative=module('pair_N_isolated_negatives','ujemne-pary.py');items={r[0]:r for r in negative.variants()}
        self.assertEqual(items['N-zero'][1:3],(b'PORT9A 0\n',b'PORT9A 0\n'))
        for index,dec in ((1,False),(2,True)):
            lines=items['N-over'][index].decode('ascii').splitlines()
            self.assertEqual(len(lines),1+3*449)
            reduced='\n'.join(['PORT9A 448',*lines[1:1+3*448]])+'\n'
            self.assertEqual(len(g.read_input(reduced,dec)),448)
    def test_all_paired_negative_witnesses_reject_in_the_input_model(self):
        negative=module('pair_negatives_tests','ujemne-pary.py');rows=negative.variants()
        self.assertEqual(len(rows),46);self.assertEqual(len({r[0] for r in rows}),46)
        for name,c,d,cd,dd in rows:
            self.assertTrue(cd.startswith(b'PORT9A: '));self.assertEqual(cd.count(b'\n'),1)
            self.assertTrue(dd.startswith(b'BLAD: '));self.assertEqual(dd.count(b'\n'),1)
            for data,dec in ((c,False),(d,True)):
                with self.assertRaises((ValueError,IndexError),msg=name):g.read_input(data.decode('ascii'),dec)

if __name__=='__main__':unittest.main()
