"""Extend the pinned historical cache with the two already closed H13 exports.

Only FMJD legality is replayed. No independent cohort, signature, target score
or search is acquired. Quarantines contribute confirmed prefixes, never guessed
complete trajectories. The old cache and its hashes remain unchanged.
"""
import argparse
import json
from pathlib import Path
import tempfile

from research.mtdp.historical_exclusion_inventory_audit import MEMBERS, check_game_audit, reconcile
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine, index_games, token_fingerprint
from research.mtdp.jass_benchmark.prospective_candidate_replay import public_ids
from research.mtdp.jass_cohort import ADAPTER_COMMIT
from research.mtdp.pdn import read_games
from research.mtdp.reserved_source_inventory import build, encoded, sha

EVENTS = ('s7ahYqL4', 'D9PF2OSW')


def combine(base, base_counts, extension, sources, public, tokens):
    counts, fingerprints = check_game_audit(sources, extension['game_audit'])
    if dict(counts) != extension['status_counts'] or set(fingerprints) != set(extension['fingerprints']):
        raise ValueError('Extension status/fingerprint accounting changed')
    all_sources = base['sources'] + sources
    if len({s['file'] for s in all_sources}) != len(all_sources):
        raise ValueError('Repeated historical source filename')
    if len(base['fingerprints']) != base_counts['unique_complete_trajectories']:
        raise ValueError('Base unique trajectory count changed')
    if base_counts['complete_replay_game_records'] + base_counts['quarantined_game_records'] != sum(s['games'] for s in base['sources']):
        raise ValueError('Base replay/quarantine denominator changed')
    complete = base_counts['complete_replay_game_records'] + len(fingerprints)
    quarantined = base_counts['quarantined_game_records'] + counts['quarantined']
    union = sorted(set(base['fingerprints']) | set(extension['fingerprints']))
    fens = sorted(set(base['confirmed_fens']) | set(extension['confirmed_fens']))
    games = sum(s['games'] for s in all_sources)
    if complete + quarantined != games:
        raise ValueError('Combined game denominator changed')
    return {'sources': all_sources, 'fingerprints': union, 'confirmed_fens': fens,
            'public_game_ids': sorted(set(base['public_game_ids']) | set(public)),
            'normalized_token_sequence_sha256': sorted(set(base['normalized_token_sequence_sha256']) | set(tokens)),
            'extension_game_audit': extension['game_audit'],
            'extension_status_counts': dict(sorted(counts.items())),
            'extension_complete_trajectories_already_base': len(set(base['fingerprints']) & set(extension['fingerprints'])),
            'accounting': {'source_count': len(all_sources), 'source_game_records': games,
                           'extension_game_records': sum(s['games'] for s in sources),
                           'complete_replay_game_records': complete,
                           'quarantined_game_records': quarantined,
                           'unique_complete_trajectories': len(union),
                           'duplicate_complete_trajectory_records': complete - len(union),
                           'confirmed_prefix_fens': len(fens)}}


def prepare(root, base_dir, adapter):
    data = {}
    for name, digest in MEMBERS.items():
        raw = (base_dir / name).read_bytes()
        if sha(raw) != digest:
            raise ValueError('Pinned historical base member changed')
        data[name] = json.loads(raw)
    base = data['two-arena-exclusions.json']
    reserved = build(root)
    base_counts = reconcile(data['P1RUlfJc-exclusions.json'], data['P1RUlfJc-canonical-history.json'], base, reserved)
    if base_counts['reserved_events_missing_as_sources'] != list(EVENTS):
        raise ValueError('Expected exactly the two closed missing exports')
    events = [e for e in reserved['events'] if e['reserved_event_id'] in EVENTS]
    engine = checked_engine(adapter)
    sources, public, tokens = [], [], []
    # Both original archive paths are named first.pdn. Byte-identical temporary
    # copies get canonical filenames so index_games preserves unique identities.
    with tempfile.TemporaryDirectory(prefix='mtdp-closed-exclusions-') as directory:
        paths = []
        for event in events:
            raw = (root / event['path']).read_bytes()
            if sha(raw) != event['pdn_sha256']:
                raise ValueError('Closed reserved PDN changed during replay')
            name = f"mtdp-lidraughts-{event['reserved_event_id']}.pdn"
            path = Path(directory) / name
            path.write_bytes(raw)
            count = len(event['games'])
            sources.append({'file': name, 'games': count, 'sha256': event['pdn_sha256']})
            paths.append((path, count))
            public.extend(public_ids(path))
            tokens.extend(token_fingerprint(g) for g in read_games(path))
        extension = index_games(paths, engine)
    result = combine(base, base_counts, extension, sources, public, tokens)
    for event in reserved['events']:
        if event['pdn_sha256'] not in {s['sha256'] for s in result['sources']}:
            raise ValueError('A reserved event is still absent from the source inventory')
        if not {g['public_game_id'] for g in event['games']} <= set(result['public_game_ids']):
            raise ValueError('A reserved public game identity was lost')
    return {'schema': 'mtdp-h13-four-reserved-events-historical-exclusions-v1',
            'base_member_sha256': MEMBERS, 'adapter_commit': ADAPTER_COMMIT,
            'implementation_sha256': sha(Path(__file__).read_bytes()),
            'closed_event_sources': [{'event_id': e['reserved_event_id'], 'path': e['path'],
                                      'sha256': e['pdn_sha256'], 'games': len(e['games'])} for e in events],
            'known_four_reserved_sources_accounted_for': True,
            'independent_cohort_qualified': False, 'complete_historical_exclusion_registry': False,
            'scientific_freeze': False, 'new_reference_scores_acquired': False,
            'scope': 'historical_cache_plus_two_existing_closed_reserved_exports_no_new_cohort_or_scoring',
            'fen_scope': 'all_confirmed_prefixes_including_quarantines_no_guessed_continuation',
            **result}


def summary(result):
    return {k: v for k, v in result.items() if k not in (
        'fingerprints', 'confirmed_fens', 'public_game_ids',
        'normalized_token_sequence_sha256', 'extension_game_audit')} | {
        'exclusions_sha256': sha(encoded(result)),
        'public_game_ids': len(result['public_game_ids']),
        'normalized_notation_fingerprints': len(result['normalized_token_sequence_sha256'])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'base-dir', 'adapter', 'output', 'summary'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.summary.exists():
        raise ValueError('Refuse to overwrite a historical extension')
    result = prepare(a.root, a.base_dir, a.adapter)
    with a.output.open('xb') as out:
        out.write(encoded(result))
    with a.summary.open('xb') as out:
        out.write(encoded(summary(result)))
    print(json.dumps(summary(result)['accounting'], sort_keys=True))


if __name__ == '__main__':
    main()
