# Seventh independent ablation — mover occupancy versus legal actions

Status: **preregistered only**. No seventh-event tournament, scoring, or Jass run is claimed by this document.

## Motivation and falsifiable question

The sixth held-out comparison found 138 legal-action-only matches among 8,633 eligible targets, versus 39 when a quiet-man geometric signature was additionally required. On the 39 shared targets, best-of-three regret was identical. This motivates a new, independently frozen comparison testing whether *the mover's exact occupied squares* explain transfer quality beyond legal actions, without using a complete position key.

Primary question: among targets matched by both arms, does the stricter key improve depth-16 best-of-three regret relative to legal actions alone? Null hypothesis: the paired game-clustered mean regret difference is zero. Secondary outcomes: match coverage, top-one regret, optimal-move coverage, and catastrophic transfers (regret >= 0.5 man or category transition).

## Representations (fixed before sampling)

- **L**: side to move and exact set of legal actions, including full capture paths, captured squares and promotion flags.
- **LM**: L plus the exact occupied squares of all men of the side to move, and their type (men versus kings); reject any state with a mover king from the *primary quiet-men stratum*, and report the excluded stratum separately. This adds mover occupancy only; it does **not** add exact opponent occupancy or an outcome-dependent filter.
- **LMB** (secondary mechanistic control): LM plus the exact opponent-occupied squares that block the mover's immediate non-capturing forward diagonals. Define blockers solely from board occupancy and side to move; never consult Scan or the target score.

Restrict primary analyses to FMJD-verified states with mover men only and no available capture, as determined by the legal move generator. Record full-cohort coverage separately so exclusions cannot masquerade as success.

## Freeze and independent event

Select the next eligible FMJD 5+0 tournament chronologically after the sixth event, excluding all previously used tournament IDs, PDN digests and game IDs. Before scoring, commit a freeze manifest containing source URL, download timestamp, SHA-256 of PDN, pinned draught-master revision, adapter revision, Scan binary SHA-256, game IDs, deterministic source/target selection and seed. Check for canonical-FEN overlap against previous source and target cohorts; quarantine overlaps and report counts. If no independent event qualifies, stop and report that fact rather than recycle a cohort.

The source selection and tie-breaking rule must be fixed using *only* signatures and game metadata, not engine evaluations. Use the same source for all arms when keys permit; explicitly distinguish conditional-on-match, common-target paired and all-eligible coverage estimands. Do not assign zero regret to unmatched targets.

## Scoring and analysis

Pin Scan 3.1, single thread, cold transposition table, no opening book or tablebases. Score every legal source successor at depth 12 and every legal target successor at depth 16. Preserve raw outputs, exact score categories, engine commands, per-position provenance and digests. Select top three source moves with a deterministic canonical tie-breaker; evaluate their target regret against the full target optimum set, allowing ties.

For the paired primary endpoint use targets matched by L and LM, with identical source-selection policy and game-clustered bootstrap (10,000 resamples, fixed seed 20261112). Report point estimates, 95% intervals, denominator and effective game clusters. Report LM-versus-L coverage loss on *all eligible* targets, plus LMB as a clearly secondary analysis. If no paired targets, report non-estimability. Never compare unmatched conditional means as if randomized.

## Validation and stopping conditions

Before accepting scores, verify all PDN and engine digests, every FMJD move mapping (reject ambiguous capture paths), deterministic signatures and selection, source/target disjointness, no forbidden historical cohort overlap, exact node/depth settings, and full legal successor coverage. Add negative tests for altered digests, duplicate action keys, swapped turn, missing successor scores, overlapping games and malformed category transitions. Recompute aggregate metrics from archived raw data and compare byte-for-byte where deterministic.

Stop if provenance fails, if the FMJD adapter disagrees on a legal move, if a signature maps non-equivalent legal sets, or if the scoring configuration drifts. No deployment, merge to develop, or paid compute is authorized.

## Interpretation boundary

Even a positive result would demonstrate transfer of Scan-evaluated candidate information, **not** improved playing strength of Jass. A separate node-matched Jass experiment and independent replication remain necessary.
