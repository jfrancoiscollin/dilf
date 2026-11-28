# Eighth study — prospective multi-event replication of spatial matching

Status: **preregistered, not executed**. This document freezes analysis choices before identifying new events or reading new Scan scores. It does not claim Jass playing-strength gains.

## Question and hypotheses

The seventh independent 5+0 holdout matched 78/6,146 eligible targets using exact legal actions (L), 21 using mover-man occupancy (LM), 32 using mover-man count plus immediate blocker squares (LCB), and 21 using mover-man and blocker squares (LMB). On the 21 L/LM common targets, top-three regret was unchanged; only one source changed. LCB recovered 11 targets beyond LMB. This study asks whether those coverage and conditional-quality patterns replicate across *multiple new tournaments* and whether source changes alter transfer quality.

Primary descriptive estimand: per-event fraction of eligible targets matched by each arm, using the same eligible population. Primary paired quality estimand: mean (LCB minus L) best-of-three target regret on their common matched targets, weighted equally by target (not by number of candidate moves). A paired analysis restricted to cases where the selected source differs is **secondary and selection-conditioned**; its denominator and game count must be shown. Null hypothesis: mean paired regret difference equals zero. Report absolute and relative coverage loss against L and the catastrophic-regret tail (>= 0.5 man), without substituting unmatched-target zeroes.

## Fixed arms and eligibility

Reuse the frozen seventh-study implementation and canonical move identities, including full capture path, captures and promotion information. L = side to move plus exact legal action set; LM = L plus exact mover-man occupied squares; LCB = L plus mover-man count and exact immediate opponent blocker squares; LMB = L plus exact mover-man and blocker squares. Do not modify key definitions or source tie-breakers after the first event freeze. Analyze the same FMJD-verified no-capture, mover-men-only quiet stratum for all arms. Report full replay, eligible, excluded, unique and matched denominators separately.

## Prospective event sampling and freeze

Select the **next three eligible independent FMJD 5+0 tournaments in chronological order after the seventh event**, subject to availability of public PDN and legal replay. Eligibility must be determined using only event metadata, PDN, canonical FENs and legal-move signatures, before Scan scores. Exclude all tournaments and game IDs used in cohorts 1–7, duplicate PDN hashes and overlapping canonical source/target FENs. Archive the chronological candidate log, including exclusions and reasons; if fewer than three qualify, stop and report the number found rather than backfill from an outcome-selected event. No extra event may be added based on observed scores.

Before *any* new scoring, commit a per-event freeze containing source URL, retrieval time, PDN SHA-256, game identifiers, source/target deterministic selection, exact excluded overlaps, code and adapter revisions, Scan 3.1 executable digest, scoring configuration and fixed seed **20261112**. Lock all three freezes before inspecting any of their Scan outcomes. No overlap between source and target games within or across events. If the available corpus cannot satisfy this, stop without silently relaxing the rule.

## Scoring and reproducibility

Reuse depth 12 for all legal successors of source FENs and depth 16 for all legal successors of target FENs, Scan 3.1 with one thread, cold TT, no book and no tablebases. Record complete successor sets, raw scores and categories, commands, binaries, SHA-256 digests and exact deterministic tie-breaks. Score once per distinct (FEN, depth, configuration), and reuse only after hash verification. Require exact legal move-set equivalence from the FMJD adapter; reject duplicate canonical action keys and ambiguous capture mapping. Any missing score, drift in digest or rule disagreement halts the affected event before aggregation.

## Analysis locked before outcomes

For each event and pooled results, report matched/eligible and matched/all replayed for all four arms, optimum coverage of top one and top three, best-of-three mean/median/max regret, number of regrets >= 0.5 man, and categorical transitions. Report separately: (1) all L/LCB common matched targets, (2) common targets where selected source differs, (3) all L/LM common targets, (4) LCB/LMB common targets. Always provide target and owning-game counts; show source-change rates explicitly. The changed-source subset is exploratory for causal interpretation even though the calculation is preregistered.

For confidence intervals, use **10,000 hierarchical bootstrap replicates with seed 20261112**, resampling tournaments, then whole target games within selected tournaments; never resample individual positions as independent units. With only three events, intervals may be unstable: additionally show each event separately, the range of event estimates and a leave-one-event-out sensitivity. If fewer than two events or fewer than two owning games in a contrast, report its interval as non-estimable rather than presenting spurious precision. No significance claim based solely on a pooled conditional mean across different matched populations.

## Tests and interpretation boundaries

Before accepting results, run existing MTDP and DILF tests, the downstream FMJD compatibility workflow and PC Blues replay, plus negative cases for swapped turn, changed man count, changed blocker square, changed mover square, duplicated canonical moves, malformed capture paths, overlapping cohorts, altered hashes and incomplete successor scores. Archive a deterministic machine-readable summary and verify repeated analysis byte-for-byte.

A coverage/quality improvement is evidence only for **offline transfer of Scan-evaluated candidate information**, not improved Jass playing strength. A separately frozen, node-matched Jass comparison is required before claiming engine benefit. No merge to develop, deployment or paid compute is authorized.
