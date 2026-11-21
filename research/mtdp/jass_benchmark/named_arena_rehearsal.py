"""Explicit synthetic transport/clock rehearsal with the real FMJD/Jass oracles."""
import argparse
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from research.mtdp.jass_benchmark import named_arena_acquisition as acquisition
from research.mtdp.jass_benchmark import named_arena_inputs as inputs
from research.mtdp.jass_benchmark import named_freeze_bundle as bundle
from research.mtdp.jass_benchmark.named_arena_replay import proposal
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest

FIXTURE_FEN = 'B:W25,26,27,32,33,35,36,37,38,39,40,41,42,43,45,46,47,48,49:B2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,23,24'


class FixtureClock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime(2026, 11, 18, 21, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz is not None else value.replace(tzinfo=None)


class Response(io.BytesIO):
    def getcode(self): return 200


def rehearse(root, registry, index, adapter, jass, executable, output):
    output.mkdir(parents=True, exist_ok=False)
    metadata = {**inputs.registration(root)['event'], 'isFinished': True, 'secondsToStart': 0,
                'nbPlayers': 1, 'quote': 'unrelated fixture prose'}
    pdn = (f'[Event "SYNTHETIC engineering fixture"]\r\n[Site "https://lidraughts.org/SYNTH001"]\r\n'
           f'[Synthetic "true"]\r\n[FEN "{FIXTURE_FEN}"]\r\n\r\n*\r\n').encode()
    calls = []
    identities = iter(['synthetic-metadata', 'synthetic-first', 'synthetic-repeat'])
    def fake_open(request, timeout):
        url = request.full_url; calls.append(url)
        if url == f'https://lidraughts.org/api/tournament/{inputs.EVENT}':
            return Response(json.dumps(metadata).encode())
        if url == f'https://lidraughts.org/api/tournament/{inputs.EVENT}/games':
            return Response(pdn)
        raise AssertionError('Unexpected endpoint in a no-network synthetic rehearsal')
    acquired = output / 'acquired'
    fixed = FixtureClock.now(timezone.utc)
    with patch.object(acquisition, 'urlopen', fake_open), patch.object(acquisition, '_now', lambda: fixed), \
         patch.object(acquisition.uuid, 'uuid4', lambda: SimpleNamespace(hex=next(identities))), \
         patch.object(inputs, 'datetime', FixtureClock):
        acquisition.acquire(root, acquired)
        if len(calls) != 3: raise ValueError('Expected one metadata and two separate PDN requests')
        paths = []
        for n in (1, 2):
            value = proposal(root, acquired / 'final-metadata.json', acquired / bundle.FIRST,
                             acquired / 'final-repeat.pdn', acquired / 'final-downloads.json',
                             registry, index, adapter, jass, executable)
            value['synthetic_rehearsal'] = True
            path = output / f'synthetic-proposal-{n}.json'; path.write_bytes(bundle._bytes(value)); paths.append(path)
        publication = bundle._compose(root, acquired, *paths, {'kind': 'synthetic_in_process_repeats', 'attempts': 2},
                                      output / 'bundle', synthetic=True, now=fixed)
    payloads = {n: (output / 'bundle' / n).read_bytes() for n in bundle.FILES | {'publication.json'}}
    bundle.validate_payloads(payloads, allow_synthetic=True)
    try:
        bundle.validate_payloads(payloads)
    except ValueError as error:
        if 'Synthetic' not in str(error): raise
    else:
        raise AssertionError('Synthetic artifacts could authorize real scoring')
    restored = json.loads(json.dumps(bundle._text_entries(payloads, 'synthetic-do-not-publish')))
    if any(r['content'].encode() != payloads[r['path'].split('/')[-1]] for r in restored):
        raise ValueError('Tree export changed raw bytes')
    value = json.loads(paths[0].read_bytes())
    if len(value['benchmark_targets']) != 1 or value['jass_catalogue']['target_action_occurrences'] != 10:
        raise ValueError('Synthetic positive-control population changed')
    report = {'schema': 'mtdp-synthetic-freeze-rehearsal-v1', 'synthetic_rehearsal': True, 'scientific_freeze': False,
              'hash_seed': os.environ.get('PYTHONHASHSEED', 'unset'), 'http_transport': 'in_memory_fixture_no_network',
              'http_calls': 3, 'targets': 1, 'target_actions': 10, 'production_validator_refused': True,
              'raw_crlf_preserved': b'\r\n' in payloads[bundle.FIRST], 'proposal_sha256': digest(paths[0].read_bytes()),
              'manifest_sha256': publication['files']['manifest.json']['sha256'], 'publication_sha256': digest(payloads['publication.json'])}
    (output / 'rehearsal-report.json').write_bytes(bundle._bytes(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'registry', 'index', 'adapter', 'jass', 'executable', 'output'):
        p.add_argument(f'--{key}', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(rehearse(a.root, a.registry, a.index, a.adapter, a.jass, a.executable, a.output), sort_keys=True))


if __name__ == '__main__':
    main()
