"""Transport validation only; tests never perform HTTP requests."""
import pytest

from research.mtdp.reserved_endpoint_verification import verify_response
from research.mtdp.reserved_source_inventory import sha

RAW = b'[Event "synthetic"]\n1. 32-28 *\n'
EVENT = {'reserved_event_id': 'Synthetic', 'bytes': len(RAW),
         'pdn_sha256': sha(RAW), 'games': [{'game_id': 'synthetic'}]}
URL = 'https://lidraughts.org/api/tournament/Synthetic/games'


def test_response_binds_expected_public_endpoint_to_exact_pdn_bytes():
    result = verify_response(EVENT, RAW, 200, URL)
    assert result['byte_equal_to_pinned_archive']
    assert result['pdn_sha256'] == sha(RAW)
    assert result['archived_games'] == 1


@pytest.mark.parametrize('raw,status,url', [
    (RAW, 429, URL),
    (RAW, 200, URL.replace('/Synthetic/', '/Other/')),
    (RAW, 200, URL.replace('https://', 'http://')),
    (RAW + b'\n', 200, URL),
    (RAW[:-1], 200, URL),
    (RAW.replace(b'32-28', b'31-27'), 200, URL),
])
def test_changed_status_endpoint_or_pdn_is_rejected(raw, status, url):
    with pytest.raises(ValueError):
        verify_response(EVENT, raw, status, url)
