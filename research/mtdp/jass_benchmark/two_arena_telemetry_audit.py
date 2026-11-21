"""Offline audit of all frozen Jass node receipts, with no target scores or search."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

from research.mtdp.jass_benchmark import two_arena_execution as runtime

BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
PREFIX = BASE + 'two-named-arenas-decisions/'
FREEZE = '3fa9a56a3fa60954d5391d7e1b302c07e04f1f04'
DECISIONS = '03b1a270b12244a03df715f265f597bd0f00cd50'
MANIFEST_SHA = 'c079ca061d3645b42ce93235854e032de2be43a4cb08d8cea5ddbc1d92f1b5aa'
BUDGETS = (10000, 50000, 200000)


def pinned(root, commit, path, sha=None):
    raw = (root / path).read_bytes()
    if raw != runtime._blob(root, commit, path) or (sha is not None and runtime.digest(raw) != sha):
        raise ValueError(f'Frozen receipt bytes changed: {path}')
    return json.loads(raw), runtime.digest(raw)


def audit_row(row, target, budget, prefix, path, owner):
    if not runtime.check_receipt(row, target, budget, prefix):
        raise ValueError('This frozen complete campaign has an unexpected ceiling')
    calls = row['verification_receipts']
    if not calls or calls[0]['phase'] != 'preliminary' or any(c['phase'] != 'probe' for c in calls[1:]):
        raise ValueError('Verification phase sequence changed')
    if calls[0]['nodes'] != row['preliminary_nodes']:
        raise ValueError('Preliminary node receipt differs from charged nodes')
    probes = [c['move'] for c in calls[1:]]
    legal = {m['jass_key'] for m in target['legal_moves']}
    if len(probes) != len(set(probes)) or not set(probes) <= legal:
        raise ValueError('Repeated or illegal probe')
    reason, chosen = row['decision_reason'], row['intervention']
    if reason.startswith('verified_') and set(probes) != legal:
        raise ValueError('Verified claim lacks a full legal probe inventory')
    if (chosen is not None) != (reason == 'verified_tie') or (chosen is not None and chosen not in legal):
        raise ValueError('Intervention and reported decision reason disagree')
    control, native, lcb = (row[k] for k in ('control_main', 'native_baseline', 'lcb_baseline'))
    return {'path': path, 'event': row['event'], 'fen': row['fen'], 'owner': owner,
            'budget': budget, 'verification_nodes': row['verification_nodes'],
            'verification_fraction': row['verification_nodes'] / budget,
            'preliminary_nodes': row['preliminary_nodes'],
            'probe_nodes': sum(c['nodes'] for c in calls[1:]),
            'verification_calls': len(calls), 'probe_calls': len(probes),
            'control_main_nodes': row['main_nodes'], 'decision_reason': reason,
            'reported_intervention': chosen, 'control': control, 'native': native, 'lcb': lcb,
            'control_native_same_move': control['best_move'] == native['best_move'],
            'control_lcb_same_move': control['best_move'] == lcb['best_move'],
            'control_native_score_delta': control['score'] - native['score'],
            'control_native_depth_delta': control['completed_depth'] - native['completed_depth'],
            'intervention_equals_final_control': chosen == control['best_move'] if chosen is not None else None,
            'main_attempt_trace_retained': 'attempts' in control,
            'full_verification_evidence_retained': all(
                all(k in c for k in ('completed', 'score', 'alpha_before', 'beta')) for c in calls)}


def summarize(rows):
    costs = [r['verification_nodes'] for r in rows]
    interventions = [r for r in rows if r['reported_intervention'] is not None]
    return {'receipts': len(rows), 'unique_positions': len({r['fen'] for r in rows}),
            'verification_nodes_sum': sum(costs),
            'verification_nodes_min': min(costs) if costs else None,
            'verification_nodes_max': max(costs) if costs else None,
            'verification_nodes_mean': fmean(costs) if costs else None,
            'control_total_nodes': sum(r['budget'] for r in rows),
            'verification_fraction_of_control_total': sum(costs) / sum(r['budget'] for r in rows) if rows else None,
            'preliminary_nodes_sum': sum(r['preliminary_nodes'] for r in rows),
            'probe_nodes_sum': sum(r['probe_nodes'] for r in rows),
            'verification_calls': sum(r['verification_calls'] for r in rows),
            'probe_calls': sum(r['probe_calls'] for r in rows),
            'control_main_nodes_sum': sum(r['control_main_nodes'] for r in rows),
            'decision_reasons': dict(sorted(Counter(r['decision_reason'] for r in rows).items())),
            'reported_intervention_receipts': len(interventions),
            'reported_intervention_unique_positions': len({r['fen'] for r in interventions}),
            'intervention_equals_final_control': sum(r['intervention_equals_final_control'] for r in interventions),
            'control_native_same_move': sum(r['control_native_same_move'] for r in rows),
            'control_lcb_same_move': sum(r['control_lcb_same_move'] for r in rows),
            'control_native_same_score_and_depth': sum(
                r['control_native_score_delta'] == r['control_native_depth_delta'] == 0 for r in rows),
            'depth_difference_cases': [r['path'] for r in rows if r['control_native_depth_delta']],
            'score_difference_cases': [r['path'] for r in rows if r['control_native_score_delta']],
            'main_attempt_traces_retained': sum(r['main_attempt_trace_retained'] for r in rows),
            'full_verification_evidence_retained': sum(r['full_verification_evidence_retained'] for r in rows)}


def analyze(root):
    joint, _ = pinned(root, FREEZE, BASE + 'two-named-arenas-final/manifest.json', MANIFEST_SHA)
    complete, complete_sha = pinned(root, DECISIONS, PREFIX + 'complete.json')
    methods = runtime.method(root, FREEZE)
    if (complete['complete'] is not True or complete['freeze_commit'] != FREEZE
            or complete['manifest_sha256'] != MANIFEST_SHA or complete['execution_sha256'] != methods):
        raise ValueError('Complete decision archive differs from frozen campaign')
    expected = {'source12.json', 'plan.json'} | {
        f'{e}/{b}/{i:05d}.json' for e in runtime.study.EVENTS for b in BUDGETS
        for i in range(len(joint['events'][e]['benchmark_targets']))}
    if set(complete['files']) != expected:
        raise ValueError('Complete archive inventory changed')
    packets = {n: pinned(root, DECISIONS, PREFIX + n, sha)[0] for n, sha in complete['files'].items()}
    sources = runtime._source12(joint, {'published_commit': FREEZE, 'manifest_sha256': MANIFEST_SHA},
                               packets['source12.json'], methods)
    rows = []
    for event in runtime.study.EVENTS:
        for budget in BUDGETS:
            targets = sorted(joint['events'][event]['benchmark_targets'], key=lambda t: t['target_fen'])
            for i, target in enumerate(targets):
                path = f'{event}/{budget}/{i:05d}.json'
                prefix = runtime.candidate_lists(target['legal_moves'], sources[target['source_fens']['LCB']])[1]['transfer']
                row = packets[path]
                if row['event'] != event:
                    raise ValueError('Receipt event differs from its frozen file')
                rows.append(audit_row(row, target, budget, prefix, path, target['bootstrap_owner']))
    by_position = defaultdict(list)
    for r in rows:
        by_position[r['fen']].append(r)
    same_verification = all(len(group) == 3 and len({r['verification_nodes'] for r in group}) == 1
                            and len({r['decision_reason'] for r in group}) == 1
                            and len({r['reported_intervention'] for r in group}) == 1
                            for group in by_position.values())
    selected = [r for r in rows if r['reported_intervention'] is not None]
    return {'schema': 'mtdp-two-arena-telemetry-audit-v1',
            'scope': 'post_hoc_archived_node_telemetry_no_new_quality_population_or_causal_attribution',
            'new_engine_searches': 0, 'target_references_opened': 0, 'new_independent_cohort': False,
            'freeze_commit': FREEZE, 'decisions_commit': DECISIONS,
            'complete_sha256': complete_sha, 'manifest_sha256': MANIFEST_SHA,
            'frozen_file_sha256': complete['files'], 'execution_sha256': methods,
            'all': summarize(rows), 'by_budget': {str(b): summarize([r for r in rows if r['budget'] == b]) for b in BUDGETS},
            'by_event': {e: summarize([r for r in rows if r['event'] == e]) for e in runtime.study.EVENTS},
            'verification_nodes_reason_and_intervention_same_across_budgets': same_verification,
            'rows': rows,
            'next_diagnostic_mask': {
                'selection': 'all_previously_reported_nonnull_interventions_no_target_score_filter',
                'independent_validation': False, 'cases': [{k: r[k] for k in (
                    'path', 'event', 'fen', 'owner', 'budget', 'verification_nodes', 'reported_intervention')} for r in selected],
                'required_additional_arms': ['LCB_unforced_same_residual_nodes', 'native_same_residual_nodes'],
                'required_trace': ['raw_preliminary_and_all_probe_receipts_with_exactness_bounds',
                                   'raw_main_native_LCB_stdout', 'all_depth_attempt_best_moves_and_orders'],
                'must_reproduce_archived_three_arm_summary_before_interpretation': True,
                'no_changes_to_frozen_primary_methods_or_results': True}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = analyze(a.root)
    with a.output.open('xb') as stream:
        stream.write(runtime._bytes(report))
    print(json.dumps({'receipts': report['all']['receipts'],
                      'unique_intervention_positions': report['all']['reported_intervention_unique_positions'],
                      'new_engine_searches': 0}))


if __name__ == '__main__':
    main()
