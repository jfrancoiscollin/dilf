# New named-arena replication: prospective total-budget control

**New study registration, before the event; not a position freeze.**

## Selection fixed before games

Select exactly **P1RUlfJc**, the official Lidraughts Hourly Blitz Arena,
scheduled for **18 November 2026, 20:00–20:57 UTC (21:00–21:57 Paris)**,
standard 10×10, 300 seconds + 0, arena system, created by `lidraughts`.
The [machine-readable registration](P1RUlfJc-preregistration.json) records a
pre-start metadata observation and its response hash. No games or scores from
this event were acquired for selection. The public observation had a positive
`secondsToStart` and the registration is being committed before the start.

This is a **named, prospectively selected event**, not a claim that it is the
first eligible event after the historical 14 November cutoff. The old
fFgE7oED study remains paused at its chronology gate and remains reserved.
Current calendar and finished-list sources do not recover its cutoff instant;
see [the verified source-gap audit](CANDIDATE_JASS_CATALOGUE_2026-11-18.md).
The new study avoids making an unprovable historical completeness claim by
fixing the event identity before games exist. It does not retrospectively
amend or certify the old cohort, and results must not be relabelled as its
confirmatory result or pooled with the archived 473 targets.

Keep this exact event regardless of eligible population, source changes or
outcomes. Cancellation, changed format, failed independence, unresolved legal
mapping or an empty cohort must be reported. Do not switch to a favourable
replacement. Any later event needs its own prospective registration.

## Frozen scientific question and method

Replicate [the total-budget protocol](TOTAL_BUDGET_TIEBREAK_PROTOCOL.md):
does native-order resolution of verified depth-one ties change ordinary
Scan regret compared with native Jass, after **all verification nodes** are
charged to the same total budget? Include native Jass, unchanged LCB and the
metered control on every common L/LCB target.

Use the current method at DILF `8d62f76fae1ccd9578927792e140e61e5fa2a494`,
Jass `cfe07fce6385b980553a898e9651d53419589ebc`, FMJD adapter
`0e5189fbb251bf5eaf2e613d0f878bb17c740311`, and the existing pinned Scan 3.1
build/configuration. The source ranking is Scan successor depth 12; the
separate target reference is successor depth 16. Use **10k, 50k and 200k total
nodes**, with **50k primary**. Verification is capped at 10% per position;
main search receives the remainder including fallback. Keep the existing
full-window/exact-return conditions, native-order tie rule, fresh tables,
root-trace accounting and depth-ceiling exception policy unchanged.
No target Scan value or archived winner enters selection or tie resolution.

The primary endpoint is ordinary regret(control) minus regret(native) at
50k total nodes, in the declared Scan units, with a whole-game bootstrap
interval (seed 20261113; 10,000 resamples). Report the paired denominator,
optimum hits, move agreement, changed-choice costs, categorical scores,
verification fallbacks, nodes per call, and every depth-ceiling exclusion.
Keep draws/mates and unavailable ordinary estimates explicit rather than
silently converting them to ordinary scores. Report the three arms and
all budgets, including null or adverse results. A single named arena is a
convenience sample; a within-arena interval does not establish generality
across tournaments.

## Acquisition and freeze gate

1. After 20:57 UTC, verify the event is finished and its format/ID/start match
   this registration. Download two final PDNs independently, compare bytes
   and record hashes, retrieval times and final metadata.
2. Restore the complete existing historical input inventory, including PC
   Blues, all prior benchmark exports/manifests and **the entire fFgE7oED
   export**. Preserve existing exclusions and quarantine policies. Exclude
   known public game IDs, complete duplicate trajectories and all confirmed
   prior FENs. Record the scope and limitations of ambiguous prior games;
   do not imply that unresolved continuations have been canonicalized.
3. Replay complete games under pinned FMJD rules. Quarantine whole games
   on ambiguity or invalidity; do not select an arbitrary capture path.
   Deduplicate trajectories before target selection. Use all novel quiet
   mover-man positions with both L/LCB matches, the unchanged source-order
   tie-break and PC Blues baseline; include an empty population. Preserve
   per-game provenance, first ply, source identities and every rejection.
4. Verify complete canonical-action/Jass-key bijections for all selected
   targets and both sources, including promotion flags. Reproduce the
   population, mappings and manifest under hash seeds 7 and 61.
5. Publish immutable input digests, exclusion inventory, all selected target
   rows and source mappings in a **freeze commit before any new scoring**.
   Generalizing the old fixed-ID replay CLI is allowed only to parameterize
   the event/digests and add this registered exclusion inventory; no tuning
   of selection or signatures after seeing the population or scores.
6. Only then produce Scan source/target receipts and paired Jass searches.
   Use accessible remote resources; request Jeff's PC only if the required
   engine/reference cannot actually execute remotely. Never spend paid
   resources or deploy/merge as part of this registration.

## Coordination

Reserve **the whole P1RUlfJc event**, its future games and target FENs, from D1
training, signature selection, dimension reduction and threshold tuning.
Keep fFgE7oED and its 78 targets separately reserved as before. D1 must not
use either event even if the eventual cohort is empty or fails a freeze gate.
No new signature/top-K campaign is registered here. Next foundation action:
prepare and test the fixed-ID/digest parameterization and added exclusion
inventory without changing selectors or collecting an incomplete final export;
then collect final metadata and paired exports after the scheduled finish and
run the freeze gates.
