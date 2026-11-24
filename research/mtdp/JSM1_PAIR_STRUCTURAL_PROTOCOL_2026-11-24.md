# H13 — six JNNW/JSM1 pairs: structural compatibility only

Pre-execution protocol. The six exact pairs are those named in
R2_JSM1_LINEAGE_MAP_2026-11-23.md, totalling 10M declared records.
No new target scores, signatures, rank analysis or cohort is selected here.

Inputs are pinned to data commit 4ae90c3932f7cb0a10b5df27cfbd73cd220b6139
and manifest SHA-256 e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c.
For both files of every pair, verify stored size/SHA-256, gzip CRC, magic,
header count, exact record framing, decompressed size/SHA-256 and absence of
trailing data. Require JNNW positions and JSM1 metadata units, equal counts
and a 20M-row per-file safety bound. Check every board/trait/WDL structurally
and every seeded byte in {0,1}; discard score and WDL values after validation.
Any integrity or structural defect aborts; no successful report is written.

Retain at most 1024 evenly spaced metadata rows per pair; report distinct
sampled numeric game/opening IDs and full seeded-row count separately for
each source object. These numeric IDs have no authenticated external
namespace or event identity and MUST NOT be merged across sources or treated
as independent games. No population estimates or confidence intervals.

Equal length, valid headers and matching source stems do not prove row-level
semantic correspondence. In particular, a reordered but valid sidecar can
pass these checks: an explicit synthetic regression demonstrates this limit.
Thus row_alignment_authenticated, external_game_event_identity_authenticated,
historical_exclusions_checked, independent_cohort_admitted and
safe_decision_pruning_claim remain false even after structural success.
JSM1 has no ply; chronology cannot be recovered by assigning row index as ply.

Reproduction (stdlib only):

    python -m unittest research.mtdp.tests.test_jsm1_pair_audit
    python -m research.mtdp.jsm1_pair_audit \
      --root snapshot-data/data/r2_positions/2026-11-21 \
      --output /tmp/jsm1-pair-structural-audit.json

The workflow reads existing GitHub-published snapshots only, with no R2,
self-hosted runner, engine invocation or paid resource provisioning.
After success, authenticate original generation/merge index alignment and
source/game/event identities, then full trajectories and historical exclusion
coverage. Until those independent gates pass, quarantine all six pairs from
D1 confirmatory fitting/test and prospective Jass/Scan experiments. The four
reserved events remain wholly excluded; no fresh cohort is reserved here.
