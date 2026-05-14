# ai-draught PR 13 — `backend/pedagogy/scripts/tag_existing_exercises.py`

> **Status**: **shipped** in `jfrancoiscollin/ai-draught` (renamed
> `draught-master`) on branch `develop` — see
> `backend/pedagogy/scripts/tag_existing_exercises.py` (~211 lines).
> Same argparse CLI (`--dry-run`, `--only`), same idempotent
> set-vs-set diff, same per-exercise error handling.
>
> Known residual gap (tracked in a separate cleanup PR on
> draught-master): the script has **no test file**. The 5 test cases
> listed in Step 3 below (happy path, idempotence, dry-run, invalid
> JSON, --only filter) are still to be implemented in
> `backend/tests/test_tag_existing_exercises.py`.
>
> Depends on: ai-draught PR 7 (the `exercise_tags` table exists and
> `storage.set_exercise_tags` works) — shipped.
>
> Spec source: `SPEC FRAMEWORK PEDAGOGIQUE.pdf` §10 (last paragraph)
> + §15.

## Goal

A **one-shot, idempotent** script that walks every row in
`exercises` and writes the motifs it triggers into `exercise_tags`.
After this runs once in production, `recommend_exercises()` returns
matches; before this runs, the recommender returns an empty list.

The script must:

- Be safe to re-run (rows already tagged with the same motif set are a
  no-op).
- Not crash on a malformed exercise — log and skip.
- Print a short summary at the end (`X exercises tagged, Y skipped,
  Z unchanged`).

## File layout

```
Ai-draught/backend/pedagogy/
├── api.py                     # (from PR 8)
├── storage.py                 # (from PR 7)
└── scripts/
    ├── __init__.py            # empty
    └── tag_existing_exercises.py  # ← this PR
```

## How exercises look in the DB

(Verify these column names in `backend/db/schema.py` first — adapt
queries below if they differ.)

```sql
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    fen_start TEXT NOT NULL,
    solution_moves_json TEXT NOT NULL,  -- JSON list of moves
    difficulty INTEGER,
    -- ... other fields
);
```

The "position of interest" for tagging is the FEN at `fen_start` plus
the first move from `solution_moves_json`. That's where the motif is
expected to occur.

## Step 1 — `backend/pedagogy/scripts/__init__.py`

Empty file.

## Step 2 — `backend/pedagogy/scripts/tag_existing_exercises.py` (~120 lines)

```python
"""Backfill exercise_tags from dilf's deterministic motif detectors.

Idempotent one-shot. Run once after the exercise_tags table is created,
and again if new detectors land. The script writes the **detected
motif set** for each exercise to exercise_tags, replacing any prior
tag set for that exercise.

Usage:
    python -m backend.pedagogy.scripts.tag_existing_exercises
    python -m backend.pedagogy.scripts.tag_existing_exercises --dry-run
    python -m backend.pedagogy.scripts.tag_existing_exercises --only 42 43 44
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Iterable, Optional

import aiosqlite

from pedagogy.game import GameState  # dilf
from pedagogy.motifs import ALL_DETECTORS  # dilf

from .. import storage
from ... import database as db_module

logger = logging.getLogger("pedagogy.tag_existing_exercises")


# ---------------------------------------------------------------------------
# Per-exercise tagging
# ---------------------------------------------------------------------------


def _detect_tags(fen_start: str, solution_moves: list[str]) -> set[str]:
    """Run every detector on (state_before, first_move, state_after).

    Returns the motif names that fired in any role. We don't store
    severity or role here — exercise_tags is just a coarse index for
    recommendations.
    """
    state_before = GameState.from_fen(fen_start)
    if not solution_moves:
        return set()

    # The exact API depends on how moves are stored. Two common shapes:
    #   solution_moves = ["32-28", "..."]  → parse via game_engine helper.
    #   solution_moves = [{"from": 32, "to": 28, "path": [32, 28]}, ...]
    # Adapt the line below to match the actual format in ai-draught.
    first_move = state_before.parse_move_notation(solution_moves[0])
    state_after = state_before.apply_move(first_move)

    tags: set[str] = set()
    for cls in ALL_DETECTORS:
        detector = cls()
        match = detector.detect(state_before, first_move, state_after)
        if match is not None:
            tags.add(match.motif)
    return tags


# ---------------------------------------------------------------------------
# DB iteration
# ---------------------------------------------------------------------------


async def _iter_exercises(
    conn: aiosqlite.Connection,
    only_ids: Optional[Iterable[int]] = None,
) -> list[tuple[int, str, list[str]]]:
    if only_ids:
        placeholders = ",".join("?" * len(list(only_ids)))
        cur = await conn.execute(
            f"SELECT id, fen_start, solution_moves_json FROM exercises "
            f"WHERE id IN ({placeholders})",
            tuple(only_ids),
        )
    else:
        cur = await conn.execute(
            "SELECT id, fen_start, solution_moves_json FROM exercises"
        )
    rows = await cur.fetchall()
    out: list[tuple[int, str, list[str]]] = []
    for row in rows:
        try:
            moves = json.loads(row[2])
        except (json.JSONDecodeError, TypeError):
            logger.warning("exercise %s has invalid solution_moves_json; skipping", row[0])
            continue
        out.append((int(row[0]), str(row[1]), list(moves)))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def _run(only_ids: Optional[list[int]], dry_run: bool) -> int:
    tagged = 0
    unchanged = 0
    skipped = 0

    async with aiosqlite.connect(db_module.DB_PATH) as conn:
        exercises = await _iter_exercises(conn, only_ids)
        for ex_id, fen, moves in exercises:
            try:
                new_tags = _detect_tags(fen, moves)
            except Exception as exc:  # noqa: BLE001 — log and continue, never crash
                logger.warning("exercise %s: detector error: %s", ex_id, exc)
                skipped += 1
                continue

            current = set(await storage.get_exercise_tags(conn, ex_id))
            if new_tags == current:
                unchanged += 1
                continue

            if dry_run:
                logger.info(
                    "[dry-run] exercise %s: %s -> %s",
                    ex_id, sorted(current), sorted(new_tags),
                )
                tagged += 1
                continue

            await storage.set_exercise_tags(conn, ex_id, sorted(new_tags))
            logger.info(
                "exercise %s tagged with %s",
                ex_id, sorted(new_tags) or "(none — cleared)",
            )
            tagged += 1

    logger.info(
        "done: %d tagged, %d unchanged, %d skipped",
        tagged, unchanged, skipped,
    )
    return 0 if skipped == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute the diff but don't write.")
    parser.add_argument("--only", type=int, nargs="*", default=None,
                        help="Only re-tag this/these exercise id(s).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return asyncio.run(_run(args.only, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
```

