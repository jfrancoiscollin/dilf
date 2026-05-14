# ai-draught PR 7 — DB schema migration + `backend/pedagogy/storage.py`

> **Status**: **shipped** in `jfrancoiscollin/ai-draught` (renamed
> `draught-master`) on branch `develop` — see
> `backend/db/schema.py:126-178` (3 tables) and
> `backend/pedagogy/storage.py` (~372 lines). This file documents the
> design that landed and stays in dilf as the contract.
>
> Known residual gaps (tracked in a separate cleanup PR on
> draught-master):
> - Missing `idx_move_verdicts_motifs` JSON-extract index.
> - Missing `backend/pedagogy/README.md`.
> - Missing one ordering verification test
>   (`fetch_user_games_with_verdicts` DESC).
>
> **Important schema correction vs the first draft** of this file:
> `games.id` in ai-draught has always been `TEXT PRIMARY KEY` (UUID
> string), not `INTEGER`. Every `game_id` reference below is therefore
> `TEXT NOT NULL` (DDL) and `str` (Python). The original draft
> incorrectly typed it as `INTEGER` / `int` — fixed in the relevant
> blocks.
>
> Spec source: `SPEC FRAMEWORK PEDAGOGIQUE.pdf` §10 (schema) + §15
> (definition-of-done).

## Goal

Add three SQLite tables (`move_verdicts`, `pedagogy_explanations`,
`exercise_tags`) to the ai-draught backend and a small async helper
module `backend/pedagogy/storage.py` that round-trips
`MoveVerdict` / `GameAnalysis` / explanation rows.

This PR is **pure backend persistence**. No HTTP routes, no script — those
land in PR 8 and PR 13 respectively.

## Repo layout assumed (read before editing)

```
Ai-draught/
├── backend/
│   ├── main.py                # FastAPI entrypoint (do NOT touch in this PR)
│   ├── database.py            # compatibility shim re-exporting from db/
│   ├── db/
│   │   └── schema.py          # ← schema.py: extend init_db() here
│   ├── pedagogy/              # ← create this package
│   │   ├── __init__.py        # empty
│   │   └── storage.py         # ← created in this PR
│   ├── requirements.txt       # ← add dilf dependency
│   └── tests/
│       └── test_game_engine.py
```

ai-draught already uses **aiosqlite** (see `requirements.txt`). All DB I/O
in `storage.py` is `async`.

## Step 1 — `requirements.txt`

Add the dilf dependency at the bottom of `backend/requirements.txt`:

```
git+https://github.com/jfrancoiscollin/dilf.git@main#egg=dilf
```

Pin to a commit SHA later if dilf moves fast. For now `main` is fine —
the dilf surface (`pedagogy.types.MoveVerdict`, `pedagogy.types.UserProfile`,
`pedagogy.types.Phase`, `pedagogy.types.Verdict`, `pedagogy.types.MotifMatch`)
is stable post-PR-12.

The `[explanations]` extra brings in `scikit-learn` and `anthropic` —
opt-in:

```
git+https://github.com/jfrancoiscollin/dilf.git@main#egg=dilf[explanations]
```

Pick `[explanations]` if PR 8 will also be merged before deploy; otherwise
keep the bare install.

## Step 2 — `backend/db/schema.py`

Locate the `init_db()` function (or the equivalent place where the
existing `CREATE TABLE IF NOT EXISTS games …` calls live) and **append**
the following statements. Order matters because of foreign keys —
`exercise_tags` references `exercises`, `move_verdicts` references
`games`, `pedagogy_explanations` references `move_verdicts`.

