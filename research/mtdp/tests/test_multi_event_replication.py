import hashlib
import json
import sys
from copy import deepcopy

import pytest

from research.mtdp.jass_benchmark import geometry_ablation, multi_event_freeze
from research.mtdp.jass_benchmark import multi_event_replication as study


def row(event_id, phase, start, *, minutes=5, status=30):
    return {"id": event_id, "phase": phase, "starts_at": start, "finishes_at": start + 3_420_000,
            "clock": {"limit": minutes * 60, "increment": 0},
            "system": "arena", "variant": "standard", "status": status}


def test_candidates_keep_old_finished_records_and_chronological_order():
    after = study.AFTER
    old = {"retrieved_at": "2026-11-12T10:00:00Z", "events": [
        row("prior", "finished", after - 1), row("pRW2Ahpz", "finished", after),
        row("first", "finished", after + 1), row("later", "created", after + 2, status=10),
        row("wrong-cadence", "finished", after + 3, minutes=3),
        row("aborted", "finished", after + 4, status=35),
    ]}
    new = {"retrieved_at": "2026-11-12T12:00:00Z", "events": [
        row("third", "started", after + 5, status=20), row("later", "finished", after + 2),
        row("first", "created", after + 1, status=10),
    ]}
    result = study.candidates([new, old])
    assert result["metadata_candidates"] == ["first", "later"]
    assert result["pending_events"] == ["third"]
    assert {r["id"]: r["candidate_status"] for r in result["candidate_log"]}["pRW2Ahpz"] == "used"
    assert {r["id"]: r["candidate_status"] for r in result["candidate_log"]}["aborted"] == "not_completed"


def sample_packet(event, hour, costs):
    arms = list(study.OCCUPANCY_ARMS)
    rows, frozen = [], []
    for index, (game, value, changes) in enumerate(costs):
        fen = f"{event}-fen{index}"
        original, updated = ["pc:1", 0, "source"], ["pc:2", 2, "other"]
        selected = {arm: original if arm == "L" or not changes else updated for arm in arms}
        row = {"fen": fen, "owner": game, "selected_sources": selected,
               "match_counts": dict.fromkeys(arms, 1)}
        for arm in arms:
            cost = 100 if arm == "L" else 100 + value
            outcome = {"ordinary_regret_centimen": cost, "covered": cost == 0,
                       "best_category": "ordinary", "candidate_category": "ordinary"}
            row[arm] = {"top1": outcome, "top3": outcome, "disjoint_optima": False}
        rows.append(row)
        frozen.append({"fen": fen, "owner": game, "matches": {arm: [selected[arm]] for arm in arms}})
    provenance = {
        "event": {"id": event, "startsAt": f"2026-11-12T{hour}:00:00Z", "isFinished": True,
                  "variant": "standard", "clock": {"limit": 300, "increment": 0}},
        "arms": arms, "event_game_ids": [f"{event}-game"],
        "inputs": {"event": [{"sha256": event}]},
        "counts": {"eligible": len(rows), "held_fens": len(rows) + 1},
    }
    return provenance, {"targets": len(rows), "matched_rows": rows}, frozen


def test_pooled_regret_is_target_weighted_and_changed_subset_is_explicit():
    packets = [
        sample_packet("A", "11", [("same-game", 0, False), ("same-game", 0, False)]),
        sample_packet("B", "14", [("game", 30, True)]),
        sample_packet("C", "17", [("game", -10, True)]),
    ]
    row = packets[1][1]["matched_rows"][0]
    row["LCB"]["top1"] = {**row["LCB"]["top1"], "ordinary_regret_centimen": 150}
    first = study.aggregate(packets)
    assert first == study.aggregate(packets)
    full = first["paired"]["LCB_vs_L"]
    assert full["mean_regret_delta_centimen"] == 5
    assert full["targets"] == 4 and full["owning_games"] == 3 and full["changed_sources"] == 2
    assert full["changed_source_rate"] == 0.5
    assert full["by_event"]["A"]["changed_source_rate"] == 0
    assert full["regret_interval"]["events"] == 3
    assert full["leave_one_event_out"]["A"]["mean_regret_delta_centimen"] == 10
    changed = first["paired"]["LCB_vs_L_changed_sources"]
    assert changed["targets"] == 2 and changed["regret_interval"]["events"] == 2
    assert changed["mean_regret_delta_centimen"] == 10
    top1 = first["paired_top1"]["LCB_vs_L"]
    assert top1["mean_regret_delta_centimen"] == 10
    assert top1["changed_source_rate"] == full["changed_source_rate"]
    top1_changed = first["paired_top1"]["LCB_vs_L_changed_sources"]
    assert top1_changed["mean_regret_delta_centimen"] == 20
    assert top1_changed["by_event"]["A"]["changed_source_rate"] is None


def test_rejects_partial_and_overlapping_freezes_and_changed_source():
    packets = [sample_packet(event, hour, [("game", 0, False)])
               for event, hour in zip(("A", "B", "C"), ("11", "14", "17"), strict=True)]
    with pytest.raises(ValueError, match="Exactly three"):
        study.aggregate(packets[:2])
    overlapping = deepcopy(packets)
    overlapping[1][0]["event_game_ids"] = overlapping[0][0]["event_game_ids"]
    with pytest.raises(ValueError, match="overlap"):
        study.aggregate(overlapping)
    changed = deepcopy(packets)
    changed[1][1]["matched_rows"][0]["selected_sources"]["LCB"] = ["elsewhere", 2, "fen"]
    with pytest.raises(ValueError, match="frozen source"):
        study.aggregate(changed)


def test_single_event_interval_is_not_estimable_even_with_two_games():
    assert study.hierarchical_interval([("one", "g1", 1), ("one", "g2", 2)]) == {
        "events": 1, "games": 2, "ci95": None,
    }


