# H13 — six JNNW/JSM1 structural checks, 24 November 2026

Code/protocol commit: ca7f84a253a6501bb1943d27fb8d5129e82e5a69.
Actions run45295976368/job138116323739 completed successfully, including eight
synthetic tests and the complete real-file structural audit. No duplicate
campaign, R2 access or engine calculation was launched.

Artifact14875928703 was downloaded and its ZIP SHA-256 matched GitHub:
0b6943ae1ec0b66888c01c93ece318918c39adbbf3a5c2e250af3e71a4b9c014.
The exact report is validation/jsm1-pair-structural-audit-2026-11-24.json;
SHA-256 53886251c2d5072c88a2ef67d95219b8b55648230ade3c910514b5e5d9f6fc88.
Data commit and manifest are pinned in the protocol and workflow.

| Pair stem | Structurally checked rows | Sampled metadata rows | Distinct sampled game IDs | Distinct sampled opening IDs | Seeded rows (full file) |
| --- | ---: | ---: | ---: | ---: | ---: |
| m2-d8 | 2,000,000 | 1,024 | 1,024 | 1,024 | 0 |
| f2m.raw | 2,000,000 | 1,024 | 1,024 | 1,024 | 0 |
| m2.fit | 2,000,000 | 1,024 | 1,024 | 1,024 | 0 |
| f2m-extra | 1,500,000 | 1,024 | 1,024 | 1,024 | 0 |
| turnover1to1 | 2,000,000 | 1,024 | 1,024 | 1,024 | 0 |
| f2m-common | 500,000 | 1,024 | 1,024 | 1,024 | 0 |

Every stored and decompressed file hash/size, gzip integrity, header, record
count, row framing, board occupancy/trait/WDL and seeded flag passed. This is
structural validation, not FMJD replay or best-move preservation. Numeric IDs
are reported separately by file: the sample says nothing about their external
identity, provenance, cross-file namespace or whole-game uniqueness. Sampling
is deterministic; do not estimate population rates or confidence intervals.

The files remain in quarantine for confirmatory D1 use. All admission flags
remain false. JSM1 contains no ply. A synthetically permuted valid sidecar passes
structural compatibility, demonstrating why byte verification cannot establish
semantic index alignment. Shared source names and equal counts cannot replace
original generation/merge receipts. No independence or safe pruning is proved.

Next: locate and authenticate original Jass producer/merge transformations and
run receipts that bind position and metadata row indices; check whether IDs
represent real game/opening lineage. Only then attempt full-trajectory and
historical-exclusion checks, including all four reserved events. No new cohort
is frozen and no prospective Jass/Scan budget comparison is admitted here.
Jeff's PC is not required for this structural stage.
