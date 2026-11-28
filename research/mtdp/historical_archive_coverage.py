"""Authenticate old scored-manifest FEN coverage in the pinned H13 cache.

Known archive scope only: no global completeness, event authenticity, new
cohort admission, reference scores, signatures or engine calls are established.
"""
import argparse
import hashlib
import json
from pathlib import Path

from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_fen_bridge import CACHE_SHA256, load_verified_cache
from research.mtdp.jass_benchmark.prospective_candidate_replay import validated_archive_fens

PROVENANCE = 'research/mtdp/jass_benchmark/spatial-jass/replication/CARZrQpl/provenance.json'
PROVENANCE_SHA = 'e8029eff15b30352db9e33857ba58444d093902bfd539800d30cb237829d131f'


def coverage(archived, confirmed):
    """Canonical occupancy containment, never infer legality from FEN syntax."""
    a = {canonical_fen(f) for f in archived}
    b = {canonical_fen(f) for f in confirmed}
    if not a or not b:
        raise ValueError('Nonempty archive and historical cache required')
    missing = a - b
    if missing:
        raise ValueError(f'Historical cache misses {len(missing)} archived canonical FENs')
    def digest(values):
        return hashlib.sha256('\n'.join(sorted(values)).encode()).hexdigest()
    return {'archived_canonical_fens': len(a), 'cache_canonical_fens': len(b),
            'archived_fens_missing_from_cache': len(missing),
            'known_archive_fens_contained': True,
            'archive_canonical_fen_set_sha256': digest(a),
            'cache_canonical_fen_set_sha256': digest(b)}


def audit(root, cache_path):
    raw = (Path(root) / PROVENANCE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROVENANCE_SHA:
        raise ValueError('Historical archive provenance bytes changed')
    cache = load_verified_cache(cache_path)
    # Existing verifier authenticates each listed raw/gzip file before FEN extraction.
    archived, inventory = validated_archive_fens(Path(root), json.loads(raw))
    if inventory != {'archived_files': 247, 'excluded_fens': 188809}:
        raise ValueError('Pinned archive population changed')
    return {'schema': 'mtdp-h13-known-archive-cache-coverage-v1',
            'provenance_path': PROVENANCE, 'provenance_sha256': PROVENANCE_SHA,
            'historical_cache_sha256': CACHE_SHA256, **inventory,
            **coverage(archived, cache['confirmed_fens']),
            'new_engine_nodes': 0, 'new_reference_scores_acquired': False,
            'external_event_identity_authenticated': False,
            'complete_historical_exclusion_registry': False,
            'independent_cohort_qualified': False, 'scientific_freeze': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root, a.cache)
    with a.output.open('x') as f:
        f.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
