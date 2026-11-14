# Prospective multi-arena replication of spatial Jass ordering

The [KXaMpuNe pilot](../KXaMpuNe/results/RESULTS_2026-11-13.md)
had only two changed initial orders among 34 common positions. A fixed
sample of five fresh arenas increases the number of opportunities to
observe a change and allows comparison across events. The pilot and
the earlier three-event Scan study are excluded from this analysis.
Five arenas are a fixed acquisition target. No minimum number of
changed orders or power claim determines when to stop.

## Acquisition

Take the first five eligible completed standard FMJD 5+0 arenas with
starts at or after **2026-11-13 02:00 UTC**, ordered by start time and
then event ID. The [initial listing](initial-listing.json) puts
[uG0fGZzB](https://lidraughts.org/tournament/uG0fGZzB) first,
scheduled for 02:00–02:57 UTC. Preserve all listings, finished details
and documented rejections. An unresolved earlier event holds the gate.
Retry transient acquisition failures. A rejection must rest on format,
confirmed unavailability, independence or replay and be recorded before
scoring. Keep an arena with zero common targets or zero changed orders.
Finish and publish all five reproducible freezes before computing any
new scores or Jass outcomes.

Use the [pilot eligibility and source selection](../PROTOCOL.md#cohort-and-freeze).
Exclude earlier PDNs and archived FENs, including the pilot and all
preceding replication arenas. Replay with the pinned FMJD adapter, check
public game IDs and duplicate trajectories, compare two separately
fetched completed PDNs, and reproduce each freeze and Jass/FMJD manifest
under Python hash seeds 7 and 61. A catalogue mismatch blocks scoring
until diagnosed. Preserve every eligible LCB target in the manifest.

From the repository root, follow the
[eighth-study acquisition commands](../../eighth-replication/README.md#continue-acquisition)
with the eighth-study snapshots, the pilot initial and later snapshots
(including its finished listing), this initial listing and all subsequent
replication listings. Run the same freeze command with
`--spatial-jass-replication`, `--pdn-repeat` and the archived rejection
record. Pass `--previous-freeze` once for each of xAnBIxHN, MoXhmT9b,
MIDBy9dl, KXaMpuNe and the already frozen replication arenas, in that order.
Use `spatial_jass prepare` from the pilot protocol on each resulting
provenance. Preserve the same output paths across both hash-seed runs.

## Scores and paired comparisons

Keep the pilot's pinned Scan 3.1 depths of 12 for source successors and
16 for target successors, and Jass budgets of 10,000, 50,000 and
200,000 nodes. Use the same engine revisions, one-thread settings,
fresh transposition table, bytewise tie-break and initial-only ordering.
Publish source-change and ordered-prefix-change counts by arena before
running Jass. Use the pilot's score, diagnose and run commands with
`--replication` on the run command. For an arena with zero common targets,
publish its empty manifest and report zero searches.

The primary endpoint is the position-weighted mean paired difference
(LCB minus L) in ordinary Scan regret at 50,000 nodes. For each budget,
include a target in the main paired summaries when all three arms
reach the requested node count. Record a depth-ceiling receipt with
actual depth and nodes for each affected arm, and report the full-cohort
comparison as incomplete wherever any target hits the ceiling early.
Apply the same rule to all arenas. Treat any other shortfall as a
technical failure to diagnose and rerun with the same inputs. Among
budget-complete targets include both-optimal pairs as zero regret,
and count non-ordinary outcomes and category transitions separately.
Report per-arena counts of eligible, common, changed-source,
changed-order, budget-complete and ordinary pairs.

Secondary summaries use the other budgets, native ordering, and the
pre-search changed-order subset. Report optimum hits, changed moves
and ordinary costs, including the individual costs for changed moves.
Use the existing hierarchical bootstrap (10,000 resamples, seed
20261112), resampling arenas then whole owning games inside arenas,
for contrasts with ordinary observations in at least two arenas.
Report the number of contributing arenas and games. An interval
collapsed at zero with few changed orders describes the observed sample.
Archive the frozen manifests, scoring receipts, node traces and
reproducible pooled summary.

## Next action

After the first candidate's scheduled finish at 02:57 UTC, confirm the
finished listing and detail, fetch its final export twice, then attempt
the first replication freeze. The next scoring gate is five verified
freezes.
