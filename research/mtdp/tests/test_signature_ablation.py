"""Signature ablation invariants using controlled synthetic states."""
from types import SimpleNamespace

from research.mtdp import signature_ablation as ablation
from research.mtdp.spatial_dynamics import _FIELDS


def position(fen, white_men, legal, turn="white"):
    return SimpleNamespace(
        fen=fen, turn=turn,
        white_men=frozenset(white_men), white_kings=frozenset(),
        black_men=frozenset({20}), black_kings=frozenset(),
        legal=frozenset(legal),
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
