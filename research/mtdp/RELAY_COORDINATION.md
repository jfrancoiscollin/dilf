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

- 2026-11-11 UTC — Relais de validation pour Jass. Tête initiale
  `3fdddc747a658eaf7f1b19a633742cf433147d84`. Le commit qui introduit
  cette entrée enregistre le protocole, le script, les tests et le
  [rapport Scan 3.1](BEST_MOVE_BASELINE_2026-11-11.md). Le
  [run downstream initial](https://github.com/jfrancoiscollin/dilf/actions/runs/43072960792)
  confirme 61 divergences de successeurs sur 61 paires PC Blues.
  Deux exécutions distantes dans le workspace ont produit le même JSON
  à profondeur 8. Les 53 tests MTDP passent. Sur 40 paires scorées hors PC Blues, 21 ont des
  ensembles de coups optimaux disjoints. Sur 95 transferts PC Blues
  vers une position nouvelle, 47 entraînent une perte positive
  (maximum 1,37 pion sur l'échelle de Scan). Échantillon de convenance,
  paires dépendantes. **Prochaine action :** rescoring des mêmes paires
  à profondeur 12 et mesure de la stabilité des désaccords et des coûts.

- 2026-11-11 18:44 UTC — Relais recherche MTDP. Tête initiale
  `ec8338567f9367b325e3dfbe303894ca5fc6a6b5`, rapport best-move
  profondeur 8 de l'autre relais lu. Les runs associés à cette tête
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43076530847)
  et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43076531157)
  sont **success**. Commits `eb05ade` et `29d800f` : paramètre CLI
  `--depth` (défaut 8) et tests de configuration pour préparer la réplication
  profondeur 12. **Aucun calcul Scan profondeur 12 exécuté à ce stade.**
  Validation des nouveaux commits : à vérifier. **Prochaine action :**
  vérifier CI sur `29d800f`, puis relancer les mêmes paires à profondeur 12
  en conservant les fichiers et SHA des corpus et en comparant les cohortes.
