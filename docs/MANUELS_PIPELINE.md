# Pipeline manuels pédagogiques

Document de référence du flux end-to-end qui transforme le corpus de
PDFs Dubois (et autres) en manuels pédagogiques exploitables par
draught-master.

> **Pourquoi ce pipeline existe.** L'approche initiale — exposer les
> PDFs du corpus directement à draught-master et y construire la
> pédagogie « à la main » — bute sur deux problèmes : la transcription
> case par case des diagrammes est coûteuse et faillible, et le matériel
> brut (53 PDFs, ~6100 pages) est trop volumineux pour entrer tel quel
> dans l'app. On insère donc une **étape de pré-processing** où Claude,
> outillé par dilf, transforme le corpus en 4 manuels (Débutant,
> Intermédiaire, Avancé, Expert), un par niveau. Seuls les manuels
> produits — pas le corpus brut — sont consommés par draught-master.

## Vue d'ensemble

```
┌───────────────────────────────────────────────────────────────────┐
│ dilf/docs/corpus/   (53 PDFs Dubois, Springer, …)                 │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               │ scripts/extract_diagrams.py
                               │ (pipeline pixel-déterministe, $0)
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│ pedagogy/tests/fixtures/dubois_diagrams.py                        │
│ ALL_DIAGRAMS = [DuboisDiagram(state, page, region, crop_id), …]   │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               │ Claude (1 conversation par manuel)
                               │ + outillage dilf/docs/pre_process_corpus/
                               │   - generate_chapter.py
                               │   - validate_final_moves.py
                               │ + protocole anti-hallucination (CADRAGE §4)
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│ Livrables par manuel (déposés dans dilf/docs/pre_process_corpus/) │
│  - manuel_<niveau>.md       (prose pédagogique)                   │
│  - fixtures_<niveau>.py     (BeginnerPosition, GameState, Move)   │
│  - sources_<niveau>.md      (traçabilité)                         │
│  - ameliorations_dilf_<niveau>.md  (backlog framework)            │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               │ Intégration draught-master
                               │ (copie des livrables)
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│ draught-master/                                                   │
│  - docs/manuels/<niveau>/manuel_<niveau>.md                       │
│  - backend/manuels/fixtures_<niveau>.py                           │
│  - backend/scripts/smoke_test_manuel_<niveau>.py                  │
│  → consommation à venir : conversion en INITIAL_EXERCISES,        │
│    nouvelle API /api/manuels, page Manuel dans le frontend.       │
└───────────────────────────────────────────────────────────────────┘
```

## Étapes en détail

### 1. Extraction outillée des positions

Le pipeline `scripts/extract_diagrams.py` rasterise les pages d'un PDF
Dubois, détecte les régions de damier, et classifie chaque case sombre
par échantillonnage de pixels. Output : une liste `DuboisDiagram`
porteuse de la position brute (`white_men`, `black_men`, `turn`), de la
page, du crop_id, et de la légende OCR.

**Garanties** : déterministe, $0, sans appel LLM. 98.8 % de taux de
matérialisation observé sur le manuel Débutant (Dubois Apprentissage
Combinaisons).

Voir `dilf/docs/extract-diagrams.md` pour le mode opératoire détaillé.

### 2. Production du manuel par Claude

Chaque manuel est produit dans **une conversation Claude dédiée**. Le
protocole est figé dans `dilf/docs/pre_process_corpus/CADRAGE_MANUELS.md`
et résumé ici :

- **Phrase d'amorce** : *« Lis le CADRAGE_MANUELS.md, le JOURNAL.md et
  l'ETAT_DILF.md, puis attaque le manuel \<niveau\>. Mode fonce
  autorisé. »*
- **Outillage industriel** réutilisé tel quel depuis le cycle Débutant :
  - `generate_chapter.py` — génère le code Python d'un chapitre depuis
    une définition déclarative `chN_def.py`.
  - `validate_final_moves.py` — vérifie que chaque `final_move` est
    une rafle maximale légale FMJD via
    `pedagogy.notation.dubois.enumerate_pawn_captures`.
