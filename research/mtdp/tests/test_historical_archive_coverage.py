"""Known-archive containment, representation aliases and tampered provenance."""
import json
import os
import unittest
from pathlib import Path

from research.mtdp.historical_archive_coverage import audit, coverage, PROVENANCE

ROOT = Path(__file__).resolve().parents[3]


class TestHistoricalArchiveCoverage(unittest.TestCase):
    def test_king_order_alias_is_canonicalized(self):
        r = coverage(['B:WK48,13:BK46,3'], ['B:W13,K48:B3,K46'])
        self.assertEqual(r['archived_fens_missing_from_cache'], 0)
        self.assertEqual(r['archive_canonical_fen_set_sha256'], r['cache_canonical_fen_set_sha256'])

    def test_partial_overlap_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, 'misses 1'):
            coverage(['W:W32:B1', 'B:W28:B1'], ['W:W32:B1'])

    def test_turn_is_part_of_identity(self):
        with self.assertRaises(ValueError):
            coverage(['W:W32:B1'], ['B:W32:B1'])

    def test_man_king_identity_preserved(self):
        with self.assertRaises(ValueError):
            coverage(['W:WK32:B1'], ['W:W32:B1'])

    def test_cache_superset_does_not_need_equal_population(self):
        r = coverage(['W:W32:B1'], ['W:W32:B1', 'B:W28:B1'])
        self.assertEqual((r['archived_canonical_fens'], r['cache_canonical_fens']), (1, 2))

    def test_empty_inputs_refused(self):
        for a, b in [([], ['W:W32:B1']), (['W:W32:B1'], [])]:
            with self.assertRaises(ValueError):
                coverage(a, b)

    def test_tampered_inventory_fails_before_cache(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / PROVENANCE
            p.parent.mkdir(parents=True)
            p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'provenance bytes'):
                audit(Path(directory), Path(directory) / 'absent-cache')

    def test_real_pinned_archive_and_cache_match_versioned_report(self):
        cache = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
        if not cache:
            if os.environ.get('MTDP_REQUIRE_HISTORICAL_ALIASES') == '1':
                self.fail('Pinned cache required')
            self.skipTest('Pinned cache unavailable')
        result = audit(ROOT, Path(cache))
        expected = json.loads((ROOT / 'research/mtdp/validation/historical-archive-cache-coverage-2026-11-23.json').read_text())
        self.assertEqual(result, expected)
        self.assertFalse(result['complete_historical_exclusion_registry'])
        self.assertFalse(result['independent_cohort_qualified'])


if __name__ == '__main__':
    unittest.main()
