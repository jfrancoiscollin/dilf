# draught-master — base de connaissances stratégique depuis les diagrammes

> **Status**: **shipped** dans `jfrancoiscollin/draught-master` sur la
> branche `develop` (PR #118, #119). Tout le code vit dans
> `backend/strategy/` côté draught-master ; **dilf n'est pas modifié**.
> Ce document enregistre, côté dilf, comment le consumer downstream
> exploite le corpus prose de dilf pour rendre les diagrammes
> interactifs, dans la lignée des autres notes de `docs/integration/`.
>
> Doc de référence côté consumer :
> `draught-master/docs/STRATEGIE_KNOWLEDGE_BASE.md`.

## Contexte

Les quatre manuels scannés (Sijbrands, Springer, Roozenburg, Keller) ont
été entièrement numérisés et les positions de tous les diagrammes
extraites en FEN. draught-master consolide ces 1369 positions en un
pipeline à quatre couches :

1. **Bibliothèque de positions** — 1308 positions validées par le moteur
   (`build_position_library.py` → `position_library.json`).
2. **Base de connaissances thématique** — 66 thèmes de leçon + 68/79 tips
   enrichis de positions-exemples des manuels.
3. **Exercices vérifiés** — 108 exercices (finales, gains de matériel,
   annihilations), chaque solution prouvée par rejeu moteur.
4. **Prose interactive** — voir le lien d'interop ci-dessous.

## Lien d'interop dilf → draught-master

Le seul point de contact avec dilf est le **corpus prose** :

- Les passages affichés dans le panneau « Apprendre » de draught-master
  proviennent des fixtures dilf
  `pedagogy/prose/fixtures/prose_passages_{sijbrands,springer,roozenburg,keller}_*.py`,
  consommées via `pedagogy.prose.retrieval` (déjà couvert par le contrat
  `INTEROP.md`, non élargi ici).
- Lorsqu'un passage cite « **Diagramme N** » (ancre présente dans le
  texte prose de dilf), draught-master résout la position via son propre
  endpoint `GET /api/strategy/diagram-fen?source=…&page=…&number=N` et
  rend un plateau à côté du texte.
- La résolution FEN, la validation de légalité et le rendu sont
  **entièrement côté draught-master**. dilf ne fournit que le texte et
  l'ancre « Diagramme N ».

**Aucune nouvelle surface d'API dilf n'est requise.** Le contrat
`INTEROP.md` (symboles `pedagogy.*` importés par draught-master) est
inchangé. Si un jour le format des ancres « Diagramme N » devait évoluer
dans les fixtures prose, ce serait un changement coordonné à signaler ici
(le frontend détecte l'ancre par regex `\bdiagramme\s+(\d+)`).

## Pourquoi côté draught-master et pas dilf

- dilf est la **bibliothèque pédagogique pure** (features, motifs,
  verdicts, prose) ; pas de moteur de recherche temps réel ni de stockage
  applicatif (cf. `ROADMAP.md` « Out of scope »).
- Le pipeline s'appuie sur le **moteur** de draught-master
  (`game_engine`, `ai_engine`) pour valider la légalité et miner les
  lignes gagnantes — hors périmètre dilf par conception.

## Suivi possible

- Couverture humaine faible côté Springer (3 FEN vérifiées) : une
  campagne de transcription manuelle ciblée améliorerait la confiance.
- Keller n'a pas de thèmes (table des matières mal extraite par
  `extract_strategy_sections.py`) : ses positions restent dans la
  bibliothèque sans thème.
