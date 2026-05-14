# ai-draught PR 8 — `backend/pedagogy/api.py` (FastAPI router)

> **Status**: **shipped** in `jfrancoiscollin/ai-draught` (renamed
> `draught-master`) on branch `develop` — see
> `backend/pedagogy/api.py` (~476 lines) wired in `backend/main.py:139`.
> All 5 endpoints (`analyze-game`, `move-verdict`, `explain-move`,
> `profile/{user_id}`, `profile/me/recommendations`) are live, plus
> two bonuses (`/profile/me` and `/motifs/{slug}`) that landed beyond
> the original spec.
>
> Known residual gaps (tracked in a separate cleanup PR on
> draught-master):
> - `explain-move?mode=template` is not rate-limited (spec §14.6
>   asks for 60/min).
> - 3 of the 8 test cases listed below are missing
>   (`test_explain_move_template_mode_no_llm`,
>   `test_explain_move_uses_cache_on_second_call`,
>   `test_explain_move_different_lang_creates_separate_cache`,
>   `test_get_recommendations_filters_solved`).
>
> **Important schema correction vs the first draft** of this file:
> `games.id` is `TEXT PRIMARY KEY` (UUID), not `INTEGER`. Every
> `game_id` reference here is therefore `str` (Pydantic) / `TEXT`
> (DB). Same correction applied in the PR 7 spec.
>
> Depends on: ai-draught PR 7 (DB schema + `storage.py`) — shipped.
>
> Spec source: `SPEC FRAMEWORK PEDAGOGIQUE.pdf` §9.

## Goal

Add a FastAPI router exposing 5 endpoints under `/api/pedagogy/*` and
wire it into `backend/main.py` via `app.include_router(...)`.

The endpoints are **additive**. Existing frontend keeps working
untouched (spec §14.5).

## Files

```
Ai-draught/backend/
├── main.py                    # 1 line added: app.include_router(pedagogy_router)
├── pedagogy/
│   ├── api.py                 # ← created here
│   ├── models.py              # ← Pydantic request/response models
│   └── storage.py             # (from PR 7 — read-only here)
└── tests/
    └── test_pedagogy_api.py   # ← new
```

## Step 1 — `backend/pedagogy/models.py` (~80 lines)

Pydantic schemas. Keep these separate from `pedagogy.types` (dilf) so
the wire format and the in-memory dataclass can evolve independently.

```python
"""Pydantic models for the /api/pedagogy/* routes (PR 8)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class AnalyzeGameRequest(BaseModel):
    """One of game_id / pdn is required."""

    game_id: Optional[str] = None       # games.id is a TEXT UUID
    pdn: Optional[str] = None
    user_side: Optional[str] = Field(default=None, pattern="^(white|black)$")
    lang: str = Field(default="fr", pattern="^(fr|en)$")


class ExplainMoveRequest(BaseModel):
    game_id: str                                  # TEXT UUID
    move_number: int
    mode: str = Field(default="template", pattern="^(template|template\\+book|claude)$")
    lang: str = Field(default="fr", pattern="^(fr|en)$")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class MotifMatchOut(BaseModel):
    motif: str
    role: str
    squares: list[int]
    pv: list[str]
    severity: float
    metadata: dict[str, Any] = {}


class MoveVerdictOut(BaseModel):
    move_number: int
    side: str
    move_notation: str
    fen_before: str
    fen_after: str
    score_before: float
    score_after: float
    delta_winchance: float
    verdict: str
    is_forced: bool
    phase: str
    motifs: list[MotifMatchOut] = []


class AnalyzeGameResponse(BaseModel):
    game_id: str
    verdicts: list[MoveVerdictOut]
    summary: dict[str, Any] = {}


class ExplainMoveResponse(BaseModel):
    text: str
    mode: str
    lang: str
    cached: bool


class UserProfileOut(BaseModel):
    user_id: int
    games_count: int
    average_accuracy: float
    strengths: list[dict[str, Any]]
    weaknesses: list[dict[str, Any]]
    weakest_phase: str
    recommended_exercise_tags: list[str]


class RecommendationsResponse(BaseModel):
    exercises: list[dict[str, Any]]
```

