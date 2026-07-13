# État de l'infrastructure dilf

> **Document de référence — état réel du framework au démarrage d'une
> nouvelle conversation manuel.** À lire en début de chaque conversation
> après le `CADRAGE_MANUELS.md` et le `JOURNAL.md`.
>
> **Mise à jour** : 2026-07-12 (campagne PC Blues) ; mai 2026 (post-cycle Débutant).

## 0. ⭐ CAMPAGNE PC BLUES — CORPUS 60 VOLUMES RAFFINÉ (2026-07-12)

Les 60 volumes PC Blues (10 165 pages, © Piens Christiaan) sont passés dans
la raffinerie `scripts/pcblues/` (extraction texte + pixel → re-jeu FMJD
complet → artefacts contractuels versionnés). **Livré dans
`data/exports/pcblues/`** (API gelée, section EXPORTS d'`INTEROP.md`) :

| artefact | contenu |
|---|---|
| **A2** `pcblues_combos.jsonl` | **21 718 combinaisons certifiées-jouées** vérifiées (58 vol., +787 réparées §4.13) |
| **A3** `pcblues_prefs_graded.jsonl` | **10 219 préférences graduées** (5 712 positives !/!!, 4 450 négatives ?/?? certifiées) |
| **A5** `pcblues_tests.jsonl` | **960 Vaardigheidstesten** vérifiés |
| **A4** `pcblues_endgame_qa.jsonl` | **73 QA finales** (dames par hypothèse-re-jeu minimisée, book_claim) |
| **A1** `pcblues_games.pdn` | **26 parties complètes** rejouées |

Principe central : **ancrage-par-re-jeu** (la légalité FMJD intégrale est à
la fois critère d'appariement diagramme↔séquence, gate de validation
`verified=true`, et arbitre des hypothèses de vision — 4 rendus de
diagrammes traités, dames comprises). Rien ne sort sans re-jeu. Quarantaines
diagnostiquées conservées (2e passes). Consommé par jass (ingestion
`tools/pcblues_ingest.py`, tag de version). Détail : `INTEROP.md` §EXPORTS,
`JOURNAL.md`, `scripts/pcblues/`.

### Extensions (chantiers d'enrichissement C1-C3, 2026-07-12)

- **C2 — corpus Dubois FMJD** (`scripts/pcblues/extract_dubois.py`,
  `data/exports/dubois/`, tag `dubois-a2bis-v1`, §EXPORTS-bis d'INTEROP) :
  même raffinerie re-pointée sur `docs/corpus/` — **789 combinaisons Dubois
  vérifiées** (expert 404, apprentissage 258, perfectionnement 127 ; 25
  seulement recouvrent pcblues = matière neuve). `extract_diagrams` avait
  été construit pour Dubois → positions pixel + trait explicite ; appariement
  diagramme↔solution arbitré par le re-jeu (index global par D-numéro).
- **C3 — A4-bis finales Dubois** (`extract_dubois_endgames.py`) : verdict
  WIN/DRAW des marqueurs de solution, pilote 4 QA (volumes finales en analyse
  inline = rendement limité par-volume, documenté).
- **C1 — prédicat de BLOCAGE STRUCTUREL** (`pedagogy/features/blocage.py`,
  6 tests) : reconnaît par MOBILITÉ (zéro éval) les milieux bloqués
  ply-cappés (trou d'oracle n°1, ~19 %) → verdict DRAW-de-blocage propre.
  `mutual_blocked`/`blocage_structurel` sur `EngineProtocol`. Le harnais de
  notation (TB + arbitre-fort + gate DRAW≥99,9 %) est côté jass.

### Exploitation MAX du corpus original (chantiers E1-E5, 2026-07-13)

> Décision JFC : exploiter le corpus À FOND (indépendamment du verdict A/B). Le
> tri post-0691 ne change que le ROUTAGE (oracles/QA + RAG ; ⛔ jamais prefs-éval).
> **Bilan : 73 → 802 positions certifiées par re-jeu + ~6 100 passages RAG.**

- **E1 — finales à l'échelle** : `extract_volume_v3` (appariement-par-re-jeu des
  blocs « Solution : » + **port des hypothèses-de-dames A4** : `boards_of_page` +
  extension verticale + gate exercice-dames + minimisation) → **Dubois finales
  4→66** (20 à dames) ; `extract_cid.py` (prose CID anglaise) → **1.The_endgame
  211** (62 à dames). `data/exports/dubois/endgame_*`, `data/exports/cid/endgame_*`.
  S5.The_endgame = 0 (layout à sonder). Consommateur = oracles/QA finale + seeds.
- **E2 — Locks** (`extract_cid.py` sur `7.Locks`) : **113 verrous vérifiés**
  (`data/exports/cid/locks_*`) → nourrit la notation P2-blocage (le prédicat C1
  doit tirer dessus ; verdict par TB).
- **E3 — Goedemoed** (`extract_cid.py --detector goedemoed`, détection gris-
  échiquier tunée) : **Exercise_2 150 + Exercise_3 262 = 412 combos** vérifiées
  (`data/exports/goedemoed/`).
- **E4 — stratégie/cours → RAG** (`index_prose.py`, ⚠️ `--cache` PAR volume
  obligatoire, cf bug cache partagé) : **13 volumes ~6 100 passages** (Dubois
  sens-du-jeu ×5, CID thématiques ×5, cours ×3) → `pedagogy/prose/fixtures/`.
- **E5 — openings systèmes** : ~0 (les `le_systeme_*` sont de la PROSE, déjà E4).
- Tout `verified_engine=false` → **revalidation d14+TB côté jass** avant gate dur.

---
>
> Ce document décrit **ce qui existe et est utilisable**, **ce qui manque
> encore** et les **patterns observés** pendant la production des manuels.
> Il remplace l'ancien `ameliorations_dilf_debutant.md` (qui est conservé
> comme archive historique du backlog initial).

---

## 1. Modules dilf disponibles et utilisables

### 1.1. `pedagogy/game.py` — schéma de référence

- `GameState`, `Move`, `Side`, `Square` : dataclasses + types canoniques.
- `parse_fen`, `state_to_fen` : sérialisation FEN dames.
- `initial_state`, `empty_state`, `state_from_pieces` : constructeurs.
- Toute fixture publiée **doit** produire un `GameState` valide via ce module.

### 1.2. `pedagogy/notation/dubois.py` — reconstruction des rafles

✅ **Mergé sur main via PR #31** (pions) **et PR #32** (dames + dispatcher).

**API complète** :

```python
from pedagogy.notation.dubois import (
    enumerate_pawn_captures,    # énumère rafles maximales de pion
    enumerate_king_captures,    # énumère rafles maximales de dame
    reconstruct_pawn_capture,   # reconstruit Move pour rafle pion
    reconstruct_king_capture,   # reconstruit Move pour rafle dame
    reconstruct_capture,        # dispatcher unifié pion/dame
    NotAManError,               # from_sq vide ou dame (côté pawn API)
    NotAKingError,              # from_sq vide ou pion (côté king API)
    NoSuchRafleError,           # aucune rafle maximale n'atteint to_sq
    AmbiguousRafleError,        # plusieurs rafles non équivalentes
)
```

**Couverture** : sur les 166 fixtures du manuel Débutant, le module
reconstruit avec succès 135 `final_move` (81%). Les 31 restantes
sont des cas de gambit terminant par coup simple (comportement
attendu, pas de rafle finale) ou des cas mixtes pion+dame que le
dispatcher unifié pourra traiter dans le manuel Intermédiaire.

### 1.3. `scripts/extract_diagrams.py` — pipeline pixel-déterministe

Pipeline en 3 étapes :

```bash
python3 -m scripts.extract_diagrams render --pdf <PDF> --pages <plage>
python3 -m scripts.extract_diagrams extract
python3 -m scripts.extract_diagrams materialize
```

Produit `pedagogy/tests/fixtures/dubois_diagrams.py` contenant la liste
`ALL_DIAGRAMS` de `DuboisDiagram` (position + métadonnées).

**Taux de succès observé** sur le manuel Débutant : 569/576 fixtures
matérialisées = **98.8%**. Les échecs sont essentiellement des pages
narratives où une position est sciemment vide ou ne correspond pas à
un diagramme.

### 1.4. Corpus PDF — `docs/corpus/`

53 PDFs (~6100 pages) déjà dans le repo dilf. Pas besoin d'upload.
Référence Dubois principale :
`docs/corpus/dubois_apprent_combin.pdf` (utilisée pour le Débutant).
Pour les niveaux suivants, voir §6 du `CADRAGE_MANUELS.md`.

### 1.5. Détecteurs de motifs — `pedagogy/motifs/`

Disponibles : `coup_royal.py` (existant pré-projet) + 4 nouveaux ajoutés
par #30 (Napoleon, Manoury, Enfilade, Brûleur). À ce jour, **5
détecteurs** sur les ~16 thèmes du manuel Débutant (voir §6 de ce
document pour la liste exhaustive à implémenter).

---

## 2. Outillage industriel hors dilf

### 2.1. `generate_chapter.py` — générateur de fixtures

Script produit pendant le cycle Débutant. Prend en entrée un fichier
`chN_def.py` contenant une liste `SELECTION` de tuples :

```python
SELECTION = [
    ("BEG_CHN_001", page, region_index, "published_notation",
     has_king_rafle, meta_dict),
    ...
]
```

et émet le code Python des fixtures sur stdout, avec `final_move`
reconstruit via le module dubois. Les erreurs de reconstruction sont
émises sur stderr pour traitement (correction automatique pattern §4.13
ou interpellation §4.11).

**À conserver dans les outils de production** — pas dans dilf (c'est
un outil de conversation, pas un module framework).

### 2.2. `validate_final_moves.py` — validation moteur structurelle

Script qui re-joue chaque `published_notation` jusqu'au `final_move` et
vérifie que ce dernier est une **rafle maximale légale** selon les
règles FMJD (via `enumerate_pawn_captures`).

**Limitation actuelle** : ne valide pas la maximalité globale (toutes
les cases du joueur), uniquement la maximalité depuis la case de
départ du `final_move`. Suffisant pour détecter 99% des erreurs.

**À conserver dans les outils de production**.

---

## 3. Patterns de coquilles PDF observés (Dubois Apprentissage)

Cette typologie a émergé du cycle Débutant. Elle sert de bibliothèque
d'heuristiques pour le protocole §4.13 du cadrage.

**Statistique de référence** : 6 coquilles détectées sur 152 fixtures
CORPUS du manuel Débutant = **4% de taux de coquilles**.

### Pattern 1 — Substitution de coup

Un coup entier remplacé par un autre. Ex (R009 Débutant) : Dubois écrit
`43-38` mais le vrai coup est `38-32`. Le pion source publié peut ne
pas exister ou le coup est illégal.

**Heuristique** : énumérer tous les coups blancs simples possibles
dans l'état précédent et tester chacun. Si **une seule** solution
mène à la rafle finale publiée, c'est elle.

### Pattern 2 — Inversion de chiffres

Plusieurs nombres décalés systématiquement. Ex (R010 Débutant) :
Dubois écrit `37-31 (26x28)` mais le vrai est `27-21 (17x28)` —
digits de gauche décalés de 1.

**Heuristique** : recherche exhaustive sur **toute la séquence**
(plusieurs sacrifices + rafle finale) plutôt que correction
case-par-case.

### Pattern 3 — Inversion des opérandes

Notation `(aXb)` écrite à l'envers. Ex (R011 Débutant) : `(18x27)`
devrait être `(27x18)`. Le pion `a` n'existe pas mais le pion `b` peut
prendre vers `a`.

**Heuristique de premier recours** : si un coup `(aXb)` est invalide
parce que `a` est vide, tester immédiatement `(bXa)`.

### Coquilles simples (chiffres adjacents)

3 autres coquilles plus mineures observées (R002, R004, R006 Débutant) :
- `43-38` ↔ `44-39` (digit `±1`)
- `(15x21)` ↔ `(15x31)` (digit `±1`)
- `31x3` ↔ `32x3` (digit `±1`)

**Heuristique** : tester systématiquement les variantes `±1` sur chaque
digit du coup invalide avant d'invoquer §4.11.

---

## 4. Notations Dubois reconnues

Documentées dans `docs/dubois-notation.md` (livré avec PR #31, étendu
par PR #32) :

- `aXb` : rafle abrégée (départ → arrivée, chemin implicite)
- `a-b` : coup simple non capturant
- `(coup)` : coup adverse forcé
- Séquentialité alternée (blanc, noir, blanc, ...)

**Non encore documentées formellement** (suggestions de §5 du backlog) :

- `(ad lib)` : captures forcées équivalentes — l'adversaire a plusieurs
  rafles obligatoires aboutissant au même résultat. Rencontré dans
  BEG_CH07_012 et BEG_CH12_008 (Dubois ch8 D10, ch16 D8).
- `+1p`, `+2p` : indicateur de gain matériel net après combinaison
  non-rafle (gambit). À ignorer dans `published_notation`.
- `etc.` : indique une suite triviale ou longue. Arrêter au dernier
  coup explicitement noté.
- `30.48x6` (ou similaire avec point) : notation ambiguë rencontrée
  une fois (BEG_CH16_010). Disambiguation manuelle nécessaire.

---

## 5. Wrapper pédagogique — état actuel

**Statut** : non standardisé.

Le manuel Débutant a défini son propre wrapper local `BeginnerPosition`
dans `fixtures_debutant.py`, avec naming aligné sur `DuboisCoupRoyalCase`
de dilf (`published_notation`, `final_move`).

**Pour le manuel Intermédiaire** : deux options possibles selon le
choix éditorial :

- **Option A — Wrapper local** : définir `IntermediatePosition` sur le
  même modèle que `BeginnerPosition`, accepté pour la production mais
  duplique la dataclass.
- **Option B — Migration vers wrapper standardisé** : implémenter
  d'abord la suggestion §1 du backlog (création de
  `PedagogicalPosition` dans dilf), puis utiliser cette classe pour
  Intermédiaire ET pour rétrofitter Débutant.

**Recommandation** : Option B si l'effort de migration est < 1h. Sinon
Option A et reporter §1 du backlog à plus tard.

---

## 6. Suggestions backlog dilf — état d'avancement

| # | Suggestion | Statut | Priorité |
|---|---|---|---|
| §2 | Module `pedagogy/notation/dubois.py` (pions) | ✅ Mergé PR #31 | — |
| §3 | Extension dames du module dubois | ✅ Mergé PR #32 | — |
| §5 (partiel) | Glossaire notation Dubois pions+dames | ✅ Livré PR #31 + #32 | — |
| **§1** | Wrapper `PedagogicalPosition` standardisé | À faire | **Haute** |
| **§4** | Détecteur de coquilles PDF | À faire | Haute |
| §5 (suite) | Glossaire étendu (`ad lib`, `+1p`, `etc.`) | À faire | Moyenne |
| §6 | Détecteurs de motifs (10 coups nommés) | 5/16 disponibles | Moyenne |
| §7 | Validation interactive des blocages | À faire | Moyenne |
| **§8** | Validateur prose/fixtures | ✅ Outillage local fourni (validate_prose_vs_fixtures.py) | Haute |
| **S1** | Pipeline `index_prose.py` (chunk + tag + embed + emit) — *stratégie* | 🟡 Squelette livré (`scripts/index_prose.py`, 5 sous-commandes, embed optionnel) ; embeddings réels + corpus à câbler | **Haute** |
| **S2** | Wrapper `StrategicConcept` dans `pedagogy/` — *stratégie* | 🟡 Format livré (`pedagogy/prose/{passages,concepts}.py` conformes §6) ; pas de fixtures encore | Haute |
| **S3** | `validate_strategic.py` (traçabilité + passage Scan) — *stratégie* | À faire | Haute |
| S4 | Détection automatique du `system` dans les passages — *stratégie* | À faire | Moyenne |
| S5 | Banque de positions-types par système (§4.S4) — *stratégie* | À faire | Moyenne |
| **S6** | Prompt système contraint usage B (garde-fou §8 stratégie) | À faire | **Haute** |

Les lignes **S1-S6** sont induites par `CADRAGE_STRATEGIE.md` (production
de contenu stratégique). S1, S2, S3, S6 sont bloquantes pour l'usage B
(explication temps réel dans l'app) ; S4 et S5 améliorent la qualité.

**Pour démarrer Intermédiaire** : §1 et §4 sont les seules suggestions
qui pourraient bloquer ou ralentir la production. §6 (détecteurs) est
optionnel — utile pour les exercices guidés mais pas pour les fixtures.

---

## 7. Statistiques de référence (cycle Débutant)

À utiliser pour calibrer les attentes du manuel Intermédiaire :

| Mesure | Valeur Débutant | Projection Intermédiaire |
|---|---|---|
| Fixtures totales | 166 | 200-250 (volume + grand) |
| Sources CORPUS | 92% (152) | viser 90%+ |
| Avec final_move reconstruit | 81% (135) | viser 85%+ avec dames PR #32 |
| Coquilles PDF | 4% (6) | prévoir 8-12 sur Intermédiaire |
| Interpellations §4.11 | 3 | viser 0-2 avec patterns §4.13 |
| Durée de production | ~1 session intensive | similaire si industrialisé |

---

## 8. Conventions de noms produits par les conversations

Pour homogénéiser la production cross-niveaux :

- IDs fixtures : `BEG_CHnn_mmm` (Débutant), `INT_CHnn_mmm` (Intermédiaire),
  `ADV_CHnn_mmm` (Avancé), `EXP_CHnn_mmm` (Expert).
- Fichiers : `manuel_<niveau>.md`, `fixtures_<niveau>.py`,
  `sources_<niveau>.md`, `ameliorations_dilf_<niveau>.md`,
  `RESOLUTIONS_<niveau>.md`, `BLOCAGES_<niveau>.md` (si applicable).
- Wrapper : `BeginnerPosition`, `IntermediatePosition`, etc. (ou
  `PedagogicalPosition` partagée si §1 du backlog livré).

---

## 9. Pour aller plus loin

- **Archive historique** du backlog initial Débutant : voir
  `ameliorations_dilf_debutant.md` dans le repo dilf (sous
  `manuels/debutant/` ou équivalent). Conservé pour traçabilité.
- **Résolutions consignées** Débutant : `RESOLUTIONS_debutant.md`
  (11 résolutions R001-R011, dont la typologie de coquilles §3 ci-dessus).
- **PRs dilf de référence** : #30 (motifs P3), #31 (notation dubois pions),
  #32 (notation dubois dames).
