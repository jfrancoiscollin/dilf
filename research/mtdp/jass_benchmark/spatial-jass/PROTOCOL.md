# Prospective Jass comparison of LCB and exact legal actions

The [three-event replication](../eighth-replication/scan-results/RESULTS_2026-11-12.md)
and its [depth-18 check](../eighth-replication/scan-results/depth18/RESULTS_2026-11-12.md)
found similar best-of-three regret for LCB and L on common targets.
This pilot tests whether the two source-selection rules lead to
different Jass choices under identical node budgets.

## Cohort and freeze

Select the first eligible completed standard FMJD 5+0 arena starting
at or after **2026-11-12 23:00 UTC**, in chronological order. The
[initial listing](initial-listing.json) records KXaMpuNe as the first
scheduled candidate (23:00–23:57 UTC), followed by uG0fGZzB
(02:00–02:57 UTC on 13 November). Archive chronological snapshots
and finished detail responses. An earlier pending candidate must be
resolved before moving on. Record any rejection using metadata,
export availability, independence or replay, before inspecting scores.

Reuse the eighth study's FMJD eligibility and L/LCB definitions.
Restore the seventh and all three eighth-study freezes and their
exclusion PDNs/manifests. Confirm two independently fetched exports
match, validate game IDs and replay, and reproduce the new freeze
under two Python hash seeds. Use all positions matched by LCB,
which are also matched by L. Select each arm's source by the existing
minimum (PC Blues game ID, ply, FEN) rule. Require exact Jass/FMJD
legal action mapping. Publish the freeze and derived benchmark
manifest before scoring. Stop on a mapping mismatch and investigate
it before interpreting any result.

## Scores, searches and analysis

Use the pinned Scan 3.1 configuration from the eighth study, with
successor depth 12 for source rankings and 16 for target evaluation.
Rank the first three by score, breaking ties by the existing
bytewise Jass key convention in both arms. Publish source-change
and ordered-prefix-change counts before running Jass. Keep all
common targets and report the changed-prefix subset separately. If
the pilot has zero changed prefixes, report the observed denominator
and stop the LCB-versus-L comparison. Do not substitute a tournament
based on scores or observed prefix changes.

Compare LCB, L and native Jass on the same positions with 10,000,
50,000 and 200,000 nodes per arm. Use pinned Jass cfe07fc plus the
archived [initial-only patch](../../jass_preflight/initial-only.patch).
Apply the transferred order at depth one and use the engine's
adaptive order thereafter. Use one thread, handcrafted evaluation,
a fresh 1 MiB transposition table and no external tablebases. Shuffle
arm order with seed 20261113. Require identical legal actions,
observed order matching the configured schedule, and exact node
consumption. Diagnose technical errors before rerunning. Record any
case that legitimately reaches the depth ceiling before the budget
and report the affected pilot comparison as incomplete.

The primary endpoint is the paired mean difference in ordinary
depth-16 Scan regret of Jass's selected move, LCB minus L at
50,000 nodes on all common targets. The other budgets, native
comparison and changed-prefix subset are secondary. Report owning
games, changed moves, optimum hits, category transitions and
whole-target-game bootstrap intervals. Read one-arena intervals as
within-arena uncertainty. A pilot with few changed prefixes can
measure feasibility and the observed effect on those cases.

## Reproduction

From the DILF root, follow the eighth study's
[acquisition procedure](../eighth-replication/README.md#continue-acquisition)
to build the candidate log from the earlier snapshots, the initial
listing here and fresh snapshots. Use the
[freeze command](../eighth-replication/README.md#freeze-the-next-finished-candidate)
with `--spatial-jass` and three ordered `--previous-freeze` arguments
(xAnBIxHN, MoXhmT9b, MIDBy9dl). Use a pinned Jass catalogue and the
[initial-only runner build](../../jass_preflight/INITIAL_ONLY_RESULTS_2026-11-12.md#reproduction)
with target `mtdp_jass_benchmark`.

```sh
module=research.mtdp.jass_benchmark.spatial_jass
export PYTHONPATH="$PWD:$DRAUGHT_MASTER_ROOT"
python -m "$module" prepare --provenance "$FREEZE/provenance.json" \
  --catalogue "$JASS_CATALOGUE" --manifest "$RUN_DIR/manifest.json"
# Publish the reproducible freeze and manifest before scoring.
for role in source target; do
  case "$role" in source) depth=12 ;; target) depth=16 ;; esac
  python -m research.mtdp.jass_scan_reference --role "$role" --depth "$depth" \
    --manifest "$RUN_DIR/manifest.json" --scan "$SCAN_ROOT/scan_linux" \
    --output "$RUN_DIR/$role.json"
done
python -m "$module" diagnose --manifest "$RUN_DIR/manifest.json" \
  --source "$RUN_DIR/source.json" --output "$RUN_DIR/source-diagnostic.json"
# Publish the source diagnostic before Jass.
python -m "$module" run --manifest "$RUN_DIR/manifest.json" \
  --source "$RUN_DIR/source.json" --target "$RUN_DIR/target.json" \
  --diagnostic "$RUN_DIR/source-diagnostic.json" \
  --runner "$JASS_BUILD/mtdp_jass_benchmark" --output "$RUN_DIR/jass-results"
```

The mechanical preflight used one archived eighth-study FEN with two
different prefixes. All nine searches consumed exactly their node
budgets and passed the root-order trace checks. The runner digest was
`cf6b992de7dee3fa859522357dbc31fdbdd184d5432f8d1ef454671abc37535c`.
The new arena's export, freeze, scores and searches are pending.
Next action: verify KXaMpuNe after 23:57 UTC and freeze it if eligible.
