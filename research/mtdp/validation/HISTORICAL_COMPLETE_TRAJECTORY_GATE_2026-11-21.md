# H13 — exclusion des trajectoires complètes connues

Le raccord conserve le cache SHA2565cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7 et la fonction historique d’empreinte inchangés. Aucun module D1 n’est modifié.

Le précontrôle source/index/position existant précède un rejeu par source/index distinct. Toute empreinte de trajectoire complète déjà connue fait rejeter le lot. Les octets du PDN sont authentifiés avant rejeu ; indices absents, source modifiée, coup illégal/ambigu et tokens après résultat font échouer le contrôle. L’observation d’une position précoce ne permet pas d’ignorer une continuation illégale. Le contrôle FEN historique continue de précéder ce parcours.

Le CLI produit un audit descriptif, sans autoriser l’admission. Avec les règles FMJD0e5189fbb251bf5eaf2e613d0f878bb17c740311, les26 parties du PDN PC Blues épinglé025ad0a1a9ddcf508e3284eef65eb1cf76ebf7763d1241a127432f99eac3d8be sont légalement rejouées et leurs26 empreintes sont retrouvées parmi les4 468 connues. Le rapport JSON versionné est comparé octet pour octet en CI.

Reproduction dans un environnement avec le dépôt FMJD épinglé dans PYTHONPATH :

```bash
python -m research.mtdp.historical_trajectory_gate --cache CACHE.json --pdn data/exports/pcblues/pcblues_games.pdn --pdn-sha256 025ad0a1a9ddcf508e3284eef65eb1cf76ebf7763d1241a127432f99eac3d8be --adapter ADAPTER --output /tmp/trajectory-audit.json
cmp /tmp/trajectory-audit.json research/mtdp/validation/historical-complete-trajectory-audit-2026-11-21.json
MTDP_HISTORICAL_FEN_CACHE=CACHE.json MTDP_HISTORICAL_ADAPTER=ADAPTER MTDP_REQUIRE_HISTORICAL_TRAJECTORIES=1 python -m pytest -q research/mtdp/tests/test_historical_trajectory_gate.py
```

Validation locale initiale :28 tests réussis (pont FEN réel, précontrôle et nouveau raccord), puis ajout d’un test positif vérifiant que le dédoublonnage source/index ne confère jamais l’indépendance. Le workflow dédié exige le cache et les règles réels ; le test réel peut être sauté uniquement hors de ce workflow. Les tests synthétiques isolant le raccord utilisent une vue FEN artificielle explicitement vide, jamais un cache de production modifié.

Limites : il s’agit des trajectoires complètes enregistrées, y compris des parties inachevées, pas de la complétude de l’ensemble du corpus. Aucune nouvelle cohorte, signature, score, équivalence minimax ou accélération n’est mesurée. Prochaine action : réconcilier les alias publics et empreintes de notation des25 sources historiques avant toute qualification indépendante.

## Validation distante et artefact vérifiés

Code[1ec5add](https://github.com/jfrancoiscollin/dilf/commit/1ec5add6d233b5bfd6f96941a5105a0743f38847), contrôlé sur son successeur documentaire D1[786952c](https://github.com/jfrancoiscollin/dilf/commit/786952c2851c6151648df233ef9a21cc8b01e7dd), sans différence des fichiers H13 : huit workflows réussis, dont [historique44956890927](https://github.com/jfrancoiscollin/dilf/actions/runs/44956890927). Le premier run historique44956569874 a été annulé par cette mise à jour concurrente ; aucun doublon n’a été relancé. Les15 tests dédiés passent sans saut, ainsi que les8 tests du pont FEN réel. Le rapport confirme26/26 parties connues parmi4 468 trajectoires.

Artefact14727059782 téléchargé et recalculé :14 756 988 octets, ZIP SHA256200444ff6e5567c282284568a5c40b207e9502a635353f839e27537f1efeb559. Le cache conserve son SHA5cb4247… ; rapport FEN et nouveau rapport des trajectoires sont chacun identiques octet pour octet aux fichiers versionnés. Nouveau rapport SHA256aa0305571cd475c3291c394ec98eed3fd1ad495c99d2509faacbe77224d0becf. Détails dans historical-complete-trajectory-ci-2026-11-21.json.

Le préenregistrement D1 concurrent est préservé. Ces preuves ne qualifient pas une nouvelle cohorte ; les alias publics et de notation restent la prochaine réconciliation H13.
