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

Le plan initial prévoyait 4 824 parties sur 25 sources ; les comptes effectivement observés sont présentés ci-dessous. La couverture des **quatre sources réservées connues** sera vérifiée explicitement, mais `complete_historical_exclusion_registry=false`, `independent_cohort_qualified=false` et `scientific_freeze=false` restent imposés. Les autres manifestes/alias et la qualification indépendante restent nécessaires avant tout nouveau gel H13.

Ce travail traite des données historiques déjà exclues, sans acquisition de nouveau corpus, scores Scan/Jass, évaluation de signature ou campagne D1. Les quatre événements entiers et leurs parties/FEN demeurent exclus de fitting, validation indépendante, signatures, top-K, refinement, seuils et dimension.


## Résultats observés et vérifiés

Code `6d137756f1f5be5af1de2fbde0b303300211357e`, run [44743125397](https://github.com/jfrancoiscollin/dilf/actions/runs/44743125397), job 136311527395/étape 12 : succès ; les processus 7/61 et leurs comparaisons de cache/résumé réussissent. Les huit workflows sont réussis ; CI générale : **747 tests MTDP réussis**, 14 sauts optionnels.

| Compte | Base conservée | Après extension |
|---|---:|---:|
| Sources | 23 | 25 |
| Parties enregistrées | 4 616 | 4 824 |
| Rejeux complets | 4 434 | 4 634 |
| Trajectoires complètes distinctes | 4 276 | 4 468 |
| Doublons de trajectoire complète | 158 | 166 |
| Parties en quarantaine | 182 | 190 |
| FEN de préfixes confirmés distinctes | 433 363 | 452 526 |

Les 208 parties donnent **200 rejeux complets et8 quarantaines** : s7ahYqL4 a142 rejeux complets/5 quarantaines ; D9PF2OSW a58/3. Les huit erreurs sont des prises dont les seuls points de départ/arrivée correspondent à deux coups légaux : aucune branche n'a été choisie. L'extension contient193 trajectoires distinctes, dont une déjà dans la base ; elle ajoute donc192 trajectoires et19 163 FEN distinctes. Les 7 doublons internes à l'extension et le chevauchement avec la base expliquent les8 doublons complets supplémentaires.

Artefact14631697430 téléchargé et vérifié : 14 754 558 octets, ZIP SHA-256 `fbdec268941ca5b6d99c5644a94679c7fa864dc20f5b6be8e8c069d2423ab120`. Le cache complet de 34 698 610 octets a pour SHA-256 **`5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7`**. Les trois membres historiques sont inchangés et les ensembles FEN/empreintes/IDs/notations de la base sont tous inclus.

Le résumé extrait sans modification est `four-reserved-events-exclusions-summary-2026-11-20.json` ; les 208 audits de parties sont conservés dans `closed-reserved-events-game-audit-2026-11-20.json`. La preuve technique et les empreintes sont dans `closed-reserved-exclusions-ci-2026-11-20.json`. Le cache complet reste archivé par le workflow et reproductible à partir des entrées épinglées ; ce n'est ni un nouveau corpus ni une preuve d'indépendance.

La lacune de couverture **des deux sources réservées** est fermée à ce niveau d'indexation (quarantaines comprises). La qualification historique globale reste refusée : D1/H43 doivent exploiter ce cache vérifié et réconcilier les autres alias/manifestes/FEN/trajectoires avant toute admission indépendante. Ne pas répéter ces208 parties comme un nouveau holdout.
