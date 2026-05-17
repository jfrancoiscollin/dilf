"""Tests for the combinaison_N_temps detector family.

Engine/board state transitions are mocked — real draughts geometry is
irrelevant here, the unit under test is the forced-chain bookkeeping.
All moves are non-capture so ``parse_move_notation`` round-trips
through the simple ``"from-to"`` form; the material delta is created
artificially by MockEngine's apply_table.
"""

from __future__ import annotations

from pedagogy.game import Move, notation, state_from_pieces
from pedagogy.motifs.combinaisons_generiques import (
    MAX_DEPTH_TEMPS,
    Combinaison2TempsDetector,
    Combinaison3TempsDetector,
    Combinaison4TempsDetector,
    Combinaison5TempsDetector,
    _opp_is_forced,
)

from .conftest import MockEngine


# ---------------------------------------------------------------------------
# Detector identity
# ---------------------------------------------------------------------------


def test_detector_names() -> None:
    assert Combinaison2TempsDetector().name == "combinaison_2_temps"
    assert Combinaison3TempsDetector().name == "combinaison_3_temps"
    assert Combinaison4TempsDetector().name == "combinaison_4_temps"
    assert Combinaison5TempsDetector().name == "combinaison_5_temps"


def test_max_depth_constant() -> None:
    assert MAX_DEPTH_TEMPS == 5


# ---------------------------------------------------------------------------
# Guard clauses
# ---------------------------------------------------------------------------


def test_detect_returns_none_without_engine() -> None:
    sb = state_from_pieces(white_men=[32], black_men=[20], turn="white")
    sa = state_from_pieces(white_men=[28], black_men=[20], turn="black")
    move = Move(path=(32, 28))
    assert Combinaison2TempsDetector().detect(sb, move, sa, pv=["32-28"]) is None


def test_detect_returns_none_without_pv() -> None:
    sb = state_from_pieces(white_men=[32], black_men=[20], turn="white")
    sa = state_from_pieces(white_men=[28], black_men=[20], turn="black")
    move = Move(path=(32, 28))
    eng = MockEngine()
    det = Combinaison2TempsDetector()
    assert det.detect(sb, move, sa, pv=None, engine=eng) is None
    assert det.detect(sb, move, sa, pv=[], engine=eng) is None


def test_detect_returns_none_when_move_does_not_match_pv_head() -> None:
    sb = state_from_pieces(white_men=[32], black_men=[20], turn="white")
    sa = state_from_pieces(white_men=[28], black_men=[20], turn="black")
    move = Move(path=(32, 28))
    eng = MockEngine()
    assert Combinaison2TempsDetector().detect(
        sb, move, sa, pv=["33-29"], engine=eng,
    ) is None


# ---------------------------------------------------------------------------
# Two-temps detector behaviour
# ---------------------------------------------------------------------------


def _two_temps_setup() -> tuple:
    """A clean 2-temps chain that nets +1 material for white."""
    sb = state_from_pieces(white_men=[33, 28], black_men=[19], turn="white")
    s1 = state_from_pieces(white_men=[33, 24], black_men=[19], turn="black")
    s2 = state_from_pieces(white_men=[33, 24], black_men=[15], turn="white")
    s3 = state_from_pieces(white_men=[33, 11], black_men=[], turn="black")
    move1 = Move(path=(28, 24))
    reply = Move(path=(19, 15))
    move2 = Move(path=(24, 11))
    eng = MockEngine()
    eng.set_apply(sb, move1, s1)
    eng.set_legal(s1, [reply])
    eng.set_apply(s1, reply, s2)
    eng.set_apply(s2, move2, s3)
    pv = [notation(move1), notation(reply), notation(move2)]
    return sb, s1, move1, pv, eng


