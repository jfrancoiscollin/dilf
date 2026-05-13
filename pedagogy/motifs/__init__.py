"""Motif detector registry.

Each detector lives in its own module; this package re-exports the abstract
base, the concrete classes and a tiny orchestrator (``detect_all``,
``detect_all_missed``) that drives them in a fixed order.

Adding a new motif: implement a subclass of :class:`MotifDetector` in a new
module, import it here, and append the class to :data:`ALL_DETECTORS`. No
other change is required.
"""

from __future__ import annotations

from ..game import GameState, Move
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector
from .coup_royal import CoupRoyalDetector
from .prise_max_ratee import PriseMaxRateeDetector

#: Detectors invoked by :func:`detect_all`, in deterministic order.
ALL_DETECTORS: list[type[MotifDetector]] = [
    CoupRoyalDetector,
    PriseMaxRateeDetector,
]


def detect_all(
    state_before: GameState,
    move: Move,
    state_after: GameState,
    *,
    pv: list[str] | None = None,
    scan_score_before: float = 0.0,
    scan_score_after: float = 0.0,
    engine: EngineProtocol | None = None,
) -> list[MotifMatch]:
    """Run every detector against the played move; return the matches."""
    matches: list[MotifMatch] = []
    for cls in ALL_DETECTORS:
        det = cls()
        match = det.detect(
            state_before,
            move,
            state_after,
            pv=pv,
            scan_score_before=scan_score_before,
            scan_score_after=scan_score_after,
            engine=engine,
        )
        if match is not None:
            matches.append(match)
    return matches


def detect_all_missed(
    state_before: GameState,
    best_move: Move,
    best_pv: list[str],
    played_move: Move,
    *,
    engine: EngineProtocol | None = None,
) -> list[MotifMatch]:
    """Run every detector's ``detect_missed`` against the unplayed best move."""
    matches: list[MotifMatch] = []
    for cls in ALL_DETECTORS:
        det = cls()
        match = det.detect_missed(
            state_before,
            best_move,
            best_pv,
            played_move,
            engine=engine,
        )
        if match is not None:
            matches.append(match)
    return matches


__all__ = [
    "ALL_DETECTORS",
    "CoupRoyalDetector",
    "MotifDetector",
    "PriseMaxRateeDetector",
    "detect_all",
    "detect_all_missed",
]
