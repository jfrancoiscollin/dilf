"""D1-B regression: combinatorial pair counts agree with exhaustive enumeration."""
from itertools import combinations

from research.mtdp.decision_equivalence.signature_collision_audit import audit


def test_pair_counts_against_exhaustive_reference():
    # Repeated game and successor labels exercise inclusion-exclusion.
    rows = [
        {"game_id": f"g{i % 4}", "position_id": str(i),
         "signatures": {"L": f"s{i % 3}"},
         "successor_fingerprint": f"t{i % 5}"}
        for i in range(91)
    ]
    report = audit(rows)["families"]["L"]
    pairs = [(a, b) for a, b in combinations(rows, 2)
             if a["signatures"]["L"] == b["signatures"]["L"]]
    assert report["collision_pairs"] == len(pairs)
    assert report["cross_game_collision_pairs"] == sum(
        a["game_id"] != b["game_id"] for a, b in pairs)
    assert report["successor_divergent_collision_pairs"] == sum(
        a["successor_fingerprint"] != b["successor_fingerprint"] for a, b in pairs)
    assert report["cross_game_successor_divergent_pairs"] == sum(
        a["game_id"] != b["game_id"] and
        a["successor_fingerprint"] != b["successor_fingerprint"]
        for a, b in pairs)


def test_large_collision_group_counts_without_pair_materialization():
    n = 10000
    rows = [{"game_id": "g", "position_id": str(i),
             "signatures": {"L": "shared"},
             "successor_fingerprint": "same"} for i in range(n)]
    report = audit(rows)["families"]["L"]
    assert report["collision_pairs"] == n * (n - 1) // 2
    assert report["cross_game_successor_divergent_pairs"] == 0
