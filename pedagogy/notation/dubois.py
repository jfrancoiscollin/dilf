"""Reconstruct rafle (multi-jump capture) trajectories from Dubois short notation.

In Dubois pedagogical books, a capture sequence is written ``aXb`` where ``a``
is the departure square and ``b`` is the final landing square. The intermediate
squares and the captured pieces are left **implicit** — the reader is expected
to reconstruct them geometrically from the position.

A rafle is **not** a straight-line slide; the moving pawn can change diagonal
at each jump. For example, in the canonical Dubois D1 (Apprentissage
Combinaisons, ch. 1, p. 6), the rafle ``17x28`` is the trajectory
``17 → 26 → 37 → 28`` (BG, BD, HD), capturing the pawns on 21, 31 and 32.

This module reconstructs the full :class:`pedagogy.game.Move` from the short
``(from_sq, to_sq)`` notation by enumerating every legal pawn rafle from
``from_sq`` and retaining the one (or those) ending on ``to_sq`` with the
maximum number of captures (FMJD prise majoritaire rule).

**Pawns only.** This first version handles **men**, not kings. King captures
follow a different geometry (sliding any distance along a diagonal, jumping
over a single enemy piece, landing any distance beyond it) and require a
separate implementation. Passing a square occupied by a king as ``from_sq``
raises :class:`NotAManError`.

**Coup turc.** A pawn may traverse the same empty square twice during one
rafle, provided it does not re-jump a captured piece (FMJD non-blowing rule).
The enumerator supports this.

**Equivalent trajectories.** Two different paths from ``from_sq`` to ``to_sq``
that capture **exactly the same set of enemy pieces** are gameplay-equivalent.
:func:`reconstruct_pawn_capture` returns the first of these; if two paths
ending on ``to_sq`` differ by their capture set, the rafle is genuinely
ambiguous and :class:`AmbiguousRafleError` is raised.
"""

from __future__ import annotations

from pedagogy.game import GameState, Move, Side, Square


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NotAManError(ValueError):
    """Raised when ``from_sq`` is not occupied by a man (or is empty).

    Kings have a different jump geometry and are out of scope for this
    pawn-only reconstructor.
    """


class NoSuchRafleError(ValueError):
    """Raised when no maximal rafle from ``from_sq`` ends on ``to_sq``."""


class AmbiguousRafleError(ValueError):
    """Raised when several rafles from ``from_sq`` to ``to_sq`` capture
    **different** sets of pieces (genuine gameplay ambiguity, not just
    a coup-turc trajectory variant)."""


# ---------------------------------------------------------------------------
# Board geometry — diagonal neighbours
# ---------------------------------------------------------------------------


def _case_to_rc(c: Square) -> tuple[int, int]:
    """Convert FMJD square number 1..50 to (row, visual_col), both 0-indexed.

    Row 0 is the top row (squares 1..5), row 9 the bottom row (squares 46..50).
    Visual column 0 is the leftmost column.
    """
    row = (c - 1) // 5
    col_index = (c - 1) % 5
    if row % 2 == 0:
        col = 1 + 2 * col_index   # row 0, 2, 4...: dark squares at cols 1,3,5,7,9
    else:
        col = 2 * col_index       # row 1, 3, 5...: dark squares at cols 0,2,4,6,8
    return (row, col)


def _rc_to_case(row: int, col: int) -> Square | None:
    """Inverse of :func:`_case_to_rc`. Returns None if off-board or light square."""
    if not (0 <= row <= 9 and 0 <= col <= 9):
        return None
    # Dark square check: parity of (row + col) must be 1
    if (row + col) % 2 == 0:
        return None
    if row % 2 == 0:
        col_index = (col - 1) // 2
    else:
        col_index = col // 2
    return row * 5 + col_index + 1


def _diagonal_neighbours(c: Square) -> dict[str, Square | None]:
    """Diagonal neighbours of square ``c`` (one step on each of the 4 diagonals)."""
    r, col = _case_to_rc(c)
    return {
        "HG": _rc_to_case(r - 1, col - 1),
        "HD": _rc_to_case(r - 1, col + 1),
        "BG": _rc_to_case(r + 1, col - 1),
        "BD": _rc_to_case(r + 1, col + 1),
    }


# ---------------------------------------------------------------------------
# Pawn capture enumeration
# ---------------------------------------------------------------------------


