# Q2 — Information-loss bounds from the archived R2 geometry pilot (2026-11-28)

Status: new **derived descriptive result**, not a new corpus experiment or efficacy result. Q2 of THREE_QUESTIONS_2026-11-26.md. No raw position/score access, engine calls, new cohort, freeze, pruning or production change.

## Inputs and result

Source: [RESULTS_R2_100K_GEOMETRY_2026-11-23.md](../RESULTS_R2_100K_GEOMETRY_2026-11-23.md), pinned at 6eeecb9b5497110056298345b5163894d8875ec8. The source reports N=98,306 distinct typed-board+turn keys, class counts K, nonsingleton class counts m, maximum class size M, and mixed-raw-WDL class counts. Use the uniform distribution on distinct board keys, NOT record frequency or a population estimate. All logs base 2.

For deterministic class label C=f(X), H(X|C)=log2(N)-H(C)=sum_i n_i log2(n_i)/N. This is lost exact-board identity information, **not decision information**, not actual encoded bytes and not a safe-pruning bound. Exact board entropy is 16.584991852 bits. The published aggregates do not identify the full size histogram, but give sharp bounds given only N,K,m,M.

| Representation | K | m | M | Loss lower (bits) | Loss upper (bits) | Mixed raw WDL / nonsingleton classes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Material | 2090 | 1649 | 1365 | 5.908531 | 10.058162 | 76.35% |
| Halves | 13494 | 7166 | 665 | 3.474818 | 7.569959 | 61.18% |
| Two rows | 69617 | 12235 | 121 | 0.735628 | 1.423068 | 60.94% |
| Rows | 93827 | 2203 | 76 | 0.111337 | 0.192552 | 61.33% |

Mixed raw labels are not independent reference outcomes; a position may carry multiple labels. Class-level fractions are NOT error rates, and cannot be interpreted as best-move regret. Neither cross-game coverage nor action maps are available in these aggregates. No independent corpus inferred. Half-board and two-row partitions are not nested.

## Derivation

There are K-m singleton classes and S=N-K+m nonsingleton members. For m>1, fix one class of size M. Convexity of g(x)=x log2 x implies that the lower bound is attained by making the remaining m-1 classes as equal as possible (integer floor/ceiling). For the upper bound, moving one member from a smaller class above size 2 to a larger class below M increases the convex sum: start with m classes of size 2, put the excess S-2m into classes up to M, then one partially filled class and the remaining classes of size 2. Both constructions respect the observed maximum for feasible summaries. Singleton contributions vanish. For m=0 loss=0; for m=1 loss=M log2(M)/N; for M=2 all nonsingletons have size 2.

Reproduction (Python standard library; input constants copied from the cited report):
```python
from math import log2

def bounds(n, k, m, M):
    assert n >= k >= 1 and 0 <= m <= k
    if m == 0:
        assert n == k and M == 1
        return 0., 0.
    S = n-k+m
    assert 2 <= M and M+2*(m-1) <= S <= m*M
    g = lambda x: x*log2(x)
    if m == 1 or M == 2:
        v = (g(M) if m == 1 else 2*m)/n
        return v, v
    q,r = divmod(S-M,m-1)
    lo = (g(M)+(m-1-r)*g(q)+r*g(q+1))/n
    t,u = divmod(S-2*m,M-2)
    hi = (t*g(M)+(g(2+u) if u else 0)
          +2*(m-t-int(bool(u))))/n
    return lo,hi

for k,m,M in [(2090,1649,1365),(13494,7166,665),
              (69617,12235,121),(93827,2203,76)]:
    print(bounds(98306,k,m,M))
```

Validation performed in the current analysis: equivalent JavaScript formula compared against exhaustive enumeration of all integer partitions of n=1..16, grouped by (n,k,m,M); all 794 feasible summary groups matched both extrema to 1e-10. This verifies the arithmetic, not the underlying archived experiment; Python snippet not separately executed. Existing report and reproductions unchanged.

## Next bounded hypothesis — action-relative abstraction (proposal, not frozen)

The existing Q signature keeps absolute mover squares; coarse board counts may group unrelated legal choices. Test a new action-centric representation instead of more global occupancy buckets. First scope to quiet man moves without active kings or compulsory captures; use the authenticated legal catalogue and explicitly versioned king-origin-v1 where required. Normalize mover color by a 180-degree rotation for black, keeping forward direction. For each legal action, encode displacement, local typed occupancy relative to origin/destination (diagonal graph distance 1, 2, 3), edge/promotion distance, and material counts as separately ablated feature blocks. Use explicit off-board symbols; retain action paths and original mapping externally. Treat all tactical/king/ambiguous cases as fallback, report them, and do not collapse legal actions. Do not select or order features using target scores.

First diagnostic: on historically admitted positions only, measure the distinct state/action counts, signature counts, collision class sizes, empirical label entropy, ambiguity/ties within a state, and cross-game coverage where real game provenance exists. Multiple actions sharing a local descriptor are indistinguishable to this descriptor, not equivalent. Compare same population against absolute L/Q controls and report fallback. If required raw historical catalogues or provenance are unavailable, record blocker and do not substitute reserved or raw unadmitted sources. No score acquisition until independent admission/freeze; no runtime claim before matched-cost experiment. This proposal is distinct from frozen E/L/LCB/Q/Q+ and does not change them.

Coordination: H:28 owns this Q2 diagnostic; H:43 handles mathematical counterexamples; H:13 handles gated search utility. Do not repeat closed successor audits. Before executing check for an active equivalent experiment and available data/compute within existing authorization.
