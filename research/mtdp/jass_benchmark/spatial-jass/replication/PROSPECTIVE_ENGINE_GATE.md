# Prospective Jass engine integration gate — code audit

Status: **not integrated**; no prospective Jass run or 473-position result claimed.

## Inspected interfaces

- `prospective_tiebreak.choose_native_order_tie` is a pure Python selector. It requires an independently supplied canonical native legal-move order, integer scores, and **explicit exactness/completion evidence for every legal candidate**. It fails closed to the original LCB winner when evidence is missing.
- `jass_preflight/depth-one-winner.patch` is a **retrospective** intervention: it reads `MTDP_DEPTH_ONE_WINNER` from the environment and requires that the requested action's score equal `iter_score`. It does **not** compute a native-order winner and does **not** independently certify exactness of each alpha-beta root score.
- `spatial_tie_intervention.py` deliberately obtains `forced` from `case["original"]["native"]["winner"]`. This is valid for the published causal intervention, but **must never be used** as the prospective control.

## Blocking technical gap

An alpha-beta root action's reported score may be a bound after a window cutoff; equality of recorded integers is not by itself proof of equal minimax values. The current retrospective patch's `entry->score == iter_score` is therefore insufficient to authorize an outcome-blind prospective tie-break. Reusing it without new evidence would violate the preregistered protocol.

## Safe implementation sequence

1. Add a separate, opt-in Jass research mode; leave native and LCB baseline arms and production behavior untouched.
2. In the C++ runner, derive canonical native legal order from the **current position**, not archived native receipts. Confirm every key is unique, legal, and maps to the current root action list.
3. At the completed depth-one boundary, export each candidate's score **and bound type**, completion status, search window, root visit order, node count, and runner fingerprint. If bounds are not exact, do not change the winner. Alternatively perform a separately metered full-window verification; account for its nodes and do not describe the result as unchanged-budget.
4. Select the first native-ordered member of the verified exact-score maximum; preserve original root visitation and depth-one search log. Feed the choice through normal transposition and next-iteration bookkeeping. On missing or inconsistent evidence, retain original LCB choice and log the reason.
5. Add C++ integration tests for exact ties, bound-only apparent ties, illegal/missing moves, and no-tie fallback. Then build the pinned disposable Jass checkout, run the frozen 473-position cohort and verify both GitHub workflows. Keep the diagnostic 48-position sample separate from the prospective inference.

**Decision:** Do not wire `MTDP_DEPTH_ONE_WINNER` to archived native winners for prospective runs. Do not claim an engine integration until the exact-score evidence path and C++ integration tests exist.
