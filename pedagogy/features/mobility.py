"""Mobility features.

These functions need an :class:`EngineProtocol` instance because legal move
generation under FMJD rules (forced and maximal capture) is non-trivial and
intentionally kept outside of this package — see the module README.
"""

from __future__ import annotations

from dataclasses import replace

from ..game import GameState, Move, Side
from ..protocols import EngineProtocol


def _with_turn(state: GameState, side: Side) -> GameState:
    """Return ``state`` modified to have ``side`` to move."""
    if state.turn == side:
        return state
    return replace(state, turn=side)


def count_legal_moves(state: GameState, side: Side, engine: EngineProtocol) -> int:
    """Number of legal half-moves for ``side`` in ``state``.

    The engine is consulted with ``side`` to move regardless of
    ``state.turn``; useful for symmetric reporting on the same position.
    """
    return len(engine.legal_moves(_with_turn(state, side)))


def threatened_captures(state: GameState, by_side: Side, engine: EngineProtocol) -> list[Move]:
    """Captures ``by_side`` could play if it were its turn.

    Returned moves are pre-filtered to ``is_capture``. The order is whatever
    the engine yields; callers should not rely on it.
    """
    moves = engine.legal_moves(_with_turn(state, by_side))
    return [m for m in moves if m.is_capture]


def hanging_pieces(state: GameState, side: Side, engine: EngineProtocol) -> list[int]:
    """Squares of ``side``'s pieces that the opponent could capture next turn.

    A piece is *hanging* if it appears in the captures of any legal move the
    opponent would have on their turn. The function does not assess whether
    a *recapture* compensates — that finer judgement belongs to a tactical
    detector, not to a feature.
    """
    opp: Side = "black" if side == "white" else "white"
    hanging: set[int] = set()
    for move in threatened_captures(state, opp, engine):
        hanging.update(move.captures)
    own = state.pieces_of(side)
    return sorted(hanging & own)
