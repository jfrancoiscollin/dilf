"""Pick exercises that target a user's weakest motifs (spec §8).

The recommender is intentionally db-free: the caller hands in the candidate
exercise pool and the set of already-solved IDs. dilf doesn't own the
exercises table — Ai-draught's SQLite layer does.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from ..types import UserProfile

#: An exercise is anything dict-shaped with ``id`` and ``tags`` keys. Most
#: callers will pass rows fetched as dicts from SQLite or Pydantic models
#: serialised via ``.model_dump()``.
Exercise = Mapping[str, object]


def recommend_exercises(
    profile: UserProfile,
    exercise_pool: Sequence[Exercise],
    *,
    exclude_ids: Iterable[int] = (),
    n: int = 10,
) -> list[Exercise]:
    """Return up to ``n`` exercises matching the user's weakness tags.

    An exercise is selected when at least one of its ``tags`` matches one
    of ``profile.recommended_exercise_tags`` and its ``id`` is not in
    ``exclude_ids``. Order is preserved from ``exercise_pool`` so the
    caller can pre-sort (by difficulty, freshness, etc.).

    Returns the empty list when the profile carries no weakness tags —
    a player without enough data to recommend against shouldn't be served
    a degenerate "all exercises" pool.
    """
    weak_tags = set(profile.recommended_exercise_tags)
    if not weak_tags:
        return []
    exclude_set = {int(i) for i in exclude_ids}

    out: list[Exercise] = []
    for ex in exercise_pool:
        ex_id = ex.get("id")
        if not isinstance(ex_id, int) or ex_id in exclude_set:
            continue
        ex_tags = ex.get("tags")
        if not isinstance(ex_tags, (list, tuple, set, frozenset)):
            continue
        if set(ex_tags) & weak_tags:
            out.append(ex)
            if len(out) >= n:
                break
    return out
