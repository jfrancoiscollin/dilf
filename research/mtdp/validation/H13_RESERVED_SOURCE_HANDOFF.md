# H13 → D1/H43 : identités réservées dans les exports archivés

L'inventaire `h13-reserved-source-inventory.json` énumère **toutes les parties** des quatre exports H13 déjà archivés, pas seulement les positions ciblées ou éligibles. C'est une aide à l'exclusion ; aucune nouvelle cohorte n'est admise, aucun score ou moteur n'est appelé.

| Événement réservé entier | Parties de l'export archivé |
|---|---:|
| fFgE7oED | 157 |
| P1RUlfJc | 241 |
| s7ahYqL4 | 147 |
| D9PF2OSW | 61 |
| Total des entrées | 606 |

Chaque entrée relie `game_id=<sha256 des octets PDN>:<index 1-based>` à `public_game_id`, avec source, empreinte et index explicites. Ce total ne désigne ni 606 parties indépendantes ni 606 parties légalement rejouées : les parties ambiguës sont elles aussi exclues entières. Les exports répétés concordants ne sont pas recomptés.

## Reproduction sans score ni moteur

```bash
python -m research.mtdp.reserved_source_inventory --root . --output /tmp/h13-reserved-source-inventory.json
cmp /tmp/h13-reserved-source-inventory.json research/mtdp/validation/h13-reserved-source-inventory.json
python -m pytest -q research/mtdp/tests/test_reserved_source_inventory.py
```

L'archive historique entière, chaque PDN et les nombres de parties sont épinglés ; octets altérés, indexation ambiguë, suffixe post-résultat et identifiant public absent/répété font échouer le producteur. Aucun fichier existant n'est écrasé.

## Usage et limites du relais

D1 peut extraire les `game_id` de `events[*].games[*]` comme lignes `{"game_id": "..."}` d'un registre interdit pour `cohort_exclusion_gate`. Cela ne suffit jamais à qualifier le registre d'exclusions complet : conserver aussi les identifiants publics, les exclusions par événement entier et les identités de trajectoire/FEN déjà confirmées. Un changement d'octets, d'ordre des parties ou un export partiel change l'identifiant adressé par contenu ; une nouvelle empreinte ne rend donc pas une partie indépendante.

L'association événement→export suit les sources archivées et gels H13 précédents ; cette publication ne constitue pas une nouvelle authentification externe des labels. Aucun inventaire de toutes les FEN/trajectoires n'est produit. Les autres corpus historiques (PC Blues, Scan, benchmarks Jass et alias) restent à réconcilier par H43/D1 avant toute qualification puis protocole et gel prospectifs H13. Les quatre événements entiers et leurs FEN restent interdits pour fitting, validation indépendante, signatures, top-K, refinement, seuils et réduction de dimension.

Validation locale : 7 nouveaux tests ; sélection avec admission D1 et exclusions historiques : **20 tests réussis**. La CI du commit publié doit être confirmée séparément ; aucun résultat ancien n'est modifié.
