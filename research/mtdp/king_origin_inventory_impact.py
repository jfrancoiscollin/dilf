"""Fixed complete two-inventory legality impact audit, no strategic scores."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from pedagogy.game import parse_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT,ADAPTER_COMMIT
from research.mtdp.king_origin_correction import corrected_engine
from research.mtdp.return_capture_oracle import root_key,parse_catalogues

PROTOCOL_COMMIT='42821e3182b5496c5010fdc2570757be9eee84a3'
INPUTS={
    'historical_quarantines':('df9b357d08b9d6005d8b1726cb2e049d7dd1971dbf25b6210c54d7d86f66b8a1',21645),
    'fresh_candidate':('62a71b82e09794ddd2bdc68d8c44749bf7741dddaee28a0722295a54abaac36e',12795),
}
BATCH_SIZE=1000


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def load_inventory(path,role):
    raw=Path(path).read_bytes()
    expected,count=INPUTS[role]
    if digest(raw)!=expected:
        raise ValueError('inventory digest changed: '+role)
    rows={}
    for line in raw.splitlines():
        row=json.loads(line)
        fen=row['fen']
        if canonical_fen(fen)!=fen or fen in rows:
            raise ValueError('noncanonical or duplicate inventory FEN')
        rows[fen]=row
    if len(rows)!=count:
        raise ValueError('fixed inventory population changed')
    return rows


def path_key(move):
    return move.path,tuple(sorted(move.captures)),bool(move.promotion)


def compare_actions(legacy,fixed,reference):
    old_paths=set(map(path_key,legacy)); new_paths=set(map(path_key,fixed))
    old_roots=set(map(root_key,legacy)); new_roots=set(map(root_key,fixed)); ref=set(reference)
    metrics=dict(legacy_paths=len(legacy),corrected_paths=len(fixed),
        legacy_unique_paths=len(old_paths),corrected_unique_paths=len(new_paths),
        legacy_roots=len(old_roots),corrected_roots=len(new_roots),jass_roots=len(ref),
        root_sets_changed=old_roots!=new_roots,path_sets_changed=old_paths!=new_paths,
        legacy_jass_mismatch=old_roots!=ref,corrected_jass_mismatch=new_roots!=ref,
        newly_introduced_jass_mismatch=old_roots==ref and new_roots!=ref,
        jass_duplicate_root_keys=len(reference)!=len(ref),
        added_root_count=len(new_roots-old_roots),removed_root_count=len(old_roots-new_roots),
        legacy_paths_sha256=digest(encoded(sorted(old_paths))),corrected_paths_sha256=digest(encoded(sorted(new_paths))),
        legacy_roots_sha256=digest(encoded(sorted(old_roots))),corrected_roots_sha256=digest(encoded(sorted(new_roots))),
        jass_roots_sha256=digest(encoded(sorted(ref))))
    witness=dict(added_roots=sorted(new_roots-old_roots),removed_roots=sorted(old_roots-new_roots),
        added_paths=sorted(new_paths-old_paths),removed_paths=sorted(old_paths-new_paths),
        legacy_only_vs_jass=sorted(old_roots-ref),jass_only_vs_legacy=sorted(ref-old_roots),
        corrected_only_vs_jass=sorted(new_roots-ref),jass_only_vs_corrected=sorted(ref-new_roots))
    return metrics,witness


METRICS=('root_sets_changed','path_sets_changed','legacy_jass_mismatch','corrected_jass_mismatch',
         'newly_introduced_jass_mismatch','jass_duplicate_root_keys')


def audit(historical,fresh,adapter,jass,executable):
    inputs={'historical_quarantines':load_inventory(historical,'historical_quarantines'),
            'fresh_candidate':load_inventory(fresh,'fresh_candidate')}
    fens=sorted(set().union(*(set(rows) for rows in inputs.values())))
    pinned_checkout(Path(jass).resolve(),JASS_COMMIT)
    legacy=checked_engine(Path(adapter).resolve())
    fixed,receipt=corrected_engine(adapter)
    if receipt['corrected_rules_sha256']!='4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d':
        raise ValueError('wrong corrected research engine identity')
    catalogues=[];raw_catalogue=bytearray()
    for start in range(0,len(fens),BATCH_SIZE):
        chunk=fens[start:start+BATCH_SIZE]
        process=subprocess.run([str(Path(executable).resolve())],input=''.join(f+'\n' for f in chunk),
            capture_output=True,text=True,check=True,timeout=30)
        catalogues.extend(parse_catalogues(process.stdout,chunk))
        raw_catalogue.extend(process.stdout.encode())
    summary=Counter();by_role={role:Counter() for role in inputs}
    ledger=bytearray();witnesses=bytearray()
    changed_owners={role:set() for role in inputs}
    for index,(fen,catalogue) in enumerate(zip(fens,catalogues,strict=True)):
        state=parse_fen(fen)
        old_moves=legacy.legal_moves(state);new_moves=fixed.legal_moves(state)
        metrics,witness=compare_actions(old_moves,new_moves,catalogue)
        active_king=bool(state.kings_of(state.turn))
        if not active_king and (metrics['path_sets_changed'] or metrics['root_sets_changed']):
            raise ValueError('unexpected change without active-side king')
        roles=sorted(role for role,rows in inputs.items() if fen in rows)
        summary['positions']+=1;summary['positions_with_active_king']+=active_king
        for metric in METRICS:summary[metric]+=metrics[metric]
        summary['path_only_changes']+=metrics['path_sets_changed'] and not metrics['root_sets_changed']
        summary['added_roots']+=metrics['added_root_count'];summary['removed_roots']+=metrics['removed_root_count']
        for role in roles:
            by_role[role]['positions']+=1
            for metric in METRICS:by_role[role][metric]+=metrics[metric]
            if metrics['path_sets_changed'] or metrics['root_sets_changed']:
                field='historical_game_key' if role=='historical_quarantines' else 'game_id'
                changed_owners[role].update(o[field] for o in inputs[role][fen]['owners'])
        ledger.extend(encoded(dict(index=index,fen_sha256=digest(fen.encode()),roles=roles,
            active_side_has_king=active_king,**metrics)))
        if metrics['path_sets_changed'] or metrics['legacy_jass_mismatch'] or metrics['corrected_jass_mismatch']:
            owners={role:inputs[role][fen]['owners'] for role in roles}
            witnesses.extend(encoded(dict(fen=fen,owners=owners,**metrics,**witness)))
        if (index+1)%5000==0 or index+1==len(fens):
            print(f'Compared {index+1}/{len(fens)} positions',flush=True)
    report=dict(schema='mtdp-king-origin-v1-two-inventory-impact-v1',protocol_commit=PROTOCOL_COMMIT,
        inputs={role:dict(sha256=sha,distinct_fens=n) for role,(sha,n) in INPUTS.items()},
        adapter_base_commit=ADAPTER_COMMIT,jass_commit=JASS_COMMIT,**receipt,
        jass_batch_size=BATCH_SIZE,summary=dict(sorted(summary.items())),
        by_role={role:dict(sorted(counts.items())) for role,counts in sorted(by_role.items())},
        changed_position_owners={role:sorted(values) for role,values in sorted(changed_owners.items())},
        position_ledger_sha256=digest(ledger),position_ledger_bytes=len(ledger),
        witnesses_sha256=digest(witnesses),witnesses_bytes=len(witnesses),
        raw_catalogue_sha256=digest(raw_catalogue),raw_catalogue_bytes=len(raw_catalogue),
        no_active_king_changes=0,default_rules_or_cache_changed=False,
        corrected_whole_game_replay_performed=False,global_historical_impact_audited=False,
        engine_scores_computed=False,signatures_computed=False,independent_cohort_admitted=False,scientific_freeze=False)
    provenance=dict(catalogue_binary_sha256=digest(Path(executable).read_bytes()),
        adapter_base_commit=ADAPTER_COMMIT,jass_commit=JASS_COMMIT,**receipt)
    return report,bytes(ledger),bytes(witnesses),bytes(raw_catalogue),provenance


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('historical','fresh','adapter','jass','executable','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.output_dir.mkdir(exist_ok=False)
    report,ledger,witnesses,raw,receipt=audit(a.historical,a.fresh,a.adapter,a.jass,a.executable)
    for name,data in [('king-origin-impact.json',report),('provenance.json',receipt)]:
        (a.output_dir/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for name,data in [('position-ledger.jsonl',ledger),('change-witnesses.jsonl',witnesses),('jass-catalogues.txt',raw)]:
        (a.output_dir/name).write_bytes(data)


if __name__=='__main__':main()
