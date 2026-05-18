# dilf roadmap

Living document of what's shipped, what's next, and what's deliberately
deferred. Update when a tier item lands or when the priority of an item
changes. Companion changelog: `CHANGELOG.md`. Downstream consumer
roadmap: [`jfrancoiscollin/draught-master` ROADMAP.md](https://github.com/jfrancoiscollin/draught-master/blob/develop/ROADMAP.md).

## Where we are today

The pedagogy library is in production via draught-master. Current
`develop` HEAD is `9fccc1f`.

- **18 detectors** in `ALL_DETECTORS` (6 P1 + 4 P2 + 4 P3 + 4 generic
  forcing-combination family):
  - **P1** (6) — CoupRoyal, CoupTurc, CoupDeTalon, EnvoiADame,
    Sacrifice, PriseMaxRatee.
  - **P2** (4) — CoupPhilippe, CoupRaphael, CoupExpress, CoupBonnard.
  - **P3** (4) — CoupNapoleon, CoupManoury, CoupEnfilade, CoupDuBruleur.
  - **Generic** (4, PR #38) — Combinaison2TempsDetector through
    Combinaison5TempsDetector. Catches ad-hoc forcing sequences with
    no named pattern.
- 502 tests pass. `mypy --strict pedagogy` clean.
- `_walk_forced_chain` accepts FMJD prise-max ties as a forced reply
  (CHANGELOG.md "Unreleased") — combinations fire on real games where
  the defender has multiple equal-length captures.
- Spec PRs landed: 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 14. PRs 7/8/13
  (DB schema, FastAPI router, tagging script) shipped downstream in
  draught-master.

Side-deliverable:

- `scripts/extract_diagrams.py` — deterministic pure-CV (pixel sampling)
  pipeline that extracts board positions from corpus PDFs. ~1 minute
  wall, $0, no LLM. Currently produces 324 hand-spot-checked positions
  from `jpdubois_perfectionnement_combinaisons_V4.pdf` in
  `pedagogy/tests/fixtures/dubois_diagrams.py`.

## Tier 1 — Consolidate the FMJD relaxation

The combinaison detectors started firing on real games on 2026-05-17.
Validate before moving on.

- [ ] **Real-game regression set** — pick 5–10 Lidraughts PDNs with
      prise-max ambiguity (multi-path captures) and a known
      combinaison. Add as a pytest fixture exercising the real Scan
      engine through the assemble_verdict pipeline. Asserts the right
      `combinaison_N_temps` slug fires on the expected half-move.
      Owner: TBD. (S)
- [ ] **False-positive watch in staging** — if `_opp_is_forced` is
      too permissive (combis firing where the defender had a real
      choice), tighten by requiring uniform material gain across all
      tied legal captures. Re-evaluate after 1 week of real usage. (S)

## Tier 2 — closed (was: consumer contract gap)

The "missing helpers" item in INTEROP turned out to be documentation
drift, not engineering work: `pedagogy.notation.dubois.parse_move_notation`
shipped on 2026-05-15 (with king-rafle support) and consumers can call
`engine.apply_move` through their own `EngineProtocol` adapter. The
downstream tagging script imports both correctly and fires
capture-based detectors on real exercises.

Coverage proving this lives downstream in
`draught-master/backend/tests/test_tag_existing_exercises_real.py`.

## Tier 3 — CI and operations

Goal: prevent regressions and surface costs / failures fast.

- [ ] **CI on dilf** — `.github/workflows/ci.yml` runs `pytest` and
      `mypy --strict pedagogy` on every push to `main` and every PR.
      Already enforced indirectly via downstream-compat.yml, but a
      first-class workflow on this repo is overdue.
- [ ] **Branch protection** on `main` — `Restrict deletions`,
      `Block force pushes`. Once CI is in place, require status checks.
- [ ] **5 hand-annotated reference games** (spec §11) — PDN format
      with expected verdicts per move; round-tripped through the full
      pipeline as an end-to-end test.

## Tier 4 — Extend the corpus

Goal: turn the 53 PDFs in `docs/corpus/` (~6100 pages) into actual
test fixtures and BookRAG content. Right now only 86 pages of V4 are
exploited. Run in phases to avoid importing thousands of bad fixtures.

The current pipeline (`scripts/extract_diagrams.py`) blocks bulk
extraction for three reasons:

1. `_count_diagram_captions` requires French keywords (`trait aux`,
   `<n>e rafle`), so non-French books skip every page.
2. Thresholds (`--white-threshold 225 --black-threshold 100`) are
   calibrated for the V4 visual style. Other books vary.
3. No king detection — endgame-heavy books produce fixtures with
   `white_kings=[]` lies.

Phase plan:

- [ ] **P1** — Extract the 8 other Dubois PDFs with V4 thresholds.
      Spot-check 5 positions per book, decide if quality is mergeable.
      ~30 min curation, $0.
- [ ] **P2** — King detector: second-pass CV that looks at the centre
      patch of each detected piece for an inner-circle / crown
      contrast. Unblocks the endgame books (`apprentissage_fins_de_parties`,
      `perfectionnement_sens_du_jeu_tome_*`). ~1 day engineering.
- [ ] **P3** — Generalize caption filter. Either drop the
      French-keyword skip, or borrow the per-book config pattern from
      `draught-master/scripts/book_extraction/configs/`. ~½ day.
- [ ] **P4** — Bulk-extract the remaining 44 non-Dubois PDFs. ~10 min
      CPU + 5-position spot-check per book (~½ day curation).
- [ ] **P5** — BookRAG multilingual: motif name → translations per
      language so `BookRAG.search("coup_royal")` also returns hits
      from English books mentioning "royal coup". ~½ day.

**Total**: ~3 days engineering + 1 day curation, $0 API.

## Tier 5 — Ambition

Goal: ship beyond the spec. Not committed; each item earns its place
when the value is clear.

- [ ] **Remaining P3 motifs from spec §1**: `coup_de_mazette`,
      `coup_fabre`, `opposition`, `percee`, `enchainement`, plus
      finales detectors (`opposition_dame_pion`,
      `dame_contre_3_pions_diagonale`, `coup_de_l_escalier`).
- [ ] **Active learning loop on OCR** — capture per-position human
      corrections in `dubois_corrections.json`, feed them as few-shot
      examples on subsequent runs.
- [ ] **Opening recognition** — extend `features/formations.py` with
      named opening detectors (Roozenburg, Keller, Ghestem,
      Souffleur, …).
- [ ] **dilf as a published PyPI package** — currently consumed via
      git URL. Publishing simplifies draught-master's `requirements.txt`.

## Out of scope

These items are deliberately not on the roadmap:

- Replacing the deterministic detectors with a learned model. The
  determinism is a feature; we want auditability.
- Real-time analysis during play. The framework is built around
  post-game analysis; live commentary would need a different
  architecture.
- Engine integration (Scan, sjaak). dilf consumes engines through
  `protocols.EngineProtocol` and `ScanProtocol`; the actual engines
  live in `draught-master/backend/`.

## How this document moves

When a tier item ships, check the box and add an entry to
`CHANGELOG.md`. When priorities change, edit the relevant section and
note the date. The "Where we are today" section at the top should
always reflect what's actually on `develop`.
