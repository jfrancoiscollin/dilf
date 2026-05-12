"""Material counts.

A king is worth 3 men in :func:`material_balance`; this is the same constant
used by the spec when reporting ``Features.material_balance``.
"""

from __future__ import annotations

from typing import TypedDict

from ..game import GameState


class MaterialCount(TypedDict):
    white_men: int
    white_kings: int
    black_men: int
    black_kings: int
    balance: int


KING_VALUE: int = 3


def count_material(state: GameState) -> MaterialCount:
    """Return ``{white_men, white_kings, black_men, black_kings, balance}``.

    ``balance = (white_men + 3*white_kings) - (black_men + 3*black_kings)``.
    Positive values favour white.
    """
    wm = len(state.white_men)
    wk = len(state.white_kings)
    bm = len(state.black_men)
    bk = len(state.black_kings)
    return MaterialCount(
        white_men=wm,
        white_kings=wk,
        black_men=bm,
        black_kings=bk,
        balance=(wm + KING_VALUE * wk) - (bm + KING_VALUE * bk),
    )


def material_balance(state: GameState) -> int:
    """Shorthand for ``count_material(state)["balance"]``."""
    return count_material(state)["balance"]


def total_pieces(state: GameState) -> int:
    """Total number of pieces (men + kings) on the board."""
    return (
        len(state.white_men)
        + len(state.white_kings)
        + len(state.black_men)
        + len(state.black_kings)
    )
