# H13 — historical JNNW/JSM1 byte lineage reproduced

Code/protocol commit04a8f8b5d24d27ff41d3054de6895648d47c07ed.
Actions run45304083764/job138143506016 completed successfully, including
12 synthetic tests and all three historical byte transformations. No engine,
training, fresh target scoring, R2 access or duplicate campaign.

Artifact14879932509 downloaded; ZIP SHA-256 matches GitHub:
bc94a1b8041524328c66b803ba7780ce4a0b2c895bf5f0a0a083010ec354659a.
The exact JSON is validation/jsm1-lineage-reproduction-2026-11-24.json,
SHA-256 95df9cf38573575b3d0229d660af0d7b08c8ba247f09d79e45c0211fdf5064e9.
Jass transformer and data snapshot commits, manifest and code SHA-256 are
pinned in the preregistered protocol and the JSON.

| Historical operation | Published output | Position payload | Metadata payload |
| --- | --- | --- | --- |
| Merge common+extra, renamespace nested IDs | f2m.raw | exact SHA-256 match | exact SHA-256 match |
| Mix PARENT/FRESH 1:1, seed141421, namespaced openings | turnover1to1 | exact SHA-256 match | exact SHA-256 match |
| Opening split, mod10, seed577215 | m2.fit | exact SHA-256 match | exact SHA-256 match |

**6/6 expected output payloads reproduced without changing recipe or seeds.**
The published files have the deterministic transformation relationship specified
by the historical Jass tool. This establishes compatibility of the position
and metadata transformations *relative to the initial published source pairs*.
It is stronger than merely observing equal lengths and matching filenames.

## Implication for independent cohorts

In the pinned original tool, merge copies records, mix selects and copies input
records, and split reorders the complete set of records (train followed by
holdout); none creates new board states. These code paths were inspected at
Jass commit336bb98451a205266d6646c4d801027af4b30294,
tools/selfplay_frontier.py: do_merge, do_mix, do_split.

Consequently the six published files' **10M gross observations derive from
at most 4M ancestral input record occurrences**: common0.5M + extra1.5M +
fresh M2 2M. This is a logical upper bound from the reproduced copy/select
recipe, not a measurement of unique positions or independent games. The three
derived files cannot constitute independent confirmation of those same inputs.
Never split these six files into nominally independent D1 training/test sets.
Namespaced numeric game/opening IDs do not remove board or trajectory leakage.

## Remaining admission gate

Initial source row alignment, authentic game/opening/event identities, ply,
full legal trajectories and historical exclusions remain unproved. In
particular, both outputs can be perfectly reproduced from a consistently
mispaired original input: this experiment cannot authenticate the originals.
All corresponding JSON admission flags remain false. No inference of
best-move preservation, minimax equivalence, safe pruning or Jass gain.
The four reserved events remain excluded and no new cohort is frozen.

Next: inspect initial generator code and pinned generation receipts for M2 d8
and the common/extra F2M sources, including original run identities and merge
contracts. Do not recompute these already reproduced transforms without a new
failure or changed input. Authenticate trajectories and exclusions before any
D1 independent cohort or prospective equal-total-budget Jass/Scan experiment.
Jeff's PC is not required for the completed byte-reproduction stage.
