# MTDP real-node equal-compute archive verdict — 15 November 2026

**Status: engineering and retrospective diagnosis complete; prospective
playing-strength claim NOT established.** All 473 frozen targets from five
previously studied arenas were replayed with independent native, unchanged LCB
and metered tie-control Jass searches at **10k, 50k and 200k TOTAL nodes per
position per arm**. The treatment's preliminary search and all root probes
are charged against the same node allowance as its main search.

## Evidence and provenance

- Frozen cohort: `spatial-jass/replication/frozen-cohort.json`, five arenas
  `uG0fGZzB` (25), `l45uk39x` (12), `GYEtKzUg` (55),
  `MtDQWBNR` (33), `CARZrQpl` (348). Positions/identities are
  identical at all three budgets.
- Jass revision: `cfe07fce6385b980553a898e9651d53419589ebc`.
  Disposable pinned C++ builds of first-root and initial-only runner, with
  one thread, full-window depth-one independent probes, exact node caps,
  live legal root catalogue and fresh search tables. Frozen Scan **depth-12
  SOURCE** scores generated the LCB prefixes, not archived native winners
  or Scan target outcomes.
- **Engine accounting gate, all green**:
  [GitHub Actions #43709965786](https://github.com/jfrancoiscollin/dilf/actions/runs/43709965786),
  commit `a4f252d8061c3a93d436d14352b60ac9625a20ed`.
  Artifact `mtdp-metered-archive-technical-gate`,
  artifact ID `14160023070`, ZIP SHA256
  `230563880edb522ee719726a779500429486fe985ebd82274dab04dce47904df`.
  Contains all 15 JSON packets (five arenas × three budgets), receipt by
  position, per-call verification node costs, controlled main Jass decision,
  and native/LCB baseline decisions. Engineering source-only input validator:
  `metered_archive_gate.py`.
- **Separate retrospective Scan-16 quality audit, all green**:
  [GitHub Actions #43716022780](https://github.com/jfrancoiscollin/dilf/actions/runs/43716022780).
  It downloads exactly the *completed, pinned* Jass receipt run above
  instead of searching again; it verifies the frozen Scan reference provenance
  and scores decisions only **after** engine receipts are fixed.
  Quality artifact `mtdp-retrospective-scan16-quality`,
  artifact ID `14162397806`, ZIP SHA256
  `2a64e52794b543c01fcec66965f4ddb4988c6424970e96d58f62a68958c697d7`.
  Reproduce with `python -m research.mtdp.jass_benchmark.metered_archive_quality`.
  These were **previously studied archives**; the Scan-16 comparison is
  strictly diagnostic, not a new independent trial.

## Three-budget totals

| Measure | 10,000 nodes | 50,000 nodes | 200,000 nodes |
|---|---:|---:|---:|
| Paired, metered positions | 473 / 473 | 473 / 473 | 473 / 473 |
| Control final choice equal to native | **467** | **472** | **473** |
| Unchanged LCB final choice equal to native | 457 | 453 | 457 |
| Control final choice equal to LCB | 451 | 452 | 457 |
| Verified intervention requests | 48 | 48 | 48 |
| Mean control verification nodes/position | 185.723 | 185.723 | 185.723 |
| Maximum control verification nodes | 422 | 422 | 422 |
| Verification fraction of total budget | 1.8572% | 0.3714% | 0.0929% |
| All verification calls within 10% hard cap | yes | yes | yes |
| All main/control/reference budgets exactly exhausted | yes | yes | yes |
| Scan-16 optimum hits: control / native / LCB | 134 / 136 / 138 | 154 / 155 / 153 | 146 / 146 / 142 |

The *same* 87,847 verification nodes are used across all 473 target
positions at each budget. There were 97 independently verified
depth-one score ties (48 requiring a different native-order tie winner,
49 with the same winner) and 376 unique maxima, at each budget.
**There were zero verification fallbacks** in this archived population.

### Actual Scan-16 quality differences versus native

Score unit: **centimen**, the reference's action-score field. Ordinary
regret is defined only where the reference's best and chosen outcomes
are both classified `ordinary`; comparison uses **469/473** positions
at each budget. A **positive** control-minus-native regret is worse.

| Budget | Distinct final choices | Control better | Control worse | Average ordinary regret, control minus native |
|---|---:|---:|---:|---:|
| 10k | 6 | 2 | 4 | +0.2516 centimen |
| 50k | 1 | 0 | 1 | +0.0149 centimen |
| 200k | 0 | 0 | 0 | 0 |

At 10k, six choice differences total **+118 centimen** of additional
ordinary regret over 469 comparable positions (four worsenings totalling
132, two improvements totalling 14). Whole-game event-stratified bootstrap
of this descriptive retrospective contrast, 336 eligible game clusters:
95% interval approximately **[-0.0249, +0.6510] centimen**.
At 50k, the **single** divergence, in arena `GYEtKzUg`, chooses
`34-29` rather than native `34-30`: **+7 centimen**
additional regret on that position; mean +7/469. Descriptive whole-game
interval **[0, +0.046875] centimen**. At 200k the decision choices
coincide on all targets and their Scan-16 regret is identically equal.

**Critical mechanistic finding:** all seven final control/native
disagreements across the two smaller budgets occurred with
`intervention=null` (six at 10k and one at 50k). Thus they do **not**
come from a different chosen depth-one tie winner. They occur on
**nonintervention** paths where the verification node debit leaves fewer
nodes for the normal search. This distinction rules out describing those
differences as an improvement introduced by the tie-break itself.

## Scientific decision and next experimental gates

1. **Established:** opt-in full-window probes are truly executable, bounded,
   node-accounted, and significantly cheaper than the former retrospective
   auxiliary approach. Native-order depth-one ties are real, not just
   inferred from unverified fail-soft integers. All 473×3 comparisons meet
   the same total node contract.
2. **Not established:** this does **not** demonstrate that MTDP improves
   Jass search quality, playing strength, Elo, or solves the large Jass–Scan
   performance gap. At 50k the archived evidence mildly favours native,
   but archival reuse prohibits independent significance claims.
3. **Preregistered next step:** retain
   `TOTAL_BUDGET_TIEBREAK_PROTOCOL.md` unchanged and obtain the first
   new eligible independent Lidraughts standard 5+0 arena that satisfies
   its start time, independence, duplicate and two-export checks.
   Freeze the complete target population and file digests **before**
   reading or scoring Scan depth-16 target actions. Analyse the
   predesignated primary 50k ordinary regret contrast with a whole-game
   bootstrap only after the freeze. Empty eligible cohorts must still
   be reported.
4. **Separate exploratory hypothesis (not the preregistered primary):**
   where no tie intervention is possible or warranted, the verification
   tax can be harmful. A future *new* preregistered arm could compare
   early-exit/conditional verification against native and the existing
   tie-control with all remaining nodes reused. Do not silently modify
   the already registered primary arm. The broader MTDP objective should
   also resume equivalence-class/dimensionality-reduction hypotheses
   rather than assume a depth-one tie-break can itself exceed Jass native.

This document reports archived evidence only; it makes no prospective
performance or model-strength claim.
