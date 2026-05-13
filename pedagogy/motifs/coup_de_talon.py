"""``coup_de_talon`` — rafle that reverses diagonal direction mid-trajectory.

The detector implements the spec pseudo-code: for each pair of consecutive
squares in the path, derive a ``(going_down, going_right)`` boolean tuple.
Any change between consecutive direction tuples is a "heel" motion.

We additionally require the move to be a rafle (≥ 2 captures); a single
non-capturing king redirection is not a coup de talon.
"""

from __future__ import annotations

from ..features.geometry import square_to_coords
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector


def _has_heel_motion(path: tuple[int, ...]) -> bool:
    """``True`` if the diagonal direction changes at least once in ``path``."""
    if len(path) < 3:
        return False
    directions: list[tuple[bool, bool]] = []
    for a, b in zip(path, path[1:]):
        ra, ca = square_to_coords(a)
        rb, cb = square_to_coords(b)
        directions.append((rb - ra > 0, cb - ca > 0))
    for d1, d2 in zip(directions, directions[1:]):
        if d1 != d2:
            return True
    return False


def _build_match(move: Move, *, role: str, severity: float) -> MotifMatch:
    return MotifMatch(
        motif="coup_de_talon",
        role=role,
        squares=list(move.path),
        pv=[notation(move)],
        severity=severity,
        metadata={
            "captures_count": len(move.captures),
            "path_length": len(move.path),
        },
    )


class CoupDeTalonDetector(MotifDetector):
    """Detector for the ``coup_de_talon`` motif."""

    name = "coup_de_talon"

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
        if not _has_heel_motion(move.path):
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
        if not _has_heel_motion(best_move.path):
            return None
        return _build_match(best_move, role="missed", severity=1.0)
