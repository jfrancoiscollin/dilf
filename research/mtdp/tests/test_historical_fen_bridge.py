"""Representation and preflight wiring checks; no search or target scores."""
import hashlib
import os
from pathlib import Path

import pytest

from pedagogy.game import parse_fen
from research.mtdp.historical_fen_bridge import canonical_view, load_historical_fens, reject_historical_fen_overlap
from research.mtdp.prospective_source_preflight import preflight_sources

RAW = 'B:WK48,13,16:BK46,3,5'
CANONICAL = 'B:W13,16,K48:B3,5,K46'


def test_same_occupancy_is_rejected_despite_a_different_text_order():
    assert parse_fen(RAW) == parse_fen(CANONICAL)
    assert CANONICAL not in {RAW}
    view = canonical_view([RAW])
    with pytest.raises(ValueError, match='Historical canonical FEN overlap'):
        reject_historical_fen_overlap([{'fen': CANONICAL}], view)


def test_aliases_are_deduplicated_without_new_positions():
    view = canonical_view([RAW, CANONICAL])
    assert view['raw_distinct_fens'] == 2
    assert view['canonical_distinct_fens'] == 1
    assert view['representation_aliases_collapsed'] == 1


@pytest.mark.parametrize('fens', [[], ['W:W1,1:B2'], ['B:W51:B1']])
def test_empty_or_invalid_registry_is_rejected(fens):
    with pytest.raises(ValueError):
        canonical_view(fens)


def test_unverified_cache_cannot_be_used(tmp_path):
    path = tmp_path / 'fake-cache.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='cache digest mismatch'):
        load_historical_fens(path)


def test_unmatched_fen_is_only_a_screen_not_a_qualification():
    reject_historical_fen_overlap([{'fen': 'W:W32:B1'}], canonical_view([RAW]))


def test_real_pinned_cache_blocks_reordered_known_fen_before_any_rules_call(tmp_path):
    path = os.environ.get('MTDP_HISTORICAL_FEN_CACHE')
    if not path:
        if os.environ.get('MTDP_REQUIRE_HISTORICAL_FEN_CACHE') == '1':
            raise AssertionError('Required pinned historical FEN cache unavailable')
        pytest.skip('Dedicated historical workflow supplies the pinned cache')
    view = load_historical_fens(Path(path))
    witness = view['examples'][0]
    assert witness['canonical_string_in_raw_set'] is False
    raw = ('[Event "synthetic"]\n[FEN "' + witness['raw_fen'] + '"]\n*\n').encode()
    source = tmp_path / 'synthetic.pdn'
    source.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    gid = digest + ':1'
    rows = [{'game_id': gid, 'event_id': 'synthetic', 'tournament_id': 'synthetic',
             'split': 'train', 'ply': 0, 'fen': witness['canonical_fen'],
             'source_pdn_sha256': digest}]
    class NeverReplay:
        def legal_moves(self, state):
            raise AssertionError('Historical exclusion must precede replay')
    root = Path(__file__).resolve().parents[3]
    with pytest.raises(ValueError, match='Historical canonical FEN overlap'):
        preflight_sources(rows, {gid: source}, NeverReplay(), root=root, historical_cache=Path(path))
