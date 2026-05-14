"""Snapshot test for the dilf public API surface (see ``INTEROP.md``).

This file is the machine-enforced version of the API table in
``INTEROP.md``. Each symbol below is imported and inspected so that any
accidental removal, rename, or breaking signature change fails the
test before the consumer (``draught-master/backend/pedagogy/``) breaks
on the next deploy.

When you intentionally break the API, update this test **in the same
PR** as the API change so reviewers see the breakage explicitly. Then
follow the two-step dance described in ``INTEROP.md``.
"""

from __future__ import annotations

import dataclasses
import inspect
from typing import get_type_hints


# ---------------------------------------------------------------------------
# pedagogy.types — dataclasses + enums persisted by the consumer
# ---------------------------------------------------------------------------


def test_pedagogy_types_exports() -> None:
    from pedagogy.types import (
        Features,
        GameAnalysis,
        MotifMatch,
        MoveVerdict,
        Phase,
        UserProfile,
        Verdict,
    )

    assert dataclasses.is_dataclass(Features)
    assert dataclasses.is_dataclass(GameAnalysis)
    assert dataclasses.is_dataclass(MotifMatch)
    assert dataclasses.is_dataclass(MoveVerdict)
    assert dataclasses.is_dataclass(UserProfile)
    assert issubclass(Phase, str)  # str-enum semantics
    assert issubclass(Verdict, str)


def test_verdict_enum_values_are_stable() -> None:
    """Persisted verbatim into draught-master's `move_verdicts.verdict`
    column. Renaming a value is a data-migration-grade breaking change."""
    from pedagogy.types import Verdict

    expected = {
        "brilliant", "best", "excellent", "good",
        "inaccuracy", "mistake", "blunder", "forced", "book",
    }
    assert {v.value for v in Verdict} == expected


def test_phase_enum_values_are_stable() -> None:
    """Persisted into `move_verdicts.phase`."""
    from pedagogy.types import Phase

    assert {p.value for p in Phase} == {"opening", "middlegame", "endgame"}


def test_move_verdict_field_names_are_stable() -> None:
    """draught-master serialises MoveVerdict into JSON and back. Field
    renames are breaking. New fields with defaults are non-breaking."""
    from pedagogy.types import MoveVerdict

    required = {
        "move_number", "side", "move_notation",
        "fen_before", "fen_after",
        "score_before", "score_after", "delta_winchance",
        "verdict", "is_forced", "motifs",
        "features_before", "features_after", "phase",
    }
    actual = {f.name for f in dataclasses.fields(MoveVerdict)}
    missing = required - actual
    assert not missing, f"MoveVerdict missing fields: {missing}"


def test_motif_match_field_names_are_stable() -> None:
    from pedagogy.types import MotifMatch

    required = {"motif", "role", "squares", "pv", "severity", "metadata"}
    actual = {f.name for f in dataclasses.fields(MotifMatch)}
    missing = required - actual
    assert not missing, f"MotifMatch missing fields: {missing}"


def test_features_field_names_are_stable() -> None:
    from pedagogy.types import Features

    required = {
        "white_men", "white_kings", "black_men", "black_kings",
        "material_balance",
        "center_count_white", "center_count_black",
        "formations", "phase",
    }
    actual = {f.name for f in dataclasses.fields(Features)}
    missing = required - actual
    assert not missing, f"Features missing fields: {missing}"


def test_user_profile_field_names_are_stable() -> None:
    from pedagogy.types import UserProfile

    required = {
        "user_id", "games_count", "average_accuracy",
        "strengths", "weaknesses",
        "weakest_phase", "recommended_exercise_tags",
    }
    actual = {f.name for f in dataclasses.fields(UserProfile)}
    missing = required - actual
    assert not missing, f"UserProfile missing fields: {missing}"


def test_game_analysis_has_user_side_field() -> None:
    """draught-master writes user_side per-game; aggregate_user_profile
    reads it back to classify motifs as played-by-user vs suffered."""
    from pedagogy.types import GameAnalysis

    assert "user_side" in {f.name for f in dataclasses.fields(GameAnalysis)}


# ---------------------------------------------------------------------------
# pedagogy.game — primitive types + FEN parser
# ---------------------------------------------------------------------------


def test_pedagogy_game_exports() -> None:
    from pedagogy.game import GameState, Move, parse_fen

    assert dataclasses.is_dataclass(GameState)
    assert dataclasses.is_dataclass(Move)
    assert callable(parse_fen)
    sig = inspect.signature(parse_fen)
    assert "fen" in sig.parameters


def test_move_has_path_and_captures() -> None:
    """The motif detectors read these two fields. Renaming = breaking."""
    from pedagogy.game import Move

    names = {f.name for f in dataclasses.fields(Move)}
    assert "path" in names
    assert "captures" in names


# ---------------------------------------------------------------------------
# pedagogy.motifs — registry of detectors
# ---------------------------------------------------------------------------


def test_all_detectors_is_a_non_empty_list() -> None:
    from pedagogy.motifs import ALL_DETECTORS

    assert isinstance(ALL_DETECTORS, list)
    assert len(ALL_DETECTORS) >= 6  # 6 P1 detectors at the floor


def test_detectors_have_name_and_detect_method() -> None:
    """draught-master's tag_existing_exercises iterates ALL_DETECTORS
    and calls .detect() on each. Both must remain on every entry."""
    from pedagogy.motifs import ALL_DETECTORS

    for cls in ALL_DETECTORS:
        instance = cls()
        assert hasattr(instance, "name"), f"{cls.__name__} has no .name"
        assert callable(getattr(instance, "detect", None)), \
            f"{cls.__name__} has no callable .detect"


# ---------------------------------------------------------------------------
# pedagogy.explanations — pipeline + BookRAG
# ---------------------------------------------------------------------------


def test_explain_verdict_is_async_with_expected_signature() -> None:
    """The consumer awaits this; making it sync is breaking."""
    from pedagogy.explanations import explain_verdict

    assert inspect.iscoroutinefunction(explain_verdict)
    params = inspect.signature(explain_verdict).parameters
    assert "mode" in params
    assert "book_rag" in params
    assert "lang" in params


def test_book_rag_class_and_from_directory_factory() -> None:
    from pedagogy.explanations import BookRAG

    assert inspect.isclass(BookRAG)
    assert hasattr(BookRAG, "from_directory"), \
        "draught-master's main.py builds BookRAG.from_directory at startup"


# ---------------------------------------------------------------------------
# pedagogy.profile — aggregator + recommender
# ---------------------------------------------------------------------------


def test_aggregate_user_profile_signature() -> None:
    from pedagogy.profile.aggregator import aggregate_user_profile

    assert callable(aggregate_user_profile)
    params = list(inspect.signature(aggregate_user_profile).parameters)
    assert params[0] == "user_id"
    assert "games" in params


def test_recommend_exercises_signature() -> None:
    from pedagogy.profile.recommender import recommend_exercises

    assert callable(recommend_exercises)
    params = inspect.signature(recommend_exercises).parameters
    assert "profile" in params
    assert "exclude_ids" in params
    assert "n" in params


# ---------------------------------------------------------------------------
# pedagogy.verdicts — orchestrator
# ---------------------------------------------------------------------------


def test_assemble_verdict_is_callable() -> None:
    from pedagogy.verdicts.assembler import assemble_verdict

    assert callable(assemble_verdict)


# ---------------------------------------------------------------------------
# pedagogy.protocols — typing.Protocol for engines
# ---------------------------------------------------------------------------


def test_engine_protocol_exposed() -> None:
    from pedagogy.protocols import EngineProtocol

    assert inspect.isclass(EngineProtocol)
