"""Score-blind exact-position footprint; descriptive, never cohort admission."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from pedagogy.game import state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import verify_archive, digest, ARCHIVE_SHA, EVENT
from research.mtdp.fresh_capture_ambiguity_audit import REPLAY_SHA
from research.mtdp.historical_fen_bridge import load_verified_cache, CACHE_SHA256
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine, trajectory_fingerprint
from research.mtdp.pdn import validated_trajectory, PdnReplayError
from research.mtdp.pdn_strict import parse_games_strict


def footprint(trajectories, historical):
    """Count occurrences and unique boards separately; cluster shared novel FENs.

    A component is only a lower bound on dependence visible via exact FENs.
    Singletons are NOT proof of independence (openings, players, event remain).
    """
    by_fen = defaultdict(lambda: defaultdict(list))
    for identity, fens in sorted(trajectories.items()):
        for ply, fen in enumerate(fens):
            by_fen[fen][identity].append(ply)
    groups = {identity: {identity} for identity in trajectories}
    shared = []
    rows = []
    for fen, owners in sorted(by_fen.items()):
        known = fen in historical
        row = dict(fen=fen, fen_sha256=digest(fen.encode()), historical=known,
                   owners=[dict(game_id=g, plies=plies) for g, plies in sorted(owners.items())])
        rows.append(row)
        if not known and len(owners) > 1:
            combined = set().union(*(groups[g] for g in owners))
            for g in combined:
                groups[g] = combined
            shared.append(dict(fen_sha256=row['fen_sha256'], game_ids=sorted(owners),
                               occurrences=sum(map(len, owners.values()))))
    components = sorted({tuple(sorted(g)) for g in groups.values()})
    payload = b''.join((json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n').encode() for r in rows)
    novel_owners = {g for fen, owners in by_fen.items() if fen not in historical for g in owners}
    summary = dict(games_with_nonhistorical_fens=len(novel_owners),
                   games_without_nonhistorical_fens=sorted(set(trajectories) - novel_owners),
                   novel_fen_components_with_observations=sum(bool(set(c) & novel_owners) for c in components),
                   complete_games=len(trajectories), position_occurrences=sum(map(len, trajectories.values())),
                   distinct_fens=len(rows), historical_distinct_fens=sum(r['historical'] for r in rows),
                   nonhistorical_distinct_fens=sum(not r['historical'] for r in rows),
                   historical_occurrences=sum(sum(len(o['plies']) for o in r['owners']) for r in rows if r['historical']),
                   nonhistorical_occurrences=sum(sum(len(o['plies']) for o in r['owners']) for r in rows if not r['historical']),
                   repeated_within_game_occurrences=sum(len(o['plies']) - 1 for r in rows for o in r['owners']),
                   nonhistorical_cross_game_shared_fens=len(shared),
                   shared_nonhistorical_fens=shared,
                   nonhistorical_exact_fen_game_components=[list(c) for c in components],
                   exact_fen_component_count=len(components),
                   components_with_multiple_games=sum(len(c) > 1 for c in components),
                   largest_component_games=max(map(len, components), default=0),
                   inventory_jsonl_sha256=digest(payload), inventory_jsonl_bytes=len(payload))
    return summary, payload


def audit(archive, baseline, cache, adapter):
    raw = Path(baseline).read_bytes()
    if digest(raw) != REPLAY_SHA:
        raise ValueError('strict baseline changed')
    expected = json.loads(raw)
    _, _, pdn = verify_archive(archive)
    known = load_verified_cache(cache)
    historical = {canonical_fen(f) for f in known['confirmed_fens']}
    engine = checked_engine(Path(adapter).resolve())
    trajectories = {}
    trajectory_owners = defaultdict(list)
    for game, previous in zip(parse_games_strict(pdn.decode('utf-8-sig')), expected['games'], strict=True):
        identity = public_id(game)
        if identity != previous['public_game_id'] or game.index != previous['source_game_index']:
            raise ValueError('game identity mismatch')
        # Re-establish exactly the original strict complete-game population.
        try:
            result = validated_trajectory(game, engine)
        except PdnReplayError as error:
            if previous['complete_legal_replay'] or str(error) != previous['quarantine_reason']:
                raise ValueError('strict quarantine changed') from error
            continue
        fingerprint = trajectory_fingerprint(result)
        if not previous['complete_legal_replay'] or fingerprint != previous['trajectory_sha256']:
            raise ValueError('strict trajectory changed')
        trajectories[identity] = [canonical_fen(state_to_fen(s)) for _, _, s in result]
        trajectory_owners[fingerprint].append(identity)
    summary, payload = footprint(trajectories, historical)
    if (summary['complete_games'] != expected['complete_legal_games']
            or summary['historical_occurrences'] != sum(r.get('historical_position_occurrences', 0) for r in expected['games'])
            or summary['nonhistorical_occurrences'] != sum(r.get('nonhistorical_position_occurrences', 0) for r in expected['games'])):
        raise ValueError('original complete-population accounting mismatch')
    return dict(schema='mtdp-fresh-exact-position-footprint-v1', event=EVENT,
                intake_zip_sha256=ARCHIVE_SHA, strict_replay_sha256=REPLAY_SHA,
                historical_cache_sha256=CACHE_SHA256, adapter_commit=known['adapter_commit'],
                distinct_complete_trajectory_hashes=len(trajectory_owners),
                duplicate_complete_trajectory_groups=[dict(trajectory_sha256=k, game_ids=sorted(v))
                    for k, v in sorted(trajectory_owners.items()) if len(v) > 1],
                **summary, independent_cohort_admitted=False, scientific_freeze=False,
                partitions_selected=False, target_positions_selected=False, new_engine_scores_computed=False,
                complete_historical_registry_proven=False,
                scope='all original 145 complete games; seven quarantines excluded; no game representative selected'), payload


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'baseline', 'cache', 'adapter', 'output', 'inventory'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    report, inventory = audit(a.archive, a.baseline, a.cache, a.adapter)
    with a.output.open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    with a.inventory.open('xb') as f:
        f.write(inventory)


if __name__ == '__main__':
    main()
