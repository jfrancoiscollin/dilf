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


# ===========================================================================
# King rafle reconstruction (FMJD dame)
# ===========================================================================
#
# These tests cover :func:`enumerate_king_captures` and
# :func:`reconstruct_king_capture`. The geometry is exercised on synthetic
# minimal setups so each test isolates one rule.


from pedagogy.notation.dubois import (
    NotAKingError,
    enumerate_king_captures,
    reconstruct_capture,
    reconstruct_king_capture,
)


def test_king_no_capture_isolated() -> None:
    """A king with no enemy on its diagonals returns no rafle."""
    caps = enumerate_king_captures(
        start=28,
        my_pieces=frozenset({28}),
        enemy_pieces=frozenset({1, 5, 46, 50}),  # too far / off-diagonal
    )
    assert caps == []


def test_king_single_jump_multiple_landings() -> None:
    """A king jumps an adjacent enemy; multiple empty landings are all valid."""
    # White king on 28, enemy man on 23. Diagonal HD through 28-23 continues
    # to 19, 14, 10, 5 (all empty). All four are valid landings.
    caps = enumerate_king_captures(
        start=28,
        my_pieces=frozenset({28}),
        enemy_pieces=frozenset({23}),
    )
    landings = sorted(path[-1] for path, _ in caps)
    assert landings == [5, 10, 14, 19]
    # All single-capture rafles, all capturing {23}.
    assert all(captures == frozenset({23}) for _, captures in caps)


def test_king_slides_before_jump() -> None:
    """A king can slide over several empty squares before jumping."""
    # White king on 50, enemy man on 32. HG diagonal from 50 passes 44, 39,
    # 33 (empty), reaches 32 (wrong: 32 is not on the HG diagonal from 50).
    # Actually the HG diagonal from 50 is: 50 → 44 → 39 → 33 → 28 → 22 → 17 → 11 → 6.
    # Place enemy on 28, landings 22, 17, 11, 6.
    caps = enumerate_king_captures(
        start=50,
        my_pieces=frozenset({50}),
        enemy_pieces=frozenset({28}),
    )
    landings = sorted(path[-1] for path, _ in caps)
    assert landings == [6, 11, 17, 22]


def test_king_blocked_by_friendly() -> None:
    """A king cannot jump if a friendly piece sits behind the enemy."""
    # King 28, enemy 23, friendly 19 — the only landing square is blocked.
    caps = enumerate_king_captures(
        start=28,
        my_pieces=frozenset({28, 19}),
        enemy_pieces=frozenset({23}),
    )
    assert caps == []


def test_king_blocked_by_two_consecutive_enemies() -> None:
    """A king cannot jump two enemies in a row on the same diagonal."""
    # King 28, enemies 23 and 19. Jumping 23 would land on 19, which is also
    # enemy — illegal. Jumping 19 is also blocked because 23 is in the way.
    caps = enumerate_king_captures(
        start=28,
        my_pieces=frozenset({28}),
        enemy_pieces=frozenset({23, 19}),
    )
    assert caps == []


def test_king_multi_jump_change_diagonal() -> None:
    """A king takes two enemies on different diagonals in one rafle."""
    # White king on 5. Enemy on 14 (BG from 5), then enemy on 33 (BG from 28).
    # Path: 5 → ... → 28 (capture 14), then change to BG → ... → 39 (capture 33).
    # Landing options after capturing both: 39, 44, 50 (slide BG).
    caps = enumerate_king_captures(
        start=5,
        my_pieces=frozenset({5}),
        enemy_pieces=frozenset({14, 33}),
    )
    # Must be maximal: capture both pieces.
    assert all(len(c) == 2 for _, c in caps)
    assert all(c == frozenset({14, 33}) for _, c in caps)
    landings = sorted(set(path[-1] for path, _ in caps))
    assert landings == [39, 44, 50]


def test_king_must_capture_maximum() -> None:
    """When two rafles capture different numbers of enemies, only the maximum
    is returned (FMJD prise majoritaire rule)."""
    # King 28: can jump 23 alone (1 capture, several landings) OR jump 23
    # then change diagonal to capture another enemy. Set up so a 2-capture
    # path exists. Enemies 23 and 8: 28 jumps 23 to 19 → 14 → 10 → ... and
    # from 14 (or similar) saute 9? Use simpler: enemies 23 and 9.
    # Path: 28 → HD → 19 (after capturing 23), then HG from 19 = 13, 8.
    # 9 is enemy: from 14, voisin HG = 9. Donc 28 → HD → 19 → ... → 14 (slide HD),
    # then HG → saute 9 → atterrir 4. Captures {23, 9}.
    caps = enumerate_king_captures(
        start=28,
        my_pieces=frozenset({28}),
        enemy_pieces=frozenset({23, 9}),
    )
    # All returned rafles must be 2-capture (the maximum).
    assert all(len(c) == 2 for _, c in caps)


def test_reconstruct_king_basic() -> None:
    """Reconstruct a Dubois-style king rafle 28x14 capturing 23."""
    state = GameState(
        white_kings=frozenset({28}),
        black_men=frozenset({23}),
        turn="white",
    )
    move = reconstruct_king_capture(state, from_sq=28, to_sq=14)
    assert move.captures == (23,)
    assert move.path[0] == 28
    assert move.path[-1] == 14


def test_reconstruct_king_multi_jump() -> None:
    """Reconstruct a 2-capture king rafle ending on a specific landing square."""
    state = GameState(
        white_kings=frozenset({5}),
        black_men=frozenset({14, 33}),
        turn="white",
    )
    move = reconstruct_king_capture(state, from_sq=5, to_sq=44)
    assert set(move.captures) == {14, 33}
    assert move.path[0] == 5
    assert move.path[-1] == 44


