# Named-arena acquisition and publication gate

Engineering preparation only. P1RUlfJc remains the exactly named standard 5+0
arena registered before its 20:00–20:57 UTC start/finish window on 18 November.
No real target game, target score or new quality estimate was acquired here.
The earlier local acquisition/publication preparation had not reached the
research branch; these modules and tests are now being recorded and validated.

## Acquisition

`named_arena_acquisition` refuses before 20:57 UTC, before any HTTP request or
output creation. It verifies finished metadata and the registered identity,
creator, start, duration, variant and clock before requesting games. Each GET
has a unique request ID, timestamps, bytes, SHA-256 and retry ledger. Transport,
incomplete HTTP and malformed-response failures are retried four times. Up to
four divergent PDN pairs are retained and retried; no other arena is selected.
Existing directories are never overwritten. Event facts are saved while the
full metadata-response hash is retained without copying unrelated prose.

Acquisition success is not a scientific freeze. Two distinct matching files
and consistent independent-request receipts are checked by the existing gate.
No partial export is accepted for scoring, and empty eligible populations must
still be retained once valid full inputs pass the registered replay policy.

## Prepared bundle, exact-byte export and remote proof

`named_freeze_bundle prepare` runs the production proposal in fresh subprocesses
under hash seeds 7 and 61 and requires identical output bytes. It checks all
population/action mappings, registered references, budgets, analysis settings
and input/provenance bindings. Prepared manifest and publication envelope keep
`scientific_freeze: false` and `publication_required: true`.

The eleven exported files contain exact final inputs, protocol/registration,
proposal, reproduction receipts, provenance, manifest and publication inventory.
`export-tree` decodes raw UTF-8 bytes without newline conversion; CRLF, BOM and
Unicode survive JSON transport. An already occupied committed prefix is refused.
Publish these exact entries on a freshly read research head with a non-forced
lease. Do not normalize PDN bytes with `read_text()`.

Only `verify` may return a positive verification receipt. It fetches the explicit
research remote-tracking ref (not the shared FETCH_HEAD), requires the exact
freeze commit to be its ancestor, checks committed blobs and cross-hashes,
implementation ancestry/source fingerprints and the actual final-input gate.
A local-only commit is refused. Uncommitted working-tree changes do not alter
the verified snapshot. The execution adapter must require this receipt before
any target reference or search; a prepared manifest alone is insufficient.

## Synthetic rehearsal and current validation scope

`named_arena_rehearsal` uses a manufactured FEN and a PDN explicitly tagged
`Synthetic`, with in-memory HTTP and a scoped test clock. It uses the real
pinned FMJD oracle and Jass catalogue. The prescribed positive control is one
common L/LCB target with ten legal actions, never an independent game sample.
Production preparation, export and verification refuse synthetic artifacts.

The workflow executes the entire rehearsal in separate processes under seeds
7/61 and compares proposal, manifest and publication-envelope hashes. It also
checks refusal of synthetic scoring and preservation of raw CRLF bytes. These
integration results must be confirmed by the new CI run; they are not inferred
from the earlier interrupted local workspace. Reproduction is within the same
checkout/build; executable hashes may differ between compilers.

**59 targeted tests passed locally**, including 20 acquisition/publication
regressions. They cover premature network access, separate GETs, divergent-pair
preservation, transport retries/exhaustion, overwrite refusal, changed files,
proposals, budgets and action keys, synthetic rejection, exact byte export,
two hash-seed child invocations and failed-child refusal. A local isolated Git
remote tests rejection of unpublished commits, remote ancestor acceptance and
immunity to uncommitted edits. It is not a real cohort publication.

