# Q3 — Préparation disponible et condition de reprise, 28 novembre 2026

État vérifié à la tête `6fb3f0779cb9c7412d75c9cbd145b36d3a69ad0a` : PR43 ouverte/draft, neuf contrôles de cette tête réussis, aucun job en cours/en attente, aucun échec technique à réparer. Les derniers commits ne contiennent pas de paquet candidat Q1/Q2 indépendant. Le diagnostic Q2 relatif à l’action reste une proposition, pas un candidat ayant franchi les gates.

## Ce qui est acquis pour Q3

| Préalable | Preuve fermée | Limite |
|---|---|---|
| Coût complet froid | Contrat et 87 tests CI ; `Q3_TOTAL_COST_PROTOCOL_2026-11-28.md` | Seuils prospectifs proposés, pas nouveau gel |
| Liaison au natif | 20 appels/200000 nœuds locaux+distants, sorties identiques, 110 tests ; `Q3_NATIVE_BINDING_RESULTS_2026-11-28.md` | Témoin technique unique, pas effet observateur causal précis ni gain de force |
| Setup du lot chaud | 126 tests et deux scénarios synthétiques ; `Q3_WARM_BATCH_CONTRACT_2026-11-28.md` | Pas de cache stratégique chaud Jass validé, payload != mémoire/codec complet |
| Grille coût/regret existante | 85 tests et neuf points/38 positions/31 propriétaires ; `Q3_ARCHIVED_BUDGET_QUALITY_RESULTS_2026-11-28.md` | Post-hoc : aucun point moins cher sans hausse moyenne observée face au natif 50k ; pas preuve générale d’absence de gain |

Dernier artefact de grille 15271061875/run 46164508676 : ZIP 20403 octets SHA-256 4990f2243162757110cca0390db7ea7b2f6558429989ae48f79dcf60465b9e20 vérifié et conservé dans le dépôt. Aucun de ces reçus ne prouve minimax/WDL exact ou non-infériorité sur un nouveau corpus. Scan reste une référence empirique. Les 114 contextes ou 342 cellules ne deviennent pas de nouvelles observations indépendantes.

## Blocage précis

Le prochain essai utile est une intégration réelle d’un **candidat Q1/Q2 validé indépendamment**, puis comparaison Q3 à qualité égale et à budget égal. Le dépôt ne fournit actuellement pas le paquet nécessaire. Augmenter les profils synthétiques, rejouer les arènes connues ou ajouter des points après lecture des scores ne remplace pas cette preuve. Aucun allumage du PC de Jeff, dépense ou changement de production ne résout ce manque scientifique.

## Paquet attendu pour reprendre H13

1. Définition/version/hash du candidat, caractéristiques et cache/modèle ; mapping explicite des actions et garde-fous tactiques/ambiguïtés avec fallback. La proposition Q2 relative à l’action seule ne suffit pas.
2. Reçus d’admission et d’exclusion authentifiés : sources brutes/licence/provenance, événements/parties et trajectoires/FEN canoniques, indépendance et partitions, couverture du registre historique et des quatre événements réservés. Les vérifications structurelles seules ne valent pas admission indépendante. Utiliser les gates D1 existants, sans les redéfinir ici.
3. Rapport de validation Q1/Q2 sur jeux indépendants avec référence, budgets et critères annoncés avant scores : optimum/ties, regret et catégories WDL traités distinctement, couverture/fallback et unité propriétaire. Ne pas convertir une tolérance choisie après résultat en préservation du meilleur coup.
4. Artefacts reproductibles et budget de construction/runtime du candidat pour brancher l’instrumentation : setup/cache/signature/lookup/vérification/fallback/recherche, nœuds réels et temps complet, conditions froid/chaud et TT explicites. Les métriques mémoire/codec restent à établir si une compression est revendiquée.

À réception : lire d’abord l’état distant et les travaux actifs ; vérifier les reçus avant de réserver un nouveau corpus. Fixer ensuite le protocole Q3 du candidat avant nouvelles références, commencer par ordonnancement conservant tous les coups, comparer au natif et conserver les échecs dans le dénominateur. Une éventuelle sélectivité nécessite une validation indépendante et une justification distinctes. Aucune fusion, dépense ou production autorisée par ce document.

## Coordination et décision

**Mettre H13 en attente de ce paquet, arrêter les répétitions sans nouveau déclencheur.** H:28/D1 conserve Q2 et l’admission fraîche, H:43 Q1. Aucun autre relais n’est suspendu par cette décision. Les cohortes et protocoles gelés, résultats négatifs, quarantaines et quatre événements exclus sont préservés ; aucune nouvelle réservation, signature, score ou campagne. La reprise utile dépend d’un nouveau paquet de preuve, pas d’un calcul plus long sur les mêmes données.
