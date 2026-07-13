"""Extraction des volumes CID/TaoW (prose analytique anglaise) → positions QA.

Format CID (1.The_endgame, 7.Locks, S5…) : diagrammes + prose d'analyse avec
lignes de coups numérotées « 1.31-26 12-18 … W+ » et verdicts W+/B+/draw. On
réutilise le mécanisme A4 : par page, :func:`boards_of_page` + `extract_runs`,
chaque plateau ancré à une ligne de coups par re-jeu SOUS hypothèses-de-dames
(gate exercice-dames + minimisation), jamais de FEN silencieusement fausse. Le
re-jeu est à la fois l'appariement ET la validation.

Sortie schéma A4 (`verified_engine=false` → revalidation d14+TB côté jass).
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import numpy as np
import pypdf
from PIL import Image

from .boards import boards_of_page
from .extract_combos import position_hash
from .extract_dubois import _pages
from .extract_endgames import (
    _king_hypotheses,
    _kings_exercised,
    _minimize_kings,
    _state_with_kings,
)
from .notation import extract_runs
from .replay import anchor_run, fen_of

_MIN_PIECES, _MAX_PIECES = 2, 20
_VERDICT_RE = re.compile(r"([WB])\s*\+")


def _expected(winner: str | None, turn: str) -> str | None:
    if winner is None:
        return None
    win_is_turn = (winner == "W" and turn == "white") or (winner == "B" and turn == "black")
    return "WIN" if win_is_turn else "LOSS"


def extract_volume(pdf: Path, source: str, cache: Path) -> tuple[list[dict], list[dict]]:
    n_pages = _pages(pdf)
    reader = pypdf.PdfReader(str(pdf))
    records: list[dict] = []
    quarantine: list[dict] = []
    seen: set[str] = set()
    for pg in range(1, n_pages + 1):
        try:
            boards = boards_of_page(pdf, pg, cache)
        except Exception:
            boards = []
        boards = [
            b
            for b in boards
            if (b.white_men or b.white_kings) and (b.black_men or b.black_kings)
            and _MIN_PIECES <= len(b.white_men) + len(b.white_kings) <= _MAX_PIECES
            and _MIN_PIECES <= len(b.black_men) + len(b.black_kings) <= _MAX_PIECES
        ]
        if not boards:
            continue
        png = cache / f"page_{pg:04d}.png"
        if not png.exists():
            continue
        gray = np.asarray(Image.open(png).convert("L"), dtype=float)
        text = reader.pages[pg - 1].extract_text() or ""
        runs = [r for r in extract_runs(text) if len(r.tokens) >= 3]
        winners = _VERDICT_RE.findall(text)  # ordre de lecture : W/B
        used: set[int] = set()
        for board in boards:
            got = None  # (run_index, ReplayResult)
            for wk, bk in _king_hypotheses(gray, board):
                state0 = _state_with_kings(board, wk, bk)
                for ri, run in enumerate(runs):
                    if ri in used:
                        continue
                    res = anchor_run(state0, run)
                    if res.ok and _kings_exercised(res):
                        mini = _minimize_kings(board, wk, bk, run)
                        if mini is not None:
                            got = (ri, mini[2])
                        break
                if got is not None:
                    break
            if got is None:
                quarantine.append({"source": source, "page": pg, "reason": "plateau non ancré (hyp. dames incluses)"})
                continue
            ri, res = got
            used.add(ri)
            s0 = res.plies[0].state_before
            fen = fen_of(s0)
            ph = position_hash(fen)
            if ph in seen:
                continue
            seen.add(ph)
            winner = winners[ri] if ri < len(winners) else None
            records.append(
                {
                    "id": f"cid-{source[:10]}-p{pg}-{ph[:8]}",
                    "fen": fen,
                    "position_hash": ph,
                    "side_to_move": s0.turn,
                    "expected": _expected(winner, s0.turn),
                    "book_claim": True,
                    "replay_anchored": True,
                    "verified_engine": False,
                    "kings": {"white": list(s0.white_kings), "black": list(s0.black_kings)},
                    "solution_plies": len(res.plies),
                    "source": source,
                    "page": pg,
                    "verified_position": True,
                }
            )
    return records, quarantine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="data/exports/cid")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--tag", default="qa", help="préfixe de sortie (ex. locks, endgame)")
    args = ap.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache or f".cache/cid/{pdf.stem}")
    records, quarantine = extract_volume(pdf, args.source, cache)

    stem = f"{args.tag}_{args.source}"
    path = out_dir / f"{stem}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (out_dir / f"{stem}_seeds.fen").open("w", encoding="utf-8") as fh:
        fh.write(f"# CID seeds — {args.source} — {len(records)} positions verifiees-position\n")
        for rec in records:
            fh.write(f"{rec['fen']}  # {rec.get('expected')} p{rec['page']}\n")
    with (out_dir / f"{stem}_quarantine.jsonl").open("w", encoding="utf-8") as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    stats = {
        "source": args.source,
        "positions": len(records),
        "quarantined": len(quarantine),
        "king_bearing": sum(1 for r in records if r["kings"]["white"] or r["kings"]["black"]),
        "verdicts": dict(collections.Counter(r["expected"] for r in records)),
        "license": "CID / The art of Winning (TaoW) — droits à identifier avant reprise publique. Usage interne QA.",
    }
    (out_dir / f"{stem}_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
