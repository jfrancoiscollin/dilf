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
Archive the root traces under `results/traces-10000.jsonl.gz`,
`results/traces-50000.jsonl.gz` and `results/traces-200000.jsonl.gz`,
retaining one record per FEN, budget and arm. The aggregator checks
these archives against the paired receipts and frozen move lists.
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

## Third verified freeze on 13 November

The [12:16 UTC listing](20261113T121652Z-tournaments.json) and
[finished detail](GYEtKzUg-evidence/event-metadata.json) confirm
GYEtKzUg as the third eligible arena. Two separately fetched final
PDNs matched byte for byte (193,304 bytes). FMJD replay accepted
151 of 165 records, with eight duplicate trajectories and six
rejected records. The [chronology](GYEtKzUg-evidence/candidate-log.json)
and [provenance](GYEtKzUg/provenance.json) preserve the acquisition
and exclusion evidence.

Of 9,839 eligible positions, L matches 139, LCB 55 and LMB 38.
The [manifest](GYEtKzUg/manifest.json) includes all 55 common L/LCB
targets from 27 owning games. Four targets select a different
PC Blues source under LCB. Jass and FMJD agree on all 555 target
actions and the corresponding source mappings. The complete freeze
and manifest reproduced byte for byte with Python hash seeds 7 and
61. All 127 MTDP and 643 DILF tests passed.

Three of five arenas are frozen, with 92 common targets so far.
The next candidate is MtDQWBNR on 13 November, scheduled for
14:00–14:57 UTC. After it finishes, verify its final listing,
detail and two exports. Keep the three frozen exports in the
exclusion inventory and add GYEtKzUg as the seventh ordered
`--previous-freeze`. Start new scoring after all five freezes
are published.

## Input inventory before the fourth freeze

On the published three-arena cohort, `validate_replication_history`
and `previous_inputs` verified 18 exclusion PDNs and 101 archived
manifests and shards covering 72,697 distinct excluded FENs. To
repeat the check, supply the seventh study's provenance first to
`previous_inputs`, followed by the three eighth-study provenances,
the KXaMpuNe pilot and the three replication freezes in order. Pass
the restored PDN directory and the pinned FMJD checkout. The
`read_freeze` and `score_catalogue` checks give the following
workload for the three published manifests:

| Arena | Source actions at depth 12 | Target actions at depth 16 | Planned Jass searches |
| --- | ---: | ---: | ---: |
| uG0fGZzB | 225 | 249 | 225 |
| l45uk39x | 116 | 115 | 108 |
| GYEtKzUg | 424 | 555 | 495 |
| Total | 765 | 919 | 828 |

Actions count distinct FEN/action pairs within each arena and role.
Search counts cover three budgets and three arms per target. These
counts come from the frozen manifests before scoring.

The [13:16 UTC listing](20261113T131647Z-tournaments.json) and event
details confirm MtDQWBNR is scheduled for 14:00–14:57 UTC. The next
listed candidate, CARZrQpl, is a six-hour standard 5+0 arena
scheduled for 16:00–22:00 UTC. Refresh the chronology after 14:57 UTC
and check two final MtDQWBNR exports before freezing it.

## Scoring handoff

With the pinned Scan 3.1 build and FMJD adapter, the archived
KXaMpuNe pilot reference reproduced byte for byte at both registered
depths. The source run covered 302 actions at depth 12 (13 seconds)
and the target run covered 323 actions at depth 16 (120 seconds).
Regenerating the source diagnostic from the new receipt also
reproduced the published bytes. The replay used the archived pilot.

The [14:19 UTC listing](20261113T141948Z-tournaments.json) shows
MtDQWBNR underway. Its scheduled finish remains 14:57 UTC on
13 November. The next step is to verify the finished detail and
compare two final PDNs before the fourth freeze.

