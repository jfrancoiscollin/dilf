# MTDP — protocole préenregistré pour une évaluation prospective indépendante de Jass (brouillon)

**Statut :** proposition méthodologique, **non exécutée** ; aucune performance mesurée ou cohorte admise. Rédaction initiale : relais fondation H43 ; responsabilité du protocole prospectif Jass/Scan, des contrôles à budget égal et du gel des nouvelles cohortes : H13, selon `RELAY_COORDINATION.md`. Ne modifie pas les expériences ni les seuils de MTDP-D1.

## Question falsifiable
À budget de calcul égal, une politique Jass utilisant les caractéristiques spatiales MTDP choisit-elle des coups de regret inférieur à une politique Jass témoin, sur des positions jamais utilisées pour définir ou ajuster la politique ? La stabilité top-1/top-3 et le coût de calcul sont des résultats secondaires, pas des substituts à la qualité de décision.

## Séparation des données et gel préalable
1. **Avant tout calcul**, figer dans un manifeste versionné les SHAs de DILF, Jass, moteur arbitre, code d'échantillonnage, paramètres et seeds, ainsi que les identifiants des parties et la règle de déduplication des positions (FEN normalisée + joueur au trait).
2. Maintenir exclus de l'entraînement, du choix de seuils et de la validation D1 les tournois/événements réservés `fFgE7oED`, `P1RUlfJc`, `s7ahYqL4`, `D9PF2OSW` et leurs parties/FEN. Ce protocole ne les réaffecte pas à une cohorte prospective.
3. Sélectionner une cohorte **nouvelle**, indépendante des jeux utilisés pour construire les signatures et régler les hyperparamètres ; conserver la provenance des parties, les exclusions, les doublons et les erreurs de légalité. Ne jamais publier `score_blind=true` sans validation des champs imbriqués et d'un schéma fermé ; la résolution appartient à D1.
4. Geler **avant consultation des résultats** les critères d'admission, budgets, politique MTDP, politique témoin, arbitre, tests et conditions d'arrêt. Si un changement est requis, créer une nouvelle version du protocole et étiqueter la précédente comme exploratoire.

## Plan apparié
- Pour chaque position admise, exécuter les deux politiques sur le **même état**, avec la même limite de nœuds et, si applicable, plusieurs seeds préfixées. Randomiser l'ordre des politiques pour limiter les effets d'environnement.
- Rapporter les budgets historiques `10k/50k/200k` nœuds comme **strates de comparaison**, sans affirmer qu'ils sont optimaux. Enregistrer nœuds réellement visités, temps, profondeur et arrêts ; ne pas confondre budget nominal et coût réel.
- Obtenir une référence indépendante (analyse plus profonde et identique pour les deux coups candidats, ou arbitrage externe préspécifié). Si l'arbitre ne discrimine pas les coups, enregistrer une égalité/incertitude au lieu d'inventer un regret précis.

## Critères et analyses
**Critère principal :** différence appariée de regret `regret(MTDP) - regret(témoin)` dans l'unité native documentée de l'arbitre (négatif favorable à MTDP). Rapporter moyenne, médiane, distribution, intervalle de confiance par bootstrap **groupé par partie** (et non par position), effectif des parties/positions et valeurs manquantes. Ne pas présenter un résultat exploratoire comme significatif.

**Secondaires :** taux d'accord top-1, recouvrement top-3, stabilité entre seeds/profondeurs, nœuds et temps réellement consommés, taux d'égalité des coups et erreurs de légalité. Les résultats doivent être ventilés par budget et caractéristiques de position préspécifiées ; toute analyse a posteriori est explicitement exploratoire.

**Garde-fous :** audit des doublons entre groupes, séparation par partie et événement, vérification des coups légaux par moteur FMJD, absence de fuite de scores dans les entrées, empreintes SHA-256 des fichiers et sorties. Les échecs d'exécution ne sont jamais comptés comme décisions gagnantes.

## Décision et arrêt
- **Succès scientifique** seulement si l'intervalle de confiance du critère principal est entièrement favorable à MTDP **et** si la validité de l'arbitre, l'indépendance des données et les contrôles de provenance sont établis. Un seuil de taille d'effet minimale doit être fixé avant exécution, sans être choisi après observation.
- **Inconclusif** si l'intervalle inclut zéro, si les données sont insuffisantes ou si l'arbitre ne départage pas les coups.
- **Échec de validité / arrêt** en cas de fuite, collision entre cohortes, coups illégaux non résolus, absence d'artefacts, dépassement des ressources autorisées ou modification non préenregistrée. Ne pas extrapoler à la force en match sans tournoi prospectif dédié.

