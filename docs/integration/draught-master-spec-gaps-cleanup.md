# draught-master cleanup — apply `draught-master-spec-gaps-cleanup.patch`

This directory contains the patch file
[`draught-master-spec-gaps-cleanup.patch`](./draught-master-spec-gaps-cleanup.patch)
that closes the residual spec §14.6 / §15 gaps found by the audit
documented in the status banners of `ai-draught-pr-{7,8,13}-*.md`.

The patch was authored by Claude Code on `2026-05-14` against
`jfrancoiscollin/ai-draught` `develop@e6611c9`. It was prepared inside
a Claude Code container that had **filesystem read/write access but
no push credentials** to `github.com/jfrancoiscollin/ai-draught`, so
the commit lives only as a patch artifact here — pull it down on your
local machine and push from there.

## What the patch does (5 files, +355 lines)

- `backend/db/schema.py` — add `idx_move_verdicts_motifs`
  JSON-extract index (spec §10).
- `backend/pedagogy/api.py`:
  - Fix latent bug: `explain_verdict` was called without `await`,
    leaving a coroutine in the response body. Existing tests only
    covered the 404 path so it was never exercised.
  - Rebuild the rate-limiter wiring so it actually fires. 5/min on
    `mode=claude` (was a no-op), 60/min on the rest (spec §14.6).
- `backend/pedagogy/README.md` (new) — layout, how to add a motif
  detector / template, known gaps for future PRs.
- `backend/tests/test_pedagogy_storage.py` — add
  `test_fetch_user_games_with_verdicts_orders_desc`.
- `backend/tests/test_pedagogy_api.py` — add 4 tests:
  - `test_explain_move_template_mode_returns_string` — regression
    test for the missing `await`.
  - `test_explain_move_uses_cache_on_second_call`.
  - `test_explain_move_different_lang_creates_separate_cache`.
  - `test_get_recommendations_filters_solved`.

After the patch: 74 backend tests pass (`pytest backend/tests/`).

## How to apply

From your local clone of `jfrancoiscollin/ai-draught`:

```bash
git checkout develop
git pull
git checkout -b feat/pedagogy-spec-gaps
curl -L https://raw.githubusercontent.com/jfrancoiscollin/dilf/main/docs/integration/draught-master-spec-gaps-cleanup.patch \
  | git am
pytest backend/tests/  # expect 74 passing
git push -u origin feat/pedagogy-spec-gaps
gh pr create --base develop --title "fix(pedagogy): close spec §14.6 / §15 gaps"
```

`git am` preserves the original commit metadata; the result is
identical to what would have landed via a direct push from the Claude
Code session.

## Why this is a patch instead of a PR

- The MCP scope of the session that produced this work is restricted
  to `jfrancoiscollin/dilf`, so it cannot open a PR on the ai-draught
  repo directly.
- `git push` from the session fails because no GitHub credentials
  are configured for `github.com/jfrancoiscollin/ai-draught` in the
  container.
- The cleanest workaround is to land the artifact in dilf (where the
  session can push) and apply it locally — same commit hash will land
  on ai-draught either way.

## Known gaps still open after this cleanup

- `backend/pedagogy/scripts/tag_existing_exercises.py` has a happy-path
  test gap for `coup_royal`. Blocked on dilf shipping a
  `parse_move_notation(state, notation)` helper that infers captured
  pieces; the current `_parse_move_fallback` returns
  `captures=()` so capture-based detectors silently produce empty
  tag sets on exercises. Tracked in dilf's `ROADMAP.md` Tier 4.
- Rate limiter is in-memory. For multi-worker uvicorn or horizontal
  scale-out, move to a shared store (Redis). Tracked in Tier 2
  alongside the dilf CI work.
