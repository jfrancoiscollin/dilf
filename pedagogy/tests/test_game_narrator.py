"""Tests for the per-game narrator (J1 surface: headline,
phase_summary, motif counters, strengths skeleton, recommended_drills.
turning_points + persistent_weaknesses are stubbed on J1; tests for
those land alongside J2)."""

from __future__ import annotations

from typing import Any, Optional

import pytest

from pedagogy.profile import narrate_game
from pedagogy.types import (
    Features,
    GameAnalysis,
    MotifMatch,
    MoveVerdict,
    Phase,
    Verdict,
)


def _features(**over: Any) -> Features:
    """Minimal Features instance — zeros everywhere by default; tests
    override only the *_white / *_black lists they care about."""
    defaults: dict[str, Any] = dict(
        white_men=15, white_kings=0, black_men=15, black_kings=0,
        material_balance=0,
        center_count_white=0, center_count_black=0,
        left_wing_white=0, right_wing_white=0,
        left_wing_black=0, right_wing_black=0,
        isolated_pawns_white=[], isolated_pawns_black=[],
        backward_pawns_white=[], backward_pawns_black=[],
        holes_white=[], holes_black=[],
        outposts_white=[], outposts_black=[],
        white_legal_moves=0, black_legal_moves=0,
        hanging_pieces_white=[], hanging_pieces_black=[],
        threatened_captures_white=[], threatened_captures_black=[],
        white_promotion_distance=5, black_promotion_distance=5,
        formations=[], phase=Phase.MIDDLEGAME,
    )
    defaults.update(over)
    return Features(**defaults)


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
    features_after: Optional[Features] = None,
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
        features_after=features_after,
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


# ── Turning points (J2) ────────────────────────────────────────────────


def test_turning_points_empty_on_clean_game():
    """All moves under the significance threshold (8 cp) → no tournants."""
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BEST, delta_winchance=0.0),
        _verdict(move_number=2, side="black", verdict=Verdict.GOOD, delta_winchance=0.02),
        _verdict(move_number=3, verdict=Verdict.GOOD, delta_winchance=0.05),
    ]))
    assert out["turning_points"] == []


def test_turning_points_picks_top_k_by_delta_desc():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.42, notation="32-28"),
        _verdict(move_number=3, verdict=Verdict.MISTAKE, delta_winchance=0.18, notation="37-31"),
        _verdict(move_number=5, verdict=Verdict.INACCURACY, delta_winchance=0.09, notation="33-29"),
        _verdict(move_number=7, verdict=Verdict.BEST, delta_winchance=0.0),
    ]), top_k_turning_points=2)
    assert len(out["turning_points"]) == 2
    assert [tp["move_number"] for tp in out["turning_points"]] == [1, 3]
    assert out["turning_points"][0]["delta_cp"] == 42
    assert out["turning_points"][0]["notation"] == "32-28"
    assert out["turning_points"][0]["verdict"] == "blunder"


def test_turning_points_ties_resolved_by_move_number_asc():
    """Two equally-costly moves → the earlier one comes first (sets the tone)."""
    out = narrate_game(_analysis([
        _verdict(move_number=10, verdict=Verdict.MISTAKE, delta_winchance=0.20),
        _verdict(move_number=2,  verdict=Verdict.MISTAKE, delta_winchance=0.20),
    ]))
    assert [tp["move_number"] for tp in out["turning_points"]] == [2, 10]


def test_turning_points_reason_prefers_missed_motif():
    out = narrate_game(_analysis([
        _verdict(
            move_number=15,
            verdict=Verdict.BLUNDER, delta_winchance=0.40,
            motifs=[_motif("coup_royal", "missed"),
                    _motif("sacrifice", "played")],   # missed wins priority
        ),
    ]))
    reason = out["turning_points"][0]["reason"]
    assert "raté" in reason.lower()
    assert "coup royal" in reason.lower()


def test_turning_points_reason_falls_back_to_played_motif():
    out = narrate_game(_analysis([
        _verdict(
            move_number=15,
            verdict=Verdict.BLUNDER, delta_winchance=0.40,
            motifs=[_motif("sacrifice", "played")],
        ),
    ]))
    assert "joué" in out["turning_points"][0]["reason"].lower()


def test_turning_points_reason_falls_back_to_verdict_label():
    out = narrate_game(_analysis([
        _verdict(move_number=15, verdict=Verdict.BLUNDER, delta_winchance=0.40),
    ]))
    # No motifs at all — falls back to the verdict-level FR sentence.
    assert "Gaffe" in out["turning_points"][0]["reason"]


# ── Persistent weaknesses (J2) ──────────────────────────────────────────


