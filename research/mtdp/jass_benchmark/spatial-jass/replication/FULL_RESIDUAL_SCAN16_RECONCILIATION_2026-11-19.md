# Exhaustive residual controls: fixed Scan16 reconciliation

Status: completed offline on the existing prospective population; **post-hoc diagnostic**, not another independent validation. No engine calls or new target scores. Primary geometry and equal-total-node Jass results remain immutable.

## Publication and reproducibility

Plan `full-frozen-residual-quality-plan.json` and all decisions/raws were published at `176340e4971b1dba6de626447f9e8e00fb27b023`. Analysis implementation `full_residual_quality.py` was published and its live ancestry verified at `6c4746f738288180bf26851a7803551fa72e1e67` **before loading the target packet**. It verifies both complete raw archives, normalized SHA, original analysis SHA and parent results, then reads the already frozen Scan16 packet from `ec8c4dfc2b8ddc11de74c1af5d7d0e9d9d581a0b` (SHA `8755f7d32ca849708116dd1bf8b0f27b0d7368cd70557f9f416656095f02afd8`). No target information enters decision production, ranking, filtering or thresholds.

All 114 contexts (38 targets, 31 owner games, two arenas, three budgets) are retained. All three original arm rows, points and bootstrap intervals are reproduced exactly, before interpreting supplementary contrasts. All 570 arm scores are ordinary/ordinary; complete reference optimum ties are retained. The independent stdlib verifier reconstructs 570 arm cells and **126 bootstrap estimates**, including the original 45. No undefined draws. Explicit process hash seeds 7/61 yield identical result bytes (SHA `b10de948f1349a714f32fa38b3cc373cfc305fc53a4d27be226d56801adc2f4f`).

Bootstrap: whole frozen owner games, fixed arena order s7ahYqL4/D9PF2OSW, all 19/12 owner games even in sparse estimands, 10,000 draws, seed 20261113, fixed percentile indices 249/9749. Undefined draws would suppress the interval, with no dropping/retry. These are within-sample descriptive intervals, not a tournament population guarantee.

## Results

Units below are integer Scan units (0.01 HUB), **not calibrated material pawns**. Positive regret difference means the first arm is worse. Primary total budget is 50,000; 10,000 and 200,000 remain secondary.

| Total budget | Native/control mean regret | LCB full/residual mean regret | Control minus LCB residual, mean [95% interval] | Optimum hits native/control : LCB |
|---|---:|---:|---|---|
| 10,000 | 10.210526 | 10.210526 | 0 [0, 0] | 10/38 : 10/38 |
| **50,000** | **8.526316** | **8.236842** | **+0.289474 [0, 0.942857]** | **11/38 : 12/38** |
| 200,000 | 6.052632 | 6.052632 | 0 [0, 0] | 15/38 : 15/38 |

At every budget, and separately in both arenas:

- LCB residual minus LCB full regret: 0, interval [0, 0].
- Native residual minus native full regret: 0, interval [0, 0].
- Control minus native residual regret: 0, interval [0, 0].

The entire nonzero comparison at 50k comes from **D9PF2OSW game 53**: control/native choose 17-21, target Scan16 score 23; both LCB orders choose 20-24, score 34 (target optimum), hence regret difference +11. Control and both residual arms use exactly **49,916 main nodes**; full arms use 50,000. In arena D9 alone the difference is +11/14 = 0.785714, interval [0, 2.75]; s7 alone is 0 [0, 0].

Thus the archived one-ply verification withdrawal changes no chosen-action regret in this complete frame, even though the previously documented 10k witness loses a completed depth. This zero observed quality cost is a fact about these decisions, not proof that verification is free or that costs never matter. The supplemental arms match **main search nodes**, and do not acquire their own charged verification; only the original three arms are the primary equal-total-node comparison. Control versus LCB residual is a conditional ordering/intervention contrast, not general efficacy or Elo.

The earlier prospective geometry result remains: 14/26 full-quiet-signature-equal pairs have disjoint Scan16 optimum sets, mean transfer regret 28.576923. A shared quiet-man geometry does not preserve a best move under this fixed reference. Depth20 sensitivity and crossed-reference checks do not establish minimax claims.

## Reproduce

From a checkout containing the published implementation and all pinned ancestors:

```bash
python -m research.mtdp.jass_benchmark.full_residual_quality --root . --analysis-commit 6c4746f738288180bf26851a7803551fa72e1e67 --output /tmp/residual-quality.json
python -m research.mtdp.jass_benchmark.verify_full_residual_quality --root . --report /tmp/residual-quality.json --output /tmp/residual-quality-proof.json
cmp /tmp/residual-quality.json research/mtdp/jass_benchmark/spatial-jass/replication/full-frozen-residual-quality-results.json
cmp /tmp/residual-quality-proof.json research/mtdp/jass_benchmark/spatial-jass/replication/full-frozen-residual-quality-independent.json
```

Local validation: 313 targeted tests pass, including nine new reconciliation/independent-bootstrap tests and current D1 corpus guards. CI of the analysis-only commit is checked separately from the data/verification successor. The offline Actions job reproduces both seeds and the independent result from committed archives.

## Next scientific gate / coordination

This closes the planned residual-control/Scan16 reconciliation. **No additional engine replay or enlargement of this scored population is justified by these results.** The next H13 action is to verify publication CI/artifacts, then prepare a new prospective protocol only after a concrete D1 candidate has passed its independent evaluation gate and its event/game/FEN provenance and legal mapping are frozen. Do not consume new target scores while designing that protocol. A fresh cohort must be jointly reserved before acquisition/scoring; none is reserved by this audit.

D1 retains signatures/top-K/refinement/dimension; H13 retains prospective Jass/Scan, equal-total budgets and new freezes. Entire events fFgE7oED, P1RUlfJc, s7ahYqL4 and D9PF2OSW, every game/FEN, remain excluded from D1 fitting and independent validation, signatures, top-K, refinement, thresholds and dimension tuning. They are already scored, and reuse would leak. Current D1 still has no admitted independent real corpus; its next documented task is FMJD legality/canonicalization before historical admission. No D1 campaign duplicated. Jeff's PC is not required.
