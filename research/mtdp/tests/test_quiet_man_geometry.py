"""Adversarial geometry checks for the conditional quiet-man signature.

The key is only permitted when the mover has no king and no immediate
capture. It must detect captures in both directions under FMJD rules.
"""
from research.mtdp.signature_ablation import _COORDS, _SQUARE_AT, _quiet_man_key


def _three_square_diagonal():
    for origin, (row, col) in sorted(_COORDS.items()):
        for dr in (-1, 1):
            for dc in (-1, 1):
                middle = _SQUARE_AT.get((row + dr, col + dc))
                landing = _SQUARE_AT.get((row + 2 * dr, col + 2 * dc))
                if middle is not None and landing is not None:
                    yield origin, middle, landing, dr


def test_detects_backward_man_capture():
    origin, middle, landing, _ = next(
        (a, b, c, dr) for a, b, c, dr in _three_square_diagonal() if dr == 1
    )
    assert _quiet_man_key("white", frozenset({origin}),
                          frozenset({middle})) is None


def test_occupied_landing_prevents_capture():
    origin, middle, landing, _ = next(_three_square_diagonal())
    result = _quiet_man_key(
        "white", frozenset({origin, landing}), frozenset({middle})
    )
    assert result is not None


def test_enemy_piece_not_capturable_when_no_landing():
    origin, middle, landing, _ = next(_three_square_diagonal())
    # The opponent on the landing square does not create a jump unless
    # an opponent also occupies the adjacent square.
    result = _quiet_man_key("white", frozenset({origin}),
                            frozenset({landing}))
    assert result is not None


def test_empty_mover():
    assert _quiet_man_key("black", frozenset(), frozenset({1})) == (
        "black", frozenset(), frozenset()
    )
