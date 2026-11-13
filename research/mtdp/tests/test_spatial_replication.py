from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark.spatial_replication import (
    BUDGETS, REPLICATION_CUTOFF, aggregate, read_arena,
)

PILOT = Path("research/mtdp/jass_benchmark/spatial-jass/KXaMpuNe")


def test_published_pilot_receipts_validate_against_scan():
    _, _, diagnostic, rows = read_arena(PILOT)
    assert diagnostic["matched"] == 34
    assert len(rows) == 34 * len(BUDGETS)
    assert sum(arm["stop"] == "depth_ceiling" for row in rows for arm in row["arms"].values()) == 9


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
