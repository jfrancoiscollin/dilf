# OCR workflow — diagram extraction

A GitOps pipeline that turns reference draughts books (PDF) into hand-reviewable Python fixtures usable by the `pedagogy/` test suite.

```
PDF page  →  pdftoppm  →  PNG/page  →  CV detection  →  PNG crops
                                                            ↓
       pedagogy/tests/fixtures/  ←  materialize  ←  Claude Vision  →  extracted.json
```

Everything is implemented in two files:
- `scripts/extract_diagrams.py` — CLI with three idempotent subcommands (`render`, `extract`, `materialize`) and a `all` wrapper.
- `.github/workflows/extract-diagrams.yml` — `workflow_dispatch` job that runs the chain on a GitHub Actions runner and opens a PR via `peter-evans/create-pull-request`.

## Why GitOps

The script needs three things that don't co-exist nicely on a laptop:
1. **Internet** to call `api.anthropic.com`.
2. **The `ANTHROPIC_API_KEY` secret**, but never on disk in plaintext.
3. **A clean Linux + `poppler-utils` + Python 3.11 environment** to render PDFs identically every run.

Running on a runner solves all three: the secret is injected via `${{ secrets.ANTHROPIC_API_KEY }}`, the runner is ephemeral, and the only artifact that touches the repo is the resulting PR.

## Running it from the GitHub UI

1. Add the API key once: `Settings → Secrets and variables → Actions → New repository secret` named `ANTHROPIC_API_KEY` (Anthropic Console standalone key, not the Claude Code OAuth account).
2. `Actions → Extract diagrams (Claude Vision) → Run workflow` and fill in:

| Input | Default | Meaning |
|---|---|---|
| `pdf` | `docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf` | Path on `main`, relative to repo root. The reference corpus lives under `docs/corpus/` (see its README for the catalogue). |
| `pages` | `5-90` | `"all"`, a single int, a range (`5-90`), or a CSV (`5,7,12`). |
| `max_diagrams` | `0` | Cap on API calls (0 = no cap). Use for cheap dry-runs. |
| `model` | `claude-haiku-4-5` | Any vision-capable Claude model. Sonnet is ~10× the cost. |
| `target_branch` | `claude/read-spec-start-Ai5jV` | Branch the auto-PR will target. |

3. Watch the job. When extraction is done it creates a branch `dubois-extract/run-<run_id>` with one file changed (`pedagogy/tests/fixtures/dubois_diagrams.py`) and opens a PR titled `Dubois diagrams from <pdf> (run <run_id>)`.

## Running it locally (for debug)

```bash
pip install -e ".[extract]"
sudo apt-get install -y poppler-utils

export ANTHROPIC_API_KEY=sk-ant-...
python3 -m scripts.extract_diagrams all \
    --pdf docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf \
    --pages 5-90 \
    --model claude-haiku-4-5 \
    --verbose
```

The three subcommands can also be run independently — handy for iterating on a single piece without burning API calls:

```bash
python3 -m scripts.extract_diagrams render     --pdf <pdf> --pages 5-90      # CPU only
python3 -m scripts.extract_diagrams extract    --cache .cache/diagrams        # API calls
python3 -m scripts.extract_diagrams materialize --cache .cache/diagrams       # CPU only
```

## What each step does

### `render`

For each requested page, the script:

1. Runs `pdftotext -layout` and counts diagram captions with the regex `trait aux | <n>e rafle` (case-insensitive). If a page yields zero matches it is **skipped** — there are no diagrams to extract.
2. Rasterises the page at 200 DPI via `pdftoppm`.
3. Detects board regions with PIL + scipy:
   - Threshold to black pixels (`DARK_THRESHOLD = 230`)
   - Dilate 5 iterations to merge board squares into one blob
   - Label connected components, keep those with area ≥ 150 000 px² and aspect ratio in `[0.85, 1.20]`
4. Pulls each bounding box down by ~60 px to capture the caption (`Dn : trait aux X`).
5. Saves the crops as `.cache/diagrams/crops/page_<n>_d<i>.png`, plus a `crops.json` manifest.

