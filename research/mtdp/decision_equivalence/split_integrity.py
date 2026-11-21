"""Score-blind split-integrity audit for D1. No scores, no cohort admission.

The caller must supply canonical FMJD FENs and provenance from a pinned replay.
A clean result is necessary but not sufficient for statistical independence.
"""
from collections import defaultdict
from hashlib import sha256


def audit_split_integrity(rows, reserved_fen_sha256=()):
    """Fail closed on cross-split game/FEN leakage and reserved positions.

    rows: dictionaries with game_id, position_id, split, fen.
    SHA-256 hashes refer to UTF-8 canonical FEN bytes, without trimming.
    """
    reserved = set(reserved_fen_sha256)
    if any(not isinstance(h, str) or len(h) != 64 or
           any(c not in "0123456789abcdef" for c in h) for h in reserved):
        raise ValueError("invalid reserved FEN digest")
    games, fens = defaultdict(set), defaultdict(set)
    identities = set()
    counts = defaultdict(int)
    reserved_hits = []
    for row in rows:
        game, pos, split, fen = (row[k] for k in ("game_id", "position_id", "split", "fen"))
        if not isinstance(game, str) or not game.strip():
            raise ValueError("invalid game_id")
        if not isinstance(pos, (str, int)) or isinstance(pos, bool) or not str(pos):
            raise ValueError("invalid position_id")
        if not isinstance(split, str) or split not in ("train", "validation", "test"):
            raise ValueError("invalid split")
        if not isinstance(fen, str) or not fen.strip():
            raise ValueError("invalid FEN")
        identity = (game, str(pos))
        if identity in identities:
            raise ValueError("duplicate position identity")
        identities.add(identity)
        digest = sha256(fen.encode("utf-8")).hexdigest()
        games[game].add(split)
        fens[digest].add(split)
        counts[split] += 1
        if digest in reserved:
            reserved_hits.append(identity)
    game_leaks = sorted(g for g, splits in games.items() if len(splits) > 1)
    fen_leaks = sorted(h for h, splits in fens.items() if len(splits) > 1)
    return {
        "admissible": not (game_leaks or fen_leaks or reserved_hits),
        "counts": dict(sorted(counts.items())),
        "cross_split_games": game_leaks,
        "cross_split_fen_sha256": fen_leaks,
        "reserved_hits": sorted(reserved_hits),
        "statistical_independence_proven": False,
        "fmjd_legality_proven": False,
    }
