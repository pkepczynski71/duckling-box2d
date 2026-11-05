pass                                                                 
import io
import json
from pathlib import Path
import unittest
import zapytania18_tools as t


class Transport18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = t.manifest()

    def test_populations_and_literal_sides(self):
        for profile, n in [('DIRECT', 96), ('PUBLIC', 96), ('GUARD', 821)]:
            c, d = (t.emit(profile, side, self.data).splitlines() for side in 'CD')
            self.assertEqual(c[0], f'PORT18 A {profile} {n}')
            self.assertEqual(len(c), len(d))
            for a, b in zip(c, d):
                aa, bb = a.split(), b.split()
                offset = 4 if aa[0] == 'O' else 5 if aa[0] == 'G' else len(aa)
                self.assertEqual(aa[:offset], bb[:offset])
                self.assertEqual([int(x, 16) for x in aa[offset:]], [int(x) for x in bb[offset:]])

    def test_full_transcript_arities_counts(self):
        expected_counts = {
            'DIRECT': {'CASE': 96, 'E18': 96, 'R18': 96, 'I18': 96, 'ENDCASE': 96, 'END': 1},
            'PUBLIC': {'CASE': 96, 'E18': 768, 'R18': 768, 'I18': 384, 'V18': 1248, 'ENDCASE': 96, 'END': 1},
            'GUARD': {'CASE': 821, 'G18': 1642, 'GA18': 1642, 'ENDCASE': 821, 'END': 1},
        }
        for profile, tags in expected_counts.items():
            self.assertEqual(t.compare(t.expected(profile), t.expected(profile))['tags'], tags)

    def test_comparator_detects_corruption(self):
        good = list(t.expected('DIRECT'))
        alternatives = []
        changed = good.copy(); changed[2] = changed[2].replace('00000001\n', '00000000\n'); alternatives.append(changed)
        alternatives += [good[:-1], good[1:], good + [good[-1]], good[:2]+good[3:], good[:2]+[good[2]]+good[2:]]
        swapped = good.copy(); swapped[1], swapped[2] = swapped[2], swapped[1]; alternatives.append(swapped)
                                                                                     
        alternatives.append([x for x in good if not x.startswith('I18 ')])
        for altered in alternatives:
            with self.assertRaises(ValueError):
                t.compare(iter(altered), iter(good))

    def test_noncanonical_outputs_rejected(self):
        for s in ['END 096\n', 'END 96 \n', 'END 96\r\n', 'END 96', 'END 96\nEND 96\n',
                  'R18 1 1 500 0 0 1 1 0000000A\n', 'R18 1 1 500 0 0 2 1 00000001\n']:
            with self.assertRaises(ValueError):
                t.parse_record(s)

    def test_public_different_result_and_refusal(self):
        raw = {x['id']: x for x in self.data['direct']}
        for p in self.data['public']:
            self.assertNotEqual(raw[p['id']]['resultH'], raw[p['differentQueryDirectId']]['resultH'])
            self.assertEqual([x['seq'] for x in p['operations']], list(range(1, 9)))
            self.assertEqual(p['operations'][0]['payloadH'], p['operations'][7]['payloadH'])
            self.assertEqual(p['refusalSeq7']['status'], 0 if p['kind'] == 0 else 5)

    def test_guard_populations_and_parser_pairs(self):
        from collections import Counter
        self.assertEqual(Counter((r['negativeAccepted'], r['negativeStatus'], r['negativeReason']) for r in self.data['guards']),
                         {(1, 0, 0): 35, (0, 5, 22): 222, (0, 4, 0): 564})
        for p in self.data['parsers']:
            self.assertEqual(p['exitCode'], 2)
            self.assertEqual(p['stderr'], 'PORT18A: '+p['error']+'\n')
            self.assertTrue(p['positiveStdout'].endswith('END 1\n'))
            self.assertTrue(p['positiveC'] and p['positiveD'])

    def test_separate_proposed_N13_has_real_C_witnesses_and_copy_recipe(self):
        packet=json.loads((t.HERE/'18a-N-propozycja.json').read_text(encoding='utf-8'))
        self.assertEqual(len(packet['direct']),13)
        data=t.additional_data(packet,self.data)
        for row in packet['direct']:
            self.assertTrue(row['positiveCounters'])
            self.assertTrue(all(v>0 for v in row['positiveCounters'].values()))
        self.assertEqual(next(r for r in packet['direct'] if r['proposal']=='iteration20-finite-overflow')['resultH'][-1],'00000014')
        overflow=next(r for r in packet['public'] if r['proposal']=='circle-finite-input-overflow')
        self.assertEqual(overflow['resultForSeq6'],{'status':5,'reason':22,'resultH':['00000000']*7})
        for profile,n in [('DIRECT',13),('PUBLIC',104)]:
            result=t.compare(t.expected(profile,data[profile]),t.expected(profile,data[profile]))
            self.assertEqual(result['tags']['R18'],n)
            self.assertEqual(t.additional_input(packet,profile,'C').splitlines()[0],f'PORT18 A {profile} 13')


if __name__ == '__main__':
    unittest.main()
