# Décomposition croisée des profondeurs — analyse exploratoire

Plan écrit le 19 novembre 2026 après les résultats 16/16 et 20/20, avant le calcul des tableaux croisés. **Post-hoc, même cohorte ; aucune nouvelle validation indépendante.** Aucune recherche moteur, aucun ajustement de signature, top-K ou dimension.

Conserver toutes les 26 paires LCB à signature complète égale du gel `3fa9a56`, source, correspondance des actions et propriétaires inchangés, y compris les coûts nuls. Relire les quatre paquets source/cible 16/20 archivés avec leurs octets publiés, hashes, types et catalogues légaux. Les cellules 16/16 et 20/20 doivent reproduire exactement les résumés et IC déjà publiés.

Pour chaque paire, `a16` et `a20` sont les premiers maximisateurs source selon l'ordre canonique déjà utilisé, sans changer les sources. `R(a,T) = max(T) - T[a]` en unités brutes ordinaires. Calculer les quatre cellules S16/T16, S16/T20, S20/T16, S20/T20 ; conserver aussi les ensembles complets de maximisateurs, les catégories et les échecs de départage malgré intersection.

Sur le **même masque des paires ordinaires dans les quatre cellules**, calculer :

- effet de référence à choix16 fixé : `R(a16,T20)-R(a16,T16)` ;
- effet du choix source à référence20 fixée : `R(a20,T20)-R(a16,T20)` ;
- chemin réciproque : changement de choix à référence16, puis de référence à choix20 ;
- delta apparié total 20/20−16/16 et interaction (différence des effets du choix entre références).

Vérifier l'identité additive exacte par paire et sur les sommes, pour les deux chemins. Si une cellule n'est pas ordinaire, garder la paire/catégories mais ne pas soustraire ces scores catégoriels ; tous les effets de cette paire valent null. Rapporter la taille de ce dénominateur, les changements de coup source et tous les cas, par arène et ensemble.

Bootstrap inchangé : cadre complet de 31 propriétaires gelés, parties entières avec remise, stratifié par les deux arènes, mêmes 10 000 tirages et seed 20261113, indices percentiles 249/9749 pour chaque cellule/effet. Aucune suppression ni nouveau tirage si un estimand est indéfini ; compteur explicite et IC null. Variation interne aux deux arènes, pas une inférence entre tournois. Les chemins sont des identités descriptives dépendant de la référence, pas une attribution causale ni un gain Jass.

Reproduction : `python -m research.mtdp.jass_benchmark.two_arena_crossed_depth --root . --output /tmp/crossed.json`. Deux processus aux PYTHONHASHSEED 7/61 doivent produire les mêmes octets ; recalcul indépendant des quatre cellules et des IC à partir des vecteurs bruts. Les résultats primaires et les 114 reçus Jass ne sont jamais réécrits.

Coordination D1 : les quatre événements entiers fFgE7oED, P1RUlfJc, s7ahYqL4 et D9PF2OSW restent exclus de fitting, validation indépendante, signature, top-K, refinement, seuils et dimension. Aucun nouveau corpus réservé.
