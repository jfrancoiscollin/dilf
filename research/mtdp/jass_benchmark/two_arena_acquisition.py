"""Joint final-input acquisition for the exact future pair; never scores/freezes."""
import argparse
import json
import time
from pathlib import Path

from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark.named_arena_acquisition import _fetch, FACT_FIELDS
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest


def _clock_gate():
    now = study._now()
    if now < study.FINAL_GATE:
        raise ValueError('Joint final-input gate is closed until both scheduled finishes')
    return now


def check(root, directory):
    record = study.load(root); now = _clock_gate()
    metadata = {e:json.loads((directory/e/'metadata.json').read_bytes()) for e in study.EVENTS}
    study.final_gate(record,metadata,now)
    checks, identities = {}, set()
    for event in study.EVENTS:
        d=directory/event; first,repeat=d/'first.pdn',d/'repeat.pdn'
        if first.resolve()==repeat.resolve() or first.samefile(repeat):
            raise ValueError('Two distinct files per event are required')
        raw=first.read_bytes()
        if not raw or raw!=repeat.read_bytes():
            raise ValueError('Independent joint final exports are empty or divergent')
        log=(d/'downloads.json').read_bytes();receipts=json.loads(log)
        for role in ('first','independent_repeat'):
            r=receipts[role]
            if (r['url']!=f'https://lidraughts.org/api/tournament/{event}/games'
                    or r['sha256']!=digest(raw) or r['bytes']!=len(raw)
                    or not study.FINAL_GATE<=study.utc(r['requested_at_utc'])<=study.utc(r['retrieved_at_utc'])<=now
                    or not isinstance(r['request_id'],str) or not r['request_id'] or r['request_id'] in identities):
                raise ValueError('Joint final acquisition receipt is inconsistent')
            identities.add(r['request_id'])
        checks[event]={'pdn_sha256':digest(raw),'bytes':len(raw),'metadata_sha256':digest((d/'metadata.json').read_bytes()),
                       'download_receipts_sha256':digest(log)}
    return {'schema':'mtdp-two-arena-final-input-check-v1','registration_sha256':study.REGISTRATION_SHA,
            'protocol_sha256':study.PROTOCOL_SHA,'events':checks,'scientific_freeze':False,
            'scope':'joint_final_input_receipts_only_population_and_published_freeze_still_required'}


def acquire(root, output):
    record=study.load(root);_clock_gate()
    output.mkdir(parents=True,exist_ok=False)
    try:
        metadata={}
        # Both completion/format records must pass before ANY game request.
        for event in study.EVENTS:
            d=output/event;d.mkdir()
            raw,receipt=_fetch(f'https://lidraughts.org/api/tournament/{event}',metadata=True)
            facts=json.loads(raw);metadata[event]={k:facts[k] for k in FACT_FIELDS if k in facts}
            (d/'metadata.json').write_bytes(_bytes(metadata[event]))
            (d/'metadata-download.json').write_bytes(_bytes(receipt))
        study.final_gate(record,metadata,study._now())
        for event in study.EVENTS:
            d=output/event;url=f'https://lidraughts.org/api/tournament/{event}/games'
            for number in range(1,5):
                attempt=d/f'attempt-{number:02d}';attempt.mkdir()
                first,a=_fetch(url)
                # Preserve the first response even if the repeat fails technically.
                (attempt/'first.pdn').write_bytes(first);(attempt/'first-download.json').write_bytes(_bytes(a))
                repeat,b=_fetch(url)
                (attempt/'repeat.pdn').write_bytes(repeat);(attempt/'repeat-download.json').write_bytes(_bytes(b))
                receipt={'first':a,'independent_repeat':b,'matching':first==repeat,'attempt':number}
                (attempt/'downloads.json').write_bytes(_bytes(receipt))
                if first==repeat:
                    (d/'first.pdn').write_bytes(first);(d/'repeat.pdn').write_bytes(repeat)
                    (d/'downloads.json').write_bytes(_bytes(receipt));break
                if number<4:time.sleep(min(number*2,8))
            else:raise ValueError(f'No matching final pair for {event}')
        result=check(root,output)
        (output/'acquisition.json').write_bytes(_bytes(result));return result
    except Exception as error:
        (output/'acquisition.json').write_bytes(_bytes({'schema':'mtdp-two-arena-acquisition-failure-v1',
            'scientific_freeze':False,'error':type(error).__name__,'detail':str(error),
            'failed_request_attempts':getattr(error,'attempts',[])}))
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('acquire','check'));p.add_argument('--root',type=Path,required=True)
    p.add_argument('--directory',type=Path,required=True);a=p.parse_args()
    print(json.dumps(acquire(a.root,a.directory) if a.mode=='acquire' else check(a.root,a.directory),sort_keys=True))


if __name__=='__main__':main()
