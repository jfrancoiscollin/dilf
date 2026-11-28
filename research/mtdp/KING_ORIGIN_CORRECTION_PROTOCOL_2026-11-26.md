# H13 — isolated king-origin correction v1 regression protocol (2026-11-26)

Fix before patched execution. Base FMJD0e5189f, backend SHA-256
5855ceae76fc7db243af85c61508d9505e17904925b9f73d79ed327296690394.
Within _capture_sequences_king ONLY replace the one occurrence of
piece = board[s] with piece = EMPTY if s == path[0] else board[s].
All captured-piece blocking, maximum-capture, other-friendly blocking,
promotion and move application code remain identical. Guard original hash
and exact replacement count. Load corrected bytes as a uniquely named research
module and explicit DraughtMasterRules instance, not backend.game_engine.
Do not modify the pinned checkout, normal create_engine factory, old artifacts
or default workflows. Identify the result as king-origin-v1, not FMJD0e5189f.

Fixed regression population: the two return-capture witnesses48x48 and3x3;
their 180-degree/color-swapped counterparts; standard initial board;
man-loop prefix W:W20,26,28,32,33,38,39,43:B8,11,13,14,16,17,19,23,24,36;
quiet-king board W:WK28:B1; other-friendly blocker board W:WK3,14:B9,17,27,28.
Exactly eight boards, no additions or substitutions based on results.
Compare full root identities(endpoints+captured set+promotion) with unchanged
Jasscfe07fc legal exporter, native/SIMD disabled, timeout30s. Preserve Python
landing paths separately; root equality is not a played-path certificate.

Require the correction to restore the expected two tokens and their symmetric
counterparts, agree with Jass across all eight boards, preserve original
backend bytes/module/default factory, and leave man-only/initial controls
unchanged relative to legacy. Guard malformed/tampered source failure.
If any condition fails, report failure; do not tune the patch or controls on
that result. Preserve raw catalogue, corrected-source hash, binary provenance,
two-hash-seed reproducibility and remote Actions verification.

This is code regression evidence only. No historical corpus-wide impact
estimate, original trajectory rewrite, changed quarantine/cache, source
licence, scientific freeze, independent-cohort admission, signature/top-K/
dimension campaign or score/search. Next after passing: preregister a separate
impact audit over authenticated historical/fresh inventories before any revised
exclusion ledger or scoring. Four whole historical events remain reserved;
uDIrrl1c remains unadmitted. PC Jeff not required.
