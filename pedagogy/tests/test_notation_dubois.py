"""Tests for :mod:`pedagogy.notation.dubois`.

The reference cases are drawn from Dubois Apprentissage Combinaisons,
chapter 1, page 6 (D1-D10). The starting positions are taken from the
auto-generated ``dubois_diagrams.py`` fixture; the published notations
are quoted verbatim from the Dubois PDF, with the explicit exception of
D9 where the PDF carries a typographic erratum (``43-38`` instead of
``44-39``) — see comments in the D9 test for the full story.
"""

from __future__ import annotations

import pytest

from pedagogy.game import GameState, Move
from pedagogy.notation.dubois import (
    AmbiguousRafleError,
    NoSuchRafleError,
    NotAManError,
    enumerate_pawn_captures,
    reconstruct_pawn_capture,
)


# ---------------------------------------------------------------------------
# Diagonal neighbours sanity check (internal helpers, but worth a smoke test)
# ---------------------------------------------------------------------------


def test_neighbours_corner_squares() -> None:
    """Sanity-check the internal geometry on the four corners."""
    from pedagogy.notation.dubois import _diagonal_neighbours

    # Square 1: top-left dark square (FMJD)
    nbrs = _diagonal_neighbours(1)
    assert nbrs == {"HG": None, "HD": None, "BG": 6, "BD": 7}
    # Square 5: top-right dark square — has a neighbour BG=10, no others (right column)
    assert _diagonal_neighbours(5) == {"HG": None, "HD": None, "BG": 10, "BD": None}
    # Square 46: bottom-left — has neighbour HD=41, no others (left column + bottom)
    assert _diagonal_neighbours(46) == {"HG": None, "HD": 41, "BG": None, "BD": None}
    # Square 50: bottom-right — has neighbours HG=44 and HD=45, no others (bottom row)
    assert _diagonal_neighbours(50) == {"HG": 44, "HD": 45, "BG": None, "BD": None}


def test_neighbours_central_square() -> None:
    """Square 28 sits comfortably inside the board with 4 neighbours."""
    from pedagogy.notation.dubois import _diagonal_neighbours

    assert _diagonal_neighbours(28) == {"HG": 22, "HD": 23, "BG": 32, "BD": 33}


# ---------------------------------------------------------------------------
# enumerate_pawn_captures: trivial / no-capture cases
# ---------------------------------------------------------------------------


def test_enumerate_no_capture_available() -> None:
    """A man with no enemy adjacent returns an empty list."""
    result = enumerate_pawn_captures(
        start=31, my_men=frozenset({31}), enemy_pieces=frozenset({1})
    )
    assert result == []


def test_enumerate_start_not_in_my_men_raises() -> None:
    with pytest.raises(ValueError, match="not in my_men"):
        enumerate_pawn_captures(
            start=31, my_men=frozenset({32}), enemy_pieces=frozenset({27})
        )


def test_enumerate_blocked_by_friendly() -> None:
    """A man with an enemy adjacent but landing square blocked by a friendly: no capture."""
    # White man on 31, enemy man on 27, friendly man on 22 (would-be landing).
    result = enumerate_pawn_captures(
        start=31,
        my_men=frozenset({22, 31}),
        enemy_pieces=frozenset({27}),
    )
    assert result == []


# ---------------------------------------------------------------------------
# enumerate_pawn_captures: single jump
# ---------------------------------------------------------------------------


def test_enumerate_single_jump() -> None:
    """Classical single-pawn capture: 31 jumps 27 (an enemy) and lands on 22."""
    result = enumerate_pawn_captures(
        start=31,
        my_men=frozenset({31}),
        enemy_pieces=frozenset({27}),
    )
    assert result == [((31, 22), frozenset({27}))]


def test_enumerate_backward_jump() -> None:
    """A man may capture backwards (FMJD rule)."""
    # White man on 22, enemy man on 27, landing on 31 (backward = increasing row).
    result = enumerate_pawn_captures(
        start=22,
        my_men=frozenset({22}),
        enemy_pieces=frozenset({27}),
    )
    # 22 has two enemy-adjacent cells from this set (only 27); land on 31.
    assert ((22, 31), frozenset({27})) in result


