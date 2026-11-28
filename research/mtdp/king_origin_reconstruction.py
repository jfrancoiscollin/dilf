"""Corrected bounded replay of fixed historical quarantines and full fresh intake."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen,state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import verify_archive,digest
from research.mtdp.fresh_capture_ambiguity_audit import REPLAY_SHA
from research.mtdp.historical_exclusion_inventory_audit import MEMBERS,reconcile,check_game_audit
from research.mtdp.historical_fen_bridge import load_verified_cache,CACHE_SHA256
from research.mtdp.historical_base_quarantine_frontier import bind_sources
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.historical_quarantine_frontier import explore,MAX_FRONTIER,MAX_APPLICATIONS
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT,ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.king_origin_inventory_impact import load_inventory,encoded,BATCH_SIZE
from research.mtdp.return_capture_oracle import root_key,parse_catalogues
from research.mtdp.pdn import read_games
from research.mtdp.pdn_strict import parse_games_strict
from research.mtdp.reserved_source_inventory import build

PROTOCOL_COMMIT='f6d893315aa269493a8b86eb88c3e4247f815d17'
IMPACT_SHA='13061b5c12e387f5f3f359d421c73d5a9c921eada7e02b6187efd10a62aea943'


def add_owner(positions,fen,role,key,plies):
    positions.setdefault(fen,{}).setdefault((role,key),set()).update(plies)


def audit(root,base_dir,adapter,jass,executable,historical_inventory,fresh_inventory):
    root,base_dir=Path(root),Path(base_dir)
    impact_raw=(root/'research/mtdp/validation/king-origin-inventory-impact-2026-11-26.json').read_bytes()
    if digest(impact_raw)!=IMPACT_SHA:
        raise ValueError('verified impact report changed')
    prior=json.loads(impact_raw)
    if prior['summary']['corrected_jass_mismatch']!=0:
        raise ValueError('cannot reuse a mismatching reference scope')
    old_inputs={'historical_quarantines':load_inventory(historical_inventory,'historical_quarantines'),
                'fresh_candidate':load_inventory(fresh_inventory,'fresh_candidate')}
    old_union=set().union(*(set(r) for r in old_inputs.values()))
    if len(old_union)!=34172:
        raise ValueError('verified impact union changed')
    data={}
    for name,sha in MEMBERS.items():
        raw=(base_dir/name).read_bytes()
        if digest(raw)!=sha:raise ValueError('historical base member changed')
        data[name]=json.loads(raw)
    base=data['two-arena-exclusions.json'];history=data['P1RUlfJc-canonical-history.json']
    reconcile(data['P1RUlfJc-exclusions.json'],history,base,build(root))
    cache=load_verified_cache(base_dir/'four-reserved-events-exclusions.json')
    all_audit={**history['game_audit'],**base['added_event_game_audit'],**cache['extension_game_audit']}
    counts,fingerprints=check_game_audit(cache['sources'],all_audit)
    if counts['quarantined']!=190 or set(fingerprints)!=set(cache['fingerprints']):
        raise ValueError('fixed historical game accounting changed')
    selected={k:v for k,v in all_audit.items() if v['status']=='quarantined'}
    required=[s for s in cache['sources'] if any(k.rsplit(':',1)[0]==s['file'] for k in selected)]
    if len(required)!=21:raise ValueError('selected raw source scope changed')
    bound=bind_sources(base_dir,required,root)
    games={}
    for source in required:
        parsed=read_games(bound[source['file']])
        if len(parsed)!=source['games']:raise ValueError('historical raw game count changed')
        games[source['file']]=parsed
    engine,receipt=corrected_engine(adapter)
    if receipt['corrected_rules_sha256']!=prior['corrected_rules_sha256']:
        raise ValueError('corrected identity differs from reused reference proof')
    pinned_checkout(Path(jass).resolve(),JASS_COMMIT)
    cases=[]
    for key in sorted(selected):
        filename,index=key.rsplit(':',1)
        cases.append(('historical_quarantines',key,games[filename][int(index)-1],True))
    _,_,pdn=verify_archive(root/'research/mtdp/fresh_intake/2026-11-25-uDIrrl1c.zip')
    raw=(root/'research/mtdp/validation/fresh-uDIrrl1c-integrity-replay-2026-11-25.json').read_bytes()
    if digest(raw)!=REPLAY_SHA:raise ValueError('fresh legacy classification changed')
    fresh_games=parse_games_strict(pdn.decode('utf-8-sig'));baseline=json.loads(raw)['games']
    if len(fresh_games)!=152 or len({public_id(g) for g in fresh_games})!=152:
        raise ValueError('fresh identity population changed')
    for game,old in zip(fresh_games,baseline,strict=True):
        if public_id(game)!=old['public_game_id'] or game.index!=old['source_game_index']:
            raise ValueError('fresh source identity mismatch')
        cases.append(('fresh_candidate',public_id(game),game,not old['complete_legal_replay']))
    positions={};rows=[];role_fens={role:set() for role in old_inputs}
    for index,(role,key,game,legacy_quarantine) in enumerate(cases):
        row,visited=explore(game,engine)
        row.update(role=role,game_key=key,source_game_index=game.index,
                   public_game_id=public_id(game),legacy_quarantine_retained=legacy_quarantine)
        if not row['complete_board_frontier_replay']:
            row['unresolved_ply']=row['completed_plies']+1
            row['unresolved_token']=game.moves[row['completed_plies']]
        for state,plies in visited.items():
            fen=canonical_fen(state_to_fen(state))
            role_fens[role].add(fen);add_owner(positions,fen,role,key,plies)
        rows.append(row)
        if (index+1)%50==0 or index+1==len(cases):
            print(f'Reconstructed {index+1}/{len(cases)} records',flush=True)
    new_fens=sorted(set(positions)-old_union)
    oracle_ledger=bytearray();raw_catalogues=bytearray();mismatches=[];duplicates=0
    for start in range(0,len(new_fens),BATCH_SIZE):
        chunk=new_fens[start:start+BATCH_SIZE]
        process=subprocess.run([str(Path(executable).resolve())],input=''.join(f+'\n' for f in chunk),
            capture_output=True,text=True,check=True,timeout=30)
        catalogues=parse_catalogues(process.stdout,chunk);raw_catalogues.extend(process.stdout.encode())
        for fen,catalogue in zip(chunk,catalogues,strict=True):
            ours=set(map(root_key,engine.legal_moves(parse_fen(fen))));ref=set(catalogue)
            row=dict(fen=fen,corrected_roots=sorted(ours),jass_roots=sorted(ref),root_sets_equal=ours==ref)
            duplicates+=len(catalogue)!=len(ref)
            oracle_ledger.extend(encoded(row))
            if ours!=ref:mismatches.append(row)
    historical={canonical_fen(f) for f in cache['confirmed_fens']}
    inventory=b''.join(encoded(dict(fen=fen,legacy_cache_member=fen in historical,
        owners=[dict(role=role,game_key=key,plies=sorted(plies)) for (role,key),plies in sorted(owners.items())]))
        for fen,owners in sorted(positions.items()))
    overlap=sorted((role_fens['historical_quarantines']-historical)&role_fens['fresh_candidate'])
    report=dict(schema='mtdp-king-origin-v1-corrected-reconstruction-v1',protocol_commit=PROTOCOL_COMMIT,
        adapter_base_commit=ADAPTER_COMMIT,jass_commit=JASS_COMMIT,**receipt,historical_cache_sha256=CACHE_SHA256,
        reused_impact_report_sha256=IMPACT_SHA,frontier_limit=MAX_FRONTIER,application_limit=MAX_APPLICATIONS,
        historical_records=190,fresh_records=152,records=rows,
        status_counts_by_role={role:dict(sorted(Counter(r['status'] for r in rows if r['role']==role).items())) for role in sorted(role_fens)},
        incomplete_records=[dict(role=r['role'],game_key=r['game_key'],status=r['status']) for r in rows if not r['complete_board_frontier_replay']],
        distinct_possible_boards=len(positions),
        by_role={role:dict(corrected_possible_fens=len(values),old_inventory_fens=len(old_inputs[role]),
            added_vs_old_inventory=len(values-set(old_inputs[role])),lost_vs_old_inventory=len(set(old_inputs[role])-values)) for role,values in sorted(role_fens.items())},
        reused_reference_states=len(set(positions)&old_union),new_reference_states=len(new_fens),
        new_reference_mismatches=mismatches,jass_duplicate_new_root_positions=duplicates,
        historical_possible_fens_absent_from_legacy_cache=len(role_fens['historical_quarantines']-historical),
        fresh_historical_overlap_beyond_legacy_cache=[dict(fen=f,fen_sha256=digest(f.encode()),
            owners=[dict(role=role,game_key=key,plies=sorted(p)) for (role,key),p in sorted(positions[f].items())]) for f in overlap],
        inventory_bytes=len(inventory),inventory_sha256=digest(inventory),
        new_oracle_ledger_bytes=len(oracle_ledger),new_oracle_ledger_sha256=digest(oracle_ledger),
        raw_new_catalogues_bytes=len(raw_catalogues),raw_new_catalogues_sha256=digest(raw_catalogues),
        legacy_cache_or_quarantines_changed=False,unique_played_action_paths_certified=False,
        global_historical_replay_complete=False,independent_cohort_admitted=False,scientific_freeze=False,
        engine_scores_computed=False,signatures_computed=False)
    provenance=dict(catalogue_binary_sha256=digest(Path(executable).read_bytes()),**receipt)
    return report,inventory,bytes(oracle_ledger),bytes(raw_catalogues),provenance


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','base-dir','adapter','jass','executable','historical-inventory','fresh-inventory','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.output_dir.mkdir(exist_ok=False)
    report,inventory,ledger,raw,provenance=audit(a.root,a.base_dir,a.adapter,a.jass,a.executable,a.historical_inventory,a.fresh_inventory)
    for name,value in [('corrected-reconstruction.json',report),('provenance.json',provenance)]:
        (a.output_dir/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    for name,value in [('possible-board-inventory.jsonl',inventory),('new-state-oracle-ledger.jsonl',ledger),('new-state-jass-catalogues.txt',raw)]:
        (a.output_dir/name).write_bytes(value)


if __name__=='__main__':main()
