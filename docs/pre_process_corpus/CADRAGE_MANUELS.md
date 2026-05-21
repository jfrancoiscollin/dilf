# CADRAGE — Production des 4 manuels Draught Master

> **Document de référence partagé entre toutes les conversations du projet.**
> À déposer dans les fichiers du projet (et y rester). Chaque nouvelle conversation
> sur ce sujet doit commencer par : *"Lis le CADRAGE_MANUELS.md et le JOURNAL.md."*

---

## 🛑 PRINCIPE DIRECTEUR — ZÉRO INVENTION (prime sur tout le reste)

> Ce principe a été établi après que la production initiale du manuel
> Débutant a révélé des combinaisons inventées, des notations fabriquées
> de mémoire, des couleurs de pièces inversées et un narratif tactique
> entièrement faux (cf JOURNAL.md). La cause racine unique : **Claude a
> rédigé du commentaire tactique en s'appuyant sur son « sens du jeu »,
> qu'il n'a pas.** Claude ne « voit » pas le damier ; sur une combinaison
> de plus de quelques demi-coups, il produit du plausible-mais-faux.
>
> **La règle est donc absolue et prime sur toute autre section de ce
> document :**
>
> **Claude n'invente AUCUNE combinaison, AUCUNE analyse, AUCUN verdict
> tactique.** Chaque élément du manuel a une source vérifiable :
>
> | Élément | Source unique autorisée |
> |---------|-------------------------|
> | La position | Extraction pixel du corpus (`extract_diagrams.py`) — jamais saisie de mémoire |
> | La solution / les coups | `published_notation` recopiée **verbatim** du livre, OU le PV fourni par le moteur Scan |
> | Le jugement tactique (« ça gagne », « +2 », « meilleur coup X », « menace Y ») | **Moteur Scan uniquement** |
> | La couleur / géométrie / menace directe | `position_facts.py` (déterministe) |
> | La structure, le regroupement thématique, la mise en forme | Claude (sans affirmation tactique) |
>
> **Le rôle de Claude est de METTRE EN MOTS ce que les outils et le
> moteur ont établi — rien d'autre.** Si une information tactique n'a
> été établie ni par le corpus verbatim ni par Scan, Claude ne l'écrit
> pas : il marque la position `verified=false` et la consigne dans
> `A_VERIFIER_MOTEUR.md`.

### Ce que Claude PEUT produire seul (déterministe, vérifiable)

- La **description de la position** : pièces, couleurs, trait — via
  `position_facts.py`, jamais de mémoire.
- La **notation publiée recopiée verbatim** depuis le PDF (`pdftotext`),
  jamais paraphrasée ni reconstruite.
- Les **faits géométriques simples** : coups légaux d'un pion, menace
  directe pion/pion — via `position_facts.py`.
- La **structure du manuel** : découpage en chapitres, regroupement des
  positions du corpus par thème.
- La **mise en forme pédagogique SANS affirmation tactique** : « voici
  une position illustrant tel thème ; observez tel motif ».

### Ce que Claude NE produit JAMAIS seul (attend Scan)

- « Cette combinaison gagne » / « mène à +2 » / « est décisive ».
- « Le meilleur coup est X ».
- « Les Blancs menacent Y » au-delà de la menace directe pion/pion
  calculable par `position_facts.py`.
- Toute **reconstruction d'une variante** non présente verbatim dans le
  corpus.
- Tout commentaire qui suppose d'avoir « déroulé » mentalement une
  combinaison.

### La chaîne de production obligatoire

```
PDF corpus Dubois
   │  (1) extract_diagrams.py — extraction pixel, déterministe
   ▼
Positions brutes (pièces + trait)
   │  (2) pdftotext — solution publiée verbatim
   ▼
published_notation (texte brut du livre, jamais paraphrasé)
   │  (3) reconstruct_capture + position_facts.py — déterministe
   ▼
final_move + faits géométriques vérifiés
   │  (4) ⚠️ MOTEUR SCAN (backend Draught Master, hors conversation Claude)
   │      → lancé par l'utilisateur ou Claude Code
   │      → dépose un fichier scan/scan_analysis_<niveau>.json
   ▼
verified=true + eval + PV (variante principale réelle)
   │  (5) Claude lit le fichier Scan et RÉDIGE le commentaire À PARTIR
   │      du PV — sans rien inventer
   ▼
Manuel publiable
```

**Le maillon (4) ne se fait PAS dans une conversation Claude** : Scan
vit dans le backend Draught Master. L'utilisateur ou Claude Code lance
Scan et dépose les analyses dans un fichier que Claude lit (cf §4.6 et
le format ci-dessous). Claude rédige le commentaire en s'appuyant sur le
champ `pv` (la variante calculée par Scan), jamais en reconstruisant la
ligne lui-même.

### Format du fichier d'analyses Scan

Emplacement : **`pre_process_corpus/scan/scan_analysis_<niveau>.json`**
(ex. `scan_analysis_debutant.json`). Une entrée par fixture :

```json
{
  "BEG_CH07_001": {
    "verified": true,
    "eval_start": -0.4,
    "best_move": "42-37",
    "pv": ["42-37", "25x34", "40x20", "15x24", "28-22", "17x28", "32x14"],
    "eval_after_pv": 1.8,
    "winning_for": "white",
    "scan_depth": 19,
    "notes": "La published_notation correspond au PV de Scan."
  }
}
```

| Champ | Usage pour la rédaction |
|-------|--------------------------|
| `verified` | Claude ne rédige de commentaire tactique **que si `true`** |
| `eval_start` | évaluation de la position de départ (unités-pion) |
| `best_move` | meilleur coup selon Scan |
| `pv` | **variante principale complète** — c'est ELLE que Claude commente, jamais une ligne reconstruite |
| `eval_after_pv` | éval après la séquence (pour qualifier le gain) |
| `winning_for` | `white` / `black` — camp gagnant |
| `scan_depth` | profondeur d'analyse (traçabilité) |
| `notes` | signale notamment si `published_notation` diverge du PV Scan (= notation corrompue, cf CH07_002) |

Quand `published_notation ≠ pv`, **le PV Scan fait foi** ; la notation
du livre est traitée comme suspecte et la divergence est notée dans le
commentaire et dans `A_VERIFIER_MOTEUR.md`.

### Garde-fou de publication

**Aucune fixture `verified=false` ne doit être présentée au lecteur en
production.** Mécanisme retenu : **l'application masque à l'affichage
les fixtures `verified=false`** (le lecteur ne voit jamais une
combinaison non vérifiée par Scan). Les fixtures non vérifiées peuvent
exister dans le code (utiles pour le suivi), mais restent invisibles
côté lecteur jusqu'à leur passage Scan. *(Défaut proposé — l'utilisateur
peut préférer un build bloquant ou une branche/dossier séparés ;
ajuster ici le cas échéant.)*

---

