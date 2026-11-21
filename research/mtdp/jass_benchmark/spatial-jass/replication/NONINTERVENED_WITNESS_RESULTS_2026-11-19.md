# Coût de vérification : témoin sans intervention

**Contrôle séparé terminé**, une position déjà connue, D9PF2OSW:59, aux trois budgets prévus. Le plan a été publié avant l'adaptateur, puis l'adaptateur0241a50ce06982704fa0b1d7dea7e842d773d49b a été vérifié à distance avant moteur. Aucun élargissement du masque des neuf interventions, aucune nouvelle cohorte et aucune référence Scan cible ouverte.

Deux processus7/61 ont reproduit exactement les9résumés originaux chacun (trois bras × trois budgets), le sélecteur et les charges. Le meilleur coup à profondeur1 est unique, sans forçage, aux trois budgets. Le contrôle et LCB au même budget résiduel ont des **traces normalisées entières identiques**, pas seulement le même résultat final.

## La perte de profondeur vient ici de la réduction du budget principal

Chaque vérification consomme293nœuds. À10k, le contrôle dispose donc de9707nœuds principaux ; les comparateurs non forcés donnent :

| Ordre initial | Nœuds principaux | Coup final | Profondeur complétée | Score Jass |
|---|---:|---|---:|---:|
| Natif | 10 000 | 20-24 | 9 | 3 |
| Natif | 9 707 | 20-24 | 8 | 11 |
| LCB | 10 000 | 20-24 | 9 | 3 |
| LCB | 9 707 | 20-24 | 8 | 11 |
| Contrôle, sans intervention | 9 707 | 20-24 | 8 | 11 |

Les traces du budget plein situent l'achèvement de profondeur9 à**9932nœuds pour natif** et**9980pour LCB**. Ces deux seuils dépassent9707 et restent sous10000 : le retrait des293nœuds suffit donc à empêcher cette profondeur, **pour chacun des deux ordres sur ce témoin déterministe**. Le changement d'ordre ne crée ici aucun écart de profondeur au même budget ; l'interaction discrète ordre×budget sur la profondeur vaut0.

Ce contrôle explique l'écart original profondeur8/9 sans lui attribuer un effet d'intervention inexistant. Le score11 à profondeur8 contre3 à profondeur9 ne mesure pas une amélioration : ce sont des scores Jass à horizons différents, pas des regrets Scan.

## Les deux autres budgets restent dans l'analyse

| Budget total | Résiduel après293nœuds de vérification | Coup de tous les bras | Profondeur de tous les bras | Score Jass de tous les bras |
|---:|---:|---|---:|---:|
| 50 000 | 49 707 | 20-24 | 11 | 0 |
| 200 000 | 199 707 | 18-22 | 14 | 0 |

Aux50k/200k, retirer293nœuds ne change ni coup, ni profondeur finale, ni score. Les tentatives complétées du budget plein se terminent, respectivement, à29621/29669nœuds (natif/LCB, profondeur11) et170872/170920 (profondeur14), sous les limites résiduelles correspondantes. Tous les cas nuls sont conservés ; trois budgets ne représentent pas trois positions indépendantes. Cette position a été choisie après constat d'un écart connu : aucune fréquence d'erreur ou généralisation au corpus n'en est déduite.

## Reproduction et archives

Chaque exécution consomme**1 298 242nœuds**, sous le plafond1,3M ; ensemble**2 596 484**, sous2,6M. Les84reçus bruts (42par exécution) et les6fichiers de publication/statut/normalisation sont conservés. Les normalisés sont identiques SHA `8f8035cc275465693a4017107cc761e45141f5a64caaa0b267265c3535dfb90b`. Le vérificateur indépendant reconstruit sondes exactes, absence d'intervention, charges et trois résumés originaux, puis contrôle les traces et comparateurs ; seules les durées principales diffèrent entre les enveloppes brutes des deux exécutions.

