"""Fixed eight-board regression of explicit corrected rules against pinned Jass."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from pedagogy.game import GameState,parse_fen,state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.draught_master_adapter import create_engine
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT,ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.return_capture_oracle import CASES,root_key,decode_key,parse_catalogues

PROTOCOL_COMMIT='9dabb118dce1ce144bd94c2833ef6fd438eeaa62'


def rotate_swap(state):
    flip=lambda squares:frozenset(51-s for s in squares)
    return GameState(white_men=flip(state.black_men),white_kings=flip(state.black_kings),
        black_men=flip(state.white_men),black_kings=flip(state.white_kings),
        turn='black' if state.turn=='white' else 'white')


def cases():
    originals=list(CASES[:2])
    rotated=[(name+'-rotated',state_to_fen(rotate_swap(parse_fen(fen))),
        f'{51-int(token.split("x")[0])}x{51-int(token.split("x")[1])}') for name,fen,token in originals]
    return originals+rotated+[CASES[-1],
        ('man-loop','W:W20,26,28,32,33,38,39,43:B8,11,13,14,16,17,19,23,24,36','20x20'),
        ('quiet-king','W:WK28:B1',None),('other-friendly-blocker','W:WK3,14:B9,17,27,28',None)]


def roots(engine,state):
    return set(map(root_key,engine.legal_moves(state)))


def audit(adapter,jass,executable):
    legacy=checked_engine(Path(adapter).resolve())
    original_module=sys.modules['backend.game_engine']
    original_bytes=Path(legacy._rules.__file__).read_bytes()
    selected=cases()
    states=[parse_fen(f) for _,f,_ in selected]
    old=[roots(legacy,s) for s in states]
    fixed,receipt=corrected_engine(adapter)
    if fixed._rules is original_module or create_engine()._rules is not original_module:
        raise ValueError('default module isolation failed')
    pinned_checkout(Path(jass).resolve(),JASS_COMMIT)
    process=subprocess.run([str(Path(executable).resolve())],input=''.join(state_to_fen(s)+'\n' for s in states),
        capture_output=True,text=True,check=True,timeout=30)
    catalogues=parse_catalogues(process.stdout,[state_to_fen(s) for s in states])
    rows=[]
    for (name,fen,token),state,baseline,catalogue in zip(selected,states,old,catalogues,strict=True):
        moves=sorted(fixed.legal_moves(state),key=lambda m:(m.path,tuple(sorted(m.captures)),m.promotion))
        current=set(map(root_key,moves))
        reference=set(catalogue)
        row=dict(case=name,fen=canonical_fen(fen),token=token,
            legacy_roots=[list(a) for a in sorted(baseline)],corrected_roots=[list(a) for a in sorted(current)],
            jass_roots=[list(a) for a in sorted(reference)],corrected_matches_jass=current==reference,
            changed_from_legacy=current!=baseline,
            corrected_paths=[dict(path=list(m.path),captures=sorted(m.captures),promotion=m.promotion) for m in moves])
        if token is not None:
            row.update(corrected_token_matching_paths=sum(decode_key(root_key(m)[0])==token for m in moves))
            if not row['corrected_token_matching_paths']:
                raise ValueError('predeclared return-token regression failed: '+name)
        rows.append(row)
    if not all(r['corrected_matches_jass'] for r in rows):
        raise ValueError('fixed eight-board catalogue gate failed')
    if any(rows[i]['changed_from_legacy'] for i in (4,5)):
        raise ValueError('initial/man-only control changed')
    if Path(legacy._rules.__file__).read_bytes()!=original_bytes or old!=[roots(legacy,s) for s in states]:
        raise ValueError('legacy source or behavior was mutated')
    report=dict(schema='mtdp-king-origin-v1-eight-board-regression',protocol_commit=PROTOCOL_COMMIT,
        adapter_base_commit=ADAPTER_COMMIT,jass_commit=JASS_COMMIT,**receipt,cases=rows,
        boards=len(rows),all_corrected_root_sets_match_jass=True,legacy_behavior_retained=True,
        raw_catalogue_sha256=digest(process.stdout.encode()),
        search_or_scores_computed=False,historical_cache_changed=False,historical_quarantines_changed=False,
        corpus_impact_audited=False,independent_cohort_admitted=False,scientific_freeze=False)
    provenance=dict(catalogue_binary_sha256=digest(Path(executable).read_bytes()),
        adapter_base_commit=ADAPTER_COMMIT,jass_commit=JASS_COMMIT,**receipt)
    return report,provenance,process.stdout


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('adapter','jass','executable','output','provenance','raw-catalogue'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    report,receipt,raw=audit(a.adapter,a.jass,a.executable)
    for path,data in ((a.output,report),(a.provenance,receipt)):
        with path.open('x') as f:
            json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
    with a.raw_catalogue.open('x') as f:f.write(raw)


if __name__=='__main__':
    main()
