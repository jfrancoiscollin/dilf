"""H13 authenticated inputs for D1 structural preflight; no cohort admission.

Position hash contract: SHA256(canonical_fen(fen).encode('utf-8')), no newline.
Trajectory hashes retain the legacy complete legal trajectory serializer.
Public event/tournament labels and registry completeness remain unproven.
"""
import hashlib
from pathlib import Path

from research.mtdp.decision_equivalence.corpus_admission import audit
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_fen_bridge import load_verified_cache, CACHE_SHA256
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.prospective_source_preflight import preflight_sources


def canonical_position_sha256(fen):
    return hashlib.sha256(canonical_fen(fen).encode('utf-8')).hexdigest()


def export_known_exclusions(cache_path, *, exclusion_ledger=None):
    """Derive exclusions from pinned cache and optional authenticated sidecar bytes."""
    cache = load_verified_cache(cache_path)
    fens = cache['confirmed_fens']
    if exclusion_ledger is not None:
        from research.mtdp.conservative_exclusion_ledger import load_verified_ledger
        if not isinstance(exclusion_ledger, dict) or set(exclusion_ledger) != {'inventory', 'manifest', 'supplement'}:
            raise ValueError('Complete authenticated exclusion sidecar paths required')
        fens = load_verified_ledger(cache_path, **exclusion_ledger)['canonical_fens']
    return {
        'game_ids': sorted(set(cache['public_game_ids'])),
        'raw_sha256': sorted({s['sha256'] for s in cache['sources']}),
        'trajectory_sha256': sorted(set(cache['fingerprints'])),
        'canonical_sha256': sorted({canonical_position_sha256(fen)
                                    for fen in fens}),
    }


def verify_derived_rows(rows, proof):
    """Require hash claims to equal values authenticated/replayed by H13.

    This helper is a comparison only, not a standalone admission entry point.
    The public bridge produces its proof itself with the pinned rules adapter.
    """
    derived = []
    for row in rows:
        game_id = row['game_id']
        digest, index = game_id.split(':')
        canonical_hash = canonical_position_sha256(row['fen'])
        games = proof['trajectory_checks'][digest]['games']
        matches = [g for g in games if g['source_game_index'] == int(index)]
        if len(matches) != 1:
            raise ValueError('Missing unique authenticated complete trajectory')
        trajectory_hash = matches[0]['trajectory_sha256']
        expected = {'raw_sha256': digest, 'canonical_sha256': canonical_hash,
                    'trajectory_sha256': trajectory_hash}
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError('Declared D1 hash disagrees with authenticated bytes/replay')
        derived.append({**row, **expected})
    return derived


def audit_authenticated_corpus(rows, sources, *, root, adapter, historical_cache,
                               exclusion_ledger=None):
    """Compose existing H13 source/alias/FEN/whole-game proof and unchanged D1 audit.

    No caller proof object, supplied exclusion registry, engine override, source
    scores, target scores or signature definition is accepted here.
    """
    forbidden = (export_known_exclusions(historical_cache) if exclusion_ledger is None else
                 export_known_exclusions(historical_cache, exclusion_ledger=exclusion_ledger))
    engine = checked_engine(Path(adapter).resolve())
    # Remove exactly the three new D1 hash claims for the older closed schema.
    # Preserve every other key so unknown/target-derived fields still fail closed.
    replay_rows = [{key: value for key, value in row.items()
                    if key not in {'raw_sha256', 'trajectory_sha256', 'canonical_sha256'}}
                   for row in rows]
    proof = preflight_sources(replay_rows, sources, engine, root=Path(root),
                              historical_cache=Path(historical_cache))
    verified = verify_derived_rows(rows, proof)
    result = audit(verified, forbidden)
    if not result['admissible_structurally']:
        raise ValueError('D1 structural preflight rejected authenticated rows: ' +
                         ', '.join(result['errors']))
    return {'schema': 'mtdp-h13-authenticated-d1-preflight-v1',
            'historical_cache_sha256': CACHE_SHA256,
            'conservative_exclusion_sidecar_authenticated': exclusion_ledger is not None,
            'conservative_exclusion_manifest_sha256': (hashlib.sha256(
                Path(exclusion_ledger['manifest']).read_bytes()).hexdigest()
                if exclusion_ledger is not None else None),
            'canonical_hash_contract': 'sha256_utf8_canonical_fen_no_newline',
            'declared_hashes_recomputed_and_verified': True,
            'known_historical_registry_authenticated': True,
            'source_proof': proof, 'structural_preflight': result,
            'external_event_identity_authenticated': False,
            'complete_historical_exclusion_registry': False,
            'independent_cohort_qualified': False, 'scientific_freeze': False}
