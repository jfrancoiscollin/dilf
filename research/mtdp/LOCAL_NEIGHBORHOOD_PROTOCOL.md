# MTDP — preregistration: typed diagonal neighborhood, radius 2

Status: **protocol only, no result or validation claimed**. Research branch
`research/mtdp-foundation`, PR #43. This is a proposed controlled refinement
of the existing `quiet_man_geometry` signature, not a replacement of FMJD rules.

## Hypothesis

Two distinct positions that agree on mover men and immediate forward blockers
can have different best moves because the representation omits other nearby
pieces. A typed diagonal neighborhood of radius two might separate some
high-regret transfers while preserving nontrivial collisions.

## Definition (freeze before evaluation)

For a state with side to move `t`, and **no kings belonging to the mover**,
start with the existing `_quiet_signature(state)` (undefined if an immediate
capture exists). For each square `s` containing one of the mover's men, inspect
the four diagonal directions `(dr, dc) in {(-1,-1),(-1,1),(1,-1),(1,1)}`
at distances `d=1,2`, using `square_to_coords` and the inverse board
coordinate map. At each existing playable square, encode the occupant as one
of `own_man, own_king, enemy_man, enemy_king, empty`; encode off-board as
`off_board`. Emit the ordered tuple

`(s, ((dr,dc,d,occupant), ...))`

with origins `s` in ascending numeric order, directions in lexicographic
order and distances ascending. Prefix the signature with a version tag and
the existing quiet-man key. The radius is **geometric**, not legal-move
distance. The full FEN is never appended. In particular, opponent pieces
farther than two diagonal steps remain invisible unless they affect the
pre-existing key.

This intentionally includes own blockers and opponent kings, but only in
the neighborhood of the mover's men. No search score or legal-action
fingerprint enters the signature. A position ineligible for the baseline
quiet-man key remains ineligible for this refinement.

## Pre-specified comparisons

1. On the original PC Blues corpus: distinct FENs, eligible positions,
   distinct signatures, collision groups and distinct-FEN collision pairs;
   legal-action disagreements and one-ply successor-signature disagreements.
2. On the **same frozen, already scored** depth-12 holdout pairs: number
   retained under the refined signature, number removed, retained pairs
   with disjoint Scan-optimal sets, and retained directional transfers with
   ordinary regret >= 50 centimen. Preserve the original denominators,
   both transfer directions, ties and forced-category transitions.
3. On a **new external game set**, chosen and identified before inspecting
   outcomes: exclude identical FENs and duplicate whole trajectories shared
   with PC Blues or the previous holdout; record all source digests, game
   identifiers, replay rejects and overlap. Do not call a set independent
   merely because game IDs differ: shared positions and event/player
   dependence must be described.
4. Report absolute coverage as well as conditional failure rates. A
   refinement that removes all collisions is not a useful discovery.
   Do not select a different radius after viewing the same holdout results
   and then describe it as preregistered.

## Implementation and test acceptance criteria

- Deterministic key across set iteration order; distinct tags for off-board,
  empty, men and kings; correct row/column geometry for all 50 squares.
- Invariance under irrelevant changes outside every radius-2 neighborhood
  **only when** the baseline quiet-man key remains unchanged.
- Tests for enemy king adjacent, own-man blocker, backward adjacency,
  edge/corner, multiple origins, and radius-3 exclusion.
- Recheck FMJD legality and the 26 PC Blues replays on the integration
  workflow; do not assert a fixed numerical result before execution.
- No pruning, merge, deployment or paid compute. The local PC is unnecessary
  while the existing remote runners can execute the experiment.

## Interpretation limits

A better signature may reduce collisions simply by encoding more of the
board. Retained equal-action pairs can still disagree on successor
signatures, best moves, minimax values and practical performance. The
Scan fixed-depth evaluations are **proxies**, not ground truth. Statistical
claims require a sampling design and cluster-aware uncertainty treatment.
