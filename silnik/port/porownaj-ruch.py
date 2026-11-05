pass                                                                                 
import argparse
import importlib.util
import math
from pathlib import Path
import re
import sys

spec = importlib.util.spec_from_file_location('przypadki_ruch', Path(__file__).with_name('przypadki-ruch.py'))
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)
UINT = re.compile(r'(?:0|[1-9][0-9]*)\Z')
EPS = 2**-23
MASS_FIELDS = ('mass', 'rotationalInertia', 'localCenter.x', 'localCenter.y')
STATE_FIELDS = ('transform.p.x', 'transform.p.y', 'transform.q.c', 'transform.q.s',
                'worldCenter.x', 'worldCenter.y', 'linearVelocity.x', 'linearVelocity.y', 'angularVelocity')


def parse_log(text, label, cases):
    pass                                                                        
    lines = text.replace('\r\n', '\n').removesuffix('\n').split('\n') if text else []
    errors, masses, states = [], {}, {}
    if not lines or lines[0] != f'PORT3 {len(cases)}':
        errors.append(f'{label}: naglowek: expected PORT3 {len(cases)}')
    expected_count = 2+len(cases)+sum(c.words[5] for c in cases)
    if len(lines) != expected_count:
        errors.append(f'{label}: liczba wierszy {len(lines)}, expected {expected_count} (stepCount z wejscia)')
    cursor = 1

    def take(tag, case, step, count):
        nonlocal cursor
        location = f'{label}: case {case.id}, step {step}'
        if cursor >= len(lines):
            errors.append(location+': missing wiersza '+tag)
            return None
        line = lines[cursor]
        cursor += 1
        tokens = line.split(' ')
        prefix = [tag, str(case.id)] + ([str(step)] if tag == 'S' else [])
        if (len(tokens) != len(prefix)+count or tokens[:len(prefix)] != prefix
                or any(len(t) > 10 or not UINT.fullmatch(t) for t in tokens[len(prefix):])):
            errors.append(location+f': format/kolejnosc wiersza {tag}, linia {cursor}')
            return None
        words = tuple(map(int, tokens[len(prefix):]))
        if any(w >= 2**32 for w in words):
            errors.append(location+': field poza u32')
            return None
        return words

    for case in cases:
        mass = take('M', case, 0, 90)
        if mass is not None:
            masses[case.id] = mass
        for step in range(1, case.words[5]+1):
            state = take('S', case, step, 9)
            if state is not None:
                states[case.id, step] = state
    if cursor >= len(lines) or lines[cursor] != f'END {len(cases)}' or cursor != len(lines)-1:
        errors.append(f'{label}: missing/zly koniec lub nadmiar danych END {len(cases)}')
    return masses, states, errors


def shape_mass_center(words):
    pass                                                                      
    parts = []
    for i in range(words[18]):
        s = words[19+9*i:28+9*i]
        density, *p = map(g.number, s[1:])
        if s[0] == 0:
            parts.append((density*math.pi*p[2]**2, p[0], p[1]))
        elif p[6] == 0:
            parts.append((density*4*p[0]*p[1], p[2], p[3]))
        else:
            return None                                                                  
    mass = math.fsum(p[0] for p in parts)
    return mass, *(math.fsum(p[0]*p[j] for p in parts)/mass for j in (1, 2))


def mass_properties(case, mass_words, label):
    errors = []
    m, inertia, cx, cy = map(g.number, mass_words)
    if not all(map(math.isfinite, (m, inertia, cx, cy))) or m <= 0 or inertia < 0:
        return [f'{label}: case {case.id}, step 0: independent Ee7b69c7f6d8d/E9cb963a4fb28 NaN/E1daec9c71ee2/E956cb3b1ab25']
    if case.words[16] and inertia != 0:
        errors.append(f'{label}: case {case.id}, step 0: fixedRotation E003a8cb6dbd7 E0800c0a830af E2cf834c73707')
    expected = shape_mass_center(case.words)
    if expected is not None:
        em, ex, ey = expected
        if abs(m-em) > 128*EPS*em:
            errors.append(f'{label}: case {case.id}, step 0: independent field mass')
        scale = max(EPS, *(abs(g.number(case.words[19+9*i+j]))
                             for i in range(case.words[18]) for j in range(2, 9)))
        for field, actual, wanted in (('localCenter.x', cx, ex), ('localCenter.y', cy, ey)):
            if abs(actual-wanted) > 128*EPS*scale:
                errors.append(f'{label}: case {case.id}, step 0: independent field {field}')
    return errors


