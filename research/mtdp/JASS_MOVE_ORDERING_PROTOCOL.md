# MTDP — protocole préenregistré du benchmark Jass à budget de nœuds apparié

Statut : **protocole scientifique préenregistré ; prévalidation mécanique Jass implémentée et exécutée ; benchmark sur cohorte indépendante non exécuté**. Aucun gain de force ni de vitesse n'est établi.

La [prévalidation Jass](jass_preflight/README.md) utilise quatre positions artificielles, trois bras et 36 recherches avec plafonds de nœuds. Deux sorties identiques sont archivées ; le moteur est épinglé à `cfe07fce6385b980553a898e9651d53419589ebc`. Elle ne valide **ni** les classements Scan transférés, **ni** la correspondance des identifiants de coups DILF/Jass, **ni** les gains de recherche. Les [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43111437276) et [tests FMJD/PC Blues](https://github.com/jfrancoiscollin/dilf/actions/runs/43111437195) du commit `107e6ce` réussissent ; le préflight Jass n'est pas exécuté par ces workflows.

## Question et critère principal

L'ordre de recherche des trois premiers coups légaux recommandés par transfert depuis une autre position à signature MTDP identique améliore-t-il la qualité du choix de Jass à **budget fixe de nœuds**, comparé à l'ordre natif et à un ordre témoin indépendant de Scan ?

Un résultat positif sur le classement Scan ne suffit pas : la comparaison doit porter sur des **recherches Jass réellement exécutées**, sur les mêmes positions et budgets.

## Cohorte indépendante et gel avant calcul

1. Sélectionner de nouvelles parties FMJD non présentes dans PC Blues, les 40 paires du premier holdout ou les 241 parties du tournoi rapide déjà explorées. Dédupliquer les FEN et exclure les positions terminales et les positions dont les coups légaux ne sont pas reproductibles par l'adaptateur.
2. Geler les fichiers PDN, SHA-256, version de l'adaptateur FMJD, version et paramètres du binaire Scan 3.1, version/commit Jass, graine de sélection, liste ordonnée de FEN cibles et leurs ensembles de coups légaux.
3. Pour chaque cible, sélectionner la source **sans utiliser les évaluations Scan de la cible**. Source autorisée uniquement si signature MTDP de base et ensemble canonique de coups légaux sont identiques ; préciser le filtre rayon deux en analyse secondaire. Fixer une règle déterministe de départage (identifiant source, FEN lexicographique) ; ne pas chercher la meilleure source après avoir vu les résultats.
4. Publier avant exécution le nombre de cibles candidates, couvertes et exclues ; les cibles sans source sont rapportées, non remplacées a posteriori.

## Trois bras, mêmes conditions

- **Natif** : Jass inchangé.
- **Transfert top-3** : placer en tête les trois coups source ordonnés par Scan profondeur 12, puis laisser Jass rechercher **tous** les autres coups légaux.
- **Témoin top-3** : placer en tête les trois premiers coups dans l'ordre canonique des coups légaux (path, captures, promotion), puis rechercher tous les autres coups.

Les trois bras utilisent exactement le même FEN, le même moteur/commit, la même évaluation, les mêmes règles FMJD, la même graine, le même nombre maximal de nœuds, le même nombre de threads et la même politique de table de transposition. Une table neuve ou réinitialisée est obligatoire pour chaque bras ; l'ordre d'exécution des bras doit être permuté de façon déterministe. Désactiver les caches persistants ou documenter leurs états initiaux. L'implémentation doit prouver que l'ordre imposé est réellement utilisé à la racine et ne court-circuite pas les autres coups.

## Budgets et métriques préspécifiés

Budgets : **10 000, 50 000 et 200 000 nœuds** par cible et bras, sous réserve de faisabilité mesurée. Ne pas changer les budgets après inspection des résultats. Enregistrer nœuds effectivement consommés, profondeur entièrement terminée, temps mur, meilleur coup, valeur de recherche, PV, statut de fin (budget, terminal, erreur), et identifiant de build.

Critère principal : différence appariée de **regret Scan profondeur 12** du coup choisi par Jass, transfert moins témoin canonique, sur les cibles avec scores ordinaires valides. Un regret négatif favorise le transfert. Rapporter aussi transfert moins natif. Ne pas soustraire les scores catégoriels de victoire/défaite comme s'il s'agissait de centipions ordinaires : les traiter séparément. Résultats secondaires : couverture du meilleur coup Scan, fraction de cibles où le coup change, nœuds à profondeur complète égale, temps mur descriptif. Présenter les résultats par budget et par partie source, sans traiter les positions d'une même partie comme indépendantes.

## Contrôles et conditions d'arrêt

- Tests unitaires : mêmes ensembles légaux pour les trois bras ; top-3 stable avec ex æquo ; moins de trois coups ; captures/promotions ; source absente ; FEN terminal ; remise à zéro de TT ; limite de nœuds ; vérification des scores catégoriels.
- Tests d'intégration : sur quelques FEN, tracer les coups visités à la racine pour vérifier les trois ordres. Contrôler que chaque bras explore les mêmes coups autorisés et ne dépasse pas le budget hors tolérance explicitement documentée.
- Arrêter et classer le lot **invalide** si Jass n'expose pas de limite reproductible de nœuds, si l'injection d'ordre change les règles ou le générateur de coups, si les versions ne sont pas épinglées, si le corpus recoupe les jeux précédents ou si l'évaluation Scan est calculée après consultation des résultats Jass pour sélectionner les cibles.
- Si le budget distant gratuit ne suffit pas, interrompre avant tout coût payant et documenter précisément les besoins matériels. Ne pas supposer qu'un PC personnel est nécessaire.

## Artefacts à produire

`cohort-manifest.json` (SHA des sources, règles de sélection, FEN et exclusions), `jass-build-manifest.json`, `root-order-traces.jsonl`, `paired-results.jsonl`, `summary.json`, tests, commande exacte de reproduction, versions de dépendances et journal des échecs. Conserver les trois bras dans le même fichier pour empêcher un appariement ambigu.

## Interprétation

Un gain à budget égal serait une preuve expérimentale **sur cette cohorte et ces réglages**, pas une équivalence stratégique générale des signatures. La comparaison top-3 vs top-1 des rapports antérieurs est un diagnostic de couverture, **pas** un contrôle suffisant du bénéfice de l'ordre de recherche. Aucun chiffre du présent benchmark n'existe à la date de ce protocole.
