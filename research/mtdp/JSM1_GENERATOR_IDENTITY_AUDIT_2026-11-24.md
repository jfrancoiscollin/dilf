# H13 — initial M2 generator: identity semantics, not execution attestation

Static source inspection following the successful six-payload transformation
reproduction. No generator, engine or new corpus calculation was executed.

Pinned Jass commit: `012b9c716dadf2c3df668c23a7dd9d5ece423b8c`, named by the
home-0977 prepared contract as the M2 d8 source code. Exact inspected files:

| File | SHA-256 of git blob bytes |
| --- | --- |
| src/main.cpp | 98063885481c4af51e5aeaa4ad37b855dc794ded1a3810a26257b149f1ffc5de |
| jobs/templates/l3-pure-m2-train-v1.sh | 67a82ca928feea447cfbeea38879ad8dad887cbdcbfb6fc17837a423c4cc0dcf |

Primary code references (line numbers refer to that pinned revision):

- [main.cpp:648](https://github.com/jfrancoiscollin/jass/blob/012b9c716dadf2c3df668c23a7dd9d5ece423b8c/src/main.cpp#L648): game_count and opening_count begin at zero in each generator process. opening_count increments for a new opening; with pair_openings, two repetitions share the same opening position and opening_id (lines658–688).
- [main.cpp:951](https://github.com/jfrancoiscollin/jass/blob/012b9c716dadf2c3df668c23a7dd9d5ece423b8c/src/main.cpp#L951): each emitted metadata record receives the current game_count, opening_count and seeded byte, alongside the JNNW record. These are local synthetic self-play identities, not external tournament/game identifiers.
- [main.cpp:914](https://github.com/jfrancoiscollin/jass/blob/012b9c716dadf2c3df668c23a7dd9d5ece423b8c/src/main.cpp#L914): WDL follows eventual self-play outcome from side-to-move perspective; tablebase relabelling can replace it when enabled. It is not a per-action Scan reference score.
- [template:50](https://github.com/jfrancoiscollin/jass/blob/012b9c716dadf2c3df668c23a7dd9d5ece423b8c/jobs/templates/l3-pure-m2-train-v1.sh#L50): 12 producer processes, base seed1618033; lines162–176 request wdl-zero-score, pair-openings, drop-plycap, sample-meta-out and then merge pairs with a recorded merge manifest.

The generator code writes board and metadata rows in the same emission loop.
This authenticates the *code contract*. It does not attest that the published
initial pair came from an unmodified execution of this binary and these
parameters. The prepared shell entrypoint still requires EXPECTED_CODE_SHA
from its environment; its presence is not a completed-run receipt.

## Consequence for D1 admission

Run-local game IDs need the authenticated original producer/run namespace.
Two different game IDs can share an opening by design. A split by game alone
can therefore place paired opening repetitions on opposite sides, despite
no repeated numeric game ID. Preserve authenticated opening/trajectory groups
and investigate their dependencies before claiming independent partitions or
choosing a cluster/bootstrap unit. Namespacing IDs or counting 1024 distinct
sampled IDs does not solve this problem. This finding applies to these self-play
sources; it does not alter the completed PC Blues prospective results.

JSM1 omits ply and trajectories. Existing source inspection plus successful
byte-transform reproduction cannot manufacture those fields or prove exclusion
of historical events/positions. No independent cohort is admitted. Four entire
reserved PC Blues events remain excluded; no new cohort is frozen.

## Exact missing execution evidence / next action

For M2 source run `home-0966bis-l3-pure-m2-f2m-fresh2m-train-v1`, capture
`artefacts/m2-fresh-2m-merge.json`, producer input/output hashes and all twelve
`m2-s*.log` generation attestations, including actual code/binary, model,
parameters and completion counts. Authenticate their relation to published
`m2-d8` hashes. Retrieve corresponding original evidence for F2M common/extra
from the M1 source lineage before attempting trajectory/exclusion admission.
These receipts were not found in the inspected published position snapshot;
this does not assert they are absent from other archives. No R2 request or
paid retrieval is authorized by this audit.

Reproduce the static check without running Jass:

    git -C JASS show 012b9c716dadf2c3df668c23a7dd9d5ece423b8c:src/main.cpp > /tmp/m2-main.cpp
    sha256sum /tmp/m2-main.cpp
    sed -n '648,688p;910,960p' /tmp/m2-main.cpp
    git -C JASS show 012b9c716dadf2c3df668c23a7dd9d5ece423b8c:jobs/templates/l3-pure-m2-train-v1.sh | sha256sum

PC Jeff is not required for this completed source inspection. A future original
receipt may require an archive export; do not regenerate or retrospectively
label old records to replace missing execution provenance.