## Step 2 — `backend/pedagogy/api.py` (~150 lines)

```python
"""FastAPI router for the pedagogy layer (spec §9)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from pedagogy.explanations import explain_verdict
from pedagogy.profile.aggregator import aggregate_user_profile
from pedagogy.profile.recommender import recommend_exercises

from .. import database as db_module
from ..auth import current_user  # reuse the existing dependency
from . import storage
from .models import (
    AnalyzeGameRequest,
    AnalyzeGameResponse,
    ExplainMoveRequest,
    ExplainMoveResponse,
    MotifMatchOut,
    MoveVerdictOut,
    RecommendationsResponse,
    UserProfileOut,
)

# Reuse main.py's rate limiter. Import lazily inside the handler to
# avoid circular imports.

router = APIRouter(prefix="/api/pedagogy", tags=["pedagogy"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _verdict_to_out(v: Any) -> MoveVerdictOut:
    return MoveVerdictOut(
        move_number=v.move_number,
        side=v.side,
        move_notation=v.move_notation,
        fen_before=v.fen_before,
        fen_after=v.fen_after,
        score_before=v.score_before,
        score_after=v.score_after,
        delta_winchance=v.delta_winchance,
        verdict=v.verdict.value if hasattr(v.verdict, "value") else v.verdict,
        is_forced=v.is_forced,
        phase=v.phase.value if hasattr(v.phase, "value") else v.phase,
        motifs=[MotifMatchOut(**asdict(m)) for m in v.motifs],
    )


# ---------------------------------------------------------------------------
# POST /api/pedagogy/analyze-game
# ---------------------------------------------------------------------------


@router.post("/analyze-game", response_model=AnalyzeGameResponse)
async def analyze_game(
    req: AnalyzeGameRequest,
    user: Any = Depends(current_user),
) -> AnalyzeGameResponse:
    """Run dilf's `assemble_verdict` on every half-move of a game.

    - Reuses `opening_book_db` for cache hits where available.
    - Rate-limited 3/min via the existing main.py limiter.
    - Writes to `move_verdicts` (idempotent on (game_id, move_number)).
    """
    # 1. Resolve game source ----------------------------------------------------
    if req.game_id is None and not req.pdn:
        raise HTTPException(422, "game_id or pdn is required")
    # 2. Pull moves + Scan scores (same path the existing /api/analyze uses).
    # 3. Call dilf.assemble_verdict per half-move.
    # 4. Persist via storage.upsert_game_analysis.
    #
    # The first three steps are not re-specified here because they are
    # internal to ai-draught — the code that fetches PDN, calls the Scan
    # engine, and uses the opening book already exists in
    # backend/game_engine.py / backend/scan_engine.py. Plug them in.
    raise NotImplementedError(
        "Wire up to backend/game_engine.py + dilf.verdicts.assembler."
    )


# ---------------------------------------------------------------------------
# GET /api/pedagogy/move-verdict/{game_id}/{move_number}
# ---------------------------------------------------------------------------


@router.get(
    "/move-verdict/{game_id}/{move_number}",
    response_model=MoveVerdictOut,
)
async def get_move_verdict(
    game_id: str,
    move_number: int,
    user: Any = Depends(current_user),
) -> MoveVerdictOut:
    async with aiosqlite.connect(db_module.DB_PATH) as conn:
        v = await storage.get_move_verdict(conn, game_id, move_number)
    if v is None:
        raise HTTPException(404, "Verdict not yet computed for this move")
    return _verdict_to_out(v)


# ---------------------------------------------------------------------------
# POST /api/pedagogy/explain-move
# ---------------------------------------------------------------------------


@router.post("/explain-move", response_model=ExplainMoveResponse)
async def explain_move(
    req: ExplainMoveRequest,
    user: Any = Depends(current_user),
) -> ExplainMoveResponse:
    """Return a 1-3 sentence commentary for one verdict.

    Caches in `pedagogy_explanations`. Modes:
      - "template":     no LLM
      - "template+book": templates + BookRAG excerpts
      - "claude":       full Claude commentary with anti-hallucination

    Rate-limited 5/min on "claude" (existing limiter), 60/min on the rest.
    """
    # Rate limit (claude only) — reuse main.py's limiter.
    if req.mode == "claude":
        from ..main import claude_rate_limiter  # late import to avoid cycle

        await claude_rate_limiter.check(user.id)

    async with aiosqlite.connect(db_module.DB_PATH) as conn:
        # 1. Load the verdict row id + the dilf MoveVerdict.
        v = await storage.get_move_verdict(conn, req.game_id, req.move_number)
        if v is None:
            raise HTTPException(404, "Verdict not yet computed for this move")
        cur = await conn.execute(
            "SELECT id FROM move_verdicts WHERE game_id = ? AND move_number = ?",
            (req.game_id, req.move_number),
        )
        row = await cur.fetchone()
        assert row is not None
        verdict_id = int(row[0])

        # 2. Try cache.
        cached = await storage.get_explanation(conn, verdict_id, req.mode, req.lang)
        if cached is not None:
            return ExplainMoveResponse(
                text=cached, mode=req.mode, lang=req.lang, cached=True
            )

        # 3. Generate.
        from ..main import shared_book_rag  # global singleton built at startup

        text = await explain_verdict(
            v,
            mode=req.mode,
            book_rag=shared_book_rag,
            lang=req.lang,
        )

        # 4. Persist + return.
        await storage.upsert_explanation(conn, verdict_id, req.mode, req.lang, text)
        return ExplainMoveResponse(
            text=text, mode=req.mode, lang=req.lang, cached=False
        )


# ---------------------------------------------------------------------------
# GET /api/pedagogy/profile/{user_id}
# ---------------------------------------------------------------------------


@router.get("/profile/{user_id}", response_model=UserProfileOut)
async def get_user_profile(
    user_id: int,
    user: Any = Depends(current_user),
) -> UserProfileOut:
    if user.id != user_id and not getattr(user, "is_admin", False):
        raise HTTPException(403, "Forbidden")
    async with aiosqlite.connect(db_module.DB_PATH) as conn:
        games = await storage.fetch_user_games_with_verdicts(conn, user_id, lookback=30)
    profile = aggregate_user_profile(user_id, games)
    return UserProfileOut(
        user_id=profile.user_id,
        games_count=profile.games_count,
        average_accuracy=profile.average_accuracy,
        strengths=profile.strengths,
        weaknesses=profile.weaknesses,
        weakest_phase=profile.weakest_phase.value,
        recommended_exercise_tags=profile.recommended_exercise_tags,
    )


# ---------------------------------------------------------------------------
# GET /api/pedagogy/profile/me/recommendations
# ---------------------------------------------------------------------------


@router.get(
    "/profile/me/recommendations",
    response_model=RecommendationsResponse,
)
async def get_recommendations(
    n: int = 10,
    user: Any = Depends(current_user),
) -> RecommendationsResponse:
    async with aiosqlite.connect(db_module.DB_PATH) as conn:
        games = await storage.fetch_user_games_with_verdicts(conn, user.id, lookback=30)
        profile = aggregate_user_profile(user.id, games)
        excluded = await storage.fetch_already_solved_exercise_ids(conn, user.id)
        pool = await storage.fetch_exercises_by_tags(
            conn,
            profile.recommended_exercise_tags,
            exclude_ids=excluded,
            limit=100,
        )
    chosen = recommend_exercises(profile, pool, exclude_ids=excluded, n=n)
    return RecommendationsResponse(exercises=chosen)
```

