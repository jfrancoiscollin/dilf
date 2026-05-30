# Changelog

All notable changes to the dilf pedagogy library. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); dilf does not
yet publish numbered versions, so entries are grouped by date and
reference the commit / PR that landed them. The downstream consumer is
[`jfrancoiscollin/draught-master`](https://github.com/jfrancoiscollin/draught-master);
see `INTEROP.md` for the contract.

## Unreleased

### Docs

- **Note d'intégration : base de connaissances stratégique downstream**
  (`docs/integration/draught-master-strategy-knowledge-base.md`).
  Enregistre comment draught-master exploite le corpus prose de dilf
  (passages + ancres « Diagramme N ») pour rendre les diagrammes des
  manuels interactifs et en dériver une bibliothèque de positions, une
  base de connaissances thématique et des exercices. **Aucun changement
  de code dilf ni d'API** : le contrat `INTEROP.md` est inchangé.

### Fixed

- **Combinaison detectors fire under FMJD prise-max ties** (commit
  `9fccc1f`). `_walk_forced_chain` rejected the chain whenever the
  opponent had more than one legal move at any defensive ply. Under
  FMJD prise-maximale, multiple tied max-length captures are routine,
  so the strict guard silently killed almost every real-game
  combination. `_opp_is_forced` now also accepts positions where every
  legal reply is a capture (the opponent is materially committed even
  if they pick the path). When the PV names the chosen reply, the
  detector follows it instead of `opp_legal[0]`.

## 2026-05-16 — Generic forcing-combination family

### Added

- **Four new motif detectors** `combinaison_2_temps`,
  `combinaison_3_temps`, `combinaison_4_temps`, `combinaison_5_temps`
  (PR #38, commit `635d3c1`). Covers ad-hoc forcing sequences with no
  named pattern: the attacker plays N moves, the opponent's replies
  are forced, net material gain ≥ 1 pawn. Bucket on exact depth;
  5-temps catches chains ≥ 5 attacker moves.
- 11 detectors total in `ALL_DETECTORS`.

## 2026-05-14 — FMJD-strict sacrifice / promotion paths

### Added

- **`sacrifice` detector — `forced_reply` path** (PR #37). The
  detector now projects one half-move ahead via
  `engine.legal_moves(state_after)`; if every legal reply is a capture
  the projected post-capture position is used as the material yardstick.
  Captures sacrifices that are only visible after the opponent's forced
  recapture.
- **`envoi_a_dame` detector — `forced_promotion` path** (PR #37). Same
  projection trick: catches promotions that resolve after a forced
  defender capture.

## 2026-05-13 — Pedagogy framework feature-complete (spec §15)

### Added

- **Layers shipped end-to-end**: `features/`, `motifs/` (10 detectors
  at the time — 6 P1 + 4 P2), `verdicts/`, `explanations/` (templates
  FR/EN + BookRAG + claude_writer with anti-hallucination guard +
  unified `explain_verdict`), `profile/`.
- **502 tests pass**, `mypy --strict pedagogy` clean across 34 source
  files.
- **Spec PRs landed**: 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 14.
- **Side-deliverable**: `scripts/extract_diagrams.py` — deterministic
  pure-CV pipeline that extracts 324 hand-spot-checked positions from
  `jpdubois_perfectionnement_combinaisons_V4.pdf`.

### Stability contract

- **`INTEROP.md`** at the root (PR #29): every public symbol the
  downstream consumer relies on. CI-enforced via
  `.github/workflows/downstream-compat.yml`, which runs
  draught-master's `test_dilf_imports.py` against the candidate dilf
  ref on every push / PR.

## Out of scope / never going to ship

- Replacing the deterministic detectors with a learned model.
  Determinism is a feature (auditability).
- Real-time analysis during play. The framework is built for post-game
  analysis; live commentary would need a different architecture.
- Engine integration. dilf consumes engines through
  `protocols.EngineProtocol`; concrete engines live downstream in
  `draught-master/backend/`.
