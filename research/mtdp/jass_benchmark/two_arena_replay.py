"""Joint score-blind proposal for the two registered arenas; never a scoring gate.

The registered order, original PC Blues selector and whole-game quarantine are
unchanged. No new source is selected if mapping or validation fails.
"""
import argparse
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from pedagogy.game import parse_fen
from research.mtdp.best_move_audit import load_positions
from research.mtdp.successor_audit import _quiet_signature
from research.mtdp.pdn import read_games
from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark import two_arena_acquisition as acquisition
from research.mtdp.jass_benchmark.named_arena_replay import (
    checked_engine, replay_candidates, index_games, token_fingerprint, benchmark_manifest,
)
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import (
    BASELINE, digest, public_ids, select_population,
)

EXCLUSIONS_SHA = '8dac5c60e1eaa10ff8e3e27f5c1fb0d0307edaeaec438e7c9bdc33b3e666dc32'
SUMMARY = study.PREFIX + 'two-named-arenas-20261118-exclusions-summary.json'
MODULE = 'research/mtdp/jass_benchmark/two_arena_replay.py'
RUNTIME_RECEIPT = study.PREFIX + 'P1RUlfJc-runner-builds.json'
CATALOGUE_SHA = 'c4065367a315534284a3b9937b97fe51e2e2b011a26b2889ada435c0845aecfd'
DEPENDENCIES = (
    MODULE, study.MODULE, 'research/mtdp/jass_benchmark/two_arena_acquisition.py',
    'research/mtdp/jass_benchmark/two_arena_exclusions.py',
    'research/mtdp/jass_benchmark/named_arena_replay.py',
    'research/mtdp/jass_benchmark/named_arena_inputs.py',
    'research/mtdp/jass_benchmark/named_arena_acquisition.py',
    'research/mtdp/jass_benchmark/named_freeze_bundle.py', 'research/mtdp/jass_cohort.py',
    'research/mtdp/jass_benchmark/prospective_candidate_replay.py',
    'research/mtdp/jass_benchmark/geometry_ablation.py',
    'research/mtdp/jass_benchmark/candidate_jass_catalogue.py',
    'research/mtdp/jass_move_mapping.py', 'research/mtdp/draught_master_adapter.py',
    'research/mtdp/pdn.py', 'research/mtdp/successor_audit.py',
    'research/mtdp/signature_ablation.py',
    'research/mtdp/best_move_audit.py', 'pedagogy/game.py',
    'research/mtdp/jass_preflight/legal_catalogue.cpp',
    'research/mtdp/jass_preflight/move_key.hpp', RUNTIME_RECEIPT,
)


def checked_exclusions(root, path):
    raw = path.read_bytes()
    summary = json.loads((root / SUMMARY).read_bytes())
    if digest(raw) != EXCLUSIONS_SHA or summary['exclusions_sha256'] != EXCLUSIONS_SHA:
        raise ValueError('Whole historical exclusion cache differs from the registered preparation')
    return json.loads(raw)


def full_signature_labels(targets):
    """Freeze both strata for the already selected sources, before any scores."""
    result = []
    for target in targets:
        signature = _quiet_signature(parse_fen(target['target_fen']))
        if signature is None:
            raise ValueError('Selected quiet target has undefined full signature')
        equal = {}
        for arm in ('L', 'LCB'):
            source = _quiet_signature(parse_fen(target['source_fens'][arm]))
            if source is None:
                raise ValueError('Selected source has undefined full signature')
            equal[arm] = source == signature
        result.append({**target, 'same_full_quiet_signature': equal,
                       'bootstrap_owner': min(target['target_games'])})
    return result


def extend_exclusions(previous, pdn, engine):
    """Every earlier game, including rejected games and legal quarantine prefixes.

    Complete fingerprints are added only by the canonical historical indexer.
    The input cache is not mutated; token/public-ID aliases include all games.
    """
    games = read_games(pdn)
    extension = index_games([(pdn, len(games))], engine)
    value = {key: sorted(set(previous[key]) | set(extra)) for key, extra in (
        ('public_game_ids', public_ids(pdn) if games else []),
        ('normalized_token_sequence_sha256', [token_fingerprint(g) for g in games]),
        ('fingerprints', extension['fingerprints']),
        ('confirmed_fens', extension['confirmed_fens']),
    )}
    return value, extension


