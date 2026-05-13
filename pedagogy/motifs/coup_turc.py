"""``coup_turc`` — rafle whose trajectory revisits the same square.

FMJD rules forbid capturing the same piece twice; the *coup turc* of
historical literature refers to rafles whose moving piece passes a second
time through one of the intermediate squares, giving the **illusion** of a
double capture. The detector reduces this to a single test: the move's
``path`` contains a repeated square.

A coup turc is implicitly a rafle, so we require at least 2 captures.
"""

from __future__ import annotations

from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector


def _is_turc_signature(path: tuple[int, ...]) -> bool:
    """``True`` iff some square appears twice in ``path``."""
    return len(path) != len(set(path))


def _build_match(move: Move, *, role: str, severity: float) -> MotifMatch:
    return MotifMatch(
        motif="coup_turc",
        role=role,
        squares=list(move.path),
        pv=[notation(move)],
        severity=severity,
        metadata={
            "captures_count": len(move.captures),
            "path_length": len(move.path),
        },
    )


class CoupTurcDetector(MotifDetector):
    """Detector for the ``coup_turc`` motif."""

    name = "coup_turc"

    def detect(
        self,
        state_before: GameState,
        move: Move,
        state_after: GameState,
        *,
        pv: list[str] | None = None,
        scan_score_before: float = 0.0,
        scan_score_after: float = 0.0,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        if not move.is_capture or len(move.captures) < 2:
            return None
        if not _is_turc_signature(move.path):
            return None
        severity = min(1.0, len(move.captures) / 6.0)
        return _build_match(move, role="played", severity=severity)

    def detect_missed(
        self,
        state_before: GameState,
        best_move: Move,
        best_pv: list[str],
        played_move: Move,
        *,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        if played_move.path == best_move.path:
            return None
        if not best_move.is_capture or len(best_move.captures) < 2:
            return None
        if not _is_turc_signature(best_move.path):
            return None
        return _build_match(best_move, role="missed", severity=1.0)
