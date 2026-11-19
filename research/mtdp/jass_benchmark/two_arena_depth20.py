"""Exploratory horizon stability on all 26 frozen LCB-equal pairs, never Jass input."""
import argparse
import json
import subprocess
from pathlib import Path
from queue import Empty

from research.mtdp.jass_benchmark import two_arena_execution as runtime
from research.mtdp.jass_benchmark import two_arena_analysis as analysis
from research.mtdp.best_move_audit import compare_scores
from research.mtdp.jass_scan_reference import SCAN_EVAL_SHA256, SCAN_INI_SHA256

MODULE = 'research/mtdp/jass_benchmark/two_arena_depth20.py'
BASE = 'research/mtdp/jass_benchmark/spatial-jass/replication/'
PREFIX = BASE+'two-named-arenas-final'
FREEZE = '3fa9a56a3fa60954d5391d7e1b302c07e04f1f04'
RESULT_COMMIT = 'ec8c4dfc2b8ddc11de74c1af5d7d0e9d9d581a0b'
RESULT_SHA = '3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7'
PLAN = BASE+'two-named-arenas-depth20-plan.json'
METHOD_FILES = tuple(dict.fromkeys((MODULE,analysis.MODULE,*runtime.METHOD_FILES)))


class Depth20Scan(runtime.Scan):
    """Longer transport-idle allowance only; exact depth, TT and search stay fixed."""
    def until(self,marker):
        while True:
            try:line = self.lines.get(timeout=120)
            except Empty as error:raise RuntimeError(f'Scan20 transport idle waiting for {marker}') from error
            if line is None or line.startswith('error'):raise RuntimeError(f'Scan20 failed: {line}')
            if line.split(maxsplit=1)[0:1] == [marker]:return
            yield line


def subset(joint):
    selected = [{**t,'event':e} for e in runtime.study.EVENTS
                for t in joint['events'][e]['benchmark_targets'] if t['same_full_quiet_signature']['LCB']]
    pairs = [{'source_fen':t['source_fens']['LCB'],'target_fen':t['target_fen'],'legal_moves':t['legal_moves']}
             for t in selected]
    flat = {'schema':'mtdp-jass-cohort-v1','targets':pairs}
    identity = [{'event':t['event'],'target_fen':t['target_fen'],'source_fen':t['source_fens']['LCB'],
                 'owner':t['bootstrap_owner'],'games':t['target_games'],'legal_moves':t['legal_moves']} for t in selected]
    return selected,flat,identity


def plan_fields(joint,proof):
    selected,_,identity = subset(joint)
    return {'schema':'mtdp-two-arena-depth20-plan-v1','parent_freeze_commit':FREEZE,
            'parent_manifest_sha256':proof['manifest_sha256'],'parent_results_commit':RESULT_COMMIT,
            'parent_results_sha256':RESULT_SHA,'mask':'all_frozen_LCB_full_signature_equal_pairs',
            'pairs':identity,'mask_sha256':runtime.digest(runtime._bytes(identity)),
            'target_count':len(selected),'source_depth':20,'target_depth':20,
            'source_choice':'unchanged_frozen_LCB_no_reselection','new_independent_cohort':False,
            'primary_source_usable':False,'scope':'exploratory_after_known_Scan16_outcomes_no_new_holdout',
            'engines':joint['engines'],'scan_eval_sha256':SCAN_EVAL_SHA256,'scan_ini_sha256':SCAN_INI_SHA256,
            'transport_idle_timeout_seconds':120,'search_budget':'fixed_successor_depth_20_not_wall_time',
            'retain_zero_positive_and_categorical_costs':True}


def make_plan(root):
    joint,proof = runtime.published(root,PREFIX,FREEZE)
    runtime.method(root,FREEZE)
    raw = runtime._blob(root,RESULT_COMMIT,BASE+'two-named-arenas-results.json')
    if runtime.digest(raw) != RESULT_SHA:raise ValueError('Original primary results changed')
    return {**plan_fields(joint,proof),'method_files_sha256':{n:runtime.digest((root/n).read_bytes()) for n in METHOD_FILES},
            'fixed_at_utc':runtime.study._now().isoformat()}


