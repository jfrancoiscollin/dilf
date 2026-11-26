"""Full streamed historical successor complement, never search/scoring."""
import argparse
from collections import Counter
import hashlib
from itertools import islice
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fixed_successor_audit import parse_successors
from research.mtdp.nonking_oracle import StreamEvidence
from research.mtdp.nonking_oracle_scope import verified_json
from research.mtdp.risk_successor_audit import compare_record
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.king_origin_inventory_impact import encoded, BATCH_SIZE

PROTOCOL_COMMIT = '2d8429a0ce65740848f0f6888da2d9ce774e4f12'
SCOPE_SHA256 = '2f12d7dfd9c330edab6bd3a2e17f72744a8f0d53cfab3748a041428da183971e'


def file_metadata(path):
    sha = hashlib.sha256(); count = 0
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1048576), b''):
            sha.update(chunk); count += len(chunk)
    return dict(bytes=count, sha256=sha.hexdigest())


def load_scope(root, manifest, fens):
    scope = verified_json(Path(root) / 'research/mtdp/validation/complement-successor-scope-2026-11-26.json', SCOPE_SHA256)
    if file_metadata(manifest) != scope['manifest'] or file_metadata(fens) != scope['selected_fens']:
        raise ValueError('Frozen complement manifest/list changed')
    if (scope['summary']['selected_fens'], scope['summary']['selected_total_legal_roots']) != (431021, 3576681):
        raise ValueError('Frozen complement denominator changed')
    return scope


def records_stream(path, scope):
    """Recheck actually consumed bytes, ordered FENs and root count at EOF."""
    raw_sha = hashlib.sha256(); fen_sha = hashlib.sha256(); previous = None; count = roots = size = 0
    with Path(path).open('rb') as source:
        for raw in source:
            raw_sha.update(raw); size += len(raw)
            record = json.loads(raw)
            if set(record) != {'fen', 'catalogue_id', 'legal_roots'}:
                raise ValueError('Unexpected complement record fields')
            fen = record['fen']
            if canonical_fen(fen) != fen or (previous is not None and fen <= previous):
                raise ValueError('Complement parents noncanonical, duplicated or unordered')
            previous = fen; count += 1; roots += len(record['legal_roots'])
            fen_sha.update((fen + '\n').encode())
            yield record
    if (dict(bytes=size, sha256=raw_sha.hexdigest()) != scope['manifest']
            or fen_sha.hexdigest() != scope['selected_fens']['sha256']
            or count != scope['summary']['selected_fens']
            or roots != scope['summary']['selected_total_legal_roots']):
        raise ValueError('Consumed complement bytes or counts differ from frozen scope')


def compact_evidence(index, row):
    """Digest complete lists only AFTER full all-path/board comparison."""
    return dict(index=index, fen=row['parent_fen'], catalogue_id=row['catalogue_id'],
        all_roots_and_successors_equal=row['all_roots_and_successors_equal'],
        cached_legal_roots_equal=row['cached_legal_roots_equal'],
        python_paths=row['python_paths'], python_unique_roots=row['python_unique_roots'],
        jass_unique_roots=row['jass_unique_roots'], jass_duplicate_root_keys=row['jass_duplicate_root_keys'],
        multiple_python_path_roots=len(row['multiple_python_paths_same_root']),
        root_successor_lists_sha256=digest(encoded(row['root_successors'])),
        python_path_successor_lists_sha256=digest(encoded(row['python_path_successors'])))


