# H13 → D1: bounded historical quarantine frontier results

Protocola5c1a8853d242688e66e2afad4c6549b2fcdff6b was published before real
execution. Initial PR43 head5ab5842 open/draft, nine workflows successful;
no equivalent job pending/running. Scope exactly ALL eight quarantined records
in the historical cache's closed s7ahYqL4/D9PF2OSW extension. The182 other
historical quarantines are explicitly outside scope. No new source retrieval.

The original cache5cb42474…, both original PDN hashes, pinned FMJD0e5189f and
fresh exact-FEN inventory62a71b82… are verified before any comparison. The
legacy parser, resolver, quarantine reasons and cache remain unchanged.
Every matching legal action is applied, with identical typed boards+turn merged
at each token. All visited states, including hypothetical branches that might
later die, form a conservative possible-history inventory. Fixed limits128
simultaneous boards/100000 matching applications per game were not adjusted.
No actual played path, full action trajectory or history-aware draw/repetition
identity is reconstructed or certified by this control.

| Result | Observed |
| --- | ---: |
| Historical quarantine game records examined | 8 |
| Complete bounded board-frontier traversals | 8 |
| Maximum simultaneous distinct boards, every game | 1 |
| Any cap / zero-frontier failure | 0 |
| Distinct possible historical boards, all prefixes | 993 |
| Boards absent from unchanged historical cache | 153 |
| Of those153, overlapping fresh11910 nonhistorical FENs | 0 |

All eight games have a single board at every ply despite ambiguous action
paths. Per-game missing-board counts are7,13,19 (D9PF2OSW games17,20,37) and
4,9,62,13,26 (s7ahYqL4 games101,109,131,35,60); their sum is153. The eight
strict action-path quarantines stay in force, and no legacy trajectory hash
or historical-cache membership is rewritten. These153 boards are supplemental
possible-history exclusion evidence only. Zero overlap closes this specific
leak check for the existing fresh inventory, not global historical completeness,
source licensing, independent-cohort admission or a Jass/Scan efficacy gate.
The fresh145/7 strict population and its11910 descriptive FENs remain unchanged.

Five synthetic unittest cases pass (including two cap subcases), exercising
branching, successor merging, dead branches, zero frontier and bounded failure.
Two complete real runs with default Python hash seed and731 produce identical
summary and inventory bytes. Summary SHA-256:
ae9a3145060b866e84d45e84b00495e3545cc3597f96728188778a43f2bf8df8.
Full possible-board inventory174265 bytes, SHA-256
6548bacd74f6cc46262cb6c2d1ad8e16501c5d771199f3a73b07958ee4efec6d.
Summary versioned under validation/historical-quarantine-frontier-2026-11-26.json;
full inventory published by the targeted workflow. Remote reproduction is
pending at initial publication.

## Coordination / next action

Use these boards only as exclusions, never to fit D1 signatures or compare
rankings. All four whole historical reserved events remain excluded. uDIrrl1c
remains an entire raw D1 admission candidate, no new H13 reservation or split.
Next: verify targeted artifact, then scope the remaining182 historical
quarantines under a separately fixed control if needed; reconcile source data
licence and independent-event/partition evidence before any new freeze. No
scores, signature/top-K/dimension campaign, paid work or deployment. PC Jeff
is not required for this bounded control.

## Remote verification

Implementation98de8fd passed [run45734664412](https://github.com/jfrancoiscollin/dilf/actions/runs/45734664412),
job139624872823: five tests, existing pinned cache/fresh inventory, complete
bounded replay and exact summary comparison. Artifact15078322358 downloaded;
ZIP SHA-256040679671cab0be3323a30440dcb861a7b8340f045be996fcc78703f41617dd2
matches GitHub. Its summary and full174265-byte possible-board inventory are
byte-identical to both local runs. This closes the eight-game bounded check;
no strict quarantine, cache, candidate population or admission gate changed.
