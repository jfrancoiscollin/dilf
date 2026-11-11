# MTDP — protocole de relais entre conversations autonomes

Portée : `jfrancoiscollin/dilf`, branche `research/mtdp-foundation`, PR #43 ; intégration expérimentale avec `jfrancoiscollin/draught-master`.

## À chaque activation (les deux relais, environ 30 minutes d'écart)

1. Lire la PR #43 (état, head SHA), les commits récents, les GitHub Actions et **ce fichier** avant de choisir une tâche.
2. Examiner les changements intervenus depuis le précédent passage ; reprendre le travail non terminé avant d'ouvrir une nouvelle piste.
3. Écrire exclusivement sur la branche de recherche ; ne jamais fusionner dans `develop`, déployer ou engager de ressources payantes sans accord explicite.
4. Avant toute modification, relire le fichier et son blob SHA courant ; en cas de conflit, relire, réconcilier, puis seulement réessayer. Éviter les modifications simultanées des mêmes fichiers.
5. Conserver les protocoles, scripts, tests et résultats reproductibles dans le dépôt. Distinguer systématiquement : **confirmé par exécution**, **implémenté mais non validé**, **hypothèse**.
6. Ne pas considérer l'égalité des coups légaux comme une équivalence des transitions, ni cette dernière comme une équivalence stratégique.
7. En cas de travail dépassant un créneau, laisser une transmission explicite dans un commit de recherche ou dans la section « Journal de relais » ci-dessous ; ne jamais prétendre qu'un processus continue sans preuve.
8. Privilégier les GitHub Actions déjà disponibles ; demander l'allumage du PC uniquement si une étape en dépend réellement.

## Format de transmission

Pour chaque passage qui modifie le dépôt, ajouter une entrée datée (UTC) dans le journal, avec :
- relais : conversation A/B si identifiable, sinon « relais non identifié » ;
- SHA initial et SHA final ;
- fichiers / expériences modifiés ;
- validations : lien du run, conclusion, périmètre exact ; « non vérifié » si nécessaire ;
- résultats numériques sourcés, limitations et blocages ;
- **prochaine action unique prioritaire**.

Les mises à jour du journal doivent utiliser le blob SHA fraîchement relu. Si un autre relais a modifié le journal entretemps, fusionner les entrées sans en écraser aucune.

## État de départ vérifié

- Commit `50674577a66abb17bf30195b48d5f9720b56181c` : GitHub Actions `ci` run 43071644305 **success**, `downstream-compat` run 43071644331 **success** (vérification du 2026-11-11).
- Le dernier rapport scientifique annoncé dans le projet relève 61 paires candidates et 61 divergences de successeurs. **Reconsulter les artefacts ou logs avant de réutiliser ces chiffres dans une nouvelle conclusion.**
- Priorité scientifique : analyser les contre-exemples des successeurs et tester une signature locale non triviale, avec protocole préalable, tests et mesure de compression.

## Journal de relais

- 2026-11-11 — Initialisation du protocole partagé ; les deux runs associés à `5067457` sont confirmés réussis. Prochaine action : relire l'état réel de la PR et le dernier head SHA, puis auditer les divergences des successeurs avant une nouvelle expérience.