def audit(root, manifest_path, fens_path, adapter, jass, executable, output_dir):
    scope = load_scope(root, manifest_path, fens_path)
    pinned_checkout(Path(jass).resolve(), JASS_COMMIT)
    legacy = checked_engine(Path(adapter).resolve()); default_bytes = Path(legacy._rules.__file__).read_bytes()
    engine, receipt = corrected_engine(adapter)
    if receipt['corrected_rules_sha256'] != '4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d':
        raise ValueError('Corrected rules identity changed')
    output_dir = Path(output_dir)
    # The manifest/list are bound by immutable digests, so do not duplicate their large input files.
    fields = ('parents', 'python_paths', 'unique_roots', 'cases_with_disagreement', 'cached_root_disagreement_cases',
              'shared_root_successor_mismatches', 'jass_duplicate_root_keys', 'python_roots_with_multiple_successors',
              'jass_roots_with_multiple_successors', 'multiple_python_path_roots')
    summary = Counter({key: 0 for key in fields}); by_source = {label: Counter(parents=0, cases_with_disagreement=0) for label in scope['sources']}
    stream = records_stream(manifest_path, scope)
    with StreamEvidence(output_dir / 'successor-ledger.jsonl') as ledger, \
         StreamEvidence(output_dir / 'disagreement-witnesses.jsonl') as witnesses, \
         StreamEvidence(output_dir / 'jass-successors.txt') as raw_sink:
        while chunk := list(islice(stream, BATCH_SIZE)):
            process = subprocess.run([str(Path(executable).resolve())], input=''.join(r['fen'] + '\n' for r in chunk),
                capture_output=True, text=True, check=True, timeout=30)
            raw_sink.emit(process.stdout.encode())
            references = parse_successors(process.stdout, [r['fen'] for r in chunk])
            for record, reference in zip(chunk, references, strict=True):
                index = summary['parents']
                row = compare_record(index, {**record, 'categories': []},
                    engine.legal_moves(parse_fen(record['fen'])), engine.apply_move, reference)
                bad = not row['all_roots_and_successors_equal']
                summary['parents'] += 1; summary['python_paths'] += row['python_paths']; summary['unique_roots'] += row['python_unique_roots']
                summary['cases_with_disagreement'] += bad
                summary['cached_root_disagreement_cases'] += not row['cached_legal_roots_equal']
                summary['shared_root_successor_mismatches'] += len(row['shared_root_successor_mismatches'])
                summary['jass_duplicate_root_keys'] += row['jass_duplicate_root_keys']
                for key in ('python_roots_with_multiple_successors', 'jass_roots_with_multiple_successors'):
                    summary[key] += len(row[key])
                summary['multiple_python_path_roots'] += len(row['multiple_python_paths_same_root'])
                by_source[record['catalogue_id']].update(parents=1, cases_with_disagreement=bad)
                ledger.emit(encoded(compact_evidence(index, row)))
                if bad:
                    witnesses.emit(encoded(row))
            if summary['parents'] % 10000 == 0 or summary['parents'] == 431021:
                print(f'Compared {summary["parents"]}/431021 frozen complement parents', flush=True)
    if Path(legacy._rules.__file__).read_bytes() != default_bytes:
        raise ValueError('Default historical rules source changed')
    if summary['parents'] != 431021:
        raise ValueError('Incomplete complement audit')
    report = dict(schema='mtdp-h13-historical-successor-complement-audit-v1', protocol_commit=PROTOCOL_COMMIT,
        scope_report_sha256=SCOPE_SHA256, input_manifest=scope['manifest'], input_fens=scope['selected_fens'],
        adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT, **receipt,
        summary=dict(sorted(summary.items())), by_catalogue={k: dict(sorted(v.items())) for k, v in sorted(by_source.items())},
        prior_verified_historical_successor_fens=24561, known_historical_fens=455582,
        prior_fixed_audit_sha256=scope['prior_fixed_successor_audit_sha256'], prior_risk_audit_sha256=scope['prior_risk_audit_sha256'],
        all_selected_roots_and_successors_equal=summary['cases_with_disagreement'] == 0,
        known_registry_successor_coverage_complete=summary['cases_with_disagreement'] == 0,
        cached_legal_reference_reused=True, prior_successor_parents_replayed=False,
        output_files=dict(ledger=ledger.metadata(), witnesses=witnesses.metadata(), raw_successors=raw_sink.metadata()),
        compact_ledger_list_hash_contract='sha256 canonical sorted-key JSON plus LF, full lists before hashing',
        all_paths_computed_before_digest=True, typed_occupancy_and_turn_only=True,
        clock_or_repetition_state_certified=False, played_capture_path_identity_certified=False,
        universal_successor_correctness_proven=False, global_historical_registry_complete=False,
        scores_or_signatures_computed=False, independent_cohort_qualified=False,
        scientific_freeze=False, new_cohorts_reserved=False)
    provenance = dict(successor_binary_sha256=digest(Path(executable).read_bytes()),
        successor_exporter_source_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/successor_catalogue.cpp').read_bytes()),
        successor_build_recipe_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/successor-targets.cmake').read_bytes()),
        historical_build_recipe_sha256=digest((Path(root) / 'research/mtdp/jass_preflight/targets.cmake').read_bytes()), **receipt)
    return report, provenance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'manifest', 'fens', 'adapter', 'jass', 'executable', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=False)
    report, provenance = audit(a.root, a.manifest, a.fens, a.adapter, a.jass, a.executable, a.output_dir)
    for name, value in [('complement-successor-audit.json', report), ('provenance.json', provenance)]:
        (a.output_dir / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
