"""Structural features: isolated / backward pawns, holes, outposts.

These functions are deliberately *engine-free*: they reason on the geometry
of the position. That keeps the computation deterministic and < 1 ms per
call (cf. spec §14.4). When a finer judgement is needed (e.g. "is this
square truly reachable by the opponent in one half-move"), the motif layer
of the framework can layer engine calls on top.

The spec text is loose on a couple of points and the §20 worked example is
informal. The precise definitions used here are documented in each
function's docstring.
"""

from __future__ import annotations

from ..game import GameState, Side
from .geometry import (
    BLACK_PROMOTION_ROW,
    WHITE_PROMOTION_ROW,
    coords_to_square,
    diagonal_neighbors,
    row_of,
    square_to_coords,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _starting_row_men(state: GameState, side: Side) -> frozenset[int]:
    """Squares occupied by ``side`` men still sitting on their starting row.

    White's starting row is row 10 (squares 46..50); black's is row 1 (1..5).
    """
    if side == "white":
        return state.white_men & BLACK_PROMOTION_ROW
    return state.black_men & WHITE_PROMOTION_ROW


def _forward_diagonals(sq: int, side: Side) -> list[int]:
    """The (up to 2) diagonal squares one row toward ``side``'s promotion."""
    r, c = square_to_coords(sq)
    dr = -1 if side == "white" else 1
    out: list[int] = []
    for dc in (-1, 1):
        rr, cc = r + dr, c + dc
        if 1 <= rr <= 10 and 1 <= cc <= 10:
            out.append(coords_to_square(rr, cc))
    return out


def _backward_diagonals(sq: int, side: Side) -> list[int]:
    """Diagonals one row toward ``side``'s starting row (the support squares)."""
    return _forward_diagonals(sq, "black" if side == "white" else "white")


# ---------------------------------------------------------------------------
# Public detectors
# ---------------------------------------------------------------------------


def find_isolated_pawns(state: GameState, side: Side) -> list[int]:
    """Men without any friendly piece on the four diagonal neighbours.

    Kings are ignored as candidates (the spec field is ``isolated_pawns_*``)
    but they DO count as supporting neighbours when looking for friends.
    """
    friends = state.pieces_of(side)
    return sorted(
        sq for sq in state.men_of(side)
        if not friends.intersection(diagonal_neighbors(sq))
    )


def find_backward_pawns(state: GameState, side: Side) -> list[int]:
    """Men still on their starting row whose diagonal-forward squares are unsupported.

    Both diagonal-forward squares (one row toward promotion) must be either
    off-board or NOT occupied by a friendly piece. A pawn with at least one
    diagonal friend ahead is considered to have lateral support and is not
    flagged. Edge pawns with a single forward diagonal are flagged only when
    that diagonal is empty.
    """
    friends = state.pieces_of(side)
    out: list[int] = []
    for sq in sorted(_starting_row_men(state, side)):
        forwards = _forward_diagonals(sq, side)
        if not any(f in friends for f in forwards):
            out.append(sq)
    return out


def find_holes(state: GameState, side: Side) -> list[int]:
    """Empty squares "inside" ``side``'s formation.

    An empty dark square ``s`` is a hole for ``side`` if at least three of
    its diagonal neighbours are occupied by ``side``'s own pieces. The
    threshold is a geometric proxy for "inside the formation": a square
    flanked by friendly pieces on three sides is, in practice, a soft spot
    that the opponent can target.
    """
    friends = state.pieces_of(side)
    empties = state.empty_squares
    out: list[int] = []
    for sq in sorted(empties):
        neighbours = diagonal_neighbors(sq)
        if sum(1 for n in neighbours if n in friends) >= 3:
            out.append(sq)
    return out


def find_outposts(state: GameState, side: Side) -> list[int]:
    """Advanced men that are both supported and safe from a single-jump capture.

    * **Advanced**: for white, rows 1..5 (toward promotion); for black,
      rows 6..10. Note the spec table mis-states the white inequality; the
      logical interpretation is used here.
    * **Supported**: at least one friendly piece sits on a diagonal-backward
      square (toward the player's starting row).
    * **Safe**: no opponent *man* can capture the pawn in a single half-move
      jump. King attackers and multi-step rafles are NOT considered at this
      layer — the motif layer handles those.
    """
    opp: Side = "black" if side == "white" else "white"
    opp_men = state.men_of(opp)
    friends = state.pieces_of(side)
    empties = state.empty_squares

    out: list[int] = []
    for sq in sorted(state.men_of(side)):
        r = row_of(sq)
        is_advanced = (side == "white" and r <= 5) or (side == "black" and r >= 6)
        if not is_advanced:
            continue
        # Support: at least one diagonal-backward friend.
        if not any(b in friends for b in _backward_diagonals(sq, side)):
            continue
        # Capturability by an opponent man (single-jump test).
        if _capturable_by_opponent_man(state, sq, opp_men, empties):
            continue
        out.append(sq)
    return out


def _capturable_by_opponent_man(
    state: GameState,
    sq: int,
    opp_men: frozenset[int],
    empties: frozenset[int],
) -> bool:
    """True iff some opponent *man* can jump over ``sq`` in one half-move."""
    r, c = square_to_coords(sq)
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        ar, ac = r + dr, c + dc      # attacker square
        lr, lc = r - dr, c - dc      # landing square (opposite side)
        if not (1 <= ar <= 10 and 1 <= ac <= 10):
            continue
        if not (1 <= lr <= 10 and 1 <= lc <= 10):
            continue
        attacker = coords_to_square(ar, ac)
        landing = coords_to_square(lr, lc)
        if attacker in opp_men and landing in empties:
            return True
    return False