> **Infrastructure technique — outillage obligatoire.**
> Le repo **`dilf`** (Draught Intelligence Learning Framework) — public à
> `https://github.com/jfrancoiscollin/dilf` — fournit l'outillage que toute
> conversation doit utiliser pour produire les manuels :
>
> - **`pedagogy/game.py`** : le schéma de référence (`GameState`, `Move`,
>   `parse_fen`, `state_to_fen`). Toute fixture publiée doit produire un
>   `GameState` valide via ce module.
> - **`pedagogy/notation/dubois.py`** : reconstruction des rafles depuis
>   la notation courte Dubois `aXb`. Supporte les pions (`reconstruct_pawn_capture`)
>   ET les dames (`reconstruct_king_capture`), via un dispatcher unifié
>   `reconstruct_capture`. Module mergé via PR #31 et étendu via PR #32.
> - **`scripts/extract_diagrams.py`** : le pipeline d'extraction
>   pixel-déterministe qui transforme un PDF Dubois en fixtures Python en
>   ~1 minute, $0, sans hallucination. **C'est l'outil obligatoire** pour
>   transcrire les positions d'un PDF du corpus.
> - **`docs/corpus/`** : tout le corpus de référence (53 PDFs, ~6100 pages) est
>   déjà dans le repo. Aucune ré-upload nécessaire.
>
> **Conséquence pratique :** au début de chaque conversation, après avoir lu
> ce cadrage, le journal et `ETAT_DILF.md`, Claude clone dilf (`git clone --depth 1
> https://github.com/jfrancoiscollin/dilf.git`), installe les deps
> (`pip install -e ".[extract]" --break-system-packages`) et lance le pipeline
> sur les PDFs pertinents du niveau visé. La transcription manuelle case par
> case d'un diagramme Dubois est **interdite** dès lors que le pipeline est
> applicable — voir §4.10 et §5.

