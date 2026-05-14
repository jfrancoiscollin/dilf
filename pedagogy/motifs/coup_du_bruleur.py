"""``coup_du_bruleur`` — quiet move that "burns" several opponent men.

A *brûleur* is a non-capturing move that leaves at least two opponent
men with **both forward diagonals blocked**, while at least one of
those forward diagonals was free *before* the move. The opponent men
are effectively frozen: they cannot advance and their only escape is
to wait for another piece to move out of the way.

This is a *positional* motif — it does not require an engine PV or a
Scan score. It also does not require the move itself to capture: the
typical brûleur is a quiet pawn push that, by occupying a key forward
square, locks two or more enemy men at once.

Forward direction:

* white men advance toward row 1 (decreasing row index);
* black men advance toward row 10 (increasing row index).

A "forward diagonal" of a man on square *s* is therefore the up-left
and up-right neighbour for white, or the down-left and down-right
neighbour for black. Off-board counts as blocked.
"""

from __future__ import annotations

from ..features.geometry import diagonal_neighbors, row_of, square_to_coords
from ..game import GameState, Move, Side
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector


#: Minimum number of newly-burned men for the motif to fire.
BRULEUR_MIN_BURNED = 2


def _forward_diagonals(sq: int, side: Side) -> list[int]:
    """Return the two forward-diagonal squares for a ``side`` man on ``sq``.

    Off-board diagonals are simply omitted, so the list has length 0..2.
    """
    r, _ = square_to_coords(sq)
    target_row = r - 1 if side == "white" else r + 1
    out: list[int] = []
    for nb in diagonal_neighbors(sq):
        if row_of(nb) == target_row:
            out.append(nb)
    return out


def _is_blocked_man(state: GameState, sq: int, side: Side) -> bool:
    """A man on ``sq`` is blocked if every forward diagonal is occupied.

    Off-board diagonals never appear in :func:`_forward_diagonals`, so they
    implicitly count as blocked — a man at the edge with its only forward
    neighbour occupied is fully blocked.
    """
    forwards = _forward_diagonals(sq, side)
    return all(nb in state.all_pieces for nb in forwards)


def _newly_burned_men(
    state_before: GameState, state_after: GameState, opponent: Side
) -> list[int]:
    """Opponent men that became blocked between before and after."""
    burned: list[int] = []
    opp_men_after = state_after.men_of(opponent)
    opp_men_before = state_before.men_of(opponent)
    for sq in sorted(opp_men_after & opp_men_before):
        if _is_blocked_man(state_after, sq, opponent) and not _is_blocked_man(
            state_before, sq, opponent
        ):
            burned.append(sq)
    return burned


class CoupDuBruleurDetector(MotifDetector):
    """Detector for the ``coup_du_bruleur`` motif."""

    name = "coup_du_bruleur"
    requires_pv = False

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
        if move.is_capture:
            return None
        side = state_before.turn
        opponent: Side = "black" if side == "white" else "white"
        burned = _newly_burned_men(state_before, state_after, opponent)
        if len(burned) < BRULEUR_MIN_BURNED:
            return None
        return MotifMatch(
            motif="coup_du_bruleur",
            role="played",
            squares=[*move.path, *burned],
            pv=[],
            severity=min(1.0, len(burned) / 4.0),
            metadata={
                "side": side,
                "burned_count": len(burned),
                "burned_squares": burned,
            },
        )
