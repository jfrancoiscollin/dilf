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
    payload = (json.dumps({"game_id": "historical-game", forbidden: 0}) + "\n").encode()
    registry.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="score-derived field"):
        verify(path)


@pytest.mark.parametrize("nested", [
    {"provenance": {"scan_score": 0}},
    {"sources": [{"metadata": {"best_move": "32-28"}}]},
    {"annotations": [{"nested": [{"wdl": "win"}]}]},
])
def test_reject_nested_score_leak_in_registry(tmp_path, nested):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    registry = tmp_path / entry["path"]
    payload = (json.dumps({"game_id": "historical-game", **nested}) + "\n").encode()
    registry.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="score-derived field"):
        verify(path)


@pytest.mark.parametrize("rows", [
    [{"game_id": "g", "fen_sha256": "a" * 64}, {"fen_sha256": "a" * 64, "game_id": "g"}],
    [{"game_id": "g", "fen_sha256": "a" * 64}, {"game_id": "g", "fen_sha256": "a" * 64}],
])
def test_reject_duplicate_registry_rows_regardless_of_key_order(tmp_path, rows):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    payload = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (tmp_path / entry["path"]).write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    entry["rows"] = len(rows)
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate exclusion record"):
        verify(path)


def test_reject_whitespace_only_game_identity(tmp_path):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    payload = b'{"game_id":"   "}\n'
    (tmp_path / entry["path"]).write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid exclusion identity"):
        verify(path)


@pytest.mark.parametrize("payload", [
    '{"game_id":"g","game_id":"other"}\n',
    '{"game_id":"g","provenance":{"source":"a","source":"b"}}\n',
])
def test_reject_duplicate_json_keys_in_registry(tmp_path, payload):
    path, entries = make_inventory(tmp_path)
    entry = entries[0]
    raw = payload.encode()
    (tmp_path / entry["path"]).write_bytes(raw)
    entry["sha256"] = hashlib.sha256(raw).hexdigest()
    path.write_text(json.dumps({"registries": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        verify(path)


def test_reject_duplicate_json_keys_in_inventory(tmp_path):
    path, _ = make_inventory(tmp_path)
    original = path.read_text(encoding="utf-8")
    path.write_text('{"registries":[],"registries":' + original.split('"registries":', 1)[1], encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        verify(path)
