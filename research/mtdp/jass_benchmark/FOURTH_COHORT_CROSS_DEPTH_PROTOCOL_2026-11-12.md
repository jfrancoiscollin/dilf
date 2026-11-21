# Preregistered fourth-cohort cross-depth replication

Status: **protocol only — no fourth cohort selected, no Scan or Jass runs claimed**.
Registered after the three-cohort equal-size offline comparison at commit
`318ac6759c71312552fe571a6f612c5c6f73e058`. This document must not be
changed in response to the fourth-cohort outcomes; amendments require a dated
new file with explicit reasons.

## Question and estimand

Does a three-move shortlist transferred from PC Blues, **ranked only by
source Scan depth 12**, cover a target-optimal move and reduce the regret of
the best candidate under **target Scan depth 16**, compared with the first
three legal actions sorted by their frozen Jass keys (UTF-8 byte order)?
This is an offline shortlist-oracle experiment, **not** evidence that Jass
plays better under a finite node budget.

Primary outcomes on eligible target positions:
1. Paired difference in coverage of the depth-16 target-optimal move,
   transferred minus canonical (percentage points).
2. Paired difference in depth-16 target-score regret of the best
   shortlisted move, transferred minus canonical (centimen).

Report both even if they disagree. A positive coverage difference and a
negative regret difference favor transfer. Secondary outcomes: regret
>= 50 centimen, worst regret, overlap of shortlists, and tied source
scores at the third-place cutoff. No post-hoc filtering of unfavorable
positions.

## Cohort freeze before scoring

1. Select one publicly identifiable FMJD tournament absent from the
   three frozen event IDs `Z3s40c6H`, `iPQl7g7q`, `0gB7ETSW`,
   PC Blues and any source-selection material. Record event URL,
   dates, license, download timestamp, raw bytes SHA-256 and parser
   version/commit. If provenance or reuse rights are uncertain, stop.
2. Replay every game with the existing FMJD adapter, retaining a
   game-level trace of accepted/rejected moves and rejection reasons.
   Exclude invalid games **before** inspecting Scan scores.
3. Deduplicate target positions deterministically by complete FEN
   including side to move. Freeze a deterministic position selection
   rule and its random seed before evaluating any targets. Record
   every target's contributing game IDs. If any selected FEN overlaps
   any of the three previous target cohorts or PC Blues source
   positions, exclude it before scoring and log the overlap.
4. Require an unambiguous one-to-one mapping of every legal DILF
   action to its frozen Jass key. Ambiguous multiple-capture paths
   are excluded with counts and reasons, never silently merged.
   Preserve all legal moves, including captures, in the manifest.
5. Commit the immutable input manifest and a provenance JSON with
   SHA-256 for every input and engine binary, Scan build/version,
   time controls, depth, evaluation perspective, and selection code
   commit. Only then start target depth-16 scoring.

## Locked analysis

- Use source depth-12 scores exclusively to rank transfer candidates.
  Target depth-16 scores are never used to select either shortlist.
  Sort ties by UTF-8 bytes of frozen Jass keys, not numerical tuples.
  Both arms contain `min(3, number_of_legal_moves)` distinct legal
  actions; any position with fewer than three legal actions must be
  reported separately and kept in the primary intention-to-evaluate
  table.
- Verify complete source and target legal-action score catalogues,
  matching action sets and score perspectives; fail closed on missing
  values, ambiguous keys, non-finite scores or mismatched SHA-256.
  Freeze how forced wins/losses and mate-like scores are handled before
  scoring; report non-ordinary scores separately rather than silently
  converting them to centimen.
- Compute the paired outcomes at the position level. Bootstrap 10,000
  replicates, resampling **whole games** with seed 20261112, preserving
  within-game dependence. Positions appearing in multiple games
  require a deterministic, pre-scoring ownership assignment and a
  sensitivity analysis excluding multi-game positions.
- Publish counts and 95% intervals, the complete 2x2 coverage table,
  distribution of regret differences, tie rates and exact denominators.
  Report game-cluster counts. Do not interpret a confidence interval
  excluding zero as independent proof of playing strength.
- Run twice with distinct `PYTHONHASHSEED` values, require
  byte-identical JSON output and record its SHA-256. Run MTDP and
  downstream compatibility tests. If Jass is absent, mark live
  mapping tests **skipped**, not passed.

## Stop and interpretation rules

Stop on provenance mismatch, mapping ambiguity, corrupted games,
incomplete evaluation, missing hashes or unexpected action catalogues;
do not repair exclusions based on observed outcomes. No merge to
`develop`, deployment, paid compute, or PC requirement is authorized
by this protocol. Request approval before any paid or heavy local run.

The previous three-cohort comparison is exploratory for this
replication: its depth-matched source and target rankings may inflate
apparent transfer quality relative to the locked cross-depth test.
A fourth-cohort advantage would support **shortlist information
transfer**, not Jass search efficiency. A Jass playing-strength claim
requires a separate, node-matched and game-clustered benchmark.
