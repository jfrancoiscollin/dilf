# dilf

**Draught Intelligence Learning Framework** — deterministic pedagogy module for international draughts (FMJD 10×10).

The repository ships two cooperating pieces:

1. **`pedagogy/`** — a pure-Python library that turns a `GameState` into pedagogical *features* (material, mobility, structure, formations) and *motifs* (coup royal, coup turc, coup de talon, envoi à dame, prise max ratée, sacrifices). No engine, no API call, fully deterministic, 210 tests, `mypy --strict` clean.
2. **`scripts/extract_diagrams.py`** — a deterministic pure-CV pipeline that turns reference book PDFs (Dubois, Springer, Roozenburg, …) into Python fixtures usable by `pedagogy/tests/`. PDF pages are rasterised with `pdftoppm`, board regions are detected with scipy, and each of the 50 dark squares of every board is classified as white/black/empty by sampling the mean pixel value of a small patch. No LLM, no API, no network — ~1 minute wall to extract 324 positions from a 90-page book, $0 cost, fully deterministic.

The driving spec is `SPEC FRAMEWORK PEDAGOGIQUE.pdf` at the repo root.

## Layout

```
.
├── pedagogy/                     # core library (no I/O, no deps beyond stdlib)
│   ├── game.py                   # GameState, Player, Square typed primitives
│   ├── types.py                  # NewType aliases, structural protocols
│   ├── protocols.py              # Engine, Annotator, MotifDetector contracts
│   ├── features/                 # pure positional features
│   │   ├── material.py           # piece counts, ratios, kings
│   │   ├── geometry.py           # column/diagonal occupancy
│   │   ├── mobility.py           # legal-move enumeration (needs engine)
│   │   ├── structure.py          # bands, tempo, advanced-pawn count
│   │   └── formations.py         # classical, hek, drempel, oog, V-shape...
│   ├── motifs/                   # tactical-pattern detectors
│   │   ├── base.py               # MotifDetector ABC + Verdict dataclass
│   │   ├── coup_royal.py
│   │   ├── coup_turc.py
│   │   ├── coup_de_talon.py
│   │   ├── envoi_a_dame.py
│   │   ├── prise_max_ratee.py
│   │   └── sacrifices.py
│   └── tests/
│       ├── fixtures/             # hand-verified Dubois positions
│       │   └── dubois_coup_royal.py
│       ├── test_features_*.py
│       └── test_motifs_*.py
│
├── scripts/                      # build/tooling (optional install)
│   ├── extract_diagrams.py       # render → extract → materialize CLI
│   └── tests/test_extract_diagrams.py
│
├── docs/
│   ├── extract-diagrams.md       # detailed OCR workflow documentation
│   └── corpus/                   # reference corpus (53 books, ~6 100 pages)
│       ├── README.md             # index by language / author / type
│       └── *.pdf
│
└── SPEC FRAMEWORK PEDAGOGIQUE.pdf  # project spec (stays at root)
```

## Quickstart

```bash
git clone https://github.com/jfrancoiscollin/dilf.git
cd dilf
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                       # 210 tests
mypy --strict pedagogy       # clean
```

For the diagram extraction pipeline you also need the `extract` optional deps (pillow, numpy, scipy) and `poppler-utils`:

```bash
sudo apt-get install -y poppler-utils
pip install -e ".[extract]"
```

## Pedagogy module — how to use

```python
from pedagogy.game import GameState, Player
from pedagogy.features import material, structure, formations
from pedagogy.motifs import detect_all

state = GameState(
    white_men={31, 32, 33},
    white_kings=set(),
    black_men={1, 2, 3},
    black_kings=set(),
    turn=Player.WHITE,
)

# Features (pure, no engine needed)
material.piece_balance(state)
structure.advanced_pawn_count(state)
formations.has_classical_attack(state)

# Motifs (need an engine implementing protocols.Engine — Scan, sjaak,
# your own…)
verdicts = detect_all(state, engine=my_engine)
```

See `pedagogy/tests/` for end-to-end examples.

## Diagram extraction — Dubois & friends

`scripts/extract_diagrams.py` runs three idempotent steps:

| Step | Input | Output | Cost |
|---|---|---|---|
| `render` | PDF page range | Per-page PNG + per-board tight bbox + crops | CPU only |
| `extract` | `crops.json` + page PNGs | Per-diagram classified squares via pixel sampling | CPU only (~2 s for 324 crops) |
| `materialize` | `extracted.json` | `pedagogy/tests/fixtures/dubois_diagrams.py` | CPU only |

Run as a single chain:

```bash
python3 -m scripts.extract_diagrams all \
    --pdf docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf \
    --pages 5-90 \
    --white-threshold 225 \
    --black-threshold 100
```

This takes about a minute end-to-end on a laptop and produces 324 `DuboisDiagram` fixtures with zero API calls.

Full details: **[docs/extract-diagrams.md](docs/extract-diagrams.md)**.

## Development

- **Tests**: `pytest` — 187 in `pedagogy/tests/` + 28 in `scripts/tests/` (including synthetic-board CV tests for `analyze_board_fen`).
- **Type checking**: `mypy --strict pedagogy` — clean. The script (`scripts/extract_diagrams.py`) has some pre-existing strict-mode errors (untyped scipy import, `Any`-returning regex helpers); not in CI.
- **Style**: `black` configured at 100 columns. No CI enforcement yet.
- Tests for the script live in `scripts/tests/` and exercise the pure helpers (validation, caption counting, FMJD square numbering) plus the pixel-sampling extractor on synthetic boards.

## Branching

- `main` — production branch.
- `claude/read-spec-start-Ai5jV` — long-lived feature branch this assistant develops on. PRs go from this branch into `main`.

## License

MIT. See `pyproject.toml`.
