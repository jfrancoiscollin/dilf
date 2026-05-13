"""Verdict classification from Scan scores + motif context.

The sigmoid here is the **same** function used by the frontend
(``frontend/src/lib/gameAnnotations.ts`` in the parent project). Keeping the
two in lock-step guarantees the colour an annotation shows in the UI matches
the verdict the backend stored.
"""

from __future__ import annotations

import math
from typing import Iterable

from ..types import MotifMatch, Verdict

#: Slope of the sigmoid mapping a Scan pawn-unit score to a win chance.
#: A score of +0.5 pawn gives roughly +0.46 win chance, +1.0 gives +0.76.
_SIGMOID_SLOPE = 2.0

#: Brilliant gating threshold. A sacrifice that loses no more than this much
#: win-chance qualifies as brilliant (spec §6).
_BRILLIANT_MAX_DELTA = 0.05

#: Verdict bands keyed by upper-exclusive delta (spec §6 / classifier.py).
_VERDICT_BANDS: tuple[tuple[float, Verdict], ...] = (
    (0.01, Verdict.BEST),
    (0.03, Verdict.EXCELLENT),
    (0.075, Verdict.GOOD),
    (0.15, Verdict.INACCURACY),
    (0.30, Verdict.MISTAKE),
)


def win_chance(score: float) -> float:
    """Map a Scan pawn-unit score to a win chance in ``[-1, +1]``.

    Positive score => good for white. The return value is signed: ``+1.0``
    is a certain win for white, ``-1.0`` a certain loss. The sigmoid slope
    is shared with the frontend.
    """
    return 2.0 / (1.0 + math.exp(-_SIGMOID_SLOPE * score)) - 1.0


def _played_sacrifice(motifs: Iterable[MotifMatch]) -> bool:
    return any(m.motif == "sacrifice" and m.role == "played" for m in motifs)


def classify_move(
    score_before: float,
    score_after: float,
    side: str,
    is_forced: bool,
    is_book: bool,
    motifs: list[MotifMatch],
) -> Verdict:
    """Classify a half-move into a single :class:`Verdict`.

    Resolution order (spec §6):

    1. ``is_book`` short-circuits to :data:`Verdict.BOOK`.
    2. ``is_forced`` short-circuits to :data:`Verdict.FORCED`.
    3. A played sacrifice that loses ``< 0.05`` win chance is
       :data:`Verdict.BRILLIANT`.
    4. Otherwise the ``delta = win_chance_before - win_chance_after`` (from
       the moving side's perspective) is bucketed into the standard ladder
       BEST / EXCELLENT / GOOD / INACCURACY / MISTAKE / BLUNDER.
    """
    if is_book:
        return Verdict.BOOK
    if is_forced:
        return Verdict.FORCED

    sign = 1.0 if side == "white" else -1.0
    wc_before = sign * win_chance(score_before)
    wc_after = sign * win_chance(score_after)
    delta = wc_before - wc_after

    if _played_sacrifice(motifs) and delta < _BRILLIANT_MAX_DELTA:
        return Verdict.BRILLIANT

    for limit, verdict in _VERDICT_BANDS:
        if delta < limit:
            return verdict
    return Verdict.BLUNDER
