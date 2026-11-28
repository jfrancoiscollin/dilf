import unittest
from research.mtdp.fresh_position_footprint import footprint


class ExactFootprintTests(unittest.TestCase):
    def test_occurrences_are_not_distinct_positions_or_independent_games(self):
        result, _ = footprint({'g1': ['H', 'A', 'A'], 'g2': ['H', 'A', 'B']}, {'H'})
        self.assertEqual(result['position_occurrences'], 6)
        self.assertEqual(result['distinct_fens'], 3)
        self.assertEqual(result['historical_occurrences'], 2)
        self.assertEqual(result['nonhistorical_distinct_fens'], 2)
        self.assertEqual(result['repeated_within_game_occurrences'], 1)
        self.assertEqual(result['nonhistorical_cross_game_shared_fens'], 1)
        self.assertEqual(result['nonhistorical_exact_fen_game_components'], [['g1', 'g2']])

    def test_historical_opening_does_not_link_novel_components(self):
        result, _ = footprint({'g1': ['H', 'A'], 'g2': ['H', 'B']}, {'H'})
        self.assertEqual(result['exact_fen_component_count'], 2)
        self.assertEqual(result['nonhistorical_cross_game_shared_fens'], 0)

    def test_transitive_sharing_links_three_games(self):
        result, _ = footprint({'g1': ['A'], 'g2': ['A', 'B'], 'g3': ['B'], 'g4': ['C']}, set())
        self.assertEqual(result['nonhistorical_exact_fen_game_components'], [['g1', 'g2', 'g3'], ['g4']])
        self.assertEqual(result['largest_component_games'], 3)

    def test_input_insertion_order_does_not_change_inventory(self):
        first = footprint({'g1': ['A', 'A'], 'g2': ['B', 'A']}, set())
        second = footprint({'g2': ['B', 'A'], 'g1': ['A', 'A']}, set())
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
