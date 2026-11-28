# Seventh holdout freeze — pRW2Ahpz

The [12 November 2026 Hourly Blitz Arena](https://lidraughts.org/tournament/pRW2Ahpz)
started at 08:00 UTC. It was the earliest finished, unused standard
5+0 arena after the sixth event in the recorded chronological listing.
The 02:00 UTC arena was already used. The listed time range, all
selection fields, retrieval timestamp and export digest are in
[provenance.json](provenance.json). Two downloads of the
[public PDN export](https://lidraughts.org/api/tournament/pRW2Ahpz/games)
matched byte for byte. The archive contains derived positions and replay
receipts. [API guidance](https://lidraughts.org/developers)
· [Terms](https://lidraughts.org/terms-of-service)

All 99 public game IDs were unique and absent from the earlier exports.
Of 99 games, 95 distinct trajectories replayed successfully, two were
duplicates and two were quarantined for ambiguous abbreviated captures.
The source pool was the 1,260 eligible FENs from the validated 26 PC
Blues games. After removing 82 overlaps with PC Blues and 410 overlaps
with earlier holdouts from 10,120 replayed target FENs, 9,628 FENs
remained. Of these, 1,251 had a mover king, 2,200 had a capture without
a mover king, 16 were terminal and 15 had a forced quiet move. The
remaining 6,146 form the common eligible population. All 42 replay
overlaps with earlier manifests were excluded.

The four arms have 78 (L), 21 (LM), 32 (LCB) and 21 (LMB) matches.
Each eligible FEN's legal catalogue, quiet geometry, owning games and
all source candidates are in the manifest shards. Each arm uses the
first source by game ID, ply and FEN. On the common L/LM targets the
selected source changes once. Two independent freezes with different
Python hash seeds produced identical data. The freeze was published
before Scan scoring.

## Reproduction

Use the [sixth freeze invocation](../sixth-xmzj1bLG/FREEZE.md#reproduction).
Add `--mover-occupancy`, add the sixth PDN as `--exclude-previous`, pass
each sixth `eligible-*.json.gz` as `--prior-eligible-shard`, and
use `mtdp-lidraughts-pRW2Ahpz.pdn` as the new holdout. Verify all
downloaded files against provenance and compare the regenerated
eligible, game-audit and score-plan hashes. The same pinned draught-master
adapter is used.
