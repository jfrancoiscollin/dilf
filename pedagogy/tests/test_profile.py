"""Tests for ``pedagogy.profile`` — spec §8, PR 9.

Covers:
- ``compute_accuracy`` formula and edge cases.
- ``aggregate_user_profile`` over synthetic games (motif tallying, strengths,
  weaknesses, weakest phase, recommended tags).
- ``recommend_exercises`` (tag matching, exclusion, n cap, no-tags case,
  malformed exercises).
"""

from __future__ import annotations

import pytest

from pedagogy.profile import (
    aggregate_user_profile,
    compute_accuracy,
    recommend_exercises,
)
from pedagogy.types import (
    GameAnalysis,
    MotifMatch,
    MoveVerdict,
    Phase,
    UserProfile,
    Verdict,
)


# ---------------------------------------------------------------------------
# Small builders
# ---------------------------------------------------------------------------


def _motif(name: str, role: str = "played", severity: float = 0.5) -> MotifMatch:
    return MotifMatch(motif=name, role=role, squares=[], pv=[], severity=severity)


def _verdict(
    *,
    side: str = "white",
    verdict: Verdict = Verdict.BEST,
    delta: float = 0.0,
    motifs: list[MotifMatch] | None = None,
    phase: Phase = Phase.MIDDLEGAME,
    move_number: int = 1,
) -> MoveVerdict:
    return MoveVerdict(
        move_number=move_number,
        side=side,
        move_notation="32-28",
        fen_before="W:Wb:Bb",
        fen_after="B:Wb:Bb",
        score_before=0.0,
        score_after=0.0,
        delta_winchance=delta,
        verdict=verdict,
        is_forced=False,
        motifs=motifs or [],
        phase=phase,
    )


def _game(
    *,
    game_id: int = 1,
    user_side: str | None = "white",
    verdicts: list[MoveVerdict] | None = None,
) -> GameAnalysis:
    return GameAnalysis(
        game_id=game_id,
        user_id=42,
        user_side=user_side,
        opening_name=None,
        verdicts=verdicts or [],
        summary={},
    )


# ---------------------------------------------------------------------------
# compute_accuracy
# ---------------------------------------------------------------------------


def test_compute_accuracy_returns_one_for_empty_verdicts() -> None:
    assert compute_accuracy([]) == 1.0


def test_compute_accuracy_returns_one_for_only_forced_or_book() -> None:
    forced = _verdict(verdict=Verdict.FORCED, delta=0.5)
    book = _verdict(verdict=Verdict.BOOK, delta=0.5)
    assert compute_accuracy([forced, book]) == 1.0


def test_compute_accuracy_perfect_game_is_one() -> None:
    verdicts = [_verdict(verdict=Verdict.BEST, delta=0.0) for _ in range(5)]
    assert compute_accuracy(verdicts) == 1.0


def test_compute_accuracy_drops_with_losses() -> None:
    perfect = [_verdict(verdict=Verdict.BEST, delta=0.0)]
    sloppy = [_verdict(verdict=Verdict.INACCURACY, delta=0.1)]
    blundered = [_verdict(verdict=Verdict.BLUNDER, delta=0.5)]
    assert compute_accuracy(perfect) > compute_accuracy(sloppy) > compute_accuracy(blundered)


def test_compute_accuracy_clips_extreme_losses_to_zero() -> None:
    # A move that's literally impossible (delta > 1.0) shouldn't push the
    # accuracy below 0.
    verdicts = [_verdict(verdict=Verdict.BLUNDER, delta=5.0)]
    assert compute_accuracy(verdicts) == 0.0


def test_compute_accuracy_ignores_negative_deltas_as_zero_loss() -> None:
    # If the user's move improved the eval (negative delta), it shouldn't
    # cause accuracy > 1.
    verdicts = [
        _verdict(verdict=Verdict.BEST, delta=-0.2),
        _verdict(verdict=Verdict.BEST, delta=0.0),
    ]
    assert compute_accuracy(verdicts) == 1.0


# ---------------------------------------------------------------------------
# aggregate_user_profile — empty case
# ---------------------------------------------------------------------------


def test_aggregate_empty_game_list_yields_empty_profile() -> None:
    profile = aggregate_user_profile(user_id=42, games=[])
    assert isinstance(profile, UserProfile)
    assert profile.user_id == 42
    assert profile.games_count == 0
    assert profile.average_accuracy == 1.0
    assert profile.strengths == []
    assert profile.weaknesses == []
    assert profile.weakest_phase == Phase.MIDDLEGAME
    assert profile.recommended_exercise_tags == []


