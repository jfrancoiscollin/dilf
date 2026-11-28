from copy import deepcopy

import pytest

from research.mtdp import best_move_depth_comparison as comparison


def reports():
    transfer = {
        "ordinary_regret_centimen": 50,
        "best_category": "ordinary",
        "transferred_category": "ordinary",
    }
    pair = {
        "fen_a": "A", "fen_b": "B", "games_a": ["1"], "games_b": ["2"],
        "status": "scored", "same_pick": False, "optimal_sets_overlap": False,
        "a_to_b": dict(transfer), "b_to_a": dict(transfer),
    }
    shallow = {
        **dict.fromkeys(comparison._PROVENANCE),
        "scan_successor_depth": 8,
        "action_scores_centimen": {"A": [{"action": [[1, 2], [], False], "score": 0}]},
        "holdout_pairs": [pair], "pcblues_transfer_pairs": [],
    }
    deep = deepcopy(shallow)
    deep["scan_successor_depth"] = 12
    return shallow, deep


def test_counts_persistent_disagreement_and_exact_threshold():
    shallow, deep = reports()
    deep["holdout_pairs"][0]["b_to_a"]["ordinary_regret_centimen"] = 49

    result = comparison.compare(shallow, deep)["cohorts"]["holdout_pairs"]

    assert result["disjoint_at_both_depths"] == 1
    assert result["costs"]["a_to_b"]["at_least_50_at_both_depths"] == 1
    assert result["costs"]["b_to_a"]["at_least_50_at_both_depths"] == 0


def test_rejects_changed_pair_provenance():
    shallow, deep = reports()
    deep["holdout_pairs"][0]["games_b"] = ["3"]

    with pytest.raises(ValueError, match="eligibility or provenance"):
        comparison.compare(shallow, deep)


def test_rejects_changed_legal_actions():
    shallow, deep = reports()
    deep["action_scores_centimen"]["A"][0]["action"][0] = [2, 3]

    with pytest.raises(ValueError, match="legal actions"):
        comparison.compare(shallow, deep)