## Step 3 — Tests (`backend/tests/test_tag_existing_exercises.py`)

~80 lines. The tricky part is **isolating from real exercises**. Use
an in-memory DB seeded by the test:

```python
import pytest, aiosqlite, json

@pytest.mark.asyncio
async def test_run_tags_known_coup_royal_position(monkeypatch, tmp_path):
    # 1. Build an in-memory DB with one exercise that is a coup_royal.
    # 2. Monkeypatch backend.database.DB_PATH to a temp file path.
    # 3. Call _run(only_ids=None, dry_run=False).
    # 4. Assert exercise_tags contains "coup_royal" for that row.
    ...
```

Required cases:

1. `test_run_tags_known_coup_royal_position` — happy path.
2. `test_run_is_idempotent` — call twice, second run reports
   `unchanged == 1`, no DB churn.
3. `test_run_dry_run_does_not_write` — assert no rows in
   `exercise_tags` after `--dry-run`.
4. `test_run_skips_invalid_json` — exercise with garbage
   `solution_moves_json` → `skipped += 1`, exit code 1.
5. `test_run_only_filters_by_id` — seed 3 exercises, pass `--only 2`,
   only that one is touched.

Hand-curated FEN fixture for the coup_royal exercise: copy one
position from dilf's
`pedagogy/tests/fixtures/dubois_coup_royal.py`.

## Step 4 — Run in production

After deploy:

```bash
ssh <production-host>
cd /app/backend
python -m backend.pedagogy.scripts.tag_existing_exercises --verbose
```

Capture the summary line in the deploy log. Expected first-run output:

```
done: 217 tagged, 0 unchanged, 0 skipped
```

(Exercise count is illustrative — replace with the real number.)

## Acceptance criteria

- `pytest backend/tests/test_tag_existing_exercises.py` green.
- Script runs end-to-end on a copy of the production DB in < 5 minutes
  for the current exercise count.
- Re-running the script is a no-op (`unchanged == total`, 0 writes).
- `--dry-run` prints diffs without touching the DB.
- After the production run, `/api/pedagogy/profile/me/recommendations`
  returns a non-empty list for a user with a weakness on a tagged
  motif.

## Out of scope

- Tagging a single new exercise on insert. That's a future Phase
  (Tier 2 roadmap) — add a `pedagogy.api.exercises` POST hook that
  calls `_detect_tags` automatically.
- Multi-step exercises (chained motifs across moves). Today we only
  tag from the **first solution move**. If later we want to capture
  the whole sequence, extend `_detect_tags` to walk every move and
  union the tag sets.
- The `dame_contre_3_pions_diagonale` and other finales detectors
  that don't exist yet in dilf — they belong to ROADMAP Tier 4.

## Caveats for the implementer

- `GameState.from_fen` and `parse_move_notation` are dilf-side. If
  ai-draught has its own FEN/move parser (`backend/game_engine.py`),
  prefer dilf's so the tagger sees the same position the rest of the
  pedagogy layer sees. FEN format drift is the #1 source of bugs here
  (spec §14.1).
- The set-vs-set comparison in `_run` is what makes the script
  idempotent. Don't replace it with append-only logic.
- The detectors in `pedagogy.motifs.ALL_DETECTORS` evolve. When new
  detectors land in dilf, re-running this script may add tags to
  existing exercises. That's fine — `set_exercise_tags` is replace
  semantics.
