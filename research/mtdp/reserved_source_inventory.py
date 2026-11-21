"""H13 exclusion handoff: archived reserved PDNs to D1 content-addressed IDs.

No reference scores or rules engine are read. This authenticates archived bytes
and enumerates every parsed game, including games whose legality is unverified.
It is neither an exhaustive historical FEN registry nor event authentication.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import zipfile

from research.mtdp.pdn_strict import parse_games_strict

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
ARCHIVE = BASE + 'historical-replay/pdn-inputs.zip'
ARCHIVE_SHA = '4c6b2941a4e18be4df016341f62de314657f215622440999843ea05ee58c5ed3'
# Existing immutable historical exports, never selected from target scores.
SOURCES = (
    ('fFgE7oED', ARCHIVE, 'mtdp-lidraughts-fFgE7oED.pdn',
     '916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2', 157),
    ('P1RUlfJc', BASE + 'P1RUlfJc/mtdp-lidraughts-P1RUlfJc.pdn', None,
     'c1c23993b39da11442e2f4bc8cb5cbf8f9fb2713463be5b981d95a190cd68439', 241),
    ('s7ahYqL4', BASE + 'two-named-arenas-final/s7ahYqL4/first.pdn', None,
     'e90a9926b1b1d740a1d8c0eb2b430f8f6a0293446e5e8c593f0a32ab745700c7', 147),
    ('D9PF2OSW', BASE + 'two-named-arenas-final/D9PF2OSW/first.pdn', None,
     'f22cde28cbc0ffffebc632cb6e0f7b9945d6639e46030ab00f20ac71af6bca6b', 61),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def game_inventory(raw, expected_digest, expected_games):
    if sha(raw) != expected_digest:
        raise ValueError('Reserved PDN bytes changed')
    games = parse_games_strict(raw.decode('utf-8-sig'))
    if not games or len(games) != expected_games:
        raise ValueError('Reserved PDN game count changed')
    rows, seen = [], set()
    for game in games:
        site = urlsplit(game.tags.get('Site', ''))
        public_id = site.path.lstrip('/').split('/')[0]
        if site.hostname != 'lidraughts.org' or len(public_id) != 8 or not public_id.isascii() or not public_id.isalnum():
            raise ValueError('Missing canonical public game identity')
        if public_id in seen:
            raise ValueError('Repeated public game identity within reserved export')
        seen.add(public_id)
        rows.append({'game_id': f'{expected_digest}:{game.index}',
                     'source_game_index': game.index, 'public_game_id': public_id})
    return rows


def build(root):
    archive = (root / ARCHIVE).read_bytes()
    if sha(archive) != ARCHIVE_SHA:
        raise ValueError('Historical PDN archive changed')
    events = []
    for event, path, member, digest, count in SOURCES:
        if member is None:
            raw = (root / path).read_bytes()
        else:
            with zipfile.ZipFile(root / path) as z:
                if z.namelist().count(member) != 1:
                    raise ValueError('Missing or duplicate archive member')
                raw = z.read(member)
        events.append({'reserved_event_id': event, 'path': path,
                       'archive_member': member, 'pdn_sha256': digest,
                       'bytes': len(raw), 'games': game_inventory(raw, digest, count)})
    return {'schema': 'mtdp-h13-reserved-source-inventory-v1',
            'scope': 'all_games_in_four_archived_reserved_exports',
            'exclusion_only': True, 'scientific_freeze': False,
            'independent_cohort_qualified': False,
            'event_labels_externally_authenticated': False,
            'complete_historical_fen_trajectory_registry': False,
            'historical_archive_sha256': ARCHIVE_SHA,
            'implementation_sha256': sha(Path(__file__).read_bytes()),
            'games': sum(len(e['games']) for e in events), 'events': events,
            'limitations': [
                'Event association follows the existing H13 archive/freeze, not a new external verification.',
                'Content-addressed IDs change when PDN bytes change; also exclude public IDs and entire events.',
                'No legality replay or FEN/trajectory registry is produced; ambiguous games remain excluded whole.',
                'Other historical sources and aliases still require D1/H43 reconciliation before any cohort freeze.'
            ]}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = build(args.root)
    raw = encoded(value)
    with args.output.open('xb') as out:
        out.write(raw)
    print(json.dumps({'games': value['games'], 'sha256': sha(raw), 'exclusion_only': True}))


if __name__ == '__main__':
    main()
