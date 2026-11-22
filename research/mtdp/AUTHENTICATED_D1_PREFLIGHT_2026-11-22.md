# Authenticated historical inputs for D1 structural preflight

H13 input bridge only. No new cohort, signature, top-K evaluation, target scores,
or independent qualification. D1 modules and the four event reservations remain
unchanged.

`audit_authenticated_corpus(rows, sources, root=..., adapter=...,
historical_cache=...)` first authenticates the existing full cache by its exact
SHA-256, then pins the FMJD checkout/import using the existing `checked_engine`.
It invokes the H13 whole-export source/alias screen, canonical FEN exclusion,
PDN membership proof and complete legal trajectory screen. It compares the three
D1 declared hashes to source bytes, canonical FEN and the complete legal replay
before calling D1's unchanged `corpus_admission.audit` with derived exclusions.
No caller-supplied proof, exclusion list or engine is accepted by this entry point.

The three additional hash fields are removed only from the copy passed to the
older closed manifest schema. All other fields remain, so unknown fields and
nested target-outcome fields still trigger the existing refusals. The bridge
currently supports the older train/test partitions, not D1's additional
validation label; an unsupported label fails closed.

Hash contracts:

- Raw: the exact source PDN SHA-256, as in the content-addressed game ID.
- Canonical position: SHA-256 of UTF-8 `canonical_fen(fen)`, **without newline**.
- Complete trajectory: the existing legacy FEN serializer with its original
  king ordering and newline contract; no hash is redefined.

The authenticated cache yields 25 source digests, 4,790 public game IDs,
4,468 complete trajectory digests and 452,526 canonical position digests. The
compact sorted-key JSON of this derived registry, with a terminal newline,
hashes to `ccc7ee399ed496c104c4ee2f870d91b042b1adcaf1ad32c5369cf6a5ecb15ddd`.
The summary is in `validation/authenticated-d1-exclusion-export-2026-11-22.json`
and its exact hash/counts are checked against the real cache in tests.
Public game IDs alone do not equal content-addressed IDs; the whole-export alias
screen and raw/trajectory/FEN exclusions are retained for that reason.

Even a structural pass leaves external event identity, historical completeness,
independence and scientific freeze false. In particular, forged event labels do
not make an old PC Blues game eligible. The real pinned-engine negative test
rejects it on canonical historical occupancy before admission.

Reproduce with Python 3.11+ and pytest, using the exact existing historical cache
and `draught-master@0e5189fbb251bf5eaf2e613d0f878bb17c740311`:

```bash
export MTDP_HISTORICAL_FEN_CACHE=/path/to/four-reserved-events-exclusions.json
export MTDP_HISTORICAL_ADAPTER=/path/to/draught-master
export MTDP_REQUIRE_HISTORICAL_ALIASES=1
export PYTHONPATH=.:$MTDP_HISTORICAL_ADAPTER
python -m pytest -q research/mtdp/tests/test_authenticated_corpus_bridge.py research/mtdp/decision_equivalence/test_corpus_admission.py
```

The existing prospective-candidate workflow also runs the new tests with its
reconstructed exact cache and pinned adapter. No new workflow/campaign is added.

Next: D1 can use this bridge for its independently sourced candidate admission
work, while separately authenticating event/tournament ownership. H13 should
wait for a concrete D1 candidate to pass its independent evaluation gate before
registering a new Jass/Scan campaign, per
`FULL_RESIDUAL_SCAN16_RECONCILIATION_2026-11-19.md`. Do not reopen target scoring
on any of the four already scored reserved events.
