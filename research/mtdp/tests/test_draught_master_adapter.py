"""Contract tests for the optional downstream rules adapter."""
from __future__ import annotations

from types import SimpleNamespace

from pedagogy.game import initial_state, parse_fen
from research.mtdp.draught_master_adapter import DraughtMasterRules


class NativeState:
    def __init__(self, board, turn):
        self.board = board
        self.turn = turn


class NativeMove:
    def __init__(self, path, captures=()):
        self.path = list(path)
        self.captures = list(captures)


def test_conversion_and_quiet_move() -> None:
    def get_legal_moves(state):
        if state.turn == "white":
            return [NativeMove((32, 28))]
        return []

    def apply_move(state, move):
        board = state.board[:]
        board[move.path[-1]] = board[move.path[0]]
        board[move.path[0]] = 0
        return NativeState(board, "black")

    native = SimpleNamespace(
        EMPTY=0, WHITE_MAN=1, WHITE_KING=2,
        BLACK_MAN=3, BLACK_KING=4,
        GameState=NativeState,
        get_legal_moves=get_legal_moves,
        apply_move=apply_move,
    )
    adapter = DraughtMasterRules(native)
    before = initial_state()
    moves = adapter.legal_moves(before)
    assert len(moves) == 1
    assert moves[0].path == (32, 28)
    after = adapter.apply_move(before, moves[0])
    assert after.turn == "black"
    assert 32 not in after.white_men
    assert 28 in after.white_men
    assert len(after.black_men) == 20


def test_conversion_preserves_kings() -> None:
    native = SimpleNamespace(
        EMPTY=0, WHITE_MAN=1, WHITE_KING=2,
        BLACK_MAN=3, BLACK_KING=4,
        GameState=NativeState,
    )
    adapter = DraughtMasterRules(native)
    state = parse_fen("W:WK28,31:BK23,20")
    assert adapter._from_native(adapter._to_native(state)) == state
