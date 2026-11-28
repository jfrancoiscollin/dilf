# Audit des interventions et de la dépense de vérification

Audit hors ligne des **114 reçus Jass originaux**, sans nouvelle recherche, lecture de référence cible ni sélection sur regret. Les octets des 116 fichiers de décisions sont vérifiés contre le commit pré-cible `03b1a270b12244a03df715f265f597bd0f00cd50` et son inventaire complet ; manifeste, source12, méthodes figées, préfixes, catalogue légal, plafonds et sommes de nœuds sont revérifiés. Résultats primaires16/20 et reçus originaux inchangés.

## Coût réel et couverture

| Budget total par bras | Reçus | Nœuds de vérification | Part du budget contrôlé | Nœuds de recherche principale contrôlée | Interventions rapportées |
|---:|---:|---:|---:|---:|---:|
| 10 000 | 38 | 6 753 | 1,7771 % | 373 247 | 3 |
| 50 000 | 38 | 6 753 | 0,3554 % | 1 893 247 | 3 |
| 200 000 | 38 | 6 753 | 0,0889 % | 7 593 247 | 3 |

Les nœuds de vérification, la raison et l'intervention sont identiques pour chaque position aux trois budgets. Ils vont de60 à346, moyenne177,710526 ; aucun plafond dépassé, aucun cas éliminé, tous les budgets sont épuisés exactement. Par budget :2472nœuds préliminaires et4281de sondes,38préliminaires et374sondes. Ensemble :**20 259nœuds de vérification** (7416préliminaires+12843sondes) et9859741nœuds principaux sur9880000nœuds du **bras contrôlé**. Cette fraction de0,20505% ne se rapporte pas à la somme des trois bras ; elle ne mesure pas le coût CPU ou la vitesse de jeu.

À chaque budget :30`verified_unique_best`,5`verified_tie_same_winner`,3`verified_tie`. Les **neuf interventions sont trois positions**, chacune évaluée à trois budgets, et non neuf positions indépendantes. Propriétaires : s7ahYqL4:58, s7ahYqL4:132 et D9PF2OSW:53. Les neuf chemins et FEN sont conservés dans le masque mécanique du JSON ; aucune nouvelle cohorte.

## L'accord sur le coup final ne prouve pas une recherche identique

Contrôle et natif donnent le même coup **114/114** ; score Jass et profondeur finale coïncident **113/114**. Le cas `D9PF2OSW/10000/00005.json`, propriétaire `mtdp-lidraughts-D9PF2OSW.pdn:59`, a :

- aucune intervention (`verified_unique_best`),293nœuds de vérification ;
- contrôle :9707nœuds principaux, coup20-24, profondeur8, score Jass11 ;
- natif :10000nœuds, même coup20-24, profondeur9, score Jass3.

Ce sont des scores **Jass à des profondeurs différentes**, pas des regrets Scan comparables. Le préfixe LCB et la dépense de vérification diffèrent simultanément entre contrôle et natif : ce reçu ne permet pas d'attribuer causalement la perte de profondeur aux seuls293nœuds. Contrôle/LCB donnent le même coup113/114 (37/38 au budget50k,38/38 aux deux autres). Parmi les neuf interventions, le coup demandé à profondeur1 est le coup final dans2/9reçus seulement ; cela ne prouve ni son absence d'application ni le moment où la recherche converge.

## Limite de traçabilité vérifiée dans le code

`metered_control.execute` contrôle bien les scores exacts/complétés et les fenêtres avant de sélectionner le premier maximisateur natif ; il n'archive ensuite que phase, limite, nœuds et coup demandé. Les114reçus ne retiennent donc **aucun paquet complet scores/bornes/complétion des sondes**. `runner.cpp` émet déjà les tentatives par profondeur, meilleur coup et ordre attendu/visité ; `metered_engine_smoke.main_search` vérifie le contrat puis ne garde que le résumé final. **Aucune de ces114traces intermédiaires n'est conservée dans les résumés archivés.**

