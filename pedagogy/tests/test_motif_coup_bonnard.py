"""Tests for :class:`pedagogy.motifs.coup_bonnard.CoupBonnardDetector`."""

from __future__ import annotations

from pedagogy.game import GameState, Move
from pedagogy.motifs.coup_bonnard import CoupBonnardDetector


def _state(*, white_men: set[int], black_men: set[int], turn: str = "white") -> GameState:
    return GameState(
        white_men=frozenset(white_men),
        white_kings=frozenset(),
        black_men=frozenset(black_men),
        black_kings=frozenset(),
        turn=turn,  # type: ignore[arg-type]
    )


def test_detector_name() -> None:
    assert CoupBonnardDetector().name == "coup_bonnard"


def test_detect_returns_none_without_pv() -> None:
    det = CoupBonnardDetector()
    state = _state(white_men={32}, black_men={18})
    move = Move(path=(32, 28))
    assert det.detect(state, move, state, pv=None) is None


def test_detect_returns_none_when_pv_is_too_short() -> None:
    det = CoupBonnardDetector()
    state = _state(white_men={32}, black_men={18})
    move = Move(path=(32, 28))
    # Need at least 3 entries: us / opponent / us.
    assert det.detect(state, move, state, pv=["32-28", "18-22"]) is None


def test_detect_returns_none_when_no_material_lost() -> None:
    det = CoupBonnardDetector()
    state_before = _state(white_men={32, 33}, black_men={18, 19})
    # state_after identical -> no material loss.
    pv = ["32-28", "19-46", "47x46"]
    assert det.detect(state_before, Move(path=(32, 28)), state_before, pv=pv) is None


def test_detect_returns_none_when_opponent_does_not_promote() -> None:
    det = CoupBonnardDetector()
    state_before = _state(white_men={32, 33}, black_men={18, 19})
    # White loses a man (state_after has only {33}) but black's response
    # in pv[1] lands on 22, not on a promotion row.
    state_after = _state(white_men={33}, black_men={18, 19}, turn="black")
    move = Move(path=(32, 28))
    pv = ["32-28", "18-22", "33-29"]
    assert det.detect(state_before, move, state_after, pv=pv) is None


def test_detect_flags_full_bonnard_setup_for_white() -> None:
    det = CoupBonnardDetector()
    state_before = _state(white_men={32, 47}, black_men={19})
    # White sacrifices a man: after-state has only one white piece.
    state_after = _state(white_men={47}, black_men={19}, turn="black")
    move = Move(path=(32, 28))
    # pv[0] = our sacrifice; pv[1] = opponent lands on 46 (promotion row);
    # pv[2] = we capture on 46.
    pv = ["32-28", "19x46", "47x46"]
    match = det.detect(state_before, move, state_after, pv=pv)
    assert match is not None
    assert match.motif == "coup_bonnard"
    assert match.role == "played"
    assert match.metadata["side"] == "white"


def test_detect_flags_full_bonnard_setup_for_black() -> None:
    det = CoupBonnardDetector()
    state_before = _state(white_men={32}, black_men={19, 4}, turn="black")
    state_after = _state(white_men={32}, black_men={4}, turn="white")
    move = Move(path=(19, 23))
    pv = ["19-23", "32x5", "4x5"]
    match = det.detect(state_before, move, state_after, pv=pv)
    assert match is not None
    assert match.metadata["side"] == "black"


def test_detect_missed_returns_none_without_engine() -> None:
    det = CoupBonnardDetector()
    state = _state(white_men={32}, black_men={18})
    played = Move(path=(32, 28))
    best = Move(path=(32, 27))
    assert det.detect_missed(state, best, ["32-27"], played, engine=None) is None


def test_detect_missed_returns_none_when_played_equals_best() -> None:
    det = CoupBonnardDetector()
    state = _state(white_men={32}, black_men={18})
    move = Move(path=(32, 28))
    assert det.detect_missed(state, move, ["32-28"], move) is None
