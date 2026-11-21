"""Score-blind cross-split game-sequence alias detector for D1 provenance.

Shared ordered FEN windows flag potential game re-identification, not proof
of identical games. Supplements partition_guard and fen_overlap_guard.
"""
from collections import defaultdict


def find_cross_split_windows(rows, window=3):
    """Find identical ordered FEN windows shared by train and test games.

    Windows cover strictly consecutive plies, never merely adjacent records.
    No Scan/Jass scores may be supplied. This is a conservative alias check,
    not FMJD canonicalization or an independence certificate.
    """
    from .partition_guard import _reject_target_fields
    if type(window) is not int or window < 2:
        raise ValueError("window must be an integer >= 2")
    games, splits, last = defaultdict(list), {}, {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid row")
        _reject_target_fields(row)
        g, split, ply, fen = (row.get(k) for k in ("game_id", "split", "ply", "fen"))
        if not isinstance(g, str) or not g.strip() or split not in ("train", "test"):
            raise ValueError("invalid game identity or split")
        if type(ply) is not int or ply < 0 or not isinstance(fen, str) or not fen.strip():
            raise ValueError("invalid ply or fen")
        if g in splits and splits[g] != split:
            raise ValueError("game crosses splits")
        if g in last and ply <= last[g]:
            raise ValueError("non-increasing ply")
        splits[g], last[g] = split, ply
        games[g].append((ply, "".join(fen.split())))
    index = defaultdict(lambda: {"train": set(), "test": set()})
    for g, seq in games.items():
        for i in range(len(seq) - window + 1):
            segment = seq[i:i + window]
            if any(segment[j + 1][0] != segment[j][0] + 1 for j in range(window - 1)):
                continue
            index[tuple(fen for _, fen in segment)][splits[g]].add(g)
    return [{"train_games": sorted(v["train"]), "test_games": sorted(v["test"]),
             "fen_window": list(k)} for k, v in sorted(index.items())
            if v["train"] and v["test"]]
