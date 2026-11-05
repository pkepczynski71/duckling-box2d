pass                                                                          

                                                                          
                                                                               
   
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


f = load('w2_model_fixture', 'test_polaczenia_integracja.py')
m = f.m
ci = f.ci


def chain_fixture():
    world = [1,1,0,1,0,1,1,0,1,0,*([0]*6)]
    body = [1,1,0,1,0,1,1,0,1,0,2,0,*([0]*21)]
    return [('W',tuple(world)), ('B',tuple(body)),
            ('WS12',(1,1,0,*([0]*11))), ('HC12',(1,1,0,*([0]*13))),
            ('NM12',(1,1,0,*([0]*33))),
            ('UD12',(1,1,0,0,0,0,0)), ('UD12',(1,1,1,0,0,0,0)),
            ('IP13',(1,1,0,2,1,1)),
            ('CH13',(1,1,0,0,1,0,m.NULL,1,1)), ('CH13',(1,1,0,1,0,0,0,0,0)),
            ('CG13',(1,1,0,0,1,1,3,0,1,0)), ('CG13',(1,1,0,1,0,1,2,0,1,0)),
            ('CI13',(1,1,0,0,0,1,0,1,0,4,0,1,0)),
            ('CM13',(1,1,0,0,0,0,0,0,0,0,0)),
            ('BH13',(1,1,0,0,0)),
            ('CN13',(1,1,0,1,0,1,0,3,0,1,0)), ('V13',(1,1,0,1,1)),
            ('COPY13',(1,1,0,0)), ('CV13',(1,1,0,0,1,0,1,0,3,0,1,0,0,2,0,1,0,1)),
            ('CE13',(1,1,0,0,0,1,0,1,0,4,0,1,0)), ('ENDCOPY13',(1,1,0,0))]


def changed(rows, tag, index, value):
    rows = copy.deepcopy(rows)
    i = next(i for i,(t,v) in enumerate(rows) if t == tag)
    t,v = rows[i]; values = list(v); values[index] = value; rows[i] = t,tuple(values)
    return rows


class Base13BeforeChange(unittest.TestCase):
    def checked(self, rows):
        data = f.base_counter_fixture(rows)
        tag, value = data[-1]; value = list(value)
        value[13] = sum(v[4] for t,v in rows if t == 'CH13')
        data[-1] = tag, tuple(value)
        return m.check_base13_counts(data,1,1)

    def test_valid_small_chain_remains_partial_not_complete(self):
        result = self.checked(chain_fixture())
        self.assertTrue(result['base_counts_checked'])
        self.assertFalse(result['complete'])
        self.assertFalse(result['full_ownership_ready'])

    def test_pool_free_stack_cannot_contain_live_slot_after_counter_repair(self):
        with self.assertRaisesRegex(ValueError,'chain pool'):
            self.checked(changed(chain_fixture(),'IP13',5,0))

    def test_dead_chain_payload_zero_with_retained_CG_metadata(self):
        rows = chain_fixture(); i = next(i for i,(t,v) in enumerate(rows) if t == 'CH13' and v[3] == 1)
        tag,v = rows[i]; rows[i] = tag,(*v[:5],7,*v[6:])
        with self.assertRaisesRegex(ValueError,'dead chain'):
            self.checked(rows)

    def test_sparse_occupied_agrees_with_chain_alive(self):
        with self.assertRaisesRegex(ValueError,'chain occupied'):
            self.checked(changed(chain_fixture(),'CG13',4,0))

    def test_chain_segments_require_contiguous_j_not_only_equal_count(self):
        with self.assertRaisesRegex(ValueError,'chain segment'):
            self.checked(changed(chain_fixture(),'CI13',4,1))

    def test_materials_match_declared_materialCount(self):
        with self.assertRaisesRegex(ValueError,'chain material'):
            self.checked(changed(chain_fixture(),'CH13',8,2))

    def test_body_head_chain_walk_reaches_exact_owned_chains(self):
        with self.assertRaisesRegex(ValueError,'body chain'):
            self.checked(changed(chain_fixture(),'BH13',4,m.NULL))

    def test_CN_and_V_have_same_register_keys_after_counter_repair(self):
        with self.assertRaisesRegex(ValueError,'chain validity'):
            self.checked(changed(chain_fixture(),'V13',2,1))

    def test_COPY_block_count_is_not_just_aggregate_counter(self):
        with self.assertRaisesRegex(ValueError,'chain copy'):
            self.checked(changed(chain_fixture(),'CV13',17,2))


class AdapterBeforeChange(unittest.TestCase):
    def test_new_joint_refusal_cannot_change_BASE13_body_velocity(self):
        model = f.prepared_model()
        model.check(1,1,f.fixture.OP,f.fixture.snapshot())
        operation = {'opcode':203,'a':(1,0,0,6)}
        data = [(t, (1,2,*v[2:])) for t,v in f.fixture.snapshot()
                if not (t == 'J14' and v[5] == 4)]
        data[0] = 'E14',(1,2,203,4,1,0,0,6)
        i = next(i for i,(t,v) in enumerate(data) if t == 'A14')
        data[i] = 'A14',(1,2,7,1)
        i = next(i for i,(t,v) in enumerate(data) if t == 'B')
        tag,v = data[i]; value = list(v); value[19] = 0x3f800000; data[i] = tag,tuple(value)
        data = f.summary(data)
        i = next(i for i,(t,v) in enumerate(data) if t == 'J14' and v[5] == 8)
        tag,v = data[i]; value = list(v); value[22] = 2; data[i] = tag,tuple(value)
        with self.assertRaisesRegex(ValueError,'refusal changed BASE13'):
            model.check(1,2,operation,data)

    def test_partial_joint_model_names_its_remaining_BASE13_debt(self):
        result = f.prepared_model().check(1,1,f.fixture.OP,f.fixture.snapshot())
        self.assertFalse(result['complete'])
        self.assertFalse(result['full_model_ready'])
        self.assertIn('BASE13 world/body/shape/contact/chain life history', result.get('open_obligations', []))
        self.assertIn('DIRECT F4/J10 input history', result.get('open_obligations', []))

    def test_partial_or_unresolved_validator_never_certifies_native_guard(self):
        item = {'key':'unit-ctx','kind':0,'ops':(), 'expected_status':0,'expected_reason':0}
        with tempfile.TemporaryDirectory(prefix='.w2-validator-',dir=ROOT) as tmp:
            path = Path(tmp)/'stdout'; path.write_bytes(b'A14 1 0 0 0\n')
            receipt = {'native_product':True,'build_code':0,'code':0,'stderr':b'',
                       'stdout_path':path,'source_sha256':'f'*64}
            claimed = {'complete':True,'base_grammar':True,'joint_model':True,
                       'base_model':True,'full_model_ready':False,'full_ownership_ready':False,'unresolved':['BASE13 history']}
            with self.assertRaisesRegex(ValueError,'complete BASE13'):
                ci.check_guard_result(item,receipt,side='c1',observer=True,validate=lambda *a: claimed,input_bytes=b'')


if __name__ == '__main__': unittest.main()
