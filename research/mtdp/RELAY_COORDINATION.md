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

- 2026-11-11 22:22 UTC — Relais de validation pour Jass. Tête initiale
  `34c1082b50bbe2a85460b1e8c6605b1f9b2b00bb`. Les runs
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43105587481)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43105587507)
  réussissent. Le dernier artefact PC Blues est `13894171214`.
  Aucun job GitHub Actions équivalent identifié. Le commit qui introduit cette entrée
  ajoute le [test d'intégration Jass](jass_preflight/README.md) sur le moteur
  épinglé à `cfe07fc`. Sur quatre positions de test, les trois bras gardent le
  même ensemble légal. Les ordres forcés sont visibles dans les traces et
  les 36 recherches respectent le plafond fixé. Deux exécutions identiques.
  La suite Jass et les 643 tests DILF passent. Le test utilise des rangs
  artificiels et l'évaluation artisanale de Jass.
  **Prochaine action :** préparer et geler le manifeste de la cohorte
  indépendante, avec sélection des sources sans scores cibles, vérification
  de la correspondance des coups DILF/Jass et configuration d'évaluation épinglée.

- 2026-11-11 22:47 UTC — Relais recherche MTDP. Tête initiale `107e6ce09f19d1938a364c5d2a909b104bae2e7d`. [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43111437276) et [downstream-compat](https://github.com/jfrancoiscollin/dilf/actions/runs/43111437195) : **success** ; étapes explicites du downstream : rejeu PC Blues FMJD, dynamique spatiale, collisions, ablation, successeurs, voisinage diagonal, archivage, toutes réussies. Préflight Jass décrit dans `jass_preflight/README.md` (36 recherches, 4 fixtures, sorties répétées identiques), mais **non exécuté dans ces deux workflows**. Commit `260624e` : statut du protocole Jass rectifié pour distinguer préflight et benchmark scientifique non exécuté. **Prochaine action unique :** implémenter et tester la correspondance sans ambiguïté des coups canoniques DILF vers les clés Jass (départ, arrivée, ensemble des prises), avec cas de prises multi-chemins et rejet des ambiguïtés, avant de figer la cohorte indépendante.

- 2026-11-12 — Relais de validation pour Jass, tête initiale `44bfa0976228980dfda17b7b33d196a18ef48632`. [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43114783011) et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43114782996) réussies, artefact PC Blues `13898335751`. Aucun job équivalent identifié. [Correspondance DILF/Jass](jass_preflight/README.md) vérifiée sur les 26 parties PC Blues : 1 749 FEN appariées sur 1 750, dont 1 313 sans prise et 436 avec prise. Le contrôle exclut une position où deux chemins de prise partagent une seule clé Jass. Les 78 tests MTDP, les 643 tests DILF et la suite Jass passent ; le préflight reste identique à l'octet. **Prochaine action :** geler le manifeste indépendant prévu par le protocole Jass, appliquer le contrôle de correspondance avant tout calcul et rapporter les exclusions, puis produire les classements Scan à profondeur 12 et exécuter les trois bras aux budgets préenregistrés.

- 2026-11-11 23:47 UTC — Relais recherche MTDP. Tête initiale `b3ccfd54022b1756af169d0ef5fea1ab06934c5e` ; [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43119582257) et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43119581944) **success**. Audit de `jass_move_mapping.py` : une action canonique DILF dupliquée pouvait écraser silencieusement une entrée du dictionnaire ; correction `13298c7` et test de non-régression `195a7a9`. **Aucun test exécuté localement** ; aucun workflow trouvé sur `195a7a9` lors de la première vérification. Le benchmark indépendant Jass reste non exécuté. **Prochaine action :** confirmer les Actions du nouveau head, puis figer le manifeste indépendant et vérifier l'exclusion des clés de prise ambiguës avant le benchmark.

- 2026-11-12 UTC — Relais de validation pour Jass. Tête initiale
  `ae3790b39f20cbf27812fa12adcadf0fc7dcb50b`. [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43122625371)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43122625307)
  réussies, artefact PC Blues `13901342350`. Aucun job équivalent identifié.
  Le commit de cette entrée fige le [lot indépendant](jass_benchmark/README.md)
  avant tout calcul de scores. Sur 66 parties exportées, 62 trajectoires
  distinctes et 6 046 FEN nouvelles après exclusion des corpus précédents.
  28 cibles dans 17 parties ont une source PC Blues et une correspondance
  complète des coups DILF/Jass, sans rejet d'appariement. Deux gels identiques.
  Les 79 tests MTDP avec catalogue Jass et la suite Jass passent. Le
  préflight est identique à l'octet. **Prochaine action :** produire les
  scores Scan des actions du manifeste gelé à profondeur 12, puis utiliser
  ces scores dans le benchmark Jass apparié aux trois budgets.

- 2026-11-12 UTC — Relais de validation pour Jass. Tête de départ du
  calcul `c7e591318b82672b2576959847db07bb2eda81dc`, gel publié avant
  calcul. [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43126874518)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43126874033)
  de cette tête réussies. [Résultats et reproduction](jass_benchmark/RESULTS_2026-11-12.md) :
  18/28 paires à optima Scan disjoints, perte maximale de 1,34 pion pour
  le premier coup transféré et de 0,12 pion pour le meilleur des trois.
  Les 252 recherches Jass ont atteint exactement leur plafond et reproduit
  les mêmes sorties hors temps mur. L'écart moyen face au témoin
  canonique va de −0,002 à −0,015 pion et les médianes sont nulles.
  Jass natif atteint une profondeur moyenne supérieure à chaque budget.
  Les 79 tests MTDP avec catalogue, 643 tests DILF et la suite Jass passent.
  **Prochaine action :** répliquer le protocole inchangé sur un deuxième
  tournoi rapide disjoint, avec agrégation par partie cible.


- 2026-11-12 00:44 UTC — Relais recherche MTDP. Tête initiale `77cdce89184aa777b24baa314492158e6629e93e`, [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43127588828) et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43127588983) **success**. Audit du benchmark indépendant : 28 cibles, 252 recherches, comparaison avec natif et témoin canonique, pas de gain de force démontré. Correction `880ce24` : `read_run` rejette désormais un reçu Jass dont `nodes` diffère du budget demandé, en plus de vérifier le budget déclaré. **Aucun test de ce correctif exécuté ni Actions du nouveau commit vérifiées au moment de cette entrée.** Prochaine action : vérifier les deux Actions, ajouter un test négatif de reçu à mauvais nombre de nœuds, puis répliquer sur un tournoi rapide indépendant avec agrégation par partie cible.

- 2026-11-12 — Réplication Jass à partir de la tête `cd75b60`. Les deux
  Actions du gel `ad2ca47` ([CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43133648237),
  [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43133648166))
  ont réussi. Aucun job de réplication équivalent identifié. Le
  [rapport reproductible](jass_benchmark/replication-iPQl7g7q/RESULTS_2026-11-12.md)
  couvre 75 cibles d'un deuxième tournoi rapide. Scan 3.1 profondeur 12
  trouve 40/75 paires à optima disjoints. La perte maximale est de 3,80
  pions avec le premier coup et de 1,20 avec le meilleur des trois.
  Les 675 recherches Jass ont consommé exactement leur budget, avec deux
  exécutions identiques hors temps mur. À 200 000 nœuds le transfert
  perd en moyenne face aux deux témoins, y compris par partie cible.
  Les 81 tests MTDP, 643 tests DILF et 10 tests CTest de Jass passent.
  **Prochaine action :** préenregistrer puis tracer un test où les trois
  coups sont proposés à la première itération seule, pour préserver
  l'ordre adaptatif natif ensuite. Utiliser le même traitement pour le
  témoin canonique, puis tester sur une nouvelle cohorte gelée.


- 2026-11-12 01:40 UTC — Relais recherche MTDP. Audit du dernier journal : la réplication indépendante sur 75 cibles / 675 recherches est documentée dans `jass_benchmark/replication-iPQl7g7q/RESULTS_2026-11-12.md`, sans gain robuste du transfert. Les Actions du commit `cd75b60` [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43129516678) et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43129516321) sont **success**. Commit `3007707` : protocole `JASS_INITIAL_ONLY_PROTOCOL.md` préenregistrant l'ordre top-3 uniquement à la première itération et la restauration adaptative native, avec contrôle des traces, troisième cohorte gelée et analyse groupée par partie. **Aucune implémentation Jass ni nouvelle recherche exécutée**. Prochaine action : auditer le code racine de Jass et implémenter la variante initial-only avec tests de récupération de l'ordre natif, avant tout scoring.

- 2026-11-12 02:18 UTC — Relais recherche MTDP. Tête initiale
  `1e1f64512461021995af164ca3132a62255d8c23`. [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43136178074)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43136178047)
  réussies, artefact PC Blues `13907129037`. Aucun job équivalent identifié.
  Le commit qui ajoute cette entrée publie le
  [patch Jass et son préflight reproductible](jass_preflight/INITIAL_ONLY_RESULTS_2026-11-12.md).
  L'ordre imposé ne persiste plus au-delà de la première itération.
  Les 30 recherches sur quatre fixtures ont atteint exactement leur budget.
  Les 609 traces d'itération et de reprise se reproduisent à l'octet et
  confirment la reprise de l'ordre adaptatif dès la profondeur 2.
  Le préflight historique se reproduit aussi à l'octet. Le test CTest
  `jass_tests`, les 81 tests MTDP avec catalogue et les 643 tests DILF
  passent. Aucun score sur un troisième tournoi n'a été calculé.
  **Prochaine action :** geler le PDN et le manifeste d'un troisième
  tournoi disjoint, puis raccorder le runner du benchmark à ce mode et
  à la vérification des traces avant de produire les scores Scan.

- 2026-11-12 02:47 UTC — Relais recherche MTDP. PR #43 vérifiée **open**. La branche était à un commit de `1e1f645` (publication du préflight initial-only). Actions sur `1e1f645` : [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43136178074) et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43136178047) **success**. Lecture du préflight : 30 recherches, 609 tentatives racine, restauration de l'ordre natif vérifiée sur fixtures synthétiques ; aucune mesure de qualité sur troisième tournoi. Commit `e98cd40` : `jass_benchmark/THIRD_COHORT_FREEZE_GATE.md` formalise la sélection sans fuite de scores, le gel PDN/manifeste, les exclusions et les critères d'arrêt. **Aucun troisième corpus sélectionné, aucun calcul Scan/Jass effectué, nouveaux commits non validés.** Prochaine action : choisir et télécharger un tournoi FMJD achevé et indépendant, geler le PDN et les exclusions avec SHA-256, puis générer deux fois le manifeste avant tout scoring.

- 2026-11-12 03:24 UTC — Relais recherche MTDP. Tête initiale
  `a6643f1bd918d2d3d49b3aae0f14fa88cd6056ec`.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43143862415)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43143862144)
  réussies, artefact PC Blues `13910113633`. Aucun job équivalent identifié.
  Le commit de cette entrée fige le
  [troisième tournoi indépendant](jass_benchmark/initial-only-0gB7ETSW/README.md).
  Sur 81 parties exportées, 72 trajectoires distinctes ont été validées et
  17 cibles issues de 11 parties partagent la signature et les coups légaux
  d'une source PC Blues. Aucun chevauchement avec les cibles des deux
  benchmarks précédents, aucun rejet de correspondance Jass. Deux gels
  identiques, 82 tests MTDP, 643 tests DILF et `jass_tests` réussis ; trace
  de préflight reproduite à l'octet. Aucun score Scan calculé sur ce lot.
  **Prochaine action :** raccorder le runner de benchmark au mode
  initial-only et vérifier ses traces et budgets sur la cohorte gelée
  avant le calcul Scan à profondeur 12.

- 2026-11-12 03:30 UTC — Relais recherche MTDP. Tête initiale
  `7e00678710a8090a18879aefbe0ce689856c7f6e`, gel publié avant le scoring.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43148069640)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43148069648)
  de cette tête réussies. Le commit de cette entrée publie le
  [benchmark initial-only](jass_benchmark/initial-only-0gB7ETSW/RESULTS_2026-11-12.md).
  Optima Scan 3.1 profondeur 12 disjoints sur 11/17 paires ; coût maximal
  de 1,56 pion avec le premier coup transféré, 0,07 avec le meilleur des
  trois. Les 153 recherches Jass ont consommé exactement leur budget ;
  les trois bras ont choisi les mêmes coups pour chaque cible et budget.
  Les 1 875 tentatives racine confirment la reprise de l'ordre adaptatif.
  Deux calculs reproduits à l'identique hors temps mur ; 83 tests MTDP,
  643 tests DILF, `jass_tests` et la reproduction des traces historiques
  réussis. Un seul tournoi, 17 positions. **Prochaine action :** préenregistrer
  le contrôle de sensibilité de Scan à profondeur 16 sur les trois manifestes
  gelés, avec coûts des transferts et coûts des coups Jass déjà choisis,
  puis lancer ce calcul avec les mêmes sources et actions légales.

- 2026-11-12 03:39 UTC — Relais recherche MTDP. PR #43 **open** vérifiée ; journal lu jusqu'au benchmark initial-only. Les workflows du gel `7e006787` [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43148069640) et [downstream](https://github.com/jfrancoiscollin/dilf/actions/runs/43148069648) sont **success**. Commit `b8fc04b` : préenregistrement de `SCAN_DEPTH16_SENSITIVITY_PROTOCOL_2026-11-12.md` pour les 3 cohortes gelées (28+75+17 cibles), avec audit des SHA, scores de tous les successeurs, regrets des coups Jass déjà choisis et bootstrap par partie. **Aucun calcul profondeur 16, aucun nouveau test exécuté ; Actions du nouveau commit non confirmées.** Prochaine action : auditer les références et binaires épinglés, vérifier les empreintes et implémenter le comparateur 12/16 avant de lancer Scan 16 sur ressources gratuites.

- 2026-11-12 04:19 UTC — Relais recherche MTDP. Tête initiale
  `863606da8033c0851f43fa4b9090ed5807a5b8c2`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43149688965)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43149688960)
  réussies, artefact PC Blues `13913107150`. Aucun job équivalent identifié.
  Le commit de cette entrée publie le
  [contrôle Scan 12/16](jass_benchmark/scan-depth16/RESULTS_2026-11-12.md),
  les empreintes, les références et le comparateur. 120 cibles conservées,
  2 067 successeurs scorés, 69 paires à optima disjoints à chaque profondeur,
  dont 49 communes. Au seuil d'un demi-pion, le premier coup coûteux passe
  de 12 à 6 cas ; le meilleur des trois conserve un cas à 1,28 pion.
  Les 1 080 coups Jass archivés réévalués ne montrent pas de gain cohérent.
  Références reproduites à l'octet sur les cohortes de 28 et 17 cibles ;
  référence à 75 cibles exécutée une fois, avec concordance exacte sur
  les sources partagées entre cohortes. Comparaison reproduite à l'octet,
  86 tests MTDP et 643 tests DILF réussis. **Prochaine action :** préenregistrer
  le témoin hors ligne de trois coups canoniques, puis comparer à taille
  de liste égale les couvertures et regrets des deux listes, sur les trois
  manifestes et aux profondeurs 12 et 16.

- 2026-11-12 05:20 UTC — Relais recherche MTDP. Tête initiale
  `da6eba7040e9578a38871e73878b23453332c9bc`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43156595507)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43156595525)
  de cette tête réussies, artefact PC Blues `13916341745`. Aucun job
  équivalent identifié. Le commit de cette entrée publie le
  [contrôle hors ligne à taille égale](jass_benchmark/offline-top3-control/RESULTS_2026-11-12.md).
  Les 120 cibles sont conservées aux deux profondeurs. La liste transférée
  contient un optimum dans 81/120 cas à profondeur 12 et 89/120 à
  profondeur 16, contre 51/120 à chaque profondeur pour le témoin
  canonique. À profondeur 16, le regret moyen du meilleur candidat est
  0,022 contre 0,113 pion. Deux exécutions identiques, 92 tests MTDP et
  643 tests DILF réussis. Le test optionnel avec le catalogue Jass vivant
  a été sauté, les correspondances gelées ont été utilisées. **Prochaine
  action :** préenregistrer un quatrième tournoi indépendant, fixer le
  classement source à profondeur 12 et évaluer les cibles à profondeur
  16 pour confirmer l'avantage hors ligne à taille égale.

