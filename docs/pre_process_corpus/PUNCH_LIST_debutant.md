# Punch list — passe finale `manuel_debutant.md`

> Produit par audit automatisé le 2026-05-26 (Claude / Opus 4.7 1M).
> Cible : `/home/user/dilf/docs/pre_process_corpus/manuel_debutant.md`
> (930 lignes, 16 chapitres + 4 annexes, 100% tactique FMJD 10x10).
> Chaque item à statuer (**corriger / accepter / différer**) avant
> clôture du cycle Débutant.
>
> Sources de vérité utilisées pendant l'audit :
> - `fixtures_debutant.py` (166 fixtures BEG_CH01_001 → BEG_CH16_010, toutes vérifiées round-trip FEN)
> - `scan/scan_analysis_debutant.json` (166 entrées Scan, **toutes `verified=true`**)
> - `CADRAGE_MANUELS.md` §0 « zéro invention » + §4
> - `RESOLUTIONS_debutant.md` (R001-R011) + `BLOCAGES.md` (tous résolus)
> - `A_VERIFIER_MOTEUR.md` (38 divergences Scan flaggées par Scan)
> - `ETAT_DILF.md` §7 (statistiques de référence du cycle)
>
> **Convention de criticité** :
> - 🔴 **Critique / bloquant** — viole le principe directeur §0 ou induit le lecteur en erreur factuelle / tactique.
> - 🟠 **Normal** — incohérence, info périmée, à corriger pour la qualité éditoriale.
> - 🟡 **Mineur** — coquille, formulation, choix éditorial à arbitrer.

---

## 1. Conformité zéro-invention (CRITIQUE)

> Rappel : tout verdict tactique (« ça gagne », « +X », « meilleur coup »,
> « menace Y au-delà de la menace directe pion/pion ») doit citer une
> source. Sources autorisées : Scan PV, `published_notation` verbatim,
> `position_facts.py`. Le scan_analysis_debutant.json est `verified=true`
> sur **166/166 fixtures** depuis la production — il est donc disponible
> pour CITER, mais le manuel ne s'en sert que dans le chapitre 7. Tous
> les chapitres 3 à 6 et 8 à 16 narrent des verdicts tactiques sans
> jamais citer ni Scan ni le PV ni l'éval — c'est le défaut systémique
> n°1 du manuel.

### 1.1 Affirmations tactiques sans source citée (défaut systémique)

- [ ] 🔴 **L233-243 (§3.1 — chapitre entier)** — Le chap 3 énonce 8
  fixtures (`BEG_CH03_001` à `010`) avec des notations Dubois et des
  affirmations comme « ramasse 4 noirs en traversant la grande diagonale
  jusqu'à la promotion », « rafle de 4 captures », « oser sacrifier 3
  pions consécutifs ». Aucune mention de Scan (alors que toutes ces
  fixtures sont `verified=true` avec `eval_after_pv ≥ +1` pour 8/10).
  Diagnostic : prose tactique sans citation de source, contrairement
  au chap 7 qui montre le pattern attendu.
- [ ] 🔴 **L237-238 (§3.1)** — « La rafle blanche finale `43×3` ramasse
  alors 38, 28, 19 et 9 en traversant la grande diagonale jusqu'à la
  promotion. » — La liste des captures (38, 28, 19, 9) **est** un fait
  vérifiable (`final_move.captures` de la fixture = `(9, 19, 28, 38)`),
  mais elle n'est pas citée comme telle. Le lecteur ne sait pas si c'est
  un fait ou une affirmation de Claude.
- [ ] 🔴 **L237 (§3.1)** — « La rafle noire majoritaire `17→26→37→28`
  (capturant 21, 31, 32) » — La trajectoire détaillée
  `17→26→37→28` n'apparaît PAS dans la `published_notation` (qui dit
  seulement `(17x28)`). Elle vient de R001 (réinterprétation Claude). À
  rapprocher du PV Scan `17x28x21x31x32` qui confirme les captures sans
  garantir la séquence des cases intermédiaires.
- [ ] 🔴 **L253-256 (§3.2)** — « Les noirs attaquaient deux pions
  blancs ; le sacrifice `34-29` exploite cette configuration » — Affirmation
  tactique non sourcée. Conformément à `CADRAGE §0`, « les noirs
  attaquent deux pions » dépasse la « menace directe pion/pion » que
  `position_facts.py` peut vérifier (c'est une attaque sur deux pions
  simultanément, donc bien complexe).
- [ ] 🔴 **L264-266 (§3.3)** — Pour `BEG_CH03_002`, narratif sans aucune
  citation Scan ni mention que la rafle finale est validée moteur.
