# H13 — extension des exclusions historiques aux deux exports clos

Le producteur `closed_reserved_exclusions` ajoute uniquement les exports déjà archivés et réservés s7ahYqL4 (147 parties) et D9PF2OSW (61). Les trois membres du cache de départ sont vérifiés contre leurs empreintes antérieures, notamment `two-arena-exclusions.json` SHA-256 `8dac5c60e1eaa10ff8e3e27f5c1fb0d0307edaeaec438e7c9bdc33b3e666dc32`. Ils ne sont pas modifiés.

Le vrai moteur FMJD est contrôlé à la révision `0e5189fbb251bf5eaf2e613d0f878bb17c740311`, avec contrôle du chemin du module réellement importé. Le producteur réutilise `named_arena_replay.index_games`, sans modifier sa méthode figée. Les deux fichiers originaux s'appellent `first.pdn` : des copies temporaires octet pour octet identiques reçoivent des noms canoniques distincts pour conserver les identités fichier:index.

Toutes les parties sont rejouées. Une ambiguïté ou illégalité est conservée en quarantaine avec ses seuls préfixes confirmés ; aucune continuation n'est choisie arbitrairement. L'union conserve les FEN, empreintes complètes, identifiants publics et empreintes de notation antérieurs. Les doublons intersources sont comptés séparément des trajectoires distinctes, jamais comme observations indépendantes.

## Exécution reproductible

Le workflow existant `mtdp-preregistered-candidate-replay` dispose déjà des trois membres de départ et du FMJD épinglé. Sa nouvelle étape historique exécute :

```bash
python -m research.mtdp.closed_reserved_exclusions --root . --base-dir /tmp/mtdp-independent --adapter ../draught-master --output /tmp/four-events.json --summary /tmp/four-events-summary.json
```

Deux processus aux graines de hachage 7 et 61 doivent produire des caches et résumés identiques octet pour octet. Le nouveau cache et le résumé sont archivés par l'étape existante ; aucun nouveau runner ni moteur de recherche n'est créé. La validation réelle et les comptes observés doivent être lus dans la CI et son artefact, pas déduits des tests synthétiques.

Validation locale préalable : 7 nouveaux tests d'union/quarantaines/doublons et 7 tests de réconciliation antérieure réussis. Aucun moteur FMJD n'est disponible localement ; le calcul légal des 208 parties est confié à la CI existante. Aucun besoin d'allumer le PC de Jeff.

## Limites et relais

Le total source attendu est 4 824 parties sur 25 sources ; les comptes de trajectoires, doublons, quarantaines et FEN supplémentaires restent à mesurer. La couverture des **quatre sources réservées connues** sera vérifiée explicitement, mais `complete_historical_exclusion_registry=false`, `independent_cohort_qualified=false` et `scientific_freeze=false` restent imposés. Les autres manifestes/alias et la qualification indépendante restent nécessaires avant tout nouveau gel H13.

Ce travail traite des données historiques déjà exclues, sans acquisition de nouveau corpus, scores Scan/Jass, évaluation de signature ou campagne D1. Les quatre événements entiers et leurs parties/FEN demeurent exclus de fitting, validation indépendante, signatures, top-K, refinement, seuils et dimension.
