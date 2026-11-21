import unittest

from research.mtdp.decision_equivalence.signature_collision_witnesses import witnesses


def row(game, pos, sig, successor):
    return {"game_id": game, "position_id": pos,
            "signatures": {"L": sig}, "successor_fingerprint": successor}


class WitnessTests(unittest.TestCase):
    def test_cross_game_divergent_and_deterministic(self):
        rows = [row("b", "2", "x", "n2"), row("a", "1", "x", "n1"),
                row("a", "3", "x", "n3"), row("c", "4", "y", "n4")]
        first = witnesses(rows)
        self.assertEqual(first, witnesses(list(reversed(rows))))
        pair = first["families"]["L"][0]
        self.assertEqual((pair["a"]["game_id"], pair["b"]["game_id"]), ("a", "b"))
        self.assertEqual(pair["witness"], "same_signature_different_successor_cross_game")

    def test_same_game_or_same_successor_not_witness(self):
        self.assertEqual(witnesses([row("a", "1", "x", "n1"),
                                    row("a", "2", "x", "n2")])["families"]["L"], [])
        self.assertEqual(witnesses([row("a", "1", "x", "n"),
                                    row("b", "2", "x", "n")])["families"]["L"], [])

    def test_cap_and_score_rejection(self):
        rows = [row("a", "1", "x", "n1"), row("b", "2", "x", "n2")]
        self.assertEqual(witnesses(rows, max_per_family=0)["families"]["L"], [])
        with self.assertRaises(ValueError):
            witnesses(rows, max_per_family=-1)
        rows[0]["score"] = 1
        with self.assertRaises(ValueError):
            witnesses(rows)


if __name__ == "__main__":
    unittest.main()
