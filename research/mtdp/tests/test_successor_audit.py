"""Synthetic successor equivalence counterexamples, no FMJD dependency."""
from types import SimpleNamespace

from research.mtdp import successor_audit as audit


def state(fen, key, actions=("a",)):
    return SimpleNamespace(fen=fen, key=key, actions=actions)


class FakeEngine:
    def legal_moves(self, position):
        return [SimpleNamespace(path=(1, 2), captures=(), promotion=False, label=a)
                for a in position.actions]

    def apply_move(self, position, move):
        return state(position.fen + move.label, position.key + ("next",))


def install(monkeypatch, trajectories):
    monkeypatch.setattr(audit, "validated_trajectory",
                        lambda game, engine: [(i, "", s) for i, s in enumerate(trajectories)])
    monkeypatch.setattr(audit, "state_to_fen", lambda s: s.fen)
    monkeypatch.setattr(audit, "_quiet_signature", lambda s: s.key)


def test_different_successor_fens_are_reported(monkeypatch):
    install(monkeypatch, [state("A", ("quiet",)), state("B", ("quiet",))])
    report = audit.audit_successors([SimpleNamespace(index=1)], FakeEngine())
    assert report["distinct_fen_pairs"] == 1
    assert report["different_legal_action_pairs"] == 0
    assert report["different_successor_fen_pairs"] == 1
    assert report["different_successor_quiet_signature_pairs"] == 0


def test_distinct_keys_not_compared(monkeypatch):
    install(monkeypatch, [state("A", ("one",)), state("B", ("two",))])
    report = audit.audit_successors([SimpleNamespace(index=1)], FakeEngine())
    assert report["distinct_fen_pairs"] == 0


def test_empty():
    report = audit.audit_successors([], FakeEngine())
    assert report["observations"] == 0
    assert report["distinct_fen_pairs"] == 0
