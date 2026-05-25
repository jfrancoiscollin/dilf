# CADRAGE STRATÉGIE — Explication des systèmes et concepts profonds

> **Annexe au `CADRAGE_MANUELS.md`.** Ce document étend le protocole de
> production aux contenus *stratégiques* : systèmes d'ouverture (Roozenburg,
> Keller), fondamentaux du jeu classique, plans de milieu de partie, et plus
> généralement tout savoir qui ne se réduit pas à une combinaison tactique
> vérifiable par une rafle.
>
> À lire **après** `CADRAGE_MANUELS.md`, `JOURNAL.md` et `ETAT_DILF.md`,
> dès lors qu'une conversation produit ou sert du contenu stratégique.
>
> **Principe directeur** : tout ce que le cadrage tactique fonde sur un oracle
> *calculé* (Scan), le présent cadrage le refonde sur un oracle *cité*
> (la prose des maîtres du corpus). La discipline anti-hallucination est
> identique ; seule la source de vérité change.

-----

## 0. Pourquoi un cadrage séparé

Le `CADRAGE_MANUELS.md` repose sur une chaîne de vérification déterministe :
position extraite au pixel → rafle reconstruite → validation FMJD → moteur Scan.
Cette chaîne fonctionne parce qu'une tactique **a une réponse vraie calculable**.

Une stratégie n'en a pas. « Le système classique cherche le contrôle du grand
chemin » n'est ni vrai ni faux au sens d'une rafle maximale : c'est un *énoncé
de la littérature*, formulé par des maîtres, parfois contesté, jamais produit
par un moteur. Scan joue le classique remarquablement, mais sa compréhension
est encodée dans ses poids — **illisible et non interrogeable en langage**.

Conséquence directe : au niveau stratégique, **l'oracle déterministe disparaît**,
et c'est précisément le terrain où le LLM hallucine le plus dangereusement —
en produisant une prose fluide qui *sonne* juste mais peut attribuer un plan au
mauvais système, qualifier de « forte » une structure contestée, ou inventer
une filiation historique. Ce cadrage existe pour fermer cette voie d'erreur.

-----

## 1. Périmètre : deux usages, une architecture

Ce cadrage couvre **deux livrables distincts** qui partagent la même
architecture de vérité mais pas le même curseur de tolérance.

|Usage                           |Cible                           |Vérification                                       |Tolérance hallucination       |
|--------------------------------|--------------------------------|---------------------------------------------------|------------------------------|
|**A — Chapitre de manuel**      |Lecteur humain, contenu figé    |Humaine lourde + Scan sur positions-types, une fois|Nulle (relu avant publication)|
|**B — Explication à la demande**|Utilisateur de l'app, temps réel|Automatique, sans relecture humaine                |RAG cité **non négociable**   |

L'usage A peut se permettre une synthèse éditoriale riche, parce qu'un humain
la relit avant qu'elle entre au manuel. L'usage B ne le peut pas : tout ce qui
sort doit être traçable à un passage de corpus **au moment de la génération**,
sans filet humain. La règle de conception est donc : **on écrit le pipeline
pour l'usage B (le plus strict), et l'usage A en hérite gratuitement.**

-----

## 2. Le changement de nature de la vérité

|                   |Cadrage tactique (existant)     |Cadrage stratégique (ce document)                                 |
|-------------------|--------------------------------|------------------------------------------------------------------|
|Source de vérité   |Scan (**calculée**)             |Prose des maîtres (**citée**)                                     |
|Oracle             |`scan_engine.evaluate_pos()`    |Corpus indexé + RAG                                               |
|Rôle du LLM        |Verbaliser un score             |Synthétiser des passages cités                                    |
|Garde-fou principal|§4.10 transcription interdite   |§4 ci-dessous : énonciation de mémoire interdite                  |
|Unité de référence |`crop_id` (diagramme)           |`passage_id` (extrait de prose)                                   |
|Validation finale  |`validate_final_moves.py` + Scan|Traçabilité de chaque assertion + Scan sur positions illustratives|

**Le LLM n'énonce jamais un principe stratégique de mémoire.** Il le *rapporte*
depuis un passage de corpus identifié. C'est l'exact analogue de la règle §4.10
du cadrage tactique (« transcription manuelle interdite, le pipeline est
obligatoire »), transposé à la prose : *énonciation stratégique de mémoire
interdite, le passage de corpus est obligatoire.*

-----

## 3. Architecture du double ancrage

