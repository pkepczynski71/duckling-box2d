pass                                                                         
import importlib.util
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location('world_negative_inputs', Path(__file__).with_name('przypadki-swiat.py'))
g = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = g
_spec.loader.exec_module(g)


def small_cases():
    return (g.Case(1, 'E8c586909c59a E1bf61810dc30', g.build()[1].ops), *(
        g.Case(i, 'E9617961b221b E98fc34a4e5dc', (g.world(), g.op(1, 0))) for i in range(2, 65)))


def variants():
    bases = [g.encode(small_cases(), decimal).replace('\r\n', '\n') for decimal in (False, True)]
    def change(line, token, hex_word, decimal_word=None):
        output = []
        for decimal, base in enumerate(bases):
            lines = base.splitlines(); words = lines[line].split(' ')
            words[token] = (str(int(hex_word, 16)) if decimal_word is None else decimal_word) if decimal else hex_word
            lines[line] = ' '.join(words)
            output.append('\n'.join(lines).encode('ascii'))
        return tuple(output)
                                                                             
                                                                                  
    items = [
        ('nan', change(2, 4, '7fc00000')),
        ('inf', change(2, 6, '7f800000')),
        ('speed-zero', change(2, 6, '00000000')),
        ('unused-nonzero', change(2, 7, '00000001')),
        ('unused-minus-zero', change(2, 26, '80000000')),
        ('noncanonical-case-sign', change(2, 6, '43C80000', '+1137180672')),
        ('over-u32', change(2, 3, '100000000', '4294967296')),
        ('noncanonical-width', change(2, 3, '0000000', '00')),
        ('opcode', change(2, 2, '7', '7')),
        ('seq', change(2, 1, '2', '2')),
        ('seq-leading-zero', change(2, 1, '01', '01')),
        ('body-type', change(3, 5, '00000003')),
        ('rotation-zero', change(3, 8, '00000000')),
        ('fixed-flag', change(3, 13, '00000002')),
        ('nul', tuple(b.replace('64\n', '64\x00hidden\n', 1).encode('ascii') for b in bases)),
        ('truncated', tuple(b[:-30].encode('ascii') for b in bases)),
    ]
    for name, word in zip(('rotation-below', 'rotation-above'), g.rotation_boundary_words()):
        items.append((name, change(3, 8, f'{word:08x}')))
    for name, old, new in (
        ('lone-cr', '\n', '\r'), ('empty-line', '\n', '\n\n'),
        ('double-space', 'O 1 0', 'O  1 0'), ('tab', 'O 1 0', 'O\t1 0'),
        ('trailing-space', '\n', ' \n'),
    ):
        items.append((name, tuple(b.replace(old, new, 1).encode('ascii') for b in bases)))
    return tuple((name, *data) for name, data in items)


def boundary_variants():
    pass                                                           
    result, rows = [], small_cases()
    for name, word in (('rotation-at-lower', 0x3f7fec56), ('rotation-at-upper', 0x3f8009d4)):
        pair = []
        for decimal in (False, True):
            lines = g.encode(rows, decimal).replace('\r\n', '\n').splitlines()
            fields = lines[3].split(' ')
            fields[8] = str(word) if decimal else f'{word:08x}'
            lines[3] = ' '.join(fields)
            pair.append('\n'.join(lines).encode('ascii'))
        result.append((name, *pair))
    return tuple(result)


                                                                          
                                                                             
                                                                          
def expected_diagnostic(name):
    groups = {
        'NaN/Inf.': ('nan', 'inf'),
        'maximumLinearSpeed.': ('speed-zero',),
        'nieuzywane slowo.': ('unused-nonzero', 'unused-minus-zero'),
        'missing liczby u32.': ('noncanonical-case-sign', 'double-space'),
        'niekanoniczne u32.': ('over-u32', 'noncanonical-width', 'seq-leading-zero'),
        'seq/opcode.': ('opcode', 'seq'),
        'typ/bool.': ('body-type', 'fixed-flag'),
        'obrot.': ('rotation-zero', 'rotation-below', 'rotation-above',
                   'rotation-at-lower', 'rotation-at-upper'),
        'ASCII / dlugosc wiersza.': ('nul',),
        'wymagana pojedyncza spacja.': ('truncated', 'tab'),
        'samotny CR.': ('lone-cr',),
        'pusty lub brakujacy wiersz.': ('empty-line',),
        'nadmiar danych w wierszu.': ('trailing-space',),
    }
    return next(('BLAD: '+message+'\n').encode('ascii')
                for message, names in groups.items() if name in names)
