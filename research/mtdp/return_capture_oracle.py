"""Pinned three-board legal catalogue comparison; no evaluation or search."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from pedagogy.game import initial_state, parse_fen, state_to_fen
from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen
from research.mtdp.fresh_candidate_integrity_replay import digest
from research.mtdp.jass_benchmark.named_arena_replay import checked_engine
from research.mtdp.jass_benchmark.candidate_jass_catalogue import pinned_checkout
from research.mtdp.jass_cohort import JASS_COMMIT, ADAPTER_COMMIT

PROTOCOL_COMMIT='ad904dcaa4353515948a8d9f8b4001fedefe6fa3'
BASELINE_SHA='d4e28965b4df6a943e844457d29bb91a2b05f00abd2a316ee02595c6a3cd0177'
CASES=(
    ('CARZrQpl:1285','B:W15,20,22,39,K42,45:B5,K48','48x48'),
    ('CARZrQpl:382','W:WK3,24,25,35,36,37,38:B9,15,17,20,22,27,28','3x3'),
    ('initial-control',state_to_fen(initial_state()),None),
)


def root_key(move):
    key=f'{move.from_square}{"x" if move.is_capture else "-"}{move.to_square}'
    if move.is_capture:
        key+=''.join('x'+str(s) for s in sorted(move.captures))
    return key, bool(move.promotion)


def decode_key(key):
    if not re.fullmatch(r'\d+[-x]\d+(?:x\d+)*',key):
        raise ValueError('malformed root key')
    numbers=list(map(int,re.findall(r'\d+',key)))
    if any(not 1<=n<=50 for n in numbers):
        raise ValueError('root square outside board')
    capture='-' not in key
    if (capture and len(numbers)<3) or (not capture and len(numbers)!=2):
        raise ValueError('root captures missing or quiet action malformed')
    return f'{numbers[0]}{"x" if capture else "-"}{numbers[1]}'


def parse_catalogues(raw,fens):
    lines=raw.splitlines()
    if len(lines)!=len(fens):
        raise ValueError('incomplete catalogue rows')
    output=[]
    for line,fen in zip(lines,fens,strict=True):
        echoed,*fields=line.split('\t')
        if parse_fen(echoed)!=parse_fen(fen):
            raise ValueError('catalogue echoed wrong board')
        rows=[]
        for field in fields:
            key,separator,promotion=field.partition('=')
            if not separator or promotion not in ('0','1'):
                raise ValueError('invalid catalogue field')
            decode_key(key)
            rows.append((key,promotion=='1'))
        output.append(rows)
    return output


def audit(root,adapter,jass,executable):
    root=Path(root)
    raw=(root/'research/mtdp/validation/historical-base-quarantine-frontier-2026-11-26.json').read_bytes()
    if digest(raw)!=BASELINE_SHA:
        raise ValueError('two-state provenance baseline changed')
    pinned_checkout(Path(jass).resolve(),JASS_COMMIT)
    engine=checked_engine(Path(adapter).resolve())
    fens=[fen for _,fen,_ in CASES]
    process=subprocess.run([str(Path(executable).resolve())],input=''.join(f+'\n' for f in fens),
                           capture_output=True,text=True,check=True,timeout=30)
    catalogues=parse_catalogues(process.stdout,fens)
    rows=[]
    for (identity,fen,token),catalogue in zip(CASES,catalogues,strict=True):
        moves=sorted(engine.legal_moves(parse_fen(fen)),key=lambda m:(m.path,tuple(sorted(m.captures)),m.promotion))
        python_roots=set(map(root_key,moves))
        jass_roots=set(catalogue)
        row=dict(case=identity,fen=canonical_fen(fen),original_token=token,
            python_actions=[dict(path=list(m.path),captures=sorted(m.captures),promotion=m.promotion) for m in moves],
            python_root_actions=[list(a) for a in sorted(python_roots)],
            jass_root_actions=[list(a) for a in sorted(jass_roots)],
            python_legal_paths=len(moves),python_unique_root_actions=len(python_roots),
            jass_exported_roots=len(catalogue),jass_unique_root_actions=len(jass_roots),
            root_action_sets_equal=python_roots==jass_roots,
            python_only_root_actions=[list(a) for a in sorted(python_roots-jass_roots)],
            jass_only_root_actions=[list(a) for a in sorted(jass_roots-python_roots)])
        if token is not None:
            row.update(python_token_matching_paths=sum(decode_key(root_key(m)[0])==token for m in moves),
                       jass_token_matching_roots=sum(decode_key(k)==token for k,_ in jass_roots))
        rows.append(row)
    if not rows[-1]['root_action_sets_equal']:
        raise ValueError('initial-position engineering control failed')
    report=dict(schema='mtdp-two-return-capture-legal-oracle-v1',protocol_commit=PROTOCOL_COMMIT,
        baseline_sha256=BASELINE_SHA,jass_commit=JASS_COMMIT,adapter_commit=ADAPTER_COMMIT,
        adapter_rules_sha256=digest(Path(engine._rules.__file__).read_bytes()),
        jass_movegen_sha256=digest((Path(jass)/'src/movegen.cpp').read_bytes()),
        catalogue_exporter_sha256=digest((root/'research/mtdp/jass_preflight/legal_catalogue.cpp').read_bytes()),
        root_key_helper_sha256=digest((root/'research/mtdp/jass_preflight/move_key.hpp').read_bytes()),
        raw_jass_stdout_sha256=digest(process.stdout.encode()),cases=rows,
        root_identity='endpoints+sorted captured squares+promotion; not landing path identity',
        engine_scores_computed=False,search_executed=False,legacy_rules_changed=False,
        historical_quarantines_retained=True,independent_cohort_admitted=False,scientific_freeze=False)
    provenance=dict(protocol_commit=PROTOCOL_COMMIT,jass_commit=JASS_COMMIT,adapter_commit=ADAPTER_COMMIT,
                    catalogue_binary_sha256=digest(Path(executable).read_bytes()),
                    raw_stdout_sha256=report['raw_jass_stdout_sha256'])
    return report,provenance,process.stdout


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','adapter','jass','executable','output','provenance','raw-catalogue'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    report,provenance,raw=audit(a.root,a.adapter,a.jass,a.executable)
    for path,data in ((a.output,report),(a.provenance,provenance)):
        with path.open('x') as f:
            json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
    with a.raw_catalogue.open('x') as f:
        f.write(raw)


if __name__=='__main__':
    main()
