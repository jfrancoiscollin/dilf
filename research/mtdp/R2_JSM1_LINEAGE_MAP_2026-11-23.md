# MTDP-H13 — JSM1 provenance bridge found in the published Jass R2 snapshot

**Source:** immutable data from `jfrancoiscollin/dilf`, branch
`data/r2-positions-2026-11-23`, directory
`data/r2_positions/2026-11-21/`. The pinned manifest SHA-256 is
`e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c`.
The documentation for the JSM1/JSM2 wire format is
`jfrancoiscollin/jass:docs/formats/JSM2.md`.

## Six candidate sidecar↔position file pairs (not yet row-verified)

All files are published under the `objects/` subtree; the full object
names below are anchored by their stored uncompressed content SHA prefix.

| Original corpus stem | JNNW snapshot basename | JSM1 snapshot basename | Manifest rows |
| --- | --- | --- | ---: |
| m2-d8 | ee8d685cea331940-m2-d8.jnnw.gz | 42b184456375bb58-m2-d8.jsm.jsm1.gz | 2,000,000 |
| f2m.raw | 15261c89bd6520e1-f2m.raw.jnnw.gz | 6b12a94012803365-f2m.raw.jsm.jsm1.gz | 2,000,000 |
| m2.fit | 6ac60a9b3d0ede59-m2.fit.jnnw.gz | 756de534a71e5ace-m2.fit.jsm.jsm1.gz | 2,000,000 |
| f2m-extra | 79e605f3139e510f-f2m-extra.jnnw.gz | a54a1c81ce17e21b-f2m-extra.jsm.jsm1.gz | 1,500,000 |
| turnover1to1 | 9b7db67a87025baf-turnover1to1.jnnw.gz | acf3bbf4a28e7b44-turnover1to1.jsm.jsm1.gz | 2,000,000 |
| f2m-common | f1522b2afbd9feab-f2m-common.jnnw.gz | cc0e423f6e5c1a91-f2m-common.jsm.jsm1.gz | 500,000 |
| **Total candidate alignment** | **6 JNNW** | **6 JSM1** | **10,000,000** |

Each pair shares the same original source stem, R2 `pause/jass-20260922/runs/home-0977...`
run lineage, and declared record count in the published snapshot's
authenticated manifest. A source-side variant such as `work/m2.raw.jsm`
is also mapped to the published `turnover1to1` object: the source mapping
is many-to-one at payload level. Do **not** infer six independent games,
or independence of the six corpora.

## What JSM1 can and cannot establish

The pinned Jass format documents `JSM1` as an 8-byte magic/count header,
then **17 bytes per row**: `game_id (u64)`, `opening_id (u64)`,
`seeded (u8)`. This is a substantial improvement over JNNW alone:
it may permit game-wise clustered counts and source-aware exclusions for
the paired subset, after strict row-level alignment verification.

But JSM1 does **not** contain `ply`, complete move trajectories, final
game length, adjudication flags or per-game finish metadata. Those additional
fields are in JSM2 (25 bytes per row), which is not present in these
published six sidecar files. Equal count/name is not proof of exact
record alignment, no direct legal FMJD trajectory exists, and `game_id`
may collide or reset across source runs. Explicit namespace + opening
identity is required before any statistical independence assertion.

## Bounded admission plan — no execution yet

1. Authenticate both gzip byte hashes, source stems and JNNW/JSM1 exact
   framing/record counts for all six candidate pairs. Read JSM1 strictly
   (magic, count, bytes, `seeded` in 0/1). No sidecar implicit fallback.
2. Match exact original run lineage and generation/merge transformation for
   each pair; only if the source guarantees index alignment, attach per-row
   `game_id` to the matching JNNW record. Otherwise quarantine it.
3. Report game-ID distinctness per source namespace, repeated opening IDs,
   rows per game distribution, source overlap and any unexplained reuse.
   Do not confuse a same-number game ID with a canonical trajectory hash.
4. Ensure historical D1 exclusions across FEN/trajectory/source aliases
   before any sampling or validation; reserve complete games, not
   arbitrary individual positions. Keep 30M training populations out of
   an unexposed prospective holdout.

**Scientific conclusion:** the R2 snapshot contains potentially useful
provenance sidecars for **10M *records***, conditional on alignment.
This does not verify 10M independent positions or authorize D1 testing.

**Next action:** implement a strict, bounded paired JNNW/JSM1 alignment
reader and audit; preserve H13-G1 geometric results unchanged.
