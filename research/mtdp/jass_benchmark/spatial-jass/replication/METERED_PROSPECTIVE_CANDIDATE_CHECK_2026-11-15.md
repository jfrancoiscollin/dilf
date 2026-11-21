# MTDP preregistered independent 5+0 arena — first candidate observation

**Status: evidence collected, NOT a scientific freeze, NOT a selected holdout.**

The preregistered
[`TOTAL_BUDGET_TIEBREAK_PROTOCOL.md`](TOTAL_BUDGET_TIEBREAK_PROTOCOL.md)
specifies the first independently eligible standard 5+0 Lidraughts
arena starting on or after **2026-11-14 11:00 UTC**. The protocol
had named `fFgE7oED` as the next preliminary candidate. The present
check tests availability and metadata **without** choosing a tournament
after inspecting Jass or Scan scores.

## Reproducible public-source evidence

[Read-only GitHub Actions run #43716538357](https://github.com/jfrancoiscollin/dilf/actions/runs/43716538357)
collected and preserved an artifact
`mtdp-prospective-candidate-raw-evidence`, ID `14162552242`
(artifact ZIP SHA256
`6188bf01238306a8d7483ce4938327daf299367137ca4374215ccaed8c2f1403`).

- Observation time: **2026-11-15 12:58:34 UTC**.
- Candidate: `fFgE7oED`, metadata ID matches, event is finished.
- Variant: **standard**; system: **arena**; clock **300 seconds + 0**.
- Start: **2026-11-14 11:00:00 UTC** (exactly the preregistered
  earliest permitted timestamp).
- Metadata digest SHA256:
  `4b6ded3e88ee3eaa3d23d3a2fcf603d4d9684ecf3662337809014f47424ca6e2`.
- Current tournament-list snapshot digest SHA256:
  `ad6889e67431f59841293aa6aeb1d69c5ef59e65fc939621fab1c2c6d59169ca`.
- Two independent public
  [PDN API](https://lidraughts.org/api/tournament/fFgE7oED/games)
  GET requests each returned **169,802 bytes**, identical byte for byte:
  SHA256 `916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2`.
  Both downloads and the raw public metadata/listing are retained in
  the evidence artifact (30-day retention).

The evidence checker explicitly returned:
`candidate_metadata_and_exports_verified_but_not_chronologically_selected`.
No FMJD positions, Jass choices or Scan-16 target values have been
computed from this candidate by the checker.

## Mandatory remaining freeze gate

1. **Chronology:** reconstruct the first eligible completed 5+0
   tournament starting at/after the cutoff from durable calendar/listing
   snapshots, including missing or rejected predecessors. A rolling
   50-event listing at observation time **cannot itself prove**
   `fFgE7oED` was the first eligible tournament.
2. **Independence:** restore all older exclusion game IDs and FEN
   manifests from PC Blues and the earlier pre-registered studies;
   verify hashes, detect duplicate games and overlapping positions.
   Explicitly record every exclusion or rejection. Use the pinned
   `draught-master` adapter
   `0e5189fbb251bf5eaf2e613d0f878bb17c740311`.
3. **Legal replay:** validate the complete PDN with FMJD capture and
   promotion rules. Quarantine invalid games, compare two independent
   reruns with distinct hash seeds. Preserve counts and digests,
   including an empty eligible cohort.
4. **Freeze before scoring:** create an immutable manifest of every
   L/LCB common target and of its source mapping. Publish raw-input
   hashes and deterministic target population. Verify the pinned Jass
   `cfe07fce` and Scan-3.1 build/digests *before* starting their
   searches.
5. Only after this evidence is fixed should the blinded native,
   unchanged LCB and MTDP searches run at **10k/50k/200k total nodes**,
   with the separately pinned Scan-depth-16 target reference. The
   50k ordinary-regret contrast and whole-game interval are the
   preregistered primary endpoint; do not substitute the archived
   473-position result.

**Do not mark the holdout frozen or claim an independent MTDP effect
until all of these gates have succeeded.**
