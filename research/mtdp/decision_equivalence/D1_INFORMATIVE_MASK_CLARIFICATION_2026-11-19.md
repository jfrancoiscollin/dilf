# D1 — Score-dependent informative@3 is diagnostic only (2026-11-19)

**Status: prospective clarification, NOT frozen; no new cohort, target scoring or Jass benchmark.**

## Identified estimand hazard

The executable `ranking_metrics.evaluate_order` returns both `discriminating_at_3 = (n_legal >= 4)` and `informative_at_3 = (n_legal >= 4 and n_optimal <= n_legal-3)`. The latter requires *target scores* to determine `n_optimal`. Consequently, `informative_at_3` **must not be used as the primary population eligibility mask, training filter, signature-selection rule or shared transfer/fallback mask**. Doing so would violate the preregistered score-blind eligibility requirement and condition the estimand on the outcome. The property is valid mathematically but cannot define a pre-score target cohort.

## Locked evaluation hierarchy proposed for the future freeze

1. **Primary intention-to-evaluate denominator:** every independently held-out, provenance-eligible, nonterminal position with `n_legal >= 4`, selected from FMJD legal actions before scores. Include invalid mappings as failures with explicit fallback accounting. Apply the *same* target positions to L, LCB, canonical legal order and all candidate signatures. Record counts of n=0,1,2,3 separately.
2. **Primary outcome:** recall@3 and its paired improvement versus **both** L and LCB, calculated on that fixed n>=4 population, alongside recall@1 and first-action raw-score regret. The previously proposed +3 percentage-point gate remains a proposal, not a validated finding.
3. **Secondary outcome-dependent diagnostic:** after the frozen evaluation, report `informative_at_3` counts and recall@3 *within* the subset where a miss is mathematically possible. Label this a **conditional descriptive estimand**, not a replacement for the primary result; report the complementary guaranteed-success subset separately. Do not retune or exclude rows based on this diagnostic.
4. **Independent rank evidence:** first-optimum rank, first-action regret, full-rank concordance with explicit ties, and W/D/L transitions. Top-3 oracle regret is optimistic and never substitutes for first-action regret.
5. **Inference:** game-level, tournament-stratified paired bootstrap with fixed seed, identical resampled game IDs for all arms; denominators recomputed per draw. Never bootstrap individual positions as independent observations.

## Mathematical sanity checks (deductive, not empirical)

For n legal actions and m tied optimal actions, every size-three prefix intersects the optimum set exactly when `m > n-3`. Thus n=4,m=2 gives guaranteed recall@3=1, whereas n=4,m=1 allows a miss. These examples do not establish same-best-move or minimax equivalence.

## Pre-freeze and safety

Freeze the score-blind corpus manifest, source-game/tournament split, exclusions of all fFgE7oED, P1RUlfJc, s7ahYqL4 and D9PF2OSW games/FEN, signature versions, raw score semantics, numerical gates and this hierarchy **before** target-score access. Previously scored cohorts remain exploratory. No pruning is authorised; eventual Jass ordering must preserve all legal actions and charge all overhead at 10k/50k/200k equal total-node budgets.

**Next D1 action:** implement an aggregate report that enforces the fixed n>=4 primary denominator and marks the informative@3 subgroup explicitly secondary, with synthetic regression tests; then audit independent historical corpus provenance.
