# H13 — Supplément conservateur d’exclusion, 26 novembre 2026

Protocole préalable : d3aa8af0faee195f3bbda7060a1c6d79e13c0ca0. Aucune expérience décisionnelle nouvelle : ce contrôle ferme le raccordement des plateaux historiques possibles déjà reconstruits au filtre D1.

Le cache ancien reste intact : 452 526 FEN canoniques, règles 0e5189f. L’inventaire corrigé authentifié (SHA-256 9331319ea0a243a486969871803b22a48524a024227c4ac727dff0a1e223a93a ; reconstruction vérifiée run 45768311500) donne **3 056 FEN historiques supplémentaires**, donc **455 582 exclusions**. Le supplément est limité aux propriétaires historical_quarantines et conserve leurs numéros de ply. Il retire tous les propriétaires fresh_candidate ; les positions exclusivement fraîches restent hors supplément. Les deux collisions BZZ0yME2/CARZrQpl:1338 restent exclues par leur provenance historique. Les 4 790 ID publics, 25 sources et 4 468 empreintes de trajectoires complètes sont ceux du cache ancien ; aucun chemin joué n’est inféré depuis un plateau possible.

Le chargeur authentifie les entrées, recalcule tout le supplément et le manifeste, puis exige les mêmes octets. Raccordement explicite : `audit_authenticated_corpus(..., exclusion_ledger={'inventory': ..., 'manifest': ..., 'supplement': ...})`. L’API historique sans cette option garde son registre ancien. Le chemin explicite ajoute les empreintes canoniques au filtre D1 existant sans modifier son verdict de complétude historique. Le résultat porte le hash du manifeste ; une réussite structurelle conserve indépendance, gel, complétude globale et identité externe à false.

Fichiers durables : validation/conservative-exclusion-manifest-2026-11-26.json (1 292 octets ; SHA-256 8a2991c3efbece3fdd4bf5e4db15c12e7b2bc176855250a0d57ae51dcca88c32) et validation/conservative-historical-supplement-2026-11-26.jsonl (725 290 octets ; SHA-256 3d3a5dd6326b6815541b402b451c6273917252dc9955a9cefe88b8341b7ce1f8). Hash de l’ensemble canonique trié, séparateur LF sans LF final : 9db87b4e41804e95e0a376a6bef465d93b448f50698a53da237cc9bfd1f29f2a.

## Reproduction

Restaurer le cache `four-reserved-events-exclusions.json` depuis l’artefact historique du run 45768699809 (hash interne épinglé par le chargeur) et `possible-board-inventory.jsonl` depuis le run 45768311500. Le workflow dédié restaure exactement ces entrées.

```sh
python -m research.mtdp.conservative_exclusion_ledger \
  --cache historical-input/four-reserved-events-exclusions.json \
  --inventory corrected-input/possible-board-inventory.jsonl \
  --output-dir result
MTDP_HISTORICAL_FEN_CACHE=historical-input/four-reserved-events-exclusions.json \
MTDP_CORRECTED_INVENTORY=corrected-input/possible-board-inventory.jsonl \
MTDP_REQUIRE_CONSERVATIVE_LEDGER=1 \
python -m unittest research.mtdp.tests.test_conservative_exclusion_ledger
```

Deux dérivations locales, hashseeds défaut et 731, identiques à l’octet. Dix tests initiaux passent (71,4 s), puis test additionnel du chemin structurel sans admission exécuté séparément. Les 35 tests existants bridge authentifié/admission D1 passent avec cache et adaptateur épinglés, sans skip. L’absence initiale de pytest dans l’environnement local a été résolue dans un répertoire temporaire ; aucun test évité. CI ciblée à confirmer avant d’affirmer une reproduction distante.

## Limites et suite

Exclusion conservatrice de plateaux possibles, pas certification d’un chemin de prise joué, ni preuve d’équivalence stratégique. Les 190 quarantaines historiques et sept ambiguïtés fraîches persistent. Les 4 634 anciens dossiers strictement complets n’ont pas été rejoués avec king-origin-v1 : ce supplément n’est pas un registre global complet. Cache, moteur par défaut et anciens scores restent identiques.

Aucune nouvelle cohorte H13 réservée ou gelée ; uDIrrl1c entier reste candidat D1 brut non admis. Les quatre événements réservés restent exclus de l’ajustement et de l’évaluation D1. Aucun score Scan/Jass, signature, top-K, réduction de dimension ou coût moteur supplémentaire mesuré ici. Prochaine action : confirmer l’artefact distant, puis qualifier la licence/provenance et l’indépendance de la source fraîche ; si un replay corrigé plus large est justifié, le préenregistrer séparément. Ne pas relancer les campagnes décisionnelles closes. PC de Jeff non requis.
