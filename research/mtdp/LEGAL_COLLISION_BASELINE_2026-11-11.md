# MTDP — empirical legal-action collision baseline (2026-11-11)

## Provenance

GitHub Actions downstream-compat run [43025072221](https://github.com/jfrancoiscollin/dilf/actions/runs/43025072221), commit `de08025bbf509838879edd1e83cdb7f947124215`, completed successfully. Its FMJD replay, spatial dynamics, signature collisions, side-to-move control, legal-action comparison and artifact upload all succeeded. Values below are transcribed from the actual job logs; no local or unverified run is claimed.

## Observed results

| Metric | Value |
| --- | ---: |
| PC Blues games accepted | 26 |
| Position observations | 1,864 |
| Distinct coarse spatial signatures | 1,440 |
| Coarse signature collision groups | 228 |
| Cross-game coarse collision groups | 54 |
| Coarse groups containing both sides to move | 202 |
| Signatures after conditioning on side to move | 1,642 |
| Same-turn collision groups | 90 |
| Distinct FENs in same-turn collision groups | 198 |
| Same-turn pairs of distinct FENs | 137 |
| Pairs with different exact FMJD legal-action sets | 114 (83.21%) |
| Pairs with identical exact FMJD legal-action sets | 23 (16.79%) |
| Same-turn pairs spanning multiple games | 90 |

## Interpretation

The eight-feature coarse signature, even with side-to-move included,
does **not** determine the exact square-indexed legal move set on these
positions. The 114 counterexamples refute the proposed guarantee on
the observed corpus. The remaining 23 equal-action pairs are not proof
of equivalent evaluation, best move, tactics, or safe pruning.

The denominator is pairs of distinct FENs within same-turn collision
groups, not all positions or all possible position pairs. Pairs are
dependent and the 26-game corpus is not a random sample. The 83.21%
figure is descriptive and must not be generalized as a population
probability.

## Next falsifiable hypothesis

Augment signatures with piece-square occupancy and king/man status,
and evaluate collision compression versus exact legal-action
agreement. Compare against the same corpus and then independent
game-grouped holdout games. Never prune based on signature alone
without tactical and best-move safeguards.
