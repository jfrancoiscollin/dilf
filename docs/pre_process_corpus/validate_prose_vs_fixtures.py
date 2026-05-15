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

    # Construire les dicts {id: set(cases)} ET {id: published_notation}
    fixture_states: dict[str, set[int]] = {}
    fixture_notations: dict[str, str] = {}
    for p in fixtures_list:
        state_squares = (
            set(p.state.white_men)
            | set(p.state.white_kings)
            | set(p.state.black_men)
            | set(p.state.black_kings)
        )
        fixture_states[p.id] = state_squares
        fixture_notations[p.id] = p.published_notation or ""

    # Lire le manuel
    with open(manuel_path) as f:
        manuel_text = f.read()

    # Regex pour les références fixture (BEG_CHnn_mmm, INT_CHnn_mmm, ...)
    ref_pattern = re.compile(r"\b([A-Z]+_CH\d{2}_\d{3})\b")
    # Regex pour les notations Dubois entre backticks
    notation_in_backticks = re.compile(r"`([\d\s\-x×()]+)`")

    # Pour chaque référence, trouver le paragraphe qui l'entoure
    # (limite : jusqu'à la prochaine référence, ---, fin de section ou 600 chars)
    issues_strict: list[tuple] = []   # désynchro grave (peu de recouvrement de cases)
    issues_soft: list[tuple] = []     # potentielle invention (à vérifier)
    notation_issues: list[tuple] = [] # notation Dubois citée incohérente avec published_notation
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
        # Limite stricte à 300 chars après la ref pour éviter de capter
        # toute la fin du document quand il n'y a pas de paragraphe suivant.
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

        # === Validation supplémentaire : notations Dubois entre backticks ===
        # Si la prose cite une notation `aXb` ou `a-b` qui contient des
        # nombres absents de la published_notation de la fixture, c'est
        # suspect (probable copie de mémoire d'une autre combinaison).
        #
        # Heuristique stricte : on ne valide que la notation présente
        # DANS LA MÊME PHRASE que la référence (pas dans tout le paragraphe),
        # pour éviter de capter les notations d'autres fixtures voisines.
        published = fixture_notations.get(ref_id, "")
        if published:
            # Trouve la fin de la phrase contenant la ref
            sentence_end = manuel_text.find(".", match.end())
            next_newline = manuel_text.find("\n\n", match.end())
            if next_newline > 0 and (sentence_end < 0 or next_newline < sentence_end):
                sentence_end = next_newline
            if sentence_end < 0:
                sentence_end = match.end() + 200
            # Et le début de la phrase
            sentence_start = manuel_text.rfind(".", max(0, match.start() - 300), match.start())
            sentence_start = max(sentence_start + 1 if sentence_start > 0 else 0, match.start() - 300)
            sentence_context = manuel_text[sentence_start:sentence_end]

            real_normalized = re.sub(r"\s+", "", published).replace("×", "x")
            real_tokens = set(re.findall(r"\d+", real_normalized))
            for nm in notation_in_backticks.finditer(sentence_context):
                cited = nm.group(1).strip()
                if not (("x" in cited or "×" in cited or "-" in cited) and any(c.isdigit() for c in cited)):
                    continue
                # Exiger une notation Dubois "complète" : au moins 2 nombres
                # (sinon on capte des trucs comme "32" tout seul qui sont
                # juste des références de cases dans la prose)
                cited_normalized = re.sub(r"\s+", "", cited).replace("×", "x")
                cited_tokens = set(re.findall(r"\d+", cited_normalized))
                if len(cited_tokens) < 2:
                    continue
                if cited_normalized in real_normalized:
                    continue  # Citation parfaitement contenue
                if not cited_tokens.issubset(real_tokens):
                    missing_tokens = sorted(int(t) for t in cited_tokens - real_tokens)
                    notation_issues.append((ref_id, published, cited, missing_tokens))

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

    if notation_issues:
        # Dédoublonner sur (ref_id, cited)
        seen = set()
        unique = []
        for entry in notation_issues:
            key = (entry[0], entry[2])
            if key in seen:
                continue
            seen.add(key)
            unique.append(entry)
        print(f"🚨 {len(unique)} notation(s) Dubois incohérente(s) avec published_notation :")
        for ref_id, published, cited, missing in unique:
            print(f"   - {ref_id}")
            print(f"     fixture publie : {published!r}")
            print(f"     prose cite     : `{cited}` (chiffres absents : {missing})")
        print()

    if not (missing_refs or issues_strict or notation_issues):
        print("✅ Aucune désynchronisation grave détectée.")
        if issues_soft:
            print(f"   ({len(issues_soft)} mentions soft à examiner manuellement.)")

    if issues_strict or missing_refs or notation_issues:
        sys.exit(2)


if __name__ == "__main__":
    main()
