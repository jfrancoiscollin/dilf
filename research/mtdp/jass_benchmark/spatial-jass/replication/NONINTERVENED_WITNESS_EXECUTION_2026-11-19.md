# Témoin sans intervention : complément d'exécution

Le plan séparé `nonintervened-budget-witness-plan.json`, publié à8af7f2e, fixe une seule FEN déjà connue, propriétaireD9PF2OSW:59, aux trois budgets10k/50k/200k. Les deux budgets sans perte de profondeur restent inclus. Le masque des neuf interventions et tous les résultats primaires sont inchangés.

Le nouvel adaptateur distinct réutilise uniquement les fonctions pures du collecteur publié3b89ca8, dont les octets sont contrôlés, ainsi que les binaires, sondes, source12 et limites déjà épinglés. Il doit être publié et vérifié à distance avant moteur. Il vérifie que l'audit parent reproduit exactement la FEN témoin et les trois budgets, sans intervention, puis exige les trois résumés originaux et toutes les dépenses avant comparaison des deux bras résiduels. Aucun accès à une référence Scan cible.

Deux processus7/61 dans des répertoires neufs sont prévus, plafonds1,3million de nœuds chacun,2,6millions au plus ensemble. Tous les stdin/stdout/stderr sont conservés, même en cas d'échec ; sorties normalisées identiques attendues et enveloppes brutes comparées en ne retirant que la durée principale. Le diagnostic est post-hoc sur une position sélectionnée pour un écart connu, pas une validation d'efficacité indépendante.

Comparaisons fixées : contrôle/LCB résiduel (même limite et absence de forçage), LCB résiduel/plein et natif résiduel/plein (effet du budget conditionnel à l'ordre), LCB/natif au même résiduel et au budget plein (effet de l'ordre conditionnel au budget). Rapporter tous les coups, profondeurs, scores Jass et tentatives ; ne pas transformer un score Jass à horizon différent en regret Scan. L'attribution à cette position ne se généralise pas au corpus.

Les quatre événements entiers et leurs FEN fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW restent réservés hors D1 fitting/validation indépendante/signatures/top-K/refinement/seuils/dimension. Aucune nouvelle cohorte ni campagne D1.