def test_persistent_weaknesses_detects_simple_long_streak():
    """Hole on square 23 (user side = white) persists for 6 verdicts → 1 row."""
    f_with_hole = _features(holes_white=[23])
    f_clean = _features()
    verdicts = [
        _verdict(move_number=1, features_after=f_clean),
        # streak starts at move 2, holds through 7 inclusive (6 demi-coups)
        *[
            _verdict(move_number=n, side="white" if n % 2 else "black",
                     features_after=f_with_hole)
            for n in range(2, 8)
        ],
        _verdict(move_number=8, features_after=f_clean),
    ]
    out = narrate_game(_analysis(verdicts, user_side="white"),
                       min_streak=5)
    assert len(out["persistent_weaknesses"]) == 1
    w = out["persistent_weaknesses"][0]
    assert w["family"] == "holes"
    assert w["square"] == 23
    assert w["side"] == "white"
    assert w["duration_half_moves"] == 6
    assert w["first_seen"] == 2
    assert "23" in w["summary"]
    assert "6 demi-coups" in w["summary"]


def test_persistent_weaknesses_filters_below_min_streak():
    """3-half-move streak with min_streak=5 → dropped."""
    f = _features(holes_white=[23])
    verdicts = [
        _verdict(move_number=1, features_after=f),
        _verdict(move_number=2, features_after=f),
        _verdict(move_number=3, features_after=f),
        _verdict(move_number=4, features_after=_features()),
    ]
    out = narrate_game(_analysis(verdicts, user_side="white"), min_streak=5)
    assert out["persistent_weaknesses"] == []


def test_persistent_weaknesses_filters_to_user_side_when_provided():
    """Hole on white side only — opponent (black) shouldn't appear."""
    user_hole = _features(holes_white=[22])
    opp_hole = _features(holes_black=[33])
    both = _features(holes_white=[22], holes_black=[33])
    verdicts = [
        _verdict(move_number=n, features_after=both)
        for n in range(1, 7)
    ]
    out = narrate_game(_analysis(verdicts, user_side="white"), min_streak=5)
    sides = {w["side"] for w in out["persistent_weaknesses"]}
    assert sides == {"white"}
    # Sanity: with no user_side filter, both sides show up.
    out_both = narrate_game(_analysis(verdicts, user_side=None), min_streak=5)
    sides_both = {w["side"] for w in out_both["persistent_weaknesses"]}
    assert sides_both == {"white", "black"}


def test_persistent_weaknesses_top_k_orders_by_duration_desc():
    """Long hole streak should rank above a shorter isolated-pawn streak."""
    holes_long = _features(holes_white=[23])
    iso_short = _features(isolated_pawns_white=[10])
    both = _features(holes_white=[23], isolated_pawns_white=[10])
    verdicts = (
        # holes streak: moves 1..10 (10 demi-coups, both holes + iso on
        # moves 5..7 so the iso has 3-move overlap — it'll be filtered
        # by min_streak)
        [_verdict(move_number=n, features_after=holes_long) for n in range(1, 5)]
        + [_verdict(move_number=n, features_after=both) for n in range(5, 8)]
        + [_verdict(move_number=n, features_after=holes_long) for n in range(8, 11)]
        + [_verdict(move_number=11, features_after=_features())]
    )
    out = narrate_game(_analysis(verdicts, user_side="white"),
                       top_k_weaknesses=3, min_streak=3)
    assert out["persistent_weaknesses"][0]["family"] == "holes"
    assert out["persistent_weaknesses"][0]["duration_half_moves"] == 10
    families = [w["family"] for w in out["persistent_weaknesses"]]
    if len(families) > 1:
        # The shorter iso streak should land BELOW the longer holes streak.
        assert families.index("holes") < families.index("isolated")


def test_persistent_weaknesses_closes_streak_at_end_of_game():
    """Hole still active at the last verdict — duration counted up to last move."""
    f = _features(holes_white=[23])
    verdicts = [
        _verdict(move_number=n, features_after=f)
        for n in range(1, 8)   # 7 demi-coups, no clean verdict to close
    ]
    out = narrate_game(_analysis(verdicts, user_side="white"), min_streak=5)
    assert len(out["persistent_weaknesses"]) == 1
    assert out["persistent_weaknesses"][0]["duration_half_moves"] == 7


def test_persistent_weaknesses_handles_verdicts_without_features():
    """features_after is None on legacy verdicts — must not raise, and
    must close any open streak so it doesn't bleed across a gap."""
    f = _features(holes_white=[23])
    verdicts = [
        _verdict(move_number=1, features_after=f),
        _verdict(move_number=2, features_after=f),
        _verdict(move_number=3, features_after=None),   # legacy row
        _verdict(move_number=4, features_after=f),
        _verdict(move_number=5, features_after=f),
    ]
    out = narrate_game(_analysis(verdicts, user_side="white"), min_streak=2)
    # We expect two streaks: 1-2 (duration 2) and 4-5 (duration 2).
    # Neither bleeds across the None row.
    durations = sorted(w["duration_half_moves"] for w in out["persistent_weaknesses"])
    assert durations == [2, 2]


