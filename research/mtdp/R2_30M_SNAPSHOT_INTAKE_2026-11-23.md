# MTDP-H13 — GitHub-published Jass position snapshots (2026-11-23)

## Inventory read directly from the published GitHub manifests

Source branch: data/r2-positions-2026-11-23 in jfrancoiscollin/dilf.

| Snapshot | Position files | Position records | Excluded metadata |
| --- | ---: | ---: | ---: |
| R2 snapshot (2026-11-21) | 57 JNNW + 28 FEN | 13,428,708 JNNW + 120,683 FEN = **13,549,391** | 792,528 TSV + 10,000,000 JSM1 rows |
| Historical recovery (2026-06-20, recovered 2026-11-23) | 11 JNNW | **16,610,792** | 0 |
| **Gross position observations** | **96** | **30,160,183** | Excluded |

The R2 snapshot has 155 stored distinct full payloads with 264 original R2
source mappings, including metadata. This is payload-level deduplication,
not position-level deduplication. The historical snapshot has 11 objects with
159,595,365 stored compressed bytes; the R2 snapshot has 158,168,048 bytes
across its position and sidecar objects.

No historical object has an exact matching *uncompressed payload SHA-256*
among the R2 snapshot objects. This is not evidence that the underlying
individual game positions are disjoint.

The R2 manifest preserves source keys, original SHA-256 and ETag and
the inventory timestamp 2026-11-21T18:36:23.931575+00:00. The historical
recovery manifest documents SHA-256 of recovered local bytes but no original
independent historical hash. Each published snapshot contains its own
offline integrity checker; no FMJD legality proof follows from it.

## Empirical spot check of GitHub-hosted FEN (not engine replay)

Two real text blobs were read over the authenticated GitHub connector:

- objects/f0f1ff5e60d0b44d-dilf_combinations.fen:
  305 noncomment position records; 302 distinct *raw* first-token FEN
  strings (3 extra occurrences); 256 white-to-move and 49 black-to-move.
- objects/e7b89a5e3feade89-turnover.fen:
  500 position records, 500 distinct raw first-token FEN strings;
  257 white-to-move and 243 black-to-move.

Only within-file raw FEN text was compared; the 805 lines do not constitute
a representative estimate or a canonical cross-corpus overlap analysis.

## Bounded published-snapshot pilot

research/mtdp/r2_snapshot_diversity.py now accepts the two already-local
roots, validates exact stored/uncompressed SHA-256 and gzip/framing, samples
at most 100,000 *position observations* deterministically and constructs
the common four-bitboard-plus-trait key. TSV/JSM1 rows are never included as
positions. The sample yields exact matching-position counts both within and
across published snapshots plus descriptive material counts and raw-WDL labels.

The GitHub workflow mtdp-r2-published-snapshots-pilot runs on standard Actions
and uses only the published Git data-branch snapshot: no R2 token, remote R2
read, cpx62 runner dispatch, Scan/Jass engine computation, learning, mutation
or credential access. A versioned JSON receipt is uploaded after success.

Reproduction from a research checkout with a data-branch worktree in snapshot-data:

    python -m research.mtdp.r2_snapshot_diversity \
      --r2 snapshot-data/data/r2_positions/2026-11-21 \
      --historical snapshot-data/data/r2_positions/recovered-2026-06-20 \
      --max-sampled 100000 \
      --output /tmp/mtdp-r2-snapshot-pilot.json

## Scientific gates after this step

- The aggregate 30,160,183 is a **raw sum**, not a count of distinct legal
  positions or independent game trajectories.
- Deterministic proportional record-index sampling does not justify
  confidence intervals or population-level collision-rate extrapolation.
- No score, WDL, or signature similarity is a safe move-pruning certificate.
- Before D1 admission: verify source / game lineages, historical excluded
  events, leakage, FMJD legality and independence. Then separately run
  a preregistered matched-budget Jass / Scan regret experiment.
