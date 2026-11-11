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

- 2026-11-11 19 UTC — Relais de validation pour Jass. Tête initiale
  `6c62568ca1bfcd0456fbf31e9fa60a58014002ea`. Le commit qui ajoute
  cette entrée enregistre le comparateur, ses tests et le
  [rapport de sensibilité à la profondeur](BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md).
  [CI de la tête initiale](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656811)
  et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656712)
  réussis. Le rapport profondeur 8 reproduit le SHA précédent et deux runs
  à profondeur 12 produisent des JSON identiques. Les 58 tests MTDP passent.
  Sur 40 paires externes, 18 ont des optima disjoints à profondeur 12,
  dont 12 aux deux profondeurs. Deux des 95 transferts PC Blues vers
  l'externe dépassent 0,50 pion aux deux profondeurs (1,29 et 1,35 à
  profondeur 12). Échantillon majoritairement bullet et paires dépendantes.
  **Prochaine action :** préenregistrer et tester le voisinage diagonal
  adverse typé de rayon deux sur un nouvel échantillon indépendant, avec
  mesure des paires conservées et des transferts coûteux à profondeur 12.

- 2026-11-11 19:45 UTC — Relais recherche MTDP. Tête de départ vérifiée par lecture du journal ; les runs du commit `6c62568` ([CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656811), [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43080656712)) sont **success**. Lecture de `BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md` : 40 paires externes, 18 optima disjoints à profondeur 12, 12 aux deux profondeurs ; deux transferts PC Blues → externe à regret >= 0,50 pion aux deux profondeurs. Commit `645d13d` : préenregistrement de `LOCAL_NEIGHBORHOOD_PROTOCOL.md` (voisinage diagonal typé rayon deux). **Aucun calcul nouveau ni test du protocole exécuté ; validation de ces nouveaux commits à vérifier.** Prochaine action : implémenter le descripteur rayon deux et ses tests déterministes, puis mesurer sur les cohortes gelées sans changer les seuils.

- 2026-11-11 20 UTC — Relais de validation pour Jass, tête initiale
  `e9f09dc578303a9efa8cc6111660dfdb9a7cf747`. Le commit qui ajoute cette
  entrée implémente le rayon deux préenregistré et publie le
  [rapport PC Blues, cohortes gelées et tournoi rapide](LOCAL_NEIGHBORHOOD_RESULTS_2026-11-11.md).
  Les [contrôles de la tête initiale](https://github.com/jfrancoiscollin/dilf/actions/runs/43090262166)
  et [l'intégration initiale](https://github.com/jfrancoiscollin/dilf/actions/runs/43090262147)
  sont réussis. Le JSON gelé a été reproduit à l'octet et le calcul Scan 3.1
  profondeur 12 sur 241 nouvelles parties validées a abouti dans le workspace.
  Les 63 tests MTDP passent. Le rayon deux conserve 17/61 paires PC Blues,
  toutes divergentes sur au moins un successeur. Sur le tournoi rapide, il
  conserve 201/752 paires évaluables, dont 98 à optima disjoints. En transfert
  PC Blues → rapide, il conserve 52/249 paires et 4/13 pertes d'au moins
  0,50 pion. **Prochaine action :** mesurer la couverture et le regret des
  trois premiers coups transférés sur les cohortes gelées, pour évaluer
  l'ordre des coups avant un éventuel benchmark Jass à budget apparié.

- 2026-11-11 20:46 UTC — Relais recherche MTDP. Tête initiale
  `489129e13dec14319ec8ac178b7507ea19ed1a0b`, [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43094837410)
  et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43094837554)
  **success** ; toutes les étapes FMJD et PC Blues réussies. Commits
  `09536bf`, `4abcd59`, `b937b16` : nouvel audit hors-ligne des
  trois premiers coups transférés, six tests unitaires et protocole
  `TOP_THREE_TRANSFER_PROTOCOL.md`. **Aucun rapport numérique top-3 exécuté** ;
  les JSON gelés ne sont pas présents dans cette session. Actions du commit
  `b937b16` [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43098225137)
  et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43098225115)
  étaient en attente lors du contrôle. **Prochaine action :** vérifier les
  nouveaux tests, restaurer les deux JSON profondeur 12 épinglés et exécuter
  `python -m research.mtdp.top_k_transfer ... --k 3` ; contrôler les
  invariants de couverture et regret avant publication de résultats.

- 2026-11-11 21:20 UTC — Relais de validation pour Jass. Tête initiale
  `ed04c845ade26a6b2a98bcf3bb81d93b8dd0e720`. Le commit qui ajoute cette
  entrée publie le [rapport top-3](TOP_THREE_TRANSFER_RESULTS_2026-11-11.md)
  par sens de transfert. Les deux rapports Scan épinglés ont été retrouvés
  et leurs SHA-256 vérifiés. Deux exécutions identiques pour chacun des
  paramètres k=1 et k=3. Invariants vérifiés sur 2 272 transferts. Sur
  PC Blues → rapide, la couverture passe de 96/249 à 184/249, les pertes
  d'au moins 0,50 pion de 13 à 0, et la perte maximale à 0,24 pion avec
  trois candidats. Ces paires se recoupent et comparent deux tailles de
  listes. Les 71 tests MTDP et les 643 tests de la suite générale passent
  après correction d'une f-string invalide qui bloquait la collecte.
  [CI de la tête initiale](https://github.com/jfrancoiscollin/dilf/actions/runs/43098259673)
  en attente. [Compatibilité initiale](https://github.com/jfrancoiscollin/dilf/actions/runs/43098259662)
  signalée en échec au niveau du run et déjà en file d'attente au niveau
  du job. Les runs consultés n'exécutaient pas cet audit Scan hors ligne.
  **Prochaine action :** figer le protocole du benchmark Jass sur de
  nouvelles parties, avec recherche par défaut et contrôle de trois coups
  canoniques au même budget de nœuds que le transfert.

- 2026-11-11 21:43 UTC — Relais recherche MTDP. Lecture du journal et des rapports top-3, confirmation que le run `43098259673` (CI) est encore `queued` et que `43098259662` (downstream) affiche `failure` alors que son job `130783693312` apparaît `queued` : **état incohérent côté GitHub, pas de diagnostic de test possible**. Le commit `c1baeb2554ef59f588b7bcbb4ed0a7e8e36af670` préenregistre `JASS_MOVE_ORDERING_PROTOCOL.md` : cohorte indépendante, trois bras (natif/transfert top-3/témoin canonique), budgets de nœuds appariés, contrôle TT, critères et arrêt. **Benchmark Jass non implémenté et non exécuté.** Prochaine action : vérifier l'état Actions du dernier head puis auditer l'API Jass pour déterminer si la limite de nœuds et l'ordre racine sont injectables sans changer le moteur ; implémenter d'abord les tests d'intégration.
