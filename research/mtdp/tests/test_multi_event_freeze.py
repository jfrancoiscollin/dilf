import json

import pytest

from research.mtdp.jass_benchmark import multi_event_freeze as staging


def candidate(event, status, minute):
    return {"id": event, "candidate_status": status, "starts_at": 1794481200000 + minute * 60_000}


def metadata(event, minute, finished=True):
    return {"id": event, "startsAt": f"2026-11-12T11:{minute:02}:00Z", "isFinished": finished,
            "variant": "standard", "clock": {"limit": 300, "increment": 0}}


def test_waits_for_earlier_candidate_and_requires_detail_completion():
    log = {"candidate_log": [candidate("first", "pending_finish", 0),
                             candidate("later", "needs_pdn_and_replay", 52)]}
    with pytest.raises(ValueError, match="next chronological candidate"):
        staging.require_next_candidate(log, metadata("later", 52), set(), {})
    log["candidate_log"][0]["candidate_status"] = "needs_pdn_and_replay"
    with pytest.raises(ValueError, match="Detail metadata"):
        staging.require_next_candidate(log, metadata("first", 0, finished=False), set(), {})
    with pytest.raises(ValueError, match="Detail metadata"):
        staging.require_next_candidate(log, metadata("later", 52), set(), {})
    staging.require_next_candidate(log, metadata("later", 52), {"first"}, {})
    staging.require_next_candidate(log, metadata("later", 52), set(), {"first": "No public PDN"})


def test_archive_is_deterministic_and_hash_bound(tmp_path):
    output = tmp_path / "event"
    rows = [{"fen": "unique", "matches": {"L": []}}]
    fields = ({"counts": {"eligible": 1}}, rows, {"targets": []}, {"game": "accepted"}, {})
    staging.package(output, *fields)
    first = {path.name: path.read_bytes() for path in output.iterdir()}
    provenance = json.loads((output / "provenance.json").read_text())
    assert staging.read_input(provenance["eligible_shards"][0]) == rows
    for path in output.iterdir():
        path.unlink()
    output.rmdir()
    staging.package(output, *fields)
    assert first == {path.name: path.read_bytes() for path in output.iterdir()}
    shard = output / "eligible-00.json.gz"
    shard.write_bytes(shard.read_bytes() + b"\0")
    with pytest.raises(ValueError, match="Input hash mismatch"):
        staging.read_input(provenance["eligible_shards"][0])
