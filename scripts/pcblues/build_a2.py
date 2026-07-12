"""Assemble l'artefact A2 ``pcblues_combos.jsonl`` (+ manifest) — API gelée.

Fusionne les ``combos_deelNN.jsonl`` par volume en un artefact contractuel
unique, trié (deel, page, id) :

* dédup interne : même ``fen_start`` + même ``seq_moves`` -> la première
  occurrence gagne, les suivantes portent ``dup_of`` (jamais de doublon
  silencieux) ;
* dédup croisée corpus existants : les corpus jass (master-2000,
  0464/combos) sont en jnnw binaire — la clé ``position_hash`` (sha1 du
  FEN) est exposée pour que l'ingestion jass fasse la jointure ; les
  fixtures manuelles dilf sont hashées ici quand le module est importable ;
* manifest : comptes par volume, taux de quarantaine, couverture thèmes,
  licence PC Blues, version d'export (tout changement de format = bump).

Usage::

    python3 -m scripts.pcblues.build_a2 --out data/exports/pcblues
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPORT_VERSION = "pcblues-a2-v1"

LICENSE_NOTE = (
    "PC Blues © Piens Christiaan — attribution obligatoire en reprise "
    "publique, pas de modification. Usage interne entraînement/QA : OK."
)


def _manual_fixture_hashes() -> set[str]:
    """Position hashes of the hand-built dilf fixtures, when importable."""
    try:
        import hashlib
        import sys

        sys.path.insert(0, "docs/pre_process_corpus")
        import fixtures_debutant  # type: ignore

        from pedagogy.game import state_to_fen

        hashes = set()
        for name in dir(fixtures_debutant):
            if name.startswith("ALL_") and name.endswith("_POSITIONS"):
                for fx in getattr(fixtures_debutant, name):
                    state = getattr(fx, "state", None)
                    if state is not None:
                        fen = state_to_fen(state)
                        hashes.add(hashlib.sha1(fen.encode()).hexdigest()[:16])
        return hashes
    except Exception:
        return set()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/exports/pcblues")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)

    records: list[dict] = []
    per_deel: dict[int, dict] = {}
    for path in sorted(out_dir.glob("combos_deel*.jsonl")):
        recs = [json.loads(l) for l in path.open(encoding="utf-8")]
        deel = int(path.stem.replace("combos_deel", ""))
        repaired_path = out_dir / f"repaired_deel{deel:02d}.jsonl"
        repaired = (
            [json.loads(l) for l in repaired_path.open(encoding="utf-8")]
            if repaired_path.exists()
            else []
        )
        records.extend(recs + repaired)
        quarantine_path = out_dir / f"quarantine_deel{deel:02d}.jsonl"
        n_quar = (
            sum(1 for _ in quarantine_path.open(encoding="utf-8"))
            if quarantine_path.exists()
            else None
        )
        total = len(recs) + len(repaired) + (n_quar or 0)
        per_deel[deel] = {
            "combos": len(recs),
            "repaired_4_13": len(repaired),
            "quarantined": n_quar,
            "quarantine_rate": round(n_quar / total, 4) if n_quar is not None and total else None,
        }

    records.sort(key=lambda r: (r["deel"], r["page"], r["id"]))

    seen: dict[tuple, str] = {}
    manual_hashes = _manual_fixture_hashes()
    n_dups = 0
    for rec in records:
        key = (rec["fen_start"], tuple(rec["seq_moves"]))
        if key in seen:
            rec["dup_of"] = seen[key]
            n_dups += 1
        else:
            seen[key] = rec["id"]
            rec.pop("dup_of", None)
        if rec["position_hash"] in manual_hashes:
            rec["dup_position_manual_fixtures"] = True

    combos_path = out_dir / "pcblues_combos.jsonl"
    with combos_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    themes = Counter(t for r in records for t in r["themes"])
    manifest = {
        "artefact": "A2",
        "export_version": EXPORT_VERSION,
        "file": combos_path.name,
        "combos": len(records),
        "dedup_interne_dup_of": n_dups,
        "dedup_croisee": {
            "manual_fixtures_dilf": bool(manual_hashes),
            "master_2000_jnnw": "à faire côté ingestion jass via position_hash/fen_start",
            "0464_combos_jnnw": "à faire côté ingestion jass via position_hash/fen_start",
        },
        "source_deel": {str(d): per_deel[d] for d in sorted(per_deel)},
        "couverture_themes": dict(themes.most_common()),
        "verified": "100% (re-jeu FMJD complet depuis ancre diagramme — rien ne sort sans)",
        "position_hash": "sha1(fen)[:16], clé de dédup croisée",
        "license": LICENSE_NOTE,
    }
    manifest_path = out_dir / "combos_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Round-trip write -> read (règle smoke-test des formats).
    reread = [json.loads(l) for l in combos_path.open(encoding="utf-8")]
    assert len(reread) == len(records)
    assert all("fen_start" in r and "seq_moves" in r and r["verified"] for r in reread)
    print(f"{combos_path} : {len(records)} combos ({n_dups} dup_of), "
          f"volumes {sorted(per_deel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
