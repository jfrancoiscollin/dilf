# MTDP — Preregistered size-matched offline top-three control (2026-11-12)

Status: **protocol only**. No new analysis result is claimed by this document.

## Frozen inputs and population

Use the three immutable Jass cohorts `Z3s40c6H` (28 targets), `iPQl7g7q` (75) and `0gB7ETSW` (17), with their manifests, Scan depth-12 references, Scan depth-16 references and SHA-256 provenance from `jass_benchmark/scan-depth16/provenance.json`. Retain all 120 target FENs, including targets with fewer than three legal actions. Do not refit signatures, select new targets or use target Scan scores to construct candidate lists. Reject any mismatched digest, missing legal action, duplicate canonical action, or inconsistent source/target legal catalogue.

## Candidate construction, before consulting target scores

For each frozen source-target pair, define `k=min(3, number of legal target actions)`. Both candidate lists must contain exactly `k` distinct legal actions. Canonical control: sort the target legal actions lexicographically by their frozen `jass_key` (bytewise ascending), select the first `k`. MTDP transfer: rank the **source** legal actions by the source Scan score (descending), break equal scores by the same `jass_key` ordering, and select the first `k`. Only use the frozen one-to-one DILF/Jass mapping; fail closed if a source action cannot be matched unambiguously to a target action. Record ties, legal action counts, both ordered keys and both lists' overlaps. The source Scan depth is matched to the evaluation depth (12 or 16); never use target Scan scores for selection. Consequently this is a *depth-matched offline information test*, not a deployable depth-independent MTDP policy.

## Outcomes and estimands

At each depth and for each target: (1) whether the candidate set contains any target-optimal action (including ties), (2) the regret in centimen of the **best target-scored candidate** versus the target optimum, and (3) the number of distinct legal actions and candidate-set overlap. The best-of-list regret is an oracle upper bound on shortlist quality; it is **not** a Jass move-selection result. Compare transfer minus canonical regret (negative favors transfer) and transfer minus canonical optimal coverage (positive favors transfer), paired by target. Report per cohort first, then a descriptive pooled estimate. Report category changes (ordinary / winning / losing or other Scan sentinels) separately; never subtract incompatible score categories.

## Statistical protocol

For each cohort, report counts, denominators, mean/median ordinary regret, coverage, paired differences, and 95% game-cluster bootstrap intervals (10,000 resamples, seed 20261112). Assign positions shared by several games to the lexicographically first frozen target game, as in `depth_sensitivity.py`; resample games with replacement, preserving all their target positions. A pooled interval must stratify by event and is descriptive only. Also report a paired 2×2 coverage contingency table and exact discordant counts. No significance threshold or model tuning is permitted after inspecting results.

## Validation and stopping conditions

Add deterministic tests for k<3, equal source scores, different input order, duplicate Jass keys, missing source/target action, equal candidate lists, and categorical scores. Require two byte-identical executions of the comparison and passing existing MTDP and downstream FMJD CI before marking the study validated. Do not trigger paid runners. Stop and report a protocol violation instead of silently dropping a target. Preserve the previous 12/16 sensitivity reports unchanged.

## Interpretation boundary

The offline control asks whether a Scan-informed source shortlist contains more target-relevant information than a size-matched canonical shortlist. It does not demonstrate improved Jass search, nor generalize to unobserved tournaments. Any subsequent Jass experiment needs a separate preregistered, genuinely out-of-sample cohort and matched node budgets.
