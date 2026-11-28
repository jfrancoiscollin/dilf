"""Score-blind D1-B signature collision audit; no strategic equivalence claims."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def audit(records):
    identities, rows = set(), []
    for number, record in enumerate(records, 1):
        if not isinstance(record, dict) or set(record) != {
            "game_id", "position_id", "signatures", "successor_fingerprint"
        }:
            raise ValueError(f"row {number}: invalid schema or score-derived field")
        game, position, signatures, successor = (
            record[k] for k in ("game_id", "position_id", "signatures", "successor_fingerprint")
        )
        if any(not isinstance(v, str) or not v.strip() for v in (game, position, successor)):
            raise ValueError(f"row {number}: invalid identity or successor fingerprint")
        if not isinstance(signatures, dict) or not signatures or any(
            not isinstance(k, str) or not k or not isinstance(v, str) or not v
            for k, v in signatures.items()
        ):
            raise ValueError(f"row {number}: invalid signatures")
        if (game, position) in identities:
            raise ValueError(f"row {number}: duplicate game-position")
        identities.add((game, position))
        rows.append((game, signatures, successor))
    if not rows:
        raise ValueError("empty corpus")
    names = set(rows[0][1])
    if any(set(s) != names for _, s, _ in rows):
        raise ValueError("inconsistent signature families")
    report = {"positions": len(rows), "games": len({g for g, _, _ in rows}), "families": {}}
    for name in sorted(names):
        groups = defaultdict(list)
        for game, signatures, successor in rows:
            groups[signatures[name]].append((game, successor))
        collisions = [v for v in groups.values() if len(v) > 1]
        # Count unordered pairs by multiplicity, not quadratic enumeration.
        choose2 = lambda n: n * (n - 1) // 2
        pair_total = cross_game = divergent = cross_divergent = 0
        for group in collisions:
            n = len(group)
            games = Counter(g for g, _ in group)
            successors = Counter(s for _, s in group)
            joint = Counter(group)
            pair_total += choose2(n)
            cross_game += choose2(n) - sum(choose2(v) for v in games.values())
            divergent += choose2(n) - sum(choose2(v) for v in successors.values())
            cross_divergent += (
                choose2(n)
                - sum(choose2(v) for v in games.values())
                - sum(choose2(v) for v in successors.values())
                + sum(choose2(v) for v in joint.values())
            )
        report["families"][name] = {
            "unique_signatures": len(groups),
            "collision_pairs": pair_total,
            "cross_game_collision_pairs": cross_game,
            "successor_divergent_collision_pairs": divergent,
            "cross_game_successor_divergent_pairs": cross_divergent,
            "compression_ratio": len(rows) / len(groups),
            "collision_groups": len(collisions),
            "positions_in_collision_groups": sum(len(v) for v in collisions),
            "cross_game_collision_groups": sum(len({g for g, _ in v}) > 1 for v in collisions),
            "successor_divergent_collision_groups": sum(
                len({s for _, s in v}) > 1 for v in collisions
            ),
        }
    report["interpretation"] = "descriptive_only_not_best_move_or_minimax_equivalence"
    return report


def reject_duplicate_keys(pairs):
    """Reject ambiguous JSON objects, including nested signature maps."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    def reject_nonfinite(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    with args.jsonl.open(encoding="utf-8") as handle:
        records = [json.loads(line, parse_constant=reject_nonfinite,
                              object_pairs_hook=reject_duplicate_keys) for line in handle]
    print(json.dumps(audit(records), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
