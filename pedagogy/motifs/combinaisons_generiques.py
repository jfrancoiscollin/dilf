"""``combinaison_N_temps`` — generic forcing combinations of N attacker moves.

Most real-game combinations don't match a named pattern (coup_de_talon,
coup_philippe, coup_napoleon…) — they're ad-hoc forcing sequences where
the attacker plays N moves, the opponent's replies are all forced
(typically by the FMJD prise-maximale rule), and the attacker comes out
ahead materially.

Four detectors fire on the played move (and via ``detect_missed`` on the
engine's best move) — one per depth bucket:

* :class:`Combinaison2TempsDetector` — N = 2
* :class:`Combinaison3TempsDetector` — N = 3
* :class:`Combinaison4TempsDetector` — N = 4
* :class:`Combinaison5TempsDetector` — N ≥ 5 (clamped bucket)

Conditions for any of them to fire:

1. The PV walked through ``engine.apply_move`` shows every opponent
   reply is **forced** (exactly one legal move available).
2. The attacker actually completes ``N`` moves before the chain breaks
   (opponent reply non-forced, PV exhausted, or a parse failure).
3. The net material delta for the attacker is ≥ 1 pawn at the end of
   the chain.

This generalises :class:`SacrificeDetector` and
:class:`EnvoiADameDetector` — they detect specific endings (material
loss with score recovery, promotion landing) while this family detects
the structural property (forced chain with material gain).
"""

from __future__ import annotations

from typing import ClassVar

from ..features.material import material_balance
from ..game import GameState, Move, notation
from ..notation.dubois import parse_move_notation
from ..protocols import EngineProtocol
from ..types import MotifMatch
from .base import MotifDetector

#: Deepest bucket — combinations longer than this report as ``combinaison_5_temps``.
MAX_DEPTH_TEMPS = 5

#: Minimum net material gain for the attacker (kings weigh 3, per
#: :func:`pedagogy.features.material.material_balance`).
MIN_MATERIAL_GAIN = 1


def _side_sign(side: str) -> int:
    return 1 if side == "white" else -1


def _opp_is_forced(opp_legal: list[Move]) -> bool:
    """Tactically forced under FMJD: opponent has a single legal move, OR
    every legal move is a capture (prise-maximale — opponent must capture
    no matter which max-length path they pick). Multiple tied captures
    still count as forced because the attacker's combination resolves
    the same way regardless of which path the defender takes.
    """
    if not opp_legal:
        return False
    if len(opp_legal) == 1:
        return True
    return all(m.is_capture for m in opp_legal)


def _walk_forced_chain(
    state_before: GameState,
    first_move: Move,
    pv: list[str],
    engine: EngineProtocol,
) -> tuple[int, GameState] | None:
    """Apply ``first_move`` then alternate forced opponent replies and PV
    attacker moves until the chain breaks. Returns ``(N, final_state)``
    where ``N`` is the number of attacker moves chained (capped at
    :data:`MAX_DEPTH_TEMPS`), or ``None`` if fewer than 2 moves chained.

    "Forced" follows :func:`_opp_is_forced` — single legal move or
    all-capture replies (FMJD ties). When the PV names a specific reply,
    we prefer it over ``opp_legal[0]`` so Scan's chosen line drives the
    chain through prise-maximale ambiguities.
    """
    try:
        state = engine.apply_move(state_before, first_move)
    except Exception:
        return None

    attacker_moves = 1
    pv_index = 1

    while attacker_moves < MAX_DEPTH_TEMPS:
        opp_legal = list(engine.legal_moves(state))
        if not _opp_is_forced(opp_legal):
            break

        reply: Move = opp_legal[0]
        if pv_index < len(pv):
            try:
                parsed = parse_move_notation(pv[pv_index], state)
                if any(m.path == parsed.path for m in opp_legal):
                    reply = parsed
            except Exception:
                pass

        try:
            state = engine.apply_move(state, reply)
        except Exception:
            break
        pv_index += 1

        if pv_index >= len(pv):
            break
        try:
            next_attacker = parse_move_notation(pv[pv_index], state)
            state = engine.apply_move(state, next_attacker)
        except Exception:
            break
        attacker_moves += 1
        pv_index += 1

    if attacker_moves < 2:
        return None
    return attacker_moves, state


class _CombinaisonGeneriqueBase(MotifDetector):
    """Shared logic; concrete subclasses fix :attr:`target_depth`."""

    #: The depth this detector reports. The depth-5 detector ALSO fires
    #: when the chain reaches 5 or more attacker moves.
    target_depth: ClassVar[int]

    def _accepts_depth(self, attacker_moves: int) -> bool:
        if self.target_depth == MAX_DEPTH_TEMPS:
            return attacker_moves >= MAX_DEPTH_TEMPS
        return attacker_moves == self.target_depth

    def _build_match(
        self,
        attacker_side: str,
        state_before: GameState,
        final_state: GameState,
        attacker_moves: int,
        move: Move,
        pv: list[str],
        role: str,
    ) -> MotifMatch | None:
        sign = _side_sign(attacker_side)
        delta = sign * (material_balance(final_state) - material_balance(state_before))
        if delta < MIN_MATERIAL_GAIN:
            return None

        relevant_pv_len = 2 * attacker_moves - 1
        return MotifMatch(
            motif=self.name,
            role=role,
            squares=list(move.path),
            pv=list(pv[:relevant_pv_len]),
            severity=min(1.0, 0.3 + delta / 5.0),
            metadata={
                "depth_temps": attacker_moves,
                "material_gain": delta,
            },
        )

    def detect(
        self,
        state_before: GameState,
        move: Move,
        state_after: GameState,
        *,
        pv: list[str] | None = None,
        scan_score_before: float = 0.0,
        scan_score_after: float = 0.0,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        if engine is None or not pv:
            return None
        if notation(move) != pv[0]:
            return None
        result = _walk_forced_chain(state_before, move, pv, engine)
        if result is None:
            return None
        attacker_moves, final_state = result
        if not self._accepts_depth(attacker_moves):
            return None
        return self._build_match(
            attacker_side=state_before.turn,
            state_before=state_before,
            final_state=final_state,
            attacker_moves=attacker_moves,
            move=move,
            pv=pv,
            role="played",
        )

    def detect_missed(
        self,
        state_before: GameState,
        best_move: Move,
        best_pv: list[str],
        played_move: Move,
        *,
        engine: EngineProtocol | None = None,
    ) -> MotifMatch | None:
        if engine is None or not best_pv:
            return None
        if notation(best_move) != best_pv[0]:
            return None
        result = _walk_forced_chain(state_before, best_move, best_pv, engine)
        if result is None:
            return None
        attacker_moves, final_state = result
        if not self._accepts_depth(attacker_moves):
            return None
        return self._build_match(
            attacker_side=state_before.turn,
            state_before=state_before,
            final_state=final_state,
            attacker_moves=attacker_moves,
            move=best_move,
            pv=best_pv,
            role="missed",
        )


class Combinaison2TempsDetector(_CombinaisonGeneriqueBase):
    name = "combinaison_2_temps"
    target_depth = 2


class Combinaison3TempsDetector(_CombinaisonGeneriqueBase):
    name = "combinaison_3_temps"
    target_depth = 3


class Combinaison4TempsDetector(_CombinaisonGeneriqueBase):
    name = "combinaison_4_temps"
    target_depth = 4


class Combinaison5TempsDetector(_CombinaisonGeneriqueBase):
    name = "combinaison_5_temps"
    target_depth = 5
