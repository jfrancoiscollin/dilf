from pedagogy.game import Move, initial_state
from research.mtdp.jass_benchmark.candidate_ambiguities import explain
from research.mtdp.pdn import PdnGame


def test_ambiguous_paths_remain_quarantined_even_with_identical_successor():
    class Rules:
        def legal_moves(self, state):
            return [Move((31, 22, 13), (27, 18)), Move((31, 24, 13), (27, 18))]

        def apply_move(self, state, move):
            return initial_state()

    game = PdnGame(46, {"Site": "https://lidraughts.org/abcdefgh"}, ("31x13",))
    report = explain(game, Rules())
    assert len(report["legal_candidates"]) == 2
    assert report["distinct_successors"] == 1
    assert report["disposition"] == "whole_game_remains_quarantined"
    assert report["ply"] == 1
    assert report["site"].endswith("abcdefgh")