La force du projet — ce qui le distingue d'un RAG générique sur des PDF — est
de croiser **deux oracles complémentaires** : la prose dit le *pourquoi*, le
moteur dit le *combien*.

```
Question stratégique
   ("fondamentaux du classique", "logique du Roozenburg")
        │
        ▼
┌──────────────────────────────────────────────────────┐
│  ORACLE 1 — Prose citée (le POURQUOI)                  │
│  Recherche dans corpus indexé                          │
│  (Sijbrands, Springer, traités Keller/Roozenburg)      │
│  → passages pertinents + source exacte (PDF, page)     │
└───────────────────────┬──────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
┌─────────────────────┐   ┌──────────────────────────────┐
│ ORACLE 2 — Scan      │   │  LLM = SYNTHÉTISEUR            │
│ (le COMBIEN)         │   │  - relie les passages cités   │
│ Positions-types de   │   │  - n'ajoute aucun fait        │
│ la structure jouées  │   │    non sourcé                 │
│ → eval confirme ou   │   │  - marque toute synthèse      │
│   nuance l'énoncé    │   │    non traçable comme telle   │
└─────────────────────┘   └──────────────────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        ▼
        Explication = énoncé cité du maître
                     + confirmation chiffrée Scan
                     + position illustrative validée
```

Une explication stratégique bien formée contient donc trois maillons, **aucun
inventé** : (1) un énoncé attribué à une source du corpus, (2) une vérification
chiffrée par Scan sur une position-type, (3) une position illustrative passée
par la chaîne de validation FMJD du cadrage tactique.

-----

## 4. PROTOCOLE ANTI-HALLUCINATION — extension stratégique

> Cette section reprend l'esprit de la §4 du cadrage tactique. Chaque règle
> ferme une voie d'erreur propre au registre stratégique.

### 4.S1. Règle de l'énoncé sourcé

**Toute affirmation stratégique publiée porte une source.** Une affirmation
est de l'un de ces types, et le type est explicite :

- **`CITED`** : reformulation fidèle d'un passage identifié du corpus, avec
  `passage_id` (PDF + page). C'est le cas par défaut et de loin majoritaire.
- **`SYNTHESIS`** : articulation par Claude de **plusieurs** énoncés `CITED`
  (ex. relier la logique du Keller à celle du Roozenburg). Doit lister les
  `passage_id` qu'elle relie. **Plafonnée** — voir §4.S5.
- **`ENGINE`** : affirmation quantitative produite par Scan sur une position
  donnée (« cette structure évalue à +0.8 pour les Blancs »). Porte la FEN et
  les paramètres de recherche.

Il n'existe **pas** de catégorie « connaissance générale de Claude » pour le
stratégique. La différence avec le cadrage tactique (qui autorise
`GENERAL_KNOWLEDGE` pour les motifs canoniques) est délibérée : un motif
tactique canonique est vérifiable par rafle, un principe stratégique « de
mémoire » ne l'est pas. **L'énoncé stratégique non sourcé est un échec critique
du protocole.**

### 4.S2. Règle de citation, pas de paraphrase libre

