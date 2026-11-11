# MTDP — typed diagonal neighborhood at radius two, 2026-11-11

The experiment uses the [preregistered refinement](LOCAL_NEIGHBORHOOD_PROTOCOL.md)
and keeps the original quiet-man key as a prefix. Every retained pair therefore
also belongs to the original partition. The new holdout was chosen before
replay or scoring. It is the completed
[Lidraughts Yearly Rapid Arena of 14 December 2024](https://lidraughts.org/tournament/eo66EN9z),
with a nominal 10+0 time control and 263 games in the export.

## PC Blues replay

All 26 games replayed, yielding 1,750 distinct FENs and 1,260 eligible FENs.

| Measure | Quiet-man key | Typed radius two |
| --- | ---: | ---: |
| Distinct eligible signatures | 1,222 | 1,244 |
| Collision groups | 26 | 15 |
| Distinct-FEN collision pairs | 61 | 17 |
| Pairs with unequal legal-action sets | 0 | 0 |
| Pairs with a successor-signature disagreement | 61 | 17 |

With exact occupancy for the 490 ineligible positions, the two variants yield
1,712 and 1,734 signatures, respectively. The refined key preserves 16 of the
38 deduplications achieved by the quiet-man key. A successor comparison counts
any disagreement under a shared legal move, treating two undefined keys alike.

## Scan 3.1 at depth 12

The [earlier report](BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md) defines the
frozen cohort. For the rapid cohort, 241 of 263 games were accepted. Ten
duplicate whole trajectories were skipped and 12 games were quarantined.
Of 23,948 distinct FENs, 101 were present in PC Blues and another 80 were
present in the previous holdout. The remaining 23,767 form the pool of novel
positions, including 15,879 eligible for the quiet-man key. A primary pair uses two novel FENs from disjoint game sets. A
cross-corpus pair uses a PC Blues source and a novel destination.

| Cohort | Candidate pairs | Scored pairs | Disjoint optima | Cost ≥ 0.50 A→B | Cost ≥ 0.50 B→A |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen holdout, all | 53 | 40 | 18 | 0 | 0 |
| Frozen holdout, retained | 26 | 13 | 5 | 0 | 0 |
| Frozen PC Blues transfer, all | 95 | 95 | 46 | 2 | 6 |
| Frozen PC Blues transfer, retained | 35 | 35 | 10 | 1 | 2 |
| Rapid holdout, all | 1123 | 752 | 436 | 37 | 48 |
| Rapid holdout, retained | 570 | 201 | 98 | 5 | 5 |
| Rapid PC Blues transfer, all | 249 | 249 | 137 | 13 | 12 |
| Rapid PC Blues transfer, retained | 52 | 52 | 20 | 4 | 2 |

The refined key keeps 201/752 (26.7%) scored rapid-only pairs. The proportion
with disjoint optima falls from 436/752 (58.0%) to 98/201 (48.8%). In the
PC Blues → rapid direction, it removes nine of 13 transfers costing at least
0.50 men, while keeping only 52/249 (20.9%) pairs. The costly-transfer rate
among those kept is 4/52 (7.7%), versus 13/249 (5.2%) before filtering. The
maximum retained cost in this direction is 1.44 men. The frozen cohort
also retains one PC Blues → holdout transfer costing 1.29 men.

In the rapid-only cohort, the two directions have 10 and 11 switches from
an ordinary optimal score to a Scan forced-loss score after transfer. Four
and five, respectively, survive refinement. These are directional counts,
reported separately from ordinary score differences.

The two directions of the primary cohorts follow FEN sort order. Costs of
0.50 men or more use ordinary Scan scores and tie-breaking from the original
audit. The sample comprises one event with repeat players and related openings.
The 241 games and overlapping pairs do not constitute independent draws.

## Reproduction

Use the pinned [Scan and draught-master inputs and original PDN downloads](BEST_MOVE_BASELINE_2026-11-11.md#reproduction).
Run the original command at depth 12 to obtain `/tmp/depth-12.json`. Then
download the rapid PDN and run the fresh audit from the dilf checkout:

```sh
curl -fsSL https://lidraughts.org/api/tournament/eo66EN9z/games \
  -o /tmp/mtdp-lidraughts-eo66EN9z.pdn
printf '%s\n' '38d352e824420f11429f02c9fd4030d211355915a2626968fdc336bf487eadbf  /tmp/mtdp-lidraughts-eo66EN9z.pdn' | sha256sum -c -
PYTHONPATH=.:../draught-master python -m research.mtdp.best_move_audit \
  --baseline data/exports/pcblues/pcblues_games.pdn \
  --exclude-previous ../draught-master/docs/parties/Bourges2-Seilh.pdn \
  --exclude-previous ../draught-master/docs/parties/Drancy-Mirepoix.pdn \
  --exclude-previous /tmp/mtdp-lidraughts-L4F4P5R8.pdn \
  --holdout /tmp/mtdp-lidraughts-eo66EN9z.pdn \
  --scan ../scan/scan_linux --depth 12 --output /tmp/rapid-d12.json
PYTHONPATH=.:../draught-master python -m research.mtdp.local_neighborhood \
  --baseline data/exports/pcblues/pcblues_games.pdn \
  --best-move-report /tmp/depth-12.json \
  --best-move-report /tmp/rapid-d12.json --output /tmp/mtdp-local-neighborhood.json
```

The audit JSON records input digests, rejected games, ordered FENs, game
indices, legal action scores and transfer costs. The default audit with
the old inputs reproduced the original depth-12 JSON byte for byte. All
63 MTDP unit tests passed in the remote workspace. The integration workflow
replays all PC Blues games, checks that the refinement only narrows the
original partition and archives the PC Blues JSON.

| Output | SHA-256 |
| --- | --- |
| Frozen depth-12 audit | `29cd0c74a7e9469bcb5bf3775558f8f52ba975949d3637bbe4e07a2c031189b0` |
| Rapid depth-12 audit | `224e9b74237adc396bdf4e2944c3da9ea0a0abec16195bcdb19222335ea8c173` |
| Combined neighborhood summary | `4adbd08b145050784eb3bf56263f2a5c38155fa4cfc729a3a0dcbdd6152155a7` |

The next control is an offline test of the transferred top three moves as
ordering candidates on these frozen pairs. Compare both signatures against
the exact depth-12 optimal sets, with coverage, recall, and the best available
candidate's regret. A move ordering benchmark would separately search the
full legal move set in Jass at a matched budget.
