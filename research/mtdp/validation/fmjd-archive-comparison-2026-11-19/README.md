# FMJD archive drift: content comparison, 19 November 2026

This closes the H43 comparison requested in `RELAY_COORDINATION.md`. Both source ZIPs were downloaded from GitHub Actions, their recorded complete-archive SHA-256 and sizes verified, then preserved here. No engine, new acquisition, D1 campaign or independent cohort is involved.

| File | Artifact | Source commit | Bytes | ZIP SHA-256 |
|---|---|---|---:|---|
| earlier.zip | 14545492498 | 669244adec40f1a409a82b8618d8c8ce46f806a1 | 81978 | 3a67b1a2dc0b42590ab2073bc9e31b1b1bd9bea9bf4bd427092f11c0e49cae1b |
| later.zip | 14550374124 | 1cd3983e57d963e6d12d34c5caa14ff62bcbc02d | 81980 | cd26035f71eb4d0c57d6324f562b5e9f529e6bf4cb32188a3928420f4494310e |

**Result: all nine data members are byte-identical.** This includes the 1,427,716-byte trajectories file (SHA cb31167784fd8a5a9da1ed8e7c59caf4d2f9390ce2ffe4162260a4612faf9cb8), all seven descriptive JSON outputs, and empty quarantine. Each internal manifest's ten file entries was checked against actual bytes/lengths. `comparison.json` records every member's two hashes and sizes.

Two members differ: provenance and its internal-manifest entry. The only provenance changes are `dilf_sha` (the actual PR checkout/merge) and `dilf_source_sha` (the source commit). Both requested and actual FMJD revisions remain 0e5189fbb251bf5eaf2e613d0f878bb17c740311. ZIP member order also differs. Thus **whole archives are not byte-identical**; equal ZIP digests were neither expected nor required for this comparison. No numeric data drift was observed in these two archives. This is a bounded archival comparison, not a future reproducibility guarantee, legal admission of a new corpus, strategic equivalence or a Jass strength result.

Reproduce from the repository root without external downloads:

```bash
python -m research.mtdp.fmjd_artifact_comparison --left research/mtdp/validation/fmjd-archive-comparison-2026-11-19/earlier.zip --right research/mtdp/validation/fmjd-archive-comparison-2026-11-19/later.zip --left-sha256 3a67b1a2dc0b42590ab2073bc9e31b1b1bd9bea9bf4bd427092f11c0e49cae1b --right-sha256 cd26035f71eb4d0c57d6324f562b5e9f529e6bf4cb32188a3928420f4494310e --output /tmp/mtdp-fmjd-comparison.json
cmp /tmp/mtdp-fmjd-comparison.json research/mtdp/validation/fmjd-archive-comparison-2026-11-19/comparison.json
python -m pytest -q research/mtdp/tests/test_fmjd_artifact_comparison.py
```

Five focused comparison tests pass locally, alongside 21 prospective-manifest and 31 D1 corpus-guard tests (57 total). New CI is checked separately after publication. D1's remaining closed-schema/producer-compatibility and real-corpus legality gates stay its responsibility. H13 waits for independent qualification before freezing the next executable prospective protocol/cohort. All four reserved events and their games/FEN remain excluded from D1 fitting/independent validation/tuning. Jeff's PC is not required.

## Verified publication

Code/data2806b643c5040410690553fef0d96a5b593858cb published with expected exact tree; all8Actions successful. CI44575126043/job135740431681 reports643core and668MTDP tests passed (4skipped), and the explicit no-engine comparison/cmp step succeeds. All57local targeted tests ran. See ci-verification.json for hashes/run IDs. Next successor adds only proof/docs; check its CI next passage.