## Livrables attendus (non produits à ce stade)
Manifeste de préenregistrement ; cohorte et rapport de légalité/déduplication ; sorties par position et seed ; rapport statistique groupé par partie ; empreintes SHA-256 ; note de décision distinguant hypothèses, mesures et conclusions. **Aucune expérience, dépense, fusion ni déploiement n'est autorisé par ce document.**


## Portes d'exécution H13 et articulation avec D1 — 19 novembre 2026

Ce texte et `prospective_manifest.validate` sont un **brouillon de conception et un contrôle de métadonnées**, pas un gel scientifique exécutable. Un SHA bien formé ne démontre ni existence, ni contenu, ni publication antérieure aux scores. Aucun manifeste réel ni nouvelle cohorte n'est admis ici. Le contrôle refuse les identifiants entourés d'espaces et exige des budgets de type entier ; ces contrôles ne prouvent pas l'indépendance du contenu.

Avant une campagne, H13 doit publier une version d'exécution concrète après qualification indépendante du candidat D1. Elle doit fixer sans consulter de nouvelles cibles :

- Le candidat et son code, les comparateurs, la référence et ses empreintes binaires/évaluation/configuration, les règles d'éligibilité et de sélection, les positions/parties/propriétaires/événements, l'effectif justifié et les exclusions de toutes données antérieurement scorées. D1 garde signatures, top-K, raffinement et dimension ; ses seuils et portes d'évaluation restent inchangés. Les champs cibles imbriqués et le schéma d'admission D1 restent à traiter par D1.
- Un **budget total** par bras : recherche principale **plus** prérecherche, sondes et vérifications en nœuds. Mesurer séparément le coût des caractéristiques et les autres coûts en temps sans les assimiler à zéro nœud. Garder tous les coups légaux ; journaliser toutes tentatives, dépenses, arrêts, erreurs et plafonds. Toute comparaison supplémentaire à nœuds principaux égaux doit porter cette étiquette et rester distincte du critère à coût total égal.
- Un budget primaire unique, les deux sensibilités, une taille d'effet minimale et la règle de décision correspondante, le dénominateur apparié, le traitement des échecs/plafonds et la règle d'arrêt. Le simple champ `minimum_effect` ne démontre pas que ces choix sont figés ou appliqués par une analyse.
- Une référence identique et fixée pour **tous les coups légaux** de chaque cible, avec scores, égalités et catégories conservés : le regret est meilleur score de référence moins score du coup choisi. L'arbitrage limité aux deux coups proposés ne fournit pas ce regret global et doit être nommé contraste entre coups. Ne soustraire numériquement que des scores ordinaires ; présenter séparément les transitions catégorielles. Les unités Scan brutes ne sont pas une valeur matérielle de pion calibrée.
- L'analyse et les tirages groupés avant ouverture des scores cibles : unités propriétaires complètes, regroupement/stratification par événement préspécifiés, dénominateurs et graines fixes, traitement explicite des tirages indéfinis (sans suppression ni nouveau tirage silencieux), tous cas et catégories conservés. Publier les décisions brutes avant réconciliation cible et vérifier l'ascendance distante des engagements.

Les contrôles déjà achevés sur 114 contextes/38 cibles/31 propriétaires restent post-hoc pour toute réutilisation ; ils ne peuvent devenir le nouveau holdout. Les quatre événements entiers réservés et toutes leurs parties/FEN restent exclus. H13 réserve toute future cohorte dans le registre **avant acquisition/scoring**, après contrôle d'absence de campagne équivalente ; H43 ne crée pas de campagne concurrente. Aucun nouveau calcul moteur n'est requis pour cette clarification. La prochaine porte reste la validation FMJD et la qualification indépendante D1, puis le protocole d'exécution concret H13.

## Appel explicite des populations top-3 — 20 novembre 2026

Pour un résultat top-3 préspécifié sur la population à au moins quatre coups légaux, appeler le pont D1 avec `metric="recall_at_3", top3_population="fixed_n_ge_4"`. Le mode `conditional_informative` reste un diagnostic secondaire, explicitement étiqueté ; ne jamais associer son intervalle au point de la population fixe. L'audit synthétique v2 (`validation/paired-estimand-audit-v2-2026-11-20.json`) vérifie les deux appels et l'accord du mode fixe avec un calcul de contrôle groupé par partie.

