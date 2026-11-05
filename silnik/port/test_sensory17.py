pass                                                                         
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest

HERE=Path(__file__).resolve().parent


def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


tape=load('unit_tape17','sensory-tasmy.py')
inputs=load('unit_inputs17','przypadki-sensory.py')
compare=load('unit_compare17','porownaj-sensory17.py')
DATA=inputs.manifest()
FIXTURE=HERE/'sensory-fixtures'
RECIPES={19:tape.public(DATA['public'][18])}


def validate(rows,observer=True):
    g=compare.G6(RECIPES,observer)
    for row in rows:g.line(row)
    return g.finish()


class FrozenRecipes(unittest.TestCase):
    def test_f11_decision_keeps_m_and_nonempty_edits(self):
                                                                    
        for case in DATA['public'][84:90]:
            rows=tape.public(case)
            with self.subTest(id=case['id']):
                self.assertEqual(len(rows),1357)
                self.assertEqual(sum(r[0]==407 for r in rows),6)
                self.assertEqual(rows[123],tape.op(406,1,0))
                self.assertEqual(rows[11],tape.op(407,1,0,2,0,0,3))

    def test_canonical_entry_defaults_to_port17(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            r=subprocess.run([sys.executable,str(HERE/'ci-sensory.py'),'--source',str(root/'missing'),
                '--work',str(root/'work'),'--output',str(root/'out')],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            receipt=json.loads((root/'out/manifest.json').read_bytes())
            self.assertEqual(receipt['stage'],'PORT17 setup/stage failed')
            self.assertFalse(receipt['completePORT17'])

    def test_all_160_exact_operation_counts(self):
        for profile,fn in [('public',tape.public),('direct',tape.direct)]:
            for case in DATA[profile]:
                with self.subTest(case=case['id']):self.assertEqual(len(fn(case)),case['operationCountExact'])

    def test_all_50400_long_positive_steps(self):
        self.assertEqual(sum(sum(r[0] in (31,32) and r[1][1]==0x3c888889 for r in tape.public(c)) for c in DATA['public'] if not c['short']),50400)

    def test_strict_threshold_neighbours(self):
        for ident,bits in [(33,0x359fffff),(34,0x35a00000),(35,0x35a00001)]:
            rows=tape.direct(DATA['direct'][ident-1]);self.assertIn(bits,[r[1][2] for r in rows if r[0]==4])

    def test_churn_keeps_original_distinct_registers(self):
        for ident,repeat in [(12,65536),(16,65534)]:
            rows=tape.direct(DATA['direct'][ident-1]);macros=[r for r in rows if r[0]==20]
            self.assertEqual(len(macros),1);self.assertEqual(macros[0][1][:5],[0,1,2,repeat,1])
            self.assertIn(tape.flag(2,True),rows)

    def test_raw_b18_six_real_cleanup_worlds(self):
        rows=tape.direct(DATA['direct'][61]);self.assertEqual(len(rows),78)
        self.assertEqual(sum(r[0]==1 for r in rows),6)

    def test_multi_case_f8_requires_real_c_ticket_offsets(self):
        with self.assertRaises(ValueError):list(tape.materialize('PUBLIC','C',DATA,{67,68}))

    def test_multi_case_f8_xor_uses_global_birth(self):
        lines=list(tape.materialize('PUBLIC','C',DATA,{67,68},{'P067':30}))
        edits=[line.split()[-1] for line in lines if len(line.split())>2 and line.split()[0]=='O' and line.split()[2]=='407']
        self.assertEqual(edits,['00000004','00000022'])

    def test_fixture_native_receipt_and_input(self):
        receipt=json.loads((FIXTURE/'P019-receipt.json').read_bytes())
        for side in ('C','D'):
            raw=(FIXTURE/f'P019-{side}.csv').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['inputSHA'][side])
            self.assertEqual(raw,''.join(tape.materialize('PUBLIC',side,DATA,{19})).encode())
        for obs in (0,1):
            self.assertEqual(hashlib.sha256((FIXTURE/f'P019-C{obs}.out.csv.gz').read_bytes()).hexdigest(),receipt['runs'][obs]['sha256'])


class G6Calibration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=gzip.decompress((FIXTURE/'P019-C1.out.csv.gz').read_bytes()).splitlines(keepends=True)

    def assertBad(self,rows):
        with self.assertRaises(ValueError):validate(rows)

    def test_real_native_full_frame(self):
        result=validate(self.rows);self.assertEqual(result['snapshots'],len(RECIPES[19]))

    def test_real_native_projection(self):
        result=compare.compare(FIXTURE/'P019-C0.out.csv.gz',FIXTURE/'P019-C1.out.csv.gz',RECIPES)
        self.assertTrue(result['C0ProjectionC1'])

    def test_third_stream_calibration_is_exact(self):
                                                                             
        result=compare.compare(FIXTURE/'P019-C0.out.csv.gz',FIXTURE/'P019-C1.out.csv.gz',RECIPES,FIXTURE/'P019-C1.out.csv.gz')
        self.assertTrue(result['C1D'])

    def test_third_stream_birth_high_half_bit_is_not_masked(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'T17 '));p=rows[i].split();p[-1]=b'80000000';rows[i]=b' '.join(p)+b'\n'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'changed-fixture.csv';path.write_bytes(b''.join(rows))
            result=compare.compare(FIXTURE/'P019-C0.out.csv.gz',FIXTURE/'P019-C1.out.csv.gz',RECIPES,path)
        self.assertFalse(result['C1D']);self.assertIsNotNone(result['firstDifferenceD'])

    def test_missing_step_echo(self):
        self.assertBad([r for r in self.rows if not r.startswith(b'E14 19 6 ')])

    def test_missing_end(self):self.assertBad(self.rows[:-1])

    def test_trailing_record(self):self.assertBad(self.rows+[self.rows[-1]])

    def test_same_missing_counter_on_both_sides(self):
        for tag in (b'Z13 ',b'I16 ',b'A14 '):
            with self.subTest(tag=tag):self.assertBad([r for r in self.rows if not r.startswith(tag)])

    def test_same_missing_sensor_view_on_both_sides(self):
        self.assertBad([r for r in self.rows if not r.startswith(b'V17 ')])

    def test_same_missing_world_summary_on_both_sides(self):
        self.assertBad([r for r in self.rows if not r.startswith(b'W17 ')])

    def test_missing_zero_length_event_list(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'L17 ') and r.split()[-1]==b'0');del rows[i];self.assertBad(rows)

    def test_duplicate_list(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'L17 '));rows.insert(i,rows[i]);self.assertBad(rows)

    def test_drop_or_duplicate_touch(self):
        for duplicate in (False,True):
            rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'T17 '))
            if duplicate:rows.insert(i,rows[i])
            else:del rows[i]
            with self.subTest(duplicate=duplicate):self.assertBad(rows)

    def test_wrong_input_echo(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'E17 '));p=rows[i].split();p[-1]=b'00000001';rows[i]=b' '.join(p)+b'\n';self.assertBad(rows)

    def test_wrong_query_ordinal(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'Q17 '));p=rows[i].split();p[4]=b'1';rows[i]=b' '.join(p)+b'\n';self.assertBad(rows)

    def test_wrong_list_total(self):
        rows=self.rows.copy();i=next(i for i,r in enumerate(rows) if r.startswith(b'W17 '));p=rows[i].split();p[-1]=b'ffffffff';rows[i]=b' '.join(p)+b'\n';self.assertBad(rows)

    def test_owned_copy_cannot_change_on_read(self):
        rows=self.rows.copy();i=max(i for i,r in enumerate(rows) if r.startswith(b'T17 ') and r.split()[3]==b'2');p=rows[i].split();p[-1]=b'80000000';rows[i]=b' '.join(p)+b'\n';self.assertBad(rows)

    def test_noncanonical_words_and_envelope(self):
        for raw in (b'R17 1 1 400 0 0 8 0000000A\n',b'END 01\n',b'END 1\r\n',b' END 1\n'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):compare.parse(raw)

    def test_negative_zero_kept(self):
        raw=b'R17 19 8 402 0 0 1 80000000\n';self.assertEqual(compare.project(raw),raw)


if __name__=='__main__':unittest.main()
