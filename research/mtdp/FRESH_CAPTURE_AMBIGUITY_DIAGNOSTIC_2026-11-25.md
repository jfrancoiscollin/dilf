# H13 → D1: first unresolved captures in the fresh arena

Status: post-intake diagnostic, **not** a new admission or resolution rule.
PR43 is open/draft at b225cdf; all nine current branch workflows succeeded.
No equivalent pending/running diagnostic was observed before this work.
The earlier historical replay cancellation on b5daffc has a successful
successor on b225cdf (run45693660884); it needs no duplicate relaunch.

The immutable fresh intake and strict replay baseline are reused locally;
no source download, historical cache rebuild or engine search is performed.
The diagnostic visits exactly the seven quarantined games (indices9,22,24,
75,135,146,151). It replays each prefix with the **unchanged strict resolver**,
enumerates all legal actions matching the first unresolved token, applies
each through pinned FMJD0e5189f, and compares canonical typed occupancy plus
turn. It stops there, without replaying or admitting any suffix. No candidate
is selected by score, result tag, signature or downstream success.

| Game index | First unresolved ply | Token | Legal matching paths | Distinct next boards |
| --- | --- | --- | --- | --- |
| 9 | 112 | 47x15 | 3 | 1 |
| 22 | 75 | 4x31 | 2 | 1 |
| 24 | 89 | 20x20 | 2 | 1 |
| 75 | 112 | 41x5 | 2 | 1 |
| 135 | 62 | 49x16 | 2 | 1 |
| 146 | 120 | 45x1 | 2 | 1 |
| 151 | 87 | 4x42 | 2 | 1 |

Thus all seven first failures are action-path ambiguities with a single
observed successor board under this adapter:15 enumerated legal actions,
seven within-game board comparisons. This does **not** prove identical action
identities, externally authenticate the played path, verify the remaining
suffix, or imply strategic/minimax equivalence. The diagnostic state omits
game-history-dependent draw/repetition information; it is board equality only.
No new complete trajectory fingerprints are emitted. Strict results remain
145 complete games and7 quarantines; the original report is unchanged.

Five new synthetic tests cover divergent successors despite equal endpoints,
same-successor ambiguity still rejected by the frozen resolver, explicit path
and capture-kind filtering, zero matches and already complete games. Combined
with the three existing receipt tests:8 unittest cases pass locally. Two full
diagnostic executions (default Python hash seed and731) are byte-identical.
JSON: validation/fresh-uDIrrl1c-capture-ambiguity-2026-11-25.json, SHA-256
58ed434525260f0462d16970018c46a7e9eb122f970949c2815ea815ae05fd81.
The targeted workflow tests and reproduces this JSON without reacquisition;
remote execution is pending at initial publication.

## Coordination and next action

uDIrrl1c remains an **entire raw D1 admission candidate in quarantine**, not
an H13 scored holdout, an independent cohort or a scientific freeze. No new
reservation, split, signature/top-K/dimension campaign or Scan/Jass scoring.
All four older reserved events remain wholly excluded.

The existing preregistered exclusion rule is retained for ambiguous games.
A future board-only recovery would require a separate prospective amendment,
complete suffix/trajectory validation and a distinction from full action-path
identity before use; this diagnostic gives no permission to promote the seven.
Next actionable admission work remains external event/game membership and
source licence evidence, then historical exclusion coverage and whole-event/
game partitions with shared target FENs removed before scores. PC Jeff is not
required for this bounded remote-reproducible control.
