# Exploratory Scan20/20 stability control — fixed before any depth20 score

The prospective two-arena primary Scan16 results are complete and immutable in
commit ec8c4dfc2b8ddc11de74c1af5d7d0e9d9d581a0b, analysis SHA
3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7.
The cohort's Scan16 outcomes are already known. This is **exploratory horizon
sensitivity on the same cohort**, NOT another independent holdout or retroactive
confirmatory registration. No new signature, source, top-K rule or dimension
parameter is selected. The primary16/16 and Jass50k results remain unchanged.

The sensitivity uses **ALL26 already frozen LCB-full-signature-equal pairs**,
including11 zero-cost/optimal and15 positive-cost Scan16 cases, not just the
worst/disjoint cases. Sources, owners, legal mappings and arena identities are
exactly those in original freeze3fa9a56a3fa60954d5391d7e1b302c07e04f1f04.
Target counts17/9, owner games14/8, no replacement or additional event.
Mask SHA d00e0c3d73a8aafb390899117cd56b402da48a4d2b18953e0c72f261b7819b19.
The JSON plan contains every target/source/owner/legal mapping and method hash.

Only depth changes: source20 and target20 complete successor action references,
same exact Scan3.1 binary/eval/ini, normal rules, one thread, TT18, no book/EGDB.
The pinned Scan HUB code (commit7aae17e7, src/main.cpp new-game handler) executes
G_TT.clear(); the unchanged Python scorer sends new-game BEFORE EACH successor
score. Therefore a smaller subset/order does not introduce shared TT history.
The new20 scanner increases only the transport-idle allowance to120s to avoid
mistaking a long depth iteration for an I/O failure. Search budget remains
fixed depth20; no time or node cutoff replaces depth, and missing exact-depth
scores are failures. Attempt/status files retain technical errors and do not
assert a successful reference until the full catalogue validates.

`two_arena_depth20` requires an exact published plan commit, ancestor of a fresh
research head and descendant of the primary result commit. It re-verifies the
original joint freeze and exact method bytes before any engine/output access.
No CLI depth override. Sensitivity packets have distinct source20_exploratory /
target20_exploratory kinds and primary_source_usable=false, so they cannot enter
Jass source12 ranking or replace the registered16/16 packets. The source and
target references are separately archived with their mask and plan hashes.

Before reporting20, analysis independently reconstructs the original16/16
subset from published raw references and requires exact equality with every
original primary-stratum summary, including bootstrap intervals. Both depths
keep full tied optimum sets, first canonical source maximizer, target-optimal
pick, all/positive-only ordinary costs, category transitions and every case.
Report both arenas and pooled estimates, stable/resolved/new disjoint sets,
paired deltas and same original frozen-owner sampling frames (all31 owners,
including owners with no selected subgroup rows),10000 stratified draws,
seed20261113, fixed percentile indices249/9749. Undefined subgroup ratios remain
explicit with CI=null; no retries/drops. This is finite-reference robustness,
not minimax truth, Elo, new sample size or broad tournament generality.

**221 local foundation tests pass**, including10 new subset/packet/role/depth,
plan-before-engine, cache-reset command, transport-only allowance and
source-tie-vs-disjoint contract tests. Four concurrent D1 aggregate tests also
passed locally with the REAL repository imports (no API substitute); no D1
experiment or code change. No depth20 engine score has yet been computed.
No equivalent depth20 job is already queued or running; existing Actions are
engineering validations of the earlier pipeline. The existing workflow now
runs these tests without starting a new depth20 campaign itself.

After publishing this plan and exact module:

```sh
python -m research.mtdp.jass_benchmark.two_arena_depth20 score \
  --root . --plan-commit FULL_PUBLISHED_PLAN_SHA --role source \
  --adapter ../draught-master --scan ../scan/scan_linux --output /tmp/source20-UNIQUE.json
python -m research.mtdp.jass_benchmark.two_arena_depth20 score \
  --root . --plan-commit FULL_PUBLISHED_PLAN_SHA --role target \
  --adapter ../draught-master --scan ../scan/scan_linux --output /tmp/target20-UNIQUE.json
python -m research.mtdp.jass_benchmark.two_arena_depth20 analyze \
  --root . --plan-commit FULL_PUBLISHED_PLAN_SHA --source /tmp/source20-UNIQUE.json \
  --target /tmp/target20-UNIQUE.json --output /tmp/depth20-sensitivity-UNIQUE.json
```

Next: run both pinned20 packets only after the live plan check; retain all26
cases, report either stability or reversals, reproduce analysis7/61 and archive
raw references/results. Never retune on20 to claim a fresh independent success.
All four whole events and now-scored FENs stay reserved/excluded from D1 fitting,
validation, thresholds, signatures/refinement/top-K/dimension selection.
No paid resource or develop merge/deployment. Jeff's PC is not needed for the
available remote resources; report if the actual computation cannot finish there.
