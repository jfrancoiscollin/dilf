"""H13 complete-game exclusion using the unchanged legacy trajectory serializer.

No signatures, target scores, independence certificate or cohort freeze.
"""
import argparse
import hashlib
import json
from pathlib import Path

from research.mtdp.historical_fen_bridge import CACHE_SHA256, load_verified_cache
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine, trajectory_fingerprint
from research.mtdp.pdn import validated_trajectory
from research.mtdp.pdn_strict import parse_games_strict


def load_historical_trajectories(cache_path):
    cache = load_verified_cache(cache_path)
    values = cache['fingerprints']
    if (not isinstance(values, list) or not values or
            any(not isinstance(v, str) or len(v) != 64 or
                any(c not in '0123456789abcdef' for c in v) for v in values) or
            len(set(values)) != len(values) or
            len(values) != cache['accounting']['unique_complete_trajectories']):
        raise ValueError('Invalid historical complete trajectory registry')
    return frozenset(values)


def audit_source_trajectories(source, expected_sha256, game_indices, engine, historical):
    """Authenticate bytes, replay each requested WHOLE game, then compare hashes.

    Callers must first establish manifest source/index binding. A partial or
    ambiguous replay raises; no prefix hash can clear a complete trajectory.
    Real use requires the pinned FMJD engine; mocks only test the wiring.
    """
    indices = list(game_indices)
    if (not indices or any(type(i) is not int or i < 1 for i in indices) or
            len(set(indices)) != len(indices)):
        raise ValueError('Distinct positive game indices required')
    raw = Path(source).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('PDN source bytes do not match digest')
    games = parse_games_strict(raw.decode('utf-8-sig'))
    if max(indices) > len(games):
        raise ValueError('Game index absent from authenticated PDN')
    reports = []
    for index in sorted(indices):
        trajectory = validated_trajectory(games[index - 1], engine)
        fingerprint = trajectory_fingerprint(trajectory)
        reports.append({'source_game_index': index,
                        'trajectory_sha256': fingerprint,
                        'validated_plies': len(trajectory) - 1,
                        'historical_trajectory_match': fingerprint in historical})
    return {'source_pdn_sha256': digest, 'games': reports,
            'complete_legal_games_verified': len(reports),
            'known_historical_trajectory_matches': sum(r['historical_trajectory_match'] for r in reports),
            'independent_cohort_qualified': False, 'scientific_freeze': False}


def reject_historical_trajectories(report):
    if report['known_historical_trajectory_matches']:
        raise ValueError('Historical complete trajectory overlap: reject prospective batch')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--pdn', type=Path, required=True)
    p.add_argument('--pdn-sha256', required=True)
    p.add_argument('--adapter', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    historical = load_historical_trajectories(a.cache)
    # Authentication and strict parsing below repeat over exactly these bytes.
    games = parse_games_strict(a.pdn.read_bytes().decode('utf-8-sig'))
    engine = checked_engine(a.adapter.resolve())
    report = audit_source_trajectories(a.pdn, a.pdn_sha256, range(1, len(games) + 1), engine, historical)
    report.update({'schema': 'mtdp-h13-historical-complete-trajectory-audit-v1',
                   'historical_cache_sha256': CACHE_SHA256,
                   'historical_complete_trajectories': len(historical),
                   'trajectory_hashes_redefined': False,
                   'new_reference_scores_acquired': False,
                   'complete_historical_exclusion_registry': False})
    with a.output.open('xb') as out:
        out.write((json.dumps(report, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({k: report[k] for k in ('complete_legal_games_verified',
                      'known_historical_trajectory_matches', 'historical_complete_trajectories')}))


if __name__ == '__main__':
    main()
