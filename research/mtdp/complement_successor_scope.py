"""Stream the known historical successor complement from existing legal evidence."""
import argparse
from collections import Counter
import heapq
import json
from pathlib import Path

from research.mtdp.conservative_exclusion_ledger import load_verified_ledger, digest
from research.mtdp.fixed_successor_audit import load_fixtures
from research.mtdp.nonking_oracle import StreamEvidence
from research.mtdp.nonking_oracle_scope import verified_json
from research.mtdp.risk_successor_scope import SOURCES, authenticate_catalogue, categories, FIXED_AUDIT_SHA256
from research.mtdp.return_capture_oracle import parse_catalogues
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.king_origin_inventory_impact import encoded

RISK_SCOPE_SHA256 = '5a53f93124cba011dc69b928403c0574e1f25177700e78d260815055242a4100'
RISK_AUDIT_SHA256 = '150305baaa5874b270cd0788d2f686344851d5d7cb9a394b710c5bbe72688902'


def prior_exclusions(root, risk_fens):
    validation = Path(root) / 'research/mtdp/validation'
    scope = verified_json(validation / 'risk-successor-scope-2026-11-26.json', RISK_SCOPE_SHA256)
    audit = verified_json(validation / 'risk-successor-audit-2026-11-26.json', RISK_AUDIT_SHA256)
    fixed = verified_json(validation / 'fixed-successor-audit-2026-11-26.json', FIXED_AUDIT_SHA256)
    if (not audit['all_selected_roots_and_successors_equal'] or audit['summary']['parents'] != 24558
            or audit['manifest_sha256'] != scope['manifest_sha256']
            or fixed['cases_with_root_or_successor_disagreement'] or fixed['manual_transitions_passed'] != 12):
        raise ValueError('Prior successor proof failed or differs from scope')
    raw = Path(risk_fens).read_bytes()
    if digest(raw) != scope['selected_fens_sha256'] or len(raw) != scope['selected_fens_bytes']:
        raise ValueError('Prior risk parent list changed')
    previous = raw.decode().splitlines()
    fixtures = {row['fen'] for row in load_fixtures(root)['cases']}
    if (len(previous) != 24558 or previous != sorted(set(previous)) or set(previous) & fixtures
            or fixtures != {row['parent_fen'] for row in fixed['cases']}):
        raise ValueError('Prior successor parent identities overlap or changed')
    return set(previous) | fixtures


def catalogue_rows(label, path, expected_rows):
    previous, count = None, 0
    with Path(path).open() as stream:
        for line in stream:
            fen = canonical_fen(line.split('\t')[0].strip())
            if previous is not None and fen <= previous:
                raise ValueError('Catalogue is not strictly ordered by canonical parent')
            previous = fen; count += 1
            roots = parse_catalogues(line, [fen])[0]
            if len(roots) != len(set(roots)):
                raise ValueError('Duplicate cached legal root')
            yield fen, label, roots
    if count != expected_rows:
        raise ValueError('Pinned catalogue row count mismatch')


def derive_rows(rows, historical, excluded, manifest_sink, fens_sink):
    """Streaming helper; callers authenticate source bytes and evidence first."""
    historical, excluded = set(historical), set(excluded)
    known = set(); previous = None; counts = Counter(); inputs = Counter(); selected_sources = Counter()
    for fen, label, roots in rows:
        if previous is not None and fen <= previous:
            raise ValueError('Merged catalogue parents duplicated or unordered')
        previous = fen; inputs[label] += 1; counts['input_distinct_fens'] += 1
        if fen not in historical:
            counts['nonhistorical_fens_excluded'] += 1; continue
        known.add(fen)
        if fen in excluded:
            counts['prior_historical_successor_fens_excluded'] += 1; continue
        if any(categories(root) for root in roots):
            raise ValueError('Risk-tagged parent entered successor complement')
        record = dict(fen=fen, catalogue_id=label, legal_roots=[list(root) for root in sorted(roots)])
        manifest_sink.emit(encoded(record)); fens_sink.emit((fen + '\n').encode())
        counts['selected_fens'] += 1; counts['selected_total_legal_roots'] += len(roots); selected_sources[label] += 1
    if known != historical:
        raise ValueError('Catalogue coverage differs from complete known registry')
    return dict(**dict(sorted(counts.items())), historical_fens_covered=len(known),
        input_rows_by_catalogue=dict(sorted(inputs.items())), selected_fens_by_catalogue=dict(sorted(selected_sources.items())))


def audit(root, cache, inventory, risk_fens, catalogues, output_dir):
    validation = Path(root) / 'research/mtdp/validation'
    view = load_verified_ledger(cache, inventory=inventory,
        manifest=validation / 'conservative-exclusion-manifest-2026-11-26.json',
        supplement=validation / 'conservative-historical-supplement-2026-11-26.jsonl')
    excluded = prior_exclusions(root, risk_fens)
    if set(catalogues) != set(SOURCES):
        raise ValueError('All four cached catalogues required')
    metadata = {label: authenticate_catalogue(root, label, catalogues[label]) for label in SOURCES}
    streams = [catalogue_rows(label, catalogues[label], metadata[label]['rows']) for label in SOURCES]
    with StreamEvidence(Path(output_dir) / 'complement-manifest.jsonl') as manifest, \
         StreamEvidence(Path(output_dir) / 'complement-fens.txt') as fens:
        summary = derive_rows(heapq.merge(*streams, key=lambda row: row[0]), view['canonical_fens'], excluded, manifest, fens)
    if (summary['historical_fens_covered'], summary['prior_historical_successor_fens_excluded'], summary['selected_fens']) != (455582, 24561, 431021):
        raise ValueError('Complement denominators differ from prior handoff')
    return dict(schema='mtdp-h13-historical-successor-complement-scope-v1',
        historical_cache_sha256=view['historical_cache_sha256'],
        historical_union_fen_set_sha256=view['union_canonical_fen_set_sha256'],
        prior_fixed_successor_audit_sha256=FIXED_AUDIT_SHA256,
        prior_risk_scope_sha256=RISK_SCOPE_SHA256, prior_risk_audit_sha256=RISK_AUDIT_SHA256,
        sources=metadata, summary=summary,
        manifest=manifest.metadata(), selected_fens=fens.metadata(),
        all_selected_roots_without_risk_tags=True, streaming_evidence=True,
        new_legal_queries=False, transitions_queried=False, scores_or_signatures_computed=False,
        independent_cohort_qualified=False, scientific_freeze=False, new_cohorts_reserved=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'risk-fens', 'impact-catalogue', 'new-state-catalogue', 'king-catalogue', 'nonking-catalogue', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=False)
    catalogues = dict(impact=a.impact_catalogue, reconstruction=a.new_state_catalogue, active_king=a.king_catalogue, nonking=a.nonking_catalogue)
    report = audit(a.root, a.cache, a.corrected_inventory, a.risk_fens, catalogues, a.output_dir)
    (a.output_dir / 'complement-scope.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
