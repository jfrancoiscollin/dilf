# OCR workflow — diagram extraction

A pure-CV pipeline that turns reference draughts books (PDF) into hand-reviewable Python fixtures usable by the `pedagogy/` test suite.

```
PDF page  →  pdftoppm  →  PNG/page  →  CV detection (scipy)  →  per-board bbox
                                                                       ↓
       pedagogy/tests/fixtures/  ←  materialize  ←  pixel sampling  ←  page PNG + bbox
                                                       (numpy)
```

Everything is implemented in **one file**, `scripts/extract_diagrams.py`, with three idempotent subcommands (`render`, `extract`, `materialize`) and an `all` wrapper.

## Why pure CV (no LLM)

Earlier iterations of this pipeline used Claude Vision per crop. The cost was real (hallucinations, rate limits, ~$1 per full V4 run, ~30 min wall) and the result unreliable: a 5-sample spot-check on the first successful run showed 4/5 fixtures fabricated (column-of-pieces patterns, invented kings).

Dubois diagrams are **printed** — they have crisp piece outlines, near-constant colours, and a known geometric grid. The right tool is pixel thresholding, not a multi-modal LLM. The current pipeline:

| Metric | This pipeline | Claude Vision approach we abandoned |
|---|---|---|
| Cost per V4 run | **$0** | ~$1.50 with Sonnet |
| Wall time | **~1 min** (mostly PDF render) | ~30 min |
| Deterministic | **Yes** (same input → same output) | No (model nondeterminism + retries) |
| Hallucination risk | **None** (it's pixel arithmetic) | Significant on dense positions |
| External deps | numpy, scipy, pillow, poppler | + anthropic SDK + API key + GH secrets |

The whole `extract` step is ~30 lines of numpy. The simplicity is the feature.

## Running it

### Locally

```bash
pip install -e ".[extract]"
sudo apt-get install -y poppler-utils

python3 -m scripts.extract_diagrams all \
    --pdf docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf \
    --pages 5-90 \
    --verbose
```

Output (after ~1 min):

```
render: 324 crop(s) ready -> .cache/diagrams/crops.json
[  1/324] crops/page_005_d01.png: 9W 9B turn=black OK
[  2/324] crops/page_005_d02.png: ...
...
extract: 324 cached, 0 new failure(s) this run, 0 total failure(s) (0.0%); elapsed 2.4s
materialize: wrote 324 fixture(s) to pedagogy/tests/fixtures/dubois_diagrams.py
```

### Subcommands

| Subcommand | Input | Output | Notes |
|---|---|---|---|
| `render` | PDF + page range | `pages/*.png` + `crops/*.png` + `crops.json` | CPU only. Idempotent — re-runs skip rendered pages unless `--force`. |
| `extract` | `crops.json` + `pages/*.png` | `extracted.json` | Pixel sampling, deterministic, ~2 s for 324 crops. |
| `materialize` | `extracted.json` | `pedagogy/tests/fixtures/dubois_diagrams.py` | Pure CPU. Writes one `DuboisDiagram` per successful entry. |
| `all` | PDF + page range | everything | Run end-to-end. |

## How each step works

### `render`

For each requested page:

1. Run `pdftotext -layout` and count diagram captions (regex matches `trait aux …` and `<n>e rafle` continuations). If zero, skip the page.
2. Rasterise the page at 200 DPI via `pdftoppm`.
3. Detect rough board components with scipy: threshold to dark pixels, dilate to merge each board's squares + border into one blob, label connected components, filter by area (≥ 150 000 px²) and aspect ratio (0.85–1.20).
4. **Shrink each rough component to its actual border rectangle.** Scan inward from each side and stop at the first row / column where ≥ 60% of the pixels are darker than 80. That line is the thick black board border. The returned bbox is the playable area only — without this step, the bbox would include the caption text below the diagram and the sampling grid downstream would be misaligned.
5. Save a padded crop (board + caption) as `crops/page_NNN_dXX.png` for visual review, and record the tight playable-area bbox in `crops.json`.

### `extract`

For each crop in `crops.json`:

1. Load the corresponding `pages/page_NNN.png` as grayscale (cached per page across the run).
2. Build a 10 × 10 grid inside the bbox (5 px inset margin to skip the border line).
3. For each of the 50 dark squares (`(row + col) % 2 == 1`):
   - Compute the centre pixel.
   - Sample a 16×16 patch (`sample_radius=8`).
   - Mean > 225 → white piece.
   - Mean < 100 → black piece.
   - Otherwise → empty.
4. Infer `turn` from the caption: `trait aux noirs` → black, else white (rafle continuations inherit white by convention).
5. Validate via `validate_position` (squares in range 1-50, disjoint piece lists, at least one piece per side).
6. Append an `ExtractedDiagram` record to `extracted.json`.

The thresholds (`--white-threshold 225`, `--black-threshold 100`) are calibrated for Dubois "perfectionnement combinaisons V4". They are CLI flags so other books with different visual styles can be supported by tuning two scalars.

### `materialize`

Reads `extracted.json` and writes a Python module at `--output` (default `pedagogy/tests/fixtures/dubois_diagrams.py`) with one `DuboisDiagram` per successful entry. The file is regenerated whole on each run.

Failed entries (those with `error is not None`) are NOT written. They stay in `extracted.json` for manual review.

## Cache

`.cache/diagrams/` is the source of truth:

- `pages/page_NNN.png` — rendered page images.
- `crops/page_NNN_dXX.png` — padded crops for visual review (not used by `extract`).
- `crops.json` — manifest with bbox + caption per detected board.
- `extracted.json` — sampled positions, including any errors.

Re-running `extract` is cheap (~2 s for 324 crops) so we don't bother with incremental skips: every call re-samples every crop and overwrites `extracted.json`. Re-running `render` skips already-rendered pages unless `--force`.

The whole cache directory is gitignored.

## Limitations

- **No king detection.** All pieces are classified as men. Pixel thresholding cannot distinguish a man from a king (both are filled circles; kings have an additional inner mark). For Dubois exercise positions, kings are rare and would need manual annotation — search for entries with a "rafle" caption or specific markers in the PDF text. A second-pass king detector (looking for a contrasting inner-circle pattern) is a clean follow-up if needed.
- **Threshold-tuned per book.** The two thresholds work for Dubois "perfectionnement combinaisons V4"; they would need re-tuning for books with different colour profiles. The simplest way to find new thresholds: render one page, dump the `analyze_board_fen` debug values for known empty / white / black squares, pick the midpoints.
- **Caption-based turn inference is shallow.** `trait aux noirs` → black, anything else → white. If a future book uses a different caption convention, the turn field may be wrong.
- **No engine validation.** The pipeline checks that the position is structurally valid (squares in range, no duplicates) but doesn't ensure it is legally reachable from the starting position. That's a separate concern — Scan or another engine can be plugged in downstream.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `no diagram caption, skipped` on every page | Book uses a different caption convention | Extend `_DIAGRAM_CAPTION_RE` in `scripts/extract_diagrams.py`. |
| Many positions show identical contiguous blocks like `white_men=[31..45]` | bbox includes the caption → grid is stretched | Confirmed already fixed by `_shrink_to_border`. If it recurs on a new book, check the border line is detectable (≥ 60% pixels darker than 80 along a row/column). |
| `extract: fail ratio … exceeds threshold` | Thresholds wrong for this book, or rendering DPI mismatch | Run `extract --verbose` to see per-crop counts, eyeball a few crops to identify whether whites or blacks are being missed. Tune `--white-threshold` / `--black-threshold`. |
| Many empty `white_men=[]` or `black_men=[]` lists | Thresholds too strict (white too high, black too low) | Lower `--white-threshold` (e.g. 215) or raise `--black-threshold` (e.g. 110). |
| Position has more pieces than the actual diagram | Thresholds too lax (catches empty dark squares as pieces) | Raise `--white-threshold` (try 230–240) or lower `--black-threshold` (try 80). |

## File-by-file reference

- `scripts/extract_diagrams.py:57` — `WHITE_PIECE_THRESHOLD = 200.0` (override via `--white-threshold` per book; V4 wants 225).
- `scripts/extract_diagrams.py:386` — `analyze_board_fen` (the ~30-line pixel sampler).
- `scripts/extract_diagrams.py:225` — `_shrink_to_border` (the bbox tightener that fixes the caption-inclusion bug).
- `scripts/extract_diagrams.py:264` — `_detect_boards` (the rough scipy detector that feeds the tightener).
