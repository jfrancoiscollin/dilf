"""Tests for the per-game narrator (J1 surface: headline,
phase_summary, motif counters, strengths skeleton, recommended_drills.
turning_points + persistent_weaknesses are stubbed on J1; tests for
those land alongside J2)."""

from __future__ import annotations

from typing import Any, Optional

import pytest

from pedagogy.profile import narrate_game
from pedagogy.types import (
    GameAnalysis,
    MotifMatch,
    MoveVerdict,
    Phase,
    Verdict,
)


# ── Fixture builders ────────────────────────────────────────────────────


def _verdict(
    *,
    move_number: int = 1,
    side: str = "white",
    verdict: Verdict = Verdict.GOOD,
    delta_winchance: float = 0.0,
    phase: Phase = Phase.MIDDLEGAME,
    motifs: Optional[list[MotifMatch]] = None,
    notation: str = "32-28",
) -> MoveVerdict:
    return MoveVerdict(
        move_number=move_number,
        side=side,
        move_notation=notation,
        fen_before="W:Wxxx:Bxxx",
        fen_after="B:Wxxx:Bxxx",
        score_before=0.0,
        score_after=0.0,
        delta_winchance=delta_winchance,
        verdict=verdict,
        is_forced=False,
        motifs=motifs or [],
        phase=phase,
    )


def _motif(slug: str, role: str = "played") -> MotifMatch:
    return MotifMatch(motif=slug, role=role, squares=[], pv=[], severity=0.5)


def _analysis(
    verdicts: list[MoveVerdict],
    *,
    user_side: Optional[str] = "white",
    result: Optional[str] = None,
) -> GameAnalysis:
    summary: dict[str, Any] = {}
    if result is not None:
        summary["result"] = result
    return GameAnalysis(
        game_id=1,
        user_id=1,
        user_side=user_side,
        opening_name=None,
        verdicts=verdicts,
        summary=summary,
    )


# ── Headline ────────────────────────────────────────────────────────────


def test_headline_includes_half_move_count_and_accuracy():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BEST, delta_winchance=0.0),
        _verdict(move_number=2, side="black", verdict=Verdict.GOOD, delta_winchance=0.02),
    ]))
    assert "2 demi-coups" in out["headline"]
    assert "%" in out["headline"]


def test_headline_victory_for_user_white_on_1_0_result():
    out = narrate_game(_analysis(
        [_verdict(move_number=1, verdict=Verdict.BEST)],
        result="1-0",
        user_side="white",
    ))
    assert "Victoire" in out["headline"]
    assert "⬜" in out["headline"]


def test_headline_defeat_for_user_white_on_0_1_result():
    out = narrate_game(_analysis(
        [_verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.35)],
        result="0-1",
        user_side="white",
    ))
    assert "Défaite" in out["headline"]


def test_headline_draw():
    out = narrate_game(_analysis(
        [_verdict(verdict=Verdict.BEST)],
        result="1/2-1/2",
    ))
    assert "Nulle" in out["headline"]


def test_headline_falls_back_when_no_result_in_summary():
    out = narrate_game(_analysis([_verdict()]))
    # No Victoire / Défaite / Nulle — just the count + accuracy line.
    assert "Victoire" not in out["headline"]
    assert "Défaite" not in out["headline"]
    assert "Nulle" not in out["headline"]


# ── Phase summary ───────────────────────────────────────────────────────


def test_phase_summary_skips_phases_without_verdicts():
    """Game that ended in the middlegame — no endgame row should appear."""
    out = narrate_game(_analysis([
        _verdict(move_number=1, phase=Phase.OPENING, delta_winchance=0.01),
        _verdict(move_number=2, phase=Phase.OPENING, side="black", delta_winchance=0.02),
        _verdict(move_number=3, phase=Phase.MIDDLEGAME, delta_winchance=0.10),
    ]))
    phases = [p["phase"] for p in out["phase_summary"]]
    assert phases == ["opening", "middlegame"]
    assert "endgame" not in phases


def test_phase_summary_orders_phases_canonically_regardless_of_input_order():
    out = narrate_game(_analysis([
        _verdict(move_number=1, phase=Phase.ENDGAME),
        _verdict(move_number=2, phase=Phase.OPENING),
        _verdict(move_number=3, phase=Phase.MIDDLEGAME),
    ]))
    phases = [p["phase"] for p in out["phase_summary"]]
    assert phases == ["opening", "middlegame", "endgame"]


