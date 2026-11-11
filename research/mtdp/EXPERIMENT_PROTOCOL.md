# MTDP — preregistered experimental protocol (draft v0.1)

## Research question

Do candidate spatial descriptors provide incremental, out-of-sample information
about future outcomes or stable engine assessments **beyond** material,
side-to-move, game phase and tactical context?

This is a *hypothesis*, not an established result.

## Null and alternative

- **H0:** Spatial descriptors do not improve held-out predictive performance
  beyond a prespecified baseline with material, phase and turn.
- **H1:** At least one prespecified spatial descriptor improves held-out
  predictive performance over that baseline, with a reproducible effect.

Initial descriptors: central occupancy, same-side diagonal adjacency,
occupied fraction. These are deliberately simple; no legal control is
inferred. Candidate influence fields require separate definitions and tests.

## Sampling and leakage control

1. Dubois tactical diagrams: audit/exploration only; not the primary
   population for estimating general positional value.
2. PC Blues games: a small trajectory pilot only; all plies of a game
   belong to the same split. No per-position random split.
3. Later independent game corpora: separate sources, players/openings and
   preferably time periods for external validation.
4. Remove or cluster repeated positions and related opening transpositions.
5. Stratify by material balance, piece count, turn and verified king status.
6. Respect source restrictions and avoid publishing copyrighted game text.

## Labels and engine comparability

- PGN/PDN result tags are provenance, **not** verified WDL labels.
- Scan score is a *proxy*, not ground truth. Fix engine version, hash,
  node/time budget, perspective, hardware and evaluation protocol.
- Do not compare uncalibrated evaluations from Jass and Scan directly.
- Evaluate multiple search budgets to assess label stability.
- Separate tactical positions (forced captures, short combinations) from
  quiet positions using a verified FMJD rules engine.

## Analysis plan

1. Generate audited records and provenance summaries.
2. Inspect distributions, duplicates, king-type uncertainty and sampling
   bias **before** calculating predictive correlations.
3. Baseline model: material, phase and turn. Enhanced model adds a
   *predeclared* set of spatial descriptors.
4. Compare held-out MAE (continuous engine labels) and calibration; report
   per-game bootstrap confidence intervals rather than per-position CIs.
5. Include feature ablations, sign consistency across game phases and
   independent-corpus replication.
6. Correct for multiple comparisons when testing many metrics.
7. Preserve negative results; do not choose hypotheses after inspecting
   test-set scores.

## Stop / promotion criteria

Do not integrate a metric into Jass or stable DILF APIs unless its effect
is reproducible across independent corpora and, for Jass, improves a
controlled paired-engine match or equivalent strength benchmark.

## Compute budget

Stage 1 (metadata, metrics, audit): lightweight, suitable for GitHub Actions.
Stage 2 (legal PDN replay): modest, possible in CI with trusted engine.
Stage 3 (Scan evaluations over many positions, repeated budgets and paired
matches): potentially heavy; use dedicated machine/runner and request the
user's PC only when remote compute is insufficient.
