# H13 — historical byte-transform reproduction, preregistered

Input HEAD d47d0ff. The structural audit passes on six JNNW/JSM1 pairs but
cannot authenticate their row lineage. Primary Jass sources inspected:

- commit 336bb98451a205266d6646c4d801027af4b30294 (the home-0977 run suffix),
  tools/selfplay_frontier.py (SHA-256
  16724d0cd8748f3f2980bb210524f246f4838bea871c34cfe0f64a7b9260ce44),
  jobs/templates/l3-pure-m2-train-v1.sh;
- prepared job jobs/prepared/l3-pure-turnover-20260726/home-0977-l3-pure-turnover1to1-train-v1.sh
  inspected at Jass commit83914fbc7356862e768770fd33e766c2a2f3e7a9:
  explicit expected hashes for F2M, fresh M2 and TURNOVER match the published
  snapshot manifest. This later prepared script is a documentary contract,
  not the original executed run receipt.

Before real execution, freeze the following deterministic recipe from the
original code, with snapshot commit4ae90c3932f7cb0a10b5df27cfbd73cd220b6139
and manifest SHA-256 e41ad549a2d6d2259b1db03bb384eb98a565ae63c127b1b0b067c3a948df332c:

1. Extract and authenticate F2M common, F2M extra and fresh M2 pairs, gzip
   stored and decompressed size/SHA-256. No label-based selection.
2. Merge common then extra with --renamespace-nested; compare both output
   payload hashes with the published f2m.raw pair.
3. Mix PARENT reconstructed F2M and FRESH M2 with weights1:1, 2M output records,
   seed141421, --namespace-openings. Compare both hashes with turnover1to1.
4. Split that reconstructed pair with holdout-mod10 and seed577215; compare
   both hashes with m2.fit. The historical split reorders the entire counted
   corpus, including held-out records; its output need not be only train rows.

Run the original standalone Python tool, never the training shell script or
an engine. The wrapper pins its code SHA-256 before execution. Four new tests
check byte extraction, integrity attacks, metadata-only mismatch and rejection
of unpinned code; the eight preceding structural tests also remain required.
No equivalent lineage-reproduction workflow was active at preparation.

A command/IO failure is technical and must be diagnosed. A successfully computed
hash mismatch is a scientific negative result: preserve both expected and
observed hashes; do not alter recipe/seeds/expected hashes to force a match.
Report all three stages even if a previous comparison mismatches.

Even six matching output hashes prove only deterministic compatibility of the
published source pairs and these transforms. They cannot independently
establish that initial game/opening IDs, event ownership or source row pairing
were authentic when generated. No ply, trajectories, FMJD replay or exclusions
are supplied by this check. All corresponding admission flags remain false.
No fresh scores, model fit, signature selection, D1 rank campaign or prospective
cohort is authorized by this protocol; four entire reserved events stay excluded.

Reproduce with the pinned source/data checkouts:

    python -m unittest research.mtdp.tests.test_jsm1_lineage_reproduction research.mtdp.tests.test_jsm1_pair_audit
    python -m research.mtdp.jsm1_lineage_reproduction \
      --root snapshot-data/data/r2_positions/2026-11-21 \
      --frontier historical-jass/tools/selfplay_frontier.py \
      --work /tmp/new-lineage-work --output /tmp/new-lineage-report.json

After this check, inspect original generation code and independently pinned
run receipts that bind source board and metadata row identities. Only then
attempt whole-game trajectory/exclusion admission and a prospective equal-budget
Jass/Scan protocol. No R2 access, paid resource provisioning or Jeff PC required.
