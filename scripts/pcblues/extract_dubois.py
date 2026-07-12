"""C2 — raffinerie sur le corpus Dubois FMJD (livres d'exercices structurés).

Les volumes Dubois « combinaisons » sont des livres d'exercices au format
natif de `scripts/extract_diagrams.py` (celui pour lequel il a été
construit) :

* pages-grilles « Série n°X-Y » avec 12 diagrammes D1-D12, légende
  « D<k> : trait aux blancs/noirs » (le TRAIT est explicite → pas
  d'hypothèse à faire, contrairement à pcblues) ;
* sections « SOLUTIONS SERIE N°X-Y » avec, par exercice,
  « D<k> :  <séquence> » (parfois préfixée du nom du joueur), notation
  identique à pcblues (coups + réponses entre parenthèses).

Pipeline : extract_diagrams (position + trait + DAMES, classification
pixel prouvée 98,8 % sur Dubois) → appariement (série, D<k>) diagramme ↔
solution → **ancrage-par-re-jeu** (la solution se rejoue depuis le
diagramme, trait connu) → combo A2-bis `verified=true`. Mêmes gates que
pcblues : re-jeu FMJD, quarantaine diagnostiquée, thèmes ALL_DETECTORS,
`position_hash` pour la dédup croisée.

Usage::

    python3 -m scripts.pcblues.extract_dubois \
        --pdf docs/corpus/jpdubois_expert_combinaisons_V2.pdf \
        --source dubois_expert_combinaisons --out data/exports/dubois \
        --cache .cache/dubois_exp
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from pedagogy.game import GameState, state_to_fen

from .extract_combos import position_hash
from .notation import extract_runs
from .replay import anchor_run, notation_of, replay_tokens, themes_of

LICENSE_NOTE = (
    "J.-P. Dubois — corpus FMJD. Domaine/usage : vérifier les droits avant "
    "reprise publique. Usage interne entraînement/QA."
)

_SERIE_GRID_RE = re.compile(r"Série\s+n°(\d+(?:-\d+)?)", re.I)
#: Header de solutions : « SERIE N°X-Y » (chapitre-local) OU « N°27 »
#: (numérotation globale — incohérence des chapitres 6-7 de expert_combi).
_SERIE_SOL_RE = re.compile(r"SOLUTIONS\s+SERIE\s+N°(\d+(?:-\d+)?)", re.I)
#: Ligne de solution : "D<k> : <corps>" où le corps contient des coups
#: (au moins un token NN-NN / NNxNN), pas « trait aux ».
_SOL_ENTRY_RE = re.compile(r"^\s*D(\d+)\s*:\s*(.+)$")
_HAS_MOVE = re.compile(r"\d{1,2}[-x]\d{1,2}")
_CAPTION_RE = re.compile(r"D(\d+)\s*:\s*trait aux (blancs|noirs)", re.I)


def _pages(pdf: Path) -> int:
    return int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        .split("Pages:")[1]
        .split()[0]
    )


def _render_extract(pdf: Path, cache: Path, n_pages: int) -> list[dict]:
    """Lance extract_diagrams render+extract sur tout le volume."""
    subprocess.run(
        [
            sys.executable, "-m", "scripts.extract_diagrams", "render",
            "--pdf", str(pdf), "--pages", f"1-{n_pages}", "--cache", str(cache),
        ],
        check=True, capture_output=True,
    )
    subprocess.run(
        [
            sys.executable, "-m", "scripts.extract_diagrams", "extract",
            "--cache", str(cache),
        ],
        check=True, capture_output=True,
    )
    return json.loads((cache / "extracted.json").read_text())


def _serie_by_page(pdf: Path, n_pages: int) -> dict[int, str]:
    """Page (1-based) -> série active (dernier en-tête « Série n°X-Y » vu)."""
    out: dict[int, str] = {}
    current = None
    for page in range(1, n_pages + 1):
        text = subprocess.check_output(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
            text=True,
        )
        m = _SERIE_GRID_RE.search(text)
        if m:
            current = m.group(1)
        if current:
            out[page] = current
    return out


def _solutions(
    pdf: Path, n_pages: int
) -> tuple[dict[tuple[str, int], str], dict[int, list[str]]]:
    """Parse les solutions, série-agnostique.

    Renvoie ``(par_serie, par_dnum)`` :
    * ``par_serie[(série, D)] = texte`` quand un header « SOLUTIONS SERIE
      N°X » précède (appariement précis, volumes type expert) ;
    * ``par_dnum[D] = [textes]`` — index GLOBAL de toutes les entrées
      « D<k> : <coups> » du volume, quel que soit le format (volumes sans
      série : apprentissage/perfectionnement). Le re-jeu élit la bonne.

    Une entrée solution = ligne « D<k> : » contenant au moins un coup (pas
    « D<k> : trait aux », qui est une légende de grille). Les lignes
    suivantes porteuses de coups sont accumulées (solution multi-lignes).
    """
    by_serie: dict[tuple[str, int], list[str]] = {}
    by_dnum: dict[int, list[str]] = {}
    current_serie = None
    cur_serie_key: tuple[str, int] | None = None
    cur_dnum: int | None = None
    cur_lines: list[str] = []

    def flush():
        nonlocal cur_dnum, cur_lines, cur_serie_key
        if cur_dnum is not None and cur_lines:
            txt = "\n".join(cur_lines)
            by_dnum.setdefault(cur_dnum, []).append(txt)
            if cur_serie_key is not None:
                by_serie.setdefault(cur_serie_key, []).append(txt)
        cur_dnum, cur_lines, cur_serie_key = None, [], None

    for page in range(1, n_pages + 1):
        text = subprocess.check_output(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
            text=True,
        )
        for line in text.splitlines():
            ms = _SERIE_SOL_RE.search(line)
            if ms:
                flush()
                current_serie = ms.group(1)
                continue
            me = _SOL_ENTRY_RE.match(line)
            if me and _HAS_MOVE.search(me.group(2)) and "trait aux" not in me.group(2).lower():
                flush()
                cur_dnum = int(me.group(1))
                cur_serie_key = (current_serie, cur_dnum) if current_serie else None
                cur_lines = [me.group(2)]
            elif cur_dnum is not None and _HAS_MOVE.search(line) and "trait aux" not in line.lower():
                cur_lines.append(line)
            elif cur_dnum is not None and not line.strip():
                flush()  # ligne vide = fin d'une solution
    flush()
    return (
        {k: v[0] for k, v in by_serie.items()},
        {k: v for k, v in by_dnum.items()},
    )


def _diagram_state(rec: dict) -> GameState:
    return GameState(
        white_men=frozenset(rec.get("white_men", [])),
        white_kings=frozenset(rec.get("white_kings", [])),
        black_men=frozenset(rec.get("black_men", [])),
        black_kings=frozenset(rec.get("black_kings", [])),
        turn=rec.get("turn", "white"),
    )


def extract_volume(
    pdf: Path, source: str, cache: Path
) -> tuple[list[dict], list[dict]]:
    n_pages = _pages(pdf)
    extracted = _render_extract(pdf, cache, n_pages)
    serie_of = _serie_by_page(pdf, n_pages)
    # sols : appariement précis par (série,D) ; by_dnum : index global par
    # D-numéro (volume-agnostique, re-jeu élit la bonne parmi les candidats).
    sols, by_dnum = _solutions(pdf, n_pages)

    combos: list[dict] = []
    quarantine: list[dict] = []
    for rec in extracted:
        page = rec["page"]
        cap = rec.get("caption_text") or ""
        mcap = _CAPTION_RE.search(cap)
        if not mcap:
            continue  # crop hors-grille (page narrative)
        dk = int(mcap.group(1))
        serie = serie_of.get(page)  # peut être None (volumes sans « Série n°X-Y »)
        key = (serie, dk) if serie else None
        base = {
            "source": source,
            "serie": serie,
            "diagram": dk,
            "page": page,
            "crop_id": rec.get("crop_id"),
        }
        state0 = _diagram_state(rec)
        # Candidats solution : la label-matchée d'abord, puis toutes celles de
        # même D-numéro (fallback replay-protégé pour headers incohérents).
        candidates: list[str] = []
        if key is not None and key in sols:
            candidates.append(sols[key])
        candidates.extend(t for t in by_dnum.get(dk, []) if t not in candidates)
        if not candidates:
            quarantine.append({**base, "reason": "solution absente pour (série,D)"})
            continue

        run = None
        res = None
        for sol_text in candidates:
            cruns = [r for r in extract_runs(sol_text) if r.tokens]
            if not cruns:
                continue
            cand_run = cruns[0]
            cand_res = replay_tokens(state0, cand_run.tokens, state0.turn)
            if cand_res.ok:
                run, res = cand_run, cand_res
                break
            if run is None:  # garder la 1re (label-matchée) pour le fallback/quarantaine
                run, res = cand_run, cand_res
        if run is None:
            quarantine.append({**base, "reason": "solution sans coup parsable"})
            continue
        truncated = False
        if not res.ok:
            # 2e chance : anchor_run (essaie les deux traits, au cas où la
            # caption trait serait ambiguë)
            alt = anchor_run(state0, run)
            if alt.ok:
                res = alt
        if not res.ok:
            # 3e chance : la QUEUE de la solution est souvent contaminée par
            # des variantes/analyse (lignes « 35… », branches) appendées au
            # texte multi-lignes. Le plus long PRÉFIXE légal se terminant sur
            # une rafle EST la combinaison (reste verified=true par re-jeu).
            k = res.failed_at or 0
            while k >= 3:
                prefix = run.tokens[:k]
                if prefix[-1].capture:
                    pref_res = replay_tokens(state0, prefix, state0.turn)
                    if pref_res.ok:
                        res = pref_res
                        truncated = True
                        break
                k -= 1
        if not res.ok:
            quarantine.append(
                {
                    **base,
                    "tokens": [
                        f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in run.tokens
                    ],
                    "reason": f"solution ne se rejoue pas depuis le diagramme : {res.failure}",
                }
            )
            continue

        fen_start = state_to_fen(res.plies[0].state_before)
        seq = ",".join(f"{t.frm}{'x' if t.capture else '-'}{t.to}" for t in run.tokens)
        cid = f"dubois-{source[:8]}-s{serie}-d{dk}-{hashlib.sha1(seq.encode()).hexdigest()[:8]}"
        final_capture = None
        for ply in reversed(res.plies):
            if ply.resolved.move.is_capture:
                final_capture = "x".join(str(s) for s in ply.resolved.move.path)
                break
        combos.append(
            {
                "id": cid,
                "fen_start": fen_start,
                "position_hash": position_hash(fen_start),
                "seq_moves": [notation_of(p.resolved.move) for p in res.plies],
                "final_rafle": final_capture,
                "themes": themes_of(res.plies),
                "source": source,
                "serie": serie,
                "diagram": dk,
                "page": page,
                "side_to_move": state0.turn,
                "truncated_at_variation": truncated,
                "verified": True,
            }
        )
    return combos, quarantine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--source", required=True, help="tag de provenance (nom du volume)")
    ap.add_argument("--out", default="data/exports/dubois")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache or f".cache/dubois/{pdf.stem}")
    combos, quarantine = extract_volume(pdf, args.source, cache)

    cpath = out_dir / f"combos_{args.source}.jsonl"
    with cpath.open("w", encoding="utf-8") as fh:
        for rec in combos:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    qpath = out_dir / f"quarantine_{args.source}.jsonl"
    with qpath.open("w", encoding="utf-8") as fh:
        for rec in quarantine:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(combos) + len(quarantine)
    stats = {
        "source": args.source,
        "pdf": pdf.name,
        "combos_verified": len(combos),
        "quarantined": len(quarantine),
        "quarantine_rate": round(len(quarantine) / total, 4) if total else None,
        "license": LICENSE_NOTE,
    }
    (out_dir / f"stats_{args.source}.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False)
    )
    print(json.dumps(stats, ensure_ascii=False))
    # round-trip write -> read (règle smoke-test)
    assert len([json.loads(l) for l in cpath.open(encoding="utf-8")]) == len(combos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
