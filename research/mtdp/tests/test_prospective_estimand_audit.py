"""Reproduce the synthetic cross-module H13 inference compatibility audit."""
import json
from pathlib import Path

from research.mtdp.prospective_estimand_audit import audit


def test_synthetic_primary_and_conditional_audit_reproduces_committed_evidence():
    root = Path(__file__).resolve().parents[3]
    expected = json.loads((root / 'research/mtdp/validation/paired-estimand-audit-v2-2026-11-20.json').read_bytes())
    # audit() independently asserts the four-game fixed-mask result, two-game
    # conditional result, and score-change invariance of the primary denominator.
    assert audit() == expected


def test_historical_v1_numeric_evidence_is_preserved():
    root = Path(__file__).resolve().parents[3]
    historical = json.loads((root / 'research/mtdp/validation/paired-estimand-audit-2026-11-20.json').read_bytes())
    current = audit()
    for case in ('original', 'one_tie_changed_legal_population_unchanged'):
        assert current[case]['aggregate'] == historical[case]['aggregate']
        assert current[case]['primary_fixed_legal_count_bootstrap'] == historical[case]['primary_fixed_legal_count_bootstrap']
        secondary = dict(current[case]['new_d1_bridge_conditional_bootstrap'])
        assert secondary.pop('top3_population') == 'conditional_informative'
        assert secondary.pop('top3_population_is_primary_fixed') is False
        assert secondary == historical[case]['new_d1_bridge_conditional_bootstrap']
