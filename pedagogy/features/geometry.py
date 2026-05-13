"""Board geometry for the FMJD 10x10 board.

All numeric squares are 1..50 inclusive. ``square_to_coords`` and its inverse
implement the canonical PDN numbering used internationally: square 1 is the
top-left dark square (Black's POV), squares grow left-to-right then
top-to-bottom.

Row indices go 1..10 from top (Black's back rank) to bottom (White's back
rank). Column indices go 1..10 from left to right.
"""

from __future__ import annotations

from typing import Final

from ..game import BOARD_SQUARES, GameState, Side

#: Sentinel returned by :func:`min_promotion_distance` when no man is on the
#: board for the queried side (kings do not promote, so they are excluded).
NO_MAN_DISTANCE: Final[int] = 11

#: Heart of the board — four squares most contested in classical openings.
CENTER_CORE: Final[frozenset[int]] = frozenset({22, 23, 27, 28})

#: Extended center (cf. Dubois, "Combinaisons", chap. 1).
CENTER_EXTENDED: Final[frozenset[int]] = frozenset(
    {16, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28, 29, 31, 32, 33, 34}
)

#: Left wing squares as defined by the spec. Excludes square 1 (already in
#: White's promotion row) for asymmetry intentional to the project glossary.
LEFT_WING: Final[frozenset[int]] = frozenset({6, 11, 16, 21, 26, 31, 36, 41, 46})

#: Right wing squares as defined by the spec.
RIGHT_WING: Final[frozenset[int]] = frozenset({5, 10, 15, 20, 25, 30, 35, 40, 45, 50})

#: Row 1: where black men promote into kings (for white).
WHITE_PROMOTION_ROW: Final[frozenset[int]] = frozenset({1, 2, 3, 4, 5})

#: Row 10: where white men promote (for black).
BLACK_PROMOTION_ROW: Final[frozenset[int]] = frozenset({46, 47, 48, 49, 50})

#: The single long diagonal of the FMJD board (5..46, length 10).
MAIN_DIAGONAL: Final[tuple[int, ...]] = (5, 10, 14, 19, 23, 28, 32, 37, 41, 46)


def _check_square(sq: int) -> None:
    if sq not in BOARD_SQUARES:
        raise ValueError(f"Invalid square {sq}: must be 1..50")


def square_to_coords(sq: int) -> tuple[int, int]:
    """Return ``(row, col)`` with ``row, col`` in ``[1, 10]``.

    Only dark squares are represented. The relation ``(row + col) % 2 == 1``
    holds for every legal square.
    """
    _check_square(sq)
    row = (sq - 1) // 5 + 1
    col_in_row = (sq - 1) % 5
    # Odd rows have dark squares at columns 2, 4, 6, 8, 10.
    # Even rows have them at columns 1, 3, 5, 7, 9.
    if row % 2 == 1:
        col = 2 + 2 * col_in_row
    else:
        col = 1 + 2 * col_in_row
    return (row, col)


def coords_to_square(row: int, col: int) -> int:
    """Inverse of :func:`square_to_coords`. Raises if ``(row, col)`` is light."""
    if not (1 <= row <= 10 and 1 <= col <= 10):
        raise ValueError(f"({row}, {col}) out of 10x10 board")
    if (row + col) % 2 == 0:
        raise ValueError(f"({row}, {col}) is a light square")
    if row % 2 == 1:
        col_in_row = (col - 2) // 2
    else:
        col_in_row = (col - 1) // 2
    return (row - 1) * 5 + col_in_row + 1


def row_of(sq: int) -> int:
    """Row index of ``sq`` in ``[1, 10]``."""
    _check_square(sq)
    return (sq - 1) // 5 + 1


def diagonal_neighbors(sq: int) -> list[int]:
    """Up to four adjacent dark squares (in any diagonal direction).

    Corner squares return 1 or 2 neighbors, edge squares 2 or 3, inner
    squares 4.
    """
    r, c = square_to_coords(sq)
    out: list[int] = []
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if 1 <= rr <= 10 and 1 <= cc <= 10:
            out.append(coords_to_square(rr, cc))
    out.sort()
    return out


def squares_between(sq_a: int, sq_b: int) -> list[int]:
    """Squares strictly between ``sq_a`` and ``sq_b`` along their diagonal.

    Raises ``ValueError`` if the two squares are not on the same diagonal or
    if they are equal.
    """
    if sq_a == sq_b:
        raise ValueError(f"Squares {sq_a} and {sq_b} are equal")
    ra, ca = square_to_coords(sq_a)
    rb, cb = square_to_coords(sq_b)
    if abs(ra - rb) != abs(ca - cb):
        raise ValueError(f"Squares {sq_a} and {sq_b} are not on the same diagonal")
    dr = 1 if rb > ra else -1
    dc = 1 if cb > ca else -1
    out: list[int] = []
    r, c = ra + dr, ca + dc
    while (r, c) != (rb, cb):
        out.append(coords_to_square(r, c))
        r += dr
        c += dc
    return out


def promotion_distance(sq: int, side: Side) -> int:
    """Number of rows separating ``sq`` from ``side``'s promotion rank.

    White promotes on row 1, black on row 10. Returns 0 for a piece already
    standing on its promotion row.
    """
    r = row_of(sq)
    if side == "white":
        return r - 1
    if side == "black":
        return 10 - r
    raise ValueError(f"side must be 'white' or 'black', got {side!r}")


def min_promotion_distance(state: GameState, side: Side) -> int:
    """Smallest promotion distance among ``side``'s *men*.

    Kings are excluded because they no longer promote. Returns
    :data:`NO_MAN_DISTANCE` (= 11, an unreachable value on a 10x10 board)
    when ``side`` has no man left.
    """
    men = state.men_of(side)
    if not men:
        return NO_MAN_DISTANCE
    return min(promotion_distance(sq, side) for sq in men)
