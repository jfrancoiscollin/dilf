# Intervention de départage : traces et comparateurs au budget résiduel

**Rejeu diagnostic terminé**, sur les neuf reçus fixés par le plan publié à6313090 : **trois positions × trois budgets**, déjà connues, sans nouvelle cohorte ni référence Scan cible. Le collecteur `3b89ca824c173530e3b475ece9d3dbb3f1500dd6` a été publié et vérifié à distance avant les appels ; les binaires, limites, préfixes source12 et méthodes primaires sont inchangés.

Les deux exécutions7/61 ont chacune reproduit exactement les27résumés originaux (trois bras × neuf contextes), le sélecteur et les charges de vérification, avant toute interprétation des bras supplémentaires. **3 898 062nœuds par exécution**, soit7 796 124sur les deux, sous les plafonds explicites3,9M/7,8M. Chaque exécution conserve132reçus bruts, soit264 au total : préliminaires, toutes les sondes et les45recherches principales. Les archives incluent aussi preuve de publication, statut et sortie normalisée.

## L'intervention est appliquée et se propage

Dans les9/9contextes, les nouvelles sondes exactes conduisent au même départage attendu ; la trace principale confirme le coup imposé à profondeur1 et sa propagation en première position de l'ordre à profondeur2. Le premier meilleur coup natif est le même que celui sélectionné par le contrôle,9/9.

| Position propriétaire | Premier meilleur coup LCB non forcé | Coup sélectionné natif/contrôle à profondeur1 |
|---|---|---|
| s7ahYqL4:132 | 18-22 | 8-12 |
| s7ahYqL4:58 | 28-23 | 47-41 |
| D9PF2OSW:53 | 17-22 | 17-21 |

Chaque ligne représente une position répétée aux trois budgets ; ne pas compter neuf positions indépendantes. Les différences de trajectoire ne sont pas synonymes de différences de qualité.

## Comparaison au même budget principal

Les deux bras supplémentaires utilisent exactement `budget total − vérification`, avec tables fraîches, mêmes binaires et paramètres. Ils n'incluent pas une nouvelle dépense de vérification : ce sont des comparateurs mécaniques, pas une nouvelle campagne primaire à budget total égal.

| Comparaison sur les9contextes | Même coup final | Profondeur différente | Score Jass différent |
|---|---:|---:|---:|
| Contrôle forcé / LCB non forcé, même budget résiduel | 8/9 | 3/9 | 2/9 |
| LCB résiduel / LCB plein | 9/9 | 0/9 | 0/9 |
| Natif résiduel / natif plein | 9/9 | 0/9 | 0/9 |
| Contrôle / natif résiduel | 9/9 | 0/9 | 0/9 |

Le cas qui change de coup est **D9PF2OSW:53 au budget total50k** :

| Bras | Nœuds principaux | Coup final | Profondeur complétée | Score Jass |
|---|---:|---|---:|---:|
| Contrôle | 49 916 | 17-21 | 10 | 38 |
| LCB non forcé résiduel | 49 916 | 20-24 | 11 | 21 |
| LCB non forcé plein | 50 000 | 20-24 | 11 | 21 |
| Natif résiduel | 49 916 | 17-21 | 10 | 38 |
| Natif plein | 50 000 | 17-21 | 10 | 38 |

Préfixe LCB, nœuds principaux, binaire et paramètres sont identiques entre les deux premières lignes ; seule l'intervention de départage est activée dans le contrôle. Le résultat réfute donc l'hypothèse d'un forçage inopérant **dans ce rejeu déterministe**. L'accord contrôle/natif observé auparavant ne prouvait pas l'inertie du traitement. Les scores Jass à des profondeurs différentes ne sont pas des regrets Scan ; aucune amélioration de qualité, de force ou de population n'est établie ici.

Sur8/9contextes, les meilleurs coups des profondeurs complétées finissent par coïncider jusqu'à leur horizon commun ; le neuvième cas ci-dessus ne converge pas dans cet horizon. Pour D9PF2OSW:53, l'accord final existe à10k, disparaît à50k puis réapparaît à200k. Un accord à faible horizon ne garantit pas l'accord plus profond. Les trajectoires et les horizons communs exacts restent dans le JSON, sans extrapolation.

## Reproduction et vérification indépendante

