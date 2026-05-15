"""Reconstruct rafle (multi-jump capture) trajectories from Dubois short notation.

In Dubois pedagogical books, a capture sequence is written ``aXb`` where ``a``
is the departure square and ``b`` is the final landing square. The intermediate
squares and the captured pieces are left **implicit** — the reader is expected
to reconstruct them geometrically from the position.

A rafle is **not** a straight-line slide; the moving piece can change diagonal
at each jump. For example, in the canonical Dubois D1 (Apprentissage
Combinaisons, ch. 1, p. 6), the rafle ``17x28`` is the trajectory
``17 → 26 → 37 → 28`` (BG, BD, HD), capturing the pawns on 21, 31 and 32.

This module reconstructs the full :class:`pedagogy.game.Move` from the short
``(from_sq, to_sq)`` notation by enumerating every legal pawn or king rafle
from ``from_sq`` and retaining the one (or those) ending on ``to_sq`` with the
maximum number of captures (FMJD prise majoritaire rule).

**Pawns and kings both supported.** Pawns jump exactly one square over a single
adjacent enemy. Kings slide any number of empty squares before jumping over
exactly one enemy on the same diagonal, then slide any number of empty squares
after, before optionally jumping again. Dispatch is automatic in
:func:`reconstruct_capture`; the lower-level :func:`reconstruct_pawn_capture`
and :func:`reconstruct_king_capture` are also exposed for explicit use.

**Coup turc.** A piece (pawn or king) may traverse the same empty square twice
during one rafle, provided it does not re-jump a captured piece (FMJD
non-blowing rule). The enumerators support this.

**Equivalent trajectories.** Two different paths from ``from_sq`` to ``to_sq``
that capture **exactly the same set of enemy pieces** are gameplay-equivalent.
The reconstruction functions return the first of these; if two paths ending on
``to_sq`` differ by their capture set, the rafle is genuinely ambiguous and
:class:`AmbiguousRafleError` is raised.
"""

from __future__ import annotations

from pedagogy.game import GameState, Move, Side, Square


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NotAManError(ValueError):
    """Raised when ``from_sq`` is not occupied by a man.

    Used by :func:`reconstruct_pawn_capture` when ``from_sq`` is empty or
    holds a king. To reconstruct a king rafle, use
    :func:`reconstruct_king_capture` or the unified :func:`reconstruct_capture`.
    """


