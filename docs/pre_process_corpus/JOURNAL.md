# JOURNAL — Avancement de la production des 4 manuels

> Mis à jour à la fin de chaque conversation par Claude.
> Compagnon de `CADRAGE_MANUELS.md`.

---

## État global

| Manuel | Statut | Date | Positions livrées | Vérifiées moteur |
|--------|--------|------|-------------------|------------------|
| Débutant | **COMPLET** — chap 1-16 livrés | mai 2026 | 166 fixtures (12 + 10 + 11 + 10 + 11 + 12 + 12 + 12 + 12 + 12 + 10 + 10 + 10 + 10 + 10 + 2 intro) | 0 |
| Intermédiaire | À démarrer | — | 0 | 0 |
| Avancé | À démarrer | — | 0 | 0 |
| Expert | À démarrer | — | 0 | 0 |

---

## Historique des conversations

### Conversation initiale — Cadrage (mai 2026)

- Définition du projet : 4 manuels × ~100-200 positions, livrables = manuel prose + fixtures Python + table de traçabilité.
- Schéma `TacticalPosition` arrêté (depuis remplacé — voir conv. suivante).
- Protocole anti-hallucination rédigé (section 4 du cadrage).
- PDFs prioritaires identifiés par niveau (section 6 du cadrage).
- Aucune position produite à ce stade.

### Démarrage niveau Débutant — Découverte de dilf (mai 2026)

Conversation où on devait produire le manuel Débutant à partir du PDF
Dubois Apprentissage Combinaisons. Deux constats majeurs :

1. **Transcription manuelle d'un diagramme = piège.** Claude a passé deux
   heures à tenter de lire D1 page 6 case par case (4 essais, calibrations
   pixel manuelles, cross-check via solution Dubois). Lecture correcte
   finalement (`W{26,31,32,43} / B{9,17,19,38}`) mais avec une consommation
   de tokens et de patience disproportionnée — et avec un faux-soupçon
   d'erreur Dubois en cours de route.

2. **Le repo `dilf` existe déjà et résout exactement ce problème.**
   `scripts/extract_diagrams.py` extrait 569 positions du livre complet en
   7 secondes, déterministe, sans hallucination, $0. Le schéma
   `pedagogy/game.py` (`GameState`, `Move`, `parse_fen`) est la référence
   officielle. Tout le corpus est déjà dans `docs/corpus/`.

**Décisions actées (cadrage mis à jour) :**

- Le cadrage incorpore désormais une **règle §4.10** : transcription
  manuelle interdite, le pipeline `extract_diagrams.py` est l'outil
  obligatoire pour toute position `source=CORPUS`.
- Une **règle §4.11** (human-in-the-loop) borne le bouclage de Claude
  sur les incohérences : après 2 tentatives auto, Claude s'arrête,
  envoie l'image rasterisée + le contexte source à l'utilisateur, et
  attend une résolution.
- Un fichier de scratch `RESOLUTIONS_<conv>.md` est tenu en cours de
  conversation pour mémoriser chaque résolution et éviter de re-déranger
  l'utilisateur sur des cas similaires.
- Un livrable additionnel `ameliorations_dilf_<niveau>.md` consolide en
  fin de cycle les apprentissages, classés par catégorie, pour
  alimenter le backlog d'évolution du framework dilf.
- Le schéma `TacticalPosition` proposé initialement (section 3) est
  **remplacé** par le schéma dilf `GameState` + un wrapper pédagogique
  `BeginnerPosition` qui référence la position brute par `crop_id`.
- L'étape 0 de chaque conversation est désormais : cloner dilf, lancer
  le pipeline sur les PDFs pertinents du niveau visé.

**Validation D1 ↔ pipeline :** le pipeline confirme exactement la lecture
manuelle de D1 (4W+4B, sans pion en 22). La solution Dubois imprimée
`26-21 (17x28) 43x3` reste non-vérifiable par Claude seul (le `(17x28)`
exigerait un blanc en 22 qui n'existe pas). Première interpellation
§4.11 candidate pour la conversation suivante.

**Production effective dans cette conversation : 0 position livrée.** La
conversation aura servi à corriger structurellement le cadrage avant que
les conversations suivantes ne refassent la même erreur de méthode.

---

## Décisions actées

- Le schéma de référence pour les positions est `pedagogy.game.GameState`
  du repo dilf, **pas** le `TacticalPosition` du cadrage initial.
- Les thèmes restent stockés en `str` libre pour l'instant (Enum strict
  pas encore décidé — voir si le framework `pedagogy/` les exige).
