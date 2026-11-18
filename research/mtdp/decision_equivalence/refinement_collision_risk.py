"""Score-blind collision risk accounting for nested D1 signatures.

Only structural collision and successor disagreement are measured here.
No Scan scores, action rankings, or minimax claims are consumed.
"""
from collections import defaultdict
from itertools import combinations


def refinement_collision_risk(records, families):
    """Count distinct-position collision pairs and divergent successors per level.

    Each record has game_id, position_id, signatures, successor_fingerprint.
    Reject ambiguous identities, missing fields and non-nested refinements.
    """
    from .refinement import verify_refinement

    rows = list(records)
    checked = verify_refinement(rows, families)
    if any(not c["is_refinement"] for c in checked["comparisons"]):
        raise ValueError("signature hierarchy is not a refinement")
    result = []
    for family in families:
        groups = defaultdict(list)
        for row in rows:
            groups[row["signatures"][family]].append(row)
        collisions = divergent = cross_game = 0
        for members in groups.values():
            n = len(members)
            collisions += n * (n - 1) // 2
            by_successor = defaultdict(int)
            by_game = defaultdict(int)
            for row in members:
                by_successor[row["successor_fingerprint"]] += 1
                by_game[row["game_id"]] += 1
            divergent += n * (n - 1) // 2 - sum(
                k * (k - 1) // 2 for k in by_successor.values()
            )
            cross_game += n * (n - 1) // 2 - sum(
                k * (k - 1) // 2 for k in by_game.values()
            )
        result.append({
            "family": family, "positions": len(rows),
            "classes": len(groups), "collision_pairs": collisions,
            "divergent_successor_pairs": divergent,
            "cross_game_pairs": cross_game,
        })
    return {"levels": result, "interpretation": "score_blind_structural_only"}


def test_refinement_collision_risk():
    def row(g, p, coarse, fine, successor):
        return {"game_id": g, "position_id": p,
                "signatures": {"L": coarse, "LCB": fine},
                "successor_fingerprint": successor}
    rows = [row("g1", "a", "x", "a", "s1"),
            row("g2", "b", "x", "a", "s2"),
            row("g1", "c", "x", "b", "s1"),
            row("g3", "d", "y", "c", "s3")]
    levels = refinement_collision_risk(rows, ["L", "LCB"])["levels"]
    assert [(x["collision_pairs"], x["divergent_successor_pairs"],
             x["cross_game_pairs"]) for x in levels] == [(3, 2, 2), (1, 1, 1)]


def test_refinement_collision_risk_rejects_merge():
    rows = [
        {"game_id": "g", "position_id": str(i),
         "signatures": {"L": str(i), "LCB": "same"},
         "successor_fingerprint": "s"} for i in range(2)
    ]
    try:
        refinement_collision_risk(rows, ["L", "LCB"])
    except ValueError:
        return
    raise AssertionError("non-refinement accepted")
