# Two named arenas: preregistered Scan16 geometry and equal-node Jass results

The full quiet-man geometry **does not guarantee the Scan16 best move** in this
prospective replication. In the frozen primary LCB-full-signature-equal stratum,
**14/26 source and target optimum sets are disjoint**, on22 frozen owner games
across both named arenas.11/26 transferred first source maximizers are target-
optimal;15 have positive cost, including one source-tie failure despite an
optimum-set intersection. All26 selected costs are ordinary Scan scores.

This is a finite pinned **Scan16/16 successor reference**, not a minimax theorem.
Scores are stored integer Scan units=0.01 HUB, not a fixed0.01 material pawn.
The source remained the original earliest LCB match; the full-signature mask
was frozen BEFORE scores. No favourable source, event or case was substituted.

## Primary geometry, both arenas retained

| Arena | Equal-signature targets / owners | Disjoint optimum sets | Source pick target-optimal | Mean cost | Median | Max | Positive costs / mean positive |
|---|---:|---:|---:|---:|---:|---:|---:|
|s7ahYqL4|17/14|10/17|6/17|33.1765|2|260|11/51.2727|
|D9PF2OSW|9/8|4/9|5/9|19.8889|0|146|4/44.7500|
|all|26/22|14/26|11/26|28.5769|1|260|15/49.5333|

Pooled sum of costs743, mean28.5769, median1, max260. Mean among15 positive
costs49.5333 (conditional descriptive quantity, never substituted for the
unconditional mean). The frozen-game, arena-stratified bootstrap (10000,
seed20261113, ranks249/9749) gives mean-cost interval[5.4762,52.7083] and disjoint-
set fraction0.53846, interval[0.36,0.71429]. These describe variation among games
in TWO fixed arenas; they do not establish broad tournament failure rates.
All owners stay in the draw frame even when no subgroup row belongs to them.
No undefined primary draws occurred. Full per-arena/subgroup intervals, tie
sets and every counterexample are in the result JSON.

## Complete frozen L/LCB population and complementary stratum

Both source arms use the SAME pre-score LCB equality mask for these summaries;
L's own equality label is retained per row and is not necessarily true in the
LCB-equal stratum. No outcome/optimum-count informative@3 filter was applied.

| Arm | Frozen stratum | Positions | Disjoint optimum sets | Optimal first picks | Mean ordinary cost | Median | Max |
|---|---|---:|---:|---:|---:|---:|---:|
|L|LCB_full_equal|26|15|10|33.0385|1.5|260|
|L|LCB_full_different|12|9|3|41.9167|8|294|
|L|all|38|24|13|35.8421|3|294|
|LCB|LCB_full_equal|26|14|11|28.5769|1|260|
|LCB|LCB_full_different|12|8|3|41.9167|8|294|
|LCB|all|38|22|14|32.7895|2.5|294|

All38 pairs in each source arm have ordinary/ordinary selected-score transitions;
no missing or categorical case was silently converted into zero cost. The
complement's max294 is NOT a counterexample within the equal-signature stratum;
its actual primary-stratum maximum is260.

## Concrete finite-reference counterexample

Arena s7ahYqL4, frozen owner `mtdp-lidraughts-s7ahYqL4.pdn:145`, public game `aEi5IXPd`, source game `pcblues_games.pdn:17`. Target plies: `[9]`.

The mover's exact black-man squares, full quiet descriptor and full legal
root-action mapping coincide; opponent placement differs. The deterministic
first source maximizer is **17-21**. Transferred to the target it scores-247,
whereas target optimum **20-25** scores+13: cost260 raw units (2.60 HUB, not a
certified2.60 material pawns). Optimal sets are disjoint. Exact FENs:

```text
B:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,47,48,49,50:B1,2,3,4,5,6,7,8,9,11,12,13,15,16,17,18,19,20,23
B:W27,30,31,33,34,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,11,12,13,15,16,17,18,19,20,23
```

## Equal-total-node Jass controls

