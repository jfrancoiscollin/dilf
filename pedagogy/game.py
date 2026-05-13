"""Core game data model for the pedagogy module.

This module defines the *internal* representation of a draughts position
(``GameState``) and a move (``Move``). External draughts engines (Scan,
KingsRow, an in-house Python engine, ...) are expected to either produce
these types directly or adapt to them at the boundary.

Board geometry (FMJD 10x10, French/international rules):

* 50 dark squares numbered 1..50, read left-to-right and top-to-bottom from
  the Black player's point of view. Square 1 sits in the top-left.
* Row 1 = squares 1..5, row 2 = 6..10, ..., row 10 = 46..50.
* Square 1 is a dark square; columns are 1..10 within each row.
* White pieces move toward row 1 (decreasing square numbers along diagonals),
  black pieces toward row 10. Promotion rows: white = {1..5}, black = {46..50}.

The FEN format we accept and produce follows the PDN convention used by
international draughts servers, e.g.::

    "W:W31,32,33,K38:B1,2,K7"

* Turn marker ``W`` or ``B`` prefixes the string.
* Each side lists squares occupied by its pieces, men as plain integers and
  kings prefixed with ``K``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

Side = Literal["white", "black"]
Square = int  # 1..50

#: All legal square numbers.
BOARD_SQUARES: frozenset[int] = frozenset(range(1, 51))


@dataclass(frozen=True, slots=True)
class Move:
    """A draughts half-move.

    ``path`` is the ordered list of squares the moving piece visits, starting
    from the origin and ending on the landing square. ``captures`` is the
    (unordered) tuple of squares of captured pieces — those pieces are
    physically removed only at the end of the sequence (FMJD "blowing" rule
    is not used: a captured piece may not be jumped a second time, but the
    moving piece may pass over its now-empty square again, which is the
    signature of the *coup turc*).

    A move with no captures has ``len(path) == 2`` and ``captures == ()``.
    """

    path: tuple[Square, ...]
    captures: tuple[Square, ...] = ()
    promotion: bool = False

    def __post_init__(self) -> None:
        if len(self.path) < 2:
            raise ValueError(f"Move.path must have at least 2 squares, got {self.path!r}")
        for sq in self.path:
            if sq not in BOARD_SQUARES:
                raise ValueError(f"Move.path contains invalid square {sq}")
        for sq in self.captures:
            if sq not in BOARD_SQUARES:
                raise ValueError(f"Move.captures contains invalid square {sq}")

    @property
    def from_square(self) -> Square:
        return self.path[0]

    @property
    def to_square(self) -> Square:
        return self.path[-1]

    @property
    def is_capture(self) -> bool:
        return bool(self.captures)


def notation(move: Move) -> str:
    """Render a move in standard PDN-like notation.

    Non-capture: ``"<from>-<to>"`` (e.g. ``"32-28"``).
    Capture: ``"<sq0>x<sq1>x<sq2>..."`` along the path (e.g. ``"40x29x18"``).
    """
    if move.is_capture:
        return "x".join(str(sq) for sq in move.path)
    return f"{move.from_square}-{move.to_square}"


@dataclass(frozen=True, slots=True)
class GameState:
    """Immutable snapshot of a draughts position.

    Pieces are stored as ``frozenset`` of square numbers. Sets of any two
    fields are disjoint (a square is occupied by at most one piece).
    ``turn`` is the side to move.
    """

    white_men: frozenset[Square] = field(default_factory=frozenset)
    white_kings: frozenset[Square] = field(default_factory=frozenset)
    black_men: frozenset[Square] = field(default_factory=frozenset)
    black_kings: frozenset[Square] = field(default_factory=frozenset)
    turn: Side = "white"

    def __post_init__(self) -> None:
        all_sets = (self.white_men, self.white_kings, self.black_men, self.black_kings)
        for s in all_sets:
            for sq in s:
                if sq not in BOARD_SQUARES:
                    raise ValueError(f"GameState contains invalid square {sq}")
        # Pairwise disjointness
        seen: set[int] = set()
        for s in all_sets:
            inter = seen & s
            if inter:
                raise ValueError(f"GameState has square(s) {sorted(inter)} occupied twice")
            seen |= s
        if self.turn not in ("white", "black"):
            raise ValueError(f"GameState.turn must be 'white' or 'black', got {self.turn!r}")

    # ---- Aggregate accessors ----

    @property
    def all_pieces(self) -> frozenset[Square]:
        return self.white_men | self.white_kings | self.black_men | self.black_kings

    @property
    def empty_squares(self) -> frozenset[Square]:
        return BOARD_SQUARES - self.all_pieces

    def pieces_of(self, side: Side) -> frozenset[Square]:
        """All squares (men + kings) occupied by ``side``."""
        if side == "white":
            return self.white_men | self.white_kings
        return self.black_men | self.black_kings

    def men_of(self, side: Side) -> frozenset[Square]:
        return self.white_men if side == "white" else self.black_men

    def kings_of(self, side: Side) -> frozenset[Square]:
        return self.white_kings if side == "white" else self.black_kings

    def piece_at(self, sq: Square) -> tuple[Side, str] | None:
        """Return ``(side, kind)`` for the piece on ``sq``, or ``None`` if empty.

        ``kind`` is ``"man"`` or ``"king"``.
        """
        if sq in self.white_men:
            return ("white", "man")
        if sq in self.white_kings:
            return ("white", "king")
        if sq in self.black_men:
            return ("black", "man")
        if sq in self.black_kings:
            return ("black", "king")
        return None


# ---------------------------------------------------------------------------
# FEN parsing / serialization
# ---------------------------------------------------------------------------


def _parse_piece_list(token: str, expected_prefix: str) -> tuple[frozenset[int], frozenset[int]]:
    """Parse a ``W...`` or ``B...`` piece list. Returns (men, kings)."""
    if not token:
        raise ValueError(f"Empty FEN piece list (expected prefix {expected_prefix!r})")
    if token[0].upper() != expected_prefix:
        raise ValueError(
            f"FEN piece list should start with {expected_prefix!r}, got {token!r}"
        )
    rest = token[1:].strip()
    men: set[int] = set()
    kings: set[int] = set()
    if not rest:
        return frozenset(), frozenset()
    for raw in rest.split(","):
        tok = raw.strip()
        if not tok:
            continue
        is_king = tok[0].upper() == "K"
        body = tok[1:] if is_king else tok
        try:
            sq = int(body)
        except ValueError as exc:
            raise ValueError(f"Invalid square in FEN: {raw!r}") from exc
        if sq not in BOARD_SQUARES:
            raise ValueError(f"FEN square out of range: {sq}")
        (kings if is_king else men).add(sq)
    return frozenset(men), frozenset(kings)


def parse_fen(fen: str) -> GameState:
    """Parse a PDN-style FEN string into a :class:`GameState`.

    Raises ``ValueError`` on malformed input.
    """
    parts = [p for p in fen.strip().split(":") if p != ""]
    if len(parts) != 3:
        raise ValueError(f"FEN must have exactly 3 colon-separated parts, got {fen!r}")
    turn_token, white_token, black_token = parts
    if turn_token.upper() not in ("W", "B"):
        raise ValueError(f"FEN turn marker must be 'W' or 'B', got {turn_token!r}")
    turn: Side = "white" if turn_token.upper() == "W" else "black"
    white_men, white_kings = _parse_piece_list(white_token, "W")
    black_men, black_kings = _parse_piece_list(black_token, "B")
    return GameState(
        white_men=white_men,
        white_kings=white_kings,
        black_men=black_men,
        black_kings=black_kings,
        turn=turn,
    )


def state_to_fen(state: GameState) -> str:
    """Serialize a :class:`GameState` to a PDN-style FEN string."""
    turn_marker = "W" if state.turn == "white" else "B"
    white_parts: list[str] = [f"K{sq}" for sq in sorted(state.white_kings)]
    white_parts += [str(sq) for sq in sorted(state.white_men)]
    black_parts: list[str] = [f"K{sq}" for sq in sorted(state.black_kings)]
    black_parts += [str(sq) for sq in sorted(state.black_men)]
    return f"{turn_marker}:W{','.join(white_parts)}:B{','.join(black_parts)}"


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------


def initial_state() -> GameState:
    """Return the FMJD starting position (white to move, 20 men each)."""
    return GameState(
        white_men=frozenset(range(31, 51)),
        white_kings=frozenset(),
        black_men=frozenset(range(1, 21)),
        black_kings=frozenset(),
        turn="white",
    )


def empty_state(turn: Side = "white") -> GameState:
    """Return an empty board with the given side to move."""
    return GameState(turn=turn)


def state_from_pieces(
    white_men: Iterable[int] = (),
    white_kings: Iterable[int] = (),
    black_men: Iterable[int] = (),
    black_kings: Iterable[int] = (),
    turn: Side = "white",
) -> GameState:
    """Build a :class:`GameState` from any iterables of square numbers."""
    return GameState(
        white_men=frozenset(white_men),
        white_kings=frozenset(white_kings),
        black_men=frozenset(black_men),
        black_kings=frozenset(black_kings),
        turn=turn,
    )
