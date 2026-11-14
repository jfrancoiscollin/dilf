# Preregistered geometric-signature ablation — sixth held-out arena

Status: **protocol only**. No sixth event selected, no scores computed. Registered after fifth-cohort results, before retrieval of any sixth-event targets.

## Question and fixed comparison

Does the quiet-man geometric signature add discriminative information beyond **exact equality of the legal-action catalogue**? The fifth cohort shows shortlist signal without demonstrated Jass search improvement. This experiment concerns offline candidate selection only, not engine strength.

Use existing deterministic FMJD state, canonical legal-action identities and quiet-man signature functions without tuning thresholds. Compare two source-to-target matching arms on the **same frozen targets**:
- **L (legal-only):** exact legal-action catalogue equality.
- **LG (legal + geometry):** exact legal-action catalogue equality AND exact existing quiet-man signature equality.

Source pool: the 26 archived PC Blues games, with validated FMJD replay and exact legal catalogues. Do not modify source pool or use any held-out target as a source. For every target, enumerate all eligible PC Blues source states; report both arm match counts, not just selected matches. Require quiet nonterminal positions with at least two legal actions; freeze any exceptions and counts before evaluation.

## Holdout and freeze

Select the first finished public standard 10x10 5+0 Lidraughts arena from the API's finished list retrieved **after this protocol commit**, excluding events used in the first five cohorts. If unavailable, document retrieval and stop; do not substitute a hand-picked event. Save event ID, retrieval timestamp, original PDN bytes and SHA-256, provenance and replay rejection reasons. Validate all games via the FMJD adapter, deduplicate by canonical FEN, and exclude any positions overlapping previous target manifests or PC Blues. Publish a manifest with sorted FEN, owning game IDs, legal keys, quiet signature, matching source IDs for both arms, selection ties and SHA-256 before Scan scoring. Verify the manifest is byte-identical in two runs. No target-score-dependent exclusions.

## Frozen selection and scoring

For each target and arm, select the lexicographically first matching source by stable (game ID, ply, FEN) tuple; **do not** choose a source using target Scan scores. Score all legal successors of each selected source at Scan 3.1 depth 12 (one thread, cold TT, no book/tablebases), rank descending, break equal scores by canonical action key, and transfer top k=min(3, number of legal moves). Score **all** target legal successors independently at Scan 3.1 depth 16 under the same engine restrictions. Require source/target action-key bijection and complete score receipts; stop on missing keys, ambiguous captures, inconsistent categories or provenance failures. Pin binary hashes and full CLI/configuration in the receipts.

## Estimands and reporting

Primary descriptive endpoint: fraction of **all frozen eligible targets** matched by LG versus L; LG must be a subset of L by construction. Report exact numerator/denominator, number of sources per target and compression LG/L; also report conditional coverage among L-matched targets. These quantify selectivity, not strategic quality.

Secondary: for each arm separately, target-optimum coverage by the transferred top-3 and regret of its best target-scored candidate (ordinary-score positions only). Report conditional metrics over arm-matched targets, and a **paired comparison restricted to targets matched by both arms**; do not interpret the different conditional cohorts as a causal gain. For unmatched targets report missingness explicitly, not zero regret. Separate categorical scores and count transitions. Report top-1 and k=3, >=0.5-man regret, maximum regret and source-target optimum-set disjointness.

Use 10,000 whole-owning-game cluster bootstrap resamples, fixed seed 20261112, 95% percentile intervals for paired contrasts; report counts of owning games and sensitivity excluding multi-game targets. No p-value fishing, thresholds or matching rule changes after viewing outcomes. If zero paired matches or no ordinary scores, report endpoint unestimable and stop.

## Reproducibility gate

Archive source/target JSON receipts, SHA-256 manifests, exact scripts/commands, independent duplicate executions (byte-identical except documented runtime fields), FMJD PC Blues replay evidence, and CI test links. Add negative tests for legal-catalogue mismatch, same catalogue/different geometry, ambiguous canonical captures, empty matching arm, stable tie-breaking and cross-cohort leakage. No Jass strength claim follows from this offline ablation. Do not merge or use paid resources.