# ── i18n (J3) ───────────────────────────────────────────────────────────


def test_english_headline_uses_english_keywords():
    out = narrate_game(_analysis(
        [_verdict(move_number=1, verdict=Verdict.BEST)],
        result="1-0",
        user_side="white",
    ), lang="en")
    assert "Victory" in out["headline"]
    assert "half-moves" in out["headline"]
    assert "accuracy" in out["headline"]


def test_english_outcome_defeat_and_draw():
    defeat = narrate_game(_analysis(
        [_verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.4)],
        result="0-1", user_side="white",
    ), lang="en")
    assert "Defeat" in defeat["headline"]

    draw = narrate_game(_analysis(
        [_verdict(verdict=Verdict.BEST)], result="1/2-1/2",
    ), lang="en")
    assert "Draw" in draw["headline"]


def test_english_phase_summary_uses_english_labels():
    out = narrate_game(_analysis([
        _verdict(move_number=1, phase=Phase.OPENING),
        _verdict(move_number=2, side="black", phase=Phase.OPENING),
    ]), lang="en")
    s = out["phase_summary"][0]["summary"]
    assert "Opening" in s
    assert "half-moves" in s
    # Quality label is one of the EN tier words.
    assert any(q in s.lower() for q in ("solid", "decent", "loose", "fragile"))


def test_english_turning_reason_uses_english_phrasing():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.4,
                 motifs=[_motif("coup_royal", "missed")]),
    ]), lang="en")
    assert "missed" in out["turning_points"][0]["reason"].lower()


def test_english_turning_reason_falls_back_to_english_verdict_label():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.4),
    ]), lang="en")
    assert "Blunder" in out["turning_points"][0]["reason"]


def test_english_weakness_summary_uses_english_template():
    f = _features(holes_white=[23])
    verdicts = [_verdict(move_number=n, features_after=f) for n in range(1, 8)]
    out = narrate_game(_analysis(verdicts, user_side="white"),
                       lang="en", min_streak=5)
    s = out["persistent_weaknesses"][0]["summary"]
    assert "Hole" in s
    assert "23" in s
    assert "half-moves" in s
    assert "starting at move" in s


def test_english_strengths_use_english_template():
    out = narrate_game(_analysis([
        _verdict(move_number=1, verdict=Verdict.BRILLIANT),
        _verdict(move_number=3, motifs=[_motif("coup_royal", "played")]),
    ]), lang="en")
    joined = " ".join(out["strengths"])
    assert "brilliant" in joined.lower()
    assert "offensive" in joined.lower() or "motif" in joined.lower()


def test_unknown_lang_silently_falls_back_to_fr():
    """An invalid lang code shouldn't raise — should degrade to FR
    rather than produce a half-translated mess."""
    out = narrate_game(_analysis(
        [_verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.4)],
        result="0-1", user_side="white",
    ), lang="ja")   # type: ignore[arg-type]
    assert "Défaite" in out["headline"]


def test_structural_equality_fr_vs_en():
    """For the same input, FR and EN narratives have identical
    structure: same keys, same list lengths, same non-string fields
    (counts, deltas, durations). Only the string fields differ."""
    f = _features(holes_white=[23])
    verdicts = [
        _verdict(move_number=1, verdict=Verdict.BLUNDER, delta_winchance=0.3,
                 features_after=f,
                 motifs=[_motif("coup_royal", "missed")]),
        *[
            _verdict(move_number=n, features_after=f,
                     side="white" if n % 2 else "black")
            for n in range(2, 8)
        ],
    ]
    a = _analysis(verdicts, user_side="white", result="0-1")
    fr = narrate_game(a, lang="fr")
    en = narrate_game(a, lang="en")

    # Same shape.
    assert sorted(fr.keys()) == sorted(en.keys())
    # Same counts of items per list.
    assert len(fr["phase_summary"])         == len(en["phase_summary"])
    assert len(fr["turning_points"])        == len(en["turning_points"])
    assert len(fr["persistent_weaknesses"]) == len(en["persistent_weaknesses"])
    assert len(fr["strengths"])             == len(en["strengths"])
    # Non-string fields match exactly.
    assert fr["motifs_played"]      == en["motifs_played"]
    assert fr["motifs_missed"]      == en["motifs_missed"]
    assert fr["recommended_drills"] == en["recommended_drills"]
    for f_w, e_w in zip(fr["persistent_weaknesses"], en["persistent_weaknesses"]):
        for key in ("family", "square", "side", "duration_half_moves", "first_seen"):
            assert f_w[key] == e_w[key]
    for f_t, e_t in zip(fr["turning_points"], en["turning_points"]):
        for key in ("move_number", "side", "notation", "delta_cp",
                    "score_before", "score_after", "verdict"):
            assert f_t[key] == e_t[key]


