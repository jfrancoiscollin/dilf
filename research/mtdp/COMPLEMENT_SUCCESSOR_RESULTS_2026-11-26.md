# H13 — Complément historique des successeurs, 26 novembre 2026

Protocole publié avant transitions : `2d8429a0ce65740848f0f6888da2d9ce774e4f12`. PR43 ouverte/draft, aucun job équivalent actif ou en attente avant lancement ; ancien CI sans rapport conservé. Le contrôle des meilleurs coups et des budgets égaux est déjà clos dans les rapports deux arènes du 19 novembre et la sensibilité du 22 novembre : aucune nouvelle analyse d’efficacité n’est revendiquée ici.

## Résultat et dénominateurs

Le complément fixé contient **431 021 FEN historiques** et **3 576 681 couples parent/racine**. Les 3 576 681 chemins Python calculés par la factory explicite king-origin-v1 et tous leurs successeurs occupation typée+trait concordent avec Jass cfe07fc ; **zéro désaccord**, zéro différence avec les racines légales authentifiées, zéro clé Jass dupliquée ou racine à plusieurs successeurs. Tous les chemins ont été appliqués avant les digests du ledger ; aucun échantillonnage ni choix du premier chemin.

| Catalogue d’origine | Parents du complément | Désaccords |
|---|---:|---:|
| Dames actives | 44 527 | 0 |
| Impact initial | 20 908 | 0 |
| Sans dame active | 365 545 | 0 |
| Reconstruction corrigée | 41 | 0 |
| Total | 431 021 | 0 |

Le manifeste retire les **24 561 parents historiques déjà vérifiés** et les 12 649 FEN hors registre. L’union disjointe ferme donc les catalogues légaux et les successeurs de **455 582 FEN des 25 sources connues**. Cela ne démontre ni complétude de tout l’historique MTDP, ni équivalence minimax/meilleur coup, ni règles universelles, ni compteurs nulle/répétition ou identité du chemin réellement joué.

## Reproduction

Deux dérivations locales défaut/731, identiques à l’octet pour le résumé, le manifeste complet et la liste des parents. Deux audits locaux complets défaut/731 sont identiques à l’octet (rapport, ledger, témoins, brut et provenance locale). **Reproduction Actions confirmée** : implémentation d423aa4, run 45830653273/job139946217678 success, 33 tests. Artefact15122354253 téléchargé (75256126 octets), ZIP SHA-256 366582b4405ce265147e5f604f71482d6002598a0f3cc80b0523a0067d28fbc3 conforme GitHub ; sept fichiers sémantiques tous identiques aux deux runs locaux. GNU15.2 distant/GNU14.2 local, provenances séparées. Reçu `validation/complement-successor-ci-proof-2026-11-26.json` versionné. Les 33 tests de périmètre, intégrité de flux, successeurs complets, désaccord typé, parseur et correction passent. Commandes de reproduction et téléchargements des six artefacts épinglés dans `.github/workflows/mtdp-complement-successor-audit.yml` ; aucune acquisition de nouvelles parties ni recherche moteur. Lots de 1 000, mémoire et I/O bornées, fichier témoin complet pour chaque éventuel désaccord.

| Sortie | Octets | SHA-256 |
|---|---:|---|
| Résumé de périmètre | 2 746 | 2f12d7dfd9c330edab6bd3a2e17f72744a8f0d53cfab3748a041428da183971e |
| Manifeste | 108 610 881 | 5123971a002f9e2a07f41649ed155cc5068000f573c81d1afab714b0c574941e |
| Liste FEN | 29 517 395 | ae6d5b47af468cb778f47f29e22fbfc7c6329579865cbc247132c2e0f45b7e80 |
| Rapport | 3 052 | 1f1253191c6478fac4662b29fa1c67c5cf73d610903ffc58f489cb4463bcdad0 |
| Ledger compact | 221 581 268 | 74f7eaf79f62e1812b93c08d4a88e7192e4720410c889fc5dfeb92c8d16b6d2b |
| Catalogue Jass intégral | 302 128 071 | acff8b3471d73450f01fc4fa8a9da7570c60bc8bde502beb4a5b7a5092d18281 |
| Témoins | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |

Provenances binaire/compilateur séparées des sorties sémantiques. Source corrigée 4714fef6…, ancien moteur et factory par défaut inchangés ; `targets.cmake` reste à 11cedf28… et wrapper de successeurs séparé à 38b7a385… .

## Suite H13 et coordination D1

Après reproduction distante, ne plus refaire les campagnes de racines/successeurs de ce registre. Préenregistrer une entrée prospective **explicitement versionnée** du préflight authentifié utilisant king-origin-v1 et le registre conservateur d’exclusions : l’entrée actuelle `audit_authenticated_corpus` appelle encore `checked_engine` historique. Préserver cette API et ses reçus ; vérifier des témoins de retour/promotion/prises et des trajectoires corrigées sans score, avec identité de règles déclarée et refus des preuves appelant un autre moteur. Cette entrée nouvelle ne pourra à elle seule admettre ni geler une cohorte.

uDIrrl1c entier reste brut non admis ; licence du corpus, provenance et indépendance fraîche restent les gates D1. Aucun score/signature/top-K/dimension, partition, gel, nouvelle réservation H13 ou campagne D1 dupliquée. Quatre événements réservés exclus, cache/règles par défaut/anciens scores/190 quarantaines/frais145-7 préservés. Aucun besoin du PC de Jeff pour ce contrôle borné sur les ressources distantes existantes.
