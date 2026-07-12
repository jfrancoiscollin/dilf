"""Tests du prédicat de blocage structurel (C1 — P2-structurel)."""

import sys
from dataclasses import replace
from pathlib import Path

from pedagogy.game import GameState
from pedagogy.features.blocage import (
    blocage_structurel,
    is_suicidal,
    mutual_blocked,
    opponent_net_gain,
    side_is_blocked,
)

# Moteur FMJD complet (génération de coups légaux) réutilisé de la raffinerie.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.pcblues.rules import RulesEngine  # noqa: E402

ENGINE = RulesEngine()

#: Verrou mutuel réel (trouvé par recherche) : chaque coup quiet des deux
#: camps offre une prise nette adverse. Sans dames. Position typique
#: ply-cappée et mal-étiquetée « nulle par épuisement ».
LOCK = GameState(
    white_men=frozenset([23, 35, 37, 40]),
    white_kings=frozenset(),
    black_men=frozenset([22, 24, 27, 30]),
    black_kings=frozenset(),
    turn="white",
)


def test_forced_capture_is_not_blocked() -> None:
    # Blanc 33 DOIT prendre 28/29 → coup obligatoire, pas un blocage.
    st = GameState(
        white_men=frozenset([33]), white_kings=frozenset(),
        black_men=frozenset([28, 29]), black_kings=frozenset(), turn="white",
    )
    assert not side_is_blocked(st, "white", ENGINE)


def test_suicidal_move_detected() -> None:
    # Dans le verrou, tout coup quiet blanc est suicidaire.
    for m in ENGINE.legal_moves(LOCK):
        assert not m.is_capture
        assert is_suicidal(LOCK, m, ENGINE)


def test_opponent_net_gain_positive_after_suicidal() -> None:
    move = ENGINE.legal_moves(LOCK)[0]
    after = ENGINE.apply_move(LOCK, move)
    assert opponent_net_gain(after, "black", ENGINE) >= 1


def test_mutual_blocked_fires_on_lock() -> None:
    assert side_is_blocked(LOCK, "white", ENGINE)
    assert side_is_blocked(LOCK, "black", ENGINE)
    assert mutual_blocked(LOCK, ENGINE)


def test_mutual_blocked_false_on_open_position() -> None:
    # Position ouverte (départ tronqué) : les deux camps ont des coups sûrs.
    st = GameState(
        white_men=frozenset([31, 32, 33, 34, 35]), white_kings=frozenset(),
        black_men=frozenset([16, 17, 18, 19, 20]), black_kings=frozenset(),
        turn="white",
    )
    assert not mutual_blocked(st, ENGINE)


def test_kings_guard_v0() -> None:
    # Garde v0 : dès qu'une dame est présente, pas de blocage structurel.
    with_king = replace(LOCK, white_kings=frozenset([1]))
    assert not mutual_blocked(with_king, ENGINE)
    assert not blocage_structurel(with_king, ENGINE)