A `WARN expected N diagrams (from caption count), detected M board(s)` line is printed when caption count and CV detection disagree. After `fix(extract)` (PR #2) the caption count understands rafle continuations, so this warning fires only on real mismatches.

### `extract`

For each crop not yet recorded as successful in `extracted.json`:

1. Send the PNG + a system prompt (`SYSTEM_PROMPT`) describing the FMJD 10×10 numbering convention to the model. The user message is just `"Extract the position."`.
2. Parse the JSON response (`parse_api_response` strips Markdown fences if present).
3. Validate (`validate_position`): every square must be `1..50`, never appear in two of the four piece lists, and `turn` must be `"white"` or `"black"`.
4. **On failure (JSON parse or validation), retry exactly once** with `STRICT_SYSTEM_PROMPT` — same prompt plus a "CRITICAL INVARIANT" reminder + an instruction to recount before responding. `ExtractedDiagram.retries` records whether the result came from attempt 1 or 2.

After the loop, the script:

- Aggregates tokens (`input_tokens`, `output_tokens`) across all attempts of all crops.
- Computes the cumulative fail ratio over the whole `extracted.json` table.
- Returns exit code `0` if `fail_ratio ≤ --fail-threshold` (default 0.10), else `1`.

The tolerance threshold is what lets the workflow ship the PR even when a few diagrams fail. Without it, a single API hiccup in a 300-diagram run would block everything.

### `materialize`

Reads `extracted.json` and writes a Python module at `--output` (default `pedagogy/tests/fixtures/dubois_diagrams.py`) with one `DiagramFixture` per successful extraction. The file is regenerated whole on each run; treat it as machine-owned and never edit by hand.

## Caching semantics

`.cache/diagrams/` is the source of truth for re-runs:

- `crops.json` — manifest of detected crops (idempotent, no API cost).
- `extracted.json` — per-crop API result. **Re-running `extract` re-processes only entries that are missing or have `error is not None`.** Successful extractions are kept verbatim.

In the GitHub workflow, `actions/cache@v4` persists `.cache/diagrams/` keyed by `<pdf>-<pages>-<model>`. The second run on the same inputs only re-tries the failures.

## Failure handling and observability

```
[183/324] crops/page_054_d03.png
    VALIDATION (attempt 1): square 14 appears in more than one piece list
    VALIDATION (attempt 2): square 14 appears in more than one piece list
```

When you see two `(attempt N)` lines for the same crop, both the normal and the strict prompts have failed. That crop ends up in `extracted.json` with `error: "..."` and `retries: 1`, and the loop moves on.

End-of-run summary:

```
extract: 324 cached, 4 new failure(s) this run, 4 total failure(s) (1.2%); tokens in=263412 out=43021
```

Plus the workflow's `GITHUB_STEP_SUMMARY` markdown shows totals, top-20 errors, and tokens used.

## Cost estimate

Measured on `jpdubois_perfectionnement_combinaisons_V4.pdf` pages 5–90 with Haiku 4.5:

| Metric | Value |
|---|---|
| Diagrams | 324 |
| Input tokens | ~250 K |
| Output tokens | ~40 K |
| **Total cost** | **~$0.45** |
| Per diagram | ~$0.0014 |
| Wall clock (single runner) | ~10 min |

Extrapolation for the full corpus (~6 100 pages, ~18 000 diagrams):

- Sequential single runner: ~9 h wall (exceeds the 6 h GH Actions job limit — must be split).
- Matrix 20-way (1 PDF per job, 20 concurrent on free tier): ~1 h wall.
- **Total cost**: ~$25–30 with Haiku, ~$300 with Sonnet.

## Knobs to know

| CLI flag | Default | When to change |
|---|---|---|
| `--model` | `claude-haiku-4-5` | Switch to Sonnet on noisy scans where Haiku confuses pieces. ~10× the cost. |
| `--dpi` | 200 | Lower (150) for faster local iteration; raise (300) for blurry scans. |
| `--max-diagrams` | 0 | Cap to e.g. 6 during integration testing. |
| `--fail-threshold` | 0.10 | Lower to 0 for strict gating; raise to 0.20 when piloting a noisier book. |
| `--force` | off | Re-render PNGs even when cached. |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `no diagram caption, skipped` on every page | Book uses a different caption convention | Extend `_DIAGRAM_CAPTION_RE` in `scripts/extract_diagrams.py`. |
| `WARN expected N, detected M>N` on many pages | CV detects decorative borders or partial boards | Bump `MIN_BOARD_AREA` or `BOARD_ASPECT_RANGE`. Re-render to confirm. |
| `Resource not accessible by integration` on PR creation | `permissions:` block in workflow | Already set to `contents: write` + `pull-requests: write`. If forking, also enable "Allow GitHub Actions to create pull requests" in repo settings. |
| `VALIDATION` failures > 10% | Model genuinely struggles on this book's visuals | Try Sonnet, or hand-curate the failures from the workflow's artifact (`extracted.json` is uploaded for 30 days). |
| Workflow doesn't appear in the Actions tab | The `extract-diagrams.yml` file isn't on `main` | The default branch must contain the workflow file for `workflow_dispatch` to surface it. |

## File-by-file reference

- `scripts/extract_diagrams.py:53` — `DEFAULT_MODEL = "claude-haiku-4-5"`.
- `scripts/extract_diagrams.py:70` — `SYSTEM_PROMPT` (FMJD 10×10 numbering + JSON schema).
- `scripts/extract_diagrams.py:101` — `STRICT_SYSTEM_PROMPT` (retry prompt).
- `scripts/extract_diagrams.py:158` — `validate_position`.
- `scripts/extract_diagrams.py:246` — `_DIAGRAM_CAPTION_RE` (caption count for rendering / skip).
- `scripts/extract_diagrams.py:444` — `cmd_extract` (retry loop + threshold).
- `.github/workflows/extract-diagrams.yml` — full GitOps pipeline.

## Roadmap

Things deliberately left out of the current iteration:

- **Matrix across PDFs**: the workflow runs on one PDF at a time. To OCR the whole corpus in a single click, add a matrix strategy reading from a `corpus.yml` file. Estimated effort: 1 hour.
- **Mypy strict on scripts**: 3 pre-existing errors (untyped scipy, `Any`-returning regex). Add `scipy-stubs` + cast helpers. Effort: 30 min.
- **Sonnet retry on persistent failure**: when both Haiku attempts fail, escalate that single crop to Sonnet. Catches the ~1% of dense positions Haiku cannot read. Effort: 30 min.
