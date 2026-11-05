pass                                                                        
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('pair_native_mutator8',Path(__file__).with_name('mutacje-ruch-swiata.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
function_span=base.function_span
apply=base.apply
