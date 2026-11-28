"""H13 known historical PDN/public-ID/notation aliases; exclusion only.

No engine or target scores. A notation match is conservative evidence, not
canonical trajectory equality or external event authentication.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import zipfile

from research.mtdp.historical_fen_bridge import CACHE_SHA256, load_verified_cache
from research.mtdp.jass_benchmark.named_arena_replay import token_fingerprint
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import ADAPTER_COMMIT
from research.mtdp.pdn_strict import parse_games_strict
from research.mtdp.reserved_source_inventory import SOURCES, ARCHIVE, ARCHIVE_SHA


def public_id(game):
    site = urlsplit(game.tags.get('Site', ''))
    value = site.path.lstrip('/').split('/')[0]
    if site.hostname != 'lidraughts.org':
        return None
    if len(value) != 8 or not value.isascii() or not value.isalnum():
        raise ValueError('Invalid Lidraughts public game identity')
    return value


def load_historical_aliases(cache_path):
    cache = load_verified_cache(cache_path)
    return {'source_sha256': frozenset(s['sha256'] for s in cache['sources']),
            'public_game_ids': frozenset(cache['public_game_ids']),
            'notation_sha256': frozenset(cache['normalized_token_sequence_sha256'])}


def screen_historical_source(raw, expected_sha256, aliases):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Candidate PDN digest mismatch')
    games = parse_games_strict(raw.decode('utf-8-sig'))
    if not games:
        raise ValueError('Empty candidate PDN')
    findings = []
    for game in games:
        reasons = []
        if expected_sha256 in aliases['source_sha256']:
            reasons.append('historical_source_digest')
        if public_id(game) in aliases['public_game_ids']:
            reasons.append('historical_public_game_id')
        if token_fingerprint(game) in aliases['notation_sha256']:
            reasons.append('historical_normalized_notation')
        if reasons:
            findings.append({'source_game_index': game.index, 'reasons': reasons})
    return {'candidate_pdn_sha256': expected_sha256, 'candidate_games': len(games),
            'findings': findings, 'independent_cohort_qualified': False,
            'eligible_for_freeze': False}


def reject_historical_source(report):
    if report['findings']:
        raise ValueError('Historical source alias overlap: reject entire prospective batch')


def reconcile(root, adapter, cache_path):
    cache = load_verified_cache(cache_path)
    aliases = load_historical_aliases(cache_path)
    pinned_checkout(adapter, ADAPTER_COMMIT)
    archive = (root / ARCHIVE).read_bytes()
    if hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA:
        raise ValueError('Historical source archive changed')
    with zipfile.ZipFile(root / ARCHIVE) as z:
        names = [n for n in z.namelist() if n.endswith('.pdn') and Path(n).name != 'independent-repeat.pdn']
        if len({Path(n).name for n in names}) != len(names):
            raise ValueError('Duplicate historical archive basename')
        data = {Path(n).name: z.read(n) for n in names}
        for event, path, member, digest, count in SOURCES:
            data[f'mtdp-lidraughts-{event}.pdn'] = z.read(member) if member else (root / path).read_bytes()
    data['pcblues_games.pdn'] = (root / 'data/exports/pcblues/pcblues_games.pdn').read_bytes()
    for name in ('Bourges2-Seilh.pdn', 'Drancy-Mirepoix.pdn'):
        data[name] = (adapter / 'docs/parties' / name).read_bytes()
    public, notation, reports = set(), set(), []
    for source in cache['sources']:
        raw = data[source['file']]
        report = screen_historical_source(raw, source['sha256'], aliases)
        if report['candidate_games'] != source['games']:
            raise ValueError('Historical game denominator changed')
        games = parse_games_strict(raw.decode('utf-8-sig'))
        ids = [public_id(g) for g in games]
        public.update(i for i in ids if i is not None)
        tokens = {token_fingerprint(g) for g in games}
        notation.update(tokens)
        reports.append({'file': source['file'], 'pdn_sha256': source['sha256'],
                        'games': len(games), 'games_with_public_id': sum(i is not None for i in ids),
                        'matched_games': len(report['findings']),
                        'distinct_notation_fingerprints': len(tokens)})
    if public != aliases['public_game_ids'] or notation != aliases['notation_sha256']:
        raise ValueError('Historical public-ID/notation registry reconciliation failed')
    return {'schema': 'mtdp-h13-historical-source-alias-reconciliation-v1',
            'historical_cache_sha256': CACHE_SHA256, 'adapter_commit': ADAPTER_COMMIT,
            'sources': reports, 'source_count': len(reports),
            'game_records': sum(r['games'] for r in reports),
            'matched_game_records': sum(r['matched_games'] for r in reports),
            'public_game_ids': len(public), 'notation_fingerprints': len(notation),
            'public_registry_exact_set_equality': True,
            'notation_registry_exact_set_equality': True,
            'new_reference_scores_acquired': False, 'scientific_freeze': False,
            'independent_cohort_qualified': False,
            'complete_historical_exclusion_registry': False,
            'public_ids_externally_authenticated': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'adapter', 'cache', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    report = reconcile(a.root, a.adapter, a.cache)
    with a.output.open('xb') as out:
        out.write((json.dumps(report, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({k: report[k] for k in ('source_count', 'game_records',
                      'matched_game_records', 'public_game_ids', 'notation_fingerprints')}))


if __name__ == '__main__':
    main()
