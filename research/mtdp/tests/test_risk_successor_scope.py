"""Structural selection only: no legal queries, transitions, scores or efficacy."""
from pathlib import Path
import tempfile
import unittest
from research.mtdp.risk_successor_scope import categories, select_rows, authenticate_catalogue


class RiskScopeTests(unittest.TestCase):
    def test_risk_predicates_overlap_and_normalize_capture_mask(self):
        self.assertEqual(categories(('20x20x18x19x23x24', False)), ['multiple_capture', 'return_origin'])
        self.assertEqual(categories(('12x3x8', True)), ['promotion'])
        self.assertEqual(categories(('6-1', True)), ['promotion'])
        self.assertEqual(categories(('6-1', False)), [])
        self.assertEqual(categories(('31x22x27', False)), [])

    def test_bad_capture_order_duplicate_and_promotion_type_refused(self):
        for root in [('20x20x24x18', False), ('20x20x18x18', False), ('6-1', 1)]:
            with self.subTest(root=root), self.assertRaises(ValueError):
                categories(root)

    def test_fresh_only_risks_cannot_enter_and_prior_fixtures_are_removed(self):
        a, b, fresh = 'W:W31:B20', 'B:W31:B20', 'W:W32:B20'
        rows = [('old', a, [('31x31x18x27', False)]), ('old', b, [('20-24', False)]),
                ('fresh', fresh, [('32x32x18x27', False)])]
        selected, summary = select_rows(rows, {a, b}, {a})
        self.assertEqual(selected, [])
        self.assertEqual(summary['nonhistorical_fens_excluded'], 1)
        self.assertEqual(summary['prior_risk_fixture_fens_excluded'], 1)

    def test_all_roots_preserved_for_selected_parent(self):
        fen = 'W:W6,31:B45'
        rows, summary = select_rows([('synthetic', fen, [('31-26', False), ('6-1', True)])], {fen}, set())
        self.assertEqual(rows[0]['legal_roots'], [['31-26', False], ['6-1', True]])
        self.assertEqual(len(rows[0]['risk_roots']), 1)
        self.assertEqual(summary['selected_total_legal_roots'], 2)

    def test_parent_count_and_root_category_counts_are_not_conflated(self):
        fen = 'W:W20:B18,19,23,24'
        roots = [('20x20x18x19x23x24', False), ('20x20x8x9x13x14', False)]
        rows, summary = select_rows([('synthetic', fen, roots)], {fen}, set())
        self.assertEqual(summary['selected_fens'], 1)
        self.assertEqual(summary['selected_risk_roots'], 2)
        self.assertEqual(summary['selected_fens_by_category']['return_origin'], 1)
        self.assertEqual(summary['selected_roots_by_category']['return_origin'], 2)

    def test_source_order_does_not_change_sorted_manifest(self):
        a, b = 'W:W6:B45', 'B:W6:B45'
        rows = [('a', a, [('6-1', True)]), ('b', b, [('45-50', True)])]
        one, _ = select_rows(rows, {a, b}, set())
        two, _ = select_rows(reversed(rows), {a, b}, set())
        self.assertEqual(one, two)

    def test_missing_duplicate_parent_or_duplicate_root_fail(self):
        a, b = 'W:W6:B45', 'B:W6:B45'
        row = ('synthetic', a, [('6-1', True)])
        for rows, history in [([row], {a, b}), ([row, row], {a}),
                              ([('synthetic', a, [('6-1', True), ('6-1', True)])], {a})]:
            with self.assertRaises(ValueError):
                select_rows(rows, history, set())

    def test_tampered_catalogue_bytes_refused_before_parsing(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'forged-catalogue'; path.write_bytes(b'fake\n')
            with self.assertRaisesRegex(ValueError, 'Pinned catalogue digest/size mismatch'):
                authenticate_catalogue(root, 'nonking', path)


if __name__ == '__main__':
    unittest.main()