Le patch épinglé `depth-one-winner.patch` vérifie à l'exécution que le coup forcé est un tie complété et modifie `iter_best` à profondeur1. Cette garantie de code et les recherches terminées ne remplacent pas une preuve individuelle issue de la trace brute. Nous ne concluons ni « intervention inerte », ni causalité, ni équivalence générale à partir des114accords finaux.

## Validation et suite concrète

`two_arena_telemetry_audit.py` produit tous les cas et dénominateurs ;8tests synthétiques vérifient notamment la conservation des nœuds, les phases/sondes, l'unicité des positions malgré les trois budgets et les différences de profondeur malgré un même coup. Deux processus7/61 produisent les mêmes octets, SHA `95a5cade6055ceca051f8751b12f486c0fece6e633e6563b6b679c3dc477f63c`. Le vérificateur indépendant stdlib relit les114reçus et confirme les sommes, dénominateurs, deltas et masque. **241 tests H13 ciblés passent localement**, dont huit nouveaux. Une étape CI dédiée sans moteur est ajoutée au workflow existant ; validation distante réussie sur `48b55a691e7129b17e61b7841d4deed793220ca0` : [run44483463706](https://github.com/jfrancoiscollin/dilf/actions/runs/44483463706), job135421062605, huit tests, deux seeds et recalcul indépendant conformes. Artefact14509013690 téléchargé et vérifié,35188octets, ZIP SHA `a3b68d773e4aafb897da744a326e51246595f9e9506a2405cf7054d7f3da7c8f` ; ses trois fichiers concordent exactement avec le dépôt. Les8/8workflows du commit réussissent. Preuve complète dans `telemetry-audit-ci-verification-2026-11-19.json`.

```bash
python -m research.mtdp.jass_benchmark.two_arena_telemetry_audit --root . --output /tmp/telemetry.json
python -m research.mtdp.jass_benchmark.verify_two_arena_telemetry --root . --report /tmp/telemetry.json --output /tmp/telemetry-check.json
```

Le prochain calcul est fixé dans `two-named-arenas-mechanistic-residual-plan.json` : **les neuf reçus déjà intervenus, trois positions, sélection indépendante des scores cibles**, diagnostic post-hoc uniquement. Pas de nouvelle estimation d'efficacité sur une population indépendante.

1. Ajouter un collecteur distinct, sans modifier les méthodes primaires figées ni les binaires. Conserver stdout/stderr bruts préliminaires, de toutes les sondes et des trois recherches ; garder scores, bornes, complétion et tentatives par profondeur, avec le meilleur coup et les ordres.
2. Publier/vérifier le plan et ce collecteur avant calcul. Restaurer les mêmes binaires épinglés, source12 et catalogues ; aucun accès aux paquets cible16/20. Tous les cas sont conservés, y compris échecs ou plafonds.
3. Reproduire les trois bras originaux et chaque résumé/nombre de nœuds avant interprétation. Le sélecteur est recalculé depuis les nouvelles sondes ; l'intervention archivée sert de contrôle attendu, jamais d'entrée imposant le choix.
4. Ajouter deux recherches principales non forcées au budget résiduel exact : LCB et natif. Contrôle vs LCB résiduel garde préfixe et nœuds principaux identiques ; LCB résiduel vs LCB plein et natif résiduel vs natif plein mesurent séparément les changements de budget conditionnels à l'ordre. Ces deux bras supplémentaires n'incluent pas une dépense de vérification : ne pas les présenter comme une nouvelle campagne primaire à budget total égal.
5. Conserver les données brutes séparément des sorties normalisées ; seule la durée mesurée est exclue des comparaisons déterministes. Rapport par cas, aucun test de force/Elo ni extrapolation. Plafond de3,9millions de nœuds pour les cinq bras sur neuf cas, hors répétitions explicitement enregistrées.

Les quatre événements entiers fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW et leurs FEN restent réservés hors fitting, validation indépendante, signatures, top-K, refinement, seuils et dimension D1. Pas de campagne D1 dupliquée. Les ressources distantes suffisent ; PC de Jeff non requis.
