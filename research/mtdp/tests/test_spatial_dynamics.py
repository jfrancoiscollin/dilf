"""Controlled tests for within-game spatial dynamics."""
import pytest

from research.mtdp.spatial_dynamics import analyze_dynamics


def row(game, ply, hash_, core=0, verified=True):
    return {
        "source": "pcblues_game_pdn", "source_id": game,
        "position_hash": hash_,
        "metadata": {"ply": ply, "king_detection_verified": verified},
        "metrics": {
            "center_core_white": core, "center_core_black": 0,
            "center_extended_white": 0, "center_extended_black": 0,
            "adjacency_edges_white": 0, "adjacency_edges_black": 0,
            "occupied_squares": 40, "material_balance": 0,
        },
    }


def test_game_boundaries_and_repetition():
    report = analyze_dynamics([
        row("g2", 1, "y", 2),
        row("g1", 2, "x", 1),
        row("g1", 0, "x", 0),
        row("g2", 0, "x", 1),
        row("g1", 1, "y", 1),
    ])
    assert report["games"] == 2
    assert report["transitions"] == 3
    assert report["revisited_exact_positions_within_games"] == 1
    assert report["descriptor_change_counts"]["center_core_white"] == 2
    assert report["unchanged_descriptors_transitions"] == 1


def test_empty_dataset():
    report = analyze_dynamics([])
    assert report["games"] == 0
    assert report["mean_absolute_ply_change"]["center_core_white"] is None


def test_missing_ply_rejected():
    with pytest.raises(ValueError, match="non-contiguous"):
        analyze_dynamics([row("g1", 0, "a"), row("g1", 2, "b")])


def test_unverified_kings_rejected():
    with pytest.raises(ValueError, match="king"):
        analyze_dynamics([row("g1", 0, "a", verified=False)])


def test_other_source_rejected():
    sample = row("g1", 0, "a")
    sample["source"] = "dubois_diagram_fixture"
    with pytest.raises(ValueError, match="Only validated"):
        analyze_dynamics([sample])
