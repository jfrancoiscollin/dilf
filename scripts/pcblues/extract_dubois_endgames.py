"""C3 — A4-bis : QA finales depuis les volumes d'endgames Dubois.

Même appariement diagramme↔solution que `extract_dubois` (position
pixel-extraite + trait explicite → re-jeu FMJD → validité de la position),
mais la sortie est une QA finale A4 : le VERDICT (WIN/DRAW) vient des
marqueurs de la solution Dubois — « + » en fin de coup (gain), « = » /
« nulle » / « remise » (nulle). `book_claim=true` toujours (revalidation
moteur côté consommateur). N'émet que si le verdict est NON-AMBIGU (un seul
des deux signaux) et la position re-jeu-validée — prudence > volume.

Usage::

    python3 -m scripts.pcblues.extract_dubois_endgames \
        --pdf docs/corpus/jpdubois_apprentissage_fins_de_parties_V1.pdf \
        --source dubois_apprentissage_finales --out data/exports/dubois \
        --cache .cache/dubois/finales_appr
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .extract_combos import position_hash
from .extract_dubois import (
    _CAPTION_RE,
    _diagram_state,
    _pages,
    _render_extract,
    _serie_by_page,
    _solutions,
    LICENSE_NOTE as DUBOIS_LICENSE,
)
from .notation import extract_runs
from .replay import fen_of, replay_tokens

#: « + » collé à un coup (4-15+) OU mots de gain.
_WIN_RE = re.compile(r"\d[+]|\bgain\b|\bgagne(nt)?\b", re.I)
#: « = » de nulle, ou mots de nulle. (« remise gegeven » n'existe pas ici.)
_DRAW_RE = re.compile(r"\bnulle\b|\bremise\b|(?<![\d)])=", re.I)


def _verdict(sol_text: str) -> str | None:
    win = bool(_WIN_RE.search(sol_text))
    draw = bool(_DRAW_RE.search(sol_text))
    if win == draw:  # les deux, ou aucun → ambigu
        return None
    return "WIN" if win else "DRAW"


def extract_volume(pdf: Path, source: str, cache: Path) -> tuple[list[dict], list[dict]]:
    n_pages = _pages(pdf)
    extracted = _render_extract(pdf, cache, n_pages)
    serie_of = _serie_by_page(pdf, n_pages)
    sols, by_dnum = _solutions(pdf, n_pages)

    records: list[dict] = []
    quarantine: list[dict] = []
    seen: set[str] = set()
    for rec in extracted:
        cap = rec.get("caption_text") or ""
        mcap = _CAPTION_RE.search(cap)
        if not mcap:
            continue
        dk = int(mcap.group(1))
        serie = serie_of.get(rec["page"])
        key = (serie, dk) if serie else None
        base = {"source": source, "serie": serie, "diagram": dk, "page": rec["page"]}

        candidates: list[str] = []
        if key is not None and key in sols:
            candidates.append(sols[key])
        candidates.extend(t for t in by_dnum.get(dk, []) if t not in candidates)

        # Les solutions d'ENDGAME sont branchées (A/B) et à ligne principale
        # courte : on ne valide pas toute la ligne mais le plus long PRÉFIXE
        # légal (>= 1 ply). Position pixel-extraite (prouvée) + 1er coup du
        # livre légal = validation suffisante pour une QA book_claim.
        state0 = _diagram_state(rec)
        chosen = None
        best_prefix = 0
        for sol_text in candidates:
            cruns = [r for r in extract_runs(sol_text) if r.tokens]
            if not cruns:
                continue
            toks = cruns[0].tokens
            full = replay_tokens(state0, toks, state0.turn)
            if full.ok:
                chosen = (sol_text, full, len(full.plies))
                break
            k = full.failed_at or 0
            if k >= 1:
                pref = replay_tokens(state0, toks[:k], state0.turn)
                if pref.ok and k > best_prefix:
                    chosen = (sol_text, pref, k)
                    best_prefix = k
        if chosen is None:
            quarantine.append({**base, "reason": "position non validée : aucun coup légal de la solution"})
            continue
        sol_text, res, n_ply = chosen
        verdict = _verdict(sol_text)
        if verdict is None:
            quarantine.append({**base, "reason": "verdict gain/nulle ambigu ou absent"})
            continue

        fen = fen_of(res.plies[0].state_before)
        if position_hash(fen) in seen:
            continue
        seen.add(position_hash(fen))
        rationale = " ".join(sol_text.split())[:160]
        records.append(
            {
                "id": f"dubois-endgame-{source[:8]}-d{dk}-{position_hash(fen)[:8]}",
                "fen": fen,
                "position_hash": position_hash(fen),
                "side_to_move": state0.turn,
                "expected": verdict,
                "rationale_courte": rationale,
                "book_claim": True,
                "replay_anchored": True,
                "kings": {
                    "white": list(res.plies[0].state_before.white_kings),
                    "black": list(res.plies[0].state_before.black_kings),
                },
                "source": source,
                "diagram": dk,
                "page": rec["page"],
                "verified_position": True,
            }
        )
    return records, quarantine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="data/exports/dubois")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache or f".cache/dubois/{pdf.stem}")
    records, quarantine = extract_volume(pdf, args.source, cache)

    path = out_dir / f"endgame_{args.source}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (out_dir / f"endgame_quarantine_{args.source}.jsonl").open("w", encoding="utf-8") as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    import collections

    stats = {
        "source": args.source,
        "endgames": len(records),
        "quarantined": len(quarantine),
        "verdicts": dict(collections.Counter(r["expected"] for r in records)),
        "license": DUBOIS_LICENSE,
    }
    (out_dir / f"endgame_stats_{args.source}.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False)
    )
    print(json.dumps(stats, ensure_ascii=False))
    assert len([json.loads(l) for l in path.open(encoding="utf-8")]) == len(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
