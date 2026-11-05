pass                                                                               
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import sprawdz


                                                                                    
DEFINITIONS = '''DEF world.gravity_y -10.000000
DEF world.contact_hertz 30.000000
DEF world.enable_sleep 1
DEF world.worker_count 0
DEF body.type 0
DEF body.rotation_c 1.000000
DEF body.gravity_scale 1.000000
DEF body.is_enabled 1
DEF body.internal_value 42
DEF shape.material_friction 0.600000
DEF shape.density 1.000000
DEF shape.filter_category_bits 1
DEF shape.filter_mask_bits 18446744073709551615
DEF shape.update_body_mass 1'''


def make_log():
    lines = [DEFINITIONS]
    for step in range(1, 181):
        y = max(0.7, 5.0 - 0.003 * step * step)
        lines.append(f'POS {step} 4.000000 {y:.6f} 1.000000 0.000000')
    return '\n'.join(lines) + '\nKONIEC OK\n'


def chunk(tag, payload):
    return (struct.pack('>I', len(payload)) + tag + payload
            + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff))


def encode_png(rows, width, channels=3, modes=(0,), split_idat=False):
    pass                                                                     
    encoded = bytearray()
    previous = bytes(width * channels)
    for index, row in enumerate(rows):
        mode = modes[index % len(modes)]
        encoded.append(mode)
        if mode == 0:
            encoded.extend(row)
        else:
            for x, value in enumerate(row):
                a = row[x - channels] if x >= channels else 0
                b = previous[x]
                c = previous[x - channels] if x >= channels else 0
                if mode == 1:
                    predictor = a
                elif mode == 2:
                    predictor = b
                elif mode == 3:
                    predictor = (a + b) // 2
                else:
                    estimate = a + b - c
                    da, db, dc = abs(estimate - a), abs(estimate - b), abs(estimate - c)
                    predictor = a if da <= db and da <= dc else b if db <= dc else c
                encoded.append((value - predictor) % 256)
        previous = row
    compressed = zlib.compress(bytes(encoded))
    header = struct.pack('>IIBBBBB', width, len(rows), 8, 2 if channels == 3 else 6, 0, 0, 0)
    blocks = ([compressed[:len(compressed)//2], compressed[len(compressed)//2:]]
              if split_idat else [compressed])
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
            + b''.join(chunk(b'IDAT', part) for part in blocks) + chunk(b'IEND', b''))


def scene_png(step, blank=False, box_x=400, box_color=(230, 41, 55)):
    y = max(0.7, 5.0 - 0.003 * step * step)
    center_y = round(600 - 100 * y)
    background = bytes((245, 245, 245)) * 800
    floor = bytes((0, 117, 44)) * 800
    rows = []
    for sy in range(600):
        row = background if blank or sy < 550 else floor
        if not blank and center_y - 20 <= sy < center_y + 20:
            row = (row[:(box_x - 20) * 3] + bytes(box_color) * 40
                   + row[(box_x + 20) * 3:])
        rows.append(row)
    return encode_png(rows, 800)


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='test-sprawdz-', dir=Path(__file__).resolve().parent)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.png = cls.root / 'wynik'
        (cls.png / 'klatki').mkdir(parents=True)
        cls.good = make_log()
        for step in range(2, 181, 2):
            content = scene_png(step)
            (cls.png / 'klatki' / f'klatka-{step:03d}.png').write_bytes(content)
        (cls.png / 'klatka-180.png').write_bytes(scene_png(180))

    def assess(self, duck=None, reference=None, exit_code=0):
        return sprawdz.check(self.good if reference is None else reference,
                             self.good if duck is None else duck, self.png, exit_code)

    def assert_failure(self, rows, criterion, message):
        number, passed, detail = next(row for row in rows if row[0] == criterion)
        self.assertEqual(number, criterion)
        self.assertFalse(passed, detail)
        self.assertIn(message, detail)

    def replace_file(self, path, content):
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(content)

    def change_pos(self, text, step, field, value):
        lines = text.splitlines()
        index = 14 + step - 1
        parts = lines[index].split(' ')
        parts[2 + field] = value
        lines[index] = ' '.join(parts)
        return '\n'.join(lines) + '\n'

    def test_good_data_pass_all_four(self):
        rows = self.assess()
        self.assertEqual([True, True, True, True], [row[1] for row in rows], rows)
        self.assertIn('PNG=91/91', rows[2][2])
        self.assertIn('porownan=720', rows[1][2])

    def test_empty_png_file_fails(self):
        self.replace_file(self.png / 'klatka-180.png', b'')
        self.assert_failure(self.assess(), 3, 'pusty lub uszkodzony')

    def test_valid_but_blank_png_fails(self):
        self.replace_file(self.png / 'klatka-180.png', scene_png(180, blank=True))
        self.assert_failure(self.assess(), 3, 'pudelko')

    def test_box_in_wrong_place_fails(self):
        self.replace_file(self.png / 'klatka-180.png', scene_png(180, box_x=500))
        self.assert_failure(self.assess(), 3, 'pudelko w (400, 530)')

    def test_early_box_in_wrong_place_fails(self):
        self.replace_file(self.png / 'klatki' / 'klatka-002.png', scene_png(2, box_x=500))
        self.assert_failure(self.assess(), 3, 'klatka-002.png: PNG: pudelko')

    def test_both_logs_without_falling_fail_independently(self):
        frozen = self.good
        for step in range(1, 181):
            frozen = self.change_pos(frozen, step, 1, '0.700000')
        self.assert_failure(self.assess(duck=frozen, reference=frozen), 2, 'missing spadania')

    def test_pos_difference_above_threshold_fails(self):
        changed = self.change_pos(self.good, 50, 0, '4.000101')
        self.assert_failure(self.assess(duck=changed), 2, 'difference POS step=50 field=x')

    def test_pos_difference_at_threshold_passes(self):
        changed = self.change_pos(self.good, 50, 0, '4.000100')
        rows = self.assess(duck=changed)
        self.assertTrue(rows[1][1], rows[1])

    def test_rotation_difference_fails(self):
        changed = self.change_pos(self.good, 1, 2, '0.999899')
        self.assert_failure(self.assess(duck=changed), 2, 'field=cos')

    def test_mismatched_def_fails(self):
        changed = self.good.replace('DEF body.type 0', 'DEF body.type 2')
        self.assert_failure(self.assess(duck=changed), 1, 'DEF body.type: C=')

    def test_uint64_is_not_rounded_through_float(self):
        changed = self.good.replace('18446744073709551615', '18446744073709551614')
        self.assert_failure(self.assess(duck=changed), 1, 'shape.filter_mask_bits')

    def test_missing_end_marker_fails(self):
        self.assert_failure(self.assess(duck=self.good.replace('KONIEC OK\n', '')), 4, 'Duckling: missing')

    def test_missing_reference_end_marker_fails(self):
        self.assert_failure(self.assess(reference=self.good.replace('KONIEC OK\n', '')), 4, 'C: missing')

    def test_nonzero_exit_fails(self):
        self.assert_failure(self.assess(exit_code=7), 4, 'code exit Ee6b67ce8a51d=7')

    def test_missing_intermediate_frame_fails(self):
        path = self.png / 'klatki' / 'klatka-090.png'
        data = path.read_bytes()
        path.unlink()
        self.addCleanup(path.write_bytes, data)
        self.assert_failure(self.assess(), 3, 'klatka-090.png')

    def test_wrong_dimensions_fail(self):
        self.replace_file(self.png / 'klatka-180.png', encode_png([bytes((230, 41, 55))], 1))
        self.assert_failure(self.assess(), 3, 'rozmiar')

    def test_corrupt_crc_fails(self):
        path = self.png / 'klatka-180.png'
        data = bytearray(path.read_bytes())
        data[-1] ^= 1
        self.replace_file(path, bytes(data))
        self.assert_failure(self.assess(), 3, 'CRC')

    def test_final_copy_must_match_pixels(self):
        path = self.png / 'klatka-180.png'
                                                                  
        background = bytes((245, 245, 245)) * 800
        floor = bytes((0, 117, 44)) * 800
        rows = []
        for y in range(600):
            row = background if y < 550 else floor
            if 510 <= y < 550:
                row = row[:380*3] + bytes((230, 41, 55)) * 40 + row[420*3:]
            rows.append(row)
        rows[0] = bytes((1, 2, 3)) + rows[0][3:]
        self.replace_file(path, encode_png(rows, 800))
        self.assert_failure(self.assess(), 3, 'rozne piksele')

    def test_color_tolerance_boundary_passes(self):
        for path in (self.png / 'klatka-180.png', self.png / 'klatki' / 'klatka-180.png'):
            self.replace_file(path, scene_png(180, box_color=(240, 51, 65)))
        rows = self.assess()
        self.assertTrue(rows[2][1], rows[2])

    def test_color_outside_tolerance_fails(self):
        self.replace_file(self.png / 'klatka-180.png', scene_png(180, box_color=(241, 41, 55)))
        self.assert_failure(self.assess(), 3, 'tolerancja=10')

    def test_final_y_outside_range_even_with_matching_logs_fails(self):
        changed = self.change_pos(self.good, 180, 1, '0.720001')
        self.assert_failure(self.assess(duck=changed, reference=changed), 2, 'poza [0.68,0.72]')

    def test_x_strict_boundary_even_with_matching_logs_fails(self):
        changed = self.change_pos(self.good, 1, 0, '4.010000')
        self.assert_failure(self.assess(duck=changed, reference=changed), 2, 'musi byc <0.01')

    def test_line_order_and_nan_are_rejected(self):
        for changed in (self.good.replace('POS 2 ', 'POS 1 ', 1),
                        self.good.replace('POS 1 4.000000', 'POS 1 nan', 1),
                        self.good.replace('DEF world.enable_sleep 1', 'DEF world.enable_sleep true'),
                        self.good.replace('18446744073709551615', '18446744073709551616')):
            with self.subTest(changed=changed[:80]):
                self.assert_failure(self.assess(duck=changed), 2, 'Duckling:')

    def test_extra_stdout_and_duplicate_marker_fail(self):
        self.assert_failure(self.assess(duck=self.good + 'KONIEC OK\n'), 4, 'multiple')
        self.assert_failure(self.assess(duck='log raylib\n' + self.good), 1, 'format')

    def test_crlf_is_accepted(self):
        rows = self.assess(duck=self.good.replace('\n', '\r\n'))
        self.assertTrue(all(row[1] for row in rows), rows)

    def test_cli_writes_report_and_returns_zero_or_one(self):
        reference = self.root / 'C.csv'
        duckling = self.root / 'Duckling.csv'
        report = self.root / 'SPRAWDZENIE.md'
        reference.write_text(self.good, encoding='utf-8')
        duckling.write_text(self.good, encoding='utf-8')
        arguments = ['--wzorzec', str(reference), '--duckling', str(duckling),
                     '--png', str(self.png), '--kod-wyjscia', '0', '--raport', str(report)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, sprawdz.main(arguments))
        self.assertIn('Zaliczone: 4/4', report.read_text(encoding='utf-8'))
        duckling.write_text(self.good.replace('KONIEC OK\n', ''), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, sprawdz.main(arguments))
        self.assertIn('KONIEC OK', report.read_text(encoding='utf-8'))
        self.assertIn('BLAD', report.read_text(encoding='utf-8'))

    def test_cli_bad_arguments_return_one(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, sprawdz.main([]))

    def test_cli_missing_input_writes_failure_report(self):
        report = self.root / 'brak-SPRAWDZENIE.md'
        with contextlib.redirect_stdout(io.StringIO()):
            result = sprawdz.main(['--wzorzec', str(self.root / 'does-not-exist'),
                                   '--duckling', str(self.root / 'also-missing'),
                                   '--png', str(self.png), '--kod-wyjscia', '0', '--raport', str(report)])
        self.assertEqual(1, result)
        self.assertIn('NOT E04ff0184c025 E675b88752d5e', report.read_text(encoding='utf-8'))


