"""Score-blind exact FEN overlap gate for prospective D1 manifests.

Exact text equality is a necessary duplicate check, not a canonical FMJD
position identity. Do not interpret passing this check as proof of no leakage.
"""
import hashlib
import json


def audit_exact_fen_overlap(rows, reserved_fens=()):
    """Reject identical FEN across records or reserved prospectives.

    Requires game_id, position_id, fen (nonempty strings). Preserves input
    order in the digest and rejects score-like metadata by reusing the
    partition guard. This is deliberately strict: repeated FENs, even within
    a game, are quarantined rather than silently treated as independent.
    """
    from .partition_guard import _reject_target_fields

    reserved = set(reserved_fens)
    if any(not isinstance(f, str) or not f.strip() for f in reserved):
        raise ValueError("invalid reserved FEN")
    seen = set()
    seen_whitespace_aliases = set()
    reserved_aliases = {''.join(f.split()) for f in reserved}
    manifest = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid record")
        _reject_target_fields(row)
        g, p, fen = (row.get(k) for k in ("game_id", "position_id", "fen"))
        if any(not isinstance(x, str) or not x.strip() for x in (g, p, fen)):
            raise ValueError("missing identity or FEN")
        # Conservative textual alias quarantine; not FMJD canonicalization.
        alias = ''.join(fen.split())
        if fen in reserved:
            raise ValueError("reserved prospective FEN overlap")
        if alias in reserved_aliases:
            raise ValueError("reserved prospective FEN whitespace alias overlap")
        if fen in seen:
            raise ValueError("duplicate exact FEN")
        if alias in seen_whitespace_aliases:
            raise ValueError("duplicate FEN whitespace alias")
        seen.add(fen)
        seen_whitespace_aliases.add(alias)
        manifest.append((g, p, fen))
    if not manifest:
        raise ValueError("empty manifest")
    payload = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
    return {"sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "positions": len(manifest), "unique_exact_fens": len(seen)}
