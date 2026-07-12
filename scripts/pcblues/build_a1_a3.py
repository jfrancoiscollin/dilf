"""Assemble A1 (``pcblues_games.pdn``) et A3 (``pcblues_prefs_graded.jsonl``).

* A1 : concatène les ``games_deelNN.pdn`` par volume (parties complètes,
  100% rejouées moteur — le PDN émis est la notation reconstruite).
* A3 : fusionne les ``prefs_deelNN.jsonl`` (parties complètes) et les
  ``graded_moves`` des combos A2 (fragments annotés — la source majeure).
  Schéma d'une ligne : ``{fen, move_played, grade, annotator, deel, page}``
  (+ provenance players/event/year/source).

Usage::

    python3 -m scripts.pcblues.build_a1_a3 --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPORT_VERSION_A1 = "pcblues-a1-v1"
EXPORT_VERSION_A3 = "pcblues-a3-v1"

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/exports/pcblues")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)

    # ---- A1 : PDN ----
    pdn_parts: list[str] = []
    games_per_deel: dict[int, int] = {}
    for path in sorted(out_dir.glob("games_deel*.pdn")):
        deel = int(path.stem.replace("games_deel", ""))
        content = path.read_text(encoding="utf-8").strip()
        if content:
            pdn_parts.append(content)
        games_per_deel[deel] = content.count('[Result "') if content else 0
    a1_path = out_dir / "pcblues_games.pdn"
    a1_path.write_text("\n\n".join(pdn_parts) + "\n", encoding="utf-8")

    a1_manifest = {
        "artefact": "A1",
        "export_version": EXPORT_VERSION_A1,
        "file": a1_path.name,
        "games": sum(games_per_deel.values()),
        "source_deel": {str(d): n for d, n in sorted(games_per_deel.items())},
        "verified": "100% (re-jeu FMJD intégral depuis la position initiale ; "
        "partie non-rejouable = quarantainée entière)",
        "warning_result": "Result = provenance uniquement, JAMAIS label WDL",
        "license": LICENSE_NOTE,
    }
    (out_dir / "games_manifest.json").write_text(
        json.dumps(a1_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---- A3 : prefs graduées ----
    prefs: list[dict] = []
    for path in sorted(out_dir.glob("prefs_deel*.jsonl")):
        for line in path.open(encoding="utf-8"):
            rec = json.loads(line)
            rec["source"] = "partie_complete"
            prefs.append(rec)
    for path in sorted(out_dir.glob("combos_deel*.jsonl")):
        deel = int(path.stem.replace("combos_deel", ""))
        for line in path.open(encoding="utf-8"):
            combo = json.loads(line)
            for g in combo.get("graded_moves", []):
                prefs.append(
                    {
                        "fen": g["fen"],
                        "move_played": g["move"],
                        "grade": g["grade"],
                        "annotator": None,
                        "deel": deel,
                        "page": combo["page"],
                        "players": combo.get("players"),
                        "event": combo.get("event"),
                        "year": combo.get("year"),
                        "source": f"combo:{combo['id']}",
                    }
                )
    # dédup exacte (même fen + même coup + même grade)
    seen: set[tuple] = set()
    unique: list[dict] = []
    for rec in prefs:
        key = (rec["fen"], rec["move_played"], rec["grade"])
        if key not in seen:
            seen.add(key)
            unique.append(rec)

    a3_path = out_dir / "pcblues_prefs_graded.jsonl"
    with a3_path.open("w", encoding="utf-8") as fh:
        for rec in unique:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    grades = Counter(r["grade"] for r in unique)
    a3_manifest = {
        "artefact": "A3",
        "export_version": EXPORT_VERSION_A3,
        "file": a3_path.name,
        "prefs": len(unique),
        "dedup_dropped": len(prefs) - len(unique),
        "grades": dict(grades.most_common()),
        "positives_certifiees": grades.get("!", 0) + grades.get("!!", 0),
        "negatives_certifiees": grades.get("?", 0) + grades.get("??", 0),
        "note_negatives": "paire négative : le coup joué est DOMINÉ — "
        "exploitation côté jass (inversion de préférence ou meilleur coup "
        "annoté si donné)",
        "verified": "chaque fen/move provient d'une séquence rejouée moteur",
        "license": LICENSE_NOTE,
    }
    (out_dir / "prefs_manifest.json").write_text(
        json.dumps(a3_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Round-trip write -> read (règle smoke-test des formats).
    assert len([json.loads(l) for l in a3_path.open(encoding="utf-8")]) == len(unique)
    print(f"A1: {a1_manifest['games']} parties -> {a1_path}")
    print(f"A3: {len(unique)} prefs ({dict(grades)}) -> {a3_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
