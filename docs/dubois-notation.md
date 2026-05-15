# Dubois short capture notation

Reference for the abbreviated capture notation used in Jean-Pierre Dubois's
pedagogical books, and how `pedagogy.notation.dubois` reconstructs the full
trajectory from it.

## Why this exists

Dubois books print combinations using a short notation that omits the
intermediate squares of a multi-jump capture (rafle). For example, in
Apprentissage Combinaisons ch. 1 p. 6, diagram D1, the printed solution is:

```
26-21 (17x28) 43x3
```

The fragment `17x28` reads "the man on square 17 ends up on square 28 after a
capture", but the actual trajectory is `17 → 26 → 37 → 28` and the captured
pieces are on 21, 31, 32. The reader is expected to reconstruct this
geometrically from the diagram.

For automated tooling (test fixtures, motif detectors, manual building) this
is friction: every Dubois short notation has to be expanded into a full
`pedagogy.game.Move` before downstream code can consume it. The
`pedagogy.notation.dubois` module does that expansion.

## What the short notation means

| Notation        | Meaning                                                                |
|-----------------|------------------------------------------------------------------------|
| `32-28`         | Non-capture move: piece on 32 walks one diagonal step to 28.           |
| `31x22`         | Single jump: piece on 31 captures one enemy and lands on 22.           |
| `aXb` (rafle)   | Multi-jump capture: piece on `a` lands on `b` after capturing several enemies along a zigzag trajectory. **Intermediate squares are implicit.** |
| `(17x28)`       | Parentheses mark the **opponent's** forced reply in a written solution; same notation rules inside. |
| `43x3` no paren | The active player's move (no parentheses).                             |

When several moves are chained in a solution, they alternate: the active
player's move, then the parenthesised opponent reply, then the active player
again, etc.

## Rafle geometry — pawns

The pawn reconstructor (`reconstruct_pawn_capture`) handles men only.
Passing a king square as the departure raises `NotAManError` — use
`reconstruct_king_capture` or the unified `reconstruct_capture` instead.

For a man, each jump:

1. requires a diagonally-adjacent enemy piece,
2. lands on the square immediately beyond it (one step further in the same
   diagonal direction),
3. the landing square must be empty.

A rafle is the concatenation of such jumps. Two FMJD subtleties matter:

- **Direction can change at each jump.** The trajectory does not have to be a
  straight line. In D1, the man on 17 first jumps BG (down-left) to 26, then
  BD (down-right) to 37, then HD (up-right) to 28.
- **Non-blowing rule.** Captured pieces remain on the board until the end of
  the rafle, so the same enemy piece cannot be jumped twice. But the moving
  man **can** revisit an empty square it has already crossed — this is the
  *coup turc*, and `enumerate_pawn_captures` supports it.

## Rafle geometry — kings (dame)

The king reconstructor (`reconstruct_king_capture`) handles kings (dames).
Passing a man square as the departure raises `NotAKingError`.

The king's jump geometry is different from the man's:

1. The king slides any number of empty squares along a diagonal before
   jumping.
2. To capture, exactly one enemy piece must sit on the diagonal, with all
   squares between the king and the enemy being empty (no blocker).
3. After the jump, the king lands on any empty square strictly past the
   captured enemy on the same diagonal (one square or several — caller's
   choice when reconstructing). The landing slide also requires every square
   to be empty.
4. The rafle may chain multiple jumps; the king may change direction at each
   landing.
5. The non-blowing rule applies: captured pieces stay on the board until the
   end of the rafle, so the king cannot re-jump a piece it already captured.
6. Coup turc applies: the king may pass through the same empty square
   multiple times.

For ambiguous landings (multiple landings past the captured enemy all
plausible), Dubois's short notation `aXb` picks one specific landing `b`.
`reconstruct_king_capture` returns the rafle ending exactly on `b`.

## Unified dispatch

For callers that don't want to inspect the piece type, `reconstruct_capture`
auto-detects whether `from_sq` holds a man or a king and dispatches:

```python
from pedagogy.notation.dubois import reconstruct_capture

move = reconstruct_capture(state, from_sq=48, to_sq=22)
# Routes to reconstruct_king_capture if 48 is a king, to
# reconstruct_pawn_capture if it is a man.
```

## Maximal capture rule

Among all legal rafles available to the side to move,
`enumerate_pawn_captures` returns only the **maximal** ones (those with the
highest number of captures). This is the FMJD *prise majoritaire* rule. The
reconstructor uses this as the default: when expanding `aXb`, only maximal
rafles ending on `b` are candidates.

## Ambiguity

If two maximal rafles starting on `a` and ending on `b` capture exactly the
same set of pieces, they are gameplay-equivalent — only the trajectory order
differs. `reconstruct_pawn_capture` accepts this and returns the first match.

If two maximal rafles ending on `b` capture **different** sets of pieces, the
short notation is genuinely ambiguous and the function raises
`AmbiguousRafleError`. In Dubois corpora this is rare in practice; when it
happens the original diagram or surrounding text should disambiguate.

## Typographic errata

The Dubois PDFs are reliable but not infallible. The Apprentissage
Combinaisons book has at least one known typo: D9 page 6 prints `43-38`
where the position has no white piece on 43; the correct first move is
`44-39`. When the reconstructor returns `NoSuchRafleError` for a notation
that "should" work, the first thing to suspect is a typo of `±1` on a single
digit of the departure or arrival square; check the diagram before assuming
a bug in the reconstructor or the position.

## API

```python
from pedagogy.game import GameState
from pedagogy.notation.dubois import (
    enumerate_pawn_captures,
    enumerate_king_captures,
    reconstruct_pawn_capture,
    reconstruct_king_capture,
    reconstruct_capture,
    NotAManError,
    NotAKingError,
    NoSuchRafleError,
    AmbiguousRafleError,
)

# Position after the white sacrifice 26-21 in Dubois D1 p.6
state = GameState(
    white_men=frozenset({21, 31, 32, 43}),
    black_men=frozenset({9, 17, 19, 38}),
    turn="black",
)

# Reconstruct the forced black reply (17x28)
black_move = reconstruct_pawn_capture(state, from_sq=17, to_sq=28)
# Move(path=(17, 26, 37, 28), captures=(21, 31, 32))

# King rafle example: a white king on 28 captures a black man on 23 and
# lands on 14.
king_state = GameState(
    white_kings=frozenset({28}),
    black_men=frozenset({23}),
    turn="white",
)
king_move = reconstruct_king_capture(king_state, from_sq=28, to_sq=14)
# Move(path=(28, 14), captures=(23,))

# Unified dispatch — auto-detects piece type.
move = reconstruct_capture(state, from_sq=17, to_sq=28)        # pawn
move = reconstruct_capture(king_state, from_sq=28, to_sq=14)   # king
```

## Future work

- Validator pass that compares a Dubois-extracted solution text against the
  pixel-extracted position and flags inconsistencies (would have caught the
  D9 typo automatically).
- Optional caller-side `unique_trajectories=True` flag to return all
  gameplay-equivalent paths instead of just the first.
- Notation conventions beyond bare moves: `(ad lib)` for forced-equivalent
  opponent replies, `+1p` for material-gain annotations after a non-rafle
  exchange.
