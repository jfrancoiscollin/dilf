# Jass root-order integration test

This preflight exercises the search mechanics in the [benchmark protocol](../JASS_MOVE_ORDERING_PROTOCOL.md) on four fixtures. The fixture ranking reverses a numeric Jass move order. The scientific benchmark still needs Scan rankings and an independent cohort.

Jass commit: `cfe07fce6385b980553a898e9651d53419589ebc`.
Validated with GCC 14.2.0 and CMake 4.4.4 in a Linux workspace.

From the root of DILF, with Jass checked out at that commit:

```sh
test "$(git -C "$JASS_ROOT" rev-parse HEAD)" = cfe07fce6385b980553a898e9651d53419589ebc
cmake -S "$JASS_ROOT" -B "$JASS_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DJASS_ENABLE_SIMD=OFF -DJASS_NATIVE=OFF \
  -DCMAKE_PROJECT_jass_INCLUDE="$PWD/research/mtdp/jass_preflight/targets.cmake"
cmake --build "$JASS_BUILD" --target mtdp_jass_preflight jass_tests -j 4
ctest --test-dir "$JASS_BUILD" -R '^jass_tests$' --output-on-failure
JASS_TRACE_ROOT=0 "$JASS_BUILD/mtdp_jass_preflight" > preflight.tsv
JASS_TRACE_ROOT=0 "$JASS_BUILD/mtdp_jass_preflight" > preflight-repeat.tsv
cmp preflight.tsv preflight-repeat.tsv
sha256sum preflight.tsv
```

Each invocation uses one thread, handcrafted evaluation, no time cap, and a fresh 1 MiB transposition table. The test asserts that each arm sees the same legal catalogue and covers all legal moves in the first depth-one attempt. At every ordered attempt the visited moves must be a prefix of the full schedule. The schedule moves up to three candidates to the front and fills the suffix in generated order. Jass reapplies the full schedule on each attempt. The two ordered arms share the suffix rule. The comparison with native order will also include the effect of overriding Jass's previous-best hoist.

The [two identical outputs](preflight.tsv) have SHA-256 `633db9880a1582dc50fa86ee6839260fa8132230fbf24049593a3314dee663d0`. All 36 searches respected their cap. Thirty reached it exactly. Six reached the depth ceiling of 64 first, all on the two-move fixture. The Jass test suite and all 643 DILF tests passed. The initial test run misidentified native retries because Jass resets attempt numbering at each depth. Checking both depth and attempt resolved the failure.

The full benchmark needs a pinned cohort and a verified mapping from DILF's canonical action identities to Jass's from/to/captured-set keys. In particular, capture-path order is absent from the Jass keys. Reject ambiguous mappings before scoring. Pin the evaluation artifact or handcrafted configuration before running the cohort, and retain both node-cap and depth-cap outcomes in the receipts.
