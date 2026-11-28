"""Fixed references and three-arm decisions bound to the joint remote freeze.

Source12 is the only ranking input. Geometry source16 is a separate packet.
Target16 requires all source12/Jass decisions already published on the branch.
"""
import argparse
import json
import subprocess
from pathlib import Path

from research.mtdp.jass_benchmark import two_arena_freeze as freeze
from research.mtdp.jass_benchmark import two_arena_registration as study
from research.mtdp.jass_benchmark.named_arena_execution import (
    _blob, scan_fingerprints, expected_actions, Scan, score_manifest, checked_engine,
)
from research.mtdp.jass_benchmark.named_metered_campaign import checked_build, source_scores, BUILD_INPUTS
from research.mtdp.jass_benchmark.named_campaign_quality import check_receipt
from research.mtdp.jass_benchmark.metered_engine_smoke import technical_smoke
from research.mtdp.jass_benchmark.offline_top3_control import candidate_lists
from research.mtdp.jass_benchmark.depth_sensitivity import validate_reference
from research.mtdp.jass_benchmark.named_freeze_bundle import _bytes
from research.mtdp.jass_benchmark.prospective_candidate_replay import digest

MODULE = 'research/mtdp/jass_benchmark/two_arena_execution.py'
METHOD_FILES = tuple(dict.fromkeys((MODULE,freeze.MODULE,*freeze.replay.DEPENDENCIES,
    'research/mtdp/jass_benchmark/named_arena_execution.py',
    'research/mtdp/jass_benchmark/named_metered_campaign.py',
    'research/mtdp/jass_benchmark/named_campaign_quality.py',
    'research/mtdp/jass_benchmark/depth_sensitivity.py',
    'research/mtdp/jass_benchmark/offline_top3_control.py',
    'research/mtdp/jass_benchmark/metered_engine_smoke.py',
    'research/mtdp/jass_benchmark/metered_probe_adapter.py',
    'research/mtdp/jass_benchmark/metered_control.py',
    'research/mtdp/jass_benchmark/prospective_tiebreak.py',
    'research/mtdp/jass_benchmark/total_budget.py',
    'research/mtdp/jass_scan_reference.py','research/mtdp/top_k_transfer.py',*BUILD_INPUTS)))


def published(root,prefix,commit):
    proof = freeze.verify_publication(root,prefix,commit)
    raw = _blob(root,commit,f'{freeze._safe_path(prefix)}/manifest.json')
    if proof.get('scientific_freeze') is not True or proof.get('manifest_sha256') != digest(raw):
        raise ValueError('Joint publication verification does not bind the manifest')
    return json.loads(raw),proof


def method(root,commit):
    if Path(__file__).resolve() != (root/MODULE).resolve():
        raise ValueError('Imported execution method differs from the research checkout')
    result = {}
    for name in METHOD_FILES:
        raw = (root/name).read_bytes()
        if raw != _blob(root,commit,name):raise ValueError(f'Joint execution method changed after freeze: {name}')
        result[name] = digest(raw)
    return result


def flat_manifest(joint,event=None):
    if (joint.get('schema') != 'mtdp-two-arena-joint-manifest-v1'
            or joint.get('event_order') != list(study.EVENTS)
            or (event is not None and event not in study.EVENTS)):
        raise ValueError('Exact joint manifest and arena identities required')
    events = study.EVENTS if event is None else (event,)
    targets = [r for e in events for r in joint['events'][e]['benchmark_targets']]
    if len({r['target_fen'] for r in targets}) != len(targets):raise ValueError('Duplicate cross-arena target')
    pairs = [{'source_fen':s,'target_fen':t['target_fen'],'legal_moves':t['legal_moves']}
             for t in targets for s in sorted(set(t['source_fens'].values()))]
    return {'schema':'mtdp-jass-cohort-v1','targets':pairs,'benchmark_targets':targets,
            'engine':{'scan_binary_sha256':joint['engines']['scan_sha256'],
                      'jass_node_budgets':joint['analysis']['total_node_budgets']}}


