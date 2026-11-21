"""Preflight is strictly offline and rejects forged verification claims."""
import json

import pytest

from research.mtdp.r2_source_preflight import EXPECTED_PREFIXES, validate_manifest


def manifest():
    return {
        "schema": "mtdp.r2_source_inventory.v1",
        "bucket": "jass-data",
        "objects": [
            {"cell": f"c{i}", "generation": f"g{j}",
             "key": f"{EXPECTED_PREFIXES[f'c{i}']}/artefacts/g{j}-selfplay.jnnw.gz",
             "verified_present": False, "sha256": None}
            for i in range(5) for j in (1, 2)
        ],
    }


def write(tmp_path, obj):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_offline_preflight(tmp_path):
    result = validate_manifest(write(tmp_path, manifest()))
    assert result["source_key_count"] == 10
    assert result["r2_access_performed"] is False
    assert result["r2_objects_verified"] == 0


@pytest.mark.parametrize("mutation", ["duplicate", "traversal", "claimed_verified", "missing", "wrong_run"])
def test_reject_unsafe_or_unsubstantiated_manifest(tmp_path, mutation):
    obj = manifest()
    if mutation == "duplicate":
        obj["objects"][1]["generation"] = "g1"
        obj["objects"][1]["key"] = obj["objects"][0]["key"]
    elif mutation == "traversal":
        obj["objects"][0]["key"] = "runs/../artefacts/g1-selfplay.jnnw.gz"
    elif mutation == "wrong_run":
        obj["objects"][0]["key"] = "runs/other-run/artefacts/g1-selfplay.jnnw.gz"
    elif mutation == "claimed_verified":
        obj["objects"][0]["verified_present"] = True
    elif mutation == "missing":
        obj["objects"].pop()
    with pytest.raises(ValueError):
        validate_manifest(write(tmp_path, obj))
