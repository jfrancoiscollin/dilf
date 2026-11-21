# D1 numerical decision gates — prospective proposal (2026-11-18)

**Status: proposed, NOT frozen or confirmatory.** Must be reviewed, fixed, hashed together with the cohort manifest, exclusions, Jass version and analysis script **before** accessing any held-out Scan action scores. Changes after access are exploratory. The already-scored PC Blues, quick tournament and 61-pair material cannot be re-labelled independent.

## Estimands and eligibility
Unit of resampling: whole game; split by game and tournament. Report every denominator: all positions, candidate transfer positions, legal transfers, tactical fallbacks, missing-score exclusions, distinct games and tournaments. The comparison is paired on exactly the same held-out target positions. Never infer minimax equivalence from equal signatures, legal sets or top-1.

Use pinned Scan score units: 1 pawn = 100 centimen **only if the engine score contract confirms that conversion**; otherwise block centimen claims until the unit mapping is documented. Define regret for target position p and proposed action a as max_m S_p(m)-S_p(a), requiring complete action scores for all legal m. For ties, membership in the entire optimal-action set is success. All absent or incompatible scores are missing, never zero.

## Proposed go/no-go gates for D1-D
These numerical values are *design choices*, not findings:
1. Leakage gate: zero reserved-game/FEN overlaps, zero split-game overlaps, zero duplicate canonical FEN across splits, zero cross-split contiguous-window aliases (length 2 and 3); any violation stops confirmation.
2. Adequacy gate: at least 100 **distinct held-out games**, from at least 3 tournaments and at least 30 distinct source-signature groups with >=2 positions each. If unmet, report descriptive estimates only, with no go decision.
3. Eligible coverage: >=20% of all held-out positions after tactical fallback, with 95% game-bootstrap CI lower bound >=10%; coverage below this means no deployment claim.
4. Ordering-quality gate: on the same paired held-out positions, top-3 optimal-action recall improves by >=3 percentage points over **both** L and LCB; lower bound of the paired game-bootstrap 95% CI for each difference must exceed 0. Also compare canonical legal order and seeded random.
5. Safety gate: mean regret difference vs each L and LCB <=+2 centimen (upper one-sided 95% game-bootstrap bound <=+2); catastrophic regret >=50 centimen in at most 0.5% of all eligible transfers, with one-sided 95% upper bound <=1%; zero observed illegal actions. Report maximum regret and all counterexamples irrespective of passing gates.
6. Multiple candidate signatures: choose exactly one on training games only; the held-out evaluation is performed once. If selection uses test scores, label the entire analysis exploratory and acquire a new independent holdout.

Bootstrap >=2000 game-level resamples with a recorded deterministic seed, stratified by tournament where viable; compute paired differences per resample. If tournament count is inadequate, explicitly decline cross-tournament generalization. Predefine W/D/L classification thresholds and engine-score perspective in the freeze bundle; missing thresholds block W/D/L claims. Tau-b is undefined for <2 comparable actions.

## D1-E authorization is a separate gate
Passing D1-D **authorizes only an ordering-only experiment** in a pinned disposable Jass checkout; it does not authorize pruning. Preserve all legal moves. Compare native / L / LCB / D1 ordering at 10k, 50k and 200k total-node-equivalent budgets, charging signature, fallback and adapter work; publish both actual engine nodes and total normalized cost, wall time, completed depth, move, score and errors. Randomize arm execution order per position. Require >=100 independent games before claiming general improvement. Selectivity needs a new frozen protocol, exact tactical verification and its own holdout.

## Explicit stop criteria
Any leakage, unverifiable chronology/provenance, missing legal move, inconsistent score perspective, unaccounted feature cost, or post-hoc threshold tuning stops a confirmatory claim. Failure of any gate is a negative or inconclusive result, not a reason to retune on the test cohort.
