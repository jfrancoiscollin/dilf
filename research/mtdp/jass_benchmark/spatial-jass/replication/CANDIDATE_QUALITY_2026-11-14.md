# Initial candidate quality before Jass search

This descriptive follow-up compares the two transferred orders on
the same 473 positions from five independent arenas. It uses the
archived Scan 3.1 scores, with source successors at depth 12 and
target successors at depth 16. Tied source scores use the same
bytewise Jass move-key order as the searches. The three-candidate
metric asks whether any move in the list is a target optimum and
uses the best target score available within that list.

| Targets | Metric | Scan optimum LCB / L | Ordinary pairs | Mean LCB minus L regret (centimen) | 95% arena/game bootstrap interval |
| --- | --- | ---: | ---: | ---: | ---: |
| All 473 | First choice | 176 / 165 | 468 | −0.397 | [−1.406, +0.584] |
| All 473 | Best of three | 321 / 326 | 470 | +0.134 | [−0.150, +0.496] |
| 64 changed prefixes | First choice | 29 / 18 | 64 | −2.906 | [−9.635, +6.462] |
| 64 changed prefixes | Best of three | 37 / 42 | 64 | +0.984 | [−1.385, +3.500] |

Positive values mean higher regret with LCB. On the full cohort,
the first choice was optimal only with LCB on 24 positions and only
with L on 13. For best of three the corresponding counts were 19
and 24. Removing CARZrQpl reverses the sign of the full-cohort
first-choice estimate to +0.177 centimen on 124 ordinary pairs.
The best-of-three estimate stays positive when each arena is removed.
At 50,000 nodes, the [completed Jass searches](RESULTS_2026-11-13.md)
found 153 optima with each ordering.

The [machine-readable report](candidate-quality.json) contains the
per-arena estimates, optimum pairs, and individual prefixes and
regrets for all 64 changed positions. The ordinary regret means
exclude categorical outcomes. The optimum counts include all
positions and give credit for ties.

## Reproduction

From the repository root, using the archived receipts:

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
args=()
for event in uG0fGZzB l45uk39x GYEtKzUg MtDQWBNR CARZrQpl; do
  args+=(--arena "$rep/$event")
done
python -m research.mtdp.jass_benchmark.spatial_candidate_quality \
  "${args[@]}" --output /tmp/mtdp-spatial-candidate-quality.json
cmp "$rep/candidate-quality.json" /tmp/mtdp-spatial-candidate-quality.json
```

Next, use the archived 50,000-node receipts to count optimum gains
and losses from the transferred first choice to the final Jass move
for each arm on the 64 changed positions. That paired transition
check can distinguish recovery by search from cases where an initial
optimum was displaced.
