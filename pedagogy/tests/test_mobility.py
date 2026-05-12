"""Tests for mobility helpers, driven by the in-process MockEngine."""

from __future__ import annotations

from pedagogy.features.mobility import (
    count_legal_moves,
    hanging_pieces,
    threatened_captures,
)
from pedagogy.game import Move, state_from_pieces

from .conftest import MockEngine


def test_count_legal_moves_delegates_to_engine() -> None:
    state = state_from_pieces(white_men=[31, 32], black_men=[1, 2], turn="white")
    flipped = state_from_pieces(white_men=[31, 32], black_men=[1, 2], turn="black")
    engine = MockEngine()
    engine.set_legal(state, [Move(path=(31, 27)), Move(path=(32, 28))])
    engine.set_legal(flipped, [Move(path=(1, 6))])

    assert count_legal_moves(state, "white", engine) == 2
    assert count_legal_moves(state, "black", engine) == 1


def test_threatened_captures_filters_quiet_moves() -> None:
    state = state_from_pieces(white_men=[31, 33], black_men=[28], turn="white")
    engine = MockEngine()
    engine.set_legal(
        state,
        [
            Move(path=(31, 27)),  # quiet
            Move(path=(33, 22), captures=(28,)),  # capture
        ],
    )
    captures = threatened_captures(state, "white", engine)
    assert len(captures) == 1
    assert captures[0].captures == (28,)


def test_hanging_pieces_lists_own_pieces_capturable_by_opponent() -> None:
    # Black to move; the white piece on 28 is capturable via 23x32 by black 23.
    state = state_from_pieces(white_men=[28], black_men=[23], turn="black")
    flipped_black = state_from_pieces(white_men=[28], black_men=[23], turn="black")
    engine = MockEngine()
    engine.set_legal(flipped_black, [Move(path=(23, 32), captures=(28,))])
    # Hanging detection asks "what if the opponent moved" -> we flip turn.
    assert hanging_pieces(state, "white", engine) == [28]
    # The black piece is not under any white threat (no legal moves wired).
    assert hanging_pieces(state, "black", engine) == []


def test_hanging_pieces_filters_captures_of_squares_not_owned() -> None:
    # An engine that wrongly reports a non-existent capture should never make
    # a piece "hang" if the captured square is not owned by `side`.
    state = state_from_pieces(white_men=[28], black_men=[23], turn="white")
    flipped_white = state_from_pieces(white_men=[28], black_men=[23], turn="white")
    engine = MockEngine()
    # Fake: white pretends to capture its own 28 -> filter must drop it.
    engine.set_legal(flipped_white, [Move(path=(28, 32), captures=(28,))])
    # black has no moves wired, so its captures of black pieces yield nothing.
    flipped_black = state_from_pieces(white_men=[28], black_men=[23], turn="black")
    engine.set_legal(flipped_black, [])
    assert hanging_pieces(state, "black", engine) == []
