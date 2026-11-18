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