Starting HEAD `59618930d2cec66537d3275fbc6c94bbee61d157` had seven successful
workflows. Candidate run [44369549270](https://github.com/jfrancoiscollin/dilf/actions/runs/44369549270)
exposed artifact `14459370454`, published ZIP SHA-256
`d7c09fc8b6a7c873ad10d3b9dbb741e989997fca3a51f2924265fc6a86eda5f0`.
No equivalent run was active. The new candidate workflow contains all 59 tests
and the full synthetic integration; confirmation follows publication.

## Actual commands after confirmed completion only

Use unique output directories to preserve failed attempts. Restore the pinned
registry/index from the latest verified artifact or regenerate them.

```sh
python -m research.mtdp.jass_benchmark.named_arena_acquisition \
  --root . --output-directory /tmp/P1RUlfJc-final-UNIQUE
PYTHONPATH="$PWD:$PWD/../draught-master" python -m research.mtdp.jass_benchmark.named_freeze_bundle prepare \
  --root . --acquired /tmp/P1RUlfJc-final-UNIQUE \
  --registry /tmp/mtdp-independent/P1RUlfJc-exclusions.json \
  --index /tmp/mtdp-independent/P1RUlfJc-canonical-history.json \
  --adapter ../draught-master --jass ../jass \
  --executable /tmp/mtdp-catalogue-build/mtdp_jass_legal_catalogue \
  --output /tmp/P1RUlfJc-freeze-ready-UNIQUE
python -m research.mtdp.jass_benchmark.named_freeze_bundle export-tree \
  --root . --directory /tmp/P1RUlfJc-freeze-ready-UNIQUE \
  --prefix research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc
```

Publish the structured entries with their exact bytes, then verify the actual
published commit before any scoring:

```sh
python -m research.mtdp.jass_benchmark.named_freeze_bundle verify \
  --root . --directory research/mtdp/jass_benchmark/spatial-jass/replication/P1RUlfJc \
  --commit EXACT_PUBLISHED_SHA --output /tmp/P1RUlfJc-publication-verification.json
```

Next: connect the native/unchanged-LCB/metered-control execution adapter to this
verification and check the pinned Scan/Jass binaries, with synthetic node-budget
smoke checks only until the real freeze. Both fFgE7oED (entire event, 78 targets)
and P1RUlfJc (entire event/future FENs) remain reserved from D1 fitting, signature
selection and thresholds. No PC from Jeff is required for these input-stage
checks, and no new strategic-equivalence result is claimed.

## Confirmed integration evidence — 19:38 UTC

Commit `b7fb22ac88791573943d7b478512419ab0cbf85f` published the new tools.
D1 commits `6dafdc9` and `069d5c2` were preserved; the latter head has **seven
successful workflows**. The new D1 numerical-gates document was read; it is
still a proposal, with no D1 cohort or thresholds frozen by this relay.

Candidate [run 44381395324](https://github.com/jfrancoiscollin/dilf/actions/runs/44381395324),
job `135074404038`, confirms **59 tests passed** and the complete real-FMJD/Jass
synthetic rehearsal under seeds 7/61: one manufactured target, ten legal actions,
three in-memory HTTP requests, raw CRLF preserved, production validator refusal,
and `scientific_freeze: false`. Both processes produced identical digests:

| Payload | SHA-256 |
| --- | --- |
| proposal | `13b62ca816f3fb155b6e69fdb2f68ef51366035135bf521c4779318a642eb33f` |
| manifest | `cf5afc998605f8d743f59c040a61fadc143e4341ee33e69929087d64feaff9a6` |
| publication | `28549e9afb734ae528dacc5c13c0007ed2309b4b59b6a788620a353caa8e39a4` |

Artifact [14462853825](https://github.com/jfrancoiscollin/dilf/actions/runs/44381395324/artifacts/14462853825)
was downloaded: 6,823,874 bytes, SHA-256
`5b2130472bd92b9eabecde81c7a384d85a4cdbafd3a7997561fa654f81c54c8e`.
ZIP bytes, the two report hashes and every bundled inventory payload were checked
after download. The archive also contains the full historical registry/index.
The old fFgE7oED replay remains `e9de3a4c…118a16b`, 78 targets/46 sources/759
target actions; all original quarantines remain. Machine-readable evidence:
`named-freeze-rehearsal-ci-2026-11-18.json`.

These are engineering results, not a new best-move/regret estimate. No real
P1RUlfJc export or target score was acquired, and no real freeze was published.
The existing generic `jass_scan_reference` CLI accepts the cohort schema alone;
it must **not** be called directly on a prepared named bundle. The next adapter
must first verify the published snapshot and load its committed manifest, then
bind the pinned Scan binary/evaluation/configuration and both patched Jass
runners before any scoring or search. `metered_archive_gate` remains specific
to the old five-arena inventory; copying its archive acceptance condition would
not authorize this arena. Keep the registered 12/16 depths, three arms and total
budgets, including all failures/empty populations and depth-ceiling exceptions.
