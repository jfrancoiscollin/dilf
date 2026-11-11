# PC Blues game trajectory pilot

The existing `data/exports/pcblues/pcblues_games.pdn` contains 26 game
mainlines. `research.mtdp.pdn` parses them and can reconstruct positions
**only when supplied with a trusted FMJD `EngineProtocol` implementation**.

The adapter intentionally does not invent rules. It matches each PDN move
against `engine.legal_moves(state)`, then applies the unique matching move
with `engine.apply_move(state, move)`. If the same capture endpoints admit
multiple legal paths, it rejects the game instead of guessing. A caller
should use `validated_trajectory` and quarantine a rejected game.

The parser strips comments and sidelines, handles move numbers and PDN result
markers, and preserves original provenance tags. A result tag is *not* a WDL
training label. FEN-tagged noninitial positions are supported.

**Not yet done:** connecting a production rules adapter, full 26-game replay,
per-ply JSONL export, and engine evaluation. No claim is made that the games
have been independently replayed by this module.

**Caveats:** Unusual PDN constructs (e.g. move annotations outside comments,
multiple alternative mainlines, or ambiguous captures) are rejected; an
untrusted engine can still be wrong. For publication, cross-check a subset
against a second independently implemented FMJD rules engine.
