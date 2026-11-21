# D1 — Preregistration gate for independent top-K transfer (v1)

Status: **protocol only; no cohort enrolled, no scores obtained, no Jass gain**.

## Cohort admission (before engine scores)

1. Pin the FMJD rules/engine version and immutable source game files, SHA-256 each raw file and canonical position manifest. Preserve original game and ply order, game/tournament identifiers, side to move, legal-action identities and full provenance.
2. Reject all games, trajectories and position aliases associated with reserved prospective events fFgE7oED, P1RUlfJc, s7ahYqL4 and D9PF2OSW. A FEN-only exclusion is insufficient: match historical raw serialization, canonical parsed board state and complete game trajectories. Unknown provenance is **quarantine**, not admissible.
3. Reject duplicate positions across train/test and any shared game; split by **whole game**, and where possible hold out entire tournaments. Freeze split, signature definitions, exact tactical fallback, transfer policy, hyperparameters and manifest hashes **before** any Scan/Jass reference scores are consulted.
4. Report all exclusions, collisions, missing legal-action mappings, group counts and sampling dates. Reusing PC Blues 26 games, 61 known pairs, or an existing scored set is a retrospective diagnostic, **not** independent confirmation.

## Score-blind baselines and eligibility

Compare legal-move signature L, LCB, progressive quiet-structure signatures, legal enumeration order and fixed-seed random order. A signature match does not imply matching legal moves, best move, successor or minimax value. Only transfer a ranking when the full legal-action identities map bijectively; otherwise abstain and use exact tactical fallback. Every proposed ordering must contain **all** legal moves exactly once. Capture/forced tactical positions require exact fallback and are counted in denominator for coverage, not silently removed.

## Primary outcomes and uncertainty

Report out-of-sample top-1 exact-optimal membership, tie-robust recall@3 lower and upper bounds, first-action regret in the reference engine's *documented raw units* (centimen only after calibration), WDL transitions if calibrated, rank concordance, severe tactical errors, transfer validity/abstention, compression and collisions. Compare paired differences against L, LCB, legal order and fixed-seed random. Cluster bootstrap **by game**, with tournament holdout separately; show game counts, effective game count, concentration and 95% intervals. Report coverage and quality jointly: abstention must not create selective reporting.

## Prospective go/no-go rules (fixed before scoring)

- **No-go** if any leakage, invalid legal-action mapping, incomplete provenance, reference-score tuning on test, or missing pre-score hashes.
- **No-go** for Jass integration if test tie-robust recall@3 lower-bound paired difference versus the strongest prespecified baseline has a 95% cluster-bootstrap lower confidence bound below -0.01, or if any reproducible forced tactical blunder escapes exact fallback. This is a conservative noninferiority *screen*, not proof of minimax equivalence.
- **No-go** if the effective number of independent games is below 30 or the largest game contributes over 10% of primary positions; collect more independent games, do not claim success from bootstrap precision alone.
- **Go only to ordering-only shadow experiment** if the above gates pass, at least 5% of eligible decisions have a transferable nontrivial signature and there is measurable compression beyond L/LCB. Keep all legal moves. Compare pinned disposable Jass native versus ordering-only at 10k/50k/200k **total charged nodes**, including signature, lookup and fallback costs; fixed seeds, paired positions, full budget accounting. No pruning/selectivity without separate tactical verification and replicated equal-budget evidence.

Thresholds above are proposed preregistered decision gates, not measured findings. Do not retroactively label any already-scored sample as a new holdout.
