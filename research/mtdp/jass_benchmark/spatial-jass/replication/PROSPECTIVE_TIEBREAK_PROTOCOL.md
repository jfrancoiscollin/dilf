# Prospective depth-one tie-break control (pre-results protocol)

Status: **design only**. No experimental result is claimed by this document.
This protocol is deliberately separate from the retrospective native-winner intervention.

## Question and falsifiable hypotheses

Does an outcome-blind depth-one tie-break based on the canonical native legal-move order reproduce native Jass decisions while retaining the LCB root visitation order?

- H0: compared with unchanged LCB, the control does not reduce final move disagreement with native Jass at 50,000 nodes.
- H1: the control reduces that disagreement. Report the paired count and uncertainty; do not claim strategic improvement solely from agreement with native.
- Secondary: Scan regret, node cost at completed depth one, and depth-two ordering.

## Leakage prevention

1. Freeze the five-arena manifest, 473-position target cohort, engine commit, build flags, budgets (10,000 / 50,000 / 200,000), and hashes **before** implementing or running the control.
2. The tie-break may read only the position, legal moves, canonical native move order, and scores produced by its own depth-one search. It must not read archived native winners, native search receipts, Scan target evaluations, regret, or final outcomes.
3. A tie is eligible only when all candidate scores being compared are obtained under the same specified search window and proven equal. If the runner cannot establish score equality without privileged data, record the position as *unresolved* and retain unchanged LCB behavior; never infer a tie from differing winners alone.
4. Choose the earliest legal move in canonical native order **among verified equal-scoring maximizers**. Keep LCB root visitation order unchanged; use ordinary Jass bookkeeping for the selected winner. Reject illegal moves and inconsistent transposition entries.
5. Keep the original LCB and native arms untouched. Do not tune the rule after inspecting final results. Any amendment requires a versioned protocol and a fresh holdout.

## Required checks

- Deterministic legal-move ordering and FMJD agreement on the 26 PC Blues replay fixtures.
- No change to depth-one action log, node count, root visit order or returned score except the committed equal-score winner and its downstream bookkeeping.
- Unique receipt and trace per (arena, target FEN, budget, arm); reject duplicates, missing records and nonmatching hashes.
- Original arms reproduce archived non-time fields before comparison; enforce exact budget/stop rules and report depth-limit exceptions separately.
- Reproduce output with Python hash seeds 7 and 61, and record binary/toolchain/patch SHA-256.
- CI: unit tests for unequal scores, equal scores, illegal moves, duplicate receipts, missing traces, and no-tie fallback; run full MTDP suite and downstream FMJD workflow.

## Analysis (all frozen targets; no cherry-picking)

Primary: paired final-move disagreement with native at 50,000 nodes, unchanged LCB versus the new control. Give numerator/denominator and a paired bootstrap confidence interval, clustering by arena/game; show the five arena-specific estimates.

Secondary: Scan-16 ordinary regret (respect nonnumeric WDL categories), optimality transitions, depth-one node deltas, completed depth, and depth-two root-order differences. Report the 10,000- and 200,000-node budgets separately, with no pooling across budgets.

Stratify into: verified ties, unresolved ties, no ties, and the 48 previously audited depth-one disagreements. The 48 are **diagnostic only**, not an independent confirmation set. Include leave-one-arena-out sensitivity and identify outlier influence. Report any exclusions and failure cases, even when unfavorable.

## Stop and interpretation

Stop and publish an audit rather than a score if provenance, uniqueness, legality, or deterministic replay fails. An exact match to native is a mechanistic replication result, not evidence of improved playing strength. Strategic superiority requires a separately preregistered held-out evaluation.
