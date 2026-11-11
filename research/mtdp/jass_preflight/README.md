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

## Cross-engine legal move mapping

The Jass exporter uses the same key format as the root schedule. DILF keeps
the full path, sorted captured squares and promotion in its canonical action.
The mapping checks the complete legal catalogue and rejects a position if two
DILF paths project to one key, a Jass key is duplicated, or either side reports
a different key or promotion. A Jass capture flag on an existing king is
normalized to match DILF's pawn-to-king promotion semantics. The exporter
echoes the position so the caller can check that both engines parsed the same board.

Using the same Jass build as above and draught-master at
`0e5189fbb251bf5eaf2e613d0f878bb17c740311`:

```sh
cmake --build "$JASS_BUILD" --target mtdp_jass_legal_catalogue -j 4
export MTDP_JASS_CATALOGUE="$JASS_BUILD/mtdp_jass_legal_catalogue"
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
python -m pytest -q research/mtdp/tests
python - <<'PY'
import os
from collections import Counter
from pathlib import Path

from pedagogy.game import state_to_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.jass_move_mapping import MoveMappingError, map_root_moves, read_jass_catalogues
from research.mtdp.pdn import read_games, validated_trajectory

engine = create_engine()
games = read_games(Path("data/exports/pcblues/pcblues_games.pdn"))
positions = {
    state_to_fen(state): state
    for game in games
    for _, _, state in validated_trajectory(game, engine)
}
counts = Counter()
catalogues = read_jass_catalogues(Path(os.environ["MTDP_JASS_CATALOGUE"]), positions.values())
for (fen, state), catalogue in zip(positions.items(), catalogues, strict=True):
    moves = engine.legal_moves(state)
    try:
        mapped = map_root_moves(moves, catalogue)
    except MoveMappingError as error:
        counts["rejected"] += 1
        print(fen, error)
    else:
        if not mapped:
            counts["terminal"] += 1
        else:
            counts["capture" if moves[0].is_capture else "quiet"] += 1
print(len(games), len(positions), sorted(counts.items()))
PY
```

On the 26 PC Blues games (PDN SHA-256
`025ad0a1a9ddcf508e3284eef65eb1cf76ebf7763d1241a127432f99eac3d8be`),
1,749 of 1,750 distinct positions had a complete mapping, including
1,313 quiet positions and 436 capture positions. The rejected position
`B:W7,28,40,41,42,44,45,46,47,48:BK50,2,3,4,6,9,10,15,16,25`
has the paths `50x39x22` and `50x33x22`. Both project to
`50x22x28x44` in Jass. The integration test also verifies that paths with the
same endpoints and different captured sets remain separate.

The 78 MTDP tests, 643 general DILF tests and Jass test suite passed. The
36-search preflight output matched the archived TSV byte for byte. PC Blues
was used here as an integration check. The independent benchmark cohort
and its search results are still pending.
