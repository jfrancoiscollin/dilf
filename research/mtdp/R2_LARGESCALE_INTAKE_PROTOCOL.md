# MTDP-LargeScale — preregistered R2 corpus intake (proposal v0.1)

Status: **protocol only**. No R2 object was read, no Jass runner was dispatched, and no new FMJD computation was performed. This is an H43 foundation task; D1 retains ownership of decision-equivalence experiments.

## Verified provenance (GitHub control-plane metadata, not object readback)

- Private control plane: `jfrancoiscollin/jass-control`; remote named `r2:jass-data` (Cloudflare R2). No credentials or dashboard account identifiers are stored here.
- Completed job `ccx33-0832-l3-bucket-cumulative-v1`, source Jass code `f1c1f89282286286bac0e0e6b1c04d8d2e174a38`, status `completed`, exit 0, 2026-07-19; result URI `r2:jass-data/runs/ccx33-0832-l3-bucket-cumulative-v1/20260719T115948Z-f1c1f892`. Its **summary** reports ten `.jnnw` files, 1,500,000 records, 12,000,000 bucket visits, 191,533 visited buckets. These are *not* verified unique legal positions.
- Completed job `cpx62-1845-l3-decision-math-c-sibling-dataset-v2-v1`, source Jass code `4ae3fca82f19338132911811978761b91bd39573`, status `completed`, exit 0, 2026-09-06; result URI `r2:jass-data/runs/cpx62-1845-l3-decision-math-c-sibling-dataset-v2-v1/20260906T191758Z-4ae3fca8`. Summary reports 4,000 parents, 38,053 actions, split 3,200/400/400 train/valid/test; JSONL artifact listed (46,551,074 bytes). Its sample may overlap training or existing MTDP cohorts; do not declare independence.
- Sources: `jass-control/status/ccx33-0832-l3-bucket-cumulative-v1.json`, `jass-control/status/cpx62-1845-l3-decision-math-c-sibling-dataset-v2-v1.json`, `jass-control/specs/c-sibling-dataset-v2-v1.json`.

## Intake gates (in order)

1. **Read-only inventory first.** Retrieve R2 object listing, sizes, object version/ETag when available, manifest and per-object SHA-256. Record UTC capture, Jass code SHA, exact object keys and provenance. Do not trust ETag as a SHA-256 or assume `_SUCCESS` proves semantic validity. No credentials in Git.
2. **Format audit before scale.** Inspect small bounded byte samples of `.jnnw` and JSONL, identify version/encoding/record schema and whether each record contains a complete 10×10 board, side to move, kings, legal move, game/session ID, ply, outcome, policy/value labels. An `8cf` bucket visit is not a board position.
3. **FMJD admissibility.** Normalize only fully reconstructible states to a canonical 50-square representation with men/kings, side to move and rule variant; reject invalid records with reason counts. Where transitions exist, independently replay and check captures/promotions against pinned FMJD. Position-only records are **not** legal trajectory evidence.
4. **Leakage quarantine.** Before any D1 scoring, exclude PC Blues, historical reserved corpora, duplicate canonical positions/trajectories and shared self-play game/session lineage across train/validation/test. Use source-level and game-level splits; identical FEN hashes alone are insufficient proof of independence.
5. **Bounded pilot.** Deterministic seed and stable SHA-keyed stratified selection of at most 100,000 eligible records (phase, material, side to move, source and game); log attempted/accepted/rejected/unique positions and effective game count. Prefer streaming and resumable summaries, no bulk commit of corpus data.
6. **Descriptive analysis only.** Compute preregistered MTDP spatial metrics, per-stratum coverage, signature collision rates and confidence intervals clustered by game. Keep all D1 decision-equivalence or best-move testing in the D1 workstream, only after its separate admission gates.
7. **Scale decision.** Increase to 1M+ only after exact reproducibility (two independent runs same manifest and hashes), leakage audit, CPU/R2 operation-cost estimate and explicit authorization for any billable work.

## Safety and execution

- No production runner queue write, cloud instance launch, Cloudflare API calls or object downloads are authorized by this document. Jass-control `AGENTS.md` requires a separately sealed launch-admission v2 and target-host rehearsal; old `queue/done` scripts are archives, **not** launch templates.
- An existing read-only runner may later perform inventory under an approved admission and known cost ceiling; this protocol does not grant that approval.
- Keep D1 signatures, hypotheses, cohorts and thresholds unchanged.
- Local PC **not required** for documentation or GitHub metadata audit.

## Single next action

Obtain a **read-only, bounded inventory and format sample** from an already authorized R2 access path, with object hashes and a cost estimate; then implement a tested streaming parser only for the confirmed schema. Do not equate records, bucket visits, positions and independent games.

## Source-object caveat established from control-plane status

The `ccx33-0832-l3-bucket-cumulative-v1` **result URI is a report location, not a verified raw-corpus prefix**. The published `artefacts` list contains `RESULTS.txt`, `bucket-visits-cumulative.json`, `c0-decision.json`, `logs.tar.gz`, and `verified-c0.json` through `verified-c4.json`. Its `scientific_summaries.c0-decision.json.corpus.files` lists ten `/var/lib/jass-runner/.../work/c[0-4]-g[12].jnnw` **local runner paths**. No R2 object key, persistence guarantee or object hash for those ten raw files has been verified. Do **not** assume they can be downloaded from the result URI or remain available on the runner.

Before any download or reader execution, resolve the original dataset producer and exact immutable R2 source keys from its manifests/specs or a read-only R2 inventory. If the raw files are unavailable, report that gap rather than substitute a results summary. The report's 1.5M records and 12M bucket visits are aggregate counters, not unique-position counts.

## Exact source objects recovered (2026-11-21)

Pinned source: `jfrancoiscollin/jass@f1c1f89282286286bac0e0e6b1c04d8d2e174a38:jobs/templates/l3-bucket-visits-cumulative-v1.sh`. Its historical reader fetched two files per immutable source prefix via `jobs/tools/fetch_result_files.py`, checking `--expected-state completed` and publishing `verified-c0.json` through `verified-c4.json`. **These source keys are documented, but not yet read back by MTDP**:

| Cell | Exact R2 run prefix |
|---|---|
| c0 | `r2:jass-data/runs/cpx62-0817-l3-c2x1-hhh-control-v1/20260718T221711Z-7a35084f` |
| c1 | `r2:jass-data/runs/cpx62-0818-l3-c2x1-llh-v1/20260718T222242Z-7a35084f` |
| c2 | `r2:jass-data/runs/cpx62-0819-l3-c2x1-hll-v1/20260718T222759Z-7a35084f` |
| c3 | `r2:jass-data/runs/cpx62-0820-l3-c2x1-lhl-v1/20260718T223320Z-7a35084f` |
| c4 | `r2:jass-data/runs/cpx62-0821-l3-c2x1-center-v1/20260718T223829Z-7a35084f` |

For each prefix, source relative keys are `artefacts/g1-selfplay.jnnw.gz` and `artefacts/g2-selfplay.jnnw.gz` (10 compressed files total). This **supersedes the earlier ambiguity about the source keys**, but does not prove their present existence, content hash, retained access or cost. The archived script is evidence of provenance, **not** a permissible dispatch template under current launch-admission V2. Do not run it. A future authorized read-only inspection should use exact-key HEAD/list and bounded retrieval, verify source receipt and SHA-256, then decompress and audit a small bounded sample with explicit size/CPU ceilings. The five cells share seed `271828` and an experimental family: do not treat them as five independent validation cohorts.
