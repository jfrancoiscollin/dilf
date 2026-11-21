# MTDP — held-out best-move and transfer-cost protocol

Freeze the quiet-man signature from the successor audit. Compare two distinct
canonical FENs only when the signature, side to move and exact FMJD action set
agree. Report legal-action mismatches and positions with fewer than two legal
actions separately.

## Inputs and pairing

- Development corpus: the 26 repository PC Blues mainlines. Every canonical
  FEN in these games is excluded from the primary holdout.
- Holdout: all games in the two Coupe de France 2021 PDNs in
  draught-master `0e5189fbb251bf5eaf2e613d0f878bb17c740311` and in
  [Lidraughts tournament L4F4P5R8](https://lidraughts.org/tournament/L4F4P5R8).
  These two sources were chosen for availability before scoring. The online
  tournament is a convenience sample of bullet games.
- Replay mainlines atomically through the existing FMJD adapter, report rejected
  games, and deduplicate whole trajectories across all sources. Pair distinct
  FENs from disjoint sets of games. Also report a separate directional transfer
  cohort pairing a PC Blues position with a novel holdout position. Neither
  repeated positions nor overlapping pairs are independent observations.

## Search and measurements

Reference: [Scan 3.1](https://github.com/rhalbersma/scan/tree/7aae17e7b7bfc47744601afb1ee7655e18983ce5),
Linux x86-64 executable at commit `7aae17e7b7bfc47744601afb1ee7655e18983ce5`.
Use Hub `go analyze`, one thread, no book, no tablebases, TT size 18 and a
cleared TT before each search. For every legal root action, play that action with
the FMJD adapter and search its successor independently at depth 8. Require
a depth-8 score for each nonterminal successor. Negate it to the original
mover's perspective, retaining exact centimen from the Hub output. A successor
with no legal move is an immediate win for the mover and gets +100.00 in
Scan's score encoding. Search starts from each successor's board and turn
with fresh game history.

For each position, retain all actions tied for the highest reference score.
Report both agreement of deterministic picks (lexicographic action order
breaks ties) and overlap of the full optimal sets. For each direction of a
pair, report the destination's optimal score minus its score for the source
pick. Report ordinary-evaluation regret in men, separately from comparisons
involving a forced score (absolute score above 80.00). Record any switch in
forced-win / ordinary / forced-loss classification and preserve all scores and
pair identities in the JSON. For cross-corpus pairs the primary transfer
direction is PC Blues to holdout; report the reverse direction for diagnosis.
Depth 8 is a fixed experimental budget and Scan's preferred moves can change
with depth. No search-strength or pruning conclusion follows from this audit.
