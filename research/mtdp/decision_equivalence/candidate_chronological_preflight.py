"""D1-C: require chronological metadata as well as the existing candidate preflight.

This gate is internal only. External source authenticity is NOT established.
"""
from .candidate_preflight import preflight
from .candidate_ply_order import audit_ply_order


def chronological_preflight(records, **kwargs):
    """Fail closed if ply chronology or existing admission checks fail."""
    chronology = audit_ply_order(records)
    baseline = preflight(records, **kwargs)
    return {
        "internal_preflight_pass": bool(
            baseline["internal_preflight_pass"]
            and chronology["chronological_metadata_pass"]
        ),
        "chronology": chronology,
        "baseline": baseline,
        "external_authenticity_proven": False,
        "independent_cohort_admitted": False,
    }
