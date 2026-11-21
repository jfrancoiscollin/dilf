"""Side-to-move controls for MTDP coarse-signature collisions."""
import pytest

from research.mtdp.spatial_dynamics import _FIELDS
from research.mtdp.turn_control import turn_conditioned_audit


def row(fen, turn, game="g1", core=0):
    metrics = {field: 0 for field in _FIELDS}
    metrics.update(fen=fen, turn=turn, center_core_white=core)
    return {
        "source": "pcblues_game_pdn",
        "source_id": game,
        "metadata": {"king_detection_verified": True},
        "metrics": metrics,
    }


def test_opposite_turns_do_not_count_as_conditioned_collision():
    result = turn_conditioned_audit([
        row("W:W31:B20", "white"), row("B:W31:B20", "black")
    ])
    assert result["mixed_turn_coarse_signature_groups"] == 1
    assert result["turn_conditioned_collision_groups"] == 0
    assert result["turn_conditioned_signatures"] == 2


def test_same_turn_distinct_positions_collide():
    result = turn_conditioned_audit([
        row("W:W31:B20", "white"),
        row("W:W32:B20", "white"),
        row("W:W31:B20", "white", game="g2"),
    ])
    assert result["turn_conditioned_collision_groups"] == 1
    assert result["distinct_fens_in_turn_conditioned_collisions"] == 2


def test_different_signatures_do_not_collide():
    result = turn_conditioned_audit([
        row("W:W31:B20", "white", core=1),
        row("W:W32:B20", "white", core=2),
    ])
    assert result["turn_conditioned_collision_groups"] == 0


def test_invalid_turn_rejected():
    with pytest.raises(ValueError, match="Invalid side"):
        turn_conditioned_audit([row("X", "red")])


def test_empty_corpus():
    result = turn_conditioned_audit([])
    assert result["games"] == 0
    assert result["turn_conditioned_collision_groups"] == 0
