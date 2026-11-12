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
