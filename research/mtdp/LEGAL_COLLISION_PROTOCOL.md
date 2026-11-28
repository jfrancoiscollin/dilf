# MTDP — legal-action collision experiment (preregistered interpretation)

## Question

Given two distinct canonical FEN positions with the same eight coarse
spatial descriptors **and the same side to move**, do their exact FMJD legal
action sets match?

The answer measures an important necessary condition for reusing an
**untransformed** move choice. It does not test strategic equivalence or
whether a search branch may safely be pruned.

## Source and reproducibility

Use the 26 PC Blues games, replayed completely through the actual
`draught-master` FMJD rules adapter. Reject invalid games rather than
using partial trajectories. Include the starting position and every ply.
Deduplicate repeated canonical FENs within each signature; provenance is
tracked by game index. Compare each unordered pair of distinct FENs once,
within the same-turn signature bucket.

The legal-action fingerprint contains the exact ordered move path, captured
square set, and promotion flag. The same FEN must always produce the same
fingerprint; otherwise fail closed.

## Report

- Number of same-turn signature-collision pairs.
- Pairs with identical and different legal-action fingerprints.
- Number of pairs spanning multiple games.
- Up to ten counterexamples with source games and legal move counts.

The sample is curated and moves/positions within a game are dependent.
Do not report a naive binomial confidence interval over all pairs.
No engine score, WDL label, or best-move prediction is produced.

## Interpretation gates

1. Any unequal-action pair refutes the claim that the coarse signature
   determines the **exact square-indexed** legal action set.
2. Equal-action pairs do **not** establish strategic equivalence: resulting
   positions, tactics, and best moves may differ.
3. Square-indexed move equality is stricter than symmetry-normalized action
   equality. Symmetry normalization would require a separately verified
   transform that preserves turn, promotion, captures, and FMJD rules.
4. Before pruning in Jass, evaluate a held-out, game-grouped benchmark with
   tactical safety and best-move agreement against a trusted search baseline.

## Run

```bash
PYTHONPATH=.:../draught-master python -m research.mtdp.legal_collision_audit \
  --engine-factory research.mtdp.draught_master_adapter:create_engine \
  --pdn data/exports/pcblues/pcblues_games.pdn \
  --output .cache/mtdp/legal-collisions.json
```

The GitHub downstream compatibility workflow executes this analysis on
the 26 games and archives the JSON output. A passing workflow only proves
that the program completed and its assertions passed; inspect the JSON
before making any numerical claim.
