"""Tests for :class:`pedagogy.motifs.coup_royal.CoupRoyalDetector`.

The detector reasons purely on the signature of the played (or best) move,
so test fixtures are synthetic ``Move`` objects defined in
``tests/fixtures/coup_royal.py``. We do not need a real game position.
"""

from __future__ import annotations

import pytest

from pedagogy.game import Move, empty_state
from pedagogy.motifs.coup_royal import (
    ROYAL_MIN_CAPTURES,
    ROYAL_MIN_CENTER_CAPTURES,
    ROYAL_MIN_ROWS,
    CoupRoyalDetector,
    _is_royal_signature,
)
from pedagogy.types import MotifMatch

from .fixtures import coup_royal as fx
from .fixtures.dubois_coup_royal import ALL_DUBOIS_COUP_ROYAL, DuboisCoupRoyalCase


@pytest.fixture
def detector() -> CoupRoyalDetector:
    return CoupRoyalDetector()


# ---------------------------------------------------------------------------
# Static signature predicate
# ---------------------------------------------------------------------------


def test_signature_thresholds_match_documented_constants() -> None:
    assert ROYAL_MIN_CAPTURES == 6
    assert ROYAL_MIN_CENTER_CAPTURES == 4
    assert ROYAL_MIN_ROWS == 4


@pytest.mark.parametrize(
    "fixture_name",
    [
        "ROYAL_CLASSIC_SIX_PROMO",
        "ROYAL_SEVEN_PROMO",
        "ROYAL_EIGHT_PROMO",
        "ROYAL_TEN_PROMO",
        "ROYAL_TWELVE_PROMO",
        "ROYAL_SIX_VIA_MAIN_DIAGONAL",
        "ROYAL_BLACK_SIX_PROMO",
    ],
)
def test_positive_fixtures_satisfy_signature(fixture_name: str) -> None:
    move: Move = getattr(fx, fixture_name)
    assert _is_royal_signature(move) is True


@pytest.mark.parametrize(
    "fixture_name",
    [
        "NOT_ROYAL_QUIET",
        "NOT_ROYAL_SINGLE_CAPTURE",
        "NOT_ROYAL_FIVE_CAPTURES",
        "NOT_ROYAL_FEW_CENTER",
        "NOT_ROYAL_THREE_ROWS",
        "NOT_ROYAL_NO_PROMO_NO_DIAG",
    ],
)
def test_negative_fixtures_fail_signature(fixture_name: str) -> None:
    move: Move = getattr(fx, fixture_name)
    assert _is_royal_signature(move) is False


# ---------------------------------------------------------------------------
# detect()
# ---------------------------------------------------------------------------


def test_detector_name(detector: CoupRoyalDetector) -> None:
    assert detector.name == "coup_royal"


