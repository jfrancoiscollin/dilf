"""All remaining182 known historical quarantines, exclusion-only board frontier."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from pedagogy.game import state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.historical_exclusion_inventory_audit import MEMBERS, reconcile
from research.mtdp.historical_fen_bridge import load_verified_cache, CACHE_SHA256
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.historical_quarantine_frontier import explore, MAX_FRONTIER, MAX_APPLICATIONS, FRESH_INVENTORY_SHA
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.pdn import read_games, validated_trajectory, PdnReplayError
from research.mtdp.reserved_source_inventory import build

PROTOCOL_COMMIT = '111593215b6eca6774709b93568468c63efc51df'
PREVIOUS_INVENTORY_SHA = '6548bacd74f6cc46262cb6c2d1ad8e16501c5d771199f3a73b07958ee4efec6d'


def bind_sources(directory, required, repository=None):
    by_hash = defaultdict(list)
    roots = [Path(directory)] + ([Path(repository)] if repository is not None else [])
    for root in roots:
        for p in sorted(root.rglob('*.pdn')):
            by_hash[digest(p.read_bytes())].append(p)
    if len({s['file'] for s in required}) != len(required):
        raise ValueError('duplicate declared source identity')
    bound = {}
    for source in required:
        candidates = by_hash.get(source['sha256'], [])
        if not candidates:
            raise ValueError('missing exact raw source: ' + source['file'])
        bound[source['file']] = candidates[0]
    return bound


def audit(root, base_dir, adapter, fresh_inventory, previous_inventory):
    root, base_dir = Path(root), Path(base_dir)
    members = {}
    for name, sha in MEMBERS.items():
        raw = (base_dir / name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('historical member changed: ' + name)
        members[name] = json.loads(raw)
    old = members['P1RUlfJc-canonical-history.json']
    base = members['two-arena-exclusions.json']
    counts = reconcile(members['P1RUlfJc-exclusions.json'], old, base, build(root))
    if counts['quarantined_game_records'] != 182 or counts['source_count'] != 23:
        raise ValueError('fixed base scope changed')
    cache = load_verified_cache(base_dir / 'four-reserved-events-exclusions.json')
    if base['sources'] != cache['sources'][:23]:
        raise ValueError('source ancestry differs from pinned cache')
    history = {canonical_fen(f) for f in cache['confirmed_fens']}
    all_audit = {**old['game_audit'], **base['added_event_game_audit']}
    if len(all_audit) != counts['source_game_records']:
        raise ValueError('overlapping game audit identities')
    selected = {k:v for k,v in all_audit.items() if v['status']=='quarantined'}
    required = [s for s in base['sources'] if any(k.rsplit(':',1)[0]==s['file'] for k in selected)]
    if len(required) != 19 or len(selected) != 182:
        raise ValueError('fixed quarantine/source count changed')
    bound = bind_sources(base_dir, required, root)
    games = {}
    for s in required:
        parsed = read_games(bound[s['file']])
        if len(parsed) != s['games']:
            raise ValueError('raw game count changed')
        games[s['file']] = parsed
    raw = Path(fresh_inventory).read_bytes()
    if digest(raw) != FRESH_INVENTORY_SHA:
        raise ValueError('fresh inventory changed')
    fresh_rows = {r['fen']:r for line in raw.splitlines() if not (r:=json.loads(line))['historical']}
    fresh = set(fresh_rows)
    if len(fresh)!=11910:
        raise ValueError('fresh population changed')
    raw = Path(previous_inventory).read_bytes()
    if digest(raw) != PREVIOUS_INVENTORY_SHA:
        raise ValueError('previous eight-game inventory changed')
    union = defaultdict(dict)
    for line in raw.splitlines():
        r=json.loads(line)
        union[r['fen']].update({o['historical_game_key']:o['plies'] for o in r['owners']})
    previous_fens = set(union)
    previous_keys = {k for owners in union.values() for k in owners}
    if len(previous_keys)!=8 or previous_keys & set(selected):
        raise ValueError('previous scope overlaps selected base games')
    engine = checked_engine(Path(adapter).resolve())
    rows=[]
    base_possible=set()
    for key, baseline in sorted(selected.items()):
        filename,index=key.rsplit(':',1)
        game=games[filename][int(index)-1]
        try:
            validated_trajectory(game,engine)
        except PdnReplayError as error:
            if str(error)!=baseline['error']:
                raise ValueError('strict quarantine changed') from error
        else:
            raise ValueError('strict quarantine unexpectedly passed')
        row,visited=explore(game,engine)
        row['historical_game_key']=key
        row['public_game_id']=public_id(game)
        if not row['complete_board_frontier_replay']:
            row['unresolved_ply']=row['completed_plies']+1
            row['unresolved_token']=game.moves[row['completed_plies']]
        fens=set()
        for state,plies in visited.items():
            fen=canonical_fen(state_to_fen(state))
            fens.add(fen)
            union[fen][key]=sorted(plies)
        missing=fens-history
        row.update(possible_distinct_fens=len(fens),possible_fens_missing_from_cache=len(missing),
                   potential_fresh_overlap_fens=len(missing & fresh))
        base_possible |= fens
        rows.append(row)
    missing=set(union)-history
    overlap=sorted(missing & fresh)
    inventory=b''.join((json.dumps(dict(fen=f,historical=f in history,
        owners=[dict(historical_game_key=k,plies=v) for k,v in sorted(union[f].items())]),
        sort_keys=True,separators=(',',':'))+'\n').encode() for f in sorted(union))
    report=dict(schema='mtdp-historical-base-quarantine-frontier-v1',protocol_commit=PROTOCOL_COMMIT,
        historical_cache_sha256=CACHE_SHA256,base_member_sha256=MEMBERS,
        adapter_commit=cache['adapter_commit'],fresh_inventory_sha256=FRESH_INVENTORY_SHA,
        previous_eight_game_inventory_sha256=PREVIOUS_INVENTORY_SHA,raw_sources=required,
        selected_base_quarantines=len(rows),previous_quarantines_reused=8,
        total_known_historical_quarantines_examined=190,frontier_limit=MAX_FRONTIER,application_limit=MAX_APPLICATIONS,
        status_counts=dict(sorted(Counter(r['status'] for r in rows).items())),
        incomplete_base_game_keys=[r['historical_game_key'] for r in rows if not r['complete_board_frontier_replay']],
        all_selected_base_frontiers_complete=all(r['complete_board_frontier_replay'] for r in rows),
        base_possible_fens=len(base_possible),base_possible_fens_missing_from_cache=len(base_possible-history),
        combined_possible_historical_fens=len(union),combined_possible_fens_missing_from_cache=len(missing),
        previous_possible_fens=len(previous_fens),potential_fresh_overlap_fens=len(overlap),
        overlap_fen_sha256=[digest(f.encode()) for f in overlap],
        overlap_witnesses=[dict(fen=f,fen_sha256=digest(f.encode()),fresh_owners=fresh_rows[f]['owners'],
            historical_owners=[dict(historical_game_key=k,plies=v) for k,v in sorted(union[f].items())]) for f in overlap],
        games=rows,
        combined_inventory_bytes=len(inventory),combined_inventory_sha256=digest(inventory),
        strict_quarantines_retained=True,legacy_cache_changed=False,played_action_paths_certified=False,
        global_historical_registry_complete=False,independent_cohort_admitted=False,
        scientific_freeze=False,new_engine_scores_computed=False)
    return report,inventory


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','base-dir','adapter','fresh-inventory','previous-inventory','output','inventory'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    report,inventory=audit(a.root,a.base_dir,a.adapter,a.fresh_inventory,a.previous_inventory)
    with a.output.open('x') as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write('\n')
    with a.inventory.open('xb') as f:
        f.write(inventory)


if __name__=='__main__':
    main()