- Le pipeline `extract_diagrams.py` est l'outil obligatoire pour
  `source=CORPUS` (cadrage §4.10).
- Les `confidence=high` sont autorisés pour les positions extraites par
  le pipeline sans warning (l'extraction est déterministe et a été
  validée sur D1 en cross-check manuel).

---

## Points d'attention pour la vérification moteur

(À remplir au fil de la production. Format : ID position — doute à vérifier.)

—

---

### Chapitre 4 du manuel Débutant — Le collage (mai 2026)

Production effective du chapitre 4 (11 fixtures). Source : Dubois
Apprentissage Combinaisons, chapitres 6 et 7, pages 20-25.

**Bilan résolutions** :
- 3 nouvelles coquilles PDF Dubois détectées et corrigées via §4.11
  interpellation : R004 (Ch6 D1 : `(15x21)` → `(15x31)`), R005 (Ch6 D5 :
  diagramme faux, fixture omise), R006 (Ch7 D8 : `31x3` → `32x3`).
- R007 : 2 fixtures avec envoi à dame (Ch6 D10, Ch7 D5) stockées avec
  `final_move=None` car le module pédagogique `pedagogy.notation.dubois`
  est pion-only. Suggestion §5bis pour ameliorations_dilf.
- Cumul résolutions de la conversation : 8 (R000 à R007).
- Cumul interpellations §4.11 déclenchées : 5 (R001 + R002 + R004 + R005 + R006).
  Soit ~6% des fixtures Dubois produites. Taux conforme aux attentes pour
  un livre Dubois.

**Détection de coquilles PDF** : 3 coquilles détectées sur 21 fixtures
Dubois produites (≈14%). Confirme la priorité du §3 d'`ameliorations_dilf`
(détecteur automatique de coquilles).

**État cumulé du manuel Débutant** :
- 23 fixtures livrées (2 chap 1 + 10 chap 3 + 11 chap 4)
- Tous round-trip FEN OK
- 18/23 ont un `final_move` reconstruit
- 21/23 sont `source=CORPUS`, 2/23 sont `GENERAL_KNOWLEDGE`
- 0/23 vérifiées moteur Scan (passage attendu en fin de cycle)

---

### Chapitre 5 du manuel Débutant — L'envoi à dame (mai 2026)

Production effective du chapitre 5 (10 fixtures). Source : Dubois
Apprentissage Combinaisons, chapitre 4, pages 14-16.

**Composition** :
- 2 exemples narratifs page 14 (positions initiales des 2 combinaisons
  développées par Dubois en introduction).
- 8 exercices page 15 (D1-D3, D5, D7-D10 — D4 et D6 omis car gambit
  et collage sont déjà couverts au chap 4 du manuel).

**Bilan résolutions** :
- **0 interpellation §4.11 déclenchée** sur ce chapitre — bonne nouvelle,
  les coquilles PDF ne sont pas systématiques.
- **0 nouvelle résolution** : les apprentissages des chapitres précédents
  (notation zigzagante, helpers de reconstruction) ont suffi.
- **5 fixtures avec final_move=None** (envois à dame, limitation R007) :
  BEG_CH05_001, 002, 008, 009, 010. Confirme la pertinence d'étendre le
  module dilf aux rafles de dame (suggestion §5bis à ajouter au backlog).

**État cumulé du manuel Débutant** :
- **33 fixtures livrées** (2 chap 1 + 10 chap 3 + 11 chap 4 + 10 chap 5)
- Round-trip FEN : 33/33 ✓
- Avec final_move : 23/33 (70%)
- Sources : 31 CORPUS, 2 GENERAL_KNOWLEDGE
- Interpellations §4.11 cumulées : 5 (sur 31 fixtures Dubois ≈ 16%)
- Coquilles PDF détectées : 3
- Limitations kings documentées : 7 fixtures (2 chap 4 + 5 chap 5)

---

### Chapitre 2 du manuel Débutant — Les règles du jeu (mai 2026)

Production effective du chapitre 2 (12 fixtures). Source : positions
canoniques de pédagogie élémentaire (GENERAL_KNOWLEDGE) + 2 positions
INVENTED par Claude.

