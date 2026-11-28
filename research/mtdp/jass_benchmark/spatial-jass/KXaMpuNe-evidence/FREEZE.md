# KXaMpuNe prospective cohort freeze

On 13 November 2026, the chronological listing and finished detail
identified KXaMpuNe as the first completed standard 5+0 arena under the
[pilot protocol](../PROTOCOL.md). Two independent downloads of its
final PDN matched byte for byte (187,238 bytes). FMJD replay accepted
149 of 162 records, with six duplicate trajectories and seven
ambiguous capture records quarantined. The freeze checked the public
game IDs, exclusions and prior manifests.

The cohort has 9,609 eligible positions. L matches 90, LCB matches 34,
and exact mover occupancy with blockers (LMB) matches 25. The
[benchmark manifest](../KXaMpuNe/manifest.json) covers all 34 common
L/LCB targets across 18 owning games. Jass and FMJD agreed on the 323
target actions. The full freeze and benchmark manifest reproduced
byte for byte with Python hash seeds 7 and 61.

Next, score the frozen sources at Scan depth 12 and the targets at
depth 16. Publish the source-ranking diagnostic before starting Jass.