def motion_parameters(case, mass_words):
    w = case.words
    m, _, lx, ly = map(g.number, mass_words)
    px, py, c, s, vx, vy, angular = map(g.number, w[6:13])
    rx, ry = c*lx-s*ly, s*lx+c*ly
                                                                       
    v0 = (vx-angular*ry, vy+angular*rx)
    center0 = (px+rx, py+ry)
    dt, scale = g.number(w[3]), g.number(w[15])
    acceleration = tuple(g.number(v)*scale for v in w[:2])
    commands = tuple(w[38+6*i:44+6*i] for i in range(w[37]))
    skip = None
    if w[13] or w[14]:
        skip = 'tlumienie'
    elif case.category in ('prog-liniowy', 'prog-obrotowy'):
        skip = 'prog zacisku'
    else:
        bound = math.hypot(*v0)+math.hypot(*acceleration)*dt*w[5]
        contributions = {}
        rounding_budget = 0.0
        for cmd in commands:
            if cmd[1] in (0, 1, 3, 4):
                factor = dt/m if cmd[1] <= 1 else 1/m
                vector = tuple(g.number(v)*factor for v in cmd[2:4])
                contributions.setdefault(cmd[0], []).append(vector)
                rounding_budget += math.hypot(*vector)
        bound += sum(math.hypot(*(math.fsum(v[j] for v in vectors) for j in range(2)))
                     for vectors in contributions.values()) + 128*EPS*rounding_budget
        if bound >= g.number(w[2])*(1-128*EPS):
            skip = 'mozliwy zacisk liniowy'
    return m, center0, v0, dt, acceleration, commands, skip


def velocity_properties(case, step, values, params, previous, label):
    pass                                                                   
    w = case.words
    location = f'{label}: case {case.id}, step {step}: independent '
    speed, angular = math.hypot(*values[6:8]), abs(values[8])
    maximum = g.number(w[2])
    limit = math.pi/(4*g.number(w[3]))
                                                                           
    if speed > maximum + 8*EPS*maximum + math.sqrt(2*2**-149):
        errors = [location+'maximumLinearSpeed: przekroczona granica |v|']
    else:
        errors = []
    if not w[17] and angular > limit*(1+8*EPS):
        errors.append(location+'granica obrotu: przekroczona granica |w|')
    _, _, v0, dt, acceleration, commands, _ = params
    damping = tuple(map(g.number, w[13:15]))
    w0 = g.number(w[12])
                                                                            
    if (not any(damping) or any(acceleration) or commands
            or math.hypot(*v0) > maximum or not w[17] and abs(w0) > limit):
        return errors
    n, h = step*w[4], dt/w[4]
    previous_values = tuple(map(g.number, previous)) if previous is not None else None
    prior = (math.hypot(*previous_values[6:8]), abs(previous_values[8])) if previous_values else (math.hypot(*v0), abs(w0))
    for name, actual, old in zip(('liniowa', 'obrotowa'), (speed, angular), prior):
        if actual > old*(1+8*EPS)+8*2**-149:
            errors.append(location+f'tlumienie {name}: missing monotonicznosci')
    linear_decay = (1+h*damping[0])**(-n)
    angular_decay = (1+h*damping[1])**(-n)
    expected = (*[v*linear_decay for v in v0], w0*angular_decay)
    for name, actual, wanted, scale in zip(('linearVelocity.x', 'linearVelocity.y', 'angularVelocity'),
                                          values[6:9], expected, (*map(abs, v0), abs(w0))):
        tolerance = 32*EPS*(n+8)*max(scale, 2**-126) + 8*n*2**-149
        if abs(actual-wanted) > tolerance:
            errors.append(location+f'Eb6112cde002b Pade field {name}: {actual:.9g}, oczekiwano {wanted:.9g}')
    return errors


