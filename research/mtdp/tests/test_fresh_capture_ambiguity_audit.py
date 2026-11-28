"""Diagnostic counterexamples; synthetic engine is not a legality oracle."""
import unittest

from pedagogy.game import Move, parse_fen
from research.mtdp.fresh_capture_ambiguity_audit import diagnose_game, matching_actions
from research.mtdp.pdn import PdnGame, PdnReplayError, validated_trajectory


class SyntheticEngine:
    def __init__(self, pairs):
        self.pairs = pairs

    def legal_moves(self, state):
        return list(self.pairs)

    def apply_move(self, state, move):
        return self.pairs[move]


class CaptureAmbiguityTests(unittest.TestCase):
    def setUp(self):
        self.a = Move((31, 22, 13), (27, 18))
        self.b = Move((31, 24, 13), (28, 19))
        self.game = PdnGame(1, {'FEN': 'W:WK31:B18,19,27,28'}, ('31x13',))
        self.next = parse_fen('B:WK13:B19,28')

    def test_same_endpoint_can_have_divergent_successors(self):
        engine = SyntheticEngine({self.a: self.next, self.b: parse_fen('B:WK13:B18,27')})
        row = diagnose_game(self.game, engine)
        self.assertEqual(row['matching_actions'], 2)
        self.assertEqual(row['distinct_successors'], 2)
        self.assertFalse(row['same_successor'])
        self.assertTrue(row['remains_quarantined'])

    def test_same_successor_does_not_override_strict_action_identity(self):
        engine = SyntheticEngine({self.a: self.next, self.b: self.next})
        self.assertTrue(diagnose_game(self.game, engine)['same_successor'])
        with self.assertRaises(PdnReplayError):
            validated_trajectory(self.game, engine)

    def test_explicit_path_and_capture_kind_are_respected(self):
        engine = SyntheticEngine({self.a: self.next, self.b: self.next})
        self.assertEqual(matching_actions(self.next, '31x22x13', engine), [self.a])
        self.assertEqual(matching_actions(self.next, '31-13', engine), [])

    def test_zero_match_is_not_reported_as_path_ambiguity(self):
        with self.assertRaisesRegex(ValueError, 'multi-action ambiguity'):
            diagnose_game(self.game, SyntheticEngine({}))

    def test_complete_strict_game_cannot_become_a_diagnostic_case(self):
        with self.assertRaisesRegex(ValueError, 'complete strict replay'):
            diagnose_game(self.game, SyntheticEngine({self.a: self.next}))


if __name__ == '__main__':
    unittest.main()
