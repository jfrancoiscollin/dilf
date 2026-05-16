"""Aggregate per-game verdicts into a :class:`UserProfile`.

The aggregator is a **pure function** of its inputs — the caller is
responsible for loading the relevant :class:`GameAnalysis` objects from
persistence (typically the ``move_verdicts`` table described in spec §10).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

from ..types import GameAnalysis, MoveVerdict, Phase, UserProfile, Verdict

#: Verdicts excluded from accuracy because they carry no learning signal.
_ACCURACY_EXCLUDED_VERDICTS = frozenset({Verdict.FORCED, Verdict.BOOK})

#: Minimum count for a motif to qualify as a strength or weakness.
_MOTIF_THRESHOLD = 2


def compute_accuracy(verdicts: Sequence[MoveVerdict]) -> float:
    """Average move quality in ``[0.0, 1.0]`` across pre-filtered verdicts.

    ``verdicts`` must already be filtered to a single side (typically the
    user's). Forced and book moves are skipped — they carry no signal.

    Formula: ``1.0 - mean(max(0, delta_winchance))`` clamped to ``[0, 1]``.
    A perfect game returns ``1.0``; a sequence of severe blunders trends
    toward ``0.0``. When no relevant verdict is present (empty list, all
    forced/book) the function returns ``1.0`` to avoid penalising an
    absence of data.
    """
    losses: list[float] = [
        max(0.0, v.delta_winchance)
        for v in verdicts
        if v.verdict not in _ACCURACY_EXCLUDED_VERDICTS
    ]
    if not losses:
        return 1.0
    avg_loss = sum(losses) / len(losses)
    return max(0.0, min(1.0, 1.0 - avg_loss))


def _new_motif_stats() -> dict[str, float]:
    return {"played": 0.0, "missed": 0.0, "suffered": 0.0, "threatened": 0.0, "total_severity": 0.0}


def aggregate_user_profile(
    user_id: int,
    games: Sequence[GameAnalysis],
) -> UserProfile:
    """Build a :class:`UserProfile` from the user's recent games.

    For each game we walk every :class:`MoveVerdict` and tally motif roles
    from the user's perspective:

    - Verdicts on the user's side: each motif counts under its declared
      role (``played``/``missed``/etc.).
    - Verdicts on the opponent's side: motifs ``played`` by the opponent
      count as ``suffered`` for the user.

    Strengths and weaknesses are then derived by thresholds (spec §8):
    weaknesses keep motifs with ``missed + suffered >= 3``, strengths
    motifs with ``played >= 3 and played > missed``. Each list is capped
    at 5 entries.

    ``weakest_phase`` is the phase whose MISTAKE/BLUNDER moves carry the
    largest mean ``|delta_winchance|`` loss. With no MISTAKE/BLUNDER move
    we fall back to :data:`Phase.MIDDLEGAME` to keep the profile
    well-formed.
    """
    motif_stats: dict[str, dict[str, float]] = defaultdict(_new_motif_stats)
    phase_loss: dict[Phase, list[float]] = defaultdict(list)
    accuracy_scores: list[float] = []

    for game in games:
        user_verdicts = [v for v in game.verdicts if v.side == game.user_side]
        accuracy_scores.append(compute_accuracy(user_verdicts))

        for v in game.verdicts:
            if v.side != game.user_side:
                for m in v.motifs:
                    if m.role == "played":
                        motif_stats[m.motif]["suffered"] += 1
                        motif_stats[m.motif]["total_severity"] += m.severity
                continue
            for m in v.motifs:
                motif_stats[m.motif][m.role] += 1
                motif_stats[m.motif]["total_severity"] += m.severity
            if v.verdict in (Verdict.MISTAKE, Verdict.BLUNDER):
                phase_loss[v.phase].append(abs(v.delta_winchance))

    weaknesses = _collect_weaknesses(motif_stats)
    strengths = _collect_strengths(motif_stats)
    weakest_phase = _weakest_phase(phase_loss)

    return UserProfile(
        user_id=user_id,
        games_count=len(games),
        average_accuracy=(
            sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 1.0
        ),
        strengths=strengths,
        weaknesses=weaknesses,
        weakest_phase=weakest_phase,
        recommended_exercise_tags=[str(w["motif"]) for w in weaknesses],
    )


def _entry(name: str, stats: Mapping[str, float]) -> dict[str, Any]:
    """One row of the strengths/weaknesses list."""
    out: dict[str, Any] = {"motif": name}
    out.update(stats)
    return out


def _collect_weaknesses(motif_stats: Mapping[str, Mapping[str, float]]) -> list[dict[str, Any]]:
    rows: list[tuple[float, dict[str, Any]]] = []
    for name, stats in motif_stats.items():
        score = stats["missed"] + stats["suffered"]
        if score >= _MOTIF_THRESHOLD:
            rows.append((score, _entry(name, stats)))
    rows.sort(key=lambda kv: kv[0], reverse=True)
    return [row for _, row in rows[:5]]


def _collect_strengths(motif_stats: Mapping[str, Mapping[str, float]]) -> list[dict[str, Any]]:
    rows: list[tuple[float, dict[str, Any]]] = []
    for name, stats in motif_stats.items():
        if stats["played"] >= _MOTIF_THRESHOLD and stats["played"] > stats["missed"]:
            rows.append((stats["played"], _entry(name, stats)))
    rows.sort(key=lambda kv: kv[0], reverse=True)
    return [row for _, row in rows[:5]]


def _weakest_phase(phase_loss: Mapping[Phase, Iterable[float]]) -> Phase:
    """Pick the phase with the largest mean loss; fall back to MIDDLEGAME."""
    means: list[tuple[Phase, float]] = []
    for phase, losses in phase_loss.items():
        seq = list(losses)
        if not seq:
            continue
        means.append((phase, sum(seq) / len(seq)))
    if not means:
        return Phase.MIDDLEGAME
    means.sort(key=lambda kv: kv[1], reverse=True)
    return means[0][0]
