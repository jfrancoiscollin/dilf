"""Regression tests for overflow-safe D1 paired bootstrap inputs."""
import importlib.util
from pathlib import Path

import pytest

MODULE = Path(__file__).with_name("group_bootstrap.py")
spec = importlib.util.spec_from_file_location("d1_bootstrap_overflow", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_rejects_finite_inputs_with_infinite_paired_delta():
    rows = [
        ("game-a", "fen-a", -1e308, 1e308),
        ("game-b", "fen-b", 0.0, 0.0),
    ]
    with pytest.raises(ValueError, match="non-finite paired difference"):
        module.paired_game_bootstrap(rows, replicates=10)


def test_finite_delta_control():
    rows = [
        ("game-a", "fen-a", -2.0, 3.0),
        ("game-b", "fen-b", 1.0, 2.0),
    ]
    result = module.paired_game_bootstrap(rows, replicates=10, seed=1)
    assert result["estimate"] == 3.0