def published_plan(root,commit):
    if not runtime.freeze._sha(commit,40):raise ValueError('Exact published depth20 plan SHA required')
    if Path(__file__).resolve() != (root/MODULE).resolve():raise ValueError('Imported depth20 module differs from checkout')
    joint,proof = runtime.published(root,PREFIX,FREEZE)
    runtime.method(root,FREEZE)
    for a,b in ((RESULT_COMMIT,commit),(commit,proof['observed_branch_head'])):
        subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',a,b],check=True)
    raw = runtime._blob(root,commit,PLAN);p = json.loads(raw)
    expected = plan_fields(joint,proof)
    if any(p.get(k) != v for k,v in expected.items()):raise ValueError('Fixed depth20 mask, source, engine or scope changed')
    if set(p.get('method_files_sha256',{})) != set(METHOD_FILES):raise ValueError('Depth20 method inventory incomplete')
    for name,sha in p['method_files_sha256'].items():
        if runtime.digest(runtime._blob(root,commit,name)) != sha or runtime.digest((root/name).read_bytes()) != sha:
            raise ValueError('Depth20 method changed after plan publication')
    if runtime.digest(runtime._blob(root,RESULT_COMMIT,BASE+'two-named-arenas-results.json')) != RESULT_SHA:
        raise ValueError('Original primary results changed')
    return joint,proof,p,runtime.digest(raw)


def score(root,plan_commit,adapter,binary,role,output):
    if role not in ('source','target'):raise ValueError('Explicit sensitivity source/target role required')
    joint,proof,p,plan_sha = published_plan(root,plan_commit)  # before engine or output access
    _,flat,_ = subset(joint)
    if output.exists():raise ValueError('Depth20 output already exists')
    pins = runtime.scan_fingerprints(binary,{'scan_binary_sha256':joint['engines']['scan_sha256']})
    expected = runtime.expected_actions(flat,role)
    status = output.with_name(output.name+'.attempt.json')
    started = {'plan_commit':plan_commit,'plan_sha256':plan_sha,'role':role,'depth':20,'complete':False,
               'expected_positions':len(expected),'expected_action_scores':sum(map(len,expected.values())),
               'started_at_utc':runtime.study._now().isoformat(),'scope':p['scope']}
    with status.open('xb') as stream:stream.write(runtime._bytes(started))
    try:
        if expected:
            engine = runtime.checked_engine(adapter)
            with Depth20Scan(binary,depth=20) as scan:report = runtime.score_manifest(flat,engine,scan,role=role)
        else:report = {'role':role,'action_scores_centimen':{}}
        report.update(schema='mtdp-jass-scan-reference-v1',cohort_sha256=p['mask_sha256'],
            parent_manifest_sha256=proof['manifest_sha256'],scan_binary_sha256=pins['scan_linux'],
            scan_eval_sha256=pins['data/eval'],scan_ini_sha256=pins['scan.ini'],scan_successor_depth=20,
            reference_kind=role+'20_exploratory',primary_source_usable=False,
            sensitivity_plan_commit=plan_commit,sensitivity_plan_sha256=plan_sha,
            execution_sha256=p['method_files_sha256'],scope=p['scope'],publication_verification=proof)
        runtime.validate_reference(report,expected,pins,p['mask_sha256'],20)
        with output.open('xb') as stream:stream.write(runtime._bytes(report))
        status.write_bytes(runtime._bytes({**started,'complete':True,'reference_sha256':runtime.digest(runtime._bytes(report)),
                                          'finished_at_utc':runtime.study._now().isoformat()}))
        return report
    except Exception as error:
        status.write_bytes(runtime._bytes({**started,'error':type(error).__name__,'detail':str(error)}));raise


def validate_packet(packet,role,p,plan_sha,commit,flat):
    if (packet.get('reference_kind') != role+'20_exploratory' or packet.get('role') != role
            or packet.get('primary_source_usable') is not False or packet.get('sensitivity_plan_commit') != commit
            or packet.get('sensitivity_plan_sha256') != plan_sha or packet.get('execution_sha256') != p['method_files_sha256']
            or packet.get('parent_manifest_sha256') != p['parent_manifest_sha256'] or packet.get('scope') != p['scope']
            or packet.get('publication_verification',{}).get('published_commit') != FREEZE
            or packet.get('publication_verification',{}).get('scientific_freeze') is not True
            or packet.get('scan_ini_sha256') != SCAN_INI_SHA256):
        raise ValueError('Depth20 packet is not bound to this exploratory plan')
    return runtime.validate_reference(packet,runtime.expected_actions(flat,role),
        {'scan_linux':p['engines']['scan_sha256'],'data/eval':SCAN_EVAL_SHA256},p['mask_sha256'],20)


def compared_rows(selected,sources,targets):
    rows = []
    for t in selected:
        c = compare_scores(sources[t['source_fens']['LCB']],targets[t['target_fen']]);cost = c['a_to_b']['ordinary_regret_centimen']
        rows.append({'event':t['event'],'fen':t['target_fen'],'source_fen':t['source_fens']['LCB'],
            'owner':t['bootstrap_owner'],'games':t['target_games'],**c,
            'disjoint':int(not c['optimal_sets_overlap']),
            'pick_optimal':int(c['a_to_b']['best_centimen'] == c['a_to_b']['transferred_centimen']),
            'ordinary_regret':cost,'positive_regret':cost if cost is not None and cost > 0 else None})
    return rows


