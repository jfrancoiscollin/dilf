"""Score-blind duplicate-position diagnostic for D1 partition design.

A repeated canonical FEN within a split is not cross-split leakage, but
must not be counted as an independent position in uncertainty estimates.
No claim of FMJD legality or statistical independence is made.
"""
from collections import defaultdict
from hashlib import sha256


def audit_within_split_duplicates(rows):
    """Return deterministic duplicate clusters; reject ambiguous identities.

    Required: game_id, position_id, split, fen. Inputs must come from
    pinned FMJD replay; the function does not validate board legality.
    """
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        game, pos, split, fen = (row[k] for k in
                                 ("game_id", "position_id", "split", "fen"))
        if not isinstance(game, str) or not game.strip():
            raise ValueError("invalid game_id")
        if isinstance(pos, bool) or not isinstance(pos, (str, int)) or not str(pos):
            raise ValueError("invalid position_id")
        if split not in ("train", "validation", "test") or not isinstance(split, str):
            raise ValueError("invalid split")
        if not isinstance(fen, str) or not fen.strip():
            raise ValueError("invalid FEN")
        identity = (game, str(pos))
        if identity in seen:
            raise ValueError("duplicate position identity")
        seen.add(identity)
        digest = sha256(fen.encode("utf-8")).hexdigest()
        groups[(split, digest)].append(identity)
    clusters = [
        {"split": split, "fen_sha256": digest, "positions": sorted(ids),
         "games": sorted({g for g, _ in ids})}
        for (split, digest), ids in sorted(groups.items())
        if len(ids) > 1
    ]
    return {
        "duplicate_clusters": clusters,
        "duplicate_positions_beyond_first": sum(
            len(c["positions"]) - 1 for c in clusters),
        "cross_game_duplicate_clusters": sum(
            len(c["games"]) > 1 for c in clusters),
        "independent_observations_proven": False,
        "fmjd_legality_proven": False,
    }