# ---------------------------------------------------------------------------
# enumerate_pawn_captures: zigzag rafles
# ---------------------------------------------------------------------------


def test_enumerate_dubois_d1_black_reply() -> None:
    """D1 page 6, black's forced reply after 26-21 is the rafle 17 → 26 → 37 → 28.

    Position after 26-21: W{21,31,32,43} B{9,17,19,38}.
    """
    state_after_sacrifice = GameState(
        white_men=frozenset({21, 31, 32, 43}),
        black_men=frozenset({9, 17, 19, 38}),
        turn="black",
    )
    # Black 17 captures: 17 → BG(21) → 26 → BD(31) → 37 → HD(32) → 28
    candidates = enumerate_pawn_captures(
        start=17,
        my_men=state_after_sacrifice.black_men,
        enemy_pieces=state_after_sacrifice.white_men,
    )
    # The maximal rafle from 17 captures 3 pieces (21, 31, 32) and lands on 28.
    paths_ending_on_28 = [c for c in candidates if c[0][-1] == 28]
    assert paths_ending_on_28 == [((17, 26, 37, 28), frozenset({21, 31, 32}))]


def test_enumerate_dubois_d1_white_finisher() -> None:
    """D1 page 6, white's finishing rafle 43x3 captures 4 black men.

    State after 26-21 and (17x28): W{43} B{9,17→28,19,38} → captures {38,28,19,9}.
    """
    state = GameState(
        white_men=frozenset({43}),
        black_men=frozenset({9, 19, 28, 38}),
        turn="white",
    )
    candidates = enumerate_pawn_captures(
        start=43, my_men=state.white_men, enemy_pieces=state.black_men
    )
    # Maximal rafle: 43 → 32 → 23 → 14 → 3, captures {38, 28, 19, 9}
    assert candidates == [((43, 32, 23, 14, 3), frozenset({9, 19, 28, 38}))]


# ---------------------------------------------------------------------------
# reconstruct_pawn_capture: end-to-end on Dubois D1
# ---------------------------------------------------------------------------


def _state_after_simple(state: GameState, frm: int, to: int) -> GameState:
    """Apply a non-capture move and return the resulting state (test helper)."""
    if frm in state.white_men:
        return GameState(
            white_men=(state.white_men - {frm}) | {to},
            white_kings=state.white_kings,
            black_men=state.black_men,
            black_kings=state.black_kings,
            turn="black",
        )
    return GameState(
        white_men=state.white_men,
        white_kings=state.white_kings,
        black_men=(state.black_men - {frm}) | {to},
        black_kings=state.black_kings,
        turn="white",
    )


def _state_after_capture(state: GameState, move: Move) -> GameState:
    """Apply a capture move and return the resulting state (test helper).

    Captures are removed from the OPPONENT's pieces, not the mover's.
    """
    captures = set(move.captures)
    if move.from_square in state.white_men:
        # White is moving; captures are black pieces.
        return GameState(
            white_men=(state.white_men - {move.from_square}) | {move.to_square},
            white_kings=state.white_kings,
            black_men=state.black_men - captures,
            black_kings=state.black_kings - captures,
            turn="black",
        )
    # Black is moving; captures are white pieces.
    return GameState(
        white_men=state.white_men - captures,
        white_kings=state.white_kings - captures,
        black_men=(state.black_men - {move.from_square}) | {move.to_square},
        black_kings=state.black_kings,
        turn="white",
    )


def test_reconstruct_dubois_d1_full_combination() -> None:
    """End-to-end: D1 position → 26-21 → 17x28 → 43x3 reconstructed step by step.

    Position: W{26,31,32,43} B{9,17,19,38}, white to move.
    Dubois solution: 26-21 (17x28) 43x3.
    """
    state = GameState(
        white_men=frozenset({26, 31, 32, 43}),
        black_men=frozenset({9, 17, 19, 38}),
        turn="white",
    )

    # 1. Sacrifice 26-21
    after_sacrifice = _state_after_simple(state, 26, 21)
    assert after_sacrifice.white_men == frozenset({21, 31, 32, 43})

    # 2. Black's forced reply (17x28)
    black_move = reconstruct_pawn_capture(after_sacrifice, 17, 28)
    assert black_move == Move(
        path=(17, 26, 37, 28), captures=(21, 31, 32)
    )
    after_reply = _state_after_capture(after_sacrifice, black_move)
    assert after_reply.white_men == frozenset({43})
    assert after_reply.black_men == frozenset({9, 19, 28, 38})

    # 3. White's finisher 43x3
    white_move = reconstruct_pawn_capture(after_reply, 43, 3)
    assert white_move == Move(
        path=(43, 32, 23, 14, 3), captures=(9, 19, 28, 38)
    )


