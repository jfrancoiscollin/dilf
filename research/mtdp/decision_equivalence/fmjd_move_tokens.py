"""Score-blind FMJD 10x10 move-token syntax gate for D1 admission.

Only checks lexical shape and playable-square bounds. It does NOT establish
move legality, capture completeness, unique paths, or canonical identity.
"""
import re

_TOKEN = re.compile(r"([1-9][0-9]?)([-x])([1-9][0-9]?)(?:\\2([1-9][0-9]?))*\\Z", re.ASCII)


def validate_move_token(token):
    """Return an accepted token unchanged; reject ambiguous/unsupported syntax."""
    if not isinstance(token, str) or not token or not token.isascii():
        raise ValueError("ASCII FMJD move token required")
    if not _TOKEN.fullmatch(token):
        raise ValueError("invalid FMJD move-token syntax")
    separator = "x" if "x" in token else "-"
    squares = token.split(separator)
    if any(not 1 <= int(square) <= 50 for square in squares):
        raise ValueError("square outside FMJD 1..50")
    if separator == "-" and len(squares) != 2:
        raise ValueError("quiet move must have two endpoints")
    if len(set(squares)) != len(squares):
        raise ValueError("repeated square in move path")
    return token
