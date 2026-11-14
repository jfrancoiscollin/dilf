# Exact outcomes for native disagreements covered by the six-piece bitbase

Two of the 20 LCB versus native Jass final-move disagreements at
50,000 nodes have six pieces. The other 18 have 38 or 40 pieces.
The two covered positions are both theoretical losses for Black.
The seven legal successors across the two positions are also
losses for Black, including both published choices on each position.

| Position | LCB | Native Jass | Outcome for Black after either move |
| --- | --- | --- | --- |
| B:W18,21,35,50:B8,33 | 33-39 | 33-38 | Loss |
| B:WK3,16,19,24:B15,37 | 37-41 | 37-42 | Loss |

The first position changed the sign of the numerical regret
difference between Scan depths 16 and 18. The second accounted for
the largest depth-18 difference, +291 centimen. Neither changes
win/draw/loss under optimal play. The bitbase provides no distance
to a win or conversion. This exact check covers two disagreements.

## Reproduction

Set up the [separate Scan installation](LARGEST_NATIVE_DISAGREEMENT_2026-11-14.md#reproduction)
with the same bitbases and pinned FMJD adapter. From the repository root:

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
python -m research.mtdp.jass_benchmark.spatial_endgame \
  --disagreements "$rep/native-depth18/summary.json" \
  --table-scan "$TABLE_SCAN_ROOT/scan_linux" --archive "$BITBASE_ZIP" \
  --output /tmp/mtdp-native-disagreements-wdl.json
cmp "$rep/native-disagreements-wdl.json" /tmp/mtdp-native-disagreements-wdl.json
```

Python hash seeds 7 and 61 reproduced the receipt byte for byte.
The original single-position principal-variation receipt reproduced
after extracting the shared probe code.

Next, design a controlled replay of the 48 verified depth-one ties.
Keep the LCB visit order, engine and 50,000-node budget fixed and
force the archived native winner only when it ties at depth one.
Check depth-two order and final choices against the original native
receipts to isolate how much is explained by the tie winner.
