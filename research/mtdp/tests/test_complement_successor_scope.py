"""Small structural complements; no legal or successor engines queried."""
from pathlib import Path
import tempfile
import unittest
from research.mtdp.complement_successor_scope import derive_rows, catalogue_rows, prior_exclusions
from research.mtdp.nonking_oracle import StreamEvidence


class ComplementScopeTests(unittest.TestCase):
    def derive(self, rows, history, excluded):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'manifest', Path(tmp) / 'fens'
            with StreamEvidence(a) as manifest, StreamEvidence(b) as fens:
                report = derive_rows(rows, history, excluded, manifest, fens)
            return report, a.read_bytes(), b.read_bytes()

    def test_fresh_and_prior_parents_excluded_and_all_remaining_roots_kept(self):
        a, b, fresh = 'B:W31:B20', 'W:W31:B20', 'W:W32:B20'
        rows = [(a, 'old', [('20-24', False)]), (b, 'old', [('31-26', False), ('31-27', False)]), (fresh, 'old', [('32-27', False)])]
        report, manifest, fens = self.derive(rows, {a, b}, {a})
        self.assertEqual(report['selected_fens'], 1)
        self.assertEqual(report['selected_total_legal_roots'], 2)
        self.assertEqual(report['nonhistorical_fens_excluded'], 1)
        self.assertEqual(fens, (b + '\n').encode())
        self.assertIn(b'31-27', manifest)

    def test_risk_parent_cannot_leak_into_complement(self):
        with self.assertRaisesRegex(ValueError, 'Risk-tagged'):
            self.derive([('W:W6:B45', 'old', [('6-1', True)])], {'W:W6:B45'}, set())

    def test_missing_duplicate_and_unordered_parents_refused(self):
        a, b = 'B:W31:B20', 'W:W31:B20'
        row = (a, 'old', [('20-24', False)])
        for rows, history in [([row], {a, b}), ([row, row], {a}), ([(b, 'old', []), row], {a, b})]:
            with self.assertRaises(ValueError):
                self.derive(rows, history, set())

    def test_zero_action_terminal_kept_and_streamed(self):
        report, _, fens = self.derive([('W:W:B', 'old', [])], {'W:W:B'}, set())
        self.assertEqual(report['selected_fens'], 1)
        self.assertEqual(report['selected_total_legal_roots'], 0)
        self.assertEqual(fens, b'W:W:B\n')

    def test_cached_source_order_and_root_duplicates_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'catalogue'
            for raw in ['W:W31:B20\t31-26=0\t31-26=0\n', 'W:W31:B20\nB:W31:B20\n']:
                p.write_text(raw)
                with self.assertRaises(ValueError):
                    list(catalogue_rows('synthetic', p, 1))

    def test_prior_parent_file_must_match_verified_risk_proof(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'old-parents'; p.write_bytes(b'W:W31:B20\n')
            with self.assertRaisesRegex(ValueError, 'Prior risk parent list changed'):
                prior_exclusions(root, p)


if __name__ == '__main__':
    unittest.main()
