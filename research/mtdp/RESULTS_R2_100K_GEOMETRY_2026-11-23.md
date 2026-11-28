# MTDP-H13-G1 — Spatial coarse-signature collisions on 100,000 published Jass position records

**Experiment executed and verified. Descriptive only. Not a strategic-equivalence result.**

## Provenance, execution and reproducibility

- Pre-registration: [R2_100K_GEOMETRY_ABLATION_PROTOCOL_2026-11-23.md](R2_100K_GEOMETRY_ABLATION_PROTOCOL_2026-11-23.md), committed *before* this experiment.
- Executed code: `jfrancoiscollin/dilf@6a75dd3b772087751c4d092036f792f5d66da7b1`.
- GitHub Actions: https://github.com/jfrancoiscollin/dilf/actions/runs/45268838936, initial run status **success**. The six synthetic geometry tests passed in the same job before reading the corpus.
- Full first-run JSON artifact: https://github.com/jfrancoiscollin/dilf/actions/runs/45268838936/artifacts/14864905111.
- Raw JSON SHA-256: `95a3ac040ad246602b463b529b36ade20ae289ae88b68900f05c882611e244de` (3,509 bytes).
- First ZIP artifact digest: `sha256:17272aa3e67a0222b47c03a699f403d1442e0ddc2dbc49d5868f67a5b479be22`.
- Input manifest SHA-256:
  - R2: `e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c`.
  - Historical recovery: `e3ed9e2945dd3ff058868968d05343f85cf14ac6565f2180671cc44141768b19`.

**Reproducibility gate closed:** a separate rerun of the same job
(run attempt 2, job `138023831143`) published artifact
https://github.com/jfrancoiscollin/dilf/actions/runs/45268838936/artifacts/14864382238 .
Both extracted **3,509-byte JSON files are byte-identical**, with exact
SHA-256 `95a3ac040ad246602b463b529b36ade20ae289ae88b68900f05c882611e244de`.
The ZIP archives have different packaging hashes, not different JSON.
No extra sample, model run or independent-game study was performed.

The run fully rechecked stored/uncompressed file SHA-256, gzip CRC and JNNW
record framing across **96 positional objects** before producing the result.
The sampling method was the *same proportional deterministic evenly-spaced
per-file 100k* as the first two byte-identical baseline pilots.

The baseline reconciliation gate passed: 100,000 sampled, 100,000 structurally
accepted, 0 sampled rejected, **98,306 distinct exact board+trait positions**.

## Pre-registered geometric ablation results

Signatures count each of the four disjoint piece-type/color bitboards within
the indicated row partitions and preserve side to move. No WDL/score affected
a signature.

| Spatial resolution | Distinct signature classes | Classes with >1 exact position | Exact positions in such classes | Largest class (exact positions) | Hypothetical class reduction if one representative/class |
| --- | ---: | ---: | ---: | ---: | ---: |
| Material only (10 rows together) | **2,090** | 1,649 | 97,865 | 1,365 | 96,216 (97.87%) |
| Separate halves (5 rows each) | **13,494** | 7,166 | 91,978 | 665 | 84,812 (86.27%) |
| Bands of 2 rows | **69,617** | 12,235 | 40,924 | 121 | 28,689 (29.18%) |
| Each individual row | **93,827** | 2,203 | 6,682 | 76 | 4,479 (4.56%) |
| Exact 50-square state + side to move | **98,306** | — | — | 1 | 0 |

The table is **not a proven computational speedup**. The last column is
simply `98,306 - signature_classes`: the number of representatives not
needed *if*, counterfactually, all distinct positions in each coarse class
were interchangeable. They have **not** been shown interchangeable.
Unlike a genuine metric-ball experiment, sharing counts inside row bands
does **not** imply positions are even spatially close in individual squares.

The 5-row versus 2-row partitions are not nested; do not interpret them
as a monotonic guaranteed chain.

## Raw-label diagnostics (not best-move truth)

Number of collision classes containing more than one raw WDL label:

- Material-only: 1,259.
- 5-row halves: 4,384.
- 2-row bands: 7,456.
- 1-row bands: 1,351.

JNNW WDL is training data, can be relative to side to move and dependent on
game outcomes. It is neither independent Scan reference scoring nor legal
decision evidence. These counts do **not** estimate wrong-move risk. They
do show that crude positional classes should **not** be declared valid
solely because their structural description matches.

## Valid scientific interpretation

1. The sample of 100k positional observations has high exact diversity
   (98,306 distinct states); the large structural compression ratios
   emerge **only after discarding spatial information**.
2. Increasing geometric resolution produces many more distinguishable
   classes. The 2-row-level 29.18% and row-level 4.56% are only upper
   hypothetical *representation* savings on this sample.
3. No equivalence of legal moves, successors, value functions, best moves or
   Jass search trees was measured. No claim of faster or stronger Jass follows.
4. The sample is nonrandom and lacks an authenticated independent-game split:
   none of the above percentage ratios can be projected to the 30.16M
   raw-record population as an estimate or confidence interval.

**Status:** structural pilot PASS; scientific decision equivalence NOT TESTED;
pruning/promotion NOT AUTHORIZED.

## Scientific next step, single priority

Pre-register a new external **independently sourced legal game** holdout
that remains disjoint from the 30M training corpus, with source/game/ply
identity, JSM metadata where aligned, full FMJD replay and historical
leakage quarantine. Only then test whether positions from these coarse
classes retain legal successor structures and high-quality Scan/Jass moves
at matched nodes. Grouping by material/rows is a *candidate*, not an
accepted Jass evaluation feature.

No new engine scores, instance dispatch, R2 API access, cloud training,
or local-PC dependencies occurred in this phase.