def _source12(joint,proof,packet,methods):
    if packet.get('reference_kind') != 'source12' or packet.get('primary_source_usable') is not True:
        raise ValueError('Only the separate source12 packet can rank Jass prefixes')
    return source_scores(flat_manifest(joint),proof,packet,methods)


def published_decisions(root,joint,proof,commit,prefix,methods):
    if not freeze._sha(commit,40):raise ValueError('Exact published decisions commit required')
    prefix = freeze._safe_path(prefix)
    for a,b in ((proof['published_commit'],commit),(commit,proof['observed_branch_head'])):
        subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',a,b],check=True)
    complete = json.loads(_blob(root,commit,f'{prefix}/complete.json'))
    if (complete.get('schema') != 'mtdp-two-arena-decisions-v1' or complete.get('complete') is not True
            or complete.get('freeze_commit') != proof['published_commit']
            or complete.get('manifest_sha256') != proof['manifest_sha256']
            or complete.get('execution_sha256') != methods):
        raise ValueError('Published decisions do not cover this exact joint freeze/method')
    expected = {'source12.json','plan.json'} | {
        f'{e}/{b}/{i:05d}.json' for e in study.EVENTS for b in (10000,50000,200000)
        for i in range(len(joint['events'][e]['benchmark_targets']))}
    if set(complete['files']) != expected:raise ValueError('Published decision inventory incomplete')
    data = {}
    for name,sha in complete['files'].items():
        raw = _blob(root,commit,f'{prefix}/{name}')
        if digest(raw) != sha:raise ValueError('Published decision bytes changed')
        data[name] = json.loads(raw)
    sources = _source12(joint,proof,data['source12.json'],methods)
    for e in study.EVENTS:
        targets = sorted(joint['events'][e]['benchmark_targets'],key=lambda r:r['target_fen'])
        for budget in (10000,50000,200000):
            for i,t in enumerate(targets):
                prefix_moves = candidate_lists(t['legal_moves'],sources[t['source_fens']['LCB']])[1]['transfer']
                check_receipt(data[f'{e}/{budget}/{i:05d}.json'],t,budget,prefix_moves)
    return {'commit':commit,'prefix':prefix,'complete_sha256':digest(_blob(root,commit,f'{prefix}/complete.json'))}


def reference(root,prefix,commit,adapter,binary,kind,output,decisions_commit=None,decisions_prefix=None):
    if kind not in ('source12','source16','target16'):raise ValueError('Explicit fixed reference kind required')
    joint,proof = published(root,prefix,commit)  # before any engine, reference input or output
    methods = method(root,commit)
    prior = None
    if kind == 'target16':
        if not decisions_commit or not decisions_prefix:
            raise ValueError('Target16 requires published complete source12/Jass decisions')
        prior = published_decisions(root,joint,proof,decisions_commit,decisions_prefix,methods)
    if output.exists():raise ValueError('Reference output already exists')
    flat = flat_manifest(joint)
    pins = scan_fingerprints(binary,flat['engine'])
    role,depth = ('target',16) if kind == 'target16' else ('source',12 if kind == 'source12' else 16)
    expected = expected_actions(flat,role)
    if expected:
        engine = checked_engine(adapter)
        with Scan(binary,depth=depth) as scan:report = score_manifest(flat,engine,scan,role=role)
    else:report = {'role':role,'action_scores_centimen':{}}
    report.update(schema='mtdp-jass-scan-reference-v1',cohort_sha256=proof['manifest_sha256'],
        scan_binary_sha256=pins['scan_linux'],scan_eval_sha256=pins['data/eval'],scan_ini_sha256=pins['scan.ini'],
        scan_successor_depth=depth,publication_verification=proof,execution_sha256=methods,
        reference_kind=kind,primary_source_usable=kind == 'source12',prior_published_decisions=prior,
        study_id=joint['study_id'],scope='registered_two_arena_reference_not_quality_analysis')
    validate_reference(report,expected,pins,proof['manifest_sha256'],depth)
    with output.open('xb') as stream:stream.write(_bytes(report))
    return report


