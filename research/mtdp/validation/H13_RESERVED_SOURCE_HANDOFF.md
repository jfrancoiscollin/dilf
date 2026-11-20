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

## Contrôle des exports modifiés (20 novembre 2026)

`reserved_source_gate` réauthentifie les quatre sources et recherche trois clés : empreinte exacte de l'export, identifiant public, empreinte de l'état initial et de la séquence de notation normalisée déjà utilisée par H13. Ainsi, un autre SHA de fichier ne suffit pas à libérer une partie réservée.

```bash
python -m research.mtdp.reserved_source_gate --root . --candidate CANDIDATE.pdn --expected-sha256 SHA256 --output /tmp/reserved-screen.json
python -m pytest -q research/mtdp/tests/test_reserved_source_gate.py
```

Le CLI écrit le rapport puis sort avec le code **2** dès qu'une partie correspond ; l'export entier est bloqué sans filtrage opportuniste. Une sortie 0 signifie seulement « aucune identité réservée connue détectée » : `independent_cohort_qualified` et `eligible_for_freeze` restent false. Ce contrôle est une proposition exécutable H13 avant qualification, **pas encore un raccord automatique dans l'admission D1**. D1/H43 doivent décider son raccordement et compléter les autres exclusions ; aucun module D1 n'est changé ici.

Contrôle sur les octets historiques s7ahYqL4 : ajout d'une nouvelle ligne → 147/147 parties retrouvées ; export de la première partie seule → 1/1 ; remplacement de son Site par une nouvelle identité synthétique → 1/1 via la notation. Les empreintes des trois variantes sont distinctes de l'original. Résultats et limites dans `reserved-source-alias-screen-2026-11-20.json` ; les trois transformations sont reprises dans les tests. Les parties ambiguës restent exclues entières.

La notation identique est une exclusion conservatrice, pas une preuve d'identité de trajectoire canonique : des parties courtes peuvent coïncider et deux notations de prises peuvent représenter la même trajectoire sans partager cette empreinte. Aucun moteur FMJD ni score Scan/Jass n'est consulté ; les FEN/trajectoires et l'authentification externe demeurent nécessaires avant gel.

## Liaison publique URL→PDN confirmée le 20 novembre 2026

`reserved-public-endpoint-binding-2026-11-20.json` rapporte quatre nouveaux GET HTTPS des points publics `https://lidraughts.org/api/tournament/{event}/games`. Les quatre réponses HTTP200 sont strictement identiques aux octets archivés : fFgE7oED169802octets/157parties, P1RUlfJc272395/241, s7ahYqL4164438/147, D9PF2OSW75628/61. Les dates UTC de requête/réception, URLs finales, tailles et SHA-256 sont conservés. Aucun nouvel export n'a remplacé l'archive et aucun score de recherche n'a été acquis.

```bash
python -m research.mtdp.reserved_endpoint_verification --root . --output /tmp/reserved-endpoint-check.json
python -m pytest -q research/mtdp/tests/test_reserved_endpoint_verification.py
```

La première commande refait quatre requêtes publiques, à deux connexions simultanées maximum ; elle exige exactement les mêmes endpoints HTTPS, tailles et empreintes épinglées, refuse tout remplacement et n'écrase jamais un précédent rapport. La seconde est entièrement hors ligne. Toute différence ou indisponibilité empêche la production d'un rapport de succès.

Cette preuve lie **les endpoints publics actuels** aux exports H13 connus. Les indicateurs false de l'ancien inventaire restent des observations historiques ; on ne les réécrit pas pour suggérer une qualification globale. Aucun compte de joueur, annotation, légalité FMJD, totalité des exclusions historiques ou indépendance statistique n'est certifié par un GET. Il reste à raccorder l'écran réservé à D1 et réconcilier les autres identités/FEN/trajectoires avant tout protocole et gel H13 d'une nouvelle cohorte.