# ---------------------------------------------------------------------------
# aggregate_user_profile — weaknesses
# ---------------------------------------------------------------------------


def test_aggregate_promotes_motif_to_weakness_when_threshold_reached() -> None:
    # User misses a coup_royal three times -> should appear in weaknesses.
    missed = [
        _verdict(side="white", motifs=[_motif("coup_royal", role="missed")])
        for _ in range(3)
    ]
    games = [_game(verdicts=missed)]
    profile = aggregate_user_profile(user_id=1, games=games)
    motif_names = [w["motif"] for w in profile.weaknesses]
    assert motif_names == ["coup_royal"]
    assert profile.recommended_exercise_tags == ["coup_royal"]


def test_aggregate_does_not_promote_motif_below_threshold() -> None:
    # One miss is below the threshold of 2.
    games = [
        _game(verdicts=[
            _verdict(side="white", motifs=[_motif("coup_royal", role="missed")])
        ])
    ]
    profile = aggregate_user_profile(user_id=1, games=games)
    assert profile.weaknesses == []


def test_aggregate_counts_opponent_played_motifs_as_user_suffered() -> None:
    # Opponent (black) played coup_turc twice in one game -> 2 suffered.
    # Together with one we explicitly "miss" -> 1 missed + 2 suffered = 3.
    verdicts = [
        _verdict(side="white", motifs=[_motif("coup_turc", role="missed")]),
        _verdict(side="black", motifs=[_motif("coup_turc", role="played")]),
        _verdict(side="black", motifs=[_motif("coup_turc", role="played")]),
    ]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    motif_names = [w["motif"] for w in profile.weaknesses]
    assert motif_names == ["coup_turc"]
    coup_turc = profile.weaknesses[0]
    assert coup_turc["missed"] == 1
    assert coup_turc["suffered"] == 2


def test_aggregate_weaknesses_are_sorted_by_missed_plus_suffered() -> None:
    verdicts = (
        [
            _verdict(side="white", motifs=[_motif("coup_royal", role="missed")])
            for _ in range(3)
        ]
        + [
            _verdict(side="white", motifs=[_motif("coup_turc", role="missed")])
            for _ in range(5)
        ]
    )
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert [w["motif"] for w in profile.weaknesses] == ["coup_turc", "coup_royal"]


def test_aggregate_weaknesses_capped_at_five() -> None:
    verdicts: list[MoveVerdict] = []
    for i in range(7):
        for _ in range(3):
            verdicts.append(
                _verdict(side="white", motifs=[_motif(f"motif_{i}", role="missed")])
            )
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert len(profile.weaknesses) == 5


# ---------------------------------------------------------------------------
# aggregate_user_profile — strengths
# ---------------------------------------------------------------------------


def test_aggregate_promotes_motif_to_strength_when_played_dominates() -> None:
    verdicts = [
        _verdict(side="white", motifs=[_motif("coup_royal", role="played", severity=0.6)])
        for _ in range(4)
    ]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert [s["motif"] for s in profile.strengths] == ["coup_royal"]
    assert profile.strengths[0]["played"] == 4
    assert profile.strengths[0]["total_severity"] == pytest.approx(2.4)


def test_aggregate_does_not_promote_motif_with_more_missed_than_played() -> None:
    played = [
        _verdict(side="white", motifs=[_motif("coup_royal", role="played")])
        for _ in range(3)
    ]
    missed = [
        _verdict(side="white", motifs=[_motif("coup_royal", role="missed")])
        for _ in range(4)
    ]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=played + missed)])
    assert profile.strengths == []


# ---------------------------------------------------------------------------
# aggregate_user_profile — weakest_phase
# ---------------------------------------------------------------------------


def test_aggregate_falls_back_to_middlegame_when_no_mistakes() -> None:
    verdicts = [_verdict(side="white", verdict=Verdict.BEST, delta=0.0)]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert profile.weakest_phase == Phase.MIDDLEGAME


def test_aggregate_picks_phase_with_largest_mean_loss() -> None:
    verdicts = [
        _verdict(
            side="white",
            verdict=Verdict.BLUNDER,
            delta=0.4,
            phase=Phase.ENDGAME,
        ),
        _verdict(
            side="white",
            verdict=Verdict.MISTAKE,
            delta=0.2,
            phase=Phase.MIDDLEGAME,
        ),
    ]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert profile.weakest_phase == Phase.ENDGAME