## Step 3 — Wire into `main.py`

Locate the existing block where other routers are included (search for
`app.include_router(`). Add **one line**:

```python
from .pedagogy.api import router as pedagogy_router
app.include_router(pedagogy_router)
```

Place the import next to the other backend imports near the top.
Place the `include_router` call near the other ones.

If `main.py` builds a shared BookRAG at startup, expose it as a module
global (`shared_book_rag = None`) and instantiate it in the existing
`@app.on_event("startup")` hook (or its FastAPI 0.111+ lifespan
equivalent) — `api.py` imports it lazily.

```python
from pedagogy.explanations import BookRAG

shared_book_rag: BookRAG | None = None

@app.on_event("startup")
async def _init_book_rag() -> None:
    global shared_book_rag
    shared_book_rag = BookRAG(books_dir=Path("docs/corpus"))
```

If the `[explanations]` extra is not installed, leave `shared_book_rag =
None` — the `template` mode still works.

## Step 4 — Rate limiter reuse

Spec §14.6 says claude mode is 5/min, template mode is 60/min. Reuse
the limiter pattern already in `main.py`. Look for the function that
guards `/api/analyze` (or similar Claude-fronted endpoints) — it
should already be 5/min in-memory. Wire it onto `mode == "claude"`
only.

If a limiter doesn't yet exist, port the same pattern as the existing
`/api/analyze` endpoint — do not invent a new one.

