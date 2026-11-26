# MTDP — Three-question research charter (2026-11-26)

Status: prospective mathematical framework and proposed diagnostic increment; no new efficacy result, no authorization to alter frozen protocols. User decision: prioritize Q1 strategic equivalence, Q2 minimal decision information, Q3 substantial Jass computation reduction.

## Evidence boundary

At PR #43 head 1bc82adaf85dc9af1bf83a5c549c1901443e9232, RELAY_COORDINATION.md records concordance of legal roots and typed-occupancy+turn successors for the conservative registry of 455,582 FEN from 25 known sources, reproduced on Actions. This is not a full game-state certification (draw clocks, repetition), a fresh independent cohort, or decision equivalence. PROTOCOL.md records the historical Q signature: 1,750 FEN, 1,712 classes, 61 distinct-position pairs with identical legal actions; only 2.17% class-count reduction. Archived equal-node tests did not demonstrate a gain. Preserve these negative and descriptive results.

## Q1 — What equivalence actually means

Let s be a complete game state, A(s) its legal actions, T(s,a) its transition, and Q(s,a) the side-to-move action value on a common ordered utility scale. A comparison of two states requires an explicit bijection phi between their legal action sets (or a separately specified partial map with uncovered actions accounted for). Capture paths, promotion and legality are part of the map; occupancy and turn alone need not encode draw history.

Distinguish:
- structural equivalence: same versioned signature;
- legal equivalence: bijective action map;
- exact decision equivalence: phi maps the entire argmax set onto the target argmax set;
- ordinal equivalence: phi preserves the weak order of all actions;
- value equivalence: all mapped Q values equal;
- recursive game equivalence: terminal utility and mapped transitions preserved recursively, with complete state and draw rules. This sufficient condition implies minimax equivalence on finite game trees; it is not established by one-ply legal/successor checks.

A pair can have equal legal sets but different optimal actions. Approximate pairwise similarity need not be transitive, so do not call thresholded similarity an equivalence relation or merge via connected components without a diameter/representative guarantee.

### Margin lemma (mathematical, conditional)

Suppose a score surrogate q on the same legal action set satisfies |q(a)-Q(s,a)| <= e uniformly over actions. Let a_hat maximize q. Then Q(s,a*) - Q(s,a_hat) <= 2e, because Q(s,a*) <= q(a*)+e <= q(a_hat)+e <= Q(s,a_hat)+2e.
If the unique true optimum has gap Delta = Q(s,a*) - max_{a != a*} Q(s,a) > 2e, the surrogate preserves it. Equivalently a surrogate gap > 2e certifies its unique optimum under the same bound. Equality does not certify uniqueness; forced moves and ties are reported separately.

This links discarded information to decision stability. Empirical error estimates against finite-depth Scan are not deterministic bounds against minimax, and cannot authorize irreversible pruning. Category transitions (win/draw/loss) retain the existing protocol's separate handling.

## Q2 — How much information may be discarded?

Use existing D1 E/L/LCB/Q/Q+ signatures, preserving frozen semantics, and prospective nested feature removal experiments. Verify nestedness with refinement.py; nonnested variants are independent comparisons, not a hierarchy.

For each representation report:
- class-count reduction 1-K/N over N distinct board keys and K distinct classes (not a bit compression estimate);
- empirical entropy of class labels, actual encoded byte size including maps, fallback, dictionaries and any model, and amortized memory cost relative to a specified exact codec;
- cross-game eligible coverage, mapped-action ambiguity, collision diameter/heterogeneity and fallback share;
- optimum-set hit, top-K agreement, regret and catastrophic/WDL outcomes on identical covered targets; unconditional outcomes including fallback; stratify by phase, legal action count, capture/king, and reference margin.
- For training only, estimate the distribution of max mapped value residual and margin; on held-out games measure the predicted risk vs observed regret. Report calibration and uncertainty at the game/tournament level. No target label may select a signature, threshold or cohort.

Report compression-quality-coverage Pareto fronts rather than only accuracy on convenient covered positions. Theoretical minimum representation for one fixed decision task may be its answer itself, but that is not a useful representation if it costs full search to compute; all feature and inference costs count in Q3. Exact minimax, finite-depth reference, and empirical approximation remain separate.

## Q3 — Can this save actual computation?

Define total cost = signature + lookup/inference + verification + fallback + search, measured in wall time as well as native nodes. Compare identical position/game pairs:
1. Ordering only, all legal moves retained; same node budgets and native controls per PROTOCOL.md.
2. Only after independent gate passage, compare cost at a fixed quality target with preregistered noninferiority tolerances, paired intervals, and adaptive fallback. No pruning absent proven bounds or exact verification.
3. Only after both, paired games at equal time and equal nodes with color/opening swaps, and strength confidence intervals.
Class-count compression does not imply node or runtime reduction. Report overhead, cache warm/cold settings, failures, coverage and worst-case errors.

## Next bounded experiment (proposal, not a frozen run)

First inventory existing score-blind D1 collision/refinement reports and the authenticated historical catalogs. Reuse, do not replay, closed legality/successor checks. Identify which E/L/LCB/Q/Q+ metrics already exist. On the historical registry, if access and semantics permit, compute missing score-blind class size/coverage and actual encoded size summaries (no Scan score acquisition, no independent efficacy claim), preserving existing exclusions and complete provenance. Freeze a prospective test only after license/provenance/independence and target-blind admission gates; historical registry and reserved fFgE7oED cannot serve as new independent evaluation. Existing R2 inventory should be inspected for lawful authenticated eligible source candidates, not assumed accessible.

H:43 owns Q1 definitions and counterexamples; H:28 owns Q2 ablations and compression/coverage/regret; H:13 owns Q3 instrumentation and gated Jass validation. A technical task is justified only by a specific Q1–Q3 prerequisite. Keep all existing freeze and operational restrictions; repair/relaunch technical failures only without changing frozen science. Do not duplicate active experiments or modify production, merge, or incur new cost without authorization.
