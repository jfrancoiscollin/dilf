# Coût de transfert : décomposition croisée Scan16/20

**Analyse exploratoire terminée, sans nouveau calcul moteur.** Les 26 paires du masque LCB complet égal restent les mêmes, avec leurs 22 propriétaires parmi le cadre gelé complet de 31 parties. Les deux arènes ont 17 et 9 paires ; les quatre cellules sont ordinaires dans les 26 cas. Aucun filtrage sur coût, nouveau choix de source ou nouvelle cohorte indépendante.

Le plan et les formules ont été écrits et commis localement avant les premiers tableaux croisés (`TWO_ARENA_CROSSED_DEPTH_PLAN_2026-11-19.md`). Les résultats appariés 16/16 et 20/20 étaient déjà connus : il ne s'agit pas d'une analyse confirmatoire préenregistrée. Les dépendances de calcul et les octets des quatre paquets publiés sont vérifiés avant lecture des scores ; aucune récupération HTTP ni exécution Scan/Jass.

| Choix de coup source | Référence cible | Coût moyen brut | Maximum | Optima disjoints | Coup transféré optimal |
|---|---:|---:|---:|---:|---:|
| Scan16 | Scan16 | 28,576923 | 260 | 14/26 | 11/26 |
| Scan16 fixé | Scan20 | 27,961538 | 263 | 13/26 | 10/26 |
| Scan20 | Scan16 | 16,692308 | 170 | 13/26 | 11/26 |
| Scan20 | Scan20 | 15,576923 | 162 | 12/26 | 12/26 |

Le premier maximisateur source change dans **15/26 paires** (10/17 et 5/9). Les ensembles complets d'optima et le départage canonique sont conservés séparément. Les deux cellules déjà publiées, avec tous leurs résumés et IC, sont reproduites exactement.

| Décomposition descriptive appariée | Moyenne brute | IC percentile par parties à 95 % |
|---|---:|---:|
| Référence16→20, coup source16 fixé | −0,615385 | [−1,833333 ; 0,538462] |
| Coup source16→20, référence20 fixée | −12,384615 | [−29,321429 ; 1,538462] |
| Total apparié 20/20−16/16 | −13,000000 | [−30,320000 ; 1,080000] |
| Coup source16→20, référence16 fixée | −11,884615 | [−29,645161 ; 2,333333] |
| Référence16→20, coup source20 fixé | −1,115385 | [−2,000000 ; −0,190476] |
| Interaction des deux changements | −0,500000 | [−2,185185 ; 1,222222] |

Les deux chemins somment exactement au même delta, par paire et sur les sommes (−16−322 = −309−29 = **−338**, soit −13 par paire). Le changement de choix source explique descriptivement la plus grande partie de la variation observée sur le premier chemin. Ce sont des identités sur une cohorte déjà connue, dépendantes du chemin et de la référence : **aucune attribution causale, preuve d'amélioration générale, équivalence minimax ou gain Jass**. Les IC sont une variation interne aux deux arènes fixées, sans correction de multiplicité ; l'IC isolé du chemin réciproque n'est pas un nouveau test confirmatoire.

Le contre-exemple le plus coûteux à16, `mtdp-lidraughts-s7ahYqL4.pdn:145`, illustre la confusion évitée : le coup source16 `17-21` coûte **260 à16 et 263 à20** ; le nouveau coup source20 `5-10` coûte **170 à16 et 162 à20**. Le changement apparié −98 est donc +3 de référence puis −101 de choix, plutôt qu'une disparition du désaccord géométrique.

Tous les estimands, par arène et ensemble, sont dans `two-named-arenas-crossed-depth-results.json`. Bootstrap : mêmes 10 000 tirages stratifiés de parties entières, seed20261113 et rangs249/9749, cadre propriétaire complet, aucune suppression/répétition des tirages indéfinis. Les effets utilisent strictement le même masque « quatre cellules ordinaires » ; les catégories seraient retenues avec effets null si besoin.

## Reproduction vérifiée

- **233 tests ciblés locaux passent** (226 analyse/relais et sept restauration historique), dont cinq nouveaux tests de décomposition, ties, transitions catégorielles et intégrité de l'archive. Aucun substitut aux imports du dépôt.
- Deux processus PYTHONHASHSEED7/61 produisent les mêmes octets, SHA-256 `74a49c006161302384a062784bbebef0f7ebf9b2c7ce99557b39f09051110c9d` ; ajout du contrôle de dépendances sans changement des octets de résultats.
- Le vérificateur indépendant, uniquement bibliothèque standard, relit les vecteurs bruts et recalcule **104 cellules**, choix/ties/catégories, les six effets et **66 IC** (22 estimands × trois périmètres) sans importer les helpers d'analyse. Tout concorde.
- Les 13 tests D1 agrégation/bootstrap passent aussi avec les imports réels ; leurs nouveaux commits 3780c00/11e7f2e sont préservés.
- Workflow `mtdp-crossed-depth-replay` ajouté : tests, deux seeds, comparaison au résultat archivé, recalcul indépendant et artefact 30 jours. Validation distante réussie sur `3bdbe30853ce74938d2788fa9eb42cea171cf411` : [run44481264121](https://github.com/jfrancoiscollin/dilf/actions/runs/44481264121), 22 tests, artefact14508148442 téléchargé/vérifié, ZIP SHA `32e33bfb6869f48ba707a68369652380c46eab9dfb22f7c1f6cc2e184cdf5533`. Les trois fichiers produits concordent octet par octet avec les deux seeds et les résultats/preuves archivés. Les **8/8 workflows** de ce commit réussissent, dont CI générale et D1.

```bash
python -m research.mtdp.jass_benchmark.two_arena_crossed_depth --root . --output /tmp/crossed.json
python -m research.mtdp.jass_benchmark.verify_two_arena_crossed_depth --root . --report /tmp/crossed.json --output /tmp/crossed-independent.json
```

Les résultats primaires SHA `3fd8f480902e50ffcace15552f5ad71e29571e08d0bf340c167d8ad9e21d45e7`, la sensibilité20 SHA `6076aba12d4e3427b33c6bc9c6ee101c57df1a99109b3638339c1e3570709f90` et les 114 reçus Jass ne sont pas réécrits. Unité brute Scan =0,01 HUB, pas un pion matériel calibré.

## Relais suivant et coordination

Prochain contrôle H13 justifié, avant un nouveau protocole moteur : auditer les neuf interventions `verified_tie` déjà archivées et les dépenses de vérification/résolution pour comprendre pourquoi aucun choix final contrôle/natif ne change aux trois budgets. Utiliser les seuls reçus existants, sans sélectionner un nouveau masque d'efficacité ni dupliquer D1. Si les reçus ne suffisent pas, décrire précisément l'instrumentation à préenregistrer plutôt que réinterpréter l'absence de différence comme équivalence.

Les quatre événements entiers fFgE7oED/P1RUlfJc/s7ahYqL4/D9PF2OSW et leurs FEN désormais scorées restent réservés hors D1 fitting/validation indépendante/signature/top-K/refinement/seuil/dimension. Aucun nouveau corpus réservé. Le PC de Jeff n'est pas nécessaire.
