"""Score-blind compression diagnostics for precomputed FMJD signatures.

Input JSONL rows must contain position_id, game_id, signature. No engine
scores are read. This measures grouping, NOT decision/minimax equivalence.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def measure(rows):
    groups = defaultdict(list)
    positions = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(k not in row for k in ('position_id', 'game_id', 'signature')):
            raise ValueError(f'row {i}: missing identity or signature')
        pid, gid, signature = (row[k] for k in ('position_id', 'game_id', 'signature'))
        if any(not isinstance(v, str) or not v.strip() for v in (pid, gid, signature)):
            raise ValueError(f'row {i}: invalid identity or signature')
        if pid in positions:
            raise ValueError(f'row {i}: duplicate position_id')
        positions[pid] = gid
        groups[signature].append(gid)
    n = len(positions)
    if not n:
        raise ValueError('empty corpus')
    sizes = Counter(len(group) for group in groups.values())
    colliding = sum(len(group) for group in groups.values() if len(group) > 1)
    cross_game = sum(1 for group in groups.values() if len(set(group)) > 1)
    # Count unordered pairs exactly; a group of five contributes ten pairs,
    # not one. Distinguish same-game collisions from cross-game transfers.
    collision_pairs = sum(len(g) * (len(g) - 1) // 2 for g in groups.values())
    cross_game_pairs = sum(
        len(g) * (len(g) - 1) // 2 -
        sum(k * (k - 1) // 2 for k in Counter(g).values())
        for g in groups.values()
    )
    # Pair probability among all unordered distinct positions is a separate
    # estimand from the conditional fraction among colliding pairs.
    total_pairs = n * (n - 1) // 2
    same_game_pairs = collision_pairs - cross_game_pairs
    return {'positions': n, 'distinct_signatures': len(groups),
            'compression_ratio': n / len(groups), 'collision_position_fraction': colliding / n,
            'collision_groups': sum(v for k, v in sizes.items() if k > 1),
            'cross_game_collision_groups': cross_game,
            'collision_pairs': collision_pairs,
            'same_game_collision_pairs': same_game_pairs,
            'collision_pair_fraction': collision_pairs / total_pairs if total_pairs else None,
            'cross_game_pair_fraction_all_positions': cross_game_pairs / total_pairs if total_pairs else None,
            'cross_game_collision_pairs': cross_game_pairs,
            'cross_game_collision_pair_fraction': (cross_game_pairs / collision_pairs
                                                   if collision_pairs else None),
            'group_size_histogram': {str(k): v for k, v in sorted(sizes.items())},
            'decision_equivalence_established': False, 'minimax_equivalence_established': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('jsonl', type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.jsonl.read_text().splitlines() if line.strip()]
    print(json.dumps(measure(rows), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
