import unittest
from research.mtdp.decision_equivalence.signature_collision_metrics import measure


class MetricsTest(unittest.TestCase):
    def test_collisions_are_not_equivalence(self):
        rows = [dict(position_id='a', game_id='g1', signature='X'),
                dict(position_id='b', game_id='g2', signature='X'),
                dict(position_id='c', game_id='g2', signature='Y')]
        out = measure(rows)
        self.assertEqual(out['compression_ratio'], 1.5)
        self.assertEqual(out['collision_position_fraction'], 2 / 3)
        self.assertEqual(out['cross_game_collision_groups'], 1)
        self.assertEqual(out['collision_pairs'], 1)
        self.assertEqual(out['cross_game_collision_pairs'], 1)
        self.assertFalse(out['decision_equivalence_established'])

    def test_duplicate_identity_rejected(self):
        rows = [dict(position_id='a', game_id='g1', signature='X')] * 2
        with self.assertRaisesRegex(ValueError, 'duplicate position_id'):
            measure(rows)

    def test_empty_and_malformed_rejected(self):
        for rows in ([], [{}], [{'position_id': 'a', 'game_id': 'g', 'signature': ''}]):
            with self.assertRaises(ValueError):
                measure(rows)

    def test_no_collision(self):
        out = measure([dict(position_id=str(i), game_id='g', signature=str(i)) for i in range(4)])
        self.assertEqual(out['compression_ratio'], 1)
        self.assertEqual(out['collision_position_fraction'], 0)
        self.assertEqual(out['collision_pairs'], 0)
        self.assertIsNone(out['cross_game_collision_pair_fraction'])

    def test_pair_weighting_and_within_game_pairs(self):
        rows = [dict(position_id=str(i), game_id=g, signature='X')
                for i, g in enumerate(['a', 'a', 'b', 'b'])]
        out = measure(rows)
        self.assertEqual(out['collision_pairs'], 6)
        self.assertEqual(out['cross_game_collision_pairs'], 4)
        self.assertAlmostEqual(out['cross_game_collision_pair_fraction'], 2 / 3)

    def test_group_count_is_not_pair_count(self):
        rows = [dict(position_id=str(i), game_id=str(i), signature='X') for i in range(5)]
        out = measure(rows)
        self.assertEqual(out['collision_groups'], 1)
        self.assertEqual(out['collision_pairs'], 10)
        self.assertEqual(out['cross_game_collision_pairs'], 10)


if __name__ == '__main__':
    unittest.main()
