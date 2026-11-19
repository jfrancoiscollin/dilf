# D1 — Audit de couverture des rééchantillonnages bootstrap (2026-11-19)

Statut : **audit méthodologique pré-expérimental**, aucun nouveau résultat Scan/Jass.

## Problème vérifié dans le code

Dans `cluster_bootstrap.py`, le rappel@3 et le regret primaire utilisent les positions dont `n_legal >= 4`. Le bootstrap rééchantillonne **toutes** les parties, puis `interval()` écarte les tirages pour lesquels la métrique vaut `None`. Quand seules quelques parties contiennent des positions primaires, la distribution percentile est ainsi **conditionnelle à la présence d'au moins une partie éligible** ; elle n'est pas l'intervalle inconditionnel promis par une lecture rapide de `bootstrap_repetitions`.

Soient `G` parties, dont `E` avec au moins une position primaire. La probabilité qu'un tirage de `G` parties avec remise n'en contienne aucune est exactement `((G-E)/G)**G`. Exemple purement synthétique : `G=10, E=1`, soit `0.9**10 = 0.3486784401` ; environ 35 % des tirages ne définissent pas le rappel primaire. Aucun score cible n'est nécessaire pour détecter cette situation.

## Critère de validation à implémenter AVANT tout rapport

1. Rapporter `n_primary_games`, `n_bootstrap_defined_primary`, `n_bootstrap_undefined_primary` et le ratio défini, calculés **sans** modifier les tirages ou le seed.
2. Si `n_primary_games < 2` ou si moins de 95 % des tirages définissent la métrique primaire, publier `primary_ci_status = insufficient_cluster_coverage` et **ne pas** présenter l'IC percentile comme preuve. Garder les estimations observées et l'IC exploratoire explicitement étiqueté si nécessaire.
3. Conserver le dénominateur score-blind `n_legal >= 4` ; ne jamais supprimer des parties ou positions après inspection des scores pour améliorer la couverture.
4. Tester un jeu synthétique 10 parties / 1 partie primaire, un jeu où toutes les parties sont primaires, et la reproductibilité au seed fixé.
5. Ne pas convertir les scores bruts Scan en centipions sans calibration. Ne pas inférer l'équivalence minimax d'un bon rappel@3.

## Conséquences

Ce diagnostic ne démontre ni un biais mesuré sur une cohorte D1 réelle, ni une dégradation de Jass. Il indique une condition d'identifiabilité de l'intervalle statistique à faire respecter avant le gel du corpus et toute conclusion hors échantillon. Les quatre événements réservés à l'autre relais, y compris fFgE7oED, demeurent exclus du fitting, de la validation et du réglage D1.