def enumerate_pawn_captures(
    start: Square,
    my_men: frozenset[Square],
    enemy_pieces: frozenset[Square],
) -> list[tuple[tuple[Square, ...], frozenset[Square]]]:
    """Enumerate all maximal rafles for a man starting on ``start``.

    Args:
        start: square where the moving man starts. Must be in ``my_men``.
        my_men: all squares occupied by friendly men (including ``start``).
            Friendly kings, if any, should be passed in ``enemy_pieces=False``
            externally — but this function does not distinguish; it just
            treats squares in this set as blockers (cannot land there
            except on ``start`` itself which is vacated).
        enemy_pieces: all squares occupied by enemy pieces (men + kings).
            Each of these is a potential jump target.

    Returns:
        A list of ``(path, captures)`` pairs, where ``path`` is the ordered
        tuple of squares the man visits (length ≥ 2, starts with ``start``)
        and ``captures`` is the frozenset of enemy squares that get captured.
        Only **maximal** rafles are returned (FMJD prise majoritaire): if any
        rafle captures N pieces, only N-capture rafles are in the result.
        Returns an empty list if no capture is possible from ``start``.

    Notes:
        - The moving piece may pass through the same empty square more than
          once during the rafle (coup turc).
        - A captured piece is removed only at the **end** of the sequence
          (FMJD non-blowing rule), so the same enemy piece cannot be jumped
          twice within one rafle.
        - The landing square at each step must be empty (i.e. not in
          ``my_men - {start}`` and not in ``enemy_pieces - captures_so_far``).
          ``start`` itself counts as empty during the rafle since the piece
          has left it.
    """
    if start not in my_men:
        raise ValueError(f"start square {start} is not in my_men")

    results: list[tuple[tuple[Square, ...], frozenset[Square]]] = []

    def dfs(current: Square, path: list[Square], captures: set[Square]) -> None:
        extended = False
        for direction in ("HG", "HD", "BG", "BD"):
            adjacent = _diagonal_neighbours(current)[direction]
            if adjacent is None:
                continue
            if adjacent not in enemy_pieces or adjacent in captures:
                continue
            landing = _diagonal_neighbours(adjacent)[direction]
            if landing is None:
                continue
            # Landing must be empty: not a friendly piece (except `start`
            # which has been vacated) and not an enemy still on the board.
            if landing in my_men and landing != start:
                continue
            if landing in enemy_pieces and landing not in captures:
                # The would-be landing square holds an enemy not yet captured.
                continue
            extended = True
            dfs(landing, path + [landing], captures | {adjacent})

        if not extended:
            results.append((tuple(path), frozenset(captures)))

    dfs(start, [start], set())

    # Filter to maximal captures only
    capturing = [(p, c) for p, c in results if c]
    if not capturing:
        return []
    max_caps = max(len(c) for _, c in capturing)
    return [(p, c) for p, c in capturing if len(c) == max_caps]


# ---------------------------------------------------------------------------
# Reconstruction from Dubois short notation
# ---------------------------------------------------------------------------


def _side_of_man(state: GameState, sq: Square) -> Side:
    """Return the side of the man on ``sq``, or raise :class:`NotAManError`."""
    if sq in state.white_men:
        return "white"
    if sq in state.black_men:
        return "black"
    if sq in state.white_kings or sq in state.black_kings:
        raise NotAManError(
            f"square {sq} holds a king; pawn reconstruction is not applicable"
        )
    raise NotAManError(f"square {sq} is empty; cannot reconstruct a capture")


def reconstruct_pawn_capture(
    state: GameState,
    from_sq: Square,
    to_sq: Square,
) -> Move:
    """Reconstruct the :class:`Move` for a Dubois-style capture ``from_sq x to_sq``.

    Args:
        state: position before the capture is played. The mover is the side
            holding the man on ``from_sq``; that side's pieces are the
            attackers, the other side's pieces are the targets.
        from_sq: departure square (must hold a man — kings are out of scope).
        to_sq: landing square at the end of the rafle.

    Returns:
        A :class:`Move` whose ``path`` ends on ``to_sq`` and whose
        ``captures`` are the captured enemy squares (sorted ascending).

    Raises:
        NotAManError: ``from_sq`` is empty or holds a king.
        NoSuchRafleError: no maximal rafle from ``from_sq`` lands on ``to_sq``.
        AmbiguousRafleError: several maximal rafles land on ``to_sq`` but
            capture different sets of pieces (genuine ambiguity).
    """
    side = _side_of_man(state, from_sq)
    if side == "white":
        my_men = state.white_men
        enemy = state.black_men | state.black_kings
    else:
        my_men = state.black_men
        enemy = state.white_men | state.white_kings

    candidates = enumerate_pawn_captures(from_sq, my_men, enemy)
    matches = [(path, caps) for path, caps in candidates if path[-1] == to_sq]
    if not matches:
        raise NoSuchRafleError(
            f"no maximal rafle from {from_sq} ends on {to_sq} in this position"
        )

    # Multiple matching paths are fine as long as they capture the same set
    # of pieces (gameplay-equivalent — only the trajectory order differs).
    unique_capture_sets = {caps for _, caps in matches}
    if len(unique_capture_sets) > 1:
        as_lists = sorted(sorted(c) for c in unique_capture_sets)
        raise AmbiguousRafleError(
            f"rafle {from_sq}x{to_sq} is ambiguous: distinct capture sets "
            f"{as_lists}"
        )

    path, captures = matches[0]
    return Move(path=path, captures=tuple(sorted(captures)))