class PngDecoderTests(unittest.TestCase):
    def test_rgb_and_rgba_all_filters_and_split_idat(self):
        with tempfile.TemporaryDirectory(prefix='test-png-', dir=Path(__file__).resolve().parent) as directory:
            path = Path(directory) / 'filters.png'
            for channels in (3, 4):
                rows = [bytes((x * 41 + y * 17) % 256 for x in range(4 * channels)) for y in range(6)]
                for mode in range(5):
                    with self.subTest(channels=channels, mode=mode):
                        path.write_bytes(encode_png(rows, 4, channels, (mode,), split_idat=True))
                        actual = sprawdz.read_png(path)
                        self.assertEqual((4, 6, channels, tuple(rows)), actual)

    def test_truncated_and_missing_iend_fail(self):
        with tempfile.TemporaryDirectory(prefix='test-png-', dir=Path(__file__).resolve().parent) as directory:
            path = Path(directory) / 'bad.png'
            good = encode_png([bytes((1, 2, 3))], 1)
            for data in (good[:-1], good[:-12]):
                with self.subTest(length=len(data)):
                    path.write_bytes(data)
                    with self.assertRaisesRegex(ValueError, 'PNG:'):
                        sprawdz.read_png(path)


if __name__ == '__main__':
    unittest.main()