Les sorties normalisées7/61 sont identiques, SHA-256 `30f6bdb8d18111536af118c9a6706b041ac01125a8cec6cd786e96b3827970eb`. Le vérificateur indépendant stdlib relit les264reçus, recalcule le départage depuis les scores/bornes/complétions, vérifie les27résumés originaux par exécution, les limites et les sommes. Il compare aussi les enveloppes brutes complètes entre les exécutions : **seule la durée du stdout principal diffère**. Les preuves opérationnelles horodatées restent séparées de cette comparaison.

- `mechanistic-residual-raw-seed7.tar.gz` :36599octets, SHA `8d8d278a9567ae7328be504c9ff25dc1175e0c36b02bf668aa22fc78eefd2b69`.
- `mechanistic-residual-raw-seed61.tar.gz` :36629octets, SHA `9568b24bf6776e75b1048c509f8863fdafe645d4dfcf8814223231a371c09a97`.
- `mechanistic-residual-results.json` et `mechanistic-residual-independent-verification.json` contiennent tous les résultats, paramètres et empreintes des270fichiers archivés.
- **256tests H13 locaux passent**,15nouveaux (collecteur10, vérificateur5). Les8/8Actions du collecteur3b89ca8 réussissent ; les8/8Actions du snapshot résultats/correctif `c71c2dd5961de9d29e286abc416ac8c0e4c0b47f` réussissent aussi. [Job horsligne44488857824](https://github.com/jfrancoiscollin/dilf/actions/runs/44488857824),23tests,264raws revalidés sans moteur ; artefact14511966794 téléchargé et vérifié,45364octets,ZIP SHA `12dcbca6137ea817031013dbcf171eaf95e92fa866827535ae554757f5181f5f`,ses cinq fichiers sont identiques au dépôt. Preuve complète `mechanistic-residual-ci-verification-2026-11-19.json`. Aucun moteur de cohorte ne sera relancé par ce contrôle CI.

```bash
python -m research.mtdp.jass_benchmark.mechanistic_trace_analysis --root . \
  --archive7 research/mtdp/jass_benchmark/spatial-jass/replication/mechanistic-residual-raw-seed7.tar.gz \
  --archive61 research/mtdp/jass_benchmark/spatial-jass/replication/mechanistic-residual-raw-seed61.tar.gz \
  --output /tmp/mechanistic-results.json --proof /tmp/mechanistic-proof.json
```

## Correction technique D1 préservant les travaux concurrents

Les commits concurrents7c93005/fccf367/c592f46 ont été récupérés et conservés avant écriture. Les15tests réels agrégation/bootstrap ont détecté une `SyntaxError` dans le nouveau retour de `cluster_bootstrap.py` : deux caractères littéraux `\n` remplaçaient des retours à la ligne. Correction limitée à ces deux retours à la ligne ; diagnostics de concentration, dénominateurs et portes d'IC inchangés. **Les15tests passent après correction.**

Le workflow D1 était vert mais sa liste explicite ne collectait ni `test_aggregate.py` ni `test_cluster_bootstrap.py`. Les deux fichiers sont désormais inclus, afin que les prochaines validations couvrent réellement ces modules. Le [run D1 corrigé44488857953](https://github.com/jfrancoiscollin/dilf/actions/runs/44488857953) passe128tests, avec les deux chemins de tests confirmés dans le journal exécuté. Aucune campagne D1 dupliquée ni résultat de concentration interprété sur nos cohortes réservées.

## Prochain contrôle H13

Le témoin de perte de profondeur **D9PF2OSW:59** n'appartient pas au masque des neuf interventions. Il n'est donc pas expliqué par ce rejeu. Un plan **distinct** `nonintervened-budget-witness-plan.json` fixe cette seule position aux **trois budgets originaux**, y compris les deux sans écart de profondeur, sans modifier le plan des neuf cas. Prochaine action : publier un adaptateur distinct réutilisant les collecteurs purs, vérifier le plan à distance, reproduire les trois résumés et sondes originaux puis les deux bras résiduels ; comparer budget et ordre sur ce témoin. Plafond1,3Mde nœuds par exécution, avec toute répétition explicitement conservée. Diagnostic post-hoc, pas un nouveau test d'efficacité indépendant.

Toutes les données primaires, décisions114 et références16/20 restent immuables. Les quatre événements entiers fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW restent exclus de D1 fitting/validation indépendante/signatures/top-K/refinement/seuils/dimension. Aucune nouvelle cohorte. Ressources distantes suffisantes, PC de Jeff non requis.