def test_merged_sources_deduplicate_and_split_with_event_digest():
    move = {"action": [[31, 26], [], False]}
    plans = [{
        "schema": "mtdp-jass-cohort-v1", "engine": {"scan_binary_sha256": "scan"},
        "targets": [{"source_fen": "shared", "target_fen": event, "legal_moves": [move]}],
    } for event in ("A", "B", "C")]
    merged = study.merge_score_plans(plans)
    assert list(study.score_catalogue(merged, "source")) == ["shared"]
    assert list(study.score_catalogue(merged, "target")) == ["A", "B", "C"]
    receipt = {
        "schema": "mtdp-jass-scan-reference-v1", "cohort_sha256": "merged", "scan_binary_sha256": "scan",
        "scan_eval_sha256": study.SCAN_EVAL_SHA256, "scan_successor_depth": 12, "role": "source",
        "action_scores_centimen": {"shared": [{**move, "score": 20}]},
    }
    tagged = [(event, plan, f"digest-{event}") for event, plan in zip(("A", "B", "C"), plans, strict=True)]
    split = study.split_reference(merged, "merged", receipt, tagged, "source")
    assert split["A"]["cohort_sha256"] == "digest-A"
    assert split["B"]["action_scores_centimen"] == split["C"]["action_scores_centimen"] == receipt["action_scores_centimen"]
    with pytest.raises(ValueError, match="cohort_sha256"):
        study.split_reference(merged, "different", receipt, tagged, "source")


def test_cli_scores_round_trip_through_three_frozen_events(tmp_path, monkeypatch):
    def run(module, *args):
        monkeypatch.setattr(sys, "argv", [module.__name__, *map(str, args)])
        module.main()

    def read(path):
        return json.loads(path.read_bytes())

    def descriptor(path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"path": str(path), "stored_sha256": digest, "content_sha256": digest}

    write = geometry_ablation.write_json
    actions = [[[31, 26], [], False], [[32, 27], [], False]]
    moves = [{"action": action} for action in actions]
    scan_hashes = {"scan_linux": "test-scan", "data/eval": study.SCAN_EVAL_SHA256}
    events = ("A", "B", "C")
    entries = []
    for event, hour in zip(events, ("11", "14", "17"), strict=True):
        provenance, _, _ = sample_packet(event, hour, [(f"{event}-game", 0, False)])
        fen, game = f"{event}-target", f"{event}-game"
        rows = [{"fen": fen, "owner": game, "games": [game], "actions": actions,
                 "matches": {arm: [["pc:1", 0, "shared"]] for arm in study.OCCUPANCY_ARMS}}]
        plan = {"schema": "mtdp-jass-cohort-v1",
                "engine": {"scan_binary_sha256": scan_hashes["scan_linux"]},
                "targets": [{"source_fen": "shared", "target_fen": fen, "legal_moves": moves}]}
        multi_event_freeze.package(tmp_path / event, provenance, rows, plan, {},
                                   {"scan_sha256": scan_hashes})
        entries.append({"provenance": descriptor(tmp_path / event / "provenance.json")})

    index, merged_path = tmp_path / "freeze-index.json", tmp_path / "merged.json"
    write(index, entries)
    run(study, "prepare-score-plan", "--freeze-index", index, "--output", merged_path)
    merged = read(merged_path)
    for role, depth, scores in (("source", 12, (30, 0)), ("target", 16, (0, 20))):
        fens = study.score_catalogue(merged, role)
        assert len(fens) == (1 if role == "source" else 3)
        receipt = tmp_path / f"{role}.json"
        write(receipt, {
            "schema": "mtdp-jass-scan-reference-v1", "role": role, "scan_successor_depth": depth,
            "scan_binary_sha256": scan_hashes["scan_linux"], "scan_eval_sha256": scan_hashes["data/eval"],
            "cohort_sha256": descriptor(merged_path)["content_sha256"],
            "action_scores_centimen": {fen: [{**move, "score": score}
                                             for move, score in zip(moves, scores, strict=True)]
                                       for fen in fens},
        })
        run(study, "split-reference", "--freeze-index", index, "--merged-plan", merged_path,
            "--reference", receipt, "--role", role, "--output-dir", tmp_path)

    for event, entry in zip(events, entries, strict=True):
        source, target, comparison = (tmp_path / f"{event}-{role}.json"
                                      for role in ("source", "target", "comparison"))
        run(geometry_ablation, "analyze", "--provenance", entry["provenance"]["path"],
            "--source", source, "--target", target, "--output", comparison)
        entry.update(source=descriptor(source), target=descriptor(target), comparison=descriptor(comparison))

    packets, result = tmp_path / "packet-index.json", tmp_path / "summary.json"
    write(packets, entries)
    run(study, "aggregate", "--packet-index", packets, "--output", result)
    arms = read(result)["pooled"]["arms"]
    assert arms["L"]["top1"]["covered"] == 0 and arms["L"]["top1"]["max_centimen"] == 20
    assert arms["L"]["top3"]["covered"] == 3 and arms["L"]["top3"]["max_centimen"] == 0
    repeated = tmp_path / "repeated.json"
    run(study, "aggregate", "--packet-index", packets, "--output", repeated)
    assert result.read_bytes() == repeated.read_bytes()

    comparison = tmp_path / "A-comparison.json"
    edited = read(comparison)
    edited["matched_rows"][0]["L"]["top1"]["ordinary_regret_centimen"] += 1
    write(comparison, edited)
    entries[0]["comparison"] = descriptor(comparison)
    write(packets, entries)
    with pytest.raises(ValueError, match="does not reproduce"):
        run(study, "aggregate", "--packet-index", packets, "--output", result)