```sql
CREATE TABLE IF NOT EXISTS move_verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,                      -- games.id is TEXT (UUID)
    move_number INTEGER NOT NULL,
    side TEXT NOT NULL,
    fen_before TEXT NOT NULL,
    fen_after TEXT NOT NULL,
    move_notation TEXT NOT NULL,
    score_before REAL NOT NULL,
    score_after REAL NOT NULL,
    delta_winchance REAL NOT NULL,
    verdict TEXT NOT NULL,
    is_forced INTEGER NOT NULL,
    phase TEXT NOT NULL,
    motifs_json TEXT NOT NULL,
    features_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE (game_id, move_number)
);
CREATE INDEX IF NOT EXISTS idx_move_verdicts_game ON move_verdicts(game_id);
CREATE INDEX IF NOT EXISTS idx_move_verdicts_verdict ON move_verdicts(verdict);
-- JSON-extract index for profile queries that filter by motif name.
CREATE INDEX IF NOT EXISTS idx_move_verdicts_motifs
    ON move_verdicts(json_extract(motifs_json, '$'));

CREATE TABLE IF NOT EXISTS pedagogy_explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    move_verdict_id INTEGER NOT NULL,
    mode TEXT NOT NULL,        -- 'template' | 'template+book' | 'claude'
    lang TEXT NOT NULL,        -- 'fr' | 'en'
    text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (move_verdict_id) REFERENCES move_verdicts(id) ON DELETE CASCADE,
    UNIQUE (move_verdict_id, mode, lang)
);

CREATE TABLE IF NOT EXISTS exercise_tags (
    exercise_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (exercise_id, tag),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_exercise_tags_tag ON exercise_tags(tag);
```

**Why `INTEGER NOT NULL` for `is_forced`**: SQLite has no native bool;
treat as `0`/`1`. The storage layer below already converts.

**Why a `UNIQUE` on `(game_id, move_number)`**: re-running
`analyze-game` must be idempotent. We `INSERT OR REPLACE` keyed by the
unique tuple.

**Why a `UNIQUE` on `(move_verdict_id, mode, lang)`**: same explanation
mode + language combo for the same verdict should de-dupe; re-runs
should overwrite, not append.

Notes for the implementer:

- ai-draught's `init_db()` is **idempotent** — `CREATE TABLE IF NOT
  EXISTS` is enough, no Alembic-style migration tracking needed for SQLite
  in this project.
- Confirm SQLite version exposes `json_extract` (`SELECT
  sqlite_version()` ≥ 3.38 — Python 3.11 ships with 3.40+ on most
  platforms, so this should be fine).
- If the project uses `aiosqlite.connect(...).execute(...)`, leave one
  `await conn.commit()` after all the new CREATE statements (existing
  code probably already does this).

## Step 3 — `backend/pedagogy/__init__.py`

Empty file. Just so the package is importable.

## Step 4 — `backend/pedagogy/storage.py` (~150 lines)

```python
"""Persistence helpers for the pedagogy layer.

Round-trips `MoveVerdict` / `GameAnalysis` / explanation rows between
the in-memory dataclasses (provided by the `dilf` package) and the
three SQLite tables added in db/schema.py.

All functions are async (aiosqlite). No FastAPI imports here — this
module is callable from a script (PR 13) as well as from the API
router (PR 8).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Optional

import aiosqlite

from pedagogy.types import (
    Features,
    GameAnalysis,
    MotifMatch,
    MoveVerdict,
    Phase,
    Verdict,
)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _motifs_to_json(motifs: list[MotifMatch]) -> str:
    return json.dumps([asdict(m) for m in motifs], ensure_ascii=False)


def _motifs_from_json(blob: str) -> list[MotifMatch]:
    raw = json.loads(blob)
    return [MotifMatch(**m) for m in raw]


def _features_to_json(features: Optional[Features]) -> Optional[str]:
    if features is None:
        return None
    return json.dumps(asdict(features), ensure_ascii=False, default=str)


def _features_from_json(blob: Optional[str]) -> Optional[Features]:
    if blob is None:
        return None
    raw = json.loads(blob)
    # `phase` is serialised as a string; rebuild the enum.
    raw["phase"] = Phase(raw["phase"])
    return Features(**raw)


# ---------------------------------------------------------------------------
# move_verdicts CRUD
# ---------------------------------------------------------------------------


async def upsert_move_verdict(
    conn: aiosqlite.Connection,
    game_id: str,
    verdict: MoveVerdict,
) -> int:
    """Insert or replace a verdict, return its row id."""
    await conn.execute(
        """
        INSERT OR REPLACE INTO move_verdicts
            (game_id, move_number, side, fen_before, fen_after, move_notation,
             score_before, score_after, delta_winchance, verdict, is_forced,
             phase, motifs_json, features_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game_id,
            verdict.move_number,
            verdict.side,
            verdict.fen_before,
            verdict.fen_after,
            verdict.move_notation,
            verdict.score_before,
            verdict.score_after,
            verdict.delta_winchance,
            verdict.verdict.value,
            1 if verdict.is_forced else 0,
            verdict.phase.value,
            _motifs_to_json(verdict.motifs),
            _features_to_json(verdict.features_before),
        ),
    )
    await conn.commit()
    cur = await conn.execute(
        "SELECT id FROM move_verdicts WHERE game_id = ? AND move_number = ?",
        (game_id, verdict.move_number),
    )
    row = await cur.fetchone()
    assert row is not None
    return int(row[0])