class NotAKingError(ValueError):
    """Raised when ``from_sq`` is not occupied by a king.

    Used by :func:`reconstruct_king_capture` when ``from_sq`` is empty or
    holds a man. To reconstruct a pawn rafle, use
    :func:`reconstruct_pawn_capture` or the unified :func:`reconstruct_capture`.
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


# ---------------------------------------------------------------------------
# King capture enumeration
# ---------------------------------------------------------------------------
#
# King ("dame") movement geometry, FMJD rules:
#
# 1. A king slides any number of empty squares along one of the 4 diagonals.
# 2. To capture, the king may slide 0+ empty squares, then jump over exactly
#    one enemy piece on the same diagonal, then slide 0+ empty squares before
#    optionally jumping again on a (possibly different) diagonal.
# 3. The square holding the enemy is "captured" only at the end of the rafle
#    (FMJD non-blowing rule), so the king cannot re-jump a piece it already
#    captured during the same sequence — but the empty square right behind
#    can be traversed multiple times if needed (coup turc).
# 4. The squares between the king's pre-jump position and the enemy must all
#    be empty (no blocker). The squares between the enemy and the king's
#    landing position must also be empty (other than the captured piece).
# 5. Maximum-capture rule: among all possible rafles, the king must take the
#    one capturing the largest number of pieces.


def _slide_to_enemy(
    current: Square,
    direction: str,
    my_pieces: frozenset[Square],
    enemy_pieces: frozenset[Square],
    already_captured: frozenset[Square],
    start: Square,
) -> tuple[Square, Square] | None:
    """Slide along ``direction`` until finding a capturable enemy.

    Returns ``(enemy_sq, landing_sq_minimum)`` where ``enemy_sq`` is the first
    capturable enemy on this diagonal, and ``landing_sq_minimum`` is the square
    immediately after it (the closest possible landing square). The caller is
    responsible for enumerating all valid landing squares from
    ``landing_sq_minimum`` onwards (slide any number of empty squares).

    Returns ``None`` if no enemy is reachable on this diagonal — either the
    diagonal exits the board through empty squares, or it is blocked by a
    friendly piece, a captured-but-still-on-board piece, or two consecutive
    enemy pieces (the second blocks the jump).
    """
    sq = current
    while True:
        next_sq = _diagonal_neighbours(sq)[direction]
        if next_sq is None:
            return None
        # Is the next square a blocker?
        if next_sq in my_pieces and next_sq != start:
            return None
        if next_sq == start:
            # The start square is treated as empty during the rafle (vacated).
            sq = next_sq
            continue
        if next_sq in already_captured:
            # Cannot re-jump a piece already captured in this rafle.
            return None
        if next_sq in enemy_pieces:
            # Found an enemy. Check the landing square (immediately past).
            landing = _diagonal_neighbours(next_sq)[direction]
            if landing is None:
                return None
            if landing in my_pieces and landing != start:
                return None
            if landing in enemy_pieces and landing not in already_captured:
                return None
            if landing in already_captured:
                # The would-be landing square holds a piece already captured
                # in this rafle; it's "on the board" geometrically until the
                # end of the rafle, so the king cannot land there.
                return None
            return (next_sq, landing)
        # Empty square — keep sliding.
        sq = next_sq


def _enumerate_landings(
    enemy_sq: Square,
    direction: str,
    my_pieces: frozenset[Square],
    enemy_pieces: frozenset[Square],
    already_captured: frozenset[Square],
    start: Square,
) -> list[Square]:
    """List all empty squares the king can land on after jumping ``enemy_sq``.

    Starts from the square right after ``enemy_sq`` on ``direction`` and slides
    forward, collecting empty squares until hitting a blocker or the edge.
    """
    landings: list[Square] = []
    sq = enemy_sq
    while True:
        next_sq = _diagonal_neighbours(sq)[direction]
        if next_sq is None:
            return landings
        if next_sq in my_pieces and next_sq != start:
            return landings
        if next_sq in enemy_pieces and next_sq not in already_captured:
            return landings
        if next_sq in already_captured:
            return landings
        # next_sq is either empty or the start square (= empty during rafle).
        landings.append(next_sq)
        sq = next_sq


def enumerate_king_captures(
    start: Square,
    my_pieces: frozenset[Square],
    enemy_pieces: frozenset[Square],
) -> list[tuple[tuple[Square, ...], frozenset[Square]]]:
    """Enumerate all maximal rafles for a king starting on ``start``.

    Args:
        start: square where the moving king starts. Should be in ``my_pieces``.
        my_pieces: all squares occupied by friendly pieces (men + kings),
            including ``start``. Squares in this set are treated as blockers
            (cannot land there) except ``start`` itself which is vacated.
        enemy_pieces: all squares occupied by enemy pieces (men + kings).
            Each of these is a potential jump target.

    Returns:
        A list of ``(path, captures)`` pairs, where ``path`` is the ordered
        tuple of squares the king visits (length ≥ 2, starts with ``start``)
        and ``captures`` is the frozenset of enemy squares that get captured.
        Only **maximal** rafles are returned (FMJD prise majoritaire).
        Returns an empty list if no capture is possible from ``start``.

    Notes:
        - The king may slide any number of empty squares before AND after
          each jump.
        - For a single jump over enemy ``E`` on direction ``d``, the king
          can land on any empty square strictly past ``E`` on direction ``d``
          (before the next blocker or board edge).
        - A captured piece is removed only at the **end** of the sequence
          (FMJD non-blowing rule), so the same enemy piece cannot be jumped
          twice within one rafle, but the squares it occupies remain
          unavailable as landing squares until the rafle ends.
        - The king may pass through (slide over) the same empty square more
          than once during a rafle (coup turc).
    """
    if start not in my_pieces:
        raise ValueError(f"start square {start} is not in my_pieces")

    results: list[tuple[tuple[Square, ...], frozenset[Square]]] = []

    def dfs(current: Square, path: list[Square], captures: frozenset[Square]) -> None:
        extended = False
        for direction in ("HG", "HD", "BG", "BD"):
            found = _slide_to_enemy(
                current, direction, my_pieces, enemy_pieces, captures, start
            )
            if found is None:
                continue
            enemy_sq, _first_landing = found
            landings = _enumerate_landings(
                enemy_sq, direction, my_pieces, enemy_pieces, captures, start
            )
            if not landings:
                continue
            for landing in landings:
                extended = True
                dfs(landing, path + [landing], captures | {enemy_sq})

        if not extended:
            results.append((tuple(path), captures))

    dfs(start, [start], frozenset())

    capturing = [(p, c) for p, c in results if c]
    if not capturing:
        return []
    max_caps = max(len(c) for _, c in capturing)
    return [(p, c) for p, c in capturing if len(c) == max_caps]


def _side_of_king(state: GameState, sq: Square) -> Side:
    """Return the side of the king on ``sq``, or raise :class:`NotAKingError`."""
    if sq in state.white_kings:
        return "white"
    if sq in state.black_kings:
        return "black"
    if sq in state.white_men or sq in state.black_men:
        raise NotAKingError(
            f"square {sq} holds a man; king reconstruction is not applicable"
        )
    raise NotAKingError(f"square {sq} is empty; cannot reconstruct a capture")


def reconstruct_king_capture(
    state: GameState,
    from_sq: Square,
    to_sq: Square,
) -> Move:
    """Reconstruct the :class:`Move` for a Dubois-style king capture ``from_sq x to_sq``.

    Args:
        state: position before the capture is played. The mover is the side
            holding the king on ``from_sq``.
        from_sq: departure square (must hold a king — men are out of scope).
        to_sq: landing square at the end of the rafle.

    Returns:
        A :class:`Move` whose ``path`` ends on ``to_sq`` and whose
        ``captures`` are the captured enemy squares (sorted ascending).

    Raises:
        NotAKingError: ``from_sq`` is empty or holds a man.
        NoSuchRafleError: no maximal rafle from ``from_sq`` lands on ``to_sq``.
        AmbiguousRafleError: several maximal rafles land on ``to_sq`` but
            capture different sets of pieces (genuine ambiguity).
    """
    side = _side_of_king(state, from_sq)
    if side == "white":
        my = state.white_men | state.white_kings
        enemy = state.black_men | state.black_kings
    else:
        my = state.black_men | state.black_kings
        enemy = state.white_men | state.white_kings

    candidates = enumerate_king_captures(from_sq, my, enemy)
    matches = [(path, caps) for path, caps in candidates if path[-1] == to_sq]
    if not matches:
        raise NoSuchRafleError(
            f"no maximal king rafle from {from_sq} ends on {to_sq} in this position"
        )

    unique_capture_sets = {caps for _, caps in matches}
    if len(unique_capture_sets) > 1:
        as_lists = sorted(sorted(c) for c in unique_capture_sets)
        raise AmbiguousRafleError(
            f"king rafle {from_sq}x{to_sq} is ambiguous: distinct capture sets "
            f"{as_lists}"
        )

    path, captures = matches[0]
    return Move(path=path, captures=tuple(sorted(captures)))


# ---------------------------------------------------------------------------
# Unified dispatch
# ---------------------------------------------------------------------------


def reconstruct_capture(
    state: GameState,
    from_sq: Square,
    to_sq: Square,
) -> Move:
    """Reconstruct a capture from ``from_sq`` to ``to_sq``, auto-detecting piece type.

    Dispatches to :func:`reconstruct_pawn_capture` if ``from_sq`` holds a man,
    to :func:`reconstruct_king_capture` if it holds a king.

    Args:
        state: position before the capture.
        from_sq: departure square.
        to_sq: landing square.

    Returns:
        The reconstructed :class:`Move`.

    Raises:
        ValueError: ``from_sq`` is empty.
        NoSuchRafleError, AmbiguousRafleError: as in the underlying functions.
    """
    if from_sq in state.white_men or from_sq in state.black_men:
        return reconstruct_pawn_capture(state, from_sq, to_sq)
    if from_sq in state.white_kings or from_sq in state.black_kings:
        return reconstruct_king_capture(state, from_sq, to_sq)
    raise ValueError(f"square {from_sq} is empty; cannot reconstruct a capture")


# ---------------------------------------------------------------------------
# Notation-string parsing
# ---------------------------------------------------------------------------


def parse_move_notation(notation: str, state: GameState) -> Move:
    """Parse a Dubois / PDN move string into a fully-resolved :class:`Move`.

    Accepts the two notation forms used throughout the corpus:

    - ``"32-28"`` — a quiet (non-capturing) move. Returns
      ``Move(path=(32, 28), captures=())``.
    - ``"40x29x18"`` — a capture sequence. The intermediate squares
      (``29`` here) are taken as the actual trajectory : we dispatch
      to :func:`reconstruct_capture` with the FIRST and LAST squares,
      then validate that every intermediate stop in ``notation`` is on
      the reconstructed path. This catches inconsistent notations
      early.

    Unlike the previous fallback that stored ``captures=()``, the
    returned ``Move`` carries the **actual captured squares**, which
    is what motif detectors (coup_royal, prise_max_ratee, …) need to
    fire correctly. Capture-aware motif detection on exercise solutions
    depends on this function.

    Args:
        notation: the move string, e.g. ``"32-28"`` or ``"40x29x18"``.
        state: position **before** the move is played. Required to
            disambiguate trajectories and locate captured pieces.

    Returns:
        A :class:`Move` with ``path`` and ``captures`` populated.

    Raises:
        ValueError: malformed notation, empty source square, or
            intermediate squares inconsistent with the reconstructed
            trajectory.
        NoSuchRafleError, AmbiguousRafleError: see
            :func:`reconstruct_capture`.
    """
    notation = notation.strip().lstrip("K")  # tolerate optional King prefix
    if not notation:
        raise ValueError("empty move notation")

    if "x" in notation:
        try:
            squares = tuple(int(s) for s in notation.split("x"))
        except ValueError as exc:
            raise ValueError(f"malformed capture notation {notation!r}") from exc
        if len(squares) < 2:
            raise ValueError(f"capture notation needs ≥2 squares: {notation!r}")
        from_sq, to_sq = squares[0], squares[-1]
        move = reconstruct_capture(state, from_sq, to_sq)
        # Validate intermediate stops if the caller supplied them.
        if len(squares) > 2:
            path_set = set(move.path)
            stray = [s for s in squares[1:-1] if s not in path_set]
            if stray:
                raise ValueError(
                    f"notation {notation!r} lists intermediate squares "
                    f"{stray} that are not on the reconstructed trajectory "
                    f"{list(move.path)}"
                )
        return move

    if "-" in notation:
        try:
            parts = notation.split("-")
            if len(parts) != 2:
                raise ValueError
            from_sq, to_sq = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError(f"malformed quiet notation {notation!r}") from exc
        return Move(path=(from_sq, to_sq), captures=())

    raise ValueError(
        f"notation {notation!r} contains neither '-' nor 'x'; cannot parse"
    )
