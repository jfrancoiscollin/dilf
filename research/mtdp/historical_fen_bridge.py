"""H13 read-only FEN view bridging legacy cache order to D1 canonical syntax.

Never rewrite the byte-pinned cache or its trajectory hashes. Canonicalization
here is occupancy syntax, not legality, independence or a new cohort freeze.
"""
import argparse
import hashlib
import json
from pathlib import Path

from research.mtdp.decision_equivalence.fmjd_fen import canonical_fen

CACHE_SHA256 = '5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7'


def canonical_view(fens):
    if not isinstance(fens, (list, tuple, set, frozenset)) or not fens:
        raise ValueError('Nonempty historical FEN registry required')
    raw = set(fens)
    canonical, changed, missing, examples = set(), 0, 0, []
    for fen in sorted(raw):
        value = canonical_fen(fen)
        canonical.add(value)
        if value != fen:
            changed += 1
            absent = value not in raw
            missing += absent
            if len(examples) < 3:
                examples.append({'raw_fen': fen, 'canonical_fen': value,
                                 'canonical_string_in_raw_set': not absent})
    return {'canonical_fens': frozenset(canonical), 'raw_distinct_fens': len(raw),
            'canonical_distinct_fens': len(canonical), 'format_changed_fens': changed,
            'changed_canonical_strings_absent_from_raw_set': missing,
            'representation_aliases_collapsed': len(raw) - len(canonical),
            'canonical_fen_set_sha256': hashlib.sha256('\n'.join(sorted(canonical)).encode()).hexdigest(),
            'examples': examples}


def load_historical_fens(cache_path):
    raw = Path(cache_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CACHE_SHA256:
        raise ValueError('Historical cache digest mismatch')
    cache = json.loads(raw)
    if cache['adapter_commit'] != '0e5189fbb251bf5eaf2e613d0f878bb17c740311':
        raise ValueError('Historical rules engine revision changed')
    view = canonical_view(cache['confirmed_fens'])
    if view['raw_distinct_fens'] != cache['accounting']['confirmed_prefix_fens']:
        raise ValueError('Historical FEN denominator changed')
    return {**view, 'historical_cache_sha256': CACHE_SHA256}


def reject_historical_fen_overlap(rows, view):
    for row in rows:
        if canonical_fen(row['fen']) in view['canonical_fens']:
            raise ValueError('Historical canonical FEN overlap: reject prospective batch')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    view = load_historical_fens(a.cache)
    result = {k: v for k, v in view.items() if k != 'canonical_fens'}
    result.update({'schema': 'mtdp-h13-historical-fen-representation-bridge-v1',
                   'cache_bytes_modified': False, 'trajectory_hashes_redefined': False,
                   'independent_cohort_qualified': False,
                   'complete_historical_exclusion_registry': False,
                   'scientific_freeze': False, 'new_reference_scores_acquired': False})
    with a.output.open('xb') as out:
        out.write((json.dumps(result, sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({k: result[k] for k in ('raw_distinct_fens', 'canonical_distinct_fens',
                      'format_changed_fens', 'changed_canonical_strings_absent_from_raw_set')}))


if __name__ == '__main__':
    main()
