# H13 — Rejeu corrigé des anciennes parties strictes, 26 novembre 2026

Protocole publié avant exécution : e73b5d685b9a695e7dbcb8c9f489dcc40b207112. PR43 ouverte/draft ; au départ b9e847a, neuf workflows success, aucun équivalent actif. Le rejeu de référence cc11f546 annulé a été remplacé par le rejeu b9e847a réussi ; aucune relance technique nécessaire.

**4 634/4 634 dossiers complètement rejoués sous king-origin-v1**, un seul plateau à chaque ply, aucune nouvelle ambiguïté de chemin, zéro arrêt ou borne atteinte. Toutes les empreintes de suites de plateaux correspondent exactement aux empreintes historiques figées (4 468 empreintes distinctes). Les 435 262 FEN distinctes visitées par ces dossiers, réunies aux 21 657 possibilités des 190 quarantaines déjà contrôlées, donnent exactement **455 582 FEN**, hash d’ensemble 9db87b4e41804e95e0a376a6bef465d93b448f50698a53da237cc9bfd1f29f2a. Aucun FEN nouveau hors du registre conservateur, aucun FEN ancien ou du registre perdu. Le nouvel inventaire hors registre est donc vide (SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855).

## Périmètre et provenance

Population exhaustive des statuts indexed/duplicate authentifiés parmi 4 824 dossiers de 25 sources du cache ancien. Authentification des trois membres historiques, du cache 5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7 et de chaque PDN par digest. Artefact historique restauré : run 45776093044, artefact 15096795905, ZIP SHA-256 bccb48d7ee7efd7070ed5a764873ac6e623a0dadf21ce2c8cc480b445f89edb4. Deux anciens fichiers de clubs ne sont pas présents dans ce ZIP ; ils proviennent du checkout FMJD épinglé, avec les digests historiques inchangés. bind_sources accepte ce répertoire supplémentaire explicitement ; aucune source substituée selon son nom. Les autres manques sont couverts par les PDN déjà versionnés du dépôt.

Factory corrigée explicite : king-origin-v1, source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d. Bornes inchangées : 128 plateaux/frontière, 100 000 applications/dossier. L’exploration conserve toutes les actions correspondant à chaque token. Le sérialiseur historique state_to_fen/LF sans LF final est utilisé seulement si chaque ply authentifié a un seul plateau. Aucun chemin joué n’est deviné ; les 190 quarantaines sont réutilisées depuis leur preuve corrigée séparée, sans reclassement.

## Reproduction et validations

Deux exécutions locales complètes, hashseeds défaut et 731, identiques à l’octet. 24 unittest passent : huit nouveaux contrôles et seize régressions de frontières, liaison brute, correction et parseur d’oracle. Les nouveaux tests couvrent divergence suivie de fusion, plusieurs chemins vers un même plateau, troncature/bornes, chronologie et sérialiseur, digests d’entrées, répertoire brut supplémentaire et refus de corruption. **Reproduction distante confirmée** : implémentation 48ecfa16ff4d2f62e2629cd801322ed61130316a, [run 45782900246](https://github.com/jfrancoiscollin/dilf/actions/runs/45782900246), job 139782425101 success. 24 tests réussis ; deux rejeux complets sous Python 3.11 distant (Python 3.12 local), chacun d’environ une minute, puis comparaisons des trois fichiers et du résumé versionné réussies. Artefact 15099585795 téléchargé, ZIP 259 523 octets SHA-256 55ff5143ac40d37f943b0891bf627bf6287aac004114bf006dbcc2d3b46eae6c conforme GitHub. Tous ses membres — rapport complet, résumé, inventaire vide — sont identiques aux deux sorties locales. Preuve structurée versionnée : validation/king-origin-strict-history-ci-proof-2026-11-26.json. Le contrôle historique de compatibilité déclenché par l’ajout du répertoire brut supplémentaire est également success (run 45782899903).

Rapport complet par dossier conservé dans l’artefact de reproduction : strict-history-replay.json, 3 479 102 octets, SHA-256 718273685d16b7b9f99a56ac1f8d6602ef60609983c7e20909a478ddc2c74afb. Résumé versionné : validation/king-origin-strict-history-summary-2026-11-26.json, 6 609 octets, SHA-256 6a4262d763603f09ac760cbdbe586f0b24507f97f9e99c975d2bdef49f627f48. Il lie le rapport complet et toutes les entrées.

```sh
python -m research.mtdp.king_origin_strict_history \
  --root . --base-dir historical-input --adapter fmjd \
  --corrected-inventory corrected-input/possible-board-inventory.jsonl \
  --output-dir result
python -m unittest research.mtdp.tests.test_king_origin_strict_history \
  research.mtdp.tests.test_historical_quarantine_frontier \
  research.mtdp.tests.test_historical_base_quarantine_frontier \
  research.mtdp.tests.test_king_origin_correction \
  research.mtdp.tests.test_return_capture_oracle
```

## Portée scientifique et suite

Ce résultat ferme le manque de rejeu corrigé des dossiers stricts parmi les **25 sources connues**. Il ne prouve pas la complétude globale de l’historique MTDP. L’égalité des suites de plateaux jouées n’étend pas les validations des ensembles complets de coups légaux Jass à ces 435 262 FEN : des coups non joués peuvent différer sans changer le rejeu. Aucun score ancien recalculé, aucun gain ou équivalence décisionnelle nouvelle revendiqués. Cache, règles par défaut, anciens scores, 190 quarantaines et candidat frais 145/7 inchangés.

Contrôle clos. Ne pas relancer ce même rejeu : prochain contrôle H13 justifié, délimiter les états historiques avec dame au trait hors des inventaires déjà comparés à Jass, puis préenregistrer un contrôle indépendant des racines légales sur ce reste. Aucun score ni ajustement D1 pendant cette qualification de règles. Licence/provenance et indépendance de la source fraîche restent portes D1 séparées avant gel. uDIrrl1c entier toujours brut non admis ; aucune nouvelle réservation H13, quatre événements antérieurs exclus. PC de Jeff non requis.
