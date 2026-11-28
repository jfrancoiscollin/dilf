"""Authenticated remaining historical FENs without an active-side king."""
import argparse
import json
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import load_verified_ledger, INVENTORY_SHA256, RECONSTRUCTION_SHA256, digest
from research.mtdp.king_origin_remaining_scope import STRICT_SUMMARY_SHA256, IMPACT_REPORT_SHA256
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen

KING_ORACLE_SHA256 = '95adab875fcc7b3fa260d9ec61d6222d2ab82eb1618e0fd20ceccf61dde80caa'


def partition(fens, checked):
    historical, previous = set(fens), set(checked)
    if not historical or any(canonical_fen(f) != f for f in historical | previous):
        raise ValueError('Nonempty canonical FEN registry required')
    nonking = set()
    for fen in historical:
        state = parse_fen(fen)
        if not state.kings_of(state.turn):
            nonking.add(fen)
    selected = sorted(nonking - previous)
    return selected, dict(historical_fens=len(historical),
        historical_without_active_king_fens=len(nonking),
        historical_with_active_king_fens=len(historical - nonking),
        previously_checked_historical_nonking_fens=len(nonking & previous),
        remaining_historical_nonking_fens=len(selected))


def verified_json(path, expected):
    raw = Path(path).read_bytes()
    if digest(raw) != expected:
        raise ValueError('Verified evidence digest mismatch: ' + Path(path).name)
    return json.loads(raw)


def authenticated_scope(root, cache, inventory):
    validation = Path(root) / 'research/mtdp/validation'
    view = load_verified_ledger(cache, inventory=inventory,
        manifest=validation / 'conservative-exclusion-manifest-2026-11-26.json',
        supplement=validation / 'conservative-historical-supplement-2026-11-26.jsonl')
    strict = verified_json(validation / 'king-origin-strict-history-summary-2026-11-26.json', STRICT_SUMMARY_SHA256)
    impact = verified_json(validation / 'king-origin-inventory-impact-2026-11-26.json', IMPACT_REPORT_SHA256)
    reconstruction = verified_json(validation / 'king-origin-reconstruction-2026-11-26.json', RECONSTRUCTION_SHA256)
    kings = verified_json(validation / 'king-origin-remaining-active-king-oracle-2026-11-26.json', KING_ORACLE_SHA256)
    if (strict['known_25_source_possible_fen_set_sha256'] != view['union_canonical_fen_set_sha256']
            or strict['matching_legacy_board_sequence_records'] != 4634
            or impact['summary']['corrected_jass_mismatch'] != 0
            or impact['summary']['jass_duplicate_root_keys'] != 0
            or reconstruction['new_reference_mismatches']
            or reconstruction['jass_duplicate_new_root_positions'] != 0
            or not kings['all_known_historical_active_king_roots_match_jass']):
        raise ValueError('Cannot reuse contradictory replay or oracle coverage')
    raw = Path(inventory).read_bytes()
    if digest(raw) != INVENTORY_SHA256:
        raise ValueError('Corrected inventory digest mismatch')
    checked = {json.loads(line)['fen'] for line in raw.splitlines()}
    if len(checked) != 34955:
        raise ValueError('Prior oracle coverage denominator changed')
    fens, counts = partition(view['canonical_fens'], checked)
    if (counts['historical_fens'], counts['historical_without_active_king_fens'],
        counts['previously_checked_historical_nonking_fens'], len(fens)) != (455582, 403572, 18950, 384622):
        raise ValueError('Remaining nonking denominators changed')
    payload = ''.join(f + '\n' for f in fens).encode()
    report = dict(schema='mtdp-h13-remaining-historical-nonking-scope-v1',
        historical_cache_sha256=view['historical_cache_sha256'],
        historical_union_fen_set_sha256=view['union_canonical_fen_set_sha256'],
        strict_history_summary_sha256=STRICT_SUMMARY_SHA256,
        prior_impact_report_sha256=IMPACT_REPORT_SHA256,
        prior_reconstruction_report_sha256=RECONSTRUCTION_SHA256,
        prior_corrected_inventory_sha256=INVENTORY_SHA256,
        completed_active_king_oracle_sha256=KING_ORACLE_SHA256,
        selected_fens_sha256=digest(payload), selected_fens_bytes=len(payload), **counts,
        selection='historical canonical FEN without active-side king minus prior verified oracle FEN',
        new_scores_or_signatures=False, scientific_freeze=False,
        independent_cohort_qualified=False, new_cohorts_reserved=False)
    return report, payload


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(exist_ok=False)
    report, payload = authenticated_scope(a.root, a.cache, a.corrected_inventory)
    (a.output_dir / 'remaining-nonking-scope.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    (a.output_dir / 'remaining-nonking-fens.txt').write_bytes(payload)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
