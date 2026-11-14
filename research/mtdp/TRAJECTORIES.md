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

## Exporter CLI (adapter required)

From the repository root, after installing a trusted rules adapter factory:

```bash
python -m research.mtdp.trajectories \
  --engine-factory your_rules_adapter:create_engine \
  --pdn data/exports/pcblues/pcblues_games.pdn \
  --output .cache/mtdp/trajectories.jsonl \
  --quarantine .cache/mtdp/quarantine.jsonl
python -m research.mtdp.summary .cache/mtdp/trajectories.jsonl
```

The factory must return an object implementing `EngineProtocol` with
`legal_moves(state)` and `apply_move(state, move)`. Import only trusted
factories. Each accepted game is exported atomically; rejected games produce
a separate quarantine record with no partial positions.

A rules adapter and independent FMJD validation are still prerequisites for
scientifically trusted trajectories. No engine is bundled in MTDP.

## Existing draught-master adapter

A thin optional adapter is now available at
`research.mtdp.draught_master_adapter:create_engine`. It wraps
`draught-master/backend/game_engine.py` (its `GameState`, `Move`,
`get_legal_moves`, and `apply_move`) without vendoring the rules.

If the two repositories are checked out side by side:

```bash
PYTHONPATH="../draught-master:." python -m research.mtdp.trajectories \
  --engine-factory research.mtdp.draught_master_adapter:create_engine
```

The adapter preserves men/kings, turn, capture paths and promotions. Each
move is rechecked against the native legal move list before application.
The DILF repository does not require draught-master to import its research
modules or run unit tests. Before trusting the PC Blues export, run an
integration test using the actual downstream rules implementation and
independently cross-check replayed FEN sequences.