**Composition** :
- 10 fixtures GENERAL_KNOWLEDGE : déplacement, capture simple, capture
  arrière, rafle, prise obligatoire, promotion, déplacement dame, capture
  dame, règle des 50 coups.
- 2 fixtures INVENTED : prise maximale (asymétrie 1 vs 2 captures
  construite pour clarté pédagogique), non-soufflage.

**Bilan résolutions** :
- 0 interpellation §4.11 (pas de PDF à interroger).
- 0 nouvelle résolution.

**Particularité** : ce chapitre est **non-extrait du corpus Dubois**. Le
livre Apprentissage Combinaisons est tourné vers les combinaisons et
suppose les règles connues. Pour le manuel Débutant, les règles doivent
être enseignées en amont — fixtures construites par Claude à partir des
règles FMJD.

**Respect du seuil INVENTED §4.1** : 2/45 ≈ 4%, largement sous le seuil
de 15% du cadrage.

**État cumulé du manuel Débutant** :
- **45 fixtures livrées** (chap 1-2-3-4-5)
- Round-trip FEN : 45/45 ✓
- Sources : 31 CORPUS (69%), 12 GENERAL_KNOWLEDGE (27%), 2 INVENTED (4%)
- Avec final_move : 25/45 (56%)
- Interpellations §4.11 cumulées : 5
- Coquilles PDF détectées : 3
- Fixtures `final_move=None` (envois à dame OU pas de rafle finale) : 8

---

### Chapitre 6 du manuel Débutant — Méthode des points de contact (mai 2026)

Production effective du chapitre 6 (11 fixtures). Source : Dubois
Apprentissage Combinaisons, chapitre 5, pages 17-19.

