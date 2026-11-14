# MTDP — top-three transfer results (2026-11-11)

Scan 3.1 depth-12 successor scores from the two pinned audits were reused for
the [preregistered diagnostic](TOP_THREE_TRANSFER_PROTOCOL.md). Top 1 and top 3
use the same canonical tie-break and the same scored pairs. Counts are
directional. Each position may occur in several pairs.

On the 241-game rapid holdout, PC Blues → rapid coverage rose from **96/249**
with one candidate to **184/249** with three. The number of ordinary losses of
at least 50 centimen fell from **13 to 0**, with maximum top-three regret of
**24 centimen**. The radius-two filter retained 52 of these transfers and
covered **45/52**. Within the rapid cohort, the top-three shortlist still left
**8 losses of at least 50 centimen in 1,480 ordinary transfers** across both
directions, all outside the radius-two subset. The largest was 248 centimen.

## Directional results

Counts of exact coverage are relative to all scored transfers. Positive and
≥50 regret counts and maxima use only ordinary scores, in centimen. Full set
counts transfers in which three candidates already exhaust the legal actions.
A→B is PC Blues → external for the cross-corpus pairs. Within the external
holdout, A/B are the labels in the frozen report.


### Frozen holdout

| Cohort and direction | Radius two | Transfers | Full set | Top 1 optimal | Top 3 optimal | Ordinary | Positive | ≥50 | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External A→B | All | 40 | 0 | 18 | 30 | 40 | 10 | 0 | 9 |
| External A→B | Retained | 13 | 0 | 7 | 11 | 13 | 2 | 0 | 1 |
| External A→B | Removed | 27 | 0 | 11 | 19 | 27 | 8 | 0 | 9 |
| External B→A | All | 40 | 0 | 21 | 31 | 40 | 9 | 0 | 15 |
| External B→A | Retained | 13 | 0 | 8 | 11 | 13 | 2 | 0 | 15 |
| External B→A | Removed | 27 | 0 | 13 | 20 | 27 | 7 | 0 | 5 |
| PC Blues → external | All | 95 | 0 | 45 | 75 | 95 | 20 | 0 | 8 |
| PC Blues → external | Retained | 35 | 0 | 23 | 32 | 35 | 3 | 0 | 6 |
| PC Blues → external | Removed | 60 | 0 | 22 | 43 | 60 | 17 | 0 | 8 |
| External → PC Blues | All | 95 | 0 | 40 | 74 | 95 | 21 | 0 | 13 |
| External → PC Blues | Retained | 35 | 0 | 19 | 30 | 35 | 5 | 0 | 9 |
| External → PC Blues | Removed | 60 | 0 | 21 | 44 | 60 | 16 | 0 | 13 |

### Rapid holdout

| Cohort and direction | Radius two | Transfers | Full set | Top 1 optimal | Top 3 optimal | Ordinary | Positive | ≥50 | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External A→B | All | 752 | 43 | 270 | 541 | 737 | 211 | 4 | 248 |
| External A→B | Retained | 201 | 26 | 92 | 171 | 193 | 30 | 0 | 15 |
| External A→B | Removed | 551 | 17 | 178 | 370 | 544 | 181 | 4 | 248 |
| External B→A | All | 752 | 43 | 271 | 540 | 743 | 212 | 4 | 189 |
| External B→A | Retained | 201 | 26 | 89 | 171 | 196 | 30 | 0 | 13 |
| External B→A | Removed | 551 | 17 | 182 | 369 | 547 | 182 | 4 | 189 |
| PC Blues → external | All | 249 | 0 | 96 | 184 | 249 | 65 | 0 | 24 |
| PC Blues → external | Retained | 52 | 0 | 25 | 45 | 52 | 7 | 0 | 5 |
| PC Blues → external | Removed | 197 | 0 | 71 | 139 | 197 | 58 | 0 | 24 |
| External → PC Blues | All | 249 | 0 | 100 | 179 | 249 | 70 | 0 | 23 |
| External → PC Blues | Retained | 52 | 0 | 28 | 44 | 52 | 8 | 0 | 4 |
| External → PC Blues | Removed | 197 | 0 | 72 | 135 | 197 | 62 | 0 | 23 |

The top-three shortlist exhausted the legal set in 86 of 1,504 within-rapid
transfers and in none of the cross-corpus transfers. It caused no score-category
switches in either report. The remaining 24 within-rapid nonordinary transfers
had the same category for the reference and the best transferred candidate;
their numerical regret is undefined. The top-one control caused 21
ordinary-to-loss switches within the rapid cohort.

These cohorts were already used for the preceding signature analyses. The
frozen holdout is mainly bullet; the rapid holdout comes from one tournament.
The diagnostic compares a shortlist of three with a single candidate. It leaves
open how much of the coverage gain comes from shortlist size and whether
prioritizing the transferred moves improves Jass search.

## Reproduction

Recover the JSON inputs using the [frozen depth-12 report](BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md)
and the [rapid holdout report](LOCAL_NEIGHBORHOOD_RESULTS_2026-11-11.md). Use the
input basenames below to reproduce the output hashes because the CLI includes
the basenames as output keys.

```sh
for k in 1 3; do
  python -m research.mtdp.top_k_transfer /tmp/depth-12.json /tmp/rapid-d12.json \
    --k "$k" --output "/tmp/top-$k.json"
done
sha256sum /tmp/depth-12.json /tmp/rapid-d12.json /tmp/top-1.json /tmp/top-3.json
```

| File | SHA-256 |
| --- | --- |
| `depth-12.json` | `29cd0c74a7e9469bcb5bf3775558f8f52ba975949d3637bbe4e07a2c031189b0` |
| `rapid-d12.json` | `224e9b74237adc396bdf4e2944c3da9ea0a0abec16195bcdb19222335ea8c173` |
| `top-1.json` | `145ee47b68048a21c7dfea7c46466ada85e88b01bcb52ecdd7b4ba4fe1101d1a` |
| `top-3.json` | `0b1e266580e3aab99327c50237700ef33d3d8303b44aa3a0a2302c58d1d55e8a` |

Both values of k reproduced byte-for-byte. All 2,272 directional transfers
were checked individually for monotonic coverage and, when ordinary at both k
values, nonincreasing regret. Counts reconcile across directions and the
radius-two partitions.

## Next experiment

Freeze a new set of independent games and a pinned Jass build before running
a paired move-ordering benchmark. Compare default Jass, promotion of up to
three transferred root moves, and promotion of the same number of canonically
ordered legal root moves. Use the same target FENs, legal actions, node budgets,
seeds, and initial transposition-table state for each variant. Keep the search
of nonprioritized moves enabled and report targets where the shortlist exhausts
the legal set separately. Use Scan 3.1 depth-12 destination regret and exact
coverage at fixed node budgets as outcomes. Record actual nodes and completed
depth; compare nodes at equal completed depth as a secondary measure. Freeze
the source-position selection and report match coverage before any runs. The
benchmark has yet to be run.
