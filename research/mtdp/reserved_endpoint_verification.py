"""Fresh public HTTPS binding of reserved tournament endpoints to pinned PDNs.

Checks four existing reserved exports, never acquires an independent cohort or
engine score. Does not certify full historical exclusions or FMJD legality.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request

from research.mtdp.reserved_source_inventory import build, encoded, sha


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_response(event, raw, status, final_url):
    expected_url = f"https://lidraughts.org/api/tournament/{event['reserved_event_id']}/games"
    if status != 200 or final_url != expected_url:
        raise ValueError('Unexpected endpoint status or redirect')
    if len(raw) != event['bytes'] or sha(raw) != event['pdn_sha256']:
        raise ValueError('Live PDN differs from pinned reserved export; do not replace archived bytes')
    return {'event_id': event['reserved_event_id'], 'url': expected_url,
            'final_url': final_url, 'http_status': status, 'bytes': len(raw),
            'pdn_sha256': sha(raw), 'archived_games': len(event['games']),
            'byte_equal_to_pinned_archive': True}


def fetch(event):
    url = f"https://lidraughts.org/api/tournament/{event['reserved_event_id']}/games"
    started = now()
    request = urllib.request.Request(url, headers={'Accept': 'application/x-chess-pgn',
                                                 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=30) as response:
        # Bound a response before reading it into memory; no larger replacement export.
        raw = response.read(event['bytes'] + 1)
        report = verify_response(event, raw, response.status, response.geturl())
        return {**report, 'requested_at_utc': started, 'retrieved_at_utc': now(),
                'response_content_type': response.headers.get('Content-Type')}


def verify(root):
    inventory = build(root)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(fetch, inventory['events']))
    return {'schema': 'mtdp-h13-reserved-public-endpoint-binding-v1',
            'checked_at_utc': now(), 'inventory_sha256': sha(encoded(inventory)),
            'events': reports, 'reserved_export_game_entries': inventory['games'],
            'all_four_public_endpoints_byte_equal': True,
            'new_independent_cohort_qualified': False, 'fmjd_legality_verified': False,
            'complete_historical_exclusion_registry': False,
            'new_reference_scores_acquired': False,
            'scope': 'current_public_tournament_url_to_existing_reserved_pdn_digest',
            'limitations': [
                'Authenticates current endpoint bytes under normal HTTPS verification, not a signed historical attestation.',
                'Does not certify historical account ownership, annotations, legality or statistical independence.',
                'All four entire events remain reserved; these HTTP checks do not authorize a new cohort freeze.'
            ]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Refuse to overwrite a previous endpoint verification')
    result = verify(a.root)
    with a.output.open('xb') as out:
        out.write(encoded(result))
    print(json.dumps({'events_verified': len(result['events']),
                      'reserved_game_entries': result['reserved_export_game_entries'],
                      'independent_cohort_qualified': False}))


if __name__ == '__main__':
    main()
