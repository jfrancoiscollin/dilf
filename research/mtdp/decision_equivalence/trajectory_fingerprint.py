"""Score-blind lexical trajectory fingerprints for D1 admission.

These hashes identify an explicitly supplied ordered sequence of canonical
move tokens, NOT game-theoretic equivalence or canonical FMJD positions.
The caller must first validate move legality and token canonicalization.
"""
import hashlib
import json


def trajectory_fingerprint(initial_fen, moves):
    """Hash initial FEN and ordered canonical moves with domain separation.

    Fail closed on missing/invalid metadata. The returned digest is only an
    identity of the serialized input; equivalent alternate FEN spellings and
    alternate move encodings are NOT normalized here.
    """
    if not isinstance(initial_fen, str) or not initial_fen.strip():
        raise ValueError("nonempty canonical initial FEN required")
    if initial_fen != initial_fen.strip() or any(ord(ch) < 32 or ord(ch) == 127 for ch in initial_fen):
        raise ValueError("noncanonical initial FEN whitespace/control character")
    if not isinstance(moves, (list, tuple)):
        raise ValueError("ordered move sequence required")
    if any(not isinstance(m, str) or not m.strip() for m in moves):
        raise ValueError("invalid canonical move token")
    if any(m != m.strip() or any(ord(ch) < 32 or ord(ch) == 127 for ch in m) for m in moves):
        raise ValueError("noncanonical move token whitespace/control character")
    payload = json.dumps(
        ["MTDP-D1-trajectory-v1", initial_fen, list(moves)],
        ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()
