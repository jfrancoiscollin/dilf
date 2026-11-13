import gzip
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark.multi_event_replication import candidates
from research.mtdp.jass_benchmark.spatial_jass import prepare, verify_equal_prefix_receipts
from research.mtdp.jass_benchmark.spatial_replication import (
    BUDGETS, REPLICATION_CUTOFF, aggregate, pool, read_arena, validate_traces,
)

PILOT = Path("research/mtdp/jass_benchmark/spatial-jass/KXaMpuNe")


def test_replication_listing_archive_rebuilds_fourth_freeze_chronology():
    spatial = PILOT.parent
    replication = spatial / "replication"
    paths = [
        *(spatial.parent / "eighth-replication").glob("*-tournaments.json"),
        spatial / "initial-listing.json", *spatial.glob("*-tournaments.json"),
        replication / "initial-listing.json", *replication.glob("*-tournaments.json"),
    ]
    log = candidates([json.loads(path.read_bytes()) for path in paths])
    finished = [row["id"] for row in log["candidate_log"]
                if row["starts_at"] >= REPLICATION_CUTOFF
                and row["candidate_status"] == "needs_pdn_and_replay"]
    assert finished[:4] == ["uG0fGZzB", "l45uk39x", "GYEtKzUg", "MtDQWBNR"]


@pytest.mark.parametrize("event", ["uG0fGZzB", "l45uk39x"])
def test_prepare_reproduces_frozen_source_and_target_mappings(event):
    executable = os.environ.get("MTDP_JASS_CATALOGUE")
    if not executable:
        pytest.skip("Build the optional Jass integration target and set MTDP_JASS_CATALOGUE")
    directory = PILOT.parent / "replication" / event
    provenance = json.loads((directory / "provenance.json").read_bytes())
    archived = json.loads((directory / "manifest.json").read_bytes())
    del archived["provenance_sha256"]
    # The published digest identifies the build used at freeze time.
    del archived["engine"]["jass_catalogue_sha256"]
    actual = json.loads(json.dumps(prepare(provenance, Path(executable))))
    del actual["engine"]["jass_catalogue_sha256"]
    assert actual == archived


def test_published_pilot_receipts_validate_against_scan():
    provenance, frozen, diagnostic, rows = read_arena(PILOT)
    assert diagnostic["matched"] == 34
    assert len(rows) == 34 * len(BUDGETS)
    assert sum(arm["stop"] == "depth_ceiling" for row in rows for arm in row["arms"].values()) == 9
    comparisons = pool([(provenance, frozen, diagnostic, rows)], 50_000, changed_only=False)["comparisons"]
    assert comparisons["L"]["optimum_pairs"] == {
        "both_optimal": 6, "lcb_only": 0, "control_only": 0, "neither_optimal": 27,
    }
    assert comparisons["native"]["optimum_pairs"] == {
        "both_optimal": 5, "lcb_only": 1, "control_only": 0, "neither_optimal": 27,
    }


def test_equal_prefix_searches_agree_except_for_elapsed_time():
    _, _, _, rows = read_arena(PILOT)
    same_prefix = [row for row in rows if row["prefixes"]["L"] == row["prefixes"]["LCB"]]
    assert len(same_prefix) == 96
    row = deepcopy(same_prefix[0])
    row["arms"]["LCB"]["elapsed_us"] += 1
    verify_equal_prefix_receipts(row)
    row["arms"]["LCB"]["jass_score"] += 1
    with pytest.raises(ValueError, match="searches diverged with the same prefix"):
        verify_equal_prefix_receipts(row)
    row["prefixes"]["LCB"] = list(reversed(row["prefixes"]["L"]))
    verify_equal_prefix_receipts(row)


@pytest.mark.parametrize(("corruption", "error"), [
    ("missing", "Missing root trace"),
    ("duplicate", "Unexpected or duplicate root trace"),
    ("order", "Invalid root trace attempt"),
    ("nodes", "Root trace disagrees with paired receipt"),
])
def test_trace_audit_rejects_corrupted_archives(tmp_path, corruption, error):
    _, _, _, rows = read_arena(PILOT)
    manifest = json.loads((PILOT / "manifest.json").read_bytes())
    targets = {row["target_fen"]: row for row in manifest["benchmark_targets"]}
    results = tmp_path / "results"
    results.mkdir()
    for budget in BUDGETS:
        path = PILOT / "results" / f"traces-{budget}.jsonl.gz"
        (results / path.name).write_bytes(path.read_bytes())
    path = results / "traces-50000.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as archive:
        traces = [json.loads(line) for line in archive]
    if corruption == "missing":
        traces.pop()
    elif corruption == "duplicate":
        traces.append(traces[0])
    elif corruption == "order":
        traces[0]["attempts"][1]["expected"].reverse()
    else:
        traces[0]["attempts"][-1]["nodes_after"] -= 1
    with gzip.open(path, "wt", encoding="utf-8") as archive:
        for trace in traces:
            archive.write(json.dumps(trace) + "\n")
    with pytest.raises(ValueError, match=error):
        validate_traces(tmp_path, rows, targets)