Claude **reformule** le passage source dans ses mots (pas de copie verbatim
longue de la prose d'un auteur), mais **ne déforme pas le contenu** : il ne
renforce pas un énoncé prudent (« souvent favorable » ne devient pas
« toujours gagnant »), n'attribue pas à l'auteur une conclusion qu'il ne tire
pas, ne comble pas un silence de la source par une inférence présentée comme
citée. Si la source est prudente, la reformulation reste prudente.

### 4.S3. Règle de l'attribution exacte des systèmes

Confusion la plus fréquente et la plus coûteuse : attribuer au système X un
plan qui relève du système Y. Avant toute affirmation du type « dans le
Roozenburg, on cherche à… », Claude vérifie que le `passage_id` invoqué traite
**bien de ce système nommément**. Une affirmation sur le Keller ne peut pas
s'appuyer sur un passage qui parle du classique « en général ». En cas de
doute sur le rattachement, l'affirmation passe en `SYNTHESIS` et le doute est
consigné.

### 4.S4. Règle de la vérification croisée moteur

Quand un passage affirme qu'une structure est *favorable / forte / tenable*,
Claude **fait jouer Scan** sur une ou plusieurs positions-types représentatives
de cette structure et rapporte l'évaluation. Trois issues :

- **Concordance** : Scan confirme → l'affirmation devient `CITED` + `ENGINE`,
  `confidence=high`.
- **Nuance** : Scan tempère (ex. structure jugée « forte » par l'auteur mais
  évaluée proche de l'égalité par Scan) → l'explication **rapporte les deux**,
  sans trancher (« la littérature classique valorise cette structure ; le
  moteur l'évalue plus proche de l'équilibre, ce qui reflète l'écart entre
  jugement positionnel humain et calcul »).
- **Contradiction franche** : Scan dément nettement → `confidence=low`,
  interpellation §4.11 du cadrage tactique. Une contradiction franche signale
  soit une mauvaise position-type, soit un énoncé daté, soit une erreur de
  rattachement.

### 4.S5. Règle du plafond de synthèse

La **synthèse** est le maillon faible (cf §7 « limites » du cadrage tactique).
Rapporter un passage est sûr ; relier plusieurs systèmes dans une généalogie
cohérente exige une articulation que le LLM produit, donc qui peut déraper.

- Toute affirmation `SYNTHESIS` doit rester **décomposable** en énoncés `CITED`
  sous-jacents listés.
- Une synthèse qui ne se décompose pas en sources est **interdite** : elle est
  soit retirée, soit explicitement marquée comme *interprétation de Claude*
  (`confidence=low`, équivalent `claude_notes`) et **jamais** en usage B
  (temps réel) sans ce marquage visible pour l'utilisateur.
- En usage A (manuel), une synthèse riche est permise **si** elle est signalée
  pour relecture humaine.

### 4.S6. Règle du marqueur de validation

Comme pour les fixtures tactiques, tout contenu stratégique est publié
`verified=False`. La transformation `→ verified=True` exige deux passages :
(1) chaque assertion `CITED`/`SYNTHESIS` a un `passage_id` résolvable dans le
corpus ; (2) chaque assertion `ENGINE` et chaque position illustrative a passé
Scan. Sans ces deux passages, le contenu ne va pas en production.

### 4.S7. Règle de la datation des sources

Le jeu de dames a une historiographie : un jugement de Roozenburg des années
1950 peut être nuancé par l'analyse moteur moderne. Quand un énoncé `CITED`
est ancien et qu'une vérification §4.S4 le nuance, l'explication **situe**
l'énoncé (« selon l'école classique des années… ») plutôt que de le présenter
comme vérité intemporelle. Ne jamais effacer la source au profit du moteur ni
l'inverse : les deux coexistent, datés.

-----

## 5. Le pipeline manquant : indexation de la prose

`ETAT_DILF.md` décrit un pipeline qui extrait des **diagrammes**
(`extract_diagrams.py`). Le présent cadrage exige son **pendant pour la prose**,
qui n'existe pas encore (ni dans les détecteurs de motifs, ni dans
`notation/dubois.py`).

### 5.1. Spécification fonctionnelle `index_prose.py` (proposé)

```
Entrée  : PDF du corpus stratégique (Sijbrands, Springer, Keller, Roozenburg…)
Étapes  :
  1. extract   — pdftotext -layout par page (réutilise l'outillage existant)
  2. chunk     — découpage en passages cohérents (paragraphe / sous-section),
                 conservation page + offset
  3. tag       — métadonnées : système(s) traité(s), phase (ouverture/milieu/
                 finale), nature (principe / plan / avertissement)
  4. embed     — embeddings des passages pour recherche sémantique
  5. emit      — pedagogy/tests/fixtures/prose_passages.py : liste ALL_PASSAGES
                 de ProsePassage (texte + source PDF + page + tags + embedding)
Sortie  : index interrogeable, chaque passage adressable par passage_id stable
```

