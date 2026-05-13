"""Tests for :class:`pedagogy.motifs.sacrifices.SacrificeDetector`."""

from __future__ import annotations

import pytest

from pedagogy.game import Move, state_from_pieces
from pedagogy.motifs.sacrifices import SACRIFICE_FAILED_SCORE, SacrificeDetector


def _white_lost_one() -> tuple:
    """Return ``(state_before, state_after, move)`` where white loses one man."""
    state_before = state_from_pieces(
        white_men=[31, 32, 33], black_men=[1, 2], turn="white"
    )
    state_after = state_from_pieces(
        white_men=[31, 33], black_men=[1, 2], turn="black"
    )
    move = Move(path=(32, 28))
    return state_before, state_after, move


def test_detector_name() -> None:
    assert SacrificeDetector().name == "sacrifice"


def test_detect_returns_none_when_material_did_not_change() -> None:
    state_before = state_from_pieces(white_men=[31, 32], black_men=[1, 2], turn="white")
    state_after = state_from_pieces(white_men=[31, 28], black_men=[1, 2], turn="black")
    move = Move(path=(32, 28))
    det = SacrificeDetector()
    assert det.detect(state_before, move, state_after, scan_score_after=0.5) is None


def test_detect_returns_none_when_score_collapsed() -> None:
    sb, sa, m = _white_lost_one()
    det = SacrificeDetector()
    # White loses one but Scan score is too negative -> failed sacrifice.
    assert det.detect(sb, m, sa, scan_score_after=-0.5) is None


def test_detect_flags_simple_one_pawn_sacrifice() -> None:
    sb, sa, m = _white_lost_one()
    det = SacrificeDetector()
    match = det.detect(sb, m, sa, scan_score_after=0.5)
    assert match is not None
    assert match.motif == "sacrifice"
    assert match.role == "played"
    assert match.metadata["material_loss"] == 1
    assert match.metadata["score_after"] == 0.5
    assert match.severity == pytest.approx(1 / 3)


def test_severity_scales_with_loss_and_caps_at_one() -> None:
    sb = state_from_pieces(
        white_men=[31, 32, 33, 34, 35], black_men=[1, 2], turn="white"
    )
    sa = state_from_pieces(white_men=[31, 32], black_men=[1, 2], turn="black")
    move = Move(path=(33, 28))
    det = SacrificeDetector()
    match = det.detect(sb, move, sa, scan_score_after=0.4)
    assert match is not None
    # Lost 3 pawns -> severity = 3/3 = 1.0.
    assert match.metadata["material_loss"] == 3
    assert match.severity == 1.0


def test_detect_for_black_side_uses_correct_sign() -> None:
    # Black to move; black loses 1 man. Negative Scan score is favourable for black.
    sb = state_from_pieces(white_men=[1], black_men=[20, 21], turn="black")
    sa = state_from_pieces(white_men=[1], black_men=[20], turn="white")
    move = Move(path=(21, 26))
    det = SacrificeDetector()
    match = det.detect(sb, move, sa, scan_score_after=-0.6)
    assert match is not None
    assert match.metadata["material_loss"] == 1


def test_sacrifice_failed_score_threshold_value() -> None:
    assert SACRIFICE_FAILED_SCORE == pytest.approx(-0.3)


def test_pv_is_forwarded_in_motif_match() -> None:
    sb, sa, m = _white_lost_one()
    pv = ["1-7", "33-29"]
    det = SacrificeDetector()
    match = det.detect(sb, m, sa, pv=pv, scan_score_after=0.5)
    assert match is not None
    assert match.pv == pv


def test_default_detect_missed_returns_none() -> None:
    sb, _, _ = _white_lost_one()
    move = Move(path=(32, 28))
    det = SacrificeDetector()
    assert det.detect_missed(sb, move, [], move) is None
