"""C1 — prédicat de BLOCAGE STRUCTUREL (par mobilité).

Le trou d'oracle n°1 (mémo enrichissement) : les milieux BLOQUÉS qui
piétinent sont aujourd'hui étiquetés par ÉPUISEMENT (ply-cap ~19 %,
label-menteur « nulle par épuisement »). Ce prédicat les reconnaît
STRUCTURELLEMENT — indépendamment de tout score d'éval — pour poser un
verdict DRAW-de-blocage propre.

Version matérielle (« qui a plus de matériel gagne ») délibérément écartée
(morte au harnais). Version STRUCTURELLE retenue :

* un coup non-capturant est **suicidaire** s'il offre à l'adversaire une
  prise NETTE (l'adversaire regagne ≥1 unité de matériel au coup suivant —
  vérif 1-ply, prise-max FMJD) ;
* un camp est **bloqué** s'il n'a aucune capture forcée ET tous ses coups
  non-capturants sont suicidaires (aucun coup progressif sûr) ;
* la position est en **blocage structurel** si LES DEUX camps sont bloqués
  (verrou mutuel) — et que la condition **tient sur 2 plies** (stabilité :
  après n'importe quel coup forcé/suicidaire, le verrou persiste) ;
* **garde v0 : sans dames** (les dames rouvrent la mobilité — traitées plus
  tard).

Ne dépend d'aucun moteur d'ÉVAL : uniquement de la génération de coups
légaux FMJD (:class:`EngineProtocol`) et du compte matériel. Consommé par
le harnais de notation (TB + arbitre-fort) ; gate DRAW ≥ 99,9 % → admis
(tue la source ply-cap), sinon → veto ply-cap.
"""

from __future__ import annotations

from dataclasses import replace

from ..game import GameState, Move, Side
from ..protocols import EngineProtocol
from .material import material_balance

#: Unité minimale de « prise nette » : au moins 1 pion regagné par l'adversaire.
NET_CAPTURE_MIN = 1


def _other(side: Side) -> Side:
    return "black" if side == "white" else "white"


def _with_turn(state: GameState, side: Side) -> GameState:
    return state if state.turn == side else replace(state, turn=side)


def _signed_for(side: Side, balance: int) -> int:
    """Balance matériel du point de vue de ``side`` (positif = ``side`` mène)."""
    return balance if side == "white" else -balance


def has_kings(state: GameState) -> bool:
    return bool(state.white_kings or state.black_kings)


def opponent_net_gain(
    state_after: GameState, opponent: Side, engine: EngineProtocol
) -> int:
    """Gain matériel NET maximal de ``opponent`` en 1 coup depuis ``state_after``.

    On joue la meilleure capture de l'adversaire (prise-max FMJD déjà imposée
    par le moteur) et on mesure le delta de matériel du point de vue de
    l'adversaire. 0 s'il n'a pas de capture. (1-ply : suffisant pour la
    v0 ; une vérif plus profonde viendrait avec l'arbitre-fort.)
    """
    st = _with_turn(state_after, opponent)
    caps = [m for m in engine.legal_moves(st) if m.is_capture]
    if not caps:
        return 0
    before = _signed_for(opponent, material_balance(st))
    best = 0
    for cap in caps:
        after = engine.apply_move(st, cap)
        gain = _signed_for(opponent, material_balance(after)) - before
        best = max(best, gain)
    return best


def is_suicidal(state: GameState, move: Move, engine: EngineProtocol) -> bool:
    """Le coup non-capturant ``move`` offre-t-il une prise nette à l'adversaire ?"""
    opponent = _other(state.turn)
    after = engine.apply_move(state, move)
    return opponent_net_gain(after, opponent, engine) >= NET_CAPTURE_MIN


def side_is_blocked(state: GameState, side: Side, engine: EngineProtocol) -> bool:
    """``side`` n'a-t-il que des coups suicidaires (aucun coup progressif sûr) ?

    Si ``side`` a une capture forcée, il n'est PAS « bloqué » au sens de ce
    prédicat (il a un coup obligatoire qui change la structure). Sinon,
    bloqué ssi tous ses coups quiets sont suicidaires. Un camp SANS aucun
    coup légal est déjà perdu (pas un blocage) → False.
    """
    st = _with_turn(state, side)
    moves = engine.legal_moves(st)
    if not moves:
        return False
    if any(m.is_capture for m in moves):
        return False
    return all(is_suicidal(st, m, engine) for m in moves)


def mutual_blocked(state: GameState, engine: EngineProtocol) -> bool:
    """Signal CŒUR : les deux camps bloqués, sans dames (garde v0).

    C'est la condition qui distingue un verrou structurel d'un ply-cap par
    épuisement : aucun des deux camps n'a de coup progressif sûr. Le
    harnais peut noter sur ce signal seul (looser) ou exiger en plus la
    stabilité 2-plies via :func:`blocage_structurel` (plus conservateur).
    """
    if has_kings(state):
        return False
    return side_is_blocked(state, "white", engine) and side_is_blocked(
        state, "black", engine
    )


def blocage_structurel(
    state: GameState, engine: EngineProtocol, *, check_stability: bool = True
) -> bool:
    """La position est-elle en blocage structurel mutuel (verrou → nulle) ?

    Les DEUX camps sont bloqués (aucun coup progressif sûr), sans dames
    (garde v0), et — si ``check_stability`` — le verrou tient sur 2 plies :
    après n'importe quel coup (forcément suicidaire) du camp au trait,
    l'adversaire regagne son matériel et la position reste un blocage.
    """
    if has_kings(state):
        return False
    if not (
        side_is_blocked(state, "white", engine)
        and side_is_blocked(state, "black", engine)
    ):
        return False
    if not check_stability:
        return True
    # Stabilité 2 plies : tout coup du camp au trait mène (après la reprise
    # nette adverse) à une position encore bloquée OU terminale-nulle.
    st = _with_turn(state, state.turn)
    for move in engine.legal_moves(st):
        after = engine.apply_move(st, move)
        opp = _other(state.turn)
        opp_st = _with_turn(after, opp)
        opp_caps = [m for m in engine.legal_moves(opp_st) if m.is_capture]
        if not opp_caps:
            # coup non puni → pas un blocage stable (coup progressif existait)
            return False
        # l'adversaire reprend ; le verrou doit persister (sans dames)
        reprise = engine.apply_move(opp_st, opp_caps[0])
        if has_kings(reprise):
            return False
        if not side_is_blocked(reprise, reprise.turn, engine):
            return False
    return True
