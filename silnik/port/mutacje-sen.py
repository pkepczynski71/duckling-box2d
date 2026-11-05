pass                                                                   

                                                                             
                                                                             
                                                                           
   
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module); return module


f = load('sen_native_inputs', 'fixtury-sen.py')
base = load('sen_native_mutator', 'mutacje-ruch-swiata.py')


def recipes():
    result = json.loads((HERE / 'mutacje-sen.json').read_text(encoding='utf-8'))
    rows = result['native_mutations']
    if not rows or len(rows) != result['recipe_count'] or len({r['name'] for r in rows}) != len(rows):
        raise ValueError('nonempty complete native recipe inventory required')
    return result


def applicability(root, manifest=None):
    result = []
    for recipe in (manifest or recipes())['native_mutations']:
        row = {'name': recipe['name'], 'source': recipe['source'], 'scope': recipe['scope'], 'single_hit': False}
        try:
            source = (Path(root) / recipe['source']).read_text(encoding='utf-8')
            lo, hi = base.function_span(source, recipe['scope'])
            row['hits'] = source[lo:hi].count(recipe['expression'])
            changed = base.apply(source, recipe)
            row['single_hit'] = row['hits'] == 1 and changed != source
            row['port_line'] = source[:lo + source[lo:hi].index(recipe['expression'])].count('\n') + 1
        except (OSError, ValueError) as exc:
            row['error'] = str(exc)
        result.append(row)
    return result


def preparations(root):
    pass                                                                       
    result = []
    fixtures = {item.name: item for item in f.definitions()}
    source = (Path(root) / 'silnik/port/solver-swiata.dk').read_text(encoding='utf-8')
    for recipe in recipes()['native_mutations']:
        row = {'name': recipe['name'], 'status': 'OK', 'scope': 'inherited helper-only GUARD profile4'}
        try:
            item = fixtures[recipe['fixture']]
            if item.kind not in (1,2) or item.rows: raise ValueError('helper-only kind1/2 required')
            driver = f.inherited_helper_driver(source)
            row['driver_sha256'] = hashlib.sha256(driver.encode()).hexdigest()
            row['input_sha256'] = hashlib.sha256(item.encode(True)).hexdigest()
            row['expected_sha256'] = hashlib.sha256(item.expected_helper_output()).hexdigest()
        except (KeyError, ValueError) as exc:
            row.update(status='BLAD', error=str(exc))
        result.append(row)
    return result


def protected(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((Path(root) / 'silnik/fizyka').glob('*.dk'))}


def m12_recipe(root):
    pass                                                                 

                                                                           
                                                                    
       
    source = (Path(root) / 'silnik/fizyka/swiat.dk').read_text(encoding='utf-8')
    lo, hi = base.function_span(source, 'b2CollideChanges'); block = source[lo:hi]
    link = 'b2LinkContact(world, id);'
    if block.count(link) != 1: raise ValueError('M12 Link must occur exactly once')
    fresh = list(re.finditer(r'var fresh: ref ContactSim = [^;]+;', block))
    if len(fresh) != 1 or fresh[0].start() < block.index(link):
        raise ValueError('M12 actual reacquire declaration missing/ambiguous')
    expression = block[block.index(link):fresh[0].end()]
    replacement = fresh[0].group() + '\n                ' + link
    return {'name': 'M12-PRE-LINK-REFERENCE', 'scope': 'b2CollideChanges',
            'source': 'silnik/fizyka/swiat.dk', 'expression': expression,
            'replacement': replacement, 'fixture': 'M12-WAKE-GROWTH', 'class_id': 'M12',
            'original_anchor': 'world.c:649–658', 'proof_scope': 'Native wake/growth comparison not measured',
            'counted_as_killed': False}


def check_m12_setup(records):
    pass                                                                 

                                                                        
                                                                  
       
    model = load('sen_m12_model', 'model-sen.py')
    rows = {}
    for tag, value in records: rows.setdefault(tag, []).append(value)
    sets = model.index(rows, 'SS11'); contacts = model.index(rows, 'CT')
    trace = model.index(rows, 'TR11')
    if sets.get((0, 2), (0, 0, 0))[2] != 2: raise ValueError('M12 awake bodies did not grow1→2')
    if sets[(0, 2)][4] != 2 or sets[(0, 1)][4] != 0: raise ValueError('M12 two disabled sims did not transfer to awake')
    if sum(h[0] for h in contacts.values()) != 3: raise ValueError('M12 exactly three real contacts required')
    wakes = [h for (w, _), h in trace.items() if w == 0 and h[0] == 1 and h[6]]
    if len(wakes) != 1 or wakes[0][4] != 1: raise ValueError('M12 Link must wake one sleeping singleton')
    return {'awake_bodies_before': 1, 'awake_bodies_after': 2, 'transferred_non_touching': 2,
            'source_array_capacity': 2, 'temporary_awake_contact_count': 3,
            'original_capacity_rule': 'array.h B2_ARRAY_INLINE Add; capacity<2→2, then +capacity/2'}


