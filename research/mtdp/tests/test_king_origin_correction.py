import unittest
from unittest.mock import patch
from research.mtdp import king_origin_correction as correction
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.king_origin_regression import rotate_swap,cases
from pedagogy.game import parse_fen


class KingOriginTests(unittest.TestCase):
    def test_tampered_rules_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'exact pinned'):
            correction.patch_source(b'arbitrary rules')

    def test_replacement_is_scoped_to_king_function_only(self):
        before=correction.BEFORE
        source=('def elsewhere():\n'+before+'def _capture_sequences_king():\n'+before+'\n\ndef _all_captures():\n'+before).encode()
        with patch.object(correction,'BASE_RULES_SHA',digest(source)):
            changed=correction.patch_source(source).decode()
        self.assertEqual(changed.count(correction.AFTER),1)
        self.assertEqual(changed.count(before),2)

    def test_multiple_king_ray_reads_fail_closed(self):
        source=('def _capture_sequences_king():\n'+correction.BEFORE*2+'\n\ndef _all_captures():\n').encode()
        with patch.object(correction,'BASE_RULES_SHA',digest(source)),self.assertRaisesRegex(ValueError,'exactly one'):
            correction.patch_source(source)

    def test_rotation_is_involution_and_fixed_population_has_eight_boards(self):
        state=parse_fen('B:W15,20,22,39,K42,45:B5,K48')
        self.assertEqual(rotate_swap(rotate_swap(state)),state)
        self.assertEqual(len(cases()),8)


if __name__=='__main__':
    unittest.main()