async def upsert_game_analysis(
    conn: aiosqlite.Connection,
    analysis: GameAnalysis,
) -> list[int]:
    """Upsert every MoveVerdict of a GameAnalysis. Returns the row ids."""
    ids: list[int] = []
    for v in analysis.verdicts:
        ids.append(await upsert_move_verdict(conn, analysis.game_id, v))
    return ids


async def get_move_verdict(
    conn: aiosqlite.Connection,
    game_id: str,
    move_number: int,
) -> Optional[MoveVerdict]:
    cur = await conn.execute(
        """
        SELECT move_number, side, fen_before, fen_after, move_notation,
               score_before, score_after, delta_winchance, verdict,
               is_forced, phase, motifs_json, features_json
          FROM move_verdicts
         WHERE game_id = ? AND move_number = ?
        """,
        (game_id, move_number),
    )
    row = await cur.fetchone()
    if row is None:
        return None
    return MoveVerdict(
        move_number=row[0],
        side=row[1],
        fen_before=row[2],
        fen_after=row[3],
        move_notation=row[4],
        score_before=row[5],
        score_after=row[6],
        delta_winchance=row[7],
        verdict=Verdict(row[8]),
        is_forced=bool(row[9]),
        phase=Phase(row[10]),
        motifs=_motifs_from_json(row[11]),
        features_before=_features_from_json(row[12]),
        features_after=None,  # not persisted to keep rows small
    )


async def fetch_user_games_with_verdicts(
    conn: aiosqlite.Connection,
    user_id: int,
    lookback: int = 30,
) -> list[GameAnalysis]:
    """Fetch the last `lookback` finished games of `user_id` and
    materialise their verdicts. Used by aggregate_user_profile()."""
    cur = await conn.execute(
        """
        SELECT id, user_side, opening_name
          FROM games
         WHERE user_id = ?
           AND status = 'finished'
         ORDER BY id DESC
         LIMIT ?
        """,
        (user_id, lookback),
    )
    games = await cur.fetchall()
    out: list[GameAnalysis] = []
    for row in games:
        game_id = str(row[0])
        verdicts = await _fetch_verdicts_for_game(conn, game_id)
        out.append(
            GameAnalysis(
                game_id=game_id,
                user_id=user_id,
                user_side=row[1],
                opening_name=row[2],
                verdicts=verdicts,
                summary={},
            )
        )
    return out


async def _fetch_verdicts_for_game(
    conn: aiosqlite.Connection, game_id: str
) -> list[MoveVerdict]:
    cur = await conn.execute(
        """
        SELECT move_number FROM move_verdicts
         WHERE game_id = ? ORDER BY move_number
        """,
        (game_id,),
    )
    move_numbers = [int(r[0]) for r in await cur.fetchall()]
    out: list[MoveVerdict] = []
    for mn in move_numbers:
        v = await get_move_verdict(conn, game_id, mn)
        if v is not None:
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# pedagogy_explanations
# ---------------------------------------------------------------------------


async def upsert_explanation(
    conn: aiosqlite.Connection,
    move_verdict_id: int,
    mode: str,
    lang: str,
    text: str,
) -> None:
    await conn.execute(
        """
        INSERT OR REPLACE INTO pedagogy_explanations
            (move_verdict_id, mode, lang, text)
        VALUES (?, ?, ?, ?)
        """,
        (move_verdict_id, mode, lang, text),
    )
    await conn.commit()


async def get_explanation(
    conn: aiosqlite.Connection,
    move_verdict_id: int,
    mode: str,
    lang: str,
) -> Optional[str]:
    cur = await conn.execute(
        """
        SELECT text FROM pedagogy_explanations
         WHERE move_verdict_id = ? AND mode = ? AND lang = ?
        """,
        (move_verdict_id, mode, lang),
    )
    row = await cur.fetchone()
    return str(row[0]) if row is not None else None


# ---------------------------------------------------------------------------
# exercise_tags
# ---------------------------------------------------------------------------


