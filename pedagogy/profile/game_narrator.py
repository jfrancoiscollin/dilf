"""Per-game narrative generator — turn a :class:`GameAnalysis` into a
structured "résumé de partie" that a UI can render as cards.

A sibling of :mod:`heatmap_narrator`. Same philosophy: structured
output, deterministic, FR templates, no LLM, no I/O. The narrator
takes the per-half-move data dilf already produces (verdicts +
motifs + features + phase) and aggregates it into the handful of
facts that actually matter when a user opens a finished game:

  - headline                — one-line scoreboard + accuracy
  - phase_summary           — opening / middlegame / endgame breakdown
  - turning_points          — the 3 worst moves and why (J2)
  - persistent_weaknesses   — weakest structural features across phases (J2)
  - motifs_played / _missed — counts by slug, both roles
  - strengths               — short positive callouts
  - recommended_drills      — motif slugs to feed into the exercise picker

**Status: J1+J2** (this commit) — types, headline, phase_summary,
motif counters, strengths skeleton, recommended_drills, plus
turning_points (top-K by delta_winchance with FR reason templates)
and persistent_weaknesses (streak detection over
features_after.{family}_{side} across the whole game). English
templates on J3.

The function is pure: no DB call, no Scan call, no clock. Callers
load the analysis from wherever and hand it in.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Literal, Optional, TypedDict

from ..types import GameAnalysis, MoveVerdict, Phase, Verdict
from .aggregator import compute_accuracy

# ── Output shape ────────────────────────────────────────────────────────

PhaseLiteral = Literal["opening", "middlegame", "endgame"]
WeaknessFamily = Literal["isolated", "backward", "holes", "outposts"]


class PhaseSummary(TypedDict):
    phase: PhaseLiteral
    n_half_moves: int
    acpl_user: int
    acpl_opponent: int
    summary: str


class TurningPoint(TypedDict):
    move_number: int
    side: Literal["white", "black"]
    notation: str
    delta_cp: int
    score_before: float
    score_after: float
    verdict: str
    reason: str


class PersistentWeakness(TypedDict):
    family: WeaknessFamily
    square: int
    side: Literal["white", "black"]
    duration_half_moves: int
    first_seen: int
    summary: str


class GameNarrative(TypedDict):
    headline: str
    phase_summary: list[PhaseSummary]
    turning_points: list[TurningPoint]
    persistent_weaknesses: list[PersistentWeakness]
    motifs_played: dict[str, int]
    motifs_missed: dict[str, int]
    strengths: list[str]
    recommended_drills: list[str]


# ── FR templates (EN twin lands on J3, see module docstring) ────────────

PHASE_FR: dict[PhaseLiteral, str] = {
    "opening": "ouverture",
    "middlegame": "milieu de jeu",
    "endgame": "finale",
}

# Per-weakness-family vocabulary for the persistent-weakness summary
# strings ("Trou sur 23 pendant 18 demi-coups, à partir du coup 15").
# Singular form on purpose — the summary is one row per (square,
# family, side) so we never say "trous" here.
_FAMILY_LABEL_FR: dict[WeaknessFamily, str] = {
    "isolated": "Pion isolé",
    "backward": "Pion retardé",
    "holes":    "Trou",
    "outposts": "Poste",   # an outpost is a strength; still flagged when
                            # it persists, so the user knows what worked.
}
_SIDE_BADGE: dict[str, str] = {"white": "⬜", "black": "⬛"}

# Verdict-level FR fallbacks used in the TurningPoint.reason field
# when no motif explains the move. Lifted from the VERDICT_FALLBACKS
# table in templates_fr.py — kept inline here so the narrator
# doesn't import the heavy templates module.
_TURNING_REASON_FALLBACK_FR: dict[Verdict, str] = {
    Verdict.BLUNDER:    "Gaffe — coup perdant",
    Verdict.MISTAKE:    "Erreur — perte significative",
    Verdict.INACCURACY: "Imprécision",
    Verdict.GOOD:       "Coup correct",
    Verdict.EXCELLENT:  "Coup quasi-optimal",
    Verdict.BEST:       "Meilleur coup",
    Verdict.BRILLIANT:  "Coup brillant",
    Verdict.FORCED:     "Coup forcé",
    Verdict.BOOK:       "Coup de théorie",
}

# Significance threshold below which a move isn't reported as a
# turning point even if it makes the top-K — same cutoff as the
# `inaccuracy` bucket in dilf's verdict scoring (8 cp). Stops the
# "résumé" from inventing drama in a clean game.
_TURNING_MIN_DELTA = 0.08

# Quality thresholds for the per-phase 1-liner — lifted from the
# ACPL conventions used elsewhere in the codebase (Scan annotation +
# AccuracySummary). 20 cp ≈ "solide", 50 cp ≈ "bavard", 80 cp+ ≈ "fragile".
_PHASE_QUALITY_THRESHOLDS = (20, 50, 80)
_PHASE_QUALITY_LABELS_FR = ("solide", "correcte", "imprécise", "fragile")


def _phase_quality_label_fr(acpl: int) -> str:
    """Map ACPL to a one-word quality tag."""
    for i, t in enumerate(_PHASE_QUALITY_THRESHOLDS):
        if acpl < t:
            return _PHASE_QUALITY_LABELS_FR[i]
    return _PHASE_QUALITY_LABELS_FR[-1]


# ── Aggregation helpers ─────────────────────────────────────────────────


def _acpl(verdicts: Iterable[MoveVerdict]) -> int:
    """Average centipawn loss across ``verdicts``. Forced and book moves
    are filtered out — same convention as :func:`compute_accuracy`. Returns
    a rounded int so the output JSON is concise; the source unit is win-
    chance delta scaled to centipawns (×100), matching the Scan
    annotation pipeline in draught-master."""
    losses: list[int] = []
    for v in verdicts:
        if v.verdict in (Verdict.FORCED, Verdict.BOOK):
            continue
        losses.append(round(max(0.0, v.delta_winchance) * 100))
    if not losses:
        return 0
    return round(sum(losses) / len(losses))


def _phase_summary(
    verdicts: list[MoveVerdict],
    user_side: Optional[str],
) -> list[PhaseSummary]:
    """One :class:`PhaseSummary` per phase that has at least one verdict.

    Phases that the game never visited (e.g. an opening-only game that
    didn't reach the endgame) are omitted rather than emitted with
    zero data — keeps the UI clean.
    """
    by_phase: dict[Phase, list[MoveVerdict]] = defaultdict(list)
    for v in verdicts:
        by_phase[v.phase].append(v)

    out: list[PhaseSummary] = []
    # Preserve the natural phase order regardless of insertion order.
    for phase in (Phase.OPENING, Phase.MIDDLEGAME, Phase.ENDGAME):
        vs = by_phase.get(phase, [])
        if not vs:
            continue
        user_vs = [v for v in vs if user_side and v.side == user_side]
        opp_vs = [v for v in vs if user_side and v.side != user_side]
        acpl_u = _acpl(user_vs) if user_vs else 0
        acpl_o = _acpl(opp_vs) if opp_vs else 0
        quality = _phase_quality_label_fr(acpl_u)
        label = PHASE_FR[phase.value]   # type: ignore[index]
        summary = f"{label.capitalize()} {quality} : {acpl_u} cp ({len(vs)} demi-coups)"
        out.append(PhaseSummary(
            phase=phase.value,           # type: ignore[typeddict-item]
            n_half_moves=len(vs),
            acpl_user=acpl_u,
            acpl_opponent=acpl_o,
            summary=summary,
        ))
    return out


def _motif_counters(
    verdicts: list[MoveVerdict],
) -> tuple[dict[str, int], dict[str, int]]:
    """Return ``(played, missed)`` dicts, each ``slug -> count``,
    sorted by count desc + slug asc for determinism. ``threatened`` and
    ``suffered`` roles are skipped — they're not what the user *did*."""
    played: Counter[str] = Counter()
    missed: Counter[str] = Counter()
    for v in verdicts:
        for m in v.motifs:
            if m.role == "played":
                played[m.motif] += 1
            elif m.role == "missed":
                missed[m.motif] += 1
    def _sort(c: Counter[str]) -> dict[str, int]:
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
    return _sort(played), _sort(missed)


def _strengths_fr(
    verdicts: list[MoveVerdict],
    motifs_played: dict[str, int],
) -> list[str]:
    """Short positive callouts — count brilliants, count offensive
    motifs played, longest king maneuver (skipped on J1: needs Features
    streak detection that J2 introduces)."""
    out: list[str] = []
    n_brilliant = sum(1 for v in verdicts if v.verdict == Verdict.BRILLIANT)
    if n_brilliant > 0:
        word = "coup brillant" if n_brilliant == 1 else "coups brillants"
        out.append(f"{n_brilliant} {word} détecté{'s' if n_brilliant > 1 else ''}")
    n_motifs = sum(motifs_played.values())
    if n_motifs > 0:
        out.append(
            f"{n_motifs} motif{'s' if n_motifs > 1 else ''} offensif{'s' if n_motifs > 1 else ''} "
            f"({', '.join(motifs_played.keys())})"
        )
    return out


def _headline_fr(
    analysis: GameAnalysis,
    user_side: Optional[str],
) -> str:
    """One-line scoreboard. Reads ``analysis.summary['result']`` if the
    caller filled it (e.g. "1-0" / "0-1" / "1/2-1/2"); otherwise just
    reports half-move count + user accuracy.
    """
    verdicts = analysis.verdicts
    n_moves = len(verdicts)
    user_verdicts = (
        [v for v in verdicts if v.side == user_side] if user_side else verdicts
    )
    accuracy = round(compute_accuracy(user_verdicts) * 100)
    result = (analysis.summary or {}).get("result")
    side_label = (
        "⬜" if user_side == "white" else "⬛" if user_side == "black" else ""
    )

    if isinstance(result, str) and result:
        # Map FMJD result strings to a verbal outcome relative to the user.
        outcome = _outcome_fr(result, user_side)
        return f"{outcome} {side_label} en {n_moves} demi-coups · {accuracy}% précision".strip()
    return f"{n_moves} demi-coups · {accuracy}% précision".strip()


def _outcome_fr(result: str, user_side: Optional[str]) -> str:
    """Translate a result string to a verb-ish outcome for the headline."""
    norm = result.strip()
    if norm in ("1/2-1/2", "½-½", "draw"):
        return "Nulle"
    if user_side is None:
        return f"Résultat {norm}"
    won = (
        (norm == "1-0" and user_side == "white")
        or (norm == "0-1" and user_side == "black")
    )
    return "Victoire" if won else "Défaite"


# ── Turning points ──────────────────────────────────────────────────────


def _turning_reason_fr(v: MoveVerdict) -> str:
    """One short FR sentence explaining why this move is a turning point.

    Priority order:
      1. A motif the move *missed* — the most actionable insight for
         the user ("Tu as raté coup_royal au coup 15").
      2. A motif the move *played* — explains a successful but costly
         choice (rare in turning points, but happens with sacrifices).
      3. The verdict-level fallback ("Gaffe — coup perdant").

    Roles `threatened` and `suffered` are skipped — those describe
    the opponent's options, not the player's choice.
    """
    missed = [m for m in v.motifs if m.role == "missed"]
    if missed:
        slug = missed[0].motif.replace("_", " ")
        return f"Tu as raté {slug}"
    played = [m for m in v.motifs if m.role == "played"]
    if played:
        slug = played[0].motif.replace("_", " ")
        return f"Joué : {slug}"
    return _TURNING_REASON_FALLBACK_FR.get(v.verdict, "Coup décisif")


def _turning_points(
    verdicts: list[MoveVerdict],
    top_k: int,
) -> list[TurningPoint]:
    """The K verdicts that hurt the side-to-move's win chances the most.

    Filtered to ``delta_winchance >= _TURNING_MIN_DELTA`` so a clean
    game (no real swings) reports zero turning points rather than
    inflating non-events into "tournants". Ties broken by move_number
    ascending so the earliest of two equally-costly moves comes first
    in the list — usually the one that set the tone.
    """
    candidates = [v for v in verdicts if v.delta_winchance >= _TURNING_MIN_DELTA]
    candidates.sort(key=lambda v: (-v.delta_winchance, v.move_number))
    out: list[TurningPoint] = []
    for v in candidates[:top_k]:
        out.append(TurningPoint(
            move_number=v.move_number,
            side=v.side,                                # type: ignore[typeddict-item]
            notation=v.move_notation,
            delta_cp=round(v.delta_winchance * 100),
            score_before=v.score_before,
            score_after=v.score_after,
            verdict=v.verdict.value,
            reason=_turning_reason_fr(v),
        ))
    return out


# ── Persistent weaknesses ──────────────────────────────────────────────


# Map (family, side) → attribute name on Features. Same convention as
# the frontend's aggregateGameHeatmap, kept here so the streak
# detector doesn't have to know about Python's getattr quirks.
_FAMILY_FIELD: dict[tuple[WeaknessFamily, str], str] = {
    ("isolated", "white"): "isolated_pawns_white",
    ("isolated", "black"): "isolated_pawns_black",
    ("backward", "white"): "backward_pawns_white",
    ("backward", "black"): "backward_pawns_black",
    ("holes",    "white"): "holes_white",
    ("holes",    "black"): "holes_black",
    ("outposts", "white"): "outposts_white",
    ("outposts", "black"): "outposts_black",
}


def _weakness_summary_fr(
    family: WeaknessFamily, square: int, side: str,
    duration: int, first_seen: int,
) -> str:
    label = _FAMILY_LABEL_FR.get(family, family)
    badge = _SIDE_BADGE.get(side, side)
    return (
        f"{label} sur {square} ({badge}) pendant {duration} demi-coups, "
        f"à partir du coup {first_seen}"
    )


def _persistent_weaknesses(
    verdicts: list[MoveVerdict],
    top_k: int,
    min_streak: int,
    user_side: Optional[str],
) -> list[PersistentWeakness]:
    """Detect contiguous-half-move streaks where the same (square,
    family, side) was flagged in ``features_after``, return the
    longest ``top_k`` of them.

    Walk verdicts in order. For each family × side combo, project the
    set of currently-active squares; compare with the previous step
    to find opened streaks (square present now but not before) and
    closed streaks (present before but not now). Closed streaks get
    appended with their realised duration. At end-of-game any still-
    open streak is closed at the last verdict's move_number.

    Filtered down by:
      - ``duration >= min_streak`` (drops noise — a 1-2 demi-coup
        blip isn't a "persistent" weakness)
      - if ``user_side`` is given, only that side's streaks (the user
        doesn't usually care about the opponent's structure when
        analysing their own game). Pass ``None`` to keep both sides.

    Top-K ordering: duration desc, then first_seen asc (the streak
    that started earliest wins ties — often the more revealing
    pattern). Tie-break on family + square for full determinism.
    """
    # (family, side, square) -> first_seen_move_number while the
    # streak is open. Move out into a list of PersistentWeakness once
    # closed.
    open_streaks: dict[tuple[WeaknessFamily, str, int], int] = {}
    closed: list[PersistentWeakness] = []
    last_move_number = verdicts[-1].move_number if verdicts else 0

    sides_to_track: tuple[str, ...] = (
        (user_side,) if user_side else ("white", "black")
    )
    families: tuple[WeaknessFamily, ...] = (
        "isolated", "backward", "holes", "outposts",
    )

    def _close(key: tuple[WeaknessFamily, str, int], end_move: int) -> None:
        first_seen = open_streaks.pop(key)
        duration = end_move - first_seen + 1
        if duration < min_streak:
            return
        family, side, square = key
        closed.append(PersistentWeakness(
            family=family,
            square=square,
            side=side,                                  # type: ignore[typeddict-item]
            duration_half_moves=duration,
            first_seen=first_seen,
            summary=_weakness_summary_fr(family, square, side, duration, first_seen),
        ))

    for v in verdicts:
        feats = v.features_after
        # Features-less verdict (older row, engine-less compute_features
        # call) → treat as "nothing active" so any open streak closes at
        # the previous step. Avoids spurious continuation across an
        # unreliable observation.
        active: set[tuple[WeaknessFamily, str, int]] = set()
        if feats is not None:
            for side in sides_to_track:
                for family in families:
                    field = _FAMILY_FIELD.get((family, side))
                    if field is None:
                        continue
                    for sq in getattr(feats, field, []) or []:
                        active.add((family, side, int(sq)))

        # Close streaks that stopped being active this verdict.
        for key in list(open_streaks.keys()):
            if key not in active:
                _close(key, v.move_number - 1)

        # Open new streaks for newly-active (family, side, square) tuples.
        for key in active:
            if key not in open_streaks:
                open_streaks[key] = v.move_number

    # End-of-game flush.
    for key in list(open_streaks.keys()):
        _close(key, last_move_number)

    # Top-K by (-duration, first_seen, family, square) for stable
    # ordering. Family + square enter the key as the final tie-breaker
    # so two streaks of identical duration AND first_seen still sort
    # deterministically across Python dict orderings.
    closed.sort(key=lambda w: (
        -w["duration_half_moves"], w["first_seen"], w["family"], w["square"],
    ))
    return closed[:top_k]


# ── Public entry point ──────────────────────────────────────────────────


def narrate_game(
    analysis: GameAnalysis,
    *,
    user_side: Optional[Literal["white", "black"]] = None,
    top_k_turning_points: int = 3,
    top_k_weaknesses: int = 3,
    min_streak: int = 5,
    lang: Literal["fr", "en"] = "fr",
) -> GameNarrative:
    """Aggregate one :class:`GameAnalysis` into a :class:`GameNarrative`.

    ``user_side`` defaults to ``analysis.user_side`` if the caller
    doesn't override it; the per-side ACPL split + headline outcome
    are computed relative to this side. ``top_k_*`` cap the
    ``turning_points`` and ``persistent_weaknesses`` lists (both
    stubbed on J1, fully populated J2). ``min_streak`` filters out
    short-lived weaknesses; same J2.

    ``lang`` is honoured today only by FR (J1 ships FR templates).
    An EN twin lands on J3 — see the module docstring.

    No I/O, no engine call. Safe to invoke from a request handler
    inside an event loop.
    """
    if lang != "fr":
        # J3 backlog: ship EN templates. Defaulting to FR keeps the
        # contract stable and avoids a misleading half-translated output.
        lang = "fr"

    side = user_side or analysis.user_side
    verdicts = analysis.verdicts

    motifs_played, motifs_missed = _motif_counters(verdicts)

    return GameNarrative(
        headline=_headline_fr(analysis, side),
        phase_summary=_phase_summary(verdicts, side),
        turning_points=_turning_points(verdicts, top_k_turning_points),
        persistent_weaknesses=_persistent_weaknesses(
            verdicts, top_k_weaknesses, min_streak, side,
        ),
        motifs_played=motifs_played,
        motifs_missed=motifs_missed,
        strengths=_strengths_fr(verdicts, motifs_played),
        # Recommended drills: just the motifs the user MISSED most often,
        # ordered desc. The dict is already sorted by _motif_counters so
        # we just lift the keys.
        recommended_drills=list(motifs_missed.keys()),
    )


__all__ = [
    "GameNarrative",
    "PersistentWeakness",
    "PhaseLiteral",
    "PhaseSummary",
    "TurningPoint",
    "WeaknessFamily",
    "narrate_game",
]
