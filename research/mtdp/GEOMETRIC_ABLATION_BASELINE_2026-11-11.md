# MTDP — geometric ablation: measured FMJD baseline (2026-11-11)

## Reproducibility

Source: [downstream-compat GitHub Actions run 43031835253](https://github.com/jfrancoiscollin/dilf/actions/runs/43031835253), commit `9626f0a53f7d8ac5a91a822f8d24dc0e8ace28bc`. Both downstream-compat and CI succeeded. The downstream job completed real FMJD replay and the spatial ablation, uploading its JSON artifact. All numbers below are copied from the **executed job logs**, not extrapolated.

The experiment uses 26 PC Blues games, 1,864 position observations, and deduplicates canonical FENs before counting unordered collision pairs.

| Signature variant | Distinct signatures | Distinct-FEN collision pairs | Pairs with different exact legal actions |
| --- | ---: | ---: | ---: |
| Coarse + turn | 1,642 | 137 | 114 |
| + piece counts | 1,642 | 137 | 114 |
| + king counts | 1,643 | 136 | 113 |
| + quadrants | 1,676 | 84 | 63 |
| + pairs of rows | 1,698 | 74 | 52 |
| + individual rows | 1,704 | 68 | 46 |
| + mover occupancy | 1,725 | 29 | 12 |
| Conditional quiet-man geometry | 1,712 | 61 | **0** |
| Exact occupancy control | distinct per canonical FEN | 0 | 0 |

The conditional quiet-man geometry path applied to 1,260 distinct FENs; for the remaining positions the implementation falls back to exact occupancy. The conditional representation yielded 61 pairs with identical exact legal-action sets, and **no observed unequal-action pairs** on this corpus.

## Scientific interpretation

This is a **within-corpus observation**, not a universal safety proof. In particular, the conditional key can be lossy for evaluation, best-move identity, and the future opponent's responses even if the current legal actions coincide. The 61 pairs are not independent. The fallback to exact occupancy is essential and must not be confused with uniform compression of all states. Zero observed action disagreements does not justify pruning or a claim of strategic equivalence.

The current key retains the mover's men and forward enemy blockers only when the mover has no king and no capture; other cases are represented exactly. Any extension must test promotions, backward captures, multi-captures, flying kings and cross-game held-out data before claiming a safety property.

## Next steps

1. Extend adversarial unit tests around backward captures and blocked landing squares.
2. Evaluate independent held-out games with a fixed, preregistered signature.
3. Test whether identical legal-action sets lead to different successor states, evaluations and best moves.
4. Distinguish *representation collision reduction* from *search pruning*: the latter requires a separate correctness argument and benchmark.
