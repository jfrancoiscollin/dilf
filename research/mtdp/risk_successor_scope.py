"""Score-blind historical successor risk scope from authenticated existing catalogues."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from research.mtdp.conservative_exclusion_ledger import load_verified_ledger, digest
from research.mtdp.fixed_successor_audit import load_fixtures
from research.mtdp.nonking_oracle_scope import verified_json
from research.mtdp.return_capture_oracle import decode_key, parse_catalogues
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.king_origin_inventory_impact import encoded

FIXED_AUDIT_SHA256 = '1dbcf3b40f3f353a831243fa4d67e73c2ae491024b5663635eeb8de918b59f1d'
SOURCES = {
    'impact': ('king-origin-inventory-impact-2026-11-26.json', '13061b5c12e387f5f3f359d421c73d5a9c921eada7e02b6187efd10a62aea943', 34172),
    'reconstruction': ('king-origin-reconstruction-2026-11-26.json', 'c774e71d1bd29aec50e63a285fb1755dcd558393f8eaa7ef89af5be7802584bc', 783),
    'active_king': ('king-origin-remaining-active-king-oracle-2026-11-26.json', '95adab875fcc7b3fa260d9ec61d6222d2ab82eb1618e0fd20ceccf61dde80caa', 48654),
    'nonking': ('nonking-oracle-2026-11-26.json', 'f4a0bc13d397fcc78b2605217ae02b6d66fe602286eba9fc02f7fa92f329acad', 384622),
}


def categories(root):
    key, promotion = root
    if type(promotion) is not bool:
        raise ValueError('Promotion must be a boolean')
    decode_key(key)
    numbers = list(map(int, re.findall(r'\d+', key)))
    captured = numbers[2:] if 'x' in key else []
    if captured != sorted(set(captured)):
        raise ValueError('Noncanonical capture mask')
    tags = []
    if captured and numbers[0] == numbers[1]:
        tags.append('return_origin')
    if promotion:
        tags.append('promotion')
    if len(captured) >= 2:
        tags.append('multiple_capture')
    return sorted(tags)


def select_rows(rows, historical, excluded):
    """Internal derivation helper; real inputs must pass authenticated_scope()."""
    historical, excluded = set(historical), set(excluded)
    seen, known, before, removed = set(), set(), set(), set()
    selected = {}; input_counts = Counter(); fen_tags = Counter(); root_tags = Counter()
    for catalogue_id, fen, roots in rows:
        if canonical_fen(fen) != fen or fen in seen:
            raise ValueError('Noncanonical or duplicate catalogue parent')
        if len(set(roots)) != len(roots):
            raise ValueError('Duplicate legal root in authenticated source')
        seen.add(fen); input_counts[catalogue_id] += 1
        if fen not in historical:
            continue
        known.add(fen)
        risks = [dict(root=list(root), categories=tags) for root in sorted(roots) if (tags := categories(root))]
        if not risks:
            continue
        before.add(fen)
        if fen in excluded:
            removed.add(fen); continue
        tags = sorted({tag for risk in risks for tag in risk['categories']})
        fen_tags.update(tags)
        for risk in risks:
            root_tags.update(risk['categories'])
        selected[fen] = dict(fen=fen, catalogue_id=catalogue_id, categories=tags,
                             legal_roots=[list(root) for root in sorted(roots)], risk_roots=risks)
    if known != historical:
        raise ValueError('Existing catalogue coverage does not equal historical registry')
    summary = dict(input_rows_by_catalogue=dict(sorted(input_counts.items())), input_distinct_fens=len(seen),
        historical_fens_covered=len(known), nonhistorical_fens_excluded=len(seen - historical),
        historical_risk_fens_before_prior_exclusion=len(before), prior_risk_fixture_fens_excluded=len(removed),
        prior_fixture_fens_in_history=len(historical & excluded), selected_fens=len(selected),
        selected_total_legal_roots=sum(len(r['legal_roots']) for r in selected.values()),
        selected_risk_roots=sum(len(r['risk_roots']) for r in selected.values()),
        selected_fens_by_category=dict(sorted(fen_tags.items())), selected_roots_by_category=dict(sorted(root_tags.items())))
    return [selected[fen] for fen in sorted(selected)], summary


def authenticate_catalogue(root, label, path):
    name, report_sha, expected_rows = SOURCES[label]
    report = verified_json(Path(root) / 'research/mtdp/validation' / name, report_sha)
    if label == 'reconstruction':
        metadata = dict(sha256=report['raw_new_catalogues_sha256'], bytes=report['raw_new_catalogues_bytes'])
        if report['new_reference_mismatches'] or report['jass_duplicate_new_root_positions']:
            raise ValueError('Cannot reuse mismatching reconstruction oracle')
    elif label == 'nonking':
        metadata = report['output_files']['raw_catalogue']
        if not report['all_known_historical_corrected_roots_match_jass']:
            raise ValueError('Cannot reuse mismatching historical oracle')
    else:
        metadata = dict(sha256=report['raw_catalogue_sha256'], bytes=report['raw_catalogue_bytes'])
        if report['summary']['corrected_jass_mismatch'] or report['summary']['jass_duplicate_root_keys']:
            raise ValueError('Cannot reuse mismatching prior legal oracle')
    raw = Path(path).read_bytes()
    if len(raw) != metadata['bytes'] or digest(raw) != metadata['sha256']:
        raise ValueError('Pinned catalogue digest/size mismatch: ' + label)
    return dict(report_sha256=report_sha, catalogue_sha256=metadata['sha256'], catalogue_bytes=len(raw), rows=expected_rows)


def authenticated_scope(root, cache, inventory, catalogues):
    validation = Path(root) / 'research/mtdp/validation'
    view = load_verified_ledger(cache, inventory=inventory,
        manifest=validation / 'conservative-exclusion-manifest-2026-11-26.json',
        supplement=validation / 'conservative-historical-supplement-2026-11-26.jsonl')
    fixtures = load_fixtures(root)
    audit = verified_json(validation / 'fixed-successor-audit-2026-11-26.json', FIXED_AUDIT_SHA256)
    if (audit['cases_with_root_or_successor_disagreement'] or audit['manual_transitions_passed'] != 12
            or audit['jass_duplicate_root_keys'] != 0):
        raise ValueError('Prior successor fixtures did not pass')
    excluded = {row['fen'] for row in fixtures['cases']}
    if excluded != {row['parent_fen'] for row in audit['cases']}:
        raise ValueError('Prior successor coverage differs from fixed fixtures')
    if set(catalogues) != set(SOURCES):
        raise ValueError('All four pinned catalogues required')
    metadata = {label: authenticate_catalogue(root, label, catalogues[label]) for label in SOURCES}
    def rows():
        for label in SOURCES:
            count = 0
            with Path(catalogues[label]).open() as stream:
                for line in stream:
                    parent = canonical_fen(line.split('\t')[0].strip())
                    roots = parse_catalogues(line, [parent])[0]
                    count += 1
                    yield label, parent, roots
            if count != metadata[label]['rows']:
                raise ValueError('Pinned catalogue row count mismatch')
    selected, summary = select_rows(rows(), view['canonical_fens'], excluded)
    manifest = b''.join(encoded(row) for row in selected)
    fens = ''.join(row['fen'] + '\n' for row in selected).encode()
    report = dict(schema='mtdp-h13-historical-risk-successor-scope-v1',
        historical_cache_sha256=view['historical_cache_sha256'],
        historical_union_fen_set_sha256=view['union_canonical_fen_set_sha256'],
        prior_successor_audit_sha256=FIXED_AUDIT_SHA256, sources=metadata, summary=summary,
        manifest_bytes=len(manifest), manifest_sha256=digest(manifest),
        selected_fens_bytes=len(fens), selected_fens_sha256=digest(fens),
        selection='historical root returns to origin, promotes a man, or captures at least two pieces; exclude prior successor parents',
        category_counts_overlap=True, new_legal_queries=False, transitions_queried=False,
        scores_or_signatures_computed=False, independent_cohort_qualified=False,
        scientific_freeze=False, new_cohorts_reserved=False)
    return report, manifest, fens


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'impact-catalogue', 'new-state-catalogue', 'king-catalogue', 'nonking-catalogue', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(exist_ok=False)
    catalogues = dict(impact=a.impact_catalogue, reconstruction=a.new_state_catalogue, active_king=a.king_catalogue, nonking=a.nonking_catalogue)
    report, manifest, fens = authenticated_scope(a.root, a.cache, a.corrected_inventory, catalogues)
    (a.output_dir / 'risk-successor-scope.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    (a.output_dir / 'risk-successor-manifest.jsonl').write_bytes(manifest)
    (a.output_dir / 'risk-successor-fens.txt').write_bytes(fens)
    print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
