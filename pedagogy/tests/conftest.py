"""Shared pytest fixtures and the in-process MockEngine.

The mock implements :class:`pedagogy.protocols.EngineProtocol` by reading a
precomputed table ``state -> list[Move]``. Tests build it with the helper
``mock_engine`` fixture below, optionally seeded with per-state move lists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import pytest

from pedagogy.game import GameState, Move


@dataclass
class MockEngine:
    """Deterministic, table-driven engine for tests.

    ``legal_table`` maps a :class:`GameState` to the legal moves the test
    wishes to expose. Any state not in the table yields an empty list.
    ``apply_table`` maps ``(state, move) -> state``; when missing,
    :meth:`apply_move` raises ``NotImplementedError`` so that tests can't
    accidentally rely on undefined behaviour.
    """

    legal_table: dict[GameState, list[Move]] = field(default_factory=dict)
    apply_table: dict[tuple[GameState, Move], GameState] = field(default_factory=dict)

    def legal_moves(self, state: GameState) -> Sequence[Move]:
        return list(self.legal_table.get(state, []))

    def apply_move(self, state: GameState, move: Move) -> GameState:
        try:
            return self.apply_table[(state, move)]
        except KeyError as exc:
            raise NotImplementedError(
                f"MockEngine.apply_move not configured for state={state!r}, move={move!r}"
            ) from exc

    # ---- Test helpers --------------------------------------------------

    def set_legal(self, state: GameState, moves: Sequence[Move]) -> None:
        self.legal_table[state] = list(moves)

    def set_apply(self, state: GameState, move: Move, result: GameState) -> None:
        self.apply_table[(state, move)] = result


@pytest.fixture
def mock_engine() -> MockEngine:
    return MockEngine()
