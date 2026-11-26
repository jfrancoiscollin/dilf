"""Synthetic scope boundaries; no scores, legal moves, signatures or fitting."""
from pathlib import Path
import tempfile
import unittest

from research.mtdp.king_origin_remaining_scope import partition, authenticated_scope


class RemainingKingScopeTests(unittest.TestCase):
    def test_only_active_side_king_selected(self):
        active_white = 'W:WK48:B20'
        inactive_white = 'B:WK48:B20'
        active_black = 'B:W31:BK20'
        inactive_black = 'W:W31:BK20'
        men = 'W:W31:B20'
        selected, counts = partition({active_white, inactive_white, active_black, inactive_black, men}, set())
        self.assertEqual(selected, sorted([active_white, active_black]))
        self.assertEqual(counts['historical_without_active_king_fens'], 3)

    def test_prior_check_removes_exact_board_only_and_fresh_cannot_enter(self):
        old = 'W:WK48:B20'; remaining = 'B:W31:BK20'; fresh = 'W:WK49:B20'
        selected, counts = partition({old, remaining}, {old, fresh})
        self.assertEqual(selected, [remaining])
        self.assertEqual(counts['previously_checked_historical_fens'], 1)
        self.assertEqual(counts['historical_active_king_fens'], 2)

    def test_quiet_king_still_included_without_querying_capture_or_score(self):
        selected, _ = partition({'W:WK48:B1'}, set())
        self.assertEqual(selected, ['W:WK48:B1'])

    def test_order_and_partition_denominators(self):
        fens = ['W:WK48:B20', 'B:W31:BK20', 'W:W31:B20']
        one, c = partition(fens, {fens[0]})
        two, _ = partition(list(reversed(fens)), {fens[0]})
        self.assertEqual(one, two)
        self.assertEqual(c['historical_fens'], c['historical_active_king_fens'] + c['historical_without_active_king_fens'])
        self.assertEqual(c['historical_active_king_fens'], c['previously_checked_historical_active_king_fens'] + len(one))

    def test_empty_or_noncanonical_registry_rejected(self):
        for fens in (set(), {'W:WK48,31:B20'}):
            with self.assertRaises(ValueError):
                partition(fens, set())

    def test_unverified_cache_cannot_supply_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'cache'; fake.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'cache digest'):
                authenticated_scope(tmp, fake, tmp)


if __name__ == '__main__':
    unittest.main()
