# Exact endgame check of the largest native disagreement

On `B:WK3,16,19,24:B15,37`, LCB chose 37-41 and native Jass
chose 37-42 at 50,000 nodes. The six-piece Scan bitbase gives Black
a loss at the root and after every legal move.

| Black move | Exact result for Black | Scan depth-18 score for White | First reply in Scan PV |
| --- | --- | ---: | --- |
| 15-20 | Loss | +10.09 | 24x15 |
| 37-41 (LCB) | Loss | +10.29 | 3-14 |
| 37-42 (native) | Loss | +7.38 | 19-13 |

The 2.91-pawn evaluation gap leaves the theoretical outcome unchanged.
The [receipt](largest-native-disagreement-endgame.json) records the
full principal variations, successor FENs, tablebase archive digest
and executable digest. Scan's terminal bitbase results are for the
side to move. Each successor has White to move, so its win is recorded
as a loss for Black. The depth-18 evaluations use the original
configuration with bitbases disabled and reproduce the published
scores for the two selected moves. The bitbase reports win/draw/loss
and provides no distance to a win or conversion.

## Reproduction

Use the pinned Scan and FMJD adapter from the
[scoring handoff](STATUS.md#scoring-handoff). Download the
[standard Scan bitbases](https://hjetten.home.xs4all.nl/scan/bb.zip)
and extract the archive into a separate Scan directory, so the tables
are in `data/bb`. Copy the pinned engine, `data/eval` and
`scan.ini` there, then change only `book` to `false`,
`tt-size` to `18` and `bb-size` to `6` in the copy.

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
python -m research.mtdp.jass_benchmark.spatial_endgame \
  --scan "$SCAN_ROOT/scan_linux" --table-scan "$TABLE_SCAN_ROOT/scan_linux" \
  --archive "$BITBASE_ZIP" --output /tmp/mtdp-spatial-endgame.json
cmp "$rep/largest-native-disagreement-endgame.json" /tmp/mtdp-spatial-endgame.json
```

Both hash seeds 7 and 61 reproduced the receipt byte for byte.
Next, identify all other positions with at most six pieces among the
20 final LCB/native disagreements. Probe the root and both chosen
successors to count any exact changes in win/draw/loss within that
subset.
