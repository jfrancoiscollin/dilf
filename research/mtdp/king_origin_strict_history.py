"""Fixed 4634-record corrected board replay; no scores or automatic admission."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from pedagogy.game import state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.historical_base_quarantine_frontier import bind_sources
from research.mtdp.historical_exclusion_inventory_audit import MEMBERS, reconcile, check_game_audit
from research.mtdp.historical_fen_bridge import load_verified_cache, CACHE_SHA256
from research.mtdp.historical_quarantine_frontier import explore, MAX_FRONTIER, MAX_APPLICATIONS
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.conservative_exclusion_ledger import INVENTORY_SHA256, RECONSTRUCTION_SHA256, digest, encoded
from research.mtdp.pdn import read_games
from research.mtdp.reserved_source_inventory import build

PROTOCOL_COMMIT = 'e73b5d685b9a695e7dbcb8c9f489dcc40b207112'
SUPPLEMENT_SHA256 = '3d3a5dd6326b6815541b402b451c6273917252dc9955a9cefe88b8341b7ce1f8'


def board_sequence_digest(visited, source_plies, complete):
    """Legacy board serializer only if every expected ply has exactly one board.

    Path ambiguity is deliberately not collapsed into a played-action certificate.
    Incomplete frontiers cannot obtain a full-trajectory digest.
    """
    by_ply = defaultdict(set)
    for state, plies in visited.items():
        for ply in plies:
            if type(ply) is not int or not 0 <= ply <= source_plies:
                raise ValueError('Visited ply outside authenticated source length')
            by_ply[ply].add(state_to_fen(state))
    if not complete or set(by_ply) != set(range(source_plies + 1)) or any(len(v) != 1 for v in by_ply.values()):
        return None
    return digest('\n'.join(next(iter(by_ply[p])) for p in range(source_plies + 1)).encode())


def load_fixed_history(root, base_dir):
    data = {}
    for name, sha in MEMBERS.items():
        raw = (Path(base_dir) / name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('Historical member digest mismatch: ' + name)
        data[name] = json.loads(raw)
    old = data['P1RUlfJc-canonical-history.json']
    base = data['two-arena-exclusions.json']
    reconcile(data['P1RUlfJc-exclusions.json'], old, base, build(root))
    cache = load_verified_cache(Path(base_dir) / 'four-reserved-events-exclusions.json')
    if base['sources'] != cache['sources'][:23]:
        raise ValueError('Historical source ancestry mismatch')
    all_audit = {**old['game_audit'], **base['added_event_game_audit'], **cache['extension_game_audit']}
    counts, fingerprints = check_game_audit(cache['sources'], all_audit)
    if len(cache['sources']) != 25 or len(all_audit) != 4824 or counts['quarantined'] != 190 or len(fingerprints) != 4634 or set(fingerprints) != set(cache['fingerprints']):
        raise ValueError('Pinned whole-history denominators changed')
    return cache, all_audit


def load_quarantine_evidence(root, inventory_path, quarantine_keys):
    raw = (Path(root) / 'research/mtdp/validation/king-origin-reconstruction-2026-11-26.json').read_bytes()
    if digest(raw) != RECONSTRUCTION_SHA256:
        raise ValueError('Verified reconstruction report changed')
    report = json.loads(raw)
    historic = [r for r in report['records'] if r['role'] == 'historical_quarantines']
    if {r['game_key'] for r in historic} != quarantine_keys or len(historic) != 190 or not all(r['complete_board_frontier_replay'] for r in historic):
        raise ValueError('Reused historical quarantine scope changed')
    raw = Path(inventory_path).read_bytes()
    if digest(raw) != INVENTORY_SHA256:
        raise ValueError('Corrected inventory digest mismatch')
    fens, owners = set(), set()
    for line in raw.splitlines():
        row = json.loads(line)
        historical = [o for o in row['owners'] if o['role'] == 'historical_quarantines']
        if historical:
            fens.add(canonical_fen(row['fen']))
            owners.update(o['game_key'] for o in historical)
    if len(fens) != 21657 or owners != quarantine_keys:
        raise ValueError('Reused quarantine inventory owner/position scope changed')
    return fens, report['corrected_rules_sha256']


def audit(root, base_dir, adapter, inventory_path):
    root, base_dir = Path(root), Path(base_dir)
    cache, all_audit = load_fixed_history(root, base_dir)
    selected = {k: v for k, v in all_audit.items() if v['status'] != 'quarantined'}
    quarantines = set(all_audit) - set(selected)
    reused_fens, corrected_sha = load_quarantine_evidence(root, inventory_path, quarantines)
    legacy = {canonical_fen(f) for f in cache['confirmed_fens']}
    raw = (root / 'research/mtdp/validation/conservative-historical-supplement-2026-11-26.jsonl').read_bytes()
    if digest(raw) != SUPPLEMENT_SHA256:
        raise ValueError('Verified exclusion supplement changed')
    existing = legacy | {json.loads(line)['fen'] for line in raw.splitlines()}
    if len(existing) != 455582:
        raise ValueError('Existing conservative exclusion denominator changed')
    # Raw files from the pinned adapter are historical versioned inputs too.
    bound = bind_sources(base_dir, cache['sources'], root, extra_roots=(adapter,))
    games = {}
    for source in cache['sources']:
        parsed = read_games(bound[source['file']])
        if len(parsed) != source['games']:
            raise ValueError('Authenticated source game count changed')
        games[source['file']] = parsed
    engine, receipt = corrected_engine(adapter)
    if receipt['corrected_rules_sha256'] != corrected_sha:
        raise ValueError('Corrected rules differ from reused quarantine proof')
    rows, possible, new_owners = [], set(), defaultdict(dict)
    for ordinal, (key, baseline) in enumerate(sorted(selected.items()), 1):
        filename, index = key.rsplit(':', 1)
        game = games[filename][int(index) - 1]
        if game.index != int(index) or len(game.moves) != baseline['validated_plies']:
            raise ValueError('Authenticated source/index/ply binding changed')
        row, visited = explore(game, engine)
        row.pop('strict_action_quarantine_retained')
        sha = board_sequence_digest(visited, len(game.moves), row['complete_board_frontier_replay'])
        row.update(game_key=key, legacy_status=baseline['status'],
                   legacy_board_sequence_sha256=baseline['trajectory_sha256'],
                   corrected_board_sequence_sha256=sha,
                   board_sequence_matches_legacy=(sha == baseline['trajectory_sha256']) if sha else None,
                   played_action_path_identity_certified=False,
                   legacy_classification_changed=False)
        for state, plies in visited.items():
            fen = canonical_fen(state_to_fen(state))
            possible.add(fen)
            if fen not in existing:
                new_owners[fen][key] = sorted(plies)
        rows.append(row)
        if ordinal % 250 == 0 or ordinal == len(selected):
            print(f'Replayed {ordinal}/{len(selected)} strict historical records', flush=True)
    combined = possible | reused_fens
    new_inventory = b''.join(encoded({'fen': f, 'canonical_sha256': digest(f.encode()),
        'historical_owners': [{'game_key': k, 'plies': p} for k, p in sorted(owners.items())]})
        for f, owners in sorted(new_owners.items()))
    report = dict(schema='mtdp-king-origin-v1-strict-history-board-replay-v1',
        protocol_commit=PROTOCOL_COMMIT, historical_cache_sha256=CACHE_SHA256,
        base_member_sha256=MEMBERS, reused_reconstruction_report_sha256=RECONSTRUCTION_SHA256,
        reused_corrected_inventory_sha256=INVENTORY_SHA256, supplement_sha256=SUPPLEMENT_SHA256,
        **receipt, raw_sources=cache['sources'], source_records=4824, strict_records=len(selected),
        strict_unique_legacy_board_sequences=len({v['trajectory_sha256'] for v in selected.values()}),
        reused_corrected_quarantine_records=190, reused_corrected_quarantine_fens=len(reused_fens),
        frontier_limit=MAX_FRONTIER, application_limit=MAX_APPLICATIONS,
        status_counts=dict(sorted(Counter(r['status'] for r in rows).items())),
        matching_legacy_board_sequence_records=sum(r['board_sequence_matches_legacy'] is True for r in rows),
        changed_legacy_board_sequence_records=[r['game_key'] for r in rows if r['board_sequence_matches_legacy'] is False],
        unresolved_board_sequence_records=[r['game_key'] for r in rows if r['board_sequence_matches_legacy'] is None],
        corrected_action_path_ambiguity_records=[r['game_key'] for r in rows if r['ambiguities']],
        strict_possible_fens=len(possible), known_25_source_possible_fens=len(combined),
        known_25_source_possible_fen_set_sha256=digest('\n'.join(sorted(combined)).encode()),
        legacy_fens_absent_from_combined_replay=len(legacy - combined),
        existing_ledger_fens_absent_from_combined_replay=len(existing - combined),
        new_possible_fens_outside_existing_ledger=len(new_owners),
        new_fens_require_independent_legal_oracle=bool(new_owners),
        new_inventory_bytes=len(new_inventory), new_inventory_sha256=digest(new_inventory),
        records=rows, legacy_cache_or_quarantines_changed=False,
        global_historical_registry_complete=False, independent_cohort_qualified=False,
        scientific_freeze=False, scores_or_signatures_computed=False,
        new_cohorts_reserved=False)
    return report, new_inventory


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'base-dir', 'adapter', 'corrected-inventory', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(exist_ok=False)
    report, inventory = audit(args.root, args.base_dir, args.adapter, args.corrected_inventory)
    raw = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    (args.output_dir / 'strict-history-replay.json').write_bytes(raw)
    summary = {k: v for k, v in report.items() if k != 'records'}
    summary.update(full_report_bytes=len(raw), full_report_sha256=digest(raw),
                   per_record_evidence_location='strict-history-replay.json')
    (args.output_dir / 'strict-history-summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2) + '\n')
    (args.output_dir / 'new-historical-possible-fens.jsonl').write_bytes(inventory)


if __name__ == '__main__':
    main()
