"""Assemble l'artefact A5 ``pcblues_tests.jsonl`` (+ manifest) — API gelée.

Fusionne les ``tests_deelNN.jsonl`` (Vaardigheidstesten) en un artefact
contractuel : exercices structurés {position, question, solution}, 100%
vérifiés par re-jeu de la solution depuis le diagramme de la grille.

Usage::

    python3 -m scripts.pcblues.build_a5 --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPORT_VERSION = "pcblues-a5-v1"

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
    for path in sorted(out_dir.glob("tests_deel*.jsonl")):
        if "quarantine" in path.name:
            continue
        deel = int(path.stem.replace("tests_deel", ""))
        recs = [json.loads(l) for l in path.open(encoding="utf-8")]
        records.extend(recs)
        qpath = out_dir / f"tests_quarantine_deel{deel:02d}.jsonl"
        n_quar = sum(1 for _ in qpath.open(encoding="utf-8")) if qpath.exists() else 0
        per_deel[deel] = {"tests": len(recs), "quarantined": n_quar}

    records.sort(key=lambda r: (r["deel"], r["test"], r["item"]))
    a5_path = out_dir / "pcblues_tests.jsonl"
    with a5_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    manifest = {
        "artefact": "A5",
        "export_version": EXPORT_VERSION,
        "file": a5_path.name,
        "tests": len(records),
        "source_deel": {str(d): per_deel[d] for d in sorted(per_deel)},
        "verified": "100% (solution rejouée moteur depuis le diagramme de la "
        "grille — l'appariement item/plateau est validé par la légalité)",
        "license": LICENSE_NOTE,
    }
    (out_dir / "tests_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # Round-trip write -> read (règle smoke-test des formats).
    assert len([json.loads(l) for l in a5_path.open(encoding="utf-8")]) == len(records)
    print(f"A5: {len(records)} tests -> {a5_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
