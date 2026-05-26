"""Regenerate docs/pre_process_corpus/sources_debutant.md from fixtures + scan.

Source of truth:
- `docs/pre_process_corpus/fixtures_debutant.py` (`source`, `source_ref`,
  `crop_id`, `final_move`, `claude_notes`)
- `docs/pre_process_corpus/scan/scan_analysis_debutant.json`
  (`eval_after_pv`, `notes`)

Usage : `python3 scripts/regenerate_sources_doc.py` from the repo root.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "docs" / "pre_process_corpus"
SCAN_FILE = FIXTURES_DIR / "scan" / "scan_analysis_debutant.json"
OUTPUT = FIXTURES_DIR / "sources_debutant.md"

sys.path.insert(0, str(FIXTURES_DIR))
from fixtures_debutant import ALL_BEGINNER_POSITIONS  # type: ignore[import-not-found]  # noqa: E402

SOURCE_SHORT = {
    "CORPUS": "CORPUS",
    "GENERAL_KNOWLEDGE": "GENERAL",
    "INVENTED": "INVENT",
}


def main() -> None:
    scan = json.loads(SCAN_FILE.read_text())

    by_chap: dict[str, list[Any]] = defaultdict(list)
    for p in ALL_BEGINNER_POSITIONS:
        by_chap[p.id.split("_")[1]].append(p)

    total = len(ALL_BEGINNER_POSITIONS)
    src_stats: dict[str, int] = defaultdict(int)
    fm_none = fm_present = divergences = forced_wins = 0
    for p in ALL_BEGINNER_POSITIONS:
        src_stats[p.source.name] += 1
        if p.final_move is None:
            fm_none += 1
        else:
            fm_present += 1
        sc = scan.get(p.id, {})
        if "DIVERGENCE" in sc.get("notes", ""):
            divergences += 1
        if abs(sc.get("eval_after_pv", 0)) >= 99:
            forced_wins += 1

    out: list[str] = []
    out.append("# Sources et traçabilité — Manuel débutant\n")
    out.append(
        "_Audit automatique généré depuis `fixtures_debutant.py` et "
        "`scan/scan_analysis_debutant.json`. Pour régénérer :_ "
        "`python3 scripts/regenerate_sources_doc.py`\n"
    )
    out.append("## Vue d'ensemble\n")
    out.append(f"- **{total} fixtures** au total, réparties sur 16 chapitres")
    out.append(
        f"- **{src_stats['CORPUS']} CORPUS** "
        f"(~{100 * src_stats['CORPUS'] // total} %, extraites du livre Dubois)"
    )
    out.append(
        f"- **{src_stats['GENERAL_KNOWLEDGE']} GENERAL_KNOWLEDGE** "
        f"(~{100 * src_stats['GENERAL_KNOWLEDGE'] // total} %, reconstructions "
        f"Claude depuis règles FMJD canoniques)"
    )
    out.append(
        f"- **{src_stats['INVENTED']} INVENTED** "
        f"(~{100 * src_stats['INVENTED'] // total} %, exemples pédagogiques "
        f"ad-hoc, ch1-2 uniquement)"
    )
    out.append(
        f"- **{fm_present}** fixtures avec `final_move` reconstruit, "
        f"**{fm_none}** avec `final_move=None`"
    )
    out.append(
        f"- **{forced_wins}** fixtures où Scan signale un gain forcé "
        f"(éval `|·| ≥ 99`)"
    )
    out.append(
        f"- **{divergences}** fixtures avec divergence Scan / "
        f"`published_notation` (cf champ `notes` dans "
        f"`scan_analysis_debutant.json`)\n"
    )

    out.append("## Légende des colonnes\n")
    out.append(
        "- **Source** : `CORPUS` = Dubois 2014 ; `GENERAL` = règles FMJD ; "
        "`INVENT` = exemple ad-hoc"
    )
    out.append(
        "- **Réf Dubois** : `source_ref` de la fixture "
        "(`dubois_apprent_combin_<page>_<diag>`)"
    )
    out.append(
        "- **`fm`** : statut du `final_move` reconstruit — "
        "`✓` présent, `∅` `None` (cf `claude_notes`)"
    )
    out.append(
        "- **Scan** : `✓` éval positive cohérente, "
        "`⚠` éval négative (trait adverse ou divergence), "
        "`🔴` divergence flaggée explicitement dans `notes`\n"
    )

    for chap in sorted(by_chap):
        fixtures = sorted(by_chap[chap], key=lambda p: p.id)
        n = chap.lstrip("CH").lstrip("0")
        out.append(f"## Chapitre {n}\n")
        out.append("| Fixture | Source | Réf Dubois | `fm` | Scan | Notes |")
        out.append("|---|---|---|---|---|---|")
        for p in fixtures:
            sc = scan.get(p.id, {})
            src = SOURCE_SHORT[p.source.name]
            ref = p.source_ref if p.source_ref else "—"
            fm = "✓" if p.final_move is not None else "∅"
            ev = sc.get("eval_after_pv", 0)
            has_div = "DIVERGENCE" in sc.get("notes", "")
            if has_div:
                scan_st = "🔴"
            elif ev < 0:
                scan_st = "⚠"
            else:
                scan_st = "✓"
            cn = (p.claude_notes or "").replace("\n", " ").replace("|", "/")[:80]
            if has_div:
                scan_note = (
                    sc.get("notes", "").replace("\n", " ").replace("|", "/")[:80]
                )
                notes = f"🔴 {scan_note} ; {cn}" if cn else f"🔴 {scan_note}"
            else:
                notes = cn or "—"
            notes = notes[:120]
            out.append(
                f"| `{p.id}` | {src} | `{ref}` | {fm} | {scan_st} | {notes} |"
            )
        out.append("")

    out.append("---\n")
    out.append(
        "_Régénération : ce doc est dérivé. Source de vérité : "
        "`docs/pre_process_corpus/fixtures_debutant.py` (champs `source`, "
        "`source_ref`, `crop_id`, `final_move`, `claude_notes`) et "
        "`docs/pre_process_corpus/scan/scan_analysis_debutant.json` "
        "(champs `eval_after_pv`, `notes`)._"
    )

    OUTPUT.write_text("\n".join(out))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(out)} lines)")


if __name__ == "__main__":
    main()
