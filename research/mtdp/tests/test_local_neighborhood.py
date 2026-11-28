from pedagogy.game import parse_fen
from research.mtdp.local_neighborhood import typed_radius_two


def test_typed_backward_neighbor_and_own_blocker():
    pawn = typed_radius_two(parse_fen("W:W32,41:B37"))
    king = typed_radius_two(parse_fen("W:W32,41:BK37"))

    assert pawn[1] == king[1]
    assert pawn != king
    origins = dict(king[2])
    assert tuple(origins) == (32, 41)
    assert (1, -1, 1, "enemy_king") in origins[32]
    assert (1, -1, 2, "own_man") in origins[32]


def test_radius_three_is_invisible_and_edges_are_explicit():
    no_enemy = typed_radius_two(parse_fen("W:W32:B"))
    distant_enemy = typed_radius_two(parse_fen("W:W32:B16"))
    assert no_enemy == distant_enemy

    _, _, ((origin, cells),) = typed_radius_two(parse_fen("W:W6:B50"))
    assert origin == 6
    assert cells == (
        (-1, -1, 1, "off_board"), (-1, -1, 2, "off_board"),
        (-1, 1, 1, "empty"), (-1, 1, 2, "off_board"),
        (1, -1, 1, "off_board"), (1, -1, 2, "off_board"),
        (1, 1, 1, "empty"), (1, 1, 2, "empty"),
    )


def test_capture_and_mover_king_exclude_the_position():
    assert typed_radius_two(parse_fen("W:W32:B37")) is None
    assert typed_radius_two(parse_fen("W:WK32:B50")) is None


def test_black_side_labels_and_deterministic_origin_order():
    state = parse_fen("B:WK37:B41,32")
    reordered = parse_fen("B:WK37:B32,41")
    key = typed_radius_two(state)

    assert key == typed_radius_two(reordered)
    assert (1, -1, 1, "enemy_king") in dict(key[2])[32]
