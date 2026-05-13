"""Tests for ``pedagogy.verdicts.assembler.assemble_verdict`` (spec §6).

These tests use the in-process :class:`MockEngine` (see ``conftest.py``) to
expose just enough behaviour for the assembler to compute its features and
detect motifs. No real Scan is involved; scores are passed in directly.
"""

from __future__ import annotations

from typing import Sequence

import pytest

from pedagogy.game import GameState, Move
from pedagogy.tests.conftest import MockEngine
from pedagogy.types import Phase, Verdict
from pedagogy.verdicts.assembler import assemble_verdict


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------


def _open_state(turn: str = "white") -> GameState:
    """A neutral middlegame-shaped position with both sides in play.

    Used by tests that don't care about specific squares — only that the
    GameState is valid and the engine sees something.
    """
    return GameState(
        white_men=frozenset({31, 32, 33}),
        white_kings=frozenset(),
        black_men=frozenset({18, 19, 20}),
        black_kings=frozenset(),
        turn=turn,  # type: ignore[arg-type]
    )


def _quiet_move(state: GameState) -> Move:
    """A non-capture move from 32 to 28 (works for any state containing 32)."""
    return Move(path=(32, 28))


# ---------------------------------------------------------------------------
# assemble_verdict — basic shape
# ---------------------------------------------------------------------------


def test_assemble_verdict_returns_move_verdict_with_all_fields_populated() -> None:
    state_before = _open_state()
    state_after = GameState(
        white_men=frozenset({28, 31, 33}),
        white_kings=frozenset(),
        black_men=frozenset({18, 19, 20}),
        black_kings=frozenset(),
        turn="black",
    )
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.5, score_after=0.5,
        best_move=None, best_pv=None,
        half_move_number=13,
        is_book=False,
        engine=None,
    )

    assert mv.move_number == 13
    assert mv.side == "white"
    assert mv.move_notation == "32-28"
    assert mv.score_before == 0.5
    assert mv.score_after == 0.5
    assert mv.is_forced is False
    assert mv.fen_before.startswith("W:")
    assert mv.fen_after.startswith("B:")
    assert mv.features_before is not None
    assert mv.features_after is not None
    assert mv.phase in {Phase.OPENING, Phase.MIDDLEGAME, Phase.ENDGAME}


def test_assemble_verdict_uses_classifier_for_verdict_field() -> None:
    state_before = _open_state()
    state_after = state_before  # No real move, just checking classifier wiring.
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.5, score_after=0.5,
        half_move_number=15,
    )

    assert mv.verdict == Verdict.BEST  # delta_wc = 0 -> BEST


def test_assemble_verdict_computes_signed_delta_for_white() -> None:
    state_before = _open_state(turn="white")
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=1.0, score_after=0.0,
        half_move_number=15,
    )

    # White made the position worse for itself -> positive delta.
    assert mv.delta_winchance > 0.0


def test_assemble_verdict_computes_signed_delta_for_black() -> None:
    state_before = _open_state(turn="black")
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=-1.0, score_after=0.0,
        half_move_number=15,
    )

    # Black made the score swing from -1 (good for black) to 0 -> bad for
    # black -> positive delta_winchance for the moving side.
    assert mv.delta_winchance > 0.0


# ---------------------------------------------------------------------------
# assemble_verdict — is_forced detection via engine
# ---------------------------------------------------------------------------


def test_assemble_verdict_sets_is_forced_when_engine_reports_one_legal_move(
    mock_engine: MockEngine,
) -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)
    mock_engine.set_legal(state_before, [move])

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=-2.0,  # would be a blunder otherwise
        half_move_number=20,
        engine=mock_engine,
    )

    assert mv.is_forced is True
    assert mv.verdict == Verdict.FORCED


def test_assemble_verdict_is_not_forced_with_multiple_legal_moves(
    mock_engine: MockEngine,
) -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)
    other = Move(path=(31, 27))
    mock_engine.set_legal(state_before, [move, other])

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.5, score_after=0.5,
        half_move_number=15,
        engine=mock_engine,
    )

    assert mv.is_forced is False
    assert mv.verdict == Verdict.BEST


def test_assemble_verdict_defaults_is_forced_false_without_engine() -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=0.0,
        half_move_number=15,
        engine=None,
    )

    assert mv.is_forced is False


# ---------------------------------------------------------------------------
# assemble_verdict — book
# ---------------------------------------------------------------------------


def test_assemble_verdict_book_short_circuits_to_book_verdict() -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=10.0, score_after=-10.0,  # would be a blunder
        half_move_number=5,
        is_book=True,
    )

    assert mv.verdict == Verdict.BOOK


# ---------------------------------------------------------------------------
# assemble_verdict — phase determination
# ---------------------------------------------------------------------------


def test_assemble_verdict_marks_opening_for_early_half_moves() -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=0.0,
        half_move_number=6,
    )

    assert mv.phase == Phase.OPENING


def test_assemble_verdict_marks_endgame_for_low_material() -> None:
    # 6 pieces total, no kings: endgame by piece count.
    state_before = GameState(
        white_men=frozenset({31, 32, 33}),
        white_kings=frozenset(),
        black_men=frozenset({18, 19, 20}),
        black_kings=frozenset(),
        turn="white",
    )
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=0.0,
        half_move_number=40,
    )

    assert mv.phase == Phase.ENDGAME


# ---------------------------------------------------------------------------
# assemble_verdict — motif integration
# ---------------------------------------------------------------------------


def test_assemble_verdict_runs_detectors_and_collects_matches() -> None:
    # A capture move with too few captures to trigger any specific motif —
    # the field should still exist as an (empty) list, not None.
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=0.0,
        half_move_number=15,
    )

    assert isinstance(mv.motifs, list)


def test_assemble_verdict_runs_missed_pass_when_best_move_differs(
    mock_engine: MockEngine,
) -> None:
    state_before = _open_state()
    state_after = state_before
    played = _quiet_move(state_before)
    best = Move(path=(33, 29))

    mv = assemble_verdict(
        state_before, played, state_after,
        score_before=0.5, score_after=0.5,
        best_move=best,
        best_pv=["33-29"],
        half_move_number=15,
        engine=mock_engine,
    )

    # No detector will flag a missed motif on this synthetic position, but
    # the assembler must not crash and must keep the motif list well-formed.
    assert isinstance(mv.motifs, list)


def test_assemble_verdict_skips_missed_pass_when_played_equals_best() -> None:
    state_before = _open_state()
    state_after = state_before
    move = _quiet_move(state_before)

    mv = assemble_verdict(
        state_before, move, state_after,
        score_before=0.0, score_after=0.0,
        best_move=move,  # same path -> no missed pass
        best_pv=["32-28"],
        half_move_number=15,
    )

    assert isinstance(mv.motifs, list)
