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
from research.mtdp.historical_alias_gate import (
    load_historical_aliases, screen_historical_source, reject_historical_source,
)
from research.mtdp.historical_trajectory_gate import (
    load_historical_trajectories, audit_source_trajectories, reject_historical_trajectories,
)
from research.mtdp.historical_fen_bridge import load_historical_fens, reject_historical_fen_overlap


def preflight_sources(rows: list[dict], sources: Mapping[str, str | Path],
                      engine, *, root: Path, historical_cache: Path | None = None) -> dict:
    """Authenticate/screen every source, then invoke the existing D1 proof.

    The engine must be pinned real FMJD for actual scientific use; mocks only
    test wiring. No outcome grants independence or authorizes a cohort freeze.
    The optional pinned historical cache screens canonical FENs, complete
    trajectories, raw-source digests, public IDs and normalized notations.
    Independent qualification and registry completeness remain separate.
    """
    audit_with_pdn_bytes(rows, sources)
    historical_view = None
    if historical_cache is not None:
        historical_view = load_historical_fens(historical_cache)
        reject_historical_fen_overlap(rows, historical_view)
    aliases = load_historical_aliases(historical_cache) if historical_cache is not None else None
    alias_checks = {}
    checked = {}
    for row in rows:
        digest = row.get('source_pdn_sha256')
        if digest is None:
            digest = row['metadata']['source']['pdn_sha256']
        if digest in checked:
            continue
        raw = Path(sources[row['game_id']]).read_bytes()
        if aliases is not None:
            alias_report = screen_historical_source(raw, digest, aliases)
            reject_historical_source(alias_report)
            alias_checks[digest] = alias_report
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
    trajectory_checks = {}
    if historical_cache is not None:
        historical = load_historical_trajectories(historical_cache)
        source_games = {}
        for row in rows:
            digest, index = row['game_id'].split(':')
            group = source_games.setdefault(digest, {'path': sources[row['game_id']], 'indices': set()})
            group['indices'].add(int(index))
        for digest, group in sorted(source_games.items()):
            report = audit_source_trajectories(group['path'], digest, group['indices'], engine, historical)
            reject_historical_trajectories(report)
            trajectory_checks[digest] = report
    return {**proof, 'known_reserved_sources_screened': True,
            'historical_source_aliases_screened': aliases is not None,
            'historical_alias_checks': alias_checks,
            'historical_complete_trajectories_screened': historical_cache is not None,
            'trajectory_checks': trajectory_checks,
            'historical_fen_cache_screened': historical_view is not None,
            'historical_fen_cache_sha256': historical_view['historical_cache_sha256'] if historical_view is not None else None,
            'source_checks': dict(sorted(checked.items())),
            'independent_cohort_qualified': False, 'eligible_for_freeze': False,
            'complete_historical_exclusion_registry': False,
            'scope': 'H13 pre-freeze wiring only; independent qualification remains separate'}