- Archive7 :11628octets, SHA `b328151ae36fd6df12a15787519ed1747c42ee8e3440d552cd0a1a7cf57d6b9f`.
- Archive61 :11631octets, SHA `d1ee813f09aa40846d2c172c372f05c0e990d1cacdfc629a809e7e9b60150ba3`.
- Résultats SHA `0c5555d5f30d7b278b173fb41b71b18244250f7c8d4690cf5a80ae02d5c69a0f` ; preuves et empreintes de tous les90fichiers dans `nonintervened-budget-independent-verification.json`.
- **284tests ciblés locaux passent**, dont10nouveaux ;8/8Actions du collecteur0241a50 réussies. Les8/8Actions du snapshot résultats/correctif `2126486930d3b8f4c14f992e46d262c962aed334` réussissent. [Rejeu horsligne44498180402](https://github.com/jfrancoiscollin/dilf/actions/runs/44498180402) :33tests,84raws du témoin revalidés sans moteur ; artefact14515808075 téléchargé/vérifié,49542octets,ZIP SHA `355ade397be2387ef6a5bc320d12b81549e9349f8a26d5fd0a9f605bf7fd73a1`,ses7fichiers identiques au dépôt. Preuve complète `nonintervened-budget-ci-verification-2026-11-19.json`.

```bash
python -m research.mtdp.jass_benchmark.budget_witness_analysis --root . \
  --archive7 research/mtdp/jass_benchmark/spatial-jass/replication/nonintervened-budget-raw-seed7.tar.gz \
  --archive61 research/mtdp/jass_benchmark/spatial-jass/replication/nonintervened-budget-raw-seed61.tar.gz \
  --output /tmp/witness-results.json --proof /tmp/witness-proof.json
```

## Prochaine étape : dénominateur complet

Les neuf premiers contextes étaient sélectionnés pour une intervention ; ce témoin l'était pour un écart de profondeur. Pour mesurer les effets descriptifs sans ces filtres, `full-frozen-residual-control-plan.json` fixe maintenant **les114reçus originaux, toutes les38cibles/31parties propriétaires aux trois budgets**, y compris tous les cas nuls. Pas de nouvelle cohorte indépendante : les événements et résultats originaux sont déjà connus.

Prochaine action H13 : collecteur distinct publié/vérifié avant moteur, même binaire et méthodes, reproduction obligatoire de tous les trois bras/charges originaux puis ajout des deux bras résiduels ; tous les raw, cas et échecs conservés. Deux processus7/61 prévus, plafonds49,4Mde nœuds chacun/98,8Mensemble. Rapporter choix, profondeur, score et traces conditionnels au budget et à l'ordre ; aucun nouveau regret Scan ni test d'efficacité. Les bras supplémentaires restent des comparateurs au même budget principal, sans les rebaptiser bras primaires à même budget total. Aucun ajustement de signature, top-K ou dimension.

Les résultats primaires16/20,114décisions et anciens masques restent inchangés. Les quatre événements entiers fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW et leurs FEN restent réservés hors D1 fitting/validation indépendante/signature/top-K/refinement/seuils/dimension. Ressources distantes suffisantes pour le contrôle exécuté ; PC de Jeff non requis.


## Coordination et réparation de validation D1

Les commits concurrents47b491e/6076c2a/1c829fa ont été récupérés et préservés. La CI D1 du dernier commit a échoué sur une attente de test erronée : deux parties éligibles parmi dix donnent une probabilité exacte de couverture0,8926258176, inférieure au seuil0,95, alors que le test attendait `ok`. Le critère et le calcul de production sont conservés. Le test couvre désormais les deux cas : deux parties → couverture insuffisante ; trois parties →0,9717524751 et `ok`, avec statut identique aux deux seeds. **18tests agrégation/bootstrap passent localement**, inclus dans les284tests ciblés ; le [run D1 corrigé44498180309](https://github.com/jfrancoiscollin/dilf/actions/runs/44498180309) passe131tests (journal du job135470643711 confirmé), sans doublonner le job défaillant de l'ancien commit. Aucun corpus D1 ni nouveau résultat de qualité.
