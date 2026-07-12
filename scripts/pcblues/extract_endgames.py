"""A4 — QA finales : ``endgame_deelNN.jsonl`` (pilote : rendus bleus, deel 5).

Pour chaque plateau détecté (dames comprises — rendu bleu : pièces
double-empilées) :

1. la position est VÉRIFIÉE par ancrage-par-re-jeu (au moins une séquence
   d'analyse de la page se rejoue intégralement depuis le diagramme —
   dames incluses, le re-jeu les exerce) ;
2. le verdict vient de l'ANALYSE DU LIVRE : phrase déclarative à mot-clé
   (« gewonnen voor wit/zwart », « remise », « wit/zwart wint ») dans les
   lignes qui suivent la mention « Diagram N » — les interrogatives
   (« Wint wit ? ») sont ignorées. ``book_claim=true`` toujours : la
   revalidation moteur (Scan) est côté jass/backend, pas ici.

Prudence > volume : sans claim clair OU sans ancrage re-jeu, pas de record.

Usage::

    python3 -m scripts.pcblues.extract_endgames --pdf docs/5.pdf --deel 5 \
        --out data/exports/pcblues --cache .cache/pcblues/5
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .boards import boards_of_page
from .extract_combos import LICENSE_NOTE, board_to_state, page_text, position_hash
from .notation import extract_runs
from .replay import anchor_run, fen_of

#: (regex, gagnant absolu) — phrases déclaratives uniquement.
_CLAIMS = [
    (re.compile(r"gewonnen voor wit|wit wint(?!\s*\?)|winst voor wit", re.I), "white"),
    (re.compile(r"gewonnen voor zwart|zwart wint(?!\s*\?)|winst voor zwart", re.I), "black"),
    # « remise gegeven/overeengekomen » = résultat de partie (les joueurs
    # ont conclu), PAS un verdict d'analyse — exclu (⛔ Result ≠ label).
    (re.compile(r"\bremise\b(?!\s*\?)(?!\s+(gegeven|overeengekomen))", re.I), "draw"),
]


def _claim_near_diagram(text: str) -> tuple[str, str] | None:
    """(gagnant, phrase) du claim le plus proche d'une mention Diagram."""
    lines = text.splitlines()
    diagram_lines = [i for i, l in enumerate(lines) if re.search(r"\bdiagram\b", l, re.I)]
    if not diagram_lines:
        diagram_lines = [0]
    for start in diagram_lines:
        for line in lines[start : start + 15]:
            if "?" in line:
                continue
            for rx, winner in _CLAIMS:
                m = rx.search(line)
                if m:
                    return winner, " ".join(line.split())[:160]
    return None


def extract_volume(pdf: Path, deel: int, cache: Path) -> tuple[list[dict], list[dict]]:
    n_pages = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )
    records: list[dict] = []
    quarantine: list[dict] = []
    seen_hashes: set[str] = set()
    for page in range(1, n_pages + 1):
        boards = boards_of_page(pdf, page, cache)
        if len(boards) != 1:
            continue  # pilote conservateur : 1 plateau/page, pairage sûr
        board = boards[0]
        if not (board.white_men or board.white_kings) or not (
            board.black_men or board.black_kings
        ):
            continue
        text = page_text(pdf, page)
        claim = _claim_near_diagram(text)
        state0 = board_to_state(board)

        anchored = None
        for run in extract_runs(text):
            if len(run.tokens) < 3:
                continue
            res = anchor_run(state0, run)
            if res.ok:
                anchored = res
                break

        base = {
            "id": f"pcblues-endgame-d{deel:02d}-p{page:03d}",
            "deel": deel,
            "page": page,
        }
        if claim is None or anchored is None:
            quarantine.append(
                {
                    **base,
                    "reason": ("pas de claim déclaratif" if claim is None else "")
                    + ("" if anchored is not None else " position non ancrée par re-jeu"),
                }
            )
            continue

        winner, sentence = claim
        side = anchored.turn_hypothesis
        expected = (
            "DRAW"
            if winner == "draw"
            else ("WIN" if winner == side else "LOSS")
        )
        fen = fen_of(anchored.plies[0].state_before)
        if position_hash(fen) in seen_hashes:
            continue
        seen_hashes.add(position_hash(fen))
        records.append(
            {
                **base,
                "fen": fen,
                "position_hash": position_hash(fen),
                "side_to_move": side,
                "expected": expected,
                "rationale_courte": sentence,
                "book_claim": True,
                "replay_anchored": True,
                "kings": {
                    "white": list(anchored.plies[0].state_before.white_kings),
                    "black": list(anchored.plies[0].state_before.black_kings),
                },
                "verified_position": True,
            }
        )
    return records, quarantine


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
    records, quarantine = extract_volume(Path(args.pdf), args.deel, cache)

    path = out_dir / f"endgame_deel{args.deel:02d}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (out_dir / f"endgame_quarantine_deel{args.deel:02d}.jsonl").open(
        "w", encoding="utf-8"
    ) as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "deel": args.deel,
                "endgames": len(records),
                "quarantined": len(quarantine),
                "license": LICENSE_NOTE,
            },
            ensure_ascii=False,
        )
    )
    assert len([json.loads(l) for l in path.open(encoding="utf-8")]) == len(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
