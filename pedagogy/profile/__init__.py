"""User profile layer — aggregate motifs across many games (spec §8).

dilf is a pure library: it never touches a database. The aggregator and the
recommender both accept their data through arguments and return plain
dataclasses/dicts. The parent project (``Ai-draught``) wraps these with the
SQLite layer described in spec §10.
"""

from __future__ import annotations

from .aggregator import aggregate_user_profile, compute_accuracy
from .recommender import recommend_exercises

__all__ = [
    "aggregate_user_profile",
    "compute_accuracy",
    "recommend_exercises",
]
