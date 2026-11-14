# Spatial Jass rehearsal on archived games

The [00:19 Paris listing](20261112T231920Z-tournaments.json) and the
[tournament detail](https://lidraughts.org/api/tournament/KXaMpuNe)
showed KXaMpuNe in progress on 13 November 2026. Its scheduled finish
was 00:57 Paris time. The chronological gate refused to freeze it.
No scores or Jass searches were produced for KXaMpuNe.

A clean checkout restored all 14 exclusion PDNs and 63 archived
manifests, covering 44,530 distinct FENs. The pinned Scan executable,
configuration and evaluation data matched the prior provenance.
The two Jass builds matched the archived runner and catalogue
SHA-256 values. FMJD replay accepted 26 PC Blues games and exported
1,864 rows with zero quarantines. Local validation passed 118 MTDP
tests, including the live Jass catalogue check, and 643 DILF tests.

## Rehearsal and reproduction

The archived MIDBy9dl freeze and its Scan receipts exercise the
full pilot path before the new cohort is available. The prepared
manifest was byte-identical with default Python hashing and
`PYTHONHASHSEED=61`. Its 53 common targets came from 37 owning games,
with 508 target legal actions. Five targets changed source and all
five changed the ordered top three. Each of the two Jass runs
completed all 477 searches, with exact node consumption and passing
root-order checks at 10,000, 50,000 and 200,000 nodes.

Follow the [pilot reproduction instructions](PROTOCOL.md), using
`eighth-replication/MIDBy9dl/provenance.json` under the benchmark
directory for `prepare`. For each scoring role, read the MIDBy9dl
receipt from the [archived packet index](../eighth-replication/scan-results/packet-index.json)
with `depth_sensitivity.read_input`. Validate it against the
original score plan and its content hash at depth 12 for sources
or depth 16 for targets. Restrict `action_scores_centimen` to the
FENs returned by `score_catalogue(manifest, role)` for the rehearsal
manifest, replace `cohort_sha256` with the rehearsal manifest hash,
and write with `geometry_ablation.write_json`. Validate against the
rehearsal manifest and then use `diagnose` and `run` from the protocol.

| Reproduced output | SHA-256 |
| --- | --- |
| Prepared manifest | `ed4bb28ccca0ba61dd58b5b8bf6dace77980561b5189ab683bf796454a6ac2f8` |
| Root-order trace JSONL | `53697a04e185bc73f2eab626dd8a40b485a680464566d97fdd05cc59bac63b82` |
| Paired rows, excluding elapsed time | `d64f431d3d411a152be6b5a2a2c410cf09b250c81ce8022399eab12fe0ad7dde` |
| Summary, excluding median elapsed time | `acb24a53481cf96ac8b5fd3473f5e778454de31b63e4e8267fbcfc2b94850dc8` |

For the paired digest, parse JSONL into a list and remove
`elapsed_us` from each arm. For the summary, remove
`median_elapsed_us` from each arm in each budget and subset.
Serialize both with sorted keys, compact separators and one
trailing newline. The timings were the only varying fields.
MIDBy9dl is already part of the three-event replication and this
rehearsal provides a mechanical check.

## Next action

After 00:57 Paris time, refresh the chronological listing with the
new snapshot above included, verify finished detail for KXaMpuNe
and fetch the completed PDN twice. If it qualifies, run the freeze
with both Python hash seeds and publish the freeze and benchmark
manifest before Scan scoring. Check the source-order contrast
before launching the new Jass searches.
