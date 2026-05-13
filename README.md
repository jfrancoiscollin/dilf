# dilf

**Draught Intelligence Learning Framework** — deterministic pedagogy module for international draughts (FMJD 10×10).

The repository ships two cooperating pieces:

1. **`pedagogy/`** — a pure-Python library that turns a `GameState` into pedagogical *features* (material, mobility, structure, formations) and *motifs* (coup royal, coup turc, coup de talon, envoi à dame, prise max ratée, sacrifices). No engine, no API call, fully deterministic, 210 tests, `mypy --strict` clean.
2. **`scripts/extract_diagrams.py` + `.github/workflows/extract-diagrams.yml`** — a GitOps workflow that turns reference book PDFs (Dubois, Springer, Roozenburg, …) into Python fixtures usable by `pedagogy/tests/`. It uses Claude Vision to read each diagram on a GitHub Actions runner and opens a pull request with the result.

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
├── .github/workflows/
│   └── extract-diagrams.yml      # GitOps OCR pipeline (workflow_dispatch)
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

For the OCR workflow you also need the `extract` optional deps and `poppler-utils`:

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

## OCR workflow — Dubois & friends

`scripts/extract_diagrams.py` runs three idempotent steps:

| Step | Input | Output | Cost |
|---|---|---|---|
| `render` | PDF page range | Per-diagram PNG crops + `crops.json` | CPU only |
| `extract` | PNG crops | Per-diagram JSON positions via Claude Vision | ~$0.0014/diagram with Haiku 4.5 |
| `materialize` | `extracted.json` | `pedagogy/tests/fixtures/dubois_diagrams.py` | CPU only |

Run as a single chain:

```bash
python3 -m scripts.extract_diagrams all \
    --pdf docs/corpus/jpdubois_perfectionnement_combinaisons_V4.pdf \
    --pages 5-90 \
    --model claude-haiku-4-5
```

…or trigger the GitHub Actions workflow (`Actions → Extract diagrams (Claude Vision) → Run workflow`) which opens an auto-generated PR with the result.

Full details: **[docs/extract-diagrams.md](docs/extract-diagrams.md)**.

## Development

- **Tests**: `pytest` — 210 tests, runs in <1 s.
- **Type checking**: `mypy --strict pedagogy` — clean. The script (`scripts/extract_diagrams.py`) has 3 pre-existing strict-mode errors (untyped scipy import, `Any`-returning regex helpers); not in CI.
- **Style**: `black` configured at 100 columns. No CI enforcement yet.
- Tests for the script live in `scripts/tests/` and exercise the pure helpers only (validation, JSON parsing, caption counting). The image and API parts are validated by running the workflow.

## Branching

- `main` — production branch.
- `claude/read-spec-start-Ai5jV` — long-lived feature branch this assistant develops on. PRs go from this branch into `main`.

## License

MIT. See `pyproject.toml`.
