# MTDP-D1 — Decision-equivalence research protocol (v0.1)

Status: **preregistered design draft, no efficacy result**. This file is research-only and does not authorize Jass production changes, unsafe pruning, or reusing the archived five arenas as an independent holdout.

## Scientific question

Can a position signature predict **stable action ranking** across distinct FMJD 10×10 positions while compressing the representation, and can that information subsequently improve Jass alpha-beta search **at equal total node cost**?

The following are separate propositions:
1. Same signature does **not** imply same legal actions.
2. Same legal actions does **not** imply same successors, best action, or minimax value.
3. High empirical top-K agreement does **not** establish safe branch pruning.
4. Only a proved bound on value or an exact search verification may justify an irreversible exclusion.

## Existing evidence and guardrails

- `LEGAL_SIGNATURE_ABLATION_2026-11-11.md`: 1,750 distinct PC Blues FENs; the quiet-man geometric signature yields 61 distinct-position pairs with identical current legal actions and 1,712 signatures (2.17% fewer than exact occupancy). These are descriptive training/engineering data, not independent strategic-equivalence evidence.
- `successor_audit.py` checks one-ply successors and explicitly refuses to infer minimax equivalence.
- `jass_benchmark/eighth-replication/scan-results/RESULTS_2026-11-12.md`: on 138 common targets, the LCB versus L best-of-three Scan-regret difference is -0.12 centimen with interval [-0.52,+0.19]; no demonstrated paired advantage.
- `jass_benchmark/spatial-jass/replication/REAL_NODE_METERED_ARCHIVE_VERDICT_2026-11-15.md`: 473 archived positions × 3 budgets; no quality gain over native at equal total nodes. These archived positions must not be rebranded as a prospective test.
- The `fFgE7oED` candidate and its 78 common L/LCB targets belong to the **separate preregistered native-order tie-break protocol**. D1 must not use these targets to tune signatures or claim its own independent evaluation.

## D1-A: falsifiable hypotheses

**H1 (coverage):** a signature richer than L (legal-action fingerprint) and LCB (count/blocker key) produces at least one distinct-position, cross-game pair with a shared action mapping in a new independent test population. If no eligible pairs exist, report zero coverage, not a positive quality result.

**H2 (ranking stability):** for matched distinct positions with a valid one-to-one action mapping, transferring a source Scan ranking to a target gives lower mean top-three regret than a preregistered baseline on **the same target positions**. This is a paired comparison; never compare aggregate means across differing target populations.

**H3 (tactical safety):** the candidate does not increase the rate of catastrophic action-selection errors (ordinary regret >= 50 centimen, plus any adverse win/draw/loss category transition) beyond a preregistered tolerance. Report all worst cases, not only the average.

**H4 (search utility):** only if H2 and H3 survive independent evaluation, a Jass root ordering that retains all legal actions improves Scan regret or search efficiency at fixed total 10k/50k/200k nodes relative to Jass native. All signature computation, probes and search nodes must be metered; an ordering-only test must never remove actions.

## D1-B: signature ladder and controls

All signatures must be deterministic, versioned and calculated from board state and legal moves **without target Scan scores**:
- **E**: exact typed occupancy + turn (collision-free reference, zero generalization).
- **L**: full legal-action fingerprint (path, captures, promotion) + turn.
- **LCB**: published count/blocker representation; retain published semantics.
- **Q**: existing quiet-man geometry with exact tactical/king fallback.
- **Q+**: experimental augmentation of Q with promotion distance, legal mobility counts, opponent reply/capture threats and blockade geometry. Each feature must have an ablation and be computed from legal FMJD state, not inferred from FEN text alone.

For each signature report distinct FEN count, signature count, collision pairs, cross-game pairs, valid action-map pairs, false legal-set matches, successor disagreement, fallback fraction and computation cost. Keep source/target action mapping explicit and reject ambiguous capture-path identities.

## D1-C: independence and freeze

Before evaluating target Scan scores, publish a dated immutable manifest with tournament/game IDs, chronological selection rule, canonical FENs, source/target disjointness, exclusion lists (PC Blues, all previously scored arenas and reserved fFgE7oED), engine versions, action fingerprints, signatures and SHA-256. No position or game may appear across train, validation and holdout; deduplicate identical FENs globally. Do not choose the test cohort by its Scan scores, Jass winners, or post-hoc signature success. Group resampling by game and, where possible, tournament. An already scored cohort is diagnostic only.

## D1-D: target outcomes and decision gates

Pin Scan version, flags, depth, hardware-independent node accounting where available, and action-score units. Freeze target positions before Scan depth-16 scoring; optionally depth-18 sensitivity on a separately specified subset. Primary analysis: paired difference in mean **best-of-three ordinary regret** for Q+/Q/LCB vs L on identical target positions, with a 95% game-cluster bootstrap interval. Secondary: top-1 regret, Scan-optimum hit rate (ties accepted), top-3 optimum coverage, ranking inversions, fraction of matched pairs, number of independent owning games, and maximum regret. Separate non-ordinary category transitions from ordinary centimen differences; do not coerce wins/losses into numeric scores.

Predeclared engineering stop conditions: abort comparison if target score provenance or action bijection fails; if the matched holdout has fewer than 30 distinct owning games, report exploratory only; if fewer than 100 distinct matched target positions, report underpowered and no efficacy claim. Candidate advancement requires an upper 95% bootstrap bound below zero for paired mean best-of-three regret versus L, no observed adverse category transition, and no catastrophic-error rate increase versus L; if not met, refine on training data only and use a newly frozen test cohort for a fresh confirmatory claim. These thresholds are **design choices**, not results.

## D1-E: Jass integration gate

Only after D1-D, implement a pinned disposable Jass **ordering-only** runner; check every legal action remains searchable and native legality/capture rules are untouched. Compare native vs MTDP at 10k/50k/200k total nodes per arm, with costs included, fresh transposition tables, paired position/game receipts and Scan regret. Advance to selective reductions only with tactical fallback, exact re-search and a justified value bound; never claim theoretical safe pruning from approximate signature agreement. Then perform adequately powered paired games with color/opening swaps and Elo confidence intervals.

## Immediate next executable increment

Implement a **score-blind signature audit** with deterministic JSON output and synthetic unit tests for collision/action mapping, using the existing `signature_ablation.py` and `successor_audit.py` as controls. Validate locally or through CI before any new Scan scoring. Reserve prospective data through the coordination register; do not interfere with the existing fFgE7oED freeze.