def joint_population(paths, exclusions, source_states, source_plies, engine, executable):
    if tuple(paths) != study.EVENTS:
        raise ValueError('Exact registered arena order required')
    known = exclusions
    events = {}
    for event in study.EVENTS:
        path = paths[event]
        if path.name != f'mtdp-lidraughts-{event}.pdn':
            raise ValueError('Canonical event filename required for unique game ownership')
        states, owners, plies, audit = replay_candidates(path, engine, known, set(known['fingerprints']))
        rows, categories, novel = select_population(
            source_states, source_plies, states, owners, set(known['confirmed_fens']), engine,
        )
        targets, catalogue = benchmark_manifest(rows, engine, executable)
        targets = full_signature_labels(targets)
        known, extension = extend_exclusions(known, path, engine)
        events[event] = {
            'pdn_sha256': digest(path.read_bytes()),
            'game_status_counts': dict(sorted(Counter(r['status'] for r in audit.values()).items())),
            'game_audit': audit, 'novel_positions': len(novel),
            'position_categories': dict(sorted(categories.items())),
            'candidate_targets': rows, 'benchmark_targets': targets,
            'jass_catalogue': catalogue,
            'target_plies': {r['fen']: plies[r['fen']] for r in rows},
            'full_signature_strata': {arm: {
                'equal': sum(t['same_full_quiet_signature'][arm] for t in targets),
                'different': sum(not t['same_full_quiet_signature'][arm] for t in targets),
            } for arm in ('L', 'LCB')},
            'whole_event_index': extension,
            'cumulative_exclusions': {key: len(known[key]) for key in (
                'public_game_ids', 'normalized_token_sequence_sha256', 'fingerprints', 'confirmed_fens')},
        }
    a, b = [events[e]['benchmark_targets'] for e in study.EVENTS]
    if {r['target_fen'] for r in a} & {r['target_fen'] for r in b}:
        raise ValueError('Later arena retained an earlier confirmed target FEN')
    return events


def proposal(root, directory, exclusions, adapter, executable):
    inputs = acquisition.check(root, directory)  # real clock, before backend or any target replay
    registered = study.load(root)
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(root), 'diff', 'HEAD']):
        raise ValueError('Commit the proposal implementation before replaying targets')
    for name in DEPENDENCIES:
        if subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{name}']) != (root/name).read_bytes():
            raise ValueError('Proposal implementation is not committed')
    known = checked_exclusions(root, exclusions)
    if digest(executable.read_bytes()) != CATALOGUE_SHA:
        raise ValueError('Use the byte-pinned archived legal catalogue (no search)')
    engine = checked_engine(adapter)
    baseline = root / BASELINE
    expected = next(r for r in known['sources'] if r['file'] == baseline.name)
    if digest(baseline.read_bytes()) != expected['sha256']:
        raise ValueError('PC Blues baseline changed')
    source_plies = {}
    sources, _, records = load_positions([baseline], engine, set(), plies_by_game=source_plies)
    record, = records
    if record['accepted'] != 26 or record['rejected'] or record['duplicates']:
        raise ValueError('PC Blues baseline no longer reproduces')
    synthetic = False
    with tempfile.TemporaryDirectory(prefix='mtdp-two-arena-replay-') as temp:
        paths = {}
        for event in study.EVENTS:
            raw = (directory/event/'first.pdn').read_bytes()
            # Preserve raw bytes and canonical owners despite acquisition files sharing a name.
            path = Path(temp)/f'mtdp-lidraughts-{event}.pdn'
            path.write_bytes(raw); paths[event] = path
            synthetic |= any('Synthetic' in g.tags for g in read_games(path))
        events = joint_population(paths, known, sources, source_plies, engine, executable)
    return {'schema': 'mtdp-two-arena-joint-proposal-v1', 'study_id': registered['study_id'],
            'event_order': list(study.EVENTS), 'scientific_freeze': False,
            'synthetic_rehearsal': synthetic, 'input_check': inputs,
            'registration_sha256': study.REGISTRATION_SHA, 'protocol_sha256': study.PROTOCOL_SHA,
            'exclusions_sha256': EXCLUSIONS_SHA, 'implementation_commit': commit,
            'implementation_sha256': {name: digest((root/name).read_bytes()) for name in DEPENDENCIES},
            'engines': {**registered['engines'], 'jass_catalogue_sha256': CATALOGUE_SHA},
            'analysis': registered['analysis'], 'events': events,
            'next_gate': 'independent_processes_7_61_then_joint_published_freeze_verification_before_any_scores',
            'scope': 'proposal_only_no_source_or_target_scores_no_Jass_search_no_scoring_authorization'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'directory', 'exclusions', 'adapter', 'executable', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    a = parser.parse_args()
    result = proposal(a.root, a.directory, a.exclusions, a.adapter, a.executable)
    with a.output.open('xb') as stream:
        stream.write(_bytes(result))
    print(json.dumps({'scientific_freeze': False, 'synthetic_rehearsal': result['synthetic_rehearsal'],
                      'targets': {e:len(result['events'][e]['benchmark_targets']) for e in study.EVENTS}}, sort_keys=True))


if __name__ == '__main__':
    main()
