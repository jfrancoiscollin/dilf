# RESOLUTIONS — conversation Débutant (mai 2026)

Fichier scratch tenu en cours de conversation, conforme cadrage §8.1.

---

## R000 — Cadrage : utilisation obligatoire du pipeline dilf

- **Type** : règle de méthode
- **Résolution Claude** (sans interpellation) : voir CADRAGE_MANUELS.md §4.10
- **Règle d'inférence** : pour toute position `source=CORPUS`, jamais
  transcrire à la main, toujours référencer par `crop_id` issu du
  pipeline `extract_diagrams.py`.
- **Implication dilf** : aucune (méta-règle de la conversation).

---

## R001 — Notation `(17x28)` D1 p.6 : rafle zigzagante (NON-direct)

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_006_d01.png` — W{26,31,32,43} B{9,17,19,38}
- **Solution publiée** : `"26-21 (17x28) 43x3"`
- **Blocage initial** : je croyais qu'une notation `aXb` impliquait un
  chemin direct (une seule diagonale) entre a et b. Donc `17x28`
  exigeait selon moi un blanc en 22 sur le chemin direct 17→28.
- **Tentatives** :
  1. Re-lecture PDF avec `pdftotext -layout` → solution identique
  2. Re-rasterisation à 400 DPI → position identique, pas de pion en 22
- **Résolution utilisateur** : la notation `aXb` désigne **uniquement la
  case de départ et la case d'arrivée** de la rafle. La rafle peut
  **zigzaguer** sur plusieurs diagonales : entre 17 (départ) et 28
  (arrivée), le chemin réel est `17 → BG 21 (saute 21) → 26 → BD 31
  (saute 31) → 37 → HD 32 (saute 32) → 28`. **3 pions capturés** (21,
  31, 32), prise majoritaire forcée.

  La rafle blanche `43x3` qui suit fait pareil : `43 → HG 38 (saute 38)
  → 32 → HD 28 (saute 28, le 17 qui vient d'y atterrir) → 23 → HD 19
  (saute 19) → 14 → HG 9 (saute 9) → 3`. **4 pions capturés**.

- **Règle d'inférence** : **toute notation Dubois `aXb` est une rafle
  pouvant changer de diagonale à chaque saut.** Pour reconstruire la
  trajectoire complète à partir de `aXb` + position de départ, Claude
  doit énumérer tous les chemins légaux qui partent de `a` et finissent
  en `b`, en cherchant la rafle maximale (prise majoritaire). Si une
  seule trajectoire maximale existe → `(aXb)` la désigne sans ambiguïté.
  Si plusieurs → ambiguïté à signaler dans `claude_notes`.

  **Concrètement pour les fixtures** : le champ `published_notation`
  contient le verbatim Dubois `aXb`. Le champ `final_move` (optionnel)
  peut être construit en énumérant les rafles légales depuis a et en
  retenant celle qui finit en b avec le max de captures.

- **Implication dilf** : il manque dans `pedagogy/` un utilitaire
  `reconstruct_capture_path(state, from_sq, to_sq) → Move` qui prend
  une notation Dubois courte (`17x28`) et reconstruit la rafle complète
  via énumération exhaustive. Très utile pour matérialiser les
  `final_move` automatiquement à partir du texte des solutions
  Dubois. **À ajouter au livrable `ameliorations_dilf_debutant.md`
  (catégorie "Schéma `pedagogy/game.py`" ou nouveau module
  `pedagogy/notation/dubois.py`).**

  ✅ **Implémenté et mergé** (PR #31, mai 2026) : module
  `pedagogy/notation/dubois.py` avec `reconstruct_pawn_capture()` et
  `enumerate_pawn_captures()`, 16 tests verts, mypy --strict clean,
  doc à `docs/dubois-notation.md`. Périmètre limité aux pions
  (kings = follow-up).


---

## R002 — Coquille Dubois D9 p.6 : "43-38" doit se lire "44-39"

- **Livre** : `dubois_apprent_combin.pdf`
- **Position extraite** : `crops/page_006_d09.png` — W{30, 32, 35, 44, 48} B{14, 23, 25, 29, 33}
- **Solution publiée (verbatim PDF)** : `"43-38 (25x43) 48x10"`
- **Solution réelle (validée par utilisateur)** : `"44-39 (25x43) 48x10"`
- **Blocage** : la solution PDF démarre par `43-38` mais aucun pion blanc
  n'est en 43 dans la position. La rafle `(25x43)` n'est pas
  reconstructible non plus depuis 25.
- **Tentatives** :
  1. Hypothèse 'le pion en 44 est en réalité en 43' → testé, `(25x43)`
     toujours non reconstructible.
  2. Hypothèse 'pion en 43 manquant dans l'extraction' → testé avec ajout
     blanc en 43, `(25x43)` toujours non reconstructible.
- **Résolution utilisateur** : il n'y a pas de pion en 43. La vraie
  notation du coup blanc est **`44-39`**, pas `43-38`. C'est une coquille
  rarissime du PDF Dubois — sans doute typo d'impression sur deux chiffres
  successifs (4→3 et 9→8). La position de dilf est exactement juste, c'est
  la transcription textuelle de la solution dans le PDF qui est fautive.
  Trajectoires validées :
  - Sacrifice `44-39` (44 monte sur 39)
  - Rafle noire `(25x43)` = `25 → 34 → 43`, captures (30, 39), 2 pions —
    prise majoritaire (vs autres rafles à ≤1 pion)
  - Rafle blanche `48x10` = `48 → 39 → 28 → 19 → 10`, captures
    (14, 23, 33, 43), 4 pions

- **Règle d'inférence** : **quand la solution PDF mentionne une case
  de départ qui n'existe pas dans la position**, ne pas écarter d'office
  le diagramme — appliquer ce protocole en 3 étapes :
  1. Vérifier si une case voisine (±1 sur une diagonale) rend la
     solution cohérente. Une typo simultanée sur deux chiffres
     consécutifs (X-Y vs (X±1)-(Y±1)) est le motif observé.
  2. Si oui, le bug est typographique côté PDF, **pas** côté pipeline.
     Stocker la solution corrigée dans `published_notation` avec un
     `claude_notes` qui mentionne explicitement la coquille PDF.
  3. Si non, interpellation §4.11.

  **Concrètement pour les fixtures** : `published_notation` contient le
  verbatim **corrigé**, et `claude_notes` documente la divergence avec
  le PDF source pour traçabilité.

- **Implication dilf** : suggestion pour `ameliorations_dilf_debutant.md`
  (catégorie "Glossaire de notation Dubois" ou "Pipeline d'extraction") :
  ajouter un **détecteur de typos PDF** qui croise chaque coup mentionné
  dans la solution textuelle avec la position extraite, et signale les
  incohérences (case de départ sans pièce, rafle non reconstructible).
  Permettrait d'identifier les ~5-10 coquilles probables du PDF Dubois
  410 combinaisons sans intervention humaine répétée.



---

## R003 — D5 p.6 : deux trajectoires de rafle aux captures identiques

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_006_d05.png` — W{24,25,33,37,41,42,43} B{8,9,10,13,18,19,26,27}
- **Solution publiée** : `"37-31 (27x20) 25x5"`
- **Blocage léger** (résolu sans interpellation) : la rafle blanche
  `25x5` a deux trajectoires possibles qui prennent EXACTEMENT les
  mêmes 6 pions noirs :
  - `25 → 14 → 3 → 12 → 23 → 14 → 5` (coup turc traversant 14 deux fois)
  - `25 → 14 → 23 → 12 → 3 → 14 → 5`
  Captures identiques dans les deux cas : {8, 9, 10, 18, 19, 20}.
- **Résolution Claude** : équivalence de jeu (mêmes captures = même
  effet sur la position). Le helper `reconstruct_capture_move` a été
  modifié pour accepter ce cas : si plusieurs trajectoires candidates
  capturent strictement les mêmes pions, retourner la première
  (par convention `final_move`). Si les captures diffèrent, vraie
  ambiguïté → retourner None.
- **Règle d'inférence** : ce cas existera fréquemment sur les rafles
  longues passant par les grandes diagonales. Accepter l'équivalence
  par captures identiques est la règle générale.
- **Implication dilf** : la fonction `reconstruct_capture_move` mérite
  d'aller dans `pedagogy/notation/dubois.py` avec ce comportement
  documenté (cf suggestion R001).


---

## R004 — Ch6 D1 p.21 : coquille PDF `(15x21)` → vraie notation `(15x31)`

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_021_d01.png` — W{25,28,29,30,32,36,37,38,39} B{8,12,13,14,15,16,17,19,22}
- **Solution PDF** : `"25-20 (15x21) 36x20"`
- **Solution réelle** : `"25-20 (15x31) 36x20"` (validée utilisateur)
- **Mécanisme de l'erreur** : typo sur le 1er chiffre du 2e nombre (`21` → `31`).
  Le 2e coup (`36x20`) est juste — confirmé : trajectoire blanche
  `36 → 27 → 18 → 9 → 20`, captures 13, 14, 22, 31.
- **Validation géométrique** : rafle noire `(15x31)` = `15 → 24 → 33 → 42 → 31`,
  captures 20, 29, 37, 38 (prise majoritaire forcée à 4 pions).
- **Règle d'inférence (étend R002)** : les typos PDF Dubois peuvent porter sur
  un seul des chiffres d'un nombre à 2 chiffres (`21` vs `31`, pas seulement
  `±1` simultanés comme en R002). Élargir la fenêtre de recherche aux 4 voisins
  numériques quand un chiffre seul est suspect.

---

## R005 — Ch6 D5 p.21 : diagramme faux (à skip)

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_021_d05.png` — W{27,28,32,37,38} B{12,13,14,15,18}
- **Solution PDF** : `"38-33 (15x22) 28x10"` (avec mention "coup turc")
- **Blocage** : depuis 15, après 38-33, aucune rafle ne va vers 22 (géométrie
  impossible).
- **Résolution utilisateur** : **erreur dans le livre, diagramme faux**. La
  position imprimée ne correspond pas à la solution. Probable bug Dubois
  jamais corrigé.
- **Décision** : **skip** cette fixture. Ne pas inclure dans le manuel
  Débutant. Documenter l'omission dans le journal et dans
  `sources_debutant.md`.
- **Règle d'inférence** : lorsque l'utilisateur tranche "diagramme faux",
  ne pas inclure la fixture et passer à la suivante. Le skip doit être
  explicite (pas de bricolage de position).
- **Implication dilf** : alimente §3 ameliorations_dilf (détecteur de
  coquilles PDF) — ce cas serait flaggé "position incohérente avec la
  solution publiée" et passerait directement en review humaine.

---

## R006 — Ch7 D8 p.24 : coquille PDF `31x3` → vraie notation `32x3`

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_024_d08.png` — W{27,30,32,34,35,37,43} B{9,16,17,19,21,23,24}
- **Solution PDF** : `"34-29 (23x25) 27-22 (17x28) 31x3"`
- **Solution réelle** : `"34-29 (23x25) 27-22 (17x28) 32x3"` (validée utilisateur)
- **Mécanisme de l'erreur** : typo sur le 2e chiffre du 1er nombre (`31` → `32`).
- **Validation géométrique** : rafle blanche `32x3` = `32 → 23 → 14 → 3`,
  captures 9, 19, 28 (3 pions, coup de mazette canonique).
- **Règle d'inférence** : confirme R004 — les typos PDF peuvent porter sur
  un seul chiffre, **sur n'importe quelle position** dans le nombre (pas
  seulement le 1er).

---

## R007 — Limitations attendues : envois à dame (Ch6 D10, Ch7 D5)

- **Type** : limitation connue, pas d'interpellation
- **Livre** : `dubois_apprent_combin.pdf`
- **Positions concernées** :
  - Ch6 D10 : solution `"38-32 (27x49) 34-30 (49x24) 29x7"` — le noir 27
    devient dame en 49 puis fait `49x24` en tant que dame.
  - Ch7 D5 : solution `"28-23 (19x48) 17-12 (48x19) 12x1"` — le noir 19
    devient dame en 48 puis fait `48x19` en tant que dame.
- **Blocage** : `pedagogy.notation.dubois.reconstruct_pawn_capture` est
  **pion-only** dans sa version actuelle (PR #31 mergée). Il refuse de
  reconstruire un Move dont le départ est une dame
  (`NotAManError: holds a king`).
- **Résolution Claude** : pour ces deux fixtures, stocker la notation
  publiée verbatim dans `published_notation` et laisser `final_move=None`.
  Documenter dans `claude_notes` que la rafle finale est une rafle de dame
  non reconstructible avec le module actuel.
- **Règle d'inférence** : toute solution Dubois contenant un envoi à dame
  intermédiaire suivi d'une rafle de la dame nouvellement promue
  → `final_move=None`, `claude_notes` explicite. Ne pas tenter de
  reconstruire.
- **Implication dilf** : ce cas est déjà dans la liste "Future work" de
  `docs/dubois-notation.md` (PR #31). À promouvoir en suggestion explicite
  §5bis dans `ameliorations_dilf_debutant.md` : étendre le module aux
  rafles de dame. Le manuel Débutant a 2 cas qui en bénéficieraient ; les
  manuels Intermédiaire/Avancé/Expert en auront beaucoup plus.


---

## R008 — Notation Dubois `(ad lib)` : choix forcé entre 2 réponses adverses

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_027_d10.png` — Dubois ch8 D10
- **Solution publiée** : `"32-27 (21x23) 33-28 (ad lib) 38x29"`
- **Découverte** (sans interpellation) : `(ad lib)` désigne le cas où
  l'adversaire est dans une **position de prise obligatoire** avec
  plusieurs captures forcées toutes équivalentes — **toutes conduisent
  au même résultat final**. Dubois omet le détail puisque le coup est
  forcé et le résultat indépendant du choix.

- **Cas D10 spécifique** : après `33-28`, le noir doit choisir entre
  `(22x33)` ou `(23x32)`. Dans les deux cas, `38x29` ramasse 5 pions
  noirs et gagne. Le `(ad lib)` souligne cette équivalence stratégique.

- **Règle d'inférence** : quand on rencontre `(ad lib)` dans une
  notation Dubois, énumérer toutes les captures forcées de l'adversaire
  et vérifier qu'au moins une mène à la solution suivante. Pour la
  fixture, stocker une variante (la première par ordre lexicographique
  des cases de départ) et documenter dans `claude_notes` que d'autres
  variantes existent par `(ad lib)`.

- **Implication dilf** : suggestion supplémentaire pour
  `ameliorations_dilf` (catégorie "Glossaire de notation Dubois") :
  documenter `(ad lib)` comme convention reconnue dans
  `docs/dubois-notation.md` (PR future).


---

## R009 — Coquille PDF Dubois ch13 D5 page 43 : `43-38` → `38-32`

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_043_d05.png` — W{26,28,32,33,35,36,38,39,42,43,44,45} B{9,12,13,16,17,18,19,20,23,24,29,30} trait blanc
- **Solution publiée (verbatim)** : `"32-27 (23x21) 43-38 (29x40) 45x3"`
- **Diagnostic** : après `32-27 (23x21)`, la case 38 est encore occupée par un pion blanc. Le coup `43-38` est donc illégal (case de destination non vide). De plus, même si on l'ignorait, aucune rafle noire `(29x40)` n'est légale dans l'état atteint.
- **Tentatives auto** :
  1. Énumération de toutes les rafles noires après `32-27 (23x21) 43-38` → 0 résultat (le pion noir 29 n'a aucun voisin enemy sur diagonale libre).
  2. Recherche exhaustive de tous les sacrifices blancs alternatifs au coup 2 qui mènent à `45x3` finale → **1 unique solution** trouvée : `38-32` au lieu de `43-38`.
- **Validation utilisateur** : confirmée. La séquence correcte est `32-27 (23x21) 38-32 (29x40) 45x3`. La rafle noire `(29x40)` capture 33, 43 et 44 en passant par 38 → 49 → 40 (la traversée de la dernière rangée 49 sans s'y arrêter ne déclenche pas la promotion).
- **Règle d'inférence** : quand une notation Dubois échoue avec NoSuchRafleError ET qu'une recherche exhaustive révèle une **unique** solution proche, on peut la proposer en interpellation. Le pattern de coquille ici est l'inversion ou la confusion de deux nombres adjacents sur le même coup (`43-38` ↔ `38-32` partagent le digit 38).
- **Implication dilf** : alimente la suggestion §4 du backlog d'améliorations (détecteur de coquilles PDF). Ce cas pourrait être détecté automatiquement par énumération des coups blancs alternatifs.
- **`final_move` reconstruit** : `Move(path=(45, 34, 25, 14, 3), captures=(9, 20, 30, 40))`.


---

## R010 — Coquille PDF Dubois ch14 D6 page 46 : `37-31 (26x28)` → `27-21 (17x28)`

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_046_d06.png` — W{27,31,32,38,40,44,50} B{8,16,17,18,23,25,30} trait blanc
- **Solution publiée (verbatim)** : `"37-31 (26x28) 40-34 (30x39) 44x2"`
- **Diagnostic** : ni le pion blanc 37 ni le pion noir 26 n'existent dans la position extraite (confirmée par lecture haute résolution du diagramme).
- **Tentatives auto** :
  1. Énumération des coups blancs alternatifs au coup 1 (32-28, 40-34, 27-21, 27-22) — aucun ne fait sens directement.
  2. Recherche exhaustive de toutes les combinaisons 2-sacrifices + rafle gagnante atteignant `44x2` → **1 unique solution** : `27-21 (17x28) 40-34 (30x39) 44x2`.
- **Validation utilisateur** : confirmée.
- **Pattern de coquille** : double inversion typographique cohérente (37↔27, 31↔21, 26↔17 — chaque paire diffère par le digit de gauche de 1). Probable saut de ligne ou décalage de colonne lors de la saisie.
- **Règle d'inférence** : pour les coquilles complexes (plusieurs digits faux), la recherche exhaustive sur toute la séquence est plus fiable qu'une correction case-par-case.
- **Implication dilf** : confirme l'utilité de la suggestion §4 (détecteur de coquilles PDF) avec un mode "recherche exhaustive sur la séquence complète".
- **`final_move` reconstruit** : `Move(path=(44, 33, 22, 13, 2), captures=(8, 18, 28, 39))`.

---

## R011 — Coquille PDF Dubois ch17 D4 page 55 : `(18x27)` → `(27x18)`

- **Livre** : `dubois_apprent_combin.pdf`
- **Position** : `crops/page_055_d04.png` — W{28,30,32,33,34,35,37,38,39} B{9,14,15,16,17,20,21,26,27} trait blanc
- **Solution publiée (verbatim)** : `"28-22 (18x27) 37-31 (26x28) 33x4"`
- **Diagnostic** : 18 est vide dans la position. La notation Dubois `(18x27)` ne peut pas désigner un coup légal.
- **Tentatives auto** :
  1. Variante `(17x28)` : marche pour le premier sacrifice, mais la rafle finale `33x4` échoue derrière.
  2. Recherche exhaustive de toutes les combinaisons 2-sacrifices + rafle gagnante → **1 unique solution** : `28-22 (27x18) 37-31 (26x28) 33x4`.
- **Validation utilisateur** : confirmée.
- **Pattern de coquille** : **inversion des opérandes** d'une rafle — Dubois a écrit `(18x27)` au lieu de `(27x18)`, soit l'inverse de la convention `départ x arrivée`. C'est une coquille différente de R009 et R010 (substitution ou erreur d'OCR de chiffres) — ici les chiffres sont bons mais leur ordre est inversé.
- **Règle d'inférence** : quand un coup Dubois `(aXb)` est invalide parce que `a` est vide, tester systématiquement la variante `(bXa)` avant de chercher plus loin. Détectable automatiquement.
- **Implication dilf** : suggestion concrète pour le détecteur §4 — tester l'inversion des opérandes comme première heuristique de correction.
- **`final_move` reconstruit** : `Move(path=(33, 22, 13, 4), captures=(9, 18, 28))`.

