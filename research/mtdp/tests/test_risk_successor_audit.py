"""Frozen manifest and cached-root guard tests on explicit synthetic models."""
from pathlib import Path
import tempfile
import unittest

from pedagogy.game import Move, parse_fen
from research.mtdp.risk_successor_audit import compare_record, load_manifest
from research.mtdp.return_capture_oracle import root_key


class RiskSuccessorAuditTests(unittest.TestCase):
    def setUp(self):
        self.a = Move((31, 22, 13), (27, 18))
        self.b = Move((31, 24, 13), (18, 27))
        self.child = parse_fen('B:W13:B')
        self.record = dict(fen='W:W31:B18,27', catalogue_id='synthetic', categories=['multiple_capture'], legal_roots=[list(root_key(self.a))])
        self.reference = [(root_key(self.a)[0], False, 'B:W13:B')]

    def test_all_paths_and_cached_reference_match(self):
        row = compare_record(0, self.record, [self.a, self.b], lambda s, m: self.child, self.reference)
        self.assertTrue(row['all_roots_and_successors_equal'])
        self.assertTrue(row['cached_legal_roots_equal'])
        self.assertEqual(row['python_paths'], 2)
        self.assertEqual(row['risk_categories'], ['multiple_capture'])

    def test_frozen_reference_difference_is_not_hidden_by_engine_agreement(self):
        record = {**self.record, 'legal_roots': [['31x12x18x27', False]]}
        row = compare_record(0, record, [self.a], lambda s, m: self.child, self.reference)
        self.assertFalse(row['all_roots_and_successors_equal'])
        self.assertFalse(row['cached_legal_roots_equal'])
        self.assertEqual(row['cached_legal_roots'], record['legal_roots'])

    def test_successor_disagreement_is_kept_with_correct_cached_roots(self):
        row = compare_record(0, self.record, [self.a], lambda s, m: parse_fen('W:W13:B'), self.reference)
        self.assertTrue(row['cached_legal_roots_equal'])
        self.assertFalse(row['all_roots_and_successors_equal'])
        self.assertEqual(len(row['shared_root_successor_mismatches']), 1)

    def test_unverified_scope_fails_before_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'research/mtdp/validation'; p.mkdir(parents=True)
            (p / 'risk-successor-scope-2026-11-26.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'Verified evidence digest mismatch'):
                load_manifest(tmp, 'unused', 'unused')

    def test_tampered_manifest_or_list_fails_before_any_transition(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'manifest'; q = Path(tmp) / 'list'
            p.write_bytes(b'{}\n'); q.write_bytes(b'W:W31:B20\n')
            with self.assertRaisesRegex(ValueError, 'Frozen risk manifest/list digest mismatch'):
                load_manifest(root, p, q)


if __name__ == '__main__':
    unittest.main()