- 2026-11-12 06:28 UTC — Relais recherche MTDP. Tête initiale
  `c2c938da2deee0cdf3e7986e6e42afbf96d88038`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43163366193)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43163366126)
  réussies, artefact PC Blues `13919276627`. Aucun job équivalent identifié.
  Le [gel du quatrième tournoi](https://github.com/jfrancoiscollin/dilf/commit/2eb1c84132723d3913a3b17850f0bdc7552c7f55)
  précède les scores, avec [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43167755489)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43167755582)
  réussies. Le commit de cette entrée publie le
  [contrôle source Scan 12 / cible Scan 16](jass_benchmark/fourth-3onq5G6G/RESULTS_2026-11-12.md).
  Sur 74 paires d'un tournoi 3+0, 40 ont des optima disjoints. Les trois
  coups transférés couvrent un optimum sur 55/74 contre 26/74 pour
  le témoin canonique, avec 0 contre 8 coûts d'au moins un demi-pion
  parmi 73 scores ordinaires. Les références et la comparaison ont
  été reproduites à l'octet. 97 tests MTDP avec catalogue Jass et 643
  tests DILF réussis. **Prochaine action :** préenregistrer un cinquième
  tournoi indépendant pour un benchmark Jass à budgets de nœuds
  identiques, avec classement source fixé et témoin de même taille.

- 2026-11-12 07:19 UTC — Relais recherche MTDP. Tête initiale
  `ee517b24bb2d1b51df1c6a8e70b804bbcb5f8a51`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43168401948)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43168401828)
  réussies, artefact PC Blues `13920448654`. Aucun job équivalent identifié.
  [Protocole](https://github.com/jfrancoiscollin/dilf/commit/b6689c731561ba7dc78c7802898a38c7a71027dd)
  publié avant sélection et
  [gel](https://github.com/jfrancoiscollin/dilf/commit/139213894ddbb0d0da7c2aed34440dae92713b85)
  publié avant calcul. Le commit de cette entrée publie le
  [benchmark Jass à budget égal](jass_benchmark/fifth-LAYRsqON/RESULTS_2026-11-12.md).
  Sur 20 positions, 12 paires ont des optima disjoints (source Scan 12,
  cible Scan 16). La liste transférée couvre un optimum sur 14/20
  contre 9/20 pour le témoin. À 200 000 nœuds le regret Jass moyen
  transfert moins témoin est +0,0105 pion (IC 95 % −0,0063 à +0,0390).
  180 recherches au budget exact et 2 188 tentatives racine vérifiées.
  Références et traces reproduites à l'octet, reçus identiques hors temps
  mur. 98 tests MTDP, 643 tests DILF et `jass_tests` réussis.
  **Prochaine action :** préenregistrer sur un nouveau tournoi le
  contrôle de la signature géométrique face au seul ensemble exact
  des coups légaux, et mesurer couverture et regret aux profondeurs fixées.

- 2026-11-12 08:22 UTC — Relais recherche MTDP. Tête initiale
  `80323bc29587cc88494e1c9fcfbe771d169c982f`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43177832614)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43177832625)
  réussies, artefact PC Blues `13925790094`. Aucun job équivalent identifié.
  [Gel](https://github.com/jfrancoiscollin/dilf/commit/e0ea77201179bbd8fe03c3a26d130bf6e90a37d1)
  publié avant les scores, [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43181880383)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43181880404)
  réussies. Ce commit publie le
  [contrôle coups légaux seuls / géométrie](jass_benchmark/sixth-xmzj1bLG/RESULTS_2026-11-12.md).
  Sur 8 633 positions, 138 correspondances avec les coups légaux seuls
  contre 39 avec la signature. Sur les 39 cibles communes, une seule
  source change, avec un gain de 0,31 pion sur le premier coup.
  Les deux listes de trois ont le même regret sur chacune des
  39 cibles. Références et comparaison reproduites à l'octet.
  102 tests MTDP et 643 tests DILF réussis ; catalogue Jass optionnel sauté.
  **Prochaine action :** préenregistrer une ablation qui garde les coups
  légaux et les bloqueurs exacts, en remplaçant les cases de tous les
  pions du joueur au trait par leur nombre.

- 2026-11-12 09:23 UTC — Relais recherche MTDP. Tête initiale
  `95b2db99b6f9c4ee79729bdf1964935d0844f5da`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43186039717)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43186039684)
  réussies, artefact PC Blues `13928476846`. Aucun job équivalent identifié.
  [Addendum](https://github.com/jfrancoiscollin/dilf/commit/4806c83db089f24797b914c5ceef774ce18e41ef)
  avant sélection et [gel](https://github.com/jfrancoiscollin/dilf/commit/827deec4677312ecf771966002a97aa95261a52c)
  avant les scores. Le
  [rapport du septième tournoi](jass_benchmark/seventh-pRW2Ahpz/RESULTS_2026-11-12.md)
  porte sur 6 146 positions admissibles. Coups légaux seuls : 78
  correspondances ; occupation exacte : 21 ; nombre et bloqueurs
  exacts : 32 ; géométrie exacte : 21. Le comptage récupère 11
  appariements, dont huit avec un optimum dans les trois candidats.
  Regret du meilleur des trois identique sur les 21 paires communes
  du contraste principal ; le choix de source ne change qu'une fois.
  Références, analyse et reproduction du sixième rapport identiques.
  107 tests MTDP et 643 tests DILF réussis ; catalogue Jass optionnel
  sauté. **Prochaine action :** préenregistrer une réplication
  multi-tournois avec les quatre règles, mesurer séparément les
  paires où la source change et les pertes extrêmes.

- 2026-11-12 10:26 UTC — Relais recherche MTDP. Tête initiale
  `79e389aad3b7e58e110f19a38df6d5a58d83f5d3`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43194394032)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43194394099)
  réussies, artefact PC Blues `13932915439`. Aucun job équivalent identifié.
  Le [relevé chronologique](jass_benchmark/eighth-replication/README.md)
  à 10:19:52 UTC donne **0/3** nouveaux tournois 5+0 terminés.
  Les deux suivants annoncés sont `xAnBIxHN` et `MoXhmT9b`.
  Aucun gel ni score nouveau. Le code prépare le plan commun de
  scores et l'analyse à deux niveaux (tournoi puis partie), avec
  contrôle des empreintes et des chevauchements. 112 tests MTDP,
  643 tests DILF et le rejeu des 26 parties PC Blues (1 864 positions)
  réussis ; catalogue Jass optionnel sauté.
  **Prochaine action :** rafraîchir le relevé et vérifier les exports
  dans l'ordre dès la fin des tournois. Publier les trois gels avant
  tout score, puis exécuter le plan commun.

- 2026-11-12 11:24 UTC — Relais recherche MTDP. Tête initiale
  `581723619e1033c3b0ac9bc766e9e96c8cad1421`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43200471262)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43200471245)
  réussies, artefact PC Blues `13935161415`. Aucun job équivalent identifié.
  [Relevé actualisé](jass_benchmark/eighth-replication/README.md)
  à 11:18:48 UTC : `xAnBIxHN` en cours, `vHeQVFho` nouvellement
  annoncé, `MoXhmT9b` annoncé ; **0/3** nouveaux tournois terminés.
  Le gel s'exécute par une commande qui valide l'ordre des candidats,
  le PDN, les empreintes et les exclusions. Répétition sur le septième
  tournoi : 6 146 positions, plan de scores et audit identiques.
  Les 11 PDN d'exclusion sont vérifiés. Un export historique différent
  a été récupéré à l'identique après deux nouvelles tentatives.
  114 tests MTDP et 643 tests DILF réussis ; catalogue Jass optionnel sauté.
  **Prochaine action :** récupérer le premier export terminé et publier
  son gel, puis procéder dans l'ordre jusqu'aux trois gels. Aucun score
  nouveau avant leur publication.

- 2026-11-12 12:20 UTC — Relais recherche MTDP. Tête initiale
  `e4267247f49bd5a2bb143c4aafcaaeff28f35a09`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43208957078)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43208957079)
  réussies, artefact PC Blues `13938739193`. Aucun job équivalent identifié.
  [Premier gel](jass_benchmark/eighth-replication/xAnBIxHN/provenance.json)
  de la réplication publié avant tout score. Deux téléchargements du
  PDN identiques. Rejeu FMJD : 129 parties acceptées sur 141, quatre
  doublons et huit captures ambiguës. Les 8 069 positions admissibles,
  le plan et l'audit sont identiques avec deux graines de hachage.
  Les 114 tests MTDP et 643 tests DILF passent, de même que le rejeu
  PC Blues (26 parties, 1 864 positions, aucune quarantaine).
  Le test optionnel du catalogue Jass a été sauté.
  **Prochaine action :** recontrôler `vHeQVFho` après 12:37 UTC.
  Il a disparu du relevé et ses trois endpoints renvoyaient 404
  avant la fin annoncée. S'il reste indisponible, archiver le
  constat et l'exclure explicitement, puis vérifier `MoXhmT9b`
  après 14:57 UTC. Conserver l'ordre chronologique et publier
  les trois gels avant de calculer les scores Scan.