def test_aggregate_ignores_inaccuracies_when_picking_weakest_phase() -> None:
    # Only MISTAKE/BLUNDER feed phase_loss. An INACCURACY in endgame must
    # not push endgame above a real MISTAKE in middlegame.
    verdicts = [
        _verdict(
            side="white",
            verdict=Verdict.INACCURACY,
            delta=0.1,
            phase=Phase.ENDGAME,
        ),
        _verdict(
            side="white",
            verdict=Verdict.MISTAKE,
            delta=0.2,
            phase=Phase.MIDDLEGAME,
        ),
    ]
    profile = aggregate_user_profile(user_id=1, games=[_game(verdicts=verdicts)])
    assert profile.weakest_phase == Phase.MIDDLEGAME


# ---------------------------------------------------------------------------
# aggregate_user_profile — accuracy aggregation
# ---------------------------------------------------------------------------


def test_aggregate_average_accuracy_uses_user_side_only() -> None:
    user_verdicts = [_verdict(side="white", verdict=Verdict.BEST, delta=0.0)]
    opponent_blunders = [
        _verdict(side="black", verdict=Verdict.BLUNDER, delta=0.5)
        for _ in range(5)
    ]
    profile = aggregate_user_profile(
        user_id=1,
        games=[_game(verdicts=user_verdicts + opponent_blunders)],
    )
    assert profile.average_accuracy == 1.0


# ---------------------------------------------------------------------------
# recommend_exercises
# ---------------------------------------------------------------------------


def _profile_with_tags(tags: list[str]) -> UserProfile:
    return UserProfile(
        user_id=42,
        games_count=10,
        average_accuracy=0.85,
        strengths=[],
        weaknesses=[{"motif": t} for t in tags],
        weakest_phase=Phase.MIDDLEGAME,
        recommended_exercise_tags=tags,
    )


def test_recommend_returns_empty_when_profile_has_no_weakness_tags() -> None:
    profile = _profile_with_tags([])
    pool = [{"id": 1, "tags": ["coup_royal"]}]
    assert recommend_exercises(profile, pool) == []


def test_recommend_keeps_exercises_with_matching_tags() -> None:
    profile = _profile_with_tags(["coup_royal", "coup_turc"])
    pool = [
        {"id": 1, "tags": ["coup_royal", "endgame"]},
        {"id": 2, "tags": ["enchainement"]},
        {"id": 3, "tags": ["coup_turc"]},
    ]
    ids = [int(e["id"]) for e in recommend_exercises(profile, pool)]
    assert ids == [1, 3]


def test_recommend_respects_exclude_ids() -> None:
    profile = _profile_with_tags(["coup_royal"])
    pool = [
        {"id": 1, "tags": ["coup_royal"]},
        {"id": 2, "tags": ["coup_royal"]},
        {"id": 3, "tags": ["coup_royal"]},
    ]
    ids = [int(e["id"]) for e in recommend_exercises(profile, pool, exclude_ids={1, 3})]
    assert ids == [2]


def test_recommend_caps_at_n() -> None:
    profile = _profile_with_tags(["coup_royal"])
    pool = [{"id": i, "tags": ["coup_royal"]} for i in range(20)]
    out = recommend_exercises(profile, pool, n=5)
    assert len(out) == 5
    assert [int(e["id"]) for e in out] == [0, 1, 2, 3, 4]


def test_recommend_preserves_input_order() -> None:
    profile = _profile_with_tags(["coup_royal"])
    pool = [
        {"id": 9, "tags": ["coup_royal"]},
        {"id": 3, "tags": ["coup_royal"]},
        {"id": 7, "tags": ["coup_royal"]},
    ]
    out = recommend_exercises(profile, pool)
    assert [int(e["id"]) for e in out] == [9, 3, 7]


def test_recommend_skips_malformed_exercises() -> None:
    profile = _profile_with_tags(["coup_royal"])
    pool = [
        {"id": 1},                       # missing tags
        {"tags": ["coup_royal"]},         # missing id
        {"id": "not-an-int", "tags": ["coup_royal"]},  # bad id type
        {"id": 2, "tags": "coup_royal"},  # tags must be a sequence, not str
        {"id": 3, "tags": ["coup_royal"]},
    ]
    out = recommend_exercises(profile, pool)
    assert [int(e["id"]) for e in out] == [3]
