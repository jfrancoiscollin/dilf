# D1-C — Préflight Cloudflare R2 (sans extraction ni score)

État : **inventaire documentaire seulement**, 2026-11-21. Aucune lecture authentifiée du bucket ni campagne sur positions réelles n'est revendiquée.

## Sources vérifiables

- `jfrancoiscollin/jass-control`, `README.md` (branche main) : runner GitOps, sorties `runs/<job-id>/<attempt-id>/`, marqueur final `_SUCCESS` ou `_FAILED` ; credentials hors Git.
- `jfrancoiscollin/jass-control`, `status/cpx62-0765-diag.txt` : journal historique indiquant 864 blobs uniques, 9 349 788 817 octets et le préfixe `r2:jass-data/historical/jass-snapshots/main-3b0ebd8de052__develop-9ff75ca633d8`. Le même journal se termine par une erreur de réécriture Git ; ce n'est **pas** une validation de corpus FMJD.
- Le contrôle D1 du commit `32fef28d08b0728e061960c31e672159f4b9b4c1` : workflow `mtdp-d1-score-blind-pcblues` run 44899281254, success, artefact `mtdp-d1-pcblues-score-blind-engineering` (ID 14705077699). **Cet artefact n'est pas une cohorte R2 indépendante.**

## Protocole de découverte score-blind à exécuter sur un runner autorisé

1. **Lecture seule** : lister les préfixes et métadonnées des objets R2, en consignant chemin, taille, ETag, date et éventuel SHA-256 manifeste. Ne pas copier de secrets ni de fichiers massifs dans Git.
2. Repérer les formats contenant positions FMJD 10×10, FEN, identifiant de partie/tournoi, index de demi-coup, horodatage, provenance et, séparément, évaluations. Les snapshots historiques ne sont pas présumés utilisables.
3. Produire un manifeste **avant consultation des scores** : version du parseur, SHA du manifeste, règles d'éligibilité, exclusions de tous les corpus prospectifs réservés (notamment 78 cibles fFgE7oED), tri chronologique et clé canonique de position.
4. Geler les partitions par partie/tournoi, vérifier absence de partie commune entre train/test, FEN dupliquées intra/inter-partition et dépendance des positions successives. Aucun comptage par position ne remplace l'incertitude par partie.
5. Tester les signatures L, LCB et enrichies **sans labels cibles** ; ne lancer les analyses top-K/centimen/WDL que sur cohortes indépendantes effectivement scorées avec protocole préenregistré.

## Garde-fous / arrêt

- Pas d'accès R2 confirmé : arrêt après inventaire documentaire ; **zéro position évaluée**.
- Absence d'identifiant fiable de partie ou impossibilité d'exclure les cohortes réservées : ne pas annoncer de test hors échantillon.
- FEN non rejouable ou actions légales non validées : pas de transfert décisionnel.
- Aucun changement à Jass production, aucun job payant, aucune écriture R2 dans ce préflight.

**Prochaine action unique :** obtenir un inventaire R2 *lecture seule* des préfixes de données d'apprentissage et identifier le schéma d'un échantillon sans scores.

## Exécution opérationnelle sans accès aux secrets dans Git

Sur un hôte **déjà autorisé** disposant du remote `r2:` en lecture, et uniquement après validation du coût éventuel de l'inventaire :

```bash
set -euo pipefail
umask 077
rclone lsjson 'r2:jass-data' --recursive --files-only > r2-object-inventory.json
python -m research.mtdp.decision_equivalence.r2_inventory \\
  r2-object-inventory.json --output r2-object-summary.json
sha256sum r2-object-inventory.json r2-object-summary.json
```

Conserver le listing brut et les credentials **hors Git** ; partager seulement le résumé et ses empreintes après contrôle des noms d'objets (qui peuvent contenir des données sensibles). La commande n'a pas été exécutée lors de cette rédaction. Un listing exhaustif peut générer des requêtes R2 facturables : **ne pas déclencher automatiquement** sans autorisation de coût. En cas de liste volumineuse, la version actuelle de l'analyseur charge le JSON entier en mémoire ; segmenter le listing ou améliorer l'analyseur avant une campagne à très grande échelle.
