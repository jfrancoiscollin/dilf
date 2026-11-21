# MTDP-D1 B4 — score-blind E/L/LCB/Q engineering audit (2026-11-17)

## Immutable evidence
- Branch HEAD at audit: `c2c0f3f3753007fad58ad6900a83bb3bb90c31a7`.
- [D1 GitHub Actions run 43995533942](https://github.com/jfrancoiscollin/dilf/actions/runs/43995533942), job 133746539853, completed **success**, with **12/12 tests passed**.
- [Artifact 14289631432](https://github.com/jfrancoiscollin/dilf/actions/runs/43995533942/artifacts/14289631432), `mtdp-d1-pcblues-score-blind-engineering`, 81,363 bytes as reported by GitHub.
- FMJD replay on historical PC Blues: **1,864 observations**, **1,750 distinct FENs**. Workflow log prints the signature counts below; workflow asserts the collision safety checks.

| Key | Distinct signatures | Reduction vs exact E | Meaning |
| --- | ---: | ---: | --- |
| E | 1,750 | 0 (0.00%) | Exact typed occupancy and side to move |
| L | 1,464 | 286 (16.34%) | Complete canonical legal-action set |
| LCB | 1,709 | 41 (2.34%) | Quiet positions: legal actions, mover-men count, immediate opponent blockers; exact fallback in tactical/king cases |
| Q | 1,712 | 38 (2.17%) | Quiet-man geometry; exact fallback in tactical/king cases |

The CI asserts `E.distinct_fen_pairs == 0`, `LCB.different_legal_action_pairs == 0`, `Q.different_legal_action_pairs == 0`, `Q.distinct_fen_pairs == 61`, and `LCB.distinct_signatures >= L.distinct_signatures`. It does **not** assert LCB is a refinement of Q or vice versa; signature counts alone do not establish nesting or agreement of the best move. In particular, the 61 Q pairs are the **previously seen** historical regression, not a prospective independent result.

## Interpretation and next gate

LCB compresses 41 distinct FEN signatures (2.34%) versus exact E, compared with Q's 38 (2.17%), while preserving legal-action sets for grouped positions in this historical corpus. The relative difference is **three signatures**, not evidence of better strategic transfer. L is much more compressed, but that alone is not evidence of decision safety. No Scan scores, best-move agreement, top-3 recall, regret, or Jass equal-node strength are measured by this job. **No pruning or move-ordering efficacy claim is warranted.**

Next D1 action: implement a deterministic pair-level comparison of LCB vs Q on the archived score-blind JSONL: identify LCB-only/Q-only/common matched distinct-FEN pairs, cross-game provenance, legal-action discrepancies, and tactical fallbacks, with synthetic tests. This comparison must remain score-blind. Only after preregistration and an independent, disjoint cohort freeze should D1 compare Scan action ranks and regret. The reserved fFgE7oED 78-target tie-break cohort is not a D1 tuning set. No changes to Jass production.
