# MTDP — signature ablation, measured FMJD baseline (2026-11-11)

## Provenance and validation

GitHub Actions [downstream-compat run 43025727899](https://github.com/jfrancoiscollin/dilf/actions/runs/43025727899), commit `05a521483b585712abe10617b774cd95babd54e0`, **success**; companion CI run 43025727959 **success**. The real FMJD adapter replayed 26 PC Blues games; the spatial signature ablation step and artifact upload succeeded. Values below are transcribed from the actual job log, not inferred.

## Results

| Signature | Distinct signatures | Collision groups | Distinct-FEN collision pairs | Pairs with different legal sets |
| --- | ---: | ---: | ---: | ---: |
| 8 coarse descriptors + turn | 1,642 | 90 | 137 | 114 |
| + pieces per side | 1,642 | 90 | 137 | 114 |
| + kings per side | 1,643 | 89 | 136 | 113 |
| + exact piece occupancy and types | 1,750 | 0 | 0 | 0 |

Total observations: **1,864**. The 1,750 distinct exact-occupancy signatures indicate that observations include repeated board positions across games. No claim about distinct FENs beyond what the report computes is necessary.

## Falsifiable conclusions

Adding total piece counts contributes **no separation** on this corpus; this is consistent with these counts already being constrained by the original descriptor tuple, and is not evidence that material never matters. Adding king counts eliminates **one** of 114 discordant collision pairs (0.88% of the original discordant pairs). Exact occupancy eliminates all collisions by definition and therefore offers no useful compression of unique positions.

The next hypothesis must test *intermediate* geometry-aware features, not simply global counts: e.g. side-specific occupancy by board sector, diagonal structure, local contact/capture exposure, with explicit complexity/compression costs. Predefine variants and evaluate on game-grouped holdout data; do not tune and evaluate on the same 26 games. In particular, neither legal-set agreement nor signature equality alone proves safe search pruning or best-move equivalence.

Pairs within a game are dependent; the observed proportions are descriptive, not population estimates. The exact-occupancy control is a sanity check, not a model candidate.