def test_detect_returns_motif_match_on_classic_six(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    match = detector.detect(state, fx.ROYAL_CLASSIC_SIX_PROMO, state)
    assert match is not None
    assert isinstance(match, MotifMatch)
    assert match.motif == "coup_royal"
    assert match.role == "played"


def test_detect_returns_none_for_quiet_move(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    assert detector.detect(state, fx.NOT_ROYAL_QUIET, state) is None


def test_detect_returns_none_for_five_captures(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    assert detector.detect(state, fx.NOT_ROYAL_FIVE_CAPTURES, state) is None


def test_detect_returns_none_when_center_majority_missing(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    assert detector.detect(state, fx.NOT_ROYAL_FEW_CENTER, state) is None


def test_detect_returns_none_when_only_three_rows(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    assert detector.detect(state, fx.NOT_ROYAL_THREE_ROWS, state) is None


def test_detect_returns_none_when_no_promo_and_no_main_diag(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    assert detector.detect(state, fx.NOT_ROYAL_NO_PROMO_NO_DIAG, state) is None


def test_detect_accepts_path_through_main_diagonal_only(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    match = detector.detect(state, fx.ROYAL_SIX_VIA_MAIN_DIAGONAL, state)
    assert match is not None
    assert match.motif == "coup_royal"


def test_detect_for_black_side_mirror(detector: CoupRoyalDetector) -> None:
    state = empty_state(turn="black")
    match = detector.detect(state, fx.ROYAL_BLACK_SIX_PROMO, state)
    assert match is not None
    assert match.role == "played"


# ---------------------------------------------------------------------------
# Severity, metadata, squares, pv
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fixture_name", "expected_severity"),
    [
        ("ROYAL_CLASSIC_SIX_PROMO", 0.6),
        ("ROYAL_SEVEN_PROMO", 0.7),
        ("ROYAL_EIGHT_PROMO", 0.8),
        ("ROYAL_TEN_PROMO", 1.0),
        ("ROYAL_TWELVE_PROMO", 1.0),  # capped
    ],
)
def test_severity_scales_linearly_then_caps(
    detector: CoupRoyalDetector, fixture_name: str, expected_severity: float
) -> None:
    move: Move = getattr(fx, fixture_name)
    match = detector.detect(empty_state(), move, empty_state())
    assert match is not None
    assert match.severity == pytest.approx(expected_severity)


def test_metadata_contains_captures_count(detector: CoupRoyalDetector) -> None:
    match = detector.detect(empty_state(), fx.ROYAL_SEVEN_PROMO, empty_state())
    assert match is not None
    assert match.metadata == {"captures_count": 7}


def test_squares_combine_path_and_captures_unique(detector: CoupRoyalDetector) -> None:
    move = fx.ROYAL_CLASSIC_SIX_PROMO
    match = detector.detect(empty_state(), move, empty_state())
    assert match is not None
    expected = list(dict.fromkeys((*move.path, *move.captures)))
    assert match.squares == expected
    assert len(match.squares) == len(set(match.squares))  # no duplicates


def test_pv_contains_move_notation(detector: CoupRoyalDetector) -> None:
    match = detector.detect(empty_state(), fx.ROYAL_CLASSIC_SIX_PROMO, empty_state())
    assert match is not None
    # 6 captures -> "x"-separated notation.
    assert match.pv == ["40x29x23x18x12x7x3"]


# ---------------------------------------------------------------------------
# detect_missed()
# ---------------------------------------------------------------------------


def test_detect_missed_when_best_is_royal_and_played_is_quiet(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    match = detector.detect_missed(
        state, fx.ROYAL_CLASSIC_SIX_PROMO, [], fx.NOT_ROYAL_QUIET
    )
    assert match is not None
    assert match.role == "missed"
    assert match.severity == 1.0  # always max for missed
    assert match.metadata == {"captures_count": 6}


def test_detect_missed_returns_none_when_player_executed_the_motif(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    royal = fx.ROYAL_CLASSIC_SIX_PROMO
    assert detector.detect_missed(state, royal, [], royal) is None


def test_detect_missed_returns_none_when_best_is_not_royal(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    assert (
        detector.detect_missed(
            state, fx.NOT_ROYAL_FIVE_CAPTURES, [], fx.NOT_ROYAL_QUIET
        )
        is None
    )


def test_detect_missed_returns_none_when_best_fails_signature(
    detector: CoupRoyalDetector,
) -> None:
    state = empty_state()
    assert (
        detector.detect_missed(
            state, fx.NOT_ROYAL_NO_PROMO_NO_DIAG, [], fx.NOT_ROYAL_QUIET
        )
        is None
    )


def test_detect_missed_pv_uses_best_move_notation(detector: CoupRoyalDetector) -> None:
    state = empty_state()
    match = detector.detect_missed(
        state, fx.ROYAL_BLACK_SIX_PROMO, [], fx.NOT_ROYAL_QUIET
    )
    assert match is not None
    assert match.pv == ["12x17x23x28x33x39x49"]


# ---------------------------------------------------------------------------
# Real Dubois references (jpdubois_perfectionnement_combinaisons_V4.pdf)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case",
    ALL_DUBOIS_COUP_ROYAL,
    ids=lambda c: c.diagram + ":" + c.game_attribution[:30],
)
def test_dubois_case_is_detected_as_coup_royal(
    detector: CoupRoyalDetector, case: DuboisCoupRoyalCase
) -> None:
    match = detector.detect(empty_state(), case.final_move, empty_state())
    assert match is not None, f"Detector missed {case.name}"
    assert match.motif == "coup_royal"
    assert match.role == "played"
    assert match.metadata["captures_count"] >= case.expected_captures_min


@pytest.mark.parametrize("case", ALL_DUBOIS_COUP_ROYAL, ids=lambda c: c.diagram)
def test_dubois_case_book_reference_is_well_formed(case: DuboisCoupRoyalCase) -> None:
    ref = case.book_reference
    # Citation must contain the source PDF, chapter, diagram and page.
    assert case.book in ref
    assert f"ch. {case.chapter}" in ref
    assert case.diagram in ref
    assert f"p. {case.page}" in ref


def test_at_least_four_real_dubois_cases_loaded() -> None:
    # Sanity check: we explicitly catalogued D4, D11 and the two D12 traps.
    diagrams = {c.diagram for c in ALL_DUBOIS_COUP_ROYAL}
    assert {"D4", "D11", "D12"} <= diagrams
    assert len(ALL_DUBOIS_COUP_ROYAL) >= 4
