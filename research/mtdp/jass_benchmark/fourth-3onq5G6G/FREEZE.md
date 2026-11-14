# Fourth cohort freeze — 3onq5G6G

The [28 August 2026 Hourly SuperBlitz Arena](https://lidraughts.org/tournament/3onq5G6G)
was chosen from public event metadata before any source or target score
was calculated. The completed standard international draughts event
started at 09:00 UTC, lasted 57 minutes and used nominal 3+0. This
different cadence tests transport beyond the earlier rapid events.
The [public game export](https://lidraughts.org/api/tournament/3onq5G6G/games)
returned the same 293,498 bytes on two downloads. The hash, time, input
inventory and engine hashes are in [provenance.json](provenance.json).

Lidraughts documents public API use and its terms encourage study of
draughts using its services and content. The terms distinguish the
server software license from players' rights in games. Reproduction
uses the original public export URL and its digest. This commit archives
derived positions and replay outcomes. [API guidance](https://lidraughts.org/developers)
· [Terms](https://lidraughts.org/terms-of-service)

Replay of all 244 games accepted 232 distinct trajectories, skipped one
duplicate and quarantined 11 games with ambiguous abbreviated captures.
The game audit gives the verified ply count and trajectory digest of
each successfully replayed game and the exact reason for each rejection.
Of 24,231 distinct FENs, 115 overlapped PC Blues and 491 more overlapped
earlier holdouts. All prior input hashes matched their frozen inventory.
The 23,625 novel FENs included 15,462 with the quiet-man signature. There
were 38 terminal positions. Among the remaining 15,424, 74 (0.48%) had
a PC Blues match with the same exact legal catalogue and unambiguous
DILF/Jass keys. No candidate mapping was rejected. No selected FEN occurs
in the three prior target manifests. The 74 targets use 57 source FENs
and occur in 65 games, with 56 owning games and nine multi-game targets.
All 74 have at least three legal actions.

Select every eligible FEN in lexicographic order, with no sampling or
random seed. Keep eligible forced moves and exclude only terminal
positions and failed matches. Use the lexicographic minimum PC Blues
game/FEN pair as the source and the first target game ID as owner.
Both freezes produced byte-identical manifest and audit outputs.

## Reproduction

Follow the [third cohort instructions](../initial-only-0gB7ETSW/README.md)
to pin DILF's FMJD adapter and build the Jass legal catalogue. The
catalogue built with GCC 14.2.0 and CMake 4.4.4 has the same SHA-256 as
the previous catalogue. Use the same baseline and exclusion arguments,
add the previous third-event export to the exclusions, and replace
the previous holdout and output arguments with:

```sh
  --exclude-previous "$PDN_DIR/mtdp-lidraughts-0gB7ETSW.pdn" \
  --holdout "$PDN_DIR/mtdp-lidraughts-3onq5G6G.pdn" \
  --include-forced --record-provenance --game-audit /tmp/mtdp-fourth-audit.json \
  --output /tmp/mtdp-fourth-cohort.json
```

The preregistered depth-12 source ranking and depth-16 target evaluation
are pending at the freeze commit.
