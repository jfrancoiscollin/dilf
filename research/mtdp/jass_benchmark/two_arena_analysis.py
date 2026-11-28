"""Registered joint geometry and equal-node estimates; code published before target16."""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median

from research.mtdp.jass_benchmark import two_arena_execution as runtime
from research.mtdp.jass_benchmark.named_campaign_quality import ARMS
from research.mtdp.best_move_audit import compare_scores
from research.mtdp.jass_benchmark.depth_sensitivity import regret, validate_reference
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256
from research.mtdp.top_k_transfer import _action

MODULE = 'research/mtdp/jass_benchmark/two_arena_analysis.py'


def bootstrap(rows,population,field):
    """Identical whole-game draws across arms/fields, including empty strata.

    Each draw recomputes a position-weighted ratio. Source/tie/signature masks
    never alter the owner sampling frame. Undefined draws suppress a CI rather
    than being silently retried or removed from the fixed percentile ranks.
    """
    units = {e:sorted({r['owner'] for r in population if r['event'] == e}) for e in runtime.study.EVENTS}
    known = {(r['event'],r['owner']) for r in population}
    if any((r['event'],r['owner']) not in known for r in rows):raise ValueError('Bootstrap ownership changed')
    if len({(r['event'],r['fen']) for r in rows}) != len(rows):raise ValueError('Duplicate position in an estimand')
    grouped = defaultdict(list)
    for r in rows:
        if r[field] is not None:grouped[(r['event'],r['owner'])].append(r[field])
    values = [v for vs in grouped.values() for v in vs]
    result = {'positions':len(values),'owner_games':len(grouped),
              'sampling_owner_games':{e:len(v) for e,v in units.items()},
              'mean':fmean(values) if values else None,'resamples':10000,'seed':20261113,
              'percentile_indices':[249,9749],'undefined_draws':10000 if not values else 0,'ci95':None}
    if not values:return result
    tables = [[(sum(grouped[e,g]),len(grouped[e,g])) for g in units[e]] for e in runtime.study.EVENTS]
    rng = random.Random(20261113);distribution = []
    for _ in range(10000):
        draw = [v for table in tables for v in rng.choices(table,k=len(table))]
        count = sum(n for _,n in draw)
        if count:distribution.append(sum(s for s,_ in draw)/count)
    result['undefined_draws'] = 10000-len(distribution)
    if len(distribution) == 10000 and sum(map(len,tables)) > 1:
        distribution.sort();result['ci95'] = [distribution[249],distribution[9749]]
    return result


def _summary_geometry(rows,population):
    costs = [r['ordinary_regret'] for r in rows if r['ordinary_regret'] is not None]
    positive = [v for v in costs if v > 0]
    return {'positions':len(rows),'owner_games':len({(r['event'],r['owner']) for r in rows}),
            'optimal_sets_disjoint':sum(r['disjoint'] for r in rows),
            'source_pick_target_optimal':sum(r['pick_optimal'] for r in rows),
            'suboptimal_pick_despite_optimum_intersection':sum(not r['pick_optimal'] and not r['disjoint'] for r in rows),
            'ordinary_positions':len(costs),'ordinary_mean_regret':fmean(costs) if costs else None,
            'ordinary_median_regret':median(costs) if costs else None,'ordinary_max_regret':max(costs) if costs else None,
            'positive_cost_positions':len(positive),'positive_cost_mean':fmean(positive) if positive else None,
            'positive_cost_median':median(positive) if positive else None,'positive_cost_max':max(positive) if positive else None,
            'category_transitions':dict(Counter(r['a_to_b']['best_category']+'/'+r['a_to_b']['transferred_category'] for r in rows)),
            'bootstrap':{k:bootstrap(rows,population,k) for k in ('disjoint','pick_optimal','ordinary_regret','positive_regret')}}