def test_phase_summary_acpl_splits_user_vs_opponent():
    """User (white) plays cleanly; opponent (black) blunders. The
    per-phase ACPL must reflect that split."""
    out = narrate_game(_analysis([
        # White (user) all clean.
        _verdict(move_number=1, side="white", phase=Phase.OPENING, delta_winchance=0.0),
        _verdict(move_number=3, side="white", phase=Phase.OPENING, delta_winchance=0.0),
        # Black (opponent) bleeds.
        _verdict(move_number=2, side="black", phase=Phase.OPENING, delta_winchance=0.30),
        _verdict(move_number=4, side="black", phase=Phase.OPENING, delta_winchance=0.30),
    ], user_side="white"))
    op = out["phase_summary"][0]
    assert op["acpl_user"] == 0
    assert op["acpl_opponent"] == 30
    assert "ouverture" in op["summary"].lower()


def test_phase_summary_summary_string_includes_label_and_count():
    out = narrate_game(_analysis([
        _verdict(move_number=1, phase=Phase.MIDDLEGAME, delta_winchance=0.0),
        _verdict(move_number=2, side="black", phase=Phase.MIDDLEGAME, delta_winchance=0.0),
    ]))
    s = out["phase_summary"][0]["summary"]
    assert "milieu de jeu" in s.lower()
    assert "2 demi-coups" in s


# ── Motif counters ──────────────────────────────────────────────────────


def test_motif_counters_split_played_vs_missed():
    out = narrate_game(_analysis([
        _verdict(move_number=1, motifs=[_motif("coup_royal", "played"),
                                        _motif("sacrifice", "played")]),
        _verdict(move_number=2, side="black", motifs=[_motif("coup_royal", "missed")]),
        _verdict(move_number=3, motifs=[_motif("coup_turc", "threatened")]),  # ignored
    ]))
    assert out["motifs_played"] == {"coup_royal": 1, "sacrifice": 1}
    assert out["motifs_missed"] == {"coup_royal": 1}


def test_motif_counters_sorted_desc_then_alpha():
    out = narrate_game(_analysis([
        _verdict(move_number=1, motifs=[_motif("coup_turc", "played")]),
        _verdict(move_number=2, motifs=[_motif("coup_royal", "played")]),
        _verdict(move_number=3, motifs=[_motif("coup_royal", "played")]),
        _verdict(move_number=4, motifs=[_motif("sacrifice", "played")]),
    ]))
    # Count desc → coup_royal (2). Then ties sorted alpha → coup_turc, sacrifice.
    assert list(out["motifs_played"].keys()) == ["coup_royal", "coup_turc", "sacrifice"]


# ── Strengths ───────────────────────────────────────────────────────────


def test_strengths_lists_brilliant_count_when_any():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BRILLIANT),
        _verdict(move_number=3, verdict=Verdict.BRILLIANT),
        _verdict(move_number=5, verdict=Verdict.BEST),
    ]))
    joined = " ".join(out["strengths"])
    assert "2 coups brillants" in joined


def test_strengths_empty_for_clean_but_unremarkable_game():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BEST),
        _verdict(move_number=2, side="black", verdict=Verdict.BEST),
    ]))
    assert out["strengths"] == []


def test_strengths_mentions_offensive_motifs_played():
    out = narrate_game(_analysis([
        _verdict(move_number=1, motifs=[_motif("coup_royal", "played")]),
    ]))
    joined = " ".join(out["strengths"])
    assert "coup_royal" in joined or "motif" in joined.lower()


# ── Recommended drills ──────────────────────────────────────────────────


def test_recommended_drills_orders_by_missed_count_desc():
    out = narrate_game(_analysis([
        _verdict(move_number=1, motifs=[_motif("coup_turc", "missed")]),
        _verdict(move_number=2, motifs=[_motif("coup_royal", "missed")]),
        _verdict(move_number=3, motifs=[_motif("coup_royal", "missed")]),
    ]))
    assert out["recommended_drills"] == ["coup_royal", "coup_turc"]


def test_recommended_drills_empty_when_user_missed_nothing():
    out = narrate_game(_analysis([
        _verdict(move_number=1, motifs=[_motif("coup_royal", "played")]),
    ]))
    assert out["recommended_drills"] == []


# ── Stubs for J2 (turning_points + persistent_weaknesses) ───────────────


def test_turning_points_and_persistent_weaknesses_are_empty_on_j1():
    """Sanity: the J1 surface ships stubs for the two J2 fields. The
    contract is that they're always present in the output, never absent —
    consumers can rely on `out['turning_points']` existing."""
    out = narrate_game(_analysis([_verdict()]))
    assert "turning_points" in out
    assert "persistent_weaknesses" in out
    assert out["turning_points"] == []
    assert out["persistent_weaknesses"] == []
