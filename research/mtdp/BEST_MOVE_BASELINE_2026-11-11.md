# MTDP — best-move transfer on held-out games, 2026-11-11

The frozen quiet-man signature preserved the available FMJD actions for every
paired position in this sample. At the fixed Scan 3.1 budget, 21 of 40 scored
holdout pairs had **disjoint sets of optimal moves**. The same signature can
therefore map to different reference-optimal moves even after allowing ties.

## Measured results

The 26 PC Blues games replayed successfully. The holdout retained 48 games
(8 Coupe de France and 40 Lidraughts), with one duplicate trajectory removed
and three Lidraughts games quarantined for ambiguous abbreviated captures.
The holdout had 4,691 distinct FENs, of which 67 appeared in PC Blues and
4,624 were novel. Of the novel positions, 3,086 received the quiet-man key.

| Pairing | Candidate pairs | Scored pairs | Same deterministic pick | Any optimum in common | Disjoint optima |
| --- | ---: | ---: | ---: | ---: | ---: |
| Two novel positions, from separate holdout games | 53 | 40 | 14 (35.0%) | 19 (47.5%) | 21 (52.5%) |
| PC Blues position and novel holdout position | 95 | 95 | 45 (47.4%) | 49 (51.6%) | 46 (48.4%) |

The primary cohort had 13 terminal pairs, zero forced-move pairs and zero
legal-action mismatches. The transfer cohort had none in any of these
categories. The 40 scored primary pairs contain 64 distinct positions. The
95 cross-corpus pairs contain 135 distinct positions.

| Direction | Positive cost | Mean including zero (men) | Median when positive (men) | Maximum (men) |
| --- | ---: | ---: | ---: | ---: |
| Holdout, FEN order A to B | 23/40 | 0.0315 | 0.04 | 0.22 |
| Holdout, FEN order B to A | 25/40 | 0.0433 | 0.04 | 0.40 |
| PC Blues to holdout | 47/95 | 0.0902 | 0.06 | 1.37 |
| Holdout to PC Blues | 50/95 | 0.1505 | 0.065 | 2.77 |

Every reported direction used ordinary evaluation scores. In the costliest
PC Blues to holdout transfer, Scan chose **29-24** in a position from PC
Blues game 16. In the novel
position from tournament game 33, Scan scored that move at **-1.31** for
White versus **+0.06** for **32-28**, a difference of **1.37 men** on the Scan
scale. Game numbers in the JSON refer to the corresponding input file.

## Reproduction

Run from the dilf checkout with Python 3.12 on Linux x86-64 and the companion
draught-master checkout at the pinned commit. The frozen budget is eight
plies of Scan search at each successor of a candidate move. See
[BEST_MOVE_PROTOCOL.md](BEST_MOVE_PROTOCOL.md) for settings and definitions.

```sh
git clone https://github.com/jfrancoiscollin/draught-master.git ../draught-master
git -C ../draught-master checkout 0e5189fbb251bf5eaf2e613d0f878bb17c740311
git clone https://github.com/rhalbersma/scan.git ../scan
git -C ../scan checkout 7aae17e7b7bfc47744601afb1ee7655e18983ce5
curl -fsSL https://lidraughts.org/api/tournament/L4F4P5R8/games \
  -o /tmp/mtdp-lidraughts-L4F4P5R8.pdn
printf '%s\n' 'e8a5ae26d1f376a131077521a437500782fea38771c53cbdb0dbae4916d0bb34  /tmp/mtdp-lidraughts-L4F4P5R8.pdn' | sha256sum -c -
PYTHONPATH=.:../draught-master python -m research.mtdp.best_move_audit \
  --baseline data/exports/pcblues/pcblues_games.pdn \
  --holdout ../draught-master/docs/parties/Bourges2-Seilh.pdn \
  --holdout ../draught-master/docs/parties/Drancy-Mirepoix.pdn \
  --holdout /tmp/mtdp-lidraughts-L4F4P5R8.pdn \
  --scan ../scan/scan_linux --output /tmp/mtdp-best-move.json
sha256sum /tmp/mtdp-best-move.json
```

Two complete local runs produced byte-identical JSON, SHA-256
`13d957075c9c44c1502fc663cff07bf2856459179327f55a5a8978c31b52c8f7`.
The JSON includes individual scores, game identities and directional costs.
The experiment ran in the remote workspace and all 53 MTDP unit tests passed.
GitHub Actions on the preceding
commit [reproduced the successor audit](https://github.com/jfrancoiscollin/dilf/actions/runs/43072960792).

## Limits and next action

The results describe this convenience sample and the specified Scan budget.
Many positions and pairs come from the same games, and the online sample is
bullet. The score deltas are evaluation differences at this budget.

**Next action:** rescore the exact same frozen pairs at Scan depth 12, with
the same settings and cold TT, then report how many disjoint optima and
high-cost transfers survive. Keep the two cohorts and report results for all
their scored pairs.
