# Améliorations dilf — backlog issu de la conversation Débutant

> Document consolidé en fin de cycle de production du manuel Débutant,
> conforme cadrage §8.2. Destiné à alimenter le backlog d'évolution du
> framework dilf.
>
> **Statut : FINAL** — basé sur les 16 chapitres produits, les 8
> résolutions consignées dans `RESOLUTIONS_debutant.md`, et les 3
> blocages cumulés dans `BLOCAGES.md`.
>
> Cycle de production : 166 fixtures produites, dont 152 corpus, 12
> general_knowledge, 2 invented. PR #31 livrée et mergée pendant ce
> cycle. 3 coquilles PDF détectées et corrigées. 3 blocages structurels
> non résolus (cf §4 ci-dessous).

---

## 1. Schéma `pedagogy/` — wrapper pédagogique standardisé

**Constat.** Le manuel Débutant a produit son propre wrapper
`BeginnerPosition` parce qu'aucune dataclass existante dans
`pedagogy/tests/fixtures/` ne couvre les besoins d'un manuel pédagogique.
Le naming a été aligné sur `DuboisCoupRoyalCase` (`published_notation`,
`final_move`) mais les fixtures ne sont pas réutilisables hors du
contexte manuel Débutant.

**Constat enrichi en fin de cycle** : les 4 manuels prévus auront
probablement des besoins très similaires. Définir 4 wrappers distincts
(`BeginnerPosition`, `IntermediatePosition`, ...) dupliquerait la même
dataclass.

**Suggestion** : introduire dans dilf une dataclass standardisée
`PedagogicalPosition` :

```python
from dataclasses import dataclass
from enum import Enum
from typing import Literal
from pedagogy.game import GameState, Move


class SourceType(Enum):
    CORPUS = "corpus"
    GENERAL_KNOWLEDGE = "general"
    INVENTED = "invented"


@dataclass(frozen=True)
class PedagogicalPosition:
    # Identité pédagogique
    id: str                          # ex: "BEG_CH09_007", "INT_CH02_003"
    theme: str                       # cf §6 — thèmes canoniques
    level: Literal["beginner", "intermediate", "advanced", "expert"]
    title: str

    # Position (référence dilf)
    state: GameState

    # Pédagogie + bibliographie (naming aligné DuboisCoupRoyalCase)
    concept: str = ""                # 1-2 phrases : le principe enseigné
    published_notation: str = ""     # Verbatim PDF source
    final_move: Move | None = None   # None = envoi à dame, gambit, blocage
    explanation: str = ""            # 3-4 phrases : pourquoi ça gagne

    # Traçabilité
    source: SourceType = SourceType.GENERAL_KNOWLEDGE
    source_ref: str = ""             # ex: "dubois_apprent_combin_p27_d05"
    crop_id: str = ""                # ex: "crops/page_027_d05.png"

    # Qualité
    verified: bool = False           # True après passage moteur Scan
    confidence: Literal["high", "medium", "low"] = "high"
    notes: str = ""                  # Doutes, coquilles PDF, blocages
```

**Priorité** : **moyenne-haute, à faire AVANT démarrage manuel Intermédiaire.**
Sans ça, chaque conversation manuel re-définit son wrapper et la
duplication s'amplifie.

**Contexte** : R001, conversation entière du manuel Débutant.

---

## 2. Module `pedagogy/notation/dubois.py` — ✅ LIVRÉ

✅ **Implémenté et mergé sur main** via PR #31 (commit `a974109`, mai 2026).

Le module fournit :
- `reconstruct_pawn_capture(state, from_sq, to_sq) → Move`
- `enumerate_pawn_captures(start, my_pieces, enemy_pieces)`
- Exceptions `NoSuchRafleError`, `AmbiguousRafleError`, `NotAManError`
- 16 tests unitaires (mypy --strict clean)
- Doc `docs/dubois-notation.md`

**Limitations connues** : voir §3 (extension dames).

---

## 3. Reconstruction des rafles de dame (extension du module dubois)

**Constat (R007, ~24 fixtures du manuel Débutant).** La PR #31 traite
les rafles de pion uniquement. Les rafles de dame sont fréquentes dans
deux contextes :

1. **Envoi à dame** : un pion adverse fait une rafle qui le mène à la
   dernière rangée, où il promeut en dame, puis une rafle de dame
   subséquente est forcée par un sacrifice blanc.

2. **Rafle de dame pure** : dans certaines positions Dubois, une dame
   existe déjà au départ et fait la rafle finale.

Fixtures concernées dans `fixtures_debutant.py` (24 cas avec
`final_move=None` à cause de rafles de dame) :
- BEG_CH04_010 (Dubois ch7 D5)
- BEG_CH05_009, BEG_CH05_010 (Dubois ch4 D9, D10)
- BEG_CH07_002, BEG_CH07_009 (envois à dame)
- BEG_CH10_002 (combinaison à phases multiples)
- BEG_CH12_009
- BEG_CH13_001
- BEG_CH14_010
- BEG_CH16_001, BEG_CH16_008, BEG_CH16_009
- + 12 autres

