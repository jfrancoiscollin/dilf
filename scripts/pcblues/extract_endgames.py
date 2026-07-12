"""A4 — QA finales : ``endgame_deelNN.jsonl`` (tous rendus, dames comprises).

Pour chaque plateau détecté d'une page (multi-plateaux supporté) :

1. **détection des dames par hypothèse-re-jeu** (bois/gris) : les pièces
   sont classées par extension verticale (une dame = disque double-empilé,
   plus haut) puis on essaie de promouvoir les préfixes de candidats. Le
   re-jeu d'une ligne d'analyse tranche, et la royauté retenue est
   **MINIMISÉE** (toute dame dont le retrait garde la ligne re-jouable est
   démotée) → seules les dames NÉCESSAIRES restent, donc la seule
   interprétation sûre (un pion promu à tort se démote). Le rendu bleu fixe
   déjà les dames (analyze_board_color) → hypothèse unique ;
2. la position est VÉRIFIÉE par ce re-jeu intégral (dames exercées) ;
3. le verdict vient de l'ANALYSE DU LIVRE : phrase déclarative à mot-clé
   (« gewonnen voor wit/zwart », « remise », « wit/zwart wint ») ; les
   interrogatives (« Wint wit ? ») et « remise gegeven » (résultat, pas
   verdict) sont exclues. ``book_claim=true`` toujours : la revalidation
   moteur (Scan) est côté jass/backend, pas ici.

Pairage claim ↔ plateau : émis seulement si #claims == #plateaux ancrés
(ordre de lecture) ou 1/1 ; sinon quarantaine (pas de devinette).
Prudence > volume : sans claim clair, sans ancrage, ou pairage ambigu, rien.

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

from pedagogy.game import GameState

from .boards import DetectedBoard, boards_of_page, piece_vertical_extent
from .extract_combos import LICENSE_NOTE, board_to_state, page_text, position_hash
from .notation import extract_runs
from .replay import anchor_run, fen_of

#: Extension verticale au-delà de laquelle une pièce est candidate-dame
#: (loose : le ranking prime, le re-jeu tranche). Cap d'hypothèses pour
#: borner le coût combinatoire sur les plateaux chargés.
KING_EXTENT_MIN = 0.60
MAX_KING_CANDIDATES = 5


def _king_hypotheses(gray, board: DetectedBoard) -> list[tuple[frozenset, frozenset]]:
    """(white_kings, black_kings) à essayer, ordonnées par plausibilité.

    Les rendus bleus fixent déjà les dames (analyze_board_color) → une
    seule hypothèse. Sinon (bois/gris) on classe les pièces par extension
    verticale décroissante et on essaie de promouvoir les préfixes de
    candidats (0, 1, …). Le re-jeu + le gate de validation (chaque dame
    promue doit être exercée par la ligne) écartent les mauvaises
    hypothèses — jamais de FEN silencieusement fausse.
    """
    if board.white_kings or board.black_kings:
        return [(frozenset(board.white_kings), frozenset(board.black_kings))]
    pieces = [(sq, "w") for sq in board.white_men] + [
        (sq, "b") for sq in board.black_men
    ]
    ranked = sorted(
        pieces,
        key=lambda p: piece_vertical_extent(gray, board.bbox, p[0]),
        reverse=True,
    )
    candidates = [
        p
        for p in ranked
        if piece_vertical_extent(gray, board.bbox, p[0]) >= KING_EXTENT_MIN
    ][:MAX_KING_CANDIDATES]

    hyps: list[tuple[frozenset, frozenset]] = [(frozenset(), frozenset())]
    for k in range(1, len(candidates) + 1):
        wk = frozenset(sq for sq, c in candidates[:k] if c == "w")
        bk = frozenset(sq for sq, c in candidates[:k] if c == "b")
        hyps.append((wk, bk))
    return hyps


def _state_with_kings(
    board: DetectedBoard, wk: frozenset, bk: frozenset
) -> GameState:
    white = set(board.white_men) | set(board.white_kings)
    black = set(board.black_men) | set(board.black_kings)
    # auto-promotion rangée (règle §4.4) conservée
    wk = set(wk) | {s for s in white if 1 <= s <= 5}
    bk = set(bk) | {s for s in black if 46 <= s <= 50}
    return GameState(
        white_men=frozenset(white - wk),
        white_kings=frozenset(wk & white),
        black_men=frozenset(black - bk),
        black_kings=frozenset(bk & black),
        turn="white",
    )


def _replays(board: DetectedBoard, wk: frozenset, bk: frozenset, run) -> object | None:
    state0 = _state_with_kings(board, wk, bk)
    res = anchor_run(state0, run)
    return res if (res.ok and _kings_exercised(res)) else None


def _minimize_kings(
    board: DetectedBoard, wk: frozenset, bk: frozenset, run
) -> tuple[frozenset, frozenset] | None:
    """Réduit (wk,bk) au plus petit ensemble de dames qui garde la ligne.

    Ferme le trou de correction du gate d'exercice : un pion promu à tort
    en dame, dont le coup joué est aussi légal en pion, se fait DÉMOTER ici
    (le re-jeu tient sans sa royauté). Une vraie dame reste (son retrait
    casse le re-jeu). Le résultat = interprétation à dames NÉCESSAIRES,
    donc la seule sûre. ``None`` si la minimisation n'aboutit pas.
    """
    wk, bk = set(wk), set(bk)
    changed = True
    while changed:
        changed = False
        for sq in sorted(wk):
            if _replays(board, frozenset(wk - {sq}), frozenset(bk), run):
                wk.discard(sq)
                changed = True
        for sq in sorted(bk):
            if _replays(board, frozenset(wk), frozenset(bk - {sq}), run):
                bk.discard(sq)
                changed = True
    return _minimal_result(board, frozenset(wk), frozenset(bk), run)


def _minimal_result(board, wk, bk, run):
    res = _replays(board, wk, bk, run)
    return (wk, bk, res) if res else None


def _kings_exercised(res) -> bool:
    """Chaque dame de la position de départ est-elle exercée par la ligne ?

    Une dame jamais bougée ni capturée dans la séquence d'ancrage a une
    royauté NON validée par le re-jeu (un pion à sa place aurait pu donner
    la même ligne) → on refuse (règle prudence > volume). Gate de
    correction des hypothèses-dames.
    """
    start = res.plies[0].state_before
    kings = set(start.white_kings) | set(start.black_kings)
    if not kings:
        return True
    touched: set[int] = set()
    for ply in res.plies:
        mv = ply.resolved.move
        touched.add(mv.from_square)
        touched.update(mv.captures)
    return kings <= touched

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


def _claims_in_order(text: str) -> list[tuple[str, str]]:
    """Tous les claims déclaratifs de la page, en ordre de lecture.

    Sert au pairage multi-plateaux : chaque diagramme d'une page-grille de
    finales a son claim (« Diagram N : … gewonnen voor wit »). On les
    collecte séquentiellement ; le pairage n'émet que si leur nombre égale
    celui des plateaux ancrés (sinon quarantaine, pas de devinette).
    """
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        if "?" in line:
            continue
        for rx, winner in _CLAIMS:
            m = rx.search(line)
            if m:
                out.append((winner, " ".join(line.split())[:160]))
                break
    return out


def extract_volume(pdf: Path, deel: int, cache: Path) -> tuple[list[dict], list[dict]]:
    n_pages = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )
    import numpy as np
    from PIL import Image

    records: list[dict] = []
    quarantine: list[dict] = []
    seen_hashes: set[str] = set()
    for page in range(1, n_pages + 1):
        boards = boards_of_page(pdf, page, cache)
        boards = [
            b
            for b in boards
            if (b.white_men or b.white_kings) and (b.black_men or b.black_kings)
        ]
        if not boards:
            continue
        text = page_text(pdf, page)
        claims = _claims_in_order(text)
        gray = np.asarray(
            Image.open(cache / f"page_{page:04d}.png").convert("L"), dtype=float
        )
        runs = [r for r in extract_runs(text) if len(r.tokens) >= 3]

        # Ancrer chaque plateau : hypothèses-dames ordonnées, re-jeu +
        # gate d'exercice des dames tranchent.
        anchored_boards: list[tuple[int, object]] = []  # (board_index, ReplayResult)
        for bi, board in enumerate(boards):
            got = None
            for wk, bk in _king_hypotheses(gray, board):
                state0 = _state_with_kings(board, wk, bk)
                for run in runs:
                    res = anchor_run(state0, run)
                    if res.ok and _kings_exercised(res):
                        # Minimiser : ne garder que les dames NÉCESSAIRES
                        # (ferme le trou pion-promu-à-tort).
                        mini = _minimize_kings(board, wk, bk, run)
                        if mini is not None:
                            got = mini[2]
                        break
                if got is not None:
                    break
            if got is not None:
                anchored_boards.append((bi, got))

        # Pairage claim ↔ plateau : sûr seulement si autant de claims que de
        # plateaux ancrés (ordre de lecture), ou 1 claim / 1 plateau.
        if not anchored_boards:
            continue
        if len(claims) == len(anchored_boards):
            pairing = list(zip(anchored_boards, claims))
        elif len(claims) == 1 and len(anchored_boards) == 1:
            pairing = [(anchored_boards[0], claims[0])]
        else:
            for bi, _ in anchored_boards:
                quarantine.append(
                    {
                        "id": f"pcblues-endgame-d{deel:02d}-p{page:03d}-b{bi}",
                        "deel": deel,
                        "page": page,
                        "reason": f"pairage claim/plateau ambigu "
                        f"({len(claims)} claims, {len(anchored_boards)} plateaux)",
                    }
                )
            continue

        for (bi, anchored), claim in pairing:
            base = {
                "id": f"pcblues-endgame-d{deel:02d}-p{page:03d}-b{bi}",
                "deel": deel,
                "page": page,
            }
            if claim is None:
                continue
            winner, sentence = claim
            side = anchored.turn_hypothesis
            expected = (
                "DRAW"
                if winner == "draw"
                else ("WIN" if winner == side else "LOSS")
            )
            start = anchored.plies[0].state_before
            fen = fen_of(start)
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
                        "white": list(start.white_kings),
                        "black": list(start.black_kings),
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
