"""Controlled counterexamples for exact legal-action collision analysis."""
from types import SimpleNamespace

import pytest

from research.mtdp import legal_collision_audit as audit
from research.mtdp.spatial_dynamics import _FIELDS


def state(fen, turn="white", legal=()):
    return SimpleNamespace(fen=fen, turn=turn, legal=frozenset(legal))


def install(monkeypatch, trajectories):
    def replay(game, engine):
        return [(i, "", position) for i, position in enumerate(trajectories[game.index])]
    def metrics(position):
        values = {field: 0 for field in _FIELDS}
        return SimpleNamespace(fen=position.fen, **values)
    monkeypatch.setattr(audit, "validated_trajectory", replay)
    monkeypatch.setattr(audit, "compute_spatial_metrics", metrics)
    monkeypatch.setattr(audit, "_legal_fingerprint", lambda engine, position: position.legal)


def game(index):
    return SimpleNamespace(index=index)


def test_same_turn_collision_detects_unequal_actions(monkeypatch):
    install(monkeypatch, {
        1: [state("A", legal={("31", "26")}), state("B", legal={("32", "27")})],
    })
    result = audit.audit_legal_collisions([game(1)], object())
    assert result["turn_conditioned_collision_pairs"] == 1
    assert result["different_legal_move_set_pairs"] == 1
    assert result["identical_legal_move_set_pairs"] == 0
    assert len(result["counterexamples"]) == 1
    assert result["counterexamples"][0]["moves_only_a"] == 1
    assert result["counterexamples"][0]["moves_only_b"] == 1
    assert result["counterexamples"][0]["shared_moves"] == 0


def test_opposite_turns_never_compared(monkeypatch):
    install(monkeypatch, {
        1: [state("A", "white", {("a",)}), state("B", "black", {("b",)})],
    })
    result = audit.audit_legal_collisions([game(1)], object())
    assert result["turn_conditioned_collision_pairs"] == 0


def test_duplicate_fen_deduplicated_across_games(monkeypatch):
    install(monkeypatch, {
        1: [state("A", legal={("a",)}), state("B", legal={("a",)})],
        2: [state("A", legal={("a",)})],
    })
    result = audit.audit_legal_collisions([game(1), game(2)], object())
    assert result["turn_conditioned_collision_pairs"] == 1
    assert result["identical_legal_move_set_pairs"] == 1
    assert result["cross_game_collision_pairs"] == 1
    assert result["different_legal_move_set_cross_game_pairs"] == 0


def test_same_fen_inconsistent_actions_fail_closed(monkeypatch):
    install(monkeypatch, {
        1: [state("A", legal={("a",)})],
        2: [state("A", legal={("b",)})],
    })
    with pytest.raises(AssertionError, match="inconsistent"):
        audit.audit_legal_collisions([game(1), game(2)], object())


def test_empty_corpus(monkeypatch):
    install(monkeypatch, {})
    result = audit.audit_legal_collisions([], object())
    assert result["games"] == 0
    assert result["turn_conditioned_collision_pairs"] == 0
