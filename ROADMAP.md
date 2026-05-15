# dilf roadmap

Living document of what's shipped, what's next, and what's deliberately
deferred. Update when a tier item lands or when the priority of an item
changes.

## Where we are today

The pedagogy library is **feature-complete** per spec §15:

- Layers shipped: `features/`, `motifs/` (10 detectors — 6 P1 + 4 P2),
  `verdicts/`, `explanations/` (templates FR + EN, BookRAG, claude_writer
  with anti-hallucination guard, unified `explain_verdict` pipeline),
  `profile/`.
- 402 tests pass. `mypy --strict pedagogy` clean on 34 source files.
- Spec PRs landed: 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 14.
- Spec PRs intentionally out of scope for dilf: 7 (DB schema), 8 (FastAPI
  routes), 13 (tagging script) — all three are integration work that
  belongs in the parent project ``Ai-draught``.

A side-deliverable also shipped:

- `scripts/extract_diagrams.py` — deterministic pure-CV (pixel sampling)
  pipeline that extracts board positions from corpus PDFs. ~1 minute
  wall, $0, no LLM. Currently produces 324 hand-spot-checked positions
  from `jpdubois_perfectionnement_combinaisons_V4.pdf` in
  `pedagogy/tests/fixtures/dubois_diagrams.py`.

A new production workflow has also kicked off:

