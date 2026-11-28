# H13 — Extension historique des successeurs à risque, 26 novembre 2026

Préenregistrement après dérivation structurelle depuis les catalogues authentifiés, avant tout appel de transition sur ce périmètre. PR43 ouverte/draft à 619b416c63f8749623d2b9aadaea970f29f1e56d ; neuf contrôles success, aucun équivalent actif/en attente. Ancien job CI en attente sans rapport conservé.

## Population fixe et couverture

Les quatre catalogues existants totalisent 468 231 parents distincts (34 172 impact, 783 nouveaux états, 48 654 dames actives restantes, 384 622 non-dames restantes). Ils couvrent exactement les 455 582 FEN du registre historique connu ; les 12 649 FEN hors registre sont exclues. Aucun nouveau calcul de coups légaux n’a été utilisé pour la sélection.

Critère fixé : au moins une racine légale (a) retourne à son origine en prise, (b) promeut un pion, ou (c) capture au moins deux pièces. 24 560 FEN historiques satisfont le critère ; retirer les deux parents à risque déjà couverts par les 20 témoins précédents donne **24 558 FEN**, **89 505 racines légales au total**, dont **34 190 racines à risque**. Tous les coups de chaque parent sont comparés, pas seulement le coup qui a déclenché l’inclusion. Catégories qui se recoupent : 15 854 FEN de prise multiple, 9 837 de promotion, 3 de retour à l’origine. Leurs comptes ne sont pas additionnables. Les 20 témoins ne sont pas rejoués.

Le manifeste garde chaque FEN, son catalogue d’origine, toutes ses racines légales et les tags des racines à risque ; aucune association de parties indépendantes n’est inventée. Résumé figé validation/risk-successor-scope-2026-11-26.json SHA-256 5a53f93124cba011dc69b928403c0574e1f25177700e78d260815055242a4100. Ce résumé lie les digests/tailles exacts de la liste et du manifeste, ainsi que les quatre preuves d’entrée et l’exclusion des témoins déjà validés. Les données sont entièrement historiques et réservées ; aucune cohorte prospective ou partition D1 nouvelle.

## Contrôle préenregistré

Même factory explicite king-origin-v1/source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d sur FMJD 0e5189fbb251bf5eaf2e613d0f878bb17c740311, Jass cfe07fce6385b980553a898e9651d53419589ebc. Réutiliser l’exporteur de successeurs isolé et son wrapper successor-targets.cmake ; ne pas modifier targets.cmake ni les méthodes historiques gelées.

Pour chaque parent, comparer les racines du nouvel export à celles déjà authentifiées dans le manifeste ; comparer ensuite chaque chemin Python et son successeur à la racine/au successeur Jass correspondant. Ne pas choisir arbitrairement un chemin. Identité : occupation typée+trait uniquement, hors compteurs de nulle/répétition et certification du chemin joué. Lots de 1 000 maximum, délai par appel 30 s. Écrire les traces progressivement ; rapporter tous désaccords, doubles clés et chemins divergents sans retrait de cas. Une différence scientifique reste un résultat, seuls les problèmes techniques sont corrigés/rejoués par défaut.

Tests adversariaux de sélection (FEN non historiques, exclusion préalable, parent manquant/dupliqué, recoupement des catégories, conservation de toutes les racines), d’intégrité du manifeste et de transitions ; deux dérivations et deux contrôles locaux hashseeds défaut/731, une reproduction Actions 731 et comparaison de tous les fichiers sémantiques. Rapports et gros artefacts liés par SHA-256 ; provenance binaire/compilateur séparée. Aucun score, recherche, signature, top-K ou dimension.

Une réussite ne vaudra que pour ces parents et leurs coups, sans couverture de tous les successeurs du registre, vérité formelle des règles, meilleur coup ou équivalence minimax. Ne pas présenter la sélection à risque comme un échantillon représentatif d’efficacité. Cache/règles par défaut/anciens scores/190 quarantaines/frais 145-7 inchangés, quatre événements réservés exclus ; uDIrrl1c entier toujours brut non admis. D1 garde ses portes licence/provenance/indépendance. Aucun nouveau gel ou réservation scientifique H13. PC de Jeff non requis si ces calculs aboutissent à distance.
