"""Optional adapter to draught-master/backend/game_engine.py.

The downstream repository is an OPTIONAL runtime dependency. Import this
module without installing draught-master; create_engine() imports it lazily.
No modifications are made to either project's stable public APIs.
"""
from __future__ import annotations

from typing import Any

from pedagogy.game import GameState, Move


class DraughtMasterRules:
    def __init__(self, rules: Any) -> None:
        self._rules = rules

    def _to_native(self, state: GameState) -> Any:
        r = self._rules
        board = [r.EMPTY] * 51
        for squares, piece in (
            (state.white_men, r.WHITE_MAN),
            (state.white_kings, r.WHITE_KING),
            (state.black_men, r.BLACK_MAN),
            (state.black_kings, r.BLACK_KING),
        ):
            for sq in squares:
                board[sq] = piece
        return r.GameState(board=board, turn=state.turn)

    def _from_native(self, state: Any) -> GameState:
        r = self._rules
        board = state.board
        return GameState(
            white_men=frozenset(s for s in range(1, 51) if board[s] == r.WHITE_MAN),
            white_kings=frozenset(s for s in range(1, 51) if board[s] == r.WHITE_KING),
            black_men=frozenset(s for s in range(1, 51) if board[s] == r.BLACK_MAN),
            black_kings=frozenset(s for s in range(1, 51) if board[s] == r.BLACK_KING),
            turn=state.turn,
        )

    def legal_moves(self, state: GameState) -> list[Move]:
        native = self._to_native(state)
        moves = []
        for move in self._rules.get_legal_moves(native):
            path = tuple(move.path)
            captures = tuple(move.captures)
            is_man = path[0] in state.men_of(state.turn)
            promotion_row = range(1, 6) if state.turn == "white" else range(46, 51)
            moves.append(Move(
                path=path,
                captures=captures,
                promotion=is_man and path[-1] in promotion_row,
            ))
        return moves

    def apply_move(self, state: GameState, move: Move) -> GameState:
        # This method expects a move already selected from legal_moves.
        native = self._to_native(state)
        legal = self._rules.get_legal_moves(native)
        matches = [
            candidate for candidate in legal
            if tuple(candidate.path) == move.path
            and set(candidate.captures) == set(move.captures)
        ]
        if len(matches) != 1:
            raise ValueError(f"Move is not uniquely legal: {move}")
        return self._from_native(self._rules.apply_move(native, matches[0]))


def create_engine() -> DraughtMasterRules:
    """Return rules adapter if draught-master/backend is on Python import path."""
    try:
        from backend import game_engine
    except ImportError as exc:
        raise RuntimeError(
            "Install draught-master or add its repository root to PYTHONPATH"
        ) from exc
    return DraughtMasterRules(game_engine)
