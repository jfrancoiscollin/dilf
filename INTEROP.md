# dilf ↔ draught-master interop contract

dilf is consumed by [`jfrancoiscollin/draught-master`](https://github.com/jfrancoiscollin/draught-master)
via its `backend/pedagogy/` package. This document is the **contract**
between the two repos. Anything listed here must not break without
coordinated changes on the consumer side.

A mirror of this document lives at
`backend/pedagogy/INTEROP.md` in draught-master.

## Pin

draught-master pins dilf from `backend/requirements.txt`:

```text
https://github.com/jfrancoiscollin/dilf/archive/refs/heads/main.tar.gz
```

i.e. the **`main` branch tarball**. Every dilf merge to `main` is
picked up by the next draught-master deploy. There is no version
locking, so dilf `main` must always be deployable.

For a hot-fix or a deliberately-coordinated bump, replace the tarball
URL with a specific commit SHA:

```text
https://github.com/jfrancoiscollin/dilf/archive/<sha>.tar.gz
```

## Public API surface

The symbols below are imported by draught-master. Removing, renaming,
or breaking the signature of any of them is a **breaking change** and
requires the two-step dance (see below).

| Module | Symbol | Kind | Stability |
|---|---|---|---|
| `pedagogy.types` | `Features` | dataclass | stable |
| `pedagogy.types` | `GameAnalysis` | dataclass | stable |
| `pedagogy.types` | `MotifMatch` | dataclass | stable |
| `pedagogy.types` | `MoveVerdict` | dataclass | stable |
| `pedagogy.types` | `Phase` | enum | stable |
| `pedagogy.types` | `Verdict` | enum | stable |
| `pedagogy.types` | `UserProfile` | dataclass | stable |
| `pedagogy.game` | `GameState` | dataclass | stable |
| `pedagogy.game` | `Move` | dataclass | stable |
| `pedagogy.game` | `parse_fen(fen: str) -> GameState` | function | stable |
| `pedagogy.motifs` | `ALL_DETECTORS` | `list[type]` | stable |
| `pedagogy.explanations` | `explain_verdict(verdict, *, mode, book_rag, lang)` | async function | stable |
| `pedagogy.explanations` | `BookRAG` | class | stable |
| `pedagogy.explanations.book_rag` | `BookRAG.from_directory(path)` | classmethod | stable |
| `pedagogy.profile.aggregator` | `aggregate_user_profile(user_id, games)` | function | stable |
| `pedagogy.profile.recommender` | `recommend_exercises(profile, pool, *, exclude_ids, n)` | function | stable |
| `pedagogy.verdicts.assembler` | `assemble_verdict(...)` | function | stable |
| `pedagogy.protocols` | `EngineProtocol` | typing.Protocol | stable |

### Stable dataclass invariants

For each `@dataclass` exposed:

- **Field names are part of the contract.** Renaming `MoveVerdict.delta_winchance` to `delta_winrate` is a breaking change.
- **Field types are part of the contract.** Tightening `Optional[Features]` to `Features` is a breaking change. Widening is breaking too because callers pattern-match on it.
- **Adding fields** is non-breaking **only if** they have defaults — otherwise existing callers' constructors break.
- Enum values (`Verdict.BLUNDER = "blunder"`) are persisted into the SQLite DB on the consumer side. Renaming the value (`"blunder"` → `"big_blunder"`) is a **data-migration-grade breaking change**.

### Currently-missing helpers (consumer fallback path)

These are imported by `draught-master/backend/pedagogy/scripts/tag_existing_exercises.py` inside a `try/except ImportError` block:

- `pedagogy.game.apply_move(state, move) -> GameState`
- `pedagogy.game.parse_move_notation(state, notation) -> Move`

They **do not exist** in dilf today. The consumer silently falls back to a partial implementation, which means capture-based detectors (`coup_royal`, `prise_max_ratee`, `coup_express`, ...) **never fire** on exercises. Adding these two helpers to dilf in a future PR is a non-breaking improvement — see ROADMAP.md Tier 4.

## Two-step dance for breaking changes

Because draught-master tracks dilf `main`, a breaking change in dilf
will break draught-master's next deploy. The contract is:

1. **First**: open a PR on draught-master that:
   - Updates the consumer code to the new dilf API.
   - Replaces the `main` tarball pin in `backend/requirements.txt`
     with the SHA the dilf PR is currently sitting on.
   - Stays in **draft** until step 2.
2. **Second**: merge the dilf PR, then push a commit on the
   draught-master PR that bumps the SHA pin to the actual merge SHA
   (or back to `main` tarball if the change is in `main`). Mark
   ready-for-review and merge.

The downstream-compat CI (see below) verifies step 1 by running
draught-master's pedagogy tests against the dilf PR before merge.

## CI enforcement

Two workflows protect this contract:

- **dilf** `.github/workflows/downstream-compat.yml`: on every push
  and PR, clones draught-master:develop, installs the current dilf
  ref, and runs draught-master's `backend/tests/test_pedagogy_*.py`.
  Failure blocks the dilf PR.
- **draught-master** `.github/workflows/dilf-compat.yml`: on every
  push and PR, installs the dilf pin from `backend/requirements.txt`
  and runs `backend/tests/test_dilf_imports.py`, a smoke test that
  imports every symbol listed above.

Locally, you can simulate the dilf check with:

```bash
pytest pedagogy/tests/test_public_api.py
```

This snapshot test fails fast if any symbol in the table above is
removed or renamed.

## Where to find what

- This file (dilf): the contract.
- `pedagogy/tests/test_public_api.py`: machine-enforced version of
  the table above.
- `.github/workflows/downstream-compat.yml`: runs draught-master's
  tests against this dilf PR.
- `.claude/settings.json` SessionStart hook: reminds the dev about
  the contract when a new Claude Code session opens this repo.
- ROADMAP.md Tier 2: tracks CI hardening + the `parse_move_notation`
  / `apply_move` helpers.
- ROADMAP.md "Out of scope": records what we deliberately do NOT
  expose (engine implementations, real-time analysis, learned
  detectors).
