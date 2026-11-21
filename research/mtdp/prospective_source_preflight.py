"""H13 pre-freeze composition of D1 byte/membership and reserved-source gates.

This is not a new scientific admission certificate. All complete PDN exports
are screened before any FMJD replay, and one reserved match rejects the whole
input batch. No target score, signature or search is computed.
"""
from pathlib import Path
from typing import Mapping

from research.mtdp.decision_equivalence.admission_gate import audit_with_pdn_bytes
from research.mtdp.decision_equivalence.content_addressed_admission import (
    audit_content_addressed_games,
)
from research.mtdp.reserved_source_gate import screen
from research.mtdp.historical_fen_bridge import load_historical_fens, reject_historical_fen_overlap


def preflight_sources(rows: list[dict], sources: Mapping[str, str | Path],
                      engine, *, root: Path, historical_cache: Path | None = None) -> dict:
    """Authenticate/screen every source, then invoke the existing D1 proof.

    The engine must be pinned real FMJD for actual scientific use; mocks only
    test wiring. No outcome grants independence or authorizes a cohort freeze.
    The optional pinned historical cache screens observed FENs canonically.
    Full trajectory exclusions and independent qualification remain separate.
    """
    audit_with_pdn_bytes(rows, sources)
    historical_view = None
    if historical_cache is not None:
        historical_view = load_historical_fens(historical_cache)
        reject_historical_fen_overlap(rows, historical_view)
    checked = {}
    for row in rows:
        digest = row.get('source_pdn_sha256')
        if digest is None:
            digest = row['metadata']['source']['pdn_sha256']
        if digest in checked:
            continue
        raw = Path(sources[row['game_id']]).read_bytes()
        report = screen(raw, digest, root)
        if report['findings']:
            raise ValueError('Reserved source overlap: reject the entire prospective batch')
        checked[digest] = {
            'status': report['status'],
            'candidate_games': report['candidate_games'],
            'reserved_inventory_sha256': report['reserved_inventory_sha256'],
        }
    # Only after every complete export clears the known-reserved screen.
    proof = audit_content_addressed_games(rows, sources, engine)
    return {**proof, 'known_reserved_sources_screened': True,
            'historical_fen_cache_screened': historical_view is not None,
            'historical_fen_cache_sha256': historical_view['historical_cache_sha256'] if historical_view is not None else None,
            'source_checks': dict(sorted(checked.items())),
            'independent_cohort_qualified': False, 'eligible_for_freeze': False,
            'complete_historical_exclusion_registry': False,
            'scope': 'H13 pre-freeze wiring only; independent qualification remains separate'}