def analyze(root,commit,source_path,target_path):
    joint,proof,p,plan_sha = published_plan(root,commit);selected,flat,_ = subset(joint)
    raw_s,raw_t = source_path.read_bytes(),target_path.read_bytes()
    s20 = validate_packet(json.loads(raw_s),'source',p,plan_sha,commit,flat)
    t20 = validate_packet(json.loads(raw_t),'target',p,plan_sha,commit,flat)
    methods = runtime.method(root,FREEZE)
    s16 = analysis._reference(joint,proof,methods,json.loads(runtime._blob(root,RESULT_COMMIT,BASE+'two-named-arenas-source16.json')),'source16')
    t16 = analysis._reference(joint,proof,methods,json.loads(runtime._blob(root,RESULT_COMMIT,BASE+'two-named-arenas-target16.json')),'target16')
    old = json.loads(runtime._blob(root,RESULT_COMMIT,BASE+'two-named-arenas-results.json'))
    rows16,rows20 = compared_rows(selected,s16,t16),compared_rows(selected,s20,t20)
    population = [{'event':e,'fen':t['target_fen'],'owner':t['bootstrap_owner']}
                  for e in runtime.study.EVENTS for t in joint['events'][e]['benchmark_targets']]
    summaries = {}
    for scope in ('all',*runtime.study.EVENTS):
        frame = population if scope == 'all' else [x for x in population if x['event'] == scope]
        a = rows16 if scope == 'all' else [x for x in rows16 if x['event'] == scope]
        b = rows20 if scope == 'all' else [x for x in rows20 if x['event'] == scope]
        baseline = analysis._summary_geometry(a,frame)
        if baseline != old['geometry']['LCB']['estimates'][scope]['LCB_full_equal']:
            raise ValueError('Exploratory comparison changed the original Scan16 baseline')
        summaries[scope] = {'Scan16':baseline,'Scan20':analysis._summary_geometry(b,frame)}
    changes = []
    for a,b in zip(rows16,rows20,strict=True):
        x,y = a['ordinary_regret'],b['ordinary_regret']
        changes.append({'event':a['event'],'owner':a['owner'],'fen':a['fen'],'Scan16':a,'Scan20':b,
                        'disjoint_delta':b['disjoint']-a['disjoint'],
                        'ordinary_regret_delta':y-x if x is not None and y is not None else None})
    return {'schema':'mtdp-two-arena-depth20-sensitivity-v1','scope':p['scope'],'new_independent_cohort':False,
            'primary_results_unchanged':True,'plan_commit':commit,'plan_sha256':plan_sha,
            'parent_results_commit':RESULT_COMMIT,'parent_results_sha256':RESULT_SHA,'mask_sha256':p['mask_sha256'],
            'source20_sha256':runtime.digest(raw_s),'target20_sha256':runtime.digest(raw_t),
            'summaries':summaries,'rows':changes,
            'depth_transitions':{'stable_disjoint':sum(a['disjoint'] and b['disjoint'] for a,b in zip(rows16,rows20)),
                'resolved_disjoint':sum(a['disjoint'] and not b['disjoint'] for a,b in zip(rows16,rows20)),
                'new_disjoint':sum(not a['disjoint'] and b['disjoint'] for a,b in zip(rows16,rows20)),
                'stable_intersection':sum(not a['disjoint'] and not b['disjoint'] for a,b in zip(rows16,rows20))},
            'paired_bootstrap':{k:analysis.bootstrap(changes,population,k) for k in ('disjoint_delta','ordinary_regret_delta')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('make-plan','score','analyze'));parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--plan-commit');parser.add_argument('--role',choices=('source','target'))
    for n in ('adapter','scan','source','target','output'):parser.add_argument(f'--{n}',type=Path)
    a = parser.parse_args()
    required = {'make-plan':('output',),'score':('plan_commit','role','adapter','scan','output'),
                'analyze':('plan_commit','source','target','output')}[a.mode]
    if any(getattr(a,n) is None for n in required):parser.error(f'{a.mode} requires {required}')
    r = make_plan(a.root) if a.mode == 'make-plan' else score(a.root,a.plan_commit,a.adapter,a.scan,a.role,a.output) if a.mode == 'score' else analyze(a.root,a.plan_commit,a.source,a.target)
    if a.mode != 'score':
        with a.output.open('xb') as stream:stream.write(runtime._bytes(r))
    print(json.dumps({'mode':a.mode,'scope':r['scope'],'new_independent_cohort':False},sort_keys=True))


if __name__ == '__main__':main()
