from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark.spatial_replication import (
    BUDGETS, REPLICATION_CUTOFF, aggregate, read_arena,
)
from research.mtdp.jass_benchmark.spatial_jass import verify_equal_prefix_receipts

PILOT = Path("research/mtdp/jass_benchmark/spatial-jass/KXaMpuNe")


def test_published_pilot_receipts_validate_against_scan():
    _, _, diagnostic, rows = read_arena(PILOT)
    assert diagnostic["matched"] == 34
    assert len(rows) == 34 * len(BUDGETS)
    assert sum(arm["stop"] == "depth_ceiling" for row in rows for arm in row["arms"].values()) == 9


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
    assert primary["comparisons"]["L"]["arena_game_bootstrap"]["events"] == 5
    assert result["by_budget"][50_000]["changed_prefix"]["budget_complete_targets"] == 10
    with pytest.raises(ValueError, match="Exactly five"):
        aggregate(packets[:-1], "protocol")
    packets[-1][0]["event_game_ids"] = packets[0][0]["event_game_ids"]
    with pytest.raises(ValueError, match="overlapping"):
        aggregate(packets, "protocol")


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
