"""Synthetic checks of distinct-FEN and cross-game collision semantics."""
from research.mtdp.signature_collisions import collision_audit
from research.mtdp.spatial_dynamics import _FIELDS


def row(fen, game, core=0):
    metrics = {field: 0 for field in _FIELDS}
    metrics.update(fen=fen, center_core_white=core)
    return {
        "source": "pcblues_game_pdn", "source_id": game,
        "metadata": {"king_detection_verified": True},
        "metrics": metrics,
    }


def test_repeated_identical_fen_not_a_collision():
    report = collision_audit([row("A", "g1"), row("A", "g2")])
    assert report["distinct_fens"] == 1
    assert report["collision_groups"] == 0


def test_distinct_fens_same_signature_across_games():
    report = collision_audit([row("A", "g1"), row("B", "g2"), row("C", "g1", 1)])
    assert report["collision_groups"] == 1
    assert report["cross_game_collision_groups"] == 1
    assert report["cross_game_distinct_fen_pairs"] == 1
    assert report["same_game_distinct_fen_pairs"] == 0


def test_same_game_pair_and_cross_game_membership():
    report = collision_audit([row("A", "g1"), row("B", "g1"), row("A", "g2")])
    assert report["same_game_distinct_fen_pairs"] == 1
    assert report["cross_game_distinct_fen_pairs"] == 1


def test_empty():
    report = collision_audit([])
    assert report["collision_groups"] == 0
    assert report["games"] == 0
