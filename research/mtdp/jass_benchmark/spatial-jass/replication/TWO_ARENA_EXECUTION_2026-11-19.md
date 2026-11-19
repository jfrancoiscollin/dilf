# Two-arena reference and three-arm execution adapter

Prepared before the joint final-input gate19 November02:57UTC/03:57Paris.
No new-arena game/FEN or reference score has been read. Initial PR43 draft head
bc5723b:7/7 workflows successful, candidate44446506371, artifact14493482782
metadata reviewed (ZIP SHA888b5f3644d63e089fb9b1984f2036f5a873c8701e18def40e64a645ac985223).
No equivalent actual two-arena campaign is queued/running; CI uses engineering
fixtures/old historical inputs only.

`two_arena_execution` uses the joint remote verifier before engine or output
access. All execution-method bytes must already exist unchanged in the freeze
commit. It reuses the original full action scoring, Scan fingerprint checks,
Jass build receipt, source ranking, metered smoke and node-accounting validators.
No P1 fixed-ID module/global/clock or scientific selector is modified.

Three explicit reference kinds are fixed: source12 (only Jass ranking input),
source16 (geometry only, primary_source_usable=false), target16. Complete action
catalogues are scored; common sources across events are scored once. Arena
membership, all targets/sources and frozen masks remain in the joint manifest.
Relabelling source16 cannot pass the fixed-depth12 validator.

Campaign accepts only a source12 packet bound to this exact published freeze
and execution method. It executes both events at10k/50k/200k, three arms per
position, exact existing10% verification cap, with fresh engine searches. Every
receipt is validated for total-node accounting, legal winner, pairing and depth
ceilings before being saved. Failed identities/errors remain on disk; no source
or event is replaced. Empty arenas and all budgets stay in the completion
report. The output retains source12, plan and an inventory of every decision.

Target16 additionally requires an exact **published** source12/Jass decisions
commit/prefix, descendant of the freeze and ancestor of the freshly observed
research head. It verifies every inventory blob, source12 packet and all
position/budget receipts. An incomplete, local-only or foreign campaign cannot
open target scoring. Publish the entire campaign directory before target16.
Geometry source16 is a separate reference packet and never a Jass prefix input.

**204 local foundation tests pass**, including13 new execution contracts:
remote-proof ordering, both source arms/deduplication, cross-arena target alias,
kind/depth separation, published decision prerequisites before target engine,
empty references/campaigns, all budgets/arenas, missing decision inventory and
budget tampering. New CI is pending publication. Scan binary/eval/ini pins were
restored and checked. Archived Jass probe/main hashes match the frozen build.
A standard initial-position startup test (not cohort evidence) confirms native,
LCB and control all exhaust10k/50k total nodes; control100verification+9900/49900
main nodes. Scan12 initial reference returned-1 integer unit. Startup receipt
`two-arena-runtime-startup-2026-11-19.json` is explicitly engineering-only.

After the real joint freeze is published/verified:

```sh
python -m research.mtdp.jass_benchmark.two_arena_execution reference \
  --root . --prefix JOINT_BUNDLE_PREFIX --commit JOINT_FREEZE_SHA \
  --adapter ../draught-master --scan ../scan/scan_linux \
  --kind source12 --output /tmp/joint-source12-UNIQUE.json
python -m research.mtdp.jass_benchmark.two_arena_execution campaign \
  --root . --prefix JOINT_BUNDLE_PREFIX --commit JOINT_FREEZE_SHA \
  --source /tmp/joint-source12-UNIQUE.json --probe PINNED_PROBE --main PINNED_MAIN \
  --output /tmp/joint-decisions-UNIQUE
# Publish every decision-directory file to a fresh-head leased research commit.
python -m research.mtdp.jass_benchmark.two_arena_execution reference \
  --root . --prefix JOINT_BUNDLE_PREFIX --commit JOINT_FREEZE_SHA \
  --adapter ../draught-master --scan ../scan/scan_linux \
  --kind source16 --output /tmp/joint-geometry-source16-UNIQUE.json
python -m research.mtdp.jass_benchmark.two_arena_execution reference \
  --root . --prefix JOINT_BUNDLE_PREFIX --commit JOINT_FREEZE_SHA \
  --adapter ../draught-master --scan ../scan/scan_linux --kind target16 \
  --decisions-commit FULL_PUBLISHED_DECISIONS_SHA --decisions-prefix DECISIONS_PREFIX \
  --output /tmp/joint-target16-UNIQUE.json
```

Next: after BOTH actual finished/format-conforming metadata records and the
joint clock, acquire four final exports, reproduce/publish/verify the joint
population, run source12 and all decisions, publish those before target16;
prepare the fixed stratified whole-game analysis before outcomes. Keep the
registered Scan16/16 geometry, full-signature stratum/complement and whole
population, all tied optima and ordinary/categorical regret cases, primary50k
and arena-specific plus pooled paired estimates. All four entire events remain
reserved outside D1. No D1 campaign or paid computation started. Jeff's PC is
not needed for these accessible remote resources.
