# Fixed analysis implementation before target-outcome opening

Joint actual freeze3fa9a56a3fa60954d5391d7e1b302c07e04f1f04 was published and
live-verified at03:03:30UTC, before any source/target scoring. Its immutable
manifest SHA is c079ca061d3645b42ce93235854e032de2be43a4cb08d8cea5ddbc1d92f1b5aa.
The reference source12 and all114 native/LCB/control receipts are complete:
38/38 targets paired at every10k/50k/200k budget, zero ceilings/errors. Every
arm spends its exact total, including verification. Combined Jass nodes:
29,640,000. Full source12, plan, build/method hashes, all decisions and their
inventory are published together here BEFORE target16. Source16 geometry is
separately typed and cannot rank Jass prefixes. No target Scan16 reference has
yet been computed or opened; no best-move preservation/quality result claimed.

`two_arena_analysis.py` is fixed/tested in this same pre-target decisions commit.
Its exact bytes must match that commit before analysis; target16 requires this
published snapshot and records its exact commit/prefix/completion hash. No local
or incomplete campaign can satisfy that gate. All existing selectors, geometry
labels, source choices, controls, budgets and reference versions are unchanged.

This implements the already registered estimands, not a new numerical gate:

- Geometry source16/target16: full tied optimum sets, disjoint-set counts and
  rates, deterministic first canonical source-maximizer transfer, target-optimal
  pick, ordinary regret all/positive-only mean/median/max and every row/category.
- Shared primary geometry stratum: the already frozen **LCB** full-signature
  equality label, used for both L and LCB summaries; keep its complement and
  whole population. Also retain each source's own equality label in row audits.
  Never replace a source or use optimum count/informative@3 as an eligibility mask.
- Jass: all three arms/all budgets, complete pair/ceiling accounting, optimum
  hits, ordinary regret, primary control-minus-native at50k and LCB comparator.
- Report each fixed arena and pooled position-weighted estimates separately.
  No old P1RUlfJc outcome is pooled into this new registered estimate.

Bootstrap draws whole **frozen owner games**, stratified by these two fixed
arenas. Owner is the frozen lexicographically smallest game ID, never each row
as an independent observation. Resample the SAME owner sampling frames and
same draws across arms/fields (10000 draws, seed20261113). Recompute numerators
and denominators for every draw to obtain position-weighted ratios; do not
average per-game means. Owners with no rows in a geometry/category stratum
stay in the sampling frame, so masks cannot alter the draw distribution.
95% sorted percentile ranks249/9749 are fixed. If a subgroup's sampled ratio
is undefined on any draw, report that count and CI=null; do not retry/drop
undefined draws or change percentile ranks. No eligible values likewise stays
explicitly empty. Intervals describe game variation within the two named fixed
arenas, not broad tournament generality. Positive-only cost is the registered
conditional descriptive quantity and does not replace unconditional mean regret.

Raw integer Scan units equal0.01 HUB, not a universal0.01 material pawn.
Ordinary is inclusive[-8000,8000]; categorical transitions remain separate.
No minimax proof, Elo, p-value discovery gate, population equivalence or pruning
claim follows from this finite reference and two-arena sample.

**211 local foundation tests pass**, including7 new analysis tests for unequal
position/game weighting, fixed arena resampling, paired fields, preserved empty
subgroup draws, missing/duplicate owners, disjoint optima vs source-tie transfer
failures, the shared frozen LCB mask, categorical costs and pre-target code binding.
Existing execution code2225760 has7/7 successful Actions. The newly added analysis
code and the unchanged research kernels will be checked by the existing workflow;
no D1 metric/campaign was changed. All four whole events remain reserved outside
D1 fitting/signature/top-K/refinement/threshold/dimension/validation.

Next: verify this published decisions snapshot, run target16 using its exact
commit/prefix, then compute all registered tables/cases/intervals with this exact
analysis code. Archive raw target references and results, reproduce analysis7/61,
confirm CI, and report both positive and null/empty findings. Jeff's PC is not
required for this accessible remote computation.