Ce pipeline est à **proposer dans le backlog dilf** (nouvelle ligne dans le
tableau §6 d'`ETAT_DILF.md`), priorité **haute** car bloquant pour tout
contenu stratégique en usage B.

### 5.2. Distinction crops vs passages

|        |`extract_diagrams.py` (existe)|`index_prose.py` (à faire)                       |
|--------|------------------------------|-------------------------------------------------|
|Extrait |Positions (pixels)            |Texte (prose)                                    |
|Garantie|Pixel-déterministe, $0        |Découpage déterministe ; embeddings stochastiques|
|Unité   |`crop_id`                     |`passage_id`                                     |
|Vérité  |La position **est** correcte  |Le passage **est** ce qu'a écrit l'auteur        |

Note importante : l'indexation prose est déterministe **sur le texte extrait**
(le passage est verbatim ce qu'a écrit l'auteur), mais la *recherche*
sémantique par embeddings est approximative. La garantie anti-hallucination ne
porte donc pas sur « le bon passage est toujours retrouvé » mais sur « tout ce
qui est affirmé provient d'un passage réel ». Un passage non pertinent retrouvé
dégrade la qualité, pas la véracité.

-----

## 6. Format des fixtures stratégiques

Par cohérence avec le wrapper `BeginnerPosition` (cadrage §3), le contenu
stratégique se matérialise dans un wrapper dédié, référençant prose **et**
positions illustratives.

```python
from dataclasses import dataclass, field
from enum import Enum
from pedagogy.game import GameState, Move


class AssertionType(Enum):
    CITED = "cited"           # reformulation d'un passage du corpus
    SYNTHESIS = "synthesis"   # articulation de plusieurs CITED par Claude
    ENGINE = "engine"         # affirmation quantitative produite par Scan


@dataclass(frozen=True)
class Assertion:
    text: str                        # l'énoncé reformulé
    kind: AssertionType
    passage_ids: tuple[str, ...] = ()   # sources CITED/SYNTHESIS
    engine_fen: str = ""                # position évaluée si ENGINE
    engine_eval: float | None = None    # score Scan si ENGINE
    confidence: str = "medium"          # high | medium | low
    claude_notes: str = ""


@dataclass(frozen=True)
class IllustrativePosition:
    state: GameState
    caption: str                     # ce qu'illustre la position
    scan_eval: float | None = None   # rempli après passage Scan
    crop_id: str = ""                # si extraite du corpus
    verified: bool = False


@dataclass(frozen=True)
class StrategicConcept:
    # Identité pédagogique
    id: str                          # ex: "SYS_ROOZENBURG_001"
    system: str                      # "classique" | "roozenburg" | "keller" | ...
    title: str                       # ex: "Le verrouillage d'aile dans le Roozenburg"
    phase: str                       # "ouverture" | "milieu" | "finale"

    # Corps de l'explication : une liste d'assertions tracées
    assertions: tuple[Assertion, ...] = ()
    illustrations: tuple[IllustrativePosition, ...] = ()

    # Méta
    verified: bool = False           # True quand §4.S6 satisfait
    claude_notes: str = ""
```

**Invariant de production** : un `StrategicConcept` est `verified=True`
seulement si **toute** assertion `CITED`/`SYNTHESIS` a au moins un
`passage_id` résolvable, **toute** assertion `ENGINE` a une `engine_eval`, et
**toute** illustration a un `scan_eval`. C'est l'analogue de
`validate_final_moves.py` pour le stratégique — à écrire :
`validate_strategic.py`.

-----

## 7. Méthode de travail — usage A (production manuel)

Au début d'une conversation « chapitre stratégique » :

1. Lire les trois documents de cadrage habituels + **ce document**.
2. Cloner dilf, vérifier la disponibilité de `index_prose.py` (sinon le
   signaler comme bloquant et basculer en mode dégradé : extraction
   `pdftotext` manuelle des passages, avec `passage_id` reconstruit à la main —
   acceptable en usage A relu, **interdit** en usage B).
3. **Étape 0 prose** : lancer `index_prose.py` sur les PDF du système visé
   (voir §10).
4. Pour chaque concept du chapitre :
   - rechercher les passages pertinents dans l'index (oracle 1) ;
   - rédiger les `Assertion` `CITED` à partir de ces passages ;
   - construire/extraire 1-3 positions-types ; les passer à Scan (oracle 2) ;
   - n'ajouter de `SYNTHESIS` que décomposable (§4.S5) ;
   - marquer `verified=False`.
5. Validation : `validate_strategic.py` + relecture humaine (curseur usage A).
6. Livrables (§9) + mise à jour `JOURNAL.md` et `ETAT_DILF.md`.

Le mode « fonce » (§4.12 cadrage) reste applicable : production de plusieurs
concepts consécutifs, blocages différés dans `BLOCAGES.md`, interpellations
§4.11 en batch.

-----

## 8. Méthode de travail — usage B (explication temps réel)

Pour l'explication à la demande dans l'app, le pipeline est **figé et
automatique** (pas de Claude « libre ») :

```
Requête utilisateur
   1. Classement : tactique → chaîne Scan existante
                   stratégique → chaîne ci-dessous
   2. Retrieval : top-k passages du corpus indexé (oracle 1)
   3. Si position fournie : Scan évalue (oracle 2)
   4. Génération CONTRAINTE : le prompt système impose
      - n'affirmer QUE ce qui figure dans les passages fournis
      - citer le système nommément seulement si un passage le nomme (§4.S3)
      - signaler explicitement toute synthèse non décomposable (§4.S5)
      - si les passages ne couvrent pas la question : le dire,
        ne pas combler de mémoire
   5. Garde-fou sortie : toute phrase sans ancrage passage/engine
      est soit retirée, soit marquée "interprétation"
```

Règle d'or de l'usage B : **« pas de passage pertinent = pas de réponse
affirmative »**. Mieux vaut « la base ne couvre pas ce point » qu'une prose
inventée. C'est l'analogue temps réel de la règle de l'aveu (§4.7 cadrage).

-----

## 9. Livrables

Pour chaque chapitre/lot stratégique produit :

- **`manuel_<niveau>_strategie.md`** — prose lisible, chaque affirmation
  traçable, positions illustratives référencées par ID.
- **`fixtures_strategie_<systeme>.py`** — `StrategicConcept` importables.
- **`sources_strategie_<systeme>.md`** — table : assertion → `passage_id` →
  PDF+page, statut de vérification, résultat Scan des positions-types.
- **`ameliorations_dilf_strategie.md`** — backlog : qualité de l'indexation
  prose, tags système mal détectés, passages introuvables, etc. (consolidé
  depuis `RESOLUTIONS_<conv>.md`).

Conventions de noms cohérentes avec `ETAT_DILF.md §8` :
IDs `SYS_<SYSTEME>_<nnn>` (ex. `SYS_KELLER_003`, `SYS_CLASSIQUE_012`).

-----

## 10. Sources prévues par système

|Système / thème          |PDF prioritaires du corpus                 |
|-------------------------|-------------------------------------------|
|Fondamentaux du classique|`sijbrandscourse`, `springercourse`        |
|Système Roozenburg       |`le_systeme_roozenburg`                    |
|Système Keller           |`le_systeme_keller`                        |
|Plans de milieu de partie|`sijbrandscourse` + maîtrise Dubois        |
|Finales stratégiques     |`jpdubois_apprentissage_fins_de_parties_V1`|


> Comme au cadrage tactique : aucun PDF n'est uploadé en conversation, tout est
> dans `docs/corpus/` de dilf. La prise en charge passe par §7 étape 0
> (`index_prose.py` sur les PDF ci-dessus).

-----

## 11. Limites assumées — registre stratégique

Complément au §7 du cadrage tactique, spécifique au stratégique :

- **Claude ne « comprend » pas un système** au sens d'un maître. Il restitue et
  articule ce que des maîtres ont écrit. La profondeur d'explication est celle
  du corpus, pas celle de Claude.
- **La synthèse est le point de rupture.** Rapporter est sûr ; relier est
  risqué (§4.S5). Tout ce qui dépasse la somme des passages cités est suspect
  par défaut.
- **Scan ne valide pas une stratégie**, seulement des positions-types. Une
  concordance Scan ne « prouve » pas le principe général ; elle l'illustre sur
  un échantillon. Ne pas surinterpréter une eval ponctuelle en loi générale.
- **L'historiographie est un piège.** Filiations entre écoles, antériorité d'un
  système sur un autre, paternité d'une idée : terrain à hallucination élevé,
  à traiter en `CITED` strict ou à taire (§4.S7).

**Conséquence opérationnelle** : le rôle de Claude au niveau stratégique est
d'être un *synthétiseur cité et vérifié*, pas une autorité du jeu de dames.
La chaîne corpus → RAG → Scan → relecture (usage A) ou garde-fou automatique
(usage B) reste la seule garante de la véracité.

-----

## 12. Backlog dilf induit par ce cadrage

À reporter dans `ETAT_DILF.md §6` :

|# |Suggestion                                            |Priorité |Bloquant pour              |
|--|------------------------------------------------------|---------|---------------------------|
|S1|Pipeline `index_prose.py` (chunk + tag + embed + emit)|**Haute**|Usage B entier             |
|S2|Wrapper `StrategicConcept` dans `pedagogy/`           |Haute    |Production fixtures        |
|S3|`validate_strategic.py` (traçabilité + passage Scan)  |Haute    |`verified=True`            |
|S4|Détection automatique du `system` dans les passages   |Moyenne  |Qualité retrieval (§4.S3)  |
|S5|Banque de positions-types par système (pour §4.S4)    |Moyenne  |Vérification croisée moteur|
|S6|Prompt système contraint usage B (garde-fou §8)       |Haute    |Mise en prod app           |
