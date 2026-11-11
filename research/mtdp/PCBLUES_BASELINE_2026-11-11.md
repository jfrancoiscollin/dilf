# MTDP / PC Blues — first observed spatial baseline (2026-11-11)

## Execution evidence

- Repository: `jfrancoiscollin/dilf`, research branch `research/mtdp-foundation`, PR #43.
- Verified head commit: `6bf63baca638eb8669a9493ce396ce0eb7dba014`.
- GitHub Actions `downstream-compat` run **43005586104** (success), job
  `draught-master-pedagogy-tests` (success), completed 2026-11-11.
- Steps `MTDP replay of PC Blues with real FMJD rules` and
  `MTDP spatial dynamics descriptive report` both succeeded.
- Archived artifact: `mtdp-pcblues-spatial-dynamics`, artifact ID
  **13848835363**, SHA-256 archive digest
  `93bf6898127410a167968d27ced97955c704357a2621306c8a097982c566416f`.
- Source of numerical observations: the actual printed JSON in the
  GitHub Actions job logs, **not** an inferred or simulated dataset.
- Workflow: https://github.com/jfrancoiscollin/dilf/actions/runs/43005586104

## Observations

| Measure | Observed |
| --- | ---: |
| PDN games parsed | 26 |
| Games accepted by FMJD replay | 26 |
| Games quarantined | 0 |
| Positions (including initial states) | 1,864 |
| Adjacent-ply transitions | 1,838 |
| Exact position revisits within a game | 0 |
| Transitions leaving all eight coarse descriptors unchanged | 245 |
| Proportion of descriptor-unchanged transitions | 13.33% |

The denominator is **1,838 adjacent-ply transitions**, not 1,864
positions. A transition can change the actual board while leaving all
eight descriptive counts unchanged.

### Descriptor change counts (among 1,838 transitions)

| Descriptor | Changes | Mean absolute ply change |
| --- | ---: | ---: |
| White core-center occupancy | 241 | 0.1311207834602829 |
| Black core-center occupancy | 289 | 0.1572361262241567 |
| White extended-center occupancy | 484 | 0.27475516866158867 |
| Black extended-center occupancy | 469 | 0.2622415669205658 |
| White diagonal adjacency edges | 778 | 0.588683351468988 |
| Black diagonal adjacency edges | 752 | 0.5652883569096845 |
| Occupied squares | 443 | 0.279107725788901 |
| Material balance | 454 | 0.30522306855277476 |

## Interpretation and caveats

These numbers are **descriptive**, conditional on 26 curated PC Blues
games. They do not establish representative frequencies in general FMJD
play, nor strategic equivalence, move quality, or improved search.
Adjacent plies are dependent; the 1,838 transitions are not IID samples.
Zero within-game exact revisits does **not** rule out repeats across games.

The eight descriptors are **count summaries**: they discard square
identities, piece types beyond material balance, tactical obligations,
and side-to-move. In particular, the 245 descriptor-unchanged
transitions **must not** be treated as safe transpositions or collapsed
by the game-tree search. This baseline measures information loss in a
coarse representation, not proven computational savings.

## Next falsifiable experiment

1. Construct a collision dataset of **distinct canonical FENs** with
   equal eight-descriptor signatures, grouping observations by game.
2. Stratify by side to move, material and phase, and quantify collision
   frequencies at game level (avoid treating plies as independent).
3. Compare legal-move sets and tactical outcomes of collision pairs
   using the independent FMJD rules engine. A single counterexample
   invalidates any claim that the signature preserves legal actions.
4. Only after a fixed protocol, evaluate best-move agreement against a
   trusted evaluator on **held-out games**, with simple material/phase
   baselines and uncertainty computed by resampling games.

No game-tree reduction should be enabled in Jass based on this report.
