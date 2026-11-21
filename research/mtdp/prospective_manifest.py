"""Fail-closed validation of a frozen prospective Jass study manifest.

This does not read evaluation scores or admit a corpus. It checks only the
pre-execution metadata required by PROSPECTIVE_JASS_EVALUATION_PROTOCOL.md.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_SHA = re.compile(r"^[0-9a-f]{40}$")
_RESERVED = frozenset({"fFgE7oED", "P1RUlfJc", "s7ahYqL4", "D9PF2OSW"})
_BUDGETS = (10000, 50000, 200000)
_KEYS = frozenset({
    "schema_version", "dilf_sha", "jass_sha", "arbiter_sha",
    "sampler_sha", "cohort_sha256", "protocol_sha256", "seed",
    "budgets_nodes", "events", "minimum_effect", "regret_unit",
})


def validate(manifest: object) -> dict[str, object]:
    """Return a normalized manifest or raise ValueError before any experiment."""
    if not isinstance(manifest, dict) or set(manifest) != _KEYS:
        raise ValueError("manifest keys must exactly match the frozen schema")
    if manifest["schema_version"] != "mtdp-jass-prospective-v1":
        raise ValueError("unsupported schema_version")
    for field in ("dilf_sha", "jass_sha", "arbiter_sha", "sampler_sha"):
        if not isinstance(manifest[field], str) or not _SHA.fullmatch(manifest[field]):
            raise ValueError(f"invalid revision: {field}")
    for field in ("cohort_sha256", "protocol_sha256"):
        value = manifest[field]
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"invalid SHA-256: {field}")
    if type(manifest["seed"]) is not int or not (0 <= manifest["seed"] < 2**32):
        raise ValueError("seed must be a uint32")
    if (not isinstance(manifest["budgets_nodes"], list)
            or any(type(n) is not int for n in manifest["budgets_nodes"])
            or manifest["budgets_nodes"] != list(_BUDGETS)):
        raise ValueError("budgets_nodes must be frozen at 10k/50k/200k")
    events = manifest["events"]
    if not isinstance(events, list) or not events or any(
        not isinstance(event, str) or not event or event != event.strip() for event in events
    ):
        raise ValueError("nonempty event identifiers without surrounding whitespace required")
    if len(events) != len(set(events)) or set(events) & _RESERVED:
        raise ValueError("duplicate or D1-reserved event identifiers")
    effect = manifest["minimum_effect"]
    if type(effect) not in (int, float) or not (0 < effect < float("inf")):
        raise ValueError("minimum_effect must be finite and strictly positive")
    if not isinstance(manifest["regret_unit"], str) or not manifest["regret_unit"].strip():
        raise ValueError("regret_unit must be documented")
    return dict(manifest)


def validate_file(path: str | Path) -> dict[str, object]:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
