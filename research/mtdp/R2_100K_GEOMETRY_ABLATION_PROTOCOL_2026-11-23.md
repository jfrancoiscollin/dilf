# MTDP-H13-G1 — Spatial coarsening ablation (preregistered, 2026-11-23)

## Status and scope

**Protocol frozen before any large-sample computation of these signatures.**
Source: the GitHub-published 2026-11-21 R2 and recovered-2026-06-20
snapshots; unchanged signed manifest SHA-256:

- R2: e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c
- historical: e3ed9e2945dd3ff058868968d05343f85cf14ac6565f2180671cc44141768b19

Existing immutable 100k pilot: [run 45267132932](https://github.com/jfrancoiscollin/dilf/actions/runs/45267132932);
100,000 accepted position records and 98,306 exact unique boards including
side to move. The JSON receipt hash was reproduced byte-for-byte.

**Research question:** What fraction of the *sample's exact distinct states*
fall into non-singleton classes if we describe every board with decreasing
spatial detail? This addresses descriptor dimensionality, **not** evidence
that those states have the same best move.

## Frozen masks and signatures

Each board is four disjoint 50-bit bitboards (white men, white kings,
black men, black kings) and side to move (0/1). Playable squares are numbered
1..50 in row-major groups of five per 10x10 row. Preserve the full split
between piece types and colors, including side to move.

Four prespecified signatures are calculated **without scores or WDL**:

1. `material_only` — count all pieces of each type/color across all 10 rows,
   plus side to move (5 integers).
2. `rows_per_zone_5` — count pieces of each type/color separately in rows
   1..5 and 6..10, plus side to move (9 integers).
3. `rows_per_zone_2` — rows 1..2, 3..4, 5..6, 7..8, 9..10 for each type/color,
   plus side to move (21 integers).
4. `rows_per_zone_1` — counts in each of 10 rows for each type/color, plus
   side to move (41 integers).

The 5-row and 2-row descriptors partition the board differently; collision
rates should not be assumed monotonic between them.

## Per-signature precommitted readouts

- Number of signature classes over distinct exact sampled positions
  (do not count repeated observations as separate positions).
- Number of multi-position classes, total *distinct* positions within them,
  largest class, and class-size histogram: 1 / 2 / 3–9 / 10–99 / 100+.
- Upper bound on representatives that might hypothetically be removed by
  collapsing each class to one representative, defined as
  `exact_distinct_positions - signature_classes`. This is **not** a safe
  pruning rate, not search node savings, and not a valid compressor yet.
- Descriptive flags: class contains positions from both snapshots and class
  contains multiple *raw* WDL labels. WDL is not an independent outcome or
  best-move reference, and disagreements may reflect game context.
- Structural rejected sample rows; total accepted records, source manifest
  digest, total scanned object count.

No estimation of confidence intervals, independent game rate, best-move
agreement, FMJD legality, or Jass/Scan strength improvement is permitted
from this sample. No signature chosen by optimizing WDL/score is allowed.

## Gates

1. Use the **same deterministic 100,000 index selection**, per-file
   proportional quotas, strict FEN and 38-byte JNNW readers as the first
   preregistered snapshot pilot. Authenticate 96 file digests and the two
   pinned manifest SHA-256. Fail if accepted rows or exact unique baseline
   disagree with (100000, 98306).
2. Execute six synthetic tests first, plus repo CI. Run on GitHub Actions
   with no R2, Jass runner, cloud training, independent engine or PC.
3. Save deterministic compact JSON receipt and its SHA-256 under the Action
   artifact. Replicate byte-identically before treating as a fixed observation.
4. Treat all coarsened families only as **candidate classes**, never merge,
   prune or promote anything in Jass. In particular, a legal move set,
   successor congruence or best move has not been evaluated.

## Subsequent scientific gate

A real D1 best-move stability experiment would need a distinct,
source/game/ply-authenticated holdout set, full historical leakage quarantine,
the pinned FMJD legal engine and separately frozen Scan/Jass scores and node
budgets. The already annotated R2 training corpora are **not** an untouched
test population. Seek new independent games and legal trajectories before
testing any pruning policy.

Reproduce the frozen descriptive pilot:

    python -m research.mtdp.r2_geometry_ablation \
      --r2 snapshot-data/data/r2_positions/2026-11-21 \
      --historical snapshot-data/data/r2_positions/recovered-2026-06-20 \
      --output /tmp/mtdp-h13-g1-spatial-coarsening.json

**Single next action:** execute and reproduce the pinned 100k spatial
collision table, then use it only to select *which hypotheses to preregister*
for future independent decision-level testing (not to set strategic outcomes).