def state_properties(case, step, mass_words, state_words, params, first, label, previous=None):
    pass                                                                         
    location = f'{label}: case {case.id}, step {step}: independent '
    values = tuple(map(g.number, state_words))
    if not all(map(math.isfinite, values)):
        return [location+'NaN/Inf']
    x, y, c, s, cx, cy, vx, vy, angular = values
    m, center0, v0, dt, acceleration, commands, skip = params
    lx, ly = map(g.number, mass_words[2:])
    errors = velocity_properties(case, step, values, params, previous, label)
    if abs(math.hypot(c, s)-1) > 128*EPS:
        errors.append(location+'field transform.q: norma')
    local_scale = max(EPS, abs(lx), abs(ly))
    world_scale = max(EPS, abs(x), abs(y), abs(cx), abs(cy))
    transform_tolerance = 128*EPS*local_scale+8*EPS*world_scale
    for field, actual, expected in (('worldCenter.x', cx, x+c*lx-s*ly),
                                     ('worldCenter.y', cy, y+s*lx+c*ly)):
        if abs(actual-expected) > transform_tolerance:
            errors.append(location+'field '+field+': p + R*localCenter')
    if case.category == 'spoczynek':
        w = case.words
        initial = (*w[6:10], *w[6:8], *w[10:13])
        if state_words != first or state_words != initial:
            errors.append(location+'E1a5e497a2bfa Ea5703a566bf2 Ecd5b158f21b7 E35e99f929e01 E0085e8a6cd2a E89ec081d7a8f/Edce2360f10bf z E1af71faf5178')
    if skip:
        return errors
    t = step*dt
    n = step*case.words[4]
                                                                       
    gravity_position_factor = .5*t*t*(1+1/n)
    expected_v = [v0[j]+acceleration[j]*t for j in range(2)]
    expected_c = [center0[j]+v0[j]*t+acceleration[j]*gravity_position_factor for j in range(2)]
    impulse_budget = 0.0
    for cmd in commands:
        if cmd[0] > step or cmd[1] not in (0, 1, 3, 4):
            continue
        vector = tuple(map(g.number, cmd[2:4]))
        elapsed = (step-cmd[0])*dt
        force = cmd[1] <= 1
        velocity_factor = dt if force else 1
        position_factor = dt*elapsed + dt*dt*(case.words[4]+1)/(2*case.words[4]) if force else elapsed+dt
        for j in range(2):
            expected_v[j] += vector[j]/m*velocity_factor
            expected_c[j] += vector[j]/m*position_factor
                                                                                    
        impulse_budget += math.hypot(*vector)/m*velocity_factor
    velocity_scale = max(EPS, math.hypot(*v0), math.hypot(*acceleration)*t, impulse_budget,
                         math.hypot(*expected_v))
                                                                            
    velocity_tolerance = 32*EPS*(n+8)*velocity_scale
    position_scale = max(EPS, *(abs(v) for v in center0), math.hypot(*v0)*t,
                         math.hypot(*acceleration)*t*t, impulse_budget*t,
                         *(abs(v) for v in expected_c))
    position_tolerance = 64*EPS*(step+8)*position_scale + t*velocity_tolerance
    for field, actual, expected, tolerance in (
            ('linearVelocity.x', vx, expected_v[0], velocity_tolerance),
            ('linearVelocity.y', vy, expected_v[1], velocity_tolerance),
            ('worldCenter.x', cx, expected_c[0], position_tolerance),
            ('worldCenter.y', cy, expected_c[1], position_tolerance)):
        if abs(actual-expected) > tolerance:
            errors.append(location+f'field {field}: {actual:.9g}, oczekiwano {expected:.9g}, tolerancja {tolerance:.9g}')
                                                                                  
                                                                                     
    if not any(cmd[1] in (0, 3) for cmd in commands):
        inertia = g.number(mass_words[1])
        expected_w = g.number(case.words[12])
        angular_budget = abs(expected_w)
        if inertia > 0:
            for cmd in commands:
                if cmd[0] <= step and cmd[1] in (2, 5):
                    change = g.number(cmd[2])/inertia*(dt if cmd[1] == 2 else 1)
                    expected_w += change
                    angular_budget += abs(change)
        if case.words[17] or angular_budget < math.pi/(4*dt)*(1-128*EPS):
            tolerance = 32*EPS*(n+8)*max(EPS, angular_budget)
            if abs(angular-expected_w) > tolerance:
                errors.append(location+f'field angularVelocity: {angular:.9g}, oczekiwano {expected_w:.9g}')
    return errors


