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
from .coup_bonnard import CoupBonnardDetector
from .coup_de_talon import CoupDeTalonDetector
from .coup_du_bruleur import CoupDuBruleurDetector
from .coup_enfilade import CoupEnfiladeDetector
from .coup_express import CoupExpressDetector
from .coup_manoury import CoupManouryDetector
from .coup_napoleon import CoupNapoleonDetector
from .coup_philippe import CoupPhilippeDetector
from .coup_raphael import CoupRaphaelDetector
from .coup_royal import CoupRoyalDetector
from .coup_turc import CoupTurcDetector
from .envoi_a_dame import EnvoiADameDetector
from .prise_max_ratee import PriseMaxRateeDetector
from .sacrifices import SacrificeDetector

#: Detectors invoked by :func:`detect_all`, in deterministic order. P1
#: motifs come first; P2 motifs (coup_philippe, coup_raphael, coup_express,
#: coup_bonnard) run after so the older, more confidently-detected motifs
#: dominate the matches list when both apply. The P3 batch (coup_napoleon,
#: coup_manoury, coup_enfilade, coup_du_bruleur) runs last and is allowed
#: to overlap with broader P1/P2 motifs by design — they each carry their
#: own pedagogical signal.
ALL_DETECTORS: list[type[MotifDetector]] = [
    CoupRoyalDetector,
    CoupTurcDetector,
    CoupDeTalonDetector,
    EnvoiADameDetector,
    SacrificeDetector,
    PriseMaxRateeDetector,
    CoupPhilippeDetector,
    CoupRaphaelDetector,
    CoupExpressDetector,
    CoupBonnardDetector,
    CoupNapoleonDetector,
    CoupManouryDetector,
    CoupEnfiladeDetector,
    CoupDuBruleurDetector,
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
    "CoupBonnardDetector",
    "CoupDeTalonDetector",
    "CoupDuBruleurDetector",
    "CoupEnfiladeDetector",
    "CoupExpressDetector",
    "CoupManouryDetector",
    "CoupNapoleonDetector",
    "CoupPhilippeDetector",
    "CoupRaphaelDetector",
    "CoupRoyalDetector",
    "CoupTurcDetector",
    "EnvoiADameDetector",
    "MotifDetector",
    "PriseMaxRateeDetector",
    "SacrificeDetector",
    "detect_all",
    "detect_all_missed",
]
