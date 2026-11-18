"""Deterministic tests for the score-blind D1 split gate."""
import pytest
from research.mtdp.decision_equivalence.partition_guard import validate_partition


def rows():
    return [
        {"game_id": "g1", "position_id": "p1", "ply": 1, "split": "train"},
        {"game_id": "g1", "position_id": "p2", "ply": 3, "split": "train"},
        {"game_id": "g2", "position_id": "p3", "ply": 0, "split": "test"},
    ]


def test_valid_reproducible():
    a = validate_partition(rows())
    assert a == validate_partition(rows())
    assert (a["positions"], a["games"], a["train_games"], a["test_games"]) == (3, 2, 1, 1)
    assert len(a["sha256"]) == 64


@pytest.mark.parametrize("change", [
    lambda r: r[1].update(split="test"),
    lambda r: r[1].update(position_id="p1"),
    lambda r: r[1].update(ply=1),
    lambda r: r[1].update(ply=0),
    lambda r: r[0].update(score=0),
    lambda r: r[0].update(best_move="32-28"),
    lambda r: r[0].update(ply=True),
])
def test_rejects_invalid(change):
    r = rows()
    change(r)
    with pytest.raises(ValueError):
        validate_partition(r)


def test_reserved_game_and_position():
    with pytest.raises(ValueError):
        validate_partition(rows(), reserved_game_ids=["g2"])
    with pytest.raises(ValueError):
        validate_partition(rows(), reserved_position_ids=["p3"])


def test_empty_rejected():
    with pytest.raises(ValueError):
        validate_partition([])


@pytest.mark.parametrize("metadata", [
    {"Scan_Score": 12},
    {"nested": {"best_move": "32-28"}},
    {"arrays": [{"evaluation": 0}]},
    {"outer": [{"WDL": "win"}]},
])
def test_nested_and_case_varied_target_leakage_rejected(metadata):
    r = rows()
    r[0]["metadata"] = metadata
    with pytest.raises(ValueError):
        validate_partition(r)


def test_score_blind_metadata_is_allowed():
    r = rows()
    r[0]["metadata"] = {"source": {"tournament": "historical"}, "tags": ["quiet"]}
    assert validate_partition(r)["positions"] == 3
