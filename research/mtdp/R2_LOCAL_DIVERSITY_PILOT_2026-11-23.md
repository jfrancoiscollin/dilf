# H13 — offline JNNW diversity pilot (NOT a 13M-position result)

**Status:** code and synthetic tests only. No Cloudflare R2 read, runner job,
dataset download or real-corpus statistics.

The ten exact legacy keys are in research/mtdp/r2_l3_source_manifest.json.
Their historical summary reports **1.5 million records**, not 13 million
distinct positions. The larger claimed 13M corpus still lacks a separately
verified source-object manifest, record-count definition and provenance receipt.

## Scientific question

In an already-local, structurally valid JNNW sample, how much repetition is
due to **identical** four-bitboard-plus-trait states? How many keys occur in
more than one source file, and how often do they bear different raw WDL labels?

Exact redundancy is not approximate decision equivalence. Different labels
do not prove ground-truth conflict. These records do not verify independent
game lineage or a complete legal trajectory.

## Frozen v1 measurement protocol

1. Validate the existing ten-key documentary manifest. All objects must
   already be under the local mirror root. Reject symlinks, missing files,
   path escapes, bad gzip, framing and trailing bytes. No network or job launch.
2. Record compressed local file SHA-256 and size. These do not authenticate
   corresponding remote R2 source objects without separate receipts.
3. Sequentially decompress and structurally validate all records in the JNNW
   header (8-byte header plus 38-byte records). Flag bad bitboards, piece
   overlap, side to move and WDL. Cap declared rows at 20M per source by default.
4. Keep at most **100,000 sampled rows in total** (even file-wise allocation,
   normally 10,000 per file), at deterministic evenly spaced indices. An
   underfilled file does not transfer quota. **Not random or game-stratified**.
5. For valid sampled rows, deduplicate the exact 33-byte key formed by four
   bitboards and side to move, omitting score and WDL. Report distinct keys,
   duplicate occurrences, cross-file occurrences, material/trait/WDL counts
   and exact keys having more than one raw WDL label.
6. Write versioned JSON, exclusive create; do not export positions or alter
   frozen D1 evaluation, target scores, thresholds or independent cohorts.

## Reproduction on separately approved local copies

From the DILF research checkout with manifest-relative paths already present
under the local root:

    python -m research.mtdp.large_corpus_profile \
      --manifest research/mtdp/r2_l3_source_manifest.json \
      --local-root /path/to/already-copied-jass-data \
      --max-sampled 100000 \
      --output /tmp/mtdp-r2-local-diversity-pilot.json

    python -m pytest -q research/mtdp/tests/test_large_corpus_profile.py

The tool never downloads R2 objects. The external inventory should record UTC
capture, immutable keys, remote object identity and SHA-256, matching local
readback, independent sources/lineages and read costs. A local hash is not a
remote provenance proof.

## Stop/admission rules

- **No full 13M run from this proposal.** First identify the actual immutable
  13M corpus keys, schema, counts and whether the headline figure denotes visits,
  records, unique positions or independent games.
- Reject malformed sources and report defects, rather than silently accepting
  partial gzip input.
- For D1, require the existing historical-leakage, event-source ownership,
  complete legal trajectory and independent-cohort admission gates.
- Decision-safe pruning requires another paired Jass/Scan study at matched
  node budgets with a legal move baseline and measured regret.

## Relay handoff — 2026-11-23 UTC

Relay: ad hoc H13 intake. Initial PR #43 head:
d87aed097a9df2ea2381a6baea1f7ed8e86d8188.
New files: research/mtdp/large_corpus_profile.py,
research/mtdp/tests/test_large_corpus_profile.py and this document.
A local self-contained scaffold passed **four synthetic tests** plus compilation.
This is not a real R2 analysis. GitHub CI must validate the committed changes.
**There are no new numerical results from 13M positions.**

**Single next action:** authenticate a read-only, exact-key R2 inventory for
the 13M corpus, then take a bounded format sample with matching object hashes.
