# Spatial Jass replication status

The [02:16 UTC listing on 13 November](20261113T021640Z-tournaments.json)
shows uG0fGZzB underway with a scheduled 02:57 UTC finish. Its detail API
also confirmed it was underway. A second 5+0 standard arena, l45uk39x,
was listed for 08:00–08:57 UTC. The cohort stands at zero of five
published freezes. The chronology check refused the unfinished arena.

After 02:57 UTC, capture a fresh listing and finished detail for
uG0fGZzB, verify two completed exports, and follow the
[freeze protocol](PROTOCOL.md). Publish the freeze and benchmark
manifest before proceeding to the next eligible arena.

## Reproduce the pooled analysis

After five verified freezes and their searches, run from the repository root:

```sh
python -m research.mtdp.jass_benchmark.spatial_replication \
  --arena "$ARENA1" --arena "$ARENA2" --arena "$ARENA3" \
  --arena "$ARENA4" --arena "$ARENA5" --output "$POOLED_SUMMARY"
```

Supply each arena directory in chronological order. Keep its manifest,
provenance, eligible shards, source scores and diagnostic at the paths
used in the pilot. Place the target scores and gzip-compressed paired
JSONL under `results/` as `target.json` and `paired-results.jsonl.gz`.
An arena with no common targets needs its freeze and empty manifest.
The command checks the diagnostic and paired receipts against the frozen
catalogues and Scan references before pooling. It records per-arena
coverage, exact-budget and ceiling outcomes, and changed-move costs.
The archived pilot receipts and a synthetic five-arena packet exercise
the checks and the pooled estimator.
