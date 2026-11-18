# Named arena input gates: implemented and rehearsed before the event

Scope: prepare P1RUlfJc inputs without acquiring any of its games, selecting
its positions or running Scan/Jass searches. This does not freeze a cohort.
The [registered selection and method](NAMED_ARENA_TOTAL_BUDGET_PREREGISTRATION_2026-11-18.md)
remain byte-pinned and unchanged.

## Verified exclusion rehearsal

`named_arena_inputs registry` verifies the immutable registration, protocol,
CARZrQpl provenance, 247 archived FEN manifests/shards, and all historical raw
PDN hashes/game counts. It restores the two national-match PDNs from the
pinned adapter's `docs/parties/` directory rather than omitting them.
It includes the full fFgE7oED export, including its quarantined game identities
and token sequences. A clean pinned FMJD checkout and the actual imported
engine path are checked.

| Input quantity | Verified count |
| --- | ---: |
| PDN files | 22 |
| Recorded games | 4,375 |
| Public Lidraughts game IDs | 4,341 |
| Distinct normalized token-sequence fingerprints | 4,224 |
| Confirmed historical FEN union | 205,098 |
| Confirmed fFgE7oED prefix FENs | 14,170 |
| fFgE7oED whole-game quarantines retained | 5 |

The FEN union combines the existing archive with strictly verified prefixes
of fFgE7oED, PC Blues and the two national-match inputs. Every prefix stops
before its first unresolved move. The five fFgE7oED ambiguities remain at
46:89, 58:103, 94:120, 150:98 and 155:122. No ambiguous route is chosen, even
when alternate routes share a successor. No continuation beyond the first
ambiguity is inferred. The other prefix-replayed inputs had no ambiguity.

Token fingerprints normalize the initial FEN and parsed move tokens (including
capture-letter case); they **do not prove canonical board-trajectory equality**.
The complete trajectory guard, future population selection and live Jass
mapping remain required before freezing. The registry cannot certify
semantic independence by itself.

The full registry reproduced byte for byte under Python hash seeds 7 and 61:
SHA-256 `25b3ca1a6f0a096c264c8f136135a37fd7d5bb23c04af76a39b4915a611d192e`.
The [committed summary](P1RUlfJc-exclusion-inputs-summary.json) contains counts,
limitations and all five quarantine diagnostics. The existing candidate-replay
workflow now regenerates the full registry, checks that digest and preserves
it as `P1RUlfJc-exclusions.json` in its provenance artifact.

## Final-input refusal gate

`named_arena_inputs check-final` requires:

- The unmodified preregistration and protocol.
- A timezone-aware check time at or after **18 November 20:57 UTC**.
- Final metadata with literal `isFinished: true`, exact event ID, creator,
  standard variant, arena system, 300+0 clock, start and 57-minute duration.
  An explicit nonzero start countdown contradicting finished status is rejected.
- Two distinct export files, with identical nonempty bytes.
- Two acquisition receipts tied to the exact event URL, byte count and SHA-256,
  each retrieved after the scheduled finish and before the check, with distinct
  nonempty request IDs.

A copy saved under a second name is not evidence of a second HTTP acquisition;
the receipt comparison checks consistency, not independent external authenticity.
The actual downloader must issue two separate GETs and record them. Empty or
differing exports remain an acquisition failure to diagnose, never permission
to choose another arena or silently replace the population. An empty eligible
population after valid replay is retained by the registered selection policy.
Even successful input checks explicitly return `scientific_freeze: false`.
No population, legal replay or search-quality claim follows from this gate.

## Tests and reproduction

16 new regressions passed locally, including premature files, nonliteral
finished flags, event/format drift, same-file and different-byte inputs,
corrupt/reused/premature receipts, changed preregistration and strict ambiguity
prefix handling. Together with the three existing prospective gate modules,
**27 targeted tests passed**. The workflow includes all 27 explicitly.

```sh
PYTHONPATH="$PWD:$PWD/../draught-master" python -m research.mtdp.jass_benchmark.named_arena_inputs registry \
  --root . --history /tmp/mtdp-independent/previous-pdn \
  --reserved /tmp/mtdp-independent/mtdp-lidraughts-fFgE7oED.pdn \
  --adapter ../draught-master --output /tmp/mtdp-independent/P1RUlfJc-exclusions.json
python -m pytest -q research/mtdp/tests/test_named_arena_inputs.py research/mtdp/tests/test_candidate_jass_catalogue.py research/mtdp/tests/test_candidate_ambiguities.py research/mtdp/tests/test_prospective_candidate_replay.py
```

After the event finishes, the second command mode is:

```sh
python -m research.mtdp.jass_benchmark.named_arena_inputs check-final \
  --root . --metadata /tmp/final-metadata.json \
  --first /tmp/final-first.pdn --repeat /tmp/final-repeat.pdn \
  --download-log /tmp/final-downloads.json --output /tmp/final-input-check.json
```

The download log has `candidate.first` and `candidate.independent_repeat` objects,
each with `url`, `sha256`, `bytes`, `retrieved_at_utc` (UTC ISO timestamp) and
`request_id`. Those fields must come from actual separate post-finish requests.
The tests use explicitly synthetic future receipts, not acquired target games.

Initial HEAD `2c17363efbb3f8114a549327ae4df07ae1e6e142` had seven successful
workflows, including [candidate replay 44326403133](https://github.com/jfrancoiscollin/dilf/actions/runs/44326403133).
Its artifact `14437039139` has ZIP SHA-256
`93ac782a4ceb77ae73170cc037908d68173e2e6c9ace19f3778537e4074e4242`.
No equivalent job was active at the start of this rehearsal. CI of this new
implementation is checked separately after publication.

## Next foundation action

Connect the unchanged population/source selectors to this pinned registry and
the named-event input receipt, including canonical complete-trajectory rejection
and an event-parameterized Jass catalogue receipt. Reproduce the historical
fFgE7oED selection unchanged as a regression. Keep this preparation score-blind;
acquire the actual P1RUlfJc final metadata and paired PDNs **only after 20:57 UTC**,
then validate and publish the immutable position freeze before any scoring.
Both full events remain reserved from D1. No PC from Jeff is needed for this
input-stage preparation; no new best-move or equal-budget efficacy result exists.
