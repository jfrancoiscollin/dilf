"""Replay candidate move runs from diagram-anchored positions.

The anchor rule of the memo ("la plupart des fragments s'ancrent par
continuité") is implemented as *anchor-by-replay*: a text run validates
against a diagram position iff the full run replays legally from it under
FMJD rules (global prise-maximale, promotions). Beyond 2-3 plies a wrong
(board, run) pairing has essentially no chance of replaying legally, so
legality doubles as the pairing criterion — nothing is transcribed by hand
(règle §4.10) and nothing unverified is emitted (règle §4.6).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pedagogy.game import GameState, Move, state_to_fen
from pedagogy.motifs import detect_all

from .notation import MoveToken, SequenceRun
from .rules import (
    AmbiguousMoveError,
    IllegalMoveError,
    ResolvedMove,
    RulesEngine,
    apply_move,
    match_token,
)


@dataclass
class ReplayedPly:
    token: MoveToken
    resolved: ResolvedMove
    state_before: GameState
    state_after: GameState


@dataclass
class ReplayResult:
    ok: bool
    turn_hypothesis: str  # "white" | "black"
    plies: list[ReplayedPly] = field(default_factory=list)
    failure: str | None = None  # message of the first illegal token
    failed_at: int | None = None  # token index of the failure


def replay_tokens(
    state0: GameState, tokens: list[MoveToken], turn: str
) -> ReplayResult:
    """Replay ``tokens`` from ``state0`` with ``turn`` to move first."""
    state = GameState(
        white_men=state0.white_men,
        white_kings=state0.white_kings,
        black_men=state0.black_men,
        black_kings=state0.black_kings,
        turn=turn,  # type: ignore[arg-type]
    )
    result = ReplayResult(ok=False, turn_hypothesis=turn)
    for i, tok in enumerate(tokens):
        try:
            resolved = match_token(state, tok.frm, tok.to, tok.capture)
        except (IllegalMoveError, AmbiguousMoveError, ValueError) as exc:
            result.failure = f"ply {i} ({tok.frm}{'x' if tok.capture else '-'}{tok.to}): {exc}"
            result.failed_at = i
            return result
        after = apply_move(state, resolved)
        result.plies.append(
            ReplayedPly(token=tok, resolved=resolved, state_before=state, state_after=after)
        )
        state = after
    result.ok = True
    return result


def anchor_run(state0: GameState, run: SequenceRun) -> ReplayResult:
    """Try to replay ``run`` from ``state0``, resolving the side to move.

    The ellipsis hint ("NN. ...") fixes the first side when present;
    otherwise both hypotheses are tried (white first, the corpus default).
    """
    hypotheses = (
        ["black"] if run.black_starts else ["white", "black"]
    )
    best: ReplayResult | None = None
    for turn in hypotheses:
        res = replay_tokens(state0, run.tokens, turn)
        if res.ok:
            return res
        if best is None or (res.failed_at or 0) > (best.failed_at or 0):
            best = res
    assert best is not None
    return best


def anchor_run_with_repair(
    state0: GameState, run: SequenceRun, max_drops: int = 2
) -> tuple[ReplayResult, list[MoveToken]]:
    """:func:`anchor_run`, retrying with offending tokens dropped.

    A token where replay fails is often an inline alternative the prose-gap
    splitter missed ("of 26-31") or a stray number — dropping it and
    replaying the rest keeps the legality gate intact: the repaired
    sequence still must replay fully. Dropped tokens are returned for the
    record (règle de l'aveu §4.7).
    """
    dropped: list[MoveToken] = []
    tokens = list(run.tokens)
    res = anchor_run(state0, run)
    while not res.ok and res.failed_at is not None and len(dropped) < max_drops:
        # A drop is only credible strictly inside the sequence: the head
        # (>= 2 plies) and the tail (last 2 tokens) must replay untouched,
        # otherwise a wrong board could "pass" by truncation.
        if (
            len(tokens) - 1 < 3
            or res.failed_at < 2
            or res.failed_at >= len(tokens) - 2
        ):
            break
        dropped.append(tokens[res.failed_at])
        tokens = tokens[: res.failed_at] + tokens[res.failed_at + 1 :]
        trimmed = SequenceRun(
            tokens=tokens,
            variation=run.variation,
            result=run.result,
            first_line=run.first_line,
            last_line=run.last_line,
        )
        res = anchor_run(state0, trimmed)
    return res, (dropped if res.ok else [])


def themes_of(plies: list[ReplayedPly]) -> list[str]:
    """Union of motif-detector names firing on any ply of the sequence.

    Each ply gets the *remaining* sequence as PV and the pure-rules engine,
    which is what the pv/engine-dependent detectors (combinaison_N_temps,
    coup_royal…) need to walk the forced chain.
    """
    engine = RulesEngine()
    names: list[str] = []
    for i, ply in enumerate(plies):
        pv = [notation_of(p.resolved.move) for p in plies[i:]]
        for m in detect_all(
            ply.state_before,
            ply.resolved.move,
            ply.state_after,
            pv=pv,
            engine=engine,
        ):
            if m.motif not in names:
                names.append(m.motif)
    return names


def notation_of(move: Move) -> str:
    sep = "x" if move.is_capture else "-"
    return f"{move.from_square}{sep}{move.to_square}"


def fen_of(state: GameState) -> str:
    return state_to_fen(state)
