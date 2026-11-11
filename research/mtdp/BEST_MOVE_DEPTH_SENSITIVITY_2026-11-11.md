# MTDP — sensitivity to Scan search depth, 2026-11-11

The comparison uses the [original depth-8 protocol](BEST_MOVE_PROTOCOL.md)
and varies only the successor search depth. The original depth-8 JSON was
reproduced byte for byte. Both reports have identical PDN digests, replay
outcomes, Scan binary digest, ordered FEN pairs, source games, eligibility and
scored legal actions. No pair was selected or dropped based on the scores.

## Results

| Pairing | Scored pairs | Disjoint optima at 8 | Disjoint optima at 12 | Disjoint at both |
| --- | ---: | ---: | ---: | ---: |
| Two novel positions from separate games | 40 | 21 | 18 | 12 |
| PC Blues position paired with a novel position | 95 | 46 | 46 | 35 |

At depth 12, the deterministic best-move picks agreed in 17/40 and 36/95
pairs respectively. In the primary cohort, nine pairs regained a common
optimum, while six lost their common optimum. The unchanged disjoint count
in the transfer cohort masks 11 pairs changing status in each direction.
These counts allow all ties reported by Scan.

| Transfer direction | Positive costs at 8 → 12 | Mean cost including zeros at 8 → 12 (men) | Maximum at 8 → 12 (men) | Cost ≥ 0.50 at 8 / 12 / both |
| --- | ---: | ---: | ---: | ---: |
| Holdout, FEN order A to B | 23 → 22 | 0.0315 → 0.0310 | 0.22 → 0.14 | 0 / 0 / 0 |
| Holdout, FEN order B to A | 25 → 19 | 0.0433 → 0.0383 | 0.40 → 0.31 | 0 / 0 / 0 |
| PC Blues to holdout | 47 → 50 | 0.0902 → 0.0609 | 1.37 → 1.35 | 4 / 2 / 2 |
| Holdout to PC Blues | 50 → 55 | 0.1505 → 0.1566 | 2.77 → 2.75 | 6 / 6 / 6 |

All costs used ordinary Scan evaluations. The threshold of 0.50 men is
descriptive. The two PC Blues-to-holdout transfers above that threshold at
both depths kept the same source pick and destination best move:

| PC Blues game index | Lidraughts game index | Transferred move | Best move on destination | Depth 8 → 12 cost (men) |
| --- | ---: | --- | --- | ---: |
| 17 and 25 (same source FEN) | 8 | 16-21 | 5-10 | 1.30 → 1.29 |
| 16 | 33 | 29-24 | 32-28 | 1.37 → 1.35 |

The signature loses enough information to change Scan's best move at both
budgets on observed pairs. Results are descriptive because pairs reuse
positions and games, and the external sample is primarily online bullet.
The loss is a fixed-budget evaluation difference on Scan's scale.

## Reproduction

Use the [depth-8 reproduction command and pinned inputs](BEST_MOVE_BASELINE_2026-11-11.md#reproduction)
twice. Use `--depth 8 --output /tmp/mtdp-d8.json` for the first run and
`--depth 12 --output /tmp/mtdp-d12.json` for the second. Preserve the input
basenames. Then run:

```sh
python -m research.mtdp.best_move_depth_comparison /tmp/mtdp-d8.json /tmp/mtdp-d12.json
sha256sum /tmp/mtdp-d8.json /tmp/mtdp-d12.json
```

| Report | SHA-256 |
| --- | --- |
| Depth 8 | `13d957075c9c44c1502fc663cff07bf2856459179327f55a5a8978c31b52c8f7` |
| Depth 12 | `29cd0c74a7e9469bcb5bf3775558f8f52ba975949d3637bbe4e07a2c031189b0` |

Two depth-12 runs produced byte-identical JSON. All 58 MTDP tests passed
in the remote workspace. At the input commit, the
[CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656811)
and [downstream checks](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656712)
were green. Downstream archived the PC Blues audits, with the depth
comparison executed separately using the pinned Scan binary.

**Next action:** freeze a single refinement that adds typed opponent
occupancy within two diagonal steps of the mover's men. Use an additional
set of games with no shared trajectories or exact paired FENs with the
development and prior holdout data. Compare the refinement with the
original signature at depth 12 on collision coverage and the count of
transfers costing at least 0.50 men. Report both the losses removed and
the pairs lost by refinement.