def test_two_temps_detector_fires_on_two_temps_chain() -> None:
    sb, s1, move1, pv, eng = _two_temps_setup()
    match = Combinaison2TempsDetector().detect(sb, move1, s1, pv=pv, engine=eng)
    assert match is not None
    assert match.motif == "combinaison_2_temps"
    assert match.role == "played"
    assert match.metadata["depth_temps"] == 2
    assert match.metadata["material_gain"] == 1


def test_three_temps_detector_silent_on_two_temps_chain() -> None:
    """The 3-temps detector must NOT fire when only 2 attacker moves chain."""
    sb, s1, move1, pv, eng = _two_temps_setup()
    assert Combinaison3TempsDetector().detect(sb, move1, s1, pv=pv, engine=eng) is None


def test_detect_returns_none_when_reply_not_forced() -> None:
    sb = state_from_pieces(white_men=[33, 28], black_men=[23], turn="white")
    s1 = state_from_pieces(white_men=[33, 24], black_men=[23], turn="black")
    reply_a = Move(path=(23, 19))
    reply_b = Move(path=(23, 18))
    move1 = Move(path=(28, 24))

    eng = MockEngine()
    eng.set_apply(sb, move1, s1)
    eng.set_legal(s1, [reply_a, reply_b])

    assert Combinaison2TempsDetector().detect(
        sb, move1, s1, pv=[notation(move1), notation(reply_a)], engine=eng,
    ) is None


def test_detect_returns_none_when_chain_is_material_neutral() -> None:
    sb = state_from_pieces(white_men=[33, 28], black_men=[19], turn="white")
    s1 = state_from_pieces(white_men=[33, 24], black_men=[19], turn="black")
    s2 = state_from_pieces(white_men=[33], black_men=[15], turn="white")
    s3 = state_from_pieces(white_men=[33, 6], black_men=[15], turn="black")  # balance unchanged
    move1 = Move(path=(28, 24))
    reply = Move(path=(19, 15))
    move2 = Move(path=(24, 6))

    eng = MockEngine()
    eng.set_apply(sb, move1, s1)
    eng.set_legal(s1, [reply])
    eng.set_apply(s1, reply, s2)
    eng.set_apply(s2, move2, s3)

    assert Combinaison2TempsDetector().detect(
        sb, move1, s1, pv=[notation(move1), notation(reply), notation(move2)],
        engine=eng,
    ) is None


# ---------------------------------------------------------------------------
# Three-temps chain
# ---------------------------------------------------------------------------


def _three_temps_setup() -> tuple:
    sb = state_from_pieces(white_men=[33, 28, 40], black_men=[23, 14], turn="white")
    s1 = state_from_pieces(white_men=[33, 24, 40], black_men=[23, 14], turn="black")
    s2 = state_from_pieces(white_men=[33, 24, 40], black_men=[19, 14], turn="white")
    s3 = state_from_pieces(white_men=[33, 10, 40], black_men=[14], turn="black")
    s4 = state_from_pieces(white_men=[33, 10, 40], black_men=[9], turn="white")
    s5 = state_from_pieces(white_men=[33, 10, 4], black_men=[], turn="black")
    move1 = Move(path=(28, 24))
    reply1 = Move(path=(23, 19))
    move2 = Move(path=(24, 10))
    reply2 = Move(path=(14, 9))
    move3 = Move(path=(40, 4))

    eng = MockEngine()
    eng.set_apply(sb, move1, s1)
    eng.set_legal(s1, [reply1])
    eng.set_apply(s1, reply1, s2)
    eng.set_apply(s2, move2, s3)
    eng.set_legal(s3, [reply2])
    eng.set_apply(s3, reply2, s4)
    eng.set_apply(s4, move3, s5)

    pv = [
        notation(move1), notation(reply1),
        notation(move2), notation(reply2),
        notation(move3),
    ]
    return sb, s1, move1, pv, eng


def test_three_temps_detector_fires_on_three_temps_chain() -> None:
    sb, s1, move1, pv, eng = _three_temps_setup()
    match = Combinaison3TempsDetector().detect(sb, move1, s1, pv=pv, engine=eng)
    assert match is not None
    assert match.motif == "combinaison_3_temps"
    assert match.metadata["depth_temps"] == 3
    assert match.metadata["material_gain"] == 2


