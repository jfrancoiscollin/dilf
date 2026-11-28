"""Regression checks for the score-blind D1 exclusion gate (synthetic data only)."""
import hashlib
import pytest

from research.mtdp.decision_equivalence.cohort_exclusion_gate import validate


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def candidate(game="new", fen="new-fen", ply=1):
    return {
        "game_id": game,
        "trajectory_sha256": digest(game),
        "fen_sha256": digest(fen),
        "source": "synthetic",
        "tournament": "synthetic-only",
        "ply": ply,
    }


@pytest.mark.parametrize("field", ["game_id", "trajectory_sha256", "fen_sha256"])
def test_forbidden_identity_rejected(field):
    row = candidate()
    with pytest.raises(ValueError, match="overlaps forbidden"):
        validate([row], [[{field: row[field]}]])


def test_missing_forbidden_registry_fails_closed():
    with pytest.raises(ValueError, match="forbidden registry"):
        validate([candidate()], [])


def test_repeated_fen_from_different_games_is_not_independent():
    with pytest.raises(ValueError, match="duplicate FEN"):
        validate([candidate("a", "same"), candidate("b", "same")], [[{"game_id": "old"}]])


def test_nonchronological_game_is_rejected():
    with pytest.raises(ValueError, match="nonchronological"):
        validate([candidate("a", "first", 2), candidate("a", "second", 1)], [[{"game_id": "old"}]])


def test_score_field_is_rejected():
    row = candidate()
    row["scan_score"] = 0
    with pytest.raises(ValueError, match="target-score"):
        validate([row], [[{"game_id": "old"}]])


def test_distinct_synthetic_candidate_passes():
    row = candidate()
    assert validate([row], [[{"game_id": "old"}]]) == [row]
