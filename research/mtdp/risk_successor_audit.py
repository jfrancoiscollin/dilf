"""Frozen historical risk-successor audit, streamed and score-blind."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.fixed_successor_audit import compare_case, parse_successors
from research.mtdp.nonking_oracle import StreamEvidence
from research.mtdp.nonking_oracle_scope import verified_json
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.king_origin_inventory_impact import encoded, BATCH_SIZE

PROTOCOL_COMMIT = '609c6d943f54fc0311cdcf7ad1d91cf1e2d75448'
SCOPE_SHA256 = '5a53f93124cba011dc69b928403c0574e1f25177700e78d260815055242a4100'


def load_manifest(root, manifest_path, fens_path):
    scope = verified_json(Path(root) / 'research/mtdp/validation/risk-successor-scope-2026-11-26.json', SCOPE_SHA256)
    manifest, fens = Path(manifest_path).read_bytes(), Path(fens_path).read_bytes()
    if (len(manifest) != scope['manifest_bytes'] or digest(manifest) != scope['manifest_sha256']
            or len(fens) != scope['selected_fens_bytes'] or digest(fens) != scope['selected_fens_sha256']):
        raise ValueError('Frozen risk manifest/list digest mismatch')
    records = [json.loads(line) for line in manifest.splitlines()]
    ordered = [r['fen'] for r in records]
    if (len(records) != 24558 or ordered != sorted(set(ordered))
            or ''.join(f + '\n' for f in ordered).encode() != fens
            or sum(len(r['legal_roots']) for r in records) != 89505):
        raise ValueError('Frozen risk scope structure changed')
    return scope, records, manifest, fens


def compare_record(index, record, moves, apply_move, reference):
    row = compare_case('historical-parent:' + str(index), parse_fen(record['fen']), moves, apply_move, reference)
    cached = {tuple(root) for root in record['legal_roots']}
    actual = {(key, promotion) for key, promotion, _ in reference}
    equal = cached == actual
    row.update(catalogue_id=record['catalogue_id'], risk_categories=record['categories'],
               cached_legal_roots_equal=equal)
    if not equal:
        row['cached_legal_roots'] = record['legal_roots']
    row['all_roots_and_successors_equal'] = row['all_roots_and_successors_equal'] and equal
    return row


def audit(root, manifest_path, fens_path, adapter, jass, executable, output_dir):
    scope, records, manifest, fens = load_manifest(root, manifest_path, fens_path)
    pinned_checkout(Path(jass).resolve(), JASS_COMMIT)
    legacy = checked_engine(Path(adapter).resolve())
    default_bytes = Path(legacy._rules.__file__).read_bytes()
    engine, receipt = corrected_engine(adapter)
    if receipt['corrected_rules_sha256'] != '4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d':
        raise ValueError('Corrected rules identity changed')
    output_dir = Path(output_dir)
    for name, raw in [('risk-successor-manifest.jsonl', manifest), ('risk-successor-fens.txt', fens)]:
        with (output_dir / name).open('xb') as out:
            out.write(raw)
    summary = Counter({k: 0 for k in ('parents', 'python_paths', 'unique_roots', 'cases_with_disagreement',
        'cached_root_disagreement_cases', 'shared_root_successor_mismatches', 'jass_duplicate_root_keys',
        'python_roots_with_multiple_successors', 'jass_roots_with_multiple_successors', 'multiple_python_path_roots')})
    categories = {tag: Counter(parents=0, cases_with_disagreement=0, python_paths=0, unique_roots=0)
                  for tag in scope['summary']['selected_fens_by_category']}
    with StreamEvidence(output_dir / 'successor-ledger.jsonl') as ledger, \
         StreamEvidence(output_dir / 'disagreement-witnesses.jsonl') as witnesses, \
         StreamEvidence(output_dir / 'jass-successors.txt') as raw_sink:
        for start in range(0, len(records), BATCH_SIZE):
            chunk = records[start:start + BATCH_SIZE]
            process = subprocess.run([str(Path(executable).resolve())], input=''.join(r['fen'] + '\n' for r in chunk),
                capture_output=True, text=True, check=True, timeout=30)
            raw_sink.emit(process.stdout.encode())
            references = parse_successors(process.stdout, [r['fen'] for r in chunk])
            for index, (record, reference) in enumerate(zip(chunk, references, strict=True), start):
                row = compare_record(index, record, engine.legal_moves(parse_fen(record['fen'])), engine.apply_move, reference)
                bad = not row['all_roots_and_successors_equal']
                summary['parents'] += 1; summary['python_paths'] += row['python_paths']
                summary['unique_roots'] += row['python_unique_roots']; summary['cases_with_disagreement'] += bad
                summary['cached_root_disagreement_cases'] += not row['cached_legal_roots_equal']
                summary['shared_root_successor_mismatches'] += len(row['shared_root_successor_mismatches'])
                summary['jass_duplicate_root_keys'] += row['jass_duplicate_root_keys']
                for key in ('python_roots_with_multiple_successors', 'jass_roots_with_multiple_successors'):
                    summary[key] += len(row[key])
                summary['multiple_python_path_roots'] += len(row['multiple_python_paths_same_root'])
                for tag in record['categories']:
                    categories[tag].update(parents=1, cases_with_disagreement=bad,
                        python_paths=row['python_paths'], unique_roots=row['python_unique_roots'])
                ledger.emit(encoded(row))
                if bad:
                    witnesses.emit(encoded(row))
            print(f'Compared {start + len(chunk)}/{len(records)} frozen risk-successor parents', flush=True)
    if Path(legacy._rules.__file__).read_bytes() != default_bytes:
        raise ValueError('Default historical source changed')
    report = dict(schema='mtdp-h13-historical-risk-successor-audit-v1', protocol_commit=PROTOCOL_COMMIT,
        scope_report_sha256=SCOPE_SHA256, manifest_sha256=scope['manifest_sha256'],
        selected_fens_sha256=scope['selected_fens_sha256'], adapter_base_commit=ADAPTER_COMMIT,
        jass_commit=JASS_COMMIT, **receipt, summary=dict(sorted(summary.items())),
        by_category={tag: dict(sorted(values.items())) for tag, values in sorted(categories.items())},
        category_counts_overlap=True, prior_successor_audit_sha256=scope['prior_successor_audit_sha256'],
        cached_legal_reference_reused=True, prior_fixed_successor_parents_replayed=False,
        all_selected_roots_and_successors_equal=summary['cases_with_disagreement'] == 0,
        output_files=dict(ledger=ledger.metadata(), witnesses=witnesses.metadata(), raw_successors=raw_sink.metadata()),
        typed_occupancy_and_turn_only=True, clock_or_repetition_state_certified=False,
        played_capture_path_identity_certified=False, global_successor_coverage=False,
        scores_or_signatures_computed=False, historical_cache_changed=False,
        independent_cohort_qualified=False, scientific_freeze=False, new_cohorts_reserved=False)
    provenance = dict(successor_binary_sha256=digest(Path(executable).read_bytes()),
        successor_exporter_source_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/successor_catalogue.cpp').read_bytes()),
        successor_build_recipe_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/successor-targets.cmake').read_bytes()),
        historical_build_recipe_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/targets.cmake').read_bytes()), **receipt)
    return report, provenance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'manifest', 'fens', 'adapter', 'jass', 'executable', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(exist_ok=False)
    report, provenance = audit(a.root, a.manifest, a.fens, a.adapter, a.jass, a.executable, a.output_dir)
    for name, value in [('risk-successor-audit.json', report), ('provenance.json', provenance)]:
        (a.output_dir / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