**Suggestion** : étendre `pedagogy/notation/dubois.py` avec
`reconstruct_king_capture(state, from_sq, to_sq) → Move`. Algorithme :

1. La dame en `from_sq` peut sauter par-dessus N'IMPORTE QUEL pion
   adverse situé sur une diagonale libre, et atterrir sur N'IMPORTE
   QUELLE case libre au-delà.
2. Énumérer toutes les trajectoires multi-sauts maximales (DFS sur
   les diagonales, gestion du non-soufflage).
3. Retenir celle(s) qui finit/finissent en `to_sq` avec maximum de
   captures.

**Bénéfice attendu** : faire passer 24 fixtures actuelles
`final_move=None` à 24 fixtures avec `final_move` reconstruit, soit
**+14% de couverture** sur le manuel Débutant (132 → 156 / 166).
Probablement plus encore sur le manuel Intermédiaire (où les envois à
dame sont plus fréquents).

**Priorité** : **haute, à faire avant manuel Intermédiaire.** Sans ça,
les manuels suivants auront 20-30% de leurs fixtures avec
`final_move=None`.

**Cas-tests à inclure** (extraits du manuel Débutant) :
- Rafle de dame simple : `4x47` après promotion en 4 (BEG_CH04_010)
- Rafle de dame à coup turc (BEG_CH07_002 cf phase 3)
- Rafle de dame entre deux pions adverses : `48x33` (BEG_CH07_009)

**Contexte** : R007 de `RESOLUTIONS_debutant.md`, 24 fixtures du
manuel Débutant.

---

## 4. Pipeline `extract_diagrams.py` — détecteur de coquilles PDF

**Constat (R002, R004, R005, R006 + 3 blocages).** Le PDF Dubois
Apprentissage Combinaisons contient **6 problèmes typographiques ou
structurels** détectés pendant la production du manuel Débutant :

| Cas | Localisation | Type |
|---|---|---|
| R002 | ch3 D9 p6 | Coquille : `43-38` → `44-39` |
| R004 | ch6 D1 p21 | Coquille : `(15x21)` → `(15x31)` |
| R005 | ch6 D5 p21 | Diagramme faux (position et solution incohérentes) |
| R006 | ch7 D8 p24 | Coquille : `31x3` → `32x3` |
| BLOCAGE | ch13 D5 p43 | Position/solution incompatibles |
| BLOCAGE | ch14 D6 p46 | Mapping diagramme/solution erroné |
| BLOCAGE | ch17 D4 p55 | Solution entièrement décalée |

**Taux de problèmes** sur le manuel Débutant : 7/152 fixtures CORPUS =
**4,6%**. Sur un livre complet de 400 combinaisons, cela représenterait
~18 problèmes à valider manuellement.

**Suggestion** : ajouter `scripts/validate_solutions.py` qui :

1. Parse les solutions textuelles via `pdftotext -layout`.
2. Pour chaque solution, tente la reconstruction via
   `pedagogy.notation.dubois` (pions ET dames si §3 livré).
3. Émet `suspects.json` listant les diagrammes problématiques avec :
   - `crop_id`, `published_solution`, `error_message`
   - Suggestion de correction (variante 1-bit-flip sur les chiffres)
4. L'utilisateur peut valider la correction suggérée, marquer "skip"
   (cas R005), ou demander re-extraction.

**Bénéfice attendu** : sur le manuel Intermédiaire (Perfectionnement
Dubois, ~700 fixtures), repérer automatiquement les ~30 coquilles au
lieu de les découvrir une par une.

**Priorité** : **moyenne-haute, à faire avant manuel Intermédiaire.**

**Contexte** : R002, R004, R005, R006 + `BLOCAGES.md`.

---

## 5. Glossaire de notation Dubois (étendu)

**Constat (R001, R008).** Le glossaire `docs/dubois-notation.md` livré
avec la PR #31 couvre :
- Notation `aXb` = rafle abrégée
- Parenthèses = coup adverse
- Notation séquentielle

**À ajouter en V2** :

### 5.1. Notation `(ad lib)` (R008)

`(ad lib)` indique que l'adversaire a **plusieurs captures forcées
équivalentes**, toutes menant à la même conclusion.

Exemples :
- BEG_CH07_012 (Dubois ch8 D10) : `32-27 (21x23) 33-28 (ad lib) 38x29`
- BEG_CH12_008 (Dubois ch16 D8) : `26-21 (17x28) 29-23 (18x29) 39-33 (ad lib) 43x5`

**Convention proposée** : le helper peut retourner toutes les variantes
via `enumerate_forced_continuations()`, et le manuel choisit
lexicographiquement la première (case de départ la plus petite).

### 5.2. Notation `+1p`, `+2p` (R002 contexte)

Indicateur de résultat matériel à la fin d'une combinaison non-rafle.
Ex : `27-21 (26x39) 21x43 +1p` = +1 pion net.

**Convention** : ignorer cet indicateur dans `published_notation` (c'est
un résultat, pas un coup).

