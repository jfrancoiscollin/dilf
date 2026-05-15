"""Validateur cross-référence prose / fixtures pour les manuels Draught Master.

À lancer en fin de production de chaque manuel pour détecter les
désynchronisations entre le texte du manuel (manuel_<niveau>.md) et les
positions réelles des fixtures (fixtures_<niveau>.py).

Le validateur cherche, pour chaque référence `<PREFIX>_CHnn_mmm` dans
le manuel prose, les nombres mentionnés dans le paragraphe associé et
les compare aux cases réellement présentes dans la fixture. Signale :

  - Les cases mentionnées dans la prose mais ABSENTES de l'état de la
    fixture (potentielle invention).
  - Les références à des fixtures qui n'existent pas.

Usage :
    # Validation du manuel Débutant (par défaut) :
    python validate_prose_vs_fixtures.py

    # Validation d'un autre manuel :
    MANUEL_MD=manuel_intermediaire.md \\
    FIXTURES_MODULE=fixtures_intermediaire \\
    python validate_prose_vs_fixtures.py

Configuration :
- DILF_ROOT (var d'env) : chemin vers le repo dilf cloné (héritée des
  autres scripts).
- FIXTURES_MODULE (var d'env) : nom du module fixtures à valider.
  Défaut : "fixtures_debutant".
- MANUEL_MD (var d'env) : chemin vers le manuel prose à valider.
  Défaut : "manuel_debutant.md" dans le cwd.

Limites :
- Le validateur a un taux de faux positifs (cases d'arrivée de rafles
  qui n'apparaissent pas dans l'état initial sont signalées comme
  "inventées"). Le rapport indique les cases, c'est à l'humain de
  trancher.
- Heuristique : ignore les paragraphes où ≤ 2 cases sont "inventées"
  (probablement légitimes — cases d'arrivée, séquences PDN).
- Ignore les paragraphes où ≥ 60% des cases mentionnées sont dans
  l'état (les vrais cas de désynchronisation ont peu de recouvrement).
"""
import importlib
import os
import re
import sys
from pathlib import Path


def _find_dilf_root() -> Path:
    env = os.environ.get("DILF_ROOT")
    if env:
        p = Path(env).resolve()
        if (p / "pedagogy" / "game.py").exists():
            return p
        sys.exit(f"DILF_ROOT={env} ne contient pas pedagogy/game.py")
    here = Path.cwd().resolve()
    for cand in (here / "dilf", here.parent / "dilf", here):
        if (cand / "pedagogy" / "game.py").exists():
            return cand
    sys.exit("dilf non trouve. Definir DILF_ROOT ou cloner dilf a cote.")


DILF_ROOT = _find_dilf_root()
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(DILF_ROOT))