After publication of all five freezes, save the output of
`spatial_replication --check-freezes` before starting Scan. For
each nonempty manifest, use the
[pilot scoring commands](../PROTOCOL.md#reproduction) with Scan
depth 12 for `source.json` and depth 16 for `results/target.json`.
Generate `source-diagnostic.json` and publish the source and
ordered-prefix change counts before running Jass. If a Scan
attempt fails, diagnose the reported FEN and action, then retry
that arena and role with the same manifest and settings.

Use `spatial_jass run --replication` for each nonempty arena.
Point its output at a fresh directory. Preserve the root-order
traces, the runner summary and the paired receipts. For pooling,
place the paired receipts under `results/` with:

```sh
gzip -n -c "$JASS_OUTPUT/paired-results.jsonl" > "$ARENA/results/paired-results.jsonl.gz"
python - "$JASS_OUTPUT/root-order-traces.jsonl" "$ARENA/results" <<'PY'
import gzip
import json
import sys
from pathlib import Path

from research.mtdp.jass_benchmark.spatial_jass import BUDGETS

rows = Path(sys.argv[1]).read_bytes().splitlines(keepends=True)
for budget in BUDGETS:
    archive = Path(sys.argv[2]) / f"traces-{budget}.jsonl.gz"
    with archive.open("wb") as out, gzip.GzipFile(fileobj=out, filename="", mode="wb", mtime=0) as stream:
        stream.writelines(row for row in rows if json.loads(row)["budget"] == budget)
PY
```

Run the five-arena aggregation above after the per-arena files
are in place. Repeat aggregation and compare the summary bytes.

## Fourth verified freeze on 13 November

The [15:19 UTC listing](20261113T151904Z-tournaments.json) and
[finished detail](MtDQWBNR-evidence/event-metadata.json) confirm
MtDQWBNR as the fourth eligible arena. Two separately fetched final
PDNs matched byte for byte (174,747 bytes). FMJD replay accepted
140 of 151 records. Five were duplicate trajectories and six used
ambiguous capture notation. The
[chronology](MtDQWBNR-evidence/candidate-log.json) and
[provenance](MtDQWBNR/provenance.json) record those checks.

Of 8,983 eligible positions, L matches 90, LCB 33 and LMB 24.
The [manifest](MtDQWBNR/manifest.json) includes 33 common targets
from 22 owning games. Three targets select a different PC Blues
source under LCB. Jass and FMJD agree on the 344 target actions
and the corresponding source mappings. The freeze and manifest
reproduced byte for byte with Python hash seeds 7 and 61.
All 127 MTDP and 643 DILF tests passed.

Four of five arenas are frozen, with 125 common targets. The next
listed candidate is CARZrQpl, scheduled for 16:00–22:00 UTC on
13 November. Recheck the chronology and obtain two final exports
after it finishes. Keep the four frozen exports in the exclusion
inventory and add MtDQWBNR as the eighth ordered
`--previous-freeze`. After publishing the fifth freeze, run the
five-manifest check and follow the scoring handoff above.

## Stop reason validation while the fifth arena runs

The spatial Jass reader now checks the stop reason together with the
consumed node count before saving search receipts. An exact-budget
receipt must report `nodes`. The explicit depth-64 ceiling receipt
continues to be recorded when it legitimately uses fewer nodes.
This makes the live check agree with the pooled validation and
identifies the FEN, requested budget, stop reason and depth on failure.
The regression test rejects a time-stop receipt even when the node
count equals the requested budget. The archived pilot replay
reproduced all 306 traces byte for byte and the paired receipts
after excluding elapsed times. All 127 MTDP and 643 DILF tests passed.

The [16:10 UTC listing](20261113T161020Z-tournaments.json) and
tournament detail confirmed CARZrQpl was underway. Its scheduled finish
is 22:00 UTC on 13 November. Recheck the finished listing and detail,
then fetch two final exports for the fifth freeze.

## Rehearsal with identical initial orders

A rehearsal on the archived KXaMpuNe pilot checked that
`spatial_jass run --replication` retains an arena whose two
transfer rules always produce the same ordered prefix. Remove the
two FENs in the pilot diagnostic's `changed_prefix_targets` from
`benchmark_targets` and from the target side of `targets`. For
each archived Scan receipt, retain the FENs in the corresponding
`score_catalogue` of the reduced manifest and set `cohort_sha256`
to the reduced manifest's digest. Regenerate the diagnostic with
`spatial_jass diagnose` and use the pinned pilot runner.

The pilot guard returned the expected error without the replication
flag. With the flag, Jass ran all 288 planned searches on the 32
retained positions. At each of the three budgets, all arms used the
full budget on 31 positions and reached the depth ceiling early on
one. L and LCB selected the same move in every complete comparison.
The diagnostic and changed-prefix summaries recorded zero positions
with a changed order. This rehearsal used existing Scan scores.

The [17:11 UTC listing](20261113T171132Z-tournaments.json) confirms
CARZrQpl is underway with a scheduled finish at 22:00 UTC. The next
listed standard 5+0 arena is 8uv85HML at 23:00 UTC. Check CARZrQpl's
completed detail and two final exports before the fifth freeze.

## Paired optimum counts

The pooled summary now reports joint optimum hits for LCB versus
each control at every budget and in the changed-prefix subset. It
counts both arms optimal, LCB alone optimal, the control alone
optimal and neither optimal on positions where all arms reached
the budget. The counts use the pinned Scan reference, including ties.
This supplements the registered paired regret endpoint.

The archived pilot regression verifies the 50,000-node counts on
33 budget-complete positions. LCB and L both hit an optimum on six
positions and neither did on 27. Against native Jass, five positions
had both optimal and one had LCB alone optimal. These are checks
against existing pilot receipts.

The [18:18 UTC listing](20261113T181825Z-tournaments.json) shows
CARZrQpl still underway. The next acquisition is its finished detail
and two final PDNs after 22:00 UTC, followed by the fifth freeze.

## Root trace audit before scoring

The pooled analysis now requires exactly one root-order trace per
frozen target, budget and arm. It reconstructs the initial ordering
and subsequent adaptive ordering from the legal catalogue, compares
the observed visits, and checks final nodes, completed depth, chosen
move and nodes at common depth against the paired receipts. An
interrupted aspiration retry invalidates the current depth even when
an earlier window at that depth completed.

`read_arena` validates all 306 traces and 102 paired receipts in the
archived pilot. Regression tests reject missing and duplicate traces,
a corrupted adaptive order and a mismatched final node count. All
131 MTDP and 643 DILF tests passed locally.
The [19:18 UTC listing](20261113T191845Z-tournaments.json) shows
CARZrQpl underway. After 22:00 UTC, check the finished detail and
compare two final PDNs. Publish the fifth freeze and verify the full
cohort before scoring.

## Acquisition rehearsal before the fifth freeze

Converted the 19:18 UTC listing from the raw API response to the
normalized snapshot format expected by `candidates`. The normalized
receipt retains the original response digest and retrieval time. To
rebuild the chronology, include the eighth-study `*-tournaments.json`
files and the initial and dated listings from both the pilot and this
directory. Pass each file as `--snapshot` to the `candidates` mode of
`multi_event_replication`. A regression test loads the full chronology.

Restored and verified all 19 exclusion PDNs and 113 archived manifests
and shards covering 81,680 excluded FENs. The pinned Scan executable,
configuration and evaluation data match the freeze. The rebuilt Jass
runner and catalogue match the pilot digests and the Jass CTest passed.
On the four published manifests, the pinned FMJD adapter applied all
1,078 source and 1,263 target successors. The four freezes contained
27,541 distinct eligible FENs and 457 distinct public game IDs.
All 132 MTDP and 643 DILF tests passed locally. These checks used no
new Scan scores or Jass search outcomes.

The [20:16 UTC listing](20261113T201634Z-tournaments.json) leaves
CARZrQpl as the next candidate. The acquisition gate correctly
refused it while in progress. After 22:00 UTC, refresh the listing,
check the finished detail and compare two final PDNs. Reproduce and
publish the fifth freeze before scoring.

## Sensitivity to a single arena

The pooled report recomputes the ordinary paired regret mean with each
arena omitted in turn. It preserves position weighting and reports the
remaining pairs, contributing arenas and owning games for each budget
and subset. This is a descriptive check for an effect concentrated in
one tournament. The primary estimate still uses the full frozen cohort
subject to the registered receipt and ordinary-score rules.

The archived pilot yields no remaining estimate when its only arena
is omitted. In a synthetic five-arena test with a known nonzero regret
sum in one arena, the estimate drops to zero when that arena is omitted.
The earlier three-arena Scan summary also reproduced byte for byte
from its archived score receipts. All 132 MTDP and 643 DILF tests passed.

The [21:11 UTC listing](20261113T211141Z-tournaments.json) shows
CARZrQpl still in progress. After 22:00 UTC verify its finished detail
and two final exports, then publish the fifth freeze before scoring.

## Fifth verified freeze on 13 November

The [22:13 UTC listing](20261113T221306Z-tournaments.json) and
[finished detail](CARZrQpl-evidence/event-metadata.json) confirm CARZrQpl
as the fifth chronological candidate. Two separately downloaded final
PDNs matched byte for byte (2,121,245 bytes). FMJD replay accepted
1,701 of 1,831 records, with 56 duplicate trajectories and 74 replay
rejections. The [chronology](CARZrQpl-evidence/candidate-log.json)
and [provenance](CARZrQpl/provenance.json) retain the evidence.

Of 107,129 eligible positions, L matched 1,073 and LCB matched 348.
All 348 common targets from 268 owning games are in the
[manifest](CARZrQpl/manifest.json). LCB selected a different PC Blues
source on 55 positions. Jass and FMJD agreed on the 3,359 target
actions and the source mappings. Both freezes and manifests matched
byte for byte under Python hash seeds 7 and 61. All 132 MTDP and 643
DILF tests passed.

The [five-arena precheck](frozen-cohort.json) binds all 473 targets
and the five manifest digests. With the freeze published, score
sources at Scan depth 12 and targets at depth 16, publish the
ordered-prefix diagnostic, then run Jass at the three fixed budgets.

## Scan source diagnostic before Jass

Scan 3.1 scored 2,366 distinct-within-arena source actions at
successor depth 12. All 64 source changes also changed the ordered
top-three prefix. These diagnostics were computed before Jass.

| Arena | Common targets | Changed sources | Changed prefixes |
| --- | ---: | ---: | ---: |
| uG0fGZzB | 25 | 1 | 1 |
| l45uk39x | 12 | 1 | 1 |
| GYEtKzUg | 55 | 4 | 4 |
| MtDQWBNR | 33 | 3 | 3 |
| CARZrQpl | 348 | 55 | 55 |
| Total | 473 | 64 | 64 |

The target Scan run covers 4,622 actions at successor depth 16.
After target scoring, run all 4,257 Jass searches and aggregate the
paired receipts and root traces. The four other arenas contain nine
changed prefixes between them, so retain the single-arena sensitivity
estimates when interpreting the primary contrast.

## First four scored arenas

The first four arenas have complete Scan depth-16 target references,
paired Jass receipts and root-order archives. Re-reading them with
`spatial_replication.read_arena` verified all 1,125 searches, which
each reached their requested node budget. The four result directories
are ready for the five-arena aggregation. CARZrQpl target scoring and
its 3,132 Jass searches are the remaining inputs. Use the published
depth-12 source receipts and diagnostic unchanged. Check for active
processes or existing complete receipts before restarting a job.

## Completed fixed-budget replication

All five Scan depth-16 target references, all 4,257 Jass searches,
and the audited pooled summary are published. Both aggregation runs
reproduced identical bytes. See the [results](RESULTS_2026-11-13.md)
for the primary contrast and individual disagreement costs. The next
scientific check is a depth-18 Scan reference sensitivity on the five
primary-budget LCB-versus-L disagreements, using the archived Jass
choices unchanged.

## Scan depth-18 check of the five disagreements

All 48 legal successors were rescored with the pinned Scan 3.1
build. The direction of all five costs remained the same and
one LCB move became optimal at depth 18. See the
[depth sensitivity report](depth18/RESULTS_2026-11-14.md) for
individual results and reproduction. Next, compare initial
first-choice and top-three transfer on the full five-arena cohort
using the existing Scan receipts.

## Initial candidate quality before search

The [candidate quality report](CANDIDATE_QUALITY_2026-11-14.md)
compares first choice and best of three on all 473 common targets
and on the 64 changed prefixes. The first-choice regret difference
favours LCB in the pooled sample and changes sign without CARZrQpl.
Best-of-three regret slightly favours L. The next check uses the
archived 50,000-node receipts to count how often search recovers or
displaces an optimum relative to each transferred first choice.
