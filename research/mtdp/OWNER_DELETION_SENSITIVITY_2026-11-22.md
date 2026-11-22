# Whole-game deletion sensitivity of frozen prospective results

Post-hoc descriptive diagnostic. No new engines, scores, positions, reference,
signature, source selection, outcome threshold or D1 campaign. This is not a
fresh independent confirmation or a confidence interval.

Input: exact published `two-named-arenas-results.json`, SHA-256
`3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7`.
The existing frozen LCB full-signature-equal stratum remains 26 targets from
22 contributing owner games. The full registered sampling frame has **31**
owner games across 38 targets. All 31 deletion cases remain, including the nine
owners without a primary-stratum observation. Each deletion removes **all**
targets belonging to the exact (event, owner) pair, not one selected position.
The report also removes each of the two entire events separately.

| Fixed estimand | Original | Range after deleting one whole owner game |
|---|---:|---:|
| Geometry transfer mean regret | 743/26 = 28.576923 | 20.125000–30.791667 |
| Geometry disjoint-optimum fraction | 14/26 = 0.538462 | 0.500000–0.560000 |
| Jass control minus native mean regret, 50k total nodes | 0 | 0–0 |
| Jass control minus LCB mean regret, 50k total nodes | 11/38 = 0.289474 | 0–0.305556 |

Units are the original integer Scan units (0.01 HUB), not a calibrated material
pawn value. Exact rational sums/denominators for every deletion are retained in
`validation/frozen-owner-deletion-2026-11-22.json`.

The smallest geometry mean is obtained by removing s7ahYqL4 game145: it removes
two primary positions and total cost260, leaving483/24 =20.125. The geometry
counterexamples therefore survive deleting any single whole owner game in this
sample. Deleting all of D9PF2OSW leaves10/17 disjoint optima and564/17 mean cost;
deleting all of s7ahYqL4 leaves4/9 and179/9. This does not establish failure
frequencies for a broader tournament population.

The Jass control/native regret contrast remains exactly zero in every owner
and event deletion. The entire nonzero control/LCB contrast disappears when
D9PF2OSW game53 is deleted (37 targets remain), or when its entire event is
removed. This confirms the previously documented single-game concentration;
it supplies no efficacy or Elo evidence.

Reproduce offline:

```bash
python -m pytest -q research/mtdp/tests/test_owner_deletion_audit.py
PYTHONHASHSEED=7 python -m research.mtdp.jass_benchmark.owner_deletion_audit --root . --output /tmp/owner-deletion-7.json
PYTHONHASHSEED=61 python -m research.mtdp.jass_benchmark.owner_deletion_audit --root . --output /tmp/owner-deletion-61.json
cmp /tmp/owner-deletion-7.json /tmp/owner-deletion-61.json
cmp /tmp/owner-deletion-7.json research/mtdp/validation/frozen-owner-deletion-2026-11-22.json
```

Eight local tests pass: unequal cluster sizes, absent-stratum owners, identical
owner labels across distinct events, malformed frames, duplicate targets,
noninteger outcomes, changed input bytes and exact published primary totals.
The existing offline crossed-depth workflow now reproduces this diagnostic.

Next: confirm its CI and retain the existing H13 gate: await a concrete D1
candidate that passes independent evaluation before a new prospective Jass/Scan
protocol. Do not enlarge/re-score the old cohort or choose a new signature from
these deletions. All games/FENs of fFgE7oED, P1RUlfJc, s7ahYqL4 and D9PF2OSW
remain reserved and excluded from D1 fitting/independent evaluation. This
post-hoc H13 arithmetic does not qualify any D1 candidate.
