"""Contract tests for the independent prospective-study manifest gate."""
import copy

import pytest

from research.mtdp.prospective_manifest import validate


@pytest.fixture
def valid():
    return {
        "schema_version": "mtdp-jass-prospective-v1",
        "dilf_sha": "a" * 40,
        "jass_sha": "b" * 40,
        "arbiter_sha": "c" * 40,
        "sampler_sha": "d" * 40,
        "cohort_sha256": "e" * 64,
        "protocol_sha256": "f" * 64,
        "seed": 1234,
        "budgets_nodes": [10000, 50000, 200000],
        "events": ["new-independent-event"],
        "minimum_effect": 0.1,
        "regret_unit": "arbiter native units",
    }


def test_valid_manifest(valid):
    assert validate(valid) == valid


@pytest.mark.parametrize("field,value", [
    ("dilf_sha", "bad"), ("seed", True), ("seed", -1),
    ("budgets_nodes", [10000, 50000]), ("events", ["s7ahYqL4"]),
    ("events", ["x", "x"]), ("minimum_effect", 0),
    ("minimum_effect", float("nan")), ("minimum_effect", float("inf")),
    ("regret_unit", ""),
])
def test_reject_invalid_field(valid, field, value):
    bad = copy.deepcopy(valid)
    bad[field] = value
    with pytest.raises(ValueError):
        validate(bad)


def test_reject_unknown_key(valid):
    valid["score"] = 0
    with pytest.raises(ValueError):
        validate(valid)


def test_reject_missing_key(valid):
    del valid["cohort_sha256"]
    with pytest.raises(ValueError):
        validate(valid)
