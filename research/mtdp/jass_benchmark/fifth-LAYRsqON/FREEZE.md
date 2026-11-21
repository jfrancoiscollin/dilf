# Fifth-cohort freeze — LAYRsqON

The [12 November 2026 Hourly Blitz Arena](https://lidraughts.org/tournament/LAYRsqON)
is the first finished standard 5+0 arena in the API response queried
after [preregistration](../FIFTH_COHORT_JASS_PROTOCOL_2026-11-12.md).
It starts at 02:00 UTC. The response hash, retrieval time and first 14
finished records' selection fields are in [provenance.json](provenance.json).
The [public PDN export](https://lidraughts.org/api/tournament/LAYRsqON/games)
was downloaded twice with identical bytes. Use the public source and
recorded digest to reproduce the derived analysis. [API guidance](https://lidraughts.org/developers)
· [Terms](https://lidraughts.org/terms-of-service)

Replay of 92 games accepted 86 distinct trajectories, skipped two
duplicates and quarantined four games with ambiguous abbreviated
captures. The game audit records trajectory hashes, validated plies
and rejection reasons. Of 9,072 distinct FENs, 48 overlapped PC Blues
and 346 more overlapped earlier holdouts. The 8,678 novel FENs
included 5,697 with the quiet-man signature, 17 of them terminal.
There were 20 matches (0.35% of 5,680 novel nonterminal quiet FENs).
All matched targets have at least three moves, with no rejected
DILF/Jass catalogue. They use 17 distinct PC Blues source FENs,
occur in 15 games and are assigned to 14 owning games. One target
occurs in more than one game. The frozen targets have zero overlap
with the prior four target manifests. Two independent freezes
produced identical manifest and game-audit files.

Use the [fourth-cohort freeze command](../fourth-3onq5G6G/FREEZE.md)
with an added exclusion for `mtdp-lidraughts-3onq5G6G.pdn` and the
new holdout `mtdp-lidraughts-LAYRsqON.pdn`. Use the pinned initial-only
Jass build from the [third-cohort reproduction](../initial-only-0gB7ETSW/RESULTS_2026-11-12.md#reproduction)
and verify its catalogue and runner hashes. The Jass unit tests
passed and the synthetic initial-only preflight trace matched
the archive byte for byte. Neither side of this cohort was scored
before the freeze was committed.
