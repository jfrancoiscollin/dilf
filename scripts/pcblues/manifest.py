"""J1 — fiche d'identification des 60 volumes PC Blues -> corpus_manifest.json.

Chaque volume reçoit ``{deel, titre, sous_titre, auteurs, release, pages,
famille, priorite, chemin}``. La famille vient de la table du mémo
d'extraction, complétée par mots-clés du titre pour les volumes « divers »
(c'est ainsi que deel 56 « BK reeks - kombinaties 3 », 51/58 « Kombinaties
uit de Ned. Klubkompetitie » et 30/60-62 (eindspelen) ont rejoint leurs
familles). Usage::

    python3 -m scripts.pcblues.manifest --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)

#: deel -> famille, d'après l'inventaire du mémo v2 (table §0).
MEMO_FAMILLES: dict[int, str] = {
    # combinaisons certifiées-jouées
    2: "combinaisons_certifiees", 15: "combinaisons_certifiees",
    23: "combinaisons_certifiees", 37: "combinaisons_certifiees",
    43: "combinaisons_certifiees",
    # tournois BK complets
    1: "tournois_bk", 3: "tournois_bk", 6: "tournois_bk", 19: "tournois_bk",
    20: "tournois_bk", 27: "tournois_bk", 40: "tournois_bk", 44: "tournois_bk",
    45: "tournois_bk", 52: "tournois_bk", 59: "tournois_bk",
    # matériel GMI / élite
    17: "gmi_elite", 21: "gmi_elite", 22: "gmi_elite", 35: "gmi_elite",
    36: "gmi_elite", 42: "gmi_elite",
    # tests de compétence
    47: "tests_competence", 57: "tests_competence",
    # finales
    5: "finales", 49: "finales",
}

#: Mots-clés (minuscules) -> famille, pour classer les « divers » en J1.
KEYWORD_FAMILLES: list[tuple[str, str]] = [
    ("kombinaties", "combinaisons_certifiees"),
    ("eindspel", "finales"),
    ("vaardigheidstest", "tests_competence"),
    ("het bk", "tournois_bk"),
    ("bk 20", "tournois_bk"),
]

#: Priorité d'extraction (ordre §3 du mémo). 1 = premier gisement.
FAMILLE_PRIORITE = {
    "combinaisons_certifiees": 1,
    "gmi_elite": 2,
    "tests_competence": 3,
    "finales": 4,
    "tournois_bk": 5,
    "divers": 6,
}

_TITLE_RE = re.compile(
    r"PC\s+Blues\s*\(?\s*deel\s*(\d+)\s*\)?\s*:?\s*(.{0,120})", re.I
)
_AUTHOR_RE = re.compile(r"Auteur(?:\(s\))?\s*:\s*([^\n]{3,80})")
_RELEASE_RE = re.compile(r"Release\s+[\d.]+\s+(\d{2}-\d{2}-\d{4})")
_DATE_RE = re.compile(r"\b(\d{2}-\d{2}-\d{4})\b")


def volume_path(deel: int, corpus_dir: Path) -> Path:
    local = Path("docs") / f"{deel}.pdf"
    return local if local.exists() else corpus_dir / f"{deel}.pdf"


def _pdf_pages(pdf: Path) -> int:
    out = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    return int(out.split("Pages:")[1].split()[0])


def _first_pages_text(pdf: Path, n: int = 4) -> str:
    return subprocess.check_output(
        ["pdftotext", "-f", "1", "-l", str(n), str(pdf), "-"],
        text=True,
        stderr=subprocess.DEVNULL,
    )


def classify(deel: int, title: str) -> str:
    if deel in MEMO_FAMILLES:
        return MEMO_FAMILLES[deel]
    low = title.lower()
    for kw, fam in KEYWORD_FAMILLES:
        if kw in low:
            return fam
    return "divers"


def build_fiche(deel: int, corpus_dir: Path) -> dict:
    pdf = volume_path(deel, corpus_dir)
    text = _first_pages_text(pdf)
    m = _TITLE_RE.search(text)
    title = None
    if m:
        # Le titre s'arrête à la fin de ligne ; s'il est court c'est qu'il
        # continue sur la ligne suivante ("Een prachtig\nKingsrow - eindspel").
        title = " ".join(m.group(2).split()).strip(" .-:")
        if len(title) < 20:
            # ".{0,120}" ne franchit pas la fin de ligne : un titre court
            # continue sur la ligne suivante du flux texte.
            for line in text[m.end() :].splitlines()[1:3]:
                line = " ".join(line.split())
                if line and "auteur" not in line.lower():
                    title = f"{title} {line}".strip(" .-:")
                    break
    # Le sous-titre est la ligne non vide qui suit le titre dans le flux.
    sous_titre = None
    if m:
        after = text[m.end() : m.end() + 300]
        for line in after.splitlines():
            line = " ".join(line.split())
            if line and "disclaimer" not in line.lower() and "auteur" not in line.lower():
                sous_titre = line[:120]
                break
    authors = _AUTHOR_RE.search(text)
    release = _RELEASE_RE.search(text) or _DATE_RE.search(text)
    famille = classify(deel, title or "")
    return {
        "deel": deel,
        "titre": title,
        "sous_titre": sous_titre,
        "auteurs": " ".join(authors.group(1).split()) if authors else "Piens Christiaan",
        "release": release.group(1) if release else None,
        "pages": _pdf_pages(pdf),
        "famille": famille,
        "priorite": FAMILLE_PRIORITE[famille],
        "chemin": str(pdf),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus-dir", default="docs/corpus/pcblues")
    ap.add_argument("--out", default="data/exports/pcblues")
    args = ap.parse_args(argv)

    corpus_dir = Path(args.corpus_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # deel 38 et 39 n'existent pas dans la numérotation PC Blues.
    deels = [d for d in range(1, 63) if d not in (38, 39)]
    fiches = [build_fiche(d, corpus_dir) for d in deels]

    manifest = {
        "corpus": "PC Blues",
        "volumes": len(fiches),
        "pages_total": sum(f["pages"] for f in fiches),
        "license": LICENSE_NOTE,
        "familles": {
            fam: sorted(f["deel"] for f in fiches if f["famille"] == fam)
            for fam in sorted({f["famille"] for f in fiches})
        },
        "fiches": fiches,
    }
    path = out_dir / "corpus_manifest.json"
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # Round-trip write -> read (règle smoke-test des formats de reporting).
    reread = json.loads(path.read_text(encoding="utf-8"))
    assert reread["volumes"] == len(deels) and len(reread["fiches"]) == len(deels)
    print(f"{path} : {reread['volumes']} volumes, {reread['pages_total']} pages")
    for fam, vols in reread["familles"].items():
        print(f"  {fam}: {vols}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
