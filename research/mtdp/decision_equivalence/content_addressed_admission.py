"""Strict content-addressed D1 game binding and replay gate.

A caller-supplied arbitrary game_id cannot prove membership in a PDN.
For this optional admission route, the game identifier MUST be
'<64-character lowercase PDN SHA-256>:<positive 1-based game index>'.
This is a deterministic identifier convention, not independent evidence
that the historical event/tournament labels are truthful.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Mapping

from research.mtdp.decision_equivalence.admission_gate import audit_with_pdn_bytes
from research.mtdp.pdn_membership_proof import prove_pdn_position


def audit_content_addressed_games(rows: list[dict], sources: Mapping[str, str | Path],
                                  engine) -> dict:
    """Verify every row by authenticated PDN index and full legal replay.

    All positions for a game must use the same digest/index. The source map
    is keyed by the canonical content-addressed game_id. The caller must
    supply a pinned real FMJD engine for real scientific admission; mocks
    only establish test behavior. No Scan/Jass score is accessed.
    """
    report = audit_with_pdn_bytes(rows, sources)
    groups = defaultdict(list)
    for row in rows:
        digest = row.get("source_pdn_sha256")
        if digest is None:
            digest = row.get("metadata", {}).get("source", {}).get("pdn_sha256")
        game_id = row["game_id"]
        prefix = digest + ":"
        if not game_id.startswith(prefix):
            raise ValueError("game_id must bind to its declared PDN digest and game index")
        suffix = game_id[len(prefix):]
        if not suffix.isdecimal() or not suffix.isascii() or suffix.startswith("0"):
            raise ValueError("game_id must have a canonical positive decimal game index")
        index = int(suffix)
        if index < 1:
            raise ValueError("game index must be positive")
        groups[game_id].append((index, row))
    for game_id, positions in groups.items():
        index = positions[0][0]
        for _, row in positions:
            proof = prove_pdn_position(
                sources[game_id], game_id[:64], index, row["ply"], row["fen"], engine
            )
            if not (proof["pdn_bytes_verified"] and proof["fmjd_legality_verified"]
                    and proof["source_index_membership_verified"]):
                raise ValueError("incomplete PDN membership proof")
    return {
        **report,
        "game_membership_verified": True,
        "fmjd_legality_verified": True,
        "manifest_game_id_binding_verified": True,
        # Still requires external event identity, reserved corpus inventory,
        # engine pin and split provenance audit before independent qualification.
        "independent_cohort_qualified": False,
        "binding_scheme": "pdn-sha256:one-based-game-index",
        "verified_games": len(groups),
    }