# ---------------------------------------------------------------------------
# reconstruct_pawn_capture: equivalent trajectories (coup turc variant)
# ---------------------------------------------------------------------------


def test_reconstruct_equivalent_trajectories_accepted() -> None:
    """Dubois D5 white finisher 25x5 has two trajectories with identical captures.

    Position after sacrifice 37-31 and reply (27x20):
    W{24,25,31,41,42,43} - {31 captured?} ... actually we build a minimal
    repro: the 25x5 rafle on the central diagonal allows either
    25 → 14 → 3 → 12 → 23 → 14 → 5 (coup turc through 14)
    or 25 → 14 → 23 → 12 → 3 → 14 → 5,
    both capturing {8, 9, 10, 18, 19, 20}.

    The reconstructor should accept either (gameplay-equivalent).
    """
    state = GameState(
        white_men=frozenset({25}),
        black_men=frozenset({8, 9, 10, 18, 19, 20}),
        turn="white",
    )
    move = reconstruct_pawn_capture(state, 25, 5)
    assert move.from_square == 25
    assert move.to_square == 5
    assert set(move.captures) == {8, 9, 10, 18, 19, 20}


# ---------------------------------------------------------------------------
# reconstruct_pawn_capture: error paths
# ---------------------------------------------------------------------------


def test_reconstruct_empty_from_square_raises() -> None:
    state = GameState(white_men=frozenset({31}), black_men=frozenset({27}), turn="white")
    with pytest.raises(NotAManError, match="empty"):
        reconstruct_pawn_capture(state, from_sq=22, to_sq=31)


def test_reconstruct_from_king_raises() -> None:
    state = GameState(
        white_kings=frozenset({31}),
        black_men=frozenset({27}),
        turn="white",
    )
    with pytest.raises(NotAManError, match="king"):
        reconstruct_pawn_capture(state, from_sq=31, to_sq=22)


def test_reconstruct_no_such_rafle() -> None:
    """A man with no jump cannot magically land somewhere else."""
    state = GameState(white_men=frozenset({31}), black_men=frozenset({1}), turn="white")
    with pytest.raises(NoSuchRafleError):
        reconstruct_pawn_capture(state, from_sq=31, to_sq=5)


def test_reconstruct_wrong_landing_raises() -> None:
    """The man captures, but lands elsewhere than the requested square."""
    state = GameState(white_men=frozenset({31}), black_men=frozenset({27}), turn="white")
    # The only legal rafle is 31x22, requesting any other landing is invalid.
    with pytest.raises(NoSuchRafleError):
        reconstruct_pawn_capture(state, from_sq=31, to_sq=33)


# ---------------------------------------------------------------------------
# Coup turc: a man re-uses a previously visited empty square
# ---------------------------------------------------------------------------


def test_coup_turc_traversal_allowed() -> None:
    """A rafle may traverse the same square twice as long as captured pieces
    are not re-jumped (FMJD non-blowing rule)."""
    # Synthetic setup: a white man on 25 surrounded by enemies arranged so
    # that the maximal rafle revisits square 14 (the coup turc trajectory
    # of Dubois D5).
    state = GameState(
        white_men=frozenset({25}),
        black_men=frozenset({8, 9, 10, 18, 19, 20}),
        turn="white",
    )
    candidates = enumerate_pawn_captures(
        start=25, my_men=state.white_men, enemy_pieces=state.black_men
    )
    # At least one trajectory must visit square 14 more than once.
    assert any(path.count(14) >= 2 for path, _ in candidates)
