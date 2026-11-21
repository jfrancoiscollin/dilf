# Preregistered fifth-cohort Jass benchmark

The [fourth-cohort experiment](fourth-3onq5G6G/RESULTS_2026-11-12.md)
found that Scan-informed source lists contained better candidates than
equal-size canonical lists under the target reference. This benchmark
tests whether the existing first-iteration-only Jass integration
improves the move actually chosen under an equal search budget. The
earlier [mechanistic gate](../JASS_INITIAL_ONLY_PROTOCOL.md) remains in
force. No event or target has been inspected for this benchmark at
preregistration.

## Holdout and freeze

Use the first completed standard 10×10 5+0 arena in the public Lidraughts
tournament API's finished list at first successful retrieval after
preregistration, excluding events already used for MTDP. Save the
retrieval time and chosen event metadata. If none qualifies, record
that fact and pause selection. Use the documented public game export,
record its byte hash and rights provenance, and publish derived
positions and audit counts. Apply the fourth-cohort FMJD replay,
deduplication, exact quiet-signature and legal-catalogue rules, including
eligible forced moves. Exclude PC Blues and all previously used PDNs
and check explicit non-overlap with the four earlier target manifests.
Freeze all eligible targets and source choices, and publish the hashes
before scoring. No sampling or score-dependent exclusions.

## Search and reference

- Arms: native Jass, first-iteration-only canonical list, and
  first-iteration-only transferred list. Use `k = min(3, legal count)`
  for both lists. Canonical sorts frozen Jass keys by UTF-8 bytes.
  Transfer ranks source actions by Scan 3.1 successor depth 12
  descending, using the same key order for ties. All remaining legal
  moves stay in the native suffix. No target score may enter an arm.
- Use Jass `cfe07fce6385b980553a898e9651d53419589ebc` with the existing
  initial-only patch, handcrafted evaluation, one thread, a fresh
  1 MiB TT, depth ceiling 64 and no endgame tablebases. Search budgets
  are exactly 10,000, 50,000 and 200,000 nodes for every arm and target.
  Rotate arms with the existing manifest seed. Verify full depth-one
  root coverage, native adaptive order thereafter and every node receipt.
- Judge all legal target successors with pinned Scan 3.1 at depth 16,
  one thread and a cold TT, no book or tablebases. The target catalogue
  is used exclusively for evaluation of returned moves. Source ranking
  and target reference have separate receipts. Report search wall
  times descriptively. Source Scan computation is offline setup;
  the matched budgets cover Jass search nodes. No end-to-end speed
  claim follows from those budgets.

## Primary and secondary outcomes

Primary outcome: paired ordinary-score regret of the move actually
selected at 200,000 nodes, transfer minus canonical. Negative favors
transfer. Report mean and median, and a 95% percentile bootstrap
interval, resampling 10,000 whole target-game clusters with seed
20261112. Assign shared positions to their first game ID
lexicographically; repeat after dropping multi-game targets as a
sensitivity analysis. Report the number of positions, owning games,
ordinary pairs and categorical transitions. Categorical Scan scores
are counted separately. Compare against native and repeat at 10k and
50k as secondary outcomes; report optimal move coverage, changed
moves and completed depth. Report the oracle shortlist comparison
separately as a check of the source signal.

An interval spanning zero is inconclusive about a nonzero gain. A
within-cohort gain in regret is a fixed-budget reference result.
A general claim of stronger play needs independent replication.
Stop on provenance or mapping errors, incomplete Scan scores,
nonmatching node receipts or failed trace checks. A verified
technical failure can be corrected with the frozen inputs and
protocol, then rerun. Keep all frozen targets. Reproduce references,
trace and move choices and run the available DILF/Jass validations.
No paid resource is part of this design.
