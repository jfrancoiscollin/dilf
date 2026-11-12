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

Create a JSON array of three entries in chronological order. Each
entry has a `provenance` descriptor containing `path`,
`stored_sha256` and `content_sha256`. Provenance supplies the
verified score-plan and eligible-shard descriptors.

```sh
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
tool=research.mtdp.jass_benchmark.multi_event_replication
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
```

The merged scorer deduplicates positions within each role. Splitting
validates the complete merged scores and produces references bound
to each original frozen plan digest. Run the individual
`geometry_ablation analyze` on those references. Create a
chronological three-entry packet index with descriptors for
`provenance`, `source`, `target` and `comparison` in each entry.
Then aggregate:

```sh
python -m research.mtdp.jass_benchmark.multi_event_replication aggregate \
  --packet-index "$PACKET_INDEX" --output "$RUN_DIR/summary.json"
```

The aggregator recomputes event analyses from verified raw scores,
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
