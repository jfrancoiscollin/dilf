"""Synthetic regression tests for the D1 LCB/Q score-blind overlap."""
import json

import pytest

from research.mtdp.decision_equivalence.pair_overlap import compare_pairs


def row(fen, game, lcb, q, action="a"):
    return {
        "fen": fen, "game_id": game, "actions": [[action]],
        "signatures": {"E": [fen], "L": [action], "LCB": [lcb], "Q": [q]},
    }


def test_partition_and_cross_game_provenance():
    records = [
        row("A", "g1", 1, 1),
        row("B", "g2", 1, 1),
        row("C", "g1", 1, 2),
        row("D", "g3", 2, 1, "b"),
        row("E", "g1", 3, 3),
    ]
    result = compare_pairs(records)
    buckets = result["buckets"]
    assert buckets["common"]["distinct_fen_pairs"] == 1  # A-B
    assert buckets["lcb_only"]["distinct_fen_pairs"] == 2  # A-C, B-C
    assert buckets["q_only"]["distinct_fen_pairs"] == 2  # A-D, B-D
    assert buckets["q_only"]["different_legal_action_pairs"] == 2
    assert buckets["common"]["disjoint_owning_games_pairs"] == 1
    assert buckets["lcb_only"]["disjoint_owning_games_pairs"] == 1
    assert result["distinct_signatures"] == {"LCB": 3, "Q": 3}
    assert result["distinct_fens"] == 5


def test_duplicate_fen_provenance_not_counted_twice():
    records = [row("A", "g1", 1, 1), row("A", "g2", 1, 1),
               row("B", "g1", 1, 1)]
    result = compare_pairs(records)
    assert result["observations"] == 3
    assert result["distinct_fens"] == 2
    assert result["buckets"]["common"]["cross_game_provenance_pairs"] == 1
    assert result["buckets"]["common"]["disjoint_owning_games_pairs"] == 0


def test_deterministic_under_row_permutation():
    records = [row("B", "g2", 1, 1), row("A", "g1", 1, 1),
               row("C", "g3", 2, 1)]
    assert json.dumps(compare_pairs(records), sort_keys=True) == json.dumps(
        compare_pairs(list(reversed(records))), sort_keys=True
    )


@pytest.mark.parametrize("bad", [
    {"fen": "", "game_id": "g", "actions": [], "signatures": {}},
    {"fen": "A", "game_id": "g", "actions": [], "signatures": {"E": 1}},
    {"fen": "A", "game_id": "g", "actions": [["a"], ["a"]],
     "signatures": {"E": 1, "L": 1, "LCB": 1, "Q": 1}},
])
def test_fail_closed_invalid_rows(bad):
    with pytest.raises(ValueError):
        compare_pairs([bad])


def test_fail_closed_contradictory_duplicate_and_exact_collision():
    with pytest.raises(ValueError, match="contradictory"):
        compare_pairs([row("A", "g1", 1, 1), row("A", "g2", 2, 1)])
    records = [row("A", "g1", 1, 1), row("B", "g2", 1, 1)]
    records[1]["signatures"]["E"] = ["A"]
    with pytest.raises(ValueError, match="E signature"):
        compare_pairs(records)


def test_empty_population_and_example_cap():
    assert compare_pairs([])["buckets"]["common"]["distinct_fen_pairs"] == 0
    assert compare_pairs([row("A", "g1", 1, 1), row("B", "g2", 1, 1)],
                         max_examples=0)["buckets"]["common"]["examples"] == []
    with pytest.raises(ValueError):
        compare_pairs([], max_examples=-1)
