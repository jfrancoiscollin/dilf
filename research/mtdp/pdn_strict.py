"""Prospective PDN admission guard, separate from the frozen legacy parser.

research.mtdp.pdn is pinned by the archived H13 methods. Keep its exact bytes
for replay; new membership/admission code uses this stricter entry point.
Authentication must still cover the exact bytes decoded by the caller.
"""
from __future__ import annotations

import re
from research.mtdp import pdn as legacy


def parse_games_strict(text: str) -> list[legacy.PdnGame]:
    """Reject all post-result mainline tokens, allowing stripped annotations.

    Use the frozen parser's same game boundaries, tag removal and annotation
    handling, then its grammar/action-token checks. No token is silently
    discarded from the prospective authenticated game after a result.
    """
    for chunk in re.split(r'(?=^\s*\[Event\s+)', text, flags=re.M | re.I):
        if not chunk.strip():
            continue
        mainline = legacy._strip_comments_and_variations(legacy._TAG.sub('', chunk))
        terminated = False
        for token in legacy._TOKEN.findall(mainline):
            if terminated:
                raise legacy.PdnReplayError(f'Unexpected PDN token after result: {token!r}')
            if token in legacy._RESULTS:
                terminated = True
    return legacy.parse_games(text)
