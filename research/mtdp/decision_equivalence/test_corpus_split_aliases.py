"""D1 admission regression: full-source/trajectory split isolation.

Synthetic hashes only: not an independent FMJD cohort.
"""
from research.mtdp.decision_equivalence.corpus_admission import audit


def _row(split, game, tournament, raw, trajectory, position):
    return {
        "split": split, "game_id": game, "tournament_id": tournament,
        "event_id": "synthetic_" + tournament, "ply": 0,
        "fen": "synthetic_" + position,
        "raw_sha256": raw * 64,
        "trajectory_sha256": trajectory * 64,
        "canonical_sha256": position * 64,
    }


EXCLUSIONS = {"game_ids": [], "raw_sha256": [],
              "trajectory_sha256": [], "canonical_sha256": []}


def test_cross_split_raw_source_rejected_without_position_overlap():
    rows = [_row("train", "g1", "t1", "a", "b", "c"),
            _row("test", "g2", "t2", "a", "d", "e")]
    result = audit(rows, EXCLUSIONS)
    assert not result["admissible_structurally"]
    assert "cross_split_raw_source_leakage" in result["errors"]
    assert "cross_split_position_leakage" not in result["errors"]


def test_cross_split_trajectory_rejected_without_position_overlap():
    rows = [_row("train", "g1", "t1", "a", "b", "c"),
            _row("test", "g2", "t2", "d", "b", "e")]
    result = audit(rows, EXCLUSIONS)
    assert not result["admissible_structurally"]
    assert "cross_split_trajectory_leakage" in result["errors"]
    assert "cross_split_position_leakage" not in result["errors"]


def test_distinct_sources_and_trajectories_pass_structural_check_only():
    rows = [_row("train", "g1", "t1", "a", "b", "c"),
            _row("test", "g2", "t2", "d", "e", "f")]
    result = audit(rows, EXCLUSIONS)
    assert result["admissible_structurally"]
    assert result["historical_exclusion_proven"] is False


def test_shared_raw_and_trajectory_same_split_not_leakage():
    rows = [_row("train", "g1", "t1", "a", "b", "c"),
            _row("train", "g2", "t1", "a", "b", "d")]
    result = audit(rows, EXCLUSIONS)
    assert result["admissible_structurally"]