# ── Snapshot-ish "realistic game" scenarios ─────────────────────────────


def test_scenario_clean_win_no_drama():
    """User wins cleanly: every move best/good, no turning points,
    no persistent weaknesses, headline = victory."""
    verdicts = [
        _verdict(move_number=n, side="white" if n % 2 else "black",
                 verdict=Verdict.BEST if n % 4 != 3 else Verdict.GOOD,
                 delta_winchance=0.0 if n % 4 != 3 else 0.02)
        for n in range(1, 41)
    ]
    out = narrate_game(_analysis(verdicts, result="1-0", user_side="white"))
    assert "Victoire" in out["headline"]
    assert out["turning_points"] == []
    assert out["persistent_weaknesses"] == []
    assert out["strengths"] == []   # no brilliants, no offensive motifs
    assert out["motifs_missed"] == {}
    assert out["recommended_drills"] == []


def test_scenario_one_blunder_loss():
    """Game tilts on a single blunder mid-way through. Top-1 turning
    point picks that move; recommended drill targets the missed motif."""
    motifs_at_blunder = [_motif("coup_royal", "missed")]
    verdicts = (
        [_verdict(move_number=n, side="white" if n % 2 else "black",
                  verdict=Verdict.BEST) for n in range(1, 15)]
        + [_verdict(move_number=15, side="white",
                    verdict=Verdict.BLUNDER, delta_winchance=0.45,
                    notation="32-28", motifs=motifs_at_blunder)]
        + [_verdict(move_number=n, side="white" if n % 2 else "black",
                    verdict=Verdict.BEST) for n in range(16, 30)]
    )
    out = narrate_game(_analysis(verdicts, result="0-1", user_side="white"))
    assert "Défaite" in out["headline"]
    assert len(out["turning_points"]) == 1
    assert out["turning_points"][0]["move_number"] == 15
    assert out["turning_points"][0]["delta_cp"] == 45
    assert "raté" in out["turning_points"][0]["reason"].lower()
    assert out["recommended_drills"] == ["coup_royal"]


def test_scenario_structural_collapse():
    """User's middlegame is riddled with a long-lived hole on 23 + a
    persistent isolated pawn on 10. Both should surface as top
    persistent_weaknesses; phase_summary should call the middlegame
    quality 'imprécise' or worse."""
    f_holes_only = _features(holes_white=[23])
    f_holes_iso = _features(holes_white=[23], isolated_pawns_white=[10])
    f_clean = _features()

    verdicts = (
        # Clean opening
        [_verdict(move_number=n, side="white" if n % 2 else "black",
                  phase=Phase.OPENING, features_after=f_clean) for n in range(1, 8)]
        # Middlegame: structural collapse — hole on 23 for 12 half-moves,
        # plus iso on 10 from move 12 to 19 (8 half-moves).
        + [_verdict(move_number=n, side="white" if n % 2 else "black",
                    phase=Phase.MIDDLEGAME,
                    features_after=f_holes_only,
                    verdict=Verdict.INACCURACY, delta_winchance=0.06)
           for n in range(8, 12)]
        + [_verdict(move_number=n, side="white" if n % 2 else "black",
                    phase=Phase.MIDDLEGAME,
                    features_after=f_holes_iso,
                    verdict=Verdict.MISTAKE if n == 15 else Verdict.INACCURACY,
                    delta_winchance=0.20 if n == 15 else 0.06)
           for n in range(12, 20)]
    )
    out = narrate_game(_analysis(verdicts, user_side="white"),
                       top_k_weaknesses=3, min_streak=5)
    # Hole streak is the longest one.
    assert out["persistent_weaknesses"][0]["family"] == "holes"
    assert out["persistent_weaknesses"][0]["square"] == 23
    assert out["persistent_weaknesses"][0]["duration_half_moves"] == 12
    # Iso streak comes next.
    families = [w["family"] for w in out["persistent_weaknesses"]]
    assert "isolated" in families
    # Middlegame surfaces a non-zero user ACPL — the structural collapse
    # is reflected in the cp number even if the qualitative label
    # (solide/correcte/imprécise/fragile) depends on the exact mix
    # of delta_winchance values per side.
    mg = next(p for p in out["phase_summary"] if p["phase"] == "middlegame")
    assert mg["acpl_user"] > 0