- [ ] 🔴 **L293-296 (§4.2 — `BEG_CH04_005`)** — « Deux sacrifices
  successifs forcent les noirs à des prises majoritaires, puis la rafle
  blanche `28→19→8→17→6` traverse jusqu'à la promotion en dame en case
  6. » — Trajectoire `28→19→8→17→6` reconstruite par Claude (la fixture
  donne `path=(28, 19, 8, 17, 6)` mais le PV Scan
  `28x6x11x12x13x23` ne précise pas l'ordre des cases intermédiaires).
  De plus `A_VERIFIER_MOTEUR.md §1` flag explicitement cette fixture
  comme « concept à élucider au moteur » — non mentionné dans le manuel.
- [ ] 🔴 **L307-311 (§4.4 — `BEG_CH04_010`)** — Idem : trajectoire
  `32→23→14→3` détaillée comme un fait. Verdict « 5 pions et promeut »
  → la fixture dit 4 captures, pas 5. Erreur potentielle à valider.
- [ ] 🔴 **L375-379 (§6.1 — `BEG_CH06_001`)** — « inattendu `31-27`
  ouvre une prise majoritaire à 4 pions qui débouche sur la rafle. »
  L'affirmation « 4 pions » et « débouche sur la rafle » est tactique
  sans source. Aucune référence au PV Scan ni à la fixture.
- [ ] 🔴 **L389-392 (§6.3)** — Pour `BEG_CH06_002` : « Trois pions
  blancs contre trois pions noirs, sacrifice central `34-30`, rafle
  `40×7`. » Affirmation tactique sans citation.
- [ ] 🔴 **L396-398 (§6.4 — `BEG_CH06_010`)** — « rafle `1×41` qui
  semble bloquée par le pion 36 — la méthode des points de contact
  révèle que `(26-31)` fait disparaître le pion 36 et ouvre la voie. »
  Le mécanisme « le pion 36 disparaît » est une affirmation tactique
  non sourcée et non triviale.
- [ ] 🟠 **L419-444 (§7.1)** — `BEG_CH07_001` est commenté avec PV Scan
  cité (`+6.34`, profondeur 30) — **conforme au cadrage**. C'est le seul
  endroit du manuel qui suit le pattern recommandé. À utiliser comme
  référence pour reprendre les autres chapitres.
- [ ] 🔴 **L537-540 (§8.1 — `BEG_CH08_002`)** — « Le `32-28` est le
  sacrifice créateur, `34-29` est le coup gagné par le temps de repos,
  et la rafle `29×7` conclut. » Verdict tactique non sourcé.
- [ ] 🔴 **L546 (§8.2)** — « **Badal-Kemperman 1994** (`BEG_CH08_006`)
  — rafle 24×11 très rare ». L'affirmation « rare » est une appréciation
  tactique non sourcée.
- [ ] 🔴 **L572-578 (§9.1 — `BEG_CH09_001`)** — Tout l'énoncé : « Le
  pion blanc `33` parcourt toute la grande diagonale (33→22→13→2) en
  capturant 3 pions. La signature visuelle est très reconnaissable une
  fois qu'on l'a vue. » → trajectoire complète + verdict esthétique
  sans citation. Le PV Scan disponible montre `33x2x8x18x28` (3
  captures confirmées) — devrait être cité.
- [ ] 🔴 **L611-613 (§10.1)** — Pour `BEG_CH10_001` : « Le pion blanc
  28 **ricoche** sur la case 26 — exactement la case où le pion noir
  était initialement. » L'affirmation géométrique « la case 26 est où
  le pion noir était initialement » est vérifiable par
  `position_facts.py` (le pion noir 26 est dans `state.black_men`) mais
  n'est pas explicitement citée comme telle.
- [ ] 🔴 **L617-619 (§10.2 — `BEG_CH10_002`)** — Cas grave : le scan
  flag une **vraie divergence** (`published_notation` commence par
  `27-22` ; PV Scan commence par `31-26`). Le manuel cite `27-22` sans
  mentionner que Scan recommande un autre premier coup. Le lecteur va
  étudier une combinaison que Scan considère sous-optimale.
- [ ] 🔴 **L623-624 (§10.3)** — `BEG_CH10_009` : narratif « rafle finale
  `31×24` » présenté comme fait ; pas de citation Scan.
- [ ] 🔴 **L643-648 (§11)** — Les 3 schémas du coup de Rappel sont
  cités avec leurs notations Dubois mais aucun n'a de citation Scan,
  alors que tous sont `verified=true` (eval_after_pv > +90 pour
  `BEG_CH11_001`).
- [ ] 🔴 **L672-680 (§12.1-§12.2 — coup de chevron, coup renversé
  pur)** — Verdicts tactiques sans aucune citation Scan.
- [ ] 🔴 **L678-680 (§12.2)** — « la rafle finale arrive en 25 (case
  de bord proche du départ) » : la « proximité du départ » est une
  appréciation géométrique douteuse (départ 33 vs arrivée 25 = pas
  spécialement proches, mais case de bord oui).
- [ ] 🔴 **L708-712 (§13.1 — `BEG_CH13_009`)** — « Quatre sacrifices
  consécutifs ouvrent la trajectoire de la rafle finale
  `31→22→33→24→15→4` (promotion en dame avec 5 captures). »
  Trajectoire et verdict (« 5 captures ») sans citation Scan. Le PV
  Scan donne `31x4x10x20x27x28x29` (5 captures confirmées : 10, 20, 27,
  28, 29) — il faudrait citer ce PV plutôt que de paraphraser.
- [ ] 🔴 **L737-738 (§14.1 — `BEG_CH14_006`)** — Forme canonique du
  coup de la Trappe, donnée sans aucune citation Scan (`eval=+11.25` au
  Scan).
- [ ] 🔴 **L770-774 (§15.1 — `BEG_CH15_004`)** — **DIVERGENCE SCAN
  CRITIQUE NON MENTIONNÉE** : le manuel cite `34-29 (23×43) ...` mais le
  PV Scan commence par `33-29` (flag explicite dans
  scan_analysis_debutant.json, notes : « DIVERGENCE: published_notation
  starts with '34-29', Scan PV starts with '33-29' »). Le lecteur va
  apprendre une combinaison dont le premier coup n'est pas le meilleur
  selon Scan.
- [ ] 🔴 **L773-774 (§15.1 — `BEG_CH15_005`)** — Verdict « coup de
  dame à 1, symétrique du précédent » sans citation Scan (`eval=+9.70`).
- [ ] 🔴 **L778-779 (§15.2)** — « `BEG_CH15_007` et `BEG_CH15_008` sont
  des exemples longs et difficiles » — appréciation tactique non sourcée.
- [ ] 🔴 **L814-816 (§16.2 — `BEG_CH16_002`)** — « Une forme à 6
  demi-coups qui combine coup Philippe et collage. » Verdict tactique
  « combine coup Philippe et collage » non sourcé. À noter : pour
  `BEG_CH16_002`, le scan donne `eval_after_pv=+0.50` seulement → est-ce
  vraiment une combinaison gagnante au sens fort ? À documenter ou
  reformuler.
- [ ] 🔴 **L828-831 (§16.4 — `BEG_CH16_007`)** — « À retenir : la prise
  forcée `(13×31)` libère la rafle finale `32×5`. » Verdict « libère »
  est tactique sans source ; le PV Scan
  `28-22 ... 32x5x10x19x28` confirme la séquence mais n'est pas cité.

### 1.2 Tableau §7.3 — incompréhension du champ `eval_after_pv`

- [ ] 🔴 **L484-495 (§7.3)** — La colonne « Éval » du tableau présente
  les valeurs `eval_after_pv` comme s'il s'agissait de l'évaluation
  finale après la combinaison. Or plusieurs entrées montrent des
  valeurs gigantesques (`+90.67`, `+99.73`, `+99.73`) qui sont des
  signaux Scan pour « mat / gain forcé » (cf champ « Single-pass eval:
  eval_start == eval_after_pv (deep-search score) » dans les notes Scan).
  Le manuel ne précise pas cette convention ; un lecteur peut croire
  qu'il s'agit d'un avantage de 90 unités-pion (absurde). À documenter
  ou normaliser.

### 1.3 Préface — chiffres à vérifier

- [ ] 🟠 **L22-25 (Préface)** — « 152 des 166 positions sont extraites
  de l'ouvrage Apprentissage Combinaisons (...) Les 14 restantes
  illustrent des règles canoniques ou des schémas inventés à fin
  pédagogique. » — Statistique en désaccord avec l'annexe D (L915 dit
  « 152 du corpus Dubois (92 %), 12 de connaissance générale (7 %),
  2 inventées (1 %) » → total 166, donc 14 hors corpus). 14 = 12 + 2,
  cohérent. Mais préface dit « 14 illustrent règles ou schémas inventés »
  alors que parmi les 14, 12 sont GENERAL_KNOWLEDGE (et non « inventées »).
  Reformuler pour distinguer GENERAL vs INVENTED.

