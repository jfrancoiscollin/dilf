# H13 — Rejeu corrigé des 4 634 anciens dossiers stricts, 26 novembre 2026

Préenregistrement avant toute exécution sur cette population. Tête b9e847afe0dac96b755316e69f6e9535f77433ec ; PR43 ouverte/draft ; neuf contrôles success et aucun job équivalent actif. Les 190 quarantaines historiques ont déjà une reconstruction de plateaux corrigée vérifiée ; ce contrôle couvre les 4 634 dossiers complémentaires, sans nouvelle campagne décisionnelle D1.

## Population et références figées

Authentifier le cache ancien SHA-256 5cb424740ca8b3c1629b81a7add1b71420f9842cc8d321e82ef7ec926932fcb7 et les trois membres historiques épinglés de historical_exclusion_inventory_audit.MEMBERS. Réconcilier les 25 sources et leurs 4 824 identités fichier/index ; sélectionner tous les statuts indexed/duplicate (4 634 dossiers, 4 468 empreintes distinctes), conserver les 190 quarantaines. Lier chaque PDN par son digest exact depuis l’artefact historique du run 45776093044 ou les sources versionnées ; aucun remplacement de partie ou rééchantillonnage.

## Méthode et arrêts

Utiliser la factory explicite king-origin-v1 (source corrigée 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d), sans modifier les règles par défaut. Pour chaque partie, explorer toutes les actions correspondant au token PDN, avec les bornes existantes 128 plateaux par frontière et 100 000 applications par dossier. Conserver les ambiguïtés de chemin. Un plateau unique par ply permet seulement une empreinte de suite de plateaux : comparer au sérialiseur historique state_to_fen/LF, sans prétendre certifier le chemin joué. Plusieurs plateaux, zéro frontière ou borne doivent être rapportés comme résultats scientifiques incomplets, jamais résolus arbitrairement.

Réutiliser seulement la preuve des 190 quarantaines issue de la reconstruction vérifiée SHA-256 c774e71d1bd29aec50e63a285fb1755dcd558393f8eaa7ef89af5be7802584bc et son inventaire authentifié SHA-256 9331319ea0a243a486969871803b22a48524a024227c4ac727dff0a1e223a93a, en filtrant le rôle historique. Comparer les FEN visités au cache ancien et au supplément versionné SHA-256 3d3a5dd6326b6815541b402b451c6273917252dc9955a9cefe88b8341b7ce1f8 : compter nouvelles possibilités hors registre, pertes de couverture et changements d’empreinte par partie. Toute possibilité nouvelle reste diagnostic et exige un oracle Jass légal indépendant séparé avant extension du registre. Ne pas élargir automatiquement la portée des validations Jass précédentes.

## Sorties et validation

Rapport déterministe par dossier (statut ancien conservé, bornes, ambiguïtés, comparaison d’empreinte), digest de l’ensemble des FEN visités et inventaire des seules possibilités hors registre avec propriétaires/plies. Tests synthétiques : ambiguïté de chemins à même plateau, divergence de plateaux, tronquage/bornes, empreinte et sérialiseur, propriété historique et intégrité des entrées. Deux exécutions hashseeds défaut/731, reproduction Actions et comparaison des octets. Aucun score, signature, top-K, dimension, split ou sélection de cible.

La couverture des 25 sources connues ne prouve pas la complétude de tout l’historique MTDP, ni l’indépendance ou l’admission d’une nouvelle cohorte. Cache/résultats anciens et 190 quarantaines conservés ; uDIrrl1c brut non admis, quatre événements réservés intégralement exclus, aucune nouvelle réservation H13. Licence/provenance externe restent portes D1 distinctes. PC de Jeff non requis si ces rejeux bornés aboutissent sur Actions.