- **Pedagogical manuals pipeline** (`docs/pre_process_corpus/`). Rather
  than exposing the raw corpus to draught-master, we now produce one
  Claude-curated manual per level (Débutant, Intermédiaire, Avancé,
  Expert) on top of `extract_diagrams.py`. The Débutant manual is
  delivered (166 fixtures across 16 chapters, 135/135 `final_move` pass
  FMJD validation, round-trip FEN 166/166). See
  [`docs/MANUELS_PIPELINE.md`](docs/MANUELS_PIPELINE.md) for the
  end-to-end flow and [Tier 1.5](#tier-15--pedagogical-manuals-corpus--manuals--draught-master)
  below for the remaining cycles.

## Tier 1 — Make it real (top priority)

Goal: get the framework in front of users on real games so we can find
out where it's right and where it's miscalibrated.

The work for this tier lives in ``Ai-draught``, not dilf.

- [ ] **PR 7** (ai-draught) — DB schema migration: tables `move_verdicts`,
      `pedagogy_explanations`, `exercise_tags` in `backend/db/schema.py`.
      New module `backend/pedagogy/storage.py` for the read/write
      helpers. Round-trip tests.
- [ ] **PR 8** (ai-draught) — FastAPI router: `/api/pedagogy/analyze-game`,
      `/move-verdict/{game}/{move}`, `/explain-move`, `/profile/{id}`,
      `/profile/me/recommendations`. Wired into `backend/main.py`.
      Existing rate-limiter reused (5/min for `mode=claude`).
- [ ] **PR 13** (ai-draught) — `backend/pedagogy/scripts/tag_existing_exercises.py`
      run once in production to fill `exercise_tags` from the
      detectors. Idempotent.
- [ ] **Frontend wiring** — `AnalysisPanel.tsx` consumes
      `/api/pedagogy/move-verdict/...`. Profile page reads
      `/api/pedagogy/profile/me`. Mode selector
      (template / template+book / claude). FR/EN toggle.
- [ ] **Validation on real games** — analyze 5-10 personal Lidraughts
      games. Spot-check verdicts subjectively. Verify spec §15
      criterion: ≥ 80% of BLUNDER moves have at least one detected
      motif. Tune severity / thresholds if needed.
- [ ] **Deploy** — push `Ai-draught` to Railway (already configured
      via `railway.json`).

## Tier 1.5 — Pedagogical manuals (corpus → manuals → draught-master)

Goal: replace the direct exposure of the raw corpus to draught-master
with four Claude-preprocessed manuals (one per level). Decided after the
Débutant cycle exposed the cost of letting the app consume 53 PDFs
worth of unstructured material directly.

The workflow, tooling and anti-hallucination protocol live in
`docs/pre_process_corpus/` (`CADRAGE_MANUELS.md`, `JOURNAL.md`,
`ETAT_DILF.md`, `generate_chapter.py`, `validate_final_moves.py`). See
[`docs/MANUELS_PIPELINE.md`](docs/MANUELS_PIPELINE.md) for the full
description.

- [x] **Débutant manual** — 166 fixtures, 16 chapters, FEN round-trip
      166/166, `final_move` 135/135 validated by `validate_final_moves.py`,
      smoke-tested on draught-master (mai 2026).
- [ ] **Intermédiaire manual** — sources : `jpdubois_perfectionnement_sens_du_jeu_tome_1`
      + `jpdubois_perfectionnement_combinaisons_V4`. Target 200-250
      fixtures. Blocked until backlog §1 (standardised wrapper) and §4
      (PDF-typo detector) ship — these unblock fast production at scale.
- [ ] **Avancé manual** — sources : `sijbrandscourse` + `springercourse`.
      Multi-language pipeline tuning likely required (caption filter
      currently French-only, cf Tier 3 P3).
- [ ] **Expert manual** — sources : `maitrise-du-jeu-de-dames-dubois`
      + `jpdubois_expert_combinaisons_V2` + a master workbook. King
      detector (Tier 3 P2) prerequisite.
- [ ] **dilf backlog enabling §1 / §4 / §5 / §6** — wrapper
      standardisé, détecteur de coquilles, glossaire étendu, détecteurs
      de motifs pour les coups nommés. Items listed in
      `docs/pre_process_corpus/ETAT_DILF.md` §6. Closing §1 and §4 is
      the gating condition before launching Intermédiaire.

## Tier 2 — Quality and operations

Goal: prevent regressions and surface costs / failures fast.

- [ ] **CI on dilf** — `.github/workflows/ci.yml` runs `pytest` and
      `mypy --strict pedagogy` on every push to `main` and every PR.
- [ ] **Branch protection** on `main` — at minimum `Restrict deletions`
      and `Block force pushes`. Once CI exists, also require status
      checks.
- [ ] **Hand-curated reference fixtures** — pick 30 Dubois positions
      from the 324 currently in `dubois_diagrams.py`, verify each by
      eye against the PDF, gold-tag the expected motifs. These become
      the end-to-end test suite required by spec §11.
- [ ] **5 hand-annotated reference games** — promised by spec §11 but
      not yet shipped. PDN format, with expected verdicts per move.
- [ ] **Cost monitoring** — log token consumption on
      `/explain-move?mode=claude`. Alert on daily spend > $10.
- [ ] **Sentry context** — propagate game_id / user_id into the
      pedagogy Sentry breadcrumbs already configured in `Ai-draught`.

## Tier 3 — Extend the corpus

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
      `Ai-draught/scripts/book_extraction/configs/`. ~½ day.
- [ ] **P4** — Bulk-extract the remaining 44 non-Dubois PDFs. ~10 min
      CPU + 5-position spot-check per book (~½ day curation).
- [ ] **P5** — BookRAG multilingual: motif name → translations per
      language so `BookRAG.search("coup_royal")` also returns hits
      from English books mentioning "royal coup". ~½ day.

**Total**: ~3 days engineering + 1 day curation, $0 API. Do this after
Tier 1 validation, not before — Tier 1 might reveal we don't need most
of the corpus for the immediate product.

## Tier 4 — Ambition

Goal: ship beyond the spec. Not committed; each item earns its place
when the value is clear.

- [ ] **P3 motifs** from spec §1: `coup_de_mazette`, `coup_fabre`,
      `opposition`, `percee`, `enchainement`, plus finales detectors
      (`opposition_dame_pion`, `dame_contre_3_pions_diagonale`,
      `coup_de_l_escalier`).
- [ ] **Multi-half-move detector framework** — improve `coup_bonnard`
      (and future P3 motifs) with a 2-3 ply look-ahead via the PV.
- [ ] **Active learning loop on OCR** — capture per-position human
      corrections in `dubois_corrections.json`, feed them as few-shot
      examples on subsequent runs. Already partially designed; never
      shipped because we pivoted away from Vision.
- [ ] **Opening recognition** — extend `features/formations.py` with
      named opening detectors (Roozenburg, Keller, Ghestem,
      Souffleur, …).
- [ ] **dilf as a published PyPI package** — currently consumed via
      git URL. Publishing simplifies Ai-draught's `requirements.txt`.

## Out of scope

These items are deliberately not on the roadmap:

- Replacing the deterministic detectors with a learned model. The
  determinism is a feature; we want auditability.
- Real-time analysis during play. The framework is built around
  post-game analysis; live commentary would need a different
  architecture.
- Engine integration (Scan, sjaak). dilf consumes engines through
  `protocols.EngineProtocol` and `ScanProtocol`; the actual engines
  live in `Ai-draught/backend/`.

## How this document moves

When a tier item ships, check the box. When priorities change, edit
the relevant section and note the date. The current state section at
the top should always reflect what's actually on `main`.
