"""Tests for the core game data model: GameState, Move, FEN round-trips."""

from __future__ import annotations

import pytest

from pedagogy.game import (
    BOARD_SQUARES,
    GameState,
    Move,
    empty_state,
    initial_state,
    notation,
    parse_fen,
    state_from_pieces,
    state_to_fen,
)


def test_initial_state_has_20_men_per_side() -> None:
    s = initial_state()
    assert len(s.white_men) == 20
    assert len(s.black_men) == 20
    assert s.white_kings == frozenset()
    assert s.black_kings == frozenset()
    assert s.turn == "white"
    assert s.white_men == frozenset(range(31, 51))
    assert s.black_men == frozenset(range(1, 21))


def test_board_squares_constant() -> None:
    assert len(BOARD_SQUARES) == 50
    assert min(BOARD_SQUARES) == 1
    assert max(BOARD_SQUARES) == 50


def test_state_pieces_of_and_men_kings_helpers() -> None:
    s = state_from_pieces(white_men=[31], white_kings=[28], black_men=[1])
    assert s.pieces_of("white") == frozenset({28, 31})
    assert s.pieces_of("black") == frozenset({1})
    assert s.men_of("white") == frozenset({31})
    assert s.kings_of("white") == frozenset({28})
    assert s.all_pieces == frozenset({1, 28, 31})
    assert 50 in s.empty_squares
    assert 1 not in s.empty_squares


def test_state_piece_at_returns_side_and_kind() -> None:
    s = state_from_pieces(white_men=[31], white_kings=[28], black_men=[1], black_kings=[2])
    assert s.piece_at(31) == ("white", "man")
    assert s.piece_at(28) == ("white", "king")
    assert s.piece_at(1) == ("black", "man")
    assert s.piece_at(2) == ("black", "king")
    assert s.piece_at(50) is None


def test_state_rejects_invalid_square() -> None:
    with pytest.raises(ValueError):
        state_from_pieces(white_men=[0])
    with pytest.raises(ValueError):
        state_from_pieces(white_men=[51])


def test_state_rejects_overlapping_pieces() -> None:
    with pytest.raises(ValueError):
        state_from_pieces(white_men=[31], black_men=[31])


def test_state_rejects_invalid_turn() -> None:
    with pytest.raises(ValueError):
        GameState(turn="grey")  # type: ignore[arg-type]


def test_move_validation_rejects_short_path() -> None:
    with pytest.raises(ValueError):
        Move(path=(31,))


def test_move_notation_quiet_vs_capture() -> None:
    quiet = Move(path=(32, 28))
    capture = Move(path=(40, 29, 18), captures=(34, 23))
    assert notation(quiet) == "32-28"
    assert notation(capture) == "40x29x18"


def test_fen_round_trip_initial_state() -> None:
    s = initial_state()
    fen = state_to_fen(s)
    parsed = parse_fen(fen)
    assert parsed == s
    assert state_to_fen(parsed) == fen


def test_fen_parses_kings_and_turn() -> None:
    fen = "B:W31,K28:B1,K2"
    s = parse_fen(fen)
    assert s.turn == "black"
    assert s.white_men == frozenset({31})
    assert s.white_kings == frozenset({28})
    assert s.black_men == frozenset({1})
    assert s.black_kings == frozenset({2})


def test_fen_rejects_malformed_input() -> None:
    with pytest.raises(ValueError):
        parse_fen("W:W31")  # missing black part
    with pytest.raises(ValueError):
        parse_fen("X:W31:B1")  # bad turn
    with pytest.raises(ValueError):
        parse_fen("W:Z31:B1")  # bad white prefix
    with pytest.raises(ValueError):
        parse_fen("W:W99:B1")  # out-of-range square


def test_empty_state_has_no_pieces() -> None:
    s = empty_state(turn="black")
    assert s.all_pieces == frozenset()
    assert s.turn == "black"
    assert len(s.empty_squares) == 50