---

## 2. Cohérence rédactionnelle

### 2.1 Terminologie

- [ ] 🟡 **L18, L869** — Utilisation de « le moteur du framework » /
  « le moteur de recherche de l'application » sans préciser que c'est
  Draught Master + Scan (le seul nommé dans les autres documents). Pour
  un lecteur débutant qui découvre l'écosystème, cette imprécision peut
  prêter à confusion.
- [ ] 🟡 **L94** — Le mot « roi » apparaît dans le bloc FEN sans avoir
  été défini (alors que le manuel utilise « dame » partout ailleurs).
  Préciser que `K` signifie « king » en anglais (notation FEN
  internationale) mais qu'en français on dit « dame ».
- [ ] 🟡 **L168** — « C'est la fameuse règle du non-soufflage de la
  dame » — pour un lecteur débutant, le terme « non-soufflage » n'est
  pas défini, et la règle exposée ici concerne en réalité la **promotion
  passante**, pas le non-soufflage stricto-sensu (lequel concerne
  l'absence de prise reculée d'un pion déjà capturé en cours de rafle —
  qui est correctement décrit ensuite §2.8 L184).
- [ ] 🟠 **L184-193 (§2.8)** — Le titre de §2.8 « Non-soufflage (les
  captures restent jusqu'à la fin de la rafle) » entre en conflit avec
  l'usage habituel de « non-soufflage » dans la littérature francophone
  (= règle de promotion passante). Le concept ici est plutôt celui de la
  « rafle stricte » ou « pions capturés non retirés en cours de rafle ».
  À vérifier auprès de la convention Dubois.
- [ ] 🟡 **L82** — « Le trait : indiqué par W (blanc) ou B (noir) en
  tête d'une notation FEN. » Le manuel utilise ensuite parfois « les
  blancs / les noirs » (avec majuscule, ex L62), parfois « blanc / noir »
  (minuscule, L66, L168). Choisir une convention.
- [ ] 🟡 **L77 vs L79** — La notation FMJD officielle utilise `×`
  (×, U+00D7) ; le manuel mixe `x` (L75 « `31x22` ») et `×` (L233
  « `26-21 (17×28) 43×3` »). Harmoniser.
- [ ] 🟡 **L150-159 (§2.5)** — Le titre « Prise maximale (règle du
  nombre) » utilise deux dénominations en parallèle. Préciser laquelle
  est canonique FMJD (la règle s'appelle officiellement « **règle de la
  rafle majoritaire** » ou « **règle du nombre** » ; jamais « prise
  maximale » à proprement parler).

### 2.2 Niveau pédagogique

- [ ] 🟡 **L88-90** — Bloc de code FEN abstrait. OK pour un débutant si
  le bloc est explicité, ce qui est fait L92. Conforme au CADRAGE §4.14
  point 3.
- [ ] 🟡 **L94** — « `W:W31,32,K40:B7,K12,18` signifie ... » : exemple
  utile, mais aucune position de ce type n'est ensuite référencée dans
  les fixtures (toutes les positions du manuel ont des dames placées de
  façon spécifique). Acceptable comme exemple pédagogique abstrait.
- [ ] 🟡 **L75-78** — Le manuel décrit la notation « cd-cf » et « cd×cf »
  sans dire à quoi sert le `(...)` qui est introduit L79-80 puis utilisé
  immédiatement L233 dans `(17×28)`. Ordre pédagogique correct : les
  conventions sont posées avant les exemples, mais le lecteur découvre
  les parenthèses avant d'avoir compris pleinement.
- [ ] 🟡 **L162-170 (§2.6 — promotion)** — Le concept « non-soufflage
  de la dame » est nommé sans glossaire ; pour un débutant, l'expression
  est complètement opaque. Ajouter une note de bas de page ou définition
  inline.

### 2.3 Mise en forme markdown

- [ ] 🟡 **L268-270** — Double saut de ligne avant `---` (ligne vide
  L267 + L268 + L269 + L270). Esthétique mineure.
- [ ] 🟡 **L417, L508-509** — Tableau Scan §7.3 utilise la convention
  des emojis 🔴 dans le texte (`🔴 **À vérifier (rédacteur humain)**`).
  Conforme au reste du document, mais à transformer en composant
  d'avertissement plus standard si publication finale.
- [ ] 🟡 **L444 vs L498 vs L508** — Trois encarts 🔴 « À vérifier » de
  niveau de criticité variable. Manque une légende unique en début de
  chapitre.
- [ ] 🟡 **L416-418, L425-426** — Préfixe `>` pour les blocs « Position
  de départ » : convention bonne, mais inconsistante (utilisée seulement
  en §7.1 et §7.2). Les autres chapitres devraient adopter le même
  format ou aucun.
- [ ] 🟡 **L556-557 (entre ch8 et ch9)** — Double séparateur `---`
  (lignes 555-558) + ligne vide. Coquille mineure.

### 2.4 Cohérence avec les sources documentées

- [ ] 🔴 **L595-596 (§9.4 — `BEG_CH09_007`)** — « la solution publiée
  Dubois ne se reconstruit pas avec la position extraite. Position
  contestée, voir `BLOCAGES.md`. » → **OBSOLÈTE** : `BLOCAGES.md`
  indique le blocage **résolu** (R009, coquille `43-38`→`38-32`
  corrigée). La fixture a maintenant `final_move` valide et
  `published_notation` corrigée. À reformuler en « coquille PDF
  corrigée — cf R009 ».
- [ ] 🔴 **L628-629 (§10.4 — `BEG_CH10_008`)** — Idem : « mismatch
  position/solution, voir `BLOCAGES.md` » → résolu (R010). À mettre
  à jour.
- [ ] 🔴 **L721-722 (§13.3 — `BEG_CH13_004`)** — Idem : « solution
  publiée entièrement décalée par rapport à la position extraite, voir
  `BLOCAGES.md` » → résolu (R011). À mettre à jour.
- [ ] 🟠 **L791-793 (§15.4)** — « `BEG_CH15_001` (Dubois D1) contient
  une coquille typographique dans le PDF (`(19x19)` au lieu d'une
  notation valide). La reconstruction a néanmoins réussi en interprétant
  la suite logique de la position. » — Pas dans la liste des 6
  coquilles documentées (R002, R004, R006, R009, R010, R011). Le
  `claude_notes` de la fixture (`fixtures_debutant.py` L3880) confirme
  l'existence de la typo mais ne mentionne pas la « reconstruction
  réussie ». Vérifier la cohérence et clarifier dans l'annexe.

### 2.5 Sections sans correspondance fixture

- [ ] 🟠 **L411-417 (§7 introduction)** — « Chaque exercice ci-dessous
  est annoté à partir de la **variante principale (PV) calculée par
  le moteur Scan** ». Cette annonce vaut **uniquement pour CH07**.
  Reformuler : « les exercices du chapitre 7 sont annotés à partir du
  PV Scan » pour ne pas induire en erreur sur les autres chapitres.

---

## 3. Références croisées

### 3.1 « voir Ch. N » / « cf. §X »

- [ ] 🟠 **L322-323 (§5 intro)** — « approfondit le mécanisme déjà
  rencontré au chapitre 4 » : OK, le chap 4 traite bien envoi à dame +
  collage.
- [ ] 🟠 **L389-392 (§6.3)** — « **coup Philippe** — un coup nommé qui
  sera détaillé au chapitre 16. » : cohérent (CH16 = coup Philippe).
- [ ] 🟠 **L516 (§7.4)** — « Voir résolution R008 dans
  `RESOLUTIONS_debutant.md` » : R008 existe bien (`ad lib`).
- [ ] 🟠 **L552-554 (§8.3)** — « `BEG_CH08_011` ... est un coup de
  Talon — un coup nommé qui sera détaillé au chapitre 15. La formation
  blanche 31-36-37-41-46 est caractéristique. » : `BEG_CH08_011` fixture
  contient `claude_notes` mentionnant « formation 31-36-37-41-46 », **mais
  l'état réel** est `white_men={36, 37, 38, 41, 46, 24, 25, 29, 30, 31}` :
  il y a bien 31, 36, 37, 41, 46 + 38 + 24 + 25 + 29 + 30. La formation
  31-36-37-41-46 est bien présente. OK.
- [ ] 🟠 **L621-624 (§10.3)** — « `BEG_CH10_009` (Dubois D7) est un
  **coup Napoléon** — `28-22 (17×28) 27-21 (16×27) 31×24` — qui sera
  détaillé au chapitre 13. » : OK, fixture trouvée.
- [ ] 🟠 **L654-658 (§11.2 — Préview Trappe)** — « `BEG_CH11_008`
  (Dubois D5, Michiels-Marini 1986) et `BEG_CH11_009` (Dubois D6) sont
  des **coups de la Trappe** — chapitre 14. » : Les fixtures
  `BEG_CH11_008` et `BEG_CH11_009` ont theme=`coup_de_trappe` (vérifié
  fixtures_debutant.py L3030, L3053). OK.
- [ ] 🟠 **L800-803 (§16 intro)** — « (déjà été abordé au chapitre 6
  (`BEG_CH06_002`) sous sa forme la plus élémentaire) ». La fixture
  `BEG_CH06_002` a theme=`coup_philippe`. OK.

### 3.2 Annexe A — Index des coups nommés

- [ ] 🟠 **L876-892 (Annexe A)** — Tableau « Coup royal » : ligne
  présente dans l'index avec « (chap général) » mais aucune section du
  manuel ne traite explicitement le coup royal. Or `BEG_CH04_006` a
  theme=`coup_royal` et est mentionné en chap 4 → l'index dit « — »
  pour « chapitre principal » alors qu'on pourrait pointer ch 4.4 (ou
  signaler explicitement que le coup royal est traité dans le manuel
  Intermédiaire).
