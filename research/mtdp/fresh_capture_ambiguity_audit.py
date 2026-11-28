"""Diagnostic only: enumerate the first unresolved action of quarantined games.

No resolution rule, suffix reconstruction, admission, target selection or scores.
The frozen strict resolver is used for every prefix and remains unchanged.
"""
import argparse
import json
from pathlib import Path
import re

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import verify_archive, digest, ARCHIVE_SHA, EVENT
from research.mtdp.historical_alias_gate import public_id
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_cohort import ADAPTER_COMMIT
from research.mtdp.pdn import _resolve, PdnReplayError
from research.mtdp.pdn_strict import parse_games_strict

REPLAY_SHA = 'a69de36bd4618e0c5948c54b05f17d9f9e500a11c85ad24783f831bb085eb13a'
QUARANTINED = (9, 22, 24, 75, 135, 146, 151)


def matching_actions(state, token, engine):
    # Mirror the frozen notation contract; enumerate, never choose a path.
    squares = tuple(map(int, re.findall(r'\d+', token)))
    if len(squares) < 2 or any(not 1 <= s <= 50 for s in squares):
        raise ValueError('invalid move token')
    capture = 'x' in token.lower()
    return sorted((m for m in engine.legal_moves(state)
                   if m.from_square == squares[0] and m.to_square == squares[-1]
                   and m.is_capture == capture
                   and (len(squares) == 2 or m.path == squares)),
                  key=lambda m: (m.path, tuple(sorted(m.captures)), m.promotion))


def diagnose_game(game, engine):
    state = parse_fen(game.tags['FEN']) if 'FEN' in game.tags else initial_state()
    for ply, token in enumerate(game.moves, 1):
        try:
            move = _resolve(state, token, engine)
        except PdnReplayError as error:
            candidates = matching_actions(state, token, engine)
            if len(candidates) < 2:
                raise ValueError('expected a multi-action ambiguity') from error
            rows = [dict(path=list(m.path), captures=sorted(m.captures), promotion=m.promotion,
                         successor_fen=canonical_fen(state_to_fen(engine.apply_move(state, m))))
                    for m in candidates]
            successors = sorted({r['successor_fen'] for r in rows})
            return dict(source_game_index=game.index, public_game_id=public_id(game),
                        first_unresolved_ply=ply, original_token=token,
                        prefix_fen=canonical_fen(state_to_fen(state)), actions=rows,
                        matching_actions=len(rows), distinct_successors=len(successors),
                        same_successor=len(successors) == 1,
                        suffix_replayed=False, remains_quarantined=True)
        state = engine.apply_move(state, move)
    raise ValueError('expected quarantined game, found complete strict replay')


def audit(archive, baseline, adapter):
    raw = Path(baseline).read_bytes()
    if digest(raw) != REPLAY_SHA:
        raise ValueError('strict replay baseline digest mismatch')
    original = json.loads(raw)
    _, _, pdn = verify_archive(archive)
    games = parse_games_strict(pdn.decode('utf-8-sig'))
    excluded = [r for r in original['games'] if not r['complete_legal_replay']]
    if tuple(r['source_game_index'] for r in excluded) != QUARANTINED:
        raise ValueError('quarantine set changed')
    engine = checked_engine(Path(adapter).resolve())
    rows = []
    for prior in excluded:
        game = games[prior['source_game_index'] - 1]
        if public_id(game) != prior['public_game_id']:
            raise ValueError('quarantine identity mismatch')
        rows.append(diagnose_game(game, engine))
    return dict(schema='mtdp-fresh-first-capture-ambiguity-v1', event=EVENT,
                intake_zip_sha256=ARCHIVE_SHA, strict_replay_sha256=REPLAY_SHA,
                adapter_commit=ADAPTER_COMMIT, games=rows, quarantined_games=len(rows),
                same_successor_games=sum(r['same_successor'] for r in rows),
                divergent_successor_games=sum(not r['same_successor'] for r in rows),
                resolution_rule_changed=False, independent_cohort_admitted=False,
                scientific_freeze=False, target_positions_selected=False,
                new_engine_scores_computed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'baseline', 'adapter', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    report = audit(a.archive, a.baseline, a.adapter)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
