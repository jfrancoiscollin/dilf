import hashlib
import json

import pytest

from research.mtdp.decision_equivalence.registry_coverage import REQUIRED_GROUPS, verify


def make_inventory(tmp_path):
    entries = []
    for group in sorted(REQUIRED_GROUPS):
        payload = b'{"game_id":"historical-game"}\n'
        name = group + ".jsonl"
        (tmp_path / name).write_bytes(payload)
        entries.append({"group": group, "path": name, "sha256": hashlib.sha256(payload).hexdigest(), "rows": 1})
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    return path, entries


def test_valid_inventory(tmp_path):
    path, _ = make_inventory(tmp_path)
    result = verify(path)
    assert len(result["registries"]) == len(REQUIRED_GROUPS)
    assert result["status"] == "integrity_only_not_completeness_certification"


@pytest.mark.parametrize("failure", ["missing", "digest", "rows", "traversal", "duplicate"])
def test_fail_closed(tmp_path, failure):
    path, entries = make_inventory(tmp_path)
    if failure == "missing":
        entries.pop()
    elif failure == "digest":
        entries[0]["sha256"] = "0" * 64
    elif failure == "rows":
        entries[0]["rows"] = 2
    elif failure == "traversal":
        entries[0]["path"] = "../outside.jsonl"
    elif failure == "duplicate":
        entries[1]["path"] = entries[0]["path"]
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        verify(path)


@pytest.mark.parametrize("key,bad", [
    ("fen_sha256", "not-a-digest"),
    ("trajectory_sha256", "A" * 64),
    ("fen_sha256", 123),
])
def test_reject_malformed_identity_digest(tmp_path, key, bad):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    registry = tmp_path / entry["path"]
    payload = (json.dumps({"game_id": "historical-game", key: bad}) + "\n").encode()
    registry.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid .* digest"):
        verify(path)


@pytest.mark.parametrize("forbidden", ["scan_score", "best_move", "wdl", "action_rank", "regret_cp", "evaluation"])
def test_reject_score_leak_in_registry(tmp_path, forbidden):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    registry = tmp_path / entry["path"]
    payload = (json.dumps({"game_id": "historical-game", forbidden: 0}) + "\\n").encode()
    registry.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="score-derived field"):
        verify(path)