class Runtime:
    pass                                                                   
    def __init__(self, context):
        self.c = context; self.root = Path(context.ROOT); self.before = protected(self.root)
        self.directory = context.base.TEMP / 'sen-inherited-native-work'
        if self.directory.exists(): raise ValueError('native work directory already exists')
        self.directory.mkdir(parents=True)
        source = (context.PORT / 'solver-swiata.dk').read_text(encoding='utf-8')
        self.driver_text = f.inherited_helper_driver(source)
        self.driver = self.directory / 'guard11-inherited.dk'
        self.driver.write_text(self.driver_text, encoding='utf-8')
        self.baseline = context.compile_world_fixture(context.world_duckc(), 'sen-inherited-base',
                                                      self.driver, self.root / 'silnik/fizyka')
        self.baseline_receipts = {}

    def observe(self, name, binary, item):
        code, data = self.c.run_world_fixture(name, binary, item.encode(True))
        path = self.c.OUT / (name + '.csv')
        stderr = self.c.OUT / (name + '-wykonanie-stderr.csv')
                                                                          
        if not stderr.is_file(): raise ValueError('native stderr evidence missing')
        replay = path.read_bytes()
        if replay != data: raise ValueError('native output changed before compaction')
        row = {'code': code, 'stderr_empty': not stderr.read_bytes(), 'bytes': len(replay),
               'sha256': hashlib.sha256(replay).hexdigest(), 'replayed_before_compaction': True}
        try:
            records = [load('sen_native_parse', 'model-sen.py').parse(line) for line in replay.decode('ascii').splitlines(keepends=True)]
            gr = [v for tag, v in records if tag == 'GR11']
            baseline_text = item.expected_helper_output().decode('ascii')
            parser = load('sen_native_frame', 'model-sen.py')
            clean_frame = (baseline_text.replace(parser.format_record('GR11', item.helper_record()),
                                                 parser.format_record('GR11', gr[0])).encode('ascii')
                           if len(gr) == 1 else None)
            row['clean'] = code == 0 and row['stderr_empty'] and len(gr) == 1 and replay == clean_frame
            row['helper'] = list(gr[0]) if len(gr) == 1 else None
        except (ValueError, UnicodeError) as exc:
            row.update(clean=False, error=str(exc))
        row['exact_baseline'] = code == 0 and row['stderr_empty'] and replay == item.expected_helper_output()
        path.unlink()                                                          
        return row

    def mutation(self, recipe):
        item = next(x for x in f.definitions() if x.name == recipe['fixture'])
        if item.kind not in (1, 2) or item.rows: raise ValueError('inherited native driver is helper-only kind1/2')
        if item.name not in self.baseline_receipts:
            self.baseline_receipts[item.name] = self.observe('sen-base-' + item.name, self.baseline, item)
        baseline = self.baseline_receipts[item.name]
        if not baseline['exact_baseline']: raise ValueError('clean baseline failed: ' + item.name)
        work = self.directory / recipe['name']; work.mkdir()
        physics = work / 'fizyka'; shutil.copytree(self.root / 'silnik/fizyka', physics)
        target = physics / Path(recipe['source']).name
        target.write_text(base.apply(target.read_text(encoding='utf-8'), recipe), encoding='utf-8')
        binary = self.c.compile_world_fixture(self.c.world_duckc(), 'sen-mutant-' + recipe['name'], self.driver, physics)
        actual = self.observe('sen-mutant-' + recipe['name'], binary, item)
        wanted = list(item.helper_record()); wanted[3:5] = [0, 1]
        detected = bool(actual['clean'] and actual['helper'] == wanted and actual['sha256'] != baseline['sha256'])
        result = {'name': recipe['name'], 'class_id': recipe['class_id'], 'proof_scope': recipe['proof_scope'],
                  'source': recipe['source'], 'detected': detected, 'baseline': baseline, 'mutant': actual,
                  'source_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'difference': {'tag': 'GR11', 'baseline': baseline['helper'], 'mutant': actual['helper']} if detected else None}
        shutil.rmtree(work)
        return result

    def close(self):
        if protected(self.root) != self.before: raise ValueError('product sources changed')
        if self.directory.exists(): shutil.rmtree(self.directory)
