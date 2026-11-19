# Contrôle exhaustif du budget résiduel : toutes les cibles gelées

**Contrôle complet terminé et reproduit**,114contextes,38positions et31parties propriétaires, aux trois budgets10k/50k/200k. Aucun filtre sur intervention, profondeur, score ou résultat. Ce sont les deux arènes déjà connues et gelées ; pas une nouvelle validation indépendante.

Le collecteur distinct `e30b0273e206436607f0c342cdda772710f342f9` et le plan publié àaba44ed ont été vérifiés vivants avant moteur. Méthodes, binaires, source12, préfixes et limites inchangés. Chaque exécution a reproduit exactement les**342résumés originaux** des trois bras, ainsi que toutes les charges et décisions du sélecteur, avant interprétation des deux bras résiduels.

## Le retrait du coût de vérification ne change aucun choix dans ce cadre

| Comparaison | Même coup final /114 | Profondeur différente | Score Jass différent |
|---|---:|---:|---:|
| LCB résiduel / LCB plein | 114/114 | 1 | 1 |
| Natif résiduel / natif plein | 114/114 | 1 | 1 |
| Contrôle / natif plein | 114/114 | 1 | 1 |
| Contrôle / LCB résiduel, mêmes nœuds principaux | 113/114 | 3 | 2 |
| LCB / natif, même budget résiduel | 113/114 | 3 | 2 |
| LCB / natif, même budget plein | 113/114 | 3 | 2 |

Le budget de vérification reste celui effectivement mesuré,60–346nœuds par position, somme20259sur114contextes. Les comparateurs supplémentaires utilisent seulement le budget principal `N−v` : ils ne deviennent pas des bras primaires à même budget total.

### Effet du budget, conditionnel à l'ordre

Àchaque budget, les deux ordres gardent le même choix final38/38 après retrait de la vérification. La seule différence de profondeur est le témoin déjà étudié, **D9PF2OSW:59 à10k**, pour chacun des deux ordres :293nœuds de vérification,9707principaux, profondeur8 au lieu de9, scoreJass11 au lieu de3, même coup20-24. Aux deux autres budgets, aucun écart de profondeur ou de score sur les38positions. Aucun autre cas n'a été masqué par les diagnostics sélectionnés précédents.

L'identité de choix implique qu'une évaluation fixe du coup aurait la même valeur pour les deux limites de chaque ordre dans ces observations ; **cela ne prouve pas l'équivalence en population**, ni l'absence de coût CPU. Les scores Jass d'horizons différents ne sont pas des regrets Scan. Aucun paquet de scores cibles n'a été chargé par ce calcul.

### Effet du départage, à même budget principal

Les neuf interventions sont bien retrouvées et appliquées à profondeur1, puis propagées à profondeur2. Les105contextes sans forçage ont des traces entières identiques entre contrôle et LCB résiduel. Sur l'ensemble114, un seul coup final change à même préfixe et même limite : **D9PF2OSW:53 à50k**, contrôle17-21/profondeur10/score38 contreLCB non forcé20-24/profondeur11/score21, tous deux49916nœuds. Les deux autres écarts de profondeur sont à200k : s7ahYqL4:58 etD9PF2OSW:53, contrôle une profondeur plus loin queLCB, même coup final.

Ces effets sont donc réels sur les trajectoires, sans établir un gain de qualité. Le contrôle reste aligné sur les choix natifs114/114. Les38positions, les cas nuls, les propriétaires et les trois budgets restent tous dans les résultats.

## Reproduction, coût et vérification indépendante

Chaque processus7/61 a consommé**49 359 482nœuds**, sous49,4M ; ensemble**98 718 964**, sous98,8M. Chacun conserve1806reçus bruts :114préliminaires,1122sondes et570recherches principales. Total3612reçus, plus6fichiers de publication/statut/normalisation, soit3618fichiers dont les empreintes sont archivées.