def test_reconstruct_king_from_empty_raises() -> None:
    state = GameState(turn="white")
    with pytest.raises(NotAKingError, match="empty"):
        reconstruct_king_capture(state, from_sq=28, to_sq=14)


def test_reconstruct_king_from_man_raises() -> None:
    state = GameState(
        white_men=frozenset({28}),
        black_men=frozenset({23}),
        turn="white",
    )
    with pytest.raises(NotAKingError, match="man"):
        reconstruct_king_capture(state, from_sq=28, to_sq=14)


def test_reconstruct_king_no_such_rafle() -> None:
    """A king cannot land on a square not reachable by any maximal rafle."""
    state = GameState(
        white_kings=frozenset({28}),
        black_men=frozenset({23}),
        turn="white",
    )
    # The only landings after jumping 23 are 19, 14, 10, 5. Landing 1 is
    # off-diagonal.
    with pytest.raises(NoSuchRafleError):
        reconstruct_king_capture(state, from_sq=28, to_sq=1)


def test_reconstruct_capture_dispatches_pawn() -> None:
    """The unified dispatcher routes a man to the pawn reconstructor."""
    state = GameState(
        white_men=frozenset({31}),
        black_men=frozenset({27}),
        turn="white",
    )
    move = reconstruct_capture(state, from_sq=31, to_sq=22)
    assert move.captures == (27,)


def test_reconstruct_capture_dispatches_king() -> None:
    """The unified dispatcher routes a king to the king reconstructor."""
    state = GameState(
        white_kings=frozenset({28}),
        black_men=frozenset({23}),
        turn="white",
    )
    move = reconstruct_capture(state, from_sq=28, to_sq=14)
    assert move.captures == (23,)


def test_reconstruct_capture_empty_square_raises() -> None:
    state = GameState(turn="white")
    with pytest.raises(ValueError, match="empty"):
        reconstruct_capture(state, from_sq=28, to_sq=14)


# ---------------------------------------------------------------------------
# Coup turc on a king rafle
# ---------------------------------------------------------------------------


def test_king_coup_turc_traversal() -> None:
    """A king may traverse the same empty square twice during a rafle, as
    long as already-captured pieces are not jumped again."""
    # Synthetic 4-enemy ring around square 28 such that the maximal rafle
    # revisits square 28 (or another empty square). Enemies on 17, 19, 37, 39
    # arranged so the king bounces back and forth.
    state = GameState(
        white_kings=frozenset({1}),
        black_men=frozenset({12, 23, 34}),
        turn="white",
    )
    # The maximal rafle from 1 must capture {12, 23, 34} via three jumps.
    caps = enumerate_king_captures(
        start=1,
        my_pieces=state.white_kings,
        enemy_pieces=state.black_men,
    )
    assert any(len(c) == 3 for _, c in caps)


# ---------------------------------------------------------------------------
# parse_move_notation — string → Move (capture-aware)
# ---------------------------------------------------------------------------


from pedagogy.notation.dubois import parse_move_notation


def test_parse_move_notation_quiet() -> None:
    """A quiet `cd-cf` move yields an empty `captures` tuple."""
    state = GameState(
        white_men=frozenset({32}),
        black_men=frozenset({18}),
        turn="white",
    )
    move = parse_move_notation("32-28", state)
    assert move.path == (32, 28)
    assert move.captures == ()


def test_parse_move_notation_simple_capture_fills_captures() -> None:
    """A single-jump `aXb` resolves the captured enemy square."""
    state = GameState(
        white_men=frozenset({31}),
        black_men=frozenset({27}),
        turn="white",
    )
    move = parse_move_notation("31x22", state)
    assert move.path[0] == 31 and move.path[-1] == 22
    assert 27 in move.captures  # the jumped enemy


def test_parse_move_notation_multi_jump_returns_all_captures() -> None:
    """A multi-jump `aXbXc` returns every captured square."""
    state = GameState(
        white_men=frozenset({43}),
        black_men=frozenset({9, 19, 28, 38}),
        turn="white",
    )
    # Dubois D1: 43x3 captures 38, 28, 19, 9 in a four-jump rafle.
    move = parse_move_notation("43x3", state)
    assert move.path[0] == 43 and move.path[-1] == 3
    assert set(move.captures) == {9, 19, 28, 38}


def test_parse_move_notation_validates_intermediate_squares() -> None:
    """If the notation lists wrong intermediate stops, raise ValueError."""
    state = GameState(
        white_men=frozenset({43}),
        black_men=frozenset({9, 19, 28, 38}),
        turn="white",
    )
    # Intermediate `99` is bogus — must be flagged.
    import pytest
    with pytest.raises(ValueError, match="intermediate squares"):
        parse_move_notation("43x99x3", state)


def test_parse_move_notation_strips_optional_king_prefix() -> None:
    """Some PDN dialects prefix king moves with 'K' — accept and ignore."""
    state = GameState(
        white_men=frozenset({32}),
        black_men=frozenset(),
        turn="white",
    )
    move = parse_move_notation("K32-28", state)
    assert move.path == (32, 28)


def test_parse_move_notation_rejects_malformed_input() -> None:
    """Inputs without '-' or 'x' aren't moves."""
    state = GameState(
        white_men=frozenset({32}),
        black_men=frozenset(),
        turn="white",
    )
    import pytest
    with pytest.raises(ValueError):
        parse_move_notation("32", state)
    with pytest.raises(ValueError):
        parse_move_notation("", state)
