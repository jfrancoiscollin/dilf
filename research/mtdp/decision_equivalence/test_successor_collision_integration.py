"""Score-blind integration checks for D1 signature collision semantics.

Synthetic fixtures only: no cohort, Scan labels, or minimax conclusions.
"""
import unittest

from research.mtdp.decision_equivalence.canonical_successors import fingerprint
from research.mtdp.decision_equivalence.signature_collision_audit import audit


class FingerprintCollisionIntegrationTests(unittest.TestCase):
    def test_equal_legal_actions_do_not_imply_equal_transitions(self):
        first = fingerprint({"31-27": "W:27,18", "32-28": "W:28,18"})
        second = fingerprint({"31-27": "W:27,19", "32-28": "W:28,19"})
        self.assertNotEqual(first, second)
        rows = [
            {"game_id": "game-A", "position_id": "p1",
             "signatures": {"L": "same-legal-actions", "LCB": "structure-A"},
             "successor_fingerprint": first},
            {"game_id": "game-B", "position_id": "p2",
             "signatures": {"L": "same-legal-actions", "LCB": "structure-B"},
             "successor_fingerprint": second},
        ]
        result = audit(rows)
        legal = result["families"]["L"]
        refined = result["families"]["LCB"]
        self.assertEqual(legal["collision_pairs"], 1)
        self.assertEqual(legal["cross_game_successor_divergent_pairs"], 1)
        self.assertEqual(refined["collision_pairs"], 0)
        self.assertEqual(refined["unique_signatures"], 2)
        self.assertEqual(result["interpretation"],
                         "descriptive_only_not_best_move_or_minimax_equivalence")

    def test_identical_transition_fingerprint_is_not_minimax_evidence(self):
        transition = fingerprint({"31-27": "W:27,18"})
        rows = [
            {"game_id": "A", "position_id": "p1",
             "signatures": {"L": "same"}, "successor_fingerprint": transition},
            {"game_id": "B", "position_id": "p2",
             "signatures": {"L": "same"}, "successor_fingerprint": transition},
        ]
        result = audit(rows)["families"]["L"]
        self.assertEqual(result["collision_pairs"], 1)
        self.assertEqual(result["successor_divergent_collision_pairs"], 0)
        # No target scores, best-move labels or minimax certificates exist here.


if __name__ == "__main__":
    unittest.main()
