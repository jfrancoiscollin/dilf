# LCB versus native root traces on changed-prefix positions

On the 64 positions where LCB and the legal-actions control supplied
different prefixes, LCB and native Jass used different depth-one root
orders on all 64. At each of 10,000, 50,000 and 200,000 nodes, they
nevertheless chose the same best move at depth one, at every subsequent
depth completed by both arms, and at their respective final depths.
All 192 position-budget pairs reached their budgets.

The agreement was already present at depth one. These counts describe
the selected move and allow the search paths and node usage within an
iteration to differ. The [full-cohort results](RESULTS_2026-11-13.md)
also record LCB/native final-move differences outside these 64 positions.

The [trace report](native-convergence.json) records the input digests,
both moves and common completed depths for each position. The analysis
uses the last successful window at each depth, up to each arm's reported
completed depth. It compares depths shared by LCB and native, even
when L completed fewer depths. The archived receipts and traces pass
the replication validator before comparison.

## Reproduction

From the repository root:

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
args=()
for event in uG0fGZzB l45uk39x GYEtKzUg MtDQWBNR CARZrQpl; do
  args+=(--arena "$rep/$event")
done
python -m research.mtdp.jass_benchmark.spatial_native_convergence \
  "${args[@]}" --output /tmp/mtdp-native-convergence.json
cmp "$rep/native-convergence.json" /tmp/mtdp-native-convergence.json
```

The report reproduced byte for byte under Python hash seeds 7 and 61.
Next, on all 473 positions at the primary budget, compare the depth-one
winner and node cost, and check whether the depth-two root order agrees
when the depth-one winner agrees. Report the subset where LCB and native
return different final moves to locate where their search paths diverge.