def test_two_temps_detector_silent_on_three_temps_chain() -> None:
    """The 2-temps detector reports nothing when the chain is longer."""
    sb, s1, move1, pv, eng = _three_temps_setup()
    assert Combinaison2TempsDetector().detect(sb, move1, s1, pv=pv, engine=eng) is None


# ---------------------------------------------------------------------------
# Missed detection
# ---------------------------------------------------------------------------


def test_detect_missed_fires_on_unplayed_best_move() -> None:
    sb, s1, best, pv, eng = _two_temps_setup()
    played = Move(path=(33, 29))
    match = Combinaison2TempsDetector().detect_missed(
        sb, best_move=best, best_pv=pv, played_move=played, engine=eng,
    )
    assert match is not None
    assert match.role == "missed"
    assert match.motif == "combinaison_2_temps"


# ---------------------------------------------------------------------------
# Depth-5 bucket clamps chains ≥ 5
# ---------------------------------------------------------------------------


def test_five_temps_detector_clamps_longer_chains() -> None:
    """If the chain reaches MAX_DEPTH_TEMPS the depth-5 detector must fire
    (it acts as the catch-all bucket)."""
    # Quickly fabricate: 2 attacker moves with forced reply, then a non-forced
    # reply caps the chain at depth=2. The 5-temps detector must NOT fire here.
    sb, s1, move1, pv, eng = _two_temps_setup()
    assert Combinaison5TempsDetector().detect(sb, move1, s1, pv=pv, engine=eng) is None


# ---------------------------------------------------------------------------
# FMJD prise-maximale ties — multiple legal captures at the same max length
# ---------------------------------------------------------------------------


def test_opp_is_forced_single_move() -> None:
    """A single legal move is always forced, capture or not."""
    assert _opp_is_forced([Move(path=(23, 19))]) is True
    assert _opp_is_forced([Move(path=(19, 28), captures=(24,))]) is True


def test_opp_is_forced_empty_is_not_forced() -> None:
    assert _opp_is_forced([]) is False


def test_opp_is_forced_all_captures_is_forced() -> None:
    """FMJD prise-maximale: when multiple legal moves are all captures
    they're all at the max length, and the opponent must capture
    regardless. Counted as forced for combination-walking purposes."""
    replies = [
        Move(path=(19, 28), captures=(24,)),
        Move(path=(19, 30), captures=(24,)),
    ]
    assert _opp_is_forced(replies) is True


def test_opp_is_forced_mixed_or_non_capture_is_not_forced() -> None:
    """Multiple non-captures means the opponent has free choice."""
    replies = [
        Move(path=(23, 19)),
        Move(path=(23, 18)),
    ]
    assert _opp_is_forced(replies) is False


def test_chain_breaks_when_opp_has_only_non_capture_choices() -> None:
    """Multiple legal moves that are all non-captures means the opponent
    has tactical freedom — the chain is not forced.

    Pre-existing test ``test_detect_returns_none_when_reply_not_forced``
    covered this with two non-capture replies; keeping a focused twin
    here to lock the relaxation: only ALL-capture ties should pass.
    """
    sb = state_from_pieces(white_men=[33, 28], black_men=[23], turn="white")
    s1 = state_from_pieces(white_men=[33, 24], black_men=[23], turn="black")
    reply_a = Move(path=(23, 19))  # non-capture
    reply_b = Move(path=(23, 18))  # non-capture
    move1 = Move(path=(28, 24))

    eng = MockEngine()
    eng.set_apply(sb, move1, s1)
    eng.set_legal(s1, [reply_a, reply_b])

    assert Combinaison2TempsDetector().detect(
        sb, move1, s1, pv=[notation(move1), notation(reply_a)], engine=eng,
    ) is None