async def set_exercise_tags(
    conn: aiosqlite.Connection,
    exercise_id: int,
    tags: list[str],
) -> None:
    """Replace the tag set for one exercise atomically."""
    await conn.execute("DELETE FROM exercise_tags WHERE exercise_id = ?", (exercise_id,))
    for tag in tags:
        await conn.execute(
            "INSERT OR IGNORE INTO exercise_tags (exercise_id, tag) VALUES (?, ?)",
            (exercise_id, tag),
        )
    await conn.commit()


async def get_exercise_tags(
    conn: aiosqlite.Connection, exercise_id: int
) -> list[str]:
    cur = await conn.execute(
        "SELECT tag FROM exercise_tags WHERE exercise_id = ? ORDER BY tag",
        (exercise_id,),
    )
    return [str(r[0]) for r in await cur.fetchall()]


async def fetch_exercises_by_tags(
    conn: aiosqlite.Connection,
    tags: list[str],
    exclude_ids: list[int] | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return exercises matching ANY of `tags`, excluding `exclude_ids`."""
    if not tags:
        return []
    placeholders = ",".join("?" * len(tags))
    excl_clause = ""
    params: list[Any] = list(tags)
    if exclude_ids:
        excl_clause = (
            f" AND e.id NOT IN ({','.join('?' * len(exclude_ids))})"
        )
        params.extend(exclude_ids)
    params.append(limit)
    cur = await conn.execute(
        f"""
        SELECT DISTINCT e.id, e.title, e.fen_start
          FROM exercises e
          JOIN exercise_tags et ON et.exercise_id = e.id
         WHERE et.tag IN ({placeholders}){excl_clause}
         LIMIT ?
        """,
        params,
    )
    return [
        {"id": int(r[0]), "title": r[1], "fen_start": r[2]}
        for r in await cur.fetchall()
    ]


async def fetch_already_solved_exercise_ids(
    conn: aiosqlite.Connection, user_id: int
) -> list[int]:
    cur = await conn.execute(
        "SELECT exercise_id FROM user_exercise_solved WHERE user_id = ?",
        (user_id,),
    )
    return [int(r[0]) for r in await cur.fetchall()]
```

## Step 5 — tests

Create `backend/tests/test_pedagogy_storage.py` (~120 lines). Use the
same async-pytest pattern the existing `test_game_engine.py` already
uses (or fall back to `asyncio.run` wrappers if pytest-asyncio is not
installed).

Required test cases:

1. `test_upsert_move_verdict_round_trip` — write one `MoveVerdict`,
   read it back, assert dataclass equality (motifs included, features
   nullable).
2. `test_upsert_move_verdict_is_idempotent` — write twice with the
   same `(game_id, move_number)`, assert one row, last write wins.
3. `test_upsert_game_analysis_persists_all_verdicts` — analysis with
   3 verdicts → 3 rows.
4. `test_fetch_user_games_with_verdicts_orders_desc` — insert 2
   games, the most recent comes first.
5. `test_upsert_explanation_overwrites_same_mode_lang` — fr/template +
   fr/template should leave **one** row.
6. `test_upsert_explanation_distinguishes_lang` — fr/template +
   en/template = two rows.
7. `test_set_exercise_tags_replaces_atomically` — insert {a,b},
   replace with {b,c,d}, assert only those three.
8. `test_fetch_exercises_by_tags_excludes_solved` — pass
   `exclude_ids=[…]`, assert filtered.

Use an in-memory DB (`aiosqlite.connect(":memory:")`) and call
`init_db(conn)` once in a fixture. Verify the new tables exist with
`SELECT name FROM sqlite_master`.

## Step 6 — README

Append a short paragraph to `backend/pedagogy/README.md`
(create if absent):

> `storage.py` round-trips the dilf dataclasses into the three pedagogy
> tables. Schema lives in `db/schema.py`, tests in
> `backend/tests/test_pedagogy_storage.py`. Do not call this module from
> a request handler synchronously — every function is async.

## Acceptance criteria

- `init_db()` creates the 3 new tables on a fresh DB.
- `pytest backend/tests/test_pedagogy_storage.py` green.
- No regressions in existing `pytest backend/`.
- Imports work: `from pedagogy.types import MoveVerdict` etc.
- No new top-level imports inside `main.py`.

## Out of scope (do in PR 8 / PR 13)

- Wiring `storage.py` into HTTP routes.
- The `tag_existing_exercises.py` script.
- Auth checks on `user_id`.
- Frontend changes.
