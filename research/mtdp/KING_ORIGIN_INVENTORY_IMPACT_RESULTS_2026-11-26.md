# H13 → D1: king-origin-v1 impact over two complete board inventories

Protocol42821e3182b5496c5010fdc2570757be9eee84a3 published before execution.
Initial PR43 headec2e2ca open/draft, nine workflows successful, no equivalent
pending/running audit. No publisher acquisition or reference-score computation.
Both complete JSONL inputs authenticated: historical quarantine possible-board
inventorydf9b357d… (21645 FENs) and fresh complete-game footprint62a71b82…
(12795 FENs). Their exact canonical union is34172 boards, with268 common to both
roles. No sampling, substitution, filtering or game partition was performed.

Compared old FMJD0e5189f, explicit king-origin-v1 source4714fef6… and unchanged
Jasscfe07fc legal exporter. Python full landing-path sets and root identities
are counted separately. Jass reference compares root identities only; it does
not certify a unique landing path. Fixed batches1000/timeout30s; no search,
model, evaluation, score, signature or ranking. Python process capped600s.

| Metric | Historical quarantine inventory | Fresh candidate footprint | Distinct union |
| --- | ---: | ---: | ---: |
| Boards |21,645|12,795|34,172|
| Legacy/Jass root-set mismatches |2|0|2|
| Corrected/Jass root-set mismatches |0|0|0|
| Changed Python root sets |2|0|2|
| Changed Python landing-path sets |2|0|2|
| Newly introduced reference mismatches |0|0|0|

Exactly two root actions are added, none removed; no path-only changes or
duplicate Jass root keys. The4497 union boards with an active-side king include
the two known return witnesses. All29675 boards without an active-side king
are unchanged, enforced as a gate. Changed owners are only the two historical
CARZrQpl:1285 andCARZrQpl:382 records. No fresh owner has changed actions/paths.
The witnesses are the previously diagnosed48x48 and3x3 omissions, now matching
Jass after correction. This is a bounded legality-impact result, not a best-
move preservation result, regret/Elo estimate, minimax proof or independence.

## Reproduction and artifacts

Eleven tests pass: four new impact-metric cases (path-only change, repaired
mismatch, removals/new disagreement, reference duplicates), four correction
unit tests and three parser tests. Two complete real runs with default Python
hash seed and731 yield identical semantic report, full ledger, all witnesses
and raw Jass catalogues. Binary/compiler provenance is separate per host.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Semantic report |2633|13061b5c12e387f5f3f359d421c73d5a9c921eada7e02b6187efd10a62aea943|
| Complete position ledger |33437247|40339620a6243439b121a228328a1f46c6a4c5f4b991722bdbee909d00e3bf8b|
| All change/mismatch witnesses |2551|fe1a249902136b007592536eb8c6ebea3c09e068bfc07a6be06ea268ed372cd7|
| Raw Jass catalogues |4536390|6fa6118a3e2a8f2ff80d8cdf15d5dff6ae5cc30dc1640305077d48d143173da5|

Summary versioned at validation/king-origin-inventory-impact-2026-11-26.json;
full outputs are generated into a workflow artifact. Remote audit/comparison
pending at initial publication. No output depends on compiler binary hash.

## Boundaries and next action

The historical input contains possible boards from190 quarantines (including
two incomplete legacy suffixes), NOT all452526 original cache boards or all
old scored positions. The fresh input covers145 strict-complete games, not
the seven excluded ambiguous games. The current source games were not replayed
with corrected rules. This audit cannot extend its zero-disagreement claim to
unvisited corrected suffixes, arbitrary positions, full historical coverage,
draw/repetition history or scientific efficacy. Existing hashes and reports
remain the truthful archived outputs of their original engine versions.

Next after remote verification: separately fix corrected whole-game/quarantine
reconstruction and checks on newly reached states, or broader old evaluated-
population impact as justified, before any revised exclusion ledger. Keep
legacy cache/190 strict quarantines and fresh145/7 split unchanged for now.
The two BZZ0yME2 overlap witnesses remain exclusions. Four historical whole
events stay excluded from D1 fitting/evaluation; fresh uDIrrl1c remains an
unadmitted whole raw candidate, no new H13 reservation or freeze. Source-
licence and independent-event/partition gates remain open. PC Jeff not required.
