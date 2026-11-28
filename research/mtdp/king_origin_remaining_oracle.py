"""Frozen remaining historical active-king roots vs pinned independent Jass."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.king_origin_inventory_impact import compare_actions, encoded, METRICS, BATCH_SIZE
from research.mtdp.king_origin_remaining_scope import authenticated_scope
from research.mtdp.return_capture_oracle import parse_catalogues

PROTOCOL_COMMIT = '6b331c4268e4d634d4abd23d29c485a74c7129df'
SCOPE_SHA256 = 'c9a64a0a9bf9a6b348a037973b27ca687fc0fda29dca1ba231a99fe4bb9aa5d0'


def frozen_scope(root, cache, inventory):
    raw = (Path(root) / 'research/mtdp/validation/king-origin-remaining-active-king-scope-2026-11-26.json').read_bytes()
    if digest(raw) != SCOPE_SHA256:
        raise ValueError('Frozen active-king scope changed')
    actual, payload = authenticated_scope(root, cache, inventory)
    expected = json.loads(raw)
    if (actual != expected or len(payload.splitlines()) != 48654
            or len(payload) != expected['selected_fens_bytes']
            or digest(payload) != expected['selected_fens_sha256']):
        raise ValueError('Scope derivation differs from preregistration')
    return expected, payload


def audit(root, cache, inventory, adapter, jass, executable):
    scope, payload = frozen_scope(root, cache, inventory)
    fens = payload.decode().splitlines()
    pinned_checkout(Path(jass).resolve(), JASS_COMMIT)
    legacy = checked_engine(Path(adapter).resolve())
    fixed, receipt = corrected_engine(adapter)
    if receipt['corrected_rules_sha256'] != '4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d':
        raise ValueError('Corrected rules identity changed')
    ledger, witnesses, raw_catalogues = bytearray(), bytearray(), bytearray()
    summary = Counter({key: 0 for key in (*METRICS, 'positions', 'path_only_changes', 'added_roots', 'removed_roots')})
    for start in range(0, len(fens), BATCH_SIZE):
        chunk = fens[start:start + BATCH_SIZE]
        process = subprocess.run([str(Path(executable).resolve())],
            input=''.join(fen + '\n' for fen in chunk), capture_output=True, text=True,
            check=True, timeout=30)
        catalogues = parse_catalogues(process.stdout, chunk)
        raw_catalogues.extend(process.stdout.encode())
        for index, (fen, catalogue) in enumerate(zip(chunk, catalogues, strict=True), start):
            state = parse_fen(fen)
            if not state.kings_of(state.turn):
                raise ValueError('Non-active-king board entered frozen comparison')
            metrics, witness = compare_actions(legacy.legal_moves(state), fixed.legal_moves(state), catalogue)
            summary['positions'] += 1
            for key in METRICS:
                summary[key] += metrics[key]
            summary['path_only_changes'] += metrics['path_sets_changed'] and not metrics['root_sets_changed']
            summary['added_roots'] += metrics['added_root_count']
            summary['removed_roots'] += metrics['removed_root_count']
            ledger.extend(encoded(dict(index=index, fen_sha256=digest(fen.encode()), **metrics)))
            if metrics['path_sets_changed'] or metrics['legacy_jass_mismatch'] or metrics['corrected_jass_mismatch']:
                witnesses.extend(encoded(dict(fen=fen, **metrics, **witness)))
        print(f'Compared {min(start + BATCH_SIZE, len(fens))}/{len(fens)} frozen active-king positions', flush=True)
    report = dict(schema='mtdp-h13-remaining-historical-active-king-oracle-v1',
        protocol_commit=PROTOCOL_COMMIT, frozen_scope_sha256=SCOPE_SHA256,
        selected_fens_sha256=scope['selected_fens_sha256'], selected_fens_bytes=len(payload),
        adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT, **receipt,
        jass_batch_size=BATCH_SIZE, summary=dict(sorted(summary.items())),
        historical_active_king_fens=scope['historical_active_king_fens'],
        previously_verified_historical_active_king_fens=scope['previously_checked_historical_active_king_fens'],
        historical_without_active_king_fens_out_of_scope=scope['historical_without_active_king_fens'],
        prior_coverage_replayed=False,
        all_known_historical_active_king_roots_match_jass=(summary['corrected_jass_mismatch'] == 0 and summary['jass_duplicate_root_keys'] == 0),
        position_ledger_sha256=digest(ledger), position_ledger_bytes=len(ledger),
        witnesses_sha256=digest(witnesses), witnesses_bytes=len(witnesses),
        raw_catalogue_sha256=digest(raw_catalogues), raw_catalogue_bytes=len(raw_catalogues),
        default_rules_or_cache_changed=False, engine_scores_computed=False,
        signatures_computed=False, independent_cohort_qualified=False,
        global_historical_registry_complete=False, scientific_freeze=False,
        played_capture_paths_certified=False, new_cohorts_reserved=False)
    provenance = dict(catalogue_binary_sha256=digest(Path(executable).read_bytes()),
        adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT, **receipt)
    return report, payload, bytes(ledger), bytes(witnesses), bytes(raw_catalogues), provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'adapter', 'jass', 'executable', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(exist_ok=False)
    report, fens, ledger, witnesses, raw, provenance = audit(args.root, args.cache,
        args.corrected_inventory, args.adapter, args.jass, args.executable)
    for name, value in [('remaining-active-king-oracle.json', report), ('provenance.json', provenance)]:
        (args.output_dir / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    for name, value in [('remaining-active-king-fens.txt', fens), ('position-ledger.jsonl', ledger),
                        ('change-witnesses.jsonl', witnesses), ('jass-catalogues.txt', raw)]:
        (args.output_dir / name).write_bytes(value)


if __name__ == '__main__':
    main()
