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


if __name__ == '__main__':
    unittest.main()
