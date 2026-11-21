# Equal-compute MTDP control: implementation handoff (2026-11-14)

This note continues [TOTAL_BUDGET_TIEBREAK_PROTOCOL.md](TOTAL_BUDGET_TIEBREAK_PROTOCOL.md).
The objective is a **prospective, outcome-blind** comparison at the same total
node budget, not another retrospective replay with uncharged verification.

## Implemented in PR #43

- `research/mtdp/jass_benchmark/total_budget.py` validates the per-position
  10% verification cap, issued probe limits, independently measured receipts
  and main-search conservation.
- `research/mtdp/jass_benchmark/metered_control.py` now composes these
  safeguards with the exact-score, live-native-order tie selector. It accepts
  only an engine-derived preliminary receipt, first-action probe receipts,
  and a fresh-table main-search receipt. A preliminary or probe failure,
  an incomplete root action, a bound-only score, inconsistent maxima or
  exhausted verification allowance results in **no forced intervention**.
  Every measured preliminary/probe node is still charged. The main search
  receives all remaining nodes, also on fallback. A depth-ceiling exception
  is explicitly excluded from the complete-budget comparison.
- `research/mtdp/tests/test_metered_control.py` has dedicated
  simulated-engine cases, including negative receipts and a preliminary
  search that stops without a usable winner.
- The module is a **callback contract only**. It is *not connected to the
  pinned C++ Jass engine*; local tests cannot establish an engine benchmark.

New GitHub workflows for the latest commit must be checked before recording
a CI result. Do not transplant the full-budget historical
`spatial_prospective.select` into this contract: it consumes far more nodes
than the registered 10% verification allowance.

## Next concrete step (engine gate)

1. Add an opt-in disposable research runner mode to execute exactly the first
   depth-one root action with a *hard* per-call node limit and a fresh
   transposition table, reporting the actual charged nodes, move, completion,
   score, and fixed full-window bounds. A normal search to 64 plies with an
   inspected depth-one trace is **not** a cheap probe.
2. Adapt the first depth-one LCB search to the same hard limit. Supply
   genuine native legal order from **current** move generation and validate
   legal key uniqueness. Never use archived native winners or target Scan
   scores as control inputs.
3. Integrate `metered_control.execute` with explicit engine callbacks.
   Enforce that the main replay has a fresh table, unchanged LCB visit
   order, and a forced winner only when independently exact ties justify it.
   Keep native and LCB baselines unchanged.
4. Run C++ unit/integration tests on exact ties, bound-only ties, cap
   exhaustion, erroneous node receipts, illegal actions and depth-ceiling
   paths; then verify both GitHub workflows.
5. First use the archived 473 positions for a **technical gate only**,
   comparing depth-one probe scores and accounting without new inferential
   claims. Freeze the independent prospective tournament and hashes
   according to the existing protocol **before** Scan/Jass scoring. Report
   per-target fallbacks and all spent nodes. Primary endpoint:
   Scan-16 ordinary-regret difference control minus native at 50k total
   nodes, with a whole-game interval.

## Current evidence boundary

Retrospective tie intervention: 473/473 native decisions reproduced at the
three archived budgets, **with additional compute**. Historical verification
cost: 50.95 million nodes. At a 10% cap, the depth-one historical lower
bound alone exceeds the cap on 65/473 targets at 10k; at 50k and 200k,
depth-one cost alone is inconclusive. There is no successful prospective
equal-compute or strength result yet.

## 15 November update — opt-in Jass first-root integration

- A new research-only patch `jass_preflight/first-root-action.patch` adds
  `SearchLimits::research_first_root_action_only` to the **pinned** Jass
  `cfe07fce`. Its default is `false`; production code paths are unaffected.
  It rejects non-depth-one, multi-thread or non-exact-node invocations, and
  stops at the first root action. Root catalogue and true search accounting
  are retained in the existing `SearchDecisionTrace`.
- `jass_preflight/metered_probe.cpp` compiles as the isolated
  `mtdp_jass_metered_probe` executable. Input is
  `preliminary|probe FEN hard_node_cap [ordered_root_keys]`; one call builds
  a **fresh** transposition table and emits `mtdp-probe-v1` TSV including
  issued cap, measured nodes, visited and legal root actions, exactness bound,
  full window and live native move order. In probe mode, exactly the first
  requested legal action is visited; it never reads archived native winners.
- GitHub Actions
  [first executable smoke](https://github.com/jfrancoiscollin/dilf/actions/runs/43693357113)
  passed patch application, the native C++ build, the complete pinned Jass
  CTest suite and real depth-one searches. On the standard starting position
  the 200k-node-limit preliminary depth-one search used **30 nodes** to visit
  nine legal actions, and a one-action probe used **6 nodes**. Those are
  **fixture diagnostics**, not a cohort estimate or strength result.
- The strict Python adapter `jass_benchmark/metered_probe_adapter.py`
  verifies the exact TSV receipt schema, legal order, root count, limit,
  completion, full-window bound, and proposed action. A first parser
  integration run exposed the engine's mixed-case enum bound label; this was
  corrected by case-normalizing the label only and adding regression tests.
  The final CI of the fix must be checked before certifying integration.

**Remaining gate:** Connect the actual preliminary/probe callbacks to
`metered_control.execute`, then run a *real* initial-only **main Jass replay**
with the remaining node limit and no reused TT. Verify the nonintervention
baseline plus forced-tie C++ patch on the *same pinned engine revision and
build flags*. Reject any case where the trace, root order, bound, node totals
or completeness differ. This isolated smoke test is not yet the prospective
473-position engineering check, nor a new independent held-out comparison.