- [ ] 🟠 **L880** — « Coup de Mazette » index dit « (introduit ch3,
  ch16) — pas de chapitre principal ». Cohérent avec ce que dit le
  manuel (§3.3 et §16.4 mentionnent Mazette en passant). À noter pour
  la conclusion : la conclusion L860 dit « plus Mazette (introduit en
  passant) ». OK, cohérent.
- [ ] 🟠 **L884** — « Coup de Rappel ... Aperçus dans ch14 » — Vérifier
  que CH14 traite réellement du Rappel. Lecture CH14 (L726-755) : aucune
  mention de Rappel. **À corriger** : ce qui est traité en CH14
  comme aperçu c'est plutôt « combinaisons à 7 demi-coups » ; pour le
  Rappel l'aperçu vient plutôt de CH18 D2 Dubois = `BEG_CH14_002` qui a
  theme=`coup_rappel`. À vérifier l'annexe.
- [ ] 🟠 **L885** — « Coup Renversé ... Aperçus dans : — » — alors que
  le coup Renversé apparaît en aperçu en chap 12 D7 (`BEG_CH12_007`,
  « combinaison avec temps de repos », theme=coup_renverse). OK la ligne
  pointe vers ch 12 comme chapitre principal donc l'aperçu n'est pas
  applicable. OK.
