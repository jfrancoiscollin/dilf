# Preregistered P1RUlfJc replication — 18 November 2026

## Population and ordering of evidence

The exactly named official 5+0 arena was registered at 14:29 UTC before its
20:00–20:57 UTC games. Final metadata and two independent equal PDNs passed the
registered gate: 241 games, 148 participants, PDN SHA
`c1c23993b39da11442e2f4bc8cb5cbf8f9fb2713463be5b981d95a190cd68439`.
Whole-game replay retained 225 games; seven known token-sequence aliases and nine
ambiguous games were wholly excluded. The unchanged selector yields **33 common
L/LCB targets**, **26 distinct owner games**, **34 source FENs**, **327 target
actions**. All historical IDs/tokens/complete trajectories and 411980 confirmed
FENs were checked. No ambiguous continuation was inferred.

Freeze [5a050b1](https://github.com/jfrancoiscollin/dilf/commit/5a050b1068154a527cc5f35a8f795919def2dcce)
was published and freshly verified at 21:21:28 UTC, manifest SHA
`ba613fc0615c482e069b26caa471d040338486732fda3c677362474de14d503a`.
Proposal bytes reproduce under subprocess seeds 7/61. Source Scan12 and all
three Jass arms were executed only after that proof. **All 99 position/budget
receipts** and the analysis implementation/plan were published in
[dad9e70](https://github.com/jfrancoiscollin/dilf/commit/dad9e702d22aa810c5e5ad92c56af8e976be3342)
before the target Scan16 run (fresh verification at 21:27:34 UTC). Scientific
code and 118 targeted local tests were fixed before target scores. No reference
outcome selected the event, positions, source ranking, tie intervention or budgets.

## Fixed reference and geometry transfer

Jass/Scan/FMJD versions, legal-action mappings and engine hashes are pinned in
the freeze/build receipt. Source successor reference is depth 12; target reference
is depth 16. An ordinary stored integer equals 0.01 HUB display unit, not a
certified 0.01 material man. All 33 observed outcomes here are ordinary.
These **cross-depth transfer** figures do not isolate geometry from source-depth
error and are not a proof of minimax (non)equivalence.

| Source selector | Targets | Source pick is target-optimal | Optimum sets intersect | Mean selected-action regret | Median | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L | 33 | 12 | 12 | 11.1212 | 2 | 129 |
| LCB | 33 | 12 | 12 | 10.6970 | 2 | 129 |

Choices use the existing lexicographically first source maximizer; optimum-set
intersection retains all ties as a separate outcome. Thus the registered LCB
transfer misses the target optimum in 21/33 cases under these fixed references.
All per-case choices, counterexamples, ordinary costs and categories are included
in `P1RUlfJc-quality.json`; no disagreement was discarded.

## Equal-total-node three-arm result

Every position exhausts the assigned total budget in each arm. The controlled
arm charges preliminary/probe nodes before its residual main search. All 33
positions remain paired at every budget, with zero depth-ceiling exclusions or
technical failures. Mean verification cost is 170.8182 nodes per position;
four verified tie interventions occur at each budget (21 unique-best verifications,
eight ties retaining the same winner). No fallback on incomplete evidence occurred.

| Total nodes | Native optimum hits | Unchanged LCB hits | Control hits | Native/control mean regret | LCB mean regret | Control − native mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 10/33 | 12/33 | 10/33 | 9.3030 | 8.6061 | 0 |
| **50,000 primary** | **14/33** | **14/33** | **14/33** | **7.8182** | **7.2727** | **0** |
| 200,000 | 11/33 | 13/33 | 11/33 | 5.6970 | 5.1818 | 0 |

The control and native choose identical moves on all 33 targets at all budgets,
so every paired ordinary regret difference is exactly zero. The registered
whole-game bootstrap (10000 resamples, seed 20261113) gives [0,0] in-sample for
the primary mean difference. This degeneracy reflects identical observed choices;
it does **not** prove a population equivalence margin or playing-strength gain.
Budgets can yield non-monotonic optimum-hit counts under finite search.

At 50k, control-minus-unchanged-LCB mean ordinary regret is +0.5455 units,
95% game-bootstrap interval [-0.0732,1.9655]. At 10k it is +0.6970 [0,1.7105];
at 200k +0.5152 [-0.2195,2.0690]. Three LCB/native final choices differ at each
budget. All raw costs and paired denominators are retained.

The frozen ownership convention matches the previous implementation: assign each
unique target FEN to its lexicographically smallest owner game for resampling.
There are 26 distinct game owners in the manifest but **25 resampling clusters**
after this deterministic shared-FEN attribution. The sample is one named arena;
within-arena intervals do not establish multi-tournament generality or Elo.

## Reproduce and restore

The exact gzip Linux executables and pre-freeze build receipt are committed;
compiled files can be restored by decompressing each `P1RUlfJc-runtime/*.gz`,
checking its declared SHA-256 and setting executable permission. The initial
build was technically retried after installing missing CMake. No paid resource
or Jeff PC was necessary.

`P1RUlfJc-decisions.json.gz` is a gzip JSON object with `files` mapping relative
paths to exact UTF-8 raw receipt contents. Restore those files into a new
directory without newline normalization. The committed source and target packets
are bound to the same manifest; the analysis plan records the pre-target script
hash. Recompute using:

```sh
PYTHONPATH=.:../draught-master python -m research.mtdp.jass_benchmark.named_campaign_quality \
  --root . --directory research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc \
  --commit 5a050b1068154a527cc5f35a8f795919def2dcce \
  --source research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc-source.json \
  --target research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc-target16.json \
  --receipts RESTORED_NEW_DIRECTORY --output NEW_QUALITY_JSON
```

Next justified control: a **separately labelled exploratory source-depth
sensitivity** (source Scan16 versus the same target Scan16) on this already seen
cohort. Preserve primary source12, all decisions and the primary analysis unchanged.
It distinguishes cross-depth transfer error from equal-depth disagreement but
cannot be relabelled a new held-out confirmation. No new signature, D1 campaign,
threshold or cohort is selected. Entire P1RUlfJc/fFgE7oED remain reserved from D1.
New CI checks on the current branch remain to be confirmed separately.


## Completed exploratory equal-depth control and full-signature annotation

The follow-up implementation was fixed in `6cf0445` after the primary result and
before computing source16. It re-verifies the same immutable freeze and uses the
already published target16 packet from `f741ed6`. No primary source12, decisions,
analysis or selected source FEN is changed. This is an **exploratory sensitivity
on the already observed cohort**, not another independent confirmation.

At source16/target16, the existing LCB source pick is optimal on **13/33** targets;
optimal sets intersect in **16/33**, so **17/33 pairs have disjoint optimum sets**.
Mean selected-action ordinary regret is 10.6667, maximum129 integer Scan units.
For L, the selected source pick is optimal12/33, sets intersect15/33, mean10.7879.
The source12-to-source16 change therefore does not remove the finite-reference
transfer disagreements. The separate source16 packet is marked
`primary_source_usable=false` and is rejected by the primary depth12 campaign gate.

LCB is weaker than the full quiet signature: it matches legal actions, mover man
count and blocker descriptor, while full `_quiet_signature` also fixes the exact
mover-man squares. **Do not describe all 33 LCB matches as full-signature matches.**
A separately labelled post-hoc annotation computes the *existing* full signature
without learning a new signature or changing any target/source. All 33 rows and
both equal/different strata are retained in `P1RUlfJc-full-quiet-annotation.json`.

| Source choice, existing full quiet signature equal | Pairs | Owner games | Disjoint optimum sets | Source pick optimal | Mean regret (all pairs) | Mean positive regret | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L | 24 | 17 | 12 | 9 | 6.875 | 11.0 (15 cases) | 97 |
| LCB | **25** | **18** | **13** | **9** | **6.88** | **10.75 (16 cases)** | **97** |

For the LCB/full-signature stratum, three additional suboptimal chosen moves arise
from ties: optimum sets intersect but the deterministic first source maximizer is
not target-optimal. This distinguishes set disagreement from a tie-breaking cost.
These are concrete counterexamples to preservation of the **finite Scan16 optimal
move set** by this descriptor on the examined pairs; no minimax implication or
population error-rate guarantee follows. The annotation was selected after the
primary outcome, so its subgroup rates/costs remain descriptive and exploratory.
All values are stored integer Scan units; maximum97 equals0.97 HUB display unit,
not a certified0.97 material pawn.

Reproduce the source16 control with `named_source16_sensitivity` using the same
freeze and published primary-reference commit, then `named_signature_annotation`.
The latter never scores, searches, selects a different source or removes a row;
it rejects population/ownership changes and undefined (non-quiet) signatures.
Per-case primary/secondary references, exact optimal sets and all labels/costs
are committed. **125 local targeted tests pass** after the annotation checks;
new CI must still be observed on the published head.

Next foundation control: prospectively register a separate multi-arena replication
with fixed identities before play, preserving the existing signatures, all
selected positions, total budgets and adverse/empty-result reporting. This would
assess tournament-to-tournament stability; it must not pool this exploratory
subgroup as a fresh confirmatory cohort. Coordinate all new IDs/exclusions with
D1 before use. No D1 refinement/top-K/dimension campaign is authorized by these
results, and entire P1RUlfJc/fFgE7oED remain excluded from D1 fitting/thresholds.


A reproducible full-signature counterexample is frozen target game235: the source
Scan16 maximizer is `19-23`, whereas the target's maximizer is `11-16`.
The target scores are -120 for the transferred `19-23` and -23 for `11-16`, giving
97 integer units of regret. Both complete source/target FENs and action optima
are recoverable from the manifest and annotation JSON; no ambiguous move was
used. The exact mover-man squares and blocker descriptor coincide, while other
opponent placements differ. This demonstrates the descriptor's loss of relevant
information for this finite reference, without establishing minimax truth.


## Final verified controls — 21:51 UTC

Validated code HEAD `0bcabd4c516ed67c0f7d30cf33babd65d1bea2e3` has **seven successful
workflows**, including [candidate run44404104714](https://github.com/jfrancoiscollin/dilf/actions/runs/44404104714),
job135154797763, **125 targeted tests passed**. Real pinned Scan startup and the
FMJD/Jass synthetic engineering rehearsal pass; both synthetic bundles remain
rejected for production and their hashes repeat under seeds7/61. These CI checks
are separate from the actual named-arena engine/reference calculations archived
above; they do not rerun the real33-target campaign.

Artifact [14473163987](https://github.com/jfrancoiscollin/dilf/actions/runs/44404104714/artifacts/14473163987)
was downloaded, **6,824,390 bytes**, ZIP SHA-256
`8d552ce91164b685f61ac8d2a557cd96ca6a28088278d1b5b3285abcdfc172d8`.
ZIP bytes, both complete synthetic payload inventories, three repeated report
hashes and pinned historical registry/index were checked after extraction.

The actual primary analysis was independently rerun with process hash seeds7/61:
both files equal the committed quality JSON byte for byte, SHA-256
`a7c151b6d8a2c24577e3c224295359100eb669ad73643583d1c1f0068db55e9b`.
A direct recalculation from raw source16/target16 action scores (without using
the comparison-report aggregation) independently reproduces the full-signature
LCB stratum:25 pairs,13 disjoint optimum sets,9 optimal picks, total regret172,
mean6.88,16 positive costs averaging10.75, max97. All99 raw decision receipts were
also checked independently: exact three-arm totals, all verification nodes
charged, no ceiling, native/control identical moves, **25,740,000 total Jass
nodes** across positions/budgets/arms. Scan reference search work is separate
from that Jass-node total.

`P1RUlfJc-results-verification.json` contains these checks and all input digests.
No technical engine job failed; missing local CMake was corrected before successful
builds. Superseded Actions runs were replaced by newer commits, without duplicate
manual campaigns. This final evidence-only documentation commit may trigger new
automatic checks; do not attribute their unobserved result to this completed run.
Next action remains prospective multi-arena registration before games, with all
new reservations recorded for D1. No Jeff PC, paid spending, deployment or merge
was needed.
