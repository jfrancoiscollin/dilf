# Third independent Jass cohort

The [7 November 2026 Weekly Rapid Arena](https://lidraughts.org/tournament/0gB7ETSW)
was selected before scoring as a completed international-draughts event at
the same nominal 10+0 time control as both earlier Jass cohorts. The event
API confirmed standard variant, 47 participants, and a 16:00 UTC start.
The [canonical export](https://lidraughts.org/api/tournament/0gB7ETSW/games)
was retrieved on 12 November at 03:20 UTC. Two exports matched byte for
byte (88,326 raw bytes). The raw PDN SHA-256 is
`cdf0ef2f69fddaec1994c54448479b2599bcaf3a343d5d500c43ae03b19f03f4`.

## Frozen selection

81 games were parsed, 72 distinct trajectories accepted, six duplicate
trajectories skipped, and three games quarantined for ambiguous capture
paths. The 7,140 distinct FENs included 53 PC Blues FENs and 263 further
FENs present in earlier holdouts. The seven prior input hashes match the
second cohort's frozen inventory. No target appears in either previous
benchmark manifest.

Of 6,824 novel FENs, 4,585 received the quiet-man signature. Removing 11
terminal positions and eight forced moves left 4,566 with a choice. Of
these, 17 (0.37%) shared the signature and exact canonical action set with
a PC Blues source. No move mapping was rejected. These targets occur in
11 games and use 13 distinct source FENs. Three pairs also share the typed
radius-two descriptor. Coverage measures the selection gate. Scan has
yet to measure agreement or regret on this cohort.

The manifest records all accepted game/ply memberships, the selected
source game, both typed descriptors and the canonical and Jass move keys.
Two separate freezes with different Python hash seeds produced the same
uncompressed manifest SHA-256
`57d3e60fc3c52211a56ccc8548062afd567d9d8cae4723cad9ec90ff2ed74f99`.
No scores were calculated for this cohort before publication of the freeze.

## Reproduction

Use the pinned dependencies from the [first cohort](../README.md#reproduction)
and the [initial-only build and trace check](../../jass_preflight/INITIAL_ONLY_RESULTS_2026-11-12.md#reproduction).
Set `PDN_DIR` to a directory containing the four prior Lidraughts exports
(`L4F4P5R8`, `eo66EN9z`, `Z3s40c6H`, and `iPQl7g7q`, named as below).
Verify their hashes against `exclusion_inputs` in the archived manifest.

```sh
cohort=research/mtdp/jass_benchmark/initial-only-0gB7ETSW
gzip -dc "$cohort/mtdp-lidraughts-0gB7ETSW.pdn.gz" > "$PDN_DIR/mtdp-lidraughts-0gB7ETSW.pdn"
PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT" python -m research.mtdp.jass_cohort \
  --baseline data/exports/pcblues/pcblues_games.pdn \
  --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Bourges2-Seilh.pdn" \
  --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Drancy-Mirepoix.pdn" \
  --exclude-previous "$PDN_DIR/mtdp-lidraughts-L4F4P5R8.pdn" \
  --exclude-previous "$PDN_DIR/mtdp-lidraughts-eo66EN9z.pdn" \
  --exclude-previous "$PDN_DIR/mtdp-lidraughts-Z3s40c6H.pdn" \
  --exclude-previous "$PDN_DIR/mtdp-lidraughts-iPQl7g7q.pdn" \
  --holdout "$PDN_DIR/mtdp-lidraughts-0gB7ETSW.pdn" \
  --jass-catalogue "$JASS_BUILD/mtdp_jass_legal_catalogue" \
  --record-provenance --output /tmp/mtdp-third-cohort.json
gzip -dc "$cohort/cohort-manifest.json.gz" | cmp - /tmp/mtdp-third-cohort.json
```

The build used GCC 14.2.0 and CMake 4.4.4. The catalogue digest depends on
the build. Jass tests passed, and the archived initial-only preflight
trace reproduced byte for byte.
