import copy

import pytest

from research.mtdp.spatial_game_units import summarize


def report():
    return {
        "schema_version": "mtdp-spatial-dynamics-v1",
        "games": 2, "positions": 8, "transitions": 6,
        "unchanged_descriptors_transitions": 2,
        "revisited_exact_positions_within_games": 1,
        "per_game": [
            {"game_id": "a", "positions": 3, "transitions": 2,
             "unchanged_descriptors_transitions": 2, "revisited_exact_positions": 1},
            {"game_id": "b", "positions": 5, "transitions": 4,
             "unchanged_descriptors_transitions": 0, "revisited_exact_positions": 0},
        ],
    }


def test_game_weighting_not_ply_weighting():
    result = summarize(report())
    assert result["mean_game_unchanged_transition_fraction"] == 0.5
    assert result["median_game_unchanged_transition_fraction"] == 0.5
    assert result["games_with_revisited_positions"] == 1
    assert result["independent_games_verified"] is False


@pytest.mark.parametrize("field,value", [
    ("games", 3), ("positions", 7), ("transitions", 7),
    ("unchanged_descriptors_transitions", 1),
    ("revisited_exact_positions_within_games", 2),
])
def test_aggregate_mismatch(field, value):
    data = report()
    data[field] = value
    with pytest.raises(ValueError, match="inconsistent"):
        summarize(data)


def test_duplicate_game_and_bad_counts():
    data = report()
    data["per_game"][1]["game_id"] = "a"
    with pytest.raises(ValueError, match="duplicate"):
        summarize(data)
    data = report()
    data["per_game"][0]["unchanged_descriptors_transitions"] = 3
    with pytest.raises(ValueError, match="inconsistent"):
        summarize(data)
