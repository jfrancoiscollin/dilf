# First-choice to final-move transitions at 50,000 nodes

This descriptive check follows the two transferred orders on the 64
positions where their initial three-move prefixes differed. It compares
the first move in each prefix with the corresponding Jass move at
50,000 nodes, using the same depth-16 Scan 3.1 target scores for both.
All three arms reached the budget on all 64 positions.

| Initial and final Scan optimum status | LCB | L |
| --- | ---: | ---: |
| Initial and final optimum | 16 | 4 |
| Only final move optimal | 3 | 15 |
| Only initial move optimal | 13 | 14 |
| Neither optimal | 32 | 31 |
| Initial optimum total | 29 | 18 |
| Final optimum total | 19 | 19 |

The initial 11-position advantage for LCB disappeared after search.
LCB kept optimum status more often, while L recovered it in more cases.
An optimum-to-optimum transition can include a switch to a tied move.
The final moves differed on five positions. The largest arena supplied
55 of 64 positions, including 14 of the 15 recoveries with L and all
three recoveries with LCB. The counts describe this subset.

The [JSON report](search-transitions.json) records each transition,
both moves and the ordinary regret change where both scores permit
it. Inputs are bound to the published manifests and score and search
receipts. The paired results and root traces are validated first.

## Reproduction

Run from the repository root.

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
args=()
for event in uG0fGZzB l45uk39x GYEtKzUg MtDQWBNR CARZrQpl; do
  args+=(--arena "$rep/$event")
done
python -m research.mtdp.jass_benchmark.spatial_search_transitions \
  "${args[@]}" --output /tmp/mtdp-search-transitions.json
cmp "$rep/search-transitions.json" /tmp/mtdp-search-transitions.json
```

The report reproduced byte for byte under Python hash seeds 7 and 61.
Next, test whether LCB's agreement with native Jass on these 64 targets
comes from identical depth-one orders or from later convergence. Match
the archived root traces by FEN and budget and compare the depth-one
order, depth-one best move and final move for both arms.
