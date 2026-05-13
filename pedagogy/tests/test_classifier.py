"""Tests for the verdict classifier (spec §6)."""

from __future__ import annotations

import math

import pytest

from pedagogy.types import MotifMatch, Verdict
from pedagogy.verdicts.classifier import classify_move, win_chance


# ---------------------------------------------------------------------------
# win_chance
# ---------------------------------------------------------------------------


def test_win_chance_returns_zero_at_zero_score() -> None:
    assert win_chance(0.0) == pytest.approx(0.0, abs=1e-9)


def test_win_chance_is_strictly_monotone() -> None:
    values = [win_chance(s) for s in (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)]
    assert values == sorted(values)


def test_win_chance_is_bounded_by_minus_one_plus_one() -> None:
    assert -1.0 < win_chance(-10.0) < win_chance(10.0) < 1.0


def test_win_chance_is_odd_function() -> None:
    for s in (0.25, 0.5, 1.0, 2.0):
        assert win_chance(s) == pytest.approx(-win_chance(-s), abs=1e-9)


def test_win_chance_slope_matches_frontend_constant() -> None:
    # The frontend sigmoid uses slope = 2.0. A +1.0 pawn score must give the
    # same win chance as 2 / (1 + e^-2) - 1.
    expected = 2.0 / (1.0 + math.exp(-2.0)) - 1.0
    assert win_chance(1.0) == pytest.approx(expected, abs=1e-9)


# ---------------------------------------------------------------------------
# classify_move — short-circuits
# ---------------------------------------------------------------------------


def test_classify_move_returns_book_when_is_book_true_regardless_of_scores() -> None:
    v = classify_move(
        score_before=10.0, score_after=-10.0,  # would be a blunder otherwise
        side="white",
        is_forced=False,
        is_book=True,
        motifs=[],
    )
    assert v == Verdict.BOOK


def test_classify_move_returns_forced_when_is_forced_true() -> None:
    v = classify_move(
        score_before=0.0, score_after=-2.0,
        side="white",
        is_forced=True,
        is_book=False,
        motifs=[],
    )
    assert v == Verdict.FORCED


def test_classify_move_book_takes_priority_over_forced() -> None:
    v = classify_move(
        score_before=0.0, score_after=0.0,
        side="white",
        is_forced=True,
        is_book=True,
        motifs=[],
    )
    assert v == Verdict.BOOK


# ---------------------------------------------------------------------------
# classify_move — delta bands
# ---------------------------------------------------------------------------


def _sacrifice_match() -> MotifMatch:
    return MotifMatch(
        motif="sacrifice", role="played",
        squares=[32, 27], pv=[], severity=0.5,
    )


def test_classify_move_best_when_score_unchanged() -> None:
    v = classify_move(
        score_before=0.5, score_after=0.5,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.BEST


def test_classify_move_excellent_for_tiny_loss() -> None:
    # delta_wc ~0.018 (well inside the 0.01-0.03 band).
    v = classify_move(
        score_before=0.20, score_after=0.18,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.EXCELLENT


def test_classify_move_good_for_modest_loss() -> None:
    # delta_wc ~0.046 (inside 0.03-0.075).
    v = classify_move(
        score_before=0.30, score_after=0.25,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.GOOD


def test_classify_move_inaccuracy_for_noticeable_loss() -> None:
    # delta_wc ~0.083 (inside 0.075-0.15).
    v = classify_move(
        score_before=0.5, score_after=0.4,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.INACCURACY


def test_classify_move_mistake_for_significant_loss() -> None:
    # delta_wc ~0.230 (inside 0.15-0.30).
    v = classify_move(
        score_before=0.4, score_after=0.15,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.MISTAKE


def test_classify_move_blunder_for_catastrophic_loss() -> None:
    # delta well above 0.30.
    v = classify_move(
        score_before=1.0, score_after=-2.0,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.BLUNDER


def test_classify_move_uses_sign_of_side_correctly() -> None:
    # For black, a positive Scan score is BAD. A move that takes the score
    # from -0.5 to -0.5 is BEST for black (no delta).
    v = classify_move(
        score_before=-0.5, score_after=-0.5,
        side="black",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.BEST


def test_classify_move_blunder_for_black_when_score_swings_positive() -> None:
    v = classify_move(
        score_before=-0.5, score_after=2.0,
        side="black",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.BLUNDER


# ---------------------------------------------------------------------------
# classify_move — brilliant gating
# ---------------------------------------------------------------------------


def test_classify_move_brilliant_when_played_sacrifice_keeps_winchance() -> None:
    v = classify_move(
        score_before=1.0, score_after=0.95,  # delta ~0.02
        side="white",
        is_forced=False, is_book=False,
        motifs=[_sacrifice_match()],
    )
    assert v == Verdict.BRILLIANT


def test_classify_move_not_brilliant_without_played_sacrifice_motif() -> None:
    # Same scores, but no sacrifice motif -> standard delta bucket.
    v = classify_move(
        score_before=1.0, score_after=0.95,
        side="white",
        is_forced=False, is_book=False,
        motifs=[],
    )
    assert v == Verdict.EXCELLENT


def test_classify_move_not_brilliant_when_sacrifice_loses_winchance() -> None:
    # Sacrifice motif is there, but the delta is above the brilliant threshold.
    v = classify_move(
        score_before=1.0, score_after=-0.5,  # huge swing
        side="white",
        is_forced=False, is_book=False,
        motifs=[_sacrifice_match()],
    )
    assert v == Verdict.BLUNDER


def test_classify_move_brilliant_requires_role_played_not_suffered() -> None:
    suffered = MotifMatch(
        motif="sacrifice", role="suffered",
        squares=[], pv=[], severity=0.5,
    )
    v = classify_move(
        score_before=1.0, score_after=0.99,
        side="white",
        is_forced=False, is_book=False,
        motifs=[suffered],
    )
    assert v == Verdict.BEST  # falls through to delta band, not brilliant


# ---------------------------------------------------------------------------
# classify_move — interaction with other motif types
# ---------------------------------------------------------------------------


def test_classify_move_ignores_non_sacrifice_motifs_for_brilliant_decision() -> None:
    coup_royal = MotifMatch(
        motif="coup_royal", role="played",
        squares=[40, 34, 24, 14, 3], pv=[], severity=0.8,
    )
    v = classify_move(
        score_before=2.0, score_after=2.0,
        side="white",
        is_forced=False, is_book=False,
        motifs=[coup_royal],
    )
    # Coup royal is not a sacrifice — brilliant gate does NOT apply, but the
    # delta is zero so we land in BEST.
    assert v == Verdict.BEST