**Composition** :
- 1 exemple narratif page 17 (positions initiale de l'introduction)
- 10 exercices page 18 (D1-D10 complets, dont 2 traits aux noirs D6 et D9)

**Bilan résolutions** :
- 0 interpellation §4.11 — deuxième chapitre consécutif sans interpellation.
- 0 nouvelle résolution.
- 11/11 reconstruits au premier coup (D4 a final_move=None car gambit
  se terminant sur coup simple — cas attendu, déjà documenté).

**Particularité pédagogique** : ce chapitre introduit une **méthode
alternative** à la recherche de combinaisons (rechercher les points de
contact plutôt que la rafle finale). Deux nouveaux thèmes apparaissent :
`points_de_contact` (5 fixtures) et `coup_philippe` (1 fixture, motif
nommé chez Dubois).

**Parties historiques** : 3 fixtures issues de parties datées
(Laporta-Mostovoy 1970, Bergsma-de Vries 1961, Leclercq-Weiss 1903) —
le chapitre acquiert une dimension culturelle/historique appréciable
pour le lecteur.

**État cumulé du manuel Débutant** :
- **56 fixtures livrées** (chap 1-6)
- Round-trip FEN : 56/56 ✓
- Avec final_move : 37/56 (66%)
- Sources : 42 CORPUS (75%), 12 GENERAL_KNOWLEDGE (21%), 2 INVENTED (4%)
- Interpellations §4.11 cumulées : 5 (toutes au chap 3 et 4)
- Coquilles PDF détectées : 3


---

### Session production batch chap 7-16 du manuel Débutant (mai 2026)

Production en mode "fonce" autorisé par l'utilisateur. Industrialisation
complète :
- Script `generate_chapter.py` créé pour générer les fixtures depuis des
  définitions Python (`chN_def.py`).
- Reconstruction `final_move` via le module `pedagogy.notation.dubois`
  (PR #31).
- Suivi des blocages dans `BLOCAGES.md` pour interpellation §4.11
  ultérieure en batch.

**Bilan production chap 7-16 (10 chapitres, 110 fixtures)** :
- Chap 7 (Temps de repos)        : 12 fixtures, 0 blocage
- Chap 8 (Création temps repos)  : 12 fixtures, 0 blocage
- Chap 9 (Coup Express)          : 12 fixtures, **1 blocage** (BEG_CH09_007 D5)
- Chap 10 (Coup Ricochet)        : 12 fixtures, **1 blocage** (BEG_CH10_008 D6)
- Chap 11 (Coup Rappel)          : 12 fixtures, 0 blocage
- Chap 12 (Coup Renversé)        : 10 fixtures, 0 blocage
- Chap 13 (Coup Napoléon)        : 10 fixtures, **1 blocage** (BEG_CH13_004 D4)
- Chap 14 (Coup de la Trappe)    : 10 fixtures, 0 blocage
- Chap 15 (Coup de Talon)        : 10 fixtures, 0 blocage
- Chap 16 (Coup Philippe)        : 10 fixtures, 0 blocage

**3 blocages cumulés** (sur 110 fixtures = 2.7%), tous documentés
dans `BLOCAGES.md` pour interpellation manuelle ultérieure :
- BEG_CH09_007 (Dubois ch13 D5) : position/solution incompatibles
- BEG_CH10_008 (Dubois ch14 D6) : mapping diagramme/solution erroné
- BEG_CH13_004 (Dubois ch17 D4) : solution entièrement décalée

**Résolutions nouvelles** : R008 — notation Dubois `(ad lib)` désigne
des captures forcées équivalentes (utilisé chap 7 D10 et chap 12 D8).

**État final manuel Débutant** :
- **166 fixtures** réparties sur 16 chapitres
- Round-trip FEN : 166/166 ✓
- Avec final_move : 132/166 (79%)
- Sources : 152 CORPUS (92%), 12 GENERAL (7%), 2 INVENTED (1%)
- 28 thèmes pédagogiques distincts
- Coquilles PDF détectées : 3 + 3 blocages à confirmer

Le manuel Débutant est ainsi complet en termes de fixtures, prêt
pour la phase suivante (rédaction prose `manuel_debutant.md` ou
validation moteur).

---

### Session post-production — Validation, prose, et améliorations dilf finalisées (mai 2026)

Mise au point finale du livrable Débutant. Trois activités :

**1. Améliorations dilf consolidées** (`ameliorations_dilf_debutant.md`).
Version finale du document §8.2, basée sur les 16 chapitres produits et
les 8 résolutions cumulées. Contient 7 sections de suggestions, dont 2
livrées (PR #31) et 5 à faire, avec ordre de priorité recommandé pour
démarrer le manuel Intermédiaire.

**2. Manuel prose** (`manuel_debutant.md`, 841 lignes).
Rédaction d'un manuel pédagogique lisible par un humain, organisé en
16 chapitres avec préface, conclusion et 4 annexes. Chaque chapitre
résume les concepts clés et référence les fixtures par leur ID
(`BEG_CHnn_mmm`). Permet à un lecteur d'exploiter les positions de
référence sans lire le code Python.

**3. Validation moteur structurelle** (`validate_final_moves.py`).
Script de validation qui re-joue chaque `published_notation` jusqu'au
`final_move` et vérifie :
- Légalité de chaque étape selon les règles FMJD (via le helper
  `enumerate_pawn_captures` de PR #31)
- Maximalité de la rafle finale (prise maximale FMJD)

**Bilan validation** :
- 132/132 fixtures avec final_move OK (100%)
- 34 fixtures NO_FM (envoi à dame, gambit, blocage)
- **1 fixture corrigée** : BEG_CH03_002 avait une position erronée
  (`W{23,28,32}` au lieu de `W{28,32,37}`) — recopie manuelle datant
  du chap 3 (avant industrialisation), invisible jusqu'à la validation
  moteur.

**Validation incomplète volontairement** (cf §7 dans
`ameliorations_dilf_debutant.md`) :
- Pas de vérification avec Scan (donnerait l'évaluation en unités-pion,
  donc le caractère "gagnant" de la combinaison) — nécessite le backend
  Draught Master.
- Pas de vérification "globale" de la prise maximale (toutes les cases
  du joueur) — la validation se limite à vérifier que le final_move
  est une rafle maximale parmi celles du joueur au trait.

**Conséquence pratique** : les 132 final_move sont **garantis légaux
selon les règles FMJD**. La validation "gagnante" reste à faire avec
Scan, ce qui est prévu dans la phase de transformation
`verified=False → verified=True` du cadrage §4.6.


---

### PR #32 dilf — Extension dames du module dubois — ✅ MERGÉE (mai 2026)

Implémentation de la section §3 de `ameliorations_dilf_debutant.md` (priorité
haute du backlog).

**Contenu** :
- `enumerate_king_captures(start, my_pieces, enemy_pieces)` — énumère les
  rafles maximales de dame
- `reconstruct_king_capture(state, from_sq, to_sq)` — reconstruit le `Move`
  d'une rafle de dame depuis la notation Dubois courte
- `reconstruct_capture(state, from_sq, to_sq)` — dispatcher unifié (pion vs
  dame, auto-détecté)
- `NotAKingError` — exception miroir de `NotAManError`
- 16 nouveaux tests unitaires sur des configurations minimales
- Doc `docs/dubois-notation.md` mise à jour (section géométrie dame,
  exemple dispatcher, API étendue)

**Statistiques** :
- 3 fichiers modifiés : 589 lignes ajoutées, 23 retirées
- Tests : 32/32 passent (16 anciens pion + 16 nouveaux dame)
- mypy --strict clean

**Workflow PR** :
- Branche poussée depuis l'environnement Claude via PAT (révoqué après usage)
- API GitHub (`api.github.com`) bloquée par allowlist réseau → création de
  la PR par l'utilisateur via le lien `/pull/new/claude/king-rafle-extension`
- Mergée par l'utilisateur dans `main` (merge commit `8efd4fd`)

**Suite du backlog** : restent §1 (wrapper standardisé), §4 (détecteur
coquilles), §5 (glossaire étendu), §6 (détecteurs de motifs). 4 PRs à faire
quand le besoin se présente — typiquement avant démarrage manuel Intermédiaire.


---

### Session résolution des 3 blocages (mai 2026)

Traitement en batch des 3 fixtures bloquées identifiées en production
(BEG_CH09_007, BEG_CH10_008, BEG_CH13_004). Méthode appliquée pour
chacune :

1. Re-rasterisation à 300 DPI du diagramme concerné + annotation
   exhaustive des cases 1-50 pour cross-check visuel.
2. Confirmation que la position extraite par le pipeline est conforme
   au diagramme imprimé (les 3 positions sont correctes).
3. Recherche exhaustive de combinaisons gagnantes alternatives via
   énumération des sacrifices blancs possibles.
4. Interpellation §4.11 avec image + diagnostic + proposition.
5. Validation utilisateur des 3 corrections.
6. Application + re-validation moteur.

**3 nouvelles résolutions** :
- R009 : Dubois ch13 D5 — coquille `43-38` → `38-32`
- R010 : Dubois ch14 D6 — double inversion `37-31 (26x28)` → `27-21 (17x28)`
- R011 : Dubois ch17 D4 — inversion d'opérandes `(18x27)` → `(27x18)`

**Total coquilles PDF détectées pendant la production du manuel
Débutant** : 6 (R002, R004, R006, R009, R010, R011). Taux : 6/152
fixtures CORPUS = **4%**. Tous résolus.

**État final manuel Débutant après résolution des blocages** :
- 166 fixtures, 16 chapitres
- Round-trip FEN : 166/166 ✓
- Avec final_move : **135/166 (81%)** — passage de 132 à 135
- Validation moteur : **135/135 OK** — aucun échec
- Sources : 152 CORPUS (92%), 12 GENERAL (7%), 2 INVENTED (1%)
- Blocages restants : **0**

Le manuel est désormais en état final. Les 31 fixtures restant à
`final_move=None` sont toutes des cas de rafle de dame (sera levé par
intégration de la PR #32) ou de gambit se terminant par coup simple
(comportement attendu, pas un défaut).


---

### Bug report — Section CH02 du manuel prose désynchronisée des fixtures (mai 2026)

**Constat utilisateur** (5 captures de l'app `ai-draught-staging`) :
les références `BEG_CH02_001` à `BEG_CH02_005` affichées dans l'app
mènent à des diagrammes incohérents avec le texte. Ex : le texte parle
de "rafle 32×23 capturant deux pions noirs successifs" pour
`BEG_CH02_004`, mais la fixture contient juste W{22} B{27} (une seule
capture vers 31).

**Diagnostic** :
- Les fixtures du CH02 sont **internement cohérentes** (état + concept
  + title s'accordent).
- Le **manuel prose** du CH02 inventait des positions canoniques
  fictives (pion 32, noir 19) au lieu d'utiliser les vraies positions
  des fixtures (pion 35, pion 22). Erreur de rédaction sans cross-vérification.
- Il y avait aussi un décalage de numérotation : §2.3 référençait
  `BEG_CH02_004` (qui est "capture arrière") au lieu de `BEG_CH02_005`
  (qui est la vraie rafle).

**Correction appliquée** : section CH02 du manuel `manuel_debutant.md`
intégralement réécrite (§2.1 à §2.9), avec :
- Pour chaque fixture, description exacte de la position réelle (cases
  effectivement présentes dans `fixtures_debutant.py`)
- Nouvelle structure §2.1-§2.9 alignée sur les 12 fixtures dans l'ordre
- Ajout d'un §2.8 dédié au non-soufflage (BEG_CH02_011)

**Audit sur les autres chapitres** : 20 fixtures référencées avec des
cases mentionnées dans la prose mais pas dans l'état. La grande
majorité concerne des cases d'atterrissage de rafles (légitime — la
case d'arrivée n'est pas dans la position de départ). Aucun cas
manifestement faux comme le CH02 sur les autres chapitres.

**Cause racine** : la rédaction de la prose s'est faite "à la mémoire"
sans charger les fixtures pour cross-checker. À éviter pour les
prochains manuels : la prose doit citer les vraies positions
(`state.white_men`, `state.black_men`) via inspection programmatique
des fixtures, pas via reconstruction mémorielle.

**Implication pour le cadrage** : ajouter une étape de vérification
automatique "prose vs fixture" en fin de production de manuel.
À reporter dans `ETAT_DILF.md` §6 comme nouvelle suggestion §8
(validateur prose/fixture).


---

### Bug report — Chapitre 1 du manuel : grille ASCII illisible (mai 2026)

**Constat utilisateur** : la grille ASCII de numérotation 1-50 dans le
chapitre 1 du manuel rend mal dans Draught Master — colonnes
décalées, illisible sur mobile. De toute façon redondante car le
damier rendu par l'app affiche déjà tous les numéros.

**Correction appliquée** : 
- Suppression du bloc ASCII de numérotation (rangées 1-10 × colonnes 1-10).
- Remplacement par la référence à `BEG_CH01_001` (position initiale) et
  `BEG_CH01_002` (après 32-28) qui montrent la numérotation
  directement via le rendering damier de l'app.
- Suppression aussi des blocs FEN complets verbeux pour la position
  initiale et 32-28 (l'info est dans la fixture, le rendu damier la
  donne).
- Conservé : le mini-bloc abstrait `<trait>:W<cases blancs>:B<cases noirs>`
  qui explique la forme générale du FEN.
- Conservé : la description textuelle des règles de notation (coup
  simple, rafle, parenthèses, trait).

**Règle pour les manuels suivants** : ne pas réinventer ce que
Draught Master rend déjà visuellement. Les fixtures sont la source
de vérité affichable ; le manuel prose doit y référer plutôt que de
dupliquer en texte/ASCII/FEN brut.


---

### Bug report — Chapitres 3, 4, 13 du manuel : notations Dubois fictives (mai 2026)

**Constat utilisateur** : sur l'app Draught Master, `BEG_CH03_001`
affiche un diagramme avec sacrifice `26-21` (correct selon la fixture),
mais le texte du manuel dit `28-23 (19x39) 44x4` (faux — c'est une
autre combinaison Dubois imaginaire).

**Diagnostic** : malgré la correction du CH02 lors d'une session
précédente, la même erreur méthodologique persistait sur d'autres
chapitres. J'avais cité des notations Dubois "canoniques" de mémoire
au lieu de copier les `published_notation` réelles des fixtures.

**4 désynchronisations identifiées et corrigées** :

| Fixture | Prose disait | Réalité (publiée) |
|---|---|---|
| BEG_CH03_001 | `28-23 (19x39) 44x4` | `26-21 (17×28) 43×3` |
| BEG_CH03_002 | `28-22 (18x27) 32x5` | `28-22 (17×28) 32×5` |
| BEG_CH03_004 | `28-23` (mention) | `34-29 (23×21) 29×7` |
| BEG_CH04_005 | `35-30 (24x35) 34-29 (35x24) 30x4` | `29-24 (22×33) 32-28 (19×39) 28×6` |
| BEG_CH04_010 | "rafle de dame `4x47`" | `34-29 (23×25) 27-22 (17×28) 32×3` |
| BEG_CH13_009 | diagonale `31-22-13-4` | trajet `31→22→33→24→15→4` |

**Corrections appliquées dans `manuel_debutant.md`** :
- Section §3.1 et §3.2 entièrement réécrites avec les vraies
  notations des fixtures BEG_CH03_001 à BEG_CH03_010.
- §3.3 corrigée (`(17x28)` au lieu de `(18x27)` pour BEG_CH03_002).
- §4.2 et §4.4 corrigées (vraies notations CH04_005 et CH04_010).
- §13.1 corrigée (vraie trajectoire de la rafle finale 31x4).
- Note technique obsolète sur PR #31 supprimée (rendue caduque
  par PR #32 dilf — extension dames mergée).

**Audit étendu** : un script ad-hoc a comparé les notations entre
backticks dans chaque paragraphe vs `published_notation` de la
fixture. 6 désynchros détectées, dont 2 faux positifs (BEG_CH02_006
et CH02_007 mentionnent `31x22` à titre pédagogique, légitime ; et
CH13_007 voit `40×16` dans la liste de variantes adjacentes). Les
4 vraies désynchros sont toutes corrigées.

**Limitation du validateur prose/fixtures actuel** : il vérifiait
le recouvrement de cases mais pas les **notations entre backticks**.
Ce nouveau type de validation pourrait être intégré dans
`validate_prose_vs_fixtures.py` (TODO à ajouter pour le manuel
Intermédiaire).


---

### Audit final déclenché par §5 du cadrage — détection bug géométrique (mai 2026)

**Constat utilisateur** : sur Draught Master, la prose de `BEG_CH02_001`
affirmait "le pion blanc 35 peut se déplacer en 30 ou 31" — la case 31
n'est géométriquement pas en diagonale depuis 35 (35 est sur le bord
droit du plateau, en (6,9)).

**Procédure suivie** : application de la checklist d'audit §5 du
cadrage (introduite par le commit cf55c7e), point §3.c — vérification
des affirmations géométriques contre la géométrie FMJD.

**Bugs détectés** :

1. `BEG_CH02_001` (prose ET fixture concept) : "pion 35 → 30 ou 31"
   alors que seul 30 est légal (35 est en case de bord droit).
2. `BEG_CH02_008` (fixture concept uniquement, la prose avait été
   corrigée par le commit a4c647c précédent) : "pion 6 → 6-1 ou 6-2"
   alors que seul 6-1 est légal (6 est en case de bord gauche).

Le commit a4c647c (Claude Code) avait corrigé la prose du manuel pour
CH02_008 mais avait laissé le bug dans le `concept` de la fixture.
Cette désynchronisation prose/fixture n'avait pas été détectée.

**Corrections appliquées** :

- `manuel_debutant.md` §2.1 : précise que le pion 35 (sur le bord
  droit) n'a qu'un seul coup légal (35→30).
- `fixtures_debutant.py` BEG_CH02_001 concept : reformulé avec
  "seul déplacement légal est 35-30 (la diagonale haut-droite est
  bloquée par le bord du plateau)".
- `fixtures_debutant.py` BEG_CH02_008 concept : reformulé avec
  "n'a qu'un seul coup légal : 6-1, qui le promeut en dame" (au lieu
  de "deux coups possibles : 6-1 ou 6-2").

**Amélioration outillage** :

- `validate_prose_vs_fixtures.py` enrichi d'un audit géométrique FMJD :
  pour chaque référence dans la prose ET pour chaque fixture, détecte
  les affirmations "le pion X peut Y ou Z" où Y ou Z ne sont pas dans
  les diagonales légales du pion X. Inclut helpers `_case_to_rc`,
  `_rc_to_case`, `_pawn_simple_moves`, et `_check_geometric_claims`
  avec filtre négations.
- Audit complet exécuté : 0 affirmation géométrique invalide restante
  dans le manuel et dans les concepts/explanations des 166 fixtures.

**Conformité §5 du cadrage** :

- Validation moteur : ✅ 135/135 OK (inchangé)
- Validation prose/fixtures : ✅ géométrie OK ; quelques warnings notation
  soft (faux positifs structurels listes à puces, déjà documentés)
- Audit manuel chapitre par chapitre : ✅ 2 corrections appliquées
  (CH02_001 prose+fixture, CH02_008 fixture)


---

### Audit couleur des pièces — bug CH07_001 (mai 2026)

**Constat utilisateur** : sur Draught Master, la prose de `BEG_CH07_001`
disait « une seule attaque noire (sur le pion blanc 25) » alors que sur
le diagramme la case 25 est NOIRE.

**Diagnostic** : double erreur dans la prose.
1. « pion blanc 25 » : la case 25 est noire (B_men contient 25).
2. « attaque sur le pion 25 » : l'attaque noire porte en réalité sur le
   pion BLANC 30. Le mécanisme : le pion noir 25 menace de capturer le
   blanc 30 (25x34 par-dessus 30). Le blanc exploite ce « temps de
   repos » en jouant un coup utile (42-37) avant que le noir ne soit
   forcé de capturer.

**Corrections appliquées** :
- `manuel_debutant.md` §7.1 : « le pion noir 25 menace le pion blanc 30 ».
- `fixtures_debutant.py` BEG_CH07_001 concept : reformulé pour expliquer
  correctement le mécanisme (pion noir 25 menace blanc 30).

**Audit couleur étendu** : nouveau détecteur ajouté à
`validate_prose_vs_fixtures.py` (`_check_color_claims`) qui vérifie que
toute mention « pion blanc X » / « pion noir X » / « dame blanche X »
correspond à la couleur réelle de la pièce dans la fixture.

Résultats de l'audit complet :
- Prose du manuel : 1 bug (CH07_001, corrigé). 0 autre.
- Concepts/explanations des 166 fixtures : 1 bug détecté
  (`BEG_CH11_005` : « pion noir en 22 » alors que 22 est blanc — le
  concept du coup de Rappel était mal formulé). Corrigé : le concept
  explique maintenant que le Rappel force un pion noir à *revenir
  capturer* sur la case 22.

**Outillage** : `validate_prose_vs_fixtures.py` cumule désormais 4
validations : (1) recouvrement de cases prose/fixture, (2) notations
Dubois citées vs published_notation, (3) affirmations géométriques
(coups simples légaux FMJD), (4) couleur des pièces annoncée. Les 4
tournent automatiquement dans l'étape d'audit §5 du cadrage.

**Conformité §5 du cadrage** :
- Validation moteur : ✅ 135/135 OK (inchangé)
- Validation prose/fixtures : ✅ géométrie OK, couleur OK ; warnings
  notation soft = faux positifs structurels (listes à puces) déjà documentés
- Audit manuel : ✅ 2 corrections (CH07_001 prose+fixture, CH11_005 fixture)


---

### Génération assistée par position_facts.py (mai 2026)

**Demande utilisateur** : pour chaque position commentée, double-valider
automatiquement la prose contre la fixture. Choix : option 3 — la prose
factuelle de base est auto-générée depuis la fixture, Claude ne rédige à
la main que l'interprétation.

**Livré** : nouveau module `position_facts.py` qui génère une **fiche de
faits déterministe** pour chaque fixture :
- pièces + couleur exacte (case → blanc/noir, pion/dame)
- trait
- coups simples légaux de chaque pion du camp au trait (géométrie FMJD)
- menaces de capture immédiates pion/pion (les DEUX camps)
- published_notation verbatim + trajet de la rafle finale

Deux usages :
1. `render_facts_sentence(p)` : socle de rédaction (phrase factuelle de base).
2. `facts_for(p)` : dict structuré pour la double-validation.

**Validation du module** sur les bugs déjà corrigés : le générateur
reproduit exactement les bonnes réponses —
- CH07_001 : « le pion noir 25 peut capturer le pion blanc 30 » ✓
- CH02_001 : `simple_moves = {35: [30]}` (un seul coup) ✓
- CH02_008 : `simple_moves = {6: [1]}` (un seul coup) ✓

Tous les 3 bugs qu'on avait corrigés à la main auraient été évités si la
prose avait été dérivée de la fiche.

**Limite documentée (cadrage §4.14 point 5)** : position_facts ne
calcule de façon fiable que les faits matériels/géométriques simples.
Les combinaisons tactiques complexes (rafles, coups de dame) ne sont pas
déroulées — elles restent du ressort du moteur Scan.

**5 affirmations tactiques à vérifier au moteur** : concepts mentionnant
une « attaque X-Y » dont la géométrie de pion simple ne confirme pas la
menace (probablement des attaques post-sacrifice ou des coups de dame,
NON corrigées car §4.7 interdit de corriger ce qu'on ne comprend pas) :
BEG_CH04_005, BEG_CH04_008, BEG_CH07_003, BEG_CH07_004, BEG_CH07_011.

**Ces 5 cas + les 31 fixtures `final_move=None` + la validation
« gagnant » de l'ensemble sont désormais consignés dans le fichier de
suivi dédié `A_VERIFIER_MOTEUR.md`** (au lieu d'être enterrés dans ce
journal chronologique). À traiter lors de la phase
`verified=False → verified=True` (cadrage §4.6), quand le backend
Draught Master + Scan est disponible.

