"""Tests for :class:`pedagogy.motifs.envoi_a_dame.EnvoiADameDetector`."""

from __future__ import annotations

from pedagogy.game import Move, state_from_pieces
from pedagogy.motifs.envoi_a_dame import (
    ENVOI_PROMO_PLY_LIMIT,
    EnvoiADameDetector,
    _last_square_of_notation,
)


def _white_sacrifice() -> tuple:
    """Return ``(state_before, state_after, move)`` where white sacrifices one."""
    state_before = state_from_pieces(
        white_men=[31, 32, 33, 7], black_men=[1, 2], turn="white"
    )
    state_after = state_from_pieces(
        white_men=[31, 33, 7], black_men=[1, 2], turn="black"
    )
    move = Move(path=(32, 28))  # doesn't land on promo row.
    return state_before, state_after, move


def test_landing_square_helper_handles_quiet_and_capture() -> None:
    assert _last_square_of_notation("32-28") == 28
    assert _last_square_of_notation("40x29x18") == 18
    assert _last_square_of_notation("") is None
    assert _last_square_of_notation("garbage") is None


def test_ply_limit_value_matches_spec() -> None:
    assert ENVOI_PROMO_PLY_LIMIT == 2


def test_detector_name() -> None:
    assert EnvoiADameDetector().name == "envoi_a_dame"


def test_detect_returns_none_without_material_loss() -> None:
    state_before = state_from_pieces(white_men=[7], black_men=[1], turn="white")
    state_after = state_from_pieces(white_men=[3], black_men=[1], turn="black")
    move = Move(path=(7, 3))
    det = EnvoiADameDetector()
    pv = ["1-6", "7-3"]
    assert det.detect(state_before, move, state_after, pv=pv, scan_score_after=0.5) is None


def test_detect_returns_none_when_move_itself_lands_on_promo() -> None:
    # White moves directly to row 1 -> this is a plain promotion, not envoi à dame.
    sb = state_from_pieces(white_men=[7, 32], black_men=[1], turn="white")
    sa = state_from_pieces(white_men=[32], black_kings=[3], turn="black")
    # state_after has fewer white men (sacrifice via opp recapture mocked).
    move = Move(path=(7, 3))
    det = EnvoiADameDetector()
    pv = ["1-6", "32-28"]
    assert det.detect(sb, move, sa, pv=pv, scan_score_after=0.4) is None


def test_detect_returns_none_when_pv_missing_promotion() -> None:
    sb, sa, m = _white_sacrifice()
    det = EnvoiADameDetector()
    pv = ["1-6", "33-29"]  # 29 is NOT a white promotion square.
    assert det.detect(sb, m, sa, pv=pv, scan_score_after=0.5) is None


def test_detect_returns_none_when_pv_empty() -> None:
    sb, sa, m = _white_sacrifice()
    det = EnvoiADameDetector()
    assert det.detect(sb, m, sa, pv=None, scan_score_after=0.5) is None


def test_detect_returns_none_when_score_collapses() -> None:
    sb, sa, m = _white_sacrifice()
    det = EnvoiADameDetector()
    pv = ["1-6", "7-3"]
    assert det.detect(sb, m, sa, pv=pv, scan_score_after=-0.5) is None


def test_detect_flags_white_envoi_a_dame() -> None:
    sb, sa, m = _white_sacrifice()
    det = EnvoiADameDetector()
    pv = ["1-6", "7-3"]  # pv[1] lands on 3 -> promotion square for white.
    match = det.detect(sb, m, sa, pv=pv, scan_score_after=0.5)
    assert match is not None
    assert match.motif == "envoi_a_dame"
    assert match.role == "played"
    assert match.metadata["promotion_square"] == 3
    assert match.metadata["material_loss"] == 1
    assert match.pv == ["1-6", "7-3"]
    # Promotion square appended at end of `squares` for highlighting.
    assert match.squares[-1] == 3


def test_detect_flags_black_envoi_a_dame_with_correct_promo_row() -> None:
    sb = state_from_pieces(white_men=[1], black_men=[20, 21, 44], turn="black")
    sa = state_from_pieces(white_men=[1], black_men=[20, 44], turn="white")
    move = Move(path=(21, 26))
    pv = ["1-7", "44-49"]  # 49 ∈ BLACK_PROMOTION_ROW.
    det = EnvoiADameDetector()
    match = det.detect(sb, move, sa, pv=pv, scan_score_after=-0.6)
    assert match is not None
    assert match.metadata["promotion_square"] == 49


def test_first_ply_promotion_in_pv_is_also_accepted() -> None:
    # If the promotion happens already in pv[0] (extremely rare but legal),
    # the detector should still flag it within ENVOI_PROMO_PLY_LIMIT.
    sb, sa, m = _white_sacrifice()
    det = EnvoiADameDetector()
    pv = ["7-3", "1-6"]
    match = det.detect(sb, m, sa, pv=pv, scan_score_after=0.5)
    assert match is not None
    assert match.metadata["promotion_square"] == 3