- 2026-11-12 13:13 UTC — Relais recherche MTDP. Tête initiale
  `9338b56eecc3bc4507ae2a9b4330d7ea79bfb387`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43217138238)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43217138392)
  réussies, artefact PC Blues `13943932475`. Aucun job équivalent en cours
  ou en attente. Les jobs CI signalés en attente sont liés à des têtes
  du 11 novembre. Ce commit publie le
  [relevé après la fin annoncée](jass_benchmark/eighth-replication/README.md#post-finish-candidate-check-at-1313-utc).
  `vHeQVFho` est absent du calendrier et ses trois endpoints renvoient
  encore 404. Le fichier `rejections.json` conserve le motif d'exclusion
  et le relevé chronologique conserve l'annonce initiale.
  `MoXhmT9b` est annoncé et le contrôle refuse son gel à ce stade.
  114 tests MTDP, 643 tests DILF et le rejeu PC Blues (26 parties,
  1 864 positions, aucune quarantaine) réussis. Test optionnel du
  catalogue Jass sauté. Toujours un gel sur trois, aucun nouveau score.
  **Prochaine action :** revérifier le calendrier et tenter le gel de
  `MoXhmT9b` après 14:57 UTC si son export est disponible et admissible.

- 2026-11-12 14:14 UTC — Relais recherche MTDP. Tête initiale
  `3bd981f2ea23dfefad5e87d2de3714fc8f873354`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43225455843)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43225455856)
  réussies, artefact PC Blues `13948221492`. Aucun job équivalent actif.
  Le [relevé](jass_benchmark/eighth-replication/README.md#candidate-check-and-input-restoration-at-1414-utc)
  confirme `MoXhmT9b` en cours et `MIDBy9dl` annoncé pour 20:00–20:57 UTC.
  Le gel en cours de tournoi a été refusé comme prévu. Les 12 PDN
  d'exclusion et les empreintes Scan ont été vérifiés sur une
  restauration fraîche. Les 8 069 positions, le plan et l'audit du
  premier gel sont reproduits à l'octet. 114 tests MTDP, 643 tests
  DILF et le rejeu des 26 parties PC Blues passent. Le test optionnel
  du catalogue Jass est sauté. Un gel sur trois, aucun nouveau score.
  **Prochaine action :** vérifier après 14:57 UTC l'export final de
  `MoXhmT9b` et geler ce tournoi s'il est admissible.

- 2026-11-12 15:19 UTC — Relais recherche MTDP. Tête initiale
  `fa33de05f351713b08fd7119b870b1ed10ee1fc0`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43235710788)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43235711059)
  réussies, artefact PC Blues `13951474077`. Aucun job équivalent actif.
  Ce commit publie le
  [deuxième gel](jass_benchmark/eighth-replication/README.md#second-verified-freeze-at-1519-utc).
  Deux exports `MoXhmT9b` identiques, 142 parties acceptées sur 155,
  neuf doublons et quatre captures ambiguës. 9 293 positions admissibles,
  dont 74 appariements L, 29 LM, 39 LCB et 29 LMB. Aucun recouvrement
  de FEN admissibles ou d'identifiants de parties avec le premier gel.
  Fichiers de données, plan et audit reproduits à l'octet. 114 tests
  MTDP, 643 tests DILF et le rejeu PC Blues (26 parties) passent.
  Test optionnel du catalogue Jass sauté. Deux gels sur trois, aucun score
  nouveau. **Prochaine action :** vérifier le prochain tournoi 5+0
  terminé dans l'ordre du calendrier et publier son gel, en conservant
  les deux premiers comme exclusions. `MIDBy9dl` est annoncé pour
  20:00–20:57 UTC.

- 2026-11-12 16:11 UTC — Relais recherche MTDP. Tête initiale
  `b103d5012b3ba5628e41fdb6a4523b3a218dfa0d`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43247216991)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43247216948)
  réussies, artefact PC Blues `13957117638`. Aucun job équivalent actif.
  Les plans publiés contiennent 189 paires et partagent 30 FEN sources.
  L'adaptateur FMJD a confirmé et appliqué 1 039 successeurs sources
  et 1 745 successeurs cibles, sans lancer Scan. Les 13 PDN d'exclusion,
  les 47 empreintes des manifestes antérieurs et les empreintes Scan
  concordent. La commande de préparation refuse deux gels et ne produit
  aucun plan. 114 tests MTDP et 643 tests DILF passent. Le test optionnel
  du catalogue Jass est sauté. Le commit publie le
  [contrôle des entrées et les commandes d'indexation](jass_benchmark/eighth-replication/README.md#scan-input-checks-with-two-published-freezes).
  **Prochaine action :** geler le prochain tournoi 5+0 indépendant
  terminé. `MIDBy9dl` est toujours annoncé pour 20:00–20:57 UTC.

- 2026-11-12 17:16 UTC — Relais recherche MTDP. Tête initiale
  `34a8bf3f09a5260a3cd8778ba019fda9781b1e4d`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43256401930)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43256401991)
  réussies, artefact PC Blues `13960559152`. Aucun job équivalent actif.
  Ce commit publie le
  [relevé et le test d'intégration](jass_benchmark/eighth-replication/README.md#scoring-pipeline-rehearsal-and-updated-schedule).
  Le test sur trois gels synthétiques vérifie la préparation, la
  séparation des scores, la reconstruction par tournoi et
  l'agrégation. Résumé reproduit à l'octet et analyse altérée rejetée.
  115 tests MTDP et 643 tests DILF réussis, catalogue Jass optionnel sauté.
  Toujours deux gels et aucun nouveau score Scan. `MIDBy9dl` reste
  annoncé pour 20:00–20:57 UTC. `KXaMpuNe` est nouvellement annoncé
  pour 23:00–23:57 UTC. **Prochaine action :** contrôler l'export du
  premier tournoi 5+0 admissible terminé et publier son gel avant Scan.

- 2026-11-12 18:17 UTC — Relais recherche MTDP. Tête initiale
  `5d46b297831120c74b1f7264465b3edb3aeec1d2`, PR #43 ouverte.
  [CI](https://github.com/jfrancoiscollin/dilf/actions/runs/43268015310)
  et [compatibilité](https://github.com/jfrancoiscollin/dilf/actions/runs/43268015582)
  réussies, artefact PC Blues `13966762421`. Aucun job équivalent actif.
  Depuis des copies fraîches du dépôt, de l'adaptateur et de Scan,
  les 1 346 évaluations de référence du septième tournoi et leur
  comparaison ont été reproduites à l'octet. 115 tests MTDP, 643 tests
  DILF et le rejeu PC Blues réussis. Catalogue Jass optionnel sauté.
  Aucun score sur les nouveaux lots. Le relevé a confirmé deux gels
  et les créneaux déjà archivés. **Prochaine action :** vérifier le
  premier export 5+0 indépendant achevé, puis publier le troisième gel.

- 2026-11-15 08:28 UTC — Integration technique à budget **total** égal
  publiée sur la branche `research/mtdp-foundation` (PR #43, toujours
  brouillon). Le patch Jass opt-in `jass_preflight/first-root-action.patch`
  a compilé sur le commit épinglé `cfe07fce`, de même que le runner
  `mtdp_jass_metered_probe` et le runner principal initial-only avec son
  patch d'intervention. [GitHub Actions](https://github.com/jfrancoiscollin/dilf/actions/runs/43694555622)
  a exécuté une comparaison technique réelle à trois bras sur la **seule
  position initiale**, avec 9 coups légaux et 10 000 nœuds par bras :
  vérification MTDP = 100 nœuds (30 préliminaires + 70 sondes), recherche
  principale = 9 900 ; natif = 10 000 ; LCB inchangé = 10 000.
  `paired_comparable=true`, aucun dépassement et pas d'intervention
  (meilleur score unique). Les deux témoins terminent sur `32-27`.
  **Ceci valide la mécanique et la comptabilité sur une fixture, pas la
  force de jeu ni le benchmark prospectif.** Le parseur des reçus C++ est
  vérifié contre de vraies sorties ; une différence de casse de l'enum
  `Exact` a été corrigée. Le nouveau script
  `research/mtdp/jass_benchmark/metered_engine_smoke.py` peut reproduire
  ce test après compilation des deux exécutables. Le patch et le runner
  utilisent des checkouts jetables du même commit Jass ; aucune
  modification de production.

  **Prochaine action :** faire passer les tests Python du dernier commit
  (un défaut d'échappement dans un nouveau test a été corrigé), puis
  réaliser une **validation technique** du nouveau moteur sur les 473
  positions gelées (fonds et coûts par position, retombées de 10 %, reçus
  indépendants), sans prétendre à un nouveau holdout ; enfin geler une
  nouvelle arène admissible avant le calcul Scan cible et le benchmark
  prospectif à 10k/50k/200k sur les mêmes positions, contrôle vs natif/LCB
  et intervalle par partie.

- 2026-11-15 — Real-node archived engineering cohort handoff (NOT an
  independent scientific holdout). New reproducible
  `research/mtdp/jass_benchmark/metered_archive_gate.py` reads all five
  previously frozen arena manifests and **only Scan-12 source scores** to
  reconstruct each frozen LCB prefix. It does **not** read Scan-16 target
  scores, archived native winners, or reported strengths to select actions.
  Checks include hashes of arena/source/provenance, legal catalogues,
  independent preliminary depth-one probes, fresh main-table execution,
  actual total-node costs of MTDP/native/LCB at 10k/50k/200k, and per-arena
  and cross-budget identity preservation. Detailed JSON artifacts are uploaded
  from `mtdp-metered-probe` GitHub Actions.
  
  First run [43697600464](https://github.com/jfrancoiscollin/dilf/actions/runs/43697600464)
  validated **125 positions** in the first four independent archived arenas
  at 10k: every MTDP/native/LCB pair comparable, 11 verified tie
  interventions, 123/125 controlled final moves matching native versus
  122/125 LCB final moves matching native; mean 208.096 verification nodes
  per position (2.081% of 10k), all under the 10% cap. The fifth arena
  stopped on a **textual FEN encoding difference** in
  `B:WK2,25,35,40,48:B15,37`: Jass returned the equivalent
  `B:W25,35,40,48,K2:B15,37`. This was traced to Jass writing men
  before kings. `metered_engine_smoke._position_identity` now verifies
  actual colour/square/king identities instead of comparing serialized text,
  and rejects any true board discrepancy. Four archived king fixtures pass
  the fixed pinned-engine technical preflight.
  
  The most recent long-running technical archive workflow is
  [43698148848](https://github.com/jfrancoiscollin/dilf/actions/runs/43698148848)
  on `e83647fa` (state **in progress at last check**). Python CI and
  downstream compatibility both passed at that commit. The CI workflow now
  uses a per-PR concurrency group to cancel superseded future heavy jobs.
  **Do not claim 473-position or three-budget results before retrieving
  final verified receipts.** If the archive run fails, inspect exact event,
  budget and FEN and repair/re-run; if it completes, extract the per-arena
  JSON artifacts and publish fallback/intervention costs and true paired
  final-move comparisons. Any later Scan-16 outcome analysis of this
  retrospective archived cohort is only diagnostic, not prospective evidence.
  The final scientific efficacy test still requires a newly frozen,
  independent held-out arena under the preregistered protocol.

- 2026-11-15 12:58 UTC — **Disposition définitive de l'audit archivé
  à budget égal.** [Action #43709965786](https://github.com/jfrancoiscollin/dilf/actions/runs/43709965786)
  passée sur `a4f252d`: 473 positions × 3 budgets (10k/50k/200k),
  tous les reçus exacts, aucun dépassement ni fallback, 48 demandes
  d'intervention, 97 égalités exactes (48 choix déplacés, 49 inchangés),
  376 maxima uniques. Vérification moyenne 185,723 nœuds et maximum
  422, donc 1,857 %/0,371 %/0,093 % des trois budgets. MTDP reprend
  respectivement 467/472/473 coups natifs, contre 457/453/457 pour
  LCB. Artefact Jass ID `14160023070`.
  
  [Analyse de qualité Scan16 rétrospective #43716022780](https://github.com/jfrancoiscollin/dilf/actions/runs/43716022780)
  passée, artefact `14162397806`, aucune recherche Jass rejouée :
  sur les 469 cas de regret ordinaire définis, à 10k **2 choix MTDP
  meilleurs et 4 pires** que natif (+0,2516 centimen de regret moyen),
  à 50k **0 meilleur et 1 pire** (+0,0149), à 200k mêmes 473 choix
  que natif (0 écart). Les sept divergences de choix provenaient **toutes
  de cas sans intervention de départage** : elles sont compatibles avec
  le coût de vérification retranché du budget de recherche. L'amélioration
  de la force de jeu est **non démontrée**. Voir
  `jass_benchmark/spatial-jass/replication/REAL_NODE_METERED_ARCHIVE_VERDICT_2026-11-15.md`.
  **Ne pas requalifier cet audit déjà vu en holdout scientifique.**
  
  Le contrôle préliminaire du nouveau candidat indépendant
  `fFgE7oED` est réussi
  [Action #43716538357](https://github.com/jfrancoiscollin/dilf/actions/runs/43716538357)
  (ID artefact `14162552242`). Tournoi terminé en 5+0
  standard, début **2026-11-14 11:00:00 UTC**. Deux PDN de 169 802
  octets identiques, SHA256
  `916639e4daf7fae419bd4a9bb4a3530ce62f3eb40ea97f7582762e6cebf68de2`.
  Métadonnées et listings conservés. **Ce n'est pas encore un gel** :
  vérifier le premier rang chronologique et les exclusions de toutes les
  anciennes parties/FEN, rejouer les règles FMJD, figer les entrées
  et hashes AVANT le Scan16. Voir
  `jass_benchmark/spatial-jass/replication/METERED_PROSPECTIVE_CANDIDATE_CHECK_2026-11-15.md`.
  N'exécuter le nouveau protocole prospectif que sur un échantillon
  indépendant ainsi figé. Les deux automatismes MTDP existants peuvent
  reprendre sur cette étape et ne doivent pas répéter les campagnes
  archivées à 473×3 positions sans besoin de vérification.


- 2026-11-16 20:30 UTC — **MTDP-D1 handoff (design only; no performance claim)**. Dedicated protocol created at [`research/mtdp/decision_equivalence/PROTOCOL.md`](https://github.com/jfrancoiscollin/dilf/blob/0b1c6ba5fb8afc02d82d5f2cf759789da7a48add/research/mtdp/decision_equivalence/PROTOCOL.md), commit `0b1c6ba5`. D1 owns score-blind signatures, action-ranking stability, top-K regret and eventual ordering-only Jass experiments. Other relays continue general FMJD validation and the independent `fFgE7oED` tie-break holdout; **do not use its 78 reserved targets for D1 tuning**. Explicit D1-A through D1-E gates include same-position paired baselines, group independence, tactical safety, metered equal-node comparisons and fail-closed checks. The 61 PC Blues signature pairs are legal-action equivalence only; the 473 archived Jass comparisons have **no equal-budget quality improvement**. **Next D1 action:** implement score-blind signature audit and synthetic tests; no new Scan scoring or Jass production edits. This entry coordinates scope, not a new empirical result.


- 2026-11-16 21:29 UTC — **MTDP-D1 B1: score-blind audit code and synthetic tests committed; CI pending at handoff.** Commits [`5688e7fc`](https://github.com/jfrancoiscollin/dilf/commit/5688e7fc42088dea606268ea1dbb14519ba03a19) (audit), [`96c8c474`](https://github.com/jfrancoiscollin/dilf/commit/96c8c474aaa4e33de3e29190c6d3b96fa11ebe7f) (cross-game provenance fix), [`44663d37`](https://github.com/jfrancoiscollin/dilf/commit/44663d37d3e0a585d2470771506730c06030a003) (synthetic pytest). New `research/mtdp/decision_equivalence/score_blind_audit.py` accepts JSONL FEN, game provenance, canonical legal action identities and named score-blind signature keys. It emits deterministic collision, compression, cross-game and counterexample reports; rejects contradictory duplicate FEN, duplicate legal action keys, incomplete signature ladders and malformed input. It **does not yet compute signatures from FMJD state, validate input provenance, compare best moves, use Scan scores or demonstrate any search benefit**. Synthetic tests exercise deterministic counts, deduplication, fail-closed paths and empty inputs. Latest branch HEAD at handoff `44663d37`; GitHub Actions for prior `96c8c474` still running and fresh CI for `44663d37` not yet verified. **Next D1 action:** check CI for `44663d37`, fix any failure, then implement a pinned FMJD adapter emitting canonical legal action keys and E/L/Q/LCB signature rows from existing source data, with explicit capture-path ambiguity guards and no target scores. No Jass production changes or prospective fFgE7oED reuse.


- 2026-11-16 22:31 UTC — **MTDP-D1 B2: FMJD score-blind export implementation, validation pending.** Branch commits [`0aafc3df`](https://github.com/jfrancoiscollin/dilf/commit/0aafc3df5089e3d8d6baafd739473cea946ea974) and [`bf557997`](https://github.com/jfrancoiscollin/dilf/commit/bf5579977ee8be0e556134d2b68abd7b275a9595) add `decision_equivalence/fmjd_export.py` and synthetic tests. Exporter replays complete PDN games atomically through the existing FMJD adapter; emits FEN, game provenance, exact canonical legal-action identities, exact E signature, legal-action L signature, and quiet-men Q signature with exact fallback on captures/kings. Ambiguous duplicate action identities fail closed. Existing `score_blind_audit.audit` validates the full row population before JSONL output. **This does not implement published LCB semantics or Q+**, does not establish any strategic equivalence, and does not consume Scan/Jass scores. No dataset or new efficacy result yet; new commits' GitHub CI status was not available at handoff (previous HEAD `2a8ed00fa` had six successful workflows). **Next D1:** verify CI for `bf557997`, fix any failure; run exporter against pinned PC Blues engineering PDN via CI and archive SHA-256/score-blind collision report, then implement LCB only after exact published semantics and test fixtures are verified. No new prospective holdout and no Jass production changes.


- 2026-11-16 23:24 UTC — **MTDP-D1 B3: pinned PC Blues score-blind CI workflow committed; evidence still pending.** New dedicated workflow `.github/workflows/mtdp-d1-score-blind-pcblues.yml` at [`63240d07`](https://github.com/jfrancoiscollin/dilf/commit/63240d07c24c6b808f7a73a8ff0fc14ff08c8c16) runs the actual D1 audit/export pytest modules, replays 26 historical PC Blues PDNs with pinned FMJD `0e5189fb`, emits E/L/Q signatures, checks 1,864 observations, 1,750 distinct FENs, zero E collisions and expected 61 Q action-preserving pairs, archives score-blind JSONL/report and SHA-256 provenance. This is an **engineering regression**, not a new independent Scan/Jass outcome. All six preceding workflows at `847b0b5f` completed successfully. [New D1 run #43979170425](https://github.com/jfrancoiscollin/dilf/actions/runs/43979170425) was in progress on initial workflow SHA `f2d14374`; fixed incorrect pytest filename in `63240d07`, so only a run of the corrected HEAD can validate this version. **Next D1:** inspect corrected-head CI and artifact, fix any FMJD capture-path or count mismatch; only then add published LCB semantics and more signatures, keeping `fFgE7oED` reserved for its separate holdout. No Scan scoring or Jass production changes.


- 2026-11-17 00:30 UTC — **MTDP-D1 B3 validated on pinned historical PC Blues; no strategic-efficacy inference.** Corrected HEAD `be49365dc4` passed [D1 score-blind workflow #43979244723](https://github.com/jfrancoiscollin/dilf/actions/runs/43979244723) and six other workflows (CI, downstream, metered probe, retrospective quality, scout, prospective replay). The D1 job executed **12/12 pytest checks** and replayed **1,864 observations / 1,750 distinct FENs**; exact E has **1,750** signatures and zero distinct-FEN collisions, legal L **1,464** signatures, and quiet-man geometric Q **1,712** signatures with **61** distinct-position matched pairs and **zero different-legal-action pairs**. The 61-pair Q count reproduces the previously published engineering audit, not a new independent finding. Archived [artifact #14283101211](https://github.com/jfrancoiscollin/dilf/actions/runs/43979244723/artifacts/14283101211), ZIP SHA-256 `880439ca7c2b2ca967f5445f79cce4c0b0abc995aa61d7afbda70a0a7d9ffef1`, contains score-blind export/audit and provenance; its retention is 30 days. No Scan outcomes or Jass quality gains are established. **Next D1:** audit published LCB count/blocker semantics and implement a precise independent LCB signature with tests; do not relabel L as LCB, reuse fFgE7oED targets or claim pruning safety. Other relays retain prospective tie-break ownership.


- 2026-11-17 01:25 UTC — **MTDP-D1 B4: published LCB key implemented, CI pending.** On branch HEAD `5cb53283d7`, exporter now emits LCB = (`quiet-lcb-v1`, turn, complete canonical legal-action list, mover-men count, sorted immediate opponent blockers) for quiet mover-men-only positions, with exact typed-board fallback for captures and mover kings. The definition was checked against `jass_benchmark/geometry_ablation.py` `enumerate_occupancy_matches` (LCB requires equal turn/actions, mover count and blockers); no invented LCB shorthand. Commits [`66beff7f`](https://github.com/jfrancoiscollin/dilf/commit/66beff7fb4653672757e53d2927a583f0902b636) implementation, [`63e409a2`](https://github.com/jfrancoiscollin/dilf/commit/63e409a2bcc99c11485bb4498650dc86baf5030b) CI assertions, [`5cb53283`](https://github.com/jfrancoiscollin/dilf/commit/5cb53283d7f1824ef61a5aba7f342c23f44a98af) fixture. CI for this exact HEAD **not yet confirmed**; workflow [#43995489836](https://github.com/jfrancoiscollin/dilf/actions/runs/43995489836) was queued for preceding SHA `63e409a2` when checked. Next D1: verify final-head CI, fix failures, archive E/L/LCB/Q score-blind PC Blues audit and compare counts/collisions; do not infer stable best moves or claim new independent evidence. The separate fFgE7oED tie-break cohort remains reserved. The preregistered replay workflow on preceding HEAD had failed and is owned by the H:13/H:43 relays; avoid unrelated interference.


- 2026-11-17 02:28 UTC — **MTDP-D1 B4 LCB/Q score-blind CI verified; engineering only.** At HEAD `c2c0f3f375`, [D1 workflow #43995533942](https://github.com/jfrancoiscollin/dilf/actions/runs/43995533942) passed (12/12 tests), [artifact #14289631432](https://github.com/jfrancoiscollin/dilf/actions/runs/43995533942/artifacts/14289631432). Historical PC Blues: 1,864 observations / 1,750 distinct FEN; E=1,750, L=1,464, LCB=1,709, Q=1,712 distinct signatures. LCB compression 41 (2.34%) vs E; Q compression 38 (2.17%). CI asserts zero different-legal-action pairs for LCB/Q, and 61 Q pairs (previously known). Full evidence and limitations in [`decision_equivalence/LCB_Q_ENGINEERING_AUDIT_2026-11-17.md`](https://github.com/jfrancoiscollin/dilf/blob/73ce4d047bc3cab0beebf5c266c08088882aba8b/research/mtdp/decision_equivalence/LCB_Q_ENGINEERING_AUDIT_2026-11-17.md), commit `73ce4d04`. **No best-move stability or strength claim.** Next D1: deterministic score-blind LCB-only/Q-only/common matched-pair audit and tests, then independent frozen Scan ranking evaluation; preserve fFgE7oED for the other relays.

- 2026-11-17 02:39 UTC — **Relais H:43 : diagnostic prospectif vérifié, aucun gel scientifique.** HEAD initial `66c98f9888e136523492c0461d9f9d3f995ca097` (PR #43 ouverte, draft). Sept Actions sur ce SHA : toutes `success`, dont [downstream FMJD/PC Blues](https://github.com/jfrancoiscollin/dilf/actions/runs/44002782205) et [rejeu prospectif](https://github.com/jfrancoiscollin/dilf/actions/runs/44002782164). Logs du rejeu prospectif : 5 tests passent ; 157 parties candidates, 145 acceptées, **5 quarantaines pour notation de prise ambiguë** (parties 46/58/94/150/155), 7 trajectoires dupliquées ; 13 668 positions distinctes rejouées, 13 292 nouvelles selon le rapport, 78 cibles communes L/LCB. 4 184 parties publiques historiques et 18 exports de tournoi utilisés pour les exclusions ; aucune identité de partie publique candidate dupliquée signalée. L'artefact [#14293935482](https://github.com/jfrancoiscollin/dilf/actions/runs/44002782164/artifacts/14293935482) a été téléversé (22 fichiers, SHA-256 ZIP `ce32ab46b689dd1537901fd4b10141542a1888a608c1bd474ac04981e236b93c`), **non téléchargé et non revérifié indépendamment**. Les 5 prises ambiguës sont rejetées à bon droit ; ne pas choisir arbitrairement un chemin FMJD. Le rapport indique explicitement `chronological_selection_then_pinned_Jass_legal_catalogue_then_publish_scoring_freeze` : sélection chronologique, correspondance Jass et gel restent **non démontrés** ; aucun score Scan prospectif ni preuve d'amélioration. D1 a sa propre validation LCB/Q, non répétée ici. **Prochaine action unique :** auditer les 5 prises PDN ambiguës avec les trajectoires légales et la provenance source, sans les réinterpréter ni relâcher le rejet, puis établir la sélection chronologique avant gel.


- 2026-11-17 03:33 UTC — **MTDP-D1 B5: LCB/Q pair-level score-blind overlap instrumented; CI pending.** Dedicated `decision_equivalence/pair_overlap.py` computes deterministic distinct-FEN pair sets grouped by LCB and Q, partitions into `common`, `lcb_only`, `q_only`, reports action-set mismatches, cross-game provenance and the stricter disjoint-owning-game flag. It rejects contradictory duplicate FENs, duplicate action identities, missing E/L/LCB/Q, E collisions and malformed rows. Synthetic tests cover partition algebra, deterministic ordering, duplicate provenance and fail-closed behavior. Commits [`bf59427d`](https://github.com/jfrancoiscollin/dilf/commit/bf59427db049712850e7e5afd2a3f92cda3ad38a), [`62e86aba`](https://github.com/jfrancoiscollin/dilf/commit/62e86aba6956ea9eefaa0952b5f42e7e6eb244c0), [`3a362d0e`](https://github.com/jfrancoiscollin/dilf/commit/3a362d0e5c1999377753e284f30c559438ff2be6). D1 workflow now runs these tests, emits `pcblues-pair-overlap.json`, checks pair partition identities and zero LCB/Q legal-action disagreement, and archives the report with provenance. **No CI run of latest HEAD verified at handoff; no actual pair-overlap counts claimed.** Next D1: verify latest-head D1 Actions, inspect pair-overlap artifact and diagnose/fix any failure, publish counts with immutable evidence; only then plan independent, score-blind freeze before Scan ranking. No new strategic equivalence, best-move stability, pruning safety or Jass strength claim. The fFgE7oED prospective tie-break holdout remains reserved to the other relays.

- 2026-11-17 04:29 UTC — **MTDP-D1 B5 follow-up: action-map eligibility counters implemented, CI not yet verified.** The existing score-blind `pair_overlap.py` now distinguishes all same-legal-action pairs from the stricter subset with disjoint owning-game provenance in each of the common / LCB-only / Q-only buckets. This prevents treating a mere cross-game union as an independent transferable source-target pair and provides a denominator for later prospective ranking analysis. Synthetic tests now check counts, mismatched legal actions, and duplicated FEN provenance. Commits [`1d868df2`](https://github.com/jfrancoiscollin/dilf/commit/1d868df22ef70185ceeaf00334d969a758519526) and [`1f3384da`](https://github.com/jfrancoiscollin/dilf/commit/1f3384da4b1dcb58978baa6fe322a6f506309dbe). **No newly verified CI run or empirical pair counts at this handoff**; check workflow for this HEAD, inspect actual `pcblues-pair-overlap.json`, and publish immutable counts only after checking artifacts. Same legal actions and disjoint owning games do not imply decision equivalence, full independence or safe pruning. Reserved fFgE7oED remains excluded from D1.

- 2026-11-17 05:29 UTC — **MTDP-D1 B5 CI verified; overlap counts made observable, new CI pending.** PR #43 HEAD at check `dd2c9c6ee08f54a3e0573d580d79e96ae484f487`: all seven PR workflows passed, including [D1 #44017606799](https://github.com/jfrancoiscollin/dilf/actions/runs/44017606799) (20/20 tests), pinned FMJD historical PC Blues replay 1,864 observations / 1,750 distinct FEN, E/L/LCB/Q distinct counts 1750/1464/1709/1712. Pair-overlap audit was executed, asserted 61 Q pairs and zero legal-action mismatches, and archived in [artifact #14300080108](https://github.com/jfrancoiscollin/dilf/actions/runs/44017606799/artifacts/14300080108), ZIP digest `sha256:3484b4ae38f6db6fb3fe4a38b94e0a3a495138f2d24755210fc1ea4eaa59d9b0`. The workflow log did **not** print common/LCB-only/Q-only or strict disjoint-game denominators, so those numbers are **not yet verified**. Commit [`5cefe895`](https://github.com/jfrancoiscollin/dilf/commit/5cefe8959882cc6b971894ba21432848a9a0d7d3) now prints the actual bucket counts and eligibility denominators in CI logs (without target scores); its CI is pending and must be checked before reporting numbers. **Next D1:** inspect successful run of new HEAD, publish exact overlap counts and the source run; then preregister a genuinely independent D1 ranking cohort, never reusing fFgE7oED. Historical engineering pairs are not proof of best-move equivalence or pruning safety.

- 2026-11-17 05:45 UTC — **Relais H:43 : moteur FMJD historique épinglé, validation en attente.** Le workflow `downstream-compat` de la révision D1 `5cefe895` a réussi ([run #44024535919](https://github.com/jfrancoiscollin/dilf/actions/runs/44024535919)) : adaptateur FMJD, rejeu PC Blues, audits spatiaux et archive. Sur cette même révision, le rejeu prospectif [#44024535913](https://github.com/jfrancoiscollin/dilf/actions/runs/44024535913) a été annulé au checkout, donc aucun nouveau rejeu prospectif. Commit [`745f2d3`](https://github.com/jfrancoiscollin/dilf/commit/745f2d3aaa6ea7d2ce8d0ed197b048eb88014e38) : `downstream-compat.yml` remplace `draught-master:develop` par le SHA FMJD déjà épinglé dans le protocole prospectif `0e5189fbb251bf5eaf2e613d0f878bb17c740311` et inscrit ce SHA comme ref demandée dans la provenance. **La compatibilité du workflow modifié n'est pas encore vérifiée par Actions** ; aucune preuve d'équivalence stratégique. D1 conserve ses signatures et ses expériences ; aucune duplication. **Prochaine action unique :** contrôler les Actions de la nouvelle tête et corriger toute incompatibilité FMJD détectée sans relâcher le rejeu des 26 parties.

- 2026-11-17 05:50 UTC — **Relais H:43 : épinglage FMJD historique validé par CI.** Sur le commit `745f2d3aaa6ea7d2ce8d0ed197b048eb88014e38`, [downstream-compat #44026440184](https://github.com/jfrancoiscollin/dilf/actions/runs/44026440184) a réussi. Les étapes checkout du moteur épinglé `0e5189fbb251bf5eaf2e613d0f878bb17c740311`, provenance, adaptateur/rejeu des 26 parties PC Blues sans quarantaine, analyses spatiales, collisions légales, ablation, successeurs, voisinages diagonaux, manifeste SHA-256 et archivage sont toutes `success` dans les jobs GitHub. CI générale, qualité rétrospective et scout prospectif ont aussi réussi ; replay prospectif, benchmark et D1 ont été annulés sur ce SHA et ne constituent pas des validations nouvelles. **Correction de reproductibilité validée techniquement, aucune preuve de force stratégique.** Les signatures et cohortes D1 n'ont pas été modifiées ; prochaine étape fondation : auditer les cinq prises ambiguës et la provenance chronologique sans relâcher les quarantaines.

- 2026-11-17 06:29 UTC — **MTDP-D1 B5 overlap vérifié et rapport publié.** Tête contrôlée avant écriture `745f2d3aaa6ea7d2ce8d0ed197b048eb88014e38` ; [D1 #44024558704](https://github.com/jfrancoiscollin/dilf/actions/runs/44024558704) sur `6cfe921f5a5aa0a6452a7e351cb6522e3be1744e` : **success**, 20 tests réussis, [artefact #14302322531](https://github.com/jfrancoiscollin/dilf/actions/runs/44024558704/artifacts/14302322531), digest ZIP `d9254253e43367832a0daf83406787858b899aa1999488a46a0b4cb2ce355a7f`. Ligne JSON des logs : 61 paires communes LCB/Q, 3 paires LCB seules, 0 Q seules ; toutes ont les mêmes coups légaux et des propriétaires de parties disjoints ; 0 désaccord légal. Corpus historique : 1 864 observations / 1 750 FEN, E/L/LCB/Q = 1750/1464/1709/1712. Rapport [`decision_equivalence/PAIR_OVERLAP_RESULTS_2026-11-17.md`](decision_equivalence/PAIR_OVERLAP_RESULTS_2026-11-17.md) publié par commit `cc460597c89a3a15e8a609a0b4efaa86d8728ae0`. La CI du commit de documentation n'est pas vérifiée. **Limite :** aucune stabilité des meilleurs coups, équivalence minimax, cohorte indépendante ni accélération Jass prouvée. **Prochaine action D1 unique :** préenregistrer et geler un corpus D1 indépendant par partie, en excluant explicitement les 78 cibles fFgE7oED et les cohortes Scan historiques avant tout scoring.

- 2026-11-17 07:33 UTC — **MTDP-D1 C0 : préenregistrement indépendant, pas de gel.** HEAD initial `af71aaeaca8c84ef51c861dd67cba23dafa63e8a` ; ses sept Actions PR ont réussi, dont [D1 #44031610411](https://github.com/jfrancoiscollin/dilf/actions/runs/44031610411). Commit [`fc7dbb11`](https://github.com/jfrancoiscollin/dilf/commit/fc7dbb11a37f583170dc36d8c3f2db59d8be8c77) : protocole [`decision_equivalence/INDEPENDENT_COHORT_PREREGISTRATION_2026-11-17.md`](decision_equivalence/INDEPENDENT_COHORT_PREREGISTRATION_2026-11-17.md) avec exclusions par partie/trajectoire/FEN, interdiction des 78 cibles fFgE7oED, chronologie avant scores, partitions par partie/tournoi, SHA-256 et métriques top-K/regret/bootstrap. **Aucune nouvelle cohorte gelée, aucun scoring Scan ni test Jass exécuté.** Le document précise qu'un addendum doit fixer les seuils numériques avant scoring. CI du nouveau commit non vérifiée. **Prochaine action D1 unique :** inventorier les manifestes de toutes les cohortes historiques/réservées et implémenter un validateur fail-closed des exclusions avant sélection d'une source réellement nouvelle.

- 2026-11-17 08:34 UTC — **MTDP-D1 C1 : barrière d'exclusion score-blind implémentée, validation CI en attente.** Après lecture du registre et des Actions du SHA `ed2d37b233221c78feba07047de6ec02760fb78c` (7/7 success, D1 [#44039662275](https://github.com/jfrancoiscollin/dilf/actions/runs/44039662275)), commits [`b3cfc125`](https://github.com/jfrancoiscollin/dilf/commit/b3cfc1257cba1e0e4e7334756246b0c999d1f823) et [`03921a37`](https://github.com/jfrancoiscollin/dilf/commit/03921a37236de7f3b41dc3d2e533e6969a86d68b) : `decision_equivalence/cohort_exclusion_gate.py` et 9 tests synthétiques. Contrôle fail-closed des registres JSONL interdits, identité de partie, trajectoire et FEN, doublons, chronologie, provenance et champs de scores ; sortie déterministe avec SHA-256, refus d'écraser un manifeste. **Aucune exécution CI du nouveau code vérifiée, aucun corpus indépendant identifié ou gelé.** Cette barrière n'atteste pas la complétude des registres : revue humaine des sources historiques et réservées obligatoire. **Prochaine action D1 unique :** exécuter les tests en CI et constituer l'inventaire complet des registres interdits (incluant fFgE7oED), puis seulement envisager un gel sans scores.

- 2026-11-17 09:26 UTC — **MTDP-D1 C1 validation branchée sur CI (sans gel).** HEAD initial `e898f0221c4ff6e413924b60be45b3c688b9da24`, sept workflows `success`, dont [D1 #44047987807](https://github.com/jfrancoiscollin/dilf/actions/runs/44047987807), artefact #14312321817 ; ce run **n'exécutait pas** les tests de la barrière d'exclusion. Commits `cee8ebb72c6ad75a8fceb7d335a5ebbbd6cfdb92` (8 tests synthétiques de rejet identité interdite, absence de registre, FEN dupliquée, ordre, score et cas valide) et `29fd1a05678ad26db895dc2fe145badf74c443fd` (tests intégrés au workflow D1). **CI des nouveaux commits non encore vérifiée**, aucune cohorte nouvelle gelée, aucune exhaustivité des exclusions établie, aucun score Scan ni gain Jass. Prochaine action D1 : vérifier le nouveau run, corriger tout échec, puis inventorier les manifestes historiques/réservés avec empreintes et contrôle de complétude avant sélection indépendante.

- 2026-11-17 10:29 UTC — **MTDP-D1 C2 : préflight d'intégrité des registres d'exclusion.** HEAD initial `8e8fb496f3a9c30d361c64bb58bedb1267f7123f` ; ses 7 workflows PR sont `success`, dont [D1 #44055640497](https://github.com/jfrancoiscollin/dilf/actions/runs/44055640497). Commits `58691ca18ee43854048cfe2d1587af9b8e99134b` et `661101d162ac8b6959ea6b93e07dda15c8af7c35` : nouveau `decision_equivalence/registry_coverage.py` et 6 tests synthétiques (intégrité SHA-256, nombre de lignes, groupes obligatoires, chemins confinés, doublons). **Ces nouveaux tests ne sont pas encore raccordés au workflow ni validés en CI** ; vérifier en priorité leur exécution et corriger si nécessaire. L'outil refuse un inventaire partiel et atteste uniquement son intégrité technique : il ne garantit pas l'exhaustivité scientifique des registres ni l'indépendance d'une cohorte. Aucun gel, score Scan ni benchmark Jass D1. **Prochaine action D1 unique :** brancher et valider ces tests dans CI, puis constituer les vrais registres d'exclusion épinglés sans toucher aux 78 cibles réservées.

- 2026-11-17 11:25 UTC — **MTDP-D1 C2 : tests d'intégrité raccordés à Actions.** HEAD initial `535d06de10a8b1139e4a6ba61c91b477290cff1b`, sept workflows `success` dont [D1 #44065410116](https://github.com/jfrancoiscollin/dilf/actions/runs/44065410116) ; ce run **ne comprenait pas** `test_registry_coverage.py`. Commit [`e7a22697`](https://github.com/jfrancoiscollin/dilf/commit/e7a22697047579d281d1b648fe24179595ac91da) ajoute explicitement les six tests d'intégrité au job D1 ; **validation du nouveau commit non encore confirmée**. Aucune cohorte indépendante gelée, aucun score Scan nouveau, aucune amélioration Jass démontrée. **Prochaine action D1 unique :** vérifier le run D1 sur `e7a22697`, puis inventorier les registres d'exclusion réels et leurs SHA avant tout gel.

- 2026-11-17 11:40 UTC — **Relais H:43 : vérification complète des Actions sur `cf22a8f250d086ddf2223207f30ac28e6c96f6f5`.** PR #43 ouverte, brouillon, non fusionnée ; 7/7 workflows PR `success` : [downstream-compat #44073899248](https://github.com/jfrancoiscollin/dilf/actions/runs/44073899248), [prospectif #44073899240](https://github.com/jfrancoiscollin/dilf/actions/runs/44073899240), [D1 #44073899319](https://github.com/jfrancoiscollin/dilf/actions/runs/44073899319), CI et autres contrôles. Les étapes individuelles du downstream FMJD épinglé, adaptateur, rejeu historique PC Blues, audits spatiaux/légaux, manifeste SHA-256 et archivage sont `success` ; le prospectif confirme ses étapes de téléchargement/rejeu/exclusions `success`. Le workflow D1 est `success` mais la liste exacte des tests exécutés et les nombres empiriques ne sont pas établis par la seule métadonnée de job ; ne pas les inférer. Aucune expérience D1 répétée, aucune quarantaine levée, aucun nouveau score stratégique. **Prochaine priorité fondation :** audit des cinq ambiguïtés de prises avec trajectoires et provenance, sans affaiblir le rejet ; contrôle d'indépendance chronologique avant gel. Ce passage est documentaire, sans nouveau calcul indépendant.

- 2026-11-17 12:30 UTC — **MTDP-D1 C3 : audit de préparation du gel, sans cohorte.** Contrôle du HEAD connu `cf22a8f250d086ddf2223207f30ac28e6c96f6f5` : sept workflows PR `success`, dont [D1 #44073899319](https://github.com/jfrancoiscollin/dilf/actions/runs/44073899319), artefact historique #14323078245 (digest ZIP `fd2a65ef07d2919db92c7f28bf35984d5e77a7fb8b466c9da0484f348cb90a75`). Commit [`fc3e2b3b`](https://github.com/jfrancoiscollin/dilf/commit/fc3e2b3b9487b973dd8c3fdee3eb96848342809f) : [`decision_equivalence/FREEZE_READINESS_AUDIT_2026-11-17.md`](decision_equivalence/FREEZE_READINESS_AUDIT_2026-11-17.md) documente le blocage scientifique : `registry_coverage.py` contrôle les cinq registres fournis, **pas leur exhaustivité** ; aucune provenance complète réconciliée ni nouvelle cohorte gelée. Pas de nouveau score Scan, ni gain Jass. **Prochaine action D1 unique :** inventorier les cinq registres avec chemins source, SHA et dénominateurs vérifiés, puis tester l'exclusion sur un corpus réellement nouveau avant gel. CI des commits documentaires non vérifiée.

- 2026-11-17 13:28 UTC — **MTDP-D1 C4 : durcissement de l'intégrité des identités d'exclusion.** Les sept workflows du HEAD antérieur à ce passage sont `success` (D1 [#44083950565](https://github.com/jfrancoiscollin/dilf/actions/runs/44083950565)). Commits `f4a8147c` (validation des SHA-256 `trajectory_sha256`/`fen_sha256` dans chaque ligne JSONL), `84e8db08` (trois tests de régression) et `ac680cfc` (correction du saut de ligne JSONL du test). Un manifeste dont l'empreinte de fichier est valide mais qui contient une identité SHA malformée doit désormais être rejeté. **CI des nouveaux commits non encore confirmée** ; aucun corpus gelé, aucun score Scan indépendant, aucune amélioration Jass mesurée. Le contrôle d'intégrité ne certifie toujours pas l'exhaustivité des cinq sources ; prochaine action : vérifier CI et réconcilier les inventaires réels avant gel.

- 2026-11-17 14:28 UTC — **MTDP-D1 C5 : matrice de provenance des cinq exclusions publiée, gel toujours interdit.** HEAD vérifié via le commit `d6116a975c062ae712adf6b28011b7f3a093bbbd` ; ses sept Actions PR sont `success`, dont [D1 #44093233070](https://github.com/jfrancoiscollin/dilf/actions/runs/44093233070), artefact historique #14331254966 (digest ZIP `sha256:926187516c624695f3097ed3507a2a66830ab0e8e9cbb09da928314dbb930561`). Commit [`643fd6fd`](https://github.com/jfrancoiscollin/dilf/commit/643fd6fd519a658318ddeda869b013d22aafa028) : [`decision_equivalence/EXCLUSION_SOURCE_RECONCILIATION_2026-11-17.md`](decision_equivalence/EXCLUSION_SOURCE_RECONCILIATION_2026-11-17.md) identifie pour chaque groupe les pistes sources, preuves connues, preuves manquantes et critères de sortie fail-closed. **Aucun registre source complet réconcilié, aucune nouvelle cohorte, aucun score Scan indépendant, aucun gain Jass.** CI du commit documentaire non vérifiée. **Prochaine action D1 unique :** retrouver et exporter les identités des 26 parties PC Blues depuis la source épinglée, compter et hacher leur registre, puis traiter les quatre autres groupes sans toucher aux scores réservés.

- 2026-11-17 15:33 UTC — **MTDP-D1 C6 : exclusion score-blind renforcée.** HEAD initial `f37ceba5fe3c717a72c2dd57bd1063d9c38d0b36` ; Actions 6 success / 1 failure (workflow `mtdp-preregistered-candidate-replay` #44103756400, hors périmètre D1), D1 [#44103756835](https://github.com/jfrancoiscollin/dilf/actions/runs/44103756835) success, artefact historique #14337281772. Commits `aea1dd3d`, `f91cb6d6`, `545a374c` : le validateur `decision_equivalence/registry_coverage.py` rejette désormais les champs de score, évaluation, regret, meilleur coup, rang et WDL dans les identités d'exclusion ; six cas synthétiques ajoutés, correction du saut de ligne fixture. **CI des nouveaux commits non encore confirmée**, aucune nouvelle cohorte ni score indépendant. Le contrôle reste une barrière de contamination, pas une preuve d'exhaustivité des cinq sources. **Prochaine action D1 unique :** confirmer les six tests en CI puis exporter et réconcilier les identités des 26 parties PC Blues depuis la source épinglée.

- 2026-11-17 16:29 UTC — **MTDP-D1 C7 : protection contre les scores imbriqués.** Audit de `decision_equivalence/registry_coverage.py` : le rejet antérieur ne parcourait que les clés JSON de premier niveau ; une annotation `provenance.scan_score` ou un score dans une liste pouvait passer malgré une empreinte SHA valide. Commits `ccda6268` (parcours récursif des objets/listes), `f084986a` (trois cas négatifs synthétiques), `4bcbca63` (correction de la fixture JSONL). **Aucun test exécuté localement et validation CI de ces commits non encore confirmée** ; aucune nouvelle cohorte gelée, aucun score Scan ni gain Jass. Le contrôle reste une protection anti-fuite, pas une preuve d'exhaustivité des cinq sources. **Prochaine action D1 unique :** vérifier le run D1 et ses trois nouveaux tests, puis exporter les identités des 26 parties PC Blues depuis la source épinglée.

- 2026-11-17 17:29 UTC — **MTDP-D1: deduplication des registres d'exclusion (pré-gel, sans preuve de complétude).** HEAD initial `ec61694878b66f2ebc561716b5e8dd9770ce142e` ; sept Actions sur ce HEAD **success**, dont [D1 #44126584089](https://github.com/jfrancoiscollin/dilf/actions/runs/44126584089), artefact D1 `14347891806` (engineering historique uniquement). Commits `7b43db7e`, `ed9e7dd0`, `d93fc07a` : le contrôle `registry_coverage.py` rejette les lignes d'exclusion exactement dupliquées indépendamment de l'ordre des clés JSON et les identifiants de partie composés uniquement d'espaces ; trois cas de régression ajoutés. Aucun test local exécuté, nouvelle CI **non encore vérifiée**. Les doublons inter-registres ne sont pas interdits (chevauchement historique possible) ; le contrôle ne prouve toujours pas l'exhaustivité des cinq sources. **Prochaine action unique :** confirmer les tests du nouveau HEAD, puis réconcilier les 26 identités PC Blues avec le PDN épinglé avant tout gel indépendant. Aucun score Scan nouveau, aucune revendication top-K ou Jass.

- 2026-11-17 18:32 UTC — **MTDP-D1 : rejet des clés JSON dupliquées dans les exclusions (pré-gel).** HEAD initial `b1d515ca1d707fd08b0027c31b8bdade8e6c4cf4`, 7/7 workflows PR `success`, dont D1 [#44137764928](https://github.com/jfrancoiscollin/dilf/actions/runs/44137764928), artefact historique #14351709658 (pas une cohorte indépendante). Commits `0c1968ae`, `d6f95eac`, `9261319a` : `registry_coverage.py` refuse désormais les clés JSON répétées, y compris imbriquées, dans le manifeste et les lignes JSONL, au lieu de laisser `json.loads` écraser silencieusement la première valeur ; trois cas de régression ajoutés. **CI de ces commits non encore confirmée**. Contrôle d'intégrité uniquement, pas d'exhaustivité des sources, aucun gel ni scoring Scan ni gain Jass. **Prochaine action D1 :** confirmer CI, puis extraire/réconcilier les 26 parties PC Blues et les quatre autres sources avant tout gel.

- 2026-11-17 19:28 UTC — **MTDP-D1 B : audit descriptif de collisions ajouté.** HEAD de référence précédent `b5c8f8a3e9c644d6e3001b0c1b7b7be577a40351` : 7/7 workflows PR `success`, D1 [#44149203998](https://github.com/jfrancoiscollin/dilf/actions/runs/44149203998), artefact historique #14357697800 (pas une cohorte nouvelle). Commits `b2d1cb82` et `f3fb49a0` : `decision_equivalence/signature_collision_audit.py` et six tests synthétiques pour compter signatures uniques, collisions inter-parties et divergences de cartes de successeurs sans scores. Les six cas ont été reproduits localement sur une copie équivalente avant publication ; **la version GitHub n'est pas encore validée par CI**. Les empreintes de successeurs doivent provenir de cartes action→successeur canoniques, et non de seuls coups légaux. Aucun corpus indépendant, aucun top-K ni gain Jass. **Prochaine action D1 unique :** vérifier la CI de ces commits et brancher cet audit sur les exports historiques score-blind uniquement pour validation descriptive ; poursuivre la réconciliation des 26 parties PC Blues avant tout gel.

- 2026-11-17 20:31 UTC — **MTDP-D1 B : métriques de collisions par paires.** HEAD initial `5815015ef4f503730adfb5013ca52a0c65bc714d`, 7/7 Actions PR `success`, D1 [#44159009806](https://github.com/jfrancoiscollin/dilf/actions/runs/44159009806), artefact historique `14361444388` (pas un test indépendant). Commits `0f7adb9` et `f6fa284` : l'audit descriptif score-blind compte maintenant les paires en collision, inter-parties, divergentes en successeurs, et l'intersection inter-parties/divergentes ; deux tests synthétiques ajoutés. **Tests nouveaux non exécutés localement ; CI du nouveau HEAD à vérifier.** Aucune preuve d'équivalence de meilleur coup ou minimax ; aucun gel indépendant ni gain Jass. **Prochaine action D1 unique :** valider les tests CI et raccorder l'audit aux données historiques score-blind avec empreintes de successeurs canoniques, sans réutiliser ces données comme cohorte indépendante.

- 2026-11-17 21:32 UTC — **MTDP-D1 B : comptage exact des collisions en temps linéaire par groupe.** HEAD initial `76db7568bee9d07e686a541d6d68bcdca7924ba0` ; 7/7 Actions PR réussies dont [D1 #44170301475](https://github.com/jfrancoiscollin/dilf/actions/runs/44170301475), artefact historique #14367097515 (SHA-256 `a2fe6f153dd8dd5fb2887592d9451ed4d8279e5b8d65b8b7dd52510e2a3280f8`, aucune cohorte nouvelle). Commits `8f5f0604` et `9381a38e` : `decision_equivalence/signature_collision_audit.py` remplace l'énumération quadratique de toutes les paires par les comptes exacts via combinaisons et inclusion-exclusion (parties, successeurs, intersection). Deux tests nouveaux : comparaison exhaustive sur 91 positions et groupe de 10 000 positions, soit 49 995 000 paires implicites sans matérialisation. **Tests non exécutés localement ; aucune Actions encore associée au nouveau HEAD au contrôle.** Cette amélioration est algorithmique, pas un résultat scientifique sur données réelles. Aucun score Scan ni accélération Jass. **Prochaine action D1 unique :** confirmer la CI des nouveaux tests, puis raccorder l'audit aux exports historiques score-blind munis de cartes de successeurs canoniques.

- 2026-11-17 22:28 UTC — **MTDP-D1 B : empreinte canonique de carte de successeurs (outil préparatoire).** HEAD initial `e4733a685ddf314223337d6d7d539add68e39787` ; 7/7 Actions de ce HEAD `success`, dont [D1 #44181164501](https://github.com/jfrancoiscollin/dilf/actions/runs/44181164501). Commits `0c4afc992c27f3476f314e25726b5bc32915e968` et `4d668a8d2629b4b383f066597d4f6e71fc42b5ec` : `decision_equivalence/canonical_successors.py` calcule SHA-256 déterministe sur les paires action→état successeur (tri canonique, rejet des valeurs vides/ambiguës), avec quatre tests synthétiques. **4/4 tests réussis localement sur copie textuellement identique ; CI du nouveau HEAD non encore confirmée.** Précondition externe non prouvée : générateur FMJD exhaustif et canonicalisation des états (trait et compteurs pertinents inclus). Une empreinte égale ne prouve ni meilleur coup égal ni équivalence minimax. Aucun nouvel échantillon indépendant, score Scan ni gain Jass. **Prochaine action unique :** confirmer CI et intégrer cette empreinte à un export historique score-blind vérifié, puis mesurer les collisions descriptives sans qualifier l'historique de test indépendant.

- 2026-11-17 23:25 UTC — Relais MTDP-D1. HEAD de départ vérifié `a72641b13e381805798988d36af8d3ca798d58d8`; sept workflows de cette tête **success**, dont [D1](https://github.com/jfrancoiscollin/dilf/actions/runs/44190576620) et artefact `14376003469` (SHA-256 déclaré `932bd86245d1511acbe4a6e26c178b66de71a77b41b6c203301ac9475227d736`). Commit `4637f001cb846d816d2573a2b89ef39ca92d17bd` : deux tests d'intégration synthétiques reliant `canonical_successors.fingerprint` à `signature_collision_audit.audit`, vérifiant qu'une signature L identique peut cacher des successeurs divergents, qu'une signature affinée peut lever la collision et que des empreintes de transition identiques ne prouvent pas l'équivalence minimax. **Tests ajoutés, non exécutés dans cette session ; CI du nouveau HEAD non vérifiée.** Aucune nouvelle cohorte ni score stratégique. **Prochaine action unique :** vérifier le workflow D1 du commit `4637f001`, puis brancher un export historique FMJD non scoré sur l'audit, avec contrôle de complétude des successeurs.

- 2026-11-18 00:30 UTC — **MTDP-D1 B : garde de complétude des successeurs.** HEAD initial `3072e27145f96e7641ebb4d70b4125011c85737b` ; sept workflows associés `success`, dont D1 [#44199342888](https://github.com/jfrancoiscollin/dilf/actions/runs/44199342888). Commits `f5914ee8081d06f97b2de5216ec9f67bce4fe154` et `43bf1963bd03aeacd00876a6b85afa4302b29832` : `verified_successors.py` exige l'égalité exacte entre les actions du générateur légal indépendant et les clés de la carte action→successeur avant SHA-256 ; cinq tests synthétiques couvrent ordre, action manquante, action supplémentaire, doublon de l'oracle et successeur vide. **Tests nouveaux non exécutés localement, CI de ces commits non encore vérifiée.** Ce garde ne certifie ni le générateur FMJD, ni la canonicalisation des états, ni la validité stratégique. Aucune cohorte indépendante, top-K ou accélération Jass. **Suite :** confirmer CI, intégrer l'oracle FMJD épinglé à un export historique score-blind, sans toucher aux 78 cibles réservées.

- 2026-11-18 01:27 UTC — **MTDP-D1 B : intégrité de l'entrée JSONL d'audit.** HEAD initial `f1034383ec6fb571158b41bc255ab4b70e8eedcd` ; 7/7 Actions associées `success`, dont [D1 #44208501657](https://github.com/jfrancoiscollin/dilf/actions/runs/44208501657), artefact `14384294102` (digest annoncé `sha256:fa8531974f3ea5d0a4bd466f76e8b47e949cff6531546f44e49b6a183c48e0e6`). Commits `1562637cd0e65fa4629a535c852137d5cd4eea0c`, `e9c1f75e0d1e2eab6779c9fc01135f7c1c778848` : le parseur CLI de `signature_collision_audit.py` rejette maintenant les clés JSON dupliquées, y compris dans les signatures imbriquées ; trois tests synthétiques ajoutés. **Nouveaux tests non exécutés localement, CI de ces commits à confirmer.** Aucun nouveau corpus, score, top-K ni gain Jass. **Prochaine action unique :** confirmer CI puis brancher un export FMJD historique score-blind avec oracle légal épinglé et transitions exhaustives, sans toucher aux 78 cibles réservées.

- 2026-11-18 02:27 UTC — **MTDP-D1 B : réparation du CLI de collisions.** HEAD initial `5c05bb9caff7cf9ec3c50a8406d75c11fd03cf1a` ; 7/7 workflows `success` dont [D1 #44215970906](https://github.com/jfrancoiscollin/dilf/actions/runs/44215970906), artefact `14388361595` (`sha256:1d7df9f46946230c0ee144ce66f429c6f43467002b94c70bba4619d6ebe17a78`). Audit du fichier `signature_collision_audit.py` : séquence littérale `\\n` dans l'appel `json.loads`, invalide en Python ; les workflows précédents ne prouvent donc pas l'exécution du CLI. Commit `e8ded68cae668571880a63dd1dc7fe2478d9fa47` : correction de syntaxe ; `0b43e19fe8d9feb126832695dd9f2b5f0e80b705` : test bout-en-bout du CLI JSONL avec deux positions et une paire divergente. **Tests non exécutés localement ; nouvelle CI à confirmer.** Aucune cohorte indépendante, top-K ou accélération Jass. **Prochaine action unique :** vérifier CI du nouveau HEAD, puis connecter l'export historique FMJD non scoré avec oracle légal épinglé.

- 2026-11-18 03:29 UTC — **MTDP-D1 B : vérification des raffinements de signatures.** HEAD initial `20ff4bfeb301f077501d912b6690b545a23f0287` ; 7/7 workflows associés `success`, dont [D1 #44223431366](https://github.com/jfrancoiscollin/dilf/actions/runs/44223431366), artefact `14391931011` (`sha256:31bc699b06f010fa28a89a4f3423b31443ad7183635cf806dcd92dfcca4e939c`). Commits `680141bfcba1de79befe3c7b66be809ab58a8408`, `a7b6513fc5d2295da7901ea9cabd0648fee70287` : `decision_equivalence/refinement.py` contrôle qu'une signature affinée ne fusionne jamais des classes de la signature parente, et signale les contre-exemples ; cinq tests synthétiques couvrent séparation valide, fusion invalide, identité dupliquée, famille absente et champ de score interdit. **5/5 tests réussis localement sur copie textuellement équivalente ; CI des nouveaux commits non encore vérifiée.** Mesure purement structurelle, aucune cohorte FMJD nouvelle, aucune stabilité top-K ni accélération Jass revendiquée. **Prochaine action unique :** vérifier CI puis brancher les signatures progressives d'un export historique score-blind épinglé sur l'audit de raffinement et de collisions, sans utiliser les 78 cibles réservées.

- 2026-11-18 04:28 UTC — **MTDP-D1 B : comptage du risque de collision par raffinement.** HEAD de référence précédent `b9ecb3e99101eae638a3fb27b9429a3b0dec2884` ; 7/7 workflows associés `success`, dont [D1 #44230906993](https://github.com/jfrancoiscollin/dilf/actions/runs/44230906993). Commit [`9da0a042`](https://github.com/jfrancoiscollin/dilf/commit/9da0a04211559528c3a9d5b20207af9eb268c72f) : `decision_equivalence/refinement_collision_risk.py` compte par famille imbriquée les paires en collision, les paires à empreintes de successeurs divergentes et les paires inter-parties, avec rejet des raffinements qui fusionnent des classes. Deux tests synthétiques embarqués ; **non exécutés et non intégrés à CI**, aucun chiffre empirique nouveau. Le comptage inter-parties ne démontre pas l'indépendance des parties ; l'empreinte des successeurs doit être vérifiée par oracle FMJD avant interprétation. **Prochaine action unique :** exécuter ces tests dans CI et relier le comptage à l'export historique FMJD score-blind, sans confondre collisions structurelles et stabilité top-K.

- 2026-11-18 05:23 UTC — **MTDP-D1 B : tests de comptage désormais découverts par CI.** HEAD initial vérifié `7174e94cb0e0955c8f44a76df4a68b79ddf3d3a2` ; sept workflows associés `success`, dont D1 [#44237599919](https://github.com/jfrancoiscollin/dilf/actions/runs/44237599919), artefact historique `14398655476` (non réinterprété comme cohorte indépendante). Commit `788ad48c388ac02aeae6ab54491a93439ce2a33c` : six tests `unittest`/pytest découvrables pour `refinement_collision_risk.py` (référence exhaustive sur 30 tirages déterministes de 25 positions, cas de 10 000 positions/49 995 000 paires implicites, rejets des fusions, identités dupliquées et scores cibles). Commit `a5097bcb2ecb1a6068aaeb36395a9f9957dc0abd` : branchement explicite de ces tests dans `.github/workflows/mtdp-d1-score-blind-pcblues.yml`. **Tests non exécutés localement ; résultat du nouveau workflow encore à confirmer.** Les comptes ne démontrent pas stabilité top-K, équivalence minimax ni accélération Jass. Prochaine action : vérifier l'exécution effective de ces six tests en CI, diagnostiquer tout échec, puis intégrer les empreintes de successeurs FMJD vérifiées au corpus historique score-blind, sans utiliser les 78 cibles réservées.

- 2026-11-18 06:28 UTC — **MTDP-D1 B : intersection inter-parties / successeurs divergents.** HEAD initial `e7231ef1393789ea809bc67d9ce9f5906c980d3d` ; 7/7 workflows de ce HEAD `success`, dont [D1 #44244049889](https://github.com/jfrancoiscollin/dilf/actions/runs/44244049889), artefact historique `14401350138` (`sha256:b138982155342baf073dd9edb79b1585e9090591e5f901d644de16870ca2434c`). Commits `4bf16072`, `89ce9332`, `ecc72877` : `decision_equivalence/refinement_collision_risk.py` ajoute `cross_game_divergent_successor_pairs` par inclusion-exclusion exacte sur les groupes (sans matérialiser les paires) ; `test_refinement_collision_risk.py` étend la référence exhaustive et le cas connu. **Nouveaux tests non exécutés localement et CI de ces commits non confirmée**. Ce nombre est une intersection descriptive, non une preuve d'indépendance des parties ou d'équivalence des meilleurs coups ; aucun corpus FMJD nouveau ni gain Jass. **Prochaine action D1 unique :** confirmer CI sur le nouveau HEAD puis connecter les empreintes FMJD vérifiées d'un export historique score-blind, sans réutiliser les 78 cibles prospectives.

- 2026-11-18 07:26 UTC — **MTDP-D1 C : garde de partition score-blind.** HEAD initial connu `efbaf7758f590131de2a933926cccf051f650bc2` ; 7/7 workflows associés `success`, dont [D1 #44251676867](https://github.com/jfrancoiscollin/dilf/actions/runs/44251676867), artefact `14403504228` (`sha256:77c0dfeb60707c52f3ca8d79125cb08a672682b08ea50940f1bd5b09f600c867`). Commits `17896639fad9eaf62c81cd48be5db06e1519a4b3` et `061dde8e8849288c9db541240c2ae808a9fe49e2` : `decision_equivalence/partition_guard.py` et `test_partition_guard.py` contrôlent disjonction par game_id, ordre des ply, unicité position_id, exclusion explicite des identités réservées et champs de score, avec empreinte SHA-256 déterministe du manifeste ordonné. **Tests écrits mais non exécutés ; CI de ces nouveaux commits non confirmée.** Limites : identifiants de parties distincts ne prouvent pas l'indépendance réelle ; les identités réservées doivent être fournies depuis un manifeste prospectif vérifié ; aucune nouvelle cohorte gelée, aucun score top-K ni gain Jass. **Prochaine action D1 unique :** exécuter les tests du garde en CI et brancher un manifeste historique FMJD score-blind avec identités réservées vérifiées avant gel.

- 2026-11-18 08:33 UTC — **MTDP-D1 C : fermeture d'une fuite de scores imbriqués.** HEAD initial `30e7a75d6faa0409b11e92331ae80122f1f5d617` ; 7/7 Actions de ce HEAD `success`, dont [D1 #44258991902](https://github.com/jfrancoiscollin/dilf/actions/runs/44258991902). Audit du `partition_guard.py` : l'interdiction des champs cibles ne portait que sur les clés racines sensibles à la casse ; un `metadata.nested.best_move` ou `Scan_Score` pouvait passer. Commits `61f62f0cbae6ba0186da56d1df9a5beb4af0c52f` et `b5e4d351ad57b235da2ec77f8f9e7045bdd98843` : contrôle récursif des dictionnaires/listes/tuples, comparaison insensible à la casse, cinq cas de régression (quatre rejets et un témoin accepté). **Tests ajoutés mais non exécutés localement ; nouvelle CI non encore confirmée.** Aucun manifeste historique gelé, aucune cohorte indépendante ni gain Jass. **Prochaine action D1 :** confirmer l'exécution effective de ces tests en CI puis fournir un manifeste score-blind avec provenance et identités prospectives vérifiées.

- 2026-11-18 09:26 UTC — **MTDP-D1 C : couverture CI du garde score-blind.** Les 7 workflows du HEAD précédent `fc4fe53c873a57528dc6e14b5a0d693381ed8cdf` sont `success`, dont D1 [#44268160119](https://github.com/jfrancoiscollin/dilf/actions/runs/44268160119), mais le workflow D1 ne référençait pas `test_partition_guard.py` : son succès ne démontrait donc pas l'exécution des régressions de fuite de scores. Commit [`5e423d88`](https://github.com/jfrancoiscollin/dilf/commit/5e423d8887ecee8e071feaf11c4df9d1fdef6e97) : ajout explicite de `test_partition_guard.py` à la commande pytest du workflow `mtdp-d1-score-blind-pcblues.yml`. **CI du nouveau commit non encore confirmée ; aucun résultat scientifique nouveau.** Prochaine action : vérifier le nouveau job et ses logs, corriger toute erreur, puis préparer un manifeste historique non scoré avec identités prospectives vérifiées. Aucun corpus indépendant, top-K ou gain Jass revendiqué.

- 2026-11-18 10:32 UTC — **MTDP-D1 C : quarantaine des FEN exactement identiques.** HEAD initial `bf8864900ee5780af7da9013de0c24cd39ec026f` ; 7/7 workflows associés `success`, dont [D1 #44276020919](https://github.com/jfrancoiscollin/dilf/actions/runs/44276020919). Commits `455f58c`, `aae9f69`, `dc30d10` : nouveau garde `decision_equivalence/fen_overlap_guard.py`, tests synthétiques de doublons inter/intra-parties, chevauchement avec FEN réservées, fuite de scores imbriqués, déterminisme SHA-256 ; intégration explicite des tests dans le workflow D1 et déclenchement sur leur fichier. **Tests non exécutés localement ; CI du nouveau HEAD non encore confirmée.** Ce garde compare des chaînes FEN exactement égales : des encodages différents d'une même position peuvent lui échapper ; il ne prouve ni indépendance par partie ni absence de fuite sémantique. Aucun nouveau corpus, top-K ou gain Jass. **Prochaine action D1 unique :** vérifier le run D1 et ses tests, puis relier le manifeste historique aux FEN réservées vérifiées avant gel.

- 2026-11-18 10:46 UTC — **Relais fondation MTDP H:43 : validation FMJD et coordination D1.** HEAD initial `4a079c2dfdce31a0d44830f220f56b482536faaf` ; les 7 workflows de ce HEAD sont `success`, dont [downstream-compat #44286591295](https://github.com/jfrancoiscollin/dilf/actions/runs/44286591295), [CI #44286591439](https://github.com/jfrancoiscollin/dilf/actions/runs/44286591439) et [D1 #44286591309](https://github.com/jfrancoiscollin/dilf/actions/runs/44286591309). Journaux downstream vérifiés : `games_accepted=26`, `games_quarantined=0`, `positions_exported=1864` ; 18 tests d'intégration et 3 tests additionnels réussis, étapes d'analyse spatiale, collisions, successeurs et manifeste SHA-256 réussies. Journal D1 vérifié : commande pytest incluant `test_d1_fen_overlap_guard.py`, **81 tests réussis**. Le garde FEN exact est un contrôle de chaînes, non une preuve de non-chevauchement sémantique ni de validité stratégique. **Aucune expérience scientifique nouvelle, aucun correctif FMJD, aucune levée des cinq quarantaines historiques.** Prochaine action fondation unique : produire un diagnostic individuel reproductible des cinq prises historiques ambiguës avec identifiants de parties, coups, candidats de trajectoire et provenance, avant toute réconciliation des exclusions ; ne pas dupliquer les expériences D1.

- 2026-11-18 11:29 UTC — **MTDP-D1 C : quarantaine des alias FEN à espaces.** HEAD de référence `4a079c2dfdce31a0d44830f220f56b482536faaf` ; 7/7 Actions `success`, D1 [#44286591309](https://github.com/jfrancoiscollin/dilf/actions/runs/44286591309), artefact `14419162375` (`sha256:eab33ad34dc791433f84e0bfa0a4c12a56f236774b23f52e86926ea9b20b94af`). Commits `c7cc2a2d`, `b70fc1ae`, `366a8b87` : garde FEN renforcé pour rejeter les chaînes distinctes uniquement par espaces, aussi bien dans le manifeste qu'avec les FEN prospectives réservées ; trois tests de régression ajoutés. Le second commit corrige immédiatement une variable d'alias utilisée avant initialisation dans le premier ; seul le HEAD final doit être validé. **Tests nouveaux non exécutés localement, CI de ce HEAD non confirmée.** Cette normalisation textuelle conservatrice n'est pas une canonicalisation FMJD ; aucune indépendance, stabilité top-K ni accélération Jass démontrée. **Prochaine action D1 :** confirmer le run D1 du HEAD final, puis vérifier la provenance des FEN prospectives avant tout gel historique.

- 2026-11-18 11:41 UTC — **Relais fondation H:43 : nouvelle vérification FMJD et CI D1.** HEAD `c02a3c97d3859fa37a7f0befcfaa9e0d264338a5` ; 7/7 workflows associés `success`. Logs [downstream-compat #44295332233](https://github.com/jfrancoiscollin/dilf/actions/runs/44295332233) : `games_accepted=26`, `games_quarantined=0`, `positions_exported=1864`, 18 tests de compatibilité et 3 tests additionnels réussis ; toutes les étapes FMJD/spatiales/collisions/successeurs/manifeste réussies. Logs [D1 #44295332244](https://github.com/jfrancoiscollin/dilf/actions/runs/44295332244) : **84 tests réussis**, incluant le garde des alias FEN à espaces. Ces 0 quarantaines concernent le rejeu des parties, **pas** les cinq prises historiques ambiguës : leurs exclusions restent maintenues. Aucun résultat top-K ou stratégique nouveau. Prochaine action fondation : diagnostic individuel reproductible des cinq prises et réconciliation de provenance ; ne pas concurrencer D1.

- 2026-11-18 12:25 UTC — **MTDP-D1 C : unicité des identifiants dans le garde FEN.** HEAD initial `745b39eeb60db760ec83f2be30cba8a8f9075884` ; 7/7 workflows de ce HEAD `success`, dont [D1 #44297051830](https://github.com/jfrancoiscollin/dilf/actions/runs/44297051830), artefact `14423956567`. Audit : `fen_overlap_guard.py` rejetait les doublons FEN mais acceptait un même `position_id` associé à deux FEN différentes, y compris entre parties. Commits `8f6ba7febcc4a7f9a109c260dbb2549f9a151008` et `cb20fd06c4b2f9f9e96fe93bcb8a953e9803c218` : rejet global des identifiants réutilisés et trois tests synthétiques (deux rejets, un témoin). **Tests nouveaux non exécutés localement ; CI du nouveau HEAD à confirmer.** Ne prouve pas l'identité canonique FMJD ni l'indépendance des sources. Aucun nouveau corpus, top-K ni gain Jass. **Prochaine action D1 :** vérifier la CI puis construire un manifeste historique réellement sourcé avec exclusions prospectives vérifiées avant gel.


- 2026-11-18 12:47 UTC — **Relais fondation H:43 : validation détaillée après garde D1 d'identifiants.** HEAD initial `140cd14118ac0cd71f451d5c67b37d0644487f15` ; 7/7 workflows associés `success` ([CI #44303996265](https://github.com/jfrancoiscollin/dilf/actions/runs/44303996265), [FMJD #44303996067](https://github.com/jfrancoiscollin/dilf/actions/runs/44303996067), [D1 #44303996023](https://github.com/jfrancoiscollin/dilf/actions/runs/44303996023)). Journal du job FMJD `134800686476` vérifié : **26 parties acceptées, 0 partie rejetée, 1 864 positions exportées**, 18 tests de compatibilité et 3 tests supplémentaires réussis ; étapes analyses spatiales, collisions légales, successeurs et manifeste SHA-256 `success`. La quarantaine de rejeu vide (0 octet) ne lève **aucune** des cinq ambiguïtés historiques. Trois commits depuis `745b39e` touchent uniquement D1 et la coordination ; aucune correction FMJD nécessaire constatée. Les contrôles D1 sont une validation technique, non une preuve d'indépendance sémantique ni d'équivalence stratégique. **Prochaine action fondation unique :** identifier dans les sources les cinq prises ambiguës et produire leur diagnostic individuel reproductible (partie, coup, trajectoires candidates, provenance), sans modifier les exclusions ni reproduire D1. Ce commit ne possède pas encore sa propre CI confirmée.

- 2026-11-18 13:20 UTC — **Relais fondation H:13 : diagnostic individuel exécuté des cinq prises du candidat réservé.** HEAD initial `67d07842c09e863b247af1879df4d57102099a4d`, sept workflows PR terminés `success`, artefact candidat `14429007196` vérifié dans les métadonnées (SHA-256 `13f3b60f67d485e15f76f45439889f049978fd8d55ba741615cecd6da029a285`). Nouveau CLI `jass_benchmark/candidate_ambiguities.py`, export épinglé et moteur FMJD épinglé : parties 46/58/94/150/155 identifiées par leur Site, premier ply rejeté et deux trajectoires légales chacune. **Les cinq paires de trajectoires donnent chacune une même FEN successeur et les mêmes prises à ce ply** ; cela ne valide ni la route jouée ni la suite de la partie. JSON reproduit octet pour octet ; six tests ciblés réussis localement. Rapport `jass_benchmark/spatial-jass/replication/CANDIDATE_AMBIGUITIES_2026-11-18.md`. Le workflow de rejeu existant exécute le diagnostic et compare son résultat au JSON commis ; CI de la modification à confirmer. **Aucune levée des cinq quarantaines, aucun gel, aucun scoring ni campagne D1.** `fFgE7oED`, ses 78 cibles L/LCB et leurs FEN restent réservés au protocole prospectif Jass/Scan : ne pas les utiliser en D1 pour apprentissage, seuils ou sélection de signatures (risque de fuite). Prochaine action fondation : prouver la sélection chronologique, puis vérifier le catalogue Jass épinglé sur les actions cibles avant tout gel ; conserver le statut candidat si cette preuve manque. PC de Jeff non requis pour ce diagnostic.

- 2026-11-18 13:33 UTC — Relais MTDP-D1, axe exclusif signatures/corpus. HEAD précédent D1 `140cd141` : sept workflows terminés **success**, dont [D1 #44303996023](https://github.com/jfrancoiscollin/dilf/actions/runs/44303996023). Ajout du détecteur score-blind `decision_equivalence/game_overlap_guard.py` et de cinq tests synthétiques dans `test_game_overlap_guard.py`, commits `3498259e` et `c80ecd0a`. Il signale des fenêtres ordonnées de FEN partagées entre parties train/test sous des identifiants différents, complément du contrôle d'identifiants et des FEN exactes ; **ce n'est pas une preuve d'indépendance, ni une canonicalisation FMJD**. Cinq tests exécutés localement avec un substitut minimal de l'import `partition_guard` : 5/5 réussis ; CI du HEAD nouvellement publié non vérifiée. Aucun corpus FMJD nouveau ni score Scan exploité. **Prochaine action unique :** intégrer ces cinq tests au workflow D1 puis confirmer CI, avant audit de provenance d'un corpus historique réel.

- 2026-11-18 14:24 UTC — **Relais fondation H:13 : catalogue Jass score-blind exécuté, chronologie encore bloquée.** HEAD initial `0c1250f1eff233c1af1851c964b7a968b7092664`, sept workflows `success`, rejeu candidat [#44315083910](https://github.com/jfrancoiscollin/dilf/actions/runs/44315083910), artefact `14431772840` téléchargé et SHA-256 ZIP vérifié `c024ec5735b882a8819378e0b3b56968f8b35c6f34f28b1440784866057e5a57`. Le diagnostic des cinq prises du passage précédent est donc également confirmé en CI. Nouveau `candidate_jass_catalogue.py` : construction locale de l'exporteur légal Jass `cfe07fce`, oracle FMJD `0e5189fb`, checkouts propres ; **78 cibles, 46 sources distinctes, 124 positions, 759 actions cibles et 1 211 occurrences d'actions au total, zéro désaccord de bijection**. Les deux sources L/LCB de chaque cible partagent la même carte action→clé Jass ; aucune équivalence de successeurs ou de meilleurs coups déduite. Deux seeds produisent le même JSON ; **11 tests ciblés réussis localement**. Le workflow existant reconstruit et compare désormais ce reçu ; sa nouvelle CI reste à confirmer. Rapport `jass_benchmark/spatial-jass/replication/CANDIDATE_JASS_CATALOGUE_2026-11-18.md`. Calendrier actuel : plus ancien départ observé 17 novembre ; dernière ligne de page terminée 19 : 16 novembre. Ces sources ne couvrent pas le 14 novembre ; l'implémentation amont du calendrier ne sélectionne pas un mois historique. Comme fFgE7oED démarre exactement au cutoff, le risque chronologique restant concerne les candidats simultanés et leur ordre par ID. **Prochaine action fondation unique :** retrouver une liste durable complète à l'instant 14 novembre 11:00 UTC (candidats ex aequo et rejets) ; si irrécupérable, préenregistrer un nouveau cutoff futur avec acquisition contemporaine, sans certifier l'ancien candidat après coup. **Aucun gel, aucun scoring, aucune levée de quarantaine, aucune campagne D1.** fFgE7oED, ses 78 cibles et FEN restent réservés hors apprentissage/seuils/signatures D1 ; risque de fuite inchangé. PC de Jeff non requis ; aucune dépense payante engagée.

- 2026-11-18 14:28 UTC — **MTDP-D1 : intégration CI du détecteur de fenêtres entre parties.** HEAD initial `8d62f76fae1ccd9578927792e140e61e5fa2a494` ; [D1 #44324081230](https://github.com/jfrancoiscollin/dilf/actions/runs/44324081230) `success` pour ce HEAD, mais le workflow n'exécutait pas `test_game_overlap_guard.py`. Commit `b76e84b0f44d2fcc31f2561e17ac2905b9202d6c` : ajout explicite des cinq tests synthétiques au job D1 existant, sans modifier l'oracle, les données ni les cibles réservées. Les cinq tests avaient été exécutés précédemment seulement avec un substitut minimal de dépendance ; **validation CI de cette intégration à confirmer sur le nouveau HEAD**, ne pas compter le succès précédent comme preuve. Aucun nouveau corpus indépendant, aucune évaluation Scan ni accélération Jass. **Prochaine action D1 unique :** confirmer le run D1 qui contient effectivement ces cinq tests, corriger si nécessaire, puis auditer la provenance d'un corpus historique non scoré distinct de fFgE7oED.
- 2026-11-18 14:29 UTC — **Fondation H:13 : nouvelle réplication nommée préenregistrée avant les parties.** Le contrôle Jass du commit `8d62f76f` a passé localement 11 tests et les bijections des 78 cibles/46 sources ; CI complète en cours de confirmation. Pour poursuivre une expérience prospective sans réécrire la sélection historique non prouvée, `NAMED_ARENA_TOTAL_BUDGET_PREREGISTRATION_2026-11-18.md` fixe **exactement P1RUlfJc**, arène officielle standard 5+0 annoncée pour le **18 novembre 20:00–20:57 UTC (21:00–21:57 Paris)** ; métadonnées pré-départ et digest dans `P1RUlfJc-preregistration.json`, aucune partie ni résultat acquis pour la choisir. Il s'agit d'une étude distincte, sans prétention de premier tournoi au cutoff du 14 novembre, sans certification rétroactive de fFgE7oED et sans remplacement selon résultats. Même référence Scan successeur 16, source 12, trois bras natif/LCB/contrôle, budgets totaux 10k/50k/200k et plafond vérification 10 %, primaire 50k ; population entière et cas vide conservés. **Réserver dès maintenant tout P1RUlfJc hors D1** (parties, futures FEN, apprentissage/seuils/signatures/réduction de dimension), en plus de fFgE7oED et de ses 78 cibles qui restent bloqués et réservés. **Prochaine action fondation unique avant la fin :** préparer le paramétrage reproductible du CLI (ID/digests/exclusions supplémentaires fFgE7oED), avec tests synthétiques et sans changer les sélecteurs. Après 20:57 UTC seulement, vérifier fin/format, acquérir deux exports finaux, restaurer les exclusions, rejouer et geler avant tout scoring. Avant la fin, ne pas collecter un export partiel comme gel et ne pas lancer de recherche. PC de Jeff non requis à ce stade.


- 2026-11-18 14:33 UTC — **Vérification de compatibilité D1 par le relais fondation :** les cinq tests existants `decision_equivalence/test_game_overlap_guard.py` passent dans le vrai environnement du dépôt, avec les imports réels (pytest, 5/5 en 0,05 s), sans substitut de `partition_guard` et sans donnée cible. Cela ne constitue aucune campagne D1 ni preuve d’indépendance d’un corpus. Les commits concurrents `b76e84b0` et `ae3e6646` ont été préservés lors du rebasage de la nouvelle inscription prospective. Le run candidat `44324081120` a été annulé par la mise à jour concurrente ; le run équivalent `44324826343` est déjà actif, donc aucune relance en doublon.

- 2026-11-18 14:37 UTC — **Fondation : validation distante confirmée avant publication du nouveau préenregistrement.** HEAD `ae3e6646511d71ce6f88c3e7e236804c6b95d9d8` : **7/7 workflows success**, dont candidat [#44324826343](https://github.com/jfrancoiscollin/dilf/actions/runs/44324826343). Logs du job `134873331185` vérifiés : **11 tests passés**, même SHA-256 du replay `e9de3a4c…118a16b`, mêmes 124 positions/78 cibles/46 sources/759 actions cibles, comparaison complète des reçus réussie hors empreinte exécutable dépendante du compilateur. Artefact `14436224802`, ZIP SHA-256 `90288b96c19e73742402ab68ed75b2bcfb9588553054f9e32809d2f4496e46f4`. Les cinq quarantaines et les réservations D1 sont inchangées. Le commit qui publie cette confirmation et la sélection future ne modifie que documentation/métadonnées de préenregistrement ; aucun résultat de meilleur coup ou de gain à budget égal nouveau. Prochaine action : paramétrage et tests pour P1RUlfJc avant le départ, acquisition finale après 20:57 UTC seulement, gel avant scoring.

- 2026-11-18 14:57 UTC — **Fondation H:13 : préparation vérifiée des entrées P1RUlfJc, sans parties cibles.** HEAD initial `2c17363efbb3f8114a549327ae4df07ae1e6e142` : 7 workflows `success`, artefact candidat `14437039139` et métadonnées de digest vérifiés ; aucun job équivalent actif. Nouveau `named_arena_inputs.py` : sélection/protocole/provenance épinglés par SHA-256 ; registre de **22 PDN, 4 375 parties, 4 341 IDs publics, 4 224 empreintes de tokens et 205 098 FEN confirmées**. Les deux PDN nationaux sont restaurés depuis le dépôt adaptateur épinglé avec hashes concordants. fFgE7oED apporte 14 170 FEN de préfixes légaux ; arrêt avant la première ambiguïté, **cinq quarantaines entières inchangées**, aucune continuation devinée. Deux seeds reproduisent le registre à l'octet : `25b3ca1a6f0a096c264c8f136135a37fd7d5bb23c04af76a39b4915a611d192e`. Le mode final refuse avant 20:57 UTC, exige métadonnées terminées exactes, deux fichiers distincts identiques et reçus d'acquisition cohérents ; il ne déclare jamais un gel. **26 tests ciblés réussis localement, dont 15 nouveaux** ; workflow existant enrichi pour les exécuter et archiver le registre complet, nouvelle CI à confirmer. Rapport `NAMED_ARENA_INPUT_GATES_2026-11-18.md`. Les empreintes de tokens ne remplacent pas les trajectoires FMJD canoniques et les FEN confirmées ne prouvent pas seules l'indépendance sémantique. **Prochaine action unique :** raccorder les sélecteurs inchangés au registre et au reçu d'entrée final, avec garde des trajectoires complètes et catalogue Jass paramétré ; reproduire fFgE7oED comme régression. Aucun export P1RUlfJc acquis, aucune population cible, aucun scoring ni gel ; fin réelle à confirmer après 20:57 UTC seulement. **Réservations D1 : fFgE7oED entier et 78 cibles, P1RUlfJc entier et futures FEN**, hors apprentissage, seuils, signatures et réduction de dimension. PC de Jeff non requis à ce stade.

- 2026-11-18 15:00 UTC — **Complément du garde final avant le départ :** refus explicite de métadonnées `isFinished=true` avec `secondsToStart` non nul ; fixture synthétique terminée corrigée et une régression ajoutée. **27 tests ciblés réussis localement**, dont 16 nouveaux. Sélection, références, budgets et registre inchangés ; aucun export cible acquis. Le job de validation du premier commit est remplacé automatiquement par celui du correctif, sans relance manuelle équivalente.

- 2026-11-18 15:25 UTC — **MTDP-D1 : régressions du garde de fenêtres inter-parties.** Contrôle du HEAD précédent `ae3e6646511d71ce6f88c3e7e236804c6b95d9d8` : les 7 workflows associés sont `success`, notamment [D1 #44324826276](https://github.com/jfrancoiscollin/dilf/actions/runs/44324826276), artefact `14436127958` (digest `sha256:1d9449b02f6d934c9f5d32d6827cd4be4937803ea4b032b316139d3ffc85a2c7`). Ce run inclut explicitement les cinq tests `test_game_overlap_guard.py`. Commit `a65bf08e18d2eb2df5de6710832c333b2a2f15a4` : trois nouveaux cas de régression (même split non signalé, regroupement trié de plusieurs alias test, fenêtres invalides y compris bool/float). Sept assertions paramétrées reproduites localement avec une copie du détecteur et un substitut minimal de `partition_guard` : 7/7 ; **le nouveau commit reste à confirmer par CI réelle**. Aucun corpus indépendant ni scores utilisés. Les arènes prospectives `fFgE7oED` et `P1RUlfJc` restent exclues de D1. **Prochaine action unique :** confirmer la CI du nouveau test, puis auditer un manifeste historique non scoré avec identifiants et provenance vérifiés, sans réutiliser les cohortes déjà connues.
- 2026-11-18 15:28 UTC — **Fondation H:13 : sélecteur partagé et trajectoires historiques raccordés, sans cibles futures.** HEAD initial `49280b69eccb2c087f800edccb277102c429ca61`, sept workflows `success`, artefact `14438494531` et digest publiés vérifiés ; aucun job équivalent actif au départ. Extraction du sélecteur L/LCB inchangé : le rapport fFgE7oED complet reste **identique à l'octet** (SHA `e9de3a4c…118a16b`) sous seeds 7/61. Nouveau `named_arena_replay.py` : **4 375 parties historiques rejouées, 4 051 trajectoires complètes distinctes, 151 doublons, 173 quarantaines entières** ; leurs préfixes légalement vérifiés couvrent **411 980 FEN** et englobent le registre précédent de 205 098. Aucun état après ambiguïté n'est deviné ; aucun fingerprint complet pour une partie rejetée. L'index reproduit sous deux seeds est épinglé à `eafd1e7b1c447b69f96d307b38a1c7c0fbd8fa9dd9b68f8afe555e3faa02d1b6`, résumé commis et index complet archivé par le workflow existant. Le mode `proposal` raccorde garde final, registre, index, rejet par IDs/tokens/trajectoires, rejeu atomique, sélecteur existant et catalogue Jass ; appel réel confirmé bloqué avant lecture de PDN cible avec l'horloge courante. Il émet toujours une proposition non gelée, avec versions, hashes, appartenances de parties et actions complètes ; références Scan 12/16 et budgets totaux inchangés. **39 tests ciblés réussis localement, dont 12 nouveaux**, CI nouvelle à confirmer. Rapport `NAMED_ARENA_REPLAY_PIPELINE_2026-11-18.md`. **Prochaine action unique avant la fin :** répéter synthétiquement acquisition des reçus HTTP et proposition/publication de gel de bout en bout ; après 20:57 UTC seulement acquérir les exports finaux réels, confirmer fin/format, reproduire et publier le gel avant scoring. Réservations D1 inchangées : fFgE7oED entier/78 cibles et P1RUlfJc entier/futures FEN, aucun apprentissage/seuil/signature/réduction de dimension sur ces données. Pas de campagne D1 ni résultat indépendant de meilleur coup nouveau. PC de Jeff non requis.

- 2026-11-18 15:31 UTC — **Coordination de publication fondation/D1 :** commits concurrents D1 `a65bf08e` et `2d83f21e` préservés au rebasage ; leurs nouveaux tests ont également été exécutés avec les imports réels du dépôt, sans substitut. Résultat combiné : **47 tests et 5 sous-tests réussis**, dont les 39 contrôles prospectifs ci-dessus. Aucune donnée réservée utilisée dans un essai D1 et aucune modification de ses détecteurs.

- 2026-11-18 16:33 UTC — **D1 : correction de faux positifs de fenêtres FEN non contiguës.** HEAD initial `6b1969d47a221209b9f107011e4e8c12c428d71c` : 7/7 workflows `success`, dont D1 `44336859696`, artefact `14441218851` (`sha256:41c9ceffc2e8ecd56dd83b4cba07bb17f1fafdc283015b0de9037651aa80ae4d`). Le détecteur `game_overlap_guard.py` utilisait des lignes adjacentes même lorsque leurs `ply` sautaient des coups : cela pouvait produire une fausse fenêtre commune inter-parties. Commit `3192153b` : seules les fenêtres de plies strictement consécutifs sont désormais indexées ; commit `ca156fec` : deux régressions synthétiques (rejet d'une séquence trouée, conservation d'une sous-fenêtre réellement contiguë). Les anciens tests à plies contigus restent inchangés. **Nouvelle CI non encore confirmée ; aucune cohorte indépendante, aucun score ni gain Jass revendiqué.** fFgE7oED et P1RUlfJc intégralement réservés hors D1. Prochaine action : confirmer la CI et auditer les FEN historiques non scorées avec provenance complète.

- 2026-11-18 17:29 UTC — **D1 : tests des frontières de détection d'alias.** HEAD de référence au début du passage `ea79c425150eae5820e65bb82604b1202eeddae6` : sept workflows `success`, dont [D1 #44348705842](https://github.com/jfrancoiscollin/dilf/actions/runs/44348705842). Commit [`fc8ffea4`](https://github.com/jfrancoiscollin/dilf/commit/fc8ffea45777d74028dcdd3d07e9d218e287270d) : trois régressions synthétiques ajoutées à `decision_equivalence/test_game_overlap_guard.py` (identifiant de partie partagé entre splits rejeté, fenêtre commune avec décalage de ply acceptée, frontière fenêtre 2 vs 3). **Ces nouveaux tests ne sont pas encore confirmés par la CI de ce commit** ; aucune cohorte indépendante, score Scan ou gain Jass revendiqué. Les 78 cibles fFgE7oED et P1RUlfJc restent réservées. **Prochaine action unique :** confirmer la CI de ce commit, puis auditer un manifeste historique FMJD non scoré avec exclusions et provenance vérifiées.

- 2026-11-18 18:24 UTC — **D1: protocole d'évaluation score-blind ajouté, sans scores ni cohorte.** HEAD initial `89aa123f88eefaf5eac8242dea95aadfc1cabaa4` : 7/7 workflows `success`, dont D1 [#44359409204](https://github.com/jfrancoiscollin/dilf/actions/runs/44359409204), artefact `14453273865`, digest `sha256:b7d47ad162a853fd73ca72b8a4731d4aede17571dde676b279c6811f76d6e3e7`. Les trois tests du précédent commit `fc8ffea4` sont donc couverts par cette CI. Nouveau `decision_equivalence/D1_EVALUATION_CONTRACT.md` (commit `38cfed5985bbb233f719ffdc78d65a8181e6851a`) : unités d'analyse, exclusions fFgE7oED/P1RUlfJc, split par parties/tournois, témoins, top-1/top-3, regret, tau-b, bootstrap par partie, fallback exact et barrière avant Jass. **Proposition de protocole non gelée** : seuils numériques d'acceptation et manifeste historique restent à préenregistrer et hacher avant scores. Aucune cohorte nouvelle, aucun score, aucun gain Jass. Prochaine action D1 : auditer la provenance d'un manifeste historique non scoré et figer les seuils avant scoring.

- 2026-11-18 19:27 UTC — **Fondation H:13 : enregistrement de la préparation acquisition/publication encore locale.** HEAD initial `59618930d2cec66537d3275fbc6c94bbee61d157`, sept workflows `success`, artefact candidat `14459370454` et digest publiés vérifiés ; aucun job équivalent actif. Les outils d'acquisition et de gel préparés localement au passage interrompu n'étaient pas publiés ; modules/tests reconstitués et **59 tests ciblés réexécutés avec succès**, dont 20 d'acquisition/publication. Collecteur après 20:57 UTC seulement, reprise HTTP/paires divergentes avec conservation des tentatives ; préparation par processus seeds 7/61 ; export exact des octets ; vérification exigeant un vrai commit ancêtre de la branche de recherche fraîchement récupérée via sa ref nommée (pas FETCH_HEAD partagé). Un commit local seul, un manifeste préparé et tout paquet synthétique ne peuvent pas autoriser le scoring. Répétition CI programmée avec vrais FMJD/Jass mais HTTP/horloge simulés, cas fabriqué attendu 1 cible/10 actions ; **intégration actuelle à confirmer, non déduite de l'ancien espace local**. Rapport `NAMED_FREEZE_REHEARSAL_2026-11-18.md`. Contrat D1 nouvellement publié lu : proposition score-blind, aucune modification de ses campagnes ou seuils. **Prochaine action unique :** raccordement de l'exécution natif/LCB inchangé/contrôle à la preuve de publication et vérification des binaires Scan/Jass, smoke de budgets synthétique ; après 20:57 UTC seulement acquisition finale réelle, préparation, publication et vérification du gel avant tout scoring. Réservations D1 inchangées : fFgE7oED entier/78 cibles et P1RUlfJc entier/futures FEN, hors apprentissage/signatures/seuils/réduction de dimension. Aucun export cible réel, aucun gel réel ni résultat nouveau de meilleur coup. PC de Jeff non requis pour ces contrôles.

- 2026-11-18 19:30 UTC — **D1 : proposition de seuils numériques falsifiables, non gelée.** HEAD initial `b7fb22ac88791573943d7b478512419ab0cbf85f`. Sur ce HEAD, 6/7 workflows success, `mtdp-preregistered-candidate-replay` #44380959517 encore in_progress au contrôle ; D1 #44380959554 success. Commit `6dafdc925a22367d6596572559bd4d25815b02b9` ajoute `decision_equivalence/D1_NUMERICAL_GATES_PROPOSAL.md` : seuils de taille de cohorte, couverture, rappel top-3 apparié, regret, erreurs tactiques et critères d'arrêt. **Proposition non préenregistrée/gelée : aucun score cible consulté, aucun corpus historique admis, aucun résultat Jass.** Les 78 cibles fFgE7oED et P1RUlfJc restent exclus. Prochaine action unique : auditer provenance et disponibilité d'un corpus historique FMJD distinct, puis geler manifestes et seuils AVANT tout scoring.

- 2026-11-18 19:39 UTC — **Fondation H:13 : répétition complète validée à distance et outils publiés.** Commit `b7fb22ac88791573943d7b478512419ab0cbf85f` publié ; commits D1 concurrents `6dafdc9`/`069d5c2` préservés, nouvelle proposition de seuils lue. HEAD `069d5c278bfa419efe7a614f404f6a8754e37404` : **7/7 workflows success**, candidat [#44381395324](https://github.com/jfrancoiscollin/dilf/actions/runs/44381395324), job `135074404038`, **59 tests passés**. Répétition avec vrais FMJD/Jass mais HTTP/horloge simulés : seeds 7/61, **1 cible fabriquée/10 actions**, trois GET simulés, CRLF conservés, trois hashes proposition/manifeste/enveloppe identiques et refus production confirmé ; `scientific_freeze=false`. Artefact `14462853825` effectivement téléchargé : ZIP SHA `5b2130472bd92b9eabecde81c7a384d85a4cdbafd3a7997561fa654f81c54c8e`, 6 823 874 octets ; inventaires et hashes des deux paquets vérifiés après téléchargement. Ancien replay fFgE7oED `e9de3a4c…118a16b` inchangé, quarantaines conservées. Preuves dans `named-freeze-rehearsal-ci-2026-11-18.json` et rapport actualisé. **Prochain contrôle unique :** adaptateur source/target/recherches exigeant la preuve du commit publié et chargeant ses blobs, puis pins Scan (binaire/eval/ini) et deux runners Jass ; `jass_scan_reference` générique ne constitue pas cette preuve et le gate d'archive reste limité aux cinq arènes. Acquisition réelle P1RUlfJc seulement après **20:57 UTC/21:57 Paris**, métadonnées finales + deux exports concordants, gel avant tout scoring. Aucun export cible réel, gel réel ou résultat nouveau de meilleur coup ; PC de Jeff non nécessaire aux validations exécutées. **Réservations D1 inchangées : fFgE7oED entier/78 cibles et P1RUlfJc entier/futures FEN**, aucune campagne D1 dupliquée. Le run initial a été remplacé automatiquement lors des commits D1, sans relance manuelle en doublon.

- 2026-11-18 20:21 UTC — **Fondation H:13 : garde d'exécution des références préparé, Scan réel accessible à distance.** PR #43 ouverte/draft, HEAD initial `8dc96ccd719272882d3b70d495cbba38461ed1e8` : 7/7 workflows success, candidat `44383368974`, artefact `14465230867` et digest publiés consultés ; aucun job équivalent actif. Contrats et proposition de seuils D1 relus. Nouveau `named_arena_execution` : vérification distante du commit publié avant toute entrée moteur/sortie, manifeste lu dans Git et lié au reçu, méthode courante identique au gel, pins Scan binaire/eval/ini et FMJD checkout/import, profondeurs source/target 12/16 sans override, sorties complètes exclusives. **79 tests ciblés locaux passés**, dont 20 nouveaux ; le test de Git distant isolé confirme aussi le chargement du blob commis malgré un manifeste local altéré. Dispatch positif testé avec moteurs/preuve simulés, donc pas une référence réelle de cohorte. Binaire Scan exact restauré à `7aae17e` : trois hashes concordants, démarrage réel et scores de la position initiale aux profondeurs 12/16 réussis (-1/0, smoke uniquement), sans donnée P1RUlfJc ni estimation de qualité. Rapport `NAMED_PUBLISHED_REFERENCE_GATE_2026-11-18.md`, JSON du smoke et workflow enrichi ; nouvelle CI à confirmer. **Prochain contrôle unique :** raccordement du runner Jass nommé à la même preuve et au seul paquet source, attestations des deux builds patchés et trois bras à budgets totaux sur cas fabriqué. Après 20:57 UTC/21:57 Paris seulement, acquisition finale, reproduction/publication/vérification du gel avant scoring. Réservations entières fFgE7oED et P1RUlfJc maintenues hors D1, aucune campagne D1 dupliquée. PC de Jeff non requis pour le moteur Scan effectivement exécuté.