- **Protocole anti-hallucination** (CADRAGE §4) :
  - §4.1 : `source` obligatoire (CORPUS / GENERAL_KNOWLEDGE /
    INVENTED, ce dernier plafonné à 15 %).
  - §4.10 : transcription manuelle des diagrammes **interdite** — le
    pipeline est l'outil obligatoire.
  - §4.11 : human-in-the-loop après 2 tentatives infructueuses, avec
    image rasterisée + diagnostic envoyés à l'utilisateur.
  - §4.13 : bibliothèque d'heuristiques pour les 3 patterns de
    coquilles PDF observés (substitution, inversion de chiffres,
    inversion d'opérandes).
- **Wrapper pédagogique** : `BeginnerPosition` (ou `IntermediatePosition`,
  etc.) au-dessus de `pedagogy.game.GameState`. Champs alignés sur
  `DuboisCoupRoyalCase` (`published_notation`, `final_move`).

### 3. Livrables par cycle

| Fichier | Rôle |
|---|---|
| `manuel_<niveau>.md` | Prose pédagogique, ~30-50 pages, FEN intégrées |
| `fixtures_<niveau>.py` | Module Python, exposant `ALL_<NIVEAU>_POSITIONS` |
| `sources_<niveau>.md` | Traçabilité position → PDF + page (ou GENERAL_KNOWLEDGE / INVENTED) |
| `ameliorations_dilf_<niveau>.md` | Backlog d'évolutions dilf découvertes pendant le cycle |
| `RESOLUTIONS_<niveau>.md` | Trace des résolutions appliquées (scratch puis archivé) |
| `BLOCAGES_<niveau>.md` | (si mode fonce) blocages à résoudre en post-production |

### 4. Intégration côté draught-master

Les livrables sont copiés dans draught-master :

- `docs/manuels/<niveau>/manuel_<niveau>.md` — la prose, lisible par
  l'utilisateur via la doc.
- `backend/manuels/fixtures_<niveau>.py` — les fixtures Python,
  importables depuis le backend.

Avant tout branchement UI, un **smoke test backend**
(`backend/scripts/smoke_test_manuel_<niveau>.py`) valide que :

1. Le round-trip FEN `dilf.state_to_fen` ↔ `game_engine.fen_to_board`
   préserve la position sur toutes les fixtures.
2. Pour chaque `final_move` non None : après rejeu de
   `published_notation` via le module `pedagogy.notation.dubois`, le
   `final_move` est bien un coup légal selon `get_legal_moves` de
   draught-master.

C'est le critère de bascule avant d'aller plus loin (conversion vers
`INITIAL_EXERCISES`, API `/api/manuels`, page frontend Manuel).

## État

| Manuel | Statut | Fixtures | final_move OK | Smoke test draught-master |
|---|---|---|---|---|
| Débutant | ✅ Livré (mai 2026) | 166 | 135/135 | ✅ 166 FEN + 135 final_move |
| Intermédiaire | À démarrer | — | — | — |
| Avancé | À démarrer | — | — | — |
| Expert | À démarrer | — | — | — |

## Pré-requis dilf encore à livrer

Issus du backlog `ameliorations_dilf_debutant.md`, à clore avant les
prochains cycles :

- **§1** — Wrapper `PedagogicalPosition` standardisé dans `pedagogy/`
  (haute priorité). Évite la duplication de `BeginnerPosition` /
  `IntermediatePosition` / etc.
- **§4** — Détecteur automatique de coquilles PDF (haute priorité).
  L'expérience Débutant indique 4 % de taux de coquilles ; un détecteur
  réduirait les interpellations §4.11.
- **§5** — Glossaire étendu de notation Dubois (`ad lib`, `+1p`,
  `etc.`).
- **§6** — Détecteurs de motifs pour les coups nommés
  (`coup_express`, `coup_ricochet`, …).

Voir `ROADMAP.md` pour la priorisation globale.
