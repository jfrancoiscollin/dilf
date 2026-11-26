"""Synthetic transition models test enumeration; not a legality oracle."""
import unittest
from pedagogy.game import Move, parse_fen
from research.mtdp.pdn import PdnGame
from research.mtdp.historical_quarantine_frontier import explore


class Model:
    def __init__(self, graph):
        self.graph = graph
    def legal_moves(self, state):
        return list(self.graph.get(state, {}))
    def apply_move(self, state, move):
        return self.graph[state][move]


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.a = parse_fen('W:W31:B18,27')
        self.b = parse_fen('B:W13:B18')
        self.c = parse_fen('B:W13:B27')
        self.d = parse_fen('W:W8:B')
        self.m1 = Move((31,22,13),(27,18))
        self.m2 = Move((31,24,13),(28,19))
        self.m3 = Move((13,8))
        self.game = PdnGame(1, {'FEN':'W:W31:B18,27'}, ('31x13','13-8'))

    def test_branch_then_merge_preserves_all_visited_boards(self):
        r, visited = explore(self.game, Model({self.a:{self.m1:self.b,self.m2:self.c},self.b:{self.m3:self.d},self.c:{self.m3:self.d}}))
        self.assertTrue(r['complete_board_frontier_replay'])
        self.assertEqual(r['maximum_frontier'],2)
        self.assertFalse(r['every_completed_ply_single_board'])
        self.assertEqual(set(visited),{self.a,self.b,self.c,self.d})

    def test_equal_successor_paths_do_not_certify_played_action(self):
        r, _ = explore(self.game, Model({self.a:{self.m1:self.b,self.m2:self.b},self.b:{self.m3:self.d}}))
        self.assertTrue(r['every_completed_ply_single_board'])
        self.assertEqual(r['ambiguities'][0]['matching_actions'],2)
        self.assertTrue(r['strict_action_quarantine_retained'])

    def test_dead_branch_still_contributes_possible_history(self):
        r, visited = explore(self.game, Model({self.a:{self.m1:self.b,self.m2:self.c},self.b:{self.m3:self.d}}))
        self.assertTrue(r['complete_board_frontier_replay'])
        self.assertIn(self.c,visited)

    def test_zero_frontier_is_incomplete(self):
        r, _ = explore(self.game,Model({}))
        self.assertEqual(r['status'],'zero_frontier')
        self.assertFalse(r['complete_board_frontier_replay'])

    def test_caps_stop_without_completeness_credit(self):
        model=Model({self.a:{self.m1:self.b,self.m2:self.c}})
        for kwargs, status in [({'frontier_limit':1},'frontier_cap'),({'action_limit':1},'application_cap')]:
            with self.subTest(status=status):
                r,_=explore(self.game,model,**kwargs)
                self.assertEqual(r['status'],status)
                self.assertFalse(r['complete_board_frontier_replay'])


if __name__ == '__main__':
    unittest.main()
