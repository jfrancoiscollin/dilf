# Frozen Jass replication cohort

The [20 June 2026 Yearly Rapid Arena](https://lidraughts.org/tournament/iPQl7g7q)
was chosen before scoring for its completed 10+0 international-draughts
event and larger game count than the first tournament. Apply the
[original protocol](../../JASS_MOVE_ORDERING_PROTOCOL.md) with the same
pinned Scan 3.1 and Jass binaries, seeds, three arms and node budgets.

Of 199 exported games, 182 gave distinct trajectories, eight duplicated
a trajectory and nine were quarantined because a capture's endpoints
matched multiple legal paths. Exclude PC Blues and all earlier holdouts,
including the first Jass cohort. This removes 412 overlapping FENs.
Among 12,196 novel quiet FENs with a choice, 75 (0.61%) matched a PC Blues
source and had identical legal actions in DILF and Jass. No move mapping
was rejected. The 75 targets appear in 60 games and use 49 source FENs.
Two freezes produced the same manifest, SHA-256
`1c7b1543ac5b38500c9f4d61588c3e0778b40e5487de0d3500a1c09868668231`.

For a descriptive comparison weighted equally by target game, assign
each shared FEN to the lexicographically first game in its manifest entry.
Compute the mean paired ordinary-score regret delta within each game
before averaging across games. Report the original per-position summary
alongside it. The assigned games and shared sources can still be related.

## Reproduce the freeze

Start from the [first cohort command](../README.md#reproduction) with its
pinned dependencies. Fetch the new PDN and check the input hashes in the
manifest. Replace the first cohort's `--holdout` line with the two lines below.

```sh
curl -fsSL --retry 2 --max-time 90 https://lidraughts.org/api/tournament/iPQl7g7q/games \
  -o /tmp/mtdp-lidraughts-iPQl7g7q.pdn
```

```sh
  --exclude-previous /tmp/mtdp-lidraughts-Z3s40c6H.pdn \
  --holdout /tmp/mtdp-lidraughts-iPQl7g7q.pdn \
```
