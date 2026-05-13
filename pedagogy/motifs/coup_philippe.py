"""``coup_philippe`` — rafle whose first capture lands on a wing square.

Historical "coup Philippe" sees one side give a piece on the wing to lure
the opponent's man out of position, then exploits the gap with a longer
rafle. From a single-half-move signature we can only see the exploiting
move; we use the heuristic "rafle whose first captured piece sits on a
wing square (left or right)" as a tractable proxy.

Known limitation: this catches some rafles that aren't strictly Philippe
patterns. Pedagogically the explanation still fits — a wing-anchored
rafle is a related motif — but a P3 refinement should ideally peek at
the previous half-move to confirm the actual sacrifice setup.
"""

from __future__ import annotations

from ..features.geometry import LEFT_WING, RIGHT_WING
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

_WINGS = LEFT_WING | RIGHT_WING


def _starts_on_wing(move: Move) -> bool:
    return bool(move.captures) and move.captures[0] in _WINGS


def _build_match(move: Move, *, role: str, severity: float) -> MotifMatch:
    first = move.captures[0] if move.captures else move.path[0]
    wing = "left" if first in LEFT_WING else "right"
    return MotifMatch(
        motif="coup_philippe",
        role=role,
        squares=list(move.path),
        pv=[notation(move)],
        severity=severity,
        metadata={
            "captures_count": len(move.captures),
            "wing": wing,
            "first_capture": first,
        },
    )


class CoupPhilippeDetector(MotifDetector):
    """Detector for the ``coup_philippe`` motif."""

    name = "coup_philippe"

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
        if not _starts_on_wing(move):
            return None
        severity = min(1.0, len(move.captures) / 5.0)
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
        if not _starts_on_wing(best_move):
            return None
        return _build_match(best_move, role="missed", severity=1.0)