def test_replication_requires_five_disjoint_arenas_and_excludes_ceiling_pairs():
    provenance, frozen, diagnostic, receipts = read_arena(PILOT)
    packets = []
    for index in range(5):
        event = f"arena{index}"
        previous = deepcopy(provenance)
        previous["event"].update(id=event, startsAt=datetime.fromtimestamp(
            REPLICATION_CUTOFF / 1000 + index * 3600, timezone.utc
        ).isoformat())
        previous["selection"]["protocol_sha256"] = "protocol"
        previous["inputs"]["event"][0]["sha256"] = f"digest{index}"
        previous["event_game_ids"] = [f"game{index}"]
        changed = {**diagnostic, "changed_prefix_targets": [
            event + fen for fen in diagnostic["changed_prefix_targets"]
        ]}
        rows = [{**row, "target_fen": event + row["target_fen"]} for row in receipts]
        packets.append((previous, [{"fen": event + row["fen"]} for row in frozen], changed, rows))

    result = aggregate(packets, "protocol")
    primary = result["by_budget"][50_000]["all"]
    assert not primary["complete"]
    assert primary["planned_targets"] == 170
    assert primary["budget_complete_targets"] == 165
    assert primary["comparisons"]["L"]["ordinary_pairs"] == 155
    assert primary["comparisons"]["L"]["mean_delta_centimen"] == 0
    assert sum(primary["comparisons"]["L"]["chosen_category_pairs_control_to_lcb"].values()) == 165
    assert primary["comparisons"]["L"]["arena_game_bootstrap"]["events"] == 5
    assert result["by_budget"][50_000]["changed_prefix"]["budget_complete_targets"] == 10
    with pytest.raises(ValueError, match="Exactly five"):
        aggregate(packets[:-1], "protocol")
    packets[-1][0]["event_game_ids"] = packets[0][0]["event_game_ids"]
    with pytest.raises(ValueError, match="overlapping"):
        aggregate(packets, "protocol")


def test_changed_move_reports_category_without_numeric_regret():
    provenance, _, diagnostic, rows = read_arena(PILOT)
    row = deepcopy(next(row for row in rows if row["budget"] == 50_000
                        and all(arm["stop"] == "nodes" for arm in row["arms"].values())
                        and row["arms"]["LCB"]["ordinary_regret_centimen"] is not None))
    row["arms"]["LCB"].update(best_move="alternate", ordinary_regret_centimen=None,
                              scan_chosen_category="loss")
    result = pool([(provenance, [], diagnostic, [row])], 50_000, changed_only=False)
    comparison = result["comparisons"]["L"]
    assert comparison["ordinary_pairs"] == 0
    assert comparison["nonordinary_pairs"] == 1
    assert comparison["chosen_category_pairs_control_to_lcb"] == {"ordinary->loss": 1}
    change, = comparison["changed_moves"]
    assert (change["reference_category"], change["LCB_category"], change["control_category"]) == (
        "ordinary", "loss", "ordinary",
    )
    assert change["delta_centimen"] is None


def test_scoring_precheck_detects_substituted_source(monkeypatch):
    from research.mtdp.jass_benchmark import spatial_replication as study

    arena = PILOT.parent / "replication/uG0fGZzB"
    _, frozen, manifest = study.read_freeze(arena)
    assert len(frozen) == 4327
    assert len(manifest["benchmark_targets"]) == 25
    original_loads = study.json.loads

    def substitute_manifest(raw):
        data = original_loads(raw)
        if isinstance(data, dict) and "benchmark_targets" in data:
            data["benchmark_targets"][0]["source_fens"]["LCB"] = "substituted"
        return data

    monkeypatch.setattr(study.json, "loads", substitute_manifest)
    with pytest.raises(ValueError, match="differs from frozen position"):
        study.read_freeze(arena)
