# D1 — Audit des paires LCB/Q, PC Blues historique (17 novembre 2026)

## Provenance et exécution

- Source : [GitHub Actions D1 #44024558704](https://github.com/jfrancoiscollin/dilf/actions/runs/44024558704), commit DILF `6cfe921f5a5aa0a6452a7e351cb6522e3be1744e`, conclusion **success**.
- Job `score-blind-engineering` : **20 tests réussis**, rejeu FMJD des 26 parties PC Blues, 1 864 observations, 1 750 FEN distinctes.
- [Artefact #14302322531](https://github.com/jfrancoiscollin/dilf/actions/runs/44024558704/artifacts/14302322531), digest ZIP `sha256:d9254253e43367832a0daf83406787858b899aa1999488a46a0b4cb2ce355a7f` (rétention 30 jours). Les nombres ci-dessous proviennent de la ligne JSON imprimée dans les logs du job, et non d'une analyse indépendante du ZIP.

## Résultats observés (paires de FEN distinctes, sans scores)

| Partition | Paires | Mêmes coups légaux | Parties propriétaires disjointes | Coups légaux différents |
| --- | ---: | ---: | ---: | ---: |
| LCB ∩ Q | 61 | 61 | 61 | 0 |
| LCB uniquement | 3 | 3 | 3 | 0 |
| Q uniquement | 0 | 0 | 0 | 0 |
| Union | 64 | 64 | 64 | 0 |

Signatures distinctes : E=1 750, L=1 464, LCB=1 709, Q=1 712. Compression de cardinalité LCB=41/1750 (2,34 %) ; Q=38/1750 (2,17 %). Sur **ce seul corpus**, les 61 paires Q forment un sous-ensemble des 64 paires LCB. Les trois paires supplémentaires LCB sont des candidats de transfert, pas des équivalences décisionnelles. Le compte de paires ne constitue pas une mesure d'indépendance statistique, même lorsque les identifiants de parties sont disjoints.

## Limites et décision

Corpus historique déjà exploité : **aucune nouvelle cohorte indépendante**. Le partage d'une signature, de coups légaux, ou de provenance entre parties ne démontre ni égalité des successeurs, ni stabilité top-1/top-3, ni égalité minimax, ni gain alpha-bêta, ni élagage sûr. Les résultats ne contiennent aucun score Scan ni comparaison Jass. Ne pas réutiliser les 78 cibles réservées de fFgE7oED.

**Décision D1 :** conserver LCB et Q comme témoins complémentaires ; préenregistrer séparément un corpus indépendant, avec partition par partie et exclusion des cohortes déjà utilisées, avant tout classement Scan. Ne pas déclencher de sélectivité Jass sur ces seules mesures.
