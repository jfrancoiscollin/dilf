# Native-order tie-break with a total node budget

This follow-up counts every node spent on verification against the
main search budget. Freeze the first completed independent standard
5+0 Lidraughts arena starting at or after 2026-11-14 11:00 UTC. Follow
the five-arena replication's agreement, duplicate and independence
checks. Exclude PC Blues and all previously used tournament games and
eligible positions. Keep every common L/LCB target in the new arena
and publish its manifest and input digests before scoring. The cohort
size is fixed at one arena, including an empty eligible cohort.

Use the existing LCB source ranking at Scan depth 12 and evaluate final
choices against the separate Scan depth-16 target reference. Compare
native, unchanged LCB and the metered control on each target at
10,000, 50,000 and 200,000 total nodes. The primary contrast is the
ordinary Scan regret difference (control minus native) at 50,000 total
nodes. Report possibility of tie scores and category transitions,
choice agreement with both controls, optimum hits, costs of changed
choices and a whole-game bootstrap interval within the arena.

## Verification and accounting

Use the same engine revision and build flags as the previous control.
Run an unmodified depth-one LCB search to identify its initial winner
and score. Probe each legal action in turn with a fresh one-thread
search that stops after the first root action at depth one. Require
the same full window and a completed return strictly inside it for each
probe. Derive the native order from current move generation. Use the
first native-ordered exact maximizer only when the LCB winner and score
match the exact maximum. Retain the LCB winner if evidence is
incomplete. The main replay uses a fresh table and the original LCB
visit order. Check that the intervention changes only the committed
winner and its ordinary downstream bookkeeping.

Cap verification (the preliminary search and all probes together) at
10% of the per-position node budget, with a hard limit on each call
equal to the unused allowance. Spend the remainder on the main replay,
including on fallback. Record consumed nodes for every call. For each
arm verify exact requested total nodes or record the existing depth-
ceiling exception. A ceiling exception cannot contribute to the main
paired estimate. Report all verification fallbacks and costs. No
archived native winners or Scan target scores enter the selector.

As an engineering check, use the archived five-arena positions to
verify bounded probes reproduce the prior full-window scores and the
node receipts sum correctly. Keep those results separate from the new
holdout. On the initial listing the next candidate is fFgE7oED. Verify
its final listing and independently fetched exports after it finishes.
