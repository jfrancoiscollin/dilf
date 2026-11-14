# Native-order tie-break with separately metered exact-score probes

The [frozen protocol](PROSPECTIVE_TIEBREAK_PROTOCOL.md) was tested on
all 473 common positions. For every legal action, a separate fresh-table
search visited that action first in the full depth-one window. The
selector consumed the Jass legal order and these independently exact
scores. Archived native winners and Scan target scores were reserved
for validation and scoring. The original LCB and native searches
reproduced their receipts and traces apart from elapsed time.

There were 97 verified ties and 376 unique maxima. The rule changed
48 depth-one winners. The control replay preserved the LCB depth-one
visit order, action log, returned score and node count on every
position, then used the ordinary root bookkeeping for its winner.
The control matched native root order at depth two on all 473 positions
at each budget. Every search reached its requested budget.

| Nodes per main replay | Original LCB disagreements with native | Control disagreements with native | Scan-16 optima LCB / control |
| --- | ---: | ---: | ---: |
| 10,000 | 16 | 0 | 138 / 136 |
| 50,000 | 20 | 0 | 153 / 155 |
| 200,000 | 16 | 0 | 142 / 146 |

At 50,000 nodes the paired disagreement rate fell by 4.23 percentage
points, with an arena/game bootstrap interval of [−6.43, −1.29].
CARZrQpl went from 16/348 to 0/348 and each other arena went from one
disagreement to zero. Omitting any arena gave a reduction of 3.20 to
4.55 points. On 469 ordinary pairs, control-minus-LCB mean Scan regret
was −0.503 centimen. Five positions gained optimum status and three
lost it. The four categorical comparisons were losses in both arms.

## Cost and scope

The main replay uses the stated budget. Selection used 50,950,000
additional nodes across 473 positions, including the preliminary LCB
replay and the complete auxiliary searches. The depth-one portions of
the per-action probes consumed 316,542 nodes. The control's depth-one
visit itself used the same nodes as LCB, an average of 1.07 fewer than
native. These results establish agreement on the frozen cohort with
separately metered probes. Practical strength and an end-to-end
equal-compute advantage remain untested.

PC Blues replay accepted all 26 games. The native legal catalogue was
deterministic on all 1,864 positions and agreed with FMJD after folding
equivalent capture paths to identical successors. One fixture (game 24,
ply 43) had three keys with two paths each and fails the strict path
bijection. This fixture is outside the quiet experimental cohort,
whose live move keys are checked for uniqueness.

## Reproduction

Build the pinned [intervention runner](TIE_INTERVENTION_2026-11-14.md#reproduction)
using the [build freeze](prospective-tiebreak-freeze.json).
The measured runner digest is
`d372a3347d452e6c6be23ad6858d0bcddf4626eb84ad21a9e7640ddd79527856`
(GCC 14.2.0, CMake 4.4.4). From the DILF root:

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
scratch=$(mktemp -d)
receipts=()
for event in uG0fGZzB l45uk39x GYEtKzUg MtDQWBNR CARZrQpl; do
  python -m research.mtdp.jass_benchmark.spatial_prospective \
    --replication "$rep" --runner "$JASS_BUILD/mtdp_jass_benchmark" \
    --arena "$event" --output "$scratch/$event.json"
  receipts+=("$scratch/$event.json")
done
python -m research.mtdp.jass_benchmark.spatial_prospective \
  --replication "$rep" --receipts "${receipts[@]}" --output "$scratch/report.json"
gzip -dc "$rep/prospective-tiebreak-results.json.gz" | cmp - "$scratch/report.json"
```

Next, freeze an end-to-end control with a budget that includes
verification. Use full-window depth-one probes that stop after the
first action, account for all their nodes, then compare against
native on a fresh chronological holdout.
