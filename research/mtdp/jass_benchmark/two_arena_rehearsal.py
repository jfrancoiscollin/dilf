"""Manufactured two-event transport/replay rehearsal, never real tournament data."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from research.mtdp.jass_benchmark import two_arena_acquisition as acquisition
from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark.two_arena_replay import proposal
from research.mtdp.jass_benchmark.named_arena_rehearsal import FIXTURE_FEN
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest


def game(identity, fen):
    return (f'[Event "SYNTHETIC no tournament outcome"]\r\n'
            f'[Site "https://lidraughts.org/{identity}"]\r\n[Synthetic "true"]\r\n'
            f'[FEN "{fen}"]\r\n\r\n*\r\n\r\n').encode()


def rehearse(root, exclusions, adapter, executable, output):
    output.mkdir(parents=True, exist_ok=False)
    registered = study.load(root)
    fixed = datetime(2026, 11, 19, 3, tzinfo=timezone.utc)
    variant = FIXTURE_FEN.replace(',45,', ',44,')
    payloads = {
        study.EVENTS[0]: game('SYNTHA01', FIXTURE_FEN),
        study.EVENTS[1]: game('SYNTHB01', FIXTURE_FEN) + game('SYNTHB02', variant),
    }
    calls = []

    def fake_fetch(url, metadata=False):
        calls.append(url)
        event = url.split('/')[5]
        if metadata:
            record = next(r['event'] for r in registered['events'] if r['event']['id'] == event)
            raw = _bytes({**record, 'isFinished': True, 'secondsToStart': 0})
        else:
            raw = payloads[event]
        return raw, {'url': url, 'sha256': digest(raw), 'bytes': len(raw),
                     'requested_at_utc': fixed.isoformat(), 'retrieved_at_utc': fixed.isoformat(),
                     'request_id': f'synthetic-two-arena-{len(calls)}'}

    acquired = output/'acquired'
    with patch.object(acquisition, '_fetch', fake_fetch), patch.object(study, '_now', lambda: fixed):
        acquisition.acquire(root, acquired)
        value = proposal(root, acquired, exclusions, adapter, executable)
    if len(calls) != 6 or not all('/games' not in u for u in calls[:2]):
        raise ValueError('Both metadata requests must precede the four separate synthetic PDN requests')
    a, b = (value['events'][e] for e in study.EVENTS)
    if (not value['synthetic_rehearsal'] or value['scientific_freeze']
            or [len(x['benchmark_targets']) for x in (a,b)] != [1,1]
            or b['game_status_counts'] != {'accepted': 1, 'excluded_token_sequence': 1}
            or [x['jass_catalogue']['target_action_occurrences'] for x in (a,b)] != [10,10]):
        raise ValueError('Synthetic joint target/mapping/whole-game alias positive control changed')
    raw = _bytes(value)
    (output/'synthetic-proposal.json').write_bytes(raw)
    report = {'schema': 'mtdp-two-arena-synthetic-rehearsal-v1', 'scientific_freeze': False,
              'synthetic_rehearsal': True, 'hash_seed': os.environ.get('PYTHONHASHSEED', 'unset'),
              'proposal_sha256': digest(raw), 'http_transport': 'mocked_in_memory_no_network',
              'http_requests': 6, 'target_counts': [1,1], 'target_action_counts': [10,10],
              'later_whole_game_token_aliases_excluded': 1,
              'raw_crlf_preserved': all((acquired/e/'first.pdn').read_bytes() == payloads[e] for e in study.EVENTS),
              'scope': 'engineering_only_no_freeze_publication_or_search_authorization'}
    (output/'rehearsal-report.json').write_bytes(_bytes(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'exclusions', 'adapter', 'executable', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(rehearse(a.root,a.exclusions,a.adapter,a.executable,a.output),sort_keys=True))


if __name__ == '__main__':
    main()
