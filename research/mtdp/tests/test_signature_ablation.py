"""Signature ablation invariants using controlled synthetic states."""
from types import SimpleNamespace

from research.mtdp import signature_ablation as ablation
from research.mtdp.spatial_dynamics import _FIELDS


def position(fen, white_men, legal_paths, turn="white", black_men=(20,)):
    return SimpleNamespace(
        fen=fen, turn=turn,
        white_men=frozenset(white_men), white_kings=frozenset(),
        black_men=frozenset(black_men), black_kings=frozenset(),
        legal=frozenset((path, (), False) for path in legal_paths),
    )


def test_piece_counts_resolve_some_coarse_collisions(monkeypatch):
    states = [
        position("A", {31}, {("31", "26")}),
        position("B", {31, 32}, {("32", "27")}),
        position("C", {33}, {("33", "28")}),
    ]
    def metrics(state):
        values = {field: 0 for field in _FIELDS}
        return SimpleNamespace(fen=state.fen, **values)
    monkeypatch.setattr(ablation, "compute_spatial_metrics", metrics)
    monkeypatch.setattr(ablation, "validated_trajectory", lambda game, engine: [
        (i, "", state) for i, state in enumerate(states)
    ])
    monkeypatch.setattr(ablation, "_legal_fingerprint", lambda engine, state: state.legal)
    report = ablation.audit_ablation([SimpleNamespace(index=1)], object())
    variants = report["variants"]
    assert report["observations"] == 3
    assert variants["coarse_turn"]["distinct_fen_pairs"] == 3
    assert variants["plus_piece_counts"]["distinct_fen_pairs"] == 1
    assert variants["exact_occupancy"]["distinct_fen_pairs"] == 0


def test_empty(monkeypatch):
    result = ablation.audit_ablation([], object())
    assert result["games"] == 0
    assert all(x["distinct_fen_pairs"] == 0 for x in result["variants"].values())


def test_quiet_key_detects_backward_capture_and_keeps_forward_blocker():
    assert ablation._quiet_man_key("white", frozenset({32}), frozenset({38})) is None
    assert ablation._quiet_man_key("black", frozenset({32}), frozenset({38, 43})) == (
        "black", frozenset({32}), frozenset({38})
    )


def test_quiet_key_counts_distinct_fens_and_cross_game_pairs(monkeypatch):
    moves = {(32, 27), (32, 28)}
    first = position("A", {32}, moves, black_men=(1,))
    second = position("B", {32}, moves, black_men=(5,))
    games = [
        SimpleNamespace(index=1, states=[first, second]),
        SimpleNamespace(index=2, states=[first]),
    ]
    monkeypatch.setattr(ablation, "compute_spatial_metrics", lambda state: SimpleNamespace(
        fen=state.fen, **dict.fromkeys(_FIELDS, 0)
    ))
    monkeypatch.setattr(ablation, "validated_trajectory", lambda game, engine: [
        (i, "", state) for i, state in enumerate(game.states)
    ])
    monkeypatch.setattr(ablation, "_legal_fingerprint", lambda engine, state: state.legal)

    report = ablation.audit_ablation(games, object())
    quiet = report["variants"]["quiet_man_geometry"]
    assert report["observations"] == 3
    assert report["distinct_fens"] == report["quiet_man_fens"] == 2
    assert quiet["distinct_fen_pairs"] == quiet["cross_game_collision_pairs"] == 1
    assert quiet["identical_legal_move_set_pairs"] == 1
