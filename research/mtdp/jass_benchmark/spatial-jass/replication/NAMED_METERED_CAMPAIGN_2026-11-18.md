# Named three-arm execution — pre-score implementation

No selector, signature or tie policy changed. `named_metered_campaign` binds the
registered 10k/50k/200k native/unchanged-LCB/metered-control decisions to a freshly
verified published freeze. It loads the committed manifest, checks running
method blobs, and accepts only the complete depth-12 source packet from the same
freeze and reference implementation. There is no target-reference argument.
LCB ranking reuses `candidate_lists` unchanged. Current-root native keys must
exactly match the frozen catalogue, including equal-cardinality mismatches.
The existing `technical_smoke` executes all three arms with fresh searches and
charges every verification node to the control's residual total budget.
Depth-ceiling exceptions are retained, counted and excluded from paired estimates;
empty populations are recorded. Every raw position/budget receipt is preserved;
a technical exception preserves its identity and prevents a completion record.
Existing result directories are refused, never overwritten.

The pre-freeze build receipt `P1RUlfJc-runner-builds.json` pins Jass `cfe07fce6`,
exact patch/harness digests, configuration, compiler/CMake, patched-tree diff
hashes and actual executable bytes. Small gzip archives of the three Linux
binaries are saved in `P1RUlfJc-runtime/` so a later relay can restore exact bytes,
not silently substitute a compiler-dependent rebuild. The catalogue remains
unpatched; the probe applies `first-root-action.patch`; the main runner applies
`initial-only.patch` then `depth-one-winner.patch` with `--unidiff-zero`.

Rebuild in three disposable pinned Jass checkouts with:

```sh
cmake -S JASS_CHECKOUT -B BUILD -DCMAKE_BUILD_TYPE=Release \
  -DJASS_ENABLE_SIMD=OFF -DJASS_NATIVE=OFF \
  -DCMAKE_PROJECT_jass_INCLUDE=ABS_DILF/research/mtdp/jass_preflight/targets.cmake
cmake --build BUILD --target mtdp_jass_metered_probe -j 2
```

For the catalogue use target `mtdp_jass_legal_catalogue`. For main add
`-DMTDP_JASS_INITIAL_ONLY=ON` and target `mtdp_jass_benchmark` after applying the
main patches. The build receipt records this passage's compiler and file hashes;
a different build is not accepted by the frozen hash check. Restore archived
executables with gzip decompression and executable permission when exact bytes
are required. Verify every decompressed SHA before use.

Local validation: **107 targeted tests passed**, including source-only dispatch,
foreign publication/target-score rejection, fixed budgets, exact build binding,
empty population, ceiling retention, failure preservation and no overwrite.
Positive dispatch tests use fake engines; they do not constitute cohort results.
Actual pinned Jass initial-position engineering controls passed all three budgets,
with 100 verification nodes charged each time and exact total-node equality;
raw receipts in `P1RUlfJc-runner-initial-smoke.json`. CMake was initially absent,
installed as `cmake==4.4.5` in the existing environment, and builds were retried
successfully; no external paid resource or Jeff PC was needed.

PR head at start `e828dcf942004e340997c62e67bec996506e90ae`: 7/7 workflows success.
Candidate run `44393253399`, artifact `14468899048`, ZIP digest
`e5672f6d9411aa3210a0f06cc9f8c692d649eb4bd78adc09aabd7025241bed0e`
(metadata checked); no equivalent queued/running research job at the start.
Only unrelated historical `ci`/`downstream-compat` jobs were queued.
The new code/workflow awaits its own CI confirmation.

P1RUlfJc final metadata passed after the registered finish: 148 players, official
standard 300+0, starts 20:00 UTC, duration 57 minutes, `isFinished=true`.
Two separate GETs agree exactly: 272395 bytes, PDN SHA-256
`c1c23993b39da11442e2f4bc8cb5cbf8f9fb2713463be5b981d95a190cd68439`.
This is acquisition only: population, complete-game exclusions, FMJD replay,
Jass mappings, two-seed reproduction and published freeze remain required before
source or target scoring. No target scores or Jass target searches have been run.

After verified freeze and source scoring only:

```sh
python -m research.mtdp.jass_benchmark.named_metered_campaign \
  --root . --directory research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc \
  --commit EXACT_FREEZE_SHA --source /tmp/P1RUlfJc-source.json \
  --probe /tmp/mtdp-probe --main /tmp/mtdp-main --output /tmp/P1RUlfJc-decisions-UNIQUE
```

Publish decision receipts before quality analysis. Use the independent depth-16
target reference and the registered whole-game 10000-resample seed-20261113
bootstrap, primary 50k, ordinary integer Scan-unit regret and explicit categories.
This is a named convenience arena, not a multi-tournament generalization or an
Elo test. All fFgE7oED and P1RUlfJc games/FENs remain reserved outside D1.
