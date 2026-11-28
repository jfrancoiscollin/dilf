"""Score-blind fixed scope for remaining historical active-king legality checks."""
import argparse
import json
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import (
    load_verified_ledger, INVENTORY_SHA256, RECONSTRUCTION_SHA256, digest)
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen

STRICT_SUMMARY_SHA256 = '6a4262d763603f09ac760cbdbe586f0b24507f97f9e99c975d2bdef49f627f48'
IMPACT_REPORT_SHA256 = '13061b5c12e387f5f3f359d421c73d5a9c921eada7e02b6187efd10a62aea943'


def partition(fens, previously_checked):
    """Exact typed turn selects the king owner; no move or score is queried."""
    historical = set(fens)
    checked = set(previously_checked)
    if not historical or any(canonical_fen(f) != f for f in historical | checked):
        raise ValueError('Nonempty canonical FEN sets required')
    kings = set()
    for fen in historical:
        state = parse_fen(fen)
        if state.kings_of(state.turn):
            kings.add(fen)
    selected = sorted(kings - checked)
    return selected, dict(historical_fens=len(historical), historical_active_king_fens=len(kings),
        historical_without_active_king_fens=len(historical - kings),
        previously_checked_historical_fens=len(historical & checked),
        previously_checked_historical_active_king_fens=len(kings & checked),
        remaining_historical_active_king_fens=len(selected))


def authenticated_scope(root, cache_path, corrected_inventory):
    root = Path(root)
    validation = root / 'research/mtdp/validation'
    view = load_verified_ledger(cache_path, inventory=corrected_inventory,
        manifest=validation / 'conservative-exclusion-manifest-2026-11-26.json',
        supplement=validation / 'conservative-historical-supplement-2026-11-26.jsonl')
    raw = (validation / 'king-origin-strict-history-summary-2026-11-26.json').read_bytes()
    if digest(raw) != STRICT_SUMMARY_SHA256:
        raise ValueError('Verified strict history summary changed')
    strict = json.loads(raw)
    if (strict['known_25_source_possible_fen_set_sha256'] != view['union_canonical_fen_set_sha256']
            or strict['matching_legacy_board_sequence_records'] != 4634
            or strict['new_possible_fens_outside_existing_ledger'] != 0):
        raise ValueError('History replay and exclusion registry disagree')
    raw = (validation / 'king-origin-inventory-impact-2026-11-26.json').read_bytes()
    if digest(raw) != IMPACT_REPORT_SHA256:
        raise ValueError('Verified prior legal impact report changed')
    impact = json.loads(raw)
    raw = (validation / 'king-origin-reconstruction-2026-11-26.json').read_bytes()
    if digest(raw) != RECONSTRUCTION_SHA256:
        raise ValueError('Verified reconstruction report changed')
    reconstruction = json.loads(raw)
    if (impact['summary']['corrected_jass_mismatch'] != 0
            or impact['summary']['jass_duplicate_root_keys'] != 0
            or reconstruction['new_reference_mismatches']
            or reconstruction['jass_duplicate_new_root_positions'] != 0):
        raise ValueError('Cannot reuse mismatching prior oracle coverage')
    raw = Path(corrected_inventory).read_bytes()
    if digest(raw) != INVENTORY_SHA256:
        raise ValueError('Corrected inventory digest mismatch')
    checked = {json.loads(line)['fen'] for line in raw.splitlines()}
    if len(checked) != 34955:
        raise ValueError('Prior oracle coverage denominator changed')
    selected, counts = partition(view['canonical_fens'], checked)
    payload = ''.join(fen + '\n' for fen in selected).encode()
    report = dict(schema='mtdp-h13-remaining-historical-active-king-scope-v1',
        historical_cache_sha256=view['historical_cache_sha256'],
        historical_union_fen_set_sha256=view['union_canonical_fen_set_sha256'],
        strict_history_summary_sha256=STRICT_SUMMARY_SHA256,
        prior_impact_report_sha256=IMPACT_REPORT_SHA256,
        prior_reconstruction_report_sha256=RECONSTRUCTION_SHA256,
        prior_corrected_inventory_sha256=INVENTORY_SHA256,
        previously_jass_checked_union_fens=34955,
        selected_fens_sha256=digest(payload), selected_fens_bytes=len(payload),
        selection='historical canonical FEN with active-side king minus prior verified oracle FEN',
        **counts, scope_only=True, new_scores_or_signatures=False,
        new_cohorts_reserved=False, scientific_freeze=False, independent_cohort_qualified=False)
    return report, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(exist_ok=False)
    report, payload = authenticated_scope(args.root, args.cache, args.corrected_inventory)
    (args.output_dir / 'remaining-active-king-scope.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    (args.output_dir / 'remaining-active-king-fens.txt').write_bytes(payload)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
