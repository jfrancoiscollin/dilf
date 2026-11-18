# D1 — Audit of top-K saturation and paired evaluation (2026-11-18)

**Status: score-blind methodological amendment proposed; not frozen, not a new cohort, no Scan/Jass outcome.**

## Falsifiable failure mode

For a legal-action set A of size n, the candidate list is the first min(3,n) actions. If n <= 3, **every** complete legal ordering has top-3 optimal-action recall equal to 1, irrespective of its quality. Consequently a pooled top-3 rate can be dominated by positions on which *no* signature can improve the metric. If all legal moves are in the top-3, an apparent agreement is a tautology, not decision equivalence.

Synthetic checks (mathematical, not empirical observations):
- n=1, optimal action last/first: every ordering has recall@3 = 1.
- n=3, optimal action ranked third: recall@3 = 1, but top-1 = 0.
- n=4, optimal action ranked fourth: recall@3 = 0; moving it to third changes recall@3 to 1.
- Tied optimal actions: success is intersection with the *whole* optimal set, not an arbitrary tie-broken label.

## Proposed preregistration amendments before any score access

1. Report n=1, n=2, n=3 and n>=4 strata and their counts. The **primary discriminating recall@3 estimand** should use positions with n>=4, with a separate unconditional descriptive recall@3 over all positions. Do not retrospectively replace the existing numerical gate: amend and freeze it first.
2. Define a single score-blind eligibility mask and compare D1, L, LCB, canonical legal order and seeded random on **identical target positions**. Report coverage and fallback over *all* held-out positions. A candidate-specific mask cannot silently improve the denominator.
3. If a signature cannot propose a full ordered list of the recipient's legal actions, report its exact deterministic completion rule (e.g. append remaining actions in canonical order) and include that cost. If no valid mapping exists, fallback and count it. Never infer a legal move identity from the equality of two signatures.
4. Measure recall@1, recall@3 (n>=4 primary), rank correlation on common fully scored actions, selected-action regret, and full top-3 set overlap as separate outcomes. A list that contains the best action is not evidence that its first move is best.
5. Bootstrap **whole games**, paired across arms; recompute each metric from the resampled games rather than resampling position rows. Preserve tournament strata and publish both numerator and denominator for every arm. If a stratum lacks adequate distinct games, mark its confidence interval exploratory.
6. For a decision gate, retain the original proposal as historical record; publish a versioned numerical-gates amendment with the revised primary estimand and frozen hash **before** opening any target Scan scores. If already exposed, use a genuinely new holdout rather than retroactively claiming confirmation.

## Stop conditions

No confirmatory recall@3 claim if the n>=4 denominator is missing, scores are incomplete, ties are mishandled, paired masks differ, or the candidate list is assembled using target scores. Even perfect recall@3 does not establish minimax equivalence or safe pruning. D1-E remains blocked until the independent gates pass.

## Verification recipe

On any future frozen scored manifest, group by whole game and tournament, tabulate `legal_count` before computing score-dependent metrics, assert that every n<=3 position has recall@3=1 for every *complete* legal ordering, then compare arms only on the identical n>=4 target set. Failure of this assertion indicates an action-identity, missing-score, or ranking implementation defect.

**No dataset accessed for this audit; these are deductive properties of the metric.**
