# Early root search at 50,000 nodes

This descriptive comparison uses the archived LCB and native Jass
traces on all 473 common positions. All arms reached 50,000 nodes.
The initial root order differed on 470 positions. The depth-one
winner agreed on 425 positions, and the depth-two root order agreed
on every one of those 425. The final move also agreed in those cases.

The remaining 48 positions already had different best moves at
depth one. Of those, 28 ended with the same move and 20 ended with
different moves. The depth-one difference therefore identifies all
20 final disagreements in this sample. These observations compare
root choices and do not establish a causal contribution from the
early winner.

At depth one, LCB used fewer nodes on 183 positions, the same count
on 119, and more on 171. The average difference (LCB minus native)
was −1.07 nodes, with a range of −78 to +76. Among the 20 final
disagreements it was −0.90 nodes, ranging from −30 to +31.

## Reproduction

Use the [trace comparison commands](NATIVE_CONVERGENCE_2026-11-14.md#reproduction)
with `--full-cohort`. Compare the output bytes with:

```bash
gzip -dc "$rep/native-early-search.json.gz" | cmp - /tmp/mtdp-native-convergence.json
```

The full report and the previous changed-prefix report reproduced
byte for byte. Next, inspect the 48 depth-one disagreements for ties
in Jass's depth-one score. The archived traces record the selected
move without the per-move scores. Reproduce the depth-one results
on those frozen FENs using the pinned Jass build and log the root
action scores to distinguish tie-breaking from score differences.
