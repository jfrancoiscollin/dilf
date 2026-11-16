"""Synthetic safety tests for the D1 FMJD score-blind exporter."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from pedagogy.game import initial_state
from research.mtdp.decision_equivalence.fmjd_export import (
    export_records, position_record,
)
from research.mtdp.pdn import PdnGame


class FakeEngine:
    def __init__(self, duplicate=False):
        self.duplicate = duplicate

    def legal_moves(self, state):
        m = SimpleNamespace(path=(31, 26), captures=(), promotion=False)
        return [m, m] if self.duplicate else [m]


def test_exact_and_quiet_signature_are_score_blind():
    state = initial_state()
    row = position_record(state, "fixture", FakeEngine())
    assert set(row["signatures"]) == {"E", "L", "Q"}
    assert row["signatures"]["Q"][0] == "quiet-v1"
    assert row["game_id"] == "fixture"
    assert len(row["actions"]) == 1
    assert "score" not in str(row).lower()


def test_duplicate_action_identity_fails_closed():
    with pytest.raises(ValueError, match="ambiguous/duplicate"):
        position_record(initial_state(), "fixture", FakeEngine(duplicate=True))


def test_bad_game_yields_no_partial_records(monkeypatch):
    def fail_after_initial(game, engine):
        raise ValueError("invalid full trajectory")
    monkeypatch.setattr(
        "research.mtdp.decision_equivalence.fmjd_export.validated_trajectory",
        fail_after_initial,
    )
    with pytest.raises(ValueError, match="invalid full trajectory"):
        export_records([PdnGame(1, {}, ("32-28",))], FakeEngine())
