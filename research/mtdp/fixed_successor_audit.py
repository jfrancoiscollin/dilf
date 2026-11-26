"""Fixed typed-occupancy successor oracle; not path, clock or minimax equivalence."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess

from pedagogy.game import parse_fen, state_to_fen
from research.mtdp.conservative_exclusion_ledger import digest
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.return_capture_oracle import decode_key, root_key, parse_catalogues

PROTOCOL_COMMIT = '3e7bd8960df1969a7418c8c55f4bf409ad2c6682'
FIXTURES_SHA256 = 'f0f6eef86932850612d2aff16c925e53d508422a2bbd690f0d63906bd9e47571'


def load_fixtures(root):
    raw = (Path(root) / 'research/mtdp/validation/fixed-successor-fixtures-2026-11-26.json').read_bytes()
    if digest(raw) != FIXTURES_SHA256:
        raise ValueError('Fixed successor fixtures changed')
    fixtures = json.loads(raw)
    if len(fixtures['cases']) != 20 or len(fixtures['manual_transition_checks']) != 12:
        raise ValueError('Fixed successor denominators changed')
    return fixtures


def parse_successors(raw, fens):
    lines = raw.splitlines()
    if len(lines) != len(fens):
        raise ValueError('Incomplete successor catalogue rows')
    result = []
    for line, fen in zip(lines, fens, strict=True):
        parent, *fields = line.split('\t')
        if canonical_fen(parent) != canonical_fen(fen):
            raise ValueError('Successor catalogue echoed wrong parent')
        row = []
        for field in fields:
            identity, separator, successor = field.partition('>')
            key, equals, promotion = identity.partition('=')
            if not separator or not equals or promotion not in ('0', '1'):
                raise ValueError('Malformed successor catalogue field')
            decode_key(key)
            numbers = list(map(int, re.findall(r'\d+', key)))
            if 'x' in key and numbers[2:] != sorted(set(numbers[2:])):
                raise ValueError('Noncanonical captured squares')
            row.append((key, promotion == '1', canonical_fen(successor)))
        result.append(row)
    return result


def compare_case(case, state, moves, apply_move, reference):
    """Internal synthetic-testable comparison; audit() pins the real engines."""
    ours, theirs = defaultdict(set), defaultdict(set)
    counts = Counter()
    paths = []
    for move in sorted(moves, key=lambda m: (m.path, tuple(sorted(m.captures)), m.promotion)):
        root = root_key(move)
        successor = canonical_fen(state_to_fen(apply_move(state, move)))
        ours[root].add(successor); counts[root] += 1
        paths.append(dict(root=list(root), path=list(move.path), captures=sorted(move.captures),
                          successor_fen=successor))
    for key, promotion, successor in reference:
        theirs[(key, promotion)].add(successor)
    missing = sorted(set(ours) - set(theirs)); extra = sorted(set(theirs) - set(ours))
    mismatches = [dict(root=list(root), python_successors=sorted(ours[root]), jass_successors=sorted(theirs[root]))
        for root in sorted(set(ours) & set(theirs))
        if ours[root] != theirs[root] or len(ours[root]) != 1 or len(theirs[root]) != 1]
    duplicates = len(reference) - len(theirs)
    return dict(case=case, parent_fen=canonical_fen(state_to_fen(state)),
        python_paths=len(paths), python_unique_roots=len(ours), jass_unique_roots=len(theirs),
        jass_duplicate_root_keys=duplicates, python_only_roots=[list(r) for r in missing],
        jass_only_roots=[list(r) for r in extra], shared_root_successor_mismatches=mismatches,
        python_roots_with_multiple_successors=[list(r) for r in sorted(ours) if len(ours[r]) > 1],
        jass_roots_with_multiple_successors=[list(r) for r in sorted(theirs) if len(theirs[r]) > 1],
        multiple_python_paths_same_root=[dict(root=list(r), paths=counts[r], distinct_successors=len(ours[r]))
            for r in sorted(counts) if counts[r] > 1],
        all_roots_and_successors_equal=not (missing or extra or mismatches or duplicates),
        python_path_successors=paths,
        root_successors=[dict(root=list(r), python_successors=sorted(ours[r]), jass_successors=sorted(theirs[r]))
            for r in sorted(set(ours) | set(theirs))])


def check_manual(check, row):
    root = [check['root_key'], check['promotion']]
    matches = [r for r in row['root_successors'] if r['root'] == root]
    expected = canonical_fen(check['successor_fen'])
    passed = (len(matches) == 1 and matches[0]['python_successors'] == [expected]
              and matches[0]['jass_successors'] == [expected])
    return dict(**check, passed=passed, observed=matches)


def project_legal_catalogue(raw):
    return ''.join('\t'.join([line.split('\t')[0]] +
        [field.partition('>')[0] for field in line.split('\t')[1:]]) + '\n'
        for line in raw.splitlines())


def audit(root, adapter, jass, successor_executable, legal_executable):
    root = Path(root)
    fixtures = load_fixtures(root)
    fens = [row['fen'] for row in fixtures['cases']]
    pinned_checkout(Path(jass).resolve(), JASS_COMMIT)
    legacy = checked_engine(Path(adapter).resolve())
    base_source = Path(legacy._rules.__file__).read_bytes()
    engine, receipt = corrected_engine(adapter)
    def run(executable):
        return subprocess.run([str(Path(executable).resolve())], input=''.join(f + '\n' for f in fens),
            capture_output=True, text=True, check=True, timeout=30).stdout
    raw = run(successor_executable)
    legal_raw = run(legal_executable)
    references = parse_successors(raw, fens)
    legal_rows = parse_catalogues(legal_raw, fens)
    rows = [compare_case(fixture['case'], parse_fen(fixture['fen']),
                engine.legal_moves(parse_fen(fixture['fen'])), engine.apply_move, reference)
            for fixture, reference in zip(fixtures['cases'], references, strict=True)]
    by_case = {row['case']: row for row in rows}
    checks = [check_manual(check, by_case[check['case']]) for check in fixtures['manual_transition_checks']]
    projection_equal = project_legal_catalogue(raw) == legal_raw
    source_unchanged = Path(legacy._rules.__file__).read_bytes() == base_source
    if not source_unchanged:
        raise ValueError('Historical default source was mutated')
    report = dict(schema='mtdp-h13-fixed-typed-successor-audit-v1', protocol_commit=PROTOCOL_COMMIT,
        fixtures_sha256=FIXTURES_SHA256, adapter_base_commit=ADAPTER_COMMIT, jass_commit=JASS_COMMIT,
        **receipt, boards=len(rows), total_python_paths=sum(r['python_paths'] for r in rows),
        total_unique_roots=sum(r['python_unique_roots'] for r in rows),
        cases_with_root_or_successor_disagreement=[r['case'] for r in rows if not r['all_roots_and_successors_equal']],
        shared_root_successor_mismatches=sum(len(r['shared_root_successor_mismatches']) for r in rows),
        jass_duplicate_root_keys=sum(r['jass_duplicate_root_keys'] for r in rows),
        manual_transitions_passed=sum(c['passed'] for c in checks), manual_transitions=checks,
        legacy_legal_catalogue_projection_byte_equal=projection_equal,
        legacy_legal_root_counts=[len(r) for r in legal_rows], default_source_bytes_unchanged=source_unchanged,
        raw_successors_bytes=len(raw.encode()), raw_successors_sha256=digest(raw.encode()),
        raw_legal_bytes=len(legal_raw.encode()), raw_legal_sha256=digest(legal_raw.encode()),
        cases=rows, typed_occupancy_and_turn_only=True, clock_or_repetition_state_certified=False,
        played_capture_path_identity_certified=False, global_successor_coverage=False,
        scores_or_signatures_computed=False, independent_cohort_qualified=False,
        scientific_freeze=False, new_cohorts_reserved=False)
    provenance = dict(successor_binary_sha256=digest(Path(successor_executable).read_bytes()),
        legal_binary_sha256=digest(Path(legal_executable).read_bytes()),
        successor_exporter_source_sha256=digest((root / 'research/mtdp/jass_preflight/successor_catalogue.cpp').read_bytes()),
        legal_exporter_source_sha256=digest((root / 'research/mtdp/jass_preflight/legal_catalogue.cpp').read_bytes()),
        position_source_sha256=digest((Path(jass) / 'src/position.cpp').read_bytes()), **receipt)
    return report, provenance, raw, legal_raw


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'adapter', 'jass', 'successor-executable', 'legal-executable', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(exist_ok=False)
    report, provenance, raw, legal = audit(a.root, a.adapter, a.jass, a.successor_executable, a.legal_executable)
    for name, value in [('fixed-successor-audit.json', report), ('provenance.json', provenance)]:
        (a.output_dir / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    (a.output_dir / 'jass-successors.txt').write_text(raw)
    (a.output_dir / 'jass-legal-catalogues.txt').write_text(legal)


if __name__ == '__main__':
    main()
