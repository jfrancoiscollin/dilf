# Fixed-budget outcomes after a depth-one tie

The 48 positions come from the depth-one LCB/native score audit.
All arms used 50,000 nodes. Final regret uses the archived Scan 3.1
depth-16 target reference. Positive differences mean higher regret
for LCB. This is a descriptive comparison selected by the observed
depth-one disagreement.

| Final moves | Positions | Scan optima LCB / native | Lower / equal / higher LCB regret | Mean LCB minus native regret (centimen) |
| --- | ---: | ---: | ---: | ---: |
| Same | 28 | 13 / 13 | 0 / 28 / 0 | 0 |
| Different | 20 | 3 / 5 | 10 / 2 / 8 | +11.8 |

All 48 regret pairs were ordinary. The different-move costs ranged
from −18 to +243 centimen. The +243 position contributes more than
the sum of all 20 differences (+236). Omitting that one observed
position gives −0.37 centimen across the remaining 19, a descriptive
sensitivity only. The second-largest cost was +51. Both cases were
from CARZrQpl and native chose a Scan optimum in each.

The two arms agreed at least once at a common completed depth on
15 of the 20 positions with different final moves. They diverged
again at a common depth in 14 of those cases. Among the 28 positions
with the same final move, 27 agreed at a common depth and nine
diverged again before the end. One reached the same final move at
different completed depths without any agreement at a shared depth.
The [JSON receipt](tie-outcomes.json) records those paths and costs.

## Reproduction

From the repository root:

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
args=()
for event in uG0fGZzB l45uk39x GYEtKzUg MtDQWBNR CARZrQpl; do
  args+=(--arena "$rep/$event")
done
python -m research.mtdp.jass_benchmark.spatial_tie_outcomes \
  --replication "$rep" "${args[@]}" --output /tmp/mtdp-tie-outcomes.json
cmp "$rep/tie-outcomes.json" /tmp/mtdp-tie-outcomes.json
```

Both hash seeds 7 and 61 reproduced the report byte for byte.
Next, rescore the 20 final LCB/native disagreements at Scan depth
18, including all legal successors. Check whether the +243 and +51
costs persist, keeping the selections and primary reference fixed.
