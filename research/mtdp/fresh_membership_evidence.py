"""Capture/verify game-page event links; no moves, results or scores are parsed."""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
import zipfile

from research.mtdp.fresh_candidate_integrity_replay import verify_archive, digest, EVENT, ARCHIVE_SHA
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.pdn_strict import parse_games_strict

BASE = 'https://lidraughts.org/'


class MembershipHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.urls = []
        self.events = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'section':
            self.sections.append('game__tournament-link' in a.get('class', '').split())
        if tag == 'meta' and a.get('property') == 'og:url':
            self.urls.append(a.get('content'))
        if tag == 'a' and self.sections and self.sections[-1]:
            self.events.append(a.get('href'))

    def handle_endtag(self, tag):
        if tag == 'section' and self.sections:
            self.sections.pop()


def verify_page(raw, game_id, event=EVENT):
    parser = MembershipHTML()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    if parser.sections or parser.urls != [BASE + game_id] or parser.events != ['/tournament/' + event]:
        raise ValueError('missing, conflicting or unscoped game/event identity')
    return {'public_game_id': game_id, 'page_url': parser.urls[0], 'event_id': event}


def input_ids(archive):
    _, _, pdn = verify_archive(archive)
    ids = [public_id(g) for g in parse_games_strict(pdn.decode('utf-8-sig'))]
    if len(ids) != 152 or None in ids or len(set(ids)) != len(ids):
        raise ValueError('unexpected candidate identities')
    return ids


def capture(archive, directory):
    ids = input_ids(archive)
    root = Path(directory)
    root.mkdir(exist_ok=True)
    receipt = dict(schema='mtdp-fresh-game-membership-capture-v1', event=EVENT,
                   intake_zip_sha256=ARCHIVE_SHA, requested_game_ids=ids, responses=[],
                   engine_scores_parsed=False, independent_cohort_admitted=False)
    previous = root / 'receipt.json'
    if previous.exists():
        old = json.loads(previous.read_text())
        if (old['requested_game_ids'] != ids or old['intake_zip_sha256'] != ARCHIVE_SHA
                or len(old['responses']) > len(ids)):
            raise ValueError('resume population mismatch')
        for identity, row in zip(ids, old['responses'], strict=False):
            raw = (root / (identity + '.html')).read_bytes()
            if (row['public_game_id'] != identity or row['sha256'] != digest(raw)
                    or row['bytes'] != len(raw) or row.get('status') != 200
                    or row.get('final_url') != BASE + identity):
                raise ValueError('resume evidence invalid')
            verify_page(raw, identity)
        receipt = old
    completed = len(receipt['responses'])
    for index, identity in enumerate(ids):
        if index < completed:
            continue
        url = BASE + identity
        row = dict(public_game_id=identity, requested_url=url,
                   observed_utc=datetime.now(timezone.utc).isoformat())
        try:
            request = Request(url, headers={'User-Agent': 'MTDP-source-provenance/1.0', 'Accept': 'text/html'})
            with urlopen(request, timeout=20) as response:
                raw = response.read(1_000_001)
                row.update(status=response.status, final_url=response.url,
                           content_type=response.headers.get_content_type())
            if not raw or len(raw) > 1_000_000:
                raise ValueError('empty/oversized page')
            name = identity + '.html'
            (root / name).write_bytes(raw)
            row.update(file=name, sha256=digest(raw), bytes=len(raw))
            verify_page(raw, identity)
            row['page_membership_verified'] = True
        except Exception as error:
            row.update(page_membership_verified=False, error=type(error).__name__)
        receipt['responses'].append(row)
        (root / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        if (index + 1) % 20 == 0 or index + 1 == len(ids):
            print('Captured', index + 1, '/', len(ids), flush=True)
        time.sleep(0.25)
    return receipt


def audit(archive, evidence):
    ids = input_ids(archive)
    rows = []
    with zipfile.ZipFile(evidence) as z:
        if len(z.namelist()) != len(set(z.namelist())) or sum(i.file_size for i in z.infolist()) > 160_000_000:
            raise ValueError('duplicate/oversized evidence archive')
        receipt = json.loads(z.read('receipt.json'))
        if (receipt['event'] != EVENT or receipt['intake_zip_sha256'] != ARCHIVE_SHA
                or receipt['requested_game_ids'] != ids
                or [r['public_game_id'] for r in receipt['responses']] != ids):
            raise ValueError('receipt population changed')
        for identity, r in zip(ids, receipt['responses'], strict=True):
            if (r.get('status') != 200 or r.get('final_url') != BASE + identity
                    or r.get('requested_url') != BASE + identity
                    or r.get('content_type') != 'text/html'
                    or r.get('file') != identity + '.html'):
                raise ValueError('failed, redirected or wrong-content response')
            raw = z.read(r['file'])
            if digest(raw) != r['sha256'] or len(raw) != r['bytes']:
                raise ValueError('page digest/length mismatch')
            rows.append(verify_page(raw, identity))
    return dict(schema='mtdp-fresh-game-membership-evidence-v1', event=EVENT,
                intake_zip_sha256=ARCHIVE_SHA, evidence_zip_sha256=digest(Path(evidence).read_bytes()),
                receipt_sha256=digest(json.dumps(receipt, indent=2, sort_keys=True).encode() + b'\n'),
                source_games=len(ids), game_page_memberships_verified=len(rows), games=rows,
                evidence_scope='separate_public_game_pages_same_publisher_not_independent_authority',
                external_game_page_membership_observed=True, source_data_licence_established=False,
                complete_historical_registry_proven=False, independent_cohort_admitted=False,
                scientific_freeze=False, target_positions_selected=False, engine_scores_parsed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['capture', 'audit'])
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.mode == 'capture':
        capture(a.archive, a.evidence)
    else:
        if a.output is None:
            p.error('--output required for audit')
        report = audit(a.archive, a.evidence)
        with a.output.open('x') as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write('\n')


if __name__ == '__main__':
    main()
