# H13 — king-origin-v1 bounded inventory impact protocol (2026-11-26)

Fixed before impact execution. Inputs are the COMPLETE authenticated JSONL
inventories: combined190 historical-quarantine possible boards, SHA-256
df9b357d08b9d6005d8b1726cb2e049d7dd1971dbf25b6210c54d7d86f66b8a1,
21645 distinct canonical FENs; fresh uDIrrl1c strict-complete-game footprint,
SHA-25662a71b82e09794ddd2bdc68d8c44749bf7741dddaee28a0722295a54abaac36e,
12795 distinct FENs. Audit their exact union, sorted lexicographically; no
sampling, replacement, outcome-based filtering or partition. Retain provenance
roles and owners. This is NOT the full452526-board historical cache or all old
scored populations, and not a corrected replay of the source games.

Compare unchanged FMJD0e5189f against explicit king-origin-v1 source4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d,
plus unchanged Jasscfe07fc legal exporter(native/SIMD disabled).
For every board record full Python action-path sets before/after, root
identities(endpoints+captured set+promotion), counts and set hashes. Compare
root sets with Jass, not landing-path identities. Report additions/removals,
path-only changes, old/new Jass disagreements, newly introduced disagreements,
duplicate reference roots and all affected source owners. Mismatches are
scientific outcomes, not reasons to tune the patch or exclude a position.
Require no changed Python actions on positions without an active-side king.

Fixed Jass batching:1000 consecutive sorted boards per process, timeout30s
each. Preserve concatenated raw catalogues, complete per-position ledger and
all change/mismatch witnesses with hashes. Two Python hash-seed runs and remote
Actions compare semantic outputs; binary/compiler provenance stays separate.
Python audit process capped at600s in workflow, no per-result population
reduction if the cap is hit.

No search, evaluation, model, target scores, signature/top-K/dimension campaign,
new games, source retrieval, cohort admission, corrected whole-game replay,
default engine/cache/quarantine replacement or scientific freeze. Four old
whole events remain excluded; fresh candidate unadmitted. Root/path changes
must not be mistaken for strategic disagreement, minimax proof or independent
evidence. Broader historical/scored-population impact remains out of scope.

Next: verify artifacts and enumerate concrete discrepancies; then separately
register corrected whole-game/quarantine/exclusion reconstruction or broader
historical impact as justified. Keep old proofs immutable. PC Jeff not needed.