def geometry(joint,sources,targets):
    population = [{'event':e,'fen':t['target_fen'],'owner':t['bootstrap_owner']}
                  for e in runtime.study.EVENTS for t in joint['events'][e]['benchmark_targets']]
    output = {}
    for arm in ('L','LCB'):
        rows = []
        for e in runtime.study.EVENTS:
            for t in joint['events'][e]['benchmark_targets']:
                compared = compare_scores(sources[t['source_fens'][arm]],targets[t['target_fen']])
                cost = compared['a_to_b']['ordinary_regret_centimen']
                rows.append({'event':e,'fen':t['target_fen'],'source_fen':t['source_fens'][arm],
                    'owner':t['bootstrap_owner'],'games':t['target_games'],
                    'LCB_full_equal':t['same_full_quiet_signature']['LCB'],
                    'source_full_equal':t['same_full_quiet_signature'][arm],**compared,
                    'disjoint':int(not compared['optimal_sets_overlap']),
                    'pick_optimal':int(compared['a_to_b']['best_centimen'] == compared['a_to_b']['transferred_centimen']),
                    'ordinary_regret':cost,'positive_regret':cost if cost is not None and cost > 0 else None})
        output[arm] = {'rows':rows,'estimates':{}}
        for scope in ('all',*runtime.study.EVENTS):
            frame = population if scope == 'all' else [r for r in population if r['event'] == scope]
            chosen = rows if scope == 'all' else [r for r in rows if r['event'] == scope]
            # The same registered LCB equality mask is used for both source arms.
            output[arm]['estimates'][scope] = {stratum:_summary_geometry(
                chosen if equal is None else [r for r in chosen if r['LCB_full_equal'] == equal],frame)
                for stratum,equal in (('all',None),('LCB_full_equal',True),('LCB_full_different',False))}
    return output


def _reference(joint,proof,methods,packet,kind):
    role,depth = ('target',16) if kind == 'target16' else ('source',16)
    if (packet.get('reference_kind') != kind or packet.get('role') != role
            or packet.get('primary_source_usable') is not False
            or packet.get('publication_verification',{}).get('published_commit') != proof['published_commit']
            or packet.get('publication_verification',{}).get('scientific_freeze') is not True
            or packet.get('execution_sha256') != methods or packet.get('scan_ini_sha256') != SCAN_INI_SHA256):
        raise ValueError('Reference kind or joint publication/method binding changed')
    return validate_reference(packet,runtime.expected_actions(runtime.flat_manifest(joint),role),
        {'scan_linux':joint['engines']['scan_sha256'],'data/eval':SCAN_EVAL_SHA256},proof['manifest_sha256'],depth)


