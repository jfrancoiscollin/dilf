"""Admission gate for a score-blind historical D1 manifest.

This gate authenticates PDN *bytes*, not game membership, move replay, or
FMJD legality. It must not be used to label a cohort independently qualified.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from research.mtdp.decision_equivalence.corpus_guard import audit
from research.mtdp.decision_equivalence.pdn_provenance import verify_pdn_sources


def audit_with_pdn_bytes(rows: list[dict], sources: Mapping[str, str | Path]) -> dict:
    """Require both split/leakage checks and complete byte-level PDN provenance.

    Unlike audit() alone, this rejects rows without a declared source digest.
    The caller must still prove game membership and FMJD legality separately.
    """
    report = audit(rows)
    verified = verify_pdn_sources(rows, sources)
    if set(verified) != {row["game_id"] for row in rows}:
        raise ValueError("incomplete verified game coverage")
    return {**report, "pdn_bytes_verified": True,
            "verified_games": len(verified),
            "game_membership_verified": False,
            "fmjd_legality_verified": False,
            "independent_cohort_qualified": False}