> **Mode de production industrialisé (issu du cycle Débutant).**
> La production du manuel Débutant a établi un pattern reproductible qui
> doit être réutilisé pour les niveaux suivants :
>
> 1. **Définition déclarative** des chapitres dans des fichiers `chN_def.py`
>    qui contiennent une liste `SELECTION` de tuples
>    `(fixture_id, page, region, notation, has_king_rafle, meta_dict)`.
> 2. **Génération automatique** des fixtures via un script
>    `generate_chapter.py` qui :
>    - lit les positions extraites par le pipeline dilf,
>    - rejoue la `published_notation` via `pedagogy.notation.dubois`,
>    - reconstruit le `final_move`,
>    - émet le code Python prêt à intégrer.
> 3. **Intégration** dans `fixtures_<niveau>.py` via un patch templating
>    (recherche du marqueur d'index, insertion du chapitre, mise à jour
>    de l'index).
> 4. **Validation moteur** continue via un script `validate_final_moves.py`
>    qui vérifie que chaque `final_move` est une rafle maximale légale
>    selon les règles FMJD.
>
> Cette industrialisation a permis de produire 166 fixtures sur 16
> chapitres en une seule session, avec un taux d'échec de reconstruction
> de 2% (3 blocages, tous résolus par interpellation §4.11). Elle est
> **obligatoire** pour les manuels Intermédiaire et suivants. Le code
> de `generate_chapter.py` et `validate_final_moves.py` produits pendant
> le cycle Débutant doit être réutilisé tel quel ou minimalement adapté
> (changement de classe wrapper, voir §3).

---

## 1. Objectif

Produire **4 manuels pédagogiques de jeu de dames international (FMJD 10×10)**, un par
niveau, exploitables à la fois par un lecteur humain et par le framework `pedagogy/`
de l'application Draught Master.

| Manuel | Niveau cible | Cible volume | Positions cibles |
|--------|--------------|--------------|------------------|
| 1 | Débutant | 30-50 p prose | 100-200 positions |
| 2 | Intermédiaire | 40-50 p prose | 100-200 positions |
| 3 | Avancé | 40-50 p prose | 100-200 positions |
| 4 | Expert | 40-60 p prose | 100-200 positions |

---

## 2. Livrables par manuel

Pour **chaque** niveau, trois fichiers produits par Claude :

1. **`manuel_<niveau>.md`** — manuel prose pédagogique, lisible par un humain,
   organisé en chapitres thématiques, avec FEN intégrés dans le texte.
2. **`fixtures_<niveau>.py`** — fichier Python contenant les positions sous forme
   de `TacticalPosition` (ou équivalent défini par le framework `pedagogy/`),
   directement importable dans les tests/exercices de l'application.
3. **`sources_<niveau>.md`** — table de traçabilité : pour chaque position,
   l'origine exacte (PDF + page, ou "connaissance générale Claude"),
   et son statut de vérification.

---

## 3. Format des fixtures Python

**Le schéma de référence est celui de `pedagogy/game.py` dans dilf** — il
existe, il est testé (210 tests, mypy --strict clean), il est ce que consomme
le moteur Scan et les détecteurs de motifs. Toute fixture publiée doit
produire un `GameState` valide.

```python
# Schéma dilf (pedagogy/game.py)
from pedagogy.game import GameState, Move, parse_fen, state_to_fen

state = GameState(
    white_men=frozenset({31, 32, 33}),
    white_kings=frozenset(),
    black_men=frozenset({1, 2, 3}),
    black_kings=frozenset(),
    turn="white",            # Literal["white", "black"]
)
```

**Convention FEN dames** (telle qu'acceptée par `parse_fen`) :
- Format : `<trait>:W<pieces blanches>:B<pieces noires>` avec `<trait>` = `W` ou `B`
- Préfixe `K` devant une case = dame. Ex : `W:W31,32,K40:B7,K12,18`
- Cases numérotées 1-50 selon convention FMJD standard
- Case 1 = haut-gauche (côté noir), case 50 = bas-droite (côté blanc)

**Convention notation des coups :**
- Coup simple : `32-28`
- Prise : `31x22` (case d'arrivée après la prise)
- Rafle : `31x22x13x4` (toutes les cases d'arrivée intermédiaires)
- Promotion : implicite si arrivée sur la dernière rangée

### Couche pédagogique (ce que produit Claude par-dessus)

`GameState` est une primitive nue (position + trait). Le contenu pédagogique
d'un manuel (thème, concept enseigné, solution annotée, explication) vit dans
un wrapper **`BeginnerPosition`** (ou `IntermediatePosition`, etc. selon le
niveau) qui référence la position brute par son `crop_id` ou par sa FEN.

**Template de référence dans dilf** : `pedagogy/tests/fixtures/dubois_coup_royal.py`
(la dataclass `DuboisCoupRoyalCase`). C'est la fixture la plus aboutie côté
bibliographie/pédagogie de dilf. Le wrapper de manuel **doit en reprendre les
conventions de naming** :

| Champ dilf (`DuboisCoupRoyalCase`) | Rôle | Repris tel quel dans le manuel ? |
|---|---|---|
| `name` | identifiant lisible | renommé `title` (l'`id` est un slug stable distinct) |
| `book`, `chapter`, `diagram`, `page` | bibliographie | regroupés en `source_ref` + `crop_id` |
| `description` | concept enseigné | renommé `concept` (1 phrase) |
| **`published_notation`** | notation Dubois verbatim | **identique** |
| **`final_move`** | `Move` reconstruit | **identique** |
| `game_attribution` | provenance historique éventuelle | ajouté si pertinent |
| `expected_captures_min` | seuil de détecteur | non applicable manuel |

**Schéma effectif pour un manuel** :

```python
from dataclasses import dataclass
from enum import Enum
from pedagogy.game import GameState, Move


class SourceType(Enum):
    CORPUS = "corpus"               # Extraite d'un PDF via dilf extract_diagrams
    GENERAL_KNOWLEDGE = "general"   # Construite à partir de la littérature classique
    INVENTED = "invented"           # Construite par Claude pour illustrer un concept


@dataclass(frozen=True)
class BeginnerPosition:  # ou IntermediatePosition, etc.
    # Identité pédagogique
    id: str                          # ex: "BEG_CH03_001" (slug stable)
    theme: str                       # ex: "prise_majoritaire", "coup_de_mazette"
    title: str                       # ex: "Dubois D1 — Le schéma CONTACT-PRISE-RAFLE"

    # Position (référence dilf)
    state: GameState

    # Pédagogie + bibliographie (naming aligné DuboisCoupRoyalCase)
    concept: str = ""                # Le principe enseigné (1-2 phrases)
    published_notation: str = ""     # Notation Dubois verbatim
    final_move: Move | None = None   # Reconstruction Move (cf §4.10)
    explanation: str = ""            # Pourquoi la solution est gagnante (3-4 phrases)

    # Traçabilité étendue (spécifique manuels)
    source: SourceType = SourceType.GENERAL_KNOWLEDGE
    source_ref: str = ""             # ex: "dubois_apprent_combin_p6_d01"
    crop_id: str = ""                # ex: "crops/page_006_d01.png" si CORPUS
    verified: bool = False           # Mis à True après vérification moteur Scan
    confidence: str = "medium"       # "high" | "medium" | "low"
    claude_notes: str = ""           # Doutes, coquilles PDF, équivalences de rafle
```

**Pourquoi ce découpage** : la position brute (`state`) est garantie correcte
par le pipeline pixel-déterministe ; la couche pédagogique ajoutée par Claude
(thème, concept, explication) reste séparée et peut évoluer sans toucher
aux données de référence. La notation publiée est stockée **verbatim** depuis
le PDF — pas de paraphrase, pas de "correction" silencieuse par Claude (mais
correction explicite documentée dans `claude_notes` si coquille PDF avérée,
voir §4.11 et `RESOLUTIONS_<conv>.md`).

**À chaque nouvelle conversation manuel**, Claude :
1. Inspecte `pedagogy/tests/fixtures/*.py` avant de redéfinir le wrapper —
   peut-être qu'une dataclass `PedagogicalPosition` partagée existe déjà
   (proposition en cours, cf `ameliorations_dilf_debutant.md` §1).
2. À défaut, définit son wrapper local en respectant le naming
   `published_notation` / `final_move` ci-dessus, et signale la divergence
   dans `ameliorations_dilf_<niveau>.md` pour consolidation ultérieure.

---

## 4. PROTOCOLE ANTI-HALLUCINATION

> C'est la section la plus importante du document. Elle existe parce que Claude
> peut produire des positions FEN crédibles mais fausses (pièces sur mauvaises cases,
> rafles impossibles, coup royal annoncé qui n'existe pas). Chaque règle ci-dessous
> existe pour fermer une voie d'erreur précise.

### 4.1. Règle de la source obligatoire

**Toute position publiée porte un champ `source` non vide.** Il n'y a pas
de quatrième option. Une position est :

- **`CORPUS`** : Claude l'a lue dans un PDF uploadé dans la conversation,
  avec page exacte référencée dans `source_ref`.
- **`GENERAL_KNOWLEDGE`** : motif canonique du jeu de dames international
  (coup royal de Manoury, opposition de pion, finale 2 pions contre 1, etc.),
  documenté dans la littérature publique.
- **`INVENTED`** : Claude a construit la position de toutes pièces pour
  illustrer un concept. **À utiliser avec parcimonie, jamais plus de 15 %
  des positions d'un manuel.**

Quand Claude produit une position, il indique honnêtement laquelle des trois
sources s'applique. **L'invention déguisée en source corpus est un échec
critique du protocole.**

### 4.2. Règle de l'autoévaluation de confiance

Chaque position porte un champ `confidence` parmi `high | medium | low`.

- **`high`** : position lue dans un PDF du corpus avec diagramme net et
  légende claire, OU position canonique de niveau "abécédaire" du jeu
  (position de départ, opposition simple, etc.).
- **`medium`** : position de connaissance générale, motif classique mais
  Claude ne peut pas garantir la justesse case par case sans vérification.
- **`low`** : position inventée, ou tirée d'un PDF mais avec doute
  sur la transcription. **Toute position `low` doit avoir un `claude_notes`
  expliquant le doute.**

### 4.3. Règle des cases sombres uniquement

Le damier de dames international n'utilise que les **cases sombres**,
numérotées 1-50. Une pièce sur une case `> 50` ou `< 1` est une erreur
de Claude. Le pipeline de validation côté framework doit échouer dans
ce cas.

Claude vérifie systématiquement, avant de publier une position, que
toutes les cases mentionnées sont dans `[1, 50]`.

### 4.4. Règle de la zone de promotion

- Une dame blanche (`WK<case>`) ne peut exister que si la case a déjà
  été atteinte par un mouvement passant par la rangée 1-5.
- Une dame noire (`BK<case>`) ne peut exister que si la case a déjà
  été atteinte par un mouvement passant par la rangée 46-50.

Pour une **position d'exercice statique** (pas un déroulement de partie),
les dames peuvent être placées n'importe où, ce qui est légal. Mais Claude
ne place pas de pion blanc sur les cases 1-5 (il aurait déjà été promu),
ni de pion noir sur les cases 46-50.

### 4.5. Règle du contrôle des solutions

Pour chaque position avec une `solution`, Claude vérifie mentalement
au moins :

1. **Les pièces qui bougent existent bien dans la position de départ**
   (pas de coup `32-28` si la case 32 est vide).
2. **Les pièces capturées existent bien** (pas de `31x22` si la case 27
   ou 26 traversée est vide).
3. **La prise est légalement obligatoire** si la règle de prise maximale
   l'impose (cohérence avec les règles FMJD).
4. **La rafle s'arrête là où elle s'arrête** (pas de prise possible
   au-delà sinon elle serait obligatoire).

Si Claude a un doute sur l'une de ces quatre vérifications,
`confidence = low` et `claude_notes` documente le doute.

### 4.6. Règle du marqueur `verified=False` par défaut

Toutes les positions sont publiées avec `verified=False`. La vérification
définitive se fait **côté framework**, en passant chaque fixture au moteur
Scan via `scan_engine.evaluate_pos()` et en confirmant :

- que la position est légale (cohérence FMJD)
- que la `solution` annoncée est jouable
- que le verdict du moteur est cohérent avec l'`explanation`

Ce passage transforme `verified=False` → `verified=True`. **Aucune fixture
ne devrait entrer en production avec `verified=False`.**

**Mécanique concrète (cf PRINCIPE DIRECTEUR en tête de document)** :
le moteur Scan n'est PAS accessible dans une conversation Claude (il vit
dans le backend Draught Master). L'utilisateur ou Claude Code lance Scan
et dépose les analyses dans
`pre_process_corpus/scan/scan_analysis_<niveau>.json` (format détaillé
dans le préambule). Claude lit ce fichier et **rédige le commentaire
tactique à partir du champ `pv`** (variante principale calculée par
Scan), jamais d'une ligne qu'il aurait reconstruite. Tant que le fichier
Scan ne contient pas d'entrée `verified=true` pour une fixture, son
commentaire tactique reste interdit et la fixture est masquée à
l'affichage (garde-fou de publication).

### 4.7. Règle de l'aveu

Si Claude se rend compte en cours de production qu'il a publié une position
fausse, ou s'il est incertain sur une position déjà livrée, **il le signale
explicitement dans la conversation, par son ID**. Mieux vaut une fixture
rétractée qu'une fixture fausse en base.

### 4.8. Règle de la séparation "lu" vs "déduit"

Quand Claude transcrit une position depuis un PDF du corpus :

- Ce qui est **lu directement sur le diagramme** (pièces, trait, légende)
  → `source = CORPUS`, `confidence = high`.
- Ce qui n'est **pas écrit dans le livre** (la suite d'une solution dont
  le livre ne donne que le premier coup, un jugement tactique que le
  livre n'énonce pas) → **Claude ne le déduit PAS** (cf PRINCIPE
  DIRECTEUR). Il laisse le champ vide / `final_move=None`, marque
  `verified=false`, et attend l'analyse Scan. La règle initiale qui
  autorisait Claude à « déduire la solution complète » est **abrogée** :
  c'est précisément cette déduction qui a produit les combinaisons
  fausses du manuel Débutant.

### 4.9. Règle des thèmes canoniques

Les thèmes (champ `theme`) sont normalisés à travers les 4 manuels.
Un fichier `themes.py` partagé liste les thèmes valides. Claude ne
crée pas de nouveau thème sans l'annoncer dans `JOURNAL.md`.

Thèmes initiaux (à enrichir au fil des manuels) :

```
# Tactique
coup_royal | coup_turc | coup_de_talon | coup_de_bord
prise_majoritaire | sacrifice_attractif | rafle_simple

# Positionnel
centre | aile | tempo | opposition | colonne | echange

# Finales
finale_pion_vs_pion | finale_2v1 | finale_dame_vs_pion
finale_dame_vs_dame | promotion_forcee | breakthrough

# Ouvertures
classique | aile_droite | aile_gauche | partie_du_centre
```

### 4.10. Règle de l'extraction outillée (interdiction de transcrire à la main)

**Quand une position provient d'un PDF du corpus dilf, sa transcription
case par case par Claude est interdite.** Le pipeline pixel-déterministe
`scripts/extract_diagrams.py` de dilf est l'outil obligatoire — il est
prouvé sans hallucination (pixel arithmetic, pas de LLM), idempotent,
gratuit, et produit ~1 minute pour un livre complet de ~300 positions.

Conséquences :

- **Pour toute position `source=CORPUS`** : Claude lance `extract_diagrams`
  sur le PDF correspondant, récupère la fixture `DuboisDiagram` issue du
  `crop_id` désiré, et la matérialise via `to_state(diag)`. La position
  n'est jamais réécrite par Claude — elle est référencée par `crop_id`.
- **`confidence=high`** quand l'extraction sort sans warning ; le doute
  n'a plus à être marqué pour les positions extraites, contrairement à
  l'ancien protocole de transcription manuelle.
- **Solutions PDN** : la solution publiée par Dubois est extraite par
  `pdftotext` et stockée **verbatim** dans `published_notation`. Si Claude
  ne comprend pas la solution (notation qui semble incohérente avec la
  position), il **ne corrige pas** : il enregistre le doute dans
  `claude_notes` et laisse la vérification moteur trancher.
- **`source=INVENTED` ou `GENERAL_KNOWLEDGE`** : Claude peut construire la
  position en utilisant `GameState(...)`, mais doit ensuite faire
  `state_to_fen(state)` puis `parse_fen(fen)` pour s'assurer qu'elle est
  valide structurellement (cases dans 1-50, pas de doublons, etc.).
  Le `verified=False` reste obligatoire jusqu'à passage moteur.

**Si le pipeline échoue** sur un diagramme particulier (le rapport
`extract` indique `failure`), Claude le note dans `JOURNAL.md` avec le
`crop_id` concerné et **n'essaie pas de transcrire manuellement** — il
saute le diagramme et continue. Le tuning des thresholds
(`--white-threshold`, `--black-threshold`) ou un éventuel deuxième passage
est de la responsabilité du framework, pas de la conversation Claude.

### 4.11. Règle de l'interpellation (human-in-the-loop)

Cette règle existe parce que Claude peut boucler indéfiniment sur une
incohérence qu'il ne sait pas résoudre, en consommant temps et tokens.
Elle remplace le bouclage par un arrêt-question structuré, et transforme
chaque incohérence rencontrée en information actionnable pour améliorer
dilf en aval.

**Le protocole** s'applique à **toutes les classes de blocage** :

- incohérence position / solution publiée (D1 typique)
- échec du pipeline `extract_diagrams` sur un crop
- notation Dubois inconnue ou ambiguë
- terme pédagogique douteux à attribuer
- doute sur le chapitre du manuel où ranger une position
- toute autre situation où Claude n'a pas de réponse fiable

**Les trois temps :**

1. **Deux tentatives automatiques.** Claude tente de résoudre seul :
   - Tentative 1 : revérifier l'évidence brute (re-lire avec
     `pdftotext -layout` pour exclure une corruption d'OCR ; rasteriser
     la page à plus haut DPI pour exclure un artefact visuel ; relire
     les paragraphes Dubois autour de la position pour exclure un
     contexte manqué).
   - Tentative 2 : tester une hypothèse alternative (par exemple,
     interpréter `(17x28)` comme une rafle multiple, ré-extraire avec
     d'autres thresholds, etc.).
   - Si l'une résout, Claude continue et **consigne la résolution dans
     `RESOLUTIONS_<conv>.md`** (voir §9).

2. **Interpellation structurée.** Si les deux tentatives échouent,
   Claude **s'arrête** et envoie à l'utilisateur :
   - L'ID complet de la position : `<livre>` (nom du PDF), `<page>`,
     `<crop_id>` (ex : `crops/page_006_d01.png`)
   - **L'image rasterisée du diagramme** (200 DPI ou plus, croppée sur
     le board), envoyée comme attachement visible dans la conversation
     pour que l'utilisateur puisse trancher d'un coup d'œil
   - La position telle qu'extraite par dilf (`white_men`, `black_men`,
     `turn`)
   - La solution publiée verbatim depuis le PDF
   - Une description précise de l'incohérence ou du blocage
   - Les deux hypothèses testées et pourquoi elles n'ont pas résolu
   - La question précise posée à l'utilisateur

   Format de l'interpellation :

   ```
   ⚠️  BLOCAGE — interpellation human-in-the-loop

   Livre   : <nom du PDF>
   Page    : <n°>
   Crop    : <crop_id>
   [image rasterisée du diagramme attachée]

   Position extraite par dilf :
     white_men: {...}
     black_men: {...}
     turn: ...

   Solution publiée (verbatim PDF) :
     "<extrait pdftotext>"

   Incohérence :
     <description>

   Tentatives :
     1. <tentative 1> → <résultat>
     2. <tentative 2> → <résultat>

   Question pour toi :
     <question précise>
   ```

3. **Mémorisation et reprise.** Une fois la réponse de l'utilisateur
   reçue, Claude :
   - Applique la résolution à la position en cours.
   - **Consigne la résolution dans `RESOLUTIONS_<conv>.md`** (voir §9)
     avec : l'ID position, la nature du blocage, la résolution apportée
     par l'utilisateur, et **la règle d'inférence à appliquer aux
     futurs cas similaires** dans la conversation.
   - Si le même type de blocage se reproduit, Claude **applique la règle
     mémorisée sans re-déranger l'utilisateur**. La règle ne migre pas
     d'une conversation à l'autre — chaque conversation reconstruit ses
     résolutions, qui seront consolidées en fin de cycle via le livrable
     `ameliorations_dilf` (§9).

**Pertinence du déclenchement.** L'utilisateur n'est pas un service de
support : Claude n'interpelle que sur des blocages réels, après avoir
honnêtement essayé deux pistes. Pour les choix purement éditoriaux (quel
titre donner à un chapitre, faut-il mettre tel exemple avant tel autre),
Claude tranche lui-même et le consigne dans `RESOLUTIONS_<conv>.md` pour
revue de fin de cycle.

### 4.12. Mode "fonce" — production batch avec interpellations différées

Le mode "fonce" est une variante explicite du workflow §5 qui autorise
Claude à produire plusieurs chapitres consécutifs **sans valider à
chaque étape** avec l'utilisateur. Activé par phrase utilisateur du
type *"fonce, enchaîne les chapitres"* (cf cycle Débutant).

**Différences avec le mode normal** :

- **Pas de pause de validation** entre chapitres. Claude produit le
  chap N, intègre, lance la validation moteur, puis passe directement
  au chap N+1.
- **Interpellations §4.11 différées en batch.** Quand un blocage
  survient, Claude marque la fixture concernée `final_move=None` avec
  un `claude_notes` explicite, consigne le blocage dans un fichier
  `BLOCAGES.md` (ou équivalent), puis continue. L'utilisateur traite
  les blocages **en lot à la fin de la session de production**.
- **Validation moteur cumulative** plutôt qu'incrémentale : Claude
  lance `validate_final_moves.py` à intervalles réguliers (par ex.
  tous les 3-4 chapitres) plutôt qu'à chaque insertion.
- **Reporting compressé** : à chaque chapitre intégré, Claude rapporte
  en 1-2 lignes (nombre de fixtures + bilan reconstruction) plutôt
  qu'en paragraphe détaillé.

**Quand revenir au mode normal** :

- Si un blocage est **bloquant pour la suite** (par exemple : le PDF
  source contient une coquille systématique qui affecte tous les
  chapitres restants), Claude interpelle immédiatement.
- Si l'utilisateur intervient pour signaler une erreur visible, Claude
  pause et corrige avant de reprendre.
- En fin de cycle de production, Claude **doit** sortir du mode fonce
  et présenter le bilan complet + les blocages cumulés pour résolution.

### 4.13. Typologie des coquilles PDF (heuristiques de résolution)

L'expérience du cycle Débutant a fait émerger 3 patterns de coquilles
typographiques récurrents dans les solutions publiées par Dubois. Cette
typologie sert de **bibliothèque d'heuristiques** pour traiter
rapidement les blocages §4.11 sans interpellation systématique.

**Pattern 1 — Substitution de coup** (R009 cycle Débutant).
Un coup entier remplacé par un autre. Ex : Dubois écrit `43-38` mais
le vrai coup est `38-32`. Le pion source du coup publié peut ne pas
exister, ou le coup peut être illégal pour une autre raison.

*Heuristique* : énumérer tous les coups blancs simples possibles dans
l'état précédent et tester chacun pour voir s'il mène à la rafle
finale publiée. Si une **unique** solution existe, c'est elle.

**Pattern 2 — Inversion de chiffres** (R010 cycle Débutant).
Plusieurs nombres décalés systématiquement d'un digit. Ex : Dubois
écrit `37-31 (26x28)` mais le vrai est `27-21 (17x28)` — les digits
de gauche sont tous décalés de 1 (3↔2). Probable erreur de saisie ou
de mise en page.

*Heuristique* : recherche exhaustive sur toute la séquence
(plusieurs sacrifices + rafle finale) plutôt que correction
case-par-case. Si une unique combinaison reconstruite mène au même
résultat final, c'est elle.

**Pattern 3 — Inversion des opérandes** (R011 cycle Débutant).
Notation `(aXb)` écrite à l'envers, devrait être `(bXa)`. Le pion en
`a` n'existe pas dans la position, mais le pion en `b` existe et peut
prendre vers `a`.

*Heuristique* : **premier recours** quand un coup `(aXb)` est invalide
parce que `a` est vide — tester immédiatement `(bXa)` avant toute
autre piste.

**Statistique de référence** (cycle Débutant) : 6 coquilles PDF
détectées sur 152 fixtures CORPUS = **4% de taux de coquilles**. À
prévoir pour le manuel Intermédiaire : ~30 coquilles attendues sur un
corpus de ~700 fixtures.

**Politique** : si une coquille tombe clairement dans l'un des 3
patterns ci-dessus et que la recherche exhaustive donne une solution
unique, Claude peut **appliquer la correction sans interpellation**,
en documentant la coquille dans `claude_notes` ET en consignant la
résolution dans `RESOLUTIONS_<conv>.md`. Si la solution n'est pas
unique, ou si le pattern est inconnu, retour à §4.11 standard.

### 4.14. Cohérence prose / fixture — règles d'écriture du manuel

Cette règle existe parce que la production du manuel Débutant a généré
deux bugs qui ne sont apparus qu'en validation finale dans
Draught Master (cf JOURNAL.md "Bug report") : (1) section CH02
décrivant des positions canoniques imaginaires au lieu des positions
réelles des fixtures ; (2) grille ASCII de numérotation 1-50 dans le
chapitre 1, redondante et illisible. Les deux bugs ont une cause
commune : **Claude a écrit la prose "de mémoire" au lieu de la
construire par inspection des fixtures**.

**Règles d'écriture** :

1. **Inspecter les fixtures avant d'écrire la prose.** Pour chaque
   référence `<PREFIX>_CHnn_mmm` que la prose va citer, Claude lit
   d'abord son `state`, son `concept` et son `published_notation` —
   et la prose décrit **ces positions-là**, pas des positions
   canoniques fictives.

2. **Ne pas dupliquer ce que Draught Master rend.** Les damiers de
   l'app affichent la numérotation, les pièces, le trait. Le manuel
   prose ne doit donc pas :
   - reproduire la grille de numérotation en ASCII ou en tableau,
   - inclure des FEN complètes pour les positions affichables via
     `BEG_CHnn_mmm`,
   - décrire pièce par pièce une position que le rendering montre.

   Format préféré : *« Voir `BEG_CHxx_yyy` : <ce qu'il faut
   comprendre / observer / faire>. »* La position elle-même est dans
   l'app.

3. **Les blocs de code sont réservés aux formats abstraits.** Exemple
   acceptable : montrer la forme générique d'une FEN
   (`<trait>:W<cases>:B<cases>`) une fois. Exemples à éviter : FEN
   intégrales, longues séquences PDN coupées en lignes ASCII, grilles
   de numérotation.

4. **Validation obligatoire en fin de production.** Lancer
   `validate_prose_vs_fixtures.py` qui détecte automatiquement les
   passages où la prose mentionne des cases absentes de la fixture.
   Si recouvrement < 40%, désynchronisation grave probable, audit
   manuel requis. **L'audit final de §5 est ensuite obligatoire** —
   le script ne capture pas les erreurs géométriques de type « le
   pion X a deux coups possibles » (faux positifs filtrés par
   heuristique). Voir §5 pour la checklist d'audit complète.

5. **Rédaction assistée par `position_facts.py` (méthode obligatoire
   pour les manuels Intermédiaire et suivants).** L'expérience du
   manuel Débutant a montré que décrire une position « de mémoire »
   produit systématiquement des bugs (couleur inversée, coup
   impossible, notation fictive). La parade structurelle :

   - **Avant** d'écrire le moindre commentaire sur une position, Claude
     exécute `position_facts.py <fixture_id>` qui génère la **fiche de
     faits déterministe** : pièces et leur couleur exacte, trait, coups
     simples légaux de chaque pion (géométrie FMJD), menaces de capture
     immédiates pion/pion (les deux camps), `published_notation`
     verbatim, et trajet de la rafle finale.
   - Claude rédige la prose **par-dessus cette fiche**, en reprenant les
     faits tels quels. Il n'invente jamais un fait (couleur, coup,
     menace) : il le copie de la fiche.
   - La couche que Claude ajoute par-dessus est uniquement
     l'**interprétation pédagogique** : pourquoi la combinaison gagne,
     quel thème elle illustre, quelle est l'idée à retenir. Cette couche
     n'est PAS vérifiable déterministement et reste sous la
     responsabilité de Claude (rédaction) et du moteur Scan (vérité
     tactique, cf §4.6).
   - **Limite assumée** : `position_facts.py` ne calcule de façon fiable
     que les faits *matériels et géométriques simples* (couleur, coup de
     pion, menace directe pion/pion). Il ne déroule PAS les combinaisons
     tactiques (rafles multiples, coups de dame, sacrifices en chaîne).
     Pour les affirmations tactiques complexes (« l'attaque X-Y ouvre un
     coup de dame à Z »), la fiche ne tranche pas — c'est au moteur Scan
     de valider (§4.6). Claude marque ces affirmations comme
     « à vérifier au moteur » plutôt que de les corriger à l'aveugle
     (§4.7 règle de l'aveu).

---

## 5. Méthode de travail conversation par conversation

### Au début d'une conversation "manuel niveau X"

1. L'utilisateur écrit : *"Lis le CADRAGE_MANUELS.md, le JOURNAL.md et
   l'ETAT_DILF.md, puis attaque le niveau <X>."*
2. Claude relit ces trois documents. `ETAT_DILF.md` indique en
   particulier quels modules de `dilf` sont disponibles (rafles dame ?
   wrapper standardisé ? détecteur de coquilles ?) et oriente les
   choix d'implémentation.
3. **Claude clone dilf** (si pas déjà disponible) :
   ```bash
   git clone --depth 1 https://github.com/jfrancoiscollin/dilf.git
   cd dilf && pip install -e ".[extract]" --break-system-packages
   ```
   Le corpus complet (53 PDFs) est dans `docs/corpus/` — pas besoin d'upload.
4. **Étape 0 — Extraction outillée des positions du niveau visé.** Claude
   lance `scripts/extract_diagrams.py` sur les PDFs prioritaires du niveau
   (voir §6) :
   ```bash
   python3 -m scripts.extract_diagrams render \
       --pdf docs/corpus/<PDF_DU_NIVEAU>.pdf --pages <plage>
   python3 -m scripts.extract_diagrams extract
   python3 -m scripts.extract_diagrams materialize
   ```
   Cela produit `pedagogy/tests/fixtures/dubois_diagrams.py` avec
   toutes les positions disponibles. Claude inspecte le nombre extrait,
   les éventuels échecs, et le reporte au journal.
5. **Étape 0bis — Mise en place de l'outillage industriel.** Claude
   récupère depuis les livrables précédents (ou recrée si besoin) les
   deux scripts pivots :
   - `generate_chapter.py` : génère le code Python d'un chapitre
     depuis une définition déclarative `chN_def.py`.
   - `validate_final_moves.py` : valide structurellement les
     `final_move` reconstruits selon les règles FMJD.

   Ces scripts ont été produits pendant le cycle Débutant et doivent
   être réutilisés tels quels (avec adaptation mineure : changement
   du nom de la classe wrapper si §1 du backlog dilf a évolué).
6. Claude confirme en 3 lignes :
   - sa compréhension du niveau visé
   - les PDFs traités et le nombre de positions extraites par PDF
   - la table des matières qu'il propose

### Pendant la production

Workflow par chapitre (mode normal) :

1. **Définition** : Claude rédige un fichier `chN_def.py` avec la
   liste `SELECTION` des fixtures du chapitre (10-12 typiquement),
   incluant pour chacune : `fixture_id`, `page`, `region_index` du
   diagramme, `published_notation` verbatim depuis le PDF,
   `has_king_rafle` (booléen), métadonnées pédagogiques.
2. **Génération** : `python3 generate_chapter.py chN_def.py >
   chN_generated.py 2> chN_errors.txt`. Le script reconstruit chaque
   `final_move` et émet un rapport d'erreurs pour les blocages.
3. **Traitement des erreurs** :
   - Si erreur ∈ patterns connus (§4.13) → correction automatique +
     consignation dans RESOLUTIONS.
   - Sinon → interpellation §4.11 (mode normal) ou marquage
     `final_move=None` + journal BLOCAGES (mode fonce §4.12).
4. **Intégration** dans `fixtures_<niveau>.py` (patch templating
   éprouvé : recherche du marqueur d'index, insertion du chapitre,
   mise à jour de l'index).
5. **Validation moteur** : `python3 validate_final_moves.py` —
   vérifie que tous les `final_move` du fichier sont des rafles
   maximales légales. Si échec → debug avant de passer au chapitre
   suivant.

En mode "fonce" (§4.12), les étapes 3 et 5 sont décalées (validation
cumulée tous les 3-4 chapitres au lieu de chaque chapitre).

L'utilisateur peut interrompre à tout moment, demander une
vérification, signaler une erreur. Claude rétracte/corrige immédiatement.

### À la fin de la conversation

**Étape d'audit final — obligatoire avant livraison.** Cette étape
existe parce que la production du manuel Débutant a généré plusieurs
bugs uniquement détectés en validation Draught Master :

- Section CH02 décrivant des positions canoniques imaginaires au lieu
  des positions réelles des fixtures (commit dilf 7b7b6fa).
- Notations Dubois citées « de mémoire » dans CH03/CH04/CH13 au lieu
  de la `published_notation` réelle (commit dilf 62147b4).
- Affirmation géométriquement fausse « le pion 6 a deux coups
  possibles (6-1 ou 6-2) » alors que seul 6-1 existe sur un damier
  FMJD (commit dilf a4c647c).

Ces bugs ont une racine commune : **Claude écrit la prose plus vite
que le validateur automatique ne la vérifie, et certaines erreurs
échappent aux heuristiques outillées**. L'audit final est la dernière
barrière avant publication.

**Checklist d'audit, dans cet ordre, sans aucune étape sautée :**

1. **Validation moteur** — `python validate_final_moves.py`. Doit
   sortir `OK : N/N` sur les fixtures avec `final_move`. Tout échec
   est bloquant.

2. **Validation cross-référence prose ↔ fixtures** —
   `python validate_prose_vs_fixtures.py`. Doit sortir aucune
   désynchronisation grave. Les warnings « invention possible »
   sont à arbitrer manuellement (faux positifs typiques : cases
   d'arrivée de rafle citées dans la prose).

3. **Audit manuel chapitre par chapitre.** Pour **chaque** chapitre
   du manuel, Claude :
   - Liste toutes les références `<PREFIX>_CHnn_mmm` du chapitre.
   - Pour chaque référence, ouvre la fixture (state, theme, concept,
     published_notation, final_move) **et** relit le paragraphe de
     prose qui la cite.
   - Vérifie point par point :
     a. Les cases citées dans le paragraphe correspondent aux pièces
        réelles de `state` (pas de pion mentionné inexistant, pas
        de couleur inversée).
     b. Les notations citées dans la prose (`a-b`, `aXb`, séquences)
        sont identiques à `published_notation` de la fixture —
        **jamais** écrites de mémoire, **toujours** copiées depuis
        le champ.
     c. Les affirmations géométriques (« le pion X peut jouer Y »,
        « deux coups possibles », « rafle de N pions ») sont
        **vérifiées** contre la géométrie FMJD du damier : un coup
        simple existe seulement si la case d'arrivée est en diagonale
        adjacente et libre ; les cases de bord (1-5, 6, 15, 16, 25,
        26, 35, 36, 45, 46-50) ont moins de voisins diagonaux que les
        cases centrales.
     d. Le concept pédagogique annoncé est cohérent avec le `theme`
        de la fixture.

4. **Rapport d'audit dans `JOURNAL.md`.** Bloc dédié en fin de
   conversation, format :

   ```
   ### Audit final — <date>
   - validate_final_moves.py     : OK N/N
   - validate_prose_vs_fixtures  : <résumé warnings + arbitrage>
   - Audit chapitre par chapitre : <N> corrections appliquées
       - <ref> §<paragraphe>  : <nature de la correction>
       - ...
   ```

   Si aucune correction n'a été appliquée, écrire `aucune correction —
   l'audit n'a rien révélé`. **Ne pas mentir** : si la checklist a été
   sautée, le journaler honnêtement.

5. **Seulement après l'audit**, Claude produit les livrables :

- Les 3 fichiers livrables principaux : `manuel_<niveau>.md`,
  `fixtures_<niveau>.py`, `sources_<niveau>.md`
- Le livrable additionnel `ameliorations_dilf_<niveau>.md` consolidé à
  partir de `RESOLUTIONS_<conv>.md` (voir §8)
- Un fichier `BLOCAGES.md` (si mode fonce a généré des blocages
  différés) listant les fixtures à valider en interpellation
  utilisateur post-production
- Une mise à jour de `JOURNAL.md` : niveau X complété le <date>, N
  positions livrées, dont N_corpus / N_general / N_invented, points
  d'attention pour vérification moteur, nombre d'interpellations §4.11
  déclenchées et leurs résolutions, **plus le bloc « Audit final »
  décrit ci-dessus**.
- Une **mise à jour de `ETAT_DILF.md`** si des évolutions du framework
  ont été identifiées pendant la production (nouveaux patterns de
  coquilles, suggestions de modules manquants, etc.).

L'utilisateur dépose les livrables dans le repo `dilf` (ou le sous-projet
prévu) et reprend dans une nouvelle conversation pour le niveau suivant.

---

## 6. Sources prévues par niveau

| Niveau | PDFs prioritaires du corpus |
|--------|----------------------------|
| Débutant | `jpdubois_apprentissage_sens_du_jeu_V1` + `dubois_apprent_combin` |
| Intermédiaire | `jpdubois_perfectionnement_sens_du_jeu_tome_1` + `jpdubois_perfectionnement_combinaisons_V4` |
| Avancé | `sijbrandscourse` + `springercourse` (un à la fois si trop gros) |
| Expert | `maitrise-du-jeu-de-dames-dubois` + `jpdubois_expert_combinaisons_V2` + un workbook de maître |

Sources complémentaires possibles à chaque niveau : finales (`jpdubois_apprentissage_fins_de_parties_V1`),
ouvertures (`le_systeme_keller`, `le_systeme_roozenburg`), TaoW pour les motifs tactiques avancés.

> ⚠️ Cette section est conservée pour mémoire, mais la prise en charge réelle
> passe par §5 étape 0 : Claude lance le pipeline dilf sur les PDFs ci-dessus
> et travaille à partir des fixtures extraites. Aucun PDF ne doit être uploadé
> dans la conversation — ils sont déjà dans `docs/corpus/` du repo dilf.

---

## 7. Limites assumées de Claude

Document explicite des **choses que Claude ne fait pas bien** sur ce projet,
pour éviter les illusions :

- **Claude ne voit pas le damier graphiquement.** Il transcrit ce qui est dans
  le texte des PDFs, mais ne joue pas mentalement la partie case par case avec
  la même fiabilité qu'un moteur. **Conséquence : la transcription manuelle
  d'un diagramme est interdite (§4.10) — le pipeline `extract_diagrams.py`
  s'en charge.**
- **Claude ne valide pas la légalité FMJD d'une position.** La règle de prise
  maximale, en particulier, demande un calcul exhaustif que Claude ne fait
  pas avec garantie. **Conséquence : le moteur Scan en aval est non
  négociable (§4.6).**
- **Claude peut inventer une variante plausible** dans une solution longue,
  surtout au-delà de 4-5 demi-coups. **Conséquence : la solution publiée par
  Dubois est stockée verbatim depuis le PDF dans `published_notation` ;
  Claude ne la corrige pas, même si elle semble incohérente avec la position
  (§4.10).**
- **Claude peut se tromper sur la sémantique d'une notation Dubois** (par
  exemple, identifier mal une prise par rafle vs prise simple). **Conséquence :
  le champ `final_move` qui reconstruit le `Move` exécutable est optionnel ;
  si Claude doute, il le laisse à `None` et documente dans `claude_notes`.**
- **Claude peut boucler indéfiniment** sur une incohérence qu'il ne sait pas
  résoudre. **Conséquence : la règle d'interpellation §4.11 borne ce
  bouclage à deux tentatives, après quoi Claude s'arrête et demande à
  l'utilisateur.**

**Conséquence opérationnelle** : le rôle de Claude est de produire du
*contenu pédagogique structuré autour de positions extraites de façon
déterministe*, pas de la *vérité moteur*. Le pipeline dilf, le moteur
Scan, et l'expert humain via §4.11 sont la chaîne de vérification.

---

## 8. Livrables additionnels (résolutions et améliorations dilf)

En plus des 3 fichiers de production par manuel (`manuel_<niveau>.md`,
`fixtures_<niveau>.py`, `sources_<niveau>.md`), chaque conversation
produit deux fichiers complémentaires qui alimentent la boucle
d'amélioration du framework :

### 8.1. `RESOLUTIONS_<conv>.md` (tenu en cours de conversation)

Fichier scratch tenu par Claude **pendant** la conversation, mis à jour à
chaque résolution. Pas un livrable formel, mais la matière première du
livrable §8.2. Format :

```
## RESOLUTIONS — conversation <niveau>, <date>

### R001 — Incohérence position / solution Dubois D1 p.6
- **Livre** : dubois_apprent_combin
- **Position** : crops/page_006_d01.png — W{26,31,32,43} B{9,17,19,38}
- **Solution publiée** : "26-21 (17x28) 43x3"
- **Blocage** : (17x28) exigerait un blanc en 22 que la position n'a pas
- **Tentatives** :
  1. Re-extraction via pipeline → confirme W/B identique
  2. Hypothèse rafle multiple → géométriquement impossible
- **Résolution utilisateur** : <ce que tu m'as dit>
- **Règle d'inférence** : <comment je traite les cas similaires>
- **Implication dilf** : <bug ou suggestion à reporter dans le livrable §8.2>

### R002 — ...
```

Chaque résolution est consignée même si elle ne déclenche pas
d'interpellation (par exemple : choix éditorial sur un titre de chapitre).
Ce qui distingue les entrées issues d'une interpellation est explicite via
le champ « Résolution utilisateur » (rempli) vs « Résolution Claude »
(quand Claude tranche seul).

### 8.2. `ameliorations_dilf_<niveau>.md` (livré en fin de cycle)

Document final consolidé à partir de `RESOLUTIONS_<conv>.md`, classé par
catégorie d'amélioration de dilf, destiné à alimenter le backlog du
framework. Sections types :

- **Pipeline d'extraction** : crops qui échouent, thresholds à ajuster
  par livre, détection de captions manquante, etc.
- **Schéma `pedagogy/game.py`** : champs manquants pour la pédagogie,
  validateurs souhaitables, etc.
- **Glossaire de notation Dubois** : conventions de notation rencontrées
  qui ne correspondent pas au standard FMJD, mappings à documenter.
- **Détecteurs de motifs** : nouveaux motifs tactiques observés
  pendant la production qui mériteraient un détecteur.
- **Validation moteur** : positions sur lesquelles la sortie pipeline
  semblait correcte mais Scan a tranché autrement (à compléter après
  passage moteur).

Pour chaque suggestion : contexte (positions concernées, IDs des
résolutions correspondantes), proposition d'implémentation si Claude en
voit une, priorité estimée (haute/moyenne/basse).

Le but de ce livrable n'est pas que Claude implémente lui-même les
changements dans dilf, mais que l'utilisateur dispose d'une liste
prête-à-trier qui transforme l'apprentissage de la conversation en
amélioration durable du framework.

---

## 9. Glossaire

- **FMJD** : Fédération Mondiale du Jeu de Dames, qui édicte les règles
  officielles du jeu international 10×10.
- **FEN dames** : notation textuelle d'une position, dérivée du FEN d'échecs.
- **Fixture** : objet Python décrivant une position pédagogique, consommable
  par le framework de tests/exercices.
- **Rafle** : prise multiple en chaîne.
- **Coup royal / turc / de talon** : motifs tactiques canoniques du jeu de
  dames, documentés dans toute la littérature.
- **Scan** : moteur de jeu de dames intégré à Draught Master, utilisé pour
  la vérification a posteriori des fixtures.
- **dilf** (Draught Intelligence Learning Framework) : repo public
  `https://github.com/jfrancoiscollin/dilf` qui fournit l'outillage Python
  de référence pour ce projet — schéma `GameState`, pipeline d'extraction
  de diagrammes, corpus PDF complet.
- **`extract_diagrams.py`** : pipeline pixel-déterministe de dilf qui
  transforme un PDF Dubois en fixtures Python (positions extraites par
  thresholding de pixels, $0, déterministe, sans hallucination).
- **`DuboisDiagram`** : dataclass produit par le pipeline d'extraction —
  porte une position brute (white_men, black_men, turn) plus métadonnées
  (page, region_index, caption_text, crop_id).
- **`BeginnerPosition`** (et niveaux suivants) : wrapper pédagogique
  Claude construit par-dessus un `DuboisDiagram` ou un `GameState` ad hoc,
  ajoutant thème, concept, solution publiée, explication.
