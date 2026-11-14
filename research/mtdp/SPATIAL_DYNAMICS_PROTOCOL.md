# MTDP spatial dynamics — descriptive preregistration v1

## Scope and hypothesis

This first experiment audits **within-game spatial changes** in the 26 PC Blues
PDN mainlines replayed by an independent FMJD rules engine. It is **not** a
test of optimality, Scan agreement, move quality, or strategic equivalence.

Exploratory hypothesis D1: some consecutive legal positions may have
unchanged coarse spatial descriptors even though the board and side to move
have changed. D1 is a measurable compression opportunity **only for
descriptive representation**, not evidence that those positions have the same
best move.

## Data provenance and inclusion

Use only `pcblues_game_pdn` records from `trajectories.py`, with
`king_detection_verified=true`. Every game must contain contiguous plies
starting at 0; partial games and mixed diagram fixtures are rejected. Keep
all game boundaries; do not join last position of one game to first of next.

## Fixed descriptors

Track the absolute adjacent-ply change in white/black core center occupancy,
white/black extended center occupancy, white/black diagonal adjacency,
occupied-square count, and material balance. Report each descriptor's change
count and mean absolute change.

Count exact position revisits only **within a game** by the canonical
position hash (which includes side to move). Count descriptor-unchanged
transitions when all eight fixed descriptors remain equal.

## Statistical limitations and next experiment

The 26 curated games are not a representative independent sample of all
FMJD play. Plies from the same game are dependent; avoid confidence intervals
that treat plies as IID. Do not interpret unchanged descriptors as
strategic equivalence.

Next test, after descriptive audit: define a preregistered structural
fingerprint and evaluate *out-of-game* generalization of best-move
agreement using a trusted evaluator, with splits grouped by game and
controls for material, side to move, and game phase. Report failures and
counterexamples, not just aggregate similarity.

## Reproduce

With a verified `draught-master` checkout available on `PYTHONPATH`:

```bash
python -m research.mtdp.trajectories \
  --engine-factory research.mtdp.draught_master_adapter:create_engine \
  --output .cache/mtdp/trajectories.jsonl \
  --quarantine .cache/mtdp/quarantine.jsonl
python -m research.mtdp.spatial_dynamics \
  .cache/mtdp/trajectories.jsonl \
  --output .cache/mtdp/spatial_dynamics.json
```

The report is computed from actual exported positions, never fabricated
from the number of source games.
