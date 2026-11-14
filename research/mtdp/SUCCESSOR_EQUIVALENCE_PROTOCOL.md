# MTDP — successor equivalence protocol (pre-analysis, 2026-11-11)

## Research question

For distinct canonical positions that share a candidate spatial signature
and the side to move, and that have identical **square-indexed** FMJD legal
action sets, do corresponding legal actions produce successor positions with
the same signature? This is a necessary test for treating the signature as
a deterministic abstract transition system; it is **not** a sufficient
condition for safe search pruning or strategic equivalence.

## Experimental unit and controls

- Input: 26 PC Blues PDN games, replayed atomically with the real
  `draught-master` FMJD adapter. Reject/quarantine incomplete games.
- Deduplicate identical canonical FENs before pairing. Pair only distinct
  FENs within the same signature and side-to-move bucket.
- Use the exact legal action fingerprint already defined by
  `legal_collision_audit._legal_fingerprint`: ordered landing path,
  captured-square set and promotion flag.
- For each pair, first compare legal action sets. Mark a pair with unequal
  sets as **ineligible**, not as a successor-equivalence success.
- For eligible pairs, apply **every** corresponding legal action through
  `engine.apply_move` to both states. Compute successor signatures using
  the same deterministic signature function, including successor turn.
- Count a pair as transition-consistent only if every matched action yields
  equal successor signatures. Record at least one action-level
  counterexample for each inconsistent pair.
- Report both pair-weighted and game-grouped summaries; observations within
  games and overlapping pairs are dependent.

## Fail-closed invariants

1. The same canonical FEN must reproduce the same legal actions and
   successors on every occurrence; disagreement is an error.
2. A successor comparison must not be based on only the played PDN move.
   Evaluate all legal moves for the pair.
3. Promotion, captures, flying kings, forced capture and maximum-capture
   selection are delegated to FMJD, never inferred from geometry alone.
4. A pair with zero legal moves requires an explicit terminal-state label;
   do not silently treat vacuous equality as proof of useful equivalence.
5. A signature refinement can remove collisions but must not introduce
   new same-signature pairs absent from its parent partition. Test this
   monotonicity explicitly.
6. Run the exact-occupancy representation as a negative control: distinct
   canonical positions should not collide when occupancy and turn are exact.

## Reporting and inference

Publish schema version, commit SHAs for both repositories, Python version,
game count, accepted/quarantined games, observations, unique FENs,
signature definition, eligible pairs, ineligible pairs, inconsistent
successor pairs, and action-level counterexamples. Archive machine-readable
JSON and the full run URL.

A result of zero observed inconsistent pairs is only a within-corpus
observation. It is not a universal proof or a licence to prune Jass search.
The next stage requires independent, game-grouped holdout positions,
trusted engine evaluations, tactical safety tests and a controlled
search-strength benchmark.

## Operational note

On 2026-11-11 the CI workflow for commit
`1c068da9e20f837551a8dba8de5929756b0cee85` failed at
`apt-get install poppler-utils` because the Ubuntu mirror hostname
could not be resolved. No test assertion failed: the test step was not
reached. The separate `downstream-compat` workflow completed
successfully. Do not label that CI run as a regression in MTDP code.
