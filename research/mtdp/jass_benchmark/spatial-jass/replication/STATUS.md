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

## Determinism check before the next freeze

L and LCB sometimes supply the same ordered list to the same Jass
position and node budget. With a fresh table and one thread, the
resulting search receipts must agree apart from elapsed time. The
runner checks this before writing new results and the aggregator checks
it again when reading archived receipts. An unexpected difference
identifies the position and budget for diagnosis and retry.

All 96 equal-prefix pairs in the archived KXaMpuNe pilot agreed,
including the three pairs that reached the depth ceiling. A regression
test changes an elapsed time and a search score independently to
verify that the timing variation passes and the score change fails.
The independent three-arena Scan analysis also reproduced its archived
summary byte for byte using the frozen receipts. Local validation
passed 123 MTDP tests and 643 DILF tests. The live Jass catalogue test
was skipped.

The second candidate, l45uk39x, was still scheduled when checked at
07:15 UTC on 13 November. After 08:57 UTC, verify the completed detail
and two independent final exports, then reproduce the second freeze.
The five-freeze gate still applies to all new scoring.

## Engine rebuild and archived pilot replay on 13 November

The [08:21 UTC listing](20261113T082159Z-tournaments.json) shows
l45uk39x underway, with a scheduled finish at 08:57 UTC. GYEtKzUg
and MtDQWBNR are the next listed standard 5+0 candidates, scheduled
for 11:00–11:57 and 14:00–14:57 UTC. The cohort has one verified
arena. The next action is to check the finished listing and detail
for l45uk39x and compare two independently fetched final PDNs.

A fresh checkout restored all 14 archived Lidraughts exports in the
first arena's provenance inventory. Every SHA-256 matched. A second
download of uG0fGZzB also matched byte for byte. The pinned FMJD
adapter, the two club PDNs and the Scan 3.1 executable, configuration
and evaluation data passed the freeze input checks. Rebuilding the
first freeze under hash seed 61 reproduced its six position shards,
score plan and replay audit byte for byte. The new provenance receipt
reflects the checkout and output path used for this rehearsal.

GCC 14.2.0 and CMake 4.4.4 rebuilt the pinned Jass catalogue and
initial-only benchmark runner with their archived SHA-256 values.
Using the rebuilt catalogue under hash seed 7 reproduced the first
arena manifest byte for byte. All 124 MTDP tests, including the live
catalogue test, all 643 DILF tests and the Jass CTest suite passed.

To reproduce the engine check, follow the
[pilot build and run commands](../PROTOCOL.md#reproduction), using
the published pilot manifest, Scan receipts and source diagnostic.
Replaying those frozen inputs with the rebuilt runner reproduced all
306 root-order traces byte for byte after filtering by budget in
record order. The 102 paired receipts and the summary also agreed
after omitting the timing fields. This replay used the archived pilot.
Scoring on the replication cohort starts after all five freezes.

## Second verified freeze on 13 November

The [09:14 UTC listing](20261113T091433Z-tournaments.json) and
[finished detail](l45uk39x-evidence/event-metadata.json) identify
l45uk39x as the second eligible completed arena. Two final PDN
downloads made with different request URLs matched byte for byte
(83,924 bytes). FMJD replay accepted 70 of 72 records, with one
duplicate trajectory and one ambiguous capture record quarantined.
The [candidate log](l45uk39x-evidence/candidate-log.json) and
[provenance](l45uk39x/provenance.json) record the selection,
independence checks and input digests.

The freeze contains 4,392 eligible positions. L matches 29, LCB
matches 12 and LMB matches 10. The [manifest](l45uk39x/manifest.json)
contains all 12 common L/LCB positions from nine owning games.
One selects a different PC Blues source under LCB. Jass and FMJD
agree on all 115 legal actions at those targets. The freeze and
manifest reproduced byte for byte with Python hash seeds 7 and 61.
All 124 MTDP tests, including the live catalogue check, and 643
DILF tests passed.

Two of five arenas are now frozen. The next candidate is GYEtKzUg,
scheduled for 11:00–11:57 UTC on 13 November. After it finishes,
refresh the chronology, check the detail and compare two final PDNs.
Keep both replication exports in the exclusion inventory and pass
l45uk39x as the sixth ordered `--previous-freeze`. All five freezes
must be published before new Scan or Jass scoring.

## Paired category reporting before the third freeze

The pooled summary now counts the chosen Scan categories jointly
for each control and LCB on budget-complete positions. Each changed
move also records both chosen categories and the reference category.
An ordinary pair reports its signed regret difference in centimen.
A pair with a categorical result carries no numerical difference.
The primary endpoint and its population follow the original protocol.

Replaying the archived pilot at 50,000 nodes gave 31 ordinary pairs
and two loss-to-loss pairs for each comparison. Against native Jass,
the two changed moves had regret differences of −10 and +3 centimen.
A synthetic ordinary-to-loss example verified the categorical path.

The [10:19 UTC listing](20261113T101921Z-tournaments.json) still puts
GYEtKzUg next, scheduled for 11:00–11:57 UTC on 13 November. Check
its final listing and detail after 11:57 UTC and fetch two independent
final PDNs before freezing. The cohort remains at two verified arenas.

## Live source and target action check

Manifest preparation now compares the pinned Jass and FMJD action
mappings on the selected PC Blues source positions as well as the
held-out target positions. For each pair it verifies that the
canonical actions have the same Jass keys at both ends before the
source ranking can be used at the target.

The first two manifests reproduced byte for byte with the pinned
catalogue. Counting distinct positions within each role and arena,
the check covered 35 source positions (341 actions) and 37 target
positions (364 actions). Run `spatial_jass prepare` on each published
provenance with the [pilot command](../PROTOCOL.md#reproduction)
and compare its output to the published manifest.

The [11:12 UTC listing](20261113T111225Z-tournaments.json) shows
GYEtKzUg underway with a scheduled finish at 11:57 UTC. After that
time check the finished listing and detail and fetch its final PDN
twice before the third freeze. The five-freeze scoring gate still
applies.
