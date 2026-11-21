"""H13 known-reserved-source screen, before prospective cohort qualification.

Checks exact archived source digest, public game ID and normalized *notation*
sequence. A notation match is conservative exclusion evidence, not a proof of
canonical trajectory equality. No engine, score or independent cohort is used.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
import zipfile

from research.mtdp.jass_benchmark.named_arena_replay import token_fingerprint
from research.mtdp.pdn_strict import parse_games_strict
from research.mtdp.reserved_source_inventory import build, encoded, sha


def reserved_keys(root):
    inventory = build(root)  # Pins the whole archive, four PDNs and all 606 games.
    public, tokens, digests = set(), set(), set()
    for event in inventory['events']:
        path = root / event['path']
        member = event['archive_member']
        if member is None:
            raw = path.read_bytes()
        else:
            with zipfile.ZipFile(path) as z:
                raw = z.read(member)
        if sha(raw) != event['pdn_sha256']:
            raise ValueError('Reserved source changed during screening')
        digests.add(event['pdn_sha256'])
        public.update(g['public_game_id'] for g in event['games'])
        tokens.update(token_fingerprint(g) for g in parse_games_strict(raw.decode('utf-8-sig')))
    return inventory, digests, public, tokens


def screen(raw, expected_sha256, root):
    """Return explicit known-overlap findings; no outcome grants qualification."""
    if sha(raw) != expected_sha256:
        raise ValueError('Candidate PDN digest mismatch')
    games = parse_games_strict(raw.decode('utf-8-sig'))
    if not games:
        raise ValueError('Empty candidate PDN')
    inventory, digests, public, tokens = reserved_keys(root)
    findings = []
    for game in games:
        reasons = []
        if expected_sha256 in digests:
            reasons.append('reserved_source_digest')
        site = urlsplit(game.tags.get('Site', ''))
        public_id = site.path.lstrip('/').split('/')[0]
        if site.hostname == 'lidraughts.org' and public_id in public:
            reasons.append('reserved_public_game_id')
        if token_fingerprint(game) in tokens:
            reasons.append('reserved_normalized_notation')
        if reasons:
            findings.append({'source_game_index': game.index, 'reasons': reasons})
    return {'schema': 'mtdp-h13-known-reserved-source-screen-v1',
            'candidate_pdn_sha256': expected_sha256, 'candidate_games': len(games),
            'reserved_inventory_sha256': sha(encoded(inventory)),
            'reserved_export_game_entries': inventory['games'],
            'findings': findings,
            'status': 'blocked_reserved_overlap' if findings else 'no_known_reserved_match_not_qualified',
            'independent_cohort_qualified': False, 'eligible_for_freeze': False,
            'complete_historical_fen_trajectory_registry': False,
            'limitations': [
                'Only known reserved exports are screened; unknown aliases and other historical corpora remain.',
                'Different legal notations may encode the same trajectory; no canonical trajectory replay is performed.',
                'No match does not authenticate public IDs, event labels, legality or independence.',
                'Any match conservatively blocks the whole candidate export; no partial filtering or replacement.'
            ]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = screen(a.candidate.read_bytes(), a.expected_sha256, a.root)
    with a.output.open('xb') as out:
        out.write(encoded(report))
    print(json.dumps({'status': report['status'], 'matched_games': len(report['findings']),
                      'independent_cohort_qualified': False}))
    if report['findings']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
