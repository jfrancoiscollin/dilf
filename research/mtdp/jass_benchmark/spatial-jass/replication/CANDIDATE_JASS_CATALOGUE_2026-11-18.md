# Reserved candidate: pinned Jass action gate and chronology gap

Status: **legal-action check passed locally and in CI; chronology unresolved; no freeze
or scoring**. This is an independent technical prerequisite, run while
historical chronology sources are being investigated. It does not waive the
chronological gate or duplicate a D1 signature/top-K experiment.

## Verified action catalogue

The candidate report was recovered from [run 44315083910](https://github.com/jfrancoiscollin/dilf/actions/runs/44315083910),
artifact `14431772840`. The downloaded ZIP matched the published SHA-256
`c024ec5735b882a8819378e0b3b56968f8b35c6f34f28b1440784866057e5a57`.
Its `candidate-replay.json` has SHA-256
`e9de3a4cfdf44e6f33e77681290fc0ccbc23e5b9e2e02992b9d30229d118a16b`.
The new gate refuses any different input bytes.

Jass `cfe07fce6385b980553a898e9651d53419589ebc` was built with
CMake 3.31.6, Release, `JASS_ENABLE_SIMD=OFF`, `JASS_NATIVE=OFF`, using the
existing DILF `legal_catalogue.cpp` target and **no experiment patch**.
The FMJD oracle is `draught-master`
`0e5189fbb251bf5eaf2e613d0f878bb17c740311`. Both tracked checkouts were clean;
the FMJD import path was checked against that checkout.

| Quantity | Verified count |
| --- | ---: |
| Candidate targets | 78 |
| Distinct selected PC Blues source positions, both arms combined | 46 |
| Distinct positions checked | 124 |
| Target action occurrences | 759 |
| Action occurrences across all distinct positions | 1,211 |
| Catalogue or source/target mapping mismatches | 0 |

Every Jass catalogue is a complete bijection with FMJD canonical actions
(route, captured squares, **promotion** flag). Every target also matches its
committed replay action list and the action-to-Jass-key mapping of both selected
L and LCB sources. These are legal-action checks, **not successor-state,
best-move or minimax equivalence**. No node budget was consumed by a search;
no Scan scores or Jass winners were requested.

The [per-position receipt](fFgE7oED-jass-catalogue.json) records FEN, action count,
SHA-256 of each sorted canonical-action/key mapping, pinned input revisions and
local executable digest. Python hash seeds 7 and 61 produced identical JSON.
Eleven targeted tests passed locally, including rejection of replay corruption,
incomplete catalogues and source/target disagreement despite individually valid
catalogues. The updated existing candidate-replay workflow builds the same
exporter, recomputes this receipt and compares every field except the
compiler-dependent executable hash. Its own executable hash is preserved in
the artifact. CI confirmed on descendant HEAD `ae3e6646511d71ce6f88c3e7e236804c6b95d9d8`: all seven workflows succeeded. The [candidate run 44324826343](https://github.com/jfrancoiscollin/dilf/actions/runs/44324826343) executed 11 tests and reproduced all 124 position mappings and 759 target actions. Artifact `14436224802` has ZIP SHA-256 `90288b96c19e73742402ab68ed75b2bcfb9588553054f9e32809d2f4496e46f4`. The original run on `8d62f76f` was cancelled by concurrent D1 commits; the equivalent descendant run was followed instead of duplicated.

## Reproduce without scoring

Run the updated `.github/workflows/mtdp-preregistered-candidate-replay.yml`,
which fetches and hashes all prior inputs and rebuilds `candidate-replay.json`.
Its new gate is equivalent to this command from the DILF root:

```sh
PYTHONPATH="$PWD:$PWD/../draught-master" python -m research.mtdp.jass_benchmark.candidate_jass_catalogue \
  --replay /tmp/mtdp-independent/candidate-replay.json \
  --executable /tmp/mtdp-catalogue-build/mtdp_jass_legal_catalogue \
  --jass ../jass --adapter ../draught-master \
  --output /tmp/mtdp-independent/candidate-jass-catalogue.json
python -m pytest -q research/mtdp/tests/test_candidate_jass_catalogue.py research/mtdp/tests/test_candidate_ambiguities.py research/mtdp/tests/test_prospective_candidate_replay.py
```

The dependency-install step now filters the backend requirement file into a
temporary file instead of modifying the pinned adapter checkout.

## Chronology: exact unresolved question

The prior candidate observation places fFgE7oED at **2026-11-14 11:00 UTC**,
exactly the protocol cutoff. A strictly earlier *admissible start time* is
therefore impossible. The remaining chronological completeness question is
whether an unobserved arena starting at the same instant precedes it under the
inherited start-time/event-ID ordering, and how any such candidate was rejected.
The explicitly named candidate is still not an exhaustive listing.

Current-source checks on 18 November are recorded in
[the source-gap receipt](CHRONOLOGY_SOURCE_GAP_2026-11-18.json):

- `https://lidraughts.org/tournament/calendar?year=2026&month=11` returned
  56 tournaments, earliest start 17 November 15:00 UTC; it did not return a
  historical monthly view containing the cutoff.
- The [upstream implementation](https://github.com/RoepStoep/lidraughts/blob/c7feaf1810c34f44f9b5f2b719a4aa795f9c7618/modules/tournament/src/main/Cached.scala#L43)
  builds the calendar from server time minus one day and only weekly-or-better
  scheduled events plus promoted events. The controller takes no date selector.
  This supports the observed limitation; the deployed server revision itself
  was not independently pinned.
- The observed last event of finished page 19 started on 16 November
  (`yiQdWYp7`, 11:10:22.728 UTC). XHR page 20 and 30 requests returned HTTP 400.
  This does **not** prove that no other historical archive exists.
- The current API's upstream `currentTournaments` implementation does not read
  `nb` or a historical date. Increasing `nb=50` cannot be assumed to recover
  missing historical coverage.

**Next foundation action:** recover a durable, complete listing of the cutoff
instant (initial 14 November snapshot or equivalent archive), including tied
candidates and justified rejections. Do not call the cohort frozen without it.
If that evidence cannot be recovered, preregister a fresh future cutoff and
acquire contemporaneous coverage before selecting a replacement; never
retrospectively certify fFgE7oED from its observed outcomes.

All five ambiguous games remain quarantined. fFgE7oED, the 78 targets and their
FENs remain reserved from D1 training, threshold tuning and signature selection.
No independent best-move result or equal-total-budget effect is claimed here.
The reference and budgets remain Scan depth 16 and total 10k/50k/200k nodes,
with 50k primary, as preregistered. Jeff's PC is not needed for these checks.