def analyze(root,prefix,freeze_commit,decisions_commit,decisions_prefix,source16_path,target16_path):
    joint,proof = runtime.published(root,prefix,freeze_commit)
    methods = runtime.method(root,freeze_commit)
    # This exact analysis implementation must precede target opening, because
    # target16 itself requires this published decisions snapshot.
    if (root/MODULE).read_bytes() != runtime._blob(root,decisions_commit,MODULE):
        raise ValueError('Analysis implementation was not fixed in the pre-target decisions commit')
    prior = runtime.published_decisions(root,joint,proof,decisions_commit,decisions_prefix,methods)
    source_raw,target_raw = source16_path.read_bytes(),target16_path.read_bytes()
    source,target = json.loads(source_raw),json.loads(target_raw)
    if target.get('prior_published_decisions') != prior:
        raise ValueError('Target reference opened before these complete published decisions')
    sources = _reference(joint,proof,methods,source,'source16');targets = _reference(joint,proof,methods,target,'target16')
    complete_raw = runtime._blob(root,decisions_commit,f'{decisions_prefix}/complete.json')
    complete = json.loads(complete_raw)
    packet = json.loads(runtime._blob(root,decisions_commit,f'{decisions_prefix}/source12.json'))
    ranking = runtime._source12(joint,proof,packet,methods)
    population = [{'event':e,'fen':t['target_fen'],'owner':t['bootstrap_owner']}
                  for e in runtime.study.EVENTS for t in joint['events'][e]['benchmark_targets']]
    budgets = {}
    for budget in (10000,50000,200000):
        rows = []
        for e in runtime.study.EVENTS:
            ordered = sorted(joint['events'][e]['benchmark_targets'],key=lambda r:r['target_fen'])
            for i,t in enumerate(ordered):
                raw = runtime._blob(root,decisions_commit,f'{decisions_prefix}/{e}/{budget}/{i:05d}.json')
                receipt = json.loads(raw)
                prefix_moves = runtime.candidate_lists(t['legal_moves'],ranking[t['source_fens']['LCB']])[1]['transfer']
                paired = runtime.check_receipt(receipt,t,budget,prefix_moves)
                by_key = {m['jass_key']:_action(m) for m in t['legal_moves']}
                scores = targets[t['target_fen']];best = max(scores.values())
                arms = {arm:{'move':receipt[field]['best_move'],
                    'score':scores[by_key[receipt[field]['best_move']]],
                    **regret(best,scores[by_key[receipt[field]['best_move']]])} for arm,field in ARMS.items()}
                row = {'event':e,'fen':t['target_fen'],'owner':t['bootstrap_owner'],'games':t['target_games'],
                       'paired':paired,'arms':arms,'verification_nodes':receipt['verification_nodes'],
                       'control_native_agreement':arms['control']['move'] == arms['native']['move'],
                       'intervention':receipt['intervention'],'decision_reason':receipt['decision_reason']}
                for arm in ARMS:
                    row[f'{arm}_regret'] = arms[arm]['ordinary_regret_centimen'] if paired else None
                    row[f'{arm}_optimal'] = int(arms[arm]['covered']) if paired else None
                for comparator in ('native','lcb'):
                    x,y = row['control_regret'],row[f'{comparator}_regret']
                    row[f'control_minus_{comparator}'] = x-y if x is not None and y is not None else None
                rows.append(row)
        estimates = {}
        for scope in ('all',*runtime.study.EVENTS):
            chosen = rows if scope == 'all' else [r for r in rows if r['event'] == scope]
            frame = population if scope == 'all' else [r for r in population if r['event'] == scope]
            estimates[scope] = {'planned':len(chosen),'paired':sum(r['paired'] for r in chosen),
                'depth_ceiling_excluded':sum(not r['paired'] for r in chosen),
                'control_native_agreement':sum(r['control_native_agreement'] for r in chosen),
                'optimum_hits_paired':{a:sum(r[f'{a}_optimal'] or 0 for r in chosen) for a in ARMS},
                'bootstrap':{k:bootstrap(chosen,frame,k) for k in (
                    'native_regret','lcb_regret','control_regret','control_minus_native','control_minus_lcb')}}
        budgets[str(budget)] = {'rows':rows,'estimates':estimates}
    return {'schema':'mtdp-two-arena-registered-results-v1','freeze_commit':freeze_commit,
            'manifest_sha256':proof['manifest_sha256'],'decisions_commit':decisions_commit,
            'pretarget_analysis_commit':decisions_commit,'analysis_sha256':runtime.digest((root/MODULE).read_bytes()),
            'source16_sha256':runtime.digest(source_raw),'target16_sha256':runtime.digest(target_raw),
            'decision_complete_sha256':runtime.digest(complete_raw),'execution_sha256':methods,
            'primary_total_node_budget':50000,'primary_geometry_mask':'frozen_LCB_full_signature_equal',
            'geometry_source_depth':16,'target_depth':16,'Jass_ranking_source_depth':12,
            'scope':'two_fixed_registered_arenas_no_Elo_minimax_or_population_equivalence_claim',
            'score_unit':'integer Scan unit = 0.01 HUB, not fixed material pawn value',
            'bootstrap_scope':'whole frozen owner games stratified by two fixed arenas; in-sample variation only',
            'geometry':geometry(joint,sources,targets),'budgets':budgets}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for n in ('root','source16','target16','output'):parser.add_argument(f'--{n}',type=Path,required=True)
    for n in ('prefix','freeze','decisions-commit','decisions-prefix'):parser.add_argument(f'--{n}',required=True)
    a = parser.parse_args();report = analyze(a.root,a.prefix,a.freeze,a.decisions_commit,a.decisions_prefix,a.source16,a.target16)
    with a.output.open('xb') as stream:stream.write(runtime._bytes(report))
    print(json.dumps({'geometry_LCB_primary':report['geometry']['LCB']['estimates']['all']['LCB_full_equal'],
                      'primary_Jass':report['budgets']['50000']['estimates']['all']},sort_keys=True))


if __name__ == '__main__':main()
