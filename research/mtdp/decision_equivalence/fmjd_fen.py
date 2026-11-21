"""Conservative FMJD 10x10 PDN-FEN syntax and occupancy canonicalizer.

Does not certify reachability, mandatory captures, or legal game history.
"""
import re

_TOKEN = re.compile(r"(K?)([1-9]|[1-4][0-9]|50)\Z")


def canonical_fen(fen: str) -> str:
    """Return deterministic FEN or reject ambiguous/invalid occupancy."""
    if not isinstance(fen, str):
        raise ValueError("FEN must be text")
    sections = fen.strip().upper().split(":")
    if len(sections) != 3 or sections[0] not in ("W", "B"):
        raise ValueError("expected side:Wpieces:Bpieces")
    occupied = set()
    output = {}
    for color, section in zip(("W", "B"), sections[1:]):
        if not section.startswith(color):
            raise ValueError("incorrect piece section")
        pieces = section[1:]
        tokens = pieces.split(",") if pieces else []
        parsed = []
        for token in tokens:
            token = token.strip()
            match = _TOKEN.fullmatch(token)
            if not match:
                raise ValueError("invalid square or king token")
            square = int(match.group(2))
            if square in occupied:
                raise ValueError("duplicate occupied square")
            occupied.add(square)
            parsed.append((square, bool(match.group(1))))
        if len(parsed) > 20:
            raise ValueError("more than 20 pieces for one side")
        output[color] = color + ",".join(("K" if king else "") + str(square)
                                         for square, king in sorted(parsed))
    return ":".join([sections[0], output["W"], output["B"]])
