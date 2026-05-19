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

**Status: J1** (this commit) — types, headline, phase_summary,
motif counters, strengths skeleton, recommended_drills. Turning
points and persistent weaknesses are stubbed (empty lists) and
land on J2; English templates on J3.

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
        # J2 — both lists stay empty until the streak / turning-point
        # logic lands. Consumers see an empty array, render nothing.
        turning_points=[],
        persistent_weaknesses=[],
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
