# H13 — Successeurs historiques à risque, 26 novembre 2026

Protocole et périmètre publiés avant les transitions : 609c6d943f54fc0311cdcf7ad1d91cf1e2d75448. Tête initiale 619b416, PR43 ouverte/draft, neuf contrôles success, aucun équivalent actif/en attente. Le vieux job CI en attente sur une autre tête ne concerne pas cette campagne et n’est pas annulé.

**24 558 nouveaux parents historiques, 89 904 chemins Python et 89 505 couples parent/racine : zéro différence de successeur, zéro divergence avec les références légales gelées, zéro double clé Jass.** Les 351 racines à plusieurs chemins sont toutes conservées ; aucun parent ni chemin n’est retiré ou choisi arbitrairement. Aucun ensemble de successeurs ne diverge sous une même racine.

## Sélection sans scores

Les quatre catalogues légaux déjà authentifiés totalisent 468 231 FEN distinctes : 455 582 appartiennent exactement au registre historique connu et 12 649 sont exclues comme hors registre. Aucun générateur de coups ou de transitions n’est appelé pendant cette dérivation. Critère structurel : racine qui revient à l’origine en prise, promeut un pion ou prend au moins deux pièces. Sur 24 560 FEN historiques éligibles, deux parents déjà testés sont retirés, soit 24 558 nouveaux parents ; les 20 témoins précédents ne sont pas rejoués. Toutes les racines de chaque parent retenu sont vérifiées, pas seulement les 34 190 racines qui ont déclenché l’inclusion.

Catégories recoupées, non additionnables : 15 854 FEN avec prise multiple, 9 837 avec promotion, trois avec retour à l’origine. Le manifeste conserve les tags, le catalogue d’origine et toutes les racines. Il ne fabrique pas d’identifiants de parties ni de groupes indépendants. Les tableaux par catégorie du rapport comptent tous les enfants des parents étiquetés ; par exemple, les 71 427 racines sur les parents étiquetés promotion ne sont pas 71 427 promotions.

Résumé figé validation/risk-successor-scope-2026-11-26.json SHA-256 5a53f93124cba011dc69b928403c0574e1f25177700e78d260815055242a4100. Manifeste : 7 281 370 octets, SHA-256 630fcb960a8121fba170236e0b4a1be079dea2c7c660b2d26a2ae01c409f0ddd. Liste triée/LF final : 1 310 358 octets, SHA-256 941bd609f29ec7825d8bf4ed739bb0a8453a217fcd238d8a9698e20b394c9bf3. Le runner exige ces octets et digests exacts avant toute transition.

## Méthode et validation

Factory explicite king-origin-v1/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d au-dessus du FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311 ; Jass cfe07fce6385b980553a898e9651d53419589ebc, exporteur de successeurs et wrapper isolé déjà validés. La recette historique targets.cmake reste inchangée. Référence de racines reprise depuis les catalogues existants, sans rejouer les campagnes de racines. Les nouvelles transitions nécessitent naturellement l’énumération des coups des seuls parents retenus. Chaque chemin Python est appliqué et comparé au successeur Jass de sa racine correspondante. Identité : occupation typée + trait, hors compteurs de nulle, répétition et certification du chemin joué. Lots de 1 000, délai 30 s/appel ; traces et digests écrits progressivement.

Deux dérivations et deux contrôles locaux complets, hashseeds défaut/731, identiques à l’octet pour leurs sorties sémantiques. 30 tests passent : sélection historique et exclusion des témoins, catégories recoupées, référence complète conservée, parent absent/dupliqué, corruption des sources/manifeste, changement de racine gelée malgré accord des deux moteurs, chemins divergents, mauvais trait, attentes manuelles et correction isolée. **Reproduction distante vérifiée** : implémentation 34b4a982762189be9d362c0865a884249d4fc792, [run 45819172437](https://github.com/jfrancoiscollin/dilf/actions/runs/45819172437), job 139906640398 success. 30 tests ; dérivation du manifeste depuis les artefacts existants et cmp du résumé figé ; compilation isolée ; une reproduction des 24 558 parents sous hashseed 731 puis cmp du rapport réussis. Artefact 15116987046 téléchargé, ZIP 3 901 246 octets SHA-256 560af0616827f4607354589ba0a2ca9c402708442d187b61930e78a7accea81c conforme GitHub ; ses sept fichiers sémantiques sont tous identiques aux deux exécutions locales. GNU 15.2 distant/GNU 14.2 local, provenances binaires séparées et recette historique 11cedf28… inchangée. Preuve structurée : validation/risk-successor-ci-proof-2026-11-26.json. Huit autres contrôles courts de cette tête success, rejeu historique courant encore actif sans échec observé.

Rapport versionné validation/risk-successor-audit-2026-11-26.json ; les gros fichiers sont liés par digest dans l’artefact. Ledger de successeurs : 37 563 019 octets, SHA-256 1c0ef3f36a7c11b8b41d240328621a8d968fbb8f6edc2a2b31531bddc370f59d. Catalogue Jass brut : 5 519 830 octets, SHA-256 2775dc3fda44ccd4b34744a91032d6bd4901ded3eec2774cfd7253e2b8884ea2. Témoins de désaccord vides : SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. Provenances source/binaire/compilateur séparées des sorties sémantiques.

## Reproduction

Restaurer les artefacts indiqués dans le workflow : cache historique run 45810902904, impact 45761500008, reconstruction 45768311500, dames restantes 45790633522, non-dames 45801358408. Les quatre rapports, digests de catalogues, comptes de lignes, couverture historique et exclusions antérieures sont contrôlés avant la sélection. Puis :

```sh
python -m research.mtdp.risk_successor_scope \
  --root . --cache historical-input/four-reserved-events-exclusions.json \
  --corrected-inventory reconstruction-input/possible-board-inventory.jsonl \
  --impact-catalogue impact-input/jass-catalogues.txt \
  --new-state-catalogue reconstruction-input/new-state-jass-catalogues.txt \
  --king-catalogue king-input/jass-catalogues.txt --nonking-catalogue nonking-input/jass-catalogues.txt \
  --output-dir scope
python -m research.mtdp.risk_successor_audit \
  --root . --manifest scope/risk-successor-manifest.jsonl --fens scope/risk-successor-fens.txt \
  --adapter fmjd --jass jass --executable /tmp/mtdp-risk-successor-build/mtdp_jass_successor_catalogue \
  --output-dir result
```

## Limites et suite

Le critère à risque est une sélection structurelle diagnostique, pas un échantillon représentatif d’efficacité ou une estimation probabiliste du risque. Ni meilleur coup/minimax, ni complétude historique globale. Les transitions historiques vérifiées couvrent 24 561 FEN distinctes (les 24 558 nouvelles plus trois des 20 témoins antérieurs présents au registre) ; **431 021 FEN du registre connu restent hors contrôle indépendant des successeurs**. Les campagnes de racines closes ne doivent pas être refaites.

Contrôle du périmètre à risque clos. Prochain contrôle H13 justifié : délimiter et préenregistrer le complément de successeurs des 431 021 FEN historiques restantes, en réutilisant leurs catalogues légaux gelés, pour terminer cette validation de règles sur le registre connu. Aucun nouveau scoring ou résultat d’efficacité issu de ces contrôles. uDIrrl1c entier reste candidat brut D1 non admis ; licence/provenance/indépendance fraîche demeurent des portes D1 séparées. Aucun nouveau split, gel ou réservation H13, aucune signature/top-K/dimension ; quatre événements réservés exclus, cache/règles par défaut/anciens scores/190 quarantaines/frais 145-7 inchangés. PC de Jeff non requis.
