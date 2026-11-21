# H13 : compatibilité entre estimation principale et intervalle conditionnel

**Contrôle synthétique de pré-gel, aucun score Scan/Jass ni nouvelle cohorte.** Les nouveaux modules D1 sont conservés sans modification. Leurs deux résultats répondent à des questions différentes ; cet audit prévient une mauvaise association point/intervalle dans un futur protocole H13.

La clarification D1 `D1_INFORMATIVE_MASK_CLARIFICATION_2026-11-19.md` fixe la population principale par `n_legal >= 4`, sans scores cibles. `aggregate.aggregate_paired` respecte ce dénominateur. Le nouveau `paired_cluster_report(..., metric="recall_at_3")` fournit explicitement un résultat conditionnel sur `informative_at_3`, défini à partir des égalités entre scores : il est utilisable comme diagnostic secondaire.

## Contre-exemple reproductible

Quatre parties synthétiques, une observation chacune, ont les mêmes quatre actions légales. Le candidat classe a,b,c,d ; le témoin d,a,b,c. Deux observations ont d seul optimal ; deux ont c et d ex aequo optimaux.

| Résultat | Observations / parties | Écart candidat−témoin de rappel@3 | IC95 groupé par partie |
|---|---:|---:|---|
| Principal, population n≥4 fixée sans score | 4 / 4 | −0,5 | [−1 ; 0] |
| Secondaire, sous-groupe conditionnel informatif | 2 / 2 | −1 | [−1 ; −1] |

Les 2 000 tirages utilisent la graine fixe 20261120 et les utilitaires D1 existants. L'audit vérifie aussi qu'en modifiant une seule égalité de scores, le dénominateur conditionnel passe de 2 à 3 tandis que les quatre observations principales et leurs actions légales restent les mêmes. L'intervalle conditionnel ne peut donc pas accompagner l'estimation principale −0,5.

```bash
python -m research.mtdp.prospective_estimand_audit --output /tmp/paired-estimand-audit.json
cmp /tmp/paired-estimand-audit.json research/mtdp/validation/paired-estimand-audit-v2-2026-11-20.json
python -m pytest -q research/mtdp/tests/test_prospective_estimand_audit.py
```

## Relais D1 / décision H13

Avant une future évaluation, D1 doit étiqueter explicitement le nouveau résultat comme **secondaire conditionnel** et fournir, en parallèle, l'incertitude sur la population principale fixe n≥4, avec le même regroupement et la stratification préspécifiés. H13 ne combinera pas le point de l'agrégateur principal avec l'intervalle du pont conditionnel. Les autres métriques, le coût total de recherche, le traitement des échecs et les tirages indéfinis gardent leurs propres règles préenregistrées.

Ce contrôle ne remplace ni l'intégration des exclusions H13 dans l'admission D1, ni la qualification indépendante, ni le gel d'une nouvelle cohorte. Les quatre événements réservés et leurs parties/FEN restent exclus. Aucun constat sur les performances réelles de Jass ou de la signature géométrique ne découle de ces nombres artificiels.

Validation distante du code `abbdf07e87a8f28ef7754de6dc55796b646713f7` : **8/8 workflows réussis, 726 tests MTDP réussis**, 12 sauts optionnels. Preuve `paired-estimand-audit-ci-2026-11-20.json`. Si D1 ajoute un mode principal au pont, orienter explicitement le présent contre-exemple vers son mode secondaire et ajouter le contrôle du mode principal ; ne pas réimposer un filtre dépendant des scores à la population principale pour conserver un ancien résultat synthétique.

## Révision v2 : modes D1 explicites et preuve v1 conservée

D1 a ajouté `top3_population="fixed_n_ge_4"` et étiqueté le mode historique `conditional_informative`. La CI de `0d9ef05` échouait parce que la comparaison structurale avec le rapport v1 rencontrait deux nouveaux champs de population. Les effectifs, points et intervalles v1 n'avaient pas changé.

Le producteur actuel appelle explicitement les deux modes et vérifie que les six champs numériques/méthodologiques du résultat principal D1 correspondent au calcul de contrôle à n≥4. Le nouveau rapport est `paired-estimand-audit-v2-2026-11-20.json`. **Le rapport v1 et sa preuve CI restent inchangés.** Un second test compare exactement les résultats numériques et les métadonnées antérieures ; seuls les deux nouveaux champs d'étiquetage, eux-mêmes vérifiés, sont séparés de cette comparaison historique.

Le point principal reste −0,5 avec IC [−1 ; 0], le diagnostic conditionnel −1 avec IC [−1 ; −1]. Après modification d'une égalité, le mode principal D1 garde quatre observations et reproduit le contrôle ; le conditionnel passe à trois. Aucun filtre conditionné par les scores n'est réintroduit dans la population principale pour réparer la CI.
