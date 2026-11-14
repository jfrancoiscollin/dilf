# MTDP — pre-analysis specification: top-three transfer candidates

Status: **completed**. See the [numerical results](TOP_THREE_TRANSFER_RESULTS_2026-11-11.md). The diagnostic uses the **unchanged** depth-12 Scan reports from `BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md` and `LOCAL_NEIGHBORHOOD_RESULTS_2026-11-11.md`.

## Question and estimand

Can the first three actions ranked by Scan's depth-12 successor scores in one position provide useful **ordering candidates** in another position sharing the baseline quiet-man signature? This is *not* a benchmark of Jass search speed, and does not assert that Scan's fixed-depth evaluation is true minimax value.

For each **scored** pair (A,B), evaluate A→B and B→A separately. Rank the full legal action set in the source by descending integer centimen score, breaking ties by the canonical action tuple (path, captures, promotion), ascending. Transfer the first min(3, number of legal actions) actions. The two positions must share exactly the same canonical legal-action keys.

In the destination compute:
- **Optimal coverage**: whether any candidate is tied for the maximum destination score.
- **Best-candidate ordinary regret**: destination maximum minus maximum destination score among the candidates, only when both scores are in Scan's ordinary category (-8000 through +8000 centimen inclusive); otherwise record undefined.
- **Category switches**: separately count transitions among ordinary, win and loss categories, never treating a forced category as an ordinary numerical regret.
- Count positive ordinary regrets and those >= 50 centimen; report denominator and maximum.

Compare all pairs with those retained and removed by the **already frozen** typed radius-two signature. Report the four directional groups (within external holdout and PC Blues→external, both directions). The same position can recur in many pairs: no independence or statistical significance is implied. No new game selection, Scan run, or Jass run is part of this offline audit.

## Acceptance checks

- Preserve report provenance and input SHA-256 in the analysis record; depth must equal 12.
- Deterministic tie-breaking and handling of fewer than three legal actions.
- For every cohort, retained + removed directional counts equal all directional counts.
- Top-3 optimal coverage is at least top-1 coverage on the same inputs, and ordinary regret cannot increase when k increases (when both defined).
- Test mismatched legal-action sets and forced-score categories.
- Do not use the outcome to retune radius or k on these same data.

## Reproduction (after restoring the frozen JSON reports)

```sh
python -m research.mtdp.top_k_transfer /tmp/depth-12.json /tmp/rapid-d12.json \
  --k 3 --output /tmp/mtdp-top-three-transfer.json
```

The archived reports, if not available, must be regenerated using the pinned inputs and binary in the preceding scientific reports. **Do not report numbers before the actual JSON analysis completes.**

Next experiment after this audit: an independent, budget-matched Jass move-ordering benchmark, with identical positions, legal moves, node budgets and seeds, and a non-transferred control. This requires separate implementation and approval if paid compute would be involved.