def main() -> None:
    fixtures_module_name = os.environ.get("FIXTURES_MODULE", "fixtures_debutant")
    manuel_path = Path(os.environ.get("MANUEL_MD", "manuel_debutant.md"))

    if not manuel_path.exists():
        sys.exit(f"❌ Manuel introuvable : {manuel_path}")

    fx = importlib.import_module(fixtures_module_name)

    # Détecter la liste ALL_*_POSITIONS
    fixtures_list = None
    for attr in dir(fx):
        if attr.startswith("ALL_") and attr.endswith("_POSITIONS"):
            fixtures_list = getattr(fx, attr)
            break
    if fixtures_list is None:
        sys.exit(
            f"❌ Module {fixtures_module_name} ne contient aucune liste ALL_*_POSITIONS"
        )

    # Construire le dict {id: set(cases)}
    fixture_states: dict[str, set[int]] = {}
    for p in fixtures_list:
        state_squares = (
            set(p.state.white_men)
            | set(p.state.white_kings)
            | set(p.state.black_men)
            | set(p.state.black_kings)
        )
        fixture_states[p.id] = state_squares

    # Lire le manuel
    with open(manuel_path) as f:
        manuel_text = f.read()

    # Regex pour les références fixture (BEG_CHnn_mmm, INT_CHnn_mmm, ...)
    ref_pattern = re.compile(r"\b([A-Z]+_CH\d{2}_\d{3})\b")

    # Pour chaque référence, trouver le paragraphe qui l'entoure
    # (limite : jusqu'à la prochaine référence, ---, fin de section ou 600 chars)
    issues_strict: list[tuple] = []   # désynchro grave (peu de recouvrement)
    issues_soft: list[tuple] = []     # potentielle invention (à vérifier)
    missing_refs: list[str] = []

    for match in ref_pattern.finditer(manuel_text):
        ref_id = match.group(1)
        if ref_id not in fixture_states:
            if ref_id not in missing_refs:
                missing_refs.append(ref_id)
            continue
        state_sq = fixture_states[ref_id]
        # Capture le paragraphe STRICTEMENT entourant la référence :
        # commence au début de la phrase contenant la ref, finit à la
        # prochaine ref OU à 2 sauts de ligne (paragraphe).
        start = max(0, match.start() - 200)
        # On recule au début de la phrase ('. ' ou début de paragraphe)
        prev = manuel_text.rfind(". ", start, match.start())
        prev_para = manuel_text.rfind("\n\n", start, match.start())
        start = max(prev + 2 if prev > 0 else 0, prev_para + 2 if prev_para > 0 else 0)
        # On avance jusqu'à la fin de phrase suivante OU prochaine ref OU paragraphe
        end_options = []
        next_ref = ref_pattern.search(manuel_text, match.end())
        if next_ref:
            end_options.append(next_ref.start())
        next_para = manuel_text.find("\n\n", match.end())
        if next_para > 0:
            end_options.append(next_para)
        end_options.append(match.end() + 300)
        end = min(end_options)
        context = manuel_text[start:end]
        # Extraire les nombres 1-50 (cases potentielles)
        nums = set(int(n) for n in re.findall(r"\b([1-9]|[1-4]\d|50)\b", context))
        # Filtrer les digits de l'ID lui-même
        nums -= {int(d) for d in re.findall(r"\d+", ref_id)}
        if not nums:
            continue
        invented = nums - state_sq
        recouvrement = (len(nums - invented) / len(nums)) if nums else 1.0

        # Cas grave : peu de recouvrement (< 40%) ET au moins 2 cases inventées
        if recouvrement < 0.4 and len(invented) >= 2:
            issues_strict.append((ref_id, sorted(state_sq), sorted(invented), recouvrement))
        elif len(invented) >= 3 and recouvrement < 0.7:
            issues_soft.append((ref_id, sorted(state_sq), sorted(invented), recouvrement))

    # Rapport
    total_refs = sum(1 for _ in ref_pattern.finditer(manuel_text))
    print(f"\n{'=' * 70}")
    print(f"Validation prose vs fixtures — {fixtures_module_name}")
    print(f"{'=' * 70}")
    print(f"  Références fixtures dans le manuel : {total_refs}")
    print(f"  Fixtures disponibles               : {len(fixture_states)}")
    print()

    if missing_refs:
        print(f"❌ {len(missing_refs)} référence(s) à fixtures INEXISTANTES :")
        for ref in missing_refs:
            print(f"   - {ref}")
        print()

    if issues_strict:
        print(f"🚨 {len(issues_strict)} désynchronisation(s) GRAVE(S) (< 40% recouvrement) :")
        for ref_id, state, invented, rec in issues_strict:
            print(f"   - {ref_id}")
            print(f"     état fixture : {state}")
            print(f"     mentions prose absentes : {invented} (recouvrement {rec:.0%})")
        print()

    if issues_soft:
        print(f"⚠️  {len(issues_soft)} mention(s) suspecte(s) (à vérifier manuellement,")
        print(f"    souvent des cases d'arrivée légitimes) :")
        for ref_id, state, invented, rec in issues_soft[:10]:  # limit display
            print(f"   - {ref_id}: prose mentionne aussi {invented}")
        if len(issues_soft) > 10:
            print(f"   ... + {len(issues_soft) - 10} autres")
        print()

    if not (missing_refs or issues_strict):
        print("✅ Aucune désynchronisation grave détectée.")
        if issues_soft:
            print(f"   ({len(issues_soft)} mentions soft à examiner manuellement.)")

    if issues_strict or missing_refs:
        sys.exit(2)


if __name__ == "__main__":
    main()