def compare(c_text, duck_text, exit_code, cases, c_exit_code=0):
    cm, cs, errors = parse_log(c_text, 'C', cases)
    dm, ds, other = parse_log(duck_text, 'Duckling', cases)
    errors.extend(other)
    for label, code in (('C', c_exit_code), ('Duckling', exit_code)):
        if code:
            errors.append(f'{label}: code exit {code}, expected 0')
    matched = echoes = steps_matched = 0
    properties = {'C': 0, 'Duckling': 0}
    dynamic_skips = {'C': {}, 'Duckling': {}}
    first_difference = None
    table = ['| E12156e921bdb | E6c1dd2e531d4 | E17b022365622 E13991feb1b0c | E931647da0d5b |', '|---:|---|---:|---|']
    for case in cases:
        issues = []
        c, d = cm.get(case.id), dm.get(case.id)
        if c is not None and d is not None:
            echoes += c[:86] == d[:86] == case.words
        for label, row in (('C', c), ('Duckling', d)):
            if row is None:
                issues.append(f'{label}: case {case.id}, step 0: missing M')
                continue
            for i, (actual, expected) in enumerate(zip(row[:86], case.words)):
                if actual != expected:
                    issues.append(f'{label}: case {case.id}, step 0, echo.{g.INPUT_FIELDS[i]}: 0x{actual:08x}, wejscie 0x{expected:08x}')
                    break
        if c is not None and d is not None:
            for field, left, right in zip((*('echo.'+f for f in g.INPUT_FIELDS), *MASS_FIELDS), c, d):
                if left != right:
                    issue = f'case {case.id}, step 0, field {field}: C=0x{left:08x}, Duckling=0x{right:08x}'
                    issues.append(issue)
                    first_difference = first_difference or issue
                    break
        params = {}
        property_failures = {}
        for label, row in (('C', c), ('Duckling', d)):
            if row is not None:
                failures = mass_properties(case, row[86:], label)
                property_failures[label] = bool(failures)
                issues.extend(failures)
                if all(math.isfinite(g.number(w)) for w in row[86:]) and g.number(row[86]) > 0:
                    params[label] = motion_parameters(case, row[86:])
                    reason = params[label][-1]
                    if reason:
                        dynamic_skips[label][reason] = dynamic_skips[label].get(reason, 0)+1
        good_steps = 0
        for step in range(1, case.words[5]+1):
            a, b = cs.get((case.id, step)), ds.get((case.id, step))
            if a is None or b is None:
                issues.append(f'case {case.id}, step {step}: missing S')
            else:
                if a == b:
                    good_steps += 1
                else:
                    for field, left, right in zip(STATE_FIELDS, a, b):
                        if left != right:
                            issue = f'case {case.id}, step {step}, field {field}: C=0x{left:08x}, Duckling=0x{right:08x}'
                            issues.append(issue)
                            first_difference = first_difference or issue
                            break
            for label, row, state, states in (('C', c, a, cs), ('Duckling', d, b, ds)):
                if label not in params or state is None:
                    continue
                failures = state_properties(case, step, row[86:], state, params[label],
                                            states.get((case.id, 1)), label, states.get((case.id, step-1)))
                property_failures[label] |= bool(failures)
                                                                                         
                if failures and not any('niezalezne' in issue and issue.startswith(label+':') for issue in issues):
                    issues.extend(failures)
        for label in properties:
            states = cs if label == 'C' else ds
            if label in params and not property_failures[label] and all((case.id, k) in states for k in range(1, case.words[5]+1)):
                properties[label] += 1
        steps_matched += good_steps
        if not issues:
            matched += 1
        errors.extend(issues)
        table.append(f'| {case.id} | {case.category} | {good_steps}/{case.words[5]} | {('BLAD' if issues else 'OK')} |')
    total_steps = sum(c.words[5] for c in cases)
    report = '\n'.join(['# COMPARISON RUCHU', '', 'RESULT: '+('FAIL' if errors else 'OK'), '',
        'PIERWSZY ROZJAZD: '+(first_difference or (errors[0] if errors else 'brak')), '',
        f'E3e1ae1d296eb E279cf128155b: {matched}/{len(cases)}; echo: {echoes}/{len(cases)}; S: {steps_matched}/{total_steps}.',
        f'independent E50ca5bc0fbba: C {properties['C']}/{len(cases)}; Duckling {properties['Duckling']}/{len(cases)}.',
        'E058c4ccfa8a0, E1d1eff6bc05f, Ef815dff6b32c q, E845aec4e0634 E148de9c5a7a4/COM Ecf37c87714d0 E77e0ab75bed8 |E4c94485e0c21|/|E50e721e49c01| E4cf6829aa937 E7e31300840eb E867f2130853a E944d936358d6 E49b48b0619b7 Ede7d1b721a1e E3dbdae865bfb.',
        'Ef7f4153fb0ef Eb6112cde002b E283ada7088c2 E867a6ad21bd5: Ee7c2ca1286d9 Ede7d1b721a1e Efc26a86e6ec4 E30d9f9e9db80 Pade E50e721e49c01 f64.',
        *(f'{label}: E739836b198d5 E4a32c3c6b097 Ee43fd8ca90c4 E735c533baeac/Ea47f6d13afa6: {reasons}.' for label, reasons in dynamic_skips.items()),
        '', *table, '', f'Bledy: {len(errors)}', *('- '+e for e in errors), ''])
    return int(bool(errors)), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('c', 'duckling', 'wejscie', 'raport'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--kod-wyjscia', type=int, required=True)
    parser.add_argument('--kod-c', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        cases = g.read_inputs(args.wejscie)
        texts = tuple(p.read_text(encoding='ascii') if p.is_file() else '' for p in (args.c, args.duckling))
        code, report = compare(*texts, args.kod_wyjscia, cases, args.kod_c)
    except (OSError, ValueError, UnicodeError) as exc:
        code, report = 1, f'# COMPARISON RUCHU\n\nRESULT: FAIL\n\n{exc}\n'
    args.raport.parent.mkdir(parents=True, exist_ok=True)
    args.raport.write_text(report, encoding='utf-8')
    print(f'Ruch: code {code}; raport {args.raport}')
    return code


if __name__ == '__main__':
    sys.exit(main())
