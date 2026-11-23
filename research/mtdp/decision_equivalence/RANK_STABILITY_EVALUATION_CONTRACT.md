# D1-D — contrat d'évaluation des rangs, version 1 (pré-enregistrement)

Statut : **protocole uniquement, aucune cohorte admise ni mesure produite**. Ce document complète les gardes D1-C ; il ne réinterprète pas les 61 paires PC Blues, les 78 cibles réservées ni les anciens benchmarks Jass comme nouveaux tests.

## Unité, séparation, absence de fuite
- Une observation est une **position cible**, avec `source_id/event_id/game_id/ply/FEN`, ensemble canonique de coups légaux, scores Scan par action et empreintes du manifeste et du moteur. Une partie (et ses positions) appartient à une seule partition. Les doublons FEN entre partitions sont exclus ou regroupés avant gel ; les événements réservés fFgE7oED, P1RUlfJc, s7ahYqL4, D9PF2OSW restent exclus.
- Geler **avant scores cibles** les sources, ordre des positions, hachages, partitions, signatures L/LCB/structurelles, règles de repli tactique, budgets, critères ci-dessous et version du code. Ne sélectionner aucune signature ni seuil sur le test.
- Un PASS de garde interne ne vaut pas authentification externe : sans reçu source/partie/événement/ply vérifiable et exclusion historique complète, **aucune estimation hors-échantillon ne peut être qualifiée de confirmatoire**.

## Définition des actions et métriques
- Les actions sont des clés canoniques FMJD complètes, y compris prises multi-chemins ; si la correspondance DILF/Jass est ambiguë, **exclure et comptabiliser** le cas plutôt que fusionner des actions. Une signature commune n'implique ni mêmes successeurs ni même meilleur coup, encore moins équivalence minimax.
- `top1` : taux où l'action proposée appartient à l'ensemble des optima Scan **ex aequo**, selon la tolérance de score gelée avant test ; publier aussi l'exactitude sans tolérance. `top3` : taux où l'un des min(3, nombre légal) coups proposés appartient aux optima. Publier séparément la couverture des positions à au moins 3 coups légaux.
- Regret d'une proposition = meilleur score Scan légal moins score Scan de l'action, dans une orientation fixée pour le joueur au trait ; regret du top3 = minimum des regrets des trois actions. Rapport en unités natives Scan et, **seulement si conversion documentée**, en centipions. Publier moyenne, médiane, p95, maximum et proportion de regrets au-dessus du seuil tactique préenregistré ; ne pas transformer des scores moteur en vérité minimax.
- Concordance des rangs : Kendall tau-b avec gestion des ex aequo, calculé seulement sur les actions communes et rapporté avec dénominateur ; cas <2 actions comparables = non défini, pas un accord parfait. Publier top1/top3, taux de transfert valide, couverture, collisions, taux de repli tactique, compression et changement de classe W/D/L selon seuils gelés.
- Les positions d'une même partie ne sont pas indépendantes : IC bootstrap 95 % par **rééchantillonnage de parties entières**, graine et nombre de réplications fixés avant test. Afficher nombres de parties et événements, et analyse de sensibilité leave-one-event-out si assez d'événements.

## Témoins, décision, abandon
- Comparer sur **exactement les mêmes positions** L, LCB, ordre légal canonique, signatures progressives et hasard déterministe (graine gelée). Évaluer l'ordonnancement en conservant **tous** les coups ; ne pas attribuer un gain au simple fait de proposer trois coups si les autres sont supprimés.
- Critère d'accès au benchmark Jass : aucun échec de sécurité tactique dans les cas de repli exact ; IC par partie de la différence de regret top1/top3 vs LCB ne montrant pas de dégradation au-delà de la marge **fixée et justifiée avant dégel**, avec couverture et compression utiles. Si la marge, le nombre minimal de parties ou le seuil tactique ne sont pas gelés : statut **exploratoire uniquement**, pas de feu vert D1-E.
- Abandonner ou redessiner la signature si elle n'améliore pas LCB hors-échantillon, si les collisions avec successeurs divergents produisent des erreurs tactiques non récupérées, ou si le coût de calcul de signature annule l'économie de nœuds. Consigner tous les contre-exemples, y compris ceux où top1 coïncide mais les autres rangs divergent.
- D1-E, uniquement après admission : moteur Jass épinglé et jetable, budgets totaux **10k/50k/200k nœuds frais inclus**, TT/seed/temps/positions appariés, ordre natif vs ordre D1 vs témoin légal. Une éventuelle sélectivité exige un bras séparé avec recherche de contrôle et vérification tactique, jamais une inférence à partir du seul top3.

## État de preuve
Ce contrat est testable, mais **aucun seuil numérique de non-infériorité n'est fixé ici** faute d'étalonnage indépendant ; il doit être préenregistré sur entraînement seulement avant toute ouverture du test. Aucune campagne Scan/Jass n'a été lancée par ce document.