def campaign(root,prefix,commit,source_path,probe,main,output):
    joint,proof = published(root,prefix,commit)
    methods = method(root,commit)
    build = checked_build(root,commit,probe,main)
    raw = source_path.read_bytes();sources = _source12(joint,proof,json.loads(raw),methods)
    if joint['analysis']['total_node_budgets'] != [10000,50000,200000]:raise ValueError('Total-node budgets changed')
    output.mkdir(parents=True,exist_ok=False)
    plan = {'schema':'mtdp-two-arena-decisions-v1','complete':False,'freeze_commit':commit,
            'manifest_sha256':proof['manifest_sha256'],'execution_sha256':methods,'build':build,
            'source12_sha256':digest(raw),'scope':'complete_decisions_before_target16_no_target_outcomes_read'}
    (output/'plan.json').write_bytes(_bytes(plan));(output/'source12.json').write_bytes(raw)
    counts = {}
    for e in study.EVENTS:
        targets = sorted(joint['events'][e]['benchmark_targets'],key=lambda r:r['target_fen'])
        counts[e] = {}
        for budget in (10000,50000,200000):
            destination = output/e/str(budget);destination.mkdir(parents=True)
            paired = 0
            for i,t in enumerate(targets):
                moves = candidate_lists(t['legal_moves'],sources[t['source_fens']['LCB']])[1]['transfer']
                try:
                    r = technical_smoke(probe,main,t['target_fen'],total_nodes=budget,prefix=moves,
                                        expected_legal_keys=[m['jass_key'] for m in t['legal_moves']])
                    row = {'event':e,'fen':t['target_fen'],'games':t['target_games'],
                           'budget':budget,'LCB_prefix':moves,**r}
                    paired += check_receipt(row,t,budget,moves)
                    (destination/f'{i:05d}.json').write_bytes(_bytes(row))
                except Exception as error:
                    (destination/f'{i:05d}-FAILED.json').write_bytes(_bytes({'error':type(error).__name__,'detail':str(error)}))
                    raise
            counts[e][str(budget)] = {'planned':len(targets),'recorded':len(targets),'paired_comparable':paired,
                                     'depth_ceiling_excluded':len(targets)-paired}
    files = {p.relative_to(output).as_posix():digest(p.read_bytes()) for p in sorted(output.rglob('*.json'))}
    complete = {**plan,'complete':True,'counts':counts,'files':files}
    (output/'complete.json').write_bytes(_bytes(complete));return complete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('reference','campaign'))
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--prefix',required=True)
    parser.add_argument('--commit',required=True);parser.add_argument('--output',type=Path,required=True)
    for n in ('adapter','scan','source','probe','main'):parser.add_argument(f'--{n}',type=Path)
    parser.add_argument('--kind',choices=('source12','source16','target16'))
    parser.add_argument('--decisions-commit');parser.add_argument('--decisions-prefix');a = parser.parse_args()
    required = ('adapter','scan','kind') if a.mode == 'reference' else ('source','probe','main')
    if any(getattr(a,n) is None for n in required):parser.error(f'{a.mode} requires {required}')
    r = (reference(a.root,a.prefix,a.commit,a.adapter,a.scan,a.kind,a.output,a.decisions_commit,a.decisions_prefix)
         if a.mode == 'reference' else campaign(a.root,a.prefix,a.commit,a.source,a.probe,a.main,a.output))
    print(json.dumps({k:r[k] for k in ('reference_kind','scan_successor_depth') if k in r}
                     | {'complete':r.get('complete'),'scientific_outcome_analysis':False},sort_keys=True))


if __name__ == '__main__':main()