Cette précision concerne l'analyse top-3. **Le critère principal de la future expérience Jass reste la différence de regret à budget total égal.** Elle ne change ni les seuils D1, ni les études figées, ni l'admission des données. Le regroupement, les strates, les graines et dénominateurs du protocole d'exécution devront encore être gelés après qualification indépendante ; aucun nouveau gel ou calcul moteur n'est autorisé par cet ajout.

## Précontrôle H13 des sources, avant la preuve D1 et tout gel — 20 novembre 2026

Le point d'entrée H13 `prospective_source_preflight.preflight_sources(rows, sources, engine, root=...)` compose les contrôles existants sans modifier les modules D1 : validation fermée du manifeste et authentification de tous les octets PDN, écran des quatre sources réservées sur **chaque export entier**, puis seulement preuve D1 sourceSHA:index→partie→FEN par rejeu légal. Toute correspondance réservée bloque le lot entier avant le premier appel au moteur de règles ; aucune partie n'est filtrée pour sauver le lot. Les étiquettes d'événement fournies par le manifeste ne peuvent pas libérer une identité réservée connue.

Le moteur de règles doit être le vrai FMJD épinglé pour une utilisation scientifique. Les mocks ne servent qu'à tester le raccord. La suite distante dédiée vérifie aussi ce parcours avec la révision réelle et n'autorise aucun saut de test.

Un résultat positif du précontrôle signifie seulement que les identités réservées connues n'ont pas été retrouvées et que la preuve D1 a réussi. **`independent_cohort_qualified=false`, `eligible_for_freeze=false` et `complete_historical_exclusion_registry=false` restent obligatoires.** Les autres corpus historiques, alias, trajectoires/FEN et la qualification indépendante doivent encore être réconciliés. Les anciennes APIs D1 restent inchangées : ce raccord est le parcours H13 à utiliser avant tout nouveau gel, pas une certification rétroactive de leurs appels antérieurs. Aucun score Scan/Jass n'est lu et aucune campagne n'est créée par ce précontrôle.

## Vue FEN du cache historique — 21 novembre 2026

Avant de revendiquer l'exclusion des FEN historiques connues, fournir le cache épinglé au précontrôle : `preflight_sources(..., historical_cache=PATH)`. La vue H13 normalise les deux côtés avec le canonicaliseur D1 ; elle ne réécrit pas le cache historique. Le rapport `validation/historical-fen-bridge-2026-11-21.json` confirme 47 104 différences d'ordre d'écriture sur 452 526 positions, sans différence d'état. Une simple comparaison de chaînes brutes serait insuffisante.

L'appel sans cache ne qualifie toujours aucune cohorte et marque le contrôle FEN historique absent. Ce raccord ne vérifie pas encore les empreintes de trajectoires complètes : leur définition historique et leur sérialiseur doivent être conservés lors de la comparaison. Le critère principal de regret à coût total égal, les seuils D1 et l'obligation de qualification indépendante avant gel restent inchangés.

### Raccord H13 des trajectoires complètes (2026-11-21)

Avec historical_cache fourni, le précontrôle H13 authentifie aussi le registre des 4 468 empreintes connues, après la preuve D1 source/index/position. Il rejoue chaque partie enregistrée entière une fois par source/index sélectionné et utilise exactement named_arena_replay.trajectory_fingerprint (FEN historiques dames d’abord, séparées par un seul saut de ligne, sans saut final). Toute correspondance exclut tout le lot. Une continuation illégale/ambiguë ne peut produire une empreinte de préfixe déclarée complète. Il s’agit de l’intégralité de la séquence enregistrée, pas d’une preuve que la partie atteignait un résultat terminal.

Le rapport historical_complete_trajectories_screened exige le cache épinglé ; l’ancien appel sans cache rapporte false. Les empreintes reçues du manifeste ne servent jamais de preuve. Les alias publics/notations, la complétude de l’historique et la provenance indépendante restent à réconcilier ; les drapeaux indépendance/exhaustivité/gel restent false même sans correspondance. Aucun score cible n’est acquis ; ces vérifications de provenance ne changent aucun budget Jass/Scan.
