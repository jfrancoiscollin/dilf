# Multi-event replication status — 12 November 2026

The [preregistered protocol](../../EIGHTH_MULTI_EVENT_REPLICATION_PROTOCOL_2026-11-12.md)
requires the next three independent eligible 5+0 arenas after
`pRW2Ahpz`. At 10:19:52 UTC the [Lidraughts tournament API](https://lidraughts.org/api/tournament)
listed zero new finished standard 5+0 arenas after that event.
The finished list covered starts from 11 November 23:00 UTC to
12 November 09:00 UTC. The only qualifying cadence in that interval
was already used. Two later 5+0 standard arenas were scheduled.

| Event | Listed start UTC | Listed finish UTC | Status at retrieval |
| --- | --- | --- | --- |
| [xAnBIxHN](https://lidraughts.org/tournament/xAnBIxHN) | 11:00 | 11:57 | Scheduled |
| [MoXhmT9b](https://lidraughts.org/tournament/MoXhmT9b) | 14:00 | 14:57 | Scheduled |

The [timestamped snapshot](2026-11-12T101952Z-tournaments.json)
retains the selection fields and the SHA-256 of the original
response. The [candidate log](candidate-log.json) records the
chronological gate. There are no new eligible freezes or Scan
scores. Event metadata is a first filter. PDN and replay
independence still need verification for any finished candidate.

## Updated listing at 11:18:48 UTC

The [second snapshot](2026-11-12T111848Z-tournaments.json) still had
**0/3** new finished metadata candidates. It now shows the 11:00 UTC
arena underway and another standard 5+0 arena announced before the
14:00 UTC start. Eligibility of all three remains to be verified
from the completed exports and replay.

| Event | Listed start UTC | Listed finish UTC | Status |
| --- | --- | --- | --- |
| [xAnBIxHN](https://lidraughts.org/tournament/xAnBIxHN) | 11:00 | 11:57 | Started |
| [vHeQVFho](https://lidraughts.org/tournament/vHeQVFho) | 11:52 | 12:37 | Scheduled |
| [MoXhmT9b](https://lidraughts.org/tournament/MoXhmT9b) | 14:00 | 14:57 | Scheduled |

## First verified freeze at 12:17 UTC

The [third listing](2026-11-12T121710Z-tournaments.json) and
[finished event detail](xAnBIxHN-evidence/event-metadata.json) confirm that
`xAnBIxHN` finished at the scheduled 11:57 UTC cutoff. Two independent
downloads of its [game export](https://lidraughts.org/api/tournament/xAnBIxHN/games)
matched byte-for-byte. FMJD replay accepted 129 of 141 records. Four were
duplicates, and eight used ambiguous capture notation and were quarantined.
The [frozen provenance](xAnBIxHN/provenance.json) and game audit retain
the counts, hashes and quarantine reasons.

The freeze contains 8,069 eligible positions. Exact legal actions (L)
match 105, mover occupancy (LM) matches 33, mover count with immediate
blockers (LCB) matches 46, and mover occupancy with blockers (LMB) matches
33. These are counts before scoring. The score plan has 109 target/source
pair records across the four rules, using 77 distinct source FENs.
Independent runs with Python hash seeds 7 and 61 reproduced the eligible
rows, score plan and game audit. The Scan binary, configuration and
evaluation-file digests matched the prior study.

The gate is **1/3**. The previously announced `vHeQVFho` was absent from
the third listing. The [endpoint check](vHeQVFho-endpoint-check.json)
returned HTTP 404 from the detail API, tournament page and games API before its listed 12:37 UTC finish. Retain it in the
chronology and recheck after that time. If it remains unavailable,
record the post-finish evidence and use the rejection mechanism below.
`MoXhmT9b` is still scheduled for 14:00–14:57 UTC. Keep the first event
PDN in the exclusion inventory and pass
`--previous-freeze "$study/xAnBIxHN/provenance.json"` for the next freeze.
The three-event scoring gate has not been opened.

## Post-finish candidate check at 13:13 UTC

The [new listing](2026-11-12T131326Z-tournaments.json) still shows
only one finished new 5+0 arena. The tournament page, detail API and
PDN export for `vHeQVFho` again returned HTTP 404 after its announced
12:37 UTC finish. The [endpoint receipt](vHeQVFho-post-finish-endpoint-check.json)
and [rejection record](rejections.json) preserve the observation and
the reason for exclusion. The raw chronology retains the original
announcement. Pass `--rejections "$study/rejections.json"` to subsequent
freezes. If the event reappears with a completed export before the next
freeze, review its eligibility in chronological order first.

The next known candidate, `MoXhmT9b`, is scheduled for 14:00–14:57 UTC.
The freeze check rejected it while still scheduled, even after applying
the recorded exclusion. The replication remains at **1/3** with zero
new Scan scores. Refresh the listing after 14:57 UTC, check the
candidate's detail and fetch its completed PDN twice before attempting
its freeze. A third eligible event is still needed.

## Candidate check and input restoration at 14:14 UTC

The [listing](2026-11-12T141444Z-tournaments.json) shows `MoXhmT9b`
in progress with a scheduled 14:57 UTC finish and a new standard
5+0 candidate, [MIDBy9dl](https://lidraughts.org/tournament/MIDBy9dl),
scheduled for 20:00–20:57 UTC. The gate refused to freeze `MoXhmT9b`
while it was running. The replication remains at **1/3**.

The first freeze was rebuilt from a fresh download of the pinned
inputs. Its 11 eligible-position shards (8,069 rows), score plan and
game audit reproduced byte-for-byte with `PYTHONHASHSEED=131`.
The Scan Linux executable, configuration and evaluation data
matched the frozen digests. No Scan scores were computed.

To restore inputs on a fresh machine, use the newest frozen
`provenance.json` and fetch each `mtdp-lidraughts-<id>.pdn` from
`https://lidraughts.org/api/tournament/<id>/games`. Read the filenames and
SHA-256 values from both `inputs.exclusions` and `inputs.event`.
Check every download against its recorded SHA-256 and retry on a
mismatch with a fresh query parameter. Keep the two local club PDNs in
`docs/parties` of the [pinned adapter checkout](https://github.com/jfrancoiscollin/draught-master/tree/0e5189fbb251bf5eaf2e613d0f878bb17c740311).
Extract Scan from the [pinned source archive](https://codeload.github.com/rhalbersma/scan/tar.gz/7aae17e7b7bfc47744601afb1ee7655e18983ce5).
The freeze command independently checks the adapter revision, all
input and manifest digests, and the three Scan file digests.

## Second verified freeze at 15:19 UTC

The [listing](2026-11-12T151904Z-tournaments.json) and
[detail response](MoXhmT9b-evidence/event-metadata.json) confirm
`MoXhmT9b` finished. Two independent [PDN exports](https://lidraughts.org/api/tournament/MoXhmT9b/games)
matched byte-for-byte (178,542 bytes). The FMJD replay accepted 142
of 155 records. Nine were duplicates and four had ambiguous capture
notation. The [frozen provenance](MoXhmT9b/provenance.json) includes
the counts and digests. The [archived candidate log](MoXhmT9b-evidence/candidate-log.json)
and recorded rejection for `vHeQVFho` fix the selection evidence.

| Positions | Eligible | L | LM | LCB | LMB |
| --- | ---: | ---: | ---: | ---: | ---: |
| `MoXhmT9b` | 9,293 | 74 | 29 | 39 | 29 |

The score plan contains 80 target/source pairs, with 74 distinct
target FENs and 59 distinct source FENs. The two frozen events share
no eligible target FENs or game IDs. All compressed data shards, the
score plan and the audit reproduced byte-for-byte with Python hash
seeds 7 and 61. The 114 MTDP tests, 643 DILF tests and PC Blues replay
passed. The optional live Jass catalogue test was skipped.

The gate is **2/3**. `MIDBy9dl` was still scheduled for 20:00–20:57
UTC at this check. Refresh the chronological listing and freeze the
next eligible completed arena with both earlier provenances in order
(`xAnBIxHN`, then `MoXhmT9b`). No new Scan scores were computed.

## Scan input checks with two published freezes

At 16:11 UTC on 12 November the
[Lidraughts listing](https://lidraughts.org/api/tournament) still showed
only the two frozen tournaments as finished among the new candidates.
The detail endpoint for [MIDBy9dl](https://lidraughts.org/api/tournament/MIDBy9dl)
still showed the scheduled 20:00 UTC start.

The two plans contain 189 event-level target/source pair records.
They share 30 source FENs, so scoring across both plans would use 106
distinct source FENs and 179 distinct target FENs. The pinned FMJD
adapter reproduced every canonical legal action and applied all 1,039
source and 1,745 target successors. This checked the move catalogues
without running Scan. The executable, configuration and evaluation
hashes matched both provenances. The third-freeze input inventory
verified all 13 exclusion PDNs and 47 prior manifest hashes.
`prepare-score-plan` refused the two-entry index and wrote no plan.

## Scoring pipeline rehearsal and updated schedule

The [17:16 UTC listing](2026-11-12T171625Z-tournaments.json) still
shows only two finished candidates. `MIDBy9dl` remains scheduled
for 20:00–20:57 UTC. [KXaMpuNe](https://lidraughts.org/tournament/KXaMpuNe)
was newly listed for 23:00–23:57 UTC, after `MIDBy9dl`.
Both are candidates until their exports and replay pass verification.

The [CLI integration test](../../tests/test_multi_event_replication.py)
rehearses the complete post-Scan path with three synthetic freezes and
synthetic score receipts. One source FEN shared by all three events
is represented once in the merged reference. Each split receipt is
bound to its frozen plan. Aggregation reproduces identical bytes on
a second run and rejects a modified event analysis even when the
packet index contains the modified file's correct hash. No actual
Scan search was run. Local validation passed 115 MTDP tests and 643
DILF tests. The optional live Jass catalogue test was skipped.

## Scan replay from a fresh checkout

On 12 November, fresh checkouts of DILF and the pinned FMJD adapter
and a fresh copy of the pinned Scan archive reproduced both
[seventh-event references and their comparison](../seventh-pRW2Ahpz/RESULTS_2026-11-12.md#reproduction)
byte for byte. This covered all 586 source successors at depth 12
and 760 target successors at depth 16. The two runs used one Scan
thread each and took 15 and 136 seconds respectively in this workspace.
The comparison digest is
`88946e1cee8e525ade475c3a7352e479b0ae4bfe879b732ee04d0d212a8860b5`.

The [Lidraughts listing](https://lidraughts.org/api/tournament) at
18:17 UTC still had two finished candidates and confirmed the
20:00 and 23:00 UTC scheduled starts. The replay used the archived
seventh event only. The three-event study still awaits its third freeze.

## Paired top-one reporting and pre-score audit at 19:12 UTC

The [19:12 UTC listing](2026-11-12T191226Z-tournaments.json) still
shows only the two frozen events as finished candidates.
`MIDBy9dl` remains scheduled for 20:00–20:57 UTC, followed by
`KXaMpuNe` at 23:00–23:57 UTC.

Reading the verified eligible-position shards gives these counts before
any new Scan search. Each cell lists targets followed by owning games.

| Event | L/LCB common | Different selected source under LCB vs L | LCB matches beyond LMB |
| --- | ---: | ---: | ---: |
| `xAnBIxHN` | 46 / 32 | 3 / 3 | 13 / 9 |
| `MoXhmT9b` | 39 / 29 | 5 / 5 | 10 / 10 |
| Total | 85 / 61 | 8 / 8 | 23 / 19 |

To reproduce these counts, read each provenance's `eligible_shards`
using `depth_sensitivity.read_input`. Select rows with a nonempty
`matches["LCB"]`, then count separately those whose first LCB and L
source receipts differ and those with empty `matches["LMB"]`. Count
distinct `owner` values per subset. Thus far 8 of 85 common targets
(9.4%) change source, so the effect on those targets should be read
alongside their game count.

The pooled output now exposes `paired_top1` as a supplementary
diagnostic, using the same paired target populations and hierarchical
bootstrap as `paired`, which retains the preregistered best-of-three
estimand. Both report selected-source change rates. The synthetic test
verifies that first-choice regret and best-of-three regret can differ.
Local validation passed 115 MTDP tests and 643 DILF tests, and FMJD
replayed 26 PC Blues games with zero quarantines. The optional live
Jass catalogue test was skipped.

After 20:57 UTC, verify the third candidate in the listing and the
detail API, fetch its finished PDN twice and reproduce the freeze.
Once all three verified freezes are published, score the merged plan
at the pinned Scan depths 12 and 16 and reproduce its analysis.

## Third arena underway and recovered-match reporting

The [20:13 UTC listing](2026-11-12T201339Z-tournaments.json) places
`MIDBy9dl` in progress with the same 20:57 UTC finish. Its detail
API independently confirmed it was in progress. The detail API for
the earlier rejected `vHeQVFho` still returned HTTP 404. The updated
[chronology](candidate-log.json) retains `KXaMpuNe` at 23:00 UTC and
adds `uG0fGZzB` at 02:00 UTC on 13 November as later candidates.

The third-freeze inputs were restored and checked against the frozen
hashes. The inventory contains 13 exclusion PDNs and 47 prior manifests
covering 32,355 unique exclusion FENs. The pinned adapter and all three
Scan file digests matched. PC Blues replay reproduced all 1,864 rows
byte for byte across 26 games, with zero quarantines.

The [pinned Jass catalogue build](../jass-build-manifest.json) also
reproduced its executable digest. To check compatibility, load both
frozen plans with `read_input`, collect their source and target action
sets with `score_catalogue`, and deduplicate by FEN. For each FEN,
`map_root_moves` mapped the FMJD adapter's legal moves to the Jass
catalogue, and its canonical keys exactly matched the frozen set.
The check covered 285 FENs and 2,784 actions with no mismatches.
All 116 MTDP tests, including the live catalogue test, and 643 DILF
tests passed.

The aggregate now includes `lcb_recovered_vs_lmb`, a supplementary
description of targets matched by LCB with no exact mover-occupancy
match under LMB. It shows owning-game counts, top-one and top-three
optimum coverage, ordinary regret and category transitions for LCB and
the exact-legal-actions control on the same targets. The existing
preregistered estimates remain the primary analysis. A three-event
synthetic run tests subset membership, separates first-choice and
best-of-three regret, and reproduces the output byte for byte.

At this check, the study still had two frozen tournaments and zero new
Scan scores. Next, check the completed listing and detail, verify two
independent PDN exports and reproduce the third freeze. Then publish
that freeze before scoring and inspect the recovered-match summary
alongside the preregistered paired results.

## Third verified freeze on 12 November

The [21:17 UTC listing](2026-11-12T211740Z-tournaments.json) and
[detail response](MIDBy9dl-evidence/event-metadata.json) confirm that
`MIDBy9dl` finished. Two independent
[PDN downloads](https://lidraughts.org/api/tournament/MIDBy9dl/games)
matched byte for byte (240,811 bytes). FMJD replay accepted 191 of
209 records. Seven were duplicates and eleven were quarantined. The
[provenance](MIDBy9dl/provenance.json) records the exact audit and
input hashes. The [candidate log](MIDBy9dl-evidence/candidate-log.json)
binds the chronological selection.

| Event | Eligible | L | LM | LCB | LMB |
| --- | ---: | ---: | ---: | ---: | ---: |
| `MIDBy9dl` | 12,175 | 147 | 40 | 53 | 40 |
| Three events | 29,537 | 326 | 102 | 138 | 102 |

All 18 compressed eligible shards, game audit and score plan files
reproduced byte for byte with Python hash seeds 7 and 61. The three
freezes are ready for the preregistered Scan run at depths 12 and 16.
This freeze contains no Scan outcomes.

## Continue acquisition

From the DILF root, fetch a fresh listing, preserving old snapshots
so a finished arena cannot vanish from consideration as the rolling
API list advances. Check the detail endpoint for any earlier pending
arena that drops out of the list before its status is resolved.
Keep the chronology log and reasons for every rejection.

```sh
study=research/mtdp/jass_benchmark/eighth-replication
stamp=$(date -u +%Y-%m-%dT%H%M%SZ)
retrieved=$(date -u +%FT%TZ)
curl -fsSL "https://lidraughts.org/api/tournament?nb=50&_=$(date +%s)" -o /tmp/mtdp-next-tournaments.json
python -m research.mtdp.jass_benchmark.multi_event_replication snapshot \
  --raw /tmp/mtdp-next-tournaments.json --retrieved-at "$retrieved" \
  --url https://lidraughts.org/api/tournament --output "$study/$stamp-tournaments.json"
args=()
for snapshot in "$study"/*-tournaments.json; do args+=(--snapshot "$snapshot"); done
python -m research.mtdp.jass_benchmark.multi_event_replication candidates \
  "${args[@]}" --output "$study/candidate-log.json"
```

## Freeze the next finished candidate

Download the finished event's detail JSON and PDN from the public API.
Use the filename `mtdp-lidraughts-$EVENT.pdn`. Keep all earlier verified
Lidraughts PDNs in `PDN_DIR`; their names and hashes are in the
[seventh provenance](../seventh-pRW2Ahpz/provenance.json) and the
provenance of any earlier freezes from this replication. The freeze
command checks those exports and archived target manifests, verifies the
Scan build without executing it, rejects overlapping game IDs and
performs the pinned FMJD replay. It packages the eligible shards, game
audit and score plan with their hashes.

```sh
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
python -m research.mtdp.jass_benchmark.multi_event_freeze \
  --candidate-log "$study/candidate-log.json" --event-metadata "$EVENT_METADATA" \
  --pdn "$PDN_DIR/mtdp-lidraughts-$EVENT.pdn" --pdn-dir "$PDN_DIR" \
  --adapter "$DRAUGHT_MASTER_ROOT" --scan "$SCAN_ROOT/scan_linux" \
  --downloaded-at "$PDN_RETRIEVED_UTC" --output "$study/$EVENT"
```

For subsequent events, pass a `--previous-freeze` provenance path for
each earlier event in this replication, in chronological order. If an
earlier candidate is rejected, preserve the evidence in the chronology
log and pass `--rejections` with the recorded event IDs and reasons.
The next candidate must be finished in both the listing and the detail
response. `--pdn-repeat` can verify an independent duplicate download.
Repeat the freeze with a different Python hash seed and compare
`eligible_sha256`, score-plan content hash and game-audit content
hash. Publish the three verified freezes before scoring.

## Score once per distinct FEN and depth

Once the third freeze is published, run these commands from the
DILF root in Bash. Set `THIRD_EVENT` to the verified event ID and
`RUN_DIR` to a fresh directory. The input paths below bind the run
to the three frozen provenances in chronological order.

```bash
set -e
study=research/mtdp/jass_benchmark/eighth-replication
events=(xAnBIxHN MoXhmT9b "${THIRD_EVENT:?set the verified third event ID}")
mkdir -p "$RUN_DIR"
FREEZE_INDEX="$RUN_DIR/freeze-index.json"
PACKET_INDEX="$RUN_DIR/packet-index.json"

# Build input descriptors for the uncompressed JSON files used here.
build_index() {
  python - "$1" "$2" "$study" "$RUN_DIR" "${events[@]}" <<'PY_INDEX'
import hashlib
import sys
from pathlib import Path

from research.mtdp.jass_benchmark.geometry_ablation import write_json

def descriptor(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "stored_sha256": digest, "content_sha256": digest}

kind, output, study, run_dir, *events = sys.argv[1:]
entries = []
for event in events:
    entry = {"provenance": descriptor(Path(study) / event / "provenance.json")}
    if kind == "packet":
        for role in ("source", "target", "comparison"):
            entry[role] = descriptor(Path(run_dir) / f"{event}-{role}.json")
    entries.append(entry)
write_json(Path(output), entries)
PY_INDEX
}

export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
tool=research.mtdp.jass_benchmark.multi_event_replication
build_index freeze "$FREEZE_INDEX"
python -m "$tool" prepare-score-plan --freeze-index "$FREEZE_INDEX" --output "$RUN_DIR/merged.json"
for role in source target; do
  case "$role" in source) depth=12 ;; target) depth=16 ;; esac
  python -m research.mtdp.jass_scan_reference --role "$role" --depth "$depth" \
    --manifest "$RUN_DIR/merged.json" --scan "$SCAN_ROOT/scan_linux" \
    --output "$RUN_DIR/$role.json"
  python -m "$tool" split-reference --freeze-index "$FREEZE_INDEX" \
    --merged-plan "$RUN_DIR/merged.json" --reference "$RUN_DIR/$role.json" \
    --role "$role" --output-dir "$RUN_DIR"
done
for event in "${events[@]}"; do
  python -m research.mtdp.jass_benchmark.geometry_ablation analyze \
    --provenance "$study/$event/provenance.json" \
    --source "$RUN_DIR/$event-source.json" --target "$RUN_DIR/$event-target.json" \
    --output "$RUN_DIR/$event-comparison.json"
done
build_index packet "$PACKET_INDEX"
python -m "$tool" aggregate --packet-index "$PACKET_INDEX" --output "$RUN_DIR/summary.json"
```

The merged scorer deduplicates positions within each role. Splitting
validates the complete merged scores and binds them to each original
frozen plan digest. The aggregator recomputes event analyses from verified raw scores,
checks target, source-selection and game ownership receipts and
reports target-weighted outcomes with the registered tournament/game
bootstrap, changed-source subset and leave-one-event-out summaries.
Repeat the analysis and compare the output bytes.

Local validation before event acquisition completed 112 MTDP tests,
643 DILF tests and FMJD replay of 26 PC Blues games (1,864 positions,
zero quarantined games). The optional live Jass catalogue test was
skipped. No new event scoring is part of this status report.

The follow-up freeze tooling was rehearsed against the archived seventh
event. Its 6,146 eligible rows, score plan and game audit reproduced
their original hashes. All 11 exclusion PDNs and previous target
manifests were verified for the next event. One initial download of
the 2024 rapid PDN differed from the pinned bytes. Two subsequent
fetches returned the expected digest. The freeze keeps the digest
check in force. The updated local suite passed 114 MTDP tests and
643 DILF tests, with the optional Jass catalogue test skipped.
