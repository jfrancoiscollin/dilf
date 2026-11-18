# Reserved candidate fFgE7oED: individual ambiguity diagnostic

Diagnostic only, before scoring. The 157-game candidate is **not a scientific
freeze**. No Scan result, top-K experiment, Jass budget comparison or D1 campaign
was run. The five whole-game exclusions remain unchanged, as do the seven
duplicate-trajectory exclusions and the previous 145 accepted records.

## Verified inputs and result

- Candidate export: `https://lidraughts.org/api/tournament/fFgE7oED/games`.
- PDN SHA-256: `916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2`.
- FMJD engine: `jfrancoiscollin/draught-master` at
  `0e5189fbb251bf5eaf2e613d0f878bb17c740311`.
- The diagnostic verifies the export hash, adapter revision, actual imported
  engine path and absence of local changes to `backend/game_engine.py`.
- Two executions with distinct Python hash seeds reproduced the committed
  [JSON diagnostic](fFgE7oED-ambiguities.json) byte for byte. A subsequent run
  with the additional engine provenance checks matched the same output.
- Six targeted tests passed locally (existing prospective gate plus one new
  regression retaining quarantine when alternate paths share a successor).

| PDN game index | Public game ID | Ply (1-based) | Token | Legal trajectories | Distinct successor FENs |
| --- | --- | --- | --- | --- | --- |
| 46 | eW5kLtz2 | 89 | 1x40 | 1–23–40; 1–29–40 | 1 |
| 58 | ARKlsC4V | 103 | 1x45 | 1–29–45; 1–34–45 | 1 |
| 94 | rpZnh3lt | 120 | 47x15 | 47–29–15; 47–33–15 | 1 |
| 150 | YWmvLaTS | 98 | 37x5 | 37–14–5; 37–19–5 | 1 |
| 155 | DKUZmuuK | 122 | 44x11 | 44–22–11; 44–28–11 | 1 |

All five involve a king capture. In each case the abbreviated PDN token leaves
two legal routes, with identical captured squares and identical successor FEN.
This diagnoses route ambiguity rather than a divergent board successor **at
this first rejected ply**. The replay stops at that ply; it does not certify
the rest of the game, the unique played route, or best-move preservation.
The strict replay policy still requires exactly one matching legal move.
No automatic equivalence resolution or exclusion reconciliation was introduced.

## Reproduce

From the DILF root, with the pinned clean adapter checkout at `../draught-master`
and the exact PDN at `/tmp/mtdp-independent/mtdp-lidraughts-fFgE7oED.pdn`:

```sh
PYTHONPATH="$PWD:$PWD/../draught-master" python -m research.mtdp.jass_benchmark.candidate_ambiguities \
  --pdn /tmp/mtdp-independent/mtdp-lidraughts-fFgE7oED.pdn \
  --adapter ../draught-master --output /tmp/candidate-ambiguities.json
cmp /tmp/candidate-ambiguities.json research/mtdp/jass_benchmark/spatial-jass/replication/fFgE7oED-ambiguities.json
python -m pytest -q research/mtdp/tests/test_candidate_ambiguities.py research/mtdp/tests/test_prospective_candidate_replay.py
```

The existing candidate-replay workflow now runs this diagnostic after its
historical independence gate, compares it to the committed JSON and includes
it in its existing provenance artifact. No parallel campaign is dispatched.
Initial PR head `67d07842c09e863b247af1879df4d57102099a4d`: all seven
PR-triggered runs completed successfully; candidate-replay run `44307321640`,
artifact `14429007196` (SHA-256
`13f3b60f67d485e15f76f45439889f049978fd8d55ba741615cecd6da029a285`).
CI for the changes in this report is tracked separately after publication.

## Next action and coordination

Reconstruct and verify the chronological candidate selection against the
predeclared protocol, then verify the pinned Jass action catalogue on the 78
common L/LCB targets before declaring any freeze. If the chronology cannot be
proved, retain candidate status and select a new prospective cohort by the
protocol; never backfill a freeze after scoring. Keep all five games quarantined
unless an explicit prospective policy amendment is justified and recorded.

`fFgE7oED`, its 78 reserved targets and their FENs remain excluded from D1
training, threshold tuning, signature selection and retrospective campaigns.
Shared results here concern PDN provenance only. The fixed reference and equal
search budgets remain those of the current prospective Jass/Scan protocol;
this diagnostic provides no estimate of disagreement cost or speedup. Remote
resources suffice for this step; Jeff's PC is not required.
