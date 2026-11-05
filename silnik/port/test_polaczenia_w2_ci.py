pass                                                                          

                                                                            
                                                                           
   
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('w2_ci14', HERE / 'ci-polaczenia.py')
ci = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ci
spec.loader.exec_module(ci)


class SelectionBeforeFix(unittest.TestCase):
    def exercise(self, profile, *, red_build):
        calls = []
        original_load = ci.load

        def load(name, filename):
            if filename == 'ci-polaczenia-oslony.py':
                def second(ctx=None, **kwargs):
                    calls.append((ctx, kwargs))
                    return 1
                return SimpleNamespace(stage=second)
            if filename == 'budowa-polaczenia.py':
                def build(*args):
                    if red_build:
                        raise ValueError('W2 controlled red build')
                    return {'binaries': {'obs0': {'binary': 'c0'}, 'obs1': {'binary': 'c1'}}}
                return SimpleNamespace(build=build)
            return original_load(name, filename)

        budgets = {'seconds': {k: 1 for k in ('PUBLIC', 'DIRECT', 'GUARD', 'parsers', 'mutations', 'builds')}}
        with tempfile.TemporaryDirectory(prefix='.w2-ci-', dir=ROOT) as directory:
            out = Path(directory)
            with patch.object(ci, 'load', side_effect=load),\
                 patch.object(ci, 'selftest', return_value=[{'code': 0, 'tests': 1}]),\
                 patch.object(ci, 'approved_limits', return_value=budgets),\
                 patch.object(ci, 'compile_duckling', return_value={'binary': 'd'}),\
                 patch.object(ci, 'native_compare', return_value={'full_acceptance': False}) as compare,\
                 patch.dict(ci.os.environ, {'BOX2D_SOURCE': 'controlled-existing-source'}):
                self.assertEqual(ci.stage(out=out, phase='all', part='A', profile=profile), 1)
            result = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
        return calls, result, compare.call_args_list

    def test_ALL_runs_independent_second_half_after_red_build(self):
        from public_ci import check
        check(self)

    def test_explicit_GUARD_survives_PUBLIC_DIRECT_loop(self):
        from public_ci import check
        check(self)

    def test_explicit_PARSER_survives_PUBLIC_DIRECT_loop(self):
        from public_ci import check
        check(self)

    def test_explicit_MUTATIONS_survives_PUBLIC_DIRECT_loop(self):
        from public_ci import check
        check(self)

    def test_PUBLIC_never_turns_into_DIRECT(self):
        from public_ci import check
        check(self)

    def test_DIRECT_stays_DIRECT(self):
        from public_ci import check
        check(self)


if __name__ == '__main__':
    unittest.main()