- [ ] 🟠 **L886** — « Coup Napoléon ... Aperçus dans ch10 (D7) ». OK,
  `BEG_CH10_009` (=ch14 Dubois D7) a theme=`coup_napoleon`. OK.
- [ ] 🟠 **L887** — « Coup de la Trappe ... Aperçus dans : ch11 (D5,
  D6), ch12 (D5) ». OK les 3 fixtures (`BEG_CH11_008`, `BEG_CH11_009`,
  `BEG_CH12_005`) ont theme=`coup_de_trappe`. OK.
- [ ] 🟠 **L888** — « Coup de Talon ... Aperçus dans ch8 (D9) ». OK,
  `BEG_CH08_011` a theme=`coup_de_talon`. OK.
- [ ] 🟠 **L889** — « Coup Philippe ... Aperçus dans ch6 (D1) ». OK,
  `BEG_CH06_002` a theme=`coup_philippe`. OK.
- [ ] 🟠 **L890** — « Coup parallèle ch12 (D8) ». OK, `BEG_CH12_008`
  a theme=`coup_parallele`. Mais : `BEG_CH07_012` aussi est cité dans
  le manuel comme « coups parallèles » L1992 du fichier fixtures
  (« title='Dubois ch8 D10 — Coups parallèles' ») → l'index pourrait
  mentionner aussi `BEG_CH07_012`.
