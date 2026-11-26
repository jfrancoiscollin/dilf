# H13 — Oracle légal des dames historiques restantes, 26 novembre 2026

Protocole et résumé de sélection figés au commit 6b331c4268e4d634d4abd23d29c485a74c7129df avant tout appel aux générateurs sur cette population. PR43 ouverte/draft ; tête initiale 05187a3, neuf workflows success et aucun équivalent actif. Les anciens rejeux/scorings ne sont pas relancés.

**48 654 FEN historiques supplémentaires avec dame du côté au trait : zéro désaccord de racines légales corrigé/Jass, zéro régression nouvelle, zéro double clé Jass.** Dans ce reste, ancien et corrigé produisent également les mêmes ensembles de racines et de chemins : aucun ajout/retrait ni changement de chemin seul. La preuve réutilisée des 3 356 autres FEN historiques avec dame au trait complète donc la couverture **52 010/52 010** des plateaux de ce type dans les 25 sources historiques connues. Les omissions de retour identifiées auparavant appartiennent à la couverture antérieure ; ce nouveau résultat ne les efface pas.

## Population et intégrité

Registre conservateur authentifié : 455 582 FEN, hash d’ensemble 9db87b4e41804e95e0a376a6bef465d93b448f50698a53da237cc9bfd1f29f2a ; cache ancien plus supplément historique uniquement, cohérents avec le rejeu corrigé strict et les 190 quarantaines. La sélection lit uniquement les dames typées, le trait et la couverture antérieure, sans appel légal ou score. Les 52 010 FEN avec dame au trait se partagent en 3 356 déjà vérifiés et 48 654 nouveaux contrôles. Les 403 572 sans dame au trait restent hors de ce contrôle. Les positions exclusivement fraîches ne sont jamais introduites dans la population historique.

Liste figée triée avec LF final : 1 395 986 octets, SHA-256 464d7650531445c25b8e143aafc0c698620e176d34b51e614ffa84b5f1011949. Résumé versionné de la sélection : validation/king-origin-remaining-active-king-scope-2026-11-26.json, SHA-256 c9a64a0a9bf9a6b348a037973b27ca687fc0fda29dca1ba231a99fe4bb9aa5d0. Le runner recalcule le périmètre depuis les entrées authentifiées puis contrôle le résumé, le nombre, les octets et le digest de la liste avant l’oracle ; aucun fichier FEN libre accepté.

## Moteurs et méthode

Ancien adapter FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311 propre ; factory corrigée explicite king-origin-v1, source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d ; Jass légal cfe07fce6385b980553a898e9651d53419589ebc et exporteur existant. Aucun évaluateur ni recherche appelé. Chaque racine conserve origine, destination, masque des pièces prises et promotion ; les chemins Python sont comptés et hachés séparément. Lots de 1 000 au maximum, délai 30 s par appel. La provenance du binaire/compilateur est séparée des sorties sémantiques.

Deux sélections et deux comparaisons locales complètes, hashseeds défaut et 731, identiques à l’octet pour les cinq sorties sémantiques. 21 tests passent : frontières de sélection (trait/dames, exclusion antérieure, positions fraîches, ordre, syntaxe/digests), corruption/troncature du périmètre figé, métriques d’ajout/retrait/régression, parseur d’oracle et correction isolée. CI ciblée à confirmer.

## Reproduction

Le workflow restaure le cache historique du run 45783492727 (digest interne épinglé) et l’inventaire corrigé du run 45768311500 (SHA-256 9331319ea0a243a486969871803b22a48524a024227c4ac727dff0a1e223a93a). Construire l’exporteur légal selon le workflow, puis :

```sh
python -m research.mtdp.king_origin_remaining_oracle \
  --root . --cache historical-input/four-reserved-events-exclusions.json \
  --corrected-inventory corrected-input/possible-board-inventory.jsonl \
  --adapter fmjd --jass jass --executable /tmp/mtdp-remaining-king-build/mtdp_jass_legal_catalogue \
  --output-dir result
python -m unittest research.mtdp.tests.test_king_origin_remaining_scope \
  research.mtdp.tests.test_king_origin_remaining_oracle \
  research.mtdp.tests.test_king_origin_inventory_impact \
  research.mtdp.tests.test_return_capture_oracle \
  research.mtdp.tests.test_king_origin_correction
```

Ledger par position : 44 680 854 octets, SHA-256 0c821462e2bb614474db1cc63798dc3dc5397fd43f2ab34389234aedf649bb09. Catalogue Jass brut : 5 650 515 octets, SHA-256 09df1090750a040ebf17261a7c741101e00de577c42c79ab13a14859dd91f382. Témoins vides : SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. Le petit rapport versionné lie chaque sortie ; les gros fichiers sont conservés dans l’artefact reproductible.

## Limites et prochain contrôle

Concordance entre deux implémentations sur des ensembles de racines, pas preuve formelle des règles, d’identité des chemins joués, de meilleur coup ou d’équivalence minimax. Aucun nouveau score/ordre de recherche, signature, top-K, dimension ou gain moteur. Couverture des 25 sources connues seulement, aucune complétude globale MTDP. Cache, règles par défaut, anciens résultats, 190 quarantaines et frais 145/7 inchangés. uDIrrl1c entier reste candidat brut D1 non admis ; licence/provenance et indépendance restent portes séparées avant gel. Quatre événements réservés intégralement exclus ; aucune nouvelle réservation H13.

Après preuve CI, ne pas refaire ces 48 654 comparaisons. Prochain contrôle H13 justifié : délimiter puis préenregistrer l’oracle des FEN historiques sans dame au trait encore non vérifiés, soit 403 572 moins 18 950 déjà couverts = **384 622**, pour compléter le contrôle légal sur le registre connu sans nouvelle campagne décisionnelle D1. PC de Jeff non requis pour le contrôle présent.
