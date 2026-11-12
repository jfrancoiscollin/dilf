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
