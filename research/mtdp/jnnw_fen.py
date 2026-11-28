"""JNNW bitboards to FMJD-numbered Hub FEN (structural only).

Bit i maps to square i+1 per pinned Jass src/types.hpp and tools/pdn_to_jnnw.py.
Rendering a FEN does NOT establish legal reachability or game independence.
"""
from __future__ import annotations

from research.mtdp.jnnw_audit import BOARD_MASK


def _pieces(men: int, kings: int) -> str:
    return ",".join(
        ("K" if kings & (1 << bit) else "") + str(bit + 1)
        for bit in range(50)
        if (men | kings) & (1 << bit)
    )


def bitboards_to_fen(wm: int, wk: int, bm: int, bk: int, stm: int) -> str:
    boards = (wm, wk, bm, bk)
    if any(type(board) is not int or board < 0 or board & ~BOARD_MASK for board in boards):
        raise ValueError("bitboards must be unsigned 50-square integers")
    if type(stm) is not int or stm not in (0, 1):
        raise ValueError("invalid side to move")
    if sum(board.bit_count() for board in boards) != (wm | wk | bm | bk).bit_count():
        raise ValueError("overlapping pieces")
    return f"{'W' if stm == 0 else 'B'}:W{_pieces(wm, wk)}:B{_pieces(bm, bk)}"
