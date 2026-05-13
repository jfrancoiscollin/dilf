"""``coup_royal`` — the long center rafle that makes draughts famous.

Signature (cf. spec §5):

* the move is a capture sequence of at least 6 pieces;
* a majority (≥ 4) of the captured pieces sit in :data:`CENTER_EXTENDED`;
* the captures touch at least 4 distinct rows;
* AND either the landing square is on a promotion row, OR the trajectory
  crosses the great diagonal (5–46).

The last clause was left as a TODO comment in the spec; we implement it
here so that "long center rafles" that don't actually reach the back rank
or the main diagonal are excluded. Loosening this check is a one-line
change should real fixtures show it is too strict.
"""

from __future__ import annotations

from ..features.geometry import (
    BLACK_PROMOTION_ROW,
    CENTER_EXTENDED,
    MAIN_DIAGONAL,
    WHITE_PROMOTION_ROW,
    row_of,
)
from ..game import GameState, Move, notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

#: Minimum captures for a rafle to even be considered for the coup royal.
ROYAL_MIN_CAPTURES = 6

#: Required number of captures inside :data:`CENTER_EXTENDED`.
ROYAL_MIN_CENTER_CAPTURES = 4

#: Required number of distinct rows touched by the captured squares.
ROYAL_MIN_ROWS = 4

_PROMOTION_ROWS: frozenset[int] = WHITE_PROMOTION_ROW | BLACK_PROMOTION_ROW
_MAIN_DIAGONAL_SET: frozenset[int] = frozenset(MAIN_DIAGONAL)


def _is_royal_signature(move: Move) -> bool:
    """Return ``True`` iff ``move`` matches the coup royal signature."""
    captures = move.captures
    if len(captures) < ROYAL_MIN_CAPTURES:
        return False
    center_captures = sum(1 for sq in captures if sq in CENTER_EXTENDED)
    if center_captures < ROYAL_MIN_CENTER_CAPTURES:
        return False
    rows = {row_of(sq) for sq in captures}
    if len(rows) < ROYAL_MIN_ROWS:
        return False
    finishes_in_promotion = move.path[-1] in _PROMOTION_ROWS
    crosses_main_diagonal = any(
        sq in _MAIN_DIAGONAL_SET for sq in (*move.path, *move.captures)
    )
    return finishes_in_promotion or crosses_main_diagonal


def _royal_squares(move: Move) -> list[int]:
    """Path + captured squares for UI highlighting (deduplicated, ordered)."""
    seen: dict[int, None] = {}
    for sq in (*move.path, *move.captures):
        seen.setdefault(sq, None)
    return list(seen)


class CoupRoyalDetector(MotifDetector):
    """Detector for the ``coup_royal`` motif."""

    name = "coup_royal"

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
        if not _is_royal_signature(move):
            return None
        return MotifMatch(
            motif=self.name,
            role="played",
            squares=_royal_squares(move),
            pv=[notation(move)],
            severity=min(1.0, len(move.captures) / 10.0),
            metadata={"captures_count": len(move.captures)},
        )

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
            return None  # the player did execute it
        if not _is_royal_signature(best_move):
            return None
        return MotifMatch(
            motif=self.name,
            role="missed",
            squares=_royal_squares(best_move),
            pv=[notation(best_move)],
            severity=1.0,
            metadata={"captures_count": len(best_move.captures)},
        )
