"""Verify declared PDN SHA-256 against source bytes before D1 freeze.

Verifies file identity, NOT PDN parsing, game membership, or FMJD legality.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping


def verify_pdn_sources(rows: list[dict], sources: Mapping[str, str | Path]) -> dict[str, str]:
    """Fail closed unless every game has a matching, readable PDN source.

    sources maps game_id to a local PDN path. Files may be shared by games.
    No target-engine scores are consulted.
    """
    if not rows:
        raise ValueError("empty manifest")
    if not isinstance(sources, Mapping):
        raise ValueError("sources must map game IDs to PDN paths")
    expected: dict[str, str] = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("game_id"), str) or not row["game_id"]:
            raise ValueError(f"row {i}: invalid game_id")
        gid = row["game_id"]
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError(f"row {i}: invalid metadata")
        source = metadata.get("source", {})
        if not isinstance(source, dict):
            raise ValueError(f"row {i}: invalid metadata.source")
        nested = source.get("pdn_sha256")
        root = row.get("source_pdn_sha256")
        if root is not None and nested is not None and root != nested:
            raise ValueError(f"row {i}: conflicting declared digests")
        digest = root if root is not None else nested
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"row {i}: missing or invalid PDN digest")
        if gid in expected and expected[gid] != digest:
            raise ValueError(f"row {i}: inconsistent game digest")
        expected[gid] = digest
    if set(sources) != set(expected):
        raise ValueError("source map must match manifest games exactly")
    actual: dict[str, str] = {}
    cache: dict[Path, str] = {}
    for gid, digest in expected.items():
        path = Path(sources[gid]).resolve(strict=True)
        if not path.is_file():
            raise ValueError(f"{gid}: PDN source is not a file")
        if path not in cache:
            hasher = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    hasher.update(chunk)
            cache[path] = hasher.hexdigest()
        if cache[path] != digest:
            raise ValueError(f"{gid}: PDN bytes do not match declared digest")
        actual[gid] = cache[path]
    return actual
