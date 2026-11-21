# Exploratory Scan20/20 horizon stability: same26 frozen pairs

**The finite-reference geometry disagreement persists at Scan20:**12/26 source
and target optimum sets are disjoint, including9 pairs already disjoint at16.
The mean ordinary transfer cost is15.5769 raw Scan units, median1.5, max162;
12 first source maximizers are target-optimal,14 have positive cost. Two pick
failures arise from source ties despite intersecting optimum sets. All26 costs
are ordinary/ordinary; no categorical/missing case was turned into zero.

This is **exploratory sensitivity on the already scored cohort**, not a new
independent holdout. The original prospective Scan16 results (14 disjoint,
mean28.5769/max260) and all Jass primary results are unchanged. Neither finite
reference establishes minimax truth, Elo or a general population failure rate.

## Fixed method and chronology

Plan **0a7b0e8cda8da5985298b500f7f9b2a276379fe5** was published and live-checked
BEFORE both20 computations. It fixes all26 original LCB-full-signature-equal
pairs, including11 zero-cost Scan16 cases, source positions/legal mappings/
ownership unchanged. Mask SHA d00e0c3d73a8aafb390899117cd56b402da48a4d2b18953e0c72f261b7819b19.
Parent actual freeze3fa9a56; primary resultsec8c4df. Same Scan3.1 binary/eval/ini,
one thread, TT18, no book/EGDB; matched source20/target20 successor depths.
Each successor starts new-game (G_TT.clear() in pinned main.cpp); search.cpp's
Search_Global::init also calls sort_clear(). No shared search-order/TT history
from a larger16-position batch is relied upon. Transport allowance120s affects
only detection of I/O failure, never the exact-depth search budget.

Source20:26 positions/263 action scores, started03:40:12UTC, completed03:44:47.
Target20:26/263, started03:41:02UTC, completed03:45:56. Both completed without
transport/search failure and passed complete legal-action/reference validation.
Packets are expressly exploratory and primary_source_usable=false; no20 score
entered Jass source12 ranking. No new Jass search or target case was selected.
Source *positions* stay fixed; their deterministic optimal action is recomputed
at20 and may change. Thus matched16/16 vs20/20 differences combine source-action
changes and target-reference changes; they are not a causal gain of a new policy.

## Complete fixed-population comparison

| Arena | Pairs / owner games | Disjoint16 →20 | Optimal first picks16 →20 | Mean cost16 →20 | Median16 →20 | Max16 →20 |
|---|---:|---:|---:|---:|---:|---:|
|s7ahYqL4|17/14|10→10|6→6|33.1765→14.2353|2→2|260→162|
|D9PF2OSW|9/8|4→2|5→6|19.8889→18.1111|0→0|146→145|
|all|26/22|14→12|11→12|28.5769→15.5769|1→1.5|260→162|

The26 pairs/22 owner games remain identical. At20, sum costs405,14 positive
costs with conditional mean28.9286/median6/max162. Across depths:9 stable
disjoint pairs,5 resolved disjoint cases,3 new disjoint cases,9 stable
intersections. Therefore a count changing14→12 hides8 changed case statuses;
no resolved or zero case is omitted. Every tied optimum set and score/case
transition is retained in the result JSON.

The original31 frozen-owner sampling frame, including owners without a selected
stratum row, remains fixed. Whole-game bootstrap is paired and stratified by
these two named arenas,10000 draws, seed20261113, ranks249/9749. At20, mean-cost
interval[2.6786,31.8889], disjoint fraction12/26 interval[0.28,0.65217]. Paired
ordinary cost20−16 mean-13, interval[-30.32,1.08]; disjoint-rate difference-2/26,
interval[-0.27778,0.13043]. No undefined draws. Intervals describe within-sample
game variation, not new tournament generality; their inclusion of zero is not
an adaptive go/no-go result. Integer units equal0.01 HUB, NOT fixed material pawn.

## Same concrete counterexample at both references

The previously largest case, s7ahYqL4 frozen owner game145, remains disjoint and
is also the20 maximum. Source/target mover geometry and legal catalogue remain
identical, with opponent placement different. The first source maximizer changes
from17-21 at16 to5-10 at20. Target optimum remains20-25: at20 it scores+17,
while transferred5-10 scores-145, cost162 raw units. At16 the transferred17-21
scored-247 against target+13, cost260. This shows robust finite disagreement
for the same state pair while its numerical cost/source argmax depend on depth;
it does not establish a true minimax counterexample.

## Verification and retained artifacts

Both analyses, independent processes7/61, are byte-identical SHA256
**6076aba12d4e3427b33c6bc9c6ee101c57df1a99109b3638339c1e3570709f90**.
A separate direct computation from raw16/20 action vectors verifies26/12/12,
sum405/max162, all4 transitions, and independently recomputes the20 mean/rate
and paired-delta bootstrap intervals. The20 analyzer also requires exact
reconstruction of every original16 summary (including intervals) before reporting
20. Primary16 analysis SHA3fd8f480...d45e7 is unchanged.

Plan code0a7b0e8: **221 local and CI tests pass,7/7 workflows success**. Candidate
[44453019237](https://github.com/jfrancoiscollin/dilf/actions/runs/44453019237),
job135321297307; artifact14496378916 downloaded/checked,10752116bytes, ZIP SHA
6e66b724b6f97f5f98c945b50288c4c25eab4fb5b6b1a8e2bb827a4dcbaf3ca5.
Its synthetic/engineering provenance is distinct from these actual20 references.
Four concurrent D1 aggregate tests also pass locally with real repository imports;
no D1 code/experiment was duplicated or changed.

Files: `two-named-arenas-{source20,target20}-exploratory.json`,
`two-named-arenas-depth20-results.json`, `two-named-arenas-depth20-independent-verification.json`,
`two-named-arenas-depth20-reproduction.json`, `two-named-arenas-depth20-ci-verification.json`,
`two-named-arenas-depth20-{source,target}-attempt.json`. Reproduce with the
`two_arena_depth20 analyze` CLI and exact published plan0a7b0e8; raw references
are sufficient, no new engine search is needed for the tables/intervals.

The Jass primary remains source12,38 targets/31 owners,114 fully paired receipts,
29,640,000 exact nodes and control/native identical choices at all3budgets.
Existing telemetry has9 non-null verified-tie interventions (15 verified ties
with same winner,90 unique-best decisions), yet none changes the final choice;
this diagnostic does not imply an inert implementation or a strength gain.

## Next bounded scientific control

Use the ALREADY archived raw16/20 vectors for an explicitly **exploratory crossed-
depth decomposition on the same26 pairs**: freeze the first source16 maximizer
and reevaluate it at target20, and compute the reciprocal source20/target16
comparison. This separates source-action changes from target-reference changes
instead of attributing the observed-13 matched-depth cost difference to a single
mechanism. Fix code/formulas before computing derived tables, retain all26/ties/
zero/categorical cases, do not change the primary or choose cases by outcome.
Ordinary additive cost decomposition is only valid where all required scores
are ordinary; category changes stay separate. No new reference search is needed.
This is not another independent validation or a new signature/top-K policy.

All four WHOLE events and now-scored FENs remain reserved/excluded from D1 fitting,
independent validation, thresholds, signatures/refinement, top-K and dimension
selection. No paid resource, develop merge or deployment. Remote resources
completed both20 packets; Jeff's PC is not required. This last artifact/report
commit changes no code; inspect its successor Actions on the next passage.
