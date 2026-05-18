"""Heatmap narrator — turn per-square weakness counts into a 1-liner.

A weakness heatmap aggregates :class:`Features` snapshots across a user's
recent games: for each board square, it counts how many times the square
appeared in each of the four geometric weakness families (isolated /
backward / holes / outposts). The consumer (Draught Master's profile
panel today, conceivably other UIs tomorrow) renders that as a 10x10
colour-tinted grid.

The grid alone is hard to read for non-experts. This module distils the
heatmap into two short strings — top squares + a metric-specific
pedagogical hint — so the UI can surface a textual interpretation
under the grid.

**Status: v1**

The hints are canned, FR-only, and parametrised only by the dominant
geographic zone of the top squares (centre / aile gauche / aile droite /
rangée arrière). They are deliberately conservative — there's no
attempt yet to read motif co-occurrences, phase, or opponent strength.

**To enrich later** (non-exhaustive):

- **English version** mirroring :data:`HINTS_FR` (same i18n pattern as
  :mod:`pedagogy.explanations.templates_en`).
- **Phase-aware hints**: an "isolated pawn on 23 in the middlegame" is
  diagnostic; in the endgame it can be neutral or even good. Pull
  :class:`Phase` distribution from the source aggregation.
- **Cross-family correlations**: a hole on 22 paired with an outpost on
  18 tells a different story than either alone.
- **Severity weighting**: today every occurrence counts equally. A
  weakness that survived 20 half-moves in one game should weigh more
  than one that resolved in 2.
- **Motif co-occurrence**: if 95 % of the top isolated squares also
  appear in "Coup royal subi" verdicts, say so.
- **LLM hand-off**: keep this module as the structured-input layer and
  let a Claude writer (see :mod:`pedagogy.explanations.claude_writer`)
  expand the hint into a paragraph with book citations.

Until those land, callers should treat the narrative as a *starting
point* — useful, but not a complete diagnosis.
"""

from __future__ import annotations

from typing import Literal, Mapping, Optional, TypedDict

from ..features.geometry import CENTER_EXTENDED, LEFT_WING, RIGHT_WING

#: The four weakness families plus the synthetic "all" metric that sums
#: the three real weaknesses (outposts are strengths and stay separate).
HeatmapMetric = Literal["all", "isolated", "backward", "holes", "outposts"]

_REAL_METRICS: tuple[HeatmapMetric, ...] = ("isolated", "backward", "holes", "outposts")


class SquareCounts(TypedDict):
    """Per-metric occurrence count for one board square."""

    isolated: int
    backward: int
    holes: int
    outposts: int


class HeatmapNarrative(TypedDict):
    """Two short strings the UI renders under the heatmap.

    ``top_line`` lists the highest-count squares verbatim (e.g.
    ``"36 (×8) · 23 (×6) · 14 (×5)"``). ``hint`` is one pedagogical
    sentence keyed off the active metric and the dominant zone(s) of
    the top squares. Both are FR-only in v1.
    """

    top_line: str
    hint: str


# Same back-row sets as in the geometry module's WHITE_PROMOTION_ROW /
# BLACK_PROMOTION_ROW, kept here under explicit zone names so the
# narrator output reads naturally to a French-speaking user.
_WHITE_BACK_ROW = frozenset({46, 47, 48, 49, 50})
_BLACK_BACK_ROW = frozenset({1, 2, 3, 4, 5})


def _zone_of(sq: int) -> str:
    """Return a short zone label for ``sq`` (FR)."""
    if sq in CENTER_EXTENDED:
        return "centre"
    if sq in LEFT_WING:
        return "aile gauche"
    if sq in RIGHT_WING:
        return "aile droite"
    if sq in _WHITE_BACK_ROW:
        return "rangée arrière ⬜"
    if sq in _BLACK_BACK_ROW:
        return "rangée arrière ⬛"
    return "milieu"


def _summarize_zones(squares: list[int]) -> str:
    """Top 2 zones (by count) covering the supplied squares, joined by ' + '.

    Returns an empty string when ``squares`` is empty so callers can
    decide whether to skip the hint entirely.
    """
    if not squares:
        return ""
    counts: dict[str, int] = {}
    for sq in squares:
        z = _zone_of(sq)
        counts[z] = counts.get(z, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return " + ".join(z for z, _ in ordered[:2])


#: FR pedagogical hints, parametrised by the dominant zone string.
#: Empty value means "no usable narrative for this metric on this data".
#: To extend: add an EN twin and pass ``lang`` through to pick the right
#: dict, mirroring :mod:`pedagogy.explanations.templates_fr` /
#: :mod:`pedagogy.explanations.templates_en`.
HINTS_FR: dict[HeatmapMetric, str] = {
    "all": (
        "Concentration sur {zones}. C'est là que ton placement est le plus "
        "instable — toutes familles confondues."
    ),
    "isolated": (
        "Pions isolés récurrents sur {zones}. Vulnérables : un déplacement "
        "les laisse à découvert. Renforce avant d'engager."
    ),
    "backward": (
        "Pions arriérés sur {zones}. Tu tardes à activer ces pions ; ils "
        "bloquent ton développement et la mobilité de tes pièces avancées."
    ),
    "holes": (
        "Trous récurrents en {zones}. Cases vides cernées de tes pièces — "
        "futurs postes adverses si tu ne les combles pas."
    ),
    "outposts": (
        "Tu installes régulièrement des postes en {zones}. C'est une force : "
        "capitalise sur ce style de jeu."
    ),
}


def _count_for(bucket: SquareCounts, metric: HeatmapMetric) -> int:
    """Read one metric out of a square's bucket. ``all`` sums the three
    real weaknesses (outposts excluded — those are strengths)."""
    if metric == "all":
        return sum(bucket[m] for m in ("isolated", "backward", "holes"))
    return bucket[metric]


def weakness_heatmap_narrative(
    by_square: Mapping[int, SquareCounts],
    metric: HeatmapMetric,
    *,
    top_k: int = 3,
) -> Optional[HeatmapNarrative]:
    """Distil a per-square count map into a top-line + 1-sentence hint.

    Returns ``None`` when every square has a count of 0 for the chosen
    metric (caller should hide the narrative panel in that case).
    ``top_k`` controls how many squares the top-line lists.

    The function is intentionally **pure** — no I/O, no global state —
    so it can be called from a FastAPI handler, a CLI, a test, or any
    other consumer of the dilf library. The input shape is the one the
    Draught Master ``/api/pedagogy/profile/me/weakness-heatmap``
    endpoint already produces; new UIs can build the same map from
    their own storage layer and reuse this narrator unchanged.
    """
    pairs = [
        (sq, _count_for(bucket, metric))
        for sq, bucket in by_square.items()
        if _count_for(bucket, metric) > 0
    ]
    if not pairs:
        return None

    # Sort descending by count; tie-break on square number ascending so
    # the output is stable across runs and across Python dict orderings.
    pairs.sort(key=lambda p: (-p[1], p[0]))
    top = pairs[:top_k]
    top_line = " · ".join(f"{sq} (×{n})" for sq, n in top)

    zones = _summarize_zones([sq for sq, _ in top])
    template = HINTS_FR.get(metric, "")
    hint = template.format(zones=zones) if zones and template else ""
    return HeatmapNarrative(top_line=top_line, hint=hint)


__all__ = [
    "HeatmapMetric",
    "HeatmapNarrative",
    "HINTS_FR",
    "SquareCounts",
    "weakness_heatmap_narrative",
]
