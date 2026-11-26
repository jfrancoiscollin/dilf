# H13 — Oracle légal des dames historiques restantes, 26 novembre 2026

Préenregistrement après délimitation structurelle, avant tout appel aux générateurs sur les nouvelles positions. Tête 05187a3806afd28fb368c43a1b8a92b2a96a5144, PR43 ouverte/draft, neuf workflows success, aucun job équivalent actif. Les contrôles décisionnels antérieurs restent clos ; aucune campagne D1 dupliquée.

## Population figée

Registre historique conservateur de 455 582 FEN des 25 sources connues, authentifié depuis le cache ancien et son supplément, cohérent avec le rejeu corrigé des 4 634 stricts et 190 quarantaines. Parmi 52 010 FEN avec au moins une dame du côté au trait, retirer exactement les 3 356 déjà contrôlés dans l’union vérifiée Jass de 34 955 FEN. Reste : **48 654 FEN**. Ne jamais réintroduire les positions exclusivement fraîches dans cette population historique. Liste triée, une FEN canonique par ligne avec LF final : 1 395 986 octets, SHA-256 **464d7650531445c25b8e143aafc0c698620e176d34b51e614ffa84b5f1011949**. Résumé de sélection : SHA-256 c9a64a0a9bf9a6b348a037973b27ca687fc0fda29dca1ba231a99fe4bb9aa5d0. La sélection dépend exclusivement des plateaux/trait/dames et de la couverture légale antérieure, jamais de scores, signatures ou rangs.

## Comparaison et sorties

Même adapter historique 0e5189fbb251bf5eaf2e613d0f878bb17c740311, correction explicite king-origin-v1 (source 4714fef6966f2433dba42b6be3981180b87d85f69a1c6825f38599711b16aa0d), Jass légal épinglé cfe07fce6385b980553a898e9651d53419589ebc et exporteur existant. Aucun évaluateur ou recherche appelé. Pour chaque FEN comparer les ensembles complets de racines (origine, destination, masque de prises, promotion) ancien/corrigé/Jass. Conserver séparément comptes/empreintes des chemins Python ; l’oracle ne certifie pas l’identité du chemin joué. Lots de 1 000 au plus, délai 30 s par appel ; conserver provenance du binaire/compilateur séparément des sorties sémantiques.

Produire résumé, ledger par position, témoins de toute modification ou désaccord, catalogue Jass brut et liste figée. Rapporter changements de racines/chemins, ajouts/retraits, désaccords ancien/Jass et corrigé/Jass, régressions nouvelles et doubles clés Jass. Un désaccord est un résultat scientifique à diagnostiquer sous protocole distinct, pas une raison de retirer une position ou d’ajuster le correctif silencieusement. Seul un échec technique autorise correction et relance du même périmètre. Deux exécutions hashseeds défaut/731, tests des frontières de sélection et métriques, reproduction Actions et comparaison des octets. Les anciens 3 356 FEN vérifiés sont réutilisés uniquement après authentification des preuves sans désaccord.

## Limites et coordination

Ce contrôle vise le défaut de prise des dames sur les plateaux historiques connus. Il ne valide pas les 403 572 FEN sans dame au trait, ni un meilleur coup, une valeur minimax ou un gain de recherche. Aucune nouvelle cohorte indépendante, réservation H13, partition, score Scan/Jass, signature, top-K, dimension ou gel scientifique. Cache ancien, règles par défaut, anciens résultats et 190 quarantaines inchangés ; uDIrrl1c entier reste candidat brut D1 non admis, quatre événements réservés exclus. Couverture historique globale et licence/indépendance fraîche restent portes distinctes. PC de Jeff non requis pour ce contrôle borné si les ressources distantes aboutissent.
