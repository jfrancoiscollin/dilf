"""Pinned raw intake integrity, full-game rules replay and known-history audit.

No target selection, signatures, scores, independence certificate or freeze.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

from pedagogy.game import state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_fen_bridge import CACHE_SHA256, load_verified_cache
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine, trajectory_fingerprint, token_fingerprint
from research.mtdp.pdn import PdnReplayError, validated_trajectory
from research.mtdp.pdn_strict import parse_games_strict

ARCHIVE_SHA = 'efe9f4c133edb5adfaa236a30dabe1a39e931ed0e09b287ae5bb860f0ac2b28c'
RECEIPT_SHA = '5d7f76a05666a9c0bc2b8b7a297bd819fc2955bc68b1c5418625daf359033905'
EVENT = 'uDIrrl1c'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_archive(path):
    raw = Path(path).read_bytes()
    if digest(raw) != ARCHIVE_SHA:
        raise ValueError('intake ZIP digest mismatch')
    with zipfile.ZipFile(path) as z:
        if len(set(z.namelist())) != len(z.namelist()) or sum(i.file_size for i in z.infolist()) > 64_000_000:
            raise ValueError('duplicate or over-budget archive members')
        rb = z.read('receipt.json')
        if digest(rb) != RECEIPT_SHA:
            raise ValueError('receipt digest mismatch')
        receipt = json.loads(rb)
        listing = z.read('listing.json')
        if digest(listing) != receipt['listing_sha256']:
            raise ValueError('listing digest mismatch')
        if len(receipt['candidates']) != 1 or receipt['candidates'][0]['event'] != EVENT:
            raise ValueError('candidate selection differs from pinned intake')
        row = receipt['candidates'][0]
        metadata = z.read(EVENT + '-detail.json')
        pdn = z.read(EVENT + '-export-1.pdn')
        other = z.read(EVENT + '-export-2.pdn')
        if (digest(metadata) != row['metadata_sha256'] or pdn != other
                or digest(pdn) != row['export_1_sha256'] or digest(other) != row['export_2_sha256']
                or len(pdn) != row['export_1_bytes'] or len(other) != row['export_2_bytes']):
            raise ValueError('intake source evidence mismatch')
        detail = json.loads(metadata)
        if (detail['id'] != EVENT or detail['isFinished'] is not True
                or detail['system'] != 'arena' or detail['variant'] != 'standard'
                or detail['clock'] != {'limit': 300, 'increment': 0}
                or EVENT in receipt['reserved_events']):
            raise ValueError('event metadata inconsistent')
        start = datetime.fromisoformat(detail['startsAt'].replace('Z', '+00:00'))
        if start != datetime.fromisoformat(row['starts_at']) or start < datetime.fromisoformat(receipt['cutoff_utc']):
            raise ValueError('event date inconsistent')
        return receipt, row, pdn


def audit(archive, cache_path, adapter):
    receipt, source, pdn = verify_archive(archive)
    games = parse_games_strict(pdn.decode('utf-8-sig'))
    if not games:
        raise ValueError('empty source')
    engine = checked_engine(Path(adapter).resolve())
    cache = load_verified_cache(cache_path)
    historical_fens = {canonical_fen(f) for f in cache['confirmed_fens']}
    trajectories = set(cache['fingerprints'])
    notation = set(cache['normalized_token_sequence_sha256'])
    ids = set(cache['public_game_ids'])
    seen_ids = set()
    reports = []
    for game in games:
        identity = public_id(game)
        if identity is None or identity in seen_ids or game.tags.get('TimeControl') != '300+0':
            raise ValueError('invalid/duplicate identity or wrong game time control')
        seen_ids.add(identity)
        played = datetime.strptime(game.tags['UTCDate'] + ' ' + game.tags['UTCTime'], '%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc)
        if not datetime.fromisoformat(source['starts_at']) <= played <= datetime.fromisoformat(receipt['observed_utc']):
            raise ValueError('game timestamp outside observed source interval')
        row = dict(source_game_index=game.index, public_game_id=identity,
                   public_id_historical_match=identity in ids,
                   notation_historical_match=token_fingerprint(game) in notation)
        try:
            trajectory = validated_trajectory(game, engine)
        except PdnReplayError as error:
            row.update(complete_legal_replay=False, quarantine_reason=str(error))
        else:
            fens = [canonical_fen(state_to_fen(s)) for _, _, s in trajectory]
            row.update(complete_legal_replay=True, validated_plies=len(trajectory)-1,
                       trajectory_sha256=trajectory_fingerprint(trajectory),
                       trajectory_historical_match=trajectory_fingerprint(trajectory) in trajectories,
                       historical_position_occurrences=sum(f in historical_fens for f in fens),
                       nonhistorical_position_occurrences=sum(f not in historical_fens for f in fens))
        reports.append(row)
    return dict(schema='mtdp-fresh-candidate-integrity-replay-v1', event=EVENT,
                intake_zip_sha256=ARCHIVE_SHA, acquisition_receipt_sha256=RECEIPT_SHA,
                source_pdn_sha256=digest(pdn), historical_cache_sha256=CACHE_SHA256,
                adapter_commit=cache['adapter_commit'], source_games=len(games), games=reports,
                complete_legal_games=sum(r['complete_legal_replay'] for r in reports),
                quarantined_games=sum(not r['complete_legal_replay'] for r in reports),
                historical_public_id_matches=sum(r['public_id_historical_match'] for r in reports),
                historical_notation_matches=sum(r['notation_historical_match'] for r in reports),
                historical_complete_trajectory_matches=sum(r.get('trajectory_historical_match', False) for r in reports),
                external_event_membership_authenticated=False,
                complete_historical_registry_proven=False, independent_cohort_admitted=False,
                target_positions_selected=False, scientific_freeze=False,
                new_engine_scores_computed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('archive', 'cache', 'adapter', 'output'):
        p.add_argument('--'+flag, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.archive, a.cache, a.adapter)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
