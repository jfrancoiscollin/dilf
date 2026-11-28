"""Score-blind scope partitions and authentication refusal tests."""
from pathlib import Path
import tempfile
import unittest
from research.mtdp.nonking_oracle_scope import partition, verified_json, authenticated_scope


class NonkingScopeTests(unittest.TestCase):
    def test_opponent_king_does_not_exclude_active_men(self):
        selected, counts = partition({'W:W31:BK20', 'B:WK48:B20', 'W:WK48:B20'}, set())
        self.assertEqual(selected, ['B:WK48:B20', 'W:W31:BK20'])
        self.assertEqual(counts['historical_with_active_king_fens'], 1)

    def test_previous_checks_remove_exact_historical_board_only(self):
        a, b, fresh = 'W:W31:B20', 'B:W31:B20', 'W:W32:B20'
        selected, counts = partition({a, b}, {a, fresh})
        self.assertEqual(selected, [b])
        self.assertEqual(counts['previously_checked_historical_nonking_fens'], 1)

    def test_terminal_and_kingless_boards_stay_in_scope(self):
        selected, _ = partition({'W:W:B', 'B:WK48:B'}, set())
        self.assertEqual(selected, ['B:WK48:B', 'W:W:B'])

    def test_no_source_order_or_duplicate_can_change_set_partition(self):
        fens = ['W:W31:B20', 'B:W31:B20', 'W:WK48:B20']
        a, c = partition(fens, {fens[0]})
        b, _ = partition(list(reversed(fens)) + [fens[0]], {fens[0]})
        self.assertEqual(a, b)
        self.assertEqual(c['historical_fens'], c['historical_with_active_king_fens'] + c['historical_without_active_king_fens'])
        self.assertEqual(c['historical_without_active_king_fens'], c['previously_checked_historical_nonking_fens'] + len(a))

    def test_noncanonical_or_empty_population_fails(self):
        for values in (set(), {'W:W32,31:B20'}):
            with self.assertRaises(ValueError):
                partition(values, set())

    def test_forged_evidence_never_becomes_an_empty_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'evidence.json'; p.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'evidence digest mismatch'):
                verified_json(p, 'a' * 64)
            with self.assertRaisesRegex(ValueError, 'cache digest'):
                authenticated_scope(tmp, p, p)


if __name__ == '__main__':
    unittest.main()
