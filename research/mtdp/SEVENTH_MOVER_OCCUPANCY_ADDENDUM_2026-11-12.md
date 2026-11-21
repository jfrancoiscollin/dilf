# Seventh ablation — prescoring count-and-blockers control

This addendum was prepared before retrieving or inspecting seventh-event
candidates. The [registered protocol](SEVENTH_MOVER_OCCUPANCY_PROTOCOL_2026-11-12.md)
still governs event selection, source pool, L/LM primary contrast,
LMB secondary comparison and Scan settings.

Add one secondary arm **LCB**. It requires the same side to move,
exact legal actions and exact forward blocker squares as LMB, with
equality of the **number** of mover men in place of equality of their
squares. This operationalizes the next control in the sixth-event
handoff. LMB is a subset of LCB and LM, and all arms are subsets of L.
LM and LCB are distinct controls. The side-to-move requirement applies
to all arms.

Reuse the sixth-event eligibility and ordering. Keep novel, nonterminal
positions with mover men only, no capture and at least two legal moves.
Report terminal, forced, capturing and mover-king exclusions separately,
with each FEN counted once (mover kings first). Report coverage over
the eligible population and over all novel replayed FENs. Select the
first matching source by (stable game ID, ply, FEN) for each arm.
Therefore arms share a source whenever the first broader match also
satisfies the narrower key. Retain all source candidates in the freeze.

For LCB report coverage, conditional quality and paired regret against L
and LMB, with the same game-cluster method. Report LM/L as primary and
the other contrasts as secondary, even if some keys produce identical
candidate sets. Exclude all previous eligible target manifests and
all previous replayed holdout PDNs, as in the sixth study. Keep all
eligible seventh targets and verify both independent freeze executions.