- [ ] 🟠 **L891** — « Coup de chevron ch12 (D2) ». OK, `BEG_CH12_002`.
- [ ] 🟠 **L892** — « Coup turc ch16 (D1) ». OK, `BEG_CH16_001`.
  Mais « Coup turc » est aussi mentionné L283-285 (§4.1 « coup turc »)
  pour décrire `BEG_CH04_001` et `BEG_CH04_002`. À enrichir l'index.

### 3.3 Index — coups nommés manquants

- [ ] 🟠 **Annexe A** — Coups mentionnés dans le corps du manuel mais
  ABSENTS de l'index :
  - **coup_de_dame** (utilisé dans plusieurs concepts, ex
    `BEG_CH10_004` « coup de dame en 4 »)
  - **gambit** (chap 6.2 mentionne « gambit » L385, et `BEG_CH06_005`
    a theme=`gambit`)
  - **temps_de_repos** (chap 7 entier, mais ce n'est pas un « coup
    nommé » au sens strict — peut-être à séparer dans une section
    « mécanismes »)
  - **prise_majoritaire**, **collage**, **points_de_contact**,
    **envoi_a_dame**, **creation_temps_de_repos** : également des
    mécanismes fondamentaux, à indexer dans une section dédiée si
    l'annexe se veut exhaustive.

### 3.4 IDs de fixtures cités dans le manuel — existence

Vérification : **tous les `BEG_CHnn_mmm` cités dans manuel_debutant.md
existent bien dans fixtures_debutant.py** (script grep + comparaison
avec les 166 IDs). Aucun ID fictif.

- [ ] ✅ Aucun ID fictif détecté.

### 3.5 Numéros de chapitres / sections

- [ ] 🟡 **L29-44 (sommaire)** — Sommaire en 16 chapitres, conforme au
  contenu (chapitres 1 à 16). OK.
- [ ] 🟡 **L46-49** — « Les chapitres 1 et 2 posent le vocabulaire,
  les chapitres 3 à 8 introduisent les **mécanismes fondamentaux**, les
  chapitres 9 à 16 détaillent les **coups nommés** ». La conclusion
  L856-861 énumère « 8 mécanismes fondamentaux : prise majoritaire,
  collage, envoi à dame, gambit, points de contact, temps de repos,
  création de temps de repos, coup parallèle » → mais le coup parallèle
  est traité en CH12 (donc dans la zone « coups nommés »). À harmoniser.
- [ ] 🟡 **L46-49** — « les chapitres 3 à 8 introduisent les mécanismes
  fondamentaux » → CH4 traite du collage **et de l'envoi à dame
  combiné**, CH5 traite de l'envoi à dame seul. Frontières CH4/CH5
  pourraient être clarifiées.

### 3.6 Références hors-manuel

- [ ] 🟠 **L516, L920, L922** — Références à `RESOLUTIONS_debutant.md`,
  `BLOCAGES.md`, `A_VERIFIER_MOTEUR.md` — fichiers internes au cycle
  Débutant. Pour un manuel à publier hors-équipe, ces références
  deviennent opaques. Soit on les externalise dans une annexe « bug
  reports résolus », soit on les retire.
- [ ] 🟠 **L904-905 (Annexe C)** — « PR #31, mai 2026 » : référence
  à une PR GitHub privée. Pour publication externe, à reformuler.
- [ ] 🟠 **L928 (footer)** — « le framework `dilf` (Draught Intelligence
  Learning Framework) » — sigle expansé OK, mais le lecteur lambda ne
  sait pas où trouver dilf. Lien GitHub utile.

---

## 4. Complétude vs CADRAGE

### 4.1 Sections requises par CADRAGE_MANUELS.md

CADRAGE §2 demande 3 livrables par niveau :
- ✅ `manuel_<niveau>.md` — présent (le fichier audité)
- ✅ `fixtures_<niveau>.py` — présent (166 fixtures)
- ❌ `sources_<niveau>.md` — **ABSENT** dans le dossier
  pre_process_corpus. L'annexe B du manuel (L894-899) tente d'y suppléer
  mais elle est très minimaliste (4 lignes). Le cadrage demande explicitement
  une « table de traçabilité : pour chaque position, l'origine exacte
  (PDF + page, ou "connaissance générale Claude"), et son statut de
  vérification ». **Cette table n'existe pas** — info présente dans
  les fixtures (`source_ref`, `crop_id`, `verified`) mais pas exposée
  au lecteur sous forme de table.

### 4.2 Garde-fou de publication §4.6

