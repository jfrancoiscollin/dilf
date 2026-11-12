# MTDP/Jass — preregistration: seed root ordering at iteration one only

Status: **preregistered design, NOT implemented, NOT executed** (2026-11-12).
This is a new experiment following the independent 28-target benchmark and the
75-target replication. It does not reinterpret those already observed outcomes.

## Rationale and falsifiable hypothesis

The earlier benchmark forced a top-three prefix at each root iteration.
The second independent cohort (75 targets) did not consistently improve
Scan-depth-12 regret and at 200,000 nodes the mean quality favored both
controls. An initial-only prefix may preserve Jass's adaptive root ordering
at later iterations, avoiding persistent forcing costs.

Primary hypothesis: at 200,000 nodes, initial-only MTDP transfer has lower
paired Scan-depth-12 regret than initial-only canonical top-three control.
Null: no improvement. Secondary budgets: 10,000 and 50,000 nodes.

## Mechanistic gate — before any evaluation

1. In the pinned Jass checkout, identify the root iterative-deepening loop,
   root move-order state and transposition-table interactions.
2. Implement a mode that applies the requested permutation **only for the
   first completed root iteration**. On every later iteration, restore the
   exact native adaptive ordering mechanism (including native previous-PV,
   TT and history heuristics). Do not merely stop reapplying the prefix if
   the first iteration leaves an unacknowledged persistent root order.
3. Log iteration index, root legal move keys, visited order, completed-depth
   flag, node count, TT reset and best move for each arm. The trace must
   demonstrate native-order recovery after iteration one. If native order
   cannot be defined unambiguously, stop and report a mechanistic failure.
4. Confirm equal legal move sets and identical root move coverage in all
   three arms, including multi-capture keys and promotions. Reject ambiguous
   DILF/Jass mappings. Verify exact consumed-node budgets and fresh TT for
   every arm. Add negative tests for mismatched node receipts.

## Design and data leakage prevention

Freeze a **third** event's PDN SHA-256 and target manifest before computing
Scan target scores. Exclude PC Blues, both existing independent tournament
cohorts, earlier holdouts, and all duplicate target FENs. Source selection:
deterministic PC Blues match on the original MTDP signature and identical
canonical legal set, without consulting target scores; reject mapping
ambiguity instead of searching alternative sources.

Three arms: native Jass; transferred source Scan-depth-12 top three only
at first root iteration; canonical top three only at first root iteration.
Use the same pinned Jass build, evaluation, one thread, fresh 1 MiB TT,
depth ceiling 64, fixed seeds and 10k/50k/200k node budgets. Deterministically
rotate arm execution order. Preserve all legal actions after the prefix.

## Outcomes and analysis

Primary outcome: target Scan-depth-12 ordinary-score regret of the
**actually selected Jass move**, transfer minus canonical, at 200k nodes.
Negative favors transfer. Report paired position mean/median, paired
game-level means and a cluster bootstrap confidence interval resampling
target games (fixed seed, e.g. 20261112; 10,000 resamples). Treat positions
sharing source games as dependent in a sensitivity analysis. Categorical
win/loss scores must not be subtracted as ordinary men.

Secondary: comparison with native; 10k and 50k budgets; Scan optimum
coverage; chosen-move changes; fully completed depth; nodes to common
completed depth; wall time only descriptive. Report candidate denominator,
coverage, exclusions, disjoint optimal sets, and all raw paired receipts.
Do not select or revise thresholds after inspecting target scores.

## Stop conditions and outputs

Stop without claiming a scientific result if the first-iteration-only
mechanism is not verified, if later native adaptive ordering is not restored,
if any legal mapping is ambiguous, if any node receipt differs from the
budget, or if corpus independence / pinned versions cannot be demonstrated.
No paid resources or local PC needed until a measured workload requires them.

Artifacts: frozen manifest and SHA-256 provenance, Jass patch and tests,
iteration-level root traces, Scan scores, paired receipts, game-clustered
summary, reproducibility commands, and a result report clearly separating
mechanistic validation from playing-quality evidence.

Prior evidence: [second replication](jass_benchmark/replication-iPQl7g7q/RESULTS_2026-11-12.md),
[original protocol](JASS_MOVE_ORDERING_PROTOCOL.md).
