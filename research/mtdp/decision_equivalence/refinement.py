"""Score-blind verification of nested partitions for progressive D1 signatures.

A refinement is structural, not evidence of decision or minimax equivalence.
"""
from collections import defaultdict


def verify_refinement(records, families):
    """Check that each finer signature class is contained in one coarser class."""
    rows = list(records)
    if not rows or len(families) < 2 or len(set(families)) != len(families):
        raise ValueError("nonempty records and at least two distinct families required")
    identities = set()
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != {
            "game_id", "position_id", "signatures", "successor_fingerprint"
        }:
            raise ValueError(f"row {i}: invalid score-blind schema")
        ident = (row["game_id"], row["position_id"])
        if any(not isinstance(x, str) or not x.strip() for x in (*ident, row["successor_fingerprint"])):
            raise ValueError(f"row {i}: invalid identity or successor")
        if ident in identities:
            raise ValueError(f"row {i}: duplicate identity")
        identities.add(ident)
        sig = row["signatures"]
        if not isinstance(sig, dict) or any(
            not isinstance(sig.get(k), str) or not sig[k] for k in families
        ):
            raise ValueError(f"row {i}: missing/invalid signature")
    levels = []
    for family in families:
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            groups[row["signatures"][family]].append(i)
        levels.append(groups)
    comparisons = []
    for parent_name, child_name, parent, child in zip(
        families, families[1:], levels, levels[1:]
    ):
        violations = []
        for child_key, members in child.items():
            parent_keys = {rows[i]["signatures"][parent_name] for i in members}
            if len(parent_keys) > 1:
                violations.append({
                    "child_signature": child_key,
                    "parent_classes": len(parent_keys),
                    "positions": len(members),
                })
        comparisons.append({
            "parent": parent_name, "child": child_name,
            "parent_classes": len(parent), "child_classes": len(child),
            "is_refinement": not violations, "violations": violations,
        })
    return {
        "positions": len(rows), "comparisons": comparisons,
        "interpretation": "structural_partition_only_not_decision_or_minimax_equivalence",
    }
