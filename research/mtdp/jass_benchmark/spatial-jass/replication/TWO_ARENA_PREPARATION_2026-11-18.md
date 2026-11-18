# Two future named arenas: pre-start proof and exclusion extension

The new registration/protocol were published in
[2a3089c](https://github.com/jfrancoiscollin/dilf/commit/2a3089c8b5e28787eb50de7a872d748fa7bbb679)
and their live presence on the freshly fetched research branch was verified at
**18 November22:20:37 UTC**, before both starts. The exact verification receipt
is `two-named-arenas-20261118-publication-proof.json`. It records selection and
analysis registration, **not a position freeze**. The immutable registration
and protocol hashes remain unchanged.

Whole events s7ahYqL4 (18 Nov23:00UTC /19 Nov00:00Paris) and D9PF2OSW
(19 Nov02:00UTC /03:00Paris) are reserved from D1. Final-game acquisition is
closed until **both** have finished, no earlier than19 Nov02:57UTC /03:57Paris.
No future game export, future position or score was acquired in this passage.
No first-global-eligible-event claim or outcome-based replacement is made.

## Extended historical exclusion inputs

`two_arena_exclusions` pins the existing registry/index, original legal adapter
and entire published P1RUlfJc export. It replays all241 games, preserving every
legally confirmed prefix including the9 whole-game quarantines. A quarantined
game receives no full-trajectory fingerprint and no state after ambiguity is
guessed. Every raw game ID and normalized token sequence remains excluded,
including duplicates/quarantines. These are historical exclusions only, never
candidate emissions or future-game selection.

The extension contains **23 PDNs,4616 historical games,4582 public IDs,4458
token-sequence hashes,4276 distinct complete legal trajectories and433363
confirmed FENs**. P1RUlfJc alone has230 distinct complete trajectories,2 repeated
games and9 quarantines;5 of its complete trajectories were already historical,
so225 genuinely new complete trajectories are added to4051. All411980 old
confirmed FENs remain, with21383 additional P1RUlfJc prefix FENs. The whole event
is excluded, rather than only its33 scored targets.

The full deterministic JSON was regenerated in separate processes under seeds7
and61 and compared byte for byte. Both have SHA-256
`8dac5c60e1eaa10ff8e3e27f5c1fb0d0307edaeaec438e7c9bdc33b3e666dc32`.
Its compact summary and reproduction receipt are committed; the full cache is
regenerated and retained in the existing candidate workflow artifact. The same
workflow compares its digest against the committed summary, preserving old
registry/index/replay checks and the synthetic FMJD/Jass rehearsal.

Reproduce with the pinned existing historical cache and legal adapter:

```sh
PYTHONHASHSEED=7 PYTHONPATH=.:../draught-master python -m research.mtdp.jass_benchmark.two_arena_exclusions \
  --root . --base-registry /tmp/mtdp-independent/P1RUlfJc-exclusions.json \
  --base-index /tmp/mtdp-independent/P1RUlfJc-canonical-history.json \
  --adapter ../draught-master --output /tmp/two-arena-exclusions-UNIQUE.json
```

The CLI never overwrites outputs. Repeat under61 and compare bytes. No new
cohort or engine-reference score is required to build this historical cache.

## Validation and next action

**146 targeted tests passed locally**, including17 registration-gate tests and4
exclusion-merge tests. They cover exact identities/format/pre-start evidence,
fixed references/budgets/seed, the joint final clock, both final metadata records,
exact publication SHA/no late pre-start proof, protocol-byte tampering, preserved
old FENs, all IDs/tokens, legal prefixes of quarantined games, forbidden full
quarantine trajectories, deterministic sorting and no mutation of inputs.
Real FMJD replay of241 P1RUlfJc games and two-process reproduction also passed.
New CI integration still needs confirmation on the published successor head.

Starting HEAD83ed1e8 had7/7 successful workflows; candidate44406015428 exposed
artifact14475696163 with published ZIP digest
`8a44aebbde4b5d2c3eadce1c7da6baa796051261116a47dc77552088a27c7ccb`
(metadata consulted; the already verified predecessor cache has identical pinned
registry/index bytes). No equivalent active/queued research campaign existed.

Next unique foundation action: implement an **explicit new-study** final-input,
cross-event whole-game/FEN exclusion and joint proposal/freeze adapter, test with
synthetic games, preserve the already frozen P1RUlfJc code/data, and refuse any
real game acquisition until the joint final gate. Populate full-quiet equality
labels before scores, reproduce both populations/action bijections under7/61,
then publish a joint freeze before source12/source16/target16 or Jass search.
Do not reuse the P1RUlfJc fixed-ID CLI by patching globals, IDs or clock guards.
No D1 signature/refinement/top-K campaign has been started. Jeff's PC is not
needed for these accessible remote input checks.


## Joint final acquisition adapter prepared — 22:33 UTC

`two_arena_acquisition` now provides explicit `acquire`/`check` modes for this
study. The real clock is checked before HTTP or directory creation. After the
joint finish, both finished metadata records must match before *any* game GET.
Then each event receives two distinct matching exports and independent request
IDs/timestamps/hashes, with all four IDs globally unique. Divergent pairs are
retained/retried; transport retries reuse the previously tested HTTP helper.
If a repeat download fails, its already acquired first bytes and receipt remain
on disk. Failures record their identity/attempt ledger, never a successful freeze.
Existing directories/results are refused, metadata prose is projected out, and
final validation rechecks both events and every receipt. Empty/non-PDN HTTP
responses are reported as input failure, never fabricated as scored zero results;
a valid replay with zero eligible targets must still be preserved by the next
population adapter.

**154 targeted local tests pass**, including8 new in-memory transport/future-clock
cases: premature access, metadata ordering, unfinished second event, divergent
pairs, technical repeat failure preserving the first response, changed bytes,
reused request ID, and overwrite refusal. A production CLI invocation with the
actual current clock was also refused before output creation. No real new game
export was downloaded and no future position/score was observed.

```sh
# Only after both registered finishes and actual finished metadata:
python -m research.mtdp.jass_benchmark.two_arena_acquisition acquire \
  --root . --directory /tmp/two-named-final-UNIQUE
python -m research.mtdp.jass_benchmark.two_arena_acquisition check \
  --root . --directory /tmp/two-named-final-UNIQUE
```

These successful input checks remain `scientific_freeze:false`. The remaining
next action is the explicit joint population/proposal/freeze adapter, including
whole-game/FEN cross-arena exclusions and exact Jass action mappings; test it
synthetically before using actual exports. Do not start source/target scoring or
Jass search without the joint published position freeze. D1 commits c9bd6b7,
9013d75,09d020d and1e08f8c were preserved; their latest coordination explicitly
acknowledges all four whole-event reservations. No D1 metrics or campaign was
modified here. New workflow confirmation remains pending.
