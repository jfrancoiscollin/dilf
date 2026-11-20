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
cmp /tmp/paired-estimand-audit.json research/mtdp/validation/paired-estimand-audit-2026-11-20.json
python -m pytest -q research/mtdp/tests/test_prospective_estimand_audit.py
```

## Relais D1 / décision H13

Avant une future évaluation, D1 doit étiqueter explicitement le nouveau résultat comme **secondaire conditionnel** et fournir, en parallèle, l'incertitude sur la population principale fixe n≥4, avec le même regroupement et la stratification préspécifiés. H13 ne combinera pas le point de l'agrégateur principal avec l'intervalle du pont conditionnel. Les autres métriques, le coût total de recherche, le traitement des échecs et les tirages indéfinis gardent leurs propres règles préenregistrées.

Ce contrôle ne remplace ni l'intégration des exclusions H13 dans l'admission D1, ni la qualification indépendante, ni le gel d'une nouvelle cohorte. Les quatre événements réservés et leurs parties/FEN restent exclus. Aucun constat sur les performances réelles de Jass ou de la signature géométrique ne découle de ces nombres artificiels.
