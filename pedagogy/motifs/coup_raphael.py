"""``coup_raphael`` — the specific 28x6 / 23x5 rafle pattern (or its mirror).

Spec §1: "Sacrifice de pion 27 ou 24 amenant rafle 28x6 / 23x5". The
deterministic part we can observe in a single half-move is the rafle
itself: the playing piece starts at square 28 or 23 (white) — or 28 or
23 from the black side, which mirrors to the same start-set under the
51 - sq involution — and lands on the opponent's promotion row.

We detect both white and black sides:

- White Raphaël: path starts in {23, 28} and lands in {5, 6}.
- Black Raphaël (mirror): path starts in {23, 28} and lands in {45, 46}.

The rafle must capture at least three pieces; shorter sequences from the
same squares are too generic to be the named motif.
"""

from __future__ import annotations

from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

_RAPHAEL_STARTS: frozenset[int] = frozenset({23, 28})
_RAPHAEL_LANDS_WHITE: frozenset[int] = frozenset({5, 6})
_RAPHAEL_LANDS_BLACK: frozenset[int] = frozenset({45, 46})
_MIN_CAPTURES: int = 3


def _matches_raphael(move: Move) -> tuple[bool, str | None]:
    if not move.is_capture or len(move.captures) < _MIN_CAPTURES:
        return False, None
    start = move.path[0]
    end = move.path[-1]
    if start not in _RAPHAEL_STARTS:
        return False, None
    if end in _RAPHAEL_LANDS_WHITE:
        return True, "white"
    if end in _RAPHAEL_LANDS_BLACK:
        return True, "black"
    return False, None


def _build_match(move: Move, side: str, role: str, severity: float) -> MotifMatch:
    return MotifMatch(
        motif="coup_raphael",
        role=role,
        squares=list(move.path),
        pv=[notation(move)],
        severity=severity,
        metadata={
            "captures_count": len(move.captures),
            "side": side,
            "start_square": move.path[0],
            "land_square": move.path[-1],
        },
    )


class CoupRaphaelDetector(MotifDetector):
    """Detector for the ``coup_raphael`` motif."""

    name = "coup_raphael"

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
        matched, side = _matches_raphael(move)
        if not matched or side is None:
            return None
        severity = min(1.0, len(move.captures) / 5.0)
        return _build_match(move, side, "played", severity)

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
        matched, side = _matches_raphael(best_move)
        if not matched or side is None:
            return None
        return _build_match(best_move, side, "missed", 1.0)
