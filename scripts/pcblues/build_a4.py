"""Assemble l'artefact A4 ``pcblues_endgame_qa.jsonl`` (+ manifest).

Fusionne les ``endgame_deelNN.jsonl`` (QA finales, book_claim) en un
artefact contractuel pour le harnais des prédicats/vetos.

Usage::

    python3 -m scripts.pcblues.build_a4 --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPORT_VERSION = "pcblues-a4-v1"

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/exports/pcblues")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)

    records: list[dict] = []
    per_deel: dict[int, dict] = {}
    for path in sorted(out_dir.glob("endgame_deel*.jsonl")):
        if "quarantine" in path.name:
            continue
        deel = int(path.stem.replace("endgame_deel", ""))
        recs = [json.loads(l) for l in path.open(encoding="utf-8")]
        records.extend(recs)
        qpath = out_dir / f"endgame_quarantine_deel{deel:02d}.jsonl"
        n_quar = sum(1 for _ in qpath.open(encoding="utf-8")) if qpath.exists() else 0
        per_deel[deel] = {"endgames": len(recs), "quarantined": n_quar}

    records.sort(key=lambda r: (r["deel"], r["page"]))
    path = out_dir / "pcblues_endgame_qa.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    manifest = {
        "artefact": "A4",
        "export_version": EXPORT_VERSION,
        "file": path.name,
        "endgames": len(records),
        "source_deel": {str(d): per_deel[d] for d in sorted(per_deel)},
        "book_claim": "TOUS les expected viennent de l'analyse du livre "
        "(book_claim=true) — revalidation moteur À FAIRE côté consommateur "
        "avant tout gate dur (le mémo l'exige quand la profondeur le permet)",
        "verified_position": "les FEN (dames comprises) sont vérifiées par "
        "ancrage-par-re-jeu d'une séquence d'analyse de la page",
        "pilote": "extraction conservatrice (1 plateau/page, claims "
        "déclaratifs uniquement) — rendement volontairement bas, à élargir",
        "license": LICENSE_NOTE,
    }
    (out_dir / "endgame_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    assert len([json.loads(l) for l in path.open(encoding="utf-8")]) == len(records)
    print(f"A4: {len(records)} QA finales -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
