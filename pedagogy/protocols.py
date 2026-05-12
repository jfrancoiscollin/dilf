"""Engine protocols.

The pedagogy module never embeds a draughts engine. Instead it consumes one
through these structural protocols, which the parent application
(``Ai-draught/backend/game_engine.py`` and ``scan_engine.py``) is expected to
implement, and which tests can satisfy with a tiny mock.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from .game import GameState, Move


@runtime_checkable
class EngineProtocol(Protocol):
    """Rules engine: legal move generation and move application.

    Implementations must respect FMJD rules: forced capture, maximum capture
    sequence, no second jump over the same piece, promotion only when a man
    *stops* on the promotion row.
    """

    def legal_moves(self, state: GameState) -> Sequence[Move]:
        """Return every legal move for ``state.turn``."""
        ...

    def apply_move(self, state: GameState, move: Move) -> GameState:
        """Return the new state after playing ``move`` from ``state``."""
        ...


@runtime_checkable
class ScanProtocol(Protocol):
    """Evaluation engine (typically Scan via Hub v2).

    Async signatures are used because the canonical implementation in the
    parent project talks to an external process over stdin/stdout. A
    synchronous mock can wrap return values in ``asyncio.sleep(0)``.
    """

    async def evaluate_pos(self, state: GameState) -> float:
        """Return Scan's evaluation in pawn units (positive = white-favorable)."""
        ...

    async def get_pv(self, state: GameState, depth: int = 10) -> list[Move]:
        """Return the principal variation from ``state`` up to ``depth`` plies."""
        ...
