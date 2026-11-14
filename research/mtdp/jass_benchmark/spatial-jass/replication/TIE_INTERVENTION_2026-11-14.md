# Controlled replay of the depth-one tie winner

On the 48 verified LCB/native ties, commit the original native
winner after the unchanged LCB depth-one window. The experiment
requires the forced move to be legal, searched to completion and
equal to the winning returned score. An independent full-window
probe in the previous audit established the tie before intervention.

The patch feeds the new winner into normal Jass bookkeeping,
including the depth-one root transposition entry and the
depth-two move order. It leaves the original depth-one visit order,
action log, score and node count intact. Each search uses
one thread, a fresh table and exactly 50,000 nodes.

| Positions | Native depth-two order reproduced | Native final move reproduced |
| --- | ---: | ---: |
| All 48 depth-one ties | 48 | 48 |
| 20 originally different final moves | 20 | 20 |

On the 20 original final disagreements, the forced arm found
five Scan optima, as native did, compared with three with the
original LCB winner. Mean Scan regret was 8.35 centimen with
the forced winner and 20.15 with the original LCB winner.
This intervention demonstrates that changing the committed winner
and its ordinary downstream bookkeeping was sufficient to recover
the native choices on this selected sample.

## Reproduction

From the repository root, use a disposable Jass checkout and build
directory. Use GCC 14.2.0 and CMake 4.4.4, as in the
[initial-only benchmark](../PROTOCOL.md#reproduction).

```bash
test "$(git -C "$JASS_ROOT" rev-parse HEAD)" = cfe07fce6385b980553a898e9651d53419589ebc
git -C "$JASS_ROOT" apply --unidiff-zero "$PWD/research/mtdp/jass_preflight/initial-only.patch"
git -C "$JASS_ROOT" apply --unidiff-zero "$PWD/research/mtdp/jass_preflight/depth-one-winner.patch"
cmake -S "$JASS_ROOT" -B "$JASS_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DJASS_ENABLE_SIMD=OFF -DJASS_NATIVE=OFF -DMTDP_JASS_INITIAL_ONLY=ON \
  -DCMAKE_PROJECT_jass_INCLUDE="$PWD/research/mtdp/jass_preflight/targets.cmake"
cmake --build "$JASS_BUILD" --target mtdp_jass_benchmark
rep=research/mtdp/jass_benchmark/spatial-jass/replication
python -m research.mtdp.jass_benchmark.spatial_tie_intervention \
  --replication "$rep" --runner "$JASS_BUILD/mtdp_jass_benchmark" \
  --output /tmp/mtdp-tie-intervention.json
cmp "$rep/tie-intervention.json" /tmp/mtdp-tie-intervention.json
```

Both hash seeds reproduced the receipt byte for byte. Without the
intervention the patched runner reproduced the two archived searches
on all 48 positions apart from elapsed time. An invalid preferred move
was rejected.

Next, freeze a control that resolves depth-one ties using the native
move order with the LCB visit order, without supplying archived native
winners. Validate the resulting tie choices against full-window probes
and measure the choice and node-cost effects across all 473 positions.
