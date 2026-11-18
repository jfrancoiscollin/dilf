# D1 — Amendment 1: discriminating top-3 and score units (2026-11-18)

**Status: prospective proposal, NOT frozen or confirmatory. No target scores read or analysed in this amendment.** Supersedes no existing frozen protocol. This document is not an independent cohort.

## Population and denominators

For each held-out target position p, compute its complete FMJD legal-action set A(p) **without using Scan scores**. Let n(p)=|A(p)|. Preserve all positions, including n=0 and n<=3, in the coverage accounting; n=0 has no decision and is excluded from action-ranking denominators with its count reported. Stratify n=1,2,3,>=4. The primary discriminating recall@3 population is **n>=4**. Report unconditional recall@3 on n>=1 only as descriptive. A perfect recall@3 for n<=3 is a mathematical tautology when the list is complete.

For each candidate signature and each control (L, LCB, canonical legal order, seeded random), apply a **common, score-blind target eligibility mask** and the same positions for paired comparisons. Report both intention-to-evaluate (all held-out n>=4 positions, counting unavailable transfers as failure/fallback) and conditional valid-transfer metrics. Never silently change denominators by arm.

## Operational definitions

- A predicted ordering must be a permutation of A(p), with no missing or duplicate legal actions. For a partial proposal, append remaining legal actions in canonical order; charge the full mapping/completion cost. Invalid mapping triggers canonical fallback and increments fallback counter.
- Reference optimum O(p) = all actions tied for maximum target Scan score; do not arbitrarily break ties.
- recall@k(p) = 1 if the first min(k,n) actions intersect O(p), otherwise 0. Recall@3 for n>=4 is the **primary** recall estimand; recall@1 and the rank of the first optimum remain separate.
- selected-action regret = max target score minus the target score of the **first** proposed action, not the best of its top three. Top-3 oracle regret, if computed, must be explicitly labelled optimistic and never substituted for first-action regret.
- Top-3 set overlap, pairwise rank concordance and win/draw/loss transitions are separate outcomes. Rank concordance requires complete comparable target scores and explicit tie handling.
- Scores: the historical field `centimen` is the stored **integer Scan score**, equal to 0.01 HUB exported unit; it is **not proven to represent 0.01 material pawn**. Retain raw integer thresholds, report their units, and do not silently translate a 50-integer gate into a half-pawn material claim.

## Paired inference and stop rules

Resample **whole games**, stratified by tournament, with a fixed documented seed, using the *same sampled game IDs across all arms*. Recompute ratios from numerators and denominators on every bootstrap draw; report per-arm and paired-difference 95% intervals and number of independent games/tournaments. Do not bootstrap position rows. Report n>=4 game counts separately; if insufficient, mark estimates exploratory.

The previously proposed +3 percentage-point recall@3 improvement over **both L and LCB** is evaluated on n>=4 only *if this amendment is frozen before target-score access*. All other numerical gates in D1_NUMERICAL_GATES_PROPOSAL.md remain proposals until explicitly frozen together. Stop confirmatory claims if a mask differs by arm, legal sets are incomplete, score coverage differs, tie semantics fail, or target scores were used to select signatures. If any target scores for the intended cohort have already been seen, that cohort is exploratory and a new genuinely independent holdout is mandatory.

No same-signature, same-legal-moves, same-best-move or minimax-equivalence implication is assumed. No pruning or selective Jass search is authorised by this amendment. D1-E remains gated by independent evidence and full cost accounting.

## Verification examples (deductive, not data)

| n | first optimum rank | recall@1 | recall@3 |
|---|---:|---:|---:|
| 1 | 1 | 1 | 1 |
| 3 | 3 | 0 | 1 |
| 4 | 4 | 0 | 0 |
| 4 | 3 | 0 | 1 |

A test fixture with two tied optimal actions at ranks 2 and 4 must score recall@3=1; a test fixture with a suboptimal first action but optimum at rank 3 must have positive selected-action regret even though recall@3=1.

## Preregistration dependency

Before any new D1 target scoring: publish the source-game manifest and SHA-256, reserved-arena exclusions (including **all** fFgE7oED and P1RUlfJc), split by game/tournament, signature versions, tie handling, numerical gates, and this amendment in a single frozen, hash-verified receipt. Do not relabel historical Scan/Jass evaluations as independent.
