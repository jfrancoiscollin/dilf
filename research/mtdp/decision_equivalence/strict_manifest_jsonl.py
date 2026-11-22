"""Fail-closed JSONL decoder for D1 manifests: reject ambiguous duplicate JSON keys.

This is a syntax guard only; it does not authenticate games, FENs or sources.
"""
import json


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate_json_key:" + key)
        obj[key] = value
    return obj


def decode_line(line):
    return json.loads(
        line,
        object_pairs_hook=_unique_object,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError("nonfinite_json_constant:" + token)
        ),
    )
