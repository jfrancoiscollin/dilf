# Known old manifest positions are already covered by the H13 cache

The 247 old manifests used by `validated_archive_fens` contain 188,809 distinct
canonical FENs. **All 188,809 occur in the pinned 452,526-position H13 cache.**
The comparison finds zero missing FENs. No cache extension or engine replay is
needed to cover this particular historical position inventory.

The new check authenticates `CARZrQpl/provenance.json` by its exact SHA-256
`e8029eff15b30352db9e33857ba58444d093902bfd539800d30cb237829d131f`, then uses the
existing verifier to authenticate every listed manifest/shard by SHA-256 before
extracting only FEN fields. It authenticates the reconstructed four-event cache
by SHA-256 `5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7`.
Both sets use the existing D1 canonical occupancy serialization, with trait and
king identities preserved. Inclusion is checked on actual FEN strings, not only
counts or caller-supplied digests.

Canonical set hashes (sorted FEN strings joined by newline, no final newline):

| Set | FENs | SHA-256 |
|---|---:|---|
| Known 247-manifest inventory |188809|`ac3d8b4b0c38ecc7d6688d60daa53b2200193e3b72b65d01dbe5c18d60532a7c`|
| Four-event historical cache |452526|`edb4471702c3ec26ca0e9fdbe0a64384ebb65724e31c3b04badf8f49df899206`|

This closes the specific question whether these old manifests add historical
positions missing from the existing cache. It does **not** authenticate external
event identities, prove completeness over unspecified other histories, restore
unknown continuations of quarantined games, or admit an independent cohort.
Canonical FEN syntax does not establish board legality. No target score,
signature, top-K policy, prospective population or Jass budget changes.

D1 can reuse the already verified cache, alias/trajectory screens and
`authenticated_corpus_bridge.py` for this known scope. Before any new PASS,
reconcile the candidate's source/event receipts and identify any concrete
historical sources outside the pinned 25-source/247-manifest inventory. An
unresolved coverage issue should name the missing source and expected evidence;
rebuilding the same known FEN inventory is not needed. Unknown provenance remains
quarantine, and all four reserved events remain excluded in full.

Reproduce from the research checkout with the pinned cache reconstructed by the
existing prospective-candidate workflow:

```bash
MTDP_HISTORICAL_FEN_CACHE=/path/to/four-reserved-events-exclusions.json MTDP_REQUIRE_HISTORICAL_ALIASES=1 python -m unittest -q research.mtdp.tests.test_historical_archive_coverage
python -m research.mtdp.historical_archive_coverage --root . --cache /path/to/four-reserved-events-exclusions.json --output /tmp/archive-coverage.json
cmp /tmp/archive-coverage.json research/mtdp/validation/historical-archive-cache-coverage-2026-11-23.json
```

The workflow repeats the eight tests, authenticates all 247 files and compares
its output bytes to the versioned report. No new corpus or engine evaluation is
part of this diagnostic. H13 waits for an independently qualified D1 candidate
before registering a new prospective Jass/Scan experiment.

## Remote validation

Code07f3706 passed all eight workflows. Run45154318351/job137623280590 passed
the eight tests with the required rebuilt cache and reproduced the versioned
report. ZIP artifact14807074068 was downloaded, its GitHub digest verified,
and the report/cache members checked. Evidence:
`validation/historical-archive-cache-coverage-ci-2026-11-23.json`.