### 5.3. Notation `etc.` (R006 contexte)

Indique que la suite est triviale ou trop longue à écrire intégralement.
Le manuel doit s'arrêter au dernier coup explicitement noté.

### 5.4. Notation `30.48x6` (BEG_CH16_010)

Notation anormale rencontrée chez Dubois. Interprétation probable :
`30x6` ou `48x6` selon le contexte. **À documenter** comme notation
ambiguë nécessitant disambiguation manuelle.

**Priorité** : basse. Documentation, pas bloquant.

---

## 6. Détecteurs de motifs — thèmes observés

**Constat enrichi.** Le manuel Débutant a tagué les 166 fixtures avec
**28 thèmes distincts**. Les détecteurs de motifs `pedagogy/motifs/`
ne couvrent que `coup_royal.py` à ce jour. Liste des thèmes manquant
un détecteur, classés par fréquence :

| Thème | Nb fixtures | Priorité détecteur |
|---|---|---|
| `prise_majoritaire` | 15 | Haute (concept fondamental) |
| `coup_express` | 13 | Haute (coup nommé canonique) |
| `coup_de_trappe` | 12 | Haute |
| `coup_de_talon` | 11 | Haute |
| `coup_ricochet` | 11 | Haute |
| `coup_rappel` | 11 | Haute |
| `coup_philippe` | 10 | Haute |
| `temps_de_repos` | 10 | Moyenne (méta-concept) |
| `creation_temps_de_repos` | 10 | Moyenne (méta-concept) |
| `coup_napoleon` | 10 | Haute |
| `envoi_a_dame` | 8 | Haute |
| `coup_renverse` | 8 | Moyenne |
| `collage` | 7 | Haute (concept fondamental) |
| `points_de_contact` | 6 | Moyenne (méta-concept) |
| `coup_de_mazette` | 4 | Moyenne |
| `gambit` | 3 | Basse |

**Suggestion** : implémenter les détecteurs dans l'ordre de priorité.
Chaque détecteur expose `detect(state, move) → bool`.

**Cas-tests immédiatement disponibles** : les 166 fixtures du manuel
Débutant taguées par thème servent de banc d'essai.

**Priorité** : moyenne. Pas bloquant pour la production de manuels,
mais essentiel pour la phase "exercices guidés" de Draught Master.

**Contexte** : taggage thèmes du manuel Débutant complet.

---

## 7. Validation des positions extraites (cas blocages)

**Constat** (3 blocages sur 152 CORPUS = 2%). Trois fixtures ont une
position extraite qui ne correspond pas à la solution publiée. Le
diagnostic actuel est ambigu : extraction mauvaise / solution PDF
mauvaise / mapping diagramme↔solution faux.

**Suggestion** : extension de `validate_solutions.py` (§4) avec un
mode "interactive" qui re-rasterise la page à 300 DPI, affiche
l'annotation des cases extraites, permet à l'utilisateur de cocher
"position correcte / solution correcte / mapping correct" et génère
un patch correctif.

**Priorité** : moyenne. Diminue le coût des interpellations §4.11
dans les conversations manuel suivantes.

**Contexte** : `BLOCAGES.md` (3 fixtures du manuel Débutant).

---

## Synthèse finale des priorités

| Priorité | Suggestion | Statut | Bénéfice |
|---|---|---|---|
| ✅ Livré | §2 — Module `pedagogy/notation/dubois.py` (pions) | **Mergé PR #31** | Reconstruct 79% des fixtures |
| ✅ Livré | §5 (partiel) — Glossaire notation Dubois | **Livré PR #31** | Doc `docs/dubois-notation.md` |
| **Haute** | §3 — Extension dames du module dubois | À faire | +14% couverture final_move |
| **Haute** | §1 — Wrapper `PedagogicalPosition` standardisé | À faire | Évite duplication 4 manuels |
| Moyenne-haute | §4 — Détecteur de coquilles PDF | À faire | -90% coût détection coquilles |
| Moyenne | §5.1-5.4 — Compléter glossaire | À faire | Réduit interpellations |
| Moyenne | §6 — Détecteurs de motifs | À faire | Permet exercices guidés |
| Moyenne | §7 — Validation interactive des blocages | À faire | Diminue coût §4.11 |

**Ordre recommandé pour démarrer le manuel Intermédiaire** :
1. §3 (rafles de dame) — bloquant pour 20-30% des fixtures Intermédiaire
2. §1 (wrapper standardisé) — bloquant pour réutilisation cross-manuels
3. §4 (détecteur coquilles) — accélère la production de 10-15%
4. Les autres en parallèle ou après.

---

## Annexes — fichiers de référence

- `fixtures_debutant.py` (166 fixtures)
- `manuel_debutant.md` (prose pédagogique, à venir)
- `RESOLUTIONS_debutant.md` (8 résolutions consignées)
- `BLOCAGES.md` (3 blocages non résolus)
- `JOURNAL.md` (trace chronologique)
- PR #31 sur dilf : commit `a974109`
