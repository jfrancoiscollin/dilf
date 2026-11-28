# Named-arena replay and historical trajectory gate

**Engineering preparation before P1RUlfJc finishes. No target games acquired,
no position freeze, no new Scan/Jass search outcome.** The registered method,
reference depths and total node budgets are unchanged. Both fFgE7oED and
P1RUlfJc remain reserved from D1 signature selection and training.

## Shared selection without changing the historical result

The existing L/LCB population selector is now a shared `select_population`
function in `prospective_candidate_replay.py`. It retains the exact source
ordering, novelty exclusions, canonical action tuples and common-target rule.
Both Python hash seeds 7 and 61 reproduced the complete historical fFgE7oED
report byte for byte, including all 78 targets and their source assignments:
SHA-256 `e9de3a4cfdf44e6f33e77681290fc0ccbc23e5b9e2e02992b9d30229d118a16b`.
This is a regression check, not certification of its unresolved chronology.

## Full historical board-trajectory index

`named_arena_replay history` verifies the pinned 22-PDN registry and the raw
source hashes, then replays all 4,375 recorded games with the pinned FMJD oracle.
A canonical fingerprint hashes the newline-separated FEN sequence, including
the initial state. Only completely legal games receive a trajectory fingerprint.

| Quantity | Reproduced count |
| --- | ---: |
| Historical source PDNs | 22 |
| Recorded games | 4,375 |
| Distinct complete board trajectories indexed | 4,051 |
| Complete duplicate trajectories | 151 |
| Whole-game quarantines | 173 |
| Distinct legally verified historical prefix FENs | 411,980 |

All 173 quarantines are retained. Their verified prefixes contribute only to
historical exclusions; no canonical fingerprint is assigned and no state after
an ambiguous or invalid move is inferred. This includes the five previously
diagnosed fFgE7oED games. The full prefix set contains the earlier 205,098-FEN
registry, so the proposal excludes the union of both sets. This extends known
historical-state coverage before any new target population or score is seen;
it does not tune a signature or change the registered population selector.

The [index summary](P1RUlfJc-trajectory-index-summary.json) pins the full JSON:
SHA-256 `eafd1e7b1c447b69f96d307b38a1c7c0fbd8fa9dd9b68f8afe555e3faa02d1b6`.
Two independent executions with hash seeds 7 and 61 matched byte for byte.
The workflow regenerates this index, checks its digest, and preserves
`P1RUlfJc-canonical-history.json` in the existing provenance artifact. The
index records every game's status and input digests. Normalized token hashes
remain a complementary guard for rejected source games, not a substitute for
canonical complete board trajectories. Unknown continuations stay unknown;
these exact checks do not prove the absence of every form of related-game bias.

## Proposal entry point

`named_arena_replay proposal` first calls the final-input gate, before loading
any target PDN or invoking an engine. It has no production clock override.
The real-clock entry point was confirmed closed before 20:57 UTC using missing
target-file paths: no target game file was read. It also requires clean pinned
FMJD/Jass checkouts, a clean implementation checkout, the unchanged PC Blues
baseline, the fixed historical registry and the byte-pinned canonical index.

For each target game it rejects, in order, known public IDs, normalized old
token sequences, illegal/ambiguous full replay, complete historical board
trajectories and duplicates inside the event. Positions and ownership records
are emitted **only after the whole target game passes**. A valid prefix of a
quarantined target game never becomes a target position. Within-event duplicates
cannot inflate owning-game counts. Empty resulting populations are retained.

The shared selector then removes all confirmed historical FENs and applies the
unchanged L/LCB source rule. The pinned Jass exporter checks complete action/key
bijections for all selected targets and both sources. The proposal contains
benchmark rows, source-target action pairs, owning games and target plies,
per-game statuses, mapping digests, implementation commit/file hashes, engine
pins and the registered analysis settings. Source/target Scan successor depths
remain 12/16; total node budgets remain 10k/50k/200k, primary 50k, with the
registered verification cap. No reference score enters this preparation.

**The output is a proposal, with `scientific_freeze: false`, not an input that
may immediately be scored.** After the event finishes, acquire two final
exports with genuine separate-GET receipts, run this entry point under both
hash seeds, inspect all exclusions/mappings and publish immutable provenance
and a frozen manifest before generating any new scores or search receipts.
The proposal schema must be finalized as the new study's frozen input rather
than silently reusing the archived-arena scoring inventory.

## Reproduce and test

```sh
PYTHONPATH="$PWD:$PWD/../draught-master" PYTHONHASHSEED=7 python -m research.mtdp.jass_benchmark.named_arena_replay history \
  --root . --registry /tmp/mtdp-independent/P1RUlfJc-exclusions.json \
  --history /tmp/mtdp-independent/previous-pdn \
  --reserved /tmp/mtdp-independent/mtdp-lidraughts-fFgE7oED.pdn \
  --adapter ../draught-master --output /tmp/mtdp-independent/P1RUlfJc-canonical-history.json
python -m pytest -q research/mtdp/tests/test_named_arena_replay.py research/mtdp/tests/test_named_arena_inputs.py research/mtdp/tests/test_candidate_jass_catalogue.py research/mtdp/tests/test_candidate_ambiguities.py research/mtdp/tests/test_prospective_candidate_replay.py
```

After 20:57 UTC only, with verified final inputs and a clean committed checkout:

```sh
PYTHONPATH="$PWD:$PWD/../draught-master" PYTHONHASHSEED=7 python -m research.mtdp.jass_benchmark.named_arena_replay proposal \
  --root . --registry /tmp/mtdp-independent/P1RUlfJc-exclusions.json \
  --index /tmp/mtdp-independent/P1RUlfJc-canonical-history.json \
  --metadata /tmp/final-metadata.json \
  --first /tmp/mtdp-lidraughts-P1RUlfJc.pdn --repeat /tmp/final-repeat.pdn \
  --download-log /tmp/final-downloads.json \
  --adapter ../draught-master --jass ../jass \
  --executable /tmp/mtdp-catalogue-build/mtdp_jass_legal_catalogue \
  --output /tmp/P1RUlfJc-freeze-proposal.json
```

**39 targeted tests passed locally**, including 12 new regressions: alternate
explicit routes with the same complete board trajectory, reidentified historical
games, atomic target quarantine, duplicate ownership, reserved IDs/tokens,
empty catalogues, source-order/exclusion stability, complete action mapping,
final-gate ordering, altered historical index, and historical prefix retention.
These are synthetic controlled-oracle fixtures; the full historical index and
legacy regression above also ran with the real pinned FMJD engine. The future
production proposal has not run past its time gate and is not claimed tested
on independent target games.

Initial HEAD `49280b69eccb2c087f800edccb277102c429ca61` had seven successful
workflows. Artifact `14438494531` of [run 44330609290](https://github.com/jfrancoiscollin/dilf/actions/runs/44330609290)
had published ZIP digest `70dd568077cc8861cda0a9dc13b524c52b842ed9d8195e9ec7ac5f8b77f807b6`.
No equivalent job was active at the start. New implementation CI is checked
after publication. No PC from Jeff is required for this preparation.

## Next action

Before the scheduled finish, prepare/rehearse the genuine HTTP acquisition
receipts and a fully synthetic end-to-end proposal/freeze-publication check.
After 20:57 UTC, confirm actual completion, acquire the two final PDNs and
metadata, reproduce and publish the frozen population before scoring. Preserve
both D1 reservations and every old quarantine. Do not run a partial-event
export or reinterpret this historical engineering exercise as independent
best-move evidence.
