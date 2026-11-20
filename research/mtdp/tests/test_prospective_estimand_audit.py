"""Reproduce the synthetic cross-module H13 inference compatibility audit."""
import json
from pathlib import Path

from research.mtdp.prospective_estimand_audit import audit


def test_synthetic_primary_and_conditional_audit_reproduces_committed_evidence():
    root = Path(__file__).resolve().parents[3]
    expected = json.loads((root / 'research/mtdp/validation/paired-estimand-audit-2026-11-20.json').read_bytes())
    # audit() independently asserts the four-game fixed-mask result, two-game
    # conditional result, and score-change invariance of the primary denominator.
    assert audit() == expected
