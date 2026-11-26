# H13 → D1: independent legal catalogue finds omitted king returns

Protocolad904dcaa4353515948a8d9f8b4001fedefe6fa3 published before catalogue
execution. Initial PR43 head71120ec open/draft, nine successful workflows,
no equivalent pending/running job. Fixed cases from baselined4e28965… :two
historical zero-frontier states plus standard initial-board engineering control.
No new corpus, evaluation, search, target selection or source retrieval.

Pinned Python FMJD0e5189f and C++ Jasscfe07fc, using the existing legal-only
exporter with native/SIMD disabled. All checkouts and echoed boards verified.
The compiled library contains evaluation code, but this exporter instantiates
no evaluator and calls no search/model-loading function. Binary hashes and
compiler receipts are separate per-host provenance; the versioned semantic
report binds engine commits, generator/exporter source hashes and raw catalogue
output, so differing compiler binary hashes are not mistaken for result drift.

| Case | Python root actions | Jass root actions | Python matches original token | Jass matches original token |
| --- | ---: | ---: | ---: | ---: |
| CARZrQpl:1285 /48x48 |1|2|0|1|
| CARZrQpl:382 /3x3 |2|3|0|1|
| Initial control |9|9|n/a|n/a|

Python has no extra root action in either disputed case. Jass adds exactly:

- 48x48 capturing20,22,39,42; no promotion;
- 3x3 capturing9,17,27,28; no promotion.

Root identity means endpoints+captured set+promotion, **not** the full landing
path. Full Python paths and all raw Jass root keys are preserved. The initial
control agrees exactly; it checks exporter/mapping wiring, not arbitrary king
capture correctness. Each three-board subprocess is bounded to30seconds.

## Source-level diagnosis and rule context

Python backend/game_engine.py SHA-256
5855ceae76fc7db243af85c61508d9505e17904925b9f73d79ed327296690394:
_all_captures passes the original board into _capture_sequences_king. That
routine stops its ray on a friendly piece, with no exception for the capturing
king's vacated origin. The man routine separately permits landing on path[0].
Jass src/movegen.cpp SHA-256
bb2828f9857fe38a7d90e0524cb2dbf6fc78c5a4a0502308aa3b60f3a7f74dec
explicitly exempts the original square both for ray blocking and landing.
This source difference explains the observed omissions and identifies a king
origin-occupancy defect to isolate in a disposable corrected-adapter control.
No source was patched for this comparison.

Official FMJD Annex1 articles4.6–4.8 and4.11 describe multi-capture continuation,
reuse of empty squares and delayed removal of captured opponents:
https://www.fmjd.org/downloads/news/948/Annex%201%20official%20FMJD%20rules%20of%20international%20draughts.pdf
Inspected26November2026. This rule context supports treating the vacated origin
as empty; catalogue agreement/source inspection is not a formal proof of every
capture rule. Do not label the historical PDN invalid based solely on the old
adapter's zero frontier. Actual played landing paths remain uncertified.

## Reproducible validation

Three parser/unit tests pass, including malformed-key subcases, square bounds,
wrong echoed position and invalid promotion. Two complete calls under default
Python hash seed and731 yield identical semantic report and raw catalogues.
Versioned report validation/return-capture-oracle-2026-11-26.json SHA-256
8e5d2e4ab0ec64906ccc5ba37b31bfcd188da731284b44c2d8a2ddac24cafca2.
Binary identity and raw catalogue are workflow artifacts. The targeted remote
build/comparison is pending at initial publication. Local CMake was unavailable;
a temporary build tool was installed and the pinned exporter built successfully.
No model, search or paid resource was used.

## Coordination / next action

Preserve frozen engine versions, historical cache, all190 strict quarantines,
and previous results as archived evidence. Their broader sensitivity to this
king-generator omission has **not** been audited; do not extrapolate to all
historical positions or silently replace previous legality counts. The two
BZZ0yME2 overlap witnesses and fresh145/7 quarantine split remain in force.
All four reserved events stay excluded, uDIrrl1c remains unadmitted.

Next: verify remote artifact, then prepare a separately versioned disposable
origin-square correction with direct regression witnesses and independent
catalogue checks; audit its impact before any replay/exclusion extension or
new scientific freeze. No production engine change or score campaign here.
Source-licence/independent-event gates remain open. PC Jeff is not required.
