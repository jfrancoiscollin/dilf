# Jass initial-only ordering preflight

The [preregistered mechanistic check](../JASS_INITIAL_ONLY_PROTOCOL.md)
passes on synthetic fixtures. The scientific comparison on a third
independent event remains to be run.

In the pinned Jass search, the schedule edits the persistent root list.
A schedule entry for depth one alone would retain the altered list and
report invalid schedule applications at later depths. The
[experiment patch](initial-only.patch) runs the scheduled first window
against a copy of the root list. At depth two Jass starts with the generated
list and swaps its own previous best to the front. At subsequent depths it
applies the same native swap to the resulting list. Aspiration retries use
the current iteration's list. Search state (including TT, killer moves and
history) persists within each search. The native arm uses the unmodified
search path. Each arm uses a new 1 MiB TT, one thread and handcrafted evaluation.

The [complete trace](initial-only-trace.tsv.gz) records 609 root attempts
from 30 searches. The native arm and the two synthetic top-three arms
had the same legal moves and full depth-one coverage. The fixtures include
promotions and multi-captures with distinct captured sets. Each ordered
arm applied its schedule exactly once. The preflight reconstructed the
native previous-best swap after every completed depth and matched the
visited order at every subsequent attempt, including aspiration retries
and partial attempts. In 12 of the 20 seeded searches, the observed
depth-two order differs from what a persistent depth-one permutation
would have produced. Every search reached its exact node budget. The
two-move fixture ran at 10,000 nodes only because it can reach the depth
ceiling at higher budgets. The other three fixtures ran at 10,000, 50,000
and 200,000 nodes.

On the initial board at 10,000 nodes, the reversed fixture ranking
started with `35-30,34-30,34-29`. At depth two Jass began with
`35-30,32-27,33-28`: its depth-one best move followed by the native
suffix after the swap. These synthetic rankings contain no Scan or
tournament data.

## Reproduction

Use GCC 14.2.0 and CMake 4.4.4. From the root of DILF, apply the patch
to a clean, disposable checkout of
[Jass cfe07fc](https://github.com/jfrancoiscollin/jass/commit/cfe07fce6385b980553a898e9651d53419589ebc).

```sh
test "$(git -C "$JASS_ROOT" rev-parse HEAD)" = cfe07fce6385b980553a898e9651d53419589ebc
git -C "$JASS_ROOT" apply --unidiff-zero "$PWD/research/mtdp/jass_preflight/initial-only.patch"
cmake -S "$JASS_ROOT" -B "$JASS_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DJASS_ENABLE_SIMD=OFF -DJASS_NATIVE=OFF -DMTDP_JASS_INITIAL_ONLY=ON \
  -DCMAKE_PROJECT_jass_INCLUDE="$PWD/research/mtdp/jass_preflight/targets.cmake"
cmake --build "$JASS_BUILD" --target mtdp_jass_preflight mtdp_jass_legal_catalogue jass_tests -j 4
ctest --test-dir "$JASS_BUILD" -R '^jass_tests$' --output-on-failure
env -u JASS_EGDB_PATH -u JASS_EGDB_MTC_PATH JASS_TRACE_ROOT=0 \
  "$JASS_BUILD/mtdp_jass_preflight" > initial-only.tsv
gzip -dc research/mtdp/jass_preflight/initial-only-trace.tsv.gz | cmp - initial-only.tsv
MTDP_JASS_CATALOGUE="$JASS_BUILD/mtdp_jass_legal_catalogue" \
  PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT" python -m pytest -q research/mtdp/tests
```

Two executions produced identical traces. The uncompressed SHA-256 is
`db78374dcf629e161c636582060b718256c2d62dc8ad85f7566c48d0dce63a90`.
The original persistent-order preflight also reproduced its archived
output byte for byte with the experiment flag disabled. All 81 MTDP tests
passed with the Jass catalogue enabled, including the existing negative
test for a mismatched node receipt.
