"""Synthetic corpus-guard tests; no FMJD scores or held-out FENs."""
import pytest
from research.mtdp.decision_equivalence.corpus_guard import audit


def row(game="g1", event="historical", split="train", fen="W:W31:B20", ply=1):
    return dict(game_id=game, tournament_id="t1", event_id=event,
                split=split, fen=fen, ply=ply)


def test_deterministic_and_chronology_sensitive():
    a, b = row(), row(game="g2", event="other", split="test", fen="B:W31:B20")
    assert audit([a, b]) == audit([a, b])
    assert audit([a, b])["canonical_sha256"] != audit([b, a])["canonical_sha256"]


def test_reserved_event_rejected_whole():
    with pytest.raises(ValueError, match="reserved event"):
        audit([row(event="fFgE7oED")])


def test_game_split_leakage():
    with pytest.raises(ValueError, match="game crosses"):
        audit([row(), row(split="test", ply=2, fen="B:W31:B20")])


def test_fen_split_leakage():
    with pytest.raises(ValueError, match="FEN crosses"):
        audit([row(), row(game="g2", event="other", split="test")])


def test_duplicate_and_provenance():
    with pytest.raises(ValueError, match="duplicate"):
        audit([row(), row()])
    with pytest.raises(ValueError, match="provenance"):
        audit([row(), row(event="other", ply=2, fen="B:W31:B20")])


def test_invalid_input():
    for bad in ([], [row(ply=True)], [row(split="validation")], [row(fen="")]):
        with pytest.raises(ValueError):
            audit(bad)


def test_event_level_split_leakage_across_distinct_games():
    with pytest.raises(ValueError, match="event crosses splits"):
        audit([row(game="g1", split="train"),
               row(game="g2", split="test", fen="B:W31:B20")])


def test_within_game_ply_must_increase_even_if_interleaved():
    with pytest.raises(ValueError, match="nonchronological"):
        audit([row(game="g1", ply=3), row(game="g2", ply=1, fen="B:W31:B20"),
               row(game="g1", ply=2, fen="W:W32:B20")])
    assert audit([row(game="g1", ply=1), row(game="g2", ply=1, fen="B:W31:B20"),
                  row(game="g1", ply=3, fen="W:W32:B20")])["rows"] == 3