All114 position/budget receipts are paired, no ceiling/error/fallback exclusion;
all three arms exhaust each total budget, including verification. Total Jass
nodes29,640,000. Control and native choose the same action38/38 at EACH budget.
This observed identity gives zero regret difference and a degenerate[0,0]
within-sample interval; it is not a proof of population equivalence or strength.
Jass prefixes used only source12; separate geometry source16/target16 never
entered those prefixes. All source12/Jass decisions were published before
opening target16 and the analysis implementation was already in that commit.

| Total nodes | Native / LCB / control optimum hits (n=38) | Native/control mean regret | LCB mean regret | Control-native mean / interval |
|---|---:|---:|---:|---:|
|10000|10/10/10|10.2105|10.2105|0/[0,0]|
|50000|11/12/11|8.5263|8.2368|0/[0,0]|
|200000|15/15/15|6.0526|6.0526|0/[0,0]|

At primary50k, control/native mean8.5263 versus unchanged LCB8.2368;
control-minus-LCB+0.28947, interval[0,0.94286]. s7ahYqL4:24 positions, all arms
6 optimums, mean10.8333. D9PF2OSW:14 positions, native/control5 optimums and
mean4.5714, LCB6 optimums and mean3.7857. These are recorded comparisons, not
an Elo or robust speed/strength gain. No p-value or adaptive go/no-go was used.

## Chronology, reproduction and independent checks

- Registration2a3089c live-observed18 November22:20:37UTC before BOTH starts.
- Real final exports acquired only after BOTH finishes and02:57UTC, two matching
  copies/event. All208 games, quarantine/alias accounting and raw bytes retained.
- Joint freeze **3fa9a56a3fa60954d5391d7e1b302c07e04f1f04** live-verified at
  19 November03:03:30UTC before reference scoring/target search; manifest SHA
  c079ca061d3645b42ce93235854e032de2be43a4cb08d8cea5ddbc1d92f1b5aa.
- All decisions/source12 and exact analysis code published in
  **03b1a270b12244a03df715f265f597bd0f00cd50**, before target16. Target packet binds
  that exact completed inventory, which was re-read/validated before scoring.
- Source16 and target16 complete legal-action packets archived separately;
  no old P1RUlfJc result pooled into this new registered estimate.
- Analysis independently rerun under7/61 is byte-identical, SHA256
  **3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7**.
  A separate direct raw-score/FEN check confirms26/22/14/11/sum743/max260;
  independently recomputed stratified bootstrap matches both primary intervals.
  All Jass quality sums/hits/node totals were independently recomputed from
  raw target scores and decisions, confirming the table and exact29.64M nodes.
- **211 tests passed and7/7 workflows success** on pre-target code03b1a27,
  candidate44449877832/job135310927865. Artifact14496020136 downloaded/checked:
 10752121bytes, ZIP SHAefe5f1bf6adc025618ebb9d46e9d856e888b2242f3f3205f84c3bee6bc261904.
  Its engineering fixtures/provenance are distinct from these actual computations.

Files: `two-named-arenas-results.json`, `two-named-arenas-target16.json`,
`two-named-arenas-source16.json`, `two-named-arenas-decisions/`,
`two-named-arenas-independent-verification.json`,
`two-named-arenas-analysis-reproduction.json`,
`two-named-arenas-analysis-ci-verification.json`, immutable `two-named-arenas-final/`.
Reproduce the exact analysis from pre-target implementation03b1a27 using the
CLI documented in `two_arena_analysis.py`; inputs/commit/prefix are in the
result JSON. No reference search is needed to reproduce the tables/intervals.

## Next scientific control and coordination

Fix an **exploratory Scan20/20 depth-stability control on ALL26 already frozen
LCB-equal pairs**, including zero-cost/optimal cases, with unchanged source and
legal catalogues. Publish the exact plan/mask/method before any depth20 score;
keep the Scan16 primary results immutable. This tests finite-reference horizon
sensitivity, not another independent holdout or minimax truth, because this
cohort's Scan16 outcomes are now known. No new signature/top-K/refinement or
threshold is to be fitted; those remain D1's scope. All four WHOLE events
fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW stay excluded from D1 fitting, thresholds,
dimension selection and independent validation, including newly scored FENs.
No paid resource or develop merge/deployment. Jeff's PC is not required for the
available remote resources. The evidence-only successor commit's Actions must
be checked at the next passage; no scientific method changes here.
