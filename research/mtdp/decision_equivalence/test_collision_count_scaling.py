"""Synthetic reference oracle; not an independent FMJD cohort."""
from itertools import combinations
from random import Random

from research.mtdp.decision_equivalence.legal_action_collision_audit import audit_action_sets


def test_counts_match_pairwise_oracle():
    rng = Random(43)
    for size in (0, 1, 2, 10, 200):
        rows = [
            dict(
                game_id="synthetic",
                position_id=str(i),
                signature=rng.choice(["A", "B", "C"]),
                legal_moves=rng.sample(["1-6", "2-7", "3-8", "4-9"], rng.randint(1, 4)),
            )
            for i in range(size)
        ]
        result = audit_action_sets(rows)
        pairs = [(a, b) for a, b in combinations(rows, 2) if a["signature"] == b["signature"]]
        same = sum(set(a["legal_moves"]) == set(b["legal_moves"]) for a, b in pairs)
        assert result["collision_pairs"] == len(pairs)
        assert result["same_legal_action_set_pairs"] == same
        assert result["different_legal_action_set_pairs"] == len(pairs) - same
        assert not result["best_move_equivalence_proven"]
        assert not result["minimax_equivalence_proven"]


def test_large_collision_class_without_pair_materialization():
    rows = [
        dict(game_id="synthetic", position_id=str(i), signature="S", legal_moves=["1-6"])
        for i in range(10000)
    ]
    result = audit_action_sets(rows)
    assert result["collision_pairs"] == 49_995_000
    assert result["same_legal_action_set_pairs"] == 49_995_000
    assert result["different_legal_action_set_pairs"] == 0
