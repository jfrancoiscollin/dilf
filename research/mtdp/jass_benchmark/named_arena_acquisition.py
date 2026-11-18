"""Post-finish acquisition of the named arena; no search or freeze permission."""
import argparse
import json
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from urllib.request import Request, urlopen
from pathlib import Path

from research.mtdp.jass_benchmark.named_arena_inputs import EVENT, check_final, final_metadata, registration, utc
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest

FACT_FIELDS = ('id', 'createdBy', 'startsAt', 'system', 'variant', 'clock', 'minutes',
               'isFinished', 'secondsToStart', 'nbGames', 'nbPlayers')


class AcquisitionError(RuntimeError):
    def __init__(self, url, attempts):
        self.attempts = attempts
        super().__init__(f'Unable to acquire {url}: {attempts}')


def _now():
    return datetime.now(timezone.utc)


def _fetch(url, *, metadata=False):
    attempts = []
    for number in range(4):
        row = {'request_id': uuid.uuid4().hex, 'requested_at_utc': _now().isoformat()}
        try:
            request = Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'MTDP-final-inputs/1.0'})
            with urlopen(request, timeout=55) as response:
                raw = response.read()
                row.update(bytes=len(raw), sha256=digest(raw), http_status=response.getcode())
            if not raw:
                raise ValueError('Empty response')
            if metadata:
                json.loads(raw)
            elif not re.search(rb'(?im)^\s*\[Event\s', raw):
                raise ValueError('Response is not a PDN event export')
        except (OSError, ValueError, HTTPException) as error:
            row.update(error=type(error).__name__, http_status=getattr(error, 'code', None))
            attempts.append(row)
            if number < 3:
                time.sleep(min(2 * (number + 1), 8))
            continue
        row['retrieved_at_utc'] = _now().isoformat()
        attempts.append(row)
        return raw, {**row, 'url': url, 'attempts': attempts}
    raise AcquisitionError(url, attempts)


def acquire(root, output):
    reg = registration(root)
    finish = utc(reg['event']['startsAt']) + timedelta(minutes=reg['event']['minutes'])
    if _now() < finish:
        raise ValueError('Acquisition is closed until the scheduled finish')
    output.mkdir(parents=True, exist_ok=False)
    try:
        raw, metadata_receipt = _fetch(f'https://lidraughts.org/api/tournament/{EVENT}', metadata=True)
        metadata = json.loads(raw)
        final_metadata(reg, metadata, _now())
        facts = {key: metadata[key] for key in FACT_FIELDS if key in metadata}
        projection = (json.dumps(facts, sort_keys=True, indent=2) + '\n').encode()
        (output / 'final-metadata.json').write_bytes(projection)
        metadata_receipt['projection_sha256'] = digest(projection)
        attempts = []
        for number in range(1, 5):
            directory = output / f'attempt-{number:02d}'
            directory.mkdir()
            url = f'https://lidraughts.org/api/tournament/{EVENT}/games'
            first, first_receipt = _fetch(url)
            repeat, repeat_receipt = _fetch(url)
            (directory / 'first.pdn').write_bytes(first)
            (directory / 'repeat.pdn').write_bytes(repeat)
            pair = {'number': number, 'first': first_receipt, 'independent_repeat': repeat_receipt, 'matching': first == repeat}
            (directory / 'downloads.json').write_text(json.dumps(pair, sort_keys=True, indent=2) + '\n')
            attempts.append(pair)
            if first == repeat:
                first_path, repeat_path = output / f'mtdp-lidraughts-{EVENT}.pdn', output / 'final-repeat.pdn'
                first_path.write_bytes(first)
                repeat_path.write_bytes(repeat)
                log = output / 'final-downloads.json'
                log.write_text(json.dumps({'metadata': metadata_receipt, 'candidate': pair, 'pair_attempts': attempts}, sort_keys=True, indent=2) + '\n')
                checked = check_final(root, output / 'final-metadata.json', first_path, repeat_path, log, now=_now())
                result = {'schema': 'mtdp-named-acquisition-v1', 'event': EVENT, 'scientific_freeze': False,
                          'input_check': checked, 'matching_pair': number}
                (output / 'acquisition.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
                return result
            if number < 4:
                time.sleep(min(2 * number, 8))
        raise ValueError('No identical final-export pair after four attempts')
    except Exception as error:
        (output / 'acquisition.json').write_text(json.dumps({
            'schema': 'mtdp-named-acquisition-v1', 'event': EVENT, 'scientific_freeze': False,
            'status': 'failed', 'error': type(error).__name__, 'detail': str(error),
            'failed_request_attempts': getattr(error, 'attempts', []),
        }, sort_keys=True, indent=2) + '\n')
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output-directory', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(acquire(a.root, a.output_directory), sort_keys=True))


if __name__ == '__main__':
    main()
