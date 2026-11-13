import json
from pathlib import Path

import pytest

from research.mtdp.jass_benchmark.run import sha256
from research.mtdp.jass_benchmark.spatial_depth_check import compare

DEPTH18 = Path("research/mtdp/jass_benchmark/spatial-jass/replication/depth18")


def test_depth_check_reproduces_archived_disagreements_and_rejects_incomplete_scores():
    manifest_path = DEPTH18 / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    reference = json.loads((DEPTH18 / "target.json").read_bytes())
    published = json.loads((DEPTH18 / "summary.json").read_bytes())
    digest = sha256(manifest_path)
    result = compare(manifest, reference, digest)
    assert result == {key: value for key, value in published.items() if key != "reference_sha256"}
    assert len(result["positions"]) == 5
    assert sorted(row["lcb_minus_l_centimen"]["depth16"] for row in result["positions"]) == [-6, -3, 4, 10, 11]
    reference["action_scores_centimen"][manifest["targets"][0]["target_fen"]].pop()
    with pytest.raises(ValueError, match="invalid action scores"):
        compare(manifest, reference, digest)
