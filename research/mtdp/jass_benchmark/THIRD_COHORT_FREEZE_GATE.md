# Third-event freeze gate — initial-only Jass experiment

Status: **procedure only** (2026-11-12 UTC). No third event selected, no PDN downloaded, no target manifest frozen, no Scan score calculated.

This gate operationalizes [JASS_INITIAL_ONLY_PROTOCOL.md](../JASS_INITIAL_ONLY_PROTOCOL.md) without changing its hypothesis or endpoints. The first two independent cohorts are *development evidence*, not fresh test data.

## Required pre-score evidence

1. Identify the **completed** third FMJD 10×10 event, its canonical export URL, event ID, UTC export timestamp, exact raw PDN byte count and SHA-256. Record whether re-export changes bytes.
2. Freeze the exclusion inventory **before** target scoring: PC Blues 26 games, both existing independent rapid-event PDNs (17 October 2026 event `Z3s40c6H` and second cohort `iPQl7g7q`), and all previously used holdouts. Record the SHA-256 of every exclusion file, not merely its name.
3. Replay the raw PDN using the pinned FMJD adapter. Record counts for parsed games, rejected games with reasons, unique game trajectories, unique FENs, duplicate trajectories, overlap with excluded FENs, and novel eligible FENs.
4. Select candidate positions without Scan target evaluations. For each novel eligible FEN, require nonterminal status, at least two distinct legal canonical actions, the preregistered quiet-man signature, a PC Blues source with identical signature **and exact legal canonical set**, and a bijective DILF-to-Jass move mapping. Reject ambiguous capture keys; never silently substitute a second source.
5. Select a source by the previously specified lexicographic rule (source game ID, source FEN). Freeze each record's target event/game/ply/FEN, source game/ply/FEN, canonical action keys, Jass action keys, and typed radius-two descriptor. Reject any target FEN already used by the 28- or 75-target cohorts.
6. Serialize deterministically (stable order, normalized encoding), hash the complete manifest, and repeat the freeze in a clean process to check byte-for-byte equality. **Commit manifest + PDN hashes before any Scan scoring.** If no eligible positions survive, publish that fact without changing the selection rule.

## Mechanical acceptance gate

- Jass commit `cfe07fce6385b980553a898e9651d53419589ebc`; verify the patch applies to a disposable clean checkout.
- Run `jass_tests`, the DILF MTDP test suite with the Jass legal catalogue enabled, and reproduce `jass_preflight/initial-only-trace.tsv.gz` byte-for-byte.
- Confirm equal legal move sets, full first-iteration root coverage, exactly one schedule application for each ordered arm, native adaptive order after the first iteration, and a fresh 1 MiB TT per arm.
- If any check fails, stop before scoring; report the specific failing fixture/trace and avoid interpreting quality outcomes.

## Evaluation and reporting gate

After the manifest commit: compute Scan 3.1 successor depth-12 target scores using the pinned engine and explicit score units. Then execute all three arms at 10k/50k/200k exact nodes, recording per-arm receipts, iteration traces, and selected moves. Reject a receipt if actual nodes differ from the budget. Preserve failures/exclusions in the denominator.

Primary comparison at 200k: paired target regret (MTDP initial-only minus canonical initial-only), with game-clustered bootstrap (seed 20261112; 10,000 replicates). Report position-level and game-level mean/median, confidence interval, missingness, and sensitivity to shared PC Blues source games. Secondary analyses and stopping rules remain those of the preregistered protocol.

**No claim of benefit is allowed from the successful mechanical preflight alone.**
