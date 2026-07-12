"""Assemble l'artefact A2-bis Dubois ``dubois_combos.jsonl`` (+ manifest).

Fusionne les ``combos_<source>.jsonl`` (volumes Dubois raffinés par
`extract_dubois`) en un artefact contractuel, avec :

* dédup interne (même ``fen_start`` + même ``seq_moves``) → ``dup_of`` ;
* **dédup croisée avec pcblues** par ``position_hash`` : les positions déjà
  présentes dans `pcblues_combos.jsonl` portent ``dup_of_pcblues=true``
  (jamais écartées silencieusement — un même motif dans deux corpus reste
  traçable) ;
* manifest versionné (comptes par source, couverture thèmes, licence).

Usage::

    python3 -m scripts.pcblues.build_dubois --out data/exports/dubois \
        --pcblues data/exports/pcblues/pcblues_combos.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

EXPORT_VERSION = "dubois-a2bis-v1"

LICENSE_NOTE = (
    "J.-P. Dubois — corpus FMJD. Vérifier les droits avant reprise "
    "publique. Usage interne entraînement/QA."
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/exports/dubois")
    ap.add_argument(
        "--pcblues",
        default="data/exports/pcblues/pcblues_combos.jsonl",
        help="corpus pcblues pour la dédup croisée (position_hash)",
    )
    args = ap.parse_args(argv)
    out_dir = Path(args.out)

    pcblues_hashes: set[str] = set()
    pc_path = Path(args.pcblues)
    if pc_path.exists():
        for line in pc_path.open(encoding="utf-8"):
            rec = json.loads(line)
            if rec.get("position_hash"):
                pcblues_hashes.add(rec["position_hash"])

    records: list[dict] = []
    per_source: dict[str, dict] = {}
    for path in sorted(out_dir.glob("combos_*.jsonl")):
        source = path.stem.replace("combos_", "")
        recs = [json.loads(l) for l in path.open(encoding="utf-8")]
        records.extend(recs)
        stats_path = out_dir / f"stats_{source}.json"
        stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
        per_source[source] = {
            "combos": len(recs),
            "quarantined": stats.get("quarantined"),
            "quarantine_rate": stats.get("quarantine_rate"),
        }

    records.sort(key=lambda r: (r["source"], r.get("serie", ""), r.get("diagram", 0)))
    seen: dict[tuple, str] = {}
    n_dup = n_cross = n_trunc = 0
    for rec in records:
        key = (rec["fen_start"], tuple(rec["seq_moves"]))
        if key in seen:
            rec["dup_of"] = seen[key]
            n_dup += 1
        else:
            seen[key] = rec["id"]
            rec.pop("dup_of", None)
        if rec["position_hash"] in pcblues_hashes:
            rec["dup_of_pcblues"] = True
            n_cross += 1
        if rec.get("truncated_at_variation"):
            n_trunc += 1

    combos_path = out_dir / "dubois_combos.jsonl"
    with combos_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    themes = Counter(t for r in records for t in r.get("themes", []))
    manifest = {
        "artefact": "A2-bis (Dubois)",
        "export_version": EXPORT_VERSION,
        "file": combos_path.name,
        "combos": len(records),
        "dedup_interne_dup_of": n_dup,
        "dedup_croisee_pcblues": n_cross,
        "truncated_at_variation": n_trunc,
        "source": {s: per_source[s] for s in sorted(per_source)},
        "couverture_themes": dict(themes.most_common()),
        "verified": "100% (re-jeu FMJD depuis position pixel-extraite "
        "extract_diagrams, trait explicite ; queues variantes tronquées au "
        "plus long préfixe légal terminant sur rafle)",
        "position_hash": "sha1(fen)[:16], clé de dédup croisée",
        "license": LICENSE_NOTE,
    }
    (out_dir / "dubois_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    reread = [json.loads(l) for l in combos_path.open(encoding="utf-8")]
    assert len(reread) == len(records) and all(r["verified"] for r in reread)
    print(
        f"{combos_path} : {len(records)} combos "
        f"({n_dup} dup_of, {n_cross} recouvrent pcblues, {n_trunc} tronqués)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
