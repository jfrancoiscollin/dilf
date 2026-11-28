# H13 → D1 — uDIrrl1c raw-source integrity and complete-game replay

This is intake/admission evidence, not an independent scientific freeze or
an evaluation of signatures/best moves. No new source was downloaded from
Lidraughts here: the existing D1 intake artifact was audited without repetition.

PR head at inspection: db429e1a0dbe2afab78b42cd86eb8fe64ad8616e, nine workflows
successful, including acquisition run45690843969/job139475559684.
Artifact15057838002 ZIP SHA-256 verified against GitHub:
efe9f4c133edb5adfaa236a30dabe1a39e931ed0e09b287ae5bb860f0ac2b28c.
Exact archive preserved at fresh_intake/2026-11-25-uDIrrl1c.zip; includes raw
listing, all inspected metadata, ordered acquisition receipt and both exports.
Receipt SHA-256 5d7f76a05666a9c0bc2b8b7a297bd819fc2955bc68b1c5418625daf359033905.
Both PDNs are164243 bytes, SHA-256
5900c8fccf71cfbaab6690e5fd15e87fff6e0744afa67a2792e0a8733f486e64.
Metadata describes a completed standard 5+0 arena starting25 November2026
14:00UTC. Observed listing is bounded, not a complete chronology of arenas.

The validator authenticates the pinned ZIP, receipt, listing, candidate detail
and both exports, strictly parses all games, requires unique public IDs,
consistent game time control/timestamps, and replays each WHOLE game with
unchanged frozen PDN resolution and FMJD adapter0e5189f. It compares public
IDs, normalized notation, full trajectories and canonical FENs with the exact
previous H13 cache5cb42474… containing25 sources and452526 confirmed FENs.
It does not claim this known cache is a globally complete exclusion registry.

Results, reproduced byte-for-byte with Python hash seeds default and731:

- 152 source games;145 unambiguous complete legal replays,7 quarantined games.
- No public game ID matches the known historical registry.
- Five normalized-notation/full-trajectory matches: source indices5,25,51,56
  have only one ply and index134 has zero. These trivial trajectory coincidences
  are not proof that the same public games were re-exported.
- Among complete replays:1681 position occurrences already in the known FEN
  registry and11930 absent from it, including initial/opening states. These
  are occurrences, not distinct or independent positions. Do not qualify
  targets simply because their public game IDs or dates are new.
- Quarantine indices9,22,24,75,135,146,151 have abbreviated captures matching
  2–3 legal paths. No path was guessed and no partial prefix was admitted.

Three unittest cases pass, with four nested archive tampering attacks. The
report is validation/fresh-uDIrrl1c-integrity-replay-2026-11-25.json; workflow
reproduces it using the preserved ZIP and previously published cache artifact.
No engine search, signature, top-K, dimension, new reference score or target
selection is included. Existing D1 acquisition workflow is not relauched.

## Coordination / next gate

Track the WHOLE event uDIrrl1c as **D1 raw admission candidate in quarantine**.
It is not a reserved H13 scoring holdout and is not admitted for independent
D1 efficacy. Do not fit/select signatures or thresholds on its labels or
start a Jass/Scan campaign. No game/position partition is frozen here.
All four earlier H13 events remain entirely reserved and excluded from D1.

Next: D1/H13 authenticate external event/game membership and source licence,
resolve or explicitly exclude ambiguous games under a preregistered rule,
and establish historical exclusion coverage. Freeze whole-game/event partitions
and remove shared canonical target FENs across partitions before any new target
scores. Membership/replay evidence alone is not independent admission; all
admission/freezing flags remain false. PC Jeff is not required for this audit.

## Remote reproduction verified

Implementation b5daffc6e4b56a0ea704cf7859cc0bf24713e052 passed targeted
run45693331728/job139484188337: three unittest cases, restoration of the
pinned historical cache, complete source replay and exact report comparison.
Artifact15059138609 was downloaded; ZIP SHA-256
2f3da16fec9e0d42881572c1654e64400f53611ef3e5ac8cd0879b3b66fa3ddc
matches GitHub. Its JSON is byte-identical to the versioned local report
(SHA-256 a69de36bd4618e0c5948c54b05f17d9f9e500a11c85ad24783f831bb085eb13a).
This confirms reproducibility only; all admission gates above remain open.
