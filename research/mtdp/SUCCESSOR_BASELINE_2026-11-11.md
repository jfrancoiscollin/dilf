# MTDP — one-ply successor congruence baseline (2026-11-11)

## Provenance

GitHub Actions downstream-compat run [43061203371](https://github.com/jfrancoiscollin/dilf/actions/runs/43061203371), commit `0d9b4c74097716268e17904f3d51feb593f2b699`, succeeded. Figures below were read from the actual workflow job logs (job 130663947242), not inferred from the workflow status.

## Measured result (26 PC Blues games)

| Measure | Value |
| --- | ---: |
| Position observations | 1,864 |
| Distinct quiet signatures | 1,222 |
| Pairs of distinct FENs sharing a quiet signature | 61 |
| Pairs with different exact legal-action sets | 0 |
| Pairs with at least one differing exact successor FEN | 61 |
| Pairs with at least one differing successor quiet signature | 61 |

**Interpretation:** The 61 candidate equivalences preserve the current
square-indexed legal actions but **none** preserves the successor quiet
signature under every shared legal action. This falsifies one-ply
congruence for all 61 observed pairs. Exact successor FEN equality also
fails for every pair.

A pair is counted once if *any* shared action leads to a difference.
These are dependent, within-corpus pairs; 61/61 is not a population
estimate. The audit does not measure minimax values or best moves.
A successor signature can be `None` for positions with captures or
mover kings; this is an intentionally coarse representation and should
be refined in future audits rather than interpreted as equivalence.

## Engineering validation

The downstream compatibility job completed successfully, including
FMJD replay and successor analysis. The general CI run
[43061203797](https://github.com/jfrancoiscollin/dilf/actions/runs/43061203797)
failed at the `Install poppler-utils` step, before test execution.
This is not evidence of a failing MTDP unit test.

## Next experiment

Investigate whether a bounded local opponent occupancy halo around the
mover's men, together with capture/promotion guards, preserves the
successor signature. Evaluate compression, exact legal actions and
one-ply congruence on held-out games; avoid pruning claims.
