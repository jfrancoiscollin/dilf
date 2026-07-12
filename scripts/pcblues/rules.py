"""Full FMJD move generation and replay on top of pedagogy primitives.

``pedagogy.notation.dubois`` enumerates *per-piece* maximal rafles; this
module adds what full-game replay needs on top of it:

* the **global** prise-maximale rule (compare rafle lengths across every
  friendly man *and* king; quiet moves are illegal whenever any capture
  exists),
* quiet-move generation (men forward-only, kings sliding),
* promotion on rafle/move *end* (a man passing through the promotion row
  mid-rafle does not promote),
* ``apply_move`` producing the next :class:`GameState`,
* ``match_token`` resolving a PC Blues notation token ("45-40", "29x20",
  zero-padded "36x07") against the legal-move list — replay legality is the
  validation gate: a token that matches no legal move fails the sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

from pedagogy.game import GameState, Move, Side
from pedagogy.notation.dubois import (
    _diagonal_neighbours,
    enumerate_king_captures,
    enumerate_pawn_captures,
)

WHITE_PROMOTION_ROW = frozenset(range(1, 6))
BLACK_PROMOTION_ROW = frozenset(range(46, 51))

#: Quiet-move directions for men ("H" = toward row 1 = white's direction).
_MAN_DIRECTIONS: dict[Side, tuple[str, str]] = {
    "white": ("HG", "HD"),
    "black": ("BG", "BD"),
}
_ALL_DIRECTIONS = ("HG", "HD", "BG", "BD")


class IllegalMoveError(ValueError):
    """Token does not correspond to any legal move in the position."""


class AmbiguousMoveError(ValueError):
    """Token matches several legal moves with different capture sets."""


@dataclass(frozen=True)
class ResolvedMove:
    """A move matched against the legal-move list, ready to apply."""

    move: Move
    is_king_move: bool


def _other(side: Side) -> Side:
    return "black" if side == "white" else "white"


def _king_quiet_moves(state: GameState, sq: int) -> list[Move]:
    moves: list[Move] = []
    occupied = state.all_pieces
    for direction in _ALL_DIRECTIONS:
        cur = sq
        while True:
            nxt = _diagonal_neighbours(cur)[direction]
            if nxt is None or nxt in occupied:
                break
            moves.append(Move(path=(sq, nxt), captures=()))
            cur = nxt
    return moves


def legal_moves(state: GameState) -> list[ResolvedMove]:
    """Every legal move for the side to move, prise-maximale enforced globally."""
    side = state.turn
    men = state.men_of(side)
    kings = state.kings_of(side)
    mine = men | kings
    enemy = state.pieces_of(_other(side))

    captures: list[tuple[Move, bool]] = []
    for sq in men:
        for path, caps in enumerate_pawn_captures(sq, mine, enemy):
            captures.append((Move(path=path, captures=tuple(sorted(caps))), False))
    for sq in kings:
        for path, caps in enumerate_king_captures(sq, mine, enemy):
            captures.append((Move(path=path, captures=tuple(sorted(caps))), True))

    if captures:
        best = max(len(m.captures) for m, _ in captures)
        return [
            ResolvedMove(move=m, is_king_move=k)
            for m, k in captures
            if len(m.captures) == best
        ]

    quiets: list[ResolvedMove] = []
    occupied = state.all_pieces
    for sq in men:
        for direction in _MAN_DIRECTIONS[side]:
            nxt = _diagonal_neighbours(sq)[direction]
            if nxt is not None and nxt not in occupied:
                quiets.append(
                    ResolvedMove(Move(path=(sq, nxt), captures=()), is_king_move=False)
                )
    for sq in kings:
        for mv in _king_quiet_moves(state, sq):
            quiets.append(ResolvedMove(mv, is_king_move=True))
    return quiets


def apply_move(state: GameState, resolved: ResolvedMove) -> GameState:
    """Play ``resolved`` and return the next position (turn toggled)."""
    side = state.turn
    move = resolved.move
    frm, to = move.from_square, move.to_square
    caps = set(move.captures)

    white_men = set(state.white_men) - caps
    white_kings = set(state.white_kings) - caps
    black_men = set(state.black_men) - caps
    black_kings = set(state.black_kings) - caps

    men, kings = (white_men, white_kings) if side == "white" else (black_men, black_kings)
    promotion_row = WHITE_PROMOTION_ROW if side == "white" else BLACK_PROMOTION_ROW

    if resolved.is_king_move:
        kings.discard(frm)
        kings.add(to)
    else:
        men.discard(frm)
        if to in promotion_row:
            kings.add(to)
        else:
            men.add(to)

    return GameState(
        white_men=frozenset(white_men),
        white_kings=frozenset(white_kings),
        black_men=frozenset(black_men),
        black_kings=frozenset(black_kings),
        turn=_other(side),
    )


class RulesEngine:
    """:class:`pedagogy.protocols.EngineProtocol` adapter over this module."""

    def legal_moves(self, state: GameState) -> list[Move]:
        return [r.move for r in legal_moves(state)]

    def apply_move(self, state: GameState, move: Move) -> GameState:
        is_king = move.from_square in state.kings_of(state.turn)
        return apply_move(state, ResolvedMove(move=move, is_king_move=is_king))


def match_token(
    state: GameState, frm: int, to: int, is_capture: bool
) -> ResolvedMove:
    """Resolve a from/to notation token against the legal moves of ``state``.

    PC Blues capture notation gives endpoints only ("29x20" may be a triple
    rafle). Several maximal rafles sharing endpoints but capturing the same
    squares are interchangeable — the first is returned. Different capture
    sets raise :class:`AmbiguousMoveError` (quarantine upstream).
    """
    legal = legal_moves(state)
    matches = [
        r
        for r in legal
        if r.move.from_square == frm
        and r.move.to_square == to
        and r.move.is_capture == is_capture
    ]
    if not matches:
        detail = "capture" if is_capture else "quiet move"
        forced = ""
        if not is_capture and any(r.move.is_capture for r in legal):
            forced = " (a capture is mandatory here)"
        raise IllegalMoveError(f"no legal {detail} {frm}->{to}{forced}")
    capture_sets = {frozenset(r.move.captures) for r in matches}
    if len(capture_sets) > 1:
        raise AmbiguousMoveError(
            f"{frm}x{to}: {len(matches)} maximal rafles with different"
            f" capture sets {sorted(map(sorted, capture_sets))}"
        )
    return matches[0]
