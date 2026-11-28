"""Bounded all-action historical board frontier; never resolve played paths."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_capture_ambiguity_audit import matching_actions
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.historical_fen_bridge import load_verified_cache, CACHE_SHA256
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.pdn import read_games, validated_trajectory, PdnReplayError

PROTOCOL_COMMIT = 'a5c1a8853d242688e66e2afad4c6549b2fcdff6b'
MAX_FRONTIER = 128
MAX_APPLICATIONS = 100000
FRESH_INVENTORY_SHA = '62a71b82e09794ddd2bdc68d8c44749bf7741dddaee28a0722295a54abaac36e'


def explore(game, engine, *, frontier_limit=MAX_FRONTIER, action_limit=MAX_APPLICATIONS):
    start = parse_fen(game.tags['FEN']) if 'FEN' in game.tags else initial_state()
    frontier = {start}
    visited = defaultdict(set)
    visited[start].add(0)
    applications = 0
    maximum = 1
    ambiguous = []
    single = True
    status = 'complete_board_frontier'
    finished = 0
    for ply, token in enumerate(game.moves, 1):
        following = set()
        for state in sorted(frontier, key=state_to_fen):
            actions = matching_actions(state, token, engine)
            successors = set()
            for move in actions:
                if applications >= action_limit:
                    status = 'application_cap'
                    break
                successor = engine.apply_move(state, move)
                applications += 1
                following.add(successor)
                successors.add(successor)
                visited[successor].add(ply)
                if len(following) > frontier_limit:
                    status = 'frontier_cap'
                    break
            if len(actions) > 1:
                ambiguous.append(dict(ply=ply, token=token, matching_actions=len(actions),
                                      enumerated_successor_boards=len(successors)))
            if status != 'complete_board_frontier':
                break
        maximum = max(maximum, len(following))
        if status != 'complete_board_frontier':
            break
        if not following:
            status = 'zero_frontier'
            break
        single = single and len(following) == 1
        frontier = following
        finished = ply
    return dict(status=status, complete_board_frontier_replay=status == 'complete_board_frontier',
                completed_plies=finished, source_plies=len(game.moves),
                matching_action_applications=applications, maximum_frontier=maximum,
                every_completed_ply_single_board=single, ambiguities=ambiguous,
                strict_action_quarantine_retained=True), visited


def audit(root, cache_path, adapter, fresh_inventory):
    root = Path(root)
    cache = load_verified_cache(cache_path)
    raw = Path(fresh_inventory).read_bytes()
    if digest(raw) != FRESH_INVENTORY_SHA:
        raise ValueError('fresh footprint inventory changed')
    fresh = {r['fen'] for line in raw.splitlines() if not (r := json.loads(line))['historical']}
    if len(fresh) != 11910:
        raise ValueError('fresh footprint population changed')
    historical = {canonical_fen(f) for f in cache['confirmed_fens']}
    selected = {k: v for k, v in cache['extension_game_audit'].items() if v['status'] == 'quarantined'}
    if len(selected) != 8 or {s['event_id'] for s in cache['closed_event_sources']} != {'s7ahYqL4', 'D9PF2OSW'}:
        raise ValueError('fixed historical scope changed')
    engine = checked_engine(Path(adapter).resolve())
    sources = {}
    for source in cache['closed_event_sources']:
        path = root / source['path']
        if digest(path.read_bytes()) != source['sha256']:
            raise ValueError('historical PDN changed')
        games = read_games(path)
        if len(games) != source['games']:
            raise ValueError('historical game count changed')
        sources[source['event_id']] = games
    rows = []
    possible = defaultdict(lambda: defaultdict(list))
    for key, baseline in sorted(selected.items()):
        filename, index = key.rsplit(':', 1)
        event = filename[len('mtdp-lidraughts-'):-len('.pdn')]
        game = sources[event][int(index) - 1]
        try:
            validated_trajectory(game, engine)
        except PdnReplayError as error:
            if str(error) != baseline['error']:
                raise ValueError('strict quarantine reason changed') from error
        else:
            raise ValueError('historical quarantine unexpectedly passed strict resolver')
        row, visited = explore(game, engine)
        row['historical_game_key'] = key
        fens = set()
        for state, plies in visited.items():
            fen = canonical_fen(state_to_fen(state))
            fens.add(fen)
            possible[fen][key] = sorted(plies)
        missing = fens - historical
        row.update(possible_distinct_fens=len(fens), possible_fens_missing_from_cache=len(missing),
                   potential_fresh_overlap_fens=len(missing & fresh))
        rows.append(row)
    possible_missing = set(possible) - historical
    inventory = b''.join((json.dumps(dict(fen=f, historical=f in historical,
        owners=[dict(historical_game_key=k, plies=v) for k, v in sorted(possible[f].items())]),
        sort_keys=True, separators=(',', ':')) + '\n').encode() for f in sorted(possible))
    overlaps = sorted(possible_missing & fresh)
    report = dict(schema='mtdp-historical-quarantine-board-frontier-v1',
        protocol_commit=PROTOCOL_COMMIT, historical_cache_sha256=CACHE_SHA256, fresh_inventory_sha256=FRESH_INVENTORY_SHA,
        adapter_commit=cache['adapter_commit'], frontier_limit=MAX_FRONTIER, application_limit=MAX_APPLICATIONS,
        games=rows, selected_historical_quarantines=len(rows),
        complete_board_frontier_games=sum(r['complete_board_frontier_replay'] for r in rows),
        possible_historical_fens=len(possible), possible_fens_missing_from_cache=len(possible_missing),
        potential_fresh_overlap_fens=len(overlaps),
        overlap_fen_sha256=[digest(f.encode()) for f in overlaps],
        possible_inventory_sha256=digest(inventory), possible_inventory_bytes=len(inventory),
        other_historical_quarantines_out_of_scope=182, legacy_cache_changed=False,
        strict_action_quarantines_retained=True, full_played_action_trajectories_certified=False,
        complete_historical_registry_proven=False, independent_cohort_admitted=False,
        scientific_freeze=False, new_engine_scores_computed=False)
    return report, inventory


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'cache', 'adapter', 'fresh-inventory', 'output', 'inventory'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    report, inventory = audit(a.root, a.cache, a.adapter, a.fresh_inventory)
    with a.output.open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    with a.inventory.open('xb') as f:
        f.write(inventory)


if __name__ == '__main__':
    main()
