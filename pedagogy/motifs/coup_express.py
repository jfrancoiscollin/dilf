"""``coup_express`` — rafle of at least five captures travelling in a straight line.

Spec §1: "Rafle longue (5+ pions) en ligne droite". We confirm both halves
of the signature:

- ``len(move.captures) >= 5``.
- Every consecutive pair of path squares moves in the **same diagonal
  direction**. We derive the direction as
  ``(sign(row_b - row_a), sign(col_b - col_a))`` and require all pairs to
  produce the same tuple.

A direction reversal (``coup_de_talon``) or a back-passing trajectory
(``coup_turc``) would change the direction tuple and exclude the move.
"""

from __future__ import annotations

from ..features.geometry import square_to_coords
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

_MIN_CAPTURES: int = 5


def _path_is_straight(path: tuple[int, ...]) -> bool:
    if len(path) < 3:
        return True
    directions: set[tuple[int, int]] = set()
    for a, b in zip(path, path[1:]):
        ra, ca = square_to_coords(a)
        rb, cb = square_to_coords(b)
        dr = (rb > ra) - (rb < ra)
        dc = (cb > ca) - (cb < ca)
        directions.add((dr, dc))
    return len(directions) == 1


def _build_match(move: Move, *, role: str, severity: float) -> MotifMatch:
    return MotifMatch(
        motif="coup_express",
        role=role,
        squares=list(move.path),
        pv=[notation(move)],
        severity=severity,
        metadata={
            "captures_count": len(move.captures),
            "path_length": len(move.path),
        },
    )


class CoupExpressDetector(MotifDetector):
    """Detector for the ``coup_express`` motif."""

    name = "coup_express"

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
        if not move.is_capture or len(move.captures) < _MIN_CAPTURES:
            return None
        if not _path_is_straight(move.path):
            return None
        severity = min(1.0, len(move.captures) / 8.0)
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
        if not best_move.is_capture or len(best_move.captures) < _MIN_CAPTURES:
            return None
        if not _path_is_straight(best_move.path):
            return None
        return _build_match(best_move, role="missed", severity=1.0)
