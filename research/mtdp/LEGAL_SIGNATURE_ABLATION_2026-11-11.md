# MTDP legal-action signature ablation

The experiment replays 26 PC Blues games with the FMJD rules in
`draught-master` at `0e5189fbb251bf5eaf2e613d0f878bb17c740311`.
It covers 1,864 observations and 1,750 distinct canonical FENs.
The original A–D results match [GitHub Actions run 43025727899](https://github.com/jfrancoiscollin/dilf/actions/runs/43025727899).
The geometric extensions are exploratory measurements on the same games.

Each pair consists of two distinct FENs sharing a signature. A pair is
cross-game if its two positions can be sourced from different games.
Compare complete legal move paths, captured squares, and promotion flags.

| Representation | Signatures | Pairs | Different legal sets | Cross-game pairs | Different legal sets across games |
| --- | ---: | ---: | ---: | ---: | ---: |
| A, eight descriptors and turn | 1,642 | 137 | 114 | 90 | 67 |
| B, A with piece counts | 1,642 | 137 | 114 | 90 | 67 |
| C, B with king counts | 1,643 | 136 | 113 | 90 | 67 |
| C with counts by type and quadrant (5 × 5) | 1,676 | 84 | 63 | 55 | 34 |
| C with counts by type and pair of adjacent rows | 1,698 | 74 | 52 | 68 | 46 |
| C with counts by type and row | 1,704 | 68 | 46 | 68 | 46 |
| C with exact squares and types for the side to move | 1,725 | 29 | 12 | 29 | 12 |
| Geometry of non-capturing men, with exact fallback | 1,712 | 61 | 0 | 61 | 0 |
| D, exact piece locations and types with turn | 1,750 | 0 | 0 | 0 | 0 |

B leaves all A collisions intact on this corpus. C removes one disagreement.
Even exact locations and types of the side to move leave 12 disagreements
across games because opposing pieces affect which moves are available.

The geometric representation applies when the side to move has only men and
no available capture. A capture by a man must begin with a jump over a
diagonally adjacent opponent onto an empty square, in either direction.
The audit checks this criterion against FMJD capture generation for each
distinct FEN where the mover has no king. With no available first jump, the
legal actions are one-square forward diagonal steps. Turn, mover squares,
and opposing blockers on those forward diagonals determine all destinations
and promotions. Own blockers are already encoded by the mover squares. The
key uses those three ingredients. Positions with a king on the side to move
or an available capture use exact typed occupancy and turn.

The geometry applied to 1,260 of 1,750 distinct FENs. Across the full corpus
it grouped the positions into 1,712 signatures, 38 fewer than exact
occupancy (2.17%). The 61 matched pairs share the current legal action set.
Their positions after a shared move, opponent replies, and best moves can
differ. A held-out, game-grouped test with a trusted search baseline is
needed to measure best-move agreement and regret before any use in Jass
search. Cross-game pairs in this corpus may share openings and observations.

## Reproduce

```bash
PYTHONPATH=.:../draught-master python -m research.mtdp.signature_ablation \
  --pdn data/exports/pcblues/pcblues_games.pdn \
  --output .cache/mtdp/signature-ablation.json
```

PDN SHA-256 is
`025ad0a1a9ddcf508e3284eef65eb1cf76ebf7763d1241a127432f99eac3d8be`.
