# Frozen prospective verification-cost audit — 2026-11-14

Source: GitHub Actions CI run 43616922251, job 132513895793, commit `371ae6264196027ad5cbbb6da4fce4e7a2566416`. The `MTDP frozen prospective cost audit (473 positions per budget)` step completed successfully. The report was read from the frozen prospective receipt, not from a new engine run.

| Original search budget | Per-position verification cap (10%) | Depth-one probe nodes (473 positions) | Positions exceeding cap from depth-one alone | Historical full auxiliary nodes | Positions exceeding cap for historical full auxiliary |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 1,000 | 316,542 | 65 / 473 | 50,950,000 | 473 / 473 |
| 50,000 | 5,000 | 316,542 | 0 / 473 | 50,950,000 | 473 / 473 |
| 200,000 | 20,000 | 316,542 | 0 / 473 | 50,950,000 | 473 / 473 |

**Interpretation.** The original full auxiliary verification exceeds the 10% cap at every archived position for all three budgets. At 10k, 65 positions already exceed the cap using only independently metered depth-one probes, so the archived depth-one method cannot fit there. At 50k and 200k, no depth-one probe alone exceeds the cap, but this does **not** establish equal-compute feasibility. Probe costs are lower bounds on the old verification procedure; no capped runner has been executed or validated by this audit.

**Reproducibility.** `python -m research.mtdp.jass_benchmark.prospective_cost_audit --report research/mtdp/jass_benchmark/spatial-jass/replication/prospective-tiebreak-results.json.gz --budget 10000 --expected-positions 473` (repeat with 50000 and 200000). The CI step executes these checks automatically. Arena-level counts are included in the JSON output.

**Next experiment.** Pre-register a genuinely budget-capped verification procedure, count all auxiliary and main-search nodes together per position, and compare paired decisions and Scan regret on a held-out cohort. Do not interpret the retrospective 473-position audit as an equal-compute benchmark.
