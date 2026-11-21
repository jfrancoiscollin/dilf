# MTDP-D1 — préenregistrement du corpus décisionnel indépendant (protocole, NON GELÉ)

Date : 2026-11-17 UTC. Statut : **protocole préalable**, aucun corpus D1 indépendant sélectionné, haché ou scoré par cette publication.

## Question et unités
Tester si les signatures L, LCB, Q et les extensions calmes prédites *sans scores cibles* permettent de transférer un ordre de coups entre positions FMJD 10×10 distinctes. Une égalité de coups légaux n'implique ni égalité des successeurs, ni même meilleur coup, ni équivalence minimax. Un transfert n'est évaluable que si les identités canoniques des actions sont injectives et que l'ensemble légal coïncide.

## Exclusions et gel avant toute évaluation
1. Inventorier les identifiants de parties, trajectoires normalisées, FEN exactes et empreintes des jeux déjà exploités (PC Blues historique, cohortes Scan profondeur 8/12, benchmarks Jass et leurs réplications, prospectif fFgE7oED). Les **78 cibles réservées fFgE7oED** et toutes les parties qui les contiennent sont interdites pour D1 ; ne pas les rééchantillonner.
2. Acquérir des parties de source et tournoi identifiés, non encore utilisées. Rejeter tout identifiant de partie, trajectoire normalisée ou FEN exact déjà observé dans les jeux interdits ; mettre en quarantaine les notations ambiguës, sans choisir arbitrairement une prise. Si le registre des exclusions n'est pas complet, **ne pas geler**.
3. Dédupliquer par trajectoire complète avant le découpage ; garder les positions chronologiquement dans chaque partie et documenter les FEN répétées. Partitionner par partie et, si possible, par tournoi entier ; aucune partie ni trajectoire apparentée ne traverse entraînement/validation/test. Fixer la règle de sélection et les graines avant de lire les scores Scan.
4. Émettre un manifeste immuable avec pour chaque entrée : source, tournoi, game_id, hash de trajectoire, ply, FEN, hash FEN, camp au trait, actions canoniques, versions FMJD/DILF/Scan, statut de correspondance DILF/Jass et exclusion. Émettre SHA-256 du manifeste, du registre d'exclusions, du script et des versions épinglées. Publier un commit de gel **avant** le premier scoring. Ne pas appeler « indépendant » un nouveau tirage de parties déjà utilisées.

## Hypothèses et métriques gelées
- H0 : la signature n'améliore pas la stabilité top-1/top-3 ni le regret par rapport à L/LCB et à l'ordre légal, à coût de représentation comparable.
- Primaires : taux de transfert valide (dénominateur : paires candidates avant filtre), concordance top-1, inclusion du meilleur coup cible dans top-3, regret de la meilleure action transférée en unités Scan déclarées, et transitions win/draw/loss ; garder les ex-aequo explicites.
- Secondaires : corrélation des rangs sur actions communes, fréquence des pertes tactiques graves (seuil préfixé avant scores), couverture, collisions, compression, temps et coût de calcul de signature.
- Rapporter les dénominateurs par signature, les échecs de correspondance et les cas tactiques avec fallback exact. Bootstrap **par partie**, jamais par paire dépendante, avec IC à 95 % et seed gelée ; analyse par tournoi tenu à l'écart.
- Comparateurs : L, LCB, Q, ordre légal canonique et hasard à seed fixée ; pas d'apprentissage des scores des cibles, pas de sélection du meilleur résultat sur le test.

## Décision avant expérimentation Jass
La simple compression n'autorise aucun élagage. Passer à un essai d'ordonnancement Jass seulement si le test hors échantillon montre simultanément : transfert valide sans ambiguïté, regret et erreurs graves non dégradés par rapport aux témoins, et IC par partie compatibles avec un bénéfice reproductible sur un tournoi tenu à l'écart. Si les critères ne sont pas démontrés, arrêter la progression vers Jass et publier les contre-exemples. Aucun seuil numérique opportuniste ne sera choisi après lecture des scores : fixer les marges et la taille minimale dans un addendum de pré-gel, avant calcul.

L'essai Jass éventuel doit conserver **tous** les coups légaux, épingler une version jetable, comptabiliser signature/lookup/contrôle et comparer natif, ordre légal et MTDP aux mêmes budgets totaux 10k/50k/200k nœuds. Toute sélectivité ultérieure nécessite une vérification tactique et une recherche de contrôle ; jamais de promesse d'équivalence minimax.

## État de preuve au préenregistrement
PC Blues historique : 1 750 FEN, LCB 1 709 clés, Q 1 712 clés, 61 paires communes et 3 LCB seules, selon [audit existant](PAIR_OVERLAP_RESULTS_2026-11-17.md). Ces observations ont déjà été étudiées ; elles sont **exclues comme validation indépendante**. Aucune cohorte nouvelle, aucun classement Scan D1 indépendant, aucun gain Jass mesuré.
