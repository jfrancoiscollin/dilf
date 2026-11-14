# Depth-one score ties in the LCB versus native comparison

All 48 positions with different depth-one winners at 50,000 nodes
had the same winning Jass score for LCB and native. Each winner
also returned exactly that score when replayed first, inside its
full search window with a fresh transposition table. This includes
all 20 positions where the two arms still chose different moves
at the end of the search. The depth-one disagreements are therefore
ties between the observed winners under this replay.

The first replay used both archived orders. It reproduced all 96
search receipts, apart from wall-clock timing, and every structured
root-order trace. The score log includes the alpha and beta bounds,
because a later move can return a bound rather than an exact score.
The forced-first check evaluates each of the two observed winners
at the first root action to establish the tie independently of
such bounds. It makes no assertion about the exact scores of the
other root actions. The [audit receipt](depth-one-ties.json.gz)
records the original logs and forced-first scores per position.

## Reproduction

From the repository root, use the original pinned
[benchmark build](../PROTOCOL.md#reproduction).

```bash
rep=research/mtdp/jass_benchmark/spatial-jass/replication
python -m research.mtdp.jass_benchmark.spatial_depth_one \
  --replication "$rep" --runner "$JASS_BUILD/mtdp_jass_benchmark" \
  --output /tmp/mtdp-depth-one-ties.json
gzip -dc "$rep/depth-one-ties.json.gz" | cmp - /tmp/mtdp-depth-one-ties.json
```

The audit reproduced byte for byte under Python hash seeds 7 and 61.
Next, compare the archived 20 persistent and 28 resolved disagreements
at 50,000 nodes. Record their Scan regret and the first common depth at
which their best moves agree, retaining any later divergence in the
trace. This measures whether persistent depth-one ties matter to the
final Scan reference without changing the search.
