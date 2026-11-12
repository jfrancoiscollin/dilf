# Independent Jass benchmark cohort

The [preregistered benchmark](../JASS_MOVE_ORDERING_PROTOCOL.md) uses the
[17 October 2026 Weekly Rapid Arena](https://lidraughts.org/tournament/Z3s40c6H),
a completed international draughts event with a nominal 10+0 time control.
This cohort was selected and frozen before running Scan or Jass search on
its positions. The only source corpus is PC Blues. The manifest records one
source per target, chosen by lexicographic minimum of (source game ID, source
FEN) after requiring the same quiet-man signature and exact canonical legal
actions. A failed mapping excludes the pair without trying a second source.

Of the 66 exported games, 62 replayed as distinct trajectories. Four
duplicated a trajectory already loaded. Of 6,264 distinct target FENs,
60 also appeared in PC Blues and 158 more appeared in previous holdouts.
Of the 6,046 novel FENs, 4,084 received the quiet-man signature.

| Disposition of quiet candidates | FENs |
| --- | ---: |
| Terminal | 8 |
| Forced move | 6 |
| No PC Blues source with the same signature | 4,042 |
| Same signature but no identical legal set | 0 |
| Rejected by cross-engine mapping | 0 |
| Frozen targets | 28 |

The 28 targets appear in 17 target games. They use 24 source FENs with 12
selected source game IDs. Ten pairs also have the same typed radius-two
signature, recorded for secondary analysis. Coverage is 28/4,070 (0.69%)
among novel quiet positions with a genuine move choice. This single
tournament supplies the test positions. Positions from the same game and
positions sharing a source are related.

## Reproduction

Use the pinned draught-master and Scan checkouts from the
[original audit](../BEST_MOVE_BASELINE_2026-11-11.md#reproduction) and build
the [Jass legal catalogue](../jass_preflight/README.md#cross-engine-legal-move-mapping)
at the pinned Jass commit. The catalogue receipt in the manifest is specific
to the binary built with GCC 14.2.0 and CMake 4.4.4. Use the three PDN
exports below and check their SHA-256 values against the manifest before replay.
From the root of DILF:

```sh
for id in L4F4P5R8 eo66EN9z Z3s40c6H; do
  curl -fsSL --retry 2 --max-time 90 "https://lidraughts.org/api/tournament/$id/games" \
    -o "/tmp/mtdp-lidraughts-$id.pdn"
done
PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT" python -m research.mtdp.jass_cohort \
  --baseline data/exports/pcblues/pcblues_games.pdn \
  --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Bourges2-Seilh.pdn" \
  --exclude-previous "$DRAUGHT_MASTER_ROOT/docs/parties/Drancy-Mirepoix.pdn" \
  --exclude-previous /tmp/mtdp-lidraughts-L4F4P5R8.pdn \
  --exclude-previous /tmp/mtdp-lidraughts-eo66EN9z.pdn \
  --holdout /tmp/mtdp-lidraughts-Z3s40c6H.pdn \
  --jass-catalogue "$JASS_BUILD/mtdp_jass_legal_catalogue" \
  --output /tmp/mtdp-cohort.json
sha256sum /tmp/mtdp-cohort.json
```

Two freezes with the same binary gave identical output, SHA-256
`3c763000c9c07e4f1cc59b94bcc832971c48a60348ea9d6ea6e0aa8d5f7fd8f1`.
All 79 MTDP tests passed with the Jass catalogue enabled. The Jass suite
passed and the mechanical preflight reproduced its archived TSV byte for
byte.

The [benchmark report](RESULTS_2026-11-12.md) scores the frozen legal actions
with Scan 3.1 at successor depth 12. The three Jass arms use the preflight's handcrafted
evaluation and fresh 1 MiB TT, with one thread, no time limit and a depth
ceiling of 64. Use the manifest's action order for the canonical top three
and the target's Jass keys for both ordered arms. The complete scientific
comparison uses all 28 targets at each of the three node budgets.
