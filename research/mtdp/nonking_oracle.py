"""Frozen nonking legal oracle, streaming evidence without scores or search."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.nonking_oracle_scope import authenticated_scope
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.king_origin_inventory_impact import compare_actions, encoded, METRICS, BATCH_SIZE
from research.mtdp.return_capture_oracle import parse_catalogues

PROTOCOL_COMMIT = '065d39d5c3d3cb6907772a423bffb03596b805a7'
SCOPE_SHA256 = '0dc8ad714e029d19c6e342aa45e26d3d14158e726d5f9fd4ab74098af01cfb79'


class StreamEvidence:
    """Exclusive output and incremental hash; never accumulates the full ledger."""
    def __init__(self, path):
        self.file = Path(path).open('xb')
        self.count = 0
        self.hash = hashlib.sha256()

    def emit(self, raw):
        written = self.file.write(raw)
        if written != len(raw):
            raise OSError('Incomplete evidence write')
        self.hash.update(raw)
        self.count += written

    def metadata(self):
        return dict(bytes=self.count, sha256=self.hash.hexdigest())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.file.close()


def frozen_scope(root, cache, inventory):
    raw = (Path(root) / 'research/mtdp/validation/nonking-oracle-scope-2026-11-26.json').read_bytes()
    if digest(raw) != SCOPE_SHA256:
        raise ValueError('Frozen nonking scope changed')
    expected = json.loads(raw)
    actual, payload = authenticated_scope(root, cache, inventory)
    if (actual != expected or len(payload.splitlines()) != 384622
            or len(payload) != expected['selected_fens_bytes']
            or digest(payload) != expected['selected_fens_sha256']):
        raise ValueError('Nonking scope differs from preregistration')
    return expected, payload


def compare_batches(fens, legacy, fixed, catalogue_batch, output_dir, *, batch_size=BATCH_SIZE):
    """Internal computation helper; only audit() authenticates inputs and engines."""
    summary = Counter({key: 0 for key in (*METRICS, 'positions', 'path_only_changes', 'added_roots', 'removed_roots')})
    output_dir = Path(output_dir)
    with StreamEvidence(output_dir / 'position-ledger.jsonl') as ledger, \
         StreamEvidence(output_dir / 'change-witnesses.jsonl') as witnesses, \
         StreamEvidence(output_dir / 'jass-catalogues.txt') as raw:
        for start in range(0, len(fens), batch_size):
            chunk = fens[start:start + batch_size]
            catalogues, catalogue_bytes = catalogue_batch(chunk)
            raw.emit(catalogue_bytes)
            for index, (fen, catalogue) in enumerate(zip(chunk, catalogues, strict=True), start):
                state = parse_fen(fen)
                if state.kings_of(state.turn):
                    raise ValueError('Active king entered nonking scope')
                metrics, witness = compare_actions(legacy.legal_moves(state), fixed.legal_moves(state), catalogue)
                summary['positions'] += 1
                for key in METRICS:
                    summary[key] += metrics[key]
                summary['path_only_changes'] += metrics['path_sets_changed'] and not metrics['root_sets_changed']
                summary['added_roots'] += metrics['added_root_count']
                summary['removed_roots'] += metrics['removed_root_count']
                ledger.emit(encoded(dict(index=index, fen_sha256=digest(fen.encode()), **metrics)))
                if metrics['path_sets_changed'] or metrics['legacy_jass_mismatch'] or metrics['corrected_jass_mismatch']:
                    witnesses.emit(encoded(dict(fen=fen, **metrics, **witness)))
            if (start + len(chunk)) % 10000 == 0 or start + len(chunk) == len(fens):
                print(f'Compared {start + len(chunk)}/{len(fens)} frozen nonking positions', flush=True)
    return dict(sorted(summary.items())), dict(position_ledger=ledger.metadata(),
        witnesses=witnesses.metadata(), raw_catalogue=raw.metadata())


def audit(root, cache, inventory, adapter, jass, executable, output_dir):
    scope, payload = frozen_scope(root, cache, inventory)
    pinned_checkout(Path(jass).resolve(), JASS_COMMIT)
    legacy = checked_engine(Path(adapter).resolve())
    fixed, receipt = corrected_engine(adapter)
    if receipt['corrected_rules_sha256'] != '4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d':
        raise ValueError('Corrected research rules identity changed')
    with (Path(output_dir) / 'remaining-nonking-fens.txt').open('xb') as out:
        out.write(payload)
    def catalogue_batch(chunk):
        process = subprocess.run([str(Path(executable).resolve())], input=''.join(f + '\n' for f in chunk),
            capture_output=True, text=True, check=True, timeout=30)
        return parse_catalogues(process.stdout, chunk), process.stdout.encode()
    summary, files = compare_batches(payload.decode().splitlines(), legacy, fixed, catalogue_batch, output_dir)
    report = dict(schema='mtdp-h13-remaining-historical-nonking-oracle-v1',
        protocol_commit=PROTOCOL_COMMIT, frozen_scope_sha256=SCOPE_SHA256,
        selected_fens_sha256=scope['selected_fens_sha256'], selected_fens_bytes=len(payload),
        adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT, **receipt,
        jass_batch_size=BATCH_SIZE, summary=summary,
        historical_fens=455582, previously_verified_historical_active_king_fens=52010,
        previously_verified_historical_nonking_fens=18950,
        completed_active_king_oracle_sha256=scope['completed_active_king_oracle_sha256'],
        prior_coverage_replayed=False, streaming_evidence=True,
        all_known_historical_corrected_roots_match_jass=(summary['corrected_jass_mismatch'] == 0 and summary['jass_duplicate_root_keys'] == 0),
        output_files=files, default_rules_or_cache_changed=False,
        engine_scores_computed=False, signatures_computed=False,
        played_capture_paths_certified=False, independent_cohort_qualified=False,
        global_historical_registry_complete=False, scientific_freeze=False, new_cohorts_reserved=False)
    provenance = dict(catalogue_binary_sha256=digest(Path(executable).read_bytes()),
        adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT, **receipt)
    return report, provenance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'corrected-inventory', 'adapter', 'jass', 'executable', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(exist_ok=False)
    report, provenance = audit(a.root, a.cache, a.corrected_inventory, a.adapter, a.jass, a.executable, a.output_dir)
    for name, value in [('nonking-oracle.json', report), ('provenance.json', provenance)]:
        (a.output_dir / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
