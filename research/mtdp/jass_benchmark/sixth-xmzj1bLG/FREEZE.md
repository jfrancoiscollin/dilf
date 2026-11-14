# Sixth holdout freeze — xmzj1bLG

The [11 November 2026 Hourly Blitz Arena](https://lidraughts.org/tournament/xmzj1bLG)
started at 23:00 UTC. It was the first eligible finished standard
5+0 arena in the recorded API response after the
[protocol](../SIXTH_GEOMETRY_ABLATION_PROTOCOL_2026-11-12.md), after
excluding previously used IDs. Two downloads of the
[public PDN export](https://lidraughts.org/api/tournament/xmzj1bLG/games)
matched byte for byte. The response hash, selection fields, timestamps,
PDN hashes and engine provenance are in [provenance.json](provenance.json).
The archive publishes derived positions and replay outcomes. Reproduction
fetches the game records from the public API. [API guidance](https://lidraughts.org/developers)
· [Terms](https://lidraughts.org/terms-of-service)

The FMJD adapter replayed all 26 PC Blues games. Their 1,260 eligible
distinct source FENs form the matching pool. Of 141 event games, 132
distinct trajectories replayed successfully, four duplicated another
trajectory and five had ambiguous abbreviated captures. The latter were
quarantined before scoring. There were 13,800 distinct target FENs.
After excluding 75 overlapping PC Blues and 489 overlapping earlier
holdouts, 4,568 were non-quiet, 23 terminal and 12 forced. The remaining
8,633 positions constitute the frozen eligible denominator. The five
earlier manifests overlapped 23 FENs in the raw replay, all excluded.

For every eligible FEN, the shards record the action catalogue, quiet
signature, all owning-game candidates and all distinct matching PC Blues
FENs under each arm. A source FEN is represented by its first
(game ID, ply, FEN) occurrence. Each arm selects its first such tuple.
The legal-only arm matches 138 targets and the geometry arm matches 39.
The selected source differs on one of the 39 common targets. These are
match counts before any engine evaluation. Two freezes under different
Python hash seeds produced the same data.

## Reproduction

Use the baseline and exclusion inventory in provenance and the FMJD
adapter pinned to `0e5189fbb251bf5eaf2e613d0f878bb17c740311`.
With the five prior manifests in the repository and each PDN downloaded
and checked against provenance, run:

```sh
study=research/mtdp/jass_benchmark
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
args=(--baseline data/exports/pcblues/pcblues_games.pdn
      --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Bourges2-Seilh.pdn"
      --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Drancy-Mirepoix.pdn")
for id in L4F4P5R8 eo66EN9z Z3s40c6H iPQl7g7q 0gB7ETSW 3onq5G6G LAYRsqON; do
  args+=(--exclude-previous "$PDN_DIR/mtdp-lidraughts-$id.pdn")
done
for manifest in "$study/cohort-manifest.json" \
  "$study/replication-iPQl7g7q/cohort-manifest.json" \
  "$study/initial-only-0gB7ETSW/cohort-manifest.json.gz" \
  "$study/fourth-3onq5G6G/cohort-manifest.json.gz" \
  "$study/fifth-LAYRsqON/cohort-manifest.json.gz"; do
  args+=(--prior-manifest "$manifest")
done
python -m research.mtdp.jass_benchmark.geometry_ablation freeze "${args[@]}" \
  --holdout "$PDN_DIR/mtdp-lidraughts-xmzj1bLG.pdn" --output-dir /tmp/mtdp-sixth-freeze
sha256sum /tmp/mtdp-sixth-freeze/{eligible,score-plan,game-audit}.json
```

Compare the uncompressed hashes with provenance. No Scan scores were
computed before the freeze commit.