## Step 5 — Tests (`backend/tests/test_pedagogy_api.py`, ~150 lines)

Use `httpx.AsyncClient` against a TestClient. Required cases:

1. `test_get_move_verdict_404_when_not_computed` — fresh DB, request
   returns 404.
2. `test_get_move_verdict_returns_persisted_row` — write a verdict
   via `storage`, GET returns it.
3. `test_explain_move_template_mode_no_llm` — mock dilf
   `explain_verdict` to assert mode=template path doesn't touch
   Anthropic.
4. `test_explain_move_uses_cache_on_second_call` — same `(verdict,
   mode, lang)` → second call has `cached: true`, no LLM.
5. `test_explain_move_different_lang_creates_separate_cache` — `fr`
   then `en` → both `cached: false`, no Anthropic re-call for the
   second `fr` request.
6. `test_get_user_profile_forbidden_for_other_user` — non-admin
   trying to read another user's profile → 403.
7. `test_get_recommendations_filters_solved` — seed one exercise, mark
   it solved by the user, assert it is excluded.
8. `test_analyze_game_unauthenticated_returns_401` — sanity.

Mock Scan via the same `MockScanEngine` pattern dilf's own tests use.
Mock Anthropic via a fake `AsyncAnthropic` client injected through
the dilf `explain_verdict(client=...)` parameter.

## Step 6 — Update OpenAPI docs

Nothing manual. FastAPI auto-generates `/docs` from the Pydantic
schemas above. After running locally, screenshot `/docs` and attach to
the PR description as a sanity check.

## Acceptance criteria

- `pytest backend/tests/test_pedagogy_api.py` green.
- `curl http://localhost:8000/api/pedagogy/move-verdict/1/15` returns
  404 on a fresh DB.
- `/api/pedagogy/analyze-game` end-to-end on a 80-half-move game runs
  in < 30 s (excluding Scan), spec §15 budget.
- `/explain-move?mode=claude` is rate-limited to 5/min per user.
- `/explain-move?mode=template` is not rate-limited beyond 60/min.
- Existing frontend keeps working — no breaking changes outside
  `/api/pedagogy/*`.
- `mypy --strict backend/pedagogy/` clean.

## Out of scope (do in PR 13)

- The `tag_existing_exercises.py` migration script.
- Filling `exercise_tags` for existing rows. The recommender endpoint
  will return an empty `exercises` list until that runs — that's
  expected.

## Frontend wiring (out of scope here, listed for the roadmap)

Once this PR is live, the next step is to update
`frontend/src/components/AnalysisPanel.tsx` to call the new endpoints.
Specifically: a `useMoveVerdict(gameId, moveNumber)` hook that calls
`GET /api/pedagogy/move-verdict/{...}`, plus an explanation toggle for
mode. That work is tracked in ROADMAP.md Tier 1.