Les sorties normalisées sont identiques SHA `76b2990a2f6e38dd9ef453f0ef3694c55394d723b618f2f54e419ce19edf4be3`. Le vérificateur indépendant stdlib relit toutes les entrées/sorties, reconstitue scores exacts/bornes, sélecteur, limites, sommes et342résumés originaux par exécution. Il confirme que seules les durées principales diffèrent entre enveloppes brutes. Aucun échec/plafond ou cas manquant.

- Archive7 :440748octets, SHA `0fd08ea0b53ddb15c5a11ad529672423a6e00497dae9996b875be27d4585dec8`.
- Archive61 :440791octets, SHA `7b40a85914742132046086128edaafed999b4135e2b319bf31da6fdfd31d6269`.
- Résultats SHA `58205e783e2caa712256c1275a5e1c6cfc5ca6b48365dd5205f45dbcd919f2ee` ; inventaires et preuves dans `full-frozen-residual-independent-verification.json`.
- **302tests ciblés locaux passent**, dont12nouveaux H13 et24tests D1 réels. Les8/8Actions du collecteur e30b027 réussissent ; les8/8Actions du snapshot résultats `176340e4971b1dba6de626447f9e8e00fb27b023` réussissent aussi. [Rejeu horsligne44507285686](https://github.com/jfrancoiscollin/dilf/actions/runs/44507285686) :45tests,3612raws revalidés sans moteur ; artefact14520780188 téléchargé/vérifié,207994octets,ZIP SHA `2aaa77f50f702f1d8fbe2a7250521c13b4517426a3a566bc552ad5ebb921569f`,ses9fichiers sont identiques au dépôt. Preuve complète `full-frozen-residual-ci-verification-2026-11-19.json`.

```bash
python -m research.mtdp.jass_benchmark.full_frozen_residual_analysis --root . \
  --archive7 research/mtdp/jass_benchmark/spatial-jass/replication/full-frozen-residual-raw-seed7.tar.gz \
  --archive61 research/mtdp/jass_benchmark/spatial-jass/replication/full-frozen-residual-raw-seed61.tar.gz \
  --output /tmp/full-results.json --proof /tmp/full-proof.json
```

## Coordination D1 et prochaine action

Les commits concurrents6a8471d/7d8ba5b/8112146 sont récupérés et préservés. Les six tests de leur garde d'admission sont passés avec les vrais imports et ajoutés à la liste CI D1, sans modifier leur méthode ni admettre un corpus réel. Le [run D1 actuel44507285734](https://github.com/jfrancoiscollin/dilf/actions/runs/44507285734) passe137tests ; la collecte effective de `test_corpus_guard.py` est confirmée dans les logs du job135502076778. Aucune campagne D1 dupliquée.

La prochaine étape, `full-frozen-residual-quality-plan.json`, est **distincte de cette analyse de traces** : après publication/vérification des114décisions nouvelles et du code d'analyse, relire uniquement la référence Scan16 déjà figée pour réconcilier les coûts de choix, reproduire exactement tous les résultats/IC originaux des trois bras puis chiffrer les contrastes résiduels sur les mêmes38cibles/31propriétaires. Aucun nouveau calcul moteur, filtre ou masque ; budget primaire50k et sensibilités10k/200k inchangés. Bootstrap H13 figé, parties entières et deux arènes,10000tirages/seed20261113/rangs249–9749, mêmes tirages entre contrastes, cas catégoriels conservés et ICnull si tirages indéfinis. Analyse post-hoc, aucun nouveau test d'efficacité indépendant ni promotion Jass.

Les références primaires16/20 et114décisions restent immuables. Les quatre événements entiers/FEN fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW restent réservés hors fitting/validation indépendante/signature/top-K/refinement/seuils/dimension D1. Aucune nouvelle cohorte. Les ressources distantes ont exécuté le contrôle complet ; PC de Jeff non requis.
