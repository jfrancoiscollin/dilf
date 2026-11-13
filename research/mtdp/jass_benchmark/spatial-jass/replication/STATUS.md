# Spatial Jass replication status

## First verified freeze on 13 November

The [03:13 UTC listing](20261113T031349Z-tournaments.json) and
[finished detail](uG0fGZzB-evidence/event-metadata.json) confirm
uG0fGZzB as the first completed eligible standard 5+0 arena.
Two independently downloaded final PDNs matched byte for byte
(82,319 bytes). FMJD replay accepted 64 of 69 records, with three
duplicate trajectories and two ambiguous capture records quarantined.
The [chronological selection log](uG0fGZzB-evidence/candidate-log.json)
and [provenance](uG0fGZzB/provenance.json) record the selection,
input hashes, independence checks and replay audit.

The freeze contains 4,327 eligible positions. L matches 50,
LCB matches 25, and exact mover occupancy with blockers (LMB)
matches 14. The [benchmark manifest](uG0fGZzB/manifest.json) contains
all 25 common L/LCB positions, from 13 owning games. The pinned Jass
catalogue and the FMJD adapter agree on their 249 target actions.
The freeze and manifest reproduced byte for byte with Python hash
seeds 7 and 61. All 765 tests passed, including the live Jass
catalogue integration.

The study stands at **one of five** verified freezes. The next
candidate in the current listing is [l45uk39x](https://lidraughts.org/tournament/l45uk39x),
scheduled for 08:00–08:57 UTC on 13 November. Refresh the listing
and confirm the chronology before attempting the second freeze.
Include the first arena export in the exclusion inventory and its
provenance as the fifth `--previous-freeze`. Scan and Jass scoring
starts after all five freezes have been published.

## Updated tournament listing

The [05:15 UTC listing on 13 November](20261113T051550Z-tournaments.json)
still lists l45uk39x as the next candidate (08:00–08:57 UTC) and adds
[GYEtKzUg](https://lidraughts.org/tournament/GYEtKzUg) for 11:00–11:57 UTC.
The cohort remains at one verified arena. After 08:57 UTC, refresh the
listing and verify two independently fetched final exports for l45uk39x.

## Verify all five manifests before scoring

Run the command below with the five published arena directories in
chronological order and add `--check-freezes`. Save the output as the
scoring input inventory. The check works before Scan receipts exist.
It verifies the selected PC Blues sources, legal actions, fixed budgets
and cross-arena independence, and records each manifest digest. The first
published freeze passed its manifest check on a clean checkout.

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
