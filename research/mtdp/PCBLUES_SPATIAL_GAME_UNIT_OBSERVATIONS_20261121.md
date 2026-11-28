# MTDP — Audit descriptif réel par partie (PC Blues)

Date de contrôle : 2026-11-21 UTC. Ce document rapporte une **exécution locale sur un artefact GitHub Actions réellement téléchargé**, et non une simple extrapolation des logs.

## Provenance et intégrité

- Workflow `downstream-compat`, run [44910597603](https://github.com/jfrancoiscollin/dilf/actions/runs/44910597603), état `completed/success`, source `cd3447c18c724ff2d99c860bce57685b2e03d92d`.
- Archive GitHub Actions `mtdp-pcblues-spatial-dynamics`, artifact ID `14709956363`, taille ZIP 81981 octets, SHA-256 **`1a5896e9bd3d75e019f683f9158168bfb624bf42f8b8460042c6aaf6cf083ff0`** ; archive téléchargée et inspectée localement.
- Les **10 fichiers référencés** dans `mtdp-artifact-manifest.json` ont chacun une longueur et une empreinte SHA-256 correspondant exactement au manifeste (10/10, zéro anomalie). Ce contrôle vérifie l'intégrité de l'archive par rapport à son manifeste, pas l'indépendance scientifique de la cohorte.
- `mtdp-fmjd-provenance.json` identifie `draught-master@0e5189fbb251bf5eaf2e613d0f878bb17c740311` et `dilf_source_sha=cd3447c18c724ff2d99c860bce57685b2e03d92d`.

## Calcul indépendant à partir de `mtdp-spatial-dynamics.json`

Le tableau `per_game` a été parcouru localement, en utilisant chaque partie comme unité descriptive. Les taux sont des fractions de transitions dont **tous les descripteurs spatiaux suivis** restent inchangés :

| Mesure | Valeur |
|---|---:|
| Parties | 26 |
| Positions | 1864 |
| Transitions | 1838 |
| Transitions sans changement des descripteurs | 245 |
| Moyenne non pondérée des taux par partie | 0.13096247459658092 (13.0962 %) |
| Médiane des taux par partie | 0.13452432199741715 (13.4524 %) |
| Minimum / maximum par partie | 0.038461538461538464 / 0.2 |
| Taux global pondéré par transition (diagnostic uniquement) | 0.13329706202393907 (13.3297 %) |
| Parties avec répétition exacte de position | 0 |
| Positions revisitées au sein des parties | 0 |

Les deux taux (13.10 % macro contre 13.33 % micro) ne sont pas identiques, mais **leur écart ne constitue pas une preuve d'effet statistique**. Les positions successives sont corrélées ; les 26 parties ne sont pas certifiées échantillonnées indépendamment. Les descripteurs inchangés n'impliquent pas une équivalence stratégique ou minimax. Le nombre de positions revisitées est celui du rapport, pas une preuve universelle d'absence de cycles dans les dames.

## Reproduction

1. Télécharger l'artefact GitHub Actions ID `14709956363` (expiration annoncée 2026-12-21).
2. Vérifier le SHA-256 du ZIP, puis les dix couples `bytes`/`sha256` dans `mtdp-artifact-manifest.json`.
3. Exécuter `python -m research.mtdp.spatial_game_units mtdp-spatial-dynamics.json` depuis la racine du dépôt après extraction du fichier. Comparer les taux aux valeurs ci-dessus.

Aucune relance FMJD ni expérience D1 ; aucune fusion ni ressource payante. Prochaine étape : tester la robustesse des résultats aux longueurs des parties, aux phases de jeu et à la sélection des descripteurs, sans inférence IID.
