# H13 — format des FEN historiques et exclusions D1

**Audit du cache existant, sans nouveau score, moteur de recherche ou cohorte.** Le cache authentifié conserve l'empreinte `5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7`.

La fonction historique `pedagogy.game.state_to_fen` écrit d'abord les dames, puis les pions. D1 `fmjd_fen.canonical_fen` trie toutes les cases numériquement en conservant leur type. Il s'agit de deux écritures du même état, pas de positions ou règles différentes.

Sur les **452 526 FEN distinctes** du cache :

- 47 104 changent d'ordre d'écriture lors de la normalisation D1 ;
- ces 47 104 formes D1 sont absentes telles quelles de l'ensemble brut ;
- la vue normalisée conserve 452 526 positions distinctes : aucune position perdue ou nouvel alias fusionné dans ce cache.

Exemple vérifié :

```text
B:W10,12,28,31,33,37:BK45,8,26,35
B:W10,12,28,31,33,37:B8,26,35,K45
```

Une comparaison textuelle entre une FEN D1 et le seul ensemble historique brut manquerait donc cette exclusion. L'audit ne prétend pas qu'une cohorte déjà admise ait subi cette fuite : aucune cohorte indépendante n'est qualifiée.

## Raccord H13

`historical_fen_bridge.load_historical_fens` vérifie l'empreinte entière du cache avant de construire une vue normalisée en lecture seule. Toute FEN historique mal formée fait échouer le chargement ; aucune ligne n'est abandonnée. Les FEN des observations sont normalisées avec la même fonction avant comparaison.

`preflight_sources(..., historical_cache=PATH)` effectue ce contrôle après authentification des octets et du schéma, avant tout rejeu. Le témoin réel construit un PDN synthétique authentifié contenant une position historique réordonnée : il est rejeté avant le premier appel aux règles. L'appel ancien sans cache reste compatible mais rapporte explicitement `historical_fen_cache_screened=false` ; il ne prouve pas l'exclusion de ces 452 526 positions.

**Le cache, ses anciennes empreintes et les modules D1 restent inchangés.** Les empreintes de trajectoires historiques hachent une séquence produite par le sérialiseur historique : ne pas les comparer à un hachage de FEN nouvellement réordonnées. Pour les trajectoires, réutiliser la définition exacte `named_arena_replay.trajectory_fingerprint` sur les états légalement rejoués et son code épinglé ; le présent raccord traite seulement les exclusions FEN des observations.

## Reproduction et portée des validations

L'artefact Actions `14720090094`, run44936118850, a été téléchargé : 14 754 566 octets, SHA-256 `e16bac76180a1278b9f4d532ab27d5b94de55aeac825e37094f5bff9ca5f2613`. Le membre `four-reserved-events-exclusions.json` correspond exactement au SHA du cache ci-dessus.

```bash
python -m research.mtdp.historical_fen_bridge --cache CACHE.json --output /tmp/fen-bridge.json
cmp /tmp/fen-bridge.json research/mtdp/validation/historical-fen-bridge-2026-11-21.json
MTDP_HISTORICAL_FEN_CACHE=CACHE.json MTDP_REQUIRE_HISTORICAL_FEN_CACHE=1 python -m pytest -q research/mtdp/tests/test_historical_fen_bridge.py research/mtdp/tests/test_prospective_source_preflight.py
```

Localement : 14 tests réussis, y compris le test sur le cache réel. La CI générale peut sauter ce dernier sans l'artefact ; la nouvelle commande du workflow historique fournit le cache et exige sa présence. Son rapport et ses tests seront archivés avec les sorties existantes.

Le contrôle reste limité aux positions observées du cache connu. Les trajectoires complètes, alias et autres manifestes doivent encore être réconciliés. `independent_cohort_qualified=false`, `complete_historical_exclusion_registry=false` et `eligible_for_freeze=false` demeurent obligatoires. Aucun nouveau gel, seuil, signature ou résultat Jass n'est introduit.
