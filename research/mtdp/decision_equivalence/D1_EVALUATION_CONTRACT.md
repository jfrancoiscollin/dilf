# D1: score-blind evaluation contract (pre-corpus proposal, 2026-11-18)

Status: **protocol proposal only**. No historical cohort has been frozen under this contract; no Scan scores or Jass improvements are asserted. This document must be frozen and SHA-256 hashed *before* inspecting target scores. If changed after scoring, treat the revision as exploratory, never confirmatory.

## Units and non-equivalences

A position is an FMJD 10x10 board plus side to move and any rule-relevant state. Distinguish (1) equal legal-action sets, (2) equal score-blind signatures, (3) equal argmax actions under one finite reference search, and (4) equal minimax value. None implies the next without proof. A matching top-1 is empirical decision agreement, **not** minimax equivalence. Repeated positions in one game are not independent observations.

## Data admission and partitioning

Use only traceable historical games/FENs, with original source URL, acquisition timestamp, immutable bytes digest, parser/version, full game ID, tournament ID, ply, normalized position, legal actions, and a deterministic ordered record. Reject unparseable/incomplete trajectories, duplicate game IDs, exact normalized FEN overlap across splits, and cross-split contiguous game-window aliases (window 2 and 3); record rejection counts, never silently drop. Reserve the entirety of fFgE7oED (including its 78 targets) and P1RUlfJc (including future positions) from fitting, feature selection, thresholds and validation. Also exclude all known retrospective target games already used to select signatures. Chronological partition by **whole game and tournament**, never by position; document boundary dates before scores. Freeze the complete manifest, exclusions, group assignment, deterministic seeds and SHA-256 of sorted canonical bytes. No cohort is called independent without this evidence.

## Score-blind signature ladder

L: sorted exact legal actions. LCB: existing legal/capture/block descriptor with implementation pinned. Progressive extensions: material/king counts, quiet mobility and blocked men, promotion distance, forced capture and tactical threats, local successor geometry. Features and thresholds must be calculated without any target score. Report collisions by group, eligible coverage, distinct signatures / positions, and pairwise action-set agreement. Any forced capture, tactical instability, unverified transition, missing legal action or feature extraction error invokes **exact tactical fallback** (no transfer). Never use a signature match to discard a legal move.

## Outcome definitions

For each eligible position with complete action-level reference scores from one pinned engine/version/search budget, compare all candidate actions by their *identical canonical move identity*. Ties at the highest score form a set. Top-1 agreement: selected action belongs to reference argmax set. Top-3 recall: reference argmax intersects candidate first min(3, legal-action-count) actions; also report full top-3 set overlap separately. Regret in reference centimen = max reference action score minus reference score of selected action (nonnegative; report median, mean, p95, max). Rank agreement: Kendall tau-b on common actions, report undefined for fewer than two comparable ranks. W/D/L flips: classify each reference score with a **frozen** threshold convention and report confusion matrix and harmful transitions; no post-hoc threshold optimization. A transfer is valid only when its proposed action is legal in the recipient, complete target action scores exist, and no fallback gate fires. Invalid transfers count in denominator and are never silently omitted. Catastrophic tactical error threshold must be frozen before reference scoring.

## Baselines and uncertainty

Compare L, LCB, every progressive signature, canonical legal-action order and seeded random order on exactly the same held-out positions and total search budget. Report unconditional and eligible-only metrics; fallback cost is included. Bootstrap **whole games**, stratified by tournament if enough tournaments exist, at least 2,000 resamples with frozen seed, 95% percentile confidence intervals; report game and tournament counts, not just positions. If only one tournament is available, do not claim tournament-generalizing evidence. All choices made after reading test outcomes are exploratory.

## Gate before Jass

Pre-register concrete numerical acceptance and catastrophic-error limits *in a separately frozen manifest before scores are opened*; until then D1-D is descriptive and D1-E is blocked. Require held-out improvement against both L and LCB in ordering quality without a material increase in regret, tactical-error frequency or fallback-adjusted cost, with game-level uncertainty reported. First Jass experiment must preserve **all legal moves**, change ordering only, pin disposable Jass binary/commit and test paired positions at 10k, 50k and 200k **total** nodes including feature computation and fallback; record wall time, nodes, completed depth, score/choice, crashes and legality. Pruning/selectivity requires a later independent preregistration, exact tactical verification and equal-total-budget control. No Elo claim without adequately powered games.

## Stop / failure criteria

Stop confirmatory analysis on any train/test game or FEN leakage, reserved-arena intersection, untracked target-score access, non-reproducible manifest, legal-move loss, or inability to account for full costs. Mark unknown values as missing, never zero. Report negative results and all counterexamples. No result in this file constitutes a new measurement.
