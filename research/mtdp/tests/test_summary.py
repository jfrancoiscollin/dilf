"""Corpus audit invariants and duplicate detection."""
from __future__ import annotations

from pedagogy.game import initial_state
from research.mtdp.dataset import record
from research.mtdp.summary import summarize


def test_empty_audit() -> None:
    result = summarize([])
    assert result["observations"] == 0
    assert result["distinct_positions"] == 0
    assert result["mean_occupied_fraction"] is None


def test_duplicate_positions_and_king_verification() -> None:
    state = initial_state()
    a = record(state, source="test", source_id="a")
    b = record(state, source="test", source_id="b")
    result = summarize([a, b])
    assert result["observations"] == 2
    assert result["distinct_positions"] == 1
    assert result["duplicate_observations"] == 1
    assert result["king_detection_unverified_observations"] == 2
    assert result["material_balance_histogram"] == {"0": 2}
