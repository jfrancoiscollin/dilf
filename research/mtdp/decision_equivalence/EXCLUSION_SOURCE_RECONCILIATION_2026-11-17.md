# D1-C — matrice de réconciliation des exclusions (2026-11-17, 14:28 UTC)

**État : non prêt au gel.** Cette matrice est un inventaire des preuves à obtenir, pas un registre JSONL, ni une cohorte nouvelle. Elle n'autorise ni scoring Scan ni utilisation des 78 cibles réservées.

| Groupe obligatoire | Source candidate / piste vérifiable | Preuve actuellement disponible | Preuve manquante avant gel |
|---|---|---|---|
| `pcblues_historical` | Rejeu FMJD PC Blues des 26 parties, workflow `downstream-compat` | Historique : 1 864 observations / 1 750 FEN distinctes ; D1 run [44093233070](https://github.com/jfrancoiscollin/dilf/actions/runs/44093233070), artefact [14331254966](https://github.com/jfrancoiscollin/dilf/actions/runs/44093233070/artifacts/14331254966) | Source des 26 parties épinglée, identités de partie/trajectoire/FEN exportées, comptage et hash du registre |
| `scan_depth8` | Rapports historiques `research/mtdp/BEST_MOVE_BASELINE_2026-11-11.md` | Scores historiques documentés ; ne pas les traiter comme indépendants | Manifeste exhaustif des positions et de leurs parties, SHA source et registre |
| `scan_depth12` | `research/mtdp/BEST_MOVE_DEPTH_SENSITIVITY_2026-11-11.md`, `TOP_THREE_TRANSFER_RESULTS_2026-11-11.md` | Re-scoring et transferts historiques documentés | Union dédupliquée des parties/FEN réellement évaluées, y compris jeux rapides, SHA et registre |
| `jass_benchmarks` | `research/mtdp/jass_benchmark/README.md` et manifestes associés | Benchmark préexistant distinct de D1, avec provenance à réconcilier | Toutes les parties des bras évalués et contrôles, identités complètes, SHA et registre |
| `ffgE7oED_reserved` | Manifeste prospectif réservé du tournoi fFgE7oED, sous responsabilité de l'autre relais | 78 cibles réservées déclarées ; aucune réutilisation autorisée | Obtenir uniquement le manifeste d'exclusion approuvé (parties entières + FEN/trajectoires), SHA et registre, sans ouvrir les scores |

## Procédure fail-closed et critères de sortie

1. Pour chaque ligne, retrouver le fichier source **réel**, son commit ou identifiant d'artefact et son SHA-256. Une référence à un rapport agrégé ne suffit pas.
2. Exporter toutes les identités connues en JSONL (partie, trajectoire SHA-256, FEN SHA-256), en conservant les doublons inter-groupes dans les sources mais en les dédupliquant dans l'union d'exclusion. Une identité sans provenance doit être bloquante.
3. Recompter parties, positions et lignes, documenter les différences entre observations et FEN distinctes. Vérifier explicitement les 78 cibles **et toutes leurs parties**, sans consultation des scores.
4. Générer un inventaire avec `group/path/sha256/rows` et exécuter `python -m research.mtdp.decision_equivalence.registry_coverage INVENTORY.json`. Ce contrôle prouve l'intégrité, **pas** l'exhaustivité : comparer ensuite chaque groupe à son source original.
5. Seulement après réconciliation complète, exécuter `cohort_exclusion_gate` sur une nouvelle source score-blind ; enregistrer chronologie, provenance, dédoublonnage et SHA avant tout scoring.

**Échec/arrêt :** une source inaccessible, un écart inexpliqué de dénominateur, une partie réservée sans identifiant ou un chevauchement non résolu maintient le gel interdit. Les 61 paires LCB/Q et les 3 paires LCB seules restent des observations historiques, sans implication sur le top-1, le top-3 ou le minimax.
