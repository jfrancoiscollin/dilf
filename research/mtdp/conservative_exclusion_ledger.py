"""Authenticated exclusion-only sidecar; never an admission or played-path proof."""
import argparse
import hashlib
import json
from pathlib import Path

from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_fen_bridge import load_historical_fens, CACHE_SHA256

PROTOCOL_COMMIT = 'd3aa8af0faee195f3bbda7060a1c6d79e13c0ca0'
INVENTORY_SHA256 = '9331319ea0a243a486969871803b22a48524a024227c4ac727dff0a1e223a93a'
RECONSTRUCTION_SHA256 = 'c774e71d1bd29aec50e63a285fb1755dcd558393f8eaa7ef89af5be7802584bc'
BASE_RULES_SHA256 = '5855ceae76fc7db243af85c61508d9505e17904925b9f73d79ed327296690394'
CORRECTED_RULES_SHA256 = '4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def historical_supplement(rows, legacy_fens):
    """Pure role filter, not an authentication entry point. Keep historical owners only."""
    supplement, seen = [], set()
    for row in rows:
        if set(row) != {'fen', 'legacy_cache_member', 'owners'}:
            raise ValueError('Unexpected inventory schema')
        fen = canonical_fen(row['fen'])
        if fen != row['fen'] or fen in seen:
            raise ValueError('Noncanonical or duplicate inventory FEN')
        seen.add(fen)
        if type(row['legacy_cache_member']) is not bool or row['legacy_cache_member'] != (fen in legacy_fens):
            raise ValueError('Legacy membership disagrees with authenticated cache')
        owners, identities = [], set()
        if not isinstance(row['owners'], list) or not row['owners']:
            raise ValueError('Missing owners')
        for owner in row['owners']:
            if set(owner) != {'role', 'game_key', 'plies'} or owner['role'] not in {'historical_quarantines', 'fresh_candidate'}:
                raise ValueError('Unexpected owner schema or role')
            key, plies = owner['game_key'], owner['plies']
            if not isinstance(key, str) or not key or (owner['role'], key) in identities:
                raise ValueError('Invalid or duplicate owner')
            identities.add((owner['role'], key))
            if not isinstance(plies, list) or not plies or any(type(p) is not int or p < 0 for p in plies) or plies != sorted(set(plies)):
                raise ValueError('Invalid owner plies')
            if owner['role'] == 'historical_quarantines':
                owners.append(owner)
        if owners and fen not in legacy_fens:
            supplement.append({'fen': fen, 'canonical_sha256': digest(fen.encode()),
                               'historical_owners': sorted(owners, key=lambda o: o['game_key'])})
    return sorted(supplement, key=lambda row: row['fen'])


def derive(cache_path, inventory_path):
    """Authenticate upstream bytes before deriving any exclusion."""
    legacy = load_historical_fens(cache_path)['canonical_fens']
    raw = Path(inventory_path).read_bytes()
    if digest(raw) != INVENTORY_SHA256:
        raise ValueError('Corrected inventory digest mismatch')
    rows = [json.loads(line) for line in raw.splitlines()]
    supplement = historical_supplement(rows, legacy)
    union = legacy | {row['fen'] for row in supplement}
    if (len(legacy), len(rows), len(supplement), len(union)) != (452526, 34955, 3056, 455582):
        raise ValueError('Pinned exclusion denominators changed')
    payload = b''.join(encoded(row) for row in supplement)
    manifest = {
        'schema': 'mtdp-h13-conservative-exclusion-sidecar-v1',
        'protocol_commit': PROTOCOL_COMMIT,
        'historical_cache_sha256': CACHE_SHA256,
        'corrected_inventory_sha256': INVENTORY_SHA256,
        'verified_reconstruction_report_sha256': RECONSTRUCTION_SHA256,
        'legacy_rules_sha256': BASE_RULES_SHA256,
        'supplement_rules_sha256': CORRECTED_RULES_SHA256,
        'supplement_patch_id': 'king-origin-v1',
        'legacy_canonical_fens': len(legacy), 'supplement_canonical_fens': len(supplement),
        'union_canonical_fens': len(union),
        'union_canonical_fen_set_sha256': digest('\n'.join(sorted(union)).encode()),
        'supplement_bytes': len(payload), 'supplement_sha256': digest(payload),
        'required_owner_role': 'historical_quarantines',
        'fresh_only_positions_excluded_by_supplement': False,
        'exclusion_only': True, 'unique_played_action_paths_certified': False,
        'legacy_cache_or_quarantines_changed': False,
        'complete_historical_exclusion_registry': False,
        'independent_cohort_qualified': False, 'scientific_freeze': False,
        'engine_scores_computed': False,
    }
    return manifest, payload, union


def load_verified_ledger(cache_path, *, inventory, manifest, supplement):
    """Recompute exact sidecar bytes; caller-supplied hashes are never proof."""
    expected, payload, union = derive(cache_path, inventory)
    if Path(manifest).read_bytes() != encoded(expected):
        raise ValueError('Conservative manifest differs from authenticated derivation')
    if Path(supplement).read_bytes() != payload:
        raise ValueError('Conservative supplement differs from authenticated derivation')
    return {**expected, 'canonical_fens': union}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest, payload, _ = derive(args.cache, args.inventory)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / 'historical-supplement.jsonl').open('xb') as out:
        out.write(payload)
    with (args.output_dir / 'conservative-exclusion-manifest.json').open('xb') as out:
        out.write(encoded(manifest))
    print(json.dumps(manifest, sort_keys=True))


if __name__ == '__main__':
    main()
