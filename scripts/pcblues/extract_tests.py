"""A5 — Vaardigheidstesten (deel 47, 57) -> ``tests_deelNN.jsonl``.

Structure des volumes : pages-grilles « Vaardigheidstest N » (12 diagrammes,
légende « Waz/Zaz Joueur-Joueur / Événement » sous chaque rangée), puis
sections « Oplossingen Vaardigheidstesten A-B » avec, par test, des items
« K. » dont la notation est renumérotée depuis 01.

Validation : la solution K du test N doit se REJOUER intégralement depuis
le diagramme K de la grille N (trait = Waz/Zaz, recoupé par l'ellipse
« 01. ... ») — l'appariement item->plateau est vérifié par la légalité du
re-jeu, comme partout dans la raffinerie. Échec -> quarantaine.

Usage::

    python3 -m scripts.pcblues.extract_tests --pdf docs/corpus/pcblues/47.pdf \
        --deel 47 --out data/exports/pcblues --cache .cache/pcblues/47
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .boards import DetectedBoard, analyze_board, analyze_board_band, boards_of_page
from .extract_combos import LICENSE_NOTE, board_to_state, page_text, position_hash
from .notation import extract_runs
from .replay import anchor_run, fen_of, notation_of


def _board_variants(gray, board: DetectedBoard) -> list[DetectedBoard]:
    """Geometry hypotheses for one detected board, replay-arbitrated upstream.

    Certains rendus (deel 47 : plateaux 299x287 non carrés, bordure haute
    faible) laissent la bbox incertaine de quelques pixels — plutôt que de
    sur-ajuster la CV, on classifie sous plusieurs géométries plausibles et
    le re-jeu de la solution élit la bonne (comme pour tout ancrage).
    """
    x1, y1, x2, y2 = board.bbox
    w, h = x2 - x1, y2 - y1
    side = max(w, h)
    cands = {(x1, y1, x2, y2)}
    for dy in (-6, 0, 6):
        cands.add((x1, y1 + dy, x2, y1 + dy + w))  # carré ancré en haut
        cands.add((x1, y2 + dy - w, x2, y2 + dy))  # carré ancré en bas
        cands.add((x1, y1 + dy, x2, y2 + dy))      # bbox translatée
    out = []
    seen = set()
    for bb in cands:
        for classify in (analyze_board_band, analyze_board):
            white, black = classify(gray, bb)
            key = (tuple(white), tuple(black))
            if key in seen or not (white or black):
                continue
            seen.add(key)
            out.append(
                DetectedBoard(
                    page=board.page, index=board.index, bbox=bb,
                    white_men=tuple(white), black_men=tuple(black),
                )
            )
    return out

_TEST_HEADER_RE = re.compile(r"^\s*Vaardigheidstest\s+0?(\d{1,2})\s*$", re.M)
_SOLUTIONS_RE = re.compile(r"Oplossingen\s+Vaardigheidstesten", re.I)
_ITEM_RE = re.compile(r"^\s*(\d{1,2})\.\s*$")
_CAPTION_RE = re.compile(r"\b(Waz|Zaz)\b")
_PLAYERS_RE = re.compile(r"([A-Z][\w'.]*(?:\s?[A-Z][\w'.]*)*)\s*-\s*([A-Z][\w'.]*(?:\s?[A-Z][\w'.]*)*)")


def _grid_pages(pdf: Path, n_pages: int) -> dict[int, int]:
    """Map test number -> page of its diagram grid (before the solutions)."""
    grids: dict[int, int] = {}
    for page in range(1, n_pages + 1):
        text = page_text(pdf, page)
        if _SOLUTIONS_RE.search(text):
            continue
        m = _TEST_HEADER_RE.search(text)
        if m and len(_CAPTION_RE.findall(text)) >= 6:
            grids.setdefault(int(m.group(1)), page)
    return grids


def _captions(text: str) -> list[dict]:
    """Waz/Zaz + players of each diagram, reading order."""
    out: list[dict] = []
    for m in _CAPTION_RE.finditer(text):
        tail = text[m.end() : m.end() + 60].splitlines()[0]
        pm = _PLAYERS_RE.search(tail)
        out.append(
            {
                "side": "white" if m.group(1) == "Waz" else "black",
                "players": f"{pm.group(1)} - {pm.group(2)}" if pm else None,
            }
        )
    return out


def _solution_items(pdf: Path, n_pages: int) -> dict[int, dict[int, list]]:
    """{test_number: {item_number: [SequenceRun, ...]}} des sections Oplossingen.

    Le texte de chaque item est accumulé sur toutes ses lignes (les
    solutions s'étalent sur plusieurs lignes/pages) puis tokenizé en bloc.
    """
    texts: dict[int, dict[int, list[str]]] = {}
    current_test: int | None = None
    current_item: int | None = None
    in_solutions = False
    for page in range(1, n_pages + 1):
        text = page_text(pdf, page)
        if _SOLUTIONS_RE.search(text):
            in_solutions = True
        for line in text.splitlines():
            th = re.match(r"^\s*Vaardigheidstest\s+0?(\d{1,2})\s*$", line)
            if th and in_solutions:
                current_test = int(th.group(1))
                current_item = None
                texts.setdefault(current_test, {})
                continue
            im = _ITEM_RE.match(line)
            if im and current_test is not None and 1 <= int(im.group(1)) <= 12:
                current_item = int(im.group(1))
                texts[current_test].setdefault(current_item, [])
                continue
            if current_test is not None and current_item is not None:
                texts[current_test][current_item].append(line)
    return {
        t: {k: extract_runs("\n".join(lines)) for k, lines in items.items()}
        for t, items in texts.items()
    }


def extract_volume(pdf: Path, deel: int, cache: Path) -> tuple[list[dict], list[dict]]:
    n_pages = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )
    grids = _grid_pages(pdf, n_pages)
    solutions = _solution_items(pdf, n_pages)

    tests: list[dict] = []
    quarantine: list[dict] = []
    import numpy as np
    from PIL import Image

    for test_no, page in sorted(grids.items()):
        boards = boards_of_page(pdf, page, cache)
        gray = np.asarray(
            Image.open(cache / f"page_{page:04d}.png").convert("L"), dtype=float
        )
        captions = _captions(page_text(pdf, page))
        sols = solutions.get(test_no, {})
        for k, board in enumerate(boards, start=1):
            runs = sols.get(k, [])
            caption = captions[k - 1] if k - 1 < len(captions) else {}
            solved = None
            for variant in _board_variants(gray, board):
                state0 = board_to_state(variant)
                for run in runs:
                    if len(run.tokens) < 1:
                        continue
                    res = anchor_run(state0, run)
                    if res.ok:
                        solved = res
                        break
                if solved is not None:
                    break
            rec_base = {
                "id": f"pcblues-test-d{deel:02d}-t{test_no:02d}-{k:02d}",
                "deel": deel,
                "test": test_no,
                "item": k,
                "page": page,
                "players": caption.get("players"),
                "side_to_move_caption": caption.get("side"),
            }
            if solved is None:
                quarantine.append(
                    {
                        **rec_base,
                        "n_runs_candidats": len(runs),
                        "reason": "aucune solution ne se rejoue depuis le diagramme",
                    }
                )
                continue
            fen = fen_of(solved.plies[0].state_before)
            tests.append(
                {
                    **rec_base,
                    "fen": fen,
                    "position_hash": position_hash(fen),
                    "side_to_move": solved.turn_hypothesis,
                    "question": "beste zet"
                    if caption.get("side") == solved.turn_hypothesis
                    else "beste zet (trait rejoué)",
                    "solution_moves": [notation_of(p.resolved.move) for p in solved.plies],
                    "verified": True,
                }
            )
    return tests, quarantine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--deel", type=int, required=True)
    ap.add_argument("--out", default="data/exports/pcblues")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache or f".cache/pcblues/{args.deel}")
    tests, quarantine = extract_volume(Path(args.pdf), args.deel, cache)

    tpath = out_dir / f"tests_deel{args.deel:02d}.jsonl"
    with tpath.open("w", encoding="utf-8") as fh:
        for rec in tests:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    qpath = out_dir / f"tests_quarantine_deel{args.deel:02d}.jsonl"
    with qpath.open("w", encoding="utf-8") as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    stats = {
        "deel": args.deel,
        "tests_verified": len(tests),
        "quarantined": len(quarantine),
        "license": LICENSE_NOTE,
    }
    print(json.dumps(stats, ensure_ascii=False))
    # Round-trip write -> read (règle smoke-test).
    assert len([json.loads(l) for l in tpath.open(encoding="utf-8")]) == len(tests)
    return 0


if __name__ == "__main__":
    sys.exit(main())