- [ ] 🟠 **L17, L867-870** — Le manuel mentionne « chaque exercice est
  donc directement testable au damier informatique » mais ne dit pas que
  **toutes les fixtures sont `verified=true`** suite au passage Scan
  (information cruciale par rapport au cadrage §4.6 — historiquement,
  c'était bloquant). À mentionner dans la préface ou la conclusion.

### 4.3 Conclusion + 4 annexes

- ✅ **L848-870 — Conclusion** : présente, donne un bilan correct (8
  mécanismes + 8 coups nommés).
- ✅ **L876-892 — Annexe A (Index des coups nommés)** : présente, mais
  voir §3.3 ci-dessus pour ajouts.
- 🟠 **L894-899 — Annexe B (Sources)** : très minimaliste. Devrait
  inclure la statistique CORPUS/GENERAL/INVENTED, le statut
  `verified=true` Scan, le nombre de coquilles PDF détectées, les
  références aux RESOLUTIONS.
- 🟠 **L901-910 — Annexe C (Notation Dubois)** : OK pour le minimum
  vital. Manque la liste des conventions §4 d'`ETAT_DILF.md` (`(ad lib)`
  est mentionné, mais pas `+1p`, `+2p`, `etc.`).
- 🟠 **L912-922 — Annexe D (Statistiques)** : globalement cohérente
  mais :
  - L915 dit « 12 de connaissance générale (7 %), 2 inventées (1 %) »
    → total 14, cohérent avec L25.
  - L917 « 132 positions ont une notation complète reconstruite (79 %) »
    → ETAT_DILF.md §7 dit 135/166 (81%). Divergence de 3
    (les 3 blocages R009/R010/R011 ont été résolus depuis et leurs
    final_move sont reconstruits). À mettre à jour : 135 et 81%.
  - L918 « 34 positions ont `final_move=None` » → confirmé par
    fixtures (166 - 132 = 34, mais 166 - 135 = 31). À mettre à jour.
  - L920 « 3 blocages structurels documentés pour résolution ultérieure »
    → faux, **les 3 blocages sont résolus** (BLOCAGES.md). À corriger.
  - L921 « 3 coquilles PDF détectées et corrigées » → faux, **6
    coquilles** détectées (R002, R004, R006, R009, R010, R011). À
    corriger.
  - L922 « 8 résolutions consignées » → faux, **11 résolutions**
    (R001-R011 dans RESOLUTIONS_debutant.md). À corriger.

### 4.4 Couverture des thèmes pédagogiques (CADRAGE §4.9)

- [ ] 🟠 Le manuel mentionne 28 thèmes pédagogiques distincts (cf
  ETAT_DILF.md / JOURNAL.md fin de session production). Le CADRAGE §4.9
  liste un noyau initial à enrichir. L'annexe ne donne pas la table
  thèmes / fixtures. Optionnel mais aiderait le moteur du framework
  (`pedagogy/`) à indexer les exercices par thème.

### 4.5 Validation moteur globale (CADRAGE §4.6)

- [ ] 🟠 Le manuel ne signale nulle part que **toutes les 166 fixtures
  ont passé `validate_final_moves.py`** (cf JOURNAL.md fin de session)
  ET que **toutes les 166 fixtures sont `verified=true` au Scan**. C'est
  pourtant l'information clé pour le lecteur : il étudie un manuel dont
  les combinaisons sont validées par un moteur. À expliciter en préface
  et en annexe D.

### 4.6 Cohérence prose / fixture (CADRAGE §4.14)

- [ ] 🟠 Le CADRAGE §4.14 point 4 demande que
  `validate_prose_vs_fixtures.py` ait été lancé. Le journal mentionne
  qu'il l'a été plusieurs fois pour CH02, CH07, etc. Il faudrait
  consigner dans le manuel (ou en annexe technique) le résultat final
  de la dernière exécution. Idéalement, intégrer ce script dans une
  étape CI / pre-commit (mais ça dépasse le périmètre du manuel).

### 4.7 Mode Scan « zéro invention » (CADRAGE §0)

- [ ] 🔴 **Défaut systémique** — le CADRAGE §0 (prime sur tout)
  exige que le commentaire tactique soit rédigé À PARTIR du PV Scan,
  et JAMAIS d'une ligne reconstruite par Claude. Le manuel applique
  ce protocole **uniquement au chapitre 7** (CH07_001, CH07_002, et le
  tableau §7.3). Tous les autres chapitres (3-6, 8-16) rédigent la prose
  comme avant le recadrage de mai 2026, sans citation Scan.
  **Implication** : le manuel est en pratique non-conforme au principe
  directeur du cadrage. Soit on aligne tous les chapitres sur le pattern
  CH07, soit on assume explicitement (préface) que les chapitres 3-6 et
  8-16 sont en mode « rédaction héritée pré-cadrage zéro-invention » et
  qu'une passe future ré-écrira ces chapitres en mode Scan. **Item
  bloquant pour la clôture du cycle** selon le sens du cadrage.

---

## Synthèse

- **Items critiques (bloquants pour clôture)** : 29
  - Tous concernent la section 1 (zéro-invention) + 4.7 + 3 références
    obsolètes BLOCAGES.md (L595, L628, L721).
