pass                                                                       

                                                                              
   
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('chain13b_w1', HERE/'ci-lancuchy-oslony.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Gate13bControls(unittest.TestCase):
    def test_legal_fatal_prefix_preserves_inherited_G40_and_GA_H8(self):
        geometry=b'G 1 3 0 '+b' '.join([b'00000000']*40)+b'\n'
        ga=b'GA 1 '+b' '.join([b'00000000']*64)+b'\n'
        source=b'GUARD13B 1\nG 1 0 0 3\n'+ga+b'CASE 1 3\n'+geometry+b'ENDCASE 1\nEND 1\n'
        framing={'original_count':4,'keep_endcase':False,'N':1}
        wanted=b'GUARD13B 1\nG 1 0 0 4\n'+ga+b'CASE 1 4\n'+geometry
        self.assertEqual(b''.join(c.prefix_output_lines13b(io.BytesIO(source),framing)),wanted)

    def test_all_96_have_legal_wire_controls(self):
        guards = c.guard_definitions13b()
        self.assertEqual(len(guards), 96)
        self.assertTrue(all(r['materialized'] for r in guards))
        for row in guards:
            for decimal in (False, True):
                decoded = c.m.decode_input13b(c.encode_guard13b(row, decimal), decimal)
                self.assertEqual(decoded['g'][1], row['kind'])
                self.assertLessEqual(decoded['g'][3], 16)

    def test_g0_dynamic_kinematic_and_fixed_g300(self):
        rows = {r['id']: r for r in c.guard_definitions13b()}
        for name, body_type in (('GB6-CREATE-DYNAMIC',2),('GB6-CREATE-KINEMATIC',1)):
            row = rows[name]
            self.assertEqual(row['kind'], 0)
            self.assertEqual(row['ga'], (0,)*64)
            self.assertEqual(row['operations'][1]['opcode'], 2)
            self.assertEqual(row['operations'][1]['a'][2], body_type)
            self.assertEqual(row['expected_status'], 5)
            self.assertEqual(row['expected_reason'], 80)
        row = rows['GB2-ROUTE-100']
        wire = c.encode_guard13b(row)
        self.assertEqual(row['kind'], 300)
        self.assertEqual(row['ga'][3:7], (1,4,0,1))
        self.assertFalse(any(x.startswith((b'P13B ',b'U13B ')) for x in wire.splitlines()))

    def test_only_g200_has_description_after_ga(self):
        for row in c.guard_definitions13b():
            decoded = c.m.decode_input13b(c.encode_guard13b(row))
            self.assertEqual(bool(decoded['points']), row['kind'] == 200)
            self.assertEqual(bool(decoded['materials']), row['kind'] == 200)

    def test_adjacent_is_control_without_changing_frozen_count(self):
        rows = {r['id']:r for r in c.guard_definitions13b()}
        self.assertTrue(rows['GB5-ADJACENT']['liczonyJakoZabicie'])
        self.assertTrue(rows['GB5-ADJACENT']['control_only'])
        row = next(r for r in c.b.table13b(list(rows.values()))['rows'] if r['id']=='GB5-ADJACENT')
        self.assertFalse(row['counted_as_kill'])
        self.assertFalse(row['verified'])

    def test_every_negative_prefix_is_independently_decodable(self):
        for definition in c.negative_definitions13b():
            for decimal in (False,True):
                control,literal,framing = c.negative_prefix_control13b(definition,decimal)
                if control is not None:
                    decoded = c.m.decode_input13b(control,decimal)
                    self.assertEqual(len(decoded['cases'][0][1]),framing['good'])
                    self.assertTrue(definition['after_legal_O'])
                else:
                    self.assertIsInstance(literal,bytes)

    def test_guard_late_id_count_is_not_fictional(self):
        catalogue = {r['error']:r for r in c.parser_reachability13b()}
        for name in ('INPUT_ID','INPUT_OPCOUNT'):
            self.assertTrue(catalogue[name]['PORT13B']['after_legal_O'])
            self.assertFalse(catalogue[name]['GUARD13B']['after_legal_O'])
        rows = {r['name']:r for r in c.negative_definitions13b()}
        for tag in ('G','CASE'):
            self.assertEqual(rows['GUARD13B/trailing-'+tag]['error'],'INPUT_TRAILING_DATA')

    def test_real_product_inventory_shared_predicate_not_four_invented_functions(self):
                                                                                
                                                                              
        with tempfile.TemporaryDirectory(prefix='chain13b-model-') as folder:
            root = Path(folder);path=root/'silnik/fizyka';path.mkdir(parents=True)
            (path/'gra.dk').write_text('fun chainOnSegment(a: f32) -> bool = { return a >= 0.0f32; }\n')
            (path/'swiat.dk').write_text('')
            result = c.b.product_sites13b(root)
            self.assertEqual(result['required'],1)
            self.assertEqual(result['rows'][0]['function'],'chainOnSegment')
            self.assertEqual(result['rows'][0]['candidate_ids'],['GB5-COLLINEAR','GB5-TOUCH'])
            self.assertFalse(result['complete'])
            self.assertFalse(result['rows'][0]['native_verified'])


if __name__ == '__main__':
    unittest.main()
