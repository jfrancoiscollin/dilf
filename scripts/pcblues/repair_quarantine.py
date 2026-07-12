"""Passe §4.13 — heuristiques de coquilles sur la quarantaine d'un volume.

Patterns du cadrage (CADRAGE_MANUELS.md §4.13), appliqués au ply où le
re-jeu échoue, TOUJOURS sous la règle de la solution unique :

* **Pattern 3 — inversion d'opérandes** : ``aXb`` imprimé pour ``bXa``.
  Premier recours : re-tenter le token inversé.
* **Pattern 1/2 — substitution / inversion de chiffres** : recherche
  exhaustive — chaque coup légal de la position est essayé à la place du
  token fautif ; si UN SEUL permet de rejouer TOUT le reste de la
  séquence, c'est lui (sinon, quarantaine maintenue — pas de devinette).

Chaque réparation est documentée dans le record (``coquille_fix``) et dans
``RESOLUTIONS_pcblues.md`` (règle de l'aveu §4.7). Usage::

    python3 -m scripts.pcblues.repair_quarantine --deel 15 \
        --out data/exports/pcblues --cache .cache/pcblues/15
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pedagogy.game import GameState

from .boards import boards_of_page
from .extract_combos import _record, board_to_state, page_text
from .notation import MoveToken, SequenceRun, extract_runs
from .replay import ReplayedPly, ReplayResult, notation_of, replay_tokens
from .rules import apply_move, legal_moves, match_token


def _try_rest(state: GameState, tokens: list[MoveToken]) -> ReplayResult:
    return replay_tokens(state, tokens, state.turn)


def repair_run(state0: GameState, run: SequenceRun) -> tuple[ReplayResult, dict] | None:
    """Try §4.13 heuristics from one anchor; return (result, fix-note) or None."""
    for turn in (["black"] if run.black_starts else ["white", "black"]):
        res = replay_tokens(state0, run.tokens, turn)
        if res.ok:
            return res, {}  # ne devrait pas arriver (déjà hors quarantaine)
        k = res.failed_at
        if k is None or k >= len(run.tokens):
            continue
        state_k = (
            res.plies[-1].state_after if res.plies else
            GameState(
                white_men=state0.white_men, white_kings=state0.white_kings,
                black_men=state0.black_men, black_kings=state0.black_kings,
                turn=turn,  # type: ignore[arg-type]
            )
        )
        bad = run.tokens[k]
        rest = run.tokens[k + 1 :]
        # La solution unique n'a de force que si le reste de la séquence
        # porte assez de signal pour discriminer (>= 3 plies après le fix).
        if len(rest) < 3:
            continue

        # Pattern 3 : inversion d'opérandes (aXb -> bXa), premier recours.
        if bad.capture:
            try:
                resolved = match_token(state_k, bad.to, bad.frm, True)
                after = apply_move(state_k, resolved)
                rest_res = _try_rest(after, rest)
                if rest_res.ok:
                    plies = res.plies + [
                        ReplayedPly(bad, resolved, state_k, after)
                    ] + rest_res.plies
                    full = ReplayResult(ok=True, turn_hypothesis=turn, plies=plies)
                    return full, {
                        "pattern": "inversion_operandes",
                        "ply": k,
                        "published": f"{bad.frm}x{bad.to}",
                        "corrected": f"{bad.to}x{bad.frm}",
                    }
            except ValueError:
                pass

        # Pattern 1/2 : substitution — recherche exhaustive, solution unique.
        fulls = []
        for cand in legal_moves(state_k):
            after = apply_move(state_k, cand)
            rest_res = _try_rest(after, rest)
            if rest_res.ok:
                fulls.append((cand, after, rest_res))
        if len(fulls) == 1:
            cand, after, rest_res = fulls[0]
            plies = res.plies + [
                ReplayedPly(bad, cand, state_k, after)
            ] + rest_res.plies
            full = ReplayResult(ok=True, turn_hypothesis=turn, plies=plies)
            return full, {
                "pattern": "substitution_unique",
                "ply": k,
                "published": f"{bad.frm}{'x' if bad.capture else '-'}{bad.to}",
                "corrected": notation_of(cand.move),
            }
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deel", type=int, required=True)
    ap.add_argument("--event", default=None)
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--out", default="data/exports/pcblues")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    pdf = Path(args.pdf or f"docs/corpus/pcblues/{args.deel}.pdf")
    cache = Path(args.cache or f".cache/pcblues/{args.deel}")
    qpath = out_dir / f"quarantine_deel{args.deel:02d}.jsonl"
    quarantine = [json.loads(l) for l in qpath.open(encoding="utf-8")]
    if not quarantine:
        print("quarantaine vide, rien à faire")
        return 0

    # Pool de plateaux du volume : pages rendues déjà en cache.
    pages_with_q = sorted({q["page"] for q in quarantine})
    max_page = max(pages_with_q)
    pool: list[tuple[int, GameState]] = []
    for page in range(1, max_page + 1):
        for b in boards_of_page(pdf, page, cache):
            pool.append((page, board_to_state(b)))

    repaired: list[dict] = []
    still: list[dict] = []
    resolutions: list[str] = []

    for rec in quarantine:
        page = rec["page"]
        text = page_text(pdf, page)
        runs = [
            r
            for r in extract_runs(text)
            if [f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in r.tokens]
            == rec["tokens"]
        ]
        fixed = None
        if runs:
            run = runs[0]
            # ancres : page, page-1, puis pool décroissant
            ordered = (
                [(pg, st) for pg, st in pool if pg == page]
                + [(pg, st) for pg, st in pool if pg == page - 1]
                + [(pg, st) for pg, st in reversed(pool) if pg < page - 1]
            )
            for anchor_page, st in ordered:
                out = repair_run(st, run)
                if out is not None:
                    res, note = out
                    combo = _record(
                        res, run, args.deel, page, -1, args.event, text,
                        f"quarantine_repair_p{anchor_page}",
                    )
                    combo["coquille_fix"] = note
                    combo["claude_notes"] = (
                        f"§4.13 {note.get('pattern')}: coup publié "
                        f"{note.get('published')} -> {note.get('corrected')} "
                        f"(solution unique, re-jeu complet)"
                    )
                    fixed = combo
                    resolutions.append(
                        f"- deel {args.deel} p.{page} : {note.get('published')} "
                        f"-> {note.get('corrected')} ({note.get('pattern')}, "
                        f"ply {note.get('ply')})"
                    )
                    break
        if fixed is not None:
            repaired.append(fixed)
        else:
            still.append(rec)

    rpath = out_dir / f"repaired_deel{args.deel:02d}.jsonl"
    with rpath.open("w", encoding="utf-8") as fh:
        for rec in repaired:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with qpath.open("w", encoding="utf-8") as fh:
        for rec in still:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if resolutions:
        respath = out_dir / "RESOLUTIONS_pcblues.md"
        with respath.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(resolutions) + "\n")

    print(
        f"deel {args.deel}: {len(repaired)} réparées (§4.13, solution unique), "
        f"{len(still)} maintenues en quarantaine"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