- **Items normaux** : 27
- **Items mineurs** : 15
- **Total** : 71 items
- **Vérifications passées sans réserve** : tous les IDs de fixtures
  cités dans le manuel existent, le sommaire et la conclusion sont
  cohérents en nombre de chapitres, l'annexe C couvre l'essentiel
  notation Dubois.

### Top-3 findings les plus critiques

1. **Le manuel viole le principe directeur §0 « ZÉRO INVENTION »** :
   il ne cite le PV Scan que dans le chapitre 7. Les 14 autres chapitres
   tactiques rédigent les verdicts (`« ramasse 5 pions et promeut »`,
   `« libère la rafle finale »`, `« 5 captures dont coup turc par 14 »`)
   sans aucune citation, alors que les 166 fixtures sont `verified=true`
   au Scan depuis la production de `scan_analysis_debutant.json`. C'est
   **le défaut systémique** du livrable.

2. **Divergence Scan non flaggée — `BEG_CH15_004`** (L770-774) : la
   `published_notation` annonce `34-29` comme premier coup, mais le PV
   Scan recommande explicitement `33-29` (notes Scan : « DIVERGENCE:
   published_notation starts with '34-29', Scan PV starts with '33-29' »).
   Le manuel suit Dubois sans alerter le lecteur — qui va donc apprendre
   une combinaison sous-optimale. Cas similaire pour `BEG_CH10_002`,
   `BEG_CH11_005`, `BEG_CH12_008`, `BEG_CH13_002`, `BEG_CH14_007`,
   `BEG_CH15_003`, `BEG_CH16_009`, et toutes les fixtures « trait aux
   noirs » avec parenthèses (CH09_004, CH09_005, CH09_006, etc.). Au
   total, **38 divergences flaggées par Scan** dont au moins 8 vraies
   substitutions de coup, et **aucune n'est mentionnée dans le manuel**
   en dehors du chapitre 7.

3. **Annexe D « Statistiques » obsolète** (L912-922) : 4 chiffres sur
   6 sont faux (132 au lieu de 135 final_move ; 34 au lieu de 31
   final_move=None ; 3 au lieu de 6 coquilles PDF ; 8 au lieu de 11
   résolutions) ; les 3 blocages annoncés « pour résolution ultérieure »
   sont tous résolus (R009/R010/R011) — info reprise erronément aussi
   L595, L628, L721. C'est la dernière section du manuel ; un lecteur
   technique va y chercher ses repères et trouvera des nombres
   contradictoires avec les fichiers du projet.

### Recommandation globale

**Refactoring nécessaire avant clôture du cycle Débutant.** Le manuel
livre une structure de qualité, une bonne table des matières, et un
exemple-pilote propre (chapitre 7) qui montre comment le reste doit
être rédigé. Mais le **gap entre la promesse du cadrage §0 et la
rédaction effective des chapitres 3-6 + 8-16** est trop large pour
qu'une simple passe de coquilles suffise. Plan suggéré, du plus urgent
au plus accessoire :

1. **(Bloquant, ~1 j)** Mettre à jour les sections obsolètes :
   §9.4, §10.4, §13.3 (les 3 blocages sont résolus), §15.4 (coquille
   `(19x19)` à intégrer aux 6 coquilles globales), et l'annexe D
   (statistiques). Préface : remplacer « 14 inventées ou règles » par
   « 12 GENERAL_KNOWLEDGE + 2 INVENTED ».
2. **(Bloquant, ~2 j)** Réécrire les 14 chapitres tactiques (CH3-6,
   CH8-16) en alignant sur le pattern CH07 : pour chaque fixture
   commentée, citer le PV Scan (`scan_analysis_debutant.json`),
   l'éval `eval_after_pv`, et la profondeur. Flaguer explicitement les
   8 vraies divergences premier-coup. Les emojis 🔴 « à vérifier » du
   chap 7 doivent disparaître (toutes les fixtures sont
   `verified=true`).
3. **(Bloquant, ~0.5 j)** Produire le `sources_debutant.md` manquant
   (table CORPUS/GENERAL/INVENTED × fixture × verified).
4. **(Confort, ~0.5 j)** Harmoniser la notation (×/x), enrichir
   l'annexe A avec les mécanismes (gambit, prise majoritaire, collage,
   etc.), corriger le terme « non-soufflage » §2.6 vs §2.8.
5. **(Confort, optionnel)** Externaliser les références internes
   (BLOCAGES.md, RESOLUTIONS, PR #31/#32) dans une annexe technique
   séparée si le manuel est destiné à publication hors-équipe.

**Verdict** : pas prêt à publier en l'état. Compter **3-4 jours de
patch** pour traiter les 29 items critiques + les statistiques
obsolètes. Si l'option « refactor Scan-cité de tous les chapitres » est
écartée par l'utilisateur (= acceptation explicite que la prose reste
en mode pré-cadrage), l'effort tombe à **1.5 j** pour les seuls items
factuels (statistiques, blocages résolus, divergences `BEG_CH15_004` et
les 7 autres premier-coup).
